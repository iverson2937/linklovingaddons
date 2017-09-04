# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class HrConfigSettings(models.TransientModel):
    _name = 'hr.config.settings'
    _inherit = 'res.config.settings'

    factory_work_start_time = fields.Float(string=u"工厂上班时间", default=8, )

    factory_work_end_time = fields.Float(string=u"工厂下班时间", default=18.5)
