# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

from odoo.exceptions import UserError


class ReturnMaterial(models.Model):
    _name = 'return.goods'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    so_id = fields.Many2one('sale.order')
    tax_id = fields.Many2one('account.tax')
    date = fields.Date()
    remark = fields.Text(string=u'退货原因')
    tracking_number=fields.Char(string=u'物流信息')
    line_ids = fields.One2many('return.goods.line', 'return_id')
    state = fields.Selection([
        ('draft', u'草稿'),
        ('confirmed', u'确认'),
        ('done', u'完成')
    ], default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('return.goods') or 'New'

        result = super(ReturnMaterial, self).create(vals)
        return result

    @api.multi
    def _prepare_invoice(self):
        inv_obj = self.env['account.invoice']
        account_id = False
        if self.partner_id.customer:
            account_id = self.partner_id.property_account_payable_id.id
        else:
            account_id = self.partner_id.property_income_payable_id.id
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.supplier_id.name,))

        invoice = inv_obj.create({
            'origin': self.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': account_id,
            'partner_id': self.partner_id.id,
            # 'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'origin': self.name,
                'price_unit': self.unit_price,
                'account_id': 15,
                'quantity': self.qty_produced,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                # 'invoice_line_tax_ids': [(4, order.tax_id.id)],
                # 'account_analytic_id': order.project_id.id or False,
            })],
            # 'currency_id': order.pricelist_id.currency_id.id,
            # 'team_id': order.team_id.id,
            # 'comment': order.note,
        })
        # invoice.compute_taxes()
        # invoice.message_post_with_view('mail.message_origin_link',
        #             values={'self': invoice, 'origin': order},
        #             subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.multi
    def return_confirm(self):
        self._create_invoice()
        self.state = 'confirmed'


class ReturnMaterialLine(models.Model):
    _name = 'return.goods.line'
    return_id = fields.Many2one('return.goods')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    tax_id=fields.Many2one('account.tax')

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * line.product_uom_qty

            line.update({
                'price_subtotal': price
            })

    price_subtotal = fields.Float(compute=_compute_amount, string=u'小计')

    qty_delivered = fields.Float(string='Delivered', copy=False, digits=dp.get_precision('Product Unit of Measure'), default=0.0)



