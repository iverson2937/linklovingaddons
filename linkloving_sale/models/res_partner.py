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

    customer = fields.Boolean(string='Is a Customer', default=False,
                              help="Check this box if this contact is a customer.")

    team_id = fields.Many2one('crm.team')

    def _get_default_user_id(self):
        if self._context.get('default_customer'):
            return self.env.user.id

    user_id = fields.Many2one('res.users', default=_get_default_user_id)

    level = fields.Selection([
        (1, u'lst'),
        (2, u'2nd'),
        (3, u'3rd')
    ], string=u'Customer Level', default=1)

    internal_code = fields.Char(string=u'编号', copy=False)
    x_qq = fields.Char(string=u'Instant Messaging')

    _sql_constraints = [
        ('internal_code_uniq', 'unique (internal_code)', 'The No must be unique!')
    ]

    # @api.onchange('priority')
    # def _priority_default(self):
    #     for partner_data in self:
    #         data = self.env['crm.lead'].search([('partner_id', '=', partner_data.id)])
    #         if data:
    #             data.write({'priority': partner_data.priority})

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if not res.internal_code and res.customer and res.team_id:
            code = res.team_id.code if res.team_id.code else ''
            internal_code = code + self.env['ir.sequence'].next_by_code('res.partner.customer') or '/'
            res.internal_code = internal_code
        return res

    @api.multi
    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s,%s" % (
                        partner.commercial_company_name or partner.parent_id.name, name, partner.street or '')
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res


class ResPartnerSource(models.Model):
    """
    渠道
    """

    _name = 'res.partner.source'

    name = fields.Char(required=True)
    description = fields.Text()
