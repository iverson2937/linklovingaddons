# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class MrpProductionExtend(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def action_cancel(self):
        # for mo in self:
        #     if mo.product_tmpl_id.product_ll_type == 'finished' and mo.product_tmpl_id.order_ll_type == 'ordering':
        #         raise UserError(u"订单制产品的MO不能取消!")
        return super(MrpProductionExtend, self).action_cancel()
class MrpProductionCombine(models.TransientModel):
    """
    This wizard will combine the mrp production
    """

    _name = "mrp.production.combine"
    _description = "Confirm cancel the selected mo"

    @api.multi
    def action_combine(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        qty = 0
        product_id = []
        ids = []
        origin = ''
        for record in self.env['mrp.production'].browse(active_ids):
            if record.product_tmpl_id.product_ll_type == 'finished' and record.product_tmpl_id.order_ll_type == 'ordering':
                raise UserError(u"订单制产品的MO不能合并!")
            if record.state not in ['draft', 'confirmed', 'waiting_material']:
                raise UserError(_("Only draft MO can combine."))

            product_id.append(record.product_id)
            ids.append(record.id)
            qty += record.product_qty
            if origin:
                origin = origin + ', ' + record.origin
            else:
                origin = record.origin
            record.action_cancel()
        if len(set(product_id)) > 1:
            raise UserError(_('MO product must be same'))
        bom_id = product_id[0].bom_ids
        mo_id = self.env['mrp.production'].create({
            'product_qty': qty,
            'product_id': product_id[0].id,
            'bom_id': bom_id.id,
            'product_uom_id': product_id[0].uom_id.id,
            'state': 'draft',
            'origin': origin,

            'process_id': bom_id.process_id.id,
            'unit_price': bom_id.process_id.unit_price,
            'hour_price': bom_id.hour_price,
            'in_charge_id': bom_id.process_id.partner_id.id
        })
        mo_id.source_mo_ids = ids

        return {
            'name': mo_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'target': 'current',
            'res_id': mo_id.id,
        }