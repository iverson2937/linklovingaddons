# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


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
    amount = fields.Float(string=u'Amount', compute='get_amount', store=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'account.payment.register'))
    approve_id = fields.Many2one('res.users')

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
    ], 'State', readonly=True, default='draft', track_visibility='onchange')

    account_payment_ids = fields.One2many('account.payment', 'res_id',
                                          domain=[('res_model', '=', 'account.payment.register')])

    @api.multi
    def _compute_has_payment_ids(self):
        for register in self:
            if register.account_payment_ids:
                register.has_payment_ids = True
            else:
                register.has_payment_ids = False

    has_payment_ids = fields.Boolean(compute=_compute_has_payment_ids)

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
        if self.state not in ['draft', 'manager', 'posted']:
            raise UserError(_('Only can delete records state in Draft and Post'))

        return super(AccountPaymentRegister, self).unlink()

    @api.multi
    def post(self):

        self.state = 'posted'

    def get_approve(self):
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

    @api.multi
    def confirm(self):
        self.get_approve()
        self.approve_id = self.env.user.id
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


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'ir.needaction_mixin', 'mail.thread']
    team_id = fields.Many2one('crm.team', related='partner_id.team_id')
    move_ids = fields.One2many('account.move', compute='_get_move_ids')
    customer = fields.Boolean(related='partner_id.customer')
    partner_id = fields.Many2one('res.partner', track_visibility='onchange')
    state = fields.Selection(selection_add=[('confirm', u'销售确认'), ('cancel', u'取消'), ('done', u'完成')],
                             track_visibility='onchange')
    remark = fields.Text(string='备注')
    product_id = fields.Many2one('product.product')

    res_model = fields.Char()
    res_id = fields.Integer()
    sheet_id = fields.Many2one('hr.expense.sheet', compute='get_sheet_id', string='报销单')
    account_employee_payment_id = fields.Many2one('account.employee.payment', compute='get_account_employee_payment_id',
                                                  string='暂支单')
    account_payment_register_id = fields.Many2one('account.payment.register', compute='get_account_payment_register_id',
                                                  string='付款申请')

    @api.multi
    def get_account_payment_register_id(self):
        for p in self:
            if p.res_id and p.res_model == 'account.payment.register':
                print p.res_id, p.id
                account_payment_register_id = self.env[p.res_model].browse(p.res_id)
                p.account_payment_register_id = account_payment_register_id.id

    @api.multi
    def get_account_employee_payment_id(self):
        for p in self:
            if p.res_id and p.res_model == 'account.employee.payment':
                print p.res_id, p.id
                account_employee_payment_id = self.env[p.res_model].browse(p.res_id)
                p.account_employee_payment_id = account_employee_payment_id.id

    @api.multi
    def get_sheet_id(self):
        for p in self:
            if p.res_id and p.res_model == 'hr.expense.sheet':
                print p.res_id, p.id
                sheet_id = self.env[p.res_model].browse(p.res_id)
                p.sheet_id = sheet_id.id

    def _get_move_ids(self):
        self.move_ids = self.move_line_ids.mapped('move_id').ids

    # origin = fields.Char(string=u'源单据')
    @api.multi
    def set_to_post(self):
        self.state = 'posted'

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            # 如果默认给客户付钱的话，partner_type就不修改了
            elif self.payment_type == 'outbound' and not self._context.get('apply'):
                self.partner_type = 'supplier'
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        res['domain']['journal_id'] = self.payment_type == 'inbound' and [('at_least_one_inbound', '=', True)] or [
            ('at_least_one_outbound', '=', True)]
        res['domain']['journal_id'].append(('type', 'in', ('bank', 'cash')))
        res['domain']['journal_id'].append(('deprecated', '=', False))

        res['domain']['payment_method_id'] = [('payment_type', '=', self.payment_type)]
        payment_method = self.env['account.payment.method'].search([('payment_type', '=', self.payment_type)])
        if payment_method:
            self.payment_method_id = payment_method[0].id

        return res

    @api.multi
    def set_to_cancel(self):
        self.state = 'cancel'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if len(self.move_line_ids) > 2:
            raise UserError(u'不允许修改')
        if self.product_id and not self.product_id.property_account_income_id:
            raise UserError(u'请设置产品收入科目')
        if self.move_line_ids:
            for move in self.move_line_ids:
                if move.move_id.state == 'posted':
                    raise UserError(u'不可修改已过账的分录')
                if move.account_id != self.journal_id.default_credit_account_id:
                    move.account_id = self.product_id.property_account_income_id.id

    def set_to_done(self):
        if self.partner_type == 'customer' and not self.partner_id:
            raise UserError(u'请填写客户')
        if self.partner_id:
            for move in self.move_line_ids:
                move.partner_id = self.partner_id
        self.state = 'done'

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        # Set partner_id domain
        if self.partner_type == 'employee':
            return {'domain': {'partner_id': [(self.partner_type, '=', True)]}}
        elif self.partner_type in ('customer', 'supplier'):
            return {'domain': {'partner_id': [(self.partner_type, '=', True), ('is_company', '=', True)]}}

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            amount = 0.0
            for balance_id in invoice['balance_ids']:
                balance_obj = self.env['account.payment.register.balance']
                balance = balance_obj.browse(balance_id)
                if not balance.state:
                    amount += balance.amount
            rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
            rec['currency_id'] = invoice['currency_id'][0]
            rec['payment_type'] = invoice['type'] in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
            rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
            rec['partner_id'] = invoice['partner_id'][0]
            rec['amount'] = amount
        return rec

    def _get_counterpart_move_line_vals(self, invoice=False):
        if self.payment_type == 'transfer':
            name = self.name
        else:
            name = '/'
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment")
                elif self.payment_type == 'outbound':
                    name += _("Customer Refund")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Refund")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment")
            if invoice:
                name += ': '
                for inv in invoice:
                    if inv.move_id:
                        name += inv.number + ', '
                name = name[:len(name) - 2]
        print 'name', name
        return {
            'name': name,
            'account_id': self.destination_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
            'payment_id': self.id,
        }

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state not in ['draft', 'approve']:
                raise UserError(
                    _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            sequence_code = 'account.payment.employee'
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'

            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                elif rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
                elif rec.partner_type == 'other':
                    sequence_code = 'account.payment.other'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                sequence_code)

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()
            # add by allen
            for balance in rec.invoice_ids.balance_ids:
                balance.state = 1
            state = 'posted'
            if self.partner_type == 'customer' and self.payment_type == 'inbound':
                state = 'confirm'
            rec.write({'state': state, 'move_name': move.name})

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action
        """
        state = self._context.get('state')
        return [('state', '=', state)]

    def _get_counterpart_move_line_vals(self, invoice=False):
        if self.payment_type == 'transfer':
            name = self.name
        elif self.payment_type == 'other':
            name = u'其他收入'
        else:
            name = '/'
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment")
                elif self.payment_type == 'outbound':
                    name += _("Customer Refund")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Refund")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment")
            if invoice:
                name += ': '
                for inv in invoice:
                    if inv.move_id:
                        name += inv.number + ', '
                name = name[:len(name) - 2]

        return {
            'name': name,
            'account_id': self.destination_account_id.id if self.destination_account_id else self.product_id.property_account_income_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
            'payment_id': self.id,
        }

    @api.multi
    def button_journal_entries(self):

        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }
