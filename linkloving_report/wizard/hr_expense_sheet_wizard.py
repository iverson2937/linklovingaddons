# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class HrExpenseSheetWizard(models.TransientModel):
    _name = 'hr.expense.sheet.wizard'

    start_date = fields.Date(u'Start Dare',
                             default=(datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1))
    end_date = fields.Date(u'End Date', default=datetime.datetime.now())

    def _get_data_by_hr_expense_sheet(self, date1, date2):
        returnDict = {}
        hr_expense_sheet = self.env['hr.expense.sheet']

        hr_expense_sheet_ids = hr_expense_sheet.search([
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
            datas = self._get_data_by_hr_expense_sheet(report.start_date, report.end_date)
            report_name = 'linkloving_report.linkloving_hr_expense_sheet_report'

            return self.env['report'].get_action(self, report_name, datas)
