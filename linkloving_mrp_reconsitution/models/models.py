# -*- coding: utf-8 -*-
# from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        for pack in self.pick_id.pack_operation_ids:
            if cancel_backorder:#如果取消欠单,就扣除剩余的所有数量
                pack.product_id.qty_require -= pack.product_qty
            else:
                if pack.product_qty < pack.qty_done:#如果待办小于已完成 代表多出货
                    pack.product_id.qty_require -= pack.product_qty
                else:
                    pack.product_id.qty_require -= pack.qty_done
        return super(StockBackorderConfirmation, self)._process(cancel_backorder)


class linkloving_product_extend(models.Model):
    _inherit = "product.product"

    qty_require = fields.Float(u"需求数量")

class linkloving_production_extend1(models.Model):
    _inherit = "mrp.production"

    origin_sale_id = fields.Many2one("sale.order", string=u"源销售单据名称")
    origin_mo_id = fields.Many2one("mrp.production", string=u"源生产单据名称")

class linkloving_purchase_order_extend(models.Model):
    _inherit = "purchase.order"

    origin_sale_order_id = fields.Many2one("sale.order", string=u"源销售单据名称")
    origin_mo_id = fields.Many2one("mrp.production", string=u"源生产单据名称")


class linkloving_procurement_order_extend(models.Model):
    _inherit = "procurement.order"

    @api.multi
    def make_mo(self):
        """ Create production orders from procurements """
        res = {}
        Production = self.env['mrp.production']
        for procurement in self:
            ProductionSudo = Production.sudo().with_context(force_company=procurement.company_id.id)
            bom = procurement._get_matching_bom()
            if bom:
                # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
                vals = procurement._prepare_mo_vals(bom)
                if vals["product_qty"] == 0:
                    print("dont need create mo")
                    return {procurement.id : 1}
                production = ProductionSudo.create(vals)
                res[procurement.id] = production.id
                procurement.message_post(body=_("Manufacturing Order <em>%s</em> created.") % (production.name))
            else:
                res[procurement.id] = False
                procurement.message_post(body=_("No BoM exists for this product!"))
        return res
# # class linkloving_mrp_reconsitution(models.Model):
# #     _name = 'linkloving_mrp_reconsitution.linkloving_mrp_reconsitution'
#
# #     name = fields.Char()
# #     value = fields.Integer()
# #     value2 = fields.Float(compute="_value_pc", store=True)
# #     description = fields.Text()
# #
# #     @api.depends('value')
# #     def _value_pc(self):
# #         self.value2 = float(self.
# ) / 100
#
# #需求量
# from odoo.exceptions import UserError
# from odoo.osv import expression
#
# class linkloving_mrp_requirement(models.Model):
#     _name = "mrp.requirement"
#
#     required_qty = fields.Float(u"需求数量")
#     product_id = fields.Many2one("product.product", u"需求产品")
#     state = fields.Selection([("draft", u"草稿"),
#                               ("running",u"运行中"),
#                               ("done", u"完成")], default="draft")
#
#     orign_order = fields.Char(u"源单据")
#     rule_id = fields.Many2one("procurement.rule")
#     location_id = fields.Many2one('stock.location', 'Procurement Location')  # not required because task may create procurements that aren't linked to a location with sale_service
#     route_ids = fields.Many2many(
#         'stock.location.route', 'stock_route_warehouse', 'warehouse_id', 'route_id',
#         'Routes', domain="[('warehouse_selectable', '=', True)]",
#         help='Defaults routes through the warehouse')
#
#     warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
#     partner_dest_id = fields.Many2one('res.partner', 'Customer Address', help="In case of dropshipping, we need to know the destination address more precisely")
#     product_uom = fields.Many2one('product.uom', 'Unit of Measure')
#     company_id = fields.Many2one(
#         'res.company', 'Company',)
#
#     bom_id = fields.Many2one(
#         'mrp.bom', 'Bill of Material',
#         readonly=True, states={'confirmed': [('readonly', False)]},
#         help="Bill of Materials allow you to define the list of required raw materials to make a finished product.")
#
#     date_planned = fields.Datetime(
#         'Scheduled Date', default=fields.Datetime.now,
#         required=True, index=True, track_visibility='onchange')
#
#     @api.multi
#     def run(self, autocommit=False):
#         # TDE FIXME: avoid browsing everything -> avoid prefetching ?
#         for procurement in self:
#             # we intentionnaly do the browse under the for loop to avoid caching all ids which would be resource greedy
#             # and useless as we'll make a refresh later that will invalidate all the cache (and thus the next iteration
#             # will fetch all the ids again)
#             if procurement.state not in ("running", "done"):
#                res = procurement._run()
#                if res:
#                  procurement.write({'state': 'running'})
#         return True
#
#     @api.multi
#     def _run(self):
#         self.ensure_one()
#         all_parent_location_ids = self._find_parent_locations()
#         rule = self._search_suitable_rule([('location_id', 'in', all_parent_location_ids.ids)])
#         self.write({"rule_id" : rule.id})
#         if rule:
#             if rule.action == 'manufacture':#如果是製造就返回製造訂單
#                 return self.make_mo()
#             elif rule.action == 'buy':
#                 return self.make_po()
#
#     def get_actual_require_qty(self):
#         ori_require_qty = self.product_id.require_qty  # 初始需求数量
#         real_require_qty = self.required_qty + self.product_id.require_qty  # 加上本次销售的需求数量
#         stock_qty = self.product_id.qty_available  # 库存数量
#
#         actual_need_qty = 0
#         if ori_require_qty > stock_qty and real_require_qty > stock_qty:  # 初始需求 > 库存  并且 现有需求 > 库存
#             actual_need_qty = self.required_qty
#         elif ori_require_qty <= stock_qty and real_require_qty > stock_qty:
#             actual_need_qty = real_require_qty - stock_qty
#
#         return actual_need_qty
#     @api.multi
#     def make_mo(self):
#         """ Create production orders from procurements """
#         res = {}
#         Production = self.env['mrp.production']
#         for procurement in self:
#             ProductionSudo = Production.sudo().with_context()
#             bom = procurement._get_matching_bom()
#             if bom:
#                 # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
#                 production = ProductionSudo.create(procurement._prepare_mo_vals(bom))
#
#                 bom_explores = bom.explode(self.product_id, self.required_qty)
#                 mrp_requirements = self._create_ro(bom_explores[1], production)
#                 mrp_requirements.run()
#                 res[procurement.id] = production.id
#             else:
#                 res[procurement.id] = False
#         return res
#
#     def _create_ro(self, bom_explode, production_order):
#         company = self.env.user.company_id.id
#         warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
#
#         mrp_requirements = self.env["mrp.requirement"]
#         for bom_line, line_data in bom_explode:
#             requiment = mrp_requirements.create({
#                 "required_qty": line_data.get("qty"),
#                 "product_id": bom_line.product_id.id,
#                 "orign_order": production_order.name,
#                 "state": "draft",
#                 "location_id": warehouse_ids.lot_stock_id.id,
#                 'route_ids': bom_line.product_id.route_ids or [],
#                 'warehouse_id': warehouse_ids.id or False,
#                 # 'partner_dest_id': order_line.order_id.partner_shipping_id.id,
#                 'product_uom': bom_line.product_id.uom_id.id,
#                 'company_id':self.env.user.company_id.id,
#             })
#             mrp_requirements += requiment
#         return mrp_requirements
#     @api.multi
#     def _get_matching_bom(self):
#         """ Finds the bill of material for the product from procurement order. """
#         if self.bom_id:
#             return self.bom_id
#         return self.env['mrp.bom'].with_context(
#             company_id=self.company_id.id, force_company=self.company_id.id
#         )._bom_find(product=self.product_id, picking_type=self.rule_id.picking_type_id)  # TDE FIXME: context bullshit
#
#     @api.multi
#     def make_po(self):
#         cache = {}
#         res = []
#         for procurement in self:
#             suppliers = procurement.product_id.seller_ids.filtered(lambda r: not r.product_id or r.product_id == procurement.product_id)
#             if not suppliers:
#                 continue
#             supplier = suppliers[0]
#             partner = supplier.name
#
#             gpo = procurement.rule_id.group_propagation_option
#             group = (gpo == 'fixed' and procurement.rule_id.group_id) or \
#                     (gpo == 'propagate' and procurement.group_id) or False
#
#             domain = (
#                 ('partner_id', '=', partner.id),
#                 ('state', '=', 'make_by_mrp'),
#                 ('picking_type_id', '=', procurement.rule_id.picking_type_id.id),
#                 ('company_id', '=', procurement.company_id.id),
#                 ('dest_address_id', '=', procurement.partner_dest_id.id))
#             if group:
#                 domain += (('group_id', '=', group.id),)
#
#             if domain in cache:
#                 po = cache[domain]
#             else:
#                 po = self.env['purchase.order'].search([dom for dom in domain])
#                 po = po[0] if po else False
#                 cache[domain] = po
#             if not po:
#                 vals = procurement._prepare_purchase_order(partner)
#                 po = self.env['purchase.order'].create(vals)
#                 cache[domain] = po
#             elif not po.origin or procurement.orign_order not in po.origin.split(', '):
#                 # Keep track of all procurements
#                 if po.origin:
#                     if procurement.orign_order:
#                         po.write({'origin': po.origin + ', ' + procurement.orign_order})
#                     else:
#                         po.write({'origin': po.origin})
#                 else:
#                     po.write({'origin': procurement.orign_order})
#             if po:
#                 res += [procurement.id]
#
#             # Create Line
#             po_line = False
#             for line in po.order_line:
#                 if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
#                     procurement_uom_po_qty = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_po_id)
#                     seller = procurement.product_id._select_seller(
#                         partner_id=partner,
#                         quantity=line.product_qty + procurement_uom_po_qty,
#                         date=po.date_order and po.date_order[:10],
#                         uom_id=procurement.product_id.uom_po_id)
#
#                     price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, line.product_id.supplier_taxes_id, line.taxes_id) if seller else 0.0
#                     if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
#                         price_unit = seller.currency_id.compute(price_unit, po.currency_id)
#
#                     po_line = line.write({
#                         'product_qty': line.product_qty + procurement_uom_po_qty,
#                         'price_unit': price_unit,
#                         'procurement_ids': [(4, procurement.id)]
#                     })
#                     break
#             if not po_line:
#                 vals = procurement._prepare_purchase_order_line(po, supplier)
#                 self.env['purchase.order.line'].create(vals)
#         return res
#
#     def _get_date_planned(self):
#         format_date_planned = fields.Datetime.from_string(self.date_planned)
#         date_planned = format_date_planned - relativedelta(days=self.product_id.produce_delay or 0.0)
#         date_planned = date_planned - relativedelta(days=self.company_id.manufacturing_lead)
#         return date_planned
#
#     def _prepare_mo_vals(self, bom):
#         return {
#             'origin': self.orign_order,
#             'product_id': self.product_id.id,
#             'product_qty': self.get_actual_require_qty(),
#             'product_uom_id': self.product_uom.id,
#             'location_src_id': self.rule_id.location_src_id.id or self.location_id.id,
#             'location_dest_id': self.location_id.id,
#             'bom_id': bom.id,
#             'date_planned_start': fields.Datetime.to_string(self._get_date_planned()),
#             'date_planned_finished': self.date_planned,
#             # 'procurement_group_id': self.group_id.id,
#             'propagate': self.rule_id.propagate,
#             'picking_type_id': self.rule_id.picking_type_id.id or self.warehouse_id.manu_type_id.id,
#             'company_id': self.company_id.id,
#             'state' : 'draft',
#             'process_id': bom.process_id.id,
#             'unit_price': bom.process_id.unit_price,
#             'mo_type': bom.mo_type,
#             'hour_price': bom.hour_price,
#             'in_charge_id': bom.process_id.partner_id.id
#             # 'procurement_ids': [(6, 0, [self.id])],
#         }
#
#     def _search_suitable_rule(self, domain):
#         """ First find a rule among the ones defined on the procurement order
#         group; then try on the routes defined for the product; finally fallback
#         on the default behavior """
#         if self.warehouse_id:
#             domain = expression.AND([['|', ('warehouse_id', '=', self.warehouse_id.id), ('warehouse_id', '=', False)], domain])
#         Pull = self.env['procurement.rule']
#         res = self.env['procurement.rule']
#         if self.route_ids:
#             res = Pull.search(expression.AND([[('route_id', 'in', self.route_ids.ids)], domain]), order='route_sequence, sequence', limit=1)
#         if not res:
#             product_routes = self.product_id.route_ids | self.product_id.categ_id.total_route_ids
#             if product_routes:
#                 res = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
#         if not res:
#             warehouse_routes = self.warehouse_id.route_ids
#             if warehouse_routes:
#                 res = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
#         if not res:
#             res = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)
#         return res
#
#     def _find_parent_locations(self):
#         parent_locations = self.env['stock.location']
#         location = self.location_id
#         while location:
#             parent_locations |= location
#             location = location.location_id
#         return parent_locations
#
#
# class linkloving_mrp_product_extend(models.Model):
#     _inherit = "product.product"
#
#     @api.multi
#     def _compute_requirement_qty(self):
#         for product in self:
#             for req in product.mrp_requirement_ids:
#                 if req.state != "done":
#                     product.require_qty += req.required_qty
#     mrp_requirement_ids = fields.One2many("mrp.requirement", "product_id")
#     require_qty = fields.Float(u"需求数量", compute="_compute_requirement_qty")
#
class linkloving_sale_extend(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self.order_line.set_qty_require()
        return super(linkloving_sale_extend, self).action_confirm()

    def action_cancel(self):
        if self.state == "sale":
            #剪掉需求量
            self.order_line.rollback_qty_require()
class linkloving_sale_order_line_extend(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def rollback_qty_require(self):
        for line in self:
            bom = self.env['mrp.bom'].with_context(
                    company_id=self.env.user.company_id.id, force_company=self.env.user.company_id.id
                    )._bom_find(product=self.product_id)
            boms, lines = bom.explode(line.product_id, line.get_actual_require_qty(line.product_id, line.product_qty), picking_type=bom.picking_type_id)
            line.product_id.qty_require -= line.product_qty #先减少成品需求量,子阶的减不掉, 不知道上次需求量是多少
            def recursion_bom(bom_lines, order_line):
                    for b_line, data in bom_lines:
                        if b_line.product_id.qty_require < data.get("qty"): #如果需求小于这次销售的数量
                            b_line.product_id.qty_require = 0#增加bom的需求量  不是完全添加 得看父阶bom需求量多少
                        else:
                            b_line.product_id.qty_require -= data.get("qty")

                        self.delete_mo_orders_mrp_made(data.get("qty"))
                        self.update_po_ordes_mrp_made(data.get("qty"))

                        print"%s : %d" % (b_line.product_id.name, b_line.product_id.qty_require)
                        child_bom = b_line.child_bom_id
                        if child_bom:
                            boms, lines = child_bom.explode(child_bom.product_id, data.get("qty"), picking_type=child_bom.picking_type_id)
                            recursion_bom(lines, line)
            recursion_bom(lines, line)#递归bom


    def delete_mo_orders_mrp_made(self, qty):# 删除所有由so生成的单据 mo,po..
        if self.order_id:
            mos = self.env["mrp.production"].search([("origin_sale_id", "=", self.order_id.id)])
            for mo in mos:
                if mo.state == "cancel":
                    after_conbine_mo = self.env["mrp.production"].search([("source_mo_id", "=", mo.id)])#找到合并后的mo但
                    if after_conbine_mo.state not in ["draft", "confirmed"]:
                        raise UserError("该单据已经开始进入生产状态")
                    else:
                        qty_wizard = self.env['change.production.qty'].sudo().create({
                                    'mo_id': after_conbine_mo.id,
                                    'product_qty': qty,
                                        })
                        qty_wizard.change_prod_qty()
            mos.action_cancel()#批量取消所有的生产订单
        else:
            raise UserError("重大错误")

    def update_po_ordes_mrp_made(self, qty):
        if self.order_id:
            pos = self.env["purchase.order"].search([("origin", "ilike", self.order_id.name)])
            for po in pos:#SO2017040301269:MO/2017040322133, SO2017040301271:MO/2017040322137,
                for line in po.order_line:
                    if line.product_id == self.order_line.product_id and line.product_uom == self.order_id.product_id.uom_po_id:
                        #找到原有的po_line 减掉数量
                        if line.product_qty > qty:
                            po_line = line.write({
                                'product_qty':  line.product_qty - qty,
                                })
                        else:
                            line.unlink()

    @api.multi
    def set_qty_require(self):
        for line in self:
            bom = self.env['mrp.bom'].with_context(
                    company_id=self.env.user.company_id.id, force_company=self.env.user.company_id.id
                    )._bom_find(product=self.product_id)
            boms, lines = bom.explode(line.product_id, line.get_actual_require_qty(line.product_id, line.product_qty), picking_type=bom.picking_type_id)
            line.product_id.qty_require += line.product_qty #先增加成品需求量
            def recursion_bom(bom_lines, order_line):
                    for b_line, data in bom_lines:
                        real_need = order_line.get_actual_require_qty(b_line.product_id, data.get("qty"))
                        if real_need > 0:
                            b_line.product_id.qty_require += real_need#增加bom的需求量  不是完全添加 得看父阶bom需求量多少
                        print"%s : %d" % (b_line.product_id.name, b_line.product_id.qty_require)
                        child_bom = b_line.child_bom_id
                        if child_bom:
                            boms, lines = child_bom.explode(child_bom.product_id, real_need, picking_type=child_bom.picking_type_id)
                            recursion_bom(lines, line)
            recursion_bom(lines, line)#递归bom

    def get_actual_require_qty(self,product_id, require_qty_this_time):
        ori_require_qty = product_id.qty_require  # 初始需求数量
        real_require_qty = product_id.qty_require + require_qty_this_time   # 加上本次销售的需求数量
        stock_qty = product_id.qty_available  # 库存数量

        actual_need_qty = 0
        if ori_require_qty > stock_qty and real_require_qty > stock_qty:  # 初始需求 > 库存  并且 现有需求 > 库存
            actual_need_qty = require_qty_this_time
        elif ori_require_qty <= stock_qty and real_require_qty > stock_qty:
            actual_need_qty = real_require_qty - stock_qty

        return actual_need_qty
#
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