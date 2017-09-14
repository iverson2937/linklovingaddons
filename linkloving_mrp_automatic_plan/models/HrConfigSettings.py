# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class HrConfigSettings(models.Model):
    _name = 'hr.config.settings'

    is_available = fields.Boolean(string=u"是否启用", default=False)
    factory_work_start_time = fields.Float(string=u"工厂上班时间", default=8, )

    factory_work_end_time = fields.Float(string=u"工厂下班时间", default=18.5)

    rework_spent_time = fields.Float(string=u"返工默认花费时间", default=8)

    @api.model
    def create(self, vals):
        if vals.get("is_available"):
            settings = self.env["hr.config.settings"].search([])
            settings.write({
                'is_available': False
            })
        return super(HrConfigSettings, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("is_available"):
            settings = self.env["hr.config.settings"].search([])
            settings.write({
                'is_available': False
            })
        return super(HrConfigSettings, self).write(vals)
