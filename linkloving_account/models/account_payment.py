# -*- coding: utf-8 -*-
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
from odoo import models, fields, api, _


class AccountPaymentRegister(models.Model):
    _name = 'account.payment.register'
    _order = 'create_date desc'
    _rec_name = 'amount'
    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    bank_id = fields.Many2one('res.partner.bank')
    tax_id = fields.Many2one('account.tax', string='税种')
    invoice_ids = fields.One2many('account.invoice', 'payment_id')
    apply_balance = fields.Float()

    state = fields.Selection([
        ('draft', u'草稿'),
        ('posted', u'提交'),
        ('confirm', u'审核'),
        ('register', u'登记付款'),
        ('done', u'付款完成'),
        ('cancel', u'取消')
    ], default='draft')
    description = fields.Text(string='备注')
    amount = fields.Float(string='Amount')
    used_amount = fields.Float(string='Used')
    _sql_constraints = {
        ('name_uniq', 'unique(name)',
         'Name must be unique!')
    }

    @api.multi
    def apply(self):
        self.state = 'posted'

    @api.multi
    def confirm(self):
        self.state = 'confirm'

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.payment.register') or _('New')
        return super(AccountPaymentRegister, self).create(vals)


class AccountReceiveRegisterBalance(models.Model):
    _name = 'account.receive.register.balance'
    amount = fields.Float()
    register_id = fields.Many2one('account.receive.register')
    invoice_id = fields.Many2one('account.invoice')


class AccountReceiveRegister(models.Model):
    _name = 'account.receive.register'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    name = fields.Char()
    balance_ids = fields.One2many('account.receive.register.balance', 'register_id')
    amount = fields.Float(string='金额')
    balance = fields.Float()
    bank_ids = fields.One2many(related='partner_id.bank_ids', string='客户账号')
    invoice_ids = fields.Many2many('account.invoice')
    receive_date = fields.Date(string='收款日期', default=fields.date.today())
    remark = fields.Text(string='备注')
    partner_id = fields.Many2one('res.partner', string='客户')
    is_customer = fields.Boolean(related='partner_id.customer', store=True)
    receive_id = fields.Many2one('res.users')
    journal_id = fields.Many2one('account.journal', 'Salary Journal')

    state = fields.Selection([
        ('draft', u'草稿'),
        ('posted', u'提交'),
        ('confirm', u'销售确认'),
        ('register', u'登记收款'),
        ('done', u'完成'),
        ('cancel', u'取消')
    ], 'State', readonly=True, default='draft')

    _sql_constraints = {
        ('name_uniq', 'unique(name)',
         'Name mast be unique!')
    }

    @api.multi
    def apply(self):
        self.state = 'posted'

    def _check_receive_amount(self):
        """ check receive amount must less or equal the total invoice amount """
        for register in self:
            total_amount = 0.0
            for invoice in register.invoice_ids:
                total_amount += invoice.amount_total
            if register.amount > total_amount:
                return False

        return True

    _constraints = [
        (_check_receive_amount, '对账单总金额小于收款金额', []),
    ]

    @api.multi
    def post(self):
        self.state='posted'

    @api.multi
    def confirm(self):
        self.state = 'posted'

    @api.model
    def create(self, vals):

        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.receive.register') or _('New')
        payment = super(AccountReceiveRegister, self).create(vals)
        balance = payment.amount
        for invoice in payment.invoice_ids:
            self.env['account.receive.register.balance'].create({
                'register_id': payment.id,
                'invoice_id': invoice.id,
                'amount': invoice.remain_apply_balance if balance >= invoice.amount_total else balance
            })
            balance -= invoice.amount_total
        return payment

    @api.multi
    def write(self, vals):
        print self.invoice_ids
        print vals.get('invoice_ids')

        return super(AccountReceiveRegister, self).write(vals)


class account_payment(models.Model):
    _inherit = 'account.payment'
    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            balance=invoice['amount_total']-invoice['remain_apply_balance']
            rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
            rec['currency_id'] = invoice['currency_id'][0]
            rec['payment_type'] = invoice['type'] in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
            rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
            rec['partner_id'] = invoice['partner_id'][0]
            rec['amount'] = invoice['residual'] if not invoice['remain_apply_balance'] else balance
            print rec['amount']
        return rec
