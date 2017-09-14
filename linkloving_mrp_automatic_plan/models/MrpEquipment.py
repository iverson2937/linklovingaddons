# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

WORK_TIME = 8 * 60 * 60
OFF_WORK_TIME = 16 * 60 * 60
WEEKEND_LIST = [6]  # 从0 - 6 周一到周天
REWORK_DEFAULT_TIME = 8 * 60 * 60

class Inheritforarrangeproduction(models.Model):
    _inherit = 'mrp.process'

    @api.multi
    def arrange_production(self):
        return {
            'name': self.name + u'排产',
            'type': 'ir.actions.client',
            'tag': 'arrange_production',
            'process_id': self.id
        }


ORDER_BY = "planned_start_backup,id desc"
class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrderExtend, self)._prepare_mo_vals(bom)

        produced_spend = res["product_qty"] * bom.produced_spend_per_pcs + bom.prepare_time
        planned_datetime = self._get_date_planned_from_date_planned()
        # date_planned_end = fields.Datetime.to_string(planned_datetime)
        new_datetime = datetime(planned_datetime.year,
                                planned_datetime.month,
                                planned_datetime.day,
                                planned_datetime.hour,
                                planned_datetime.minute,
                                planned_datetime.second,
                                microsecond=planned_datetime.microsecond,
                                tzinfo=pytz.timezone("UTC"))

        planned_time_with_zone = new_datetime.astimezone(pytz.timezone(self.env.user.tz))

        start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(planned_time_with_zone,
                                                                            produced_spend,
                                                                            self.env.user.tz)
        res.update({'state': 'draft',
                    # 'process_id': bom.process_id.id,
                    # 'unit_price': bom.process_id.unit_price,
                    # 'mo_type': bom.mo_type,
                    # 'hour_price': bom.hour_price,
                    # 'in_charge_id': bom.process_id.partner_id.id,
                    # 'product_qty': self.get_actual_require_qty(),
                    'date_planned_start': fields.Datetime.to_string(start_time),
                    'planned_start_backup': fields.Datetime.to_string(start_time),
                    'date_planned_finished': fields.Datetime.to_string(end_time)
                    })
        return res

    def _get_date_planned_from_date_planned(self):
        format_date_planned = fields.Datetime.from_string(self.date_planned)
        date_planned = format_date_planned - relativedelta(days=self.product_id.produce_delay or 0.0)
        date_planned = date_planned - relativedelta(days=self.company_id.manufacturing_lead)
        return date_planned

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
        current_day_start_time = fields.datetime.strptime(planned_date, '%Y-%m-%d')
        tz_name = self._context.get("tz") or self.env.user.tz
        context_tz = pytz.timezone(tz_name)
        start_time_utc = current_day_start_time - relativedelta(seconds=context_tz._utcoffset.seconds)
        end_time_utc = start_time_utc + relativedelta(days=1)
        start_time_str = fields.datetime.strftime(start_time_utc, DEFAULT_SERVER_DATETIME_FORMAT)
        end_time_str = fields.datetime.strftime(end_time_utc, DEFAULT_SERVER_DATETIME_FORMAT)
        # utc_timestamp = pytz.utc.localize(start_time_utc, is_dst=False)  # UTC = no DST
        # if tz_name:
        # try:
        # return utc_timestamp.astimezone(context_tz)

        mos = self.env["mrp.production"].search_read([("production_line_id", "=", production_line_id),
                                                      # ("date_planned_start", "<=", end_time_str),
                                                      # ("date_planned_finished", ">=", start_time_str),
                                                      ("state", "not in", ['done', 'cancel', 'waiting_post_inventory'])
                                                      ],
                                                     # limit=limit,
                                                     # offset=offset,
                                                     order=ORDER_BY,
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

    @api.multi
    def _compute_factory_setting_id(self):
        setting = self.env["hr.config.settings"].search([("is_available", "=", True)], limit=1)
        if setting:
            for mo in self:
                mo.factory_setting_id = setting.id

    factory_setting_id = fields.Many2one("hr.config.settings", compute="_compute_factory_setting_id")
    production_line_id = fields.Many2one("mrp.production.line", string=u"产线")

    planned_start_backup = fields.Datetime(string=u"最晚开始时间")

    def _compute_produced_spend(self):
        if self.feedback_on_rework:
            return self.factory_setting_id.rework_spent_time or REWORK_DEFAULT_TIME
        return self.product_qty * self.bom_id.produced_spend_per_pcs + self.bom_id.prepare_time
    #根据process_id 获取未排产mo
    def get_unplanned_mo(self, **kwargs):
        process_id = kwargs.get("process_id")

        limit = kwargs.get("limit")
        offset = kwargs.get("offset")
        domain = [("process_id", "=", process_id), ("production_line_id", "=", False), ("state", "in", ['draft', 'confirmed', 'waiting_material']),]

        mos = self.env["mrp.production"].search_read(
                domain,
                limit=limit,
                offset=offset,
                order=ORDER_BY,
                # fields=[]
                )
        length = self.env["mrp.production"].search_count(domain)
        return {
            'length': length,
            'result': mos,
        }

    def get_today_time(self):
        now_time = fields.datetime.now(pytz.timezone(self.env.user.tz))
        return now_time

    def replanned_mo(self, production_line_id, ):
        self.write({
            'production_line_id': production_line_id
        })
        if not production_line_id:
            if self.production_line_id:
                production_line = self.production_line_id.id
            else:  # 从未排产拖到未排产
                return

        # 取出这条产线所有的mo
        all_mos = self.env["mrp.production"].search([("production_line_id", "=", production_line_id)], order=ORDER_BY)

        # 如果此条产线暂时无任何mo,
        if not all_mos:
            start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(self.get_today_time(),
                                                                                  self._compute_produced_spend(),
                                                                                  start_or_end="start",
                                                                                  equipment_no=len(
                                                                                      production_line.equipment_ids))
            self.write({
                'state': 'waiting_material',
                'date_planned_start': start_time,
                'date_planned_finished': end_time,
            })
        else:
            planned_start_backup = fields.Datetime.from_string(all_mos[0].date_planned_start)
            new_datetime = datetime(planned_start_backup.year,
                                    planned_start_backup.month,
                                    planned_start_backup.day,
                                    planned_start_backup.hour,
                                    planned_start_backup.minute,
                                    planned_start_backup.second,
                                    microsecond=planned_start_backup.microsecond,
                                    tzinfo=pytz.timezone("UTC"))

            next_mo_start_time = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
            for mo in all_mos:
                start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(next_mo_start_time,
                                                                                      mo._compute_produced_spend(),
                                                                                      start_or_end="start",
                                                                                      equipment_no=len(
                                                                                          production_line.equipment_ids))
                mo.write({
                    'state': 'waiting_material',
                    'date_planned_start': start_time,
                    'date_planned_finished': end_time,
                })

                next_mo_start_time = end_time.astimezone(pytz.timezone(self.env.user.tz))
        return all_mos
    # 排产或者取消排产
    def settle_mo(self, **kwargs):
        production_line_id = kwargs.get("production_line_id")
        settle_date = kwargs.get("settle_date")
        if not production_line_id:
            if self.planned_start_backup:
                planned_start_backup = fields.Datetime.from_string(self.planned_start_backup)
                new_datetime = datetime(planned_start_backup.year,
                                        planned_start_backup.month,
                                        planned_start_backup.day,
                                        planned_start_backup.hour,
                                        planned_start_backup.minute,
                                        planned_start_backup.second,
                                        microsecond=planned_start_backup.microsecond,
                                        tzinfo=pytz.timezone("UTC"))

                planned_start_backup_with_zone = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
                start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(planned_start_backup_with_zone,
                                                                                      self._compute_produced_spend(),
                                                                                      start_or_end="start")
                self.write({
                    'date_planned_start': start_time,
                    'date_planned_finished': end_time,
                })
                if self.state in ["draft", "confirmed", "waiting_material"]:
                    self.state = 'draft'
                else:
                    raise UserError(u"该单据已经开始生产,不可从产线上移除")

        production_line = self.env["mrp.production.line"].browse(production_line_id)
        all_mos = self.replanned_mo(production_line)
        # vals = {
        #     'production_line_id': production_line_id,
        # }
        # if production_line_id:  # 排
        #     current_day_start_time = fields.datetime.strptime(settle_date, '%Y-%m-%d')
        #     # start_time_utc = current_day_start_time - relativedelta(seconds=context_tz._utcoffset.seconds)
        #     line = self.env["mrp.production.line"].browse(production_line_id)
        #     start_time_utc = self.env["ll.time.util"].localize_time(current_day_start_time)
        #     start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(start_time_utc,
        #                                                                           self._compute_produced_spend(),
        #                                                                           start_or_end="start",
        #                                                                           equipment_no=len(line.equipment_ids))
        #     vals.update({
        #         'state': 'waiting_material',
        #         'date_planned_start': start_time,
        #         'date_planned_finished': end_time,
        #     })
        # else:  # 取消排产
        #     if self.planned_start_backup:
        #         planned_start_backup = fields.Datetime.from_string(self.planned_start_backup)
        #         new_datetime = datetime(planned_start_backup.year,
        #                                 planned_start_backup.month,
        #                                 planned_start_backup.day,
        #                                 planned_start_backup.hour,
        #                                 planned_start_backup.minute,
        #                                 planned_start_backup.second,
        #                                 microsecond=planned_start_backup.microsecond,
        #                                 tzinfo=pytz.timezone("UTC"))
        #
        #         planned_start_backup_with_zone = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
        #         start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(planned_start_backup_with_zone,
        #                                                                               self._compute_produced_spend(),
        #                                                                               start_or_end="start")
        #         vals.update({
        #             'date_planned_start': start_time,
        #             'date_planned_finished': end_time,
        #         })
        #     vals.update({
        #         'state': 'draft',
        #     })
        #
        # self.write(vals)
        return all_mos.read()


class SaleOrderLineExtend(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        vals = super(SaleOrderLineExtend, self)._prepare_order_line_procurement(group_id)
        date_planned = datetime.strptime(self.order_id.validity_date, DEFAULT_SERVER_DATE_FORMAT) \
                       + timedelta(days=self.customer_lead or 0.0) - timedelta(
            days=self.order_id.company_id.security_lead)
        vals.update({
            'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        })
        return vals

class TimeUtil(models.Model):
    _name = 'll.time.util'

    def g_factory_setting_id(self):
        setting = self.env["hr.config.settings"].search([("is_available", "=", True)], limit=1)
        if setting:
            return setting
        else:
            setting = self.env["hr.config.settings"].create({})
            return setting

    def transfer_spent_time_with_equipment_no(self, a=None, b=None, equipment_no=1):
        if equipment_no == 0:
            equipment_no = 1
        if not a:
            return (b - relativedelta(seconds=0)).seconds * equipment_no
        if not b:
            return (a - relativedelta(seconds=0)).seconds * equipment_no
        return (a - b).seconds * equipment_no

    def compute_mo_start_time(self, end_time, spent_time, start_or_end="end", equipment_no=1):
        if equipment_no == 0:
            equipment_no = 1
        setting = self.g_factory_setting_id()
        # tz_offset = relativedelta(seconds=0)#pytz.timezone(timezone_name)._utcoffset
        end_time_with_zone = end_time  # + tz_offset)
        corrected_end_time = self.correct_work_time(end_time_with_zone, start_or_end, setting)
        work_start_time, off_work_time = self.get_date_begin_end_time(corrected_end_time,
                                                                      relativedelta(
                                                                          hours=setting.factory_work_start_time),
                                                                      relativedelta(
                                                                          hours=setting.factory_work_end_time))
        # day_start_time = fields.datetime.strptime(fields.datetime.strftime(corrected_end_time, '%Y-%m-%d'),
        #                                           '%Y-%m-%d')  # 今日的0点
        # work_start_time = day_start_time + relativedelta(seconds=setting.factory_work_start_time)
        # off_work_time = day_start_time + relativedelta(seconds=setting.factory_work_end_time)

        if start_or_end == 'end':
            theoretics_start_time = corrected_end_time - relativedelta(
                seconds=spent_time / equipment_no)  # 理论的时间- (不计算上下班时间,节假日的)
            why = self.is_time_in_spec_day_and_not_weekend(theoretics_start_time, work_start_time, off_work_time)
            if why == 'weekday':  # 这天能完成 不做操作
                real_start_time = theoretics_start_time

            else:  # 跨天了
                if why == 'offwork':  # 如果是因为休息日导致的调整天数 不能当做是安排的时间扣除
                    arrange_time = self.transfer_spent_time_with_equipment_no(corrected_end_time,
                                                                              work_start_time,
                                                                              equipment_no)  # 今天的结束时间 - 今天上班时间 = 今天所安排的时间
                else:
                    arrange_time = 0
                left_time = spent_time - arrange_time  # 剩余安排时间
                move_corrected_time = corrected_end_time
                while left_time > 0:
                    new_day_work_start_time, new_day_work_off_time = self.get_date_begin_end_time(
                        move_corrected_time - relativedelta(days=1),
                            relativedelta(seconds=setting.factory_work_start_time),
                            relativedelta(seconds=setting.factory_work_end_time))
                    move_corrected_time = new_day_work_off_time
                    # new_day_work_start_time = new_day_0_time + relativedelta(seconds=setting.factory_work_start_time)  # 这一天的上班时间
                    # new_day_off_work_time = new_day_0_time + relativedelta(seconds=setting.factory_work_end_time)#这一天的下班时间
                    theoretics_move_start_time = move_corrected_time - relativedelta(
                        seconds=left_time / equipment_no)  # 理论的时间
                    while_why = self.is_time_in_spec_day_and_not_weekend(theoretics_move_start_time,
                                                                         new_day_work_start_time,
                                                                         new_day_work_off_time)  # 此方法返回这时间是工作日还是休息日还是下班时间
                    if while_why == 'weekday':  # 这天能完成 不做操作
                        real_start_time = theoretics_move_start_time
                        left_time = 0
                    else:
                        if while_why == 'offwork':
                            spent_this_time = self.transfer_spent_time_with_equipment_no(move_corrected_time,
                                                                                         new_day_work_start_time,
                                                                                         equipment_no)
                            left_time -= spent_this_time
                            # if theoretics_move_start_time <= new_day_off_work_time and theoretics_move_start_time >= new_day_work_start_time:
            if not real_start_time:
                raise UserWarning(u"出错了")
            return pytz.UTC.normalize(real_start_time), pytz.UTC.normalize(corrected_end_time)
        else:
            theoretics_start_time = corrected_end_time + relativedelta(
                seconds=spent_time / equipment_no)  # 理论的时间+ (不计算上下班时间,节假日的)
            why = self.is_time_in_spec_day_and_not_weekend(theoretics_start_time, work_start_time, off_work_time)
            if why == 'weekday':  # 这天能完成 不做操作
                real_start_time = theoretics_start_time
            else:  # 跨天了
                if why == 'offwork':
                    arrange_time = self.transfer_spent_time_with_equipment_no(off_work_time,
                                                                              corrected_end_time,
                                                                              equipment_no)  # 设备数量 * 今天的结束时间 - 今天上班时间 = 今天所安排的时间
                else:
                    arrange_time = 0
                left_time = spent_time - arrange_time  # 剩余安排时间

                move_corrected_time = corrected_end_time
                while left_time > 0:
                    move_corrected_time = move_corrected_time + relativedelta(days=1)
                    new_day_work_start_time, new_day_work_off_time = self.get_date_begin_end_time(move_corrected_time,
                                                                                                  relativedelta(
                                                                                                          hours=setting.factory_work_start_time),
                                                                                                  relativedelta(
                                                                                                          hours=setting.factory_work_end_time))
                    move_corrected_time = new_day_work_start_time
                    theoretics_move_start_time = move_corrected_time + relativedelta(
                        seconds=left_time / equipment_no)  # 理论的时间
                    while_why = self.is_time_in_spec_day_and_not_weekend(theoretics_move_start_time,
                                                                         new_day_work_start_time,
                                                                         new_day_work_off_time)  # 此方法返回这时间是工作日还是休息日还是下班时间
                    if while_why == 'weekday':  # 这天能完成 不做操作
                        real_start_time = theoretics_move_start_time
                        left_time = 0
                    else:
                        if while_why == 'offwork':
                            left_time -= self.transfer_spent_time_with_equipment_no(new_day_work_off_time,
                                                                                    move_corrected_time,
                                                                                    equipment_no)

            if not real_start_time:
                raise UserWarning(u"出错了")
            return pytz.UTC.normalize(corrected_end_time), pytz.UTC.normalize(real_start_time)

    # @classmethod
    # def get_off_time_zone(cls):

    def localize_time(self, planned_time_no_zone):
        tz_name = self._context.get("tz") or self.env.user.tz
        context_tz = pytz.timezone(tz_name)
        return context_tz.localize(planned_time_no_zone)

    def get_date_begin_end_time(self, the_date, delta_start, delta_end):
        start_time = fields.datetime.strptime(
                fields.datetime.strftime(the_date, '%Y-%m-%d'), '%Y-%m-%d')  # 今日的开始时间
        start_time_zone = self.localize_time(start_time)
        return start_time_zone + delta_start, start_time_zone + delta_end

    # 判断planned_time 是否在所规定的时间内,并且不是休息日
    def is_time_in_spec_day_and_not_weekend(self, planned_time, time_on_work=None, time_off_work=None):
        dayOfWeek = time_on_work.weekday()
        if dayOfWeek in WEEKEND_LIST:  # 暂定周天为休息日
            return 'weekend'
        else:
            if time_on_work <= planned_time <= time_off_work:
                return 'weekday'
            else:
                return 'offwork'

    # 是否是工作时间
    def is_time_in_work_time(self, planned_time_with_zone, setting):
        # tz_offset = pytz.timezone(self.env.user.tz)._utcoffset
        # planned_time_with_zone = (planned_time + tz_offset)
        dayOfWeek = planned_time_with_zone.weekday()
        if dayOfWeek in WEEKEND_LIST:  # 暂定周天为休息日
            return False
        else:
            current_day_start_time = fields.datetime.strptime(
                    fields.datetime.strftime(planned_time_with_zone, '%Y-%m-%d'), '%Y-%m-%d')  # 今日的开始时间
            work_start_time, off_work_time = self.get_date_begin_end_time(current_day_start_time,
                                                                          relativedelta(
                                                                              hours=setting.factory_work_start_time),
                                                                          relativedelta(
                                                                              hours=setting.factory_work_end_time))
            if work_start_time <= planned_time_with_zone <= off_work_time:
                return True
            else:
                return False
                # if planned_time_with_zone < work_start_time or planned_time_with_zone > off_work_time:
                #     return False
                # else:
                #     return True

    # 如果当前时间不是工作时间 则调整到是工作时间以及调整的时间相差了多少,方便计算剩余工时,如果是则不做操作直接返回
    def correct_work_time(self, planned_time_with_zone, start_or_end, setting):
        is_work_time = self.is_time_in_work_time(planned_time_with_zone, setting)
        if is_work_time:
            return planned_time_with_zone
        else:
            current_day_start_time = fields.datetime.strptime(
                    fields.datetime.strftime(planned_time_with_zone, '%Y-%m-%d'), '%Y-%m-%d')  # 今日的开始时间
            current_day_start_time = self.localize_time(current_day_start_time)

            if start_or_end == "end":
                current_day_on_work_time, current_day_off_work_time = self.get_date_begin_end_time(
                    current_day_start_time,
                        relativedelta(hours=setting.factory_work_start_time),
                        relativedelta(hours=setting.factory_work_end_time))
                # current_day_off_work_time = current_day_start_time + relativedelta(seconds=setting.factory_work_end_time)
                if current_day_off_work_time <= planned_time_with_zone < current_day_start_time + relativedelta(days=1):
                    yesterday_off_work_time = current_day_off_work_time
                else:
                    current_day_on_work_time, current_day_off_work_time = self.get_date_begin_end_time(
                        current_day_start_time - relativedelta(days=1),
                            relativedelta(hours=setting.factory_work_start_time),
                            relativedelta(hours=setting.factory_work_end_time))
                    yesterday_off_work_time = current_day_off_work_time

                while not self.is_time_in_work_time(yesterday_off_work_time, setting):
                    # if self.is_time_in_work_time(yesterday_off_work_time):
                    #     return yesterday_off_work_time
                    # else:
                    current_day_on_work_time, current_day_off_work_time = self.get_date_begin_end_time(
                        yesterday_off_work_time - relativedelta(days=1),
                            relativedelta(hours=setting.factory_work_start_time),
                            relativedelta(hours=setting.factory_work_end_time))
                    yesterday_off_work_time = current_day_off_work_time

                return yesterday_off_work_time
            else:
                current_day_on_work_time, current_day_off_work_time = self.get_date_begin_end_time(
                    current_day_start_time,
                        relativedelta(hours=setting.factory_work_start_time),
                        relativedelta(hours=setting.factory_work_end_time))
                # current_day_on_work_time = current_day_start_time + relativedelta(seconds=setting.factory_work_start_time)
                if current_day_start_time <= planned_time_with_zone < current_day_on_work_time:
                    next_day_on_work_time = current_day_on_work_time
                else:
                    current_day_on_work_time, current_day_off_work_time = self.get_date_begin_end_time(
                        current_day_start_time + relativedelta(days=1),
                            relativedelta(hours=setting.factory_work_start_time),
                            relativedelta(hours=setting.factory_work_end_time))
                    next_day_on_work_time = current_day_on_work_time

                while not self.is_time_in_work_time(next_day_on_work_time, setting):
                    current_day_on_work_time, current_day_off_work_time = self.get_date_begin_end_time(
                        current_day_start_time + relativedelta(days=1),
                            relativedelta(hours=setting.factory_work_start_time),
                            relativedelta(hours=setting.factory_work_end_time))
                    next_day_on_work_time = current_day_on_work_time

                return next_day_on_work_time
