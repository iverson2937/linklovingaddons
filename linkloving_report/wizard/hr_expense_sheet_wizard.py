# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpenseSheetWizard(models.TransientModel):
    _name = 'hr.expense.sheet.wizard'

    start_date = fields.Date(u'开始时间',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'结束时间', default=datetime.datetime.now())
    employee_ids = fields.Many2many('hr.employee')

    def _get_payment_by_hr_expense_sheet(self, date1, date2):

        returnDict = {}
        account_payment = self.env['account.payment'].sudo()

        payment_ids = account_payment.search([
            ('res_model', '=', 'hr.expense.sheet')], order='create_date desc')

        sheet_sequence = 1
        for payment_id in payment_ids:
            res_id = payment_id.res_id
            hr_expense_sheet = self.env['hr.expense.sheet'].browse(res_id)
            returnDict[payment_id.id] = {'data': {}, 'line': {}}
            returnDict[payment_id.id]['data'] = {
                'sequence': sheet_sequence,
                'accounting_date': payment_id.payment_date,
                'employee_id': payment_id.partner_id.name,
                'amount': payment_id.amount,
                'department_id': hr_expense_sheet.department_id.name,
                'expense_no': hr_expense_sheet.expense_no,
                'name': payment_id.name,
                'expense_sheet_amount': hr_expense_sheet.total_amount,
                # 'create_uid': payment.create_uid.name,
            }
            # for line in payment.payment_line_ids:
            #     returnDict[payment.id]['line'].update({line.id: {
            #         'expense_no': line.expense_no,
            #         'name': line.name,
            #         'amount_total': line.sheet_id.total_amount,
            #         'amount': line.amount,
            #     }})
        return returnDict

    def _get_data_by_turn_payment(self, date1, date2):
        returnDict = {}
        return_payment = self.env['account.employee.payment.return']

        return_ids = return_payment.search([
            ('create_date', '>=', date1), ('create_date', '<=', date2)], order='create_date desc')

        sheet_sequence = 1
        for return_id in return_ids:
            returnDict[return_id.id] = {'data': {}, 'line': {}}
            returnDict[return_id.id]['data'] = {
                'sequence': sheet_sequence,
                'create_date': return_id.create_date,
                'employee_id': return_id.employee_id.name,
                'amount': return_id.amount,
                'payment_id': return_id.payment_id.name,
                'create_uid': return_id.create_uid.name,
                # 'create_uid': payment.create_uid.name,
            }
            # for line in payment.payment_line_ids:
            #     returnDict[payment.id]['line'].update({line.id: {
            #         'expense_no': line.expense_no,
            #         'name': line.name,
            #         'amount_total': line.sheet_id.total_amount,
            #         'amount': line.amount,
            #     }})
        return returnDict

    def _get_data_by_sale_income_payment(self, date1, date2):
        returnDict = {}
        employee_payment = self.env['account.payment']

        payment_ids = employee_payment.search([
            ('payment_type', '=', 'inbound'),
            ('state', '!=', 'draft'),
            ('payment_date', '>=', date1), ('payment_date', '<=', date2)], order='name desc')

        sheet_sequence = 1
        for payment in payment_ids:
            returnDict[payment.id] = {'data': {}, 'line': {}}
            returnDict[payment.id]['data'] = {
                'sequence': sheet_sequence,
                'name': payment.name,
                'payment_date': payment.payment_date,
                'journal_id': payment.journal_id.name,
                'partner_id': payment.partner_id.name,
                'team_id': payment.partner_id.team_id.name if payment.partner_id.team_id.name else u'未设置团队',
                'sale_man': payment.partner_id.user_id.name if payment.partner_id.user_id else u'为设置业务员',
                'amount': payment.amount,
                'remark': payment.remark
                # 'create_uid': payment.create_uid.name,
            }
            # for line in payment.payment_line_ids:
            #     returnDict[payment.id]['line'].update({line.id: {
            #         'expense_no': line.expense_no,
            #         'name': line.name,
            #         'amount_total': line.sheet_id.total_amount,
            #         'amount': line.amount,
            #     }})
        return returnDict

    def _get_data_by_purchase_payment(self, date1, date2):
        returnDict = {}
        employee_payment = self.env['account.payment.register']

        payment_ids = employee_payment.search([
            ('state', '=', 'done'),
            ('receive_date', '>=', date1), ('receive_date', '<=', date2)], order='name desc')

        sheet_sequence = 1
        for payment in payment_ids:
            returnDict[payment.id] = {'data': {}, 'line': {}}
            returnDict[payment.id]['data'] = {
                'sequence': sheet_sequence,
                'name': payment.name,
                'receive_date': payment.receive_date,
                'supplier': payment.partner_id.name,
                'amount': payment.amount,
                'create_uid': payment.create_uid.name,
            }
            # for line in payment.payment_line_ids:
            #     returnDict[payment.id]['line'].update({line.id: {
            #         'expense_no': line.expense_no,
            #         'name': line.name,
            #         'amount_total': line.sheet_id.total_amount,
            #         'amount': line.amount,
            #     }})
        return returnDict

    def _get_data_by_pre_payment_deduct(self, date1, date2):
        returnDict = {}
        employee_payment = self.env['account.employee.payment']
        domain = [
            ('state', '=', 'paid'),
            ('accounting_date', '>=', date1), ('accounting_date', '<=', date2)]
        if self.employee_ids:
            employee_ids = self.employee_ids.ids
            domain.append(('employee_id', 'in', employee_ids))

        payment_ids = employee_payment.search(domain, order='name desc')

        sheet_sequence = 1
        for payment in payment_ids:
            returnDict[payment.id] = {'data': {}, 'line': {}}
            returnDict[payment.id]['data'] = {
                'sequence': sheet_sequence,
                'accounting_date': payment.accounting_date,
                'name': payment.name,
                'employee': payment.employee_id.name,
                'department': payment.department_id.name,
                'amount': payment.amount,
                'pre_payment_reminding': payment.pre_payment_reminding
            }
            for line in payment.payment_line_ids:
                returnDict[payment.id]['line'].update({line.id: {
                    'expense_no': line.expense_no,
                    'name': line.name,
                    'amount_total': line.sheet_id.total_amount,
                    'amount': line.amount,
                }})
        return returnDict

    def _get_data_by_pre_payment_income(self, date1, date2):
        returnDict = {}
        employee_payment = self.env['account.employee.payment']
        domain = [
            ('state', '=', 'paid'),
            ('accounting_date', '>=', date1), ('accounting_date', '<=', date2)]
        if self.employee_ids:
            employee_ids = self.employee_ids.ids
            domain.append(('employee_id', 'in', employee_ids))
        payment_ids = employee_payment.search(domain, order='name desc')

        sheet_sequence = 1
        for payment in payment_ids:
            returnDict[payment.id] = {'data': {}, 'line': {}}
            returnDict[payment.id]['data'] = {
                'sequence': sheet_sequence,
                'accounting_date': payment.accounting_date,
                'name': payment.name,
                'remark': payment.remark,
                'department': payment.department_id.name,
                'amount': payment.amount,
                'employee': payment.employee_id.name
            }
        return returnDict

    def _get_data_by_hr_expense_sheet_income(self, date1, date2):
        returnDict = {}
        hr_expense_sheet = self.env['hr.expense.sheet']

        hr_expense_sheet_ids = hr_expense_sheet.search([
            ('income', '=', True),
            ('state', 'not in', ('draft', 'cancel')),
            ('accounting_date', '>=', date1), ('accounting_date', '<=', date2)], order='expense_no desc')

        sheet_sequence = 1
        for sheet in hr_expense_sheet_ids:
            returnDict[sheet.id] = {'data': {}, 'line': {}}
            returnDict[sheet.id]['data'] = {
                'sequence': sheet_sequence,
                'accounting_date': sheet.accounting_date,
                'expense_no': sheet.expense_no,
                'department': sheet.department_id.name,

                'total_amount': sheet.total_amount,
            }
            for line in sheet.expense_line_ids:
                returnDict[sheet.id]['line'].update({line.id: {
                    'product': line.product_id.name,
                    'name': line.name,
                    'employee': sheet.employee_id.name,
                    'total_amount': line.total_amount,
                }})
        return returnDict

    def _get_data_by_hr_expense_sheet_expense(self, date1, date2):
        returnDict = {}
        hr_expense_sheet = self.env['hr.expense.sheet']

        hr_expense_sheet_ids = hr_expense_sheet.search([
            ('income', '=', False),
            ('state', 'not in', ('draft', 'cancel')),
            ('accounting_date', '>=', date1), ('accounting_date', '<=', date2)], order='expense_no desc')

        sheet_sequence = 1
        for sheet in hr_expense_sheet_ids:
            ids = []
            if sheet.account_payment_line_ids:
                for line in sheet.account_payment_line_ids:
                    if line.payment_id:
                        ids.append(line.payment_id.name + ';')
            returnDict[sheet.id] = {'data': {}, 'line': {}}
            returnDict[sheet.id]['data'] = {
                'sequence': sheet_sequence,
                'accounting_date': sheet.accounting_date,
                'expense_no': sheet.expense_no,
                'department': sheet.department_id.name,

                'total_amount': sheet.total_amount,
            }
            for line in sheet.expense_line_ids:
                returnDict[sheet.id]['line'].update({line.id: {
                    'product': line.product_id.name,
                    'quantity': line.quantity,
                    'unit_amount': line.unit_amount,
                    'name': line.name,
                    'employee': sheet.employee_id.name,
                    'remark': line.description,
                    'payment_line_ids': ids,
                    'total_amount': line.total_amount,
                }})
        return returnDict

    @api.multi
    def print_report(self):

        for report in self:
            report_name = ''
            datas = {}
            if self._context.get('prepayment_outgoing'):
                datas = self._get_data_by_pre_payment_income(report.start_date, report.end_date)
                report_name = 'linkloving_report.pre_payment_report'
            elif self._context.get('prepayment_deduct'):
                datas = self._get_data_by_pre_payment_deduct(report.start_date, report.end_date)
                report_name = 'linkloving_report.pre_payment_deduct_report'
            elif self._context.get('expense'):
                datas = self._get_data_by_hr_expense_sheet_expense(report.start_date, report.end_date)
                report_name = 'linkloving_report.linkloving_hr_expense_sheet_report'
            elif self._context.get('income'):
                datas = self._get_data_by_hr_expense_sheet_income(report.start_date, report.end_date)
                report_name = 'linkloving_report.linkloving_hr_expense_sheet_report'
            elif self._context.get('purchase'):
                datas = self._get_data_by_purchase_payment(report.start_date, report.end_date)
                report_name = 'linkloving_report.purchase_payment_report'
            elif self._context.get('sale'):
                datas = self._get_data_by_sale_income_payment(report.start_date, report.end_date)
                report_name = 'linkloving_report.account_payment_income_report'
            elif self._context.get('return'):
                datas = self._get_data_by_turn_payment(report.start_date, report.end_date)
                report_name = 'linkloving_report.return_account_payment_report'
            elif self._context.get('payment_sheet'):
                datas = self._get_payment_by_hr_expense_sheet(report.start_date, report.end_date)
                report_name = 'linkloving_report.linkloving_account_payment_hr_expense_sheet'

            if not datas:
                raise UserError(u'没找到相关数据')

            return self.env['report'].get_action(self, report_name, datas)
