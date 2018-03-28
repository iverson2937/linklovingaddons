# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    head_circle = fields.Float(string=u'刀长/面积')

    def view_new_product_cost(self):
        return {
            "type": "ir.actions.client",
            "tag": "cost_detail_new",
            'product_id': self.id,
        }

    def get_product_default_cost_detail(self):
        if self.bom_ids:
            return self.bom_ids[0].get_default_bom_cost()

    @api.multi
    def get_product_cost_detail(self):
        if self.bom_ids:
            return self.bom_ids[0].get_bom_cost_new()
        else:
            if self.product_ll_type:
                product_type_dict = dict(
                    self.fields_get(['product_ll_type'])['product_ll_type']['selection'])

            material_cost = self.product_variant_ids[0].get_material_cost_new()
            result = []
            res = {
                'id': 1,
                'pid': 0,
                'bom_id': self.id,
                'product_tmpl_id': self.id,
                'product_specs': self.product_specs,
                'name': self.name_get()[0][1],
                'code': self.default_code,
                # 'process_id': [self.process_id.id, self.process_id.name],
                'product_type': product_type_dict[self.product_ll_type],
                'material_cost': round(material_cost, 5),
                'manpower_cost': 0,
                'total_cost': round(material_cost, 5),
                # 'bom_ids': sorted(res, key=lambda product: product['code']),
            }
            result.append(res)
            return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_material_cost_new(self):
        bom_obj = self.env['mrp.bom']
        for product in self:
            bom = bom_obj._bom_find(product=product)
            if bom:
                material_cost = 0.0
                for line in bom.bom_line_ids:
                    precost = line.product_id.pre_cost_cal_new(raise_exception=False) or 0
                    material_cost += precost * line.product_qty
                return material_cost
            else:
                return product.get_highest_purchase_price(raise_exception=False)

    @api.multi
    def get_pure_manpower_cost(self):
        def _calc_manpower_cost(bom):
            total_price = 0.0000
            result, result2 = bom.explode(self, 1)
            for sbom, sbom_data in result2:
                if sbom.child_bom_id:  # 如果有子阶
                    sub_bom_price = _calc_manpower_cost(sbom.child_bom_id) * sbom_data['qty']
                    total_price += sub_bom_price
            total_price += bom.manpower_cost
            return total_price

        bom_obj = self.env['mrp.bom']
        for pp in self:
            bom = bom_obj._bom_find(product=pp)
            if bom:
                man_power_cost = _calc_manpower_cost(bom)
                return man_power_cost
            else:
                return 0

    @api.multi
    def pre_cost_cal_new(self, raise_exception=True):
        """
        计算成本(工程核价)
        :return:
        """
        buy_route_id = self.env.ref("purchase.route_warehouse0_buy")
        man_route_id = self.env.ref("mrp.route_warehouse0_manufacture")

        def _calc_price_new(bom):
            total_price = 0.0000
            result, result2 = bom.explode(self, 1)
            for sbom, sbom_data in result2:
                if sbom.child_bom_id and man_route_id in sbom.child_bom_id.product_tmpl_id.route_ids:  # 如果有子阶
                    sub_bom_price = _calc_price_new(sbom.child_bom_id) * sbom_data['qty']
                    total_price += sub_bom_price
                elif buy_route_id in sbom.product_id.route_ids:
                    # 判断是否是采购件
                    # if sbom.product_id.qty_available == 0:
                    #     continue
                    pruchase_price = sbom.product_id.uom_id._compute_price(
                        sbom.product_id.get_highest_purchase_price(raise_exception),
                        sbom.product_uom_id)
                    sub_price = pruchase_price * sbom_data['qty']
                    total_price += sub_price
            #  bom.manpower_cost
            if total_price >= 0:
                total_price = bom.product_uom_id._compute_price(total_price / bom.product_qty,
                                                                self.uom_id) + bom.manpower_cost
            return total_price

        bom_obj = self.env['mrp.bom']
        for pp in self:
            if man_route_id in pp.route_ids:
                bom = bom_obj._bom_find(product=pp)
                if bom:
                    real_time_cost = _calc_price_new(bom)
                    return real_time_cost
                else:
                    return 0
            elif buy_route_id in pp.route_ids:
                return pp.get_highest_purchase_price(raise_exception)
