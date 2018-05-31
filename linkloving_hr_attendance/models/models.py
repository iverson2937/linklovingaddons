# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions

class Linkloving_hr_attendance(models.Model):
     _inherit = 'hr.attendance'
     company_name = fields.Char(string="上班打卡所在地")
     company_off_name = fields.Char(string="下班打卡所在地")

     open_id = fields.Char(string="员工微信唯一标识")
     new_check_in = fields.Datetime(string="Check In")

     device_version = fields.Char(string="设备型号")

     attendance_on_ids = fields.One2many(comodel_name="linkloving.hr.attendance.image",
                                   inverse_name="attendance_id",
                                   string="上班补考勤图片",
                                   required=False,)

     attendance_off_ids = fields.One2many(comodel_name="linkloving.hr.attendance.off.image",
                                         inverse_name="attendance_id",
                                         string="下班补考勤图片",
                                         required=False, )

     is_location_on = fields.Boolean(string='上班是否是定位打卡', default=False)
     is_location_off = fields.Boolean(string='下班是否是定位打卡', default=False)

     rt_is_on = fields.Selection([
         ('0', u'上班'),
         ('1', u'下班'),
     ], string=u"上下班类型")

     rt_type = fields.Selection([
         ('0', u'初始数据'),
         ('1', u'补卡'),
         ('2', u'销卡'),
         ('3', u'审核补卡'),
         ('4', u'审核销卡')
     ], default='0', string=u"打卡类型")

     @api.depends('check_out','new_check_in')
     def _get_is_on(self):
         for attendance in self:
             if attendance.check_out:
                 attendance.rt_is_on = "1"
             else:
                 attendance.rt_is_on = "0"

     @api.constrains('check_in', 'check_out', 'employee_id')
     def _check_validity(self):
          """ Verifies the validity of the attendance record compared to the others from the same employee.
              For the same employee we must have :
                  * maximum 1 "open" attendance record (without check_out)
                  * no overlapping time slices with previous employee records
          """
          # for attendance in self:
          #      # we take the latest attendance before our check_in time and check it doesn't overlap with ours
          #      last_attendance_before_check_in = self.env['hr.attendance'].search([
          #           ('employee_id', '=', attendance.employee_id.id),
          #           ('check_in', '<=', attendance.check_in),
          #           ('id', '!=', attendance.id),
          #      ], order='check_in desc', limit=1)
          #      if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out >= attendance.check_in:
          #           raise exceptions.ValidationError(_(
          #                "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
          #                                                 'empl_name': attendance.employee_id.name_related,
          #                                                 'datetime': fields.Datetime.to_string(
          #                                                      fields.Datetime.context_timestamp(self,
          #                                                                                        fields.Datetime.from_string(
          #                                                                                             attendance.check_in))),
          #                                            })
          #
          #      if not attendance.check_out:
          #           # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
          #           no_check_out_attendances = self.env['hr.attendance'].search([
          #                ('employee_id', '=', attendance.employee_id.id),
          #                ('check_out', '=', False),
          #                ('id', '!=', attendance.id),
          #           ])
          #           if no_check_out_attendances:
          #                raise exceptions.ValidationError(_(
          #                     "Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
          #                                                      'empl_name': attendance.employee_id.name_related,
          #                                                      'datetime': fields.Datetime.to_string(
          #                                                           fields.Datetime.context_timestamp(self,
          #                                                                                             fields.Datetime.from_string(
          #                                                                                                  no_check_out_attendances.check_in))),
          #                                                 })
          #      else:
          #           # we verify that the latest attendance with check_in time before our check_out time
          #           # is the same as the one before our check_in time computed before, otherwise it overlaps
          #           last_attendance_before_check_out = self.env['hr.attendance'].search([
          #                ('employee_id', '=', attendance.employee_id.id),
          #                ('check_in', '<=', attendance.check_out),
          #                ('id', '!=', attendance.id),
          #           ], order='check_in desc', limit=1)
          #           if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
          #                raise exceptions.ValidationError(_(
          #                     "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
          #                                                      'empl_name': attendance.employee_id.name_related,
          #                                                      'datetime': fields.Datetime.to_string(
          #                                                           fields.Datetime.context_timestamp(self,
          #                                                                                             fields.Datetime.from_string(
          #                                                                                                  last_attendance_before_check_out.check_in))),
          #                                                 })

     @api.constrains('check_in', 'check_out')
     def _check_validity_check_in_check_out(self):
               """ verifies if check_in is earlier than check_out. """
              # for attendance in self:
                 #   if attendance.check_in and attendance.check_out:
                   #      if attendance.check_out < attendance.check_in:
                     #         raise exceptions.ValidationError(
                   #                _('"Check Out" time cannot be earlier than "Check In" time.'))

     # name = fields.Char()
     # value = fields.Integer()
     # value2 = fields.Float(compute="_value_pc", store=True)
     # description = fields.Text()

     # @api.depends('value')
     # def _value_pc(self):
     #     self.value2 = float(self.value) / 100

     @api.multi
     def print_report(self):
         print self

class Linkloving_ble_device(models.Model):
     _name = 'linkloving.ble.device'

     device_name = fields.Char(string="考勤机设备id")

     company_name = fields.Char(string="考勤机所在公司名")

class HrEmployee(models.Model):
     _inherit = 'hr.employee'
     wx_open_id = fields.Char(string="员工微信唯一标识")
     _sql_constraints = [
          ('wx_open_id', 'unique(wx_open_id)',
           '微信open id必须唯一'),
     ]
