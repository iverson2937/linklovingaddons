# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class linkloving_precost_calculation(models.Model):
#     _name = 'linkloving_precost_calculation.linkloving_precost_calculation'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    real_time_cost = fields.Float(computed="_compute_real_time_cost")

    @api.multi
    def _compute_real_time_cost(self):
        for p in self:
            if p.product_variant_count == 1:
                p.real_time_cost = p.product_variant_id.pre_cost_cal()

    def btn_pre_cost_cal(self):
        if self.product_variant_count == 1:
            price = self.product_variant_id.pre_cost_cal() or 0
            return {
                "type": "ir.actions.client",
                "tag": "action_notify",
                "params": {
                    "title": u"计算完成",
                    "text": u"成本为: %f" % price,
                    "sticky": False
                }
            }
        else:
            raise UserError(u"产品变型过多")


class ProductTemplateExtend(models.Model):
    _inherit = 'product.product'

    real_time_cost = fields.Float(related="product_tmpl_id.real_time_cost")

    @api.multi
    def pre_cost_cal(self):
        """
        计算成本(工程核价)
        :return:
        """

        def _calc_price(bom):
            total_price = 0.0000
            result, result2 = bom.explode(self, 1)
            for sbom, sbom_data in result2:
                if sbom.child_bom_id:  # 如果有子阶
                    sub_bom_price = _calc_price(sbom.child_bom_id) * sbom_data['qty']
                    total_price += sub_bom_price
                else:
                    # 判断是否是采购件
                    pruchase_price = sbom.product_id.uom_id._compute_price(sbom.product_id.get_highest_purchase_price(),
                                                                           sbom.product_uom_id)
                    sub_price = pruchase_price * sbom_data['qty']
                    total_price += sub_price
            if total_price >= 0:
                total_price = bom.product_uom_id._compute_price(total_price / bom.product_qty,
                                                                self.uom_id) + bom.expense_cost
            return total_price

        bom_obj = self.env['mrp.bom']
        for pp in self:
            bom = bom_obj._bom_find(product=pp)
            if bom:
                real_time_cost = _calc_price(bom)
                return real_time_cost
            else:
                return pp.get_highest_purchase_price()

    @api.multi
    def get_highest_purchase_price(self):
        for p in self:
            if p.seller_ids:
                return max(p.seller_ids.mapped("price"))
            else:
                raise UserError(u'%s 未设置采购价' % p.display_name)
