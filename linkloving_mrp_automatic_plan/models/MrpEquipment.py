# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrderExtend, self)._prepare_mo_vals(bom)

        produced_spend = res["product_qty"] * bom.produced_spend_per_pcs + bom.prepare_time

        res.update({'state': 'draft',
                    'process_id': bom.process_id.id,
                    'unit_price': bom.process_id.unit_price,
                    'mo_type': bom.mo_type,
                    'hour_price': bom.hour_price,
                    'in_charge_id': bom.process_id.partner_id.id,
                    'product_qty': self.get_actual_require_qty(),
                    'date_planned_start': fields.Datetime.to_string(self._get_date_planned_from_today()),
                    'date_planned_finished': fields.Datetime.from_string(self.date_planned) + relativedelta(
                        seconds=produced_spend)
                    })
        return res
# 设备
class MrpProcessEquipment(models.Model):
    _name = 'mrp.process.equipment'

    name = fields.Char(string=u"设备名称", required=True, )
    production_line_id = fields.Many2one(string=u'产线', comodel_name='mrp.production.line')
    process_id = fields.Many2one(string=u'工序', comodel_name='mrp.process', related='production_line_id.process_id')
    employee_id = fields.Many2one(comodel_name="hr.employee", string=u"产线负责人", related='production_line_id.employee_id')


# 工种
class WorkType(models.Model):
    _name = 'work.type'

    name = fields.Char(string=u"名称", required=True, )
    hourly_wage = fields.Float(string=u'时薪', required=True, )
    description = fields.Text(string=u'描述')


# 产线
class MrpProductionLine(models.Model):
    _name = 'mrp.production.line'

    @api.multi
    def _compute_euiqpment_names(self):
        for line in self:
            eq_names = ''
            for eq in line.equipment_ids:
                if eq_names != '':
                    eq_names += ', '
                eq_names = eq_names + eq.name
            line.euiqpment_names = eq_names

    @api.multi
    def _compute_line_employee_names(self):
        for line in self:
            eq_names = ''
            for em in line.line_employee_ids:
                if eq_names != '':
                    eq_names += ', '
                eq_names = eq_names + em.name
            line.line_employee_names = eq_names

    name = fields.Char(string=u"名称", required=True, )
    process_id = fields.Many2one(string=u'工序', comodel_name='mrp.process')
    equipment_ids = fields.One2many(string=u'设备', comodel_name='mrp.process.equipment',
                                    inverse_name='production_line_id')
    euiqpment_names = fields.Char(string=u'设备', compute='_compute_euiqpment_names')
    employee_id = fields.Many2one(comodel_name="hr.employee", string=u"产线负责人", required=False, )
    line_employee_ids = fields.One2many(comodel_name='hr.employee', inverse_name='production_line_id', string=u'产线人员')
    line_employee_names = fields.Char(string=u'产线人员', compute='_compute_line_employee_names')


class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    production_line_id = fields.Many2one(comodel_name='mrp.production.line', string=u'所属产线')


# 工序
class MrpProcessExtend(models.Model):
    _inherit = 'mrp.process'

    work_type_id = fields.Many2one(comodel_name="work.type", string=u"工种", required=False, )
    production_line_ids = fields.One2many(comodel_name='mrp.production.line', inverse_name='process_id', string=u'产线')
