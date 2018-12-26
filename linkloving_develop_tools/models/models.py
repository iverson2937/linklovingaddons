# -*- coding: utf-8 -*-
import calendar
import json
import logging

import datetime

import pytz
import requests
# from requests.packages.urllib3.exceptions import ConnectionError

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


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    temp_no = fields.Boolean()


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
        # 获取当月第一天的星期和当月的总天数
    firstDayWeekDay, monthRange = calendar.monthrange(year, month)

    if month - period <= 0:
        year = year - 1
        month = 12 + month


    # 获取当月的第一天

    firstDay = datetime.date(year=year, month=month - period, day=1).strftime('%Y-%m-%d')

    print year, month, monthRange
    if month > 12:
        month = month - 12
        year = year + 1
    lastDay = datetime.date(year=year, month=month, day=monthRange).strftime('%Y-%m-%d')
    print firstDay, lastDay

    return firstDay, lastDay


class CreateOrderPointWizard(models.TransientModel):
    _name = "create.order.point"

    def compute_has_bom_line_ids(self):
        products=self.env['product.template'].search([])
        for p in products:
            try:
                line = self.env['mrp.bom.line'].search([('product_id', '=', p.product_variant_ids[0].id)])
                if line:
                    p.has_bom_line_lines = True
                else:
                    p.has_bom_line_lines = False
            except Exception, e:
                p.has_bom_line_lines = False
                _logger.warning("delete, %d-------%s" % (p.id, p.display_name))

    def compute_shipping_date(self):
        sale_orders = self.env['sale.order'].search([('validity_date', '=', False)])
        for order in sale_orders:
            if not order.validity_date:
                order.validity_date = order.confirmation_date

    def compute_period_for_account_move(self):
        periods = self.env['account.period'].search([])
        for move in self.env["account.move"].search([]):
            if not move.period_id:

                for p in periods:
                    if p.date_start < move.date <= p.date_stop:
                        move.period_id = p.id

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

    def check_fiscal_year(self):
        for ex in self.env['hr.expense.sheet'].search([]):
            import calendar
            date1_start, date1_end = getMonthFirstDayAndLastDay(month=1)
            print date1_start
            print date1_end
            if ex.create_date < date1_start:
                print ex.create_date
                ex.fiscal_year_id = 1
            else:
                ex.fiscal_year_id = 2

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
                print last1_month_qty,
                print last2_month_qty,
                print last3_month_qty
                product.last1_month_qty = last1_month_qty
                product.last2_month_qty = last2_month_qty
                product.last3_month_qty = last3_month_qty
        products = self.env['product.template'].search([('purchase_ok', '=', True)])
        for product in products:
            if product.product_variant_ids:
                product_id = product.product_variant_ids[0]
                last1_month_qty = product_id.count_purchase_amount(date1_start, date1_end)
                last2_month_qty = product_id.count_purchase_amount(date2_start, date2_end)
                last3_month_qty = product_id.count_purchase_amount(date3_start, date3_end)
                product.last1_month_consume_qty = last1_month_qty
                product.last3_month_consume_qty = last2_month_qty
                product.last6_month_consume_qty = last3_month_qty

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
                c.menu_id.action.domain = '[["categ_id", "child_of", %d],["active", "=", True]]' % int(c.id)
                c.menu_id.action.context = "{'is_show_procuremnt_create_btn': True}"

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

    @api.multi
    def _set_supplier_product_code(self):
        for line in self:
            seller_ids = line.product_id.product_tmpl_id.seller_ids.filtered(
                lambda x: x.name.id == line.order_id.partner_id.id)
            if seller_ids:
                for info in seller_ids:
                    info.product_code = line.supplier_product_code
            else:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'product_code': line.supplier_product_code,
                    'name': line.order_id.partner_id.id
                })

    def get_compute_product_price(self):
        products = self.env['product.template'].search([('purchase_ok', '=', True)])
        info = self.env['product.supplierinfo']
        dis = self.env['product.price.discount']
        for product in products:
            if product.price1:
                discounts = dis.search([('product_id', '=', product.product_variant_ids[0].id)])
                for r in discounts:
                    infos = info.search([('product_tmpl_id', '=', product.id), ('name', '=', r.partner_id.id)])
                    if infos:
                        print infos[0]
                        if not infos[0].price:
                            infos[0].price = product.price1 * r.price
                    else:
                        if r.partner_id.id:
                            info.create({
                                'product_tmpl_id': product.id,
                                'name': r.partner_id.id,
                                'price': product.price1 * r.price
                            })
            elif product.price1_tax:
                discounts = dis.search([('product_id', '=', product.product_variant_ids[0].id)])
                for r in discounts:
                    infos = info.search([('product_tmpl_id', '=', product.id), ('name', '=', r.partner_id.id)])
                    if infos:
                        if not infos[0].price:
                            infos[0].price = product.price1_tax * r.price_tax
                        print infos[0]
                    else:
                        if r.partner_id.id:
                            info.create({
                                'product_tmpl_id': product.id,
                                'name': r.partner_id.id,
                                'price': product.price1_tax * r.price_tax
                            })

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
        mos = MrpProduction.search([("state", "in", ("done", "cancel"))])
        stock_moves_to_do = self.env["stock.move"]
        finish_stock_moves = self.env["stock.move"]
        for mo in mos:
            raw_stock_moves = mo.move_raw_ids.filtered(lambda x: x.state not in ["done", "cancel"])
            print raw_stock_moves
            if mo.qc_feedback_ids.filtered(
                    lambda x: x.state in ["alredy_post_inventory", "check_to_rework"]):
                finish_stock_moves = mo.move_finished_ids.filtered(
                    lambda x: x.state not in ["done", "cancel"])
            if raw_stock_moves:
                stock_moves_to_do += raw_stock_moves
            if finish_stock_moves:
                stock_moves_to_do += finish_stock_moves
        stock_moves_to_do.write({
            'state': 'cancel'
        })
        for stock in stock_moves_to_do:
            print stock.id
            print stock.production_id.name
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": str(len(stock_moves_to_do)) + u"完成",
                "text": u"完成",
                "sticky": False
            }
        }

    def quantity_done_0(self):
        StockPicking = self.env["stock.picking"]
        pickings = StockPicking.search([("state", "=", "done"), ("picking_type_code", "=", "outgoing")])
        for pick in pickings:
            if pick.pack_operation_product_ids:
                sum_qty_done = sum(pick.pack_operation_product_ids.mapped("qty_done"))
                if sum_qty_done == 0:
                    StockPicking += pick
                    for pack in pick.pack_operation_product_ids:
                        pack.qty_done = pack.product_qty
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": str(len(StockPicking)) + u"完成",
                "text": u"完成",
                "sticky": False
            }
        }

    def backup_standard_price(self):
        for p in self.env["product.template"].search([]):
            p.backup_standard_price = p.standard_price

    def set_product_category_right(self):
        """
        设置产品分类的成本方法  平均价格以及自动
        :return:
        """
        p_gs = self.env["product.category"].search([])
        p_gs.write({
            'property_cost_method': 'average',
            'property_valuation': 'real_time'
        })

    def unlink_useless_supplier_info(self):
        products = self.env['product.template'].search([('purchase_ok', '=', True)])
        for product in products:
            if product.seller_ids:
                for s in product.seller_ids:
                    line = self.env['purchase.order.line'].search(
                        [('product_id', '=', s.product_tmpl_id.product_variant_ids[0].id),
                         ('partner_id', '=', s.name.id),
                         ('state', 'in', ['purchase', 'done'])])
                    if not line and len(product.seller_ids) > 1:
                        _logger.warning("delete, %d-------%s" % (s.id, s.name.name))
                        s.unlink()

    def set_standard_price_from_subcompany(self):
        """
        从子公司回填成本到RT公司
        :return:
        """
        product_tmpl = self.env["product.template"]
        company_info_rober = self.env["sub.company.info"].search([("name", "=", "若贝尔 ")])
        company_info_diy = self.env["sub.company.info"].search([("name", "=", "鲁班DIY")])
        sub_company_rober = self.env["res.partner"].search(
            [("sub_company", "=", "sub"), ("sub_company_id", "=", company_info_rober.id)])  # 子公司鲁 2.4的地址
        sub_company_diy = self.env["res.partner"].search(
            [("sub_company", "=", "sub"), ("sub_company_id", "=", company_info_diy.id)])  # 子公司

        products = product_tmpl.search([])

        products_from_rober = products.filtered(lambda x: x.seller_ids.mapped("name") in sub_company_rober)
        products_from_diy = products.filtered(lambda x: x.seller_ids.mapped("name") in sub_company_diy)
        response = None
        if products_from_rober:
            url, db, header = company_info_rober.get_request_info('/linkloving_web/get_stand_price')
            response = self.request_to_get_stand_price(url, db, header, products_from_rober.mapped("default_code"))

        if products_from_diy:
            url, db, header = company_info_diy.get_request_info('/linkloving_web/get_stand_price')
            response = self.request_to_get_stand_price(url, db, header, products_from_rober.mapped("default_code"))

        if response:
            vals = response.get("vals")
            for val in vals:
                p = product_tmpl.search([("default_code", "=", val.get("default_code"))])
                p.standard_price = val["price_unit"]
        else:
            raise UserError(u"未收到返回")

    def request_to_get_stand_price(self, url, db, header, codes):
        try:
            response = requests.post(url, data=json.dumps({
                "db": db,
                "vals": codes
            }), headers=header)
            return self.handle_response(response)
        except Exception:
            raise UserError(u"请求地址错误, 请确认")

    def handle_response(self, response):
        res_json = json.loads(response.content).get("result")
        res_error = json.loads(response.content).get("error")
        if res_json and res_json.get("code") < 0:
            raise UserError(res_json.get("msg"))
        if res_error:
            raise UserError(res_error.get("data").get("message"))
        return res_json

    def huansuan_speed(self):
        """
        换算生产速度 ---
        :return:
        """
        for bom in self.env["mrp.bom"].search([]):
            if bom.produced_spend_per_pcs != 0:
                if bom.produce_speed_factor == 'human':
                    bom.amount_of_producer = bom.theory_factor if bom.theory_factor else 1
                    bom.produced_speed_per_hour = bom.amount_of_producer * 3600 / bom.produced_spend_per_pcs
                else:
                    bom.amount_of_producer = 1
                    bom.produced_speed_per_hour = bom.amount_of_producer * 3600 / bom.produced_spend_per_pcs
