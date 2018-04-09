# -*- coding: utf-8 -*-
import datetime
import pytz
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
import json
import urllib

from odoo.exceptions import MissingError, UserError


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    backup_standard_price = fields.Float(string=u'标准价格(不可用,仅参考)', digits=dp.get_precision('Product Price'),
                                         raedonly=True)

class ll_auto_plan_kb(models.Model):
    _name = 'auto.plan'

    name = fields.Char()
    type = fields.Char()
    count_red = fields.Integer(compute='_compute_count_red')
    count_green = fields.Integer(compute='_compute_count_green')
    count_yellow = fields.Integer(compute='_compute_count_yellow')
    count_qc = fields.Integer(compute='_compute_count_qc')
    count_confirm = fields.Integer(compute='_compute_count_confirm')
    count_inventory = fields.Integer(compute='_compute_count_inventory')
    count_waiting_file = fields.Integer(compute='_compute_count_waiting_file')
    count_to_invoice = fields.Integer(compute='_compute_to_invoice_po')

    def _compute_to_invoice_po(self):
        for plan in self:
            plan.count_to_invoice = len(
                self.env['purchase.order'].search(
                    [('invoice_status', '=', 'to invoice')]))

    @api.multi
    def _compute_count_waiting_file(self):
        for plan in self:
            if plan.type == 'waiting_file':
                plan.count_waiting_file = len(
                    self.env['purchase.order'].search(
                        [("waiting_file", '=', True), ('state', 'in', ['purchase', 'done'])]))

    @api.multi
    def _compute_count_red(self):
        # pos = self.env['purchase.order'].search([('state', '=', 'purchase')])
        # self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].cal_po_light_status(pos)
        for plan in self:
            plan.count_red = len(
                self.env['purchase.order'].search([("status_light", '=', 3), ('state', '=', 'purchase')]))

    @api.multi
    def _compute_count_green(self):
        for plan in self:
            plan.count_green = len(
                self.env['purchase.order'].search([("status_light", '=', 1), ('state', '=', 'purchase')]))

    @api.multi
    def _compute_count_yellow(self):
        for plan in self:
            plan.count_yellow = len(
                self.env['purchase.order'].search([("status_light", '=', 2), ('state', '=', 'purchase')]))

    @api.multi
    def _compute_count_qc(self):
        for plan in self:
            plan.count_qc = len(self.env["stock.picking"].search([("state", '=', 'qc_check')]))

    @api.multi
    def _compute_count_confirm(self):
        for plan in self:
            plan.count_confirm = len(self.env["stock.picking"].search([("state", '=', 'validate')]))

    @api.multi
    def _compute_count_inventory(self):
        for plan in self:
            plan.count_inventory = len(self.env["stock.picking"].search([("state", '=', 'waiting_in')]))

    @api.multi
    def get_purchase_order_to_invoice(self):
        return {
            'name': u'采购单',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('invoice_status', '=', 'to invoice')]
        }

    @api.multi
    def get_waiting_file_po(self):
        red = self.env['purchase.order'].search([("waiting_file", '=', True), ('state', 'in', ['purchase', 'done'])])
        return {
            'name': u'等待文件的订单',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', red.ids)]}

    @api.multi
    def get_red_1(self):
        red = self.env['purchase.order'].search([("status_light", '=', 3), ("state", '=', 'purchase')])
        self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].cal_po_light_status(red)
        return {
            'name': u'红',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', red.ids)]}

    def get_green(self):
        red = self.env['purchase.order'].search([("status_light", '=', 1), ("state", '=', 'purchase')])
        self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].cal_po_light_status(red)
        return {
            'name': u'绿',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', red.ids)]}

    def get_yellow(self):
        red = self.env['purchase.order'].search([("status_light", '=', 2), ("state", '=', 'purchase')])
        self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].cal_po_light_status(red)
        return {
            'name': u'黄',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', red.ids)]}

    def get_stock_picking_qc(self):
        qc_check = self.env["stock.picking"].search([("state", '=', 'qc_check')])
        return {
            'name': u'待品检',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'target': 'current',
            'domain': [('id', 'in', qc_check.ids)]}

    def get_stock_picking_purchase_confirm(self):
        qc_check = self.env["stock.picking"].search([("state", '=', 'validate')])
        return {
            'name': u'待确认',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'target': 'current',
            'domain': [('id', 'in', qc_check.ids)]}

    def get_stock_picking_inventory(self):
        qc_check = self.env["stock.picking"].search([("state", '=', 'waiting_in')])
        return {
            'name': u'待入库',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'target': 'current',
            'domain': [('id', 'in', qc_check.ids)]}

    def refresh_po(self):
        pos = self.env["purchase.order"].search([("state", '=', 'purchase')])
        self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].cal_po_light_status(pos)
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"刷新采购单状态",
                "text": u"刷新成功",
                "sticky": False
            }
        }


class linkloving_mrp_automatic_plan(models.Model):
    _name = 'linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan'

    #     value = fields.Integer()
    #     value2 = fields.Float(compute="_value_pc", store=True)
    #     description = fields.Text()
    #
    #     @api.depends('value')
    #     def _value_pc(self):
    #         self.value2 = float(self.value) / 100

    @api.multi
    def get_holiday(self):
        page = urllib.urlopen(
            "https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?query=2017%E5%B9%B48%E6%9C%88&co=&resource_id=6018&t=1496889566304&ie=utf8&oe=gbk&format=json&tn=baidu&_=1496889558209")
        html = page.read()
        # print html.decode("gbk")
        return {
            "holiday": html.decode("gbk")
        }

    def calc_status_light(self, order_id=None):

        # def get_propagate_po(propagated_procurements):
        #     pos = self.env["purchase.order"]
        #     for procurement in propagated_procurements:
        #         if procurement.rule_id.action == 'buy':
        #             if procurement.purchase_line_id:
        #                 pos += procurement.purchase_line_id.order_id
        #             else:
        #                 propagated_procurements -= procurement
        #     if pos:
        #         return pos
        #     else:
        #         return propagated_procurements

        # def get_propagate_sm(propagated_procurements):
        #     cancel_moves = propagated_procurements.filtered(lambda order: order.rule_id.action == 'move').mapped(
        #         'move_ids')
        #     new_ps = propagated_procurements.search(
        #             [('move_dest_id', 'in', cancel_moves.filtered(lambda move: move.propagate).ids)])
        #     if new_ps:
        #         return get_propagate_po(new_ps)
        #     else:
        #         return get_propagate_po(propagated_procurements)
        #
        # def get_propagate_mo(propagated_procurements):
        #     production_orders = propagated_procurements.filtered(
        #         lambda procurement: procurement.rule_id.action == 'manufacture' and procurement.production_id).mapped(
        #         'production_id')
        #     if production_orders:
        #         return production_orders
        #     return get_propagate_sm(propagated_procurements)

        # def get_propagate_order(procurements):
        #     propagated_procurements = procurements.filtered(lambda order: order.state != 'done')
        #     obj_get = get_propagate_mo(propagated_procurements)
        #     if not obj_get:
        #         return
        #     if type(obj_get) == type(self.env["procurement.order"]):
        #         get_propagate_order(obj_get)
        #     elif type(obj_get) == type(self.env["purchase.order"]):
        #         po_s[0] += obj_get
        #     elif type(obj_get) == type(self.env["mrp.production"]):
        #         mo_s[0] += obj_get
        #         for production in obj_get:
        #             finish_moves = production.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        #             raw_moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        #
        #             procurements = self.env["procurement.order"].search([('move_dest_id', 'in', raw_moves.ids)])
        #             get_propagate_order(procurements)
        #
        #     else:
        #         pass

        if order_id:
            sos = order_id
        else:
            # sos = self.env["sale.order"].browse(order_id)
            sos = self.env["sale.order"].search([("state", '=', 'sale')])
        i = 0
        for so in sos:
            print('%d/%d' % (i, len(sos)))
            i += 1
            pos = self.env["purchase.order"].search([("origin", 'like', so.name)])
            mos = self.env["mrp.production"].search([("origin", 'like', so.name)])

            if not pos and not mos:
                continue
            lv1_mo = mos.filtered(lambda x: "WH" in x.origin)

            # 获取最底下的节点
            last_nodes = self.env["mrp.production"]  # 最底下的节点
            for mo in mos:
                relate_mos = mos.filtered(lambda x: mo.name in x.origin)
                if not relate_mos:
                    last_nodes += mo

            # 根据最底下的节点 获取到每条线
            lines = []
            for mo in last_nodes:
                node = mo
                one_line = [node]
                while True:
                    if not node.origin:
                        break
                    origins = node.origin.split(",")
                    need_break_after_while = False
                    for ori in origins:
                        if ':' in ori:
                            origin = ori.split(":")[1]

                            one_mo = mos.filtered(lambda x: x.name == origin)
                            if one_mo:
                                need_break_after_while = False  # 如果有就不要跳出去了
                                one_line.append(one_mo)
                                node = one_mo
                            else:
                                need_break_after_while = True
                            if node in lv1_mo:
                                break
                        else:
                            need_break_after_while = True
                            break
                    if need_break_after_while:
                        lines.append(one_line)
                        break

                    if node in lv1_mo:
                        lines.append(one_line)
                        break

            # 获取到每张mo对应的 po
            origin_mos = {}
            for mo in mos:
                origin_pos = pos.filtered(lambda x: mo.name in x.origin)
                origin_mos[mo.id] = origin_pos

            # 计算po单 状态灯
            self.cal_po_light_status(pos)

            # 开始计算灯状态
            for line in lines:
                for mo in line:
                    self.cal_mo_light_status(mo, origin_mos, line)

            # 计算SO单订单条目 状态灯
            for line in so.order_line:
                if line.procurement_ids and line.procurement_ids[0].move_ids:
                    moves = line.procurement_ids[0].move_ids.ids
                    pros = self.env["procurement.order"].search([("move_dest_id", 'in', moves)])
                    production_ids = pros.mapped("production_id")
                    if production_ids:
                        line.status_light = max(production_ids.mapped("status_light"))
                        line.material_light = max(production_ids.mapped("material_light"))

            # so status light
            if so.order_line.mapped("status_light"):
                so.status_light = max(so.order_line.mapped("status_light"))
                so.material_light = max(so.order_line.mapped("material_light"))
                # for mo in lv1_mo:
                #     lv = 0
                #     mo_relate_mo = []
                #     rescuise(mos, mo, lv)
                #     all_mo_mo.append(mo_relate_mo)

                # so.action_cancel()
                # procurements = so.order_line.mapped('procurement_ids')
                # get_propagate_order(procurements)

    def cal_mo_light_status(self, mos, origin_mos, line):
        today_start, today_end = self.get_today_start_end()
        for mo in mos:
            # mo.status_light = False
            date_planned_start = fields.datetime.strptime(mo.date_planned_start, '%Y-%m-%d %H:%M:%S')
            date_planned_end = fields.datetime.strptime(mo.date_planned_finished, '%Y-%m-%d %H:%M:%S')

            orgin_pos = origin_mos.get(mo.id)
            if orgin_pos:
                mo.status_light = max(orgin_pos.mapped("status_light"))
                mo.material_light = max(orgin_pos.mapped("status_light"))
            else:
                mo.material_light = 1

            # 如果状态为未排产 则直接红灯
            if mo.state in ["draft"]:
                mo.status_light = 3
                continue

            # mo状态为 等待退料,接受退料,结束(成品已入库)
            if mo.state in ["done", "waiting_inventory_material", "waiting_warehouse_inspection"]:
                mo.status_light = 1
                mo.material_light = 1
                continue
            #
            index = 0
            for s in line:
                if mo == s:
                    break
                index += 1
            if index > 0:
                child_mo = line[index - 1]
                mo.status_light = max(mo.status_light, child_mo.status_light)
                mo.material_light = max(mo.material_light, child_mo.material_light)

            if date_planned_start > date_planned_end:
                mo.status_light = 3
                break
            if date_planned_start < today_start and date_planned_end < today_start:  # 开始时间-结束时间 在今天之前
                mo.status_light = 3
            elif today_end < date_planned_start and today_end < date_planned_end:  # 开始结束都在今天之后
                mo.status_light = max(1, mo.status_light)
            elif today_start > date_planned_start and today_end < date_planned_end:  # 开始在今天之前, 结束在今天之后
                mo.status_light = 3
            elif today_start > date_planned_start and today_end > date_planned_end:  # 开始时间再今天之前,结束时间再今天之内
                mo.status_light = max(2, mo.status_light)
            elif today_start < date_planned_start and today_end > date_planned_end:  # 开始结束都在今天之内
                mo.status_light = max(2, mo.status_light)
            elif today_start < date_planned_start and today_end < date_planned_end:  # 开始在今天 结束不在
                mo.status_light = 3
            else:
                mo.status_light = 3

    def cal_po_light_status(self, pos):
        today_start, today_end = self.get_today_start_end()
        four_days = datetime.timedelta(days=4)
        two_days = datetime.timedelta(days=2)
        for po in pos:
            try:
                if po.state in ['purchase']:
                    if po.handle_date:
                        handle_date = fields.datetime.strptime(po.handle_date, '%Y-%m-%d %H:%M:%S')
                    else:  # 如果没有日期 则直接红灯
                        po.status_light = 3
                        continue

                    if po.shipping_status == "done":  # 如果已经收货完成 则绿灯
                        po.status_light = False
                        continue

                    if handle_date - today_start < two_days:
                        po.status_light = 3
                    elif handle_date - today_end > four_days:
                        po.status_light = 1
                    elif (handle_date - today_end <= four_days) and (handle_date - today_start >= two_days):
                        po.status_light = 2
                    else:
                        po.status_light = 3
                elif po.state in ['draft', 'make_by_mrp']:
                    po.status_light = 3
                else:
                    continue
            except:
                continue

    def calc_orderpoint_light(self):
        orderpoints = self.env["stock.warehouse.orderpoint"].search([("active", '=', True)])
        productions = orderpoints.mapped("procurement_ids").mapped("production_id")
        for production in productions:
            pos = self.env["purchase.order"].search([("origin", 'like', production.name)])
            mos = self.env["mrp.production"].search([("origin", 'like', production.name)]) + production
            if not pos and not mos:
                continue

            # 获取最底下的节点
            last_nodes = self.env["mrp.production"]  # 最底下的节点
            for mo in mos:
                relate_mos = mos.filtered(lambda x: mo.name in x.origin)
                if not relate_mos:
                    last_nodes += mo

            # 根据最底下的节点 获取到每条线
            lines = []
            for mo in last_nodes:
                node = mo
                one_line = [node]
                while True:
                    if not node.origin:
                        break
                    origins = node.origin.split(",")
                    need_break_after_while = False
                    for ori in origins:
                        if ':' in ori:
                            origin = ori.split(":")[1]
                            one_mo = mos.filtered(lambda x: x.name == origin)
                            one_line.append(one_mo)
                            node = one_mo
                            if node in productions:
                                break
                        else:
                            need_break_after_while = True
                            break
                    if need_break_after_while:
                        break
                    if node in productions:
                        lines.append(one_line)
                        break
            # 获取到每张mo对应的 po
            origin_mos = {}
            for mo in mos:
                origin_pos = pos.filtered(lambda x: mo.name in x.origin)
                origin_mos[mo.id] = origin_pos

                # 计算po单 状态灯
            self.cal_po_light_status(pos)

            # 开始计算灯状态
            for line in lines:
                for mo in line:
                    self.cal_mo_light_status(mo, origin_mos, line)

    def get_today_start_end(self):
        timez = fields.datetime.now(pytz.timezone(self.env.user.tz)).tzinfo._utcoffset

        today_time_start = fields.datetime.strptime(fields.datetime.strftime(fields.datetime.now(), '%Y-%m-%d'),
                                                    '%Y-%m-%d') - timez
        today_time_end = today_time_start + datetime.timedelta(days=1, milliseconds=-1)
        return today_time_start, today_time_end


class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'

    prepare_time = fields.Integer(u"准备时间 (秒)")
    capacity_value = fields.Integer(u"产能 (pcs/s)")


class PuchaseOrderEx(models.Model):
    _inherit = "purchase.order"
    status_light = fields.Selection(string="状态灯", selection=[(3, '红'),
                                                             (2, '黄'),
                                                             (1, '绿')], required=False,
                                    store=True)

    waiting_file = fields.Boolean(string=u"是否等待文件", default=False)
    # @api.depends('state', 'handle_date', 'picking_ids.state')
    # def _compute_status_light(self):
    #     print("do compute status_light")
    #     self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].cal_po_light_status(self)
    sale_order_handle_date = fields.Datetime(string=u'源SO交期', compute='_compute_sale_order_handle_date')

    @api.multi
    def _compute_sale_order_handle_date(self):
        for po in self:
            group_ids = po.order_line.mapped('procurement_ids').mapped("group_id")
            sales = self.env["sale.order"].sudo().search([('name', 'in', group_ids.mapped("name"))])
            if sales.mapped("validity_date"):
                po.sale_order_handle_date = min(sales.mapped("validity_date"))

class SaleOrderEx(models.Model):
    _inherit = "sale.order"
    status_light = fields.Selection(string="状态灯", selection=[(3, '红'),
                                                             (2, '黄'),
                                                             (1, '绿')], required=False, )

    material_light = fields.Selection(string="物料状态", selection=[(3, '红'),
                                                                (2, '黄'),
                                                                (1, '绿')], )

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        if len(self) == 1 and load == '_classic_read' and False:
            self.env["linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan"].calc_status_light(self)
        return super(SaleOrderEx, self).read(fields, load)


class SaleOrderLineEx(models.Model):
    _inherit = "sale.order.line"
    status_light = fields.Selection(string="状态灯", selection=[(3, '红'),
                                                             (2, '黄'),
                                                             (1, '绿')], required=False, )
    material_light = fields.Selection(string="物料状态", selection=[(3, '红'),
                                                                (2, '黄'),
                                                                (1, '绿')], )


class MrpProductionEx(models.Model):
    _inherit = "mrp.production"
    status_light = fields.Selection(string="状态灯", selection=[(3, '红'),
                                                             (2, '黄'),
                                                             (1, '绿')], required=False, )

    material_light = fields.Selection(string="物料状态", selection=[(3, '红'),
                                                                (2, '黄'),
                                                                (1, '绿')], )

    sale_order_handle_date = fields.Datetime(string=u'源SO交期', compute='_compute_sale_order_handle_date')

    @api.multi
    def _compute_sale_order_handle_date(self):
        for mo in self:
            group_ids = mo.procurement_ids.mapped("group_id")
            sales = self.env["sale.order"].sudo().search([('name', 'in', group_ids.mapped("name"))])
            if sales.mapped("validity_date"):
                mo.sale_order_handle_date = min(sales.mapped("validity_date"))

class OrderPointEx(models.Model):
    _inherit = "stock.warehouse.orderpoint"
    status_light = fields.Selection(string="状态灯", selection=[(3, '红'),
                                                             (2, '黄'),
                                                             (1, '绿')], required=False, )

    material_light = fields.Selection(string="物料状态", selection=[(3, '红'),
                                                                (2, '黄'),
                                                                (1, '绿')], )


class ProcurementOrderResetWizard(models.TransientModel):
    _name = 'procurement.order.reset.confirm'

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        procurements = self.env['procurement.order'].search([('id', 'in', active_ids)])
        if all(p.state == "cancel" for p in procurements):
            procurements.reset_to_confirmed()
        else:
            raise UserError(u"请确保所有的单据都为'取消'状态")
