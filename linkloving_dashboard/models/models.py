# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Dashboard(models.TransientModel):
    _name = 'linkloving.dashboard'

    @api.model
    def get_dashboard_data(self):
        by_category = by_team = by_brand = []

        return {
            'by_category': by_category,
            'by_team': by_team,
            'by_brand': by_brand,

        }
