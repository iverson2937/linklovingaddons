# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrAttendanceWizard(models.TransientModel):
    _name = 'll.hr.attendance.wizard'

    start_date = fields.Date(u'开始时间',
                             default=datetime.date.today().replace(day=1))
    end_date = fields.Date(u'结束时间', default=datetime.datetime.now())

    def get_data_hr_attendance(self, start_date, end_date):
        returnDict = {}
        return_hr_attendance = self.env['hr.attendance']

        domain = [
            ('write_date', '>=', start_date), ('write_date', '<=', end_date)]
        return_ids = return_hr_attendance.read_group(domain, fields=['employee_id', 'new_check_in', 'check_out'],
                                                     groupby='employee_id')
        index = 0
        for return_id in return_ids:
            returnDict[index] = {'data': {}, 'start_date': start_date, 'end_date': end_date}
            attendance = return_hr_attendance.sudo().search([("employee_id", "=", return_id['employee_id'][0]),('write_date', '>=', start_date), ('write_date', '<=', end_date)])
            time_arr = []
            if (len(attendance)):
                for attendance_detail in attendance:
                    if attendance_detail.new_check_in:
                        time_arr.append(attendance_detail.new_check_in)
                    if attendance_detail.check_out:
                        time_arr.append(attendance_detail.check_out)
            returnDict[index]['data'] = {
                'time_arr': time_arr,
                'employee_id': attendance[0].employee_id.name,
            }
            index = index + 1
        return returnDict

    @api.multi
    def print_report(self):
        for report in self:
            report_name = ''
            datas = {}
            origin_arr = []
            datas = self.get_data_hr_attendance(report.start_date, report.end_date)

            # date1 = datetime.datetime.strptime(report.start_date, "%Y-%m-%d")
            # date2 = datetime.datetime.strptime(report.end_date, "%Y-%m-%d")
            # for index_now in range(1, ((date2 - date1).days + 2)):
            #     origin_arr.append(" ")
        # for data in datas:
        #     employee = datas[data].get('data').get('employee_id')
        #     data_time_arr = []
        #     for index_now in range(1, ((date2 - date1).days + 2)):
        #         data_time_arr.append([])
        #     for time in datas[data].get('data').get('time_arr'):
        #         time_date = datetime.datetime.strptime(time.get('time'), "%Y-%m-%d %H:%M:%S")
        #         data_time_arr[(time_date + timedelta(hours=8)).day - 1].append(time)
        #     origin_arr.append({
        #         "employee_id": employee,
        #         "data_arr": data_time_arr,
        #     })
        #     # print origin_arr
        # for arr in origin_arr:
        #     start_now = datetime.date.today().replace(day=1)
        #     for detail in arr.get('data_arr'):
        #         if len(detail) > 0:  # 当天是否有数据
        #             attendance_regular = self.env['rt.attendance.regular'].sudo().search([])
        #             check_in_1 = ''
        #             check_out_1 = ''
        #             check_in_2 = ''
        #             check_out_2 = ''
        #             start_overtime_least = ''
        #             start_overtime_continue = ''
        #
        #             # 获取当天考勤规则
        #             for regular in attendance_regular.rt_week_regular_lines:
        #                 if regular.rt_week_type == str(start_now.weekday() + 1):
        #                     check_in_1 = regular.rt_check_in_1
        #                     check_out_1 = regular.rt_check_out_1
        #                     check_in_2 = regular.rt_check_in_2
        #                     check_out_2 = regular.rt_check_out_2
        #                     start_overtime_least = regular.rt_overtime_setting_id.rt_start_over_time
        #                     start_overtime_continue = regular.rt_overtime_setting_id.rt_min_over_time
        #             # 区分每日数据
        #             check_in_time = ''
        #             check_out_time = ''
        #             # 工作时间
        #             work_seconds = 0.0
        #             # 加班时间
        #             extra_seconds = 0.0
        #
        #             # print len(detail)
        #             index_time = 0
        #             for data in detail:
        #                 index_time = index_time + 1
        #                 if check_in_time == '' and data.get('is_check_in') == True:
        #                     check_in_time = datetime.datetime.strptime(data.get('time'),
        #                                                                    "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
        #                 if check_in_time != '' and data.get('is_check_in') == True:
        #                     if check_out_time != '':
        #                         check_in_time_1 = check_in_time.replace(hour=int(check_in_1.split(':')[0])).replace(
        #                             minute=int(check_in_1.split(':')[1]))
        #                         check_out_time_1 = check_in_time.replace(hour=int(check_out_1.split(':')[0])).replace(
        #                             minute=int(check_out_1.split(':')[1]))
        #                         check_in_time_2 = check_in_time.replace(hour=int(check_in_2.split(':')[0])).replace(
        #                             minute=int(check_in_2.split(':')[1]))
        #                         check_out_time_2 = check_in_time.replace(hour=int(check_out_2.split(':')[0])).replace(
        #                             minute=int(check_out_2.split(':')[1]))
        #                         # 上班记录在check_in_1之前取check_in_1
        #                         if check_in_time <= check_in_time_1:
        #                             check_in_time = check_in_time_1
        #                             if check_out_time >= check_out_time_1 and check_out_time < check_in_time_2:
        #                                 check_out_time = check_out_time_1
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time > check_in_time_1 and check_out_time < check_out_time_1:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time >= check_in_time_2 and check_out_time < check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time_1).seconds + (
        #                                     check_out_time - check_in_time_2).seconds
        #                             elif check_out_time >= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time_1).seconds + (
        #                                     check_out_time_2 - check_in_time_2).seconds
        #                         elif check_in_time > check_in_time_1 and check_in_time < check_out_time_1:
        #                             if check_out_time > check_in_time_1 and check_out_time <= check_out_time_1:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time > check_out_time_1 and check_out_time < check_in_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time).seconds
        #                             elif check_out_time >= check_in_time_2 and check_out_time < check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time).seconds + (
        #                                     check_out_time - check_in_time_2).seconds
        #                             elif check_out_time >= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time).seconds + (
        #                                     check_out_time_2 - check_in_time_2).seconds
        #                         elif check_in_time >= check_out_time_1 and check_in_time < check_in_time_2:
        #                             if check_out_time > check_in_time_2 and check_out_time < check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time_2).seconds
        #                             elif check_out_time >= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_2 - check_in_time_2).seconds
        #                         elif check_in_time > check_in_time_2 and check_in_time < check_out_time_2:
        #                             if check_out_time > check_in_time_2 and check_out_time <= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time > check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_2 - check_in_time).seconds
        #                         elif check_in_time >= check_out_time_2:
        #                             print ''
        #                         check_in_time = datetime.datetime.strptime(data.get('time'),
        #                                                                    "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
        #                         check_out_time = ''
        #
        #                 if check_in_time != '' and data.get('is_check_in') == False:
        #                     check_out_time = datetime.datetime.strptime(data.get('time'),
        #                                                                 "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
        #
        #                     if len(detail) == index_time:
        #                         check_in_time_1 = check_in_time.replace(hour=int(check_in_1.split(':')[0])).replace(
        #                             minute=int(check_in_1.split(':')[1]))
        #                         check_out_time_1 = check_in_time.replace(hour=int(check_out_1.split(':')[0])).replace(
        #                             minute=int(check_out_1.split(':')[1]))
        #                         check_in_time_2 = check_in_time.replace(hour=int(check_in_2.split(':')[0])).replace(
        #                             minute=int(check_in_2.split(':')[1]))
        #                         check_out_time_2 = check_in_time.replace(hour=int(check_out_2.split(':')[0])).replace(
        #                             minute=int(check_out_2.split(':')[1]))
        #                         # 上班记录在check_in_1之前取check_in_1
        #                         if check_in_time <= check_in_time_1:
        #                             check_in_time = check_in_time_1
        #                             if check_out_time >= check_out_time_1 and check_out_time < check_in_time_2:
        #                                 check_out_time = check_out_time_1
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time > check_in_time_1 and check_out_time < check_out_time_1:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time >= check_in_time_2 and check_out_time < check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time_1).seconds + (
        #                                     check_out_time - check_in_time_2).seconds
        #                             elif check_out_time >= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time_1).seconds + (
        #                                     check_out_time_2 - check_in_time_2).seconds
        #                         elif check_in_time > check_in_time_1 and check_in_time < check_out_time_1:
        #                             if check_out_time > check_in_time_1 and check_out_time <= check_out_time_1:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time > check_out_time_1 and check_out_time < check_in_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time).seconds
        #                             elif check_out_time >= check_in_time_2 and check_out_time < check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time).seconds + (
        #                                     check_out_time - check_in_time_2).seconds
        #                             elif check_out_time >= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_1 - check_in_time).seconds + (
        #                                     check_out_time_2 - check_in_time_2).seconds
        #                         elif check_in_time >= check_out_time_1 and check_in_time < check_in_time_2:
        #                             if check_out_time > check_in_time_2 and check_out_time < check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time_2).seconds
        #                             elif check_out_time >= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_2 - check_in_time_2).seconds
        #                         elif check_in_time > check_in_time_2 and check_in_time < check_out_time_2:
        #                             if check_out_time > check_in_time_2 and check_out_time <= check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time - check_in_time).seconds
        #                             elif check_out_time > check_out_time_2:
        #                                 work_seconds = work_seconds + (check_out_time_2 - check_in_time).seconds
        #                         elif check_in_time >= check_out_time_2:
        #                             print '加班'
        #                         check_in_time = ''
        #                         check_out_time = ''
        #
        #             print work_seconds
        #
        #
        #         start_now = start_now + timedelta(days=1)
            # print attendance_regular


            report_name = 'linkloving_hr_attendance.ll_hr_attendance_report'
            if not datas:
                raise UserError(u'没找到相关数据')

            return self.env['report'].get_action(self, report_name, datas)

            # def calcsTimes(self):
