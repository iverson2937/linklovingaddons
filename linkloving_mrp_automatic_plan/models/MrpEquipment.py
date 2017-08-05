# -*- coding: utf-8 -*-
from odoo import models, fields, api


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
    prepare_time = fields.Integer(string=u"准备时间(秒)", default=0, )
    production_line_ids = fields.One2many(comodel_name='mrp.production.line', inverse_name='process_id', string=u'产线')
