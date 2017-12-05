# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, models, fields
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def compute_price(self):
        if self.product_variant_count == 1:
            return self.product_variant_id.compute_price()


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def compute_price(self):
        self.ensure_one()
        bom_obj = self.env['mrp.bom']
        # action_rec = self.env.ref('stock_account.action_view_change_standard_price')
        bom = bom_obj._bom_find(product=self)
        if bom:
            price = self._calc_price(bom)
            return price
        raise UserError(u"未找到BOM")

    def _calc_price(self, bom):
        price = 0.0
        workcenter_cost = 0.0
        result, result2 = bom.explode(self, 1)
        for sbom, sbom_data in result2:
            if not sbom.attribute_value_ids:
                # No attribute_value_ids means the bom line is not variant specific
                if not bom.process_id or not bom.process_id.hourly_wage:
                    raise UserError(u"该bom未找到对应的工序或者工序未设置工种")
                sub_price = sbom.product_id.uom_id._compute_price(sbom.product_id.standard_price, sbom.product_uom_id) \
                            * sbom_data['qty']
                price += sub_price
        # if bom.routing_id:
        #     total_cost = 0.0
        #     for order in bom.routing_id.operation_ids:
        #         total_cost += (order.time_cycle_manual/60) * order.workcenter_id.costs_hour
        #     workcenter_cost = total_cost / len(bom.routing_id.operation_ids)
        #     price += bom.product_uom_id._compute_price(workcenter_cost, bom.product_id.uom_id)
        # Convert on product UoM quantities
        if price > 0:
            price = bom.product_uom_id._compute_price(price / bom.product_qty, self.uom_id) + bom.expense_cost
        return price


class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def _compute_expense_cost(self):
        for bom in self:
            bom.expense_cost = bom.produced_spend_per_pcs * bom.process_id.hourly_wage / 3600

    expense_cost = fields.Float(compute='_compute_expense_cost', string=u'人工成本')


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def product_price_update_before_done(self):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on 生产入库 if the product cost_method is 'average'
        for move in self.filtered(lambda move: move.location_id.usage == 'production' and
                        move.location_dest_id.usage == 'internal' and
                        move.production_id.product_id.id == move.product_id.id and  # FIXME 不适用于多产出
                        move.product_id.cost_method == 'average' and
                not move.is_return_material and
                not move.is_scrap):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            if move.quantity_done <= 0:
                continue
            # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
            if product_tot_qty_available <= 0:
                new_std_price = move.product_id.compute_price()
            else:
                # Get the standard price
                amount_unit = move.product_id.standard_price
                new_std_price = ((amount_unit * product_tot_qty_available) + (
                move.product_id.compute_price() * move.quantity_done)) / (
                                product_tot_qty_available + move.quantity_done)

            tmpl_dict[move.product_id.id] += move.quantity_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).write({'standard_price': new_std_price})
        return super(StockMoveExtend, self).product_price_update_before_done()
