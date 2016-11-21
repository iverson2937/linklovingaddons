# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from odoo import fields, api, models


class Partner(models.Model):
    """"""

    _inherit = 'res.partner'

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    team_id = fields.Many2one('crm.team', default=_get_default_team)
    source_id = fields.Many2one('res.partner.source')
    level = fields.Selection([
        (1, u'1级'),
        (2, u'2级'),
        (3, u'3级')
    ], string=u'客户等级', default=1)
    internal_code = fields.Char(string='No')
    x_qq = fields.Char(string=u'即时通信')

    _sql_constraints = [
        ('internal_code_uniq', 'unique (internal_code)', 'The No must be unique!')
    ]


class ResPartnerSource(models.Model):
    """
    渠道
    """

    _name = 'res.partner.source'

    name = fields.Char()
    description = fields.Text()
