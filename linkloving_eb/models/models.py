# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class linkloving_eb_temporary_order_line(models.Model):
    _name = 'eb.order.line'

    eb_order_id = fields.Many2one('eb.order')
    qty = fields.Float(string=_("Quantity"))
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True,
                             ondelete='restrict', required=True)

class linkloving_eb_temporary_order(models.Model):
    _name = 'eb.order'

    @api.multi
    def _compute_is_finsish_transfer(self):
        for order in self:
            if order.state == "draft":
                order.is_finish_transfer = "no"
                continue
            order.is_finish_transfer = "yes"
            for picking in order.stock_picking_ids:
                if picking.state != "done":
                    order.is_finish_transfer = "no"
                    break

    name = fields.Char(string=_('Order Name'), require=True)
    eb_order_line_ids = fields.One2many('eb.order.line', 'eb_order_id')
    state = fields.Selection([("draft", _("Draft")),
                              ("confirm", _("Confirm")),#等待合并成销售订单
                              ("transfered", _("Transfered")),#已经合并成销售订单的
                             ], default="draft")

    my_create_date = fields.Date(string="创建时间", default=fields.datetime.now())
    stock_picking_ids = fields.One2many("stock.picking","eb_order_id")
    sale_order_id = fields.Many2one("sale.order")
    is_finish_transfer = fields.Selection([('yes', '已完成'),("no", "未完成")],"是否已经出货", compute="_compute_is_finsish_transfer")

    @api.multi
    def action_confirm(self):
        picking_out_2 = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('linkloving_eb.stock_location_eb_transfer').id,
            'eb_order_id' : self.id,
            })
        for one_line in self.eb_order_line_ids:
            self.env['stock.move'].create({
                'name': 'another move',
                'product_id': one_line.product_id.id,
                'product_uom_qty': one_line.qty,
                'product_uom': one_line.product_id.uom_id.id,
                'picking_id': picking_out_2.id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': self.env.ref('linkloving_eb.stock_location_eb_transfer').id})
        self.state = "confirm"
        return self.action_view_delivery()

    def action_view_delivery(self):

        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('stock_picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action


    @api.multi
    def back_to_wh(self):
        for line in self:
            picking_out_2 = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                'location_id': self.env.ref('linkloving_eb.stock_location_eb_transfer').id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                'eb_order_id': line.id,
            })
            for one_line in line.eb_order_line_ids:
                self.env['stock.move'].create({
                    'name': 'another move',
                    'product_id': one_line.product_id.id,
                    'product_uom_qty': one_line.qty,
                    'product_uom': one_line.product_id.uom_id.id,
                    'picking_id': picking_out_2.id,
                    'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                    'location_id': self.env.ref('linkloving_eb.stock_location_eb_transfer').id})

            picking_out_2.action_confirm()
            picking_out_2.force_assign()
            picking_out_2.do_transfer()
            picking_out_2.to_stock()

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('eb.order') or '/'

        return super(linkloving_eb_temporary_order, self).create(vals)
    

class linkloving_eb_stock_picking(models.Model):
    _inherit = "stock.picking"

    eb_order_id = fields.Many2one('eb.order')
    eb_refund_order_id = fields.Many2one("eb.refund.order")
class MultiCreateOrder(models.TransientModel):
    _name = "multi.create.order"


    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        eb_orders = self.env['eb.order'].search([('id','in', active_ids)])
        eb_order_lines = []
        for order in eb_orders:
            if order.state == "transfered":
                raise UserError(_("选择的条目中，包含了已经生成销售订单的单据"))

            # for picking in order.stock_picking_ids:
                if order.is_finish_transfer != "yes":
                    raise UserError(_("请确认选择的条目中，出库调拨是否都已完成"))

            eb_order_lines += order.eb_order_line_ids

        tax_id = self.env["account.tax"].search([('type_tax_use', '<>', "purchase")], limit=1)[0].id
        partner_id = self.env.ref("linkloving_eb.res_partner_eb_customer")
        sale_order = self.env["sale.order"].create({
            'partner_id': partner_id.id,
            'partner_invoice_id': partner_id.id,
            'partner_shipping_id': partner_id.id,
            'tax_id': tax_id,
            'order_line': [(0, 0, {'name': p.product_id.name,
                                   'product_id': p.product_id.id,
                                   'product_uom_qty': p.qty,
                                   'product_uom': p.product_id.uom_id.id,
                                   'price_unit': p.product_id.list_price,
                                   'tax_id' : [(6,0,[tax_id])]}) for p in eb_order_lines],
        })
        for order in eb_orders:
            order.back_to_wh()#先将原来的回到仓库
            order.sale_order_id = sale_order.id
            order.state = "transfered"

        return self.action_view_sale_order(sale_order.id)


    def action_view_sale_order(self, order_id):

        action = self.env.ref('linkloving_eb.action_show_sale_order').read()[0]

        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['res_id'] = order_id


        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'sale.order',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     "res_id" : order_id,
        #     'target': 'new',
        # }
        return action
        return {"type" : "ir.window.act_close"}



class Linkloving_eb_refunds_order(models.Model):
    _name = "eb.refund.order"

    tracking_num = fields.Char("快递单号")

    eb_refund_order_line_ids = fields.One2many('eb.refund.order.line', 'eb_refund_order_id')

    refund_img = fields.Binary("退货图片")
    state = fields.Selection([("draft", _("Draft")),#草稿
                              ("waiting_sale_confirm", _("等待销售确认")),#等待销售确认
                            ("confirmed", _("已确认")),  #销售已经确认
                            ], default="draft")

    stock_picking_ids = fields.One2many("stock.picking","eb_refund_order_id")


    @api.multi
    def action_confirm(self):#入库，并提交给销售确认
        self.refund_to_wh()

    @api.multi
    def action_ok(self):#已录入至后台
        for order in self:
            order.state = "confirmed"

    @api.multi
    def refund_to_wh(self):
        for line in self:
            picking_out_2 = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                'eb_refund_order_id': line.id,
            })
            for one_line in line.eb_refund_order_line_ids:
                self.env['stock.move'].create({
                    'name': 'another move',
                    'product_id': one_line.product_id.id,
                    'product_uom_qty': one_line.qty,
                    'product_uom': one_line.product_id.uom_id.id,
                    'picking_id': picking_out_2.id,
                    'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                    'location_id': self.env.ref('stock.stock_location_customers').id})

            picking_out_2.action_confirm()
            picking_out_2.force_assign()
            picking_out_2.do_transfer()
            picking_out_2.to_stock()

            line.state = "waiting_sale_confirm"

    def action_view_delivery(self):

        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('stock_picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action


class linkloving_eb_refunds_order_line(models.Model):
    _name = 'eb.refund.order.line'

    eb_refund_order_id = fields.Many2one('eb.refund.order')
    qty = fields.Float(string=_("Quantity"))
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True,
                             ondelete='restrict', required=True)