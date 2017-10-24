# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseApply(models.Model):
    _name = 'hr.purchase.apply'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char()
    apply_date = fields.Date(string=u'申请日期', default=fields.Date.context_today)
    employee_id = fields.Many2one('hr.employee',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1))
    department_id = fields.Many2one('hr.department')
    to_approve_id = fields.Many2one('hr.employee')
    line_ids = fields.One2many('hr.purchase.apply.line', 'apply_id')

    @api.multi
    def refuse_application(self, reason):
        self.write({'state': 'cancel'})
        for record in self:
            body = (_(
                "Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (
                        record.name, reason))
            record.message_post(body=body)
            record.to_approve_id = False

    state = fields.Selection([
        ('draft', u'草稿'),
        ('cancel', u'取消'),
        ('done', u'完成')
    ])
    company_id = fields.Many2one('res.company')
    total_amount = fields.Float()

    def _get_is_show(self):
        is_show = False
        if self.env.user.id == self.to_approve_id.id:
            is_show = True
        self.is_show = is_show

    is_show = fields.Boolean(compute=_get_is_show)
    description = fields.Text()

    @api.multi
    def unlink(self):
        if self.state not in ['draft', 'cancel']:
            raise UserError('只可以删除草稿状态的采购申请.')
        return super(PurchaseApply, self).unlink()


class PurchaseApplyLine(models.Model):
    _name = 'hr.purchase.apply.line'

    apply_id = fields.Many2one('purchase.apply')
    product_id = fields.Many2one('hr.employee')
    product_qty = fields.Float(string=u'申购数量')
    price_unit = fields.Float(string=u'预计金额')
    description = fields.Char(string=u'说明')
    tax_id = fields.Many2one('account.tax')
