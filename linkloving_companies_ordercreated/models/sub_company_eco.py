# -*- coding: utf-8 -*-
import json

import requests
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    cancel_order_ids = fields.One2many(comodel_name="ll.stock.picking.cancel",
                                       inverse_name="purchase_id",
                                       string=u"需求变更单",
                                       required=False, )

    def button_picking_cancel(self):
        cancel_picking = self.picking_ids.filtered(lambda x: x.state not in ["done", "cancel"])

        if self.cancel_order_ids.filtered(lambda x: x.state == 'draft'):
            raise UserError(u'已有一张草稿状态的需求变更单.')
        if not cancel_picking:
            raise UserError(u'该采购单暂无可处理的调拨单')
        return {
            'name': u'需求变更单',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'll.stock.picking.cancel',
            'target': 'current',
            'context': {
                'default_purchase_id': self.id,
            }
        }


class StockPickingEco(models.Model):
    _name = 'll.stock.picking.cancel'
    _order = 'create_date desc'
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Name', required=True, index=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('ll.stock.picking.cancel'))
    purchase_id = fields.Many2one('purchase.order', domain=[('sub_company', '=', 'sub')], string=u'采购单')
    sale_id = fields.Many2one('sale.order', domain=[('sub_company', '=', 'main')], string=u'销售单')
    picking_id = fields.Many2one('stock.picking', string=u'可处理的调拨单', domain=[('purchase_id', '=', 'purchase_id')])

    cancel_line_ids = fields.One2many(comodel_name="picking.cancel.line",
                                      inverse_name="cancel_id",
                                      string=u"明细",
                                      required=False, )

    state = fields.Selection(string=u"状态",
                             selection=[('draft', u'草稿'), ('done', u'完成'), ],
                             required=False,
                             default='draft')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "单号必须唯一"),
    ]

    def button_confirm_order(self):
        if self.picking_id.state in ["done", "cancel"]:
            raise UserError(u'该调拨单无法执行此操作')
        if self.state == 'draft':
            self._create_main_company_eco()
            self._create_sub_company_eco()
            self.state = 'done'

    def _create_main_company_eco(self):
        self.confirm_eco_split_move()

    def confirm_eco_split_move(self):
        move_after_split = self.env["stock.move"]
        # 如果取消全部 则直接把调拨单取消即可
        if all([line.cancel_qty == line.move_id.product_uom_qty for line in self.cancel_line_ids]) and \
                        len(self.cancel_line_ids) == len(self.picking_id.move_lines):
            self.picking_id.action_cancel()
            return True
        for line in self.cancel_line_ids:
            if line.cancel_qty == 0:
                continue
            if line.cancel_qty > line.move_id.product_uom_qty:
                raise UserError(u'取消数量不能大于库存移动的数量')
            move_to_split = line.move_id
            if line.cancel_qty == line.move_id.product_uom_qty:
                if len(self.picking_id.move_lines) == 1 and \
                                self.picking_id.move_lines == line.move_id:
                    self.picking_id.action_cancel()
                else:
                    move_after_split += move_to_split
            else:
                id_to_cancel = move_to_split.split(line.cancel_qty)
                move_after_split += self.env["stock.move"].browse(id_to_cancel)  # 分割后#分割后 新的move 新的move
        backorder_picking = self.picking_id.copy({
            'name': '/',
            'move_lines': [],
            'pack_operation_ids': [],
        })
        move_after_split.write({'picking_id': backorder_picking.id})
        if self.picking_id.state not in ["cancel", "done"]:
            self.picking_id.action_assign()
        backorder_picking.action_cancel()

    def _create_sub_company_eco(self):
        url, db, header = self.purchase_id.partner_id.sub_company_id.get_request_info('/linkloving_web/do_eco')
        if not self.purchase_id.so_name_from_sub or not self.purchase_id.so_id_from_sub:
            raise UserError(u'此单据未记录子系统中对应的销售单')
        cancel_lines_list = []
        for line in self.cancel_line_ids:
            cancel_lines_list.append({
                'line_id': line.id,
                'default_code': line.product_id.default_code,
                'cancel_qty': line.cancel_qty
            })

        response = requests.post(url, data=json.dumps({
            "db": db,
            "vals": {
                'po_name': self.purchase_id.name,
                'so_name': self.purchase_id.so_name_from_sub,
                'so_id': self.purchase_id.so_id_from_sub,
                'cancel_lines_list': cancel_lines_list
            }
        }), headers=header)
        return self.handle_response(response)

    def handle_response(self, response):
        res_json = json.loads(response.content).get("result")
        res_error = json.loads(response.content).get("error")
        if res_json and res_json.get("code") < 0:
            raise UserError(res_json.get("msg"))
        if res_error:
            raise UserError(res_error.get("data").get("message"))
        return res_json

    @api.model
    def create(self, vals):
        return super(StockPickingEco, self).create(vals)

    @api.onchange('purchase_id')
    def _onchange_picking_id(self):
        if self.purchase_id:
            cancel_picking = self.purchase_id.picking_ids.filtered(lambda x: x.state not in ["done", "cancel"])
            if cancel_picking:
                self.picking_id = cancel_picking[0]
                lines = self._prepare_cancel_lines()
                self.cancel_line_ids = lines
            else:
                raise UserError(u'该采购单暂无可处理的调拨单')

    def _prepare_cancel_lines(self):
        line_vals = []
        tmp_order_dic = {}
        for line in self.purchase_id.order_line:
            tmp_order_dic[line.product_id.default_code] = line

        for move in self.picking_id.move_lines.filtered(lambda x: x.state not in ['done', 'cancel']):
            line_vals.append((0, 0, {
                'move_id': move.id,
                'product_id': move.product_id,
                'product_uom_qty': move.product_uom_qty,
                'product_uom': move.product_uom,
                'cancel_qty': 0,
                'done_qty': tmp_order_dic[move.product_id.default_code].qty_received,
                'total_qty': tmp_order_dic[move.product_id.default_code].product_qty,
            }))

        return line_vals


class PickingEcoLine(models.Model):
    _name = 'picking.cancel.line'

    product_id = fields.Many2one(
            'product.product', 'Product',
            domain=[('type', 'in', ['product', 'consu'])], index=True, required=True,
    )

    product_uom_qty = fields.Float(
            '初始数量',
            digits=dp.get_precision('Product Unit of Measure'),
            required=True
    )
    product_uom = fields.Many2one(
            'product.uom', u'单位', required=True)

    total_qty = fields.Float(
            '订单总数量',
            digits=dp.get_precision('Product Unit of Measure'),
    )

    done_qty = fields.Float(
            '已完成数量',
            digits=dp.get_precision('Product Unit of Measure'),
    )
    cancel_qty = fields.Float(
            '取消数量',
            digits=dp.get_precision('Product Unit of Measure'),
            required=True
    )

    move_id = fields.Many2one('stock.move', string=u'相关的库存移动单')
    cancel_id = fields.Many2one('ll.stock.picking.cancel')
