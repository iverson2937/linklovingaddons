# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _


class AccountPaymentRegisterBalance(models.Model):
    _name = 'account.payment.register.balance'
    state = fields.Selection([
        (0, u'未付'),
        (1, u'已付'),
    ], default=0)
    amount = fields.Float()
    payment_id = fields.Many2one('account.payment.register', ondelete='cascade')
    invoice_id = fields.Many2one('account.invoice')


class AccountPaymentRegister(models.Model):
    """
    付款申请表
    """

    _name = 'account.payment.register'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    name = fields.Char()
    balance_ids = fields.One2many('account.payment.register.balance', 'payment_id')
    amount = fields.Float(string=u'Amount', compute='get_amount', store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'account.payment.register'))

    @api.model
    @api.returns('self', lambda value: value.id)
    def _company_default_get(self, object=False, field=False):
        """ Returns the default company (usually the user's company).
        The 'object' and 'field' arguments are ignored but left here for
        backward compatibility and potential override.
        """
        return self.env['res.users']._get_company()

    @api.multi
    def register_payment(self):
        amount = self.amount

        context = {'default_payment_type': 'outbound', 'default_amount': amount,
                   'default_partner_id': self.partner_id.id}

        return {
            'name': _('Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'account.supplier.payment.wizard',
            'domain': [],
            'context': dict(context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.depends('invoice_ids')
    def get_amount(self):
        amount = 0
        for invoice in self.invoice_ids:
            amount += invoice.remain_apply_balance
        self.amount = amount

    bank_id = fields.Many2one('res.partner.bank', string=u'Account', domain="[('partner_id', '=', partner_id)]")
    invoice_ids = fields.Many2many('account.invoice')
    receive_date = fields.Date(string=u'Receive Date', default=fields.date.today())
    remark = fields.Text(string=u'Remark')
    partner_id = fields.Many2one('res.partner', string=u'Partner')
    is_customer = fields.Boolean(related='partner_id.customer', store=True)
    receive_id = fields.Many2one('res.users')
    account_id = fields.Many2one('account.account')
    payment_type = fields.Selection([
        (1, u'付款'),
        (2, u'收款')
    ])

    @api.onchange('partner_id')
    def change_partner_id(self):
        self.invoice_ids = None

    state = fields.Selection([
        ('draft', u'Draft'),
        ('posted', u'Post'),
        ('confirm', u'Confirm'),
        ('register', u'Register'),
        ('done', u'Done'),
        ('cancel', u'Cancel')
    ], 'State', readonly=True, default='draft')

    _sql_constraints = {
        ('name_uniq', 'unique(name)',
         'Name must be unique!')
    }

    @api.multi
    def reject(self):

        for balance_id in self.balance_ids:
            balance_id.unlink()
        self.state = 'draft'

    @api.multi
    def unlink(self):
        if self.state not in ['draft', 'posted']:
            raise UserError(_('Only can delete records state in Draft and Post'))

        return super(AccountPaymentRegister, self).unlink()

    @api.multi
    def post(self):

        self.state = 'posted'

    @api.multi
    def confirm(self):
        balance = self.amount
        if self.payment_type == 2 and balance > sum(self.mapped('invoice_ids.amount_total')):
            raise UserError(_('Apply Amount cannot less than Invoices Amount'))
        for invoice in self.invoice_ids:
            balance_id = self.env['account.payment.register.balance'].create({
                'payment_id': self.id,
                'invoice_id': invoice.id,
                'amount': invoice.remain_apply_balance if balance >= invoice.remain_apply_balance else balance
            })
            balance -= balance_id.amount
        self.state = 'confirm'

    @api.multi
    def done(self):
        for balance in self.balance_ids:
            if not balance.state:
                raise UserError(_('These is unclosed Payment，Can not close this Record'))

        self.state = 'done'

    @api.model
    def create(self, vals):
        payment_type = self._context.get('default_payment_type')

        if 'name' not in vals or vals['name'] == _('New'):
            if payment_type == 2:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.receive') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.pay') or _('New')
        return super(AccountPaymentRegister, self).create(vals)

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """

        if self._context.get('wait_pay'):
            return [('state', '=', 'confirm')]
        if self._context.get('posted'):
            return [('state', '=', 'posted')]
