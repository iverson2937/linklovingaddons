# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
import uuid

from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def set_to_confirm(self):
        for m in self:
            if m.product_id.status == 'eol' or not m.product_id.active:
                raise UserError('%s已停产或者归档,不能生产' % m.product_id.name)

            m.state = 'confirmed'

    @api.multi
    def _compute_on_produce_qty(self):
        for stock_move in self:
            finished_product = sum(
                move.product_uom_qty for move in stock_move.move_finished_ids.filtered(lambda x: x.state == 'done'))
            stock_move.on_produce_qty = stock_move.product_qty - finished_product

    on_produce_qty = fields.Float(compute=_compute_on_produce_qty)

    @api.model
    def delete_mos(self, mo_ids):
        for mo_id in mo_ids:
            mo = self.browse(mo_id)
            if mo.state in ['draft', 'confirmed', 'waiting_material']:
                mo.action_cancel()
                mo.unlink()
            else:
                raise UserError('只有未生产的MO才可以删除')
        return True

    @api.multi
    def get_mail_message(self):
        for mo in self:
            return [
                {'name': 'allen', 'time': '2017-10-19', 'description': 'abc'}
            ]

    @api.multi
    def get_formview_id(self):
        """ Update form view id of action to open the invoice """
        if self._context.get('show_custom_form'):
            return self.env.ref('linkloving_mrp_automatic_plan.mrp_production_paichan_form_view').id
        return super(MrpProduction, self).get_formview_id()
