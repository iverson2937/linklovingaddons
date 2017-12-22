# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


# class linkloving_product_input_extend(models.Model):
#     _name = 'linkloving_product_input_extend.linkloving_product_input_extend'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class linklpving_product_product(models.Model):
    _inherit = 'product.product'

    product_ll_type = fields.Selection(related="product_tmpl_id.product_ll_type",
                                       string="类型",
                                       selection=[('raw material', '原料'),
                                                  ('semi-finished', '半成品'),
                                                  ('finished', '成品')])
    order_ll_type = fields.Selection(related="product_tmpl_id.order_ll_type",
                                     string="订单类型", selection=[('ordering', '订单制'),
                                                               ('stock', '备货制')],
                                     help="订单制:路线自动选中按订单生成项,备货制:需要填写最大最小存货数量")

    @api.onchange('order_ll_type')
    def _onchange_order_ll_type(self):
        self.order_ll_type = self.order_ll_type
        if self.order_ll_type == "ordering":  # 订单制
            self.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,
                                      self.env.ref('stock.route_warehouse0_mto').id])]
        elif self.order_ll_type == "stock":  # 备货制
            self.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id])]
            return {'warning': {
                'title': "请创建存货规则",
                'message': "具体最大最小存货数量,请点击右上方 '订货规则'按钮进行创建!"
            }
            }

    @api.onchange('product_ll_type')
    def _onchange_product_ll_type(self):
        self.product_ll_type = self.product_ll_type
        if self.product_ll_type == "raw material":  # 原料
            self.sale_ok = False
            self.purchase_ok = True
            self.route_ids = [(6, 0, (
                self.env.ref('stock.route_warehouse0_mto').id, self.env.ref('purchase.route_warehouse0_buy').id))]
        elif self.product_ll_type == "semi-finished":  # 半成品
            self.sale_ok = False
            self.purchase_ok = False
            self.route_ids = [(6, 0, (
                self.env.ref('stock.route_warehouse0_mto').id, self.env.ref('mrp.route_warehouse0_manufacture').id))]
        elif self.product_ll_type == "finished":  # 成品
            self.sale_ok = True
            self.purchase_ok = False
            self.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id, ])]


class linkloving_product_input_extend(models.Model):
    _inherit = 'product.template'

    product_ll_type = fields.Selection([
        ('raw material', '原料'),
        ('semi-finished', '半成品'),
        ('finished', '成品'),
        ('service', '服务'),
        ('assets', '固定资产')
    ], copy=True, string="物料类型")

    order_ll_type = fields.Selection(string="订单类型",
                                     selection=[('ordering', '订单制'),
                                                ('stock', '备货制')], help="订单制:路线自动选中按订单生成项,备货制:需要填写最大最小存货数量")

    @api.onchange('order_ll_type')
    def _onchange_order_ll_type(self):
        self.order_ll_type = self.order_ll_type
        if self.order_ll_type == "ordering":  # 订单制
            self.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,
                                      self.env.ref('stock.route_warehouse0_mto').id])]
        elif self.order_ll_type == "stock":  # 备货制
            self.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id])]
            return {'warning': {
                'title': "请创建存货规则",
                'message': "具体最大最小存货数量,请点击右上方 '订货规则'按钮进行创建!"
            }
            }

    @api.onchange('product_ll_type')
    def _onchange_product_ll_type(self):
        self.product_ll_type = self.product_ll_type
        if self.product_ll_type == "raw material":  # 原料
            self.sale_ok = False
            self.purchase_ok = True
            self.route_ids = [(6, 0, (
                self.env.ref('stock.route_warehouse0_mto').id, self.env.ref('purchase.route_warehouse0_buy').id))]
        elif self.product_ll_type == "semi-finished":  # 半成品
            self.sale_ok = False
            self.purchase_ok = False
            self.route_ids = [(6, 0, (
                self.env.ref('stock.route_warehouse0_mto').id, self.env.ref('mrp.route_warehouse0_manufacture').id))]
        elif self.product_ll_type == "finished":  # 成品
            self.sale_ok = True
            self.purchase_ok = False
            self.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id, ])]


class StockOrdering(models.TransientModel):
    _name = "stock.ordering"

    max_qty = fields.Float("最大存货数量")
    min_qty = fields.Float("最小存货数量")


class MultiSetType(models.TransientModel):
    _name = "multi.set.type"

    product_ll_type = fields.Selection(string="物料类型", selection=[('raw material', '原料'),
                                                                 ('semi-finished', '半成品'),
                                                                 ('finished', '成品')])

    order_ll_type = fields.Selection(string="订单类型",
                                     selection=[('ordering', '订单制'),
                                                ('stock', '备货制')], help="订单制:路线自动选中按订单生成项,备货制:需要填写最大最小存货数量")

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        products = self.env['product.template'].search([('id', 'in', active_ids)])

        for product in products:
            product.product_ll_type = self.product_ll_type
            if self.product_ll_type == "raw material":  # 原料
                product.sale_ok = False
                product.purchase_ok = True
                product.route_ids = [(6, 0, (
                    self.env.ref('stock.route_warehouse0_mto').id, self.env.ref('purchase.route_warehouse0_buy').id))]
            elif self.product_ll_type == "semi-finished":  # 半成品
                product.sale_ok = False
                product.purchase_ok = False
                product.route_ids = [(6, 0, (
                    self.env.ref('stock.route_warehouse0_mto').id,
                    self.env.ref('mrp.route_warehouse0_manufacture').id))]
            elif self.product_ll_type == "finished":  # 成品
                product.order_ll_type = self.order_ll_type
                product.sale_ok = True
                product.purchase_ok = False
                if self.order_ll_type == "ordering":  # 订单制
                    product.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,
                                                 self.env.ref('stock.route_warehouse0_mto').id])]
                elif self.order_ll_type == "stock":  # 备货制
                    product.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id])]
