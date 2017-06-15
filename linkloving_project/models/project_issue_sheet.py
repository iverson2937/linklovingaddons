# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _


class project_issue(models.Model):
    _inherit = 'project.issue'
    _description = 'project issue'

    timesheet_ids = fields.One2many('hr.analytic.timesheet', 'issue_id', 'Timesheets')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.onchange("project_id")
    def on_change_project(self):
        if not self.project_id:
            return {}

        result = super(project_issue, self).on_change_project(self.project_id)

        if 'value' not in result:
            result['value'] = {}

        account = self.project_id.analytic_account_id
        if account:
            result['value']['analytic_account_id'] = account.id

        return result

    @api.onchange("account_id")
    def on_change_account_id(self):
        if not self.account_id:
            return {}
        result = {}

        if self.account_id and self.account_id.state == 'pending':
            result = {'warning': {'title': _('Analytic Account'), 'message': _('The Analytic Account is pending !')}}

        return result


class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'account analytic line'

    create_date = fields.Datetime('Create Date', readonly=True)


class hr_analytic_timesheet(models.Model):
    _name = "hr.analytic.timesheet"
    _table = 'hr_analytic_timesheet'
    _description = "Timesheet Line"
    _inherits = {'account.analytic.line': 'line_id'}
    _order = "id desc"

    line_id = fields.Many2one('account.analytic.line', 'Analytic Line', ondelete='cascade', required=True)
    partner_id = fields.Many2one('res.partner', related='account_id.partner_id', string='Partner', store=True)
    issue_id = fields.Many2one('project.issue', 'Issue')

    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', default="_getEmployeeUnit")
    product_id = fields.Many2one('product.product', 'Product', default="_getEmployeeProduct")
    general_account_id = fields.Many2one('account.account', 'General Account', required=True, ondelete='restrict',
                                         default="_getGeneralAccount")
    journal_id = fields.Many2one('account.analytic.journal', 'Analytic Journal', required=True, ondelete='restrict',
                                 select=True, default="_getAnalyticJournal")
    date = fields.Date()
    user_id = fields.Many2one('res.users')

    @api.multi
    def unlink(self):
        toremove = {}
        for obj in self:
            toremove[obj.line_id.id] = True
        super(hr_analytic_timesheet, self).unlink()
        self.env['account.analytic.line'].unlink(toremove.keys())
        return True

    # @api.onchange("prod_id", "unit_amount", "company_id", "unit", "journal_id")
    def on_change_unit_amount(self):
        res = {'value': {}}
        if self.prod_id and self.unit_amount:
            # find company
            company_id = self.env['res.company']._company_default_get('account.analytic.line')
            r = self.env['account.analytic.line'].on_change_unit_amount(self.prod_id, self.unit_amount, company_id,
                                                                        self.unit, self.journal_id)
            if r:
                res.update(r)
        # update unit of measurement
        if self.prod_id.uom_id:
            res['value'].update({'product_uom_id': self.prod_id.uom_id.id})
        else:
            res['value'].update({'product_uom_id': False})
        return res

    def _getEmployeeProduct(self):
        emp_obj = self.env['hr.employee']
        emp_id = emp_obj.search([('user_id', '=', self._context.get('user_id') or self.env.user.id)])
        if self.emp.product_id:
            return self.emp.product_id.id
        return False

    def _getEmployeeUnit(self):
        emp_obj = self.env['hr.employee']
        emp_id = emp_obj.search([('user_id', '=', self._context.get('user_id') or self.env.user.id)])
        if self.emp.product_id:
            return self.emp.product_id.uom_id.id
        return False

    def _getGeneralAccount(self):
        emp_obj = self.env['hr.employee']
        emp_id = emp_obj.search([('user_id', '=', self._context.get('user_id') or self.env.user.id)])
        if bool(self.emp.product_id):
            a = self.emp.product_id.property_account_expense.id
            if not a:
                a = self.emp.product_id.categ_id.property_account_expense_categ.id
            if a:
                return a
        return False

    def _getAnalyticJournal(self):
        emp_obj = self.env['hr.employee']
        if self._context.get('employee_id'):
            emp_id = [self._context.get('employee_id')]
        else:
            emp_id = emp_obj.search([('user_id', '=', self._context.get('user_id') or self.env.user.id)], limit=1)
        if not emp_id:
            model, action_id = self.env['ir.model.data'].get_object_reference('hr', 'open_view_employee_list_my')
            msg = _("Employee is not created for this user. Please create one from configuration panel.")
            raise UserWarning('Go to the configuration panel')
        emp = emp_obj.browse(emp_id[0])
        if emp.journal_id:
            return emp.journal_id.id
        else:
            raise UserWarning(
                'No analytic journal defined for \'%s\'.\nYou should assign an analytic journal on the employee form.')

    @api.onchange("account_id")
    def on_change_account_id(self):
        return {'value': {}}

    @api.onchange("date")
    def on_change_date(self):
        if self._ids:
            new_date = self.read(self._ids[0], ['date'])['date']
            if self._date != new_date:
                warning = {'title': _('User Alert!'), 'message': _(
                    'Changing the date will let this entry appear in the timesheet of the new date.')}
                return {'value': {}, 'warning': warning}
        return {'value': {}}

    @api.model
    def create(self, vals):
        emp_obj = self.env['hr.employee']
        emp_id = emp_obj.search([('user_id', '=', self._context.get('user_id') or self.env.user.id)])
        ename = ''
        if emp_id:
            ename = emp_obj.browse(emp_id[0]).name
        if not vals.get('journal_id', False):
            raise UserWarning(
                'No \'Analytic Journal\' is defined for employee %s \nDefine an employee for the selected user and assign an \'Analytic Journal\'!')
        if not vals.get('account_id', False):
            raise UserWarning(
                'No analytic account is defined on the project.\nPlease set one or we cannot automatically fill the timesheet.')
        return super(hr_analytic_timesheet, self).create(vals)

    # @api.onchange("user_id")
    def on_change_user_id(self):
        if not self.user_id:
            return {}
        context = {'user_id': self.user_id}
        return {'value': {
            'product_id': self._getEmployeeProduct(),
            'product_uom_id': self._getEmployeeUnit(),
            'general_account_id': self._getGeneralAccount(),
            'journal_id': self._getAnalyticJournal(),
        }}


class hr_analytic_issue(models.Model):
    _inherit = 'hr.analytic.timesheet'
    _description = 'hr analytic timesheet'

    issue_id = fields.Many2one('project.issue', 'Issue')


class hr_timesheet_invoice_factor(models.Model):

    _name = "hr_timesheet_invoice.factor"
    _description = "Invoice Rate"
    _order = 'factor'

    name = fields.Char('Internal Name', required=True, translate=True)
    customer_name = fields.Char('Name', help="Label for the customer")
    factor = fields.Float('Discount (%)', required=True, help="Discount in percentage")


class account_analytic_account(models.Model):
    _inherit = "account.analytic.account"

    def _invoiced_calc(self):
        # obj_invoice = self.pool.get('account.invoice')
        res = {}
        #
        # cr.execute('SELECT account_id as account_id, l.invoice_id '
        #         'FROM hr_analytic_timesheet h LEFT JOIN account_analytic_line l '
        #             'ON (h.line_id=l.id) '
        #             'WHERE l.account_id = ANY(%s)', (ids,))
        # account_to_invoice_map = {}
        # for rec in cr.dictfetchall():
        #     account_to_invoice_map.setdefault(rec['account_id'], []).append(rec['invoice_id'])
        #
        # for account in self.browse(cr, uid, ids, context=context):
        #     invoice_ids = filter(None, list(set(account_to_invoice_map.get(account.id, []))))
        #     for invoice in obj_invoice.browse(cr, uid, invoice_ids, context=context):
        #         res.setdefault(account.id, 0.0)
        #         res[account.id] += invoice.amount_untaxed
        # for id in ids:
        #     res[id] = round(res.get(id, 0.0),2)

        return res

    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist',
                                   help="The product to invoice is defined on the employee form, the price will be deducted by this pricelist on the product.")

    amount_max = fields.Float('Max. Invoice Price',  help="Keep empty if this contract is not limited to a total fixed price.")

    amount_invoiced = fields.Float(compute=_invoiced_calc, string='Invoiced Amount', help="Total invoiced")

    to_invoice = fields.Many2one('hr_timesheet_invoice.factor', 'Timesheet Invoicing Ratio',
                                 help="You usually invoice 100% of the timesheets. But if you mix fixed price and timesheet invoicing, you may use another ratio. For instance, if you do a 20% advance invoice (fixed price, based on a sales order), you should invoice the rest on timesheet with a 80% ratio.")



