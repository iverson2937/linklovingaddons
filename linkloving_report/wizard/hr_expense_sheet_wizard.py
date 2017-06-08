# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class HrExpenseSheetWizard(models.TransientModel):
    _name = 'hr.expense.sheet.wizard'

    start_date = fields.Date(u'开始时间',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'结束时间', default=datetime.datetime.now())
    income = fields.Boolean()

    def _get_data_by_hr_expense_sheet(self, date1, date2, income):
        returnDict = {}
        hr_expense_sheet = self.env['hr.expense.sheet']

        hr_expense_sheet_ids = hr_expense_sheet.search([
            ('income', '=', income),
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

    @api.multi
    def print_report(self):

        for report in self:
            if self._context.get('prepayment_outgoing'):
                datas = self._get_data_by_pre_payment_income(report.start_date, report.end_date)
                report_name = 'linkloving_report.prepayment_income_report'
            elif self._context.get('income'):
                datas = self._get_data_by_hr_expense_sheet(report.start_date, report.end_date, report.income)
                report_name = 'linkloving_report.linkloving_hr_expense_sheet_report'


            return self.env['report'].get_action(self, report_name, datas)
