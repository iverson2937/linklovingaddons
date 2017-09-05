# -*- coding: utf-8 -*-
import datetime
import pytz
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrderExtend, self)._prepare_mo_vals(bom)

        produced_spend = res["product_qty"] * bom.produced_spend_per_pcs + bom.prepare_time
        date_planned_end = fields.Datetime.to_string(self._get_date_planned_from_date_planned())
        start_time, end_time = self.compute_mo_start_time(self._get_date_planned_from_date_planned(), produced_spend)
        res.update({'state': 'draft',
                    # 'process_id': bom.process_id.id,
                    # 'unit_price': bom.process_id.unit_price,
                    # 'mo_type': bom.mo_type,
                    # 'hour_price': bom.hour_price,
                    # 'in_charge_id': bom.process_id.partner_id.id,
                    # 'product_qty': self.get_actual_require_qty(),
                    'date_planned_start': fields.Datetime.to_string(start_time),
                    'date_planned_finished': fields.Datetime.to_string(end_time)
                    })
        return res

    def _get_date_planned_from_date_planned(self):
        format_date_planned = fields.Datetime.from_string(self.date_planned)
        date_planned = format_date_planned - relativedelta(days=self.product_id.produce_delay or 0.0)
        date_planned = date_planned - relativedelta(days=self.company_id.manufacturing_lead)
        return date_planned

    def compute_mo_start_time(self, end_time, spent_time):
        tz_offset = pytz.timezone(self.env.user.tz)._utcoffset
        end_time_with_zone = (end_time + tz_offset)
        corrected_end_time = self.correct_work_time(end_time_with_zone)
        day_start_time = fields.datetime.strptime(fields.datetime.strftime(corrected_end_time, '%Y-%m-%d'),
                                                  '%Y-%m-%d')  # 今日的0点
        work_start_time = day_start_time + relativedelta(seconds=8 * 60 * 60)
        off_work_time = day_start_time + relativedelta(seconds=16 * 60 * 60)
        theoretics_start_time = corrected_end_time - relativedelta(seconds=spent_time)  # 理论的时间- (不计算上下班时间,节假日的)
        if theoretics_start_time <= off_work_time and theoretics_start_time >= work_start_time:  # 当天能完成 不做操作
            real_start_time = theoretics_start_time

        else:  # 跨天了
            arrange_time = corrected_end_time - work_start_time  # 今天的结束时间 - 今天上班时间 = 今天所安排的时间
            left_time = spent_time - arrange_time.seconds  # 剩余安排时间
            move_corrected_time = corrected_end_time
            while left_time > 0:
                move_corrected_time = move_corrected_time - relativedelta(days=1)
                new_day_0_time = fields.datetime.strptime(fields.datetime.strftime(move_corrected_time, '%Y-%m-%d'),
                                                          '%Y-%m-%d')  # 这一天的0点
                new_day_work_start_time = new_day_0_time + relativedelta(seconds=8 * 60 * 60)  # 这一天的上班时间
                # new_day_off_work_time = new_day_0_time + relativedelta(seconds=16 * 60 * 60)#这一天的下班时间
                theoretics_move_start_time = move_corrected_time - relativedelta(seconds=left_time)  # 理论的时间
                if self.is_time_in_work_time(theoretics_move_start_time):
                    real_start_time = theoretics_move_start_time
                    left_time = 0
                else:
                    left_time = left_time - (move_corrected_time - new_day_work_start_time).seconds
                    # if theoretics_move_start_time <= new_day_off_work_time and theoretics_move_start_time >= new_day_work_start_time:
        if not real_start_time:
            raise UserWarning(u"出错了")
        return real_start_time, corrected_end_time

    # 是否是工作时间
    def is_time_in_work_time(self, planned_time_with_zone):
        # tz_offset = pytz.timezone(self.env.user.tz)._utcoffset
        # planned_time_with_zone = (planned_time + tz_offset)
        dayOfWeek = planned_time_with_zone.weekday()
        if dayOfWeek == 6:  # 暂定周天为休息日
            return False
        else:
            current_day_start_time = fields.datetime.strptime(
                fields.datetime.strftime(planned_time_with_zone, '%Y-%m-%d'), '%Y-%m-%d')  # 今日的开始时间
            work_start_time = current_day_start_time + relativedelta(seconds=8 * 60 * 60)
            off_work_time = current_day_start_time + relativedelta(seconds=16 * 60 * 60)
            # current_day_end_time = current_day_start_time + relativedelta(days=1) - relativedelta(microseconds=1)  # 今日的结束时间
            # print(current_day_end_time)
            if planned_time_with_zone < work_start_time or planned_time_with_zone > off_work_time:
                return False
            else:
                return True

    # 如果当前时间不是工作时间 则调整到是工作时间以及调整的时间相差了多少,方便计算剩余工时,如果是则不做操作直接返回
    def correct_work_time(self, planned_time_with_zone):

        is_work_time = self.is_time_in_work_time(planned_time_with_zone)
        if is_work_time:
            return planned_time_with_zone
        else:
            current_day_start_time = fields.datetime.strptime(
                fields.datetime.strftime(planned_time_with_zone, '%Y-%m-%d'), '%Y-%m-%d')  # 今日的开始时间
            yesterday_off_work_time = current_day_start_time - relativedelta(days=1) + relativedelta(
                seconds=16 * 60 * 60)
            while not self.is_time_in_work_time(yesterday_off_work_time):
                # if self.is_time_in_work_time(yesterday_off_work_time):
                #     return yesterday_off_work_time
                # else:
                yesterday_off_work_time = yesterday_off_work_time - relativedelta(days=1) + relativedelta(
                    seconds=16 * 60 * 60)

            return yesterday_off_work_time


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

    # 根据process_id 获取产线
    def get_production_line_list(self, **kwargs):
        process_id = kwargs.get("process_id")

        lines = self.env["mrp.production.line"].search_read([("process_id", "=", process_id), ])
        return lines

    #根据产线id获取已排产mo
    def get_mo_by_productin_line(self, **kwargs):
        production_line_id = kwargs.get("production_line_id")
        planned_date = kwargs.get("planned_date")
        limit = kwargs.get("limit")
        offset = kwargs.get("offset")

        mos = self.env["mrp.production"].search_read([("production_line_id", "=", production_line_id)],
                                                     limit=limit,
                                                     offset=offset
                                                     )
        return mos

class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    production_line_id = fields.Many2one(comodel_name='mrp.production.line', string=u'所属产线')


# 工序
class MrpProcessExtend(models.Model):
    _inherit = 'mrp.process'

    work_type_id = fields.Many2one(comodel_name="work.type", string=u"工种", required=False, )
    production_line_ids = fields.One2many(comodel_name='mrp.production.line', inverse_name='process_id', string=u'产线')


class MrpProductionExtend(models.Model):
    _inherit = "mrp.production"

    production_line_id = fields.Many2one("mrp.production.line", string=u"产线")

    #根据process_id 获取未排产mo
    def get_unplanned_mo(self, **kwargs):
        process_id = kwargs.get("process_id")

        limit = kwargs.get("limit")
        offset = kwargs.get("offset")

        mos = self.env["mrp.production"].search_read(
                [("process_id", "=", process_id), ("production_line_id", "=", False)],
                limit=limit,
                offset=offset,
                )

        return mos

    # 排产或者取消排产
    def settle_mo(self, **kwargs):
        production_line_id = kwargs.get("production_line_id")
        settle_date = kwargs.get("settle_date")

        self.production_line_id = production_line_id

        return True
