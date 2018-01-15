# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    process_id = fields.Many2one('mrp.process', string=u'工序')
    unit_price = fields.Float(string=u'计件单价')

    mo_type = fields.Selection([
        ('unit', u'Base on Unit'),
        ('time', u'Base on Time'),
    ], default='unit')
    cycle_time = fields.Integer(string=u'Cycle Time')
    cycle_time_time_unit = fields.Many2one('product.uom')
    produced_spend_per_pcs = fields.Integer(string=u'生产速度 (秒/个)', default=0, required=True)
    prepare_time = fields.Integer(string=u"准备时间(秒)", default=0, required=True)

    @api.depends('cost', 'hour_price')
    def _get_product_cost(self):
        for bom in self:
            bom.cost = (float(bom.cycle_time) / 3600) * bom.hour_price

    cost = fields.Monetary(string=u'Cost', compute=_get_product_cost, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    hour_price = fields.Float(string=u'时薪', default=30)

    @api.constrains('prepare_time')
    def _check_cycle_spend_prepare(self):
        # if self.produced_spend_per_pcs <= 0:
        #     raise ValidationError(u"生产速度 无效")
        if self.prepare_time <= 0:
            raise ValidationError(u"准备时间 无效")

    @api.onchange('process_id')
    def on_change_price(self):
        self.hour_price = self.process_id.hour_price

    @api.multi
    def bom_structure_view(self):
        return {'name': u'物料清单结构',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree',
                'view_type': 'tree',
                'view_id': self.env.ref('mrp.mrp_bom_line_tree_view').id,
                'res_id': self.id,
                'domain': [('bom_id', '=', self.id)],
                'res_model': 'mrp.bom.line',
                'target': 'new',
                }

    class MrpBomLine(models.Model):
        _inherit = 'mrp.bom.line'

        def get_process_id(self):
            for line in self:
                bom_id = line.product_id.product_tmpl_id.bom_ids[0] if line.product_id.product_tmpl_id.bom_ids else None
                line.process_id = bom_id.process_id.id if bom_id else None

        process_id = fields.Many2one('mrp.process', compute=get_process_id)
