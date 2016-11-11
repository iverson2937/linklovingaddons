# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentRegister(models.Model):
    _name = 'account.payment.register'
    _order = 'create_date desc'
    _rec_name = 'amount'
    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    bank_id = fields.Many2one('res.partner.bank')
    tax_id = fields.Many2one('account.tax', string='税种')
    invoice_ids=fields.Many2one()
    state = fields.Selection([
        ('draft', u'草稿'),
        ('posted', u'提交'),
        ('confirm', u'确认'),
        ('done', u'完成'),
        ('cancel', u'取消')
    ], default='draft')
    description = fields.Text(string='备注')
    amount = fields.Float(string='Amount')
    used_amount=fields.Float(string='Used')


    _sql_constraints = {
        ('name_uniq', 'unique(name)',
         'Name mast be unique!')
    }
    @api.multi
    def apply(self):
        self.state='posted'

    @api.multi
    def confirm(self):
        self.state = 'confirm'

class AccountReceiveRegister(models.Model):
    _name = 'account.receive.register'
    _order = 'create_date desc'
    name = fields.Char()
    amount = fields.Float(string='金额')
    bank_ids = fields.One2many(related='partner_id.bank_ids', string='客户账号')
    receive_date = fields.Date(string='收款日期', default=fields.date.today())
    remark = fields.Text(string='备注')
    partner_id = fields.Many2one('res.partner', string='客户')
    is_customer = fields.Boolean(related='partner_id.customer', store=True)
    receive_id = fields.Many2one('res.users')
    journal_id = fields.Many2one('account.journal', 'Salary Journal')
    state = fields.Selection([
        ('draft', '草稿'),
        ('posted', '提交'),
        ('confirm', '销售确认'),
        ('done', '完成'),
        ('cancel', '取消')
    ], 'State', readonly=True, default='draft')

    _sql_constraints = {
        ('name_uniq', 'unique(name)',
         'Name mast be unique!')
    }
    @api.multi
    def apply(self):
        self.state='posted'
