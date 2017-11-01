# -*- coding: utf-8 -*-
import calendar
import logging

import datetime

import pytz

from odoo import models, fields, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
import time

class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    simliar_companys = fields.Many2many(comodel_name="res.partner", relation="simliar_companys_rel",
                                        column1="company_id", column2="company_id2", string=u"相似的公司名字", )

    @api.multi
    def partner_unlink(self):
        # partners = self.env["res.partner"].search([("simliar_companys", "in", self.ids)])
        # for pa in partners:
        #     pa.simliar_companys -= self
        self.unlink()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_move_in_recent = fields.Boolean(string=u"近期是否移动过")

    @api.multi
    def create_reorder_rule(self, min_qty=0.0, max_qty=0.0, qty_multiple=1.0, overwrite=False):
        swo_obj = self.env['stock.warehouse.orderpoint']
        for rec in self:
            rec.product_tmpl_id.sale_ok = True
            rec.product_tmpl_id.purchase_ok = False
            rec.product_tmpl_id.product_ll_type = "finished"
            rec.product_tmpl_id.order_ll_type = "ordering"
            rec.product_tmpl_id.route_ids = [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,
                                                     self.env.ref('stock.route_warehouse0_mto').id])]
            reorder_rules = swo_obj.search([('product_id', '=', rec.id)])
            reorder_rules.unlink()
            continue
            reorder_vals = {
                'product_id': rec.id,
                'product_min_qty': min_qty,
                'product_max_qty': max_qty,
                'qty_multiple': qty_multiple,
                'active': True,
                'product_uom': rec.uom_id.id,
            }

            if rec.type in ('product', 'consu') and not reorder_rules:
                self.env['stock.warehouse.orderpoint'].create(reorder_vals)
            elif rec.type in ('product', 'consu') and reorder_rules and overwrite:
                for reorder_rule in reorder_rules:
                    reorder_rule.write(reorder_vals)


class CreateOrderPointWizard(models.TransientModel):
    _name = "create.order.point"

    def action_create_in_aboard_rule(self):
        # products = self.env["product.product"].search([("inner_spec", "!=", False)])
        # products = self.env["product.product"].search(
        #         ['|', ("default_code", "=ilike", "99.%"), ("default_code", "=ilike", "98.%")])

        products = self.env["product.product"].search(
            [("default_code", "=ilike", "98.%")])

        products.create_reorder_rule()

    def action_combine_purchase_order(self):
        pos = self.env["purchase.order"].search([("state", "=", "make_by_mrp")])
        same_origin = {}
        for po in pos:
            if len(po.order_line) > 1:
                continue
            if po.order_line[0].product_id.id in same_origin.keys():
                same_origin[po.order_line[0].product_id.id].append(po)
            else:
                same_origin[po.order_line[0].product_id.id] = [po]

        for key in same_origin.keys():
            po_group = same_origin[key]
            total_qty = 0
            procurements = self.env["procurement.order"]
            for po in po_group:
                total_qty += po.order_line[0].product_qty
                procurements += po.order_line[0].procurement_ids

            # 生成薪的po单 在po0的基础上
            po_group[0].order_line[0].product_qty = total_qty
            po_group[0].order_line[0].procurement_ids = procurements

            for po in po_group[1:]:
                po.button_cancel()

    def action_unreserved_stock_picking(self):
        pickings = self.env["stock.picking"].search([("state", "in", ["partially_available", "assigned"]),
                                                     ("picking_type_code", "=", "outgoing")])
        pickings.do_unreserve()

    def action_create_menu(self):
        menus = self.env["product.category"].search([])
        menus.menu_create()

    def action_handle_stock_move(self):
        moves = self.env["stock.move"].search([('id', 'in',
                                                [347132, 347037, 347061, 347076, 347185, 347031, 347032, 347033, 347034,
                                                 347035, 347036, 347038, 347039, 347040, 347041, 347042, 347043, 347044,
                                                 347045, 347046, 347047, 347048, 347049, 347050, 347051, 347052, 347053,
                                                 347054, 347055, 347057, 347058, 347059, 347060, 347062, 347063, 347064,
                                                 347065, 347066, 347056, 347067, 347068, 347069, 347070, 347071, 347072,
                                                 347073, 347074, 347075, 347077, 347078, 347079, 347080, 347081, 347082,
                                                 347083, 347084, 347085, 347086, 347087, 347088, 347089, 347090, 347091,
                                                 347092, 347093, 347094, 347095, 347096, 347097, 347098, 347099, 347100,
                                                 347101, 347102, 347103, 347104, 347105, 347106, 347107, 347108, 347109,
                                                 347110, 347111, 347112, 347113, 347114, 347115, 347116, 347117, 347118,
                                                 347119, 347120, 347121, 347122, 347123, 347124, 347125, 347126, 347127,
                                                 347128, 347129, 347130, 347131, 347133, 347134, 347135, 347136, 347137,
                                                 347138, 347139, 347140, 347141, 347142, 347143, 347144, 347145, 347146,
                                                 347147, 347148, 347149, 347150, 347151, 347152, 347153, 347154, 347155,
                                                 347156, 347157, 347158, 347159, 347160, 347161, 347162, 347163, 347164,
                                                 347166, 347170, 347165, 347167, 347168, 347169, 347171, 347172, 347173,
                                                 347174, 347175, 347176, 347177, 347178, 347179, 347180, 347181, 347182,
                                                 347183, 347184, 347186, 347187, 347188, 347189, 347190, 347191, 347192,
                                                 347193, 347194, 347195, 347196, 347197, 347198, 347199, 347200, 347201,
                                                 347202, 347203, 347204, 347205, 347206, 347207, 347208, 347209, 347210,
                                                 347211, 347212, 347213, 347214, 347215, 347216])])
        moves.action_cancel()
        print(111111)

    def action_cancel_mo(self):
        productions = self.env["mrp.production"].search([('state', 'in', ['draft', 'confirmed'])])
        productions.action_cancel()

    def action_cancel_so(self):
        # sos_unlink = self.env["sale.order"].search([('state', '=', 'cancel')])
        # sos_unlink.unlink()

        sos = self.env["sale.order"].search([('state', '=', 'sale'),
                                             ('shipping_rate', '<=', '0')])
        i = 0
        # self.order_line.mapped('procurement_ids')
        # filtered(lambda order: order.state != 'done')
        # procurement.rule_id.action == 'manufacture'
        so_cancel_redo = self.env["sale.order"]
        for so in sos:
            mos = self.env["mrp.production"].search([('origin', 'like', so.name)])
            if all(mo.state in ["draft", "confirmed", "cancel"] for mo in mos):
                so.temp_no = True
                # so_cancel_redo += so

    def cancel_temp_no(self):
        so_cancel_redo = self.env["sale.order"].search([("temp_no", "=", True)], limit=20)
        i = 0
        for so in so_cancel_redo:
            i = i + 1
            _logger.warning("start doing so, %d/%d" % (i, len(so_cancel_redo)))
            try:
                so.action_cancel()

                # sos = self.env["sale.order"].search([('state', '=', 'cancel')])
                so.action_draft()
                so.action_confirm()
                so.temp_no = False
            except:
                continue

    def modify_stock_move_company(self):
        quants = self.env["stock.quant"].search([("company_id", "=", 3)])
        for quant in quants:
            if quant.company_id != quant.product_id.company_id:
                quant.company_id = quant.product_id.company_id

    def action_confirm_canceled_so(self):
        pass
        # sos = self.env["sale.order"].search([('state', '=', 'cancel')])
        # sos.action_draft()
        # sos.action_confirm()

    def action_filter_partner(self):
        # return
        company2 = companys = self.env["res.partner"].search([("is_company", "=", True)], )
        for company in companys:
            company_obj = self.env["res.partner"]
            for similar_company in company2.filtered(lambda x: x.id != company.id):
                if ((similar_company.name and company.name and similar_company.name.upper() in company.name.upper()) or \
                            (
                                            similar_company.name and company.name and company.name.upper() in similar_company.name.upper()) or \
                            (company.phone == similar_company.phone and company.phone and similar_company.phone) or \
                            (
                                            company.email and similar_company.email and company.email.upper() == similar_company.email.upper())):
                    company_obj += similar_company

            print(company_obj)
            company.simliar_companys = company_obj
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"查重完成",
                "text": u"查重完成",
                "sticky": False
            }
        }

    # 批量改变产品的所属公司 DIY系统用  id: 131, 132
    def action_change_product_company(self):
        ps = self.env["product.template"].search([('categ_id', 'in', [131, 132])])
        ps.write({
            'company_id': 3,
        })

    def login(self, driver, loginurl, username=None, password=None):
        # open the login in page
        driver.get(loginurl)
        try:
            driver.find_element_by_xpath('//*[@id="account-login"]').click()
        except:
            print u'京东登录界面出现改版,需要把用户登陆界面切换出来'
        time.sleep(3)
        # sign in the username

        # 由于京东中使用frame来再次加载一个网页，所以，在选择元素的时候会出现选择不到的结果，所以，我们需要把视图窗口切换到frame中
        driver.switch_to.frame(u'loginFrame')

        def login_name():
            try:
                # driver.find_element_by_xpath('//*[@id="loginname"]').click()
                time.sleep(3)
                driver.find_element_by_xpath('//*[@id="loginname"]').clear()
                # driver.find_element_by_xpath('//*[@id="TPL_username_1"]').send_keys(u'若态旗舰店')
                driver.find_element_by_xpath('//*[@id="loginname"]').send_keys(username)
                print 'user success!'
            except:
                print 'user error!'
            time.sleep(3)

        def login_password():
            # sign in the pasword
            try:
                driver.find_element_by_xpath('//*[@id="nloginpwd"]').clear()
                # driver.find_element_by_xpath('//*[@id="TPL_password_1"]').send_keys('szrtkjqjd@123!!')
                driver.find_element_by_xpath('//*[@id="nloginpwd"]').send_keys(password)
                print 'pw success!'
            except:
                print 'pw error!'
            time.sleep(3)

        def click_and_login():
            # click to login
            try:
                driver.find_element_by_xpath('//*[@id="paipaiLoginSubmit"]').click()
                print 'click success!'
            except:
                print 'click error!'
            time.sleep(3)

        login_name()
        login_password()
        click_and_login()

    def compute_sale_qty(self):

        this_month = datetime.datetime.now().month
        last1_month = this_month - 1
        date1_start, date1_end = getMonthFirstDayAndLastDay(month=last1_month)
        date2_start, date2_end = getMonthFirstDayAndLastDay(month=last1_month, period=2)
        date3_start, date3_end = getMonthFirstDayAndLastDay(month=last1_month, period=5)
        products = self.env['product.template'].search([('sale_ok', '=', True)])
        for product in products:
            if product.product_variant_ids:
                product_id = product.product_variant_ids[0]
                last1_month_qty = product_id.count_amount(date1_start, date1_end)
                last2_month_qty = product_id.count_amount(date2_start, date2_end)
                last3_month_qty = product_id.count_amount(date3_start, date3_end)
                product.last1_month_qty = last1_month_qty
                product.last2_month_qty = last2_month_qty
                product.last3_month_qty = last3_month_qty

    def recompute_po_chager(self):
        pos = self.env["purchase.order"].search([])
        for po in pos:
            po.user_id = po.create_uid.id

    def compute_product_sale_situtaion(self):
        today_time, timez = self.get_today_time_and_tz()
        today_time = fields.datetime.strptime(fields.datetime.strftime(today_time, '%Y-%m-%d'), '%Y-%m-%d')
        today_time -= timez
        # today_time = fields.datetime.strptime(fields.datetime.strftime(fields.datetime.now(), '%Y-%m-%d'),
        #                                       '%Y-%m-%d')
        one_days_after = datetime.timedelta(days=60)
        after_day = today_time - one_days_after

        moves = self.env["stock.move"].search([("create_date", ">=", after_day.strftime('%Y-%m-%d %H:%M:%S'))])
        group_list = self.env["stock.move"].read_group([("create_date", ">=", after_day.strftime('%Y-%m-%d %H:%M:%S'))],
                                                       fields=["product_id"], groupby=["product_id"])
        ids = []
        for group in group_list:
            ids.append(group["product_id"][0])

        all_products = self.env["product.product"].search([])
        all_products.write({
            'is_move_in_recent': False
        })
        products = self.env["product.product"].browse(ids)
        products.write({
            "is_move_in_recent": True
        })
        print(moves)

        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"计算完成",
                "text": u"计算完成",
                "sticky": False
            }
        }

    def update_product_categ_menu(self):
        categ_ids = self.env['product.category'].search([])
        for c in categ_ids:
            if c.menu_id.action:
                _logger.warning("update menu action list, %d/%d" % (c.id, c.menu_id.id))
                c.menu_id.action.domain = '[["categ_id", "child_of", %d]]' % int(c.id)

    def mo_to_bz_process(self):
        return
        mos = self.env["mrp.production"].search([('process_id', '=', False)])
        mos.write({
            'process_id': 26,
        })
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": str(len(mos)) + u"完成",
                "text": u"完成",
                "sticky": False
            }
        }

    def bom_to_bz_process(self):
        mos = self.env["mrp.production"].search([('process_id', '=', 26)])
        for mo in mos:
            mo.write({
                'in_charge_id': mo.process_id.partner_id.id,
            })
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": str(len(mos)) + u"完成",
                "text": u"完成",
                "sticky": False
            }
        }

    def get_today_time_and_tz(self):
        if self.env.user.tz:
            timez = fields.datetime.now(pytz.timezone(self.env.user.tz)).tzinfo._utcoffset
            date_to_show = fields.datetime.utcnow()
            date_to_show += timez
            return date_to_show, timez
        else:
            raise UserError("未找到对应的时区, 请点击 右上角 -> 个人资料 -> 时区 -> Asia/Shanghai")

    # 设置已完成的mo的库存移动没有完成或者取消的问题
    def set_done_mo_to_done(self):
        MrpProduction = self.env["mrp.production"]
        mos = MrpProduction.search([("state", "=", "cancel")])
        mos_to_do = self.env["mrp.production"]
        for mo in mos:
            if mo.move_raw_ids.filtered(lambda x: x.state not in ["done", "cancel"]):
                mos_to_do += mo
            if mo.move_finished_ids.filtered(
                    lambda x: x.state not in ["done", "cancel"]) and mo.qc_feedback_ids.filtered(
                    lambda x: x.state in ["alredy_post_inventory", "check_to_rework"]):
                mos_to_do += mo
        mos_to_do.write({
            'state': 'done'
        })
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": str(len(mos_to_do)) + u"完成",
                "text": u"完成",
                "sticky": False
            }
        }




















def getMonthFirstDayAndLastDay(year=None, month=None, period=None):
    """
    :param year: 年份，默认是本年，可传int或str类型
    :param month: 月份，默认是本月，可传int或str类型
    :return: firstDay: 当月的第一天，datetime.date类型
              lastDay: 当月的最后一天，datetime.date类型
    """
    if year:
        year = int(year)
    else:
        year = datetime.date.today().year
    if not period:
        period = 0
    if month <= 0:
        year = -1
        month = 12 + month
        # 获取当月第一天的星期和当月的总天数
    firstDayWeekDay, monthRange = calendar.monthrange(year, month)

    # 获取当月的第一天
    firstDay = datetime.date(year=year, month=month - period, day=1).strftime('%Y-%m-%d')

    lastDay = datetime.date(year=year, month=month, day=monthRange).strftime('%Y-%m-%d')
    print firstDay, lastDay

    return firstDay, lastDay


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    temp_no = fields.Boolean()
