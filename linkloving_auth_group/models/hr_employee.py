# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from itertools import chain, repeat
from collections import defaultdict, MutableMapping, OrderedDict

#
# Functions for manipulating boolean and selection pseudo-fields
#
from odoo.addons.base.res.res_users import parse_m2m
from odoo.tools import partition


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hr_jobs = fields.Many2many('hr.job')
