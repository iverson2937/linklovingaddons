# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from odoo import fields,api,models


class Partner(models.Model):

    """"""

    _inherit = 'res.partner'

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    team_id = fields.Many2one('crm.team', default=_get_default_team)
    source_id=fields.Many2one('res.partner.source')
    level = fields.Selection([
        (1, '1级'),
        (2, '2级'),
        (3, '3级')
    ], string='客户等级')

class ResPartnerSource(models.Model):

    """
    渠道
    """

    _name = 'res.partner.source'

    name=fields.Char()
    description=fields.Text()

