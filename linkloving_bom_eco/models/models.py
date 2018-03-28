# -*- coding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        res = super(ProcurementOrderExtend, self).make_po()

        return res

    @api.multi
    def make_mo(self):
        res = super(ProcurementOrderExtend, self).make_mo()

        return res

    @api.multi
    def require_reduced(self):  # 级联减少需求
        propagated_procurements = self.filtered(lambda order: order.state != 'done').propagate_reduced()
        propagated_procurements.propagate_reduced()

    @api.multi
    def propagate_reduced(self):
        reduce_man_orders = self.filtered(
            lambda procurement: procurement.rule_id.action == 'manufacture' and procurement.production_id).mapped(
            'production_id')
        if reduce_man_orders:
            reduce_man_orders.require_reduced()
        for procurement in self:
            if procurement.rule_id.action == 'buy' and procurement.purchase_line_id:
                if procurement.purchase_line_id.order_id.state in ['purchase', 'done']:
                    continue
                    # if procurement.purchase_line_id.order_id.state not in ('make_by_mrp', 'draft', 'cancel', 'sent', 'to validate'):
                    #     raise UserError(
                    #         _('Can not cancel a procurement related to a purchase order. Please cancel the purchase order first.') + ('%s' % procurement.id))
            if procurement.purchase_line_id.order_id.state == 'make_by_mrp' and procurement.purchase_line_id:
                price_unit = 0.0
                product_qty = 0.0
                others_procs = procurement.purchase_line_id.procurement_ids.filtered(lambda r: r != procurement)
                for other_proc in others_procs:
                    if other_proc.state not in ['cancel', 'draft']:
                        product_qty += other_proc.product_uom._compute_quantity(other_proc.product_qty,
                                                                                procurement.purchase_line_id.product_uom)

                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if not float_is_zero(product_qty, precision_digits=precision):
                    seller = procurement.product_id._select_seller(
                            partner_id=procurement.purchase_line_id.partner_id,
                            quantity=product_qty,
                            date=procurement.purchase_line_id.order_id.date_order and procurement.purchase_line_id.order_id.date_order[
                                                                                      :10],
                            uom_id=procurement.purchase_line_id.product_uom)

                    price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                                 procurement.purchase_line_id.product_id.supplier_taxes_id,
                                                                                 procurement.purchase_line_id.taxes_id) if seller else 0.0
                    if price_unit and seller and procurement.purchase_line_id.order_id.currency_id and seller.currency_id != procurement.purchase_line_id.order_id.currency_id:
                        price_unit = seller.currency_id.compute(price_unit,
                                                                procurement.purchase_line_id.order_id.currency_id)

                    if seller and seller.product_uom != procurement.purchase_line_id.product_uom:
                        price_unit = seller.product_uom._compute_price(price_unit,
                                                                       procurement.purchase_line_id.product_uom)

                    procurement.purchase_line_id.product_qty = product_qty
                    procurement.purchase_line_id.price_unit = price_unit
                else:
                    procurement.purchase_line_id.unlink()


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def adjust_move_procure_method(self):
        """
        调整stock move的补货规则,  系统默认创建_generate_moves的时候, 补货规则是 MTS,
        调整是根据 产品的属性,来找到对应的补货规则,来调整的,
        :return:
        """
        try:
            mto_route = self.env['stock.warehouse']._get_mto_route()
        except:
            mto_route = False

        for move in self:
            product = move.product_id
            routes = product.route_ids + product.route_from_categ_ids
            # TODO: optimize with read_group?
            pull = self.env['procurement.rule'].search(
                    [('route_id', 'in', [x.id for x in routes]), ('location_src_id', '=', move.location_id.id),
                     ('location_id', '=', move.location_dest_id.id)], limit=1)
            if pull and (pull.procure_method == 'make_to_order'):
                move.procure_method = pull.procure_method
            elif not pull:  # If there is no make_to_stock rule either
                if mto_route and mto_route.id in [x.id for x in routes]:
                    move.procure_method = 'make_to_order'


class MrpProductionExtend(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    @api.depends("bom_id")
    def _compute_bom_version(self):
        for mo in self:
            mo.bom_version = mo.bom_id.version or 1

    bom_version = fields.Integer(u"BOM版本号", compute="_compute_bom_version", store=True)

    @api.multi
    def reduce_required(self, bom_line_id=None, line_data=None):
        """
        减少需求量 MO
        :param bom_line_id:
        :param line_data:
        :return:
        """
        self.ensure_one()
        if not bom_line_id and not line_data:
            pass
        move = self._update_raw_move(bom_line_id, line_data)  # 在获取完应该补充的qty之后,再更新mo的rawmove 重要!
        if move:
            procurements = self.env["procurement.order"].search([('move_dest_id', '=', move)])
            if procurements:
                procurements.require_reduced()

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    version = fields.Integer(u'版本号', default=1)


class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    bom_line_ids = fields.One2many('mrp.bom.line', 'product_id')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        index = 0
        is_enter_special = False
        for arg in args:  # 特殊处理
            if arg[0] == 'bom_line_ids.bom_id':
                product_ids = self.env["mrp.bom.line"].search([("bom_id", '=', arg[2])]).mapped("product_id")
                idx = index
                if arg[1] == '!=':
                    # 过滤的时候需要不包含本bom的产品
                    product_ids += self.env["mrp.bom"].browse(arg[2]).product_tmpl_id.product_variant_id
                    arg = ['id', 'not in', product_ids.ids]
                else:
                    arg = ['id', 'in', product_ids.ids]
                is_enter_special = True
                break
            index += 1
        if is_enter_special:
            args[idx] = arg

        return super(ProductProductExtend, self).name_search(name, args, operator, limit)


class MrpEcoOrder(models.Model):
    _name = 'mrp.eco.order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = u"变更单"
    _order = 'create_date desc'

    name = fields.Char(u'单号', copy=False, required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', u'负责人', default=lambda self: self.env.user)
    effectivity = fields.Selection([
        ('asap', u'立即'),
        ('date', u'根据时间')], string=u'何时生效?',  # Is this English ?
            default='asap', required=True)  # TDE: usefull ?

    effectivity_date = fields.Datetime(u'生效时间', track_visibility="onchange")
    eco_line_ids = fields.One2many(comodel_name="mrp.eco.line",
                                   inverse_name="eco_order_id",
                                   string=u"变更明细行", track_visibility="onchange"
                                   )

    state = fields.Selection([
        ('draft', u'草稿'),
        ('progress', u'等待至选定日生效'),
        ('done', u'完成')], string=u'状态',
            copy=False, default='draft', required=True, track_visibility="onchange")
    note = fields.Text(u'备注')

    bom_eco_ids = fields.One2many(comodel_name="mrp.bom.eco",
                                  inverse_name="eco_order_id",
                                  string=u"变更的BOM", )

    bom_eco_count = fields.Integer(string=u'变更的BOM单据数量', compute='_compute_bom_eco_count')
    eco_effect_line_ids = fields.One2many(comodel_name='eco.effect.line', inverse_name='eco_order_id')

    @api.multi
    def _compute_bom_eco_count(self):
        for eco in self:
            eco.bom_eco_count = len(eco.bom_eco_ids)

    @api.multi
    def action_change_apply(self):
        self.action_change_apply1()

    @api.multi
    def action_change_apply1(self):
        self.ensure_one()
        # for eco in self:
        if self.effectivity == 'asap':
            new_bom_ecos = self.make_mrp_bom_ecos()
            new_bom_ecos.apply_to_bom()
            new_bom_ecos.apply_bom_update()  # 应用 更新至MO
            msg = "应用成功,已生成报告并通知到相关人员"
        elif self.effectivity == 'date':
            self.state == 'progress'
            msg = "设置成功, 将于指定日期生效"

        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"设置成功",
                "text": msg,
                "sticky": False
            }
        }

    @api.model
    def create(self, vals):
        prefix = self.env['ir.sequence'].next_by_code('mrp.eco.order') or ''
        vals['name'] = '%s%s' % (prefix and '%s: ' % prefix or '', vals.get('name', ''))
        eco = super(MrpEcoOrder, self).create(vals)
        return eco

    def action_view_bom_eco(self):
        self.ensure_one()

        return {
            'name': u'变更的BOM',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom.eco',
            'view_mode': 'form',
            'view_type': 'form',
            # 'view_id': view.id,
            'views': [[False, 'tree'], [False, 'form']],
            'target': 'current',
            'domain': [('id', 'in', self.bom_eco_ids.ids)]
        }

    def action_view_bom_effect_line(self):
        self.ensure_one()
        return {
            'name': u'影响的单据',
            'type': 'ir.actions.act_window',
            'res_model': 'eco.effect.line',
            'view_mode': 'form',
            'view_type': 'form',
            # 'view_id': view.id,
            'views': [[False, 'tree'], [False, 'form']],
            'target': 'current',
            'domain': [('id', 'in', self.eco_effect_line_ids.ids)]
        }
    @api.multi
    def make_mrp_bom_ecos(self):
        mrp_bom_eco = self.env["mrp.bom.eco"]
        new_bom_ecos = self.env["mrp.bom.eco"]
        for eco in self:
            if eco.bom_eco_count > 0:
                raise UserError(u"已经生成BOM变更单,无法操作")

            same_bom_eco_line = {}
            for eco_line in eco.eco_line_ids:
                if same_bom_eco_line.get(eco_line.bom_id.id):
                    same_bom_eco_line[eco_line.bom_id.id] += eco_line
                else:
                    same_bom_eco_line[eco_line.bom_id.id] = eco_line
            for bom_id in same_bom_eco_line.keys():
                current_ver = same_bom_eco_line[bom_id][0].bom_id.version
                bom_eco_val = {
                    'eco_order_id': eco.id,
                    'user_id': eco.user_id.id,
                    'company_id': eco.company_id.id,
                    'effectivity': eco.effectivity,
                    'effectivity_date': eco.effectivity_date,
                    'old_version': current_ver,
                    'new_version': current_ver + 1,
                    'bom_id': bom_id,
                    'note': eco.note,
                    'bom_change_ids': [(6, 0, same_bom_eco_line[bom_id].ids)]
                }
                new_bom_ecos += mrp_bom_eco.create(bom_eco_val)
        return new_bom_ecos


class MrpEcoLine(models.Model):
    _name = 'mrp.eco.line'
    _description = u"变更明细行"
    # _inherit = ['mail.thread', 'ir.needaction_mixin']

    # name = fields.Char('Reference', copy=False, required=True)
    # user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    # company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    eco_order_id = fields.Many2one('mrp.eco.order', ondelete="restrict")
    effectivity = fields.Selection(related="eco_order_id.effectivity", string=u'何时生效?',  # Is this English ?
                                   default='asap')  # TDE: usefull ?
    effectivity_date = fields.Datetime(u'生效时间', related="eco_order_id.effectivity_date")

    # product_tmpl_id = fields.Many2one('product.template', "Product")
    bom_id = fields.Many2one(
            'mrp.bom', u"物料清单", ondelete="restrict", required=True)

    bom_line_id = fields.Many2one('mrp.bom.line',
                                  string=u'BOM明细行',
                                  compute="_compute_bom_line_id",
                                  )
    operate_type = fields.Selection(selection=[('add', u'新增'),
                                               ('remove', u'移除此项'),
                                               ('update', u'更新配比')],
                                    string=u'操作')
    product_id = fields.Many2one('product.product', string=u'产品', domain="[('bom_line_ids.bom_id', '=', bom_id)]")
    new_product_qty = fields.Float(
            u'更新后的配比',
            digits=dp.get_precision('Product Unit of Measure'),
            default=1.0)
    new_product_id = fields.Many2one(
            'product.product', u'更新后的产品', domain="[('bom_line_ids.bom_id', '!=', bom_id), ('type', '=', 'product')]")

    bom_eco_id = fields.Many2one(comodel_name="mrp.bom.eco", ondelete="restrict")

    @api.multi
    def _compute_bom_line_id(self):
        bom_line_obj = self.env["mrp.bom.line"]
        for line in self:
            line.bom_line_id = bom_line_obj.search([('product_id', '=', line.product_id.id),
                                                    ('bom_id', '=', line.bom_id.id)], limit=1)

    @api.multi
    @api.onchange("bom_line_id")
    def _onchange_bom_line_id(self):
        for line in self:
            line.product_id = self.bom_line_id.product_id.id


class MrpBomEco(models.Model):
    _name = 'mrp.bom.eco'
    _description = u'BOM 变更单'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'create_date desc'

    old_version = fields.Integer(string=u'变更前的版本号')
    new_version = fields.Integer(string=u'变更后的版本号')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', u'负责人', default=lambda self: self.env.user)
    # name = fields.Char('Reference', copy=False, required=True)
    # user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    # company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    eco_order_id = fields.Many2one('mrp.eco.order', ondelete="restrict", track_visibility="onchange")
    effectivity = fields.Selection([
        ('asap', u'立即'),
        ('date', u'根据时间')], string=u'何时生效?',  # Is this English ?
            default='asap', required=True, track_visibility="onchange")  # TDE: usefull ?
    effectivity_date = fields.Datetime(u'生效时间')
    bom_id = fields.Many2one(
            'mrp.bom', u"物料清单", ondelete="restrict", required=True)

    bom_change_ids = fields.One2many(comodel_name='mrp.eco.line', inverse_name='bom_eco_id', string=u'BOM变更明细')
    note = fields.Text(u'备注')

    @api.multi
    def name_get(self):
        return [(bom_eco.id, bom_eco.bom_id.product_tmpl_id.display_name)
                for bom_eco in self]

    @api.onchange("bom_id")
    def _onchange_bom_id(self):
        self.old_version = self.bom_id.version,
        self.new_version = self.bom_id.version + 1,

    @api.multi
    def _check_operate_same_product(self):
        for bom_eco in self:
            for change in bom_eco.bom_change_ids:
                if change.operate_type == 'add':  # 无法新增一个原有的
                    for line_id in bom_eco.bom_id.bom_line_ids:
                        if line_id.product_id == change.new_product_id:
                            return False
                    for change1 in bom_eco.bom_change_ids:
                        if change != change1 and change.new_product_id == change1.new_product_id:
                            return False
        return True

    @api.multi
    def _check_bom_line(self):
        """
        检查是否有在同一个bom里同时操作一个bomline的
        :return:
        """
        for bom_eco in self:
            for change in bom_eco.bom_change_ids:
                # 检查是否存在
                for change1 in bom_eco.bom_change_ids:
                    if change != change1:
                        if (change.product_id.id and change1.product_id.id) and \
                                        change.product_id == change1.product_id:  # 适用于 update和 remove
                            return False
                        if (change.product_id.id and change1.new_product_id.id) and \
                                        change.product_id == change1.new_product_id:  # 适用于 add
                            return False
                        if (change.new_product_id.id and change1.product_id.id) and \
                                        change.new_product_id == change1.new_product_id:
                            return False

                            # product_ids = bom_eco.bom_change_ids.mapped('product_id')
                            # if product_ids and (len(product_ids) != len(bom_eco.bom_change_ids)):
                            #     return False
        return True

    @api.multi
    def apply_new_version_number(self):
        """
        更新版本号
        :return:
        """
        for bom_eco in self:
            if bom_eco.bom_id.version != bom_eco.old_version:
                raise UserError(u'BOM版本不匹配,请检查')
            else:
                bom_eco.bom_id.version = bom_eco.new_version

    @api.multi
    def apply_to_bom(self):
        """
        将bOM按照表单进行更新, 并增加版本号
        :return:
        """
        if not self._check_bom_line():
            raise UserError(u'不能在一张变更单中,同时变更一个物料')
        if not self._check_operate_same_product():
            raise UserError(u'该产品已存在,无法重复添加')
        bom_line_obj = self.env['mrp.bom.line']
        for bom_eco in self:
            bom_to_apply = bom_eco.bom_id
            for bom_change in bom_eco.bom_change_ids:
                if bom_change.operate_type == 'add':

                    bom_line_obj.create({
                        'bom_id': bom_to_apply.id,
                        'product_id': bom_change.new_product_id.id,
                        'product_qty': bom_change.new_product_qty,
                    })
                elif bom_change.operate_type == 'update':
                    if not bom_change.bom_line_id:
                        raise UserError(u' %s 未找到对应的BOM明细行', bom_change.product_id.name)
                    if bom_change.bom_line_id.product_qty != bom_change.new_product_qty:
                        bom_change.bom_line_id.product_qty = bom_change.new_product_qty
                    else:
                        raise UserError(u'%s 修改前后BOM配比相同', bom_change.product_id.name)

                elif bom_change.operate_type == 'remove':
                    if not bom_change.bom_line_id:
                        raise UserError(u' %s 未找到对应的BOM明细行', bom_change.product_id.name)
                    bom_change.bom_line_id.unlink()
            if len(bom_eco.bom_id.bom_line_ids) == 0:
                raise UserError(u'变更后, %s 明细行为空.' % bom_eco.bom_id.name)
        self.apply_new_version_number()

    @api.multi
    def apply_bom_update(self):
        """
        将修改应用到MO PO等单据
        :return:
        """
        ProcurementOrder = self.env['procurement.order']
        for bom_eco in self:
            mos = self.env["mrp.production"].search(
                    [('bom_id', '=', bom_eco.bom_id.id),
                     ('state', 'not in', ['cancel', 'done']),
                     ('bom_version', '=', bom_eco.old_version)])
            for mo in mos:
                # 算出的所需物料的数量, 要减去已完成的数量
                done_moves = mo.move_finished_ids.filtered(
                        lambda x: x.state == 'done' and x.product_id == mo.product_id)
                qty_produced = mo.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')),
                                                                      mo.product_uom_id)
                factor = mo.product_uom_id._compute_quantity(mo.product_qty - qty_produced,
                                                             mo.bom_id.product_uom_id) / mo.bom_id.product_qty
                boms, lines = mo.bom_id.explode(mo.product_id, factor, picking_type=mo.bom_id.picking_type_id)
                move_obj = self.env["stock.move"]
                for change in bom_eco.bom_change_ids:
                    if change.operate_type == 'add':  # 新增物料需求, 直接在这个mo上面
                        # add的时候 只有newproduct_id有值
                        bom_line_id, line_data = self.find_line_data_with_bom_line(lines,
                                                                                   product_id=change.new_product_id)
                        move_obj = mo._generate_raw_move(bom_line_id, line_data)
                        to_qty = line_data["qty"]
                        if move_obj:
                            move_obj.adjust_move_procure_method()
                            move_obj.action_confirm()
                            sim_move_id = mo.add_one_sim_stock_move(move_obj)
                            self.create_effect_mo_type(move_obj, sim_move_id, bom_eco, change, 0, to_qty)

                    elif change.operate_type == 'update':  # 更新时,计算出更新后所需要的物料数量 并更新
                        # update的时候 只有product_id有值
                        bom_line_id, line_data = self.find_line_data_with_bom_line(lines,
                                                                                   product_id=change.product_id)
                        move = mo.move_raw_ids.filtered(
                                lambda x: x.bom_line_id.id == bom_line_id.id)
                        quantity = line_data['qty']
                        from_qty = move.product_uom_qty
                        qty_need_create = quantity - move.product_uom_qty
                        if not move:
                            continue
                        else:
                            move = move.filtered(lambda x: x.state not in ["cancel", "done"]) or move[0]
                        if qty_need_create > 0:  # need create new procurement, new po or new mo
                            #  此处有两种处理方式,1.固定生成 MO数量, 2.进行mrp运算,根据库存来生成MO数量
                            vals = move._prepare_procurement_from_move()
                            vals["product_qty"] = qty_need_create
                            procurement = self.env["procurement.order"].create(vals)
                            if procurement:
                                procurement.run()
                            mo._update_raw_move(bom_line_id, line_data)  # 在获取完应该补充的qty之后,再更新mo的rawmove 重要!
                            sim_move_id = mo.sim_stock_move_lines.filtered(
                                lambda x: x.product_id == bom_line_id.product_id)
                            self.create_effect_mo_type(move, sim_move_id, bom_eco, change, from_qty, quantity)

                        else:  # 需要 减少
                            pass
                            # procurement_order = self.env["procurement.order"].search([('move_dest_id', '=', move.id)])
                            # if procurement_order:
                            #     procurement_order.require_reduced()

                    elif change.operate_type == 'remove':  # 移除时,筛选出相同产品的,并且可用的move单 取消他们.
                        moves_to_cancel = mo.move_raw_ids.filtered(
                                lambda x: x.product_id == change.product_id and x.state not in ["done", "cancel"])
                        moves_to_cancel.action_cancel()  # 取消的对应的move 并且取消 对应的补货单
                        sim_move_id = mo.sim_stock_move_lines.filtered(lambda x: x.product_id == bom_line_id.product_id)
                        self.create_effect_mo_type(moves_to_cancel, sim_move_id, bom_eco, change,
                                                   moves_to_cancel.product_uom_qty, 0)
                        procurements = ProcurementOrder.search([('move_dest_id', 'in', moves_to_cancel.ids)])
                        if procurements:
                            procurements.cancel()

                mo.bom_version = bom_eco.new_version  # 将MO 版本号更新到新的版本

    def procurement_context(self, move=None, sim_move_id=None, bom_eco_id=None, bom_change_line_id=None, from_qty=None,
                            to_qty=None):
        """
        生成context 传到各个 补货单生成的时候, 用来创建记录
        :return:
        """
        return {
            'eco_vals': {
                'line_type': 'mrp_production',
                'production_id': sim_move_id.production_id.id,
                'bom_eco_id': bom_eco_id.id,
                'eco_order_id': bom_change_line_id.eco_order_id.id,
                'bom_change_line_id': bom_change_line_id.id,
                'move_id': move.id,
                'sim_stock_move_id': sim_move_id.id,
                'from_qty': from_qty,
                'to_qty': to_qty,
            }
        }

    def create_effect_mo_type(self, move=None, sim_move_id=None, bom_eco_id=None, bom_change_line_id=None,
                              from_qty=None, to_qty=None):
        """
        创建影响的单据
        :param move: 变更的移动
        :param sim_move_id: 变更的移动
        :param bom_eco_id: 变更单
        :param bom_change_line_id: bom变更的修改条目
        :param from_qty: 旧的数量
        :param to_qty: 新的数量
        :return:
        """

        return self.env["eco.effect.line"].create({
            'line_type': 'mrp_production',
            'production_id': sim_move_id.production_id.id,
            'bom_eco_id': bom_eco_id.id,
            'eco_order_id': bom_change_line_id.eco_order_id.id,
            'bom_change_line_id': bom_change_line_id.id,
            'move_id': move.id,
            'sim_stock_move_id': sim_move_id.id,
            'from_qty': from_qty,
            'to_qty': to_qty,
        })

    def find_line_data_with_bom_line(self, lines, product_id=None):
        """
        找到bom中对应修改的那条
        :param lines:
        :param product_id:
        :return:
        """
        for bom_line, line_data in lines:
            # if bom_line_id and bom_line_id == bom_line:  # 如果参数有 bom明细行 就使用明细行, 如果没有就使用产品
            #     return line_data
            if product_id and bom_line.product_id == product_id:
                return bom_line, line_data
        raise UserError(u"找不到对应的BOM明细行")


class EcoEffectLine(models.Model):
    _name = 'eco.effect.line'

    line_type = fields.Selection(string=u"类型", selection=[('mrp_production', u'制造单'),
                                                          ('purchase_order', u'采购单'), ],
                                 required=False, )

    purchase_id = fields.Many2one(string=u'采购单', comodel_name='purchase.order')
    purchase_line_id = fields.Many2one(string=u'采购订单行', comodel_name='purchase.order.line')
    production_id = fields.Many2one(string=u'制造单', comodel_name='mrp.production')
    sim_stock_move_id = fields.Many2one(string=u'消耗物料明细行', comodel_name='sim.stock.move')
    move_id = fields.Many2one(string=u'库存移动单', comodel_name='stock.move')
    bom_eco_id = fields.Many2one(string=u'BOM变更单', comodel_name='mrp.bom.eco')
    eco_order_id = fields.Many2one(string=u'变更单', comodel_name='mrp.eco.order')
    from_qty = fields.Float(string=u'旧的数量')
    to_qty = fields.Float(string=u'新的数量')
    bom_change_line_id = fields.Many2one(comodel_name='mrp.eco.line')
    effect_order_id = fields.Many2one(comodel_name='eco.effect.order')


class EcoEffectOrder(models.Model):
    _name = 'eco.effect.order'

    name = fields.Char(u'单号', copy=False, required=True)
    bom_eco_id = fields.Many2one(comodel_name="mrp.bom.eco", string=u"Bom变更单", required=False, )
    effect_mo_line_ids = fields.One2many(string=u'影响的MO',
                                         comodel_name='eco.effect.line',
                                         inverse_name='effect_order_id',
                                         domain=[('line_type', '=', 'mrp_production')])
    effect_po_line_ids = fields.One2many(string=u'影响的PO',
                                         comodel_name='eco.effect.line',
                                         inverse_name='effect_order_id',
                                         domain=[('line_type', '=', 'purchase_order')]
                                         )

    @api.model
    def create(self, vals):
        prefix = self.env['ir.sequence'].next_by_code('eco.effect.order') or ''
        vals['name'] = prefix
        eco = super(EcoEffectOrder, self).create(vals)
        return eco
