# -*- coding: utf-8 -*-
import datetime
import pytz

from odoo import models, fields, api
import json
import urllib

class linkloving_mrp_automatic_plan(models.Model):
    _name = 'linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan'

#     name = fields.Char()
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

    def calc_status_light(self):

        def get_propagate_po(propagated_procurements):
            pos = self.env["purchase.order"]
            for procurement in propagated_procurements:
                if procurement.rule_id.action == 'buy':
                    if procurement.purchase_line_id:
                        pos += procurement.purchase_line_id.order_id
                    else:
                        propagated_procurements -= procurement
            if pos:
                return pos
            else:
                return propagated_procurements

        def get_propagate_sm(propagated_procurements):
            cancel_moves = propagated_procurements.filtered(lambda order: order.rule_id.action == 'move').mapped(
                'move_ids')
            new_ps = propagated_procurements.search(
                    [('move_dest_id', 'in', cancel_moves.filtered(lambda move: move.propagate).ids)])
            if new_ps:
                return get_propagate_po(new_ps)
            else:
                return get_propagate_po(propagated_procurements)

        def get_propagate_mo(propagated_procurements):
            production_orders = propagated_procurements.filtered(
                lambda procurement: procurement.rule_id.action == 'manufacture' and procurement.production_id).mapped(
                'production_id')
            if production_orders:
                return production_orders
            return get_propagate_sm(propagated_procurements)

        def get_propagate_order(procurements):
            propagated_procurements = procurements.filtered(lambda order: order.state != 'done')
            obj_get = get_propagate_mo(propagated_procurements)
            if not obj_get:
                return
            if type(obj_get) == type(self.env["procurement.order"]):
                get_propagate_order(obj_get)
            elif type(obj_get) == type(self.env["purchase.order"]):
                po_s[0] += obj_get
            elif type(obj_get) == type(self.env["mrp.production"]):
                mo_s[0] += obj_get
                for production in obj_get:
                    finish_moves = production.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    raw_moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))

                    procurements = self.env["procurement.order"].search([('move_dest_id', 'in', raw_moves.ids)])
                    get_propagate_order(procurements)

            else:
                pass

        # sos = self.env["sale.order"].search([("state", '=', 'sale')])
        sos = self.env["sale.order"].browse(3510)
        mo_s = [self.env["mrp.production"]]
        po_s = [self.env["purchase.order"]]

        def rescuise(mos, lv_mo, lv):
            lv += 1
            new_mos = self.env["mrp.production"]
            new_pos = self.env["purchase.order"]
            for mo in lv_mo:
                new_mos += mos.filtered(lambda x: mo.name in x.origin)
                new_pos += pos.filtered(lambda x: mo.name in x.origin)
            mo_relate_mo[lv] = {'mo': new_mos,
                                'po': new_pos}
            if new_mos:
                rescuise(mos, new_mos, lv)

        all_data = []
        for so in sos:
            pos = self.env["purchase.order"].search([("origin", 'like', so.name)])
            mos = self.env["mrp.production"].search([("origin", 'like', so.name)])
            lv1_mo = mos.filtered(lambda x: "WH" in x.origin)
            all_mo_mo = []
            for mo in lv1_mo:
                lv = 1
                mo_relate_mo = {'id': mo,
                                'po': pos.filtered(lambda x: mo.name in x.origin)}
                rescuise(mos, mo, lv)
                all_mo_mo.append(mo_relate_mo)

            all_data.append({
                'so': so,
                'orders': all_mo_mo
            })

        print(all_data)
        self.cal_mo_light_status(all_data)
        # so.action_cancel()
        # procurements = so.order_line.mapped('procurement_ids')
        # get_propagate_order(procurements)

    def cal_mo_light_status(self, mos):
        today_start, today_end = self.get_today_start_end()
        for mo in mos.filtered(lambda x: x.state not in ['done', 'cancel']):
            date_planned_start = fields.datetime.strftime(mo.date_planned_start, '%Y-%m-%d %H:%M:%S')
            date_planned_end = fields.datetime.strftime(mo.date_planned_end, '%Y-%m-%d %H:%M:%S')
            if date_planned_start < today_start and date_planned_end < today_start:  # 开始时间-结束时间 在今天之前
                mo.status_light = "2"
            elif today_end < date_planned_start and today_end < date_planned_end:  # 开始结束都在今天之后
                mo.status_light = "0"
            elif today_start > date_planned_start and today_end < date_planned_end:  # 开始在今天之前, 结束在今天之后
                mo.status_light = "2"
            elif today_start > date_planned_start and today_end > date_planned_end:  # 开始时间再今天之前,结束时间再今天之内
                mo.status_light = "1"
            elif today_start < date_planned_start and today_end > date_planned_end:  # 开始结束都在今天之内
                mo.status_light = "1"
            elif today_start < date_planned_start and today_end < date_planned_end:  # 开始在今天 结束不在
                mo.status_light = "2"

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
    status_light = fields.Selection(string="状态灯", selection=[('2', '红'),
                                                             ('1', '黄'),
                                                             ('0', '绿')], required=False, )


class SaleOrderEx(models.Model):
    _inherit = "sale.order"
    status_light = fields.Selection(string="状态灯", selection=[('2', '红'),
                                                             ('1', '黄'),
                                                             ('0', '绿')], required=False, )


class MrpProductionEx(models.Model):
    _inherit = "mrp.production"
    status_light = fields.Selection(string="状态灯", selection=[('2', '红'),
                                                             ('1', '黄'),
                                                             ('0', '绿')], required=False, )
