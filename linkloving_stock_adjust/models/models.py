# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockTransfer(models.Model):
    _name = 'stock.transfer'
    _order = 'create_date desc'
    name = fields.Char('名称', default='New')
    picking_type_id = fields.Many2one('stock.picking')
    input_product_ids = fields.One2many('stock.transfer.line', 'transfer_id', domain=[('product_type', '=', 'input')])
    output_product_ids = fields.One2many('stock.transfer.line', 'transfer_id', domain=[('product_type', '=', 'output')])
    remark = fields.Text(string=u'备注')

    @api.model
    def _default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    location_id = fields.Many2one('stock.location', default=_default_location_id)

    state = fields.Selection([
        ('draft', u'草稿'),
        ('confirm', u'确定'),
        ('done', u'提交'),
    ], default='draft')

    # @api.model
    # def _get_default_picking_type(self):
    #     return self.env['stock.picking.type'].search([
    #         ('code', '=', 'mrp_operation'),
    #         (
    #             'warehouse_id.company_id', 'in',
    #             [self.env.context.get('company_id', self.env.user.company_id.id), False])],
    #         limit=1).id
    #
    # picking_type_id = fields.Many2one(
    #     'stock.picking.type', 'Picking Type',
    #     default=_get_default_picking_type, required=True)
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            print self.env['ir.sequence'].next_by_code('stock.transfer') or 'New'
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer') or 'New'
        return super(StockTransfer, self).create(vals)

    @api.multi
    def confirm(self):
        self.state = 'confirm'

    @api.multi
    def confirm_transfer(self):
        if self.remark:
            name = '_'.join([self.name, self.remark])
        else:
            name = self.name
        inv_id = self.env['stock.inventory'].create({
            'filter': 'partial',
            'name': name,
            'reason': self.remark,
            'remark': 'transfer'
        })
        inv_id.prepare_inventory()
        print inv_id
        for record in self.input_product_ids:
            self.env['stock.inventory.line'].create({
                'product_id': record.product_id.id,
                'product_qty': record.product_id.qty_available - record.product_qty,
                'inventory_id': inv_id.id,
                'location_id': inv_id.location_id.id,
                'remark_adjust': self.remark
            })
        for output in self.output_product_ids:
            self.env['stock.inventory.line'].create({
                'product_id': output.product_id.id,
                'product_qty': output.product_id.qty_available + output.product_qty,
                'inventory_id': inv_id.id,
                'location_id': inv_id.location_id.id,
                'remark_adjust': self.remark
            })

        self.state = 'done'


class StockTransferLine(models.Model):
    _name = 'stock.transfer.line'
    _order = 'create_date desc'
    transfer_id = fields.Many2one('stock.transfer', on_delete="cascade")
    qty_available = fields.Float(related='product_id.qty_available')
    product_id = fields.Many2one('product.product')
    product_qty = fields.Float(string=u'数量')
    product_type = fields.Selection([
        ('input', u'投入'),
        ('output', u'产出')
    ])


class AdjustInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    remark_adjust = fields.Char(string=u'备注')
