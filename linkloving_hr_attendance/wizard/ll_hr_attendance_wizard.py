# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrAttendanceWizard(models.TransientModel):
    _name = 'll.hr.attendance.wizard'

    start_date = fields.Date(u'开始时间',
                             default=datetime.date.today().replace(day=1))
    end_date = fields.Date(u'结束时间', default=datetime.datetime.now())

    def get_data_hr_attendance(self,start_date,end_date):
        returnDict = {}
        return_hr_attendance= self.env['hr.attendance']

        domain = ['|',
            ('new_check_in', '>=', start_date), ('check_out', '<=', end_date)]
        return_ids = return_hr_attendance.read_group(domain, fields=['employee_id', 'new_check_in', 'check_out'],
            groupby='employee_id')
        index = 0
        for return_id in return_ids:
            returnDict[index] = {'data': {},'start_date':start_date,'end_date':end_date}
            attendance = return_hr_attendance.sudo().search([("employee_id", "=", return_id['employee_id'][0])])
            time_arr = []
            if(len(attendance)):
                for attendance_detail in attendance:
                    if attendance_detail.new_check_in:
                        time_arr.append(attendance_detail.new_check_in)
                    if attendance_detail.check_out:
                        time_arr.append(attendance_detail.check_out)
            returnDict[index]['data'] = {
                'time_arr':time_arr,
                'employee_id': attendance[0].employee_id.name,
            }
            index = index + 1
        return returnDict

    @api.multi
    def print_report(self):

        for report in self:
            report_name = ''
            datas = {}
            datas = self.get_data_hr_attendance(report.start_date, report.end_date)
            report_name = 'linkloving_hr_attendance.ll_hr_attendance_report'
        if not datas:
            raise UserError(u'没找到相关数据')

        return self.env['report'].get_action(self, report_name, datas)