# -*- coding: utf-8 -*-
import math

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductMultiOutput(models.TransientModel):
    _name = 'product.multi.output'
