# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

WORK_TIME = 8 * 60 * 60
OFF_WORK_TIME = 16 * 60 * 60
WEEKEND_LIST = [6]  # 从0 - 6 周一到周天
REWORK_DEFAULT_TIME = 8 * 60 * 60

DONE_CANCEL_DOMAIN = ["done", "cancel"]


class ChangeProductionQtyExtend(models.TransientModel):
    _name = 'change.production.qty.dialog'

    # TDE FIXME: add production_id field
    mo_id = fields.Many2one('mrp.production', u'制造单', required=True, readonly=True)
    product_qty = fields.Float(
            u'生产数量',
            digits=dp.get_precision('Product Unit of Measure'), required=True)

    @api.model
    def create(self, vals):
        res = super(ChangeProductionQtyExtend, self).create(vals)
        if res.mo_id.state in ["confirmed", "draft"]:
            qty_wizard = self.env['change.production.qty'].create({
                'mo_id': res.mo_id.id,
                'product_qty': vals.get("product_qty")
            })
            qty_wizard.with_context({}).change_prod_qty()
        return res

class PlanMoWizard(models.TransientModel):
    _name = 'plan.mo.wizard'

    production_id = fields.Many2one(comodel_name="mrp.production", string=u"生产单", required=False, )
    process_id = fields.Many2one(comodel_name="mrp.process", string=u"工序", required=False, )
    production_line_id = fields.Many2one(comodel_name="mrp.production.line", string=u'产线', required=True)
    in_charge_id = fields.Many2one(comodel_name="res.partner", string=u'工序负责人')
    product_qty = fields.Float(string=u"生产数量")

    is_priority = fields.Boolean(string=u'是否优先', default=False)
    planned_start_backup = fields.Datetime(string=u'最晚开始时间', )
    @api.onchange('process_id')
    def onchange_process_id(self):
        if self.production_line_id not in self.process_id.production_line_ids:
            self.production_line_id = False

    @api.model
    def create(self, vals):
        mo = self.env["mrp.production"].browse(self._context.get("production_id"))
        is_priority = vals.get("is_priority")
        mo_vals = vals.copy()
        mo_vals.update({
            'state': 'waiting_material'
        })
        if mo.state in ["draft", "confirmed"]:
            mo.write(mo_vals)
            qty_wizard = self.env['change.production.qty'].create({
                'mo_id': mo.id,
                'product_qty': vals.get("product_qty")
            })
            # context = dict(self._context)
            # context.pop("default_product_qty")
            qty_wizard.with_context({}).change_prod_qty()
            mo.replanned_mo(self.env["mrp.production.line"], mo.production_line_id, is_priority=is_priority)

        else:
            raise UserError(u"该状态无法排产")

        return super(PlanMoWizard, self).create(vals)

    def print_report(self):
        return True

class Inheritforarrangeproduction(models.Model):
    _inherit = 'mrp.process'

    production_line_ids = fields.One2many(comodel_name="mrp.production.line", inverse_name="process_id", string=u'产线')
    work_type_id = fields.Many2one("work.type", string=u'工种')
    hourly_wage = fields.Float(related="work_type_id.hourly_wage", string=u'时薪', readonly=True)

    @api.multi
    def arrange_production(self):
        return {
            'name': self.name + u'排产',
            'type': 'ir.actions.client',
            'tag': 'arrange_production',
            'process_id': self.id
        }

        # produce_speed_factor = fields.Selection([('human', u'人数'), ('equipment', u'设备数'), ],
        #                                         default='equipment', string=u'生产速度因子', )
        #
        # theory_factor = fields.Integer(string=u'理论 人数/设备数', require=True)

    def get_process_info(self):
        info = self.read(fields=["name", 'partner_id'])[0]
        total_equipment = 0
        total_time = 0
        total_ava_time = 0
        for line in self.production_line_ids:
            total_equipment += len(line.equipment_ids)
            total_time += line.total_time
            total_ava_time += line.total_ava_time
        info.update({
            'total_equipment': total_equipment,
            'total_time': round(total_time, 2),
            'total_ava_time': round(total_ava_time, 2),
        })
        return info

ORDER_BY = "planned_start_backup,id desc"
FIELDS = ["name", "alia_name", "product_tmpl_id", "state", "product_qty",
          "display_name", "bom_id", "feedback_on_rework", "qty_unpost",
          "planned_start_backup", "date_planned_start", "date_planned_finished",
          'theo_spent_time', 'availability', 'product_order_type', 'production_line_id',
          'produce_speed_factor', 'theory_factor', 'real_theo_spent_time', 'ava_spent_time',
          'prepare_material_state', 'material_state', 'last_mo_time', 'total_time', 'total_ava_time',
          'sale_order_handle_date']

class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrderExtend, self)._prepare_mo_vals(bom)

        produced_spend = res["product_qty"] * bom.produced_speed_per_sec_new + bom.prepare_time
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
                                                                              equipment_no=self.env[
                                                                                  "mrp.production.line"].compute_speed_factor(
                                                                                  bom))
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
    _order = 'sequence,name asc'

    def compute_speed_factor(self, bom):
        if len(self) == 0:
            # 无产线 去获取理论数量
            return bom.theory_factor or 1
        else:
            if bom.produce_speed_factor == 'human':  # 人为因素
                return bom.theory_factor or 1
            else:
                return len(self.equipment_ids) or 1

    @api.onchange('process_id')
    def onchange_process_id(self):
        if self.process_id:
            res = self.env["hr.employee"].search([("address_home_id", "=", self.process_id.partner_id.id)])
            self.employee_id = res.id
    @api.multi
    def _compute_amount_of_planned_mo(self):
        for line in self:
            count = self.env["mrp.production"].search_count([("production_line_id", "=", line.id),
                                                             # ("date_planned_start", "<=", end_time_str),
                                                             # ("date_planned_finished", ">=", start_time_str),
                                                             ("state", "not in",
                                                              DONE_CANCEL_DOMAIN)
                                                             ], )
            line.amount_of_planned_mo = count

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

    @api.multi
    def _compute_last_mo_time(self):
        domain = [("state", "not in", DONE_CANCEL_DOMAIN)]
        for line in self:
            new_domain = domain + [("production_line_id", "=", line.id)]
            last_mo = self.env["mrp.production"].search(new_domain,
                                                        order="date_planned_finished desc",
                                                        limit=1)
            line.last_mo_time = last_mo.date_planned_finished

    @api.multi
    def _compute_total_time(self):
        domain = [("state", "not in", DONE_CANCEL_DOMAIN)]
        for line in self:
            new_domain = domain + [("production_line_id", "=", line.id)]
            mos = self.env["mrp.production"].search(new_domain)
            line.total_time = round(sum(mos.mapped("real_theo_spent_time")), 2)

    @api.multi
    def _compute_total_ava_time(self):
        domain = [("state", "not in", DONE_CANCEL_DOMAIN)]
        for line in self:
            new_domain = domain + [("production_line_id", "=", line.id)]
            mos = self.env["mrp.production"].search(new_domain)
            line.total_ava_time = round(sum(mos.mapped("ava_spent_time")), 2)

    name = fields.Char(string=u"名称", required=True, )
    process_id = fields.Many2one(string=u'工序', comodel_name='mrp.process')
    equipment_ids = fields.One2many(string=u'设备', comodel_name='mrp.process.equipment',
                                    inverse_name='production_line_id')
    euiqpment_names = fields.Char(string=u'设备', compute='_compute_euiqpment_names')
    employee_id = fields.Many2one(comodel_name="hr.employee", string=u"产线负责人", required=False, )

    line_employee_ids = fields.One2many(comodel_name='hr.employee', inverse_name='production_line_id', string=u'产线人员')
    line_employee_names = fields.Char(string=u'产线人员', compute='_compute_line_employee_names')
    amount_of_planned_mo = fields.Float(string=u'生产总数', compute="_compute_amount_of_planned_mo")
    sequence = fields.Integer(string=u'显示顺序序号', default=30, help=u"越小排序越前")
    last_mo_time = fields.Datetime(compute="_compute_last_mo_time")
    total_time = fields.Float(compute='_compute_total_time')
    total_ava_time = fields.Float(compute='_compute_total_ava_time')

    # 根据process_id 获取产线
    def get_production_line_list(self, **kwargs):
        process_id = kwargs.get("process_id")

        lines = self.env["mrp.production.line"].search_read([("process_id", "=", process_id), ])
        count = self.env["mrp.production"].search_count([("process_id", "=", process_id),
                                                         ("production_line_id", "=", False),
                                                         ("state", "not in",
                                                          DONE_CANCEL_DOMAIN + ["draft", "confirmed"])])
        lines.append({
            'id': -1,
            'name': u'未分组',
            'amount_of_planned_mo': count,
            'equipment_ids': [],
            'line_employee_ids': [],
            'employee_id': [],
            'total_ava_time': 0,
            'total_time': 0,
        })
        return lines

    def get_process_info(self, **kwargs):
        process_id = kwargs.get("process_id")
        process = self.env["mrp.process"].browse(process_id)
        info = process.get_process_info()
        return info

    def get_recent_available_planned_time(self):
        domain = [("state", "in", ['draft', 'confirmed', 'waiting_material'])]
        new_domain = domain + [("production_line_id", "=", self.id)]
        mos = self.env["mrp.production"].search(new_domain,
                                                order=ORDER_BY)
        if mos:
            return mos[0]
        else:
            return mos
    #根据产线id获取已排产mo
    def get_mo_by_productin_line(self, **kwargs):
        production_line_id = kwargs.get("production_line_id")
        process_id = kwargs.get("process_id")
        domains = kwargs.get("domains", [])
        order_by_material = kwargs.get("order_by_material", False)
        # planned_date = kwargs.get("planned_date")

        # current_day_start_time = fields.datetime.strptime(planned_date, '%Y-%m-%d')
        tz_name = self._context.get("tz") or self.env.user.tz
        context_tz = pytz.timezone(tz_name)
        # start_time_utc = current_day_start_time - relativedelta(seconds=context_tz._utcoffset.seconds)
        # end_time_utc = start_time_utc + relativedelta(days=1)
        # start_time_str = fields.datetime.strftime(start_time_utc, DEFAULT_SERVER_DATETIME_FORMAT)
        # end_time_str = fields.datetime.strftime(end_time_utc, DEFAULT_SERVER_DATETIME_FORMAT)
        # utc_timestamp = pytz.utc.localize(start_time_utc, is_dst=False)  # UTC = no DST
        # if tz_name:
        # try:
        # return utc_timestamp.astimezone(context_tz)
        if production_line_id == -1:
            production_line_id = False
            limit = kwargs.get("limit")
            offset = kwargs.get("offset")
            mos = self.env["mrp.production"].search_read(
                    domain=expression.AND([[("production_line_id", "=", production_line_id),
                                            # ("date_planned_start", "<=", end_time_str),
                                            # ("date_planned_finished", ">=", start_time_str),
                                            ("state", "not in", DONE_CANCEL_DOMAIN + ['draft', 'confirmed']),
                                            ("process_id", "=", process_id)
                                            ], domains]),
                    limit=limit,
                    offset=offset,
                    order=ORDER_BY,
                    fields=FIELDS
            )
        else:
            mos = self.env["mrp.production"].search_read(
                    domain=expression.AND([[("production_line_id", "=", production_line_id),
                                            # ("date_planned_start", "<=", end_time_str),
                                            # ("date_planned_finished", ">=", start_time_str),
                                            ("state", "not in", DONE_CANCEL_DOMAIN),
                                            ("process_id", "=", process_id)
                                            ], domains]),
                order=ORDER_BY,
                    fields=FIELDS
            )
        return self.env["mrp.production"].sorted_mos_by_material(mos, order_by_material)

class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    production_line_id = fields.Many2one(comodel_name='mrp.production.line', string=u'所属产线')


# 工序
class MrpProcessExtend(models.Model):
    _inherit = 'mrp.process'

    work_type_id = fields.Many2one(comodel_name="work.type", string=u"工种", required=False, )
    production_line_ids = fields.One2many(comodel_name='mrp.production.line', inverse_name='process_id', string=u'产线')


class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    produce_speed_factor = fields.Selection([('human', u'人数'), ('equipment', u'设备数'), ],
                                            default='equipment', string=u'生产速度因子', )

    theory_factor = fields.Integer(string=u'理论 人数/设备数', require=True)

    amount_of_producer = fields.Integer(string=u'产能')
    produced_speed_per_hour = fields.Float(string=u'个/每小时')
    produced_speed_per_sec_new = fields.Float(compute='_compute_produced_speed_per_sec_new')

    piecework_unit_price = fields.Float(string=u'计件单价(元/个)')
    produced_cost = fields.Float(string=u'生产成本',
                                 compute='_compute_produced_cost',
                                 digits=dp.get_precision('Product Unit of Measure'))

    @api.multi
    def _compute_produced_cost(self):
        for bom in self:
            bom.produced_cost = bom.produced_speed_per_sec_new * bom.process_id.hourly_wage / 3600

    @api.multi
    def _compute_produced_speed_per_sec_new(self):
        for bom in self:
            if bom.produced_speed_per_hour != 0:
                bom.produced_speed_per_sec_new = bom.amount_of_producer * 3600 / bom.produced_speed_per_hour
            else:
                bom.produced_speed_per_sec_new = 0

    @api.onchange("amount_of_producer", "produced_speed_per_hour")
    def _onchange_produced_speed_per_sec_new(self):
        if self.produced_speed_per_hour != 0:
            self.produced_speed_per_sec_new = self.amount_of_producer * 3600 / self.produced_speed_per_hour
        else:
            self.produced_speed_per_sec_new = 0


class MrpProductionExtend(models.Model):
    _inherit = "mrp.production"

    # @api.multi
    # def write(self, vals):
    #     for mo in self:
    #         if vals.get("")

    def get_change_prod_qty_formview(self):
        view_id = self.env.ref('mrp.view_change_production_qty_wizard').id
        return {
            'title': u'打开',
            'res_model': 'change.production.qty.dialog',
            # 'view_id': view_id,
            'disable_multiple_selection': True,
        }

    def get_formview(self):
        view_id = self.env.ref('linkloving_mrp_automatic_plan.form_plan_mo_wizard').id
        return {
            'title': u'打开',
            'res_model': 'plan.mo.wizard',
            'view_id': view_id,
            'disable_multiple_selection': True,
            'readonly': True,
            # 'res_id': self.id,
        }
    def show_paichan_form_view(self):
        print(123123123123)
        view_id = self.env.ref('linkloving_mrp_automatic_plan.mrp_production_paichan_form_view').id
        return view_id
        # return {
        #         'name': u"排产",
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'mrp.production',
        #         'view_id': view_id,
        #         'views': [(view_id, 'form')],
        #         'type': 'ir.actions.act_window',
        #         'res_id': self.id,
        #         'target': 'new'
        #     }

    @api.multi
    def action_cancel_plan(self):
        if all(mo.state == 'waiting_material' for mo in self):
            self.write({
                'production_line_id': False,
                'state': 'confirmed',
            })
        else:
            raise UserError(u"该状态无法取消排产")
    @api.multi
    def _compute_factory_setting_id(self):
        setting = self.env["hr.config.settings"].search([("is_available", "=", True)], limit=1)
        if setting:
            for mo in self:
                mo.factory_setting_id = setting.id

    @api.multi
    def _compute_product_order_type(self):
        for mo in self:
            mo.product_order_type = mo.product_id.order_ll_type

    @api.multi
    def _compute_theo_spent_time(self):
        for mo in self:
            mo.theo_spent_time = round(
                    (
                        mo.product_qty * mo.bom_id.produced_speed_per_sec_new + mo.bom_id.prepare_time * mo.production_line_id.compute_speed_factor(
                        mo.bom_id)) / 3600, 2)

    @api.multi
    def _compute_real_theo_spent_time(self):
        for mo in self:
            mo.real_theo_spent_time = round(
                    (mo.product_qty * mo.bom_id.produced_speed_per_sec_new + mo.bom_id.prepare_time) / 3600, 2)

    @api.multi
    def _compute_ava_spent_time(self):
        for mo in self:
            mo.ava_spent_time = round(mo.theo_spent_time / mo.production_line_id.compute_speed_factor(mo.bom_id), 2)

    @api.multi
    def _compute_prepare_material_state(self):
        for mo in self:
            rate_list = []
            mo.sim_stock_move_lines._default_product_uom_qty()  # 解决 搜索时的结果与现实列表时的结果不一样的问题
            for move in mo.sim_stock_move_lines:
                if move.product_uom_qty == 0:
                    rate_list.append(0)
                    continue
                rate = move.quantity_done * 1.0 / move.product_uom_qty
                rate_list.append(rate)
            if any(rate < 0.5 for rate in rate_list):
                mo.prepare_material_state = 'red'
            elif all(rate >= 1.0 for rate in rate_list):
                mo.prepare_material_state = 'green'
            else:
                mo.prepare_material_state = 'yellow'

    @api.multi
    def _compute_material_state(self):
        for mo in self:
            rate_list = []
            mo.sim_stock_move_lines._default_product_uom_qty()  #解决 搜索时的结果与现实列表时的结果不一样的问题
            for move in mo.sim_stock_move_lines:
                if move.product_uom_qty == 0:
                    rate_list.append(0)
                    continue
                rate = (move.quantity_done + move.product_id.qty_available if move.product_id.qty_available > 0 else 0) \
                       / move.product_uom_qty

                # rate = move.product_id.qty_available * 1.0 / move.product_uom_qty
                rate_list.append(rate)
            if any(rate < 0.5 for rate in rate_list):
                mo.material_state = 'red'
            elif all(rate >= 1.0 for rate in rate_list):
                mo.material_state = 'green'
            else:
                mo.material_state = 'yellow'

    ava_spent_time = fields.Float(string=u'平均生产用时(h)', compute='_compute_ava_spent_time')
    real_theo_spent_time = fields.Float(string=u'生产用时(h)', compute='_compute_real_theo_spent_time')
    produce_speed_factor = fields.Selection(related="bom_id.produce_speed_factor", )

    theory_factor = fields.Integer(related="bom_id.theory_factor")

    factory_setting_id = fields.Many2one("hr.config.settings", compute="_compute_factory_setting_id")
    production_line_id = fields.Many2one("mrp.production.line", string=u"产线")

    planned_start_backup = fields.Datetime(string=u"最晚开始时间")

    alia_name = fields.Char(string=u"别名", size=16)

    product_order_type = fields.Selection(string=u"产品类型",
                                          selection=[('ordering', u'订单制'),
                                                     ('stock', u'备货制'), ],
                                          required=False,
                                          compute='_compute_product_order_type')

    theo_spent_time = fields.Float(string=u'生产用时(h)', compute='_compute_theo_spent_time')

    prepare_material_state = fields.Selection(string=u"备料状态", selection=[('red', u'红'),
                                                                         ('yellow', u'黄'),
                                                                         ('green', u'绿'), ],
                                              required=False,
                                              compute='_compute_prepare_material_state')

    material_state = fields.Selection(string=u"物料状态", selection=[('red', u'红'),
                                                                 ('yellow', u'黄'),
                                                                 ('green', u'绿'), ],
                                      required=False,
                                      compute='_compute_material_state')
    '''
    操作mo信息接口
    '''

    def change_prod_qty(self, **kwargs):
        product_qty = kwargs.get("product_qty")

        qty_wizard = self.env['change.production.qty'].create({
            'mo_id': self.id,
            'product_qty': product_qty or self.product_qty,
        })
        qty_wizard.change_prod_qty()

        return self.read(FIELDS)
    # 开始生产 重新计算排产
    def produce_start_replan_mo(self):
        now_time = self.get_today_time(is_current_time=True)
        self.planned_one_mo(self, now_time, self.production_line_id)
        self.replanned_mo(self.env["mrp.production.line"], self.production_line_id, base_on_today=True)

    def change_backup_time(self, **kwargs):
        self.write({
            'planned_start_backup': kwargs.get("planned_start_backup")
        })
        origin_pl_mos, all_mos = self.replanned_mo(self.env["mrp.production.line"], self.production_line_id)
        return {'mos': all_mos.read(fields=FIELDS),
                'origin_pl_mos': origin_pl_mos.read(fields=FIELDS),
                'operate_mo': self.read(fields=FIELDS),
                'state_mapping': self.fields_get(["state"]),
                }

    #生产完成 重新计算排产
    def produce_finish_replan_mo(self):
        now_time = self.get_today_time(is_current_time=True)
        self.write({
            'date_planned_finished': pytz.UTC.normalize(now_time)
        })
        self.replanned_mo(self.env["mrp.production.line"], self.production_line_id, base_on_today=True)

    # 返工 重新计算排产
    def confirm_rework_replan_mo(self):

        mo = self.production_line_id.get_recent_available_planned_time()
        if not mo:
            now_time = self.get_today_time(is_current_time=True)
        else:
            planned_start_backup = fields.Datetime.from_string(mo.date_planned_start)
            new_datetime = datetime(planned_start_backup.year,
                                    planned_start_backup.month,
                                    planned_start_backup.day,
                                    planned_start_backup.hour,
                                    planned_start_backup.minute,
                                    planned_start_backup.second,
                                    microsecond=planned_start_backup.microsecond,
                                    tzinfo=pytz.timezone("UTC"))
            now_time = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
        self.planned_one_mo(self, now_time, self.production_line_id)

        self.replanned_mo(self.env["mrp.production.line"], self.production_line_id, base_on_today=True)
        #是否替代已生产中的单子的时间

    def _compute_produced_spend(self):
        if self.feedback_on_rework:
            return self.factory_setting_id.rework_spent_time * 60 * 60 or REWORK_DEFAULT_TIME
        return self.theo_spent_time * 3600

    #根据process_id 获取未排产mo
    def get_unplanned_mo(self, **kwargs):
        process_id = kwargs.get("process_id")
        state = kwargs.get("state")
        limit = kwargs.get("limit")
        offset = kwargs.get("offset")

        domain = [("process_id", "=", process_id),
                  ("production_line_id", "=", False),
                  ("state", "in", [state])]

        domains = kwargs.get("domains", [])
        new_domains = expression.AND([domains, domain])
        mos = self.env["mrp.production"].search_read(
                new_domains,
                limit=limit,
                offset=offset,
                order=ORDER_BY,
                fields=FIELDS
                )
        length = self.env["mrp.production"].search_count(new_domains)
        return {
            'length': length,
            'result': mos,
        }

    def get_unplanned_mo_by_search(self, **kwargs):
        process_id = kwargs.get("process_id")
        state = kwargs.get("state")
        search_domain = kwargs.get("domains", [])
        if not search_domain:
            return {
                'length': 0,
                'result': []
                }
        limit = kwargs.get("limit")
        offset = kwargs.get("offset")

        domain = [("process_id", "=", process_id),
                  ("production_line_id", "=", False),
                  ("state", "in", [state])]

        domains = kwargs.get("domains", [])
        new_domains = expression.AND([domains, domain, search_domain])
        mos = self.env["mrp.production"].search_read(
                new_domains,
                limit=limit,
                offset=offset,
                order=ORDER_BY,
                fields=FIELDS
        )
        length = self.env["mrp.production"].search_count(new_domains)
        return {
            'length': length,
            'result': mos,
        }

    def get_planned_mo_by_search(self, **kwargs):
        process_id = kwargs.get("process_id")
        domains = kwargs.get("domains", [])
        if not domains:
            return []
        order_by_material = kwargs.get("order_by_material", False)
        group_by = kwargs.get("group_by")
        state_domain = ("state", "not in", DONE_CANCEL_DOMAIN)
        new_domain = expression.AND([domains, [("process_id", "=", process_id),
                                               state_domain]])

        ungroup_domain = expression.AND([domains, [('production_line_id', '=', False),
                                                   ("process_id", "=", process_id),
                                                   ("state", "not in", ['done', 'cancel', 'draft', 'confirmed'])]])

        groups = self.read_group(domain=new_domain,
                                 fields=FIELDS,
                                 groupby=group_by)

        MrpProducion = self.env["mrp.production"]
        groups_dic = {}
        for group in groups:
            domain = group.get("__domain", [])
            line_id = group.get("production_line_id")
            if line_id:
                mos = MrpProducion.search_read(domain, fields=FIELDS, order=ORDER_BY)
                group["mos"] = self.sorted_mos_by_material(mos, order_by_material)
                groups_dic[group.get("production_line_id")[0]] = group
            else:
                mos = MrpProducion.search_read(ungroup_domain, fields=FIELDS, order=ORDER_BY)
                group["mos"] = self.sorted_mos_by_material(mos, order_by_material)
                groups_dic['-1'] = group

        return groups_dic

    def sorted_mos_by_material(self, mos, order_by_material):
        if order_by_material:  # 按照物料状态排序
            def cmp_func(a, b):
                if a.get("availability") == 'assigned':
                    a_val = 4
                elif a.get("availability") == 'partially_available':
                    a_val = 3
                elif a.get("availability") == 'waiting':
                    a_val = 2
                else:
                    a_val = 1
                if b.get("availability") == 'assigned':
                    b_val = 4
                elif b.get("availability") == 'partially_available':
                    b_val = 3
                elif b.get("availability") == 'waiting':
                    b_val = 2
                else:
                    b_val = 1
                return b_val - a_val
                # 'assigned', 'Available'),
                # ('partially_available', 'Partially Available'),
                # ('waiting', 'Waiting'),

            mos.sort(cmp_func)
            new_mos = mos
        else:
            new_mos = mos
        return new_mos

    def get_today_time(self, is_current_time=False, day_offset=0):
        now_time = fields.datetime.now(pytz.timezone(self.env.user.tz)) + relativedelta(days=day_offset)
        if not is_current_time:
            now_time = datetime(now_time.year,
                                now_time.month,
                                now_time.day,
                                0,
                                0,
                                0,
                                microsecond=0,
                                tzinfo=now_time.tzinfo)
        return now_time

    def compute_mo_time(self, all_mos, production_line, base_on_today):
        # 如果此条产线暂时无任何mo,
        self_date_planned_start = fields.Datetime.from_string(self.date_planned_start)
        if len(all_mos) == 1:
            planned_start_backup = self_date_planned_start
            new_datetime = datetime(planned_start_backup.year,
                                    planned_start_backup.month,
                                    planned_start_backup.day,
                                    planned_start_backup.hour,
                                    planned_start_backup.minute,
                                    planned_start_backup.second,
                                    microsecond=planned_start_backup.microsecond,
                                    tzinfo=pytz.timezone("UTC"))
            next_mo_start_time = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
            self.planned_one_mo(all_mos, next_mo_start_time, production_line)
        else:
            if all_mos:
                if not base_on_today:
                    if all_mos[0] == self:  # 如果本次排产的单子本身就再第一个,要取第二个的时间来作为排产时间了
                        planned_start_backup = fields.Datetime.from_string(all_mos[1].date_planned_start)
                    else:
                        datetime_start = fields.Datetime.from_string(all_mos[0].date_planned_start)
                        if datetime_start > self_date_planned_start:
                            planned_start_backup = self_date_planned_start
                        else:
                            planned_start_backup = datetime_start

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
                        start_time, end_time = self.planned_one_mo(mo, next_mo_start_time, production_line)
                        next_mo_start_time = end_time.astimezone(pytz.timezone(self.env.user.tz))
                else:  # 开始生产 重新排程
                    all_mos = all_mos - self
                    all_mos = self + all_mos
                    planned_start_backup = fields.Datetime.from_string(all_mos[0].date_planned_finished)
                    new_datetime = datetime(planned_start_backup.year,
                                            planned_start_backup.month,
                                            planned_start_backup.day,
                                            planned_start_backup.hour,
                                            planned_start_backup.minute,
                                            planned_start_backup.second,
                                            microsecond=planned_start_backup.microsecond,
                                            tzinfo=pytz.timezone("UTC"))

                    next_mo_start_time = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
                    for mo in all_mos[1:]:
                        start_time, end_time = self.planned_one_mo(mo, next_mo_start_time, production_line, )
                        next_mo_start_time = end_time.astimezone(pytz.timezone(self.env.user.tz))

    # base_on_today 第一个mo的排产时间是否基于今天
    def replanned_mo(self, origin_production_line, production_line, base_on_today=False, is_priority=False):

        # if not production_line:
        #     no_production_line = True
        #     if self.production_line_id:
        #         production_line = self.production_line_id
        #     else:  # 从未排产拖到未排产
        #         return
        #
        #     self.write({
        #         'production_line_id': None
        #     })
        # else:
        #     self.write({
        #         'production_line_id': production_line.id
        #     })
        # 取出这条产线所有的mo
        domain = [("state", "not in", DONE_CANCEL_DOMAIN)]
        origin_mos = self.env["mrp.production"]
        all_mos = self.env["mrp.production"]
        if origin_production_line:
            new_domain = domain + [("production_line_id", "=", origin_production_line.id)]
            origin_mos = self.env["mrp.production"].search(new_domain,
                                                           order=ORDER_BY)
        if production_line:
            new_domain = domain + [("production_line_id", "=", production_line.id)]
            all_mos = self.env["mrp.production"].search(new_domain,
                                                        order=ORDER_BY)
            if is_priority:  # 如果是优先排产
                all_mos -= self
                if not all_mos:  # 如果产线上只有本mo,则直接开始从今天排
                    self.planned_one_mo(self, self.get_today_time(day_offset=1), production_line)
                else:
                    first_start_time = fields.Datetime.from_string(all_mos[0].planned_start_backup)
                    new_datetime = datetime(first_start_time.year,
                                            first_start_time.month,
                                            first_start_time.day,
                                            first_start_time.hour,
                                            first_start_time.minute,
                                            first_start_time.second,
                                            microsecond=first_start_time.microsecond,
                                            tzinfo=pytz.timezone("UTC"))

                    next_mo_start_time = new_datetime.astimezone(pytz.timezone(self.env.user.tz)) - relativedelta(days=1)

                    self.planned_start_backup = next_mo_start_time
                    all_mos = self + all_mos

        if production_line.id == origin_production_line.id:
            return origin_mos, all_mos
        # filtered_all_mos = all_mos.filtered(lambda x: x.state in ["draft", "cancel", "waiting_material"])
        if origin_mos:
            self.compute_mo_time(origin_mos, origin_production_line, base_on_today)
        # 如果此条产线暂时无任何mo,
        if len(all_mos) == 1:
            self.planned_one_mo(self, self.get_today_time(day_offset=1), production_line)
        else:
            if all_mos:
                if not base_on_today:
                    if all_mos[0] == self:  # 如果本次排产的单子本身就再第一个,要取第二个的时间来作为排产时间了
                        planned_start_backup = fields.Datetime.from_string(all_mos[1].date_planned_start)
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
                        start_time, end_time = self.planned_one_mo(mo, next_mo_start_time, production_line)
                        next_mo_start_time = end_time.astimezone(pytz.timezone(self.env.user.tz))
                else:  # 开始生产 重新排程
                    all_mos = all_mos - self
                    all_mos = self + all_mos
                    planned_start_backup = fields.Datetime.from_string(all_mos[0].date_planned_finished)
                    new_datetime = datetime(planned_start_backup.year,
                                            planned_start_backup.month,
                                            planned_start_backup.day,
                                            planned_start_backup.hour,
                                            planned_start_backup.minute,
                                            planned_start_backup.second,
                                            microsecond=planned_start_backup.microsecond,
                                            tzinfo=pytz.timezone("UTC"))

                    next_mo_start_time = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
                    for mo in all_mos[1:]:
                        start_time, end_time = self.planned_one_mo(mo, next_mo_start_time, production_line,)
                        next_mo_start_time = end_time.astimezone(pytz.timezone(self.env.user.tz))
            else:  # ---从左往右移除的时候 要重置一下移除的mo的排产时间
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
                    self.planned_one_mo(self, planned_start_backup_with_zone, production_line)

        return origin_mos, all_mos

    def planned_one_mo(self, mo, next_mo_start_time, production_line):
        start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(next_mo_start_time,
                                                                              mo._compute_produced_spend(),
                                                                              start_or_end="start",
                                                                              equipment_no=production_line.compute_speed_factor(
                                                                                  mo.bom_id))


        vals = {
            'date_planned_start': start_time,
            'date_planned_finished': end_time,
        }
        if production_line:
            charge_id = production_line.employee_id.address_home_id.id or production_line.process_id.partner_id.id
            vals.update({
                'in_charge_id': charge_id
            })

        # if to_state:
        #     if mo.state in ["draft", "confirmed", "waiting_material"]:
        #         vals.update({
        #             'state': to_state,
        #         })
        mo.write(vals)
        return start_time, end_time

    # 排产或者取消排产
    def settle_mo(self, **kwargs):
        production_line_id = kwargs.get("production_line_id")
        settle_date = kwargs.get("settle_date")
        state = kwargs.get("state")
        origin_production_line = self.production_line_id
        if self.state not in ["draft", "confirmed", "waiting_material"]:
            raise UserError(u"该单据已经开始生产,不可重新进行排产")

        if production_line_id == -1:
            raise UserError(u'无法排产到未分组中...')
        # 改变产线和状态
        if not production_line_id:  #如果没有产线传上来, 就说明是从产线移除(取消排产)
            self.write({
                'production_line_id': None
            })
            # if self.planned_start_backup:
            #     planned_start_backup = fields.Datetime.from_string(self.planned_start_backup)
            #     new_datetime = datetime(planned_start_backup.year,
            #                             planned_start_backup.month,
            #                             planned_start_backup.day,
            #                             planned_start_backup.hour,
            #                             planned_start_backup.minute,
            #                             planned_start_backup.second,
            #                             microsecond=planned_start_backup.microsecond,
            #                             tzinfo=pytz.timezone("UTC"))
            #
            #     planned_start_backup_with_zone = new_datetime.astimezone(pytz.timezone(self.env.user.tz))
            #     start_time, end_time = self.env["ll.time.util"].compute_mo_start_time(planned_start_backup_with_zone,
            #                                                                           self._compute_produced_spend(),
            #                                                                           start_or_end="start")
            #     self.write({
            #         'date_planned_start': start_time,
            #         'date_planned_finished': end_time,
            #     })
            if self.state in ["draft", "confirmed", "waiting_material"]:
                self.state = state
            else:
                raise UserError(u"该单据已经开始生产,不可从产线上移除")
        else:  # 改变产线和状态
            self.write({
                'production_line_id': production_line_id
            })
            if self.state in ["draft", "confirmed", "waiting_material"]:
                self.write({
                    "state": 'waiting_material'
                })
        origin_pl_mos = self.env["mrp.production"]
        # if origin_production_line and production_line_id:  # 两条产线之间切换,
        #     origin_pl_mos = self.replanned_mo(origin_production_line, production_line_id) - self

        production_line = self.env["mrp.production.line"].browse(production_line_id)
        origin_pl_mos, all_mos = self.replanned_mo(origin_production_line, production_line)

        return {'mos': all_mos.read(fields=FIELDS),
                'origin_pl_mos': origin_pl_mos.read(fields=FIELDS),
                'operate_mo': self.read(fields=FIELDS),
                'state_mapping': self.fields_get(["state"]),
                }


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
                            relativedelta(hours=setting.factory_work_start_time),
                            relativedelta(hours=setting.factory_work_end_time))
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
