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

PRODUCT_TYPE = {
    'raw material': u'原料',
    'semi-finished': u'半成品',
    'finished': u'成品',
}
PURCHASE_TYPE = {
    'draft': u'草稿',
    'to approve': u'待审核',
    'purchase': u'采购订单',
    'make_by_mrp': u'MRP生成'
}


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    @api.multi
    def get_cost(self):
        if not self.product_variant_ids:
            raise UserError(u'已归档无法查看')
        bom_ids = self.bom_ids
        bom_lines = []
        process = False
        state_bom = False

        if bom_ids:
            bom = bom_ids[0]
            state_bom = bom.state
            lines = bom.bom_line_ids
            process = bom.process_id.name

            res = {}

            for line in lines:
                bom_ids = line.product_id.bom_ids
                if bom_ids:
                    line_process = bom_ids[0].process_id.name
                    state_bom_line = bom_ids[0].state
                res = {}
                level = False
                if line.product_id.bom_ids:
                    level = True

                total_cost = line.product_id.pre_cost_cal()
                material_cost = line.product_id.get_material_cost()
                man_cost = total_cost - material_cost
                res.update({
                    'product_id': line.product_id.product_tmpl_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'level': level,
                    'type': PRODUCT_TYPE.get(line.product_id.product_ll_type),
                    'product_qty': line.product_qty,
                    'part_no': line.product_id.default_code,
                    'service': line.product_id.order_ll_type,
                    'man_cost': round(man_cost, 5),
                    'material_cost': round(material_cost, 5),
                    'total_cost': round(total_cost, 5)

                })
                bom_lines.append(res)
        bom_lines.sort(key=lambda k: (k.get('type', 0)))
        total_cost = self.product_variant_ids[0].pre_cost_cal()
        material_cost = self.product_variant_ids[0].get_material_cost()
        man_cost = total_cost - material_cost
        return {
            'name': self.name,
            'bom_lines': bom_lines,
            'product_id': self.id,
            'product_p_id': self.product_variant_ids[0].id,
            'process': process,
            'type': PRODUCT_TYPE.get(self.product_ll_type),
            'part_no': self.default_code,
            'service': self.order_ll_type,
            'state_bom': state_bom,
            'man_cost': round(man_cost, 5),
            'material_cost': round(material_cost, 5),
            'total_cost': round(total_cost, 5)
        }

    @api.multi
    def cost_detail(self):
        return {
            'name': '成本明细',
            'type': 'ir.actions.client',
            'tag': 'cost_detail',
            'product_id': self.id
        }

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


class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    real_time_cost = fields.Float(related="product_tmpl_id.real_time_cost")

    @api.multi
    def cost_detail(self):
        return {
            'name': '成本明细',
            'type': 'ir.actions.client',
            'tag': 'cost_detail',
            'product_id': self.product_tmpl_id.id
        }

    @api.multi
    def get_material_cost(self):
        bom_obj = self.env['mrp.bom']
        for product in self:
            bom = bom_obj._bom_find(product=product)
            if bom:
                material_cost = 0.0
                for line in bom.bom_line_ids:
                    material_cost += line.product_id.pre_cost_cal() * line.product_qty
                return material_cost
            else:
                return product.get_highest_purchase_price()

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
                if sbom.child_bom_id and sbom.product_id.type == 'product':  # 如果有子阶
                    sub_bom_price = _calc_price(sbom.child_bom_id) * sbom_data['qty']
                    total_price += sub_bom_price
                else:
                    # 判断是否是采购件
                    pruchase_price = sbom.product_id.uom_id._compute_price(sbom.product_id.get_highest_purchase_price(),
                                                                           sbom.product_uom_id)
                    sub_price = pruchase_price * sbom_data['qty']
                    total_price += sub_price
            if total_price >= 0:
                expense_cost = bom.produced_spend_per_pcs * bom.process_id.hourly_wage / 3600
                total_price = bom.product_uom_id._compute_price(total_price / bom.product_qty,
                                                                self.uom_id) + expense_cost
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
