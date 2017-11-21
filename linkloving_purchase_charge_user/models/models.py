# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    po_user_id = fields.Many2one(comodel_name="res.users", string=u"采购负责人", required=False,
                                 default=lambda self: self.env.user.id)


class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    # @api.multi
    # def _compute_user_id(self):
    #     for order in self:
    #         if order.partner_id.po_user_id:
    #             order.user_id = order.partner_id.po_user_id.id
    #         else:
    #             order.user_id = order.create_uid.id
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id.po_user_id:
            self.user_id = self.partner_id.po_user_id.id
        else:
            self.user_id = self.env.user.id

    user_id = fields.Many2one(comodel_name="res.users", string=u"负责人", required=False,
                              default=lambda self: self.env.user.id, )
