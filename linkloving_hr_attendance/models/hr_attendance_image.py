# -*- coding: utf-8 -*-

from odoo import models, fields

class Linkloving_attendance_image(models.Model):
    _name = 'linkloving.hr.attendance.image'

    attendance_image = fields.Binary(u"上班考勤图片") #图片

    attendance_id = fields.Many2one("hr.attendance", ondelete='cascade')


class Linkloving_attendance_off_image(models.Model):
    _name = 'linkloving.hr.attendance.off.image'

#11

    attendance_image = fields.Binary(u"下班考勤图片")

    attendance_id = fields.Many2one("hr.attendance", ondelete='cascade')