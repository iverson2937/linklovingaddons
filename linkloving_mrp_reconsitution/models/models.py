# -*- coding: utf-8 -*-
# from dateutil.relativedelta import relativedelta
from collections import defaultdict

from psycopg2._psycopg import OperationalError
import logging

_logger = logging.getLogger(__name__)

from odoo import models, fields, api, _, registry
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare, float_round, DEFAULT_SERVER_DATETIME_FORMAT


class linkloving_product_extend(models.Model):
    _inherit = "product.product"

    qty_require = fields.Float(u"需求数量")
    is_trigger_by_so = fields.Boolean(default=False)


class linkloving_product_product_extend(models.Model):
    _inherit = "product.template"

    qty_require = fields.Float(related="product_variant_id.qty_require")
    is_trigger_by_so = fields.Boolean(default=False, related="product_variant_id.is_trigger_by_so")


class linkloving_production_extend1(models.Model):
    _inherit = "mrp.production"

    origin_sale_id = fields.Many2one("sale.order", string=u"源销售单据名称")
    origin_mo_id = fields.Many2one("mrp.production", string=u"源生产单据名称")

    @api.model
    def create(self, vals):
        return super(linkloving_production_extend1, self).create(vals)


class linkloving_purchase_order_extend(models.Model):
    _inherit = "purchase.order"

    origin_sale_id = fields.Many2one("sale.order", string=u"源销售单据名称")
    origin_mo_id = fields.Many2one("mrp.production", string=u"源生产单据名称")


class linkloving_procurement_order_extend(models.Model):
    _inherit = "procurement.order"

    def _search_suitable_rule_new(self, product_id, domain):
        """ First find a rule among the ones defined on the procurement order
        group; then try on the routes defined for the product; finally fallback
        on the default behavior """
        if self.get_warehouse():
            domain = expression.AND(
                [['|', ('warehouse_id', '=', self.get_warehouse().id), ('warehouse_id', '=', False)], domain])
        Pull = self.env['procurement.rule']
        res = self.env['procurement.rule']
        if product_id.route_ids:
            res = Pull.search(expression.AND([[('route_id', 'in', product_id.route_ids.ids)], domain]),
                              order='route_sequence, sequence', limit=1)
        if not res:
            product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
            if product_routes:
                res = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                                  order='route_sequence, sequence', limit=1)
        if not res:
            warehouse_routes = self.get_warehouse().route_ids
            if warehouse_routes:
                res = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                  order='route_sequence, sequence', limit=1)
        if not res:
            res = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)
        return res

    def get_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse_ids

    def _find_parent_locations_new(self):
        parent_locations = self.env['stock.location']
        location = self.get_warehouse().lot_stock_id
        while location:
            parent_locations |= location
            location = location.location_id
        return parent_locations

    def get_suitable_rule(self, product_id):
        all_parent_location_ids = self._find_parent_locations_new()
        rule = self._search_suitable_rule_new(product_id, [('location_id', 'in', all_parent_location_ids.ids)])
        return rule

    def get_actual_require_qty_with_param(self, product_id, require_qty_this_time):
        actual_need_qty = 0

        rule = self.get_suitable_rule(product_id)

        if rule.action == "manufacture":
            if rule.procure_method == "make_to_order":
                ori_require_qty = product_id.qty_require  # 初始需求数量
                real_require_qty = product_id.qty_require + require_qty_this_time  # 加上本次销售的需求数量
                stock_qty = product_id.qty_available  # 库存数量

                if ori_require_qty > stock_qty and real_require_qty > stock_qty:  # 初始需求 > 库存  并且 现有需求 > 库存
                    actual_need_qty = require_qty_this_time
                elif ori_require_qty <= stock_qty and real_require_qty > stock_qty:
                    actual_need_qty = real_require_qty - stock_qty
            else:
                product_id.is_trigger_by_so = True
                xuqiul = product_id.qty_require + require_qty_this_time
                OrderPoint = self.env['stock.warehouse.orderpoint'].search([("product_id", "=", product_id.id)],
                                                                           limit=1)
                qty = xuqiul + OrderPoint.product_min_qty - product_id.qty_available
                mos = self.env["mrp.production"].search(
                    [("product_id", "=", product_id.id), ("state", "not in", ("cancel", "done"))])
                qty_in_procure = 0
                for mo in mos:
                    qty_in_procure += mo.product_qty
                if qty - qty_in_procure > 0:  # 需求量+最小存货-库存-在产数量
                    actual_need_qty = xuqiul + max(OrderPoint.product_min_qty,
                                                   OrderPoint.product_max_qty) - product_id.qty_available - qty_in_procure

        elif rule.action == "buy":
            xuqiul = product_id.qty_require + require_qty_this_time
            pos = self.env["purchase.order"].search([("state", "=", ("make_by_mrp", "draft"))])
            chose_po_lines = self.env["purchase.order.line"]
            total_draft_order_qty = 0
            for po in pos:
                for po_line in po.order_line:
                    if po_line.product_id.id == product_id.id:
                        chose_po_lines += po_line
                        total_draft_order_qty += po_line.product_qty
                        break
            if total_draft_order_qty + product_id.incoming_qty + product_id.qty_available - xuqiul < 0:
                actual_need_qty = xuqiul - (total_draft_order_qty + product_id.incoming_qty + product_id.qty_available)

        return actual_need_qty

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id=False):
        """ Create procurements based on orderpoints.
        :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
        """
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))

        OrderPoint = self.env['stock.warehouse.orderpoint']
        Procurement = self.env['procurement.order']
        ProcurementAutorundefer = Procurement.with_context(procurement_autorun_defer=True)
        procurement_list = []

        orderpoints_noprefetch = OrderPoint.with_context(prefetch_fields=False).search(
            company_id and [('company_id', '=', company_id), ('active', '=', True)] or [('active', '=', True)],
            order=self._procurement_from_orderpoint_get_order())
        new_mrp_report = self.env["mrp.report"]
        exception_happend = False
        if len(orderpoints_noprefetch) != 0:
            new_mrp_report = new_mrp_report.create({
                'total_orderpoint_count': len(orderpoints_noprefetch),
            })
            report_line_obj = self.env["mrp.report.product.line"]
        while orderpoints_noprefetch:
            orderpoints = OrderPoint.browse(orderpoints_noprefetch[:1000].ids)
            orderpoints_noprefetch = orderpoints_noprefetch[1000:]
            orderpoint_need_recal = self.env['stock.warehouse.orderpoint']
            # Calculate groups that can be executed together
            location_data = defaultdict(
                lambda: dict(products=self.env['product.product'], orderpoints=self.env['stock.warehouse.orderpoint'],
                             groups=list()))
            for orderpoint in orderpoints:
                key = self._procurement_from_orderpoint_get_grouping_key([orderpoint.id])
                location_data[key]['products'] += orderpoint.product_id
                location_data[key]['orderpoints'] += orderpoint
                location_data[key]['groups'] = self._procurement_from_orderpoint_get_groups([orderpoint.id])

            for location_id, location_data in location_data.iteritems():
                location_orderpoints = location_data['orderpoints']
                product_context = dict(self._context, location=location_orderpoints[0].location_id.id)
                substract_quantity = location_orderpoints.subtract_procurements_from_orderpoints()

                for group in location_data['groups']:
                    if group['to_date']:
                        product_context['to_date'] = group['to_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    product_quantity = location_data['products'].with_context(product_context)._product_available()
                    for orderpoint in location_orderpoints:
                        try:
                            op_product_virtual = product_quantity[orderpoint.product_id.id]['virtual_available']
                            if op_product_virtual is None:
                                continue
                            if float_compare(op_product_virtual, orderpoint.product_min_qty,
                                             precision_rounding=orderpoint.product_uom.rounding) <= 0:
                                new_procurement = ProcurementAutorundefer
                                qty = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - op_product_virtual
                                remainder = orderpoint.qty_multiple > 0 and qty % orderpoint.qty_multiple or 0.0

                                if float_compare(remainder, 0.0,
                                                 precision_rounding=orderpoint.product_uom.rounding) > 0:
                                    qty += orderpoint.qty_multiple - remainder

                                if float_compare(qty, 0.0, precision_rounding=orderpoint.product_uom.rounding) < 0:
                                    continue
                                qty -= substract_quantity[orderpoint.id]
                                qty_rounded = float_round(qty, precision_rounding=orderpoint.product_uom.rounding)
                                rule = self.get_suitable_rule(orderpoint.product_id)
                                if rule.action == "buy":
                                    total_draft_order_qty = self.get_draft_po_qty(orderpoint.product_id)
                                    qty_rounded -= total_draft_order_qty
                                if qty_rounded > 0:
                                    new_procurement = ProcurementAutorundefer.create(
                                        orderpoint._prepare_procurement_values(qty_rounded,
                                                                               **group['procurement_values']))
                                    procurement_list.append(new_procurement)
                                    new_procurement.message_post_with_view('mail.message_origin_link',
                                                                           values={'self': new_procurement,
                                                                                   'origin': orderpoint},
                                                                           subtype_id=self.env.ref('mail.mt_note').id)
                                    self._procurement_from_orderpoint_post_process([orderpoint.id])
                                if use_new_cursor:
                                    cr.commit()
                                if new_mrp_report and new_procurement:
                                    report_line_obj.create(new_mrp_report.prepare_report_line_val(new_procurement,
                                                                                                  report_id=new_mrp_report,
                                                                                                  orderpoint_id=orderpoint,
                                                                                                  order_qty=qty_rounded))
                            # orderpoint.active = False  # 运算完补货规则之后,将补货规则设置成无效
                            if new_mrp_report:
                                new_mrp_report.report_end_time = fields.Datetime.now()  # 刷新最后记录时间
                        except OperationalError:
                            exception_happend = True
                            if use_new_cursor:
                                orderpoints_noprefetch += orderpoint.id
                                cr.rollback()
                                continue
                            else:
                                raise

            try:
                # TDE CLEANME: use record set ?
                procurement_list.reverse()
                procurements = self.env['procurement.order']
                for p in procurement_list:
                    procurements += p
                procurements.run()
                if use_new_cursor:
                    cr.commit()
            except OperationalError:
                exception_happend = True
                if use_new_cursor:
                    cr.rollback()
                    continue
                else:
                    raise

            if use_new_cursor:
                cr.commit()
        if new_mrp_report and not exception_happend:
            new_mrp_report.state = 'done'
            new_mrp_report.note = u"运行补货规则,但是无需要备货的条目"
        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}

    @api.multi
    def make_mo(self):
        """ Create production orders from procurements """
        res = {}
        Production = self.env['mrp.production']
        for procurement in self:
            ProductionSudo = Production.sudo().with_context(force_company=procurement.company_id.id)
            bom = procurement._get_matching_bom()
            if bom:
                # create the MO as SUPERUSER because the current user may not have the rights to do it
                # (mto product launched by a sale for example)
                vals = procurement._prepare_mo_vals(bom)
                _logger.warning("dont need create mo, %d-------%s" % (vals.get('product_id'), vals.get('product_qty')))
                if float_compare(vals["product_qty"], 0.0, precision_rounding=0.00001) <= 0:
                    print("dont need create mo")
                    return {procurement.id: 1}
                production = ProductionSudo.create(vals)
                res[procurement.id] = production.id
                procurement.message_post(body=_("Manufacturing Order <em>%s</em> created.") % (production.name))
            else:
                res[procurement.id] = False
                procurement.message_post(body=_("No BoM exists for this product!"))
        return res


class linkloving_sale_extend(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self.ensure_one()
        # 产生销售单时 根据销售单客户 更改客户 订单状态
        self.partner_id.is_order = True
        self.partner_id.crm_is_partner = False
        for line in self.order_line:
            if self.env.ref(
                    "mrp.route_warehouse0_manufacture") in line.product_id.route_ids and not line.product_id.bom_ids:
                raise UserError(u"%s 未找到对应的Bom" % line.product_id.display_name)
                # if line.product_id.bom_ids[0].state not in ('draft', 'release'):
                #     raise UserError(u"%s Bom未通过审核" % line.product_id.display_name)
        return super(linkloving_sale_extend, self).action_confirm()

    def action_cancel(self):
        # if self.state == "sale":
        # 剪掉需求
        # self.order_line.rollback_qty_require()
        return super(linkloving_sale_extend, self).action_cancel()


class linkloving_sale_order_line_extend(models.Model):
    _inherit = "sale.order.line"

    def _search_suitable_rule(self, product_id, domain):
        """ First find a rule among the ones defined on the procurement order
        group; then try on the routes defined for the product; finally fallback
        on the default behavior """
        if self.get_warehouse():
            domain = expression.AND(
                [['|', ('warehouse_id', '=', self.get_warehouse().id), ('warehouse_id', '=', False)], domain])
        Pull = self.env['procurement.rule']
        res = self.env['procurement.rule']
        if product_id.route_ids:
            res = Pull.search(expression.AND([[('route_id', 'in', product_id.route_ids.ids)], domain]),
                              order='route_sequence, sequence', limit=1)
        if not res:
            product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
            if product_routes:
                res = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                                  order='route_sequence, sequence', limit=1)
        if not res:
            warehouse_routes = self.get_warehouse().route_ids
            if warehouse_routes:
                res = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                  order='route_sequence, sequence', limit=1)
        if not res:
            res = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)
        return res

    def get_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse_ids

    def _find_parent_locations(self):
        parent_locations = self.env['stock.location']
        location = self.get_warehouse().lot_stock_id
        while location:
            parent_locations |= location
            location = location.location_id
        return parent_locations

    def get_suitable_rule(self, product_id):
        all_parent_location_ids = self._find_parent_locations()
        rule = self._search_suitable_rule(product_id, [('location_id', 'in', all_parent_location_ids.ids)])
        return rule

    @api.multi
    def rollback_qty_require(self):
        for line in self:
            line.update_po_ordes_mrp_made()

    def update_po_ordes_mrp_made(self):
        if self.order_id:
            pos = self.env["purchase.order"].search([("origin", "ilike", self.order_id.name)])
            for po in pos:  # SO2017040301269:MO/2017040322133, SO2017040301271:MO/2017040322137,
                for line in po.order_line:
                    yl_list = self.get_boms()  # 原材料
                    for yl in yl_list:
                        if line.product_id.id == yl.get("product_id").id:
                            # 找到原有的po_line 减掉数量
                            if line.product_qty > yl.get("qty"):
                                po_line = line.write({
                                    'product_qty': line.product_qty - yl.get("qty"),
                                })
                            else:
                                try:
                                    line.unlink()
                                except UserError, e:
                                    raise UserError(u"'%s' 订单中含有产品未设置供应商不能删除" % po.name)

    def get_boms(self):
        self.ensure_one()
        bom = self.env['mrp.bom'].with_context(
            company_id=self.env.user.company_id.id, force_company=self.env.user.company_id.id
        )._bom_find(product=self.product_id)
        boms, lines = bom.explode(self.product_id, self.product_qty, picking_type=bom.picking_type_id)
        yl_list = []

        def recursion_bom(bom_lines, order_line, yl_list):
            for b_line, data in bom_lines:
                child_bom = b_line.child_bom_id
                if b_line.product_id:
                    yl_list.append({"product_id": b_line.product_id, "qty": data.get("qty")})
                if child_bom:
                    boms, lines = child_bom.explode(child_bom.product_id, data.get("qty"),
                                                    picking_type=child_bom.picking_type_id)
                    recursion_bom(lines, order_line, yl_list)

        recursion_bom(lines, self, yl_list)  # 递归bom
        return yl_list

    def get_actual_require_qty(self, product_id, require_qty_this_time):
        actual_need_qty = 0

        rule = self.get_suitable_rule(product_id)

        if rule.action == "manufacture":
            if rule.procure_method == "make_to_order":
                ori_require_qty = product_id.qty_require  # 初始需求数量
                real_require_qty = product_id.qty_require + require_qty_this_time  # 加上本次销售的需求数量
                stock_qty = product_id.qty_available  # 库存数量

                if ori_require_qty > stock_qty and real_require_qty > stock_qty:  # 初始需求 > 库存  并且 现有需求 > 库存
                    actual_need_qty = require_qty_this_time
                elif ori_require_qty <= stock_qty and real_require_qty > stock_qty:
                    actual_need_qty = real_require_qty - stock_qty
            else:
                product_id.is_trigger_by_so = True
                xuqiul = product_id.qty_require + require_qty_this_time
                OrderPoint = self.env['stock.warehouse.orderpoint'].search([("product_id", "=", product_id.id)],
                                                                           limit=1)
                qty = xuqiul + OrderPoint.product_min_qty - product_id.qty_available
                mos = self.env["mrp.production"].search(
                    [("product_id", "=", product_id.id), ("state", "not in", ("cancel", "done"))])
                qty_in_procure = 0
                for mo in mos:
                    qty_in_procure += mo.product_qty
                if qty - qty_in_procure > 0:  # 需求量+最小存货-库存-在产数量
                    actual_need_qty = xuqiul + max(OrderPoint.product_min_qty,
                                                   OrderPoint.product_max_qty) - product_id.qty_available - qty_in_procure

        elif rule.action == "buy":
            xuqiul = product_id.qty_require + require_qty_this_time
            pos = self.env["purchase.order"].search([("state", "=", ("make_by_mrp", "draft"))])
            chose_po_lines = self.env["purchase.order.line"]
            total_draft_order_qty = 0
            for po in pos:
                for po_line in po.order_line:
                    if po_line.product_id.id == product_id.id:
                        chose_po_lines += po_line
                        total_draft_order_qty += po_line.product_qty
                        break
            if total_draft_order_qty + product_id.incoming_qty + product_id.qty_available - xuqiul < 0:
                actual_need_qty = xuqiul - (total_draft_order_qty + product_id.incoming_qty + product_id.qty_available)

        return actual_need_qty

        #
        #     @api.multi
        #     def _create_requirement_order(self):
        #         ret = []
        #         for order_line in self:
        #             requiment = self.env["mrp.requirement"].create({
        #                     "required_qty" : order_line.product_uom_qty,
        #                     "product_id" : order_line.product_id.id,
        #                     "orign_order" : order_line.order_id.name,
        #                     "state" : "draft",
        #                     "location_id" : order_line.order_id.warehouse_id.lot_stock_id.id,
        #                     'route_ids': order_line.route_id and [(4, order_line.route_id.id)] or [],
        #                     'warehouse_id': order_line.order_id.warehouse_id and order_line.order_id.warehouse_id.id or False,
        #                     'partner_dest_id': order_line.order_id.partner_shipping_id.id,
        #                     'product_uom': order_line.product_uom.id,
        #                     'company_id': order_line.order_id.company_id.id,
        #                 })
        #             ret.append(requiment)
        #
        #         return ret
