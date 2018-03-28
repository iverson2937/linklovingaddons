# -*- coding: utf-8 -*-
import json
import datetime
import logging
import traceback
import types

import jpush
import pytz
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare, math
from odoo.addons import decimal_precision as dp


class MrpBomExtend(models.Model):
    _inherit = 'mrp.bom'
    product_specs = fields.Text(string=u'Product Specification', related='product_tmpl_id.product_specs')

    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.", copy=False)
    state = fields.Selection([
        ('new', u'新建'),
        ('deny', u'已拒绝'),
        ('cancel', u'取消'),
        ('updated', u'更新'),
        ('draft', u'草稿'),
        ('review_ing', u'审核中'),
        ('release', u'正式')
    ], u'状态', track_visibility='onchange', default='new')

    # bom_approval_id = fields.Many2one('approval.project.picking', string=u'工程领料bom',store=True)

    @api.multi
    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    bom_remark = fields.Text(string=u"备注", track_visibility='onchange')

    @api.multi
    def set_to_release(self):
        self.state = 'release'

    def explode(self, product, quantity, picking_type=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        boms_done = [(self, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
        lines_done = []
        templates_done = product.product_tmpl_id

        bom_lines = [(bom_line, product, quantity, False) for bom_line in self.bom_line_ids]
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product):
                continue
            if current_line.product_id.product_tmpl_id in templates_done:
                raise UserError(_(
                    'Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))

            line_quantity = current_qty * current_line.product_qty  # * (1 + bom_line.scrap_rate /100)
            bom = self._bom_find(product=current_line.product_id, picking_type=picking_type or self.picking_type_id,
                                 company_id=self.company_id.id)
            if bom.type == 'phantom':
                converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty,
                                                                                        bom.product_uom_id)
                bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in
                             bom.bom_line_ids] + bom_lines
                templates_done |= current_line.product_id.product_tmpl_id
                boms_done.append((bom,
                                  {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity,
                                   'parent_line': current_line}))
            else:
                lines_done.append(
                    (current_line, {'suggest_qty': round(line_quantity * (1 + bom_line.scrap_rate / 100)),
                                    'qty': line_quantity, 'product': current_product,
                                    'original_qty': quantity, 'parent_line': parent_line}))

        return boms_done, lines_done


class MrpBomLineExtend(models.Model):
    _inherit = 'mrp.bom.line'

    product_specs = fields.Text(string='Product Specification', related='product_id.product_specs')
    scrap_rate = fields.Float(string='Scrap Rate(%)', default=3, )
    active1 = fields.Boolean(related='product_id.active')

    @api.multi
    def show_product_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': u'产品',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'product.template',
            'target': 'current',
            'res_id': self.product_id.product_tmpl_id.id
        }

    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('Reverse Exhibition'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
                'search_default_bom_line_ids': self.product_id.default_code, }
        }


class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('Reverse Exhibition'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
                'search_default_bom_line_ids': self.product_tmpl_id.default_code, }
        }


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_template_open_bom(self):
        action = self.env.ref('mrp.template_open_bom').read()[0]
        bom_ids = self.mapped('bom_ids')
        if len(bom_ids) > 1:
            action['domain'] = [('id', 'in', bom_ids.ids)]
        elif bom_ids:
            action['views'] = [(self.env.ref('mrp.mrp_bom_form_view').id, 'form')]
            action['res_id'] = bom_ids.id
        return action

    @api.multi
    def action_see_bom_structure_reverse(self):
        bom_tree_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_tree_view')
        bom_form_view = self.env.ref('linkloving_mrp_extend.linkloving_mrp_bom_form_view')

        return {
            'name': _('Reverse Exhibition'),
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_tree_view.id,
            'views': [(bom_tree_view.id, 'tree'), (bom_form_view.id, 'form')],
            'view_mode': 'tree',
            # 'view_type': 'form',
            'limit': 80,
            'context': {
                'search_default_bom_line_ids': self.default_code, }
        }

    product_insufficient = fields.Boolean(compute='_compute_insufficient', store=True)

    @api.depends('reordering_min_qty', 'qty_available')
    def _compute_insufficient(self):

        res = self._compute_quantities_dict()
        ress = {k: {'nbr_reordering_rules': 0, 'reordering_min_qty': 0, 'reordering_max_qty': 0} for k in self.ids}
        product_data = self.env['stock.warehouse.orderpoint'].read_group(
            [('product_id.product_tmpl_id', 'in', self.ids)], ['product_id', 'product_min_qty', 'product_max_qty'],
            ['product_id'])
        for data in product_data:
            product = self.env['product.product'].browse([data['product_id'][0]])
            product_tmpl_id = product.product_tmpl_id.id
            ress[product_tmpl_id]['reordering_min_qty'] = data['product_min_qty']

        for products in self:
            print res[products.id]['qty_available']
            print ress[products.id]['reordering_min_qty']
            print "完毕"
            products.product_insufficient = True if res[products.id]['qty_available'] < ress[products.id][
                'reordering_min_qty'] else False


class StockMoveExtend(models.Model):
    _inherit = 'stock.move'
    _order = 'create_date desc'
    reason = fields.Char(u'备注')
    qty_available = fields.Float(string='On Hand', related='product_id.qty_available')
    virtual_available = fields.Float(string='Forecast Quantity', related='product_id.virtual_available')
    suggest_qty = fields.Integer(string='Suggest Quantity', help=u'建议数量 = 实际数量 + 预计报废数量', )
    over_picking_qty = fields.Float(string='Excess Quantity ', )
    is_return_material = fields.Boolean(default=False)
    is_over_picking = fields.Boolean(default=False)
    is_scrap = fields.Boolean(default=False)

    authorizer_id = fields.Many2one("hr.employee", string=u'授权人', )
    authorizee_id = fields.Many2one("res.users", string=u"被授权人")

    def action_change_state_cancel(self):
        self.state = 'cancel'

    @api.multi
    # 授权人 和被授权人
    def authorized_stock_move(self, authorizer_id=None, authorizee_id=None):
        self.write({
            "authorizer_id": authorizer_id,
            "authorizee_id": authorizee_id,
        })

        # @api.multi
        # def _qty_available(self):
        #     for move in self:
        #         # For consumables, state is available so availability = qty to do
        #         if move.state == 'assigned':
        #             move.quantity_available = move.product_uom_qty
        #         else:
        #             move.quantity_available = move.reserved_availability


class ProductionTimeRecord(models.Model):
    _name = 'production.time.record'

    record_type = fields.Selection(string="记录类型", selection=[('rework', '返工'), ('secondary', '二次生产'), ],
                                   default='secondary')
    end_time = fields.Datetime(string=u'结束时间')
    production_id = fields.Many2one('mrp.production')


class BackToProgressWizard(models.TransientModel):
    _name = 'secondary.produce.wizard'

    produce_line_ids = fields.Many2many("mrp.production", string=u'相关制造单')

    def action_confirm(self):
        self.produce_line_ids.back_to_progress()
        return '1234'


class BackToProgressMoLine(models.TransientModel):
    _name = 'secondary.produce.line'

    production_id = fields.Many2one("mrp.production", string=u"制造单")
    process_id = fields.Many2one("mrp.process", related="production_id.process_id")
    product_id = fields.Many2one("product.template", related="production_id.product_tmpl_id")
    state = fields.Selection(related="production_id.state")


class MrpConfigSettingsI(models.TransientModel):
    _inherit = 'mrp.config.settings'

    allow_produced_qty_rate = fields.Integer(string=u'允许的超产率(%)')

    def get_default_allow_produced_qty_rate(self, m_fields):
        fi_val = self.env["ir.config_parameter"].get_param("mrp.config.settings.allow_produced_qty_rate", default=3)
        return {'allow_produced_qty_rate': int(fi_val)}

    @api.multi
    def set_allow_produced_qty_rate(self):
        m_fields = ['allow_produced_qty_rate']
        for record in self:
            for fi in m_fields:
                self.env['ir.config_parameter'].set_param("mrp.config.settings.%s" % fi, getattr(record, fi, ''))



class MrpProductionExtend(models.Model):
    _inherit = "mrp.production"

    is_secondary_produce = fields.Boolean(default=False)
    secondary_produce_time_ids = fields.One2many("production.time.record", 'production_id', )

    @api.model
    def create(self, vals):
        print vals,
        print '***************************************'

        return super(MrpProductionExtend, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'state' in vals and vals['state'] == 'waiting_material' and self.bom_id.state not in ('draft', 'release'):
            raise UserError('BOM还没通过审核,请联系相关负责人')
        return super(MrpProductionExtend, self).write(vals)

    def action_view_secondary_mos(self):
        mos = self.env["mrp.production"].search([("origin", "ilike", self.name),
                                                 ("state", "=", "done")])
        mos += self
        return {'type': 'ir.actions.act_window',
                'res_model': 'secondary.produce.wizard',
                'view_mode': 'form',
                'context': '{"default_production_id":%s, "default_produce_line_ids":%s}' % (self.id, mos.ids),
                # , "default_produce_line_ids": %s}' % (self.id, self),
                # 'res_id': self.product_tmpl_id.id,
                'target': 'new'
                }

    @api.multi
    def back_to_progress(self):
        for mo in self:
            mo.is_secondary_produce = True
            p_time = self.env["production.time.record"].create({
                'production_id': mo.id,
                'start_time': fields.Datetime.now(),
                'record_type': 'secondary'
            })
            mo.state = 'progress'

    @api.multi
    def action_view_qc_report(self):
        ids = []

        return {
            'name': u'品检报告',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.qc.feedback',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.qc_feedback_ids.ids)],
            'target': 'current',
        }

    def action_view_return_material_order(self):
        return {
            'name': u'退料单',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.return.material',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'),
                      (self.env.ref("linkloving_mrp_extend.view_mrp_return_material_order_form").id, 'form')],
            'domain': [('id', 'in', self.return_material_order_ids.ids)],
            'target': 'current',
        }
    def action_see_scrap_moves(self):
        self.ensure_one()
        action = self.env.ref('linkloving_mrp_extend.action_mrp_production_scrap_moves').read()[0]
        action['domain'] = [('production_id', '=', self.id), ('is_scrap', '=', True)]
        return action

    qc_feedback_ids = fields.One2many('mrp.qc.feedback', 'production_id', track_visibility='onchange')
    qty_unpost = fields.Float(string=u"已生产的数量", compute="_compute_qty_unpost")
    feedback_on_rework = fields.Many2one("mrp.qc.feedback", u"返工单", track_visibility='onchange')
    has_produced_product = fields.Boolean(compute='_compute_has_produced_product', store=True)

    @api.multi
    @api.depends('qc_feedback_ids')
    def _compute_has_produced_product(self):
        for mo in self:
            print ("3123131312131231")
            if mo.qc_feedback_ids:
                mo.has_produced_product = True
            else:
                mo.has_produced_product = False

    @api.multi
    def _compute_qty_unpost(self):
        for production in self:
            feedbacks = production.qc_feedback_ids.filtered(lambda x: x.state not in ["check_to_rework"])
            production.qty_unpost = sum(feedbacks.mapped("qty_produced"))

    @api.multi
    def _get_qc_feedback_count(self):
        for feedback in self:
            feedback.qc_feedback_count = len(feedback.qc_feedback_ids)

    @api.multi
    def _compute_return_order_count(self):
        for order in self:
            order.return_order_count = len(order.return_material_order_ids)

    return_order_count = fields.Integer(compute='_compute_return_order_count')
    return_material_order_ids = fields.One2many("mrp.return.material", "production_id", string=u"退料单")
    qc_feedback_count = fields.Integer(compute='_get_qc_feedback_count')
    availability = fields.Selection([
        ('assigned', u'可发料'),
        ('partially_available', u'缺料中'),
        ('waiting', u'等待材料'),
        ('none', 'None')], string=_('Material Status'),
        compute='_compute_availability', store=True)

    @api.depends('product_id.outgoing_qty', 'product_id.incoming_qty', 'product_id.qty_available')
    def _get_output_rate(self):
        for mo in self:
            if mo.product_id.outgoing_qty:
                rate = ((mo.product_id.incoming_qty + mo.product_id.qty_available) / mo.product_id.outgoing_qty)
                rate = round(rate, 2)

                mo.output_rate = (u"( 在制造量: " + "%s " + u"+库存:" + "%s ) /"u" 需求量：" + "%s = %s") % (
                    mo.product_id.incoming_qty, mo.product_id.qty_available, mo.product_id.outgoing_qty, rate)
            else:
                mo.output_rate = (u" 在制造量: " + "%s  " + u"库存:" + "%s  "u" 需求量：" + "%s  ") % (
                    mo.product_id.incoming_qty, mo.product_id.qty_available, mo.product_id.outgoing_qty)

    output_rate = fields.Char(compute=_get_output_rate, string=u'生产参考')

    @api.model
    def create(self, vals):
        res = super(MrpProductionExtend, self).create(vals)
        self._compute_sim_stock_move_lines(res)
        res._compute_location_ids()
        return res

    def add_one_sim_stock_move(self, move):
        if move:
            res = self.env['sim.stock.move'].create(self._prepare_sim_stock_move_values(move.product_id.id))
            return res

    @api.multi
    def _compute_sim_stock_move_lines(self, new_pr):
        list = []
        for move in new_pr.move_raw_ids:
            list.append(move.product_id.id)
        a = set(list)  # 不重复的set集合
        res_list = []
        sim_stock_move_lines = self.env["sim.stock.move"].search([("production_id", "=", new_pr.id)])
        if not sim_stock_move_lines:
            for r in a:
                dict = self._prepare_sim_stock_move_values(r)
                res = self.env['sim.stock.move'].create(dict)
                res_list.append(res.id)
                new_pr.sim_stock_move_lines = res_list
        else:
            new_pr.sim_stock_move_lines = sim_stock_move_lines
            # else:
            #     for r in a:
            #         if r.product_id not in self.sim_stock_move_lines.mapped('product_id'):
            #             dict = self._prepare_sim_stock_move_values(r)
            #             res = self.env['sim.stock.move'].create(dict)
            #             self.sim_stock_move_lines |= res
            # return

    def _prepare_sim_stock_move_values(self, value):
        return {
            'product_id': value,
            'production_id': self.id
        }

    #####仓库负责人的集合
    location_ids = fields.Many2many(comodel_name="stock.location", compute="_compute_location_ids", store=True)

    @api.depends("move_raw_ids.product_id.categ_id.fixed_location_ids.putaway_id.location_ids")
    @api.multi
    def _compute_location_ids(self):
        for mo in self:
            ids = []

            for move in mo.move_raw_ids:
                for fix_location_id in move.product_id.categ_id.fixed_location_ids:
                    for location_id in fix_location_id.putaway_id.location_ids:
                        ids.append(location_id.id)
            print ids, 'sssssssssssssssss'
            mo.location_ids = [(6, 0, set(ids))]

    # 备料信息
    prepare_material_img = fields.Binary(string='Stock Image')
    prepare_material_area_id = fields.Many2one('stock.location.area', string='Area')
    #########
    # 送完品检时的信息
    to_qc_img = fields.Binary(string='Location Image')
    to_qc_area_id = fields.Many2one('stock.location.area', string='Area')
    #####
    # 品检反馈单
    qc_feedback_id = fields.Many2one('mrp.qc.feedback', string='QC Report')
    ####
    # 是否暂停
    is_pending = fields.Boolean()
    ####


    # @api.multi
    # def _compute_origin_sale_order_id(self):
    #     def get_parent_move(move):
    #         if move.move_dest_id:
    #             return get_parent_move(move.move_dest_id)
    #         return move
    #     for production in self:
    #         move = get_parent_move(production.move_finished_ids[0])
    #         production.origin_sale_order_id = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.id or False
    #####生产完成 提交信息
    # 是否分批产出
    is_split_done = fields.Boolean(u"是否分批产出")
    produce_img = fields.Binary(u"图片信息")
    produce_area_id = fields.Many2one('stock.location.area')

    worker_line_ids = fields.One2many('worker.line', 'production_id')
    sim_stock_move_lines = fields.One2many('sim.stock.move', 'production_id')
    move_finished_ids = fields.One2many(
        'stock.move', 'production_id', 'Finished Products',
        copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain=[('scrapped', '=', False), ('is_return_material', '=', False), ('is_over_picking', '=', False)])

    production_order_type = fields.Selection(
        [('stockup', 'By Stock（Unnecessary to output all quantity）'), ('ordering', u'By Order')], string=u'Order Type',
        default='stockup',
        help=u'By Stock：Can sent to QC check without complete  the Order。\nBy order：have to completed the Order then send to the QC station')
    total_spent_time = fields.Float(default=0, compute='_compute_total_spent_time', string='Time taken', )
    total_spent_money = fields.Float(default=0, compute='_compute_total_spent_money', string='Total Cost', )
    state = fields.Selection([
        ('draft', u'草稿'),
        ('confirmed', u'需求确认'),
        ('waiting_material', u'等待备料'),
        ('prepare_material_ing', u'备料中...'),
        ('finish_prepare_material', u'备料完成'),
        ('already_picking', u'已领料'),
        ('planned', 'Planned'),
        ('progress', '生产中'),
        ('waiting_inspection_finish', u'等待品检完成'),
        ('waiting_quality_inspection', u'等待品检'),
        ('quality_inspection_ing', u'品检中'),
        ('waiting_rework', u'等待返工'),
        ('rework_ing', u'返工中'),
        ('waiting_inventory_material', u'等待清点退料'),
        ('waiting_warehouse_inspection', u'等待检验退料'),
        ('waiting_post_inventory', u'等待入库'),
        ('done', u'已完成'),
        ('cancel', u'已取消'),
        ('force_cancel_waiting_return', u'强制取消,清点退料'),
        ('force_cancel_waiting_warehouse_inspection', u'强制取消,仓库确认退料'),
    ], string='status',
        copy=False, default='confirmed', track_visibility='onchange')

    sale_remark = fields.Text(compute='_compute_sale_remark', string=u"销售单备注")

    # bom_remark = fields.Text(compute="_compute_bom_remark", string=u'Bom备注')
    remark = fields.Text(string=u"MO单备注")

    picking_material_date = fields.Datetime()

    factory_remark = fields.Text(string=u"工厂备注", track_visibility='onchange')

    material_remark_id = fields.Many2one("material.remark", string=u"无法备料原因")
    production_remark_id = fields.Many2one("material.remark", string=u"无法生产的原因")

    # @api.multi
    # def _compute_bom_remark(self):
    #     for production in self:


    @api.multi
    def _compute_sale_remark(self):
        for production in self:
            origin = production.origin
            order_name_list = []
            if origin:
                split_by_dot = origin.split(",")  # cccc
                for split in split_by_dot:
                    split_by_maohao = split.split(":")
                    order_name_list += split_by_maohao
            sale_orders = self.env["sale.order"].search([("name", "in", order_name_list)])
            sale_remark = ''
            for sale_order in sale_orders:
                if sale_order.remark:
                    sale_remark += (sale_order.name + ":" + sale_order.remark + "\n")
            production.sale_remark = sale_remark

    # 计算所有工人总共花的工时
    @api.one
    def _compute_total_spent_time(self):
        spent = 0
        for line in self.worker_line_ids:
            spent += line.cal_worker_spent_time()
        self.total_spent_time = spent / 3600.0

    # 计算生产总成本
    @api.one
    def _compute_total_spent_money(self):
        if self.mo_type == 'unit':  # 计件
            self.total_spent_money = self.qty_produced * self.unit_price
        elif self.mo_type == 'time':  # 计时
            self.total_spent_money = self.total_spent_time * self.hour_price
            # #添加工人

    # @api.multi
    # def add_worker(self):

    @api.multi
    def _compute_state(self):
        for production in self:
            # 如果有其中一个状态为品检失败
            if any(feedback.state == 'qc_fail' for feedback in production.qc_feedback_ids):
                pass
            elif all(feedback.state in ['qc_success', ] for feedback in production.qc_feedback_ids):
                pass

    def button_return_material(self, need_create_one):
        view = self.env.ref('linkloving_mrp_extend.stock_return_material_form_view2')
        if not need_create_one:
            return_obj = self.env['mrp.return.material'].get_normal_return_order(order_id=self.id)

            if return_obj:

                res = {'type': 'ir.actions.act_window',
                       'res_model': 'mrp.return.material',
                       'view_mode': 'form',
                       'view_id': view.id,
                       'res_id': return_obj.id,
                       'target': 'new'
                       }
            else:
                self.state = "done"
                res = {}
        else:
            res = {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.return.material',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'new',
                'context': {
                    'default_production_id': self.id,
                    'return_ids.product_ids': self.move_raw_ids.mapped('product_id').ids
                }
            }
        return res

    # 确认生产 等待备料
    def button_waiting_material(self):
        if self.bom_id.state not in ('draft', 'release'):
            raise UserError('BOM还没通过审核,请联系相关负责人')
        # if self.location_ids.filtered(lambda x: x.is_circulate_location == False) or not self.location_ids:
        self.write({'state': 'waiting_material'})
        # else:
        #     self.write({'state': 'finish_prepare_material'})
        if not self.is_rework:
            qty_wizard = self.env['change.production.qty'].create({
                'mo_id': self.id,
                'product_qty': self.product_qty,
            })
            qty_wizard.change_prod_qty()
        return {'type': 'ir.actions.empty'}
        # from linkloving_app_api.models.models import JPushExtend
        # JPushExtend.send_push(audience=jpush.audience(
        #     jpush.tag(LinklovingAppApi.get_jpush_tags("warehouse"))
        # ),notification=u"此订单已经可以开始备料")

    def action_force_cancel_waiting_return(self):
        """
        mo可任意状态强制取消并退料, 先取消未完成的stock_move 然后再生成一张退料单
        :return:
        """
        moves_to_cancel = (self.move_raw_ids | self.move_finished_ids).filtered(
            lambda x: x.state not in ('done', 'cancel'))
        moves_to_cancel.action_cancel()
        self.state = 'force_cancel_waiting_return'

    def action_confirm_force_return_material(self):
        """
        仓库检验强制取消的退料信息, 弹出对应的form
        :return:
        """
        view = self.env.ref('linkloving_mrp_extend.stock_return_material_form_view2')
        return_obj = self.env['mrp.return.material'].get_progress_return_order(order_id=self.id)
        if return_obj:
            res = {'type': 'ir.actions.act_window',
                   'res_model': 'mrp.return.material',
                   'view_mode': 'form',
                   'view_id': view.id,
                   'res_id': return_obj.id,
                   'target': 'new',
                   'context': {
                       'is_checking': True  # 代表是确认
                   },
                   }
        else:
            raise UserError(u'未找到对应的退料单单据')

        return res

    @api.multi
    def button_action_confirm_draft(self):
        if self.bom_id and self.bom_id.state not in ('draft', 'release'):
            raise UserError('BOM还没通过审核,请联系相关负责人')
        for production in self:
            production.write({'state': 'confirmed'})
        return {'type': 'ir.actions.empty'}

    @api.multi
    def button_action_cancel_confirm(self):
        for production in self:
            production.write({'state': 'draft'})
        return {'type': 'ir.actions.empty'}

    # 开始备料
    def button_start_prepare_material(self):
        if self.state == 'waiting_material':
            self.write({'state': 'prepare_material_ing'})
        return {'type': 'ir.actions.empty'}

    # 备料完成
    def button_finish_prepare_material(self):
        return self._show_picking_view(picking_mode='first_picking', invisible_options={'overpicking_invisible': True})
        # self.write({'state': 'finish_prepare_material'})

    # 开始生产
    @api.one
    def button_start_produce(self):
        self.write({'state': 'progress'})
        if 'produce_start_replan_mo' in dir(self):
            self.produce_start_replan_mo()

    # 给委外供应商发料
    def button_send_material_to_vendor(self):
        return {
            'name': u'填写物流单号',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'tracking.number.wizard',
            'target': 'new',
        }

        # 生产完成 等待品检

    def button_produce_finish(self):
        if self.qty_unpost == 0:
            raise UserError(_('These is not output,can not finish the order!'))
        if self.qty_unpost <= self.product_qty and self.production_order_type == 'ordering':
            raise UserError(_('You have to complete the order before close it!'))
        else:
            if self.feedback_on_rework:  # 生产完成, 但是还在返工中 说明此次返工还没产出
                raise UserError(u"该单据还在返工中,请先产出数量")
            # 生产完成 结算工时
            self.worker_line_ids.change_worker_state('outline')
            # if all(feedback.state in ['qc_success', 'alredy_post_inventory'] for feedback in self.qc_feedback_ids):
            #     self.state = "waiting_inventory_material"#等待清点退料
            # 有其中一个单据还没品捡 或者还没品捡完成, 等待品捡完成
            self.produce_finish_data_handle()
            self.env["procurement.order"].search([('production_id', 'in', self.ids)]).check()

    def produce_finish_data_handle(self):
        self.state = self.compute_order_state()
        if not self.is_secondary_produce and not self.feedback_on_rework:  # 不是第二次生产,则重新排产 或者没有返工单
            if 'produce_finish_replan_mo' in dir(self):
                self.produce_finish_replan_mo()
        else:  # 第二次生产,不影响排产,记录时间
            times = self.secondary_produce_time_ids.filtered(lambda x: not x.end_time)
            if times:  # 正常来说只有一个是没设置结束时间的
                times[0].end_time = fields.Datetime.now()
                times[0].is_secondary_produce = False
            else:
                raise UserError(u"未找到对应的数据")

    def compute_order_state(self):
        if any(feedback.state in ['draft', 'qc_ing'] for feedback in self.qc_feedback_ids):
            state = "waiting_inspection_finish"  # 等待品捡完成,
        elif any(feedback.state == 'qc_fail' for feedback in self.qc_feedback_ids):
            state = "waiting_rework"
        else:
            state = "waiting_inventory_material"
        return state

    # # 开始品检
    # def button_start_quality_inspection(self):
    #     self.write({'state': 'quality_inspection_ing'})
    #
    # # 品检通过
    # def button_quality_inspection_success(self):
    #     self.write({'state': 'waiting_inventory_material'})
    #     # self.write({'state': 'waiting_post_inventory'}

    # 清点物料
    def button_inventory_material(self):
        return self.button_return_material(need_create_one=True)

    # 仓库清点物料
    def button_check_inventory_material(self):
        return self.button_return_material(need_create_one=False)

    def picking_material(self):
        if self._context.get('picking_mode') == 'first_picking':
            is_all_0 = True  # 是否全部为0，没有填写备料数量
            for move in self.sim_stock_move_lines:
                if move.quantity_ready != 0:
                    is_all_0 = False

            if is_all_0:
                raise UserError(u"请填写备料数量")
        for move in self.sim_stock_move_lines:
            if move.over_picking_qty != 0:  # 如果超领数量不等于0
                moves_to_do = move.stock_moves.filtered(lambda x: x.state not in ('done', 'cancel'))
                if moves_to_do:
                    moves_to_do[0].quantity_done += move.over_picking_qty
                    # moves_to_do[0].action_done()
                else:
                    new_move = move.stock_moves[0].copy(
                        default={'quantity_done': move.over_picking_qty, 'product_uom_qty': move.over_picking_qty,
                                 'production_id': move.production_id.id,
                                 'raw_material_production_id': move.raw_material_production_id.id,
                                 'procurement_id': move.procurement_id.id or False,
                                 'product_uom': move.product_id.uom_id.id,
                                 'is_over_picking': True})
                    move.production_id.move_raw_ids = move.production_id.move_raw_ids + new_move
                    move.over_picking_qty = 0
                    new_move.write({'state': 'assigned', })
                    # new_move.action_done()
            if self._context.get('picking_mode') == 'first_picking':  # 如果备料数量不等于0
                if not move.stock_moves:
                    continue
                rounding = move.stock_moves[0].product_uom.rounding
                if float_compare(move.quantity_ready, move.stock_moves[0].product_uom_qty,
                                 precision_rounding=rounding) > 0:
                    qty_split = move.stock_moves[0].product_uom._compute_quantity(
                        move.quantity_ready - move.stock_moves[0].product_uom_qty,
                        move.stock_moves[0].product_id.uom_id)

                    split_move = move.stock_moves[0].copy(
                        default={'quantity_done': qty_split, 'product_uom_qty': qty_split,
                                 'production_id': move.production_id.id,
                                 'raw_material_production_id': move.raw_material_production_id.id,
                                 'procurement_id': move.procurement_id.id or False,
                                 'is_over_picking': True})
                    move.production_id.move_raw_ids = move.production_id.move_raw_ids + split_move
                    split_move.write({'state': 'assigned', })
                    move.stock_moves[0].quantity_done = move.stock_moves[0].product_uom_qty
                    # split_move.action_done()
                    # move.stock_moves[0].action_done()
                else:
                    move.stock_moves[0].quantity_done_store = move.quantity_ready
                    move.stock_moves[0].quantity_done = move.quantity_ready
                    # move.stock_moves[0].action_done()
        self.post_inventory()
        if self._context.get('picking_mode') == 'first_picking':
            self.write({'state': 'finish_prepare_material'})
            # elif self._context.get('picking_mode') == 'second_picking':
            # self.write({'state': 'already_picking'})
        return {'type': 'ir.actions.act_window_close'}

    def button_fill_material(self):
        return self._show_picking_view(picking_mode='second_picking',
                                       invisible_options={'quantity_ready_invisible': True})

    # 领料登记
    def button_already_picking(self):
        self.write({'state': 'already_picking',
                    'picking_material_date': fields.datetime.now()})

    # return self._show_picking_view(picking_mode='first_picking')

    def _show_picking_view(self, picking_mode, invisible_options):
        view = self.env.ref('linkloving_mrp_extend.picking_material_form')
        overpicking_invisible = invisible_options.get('overpicking_invisible', False)
        quantity_ready_invisible = invisible_options.get('quantity_ready_invisible', False)

        return {'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'context': {'picking_mode': picking_mode,
                            'overpicking_invisible': overpicking_invisible,
                            'quantity_ready_invisible': quantity_ready_invisible},
                'target': 'new'}

    @api.multi
    def _generate_raw_move(self, bom_line, line_data):

        quantity = line_data['qty']
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.bom_id.routing_id and self.bom_id.routing_id.location_id:
            source_location = self.bom_id.routing_id.location_id
        else:
            source_location = self.location_src_id
        original_quantity = self.product_qty - self.qty_produced
        data = {
            'name': self.name,
            'date': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
            'suggest_qty': line_data['suggest_qty'],
            'move_order_type': 'manufacturing_picking' if self.move_finished_ids else 'null',
            'quantity_adjusted_qty': bom_line.product_id.qty_available - quantity,
        }
        return self.env['stock.move'].create(data)

    @api.multi
    def update_rework_material(self, line, qty):
        quantity = line['product_qty']
        self.ensure_one()
        move = self.move_raw_ids.filtered(
            lambda x: x.product_id.id == line.product_id.id and x.state not in ('done', 'cancel'))
        if move:
            if quantity > 0:
                move[0].write({'product_uom_qty': quantity,
                               'suggest_qty': round(quantity)})
            else:
                if move[0].quantity_done > 0:
                    raise UserError(_(
                        'Lines need to be deleted, but can not as you still have some quantities to consume in them. '))
                move[0].action_cancel()
                move[0].unlink()
            return move

    @api.multi
    def _update_raw_move(self, bom_line, line_data):
        quantity = line_data['qty']
        self.ensure_one()
        move = self.move_raw_ids.filtered(
            lambda x: x.bom_line_id.id == bom_line.id and x.state not in ('done', 'cancel'))
        if move:
            if quantity > 0:
                move[0].write({'product_uom_qty': quantity,
                               'suggest_qty': line_data['suggest_qty']})
            else:
                if move[0].quantity_done > 0:
                    raise UserError(_(
                        'Lines need to be deleted, but can not as you still have some quantities to consume in them. '))
                move[0].action_cancel()
                move[0].unlink()
            return move
        else:
            self._generate_raw_move(bom_line, line_data)

    def get_today_time_and_tz(self):
        if self.env.user.tz:
            timez = fields.datetime.now(pytz.timezone(self.env.user.tz)).tzinfo._utcoffset
            date_to_show = fields.datetime.utcnow()
            date_to_show += timez
            return date_to_show, timez
        else:
            raise UserError("未找到对应的时区, 请点击 右上角 -> 个人资料 -> 时区 -> Asia/Shanghai")

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action

        """
        today_time, timez = self.get_today_time_and_tz()
        today_time = fields.datetime.strptime(fields.datetime.strftime(today_time, '%Y-%m-%d'), '%Y-%m-%d')
        today_time -= timez
        # today_time = fields.datetime.strptime(fields.datetime.strftime(fields.datetime.now(), '%Y-%m-%d'),
        #                                       '%Y-%m-%d')
        one_days_after = datetime.timedelta(days=3)
        after_day = today_time + one_days_after

        state = self._context.get('state')
        feedback_on_rework = self._context.get("feedback_on_rework")

        refuse = self._context.get("refuse")
        if refuse == 'material':
            return [('material_remark_id', '!=', False),
                    ('state', 'in', ['waiting_material',
                                     'prepare_material_ing'])]
        elif refuse == 'production':
            return [('production_remark_id', '!=', False),
                    ('state', 'in', ('finish_prepare_material', 'already_picking', 'progress'))]

        if state and state in ['finish_prepare_material', 'already_picking', 'waiting_rework',
                               'waiting_inventory_material', 'force_cancel_waiting_return']:

            return [('state', '=', state), ('in_charge_id', '=', self.env.user.partner_id.id)]
        elif state == "progress":
            if not feedback_on_rework:
                return [('state', '=', 'progress'),
                        ('in_charge_id', '=', self.env.user.partner_id.id),
                        ('feedback_on_rework', '=', None),
                        # ('date_planned_start', '<', after_day.strftime('%Y-%m-%d %H:%M:%S'))
                        ]
            else:
                return [('state', '=', "progress"),
                        ('in_charge_id', '=', self.env.user.partner_id.id),
                        ('feedback_on_rework', '!=', None),
                        # ('date_planned_start', '<', after_day.strftime('%Y-%m-%d %H:%M:%S'))
                        ]
        else:
            # locations = self.env["stock.location"].sudo().get_semi_finished_location_by_user(self._context.get("uid"))
            # location_cir = self.env["stock.location"].sudo().search([("is_circulate_location", '=', True)], limit=1).ids
            # location_domain = locations.ids + location_cir
            return [('state', '=', state),
                    # ('location_ids', 'in', location_domain),
                    # ('date_planned_start', '<', after_day.strftime('%Y-%m-%d %H:%M:%S'))
                    ]

    @api.multi
    def action_cancel(self):
        force_cancel = self._context.get("force_cancel")
        if force_cancel:
            state_domain = ["draft", "confirmed", "waiting_material",
                            "prepare_material_ing", "finish_prepare_material",
                            "already_picking", "progress", 'force_cancel_waiting_warehouse_inspection', "cancel",
                            "done"]
        else:
            state_domain = ["draft", "confirmed", "waiting_material", "cancel", "done"]
        for mo in self:
            if mo.state not in state_domain:
                raise UserError(u"不能取消已经开始生产的制造单 或者 相关的生产单已经开始生产无法取消SO")
        res = super(MrpProductionExtend, self.filtered(lambda x: x.state not in ["done"])).action_cancel()
        # for p in self:
        #     return_m = self.env["mrp.return.material"].with_context({
        #         'active_model': 'mrp.production',
        #         'active_id': p.id
        #     }).create({
        #         'production_id': p.id
        #     })
        #     move_raw = p.move_raw_ids.filtered(lambda x: x.state == 'done')
        #             if line.product_id.id == move.product_id.id:
        #                 line.return_qty += move.quantity_done
        #     return_m.no_confirm_return()
        # return_m.do_retrurn()
        return res

    def action_force_cancel_qingdian_return(self):
        view = self.env.ref('linkloving_mrp_extend.stock_return_material_form_view2')
        res = {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.return.material',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_return_type': 'progress_return',
            }
        }
        return res

    def action_cancel_and_return_material(self):

        self.action_force_cancel_waiting_return()
        # for p in self:
        #     if p.state == 'cancel':
        #         raise UserError(u"此单据已处于取消状态,无法退料")
        #     return_m = self.env["mrp.return.material"].with_context({
        #         'active_model': 'mrp.production',
        #         'active_id': p.id
        #     }).create({
        #         'production_id': p.id
        #     })
        #     move_raw = p.move_raw_ids.filtered(lambda x: x.state == 'done')
        #     for line in return_m.return_ids:
        #         for move in move_raw:
        #             if line.product_id.id == move.product_id.id:
        #                 line.return_qty += move.quantity_done
        #     return_m.no_confirm_return()
        #
        #     p.with_context({
        #         'force_cancel': True
        #     }).action_cancel()
        # return {
        #     "type": "ir.actions.client",
        #     "tag": "action_notify",
        #     "params": {
        #         "title": u"提示",
        #         "text": u"退料成功,并取消制造单",
        #         "sticky": False
        #     }
        # }

    def _generate_finished_moves(self):
        move = self.env['stock.move'].create({
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'location_id': self.product_id.property_stock_production.id,
            'location_dest_id': self.location_dest_id.id,
            'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
            'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
            'company_id': self.company_id.id,
            'production_id': self.id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
            'move_order_type': 'null' if self.move_finished_ids else 'manufacturing_orders',
            'propagate': False,
        })
        move.action_confirm()
        return move


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            produced = sum(production.move_finished_ids.mapped('quantity_done'))
            if wizard.product_qty < produced:
                raise UserError(
                    _("You have already processed %d. Please input a quantity higher than %d ") % (produced, produced))
            production.write({'product_qty': wizard.product_qty})
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')),
                                                                          production.product_uom_id)
            factor = production.product_uom_id._compute_quantity(production.product_qty - qty_produced,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            if production.is_rework:
                for line in production.rework_material_line_ids:
                    production.update_rework_material(line, production.product_qty)

            else:
                for line, line_data in lines:
                    production._update_raw_move(line, line_data)
            operation_bom_qty = {}
            for bom, bom_data in boms:
                for operation in bom.routing_id.operation_ids:
                    operation_bom_qty[operation.id] = bom_data['qty']
            self._update_product_to_produce(production, production.product_qty - qty_produced)
            moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves.do_unreserve()
            moves.action_assign()
            for wo in production.workorder_ids:
                operation = wo.operation_id

                if operation_bom_qty.get(operation.id):
                    cycle_number = math.ceil(
                        operation_bom_qty[operation.id] / operation.workcenter_id.capacity)  # TODO: float_round UP
                    wo.duration_expected = (operation.workcenter_id.time_start +
                                            operation.workcenter_id.time_stop +
                                            cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
                if production.product_id.tracking == 'serial':
                    quantity = 1.0
                else:
                    quantity = wo.qty_production - wo.qty_produced
                    quantity = quantity if (quantity > 0) else 0
                wo.qty_producing = quantity
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                # assign moves; last operation receive all unassigned moves
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(
                    lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(
                    lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_lot_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
                if wo.move_raw_ids.filtered(lambda x: x.product_id.tracking != 'none') and not wo.active_move_lot_ids:
                    wo._generate_lot_ids()

                    # @api.multi
                    # def change_prod_qty(self):
                    #     # self.mo_id.write({'state': 'waiting_material'})
                    #     return super(ChangeProductionQty, self).change_prod_qty()


class ConfirmProduction(models.TransientModel):
    _name = 'confirm.production'

    mo_id = fields.Many2one('mrp.production', 'Manufacturing Order', required=True)
    product_qty = fields.Float(
        'Quantity To Produce',
        digits=dp.get_precision('Product Unit of Measure'), required=True)

    @api.model
    def default_get(self, fields):
        res = super(ConfirmProduction, self).default_get(fields)
        if 'mo_id' in fields and not res.get('mo_id') and self._context.get(
                'active_model') == 'mrp.production' and self._context.get('active_id'):
            res['mo_id'] = self._context['active_id']
        if 'product_qty' in fields and not res.get('product_qty') and res.get('mo_id'):
            res['product_qty'] = self.env['mrp.production'].browse(res.get['mo_id']).product_qty
        return res

    @api.multi
    def confirm_production(self):
        qty_wizard = self.env['change.production.qty'].create({
            'mo_id': self.mo_id.id,
            'product_qty': self.product_qty,
        })
        qty_wizard.change_prod_qty()


class MrpProductionProduceExtend(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.model
    def default_get(self, fields):
        res = super(MrpProductionProduceExtend, self).default_get(fields)
        if res.get('production_id'):
            production = self.env['mrp.production'].browse(res.get('production_id'))
        else:
            production = self.env['mrp.production'].browse(self._context.get('active_id'))
        quantity = production.product_qty - production.qty_unpost
        quantity = quantity if (quantity > 0) else 0
        res["product_qty"] = quantity
        return res

    @api.multi
    def do_produce(self):
        self._do_produce()
        return {'type': 'ir.actions.act_window_close'}

    def _do_produce(self):
        quantity = self.product_qty
        if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) > 0:
            feedback = self.feedback_create(self.product_qty)  # 产出  生成品检单
            self.production_id.feedback_on_rework = False
            location = self.env["stock.location"].sudo().search([("is_circulate_location", "=", True)], limit=1)
            if location and location.putaway_strategy_id and location.putaway_strategy_id.fixed_location_ids:
                fixed_location_ids = location.putaway_strategy_id.fixed_location_ids

                if self.production_id.product_id.categ_id.id in fixed_location_ids.mapped("category_id").ids:  # 半成品入库
                    try:
                        feedback.action_post_inventory()
                    except ValueError, e:
                        feedback.unlink()
                        raise UserError(e)

    def do_produce_and_post_inventory(self):
        quantity = self.product_qty
        if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
            return
            # raise UserError(u"请填写生产数量!")
            # for move in moves.filtered(lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel')):
            #     if move.unit_factor:
            #         qty = quantity * move.unit_factor
            #         if qty > move.product_uom_qty:
            #             move.quantity_done_store += move.product_uom_qty
            #         else:
            #             move.quantity_done_store += qty
            # move.action_done()
            # self.production_id.post_inventory()
            # if move.product_id.virtual_available < 0:
            #     move.quantity_done_store = move.quantity_done_store / (1 + move.bom_line_id.scrap_rate / 100)
        moves = self.production_id.move_finished_ids.filtered(
            lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel'))
        if not moves:  # and self.production_id.qty_unpost > self.production_id.qty_produced:
            qty = quantity
            copy_moves = self.production_id.move_finished_ids.filtered(
                lambda x: x.product_id.id == self.production_id.product_id.id)
            if copy_moves:
                new_move = copy_moves[0].copy(default={'quantity_done': qty,
                                                   'ordered_qty': qty,
                                                   'product_uom_qty': qty,
                                                   'production_id': self.production_id.id
                                                   })
            else:  # stock——move 被意外取消
                new_move = self.production_id._generate_finished_moves()
                new_move.quantity_done = qty
            new_move.action_confirm()
        for move in moves:
            if move.product_id.id == self.production_id.product_id.id:
                move.quantity_done_store += quantity
            elif move.unit_factor:
                move.quantity_done_store += quantity * move.unit_factor
        self.check_finished_move_lots()

        self.production_id.post_inventory()

    # 创建品捡单, 如果有其他处于等待品捡的单据就合并起来
    def feedback_create(self, qty_produced):
        draft_sum_qty = qty_produced
        feedback_draft = self.env["mrp.qc.feedback"]
        if self.production_id.qc_feedback_ids:
            feedback_draft = self.production_id.qc_feedback_ids.filtered(lambda x: x.state == 'draft')
            draft_sum_qty += sum(feedback_draft.mapped("qty_produced"))
        feedback = self.env['mrp.qc.feedback'].create({
            'feedback_backorder_id': self.production_id.feedback_on_rework.id,
            'qty_produced': draft_sum_qty,
            'production_id': self.production_id.id,
            'product_id': self.production_id.product_id.id,
        })
        feedback_draft.unlink()
        return feedback


class ReturnOfMaterial(models.Model):
    _name = 'mrp.return.material'

    def _get_default_return_location_id(self):
        return self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

    def _get_default_location_id(self):
        return self.env['stock.location'].search([('usage', '=', 'production')], limit=1)

    @api.model
    def _default_return_line(self):
        product_ids = []
        if self._context.get('active_id') and self._context.get('active_model') == "mrp.production":
            mrp_production_order = self.env['mrp.production'].browse(self._context['active_id'])
            if mrp_production_order.product_id.bom_ids:
                product_ids = mrp_production_order.product_id.bom_ids[0].bom_line_ids.mapped(
                    'product_id').ids
            if mrp_production_order.process_id.is_rework:
                product_ids = mrp_production_order.rework_material_line_ids.mapped(
                    'product_id').ids
            lines = []
            for l in product_ids:
                obj = self.env['return.material.line'].create({
                    'return_qty': 0,
                    'product_id': l,
                })
                lines.append(obj.id)
            return lines

    return_ids = fields.One2many('return.material.line', 'return_id', default=_default_return_line)
    name = fields.Char(
        'Reference', default=lambda self: _('New'),
        copy=False, readonly=True, required=True, )
    owner_id = fields.Many2one('res.partner', 'Owner', )
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    # picking_id = fields.Many2one('stock.picking', 'Picking', states={'done': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'production')]",
        required=True, default=_get_default_location_id)
    return_location_id = fields.Many2one(
        'stock.location', 'Return Location', default=_get_default_return_location_id,
        domain="[('usage', '=', 'internal')]", )
    return_qty = fields.Float('Return Quantity', default=0.0, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checking', u'等待检验退料中'),
        ('done', u'已完成')], string='Status', default="draft")
    production_id = fields.Many2one('mrp.production', 'Production')

    return_type = fields.Selection(string=u"退料单类型",
                                   selection=[('normal', u'正常'),
                                              ('progress_return', u'生产中的退料'), ],
                                   required=False,
                                   default='normal')

    def get_normal_return_order(self, order_id, read=False):
        """
            获取正常产成之后的退料单
        :param order_id: 制造单号
        :param read: 结果返回类型 是json还是obj
        :return: 根据read来决定
        """
        domain = [('production_id', '=', order_id), ('state', '=', 'draft'), ("return_type", "=", "normal")]
        if read:
            return self.search_read(domain, limit=1)
        else:
            return self.search(domain, limit=1)

    def get_progress_return_order(self, order_id, read=False):
        """
            搜索强制退料的时候生成的退料单
        :param order_id: 制造单号
        :param read: 结果返回类型 是json还是obj
        :return: 根据read来决定
        """
        domain = [('production_id', '=', order_id), ('state', '=', 'checking'), ("return_type", "=", "progress_return")]
        if read:
            return self.search_read(domain, limit=1)
        else:
            return self.search(domain, limit=1)
    @api.multi
    def do_return(self):
        """
        网页用:如果是仓库检验退料阶段, 则退料回库 并且mo标记完成, 否则 只是改变mo状态
        :return:
        """
        if self._context.get('is_checking'):
            for r in self.return_ids:
                if r.return_qty == 0:
                    continue
                move = self.env['stock.move'].create(self._prepare_move_values(r))
                move.action_done()
            self.return_ids.create_scraps()
            self.production_id.button_mark_done()
            self.state = 'done'
        else:
            self.production_id.write({'state': 'waiting_warehouse_inspection'})
        return True

    def do_force_cancel_return(self):
        """
        强制取消退料,  如果单据状态是draft
        :return:
        """
        if self.state == 'draft':
            self.state = 'checking'
            self.production_id.state = 'force_cancel_waiting_warehouse_inspection'  # mo状态往下跳
        elif self.state == 'checking':
            self.generate_move_and_action_done()
            self.production_id.with_context({
                'force_cancel': True
            }).action_cancel()

    def generate_move_and_action_done(self):
        self.ensure_one()
        for r in self.return_ids:
            if r.return_qty == 0:
                continue
            move = self.env['stock.move'].create(self._prepare_move_values(r))
            move.action_done()
        self.state = 'done'

    # 不需要确认的退料
    @api.multi
    def no_confirm_return(self):
        for r in self.return_ids:
            if r.return_qty == 0:
                continue  # raise UserError(u"%s: 系统自动退料遇到问题" % self.production_id.name)
            move = self.env['stock.move'].create(self._prepare_move_values(r))
            r.return_qty = 0
            move.action_done()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mrp.return.material') or 'New'

        obj = super(ReturnOfMaterial, self).create(vals)
        if vals.get('return_ids'):
            for return_id in vals['return_ids']:
                self.env['return.material.line'].browse(return_id[1]).return_id = obj.id
        return obj

    def action_done(self):
        """
        分为正常退料流程和强制退料流程
        :return:
        """
        if self.return_type == 'normal':
            self.do_return()
        elif self.return_type == 'progress_return':
            self.do_force_cancel_return()

        return {'type': 'ir.actions.act_window_close'}

    def _prepare_move_values(self, product):
        self.ensure_one()

        return {
            'name': '退料 %s' % self.production_id.name,
            'product_id': product.product_id.id,
            'product_uom': product.product_id.uom_id.id,
            'product_uom_qty': product.return_qty,
            'quantity_done': product.return_qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.return_location_id.id,
            'production_id': self.production_id.id,
            'state': 'confirmed',
            'origin': '退料 %s' % self.production_id.name,
            'is_return_material': True,
            # 'restrict_partner_id': self.owner_id.id,
            # 'picking_id': self.picking_id.id
        }


class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    return_qty = fields.Float(string='Return Quantity', default=0)


class WareHouseArea(models.Model):
    _name = 'warehouse.area'

    name = fields.Char('Location Description')


class SimStockMove(models.Model):
    _name = 'sim.stock.move'

    def _compute_stock_moves(self):
        for sim_move in self:
            sim_move.stock_moves = []
            for move in sim_move.production_id.move_raw_ids:
                if move.product_id == sim_move.product_id:
                    sim_move.stock_moves = sim_move.stock_moves + move

    def _compute_quantity_done(self):
        for sim_move in self:
            # move_to_fill = self.env['stock.move'].search([('production_id', '=', sim_move.production_id.id)])
            sim_move.quantity_done = 0
            for move in sim_move.production_id.move_raw_ids:
                if move.product_id == sim_move.product_id and not move.is_return_material and move.state == "done":
                    sim_move.quantity_done += move.quantity_done

    def _default_product_uom_qty(self):
        if self:
            boms, lines = self[0].production_id.bom_id.explode(self[0].production_id.product_id,
                                                               self[0].production_id.product_qty)
        for sim_move in self:

            if sim_move.stock_moves:
                for bom_line, datas in lines:
                    if bom_line.product_id.id == sim_move.product_id.id:
                        sim_move.product_uom_qty = datas['qty']
                        # for l in sim_move.stock_moves:
                        #     if l.is_over_picking or l.is_return_material:
                        #         continue
                        #     if l.state != "cancel":
                        #         sim_move.product_uom_qty += l.product_uom_qty
                    # FIXME:应该在rework model allen
                    if sim_move.production_id.is_rework:
                        production_id = sim_move.production_id

                        sim_move.product_uom_qty = production_id.rework_material_line_ids.filtered(
                            lambda x: x.product_id.id == sim_move.product_id.id).product_qty

    def _default_qty_available(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.qty_available = sim_move.stock_moves[0].qty_available

    def _default_virtual_available(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.virtual_available = sim_move.stock_moves[0].virtual_available

    def _default_suggest_qty(self):
        for sim_move in self:
            sim_move.suggest_qty = sim_move.product_uom_qty * (1 + sim_move.bom_line_id.scrap_rate * 0.01)
            # if sim_move.stock_moves:
            #     for move in sim_move.stock_moves:
            #         if move.state != "cancel":
            #             sim_move.suggest_qty = move.suggest_qty
            #             break

    def _compute_quantity_available(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.quantity_available = sim_move.stock_moves[0].quantity_available

    def _compute_return_qty(self):
        for sim_move in self:
            move_to_return = self.env['stock.move'].search([('production_id', '=', sim_move.production_id.id)])
            sim_move.return_qty = 0
            for move in move_to_return:
                if move.product_id == sim_move.product_id and move.is_return_material:
                    sim_move.return_qty += move.product_qty

    def _compute_procurement_id(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.procurement_id = sim_move.stock_moves[0].procurement_id

    def _compute_raw_material_production_id(self):
        for sim_move in self:
            if sim_move.stock_moves:
                sim_move.raw_material_production_id = sim_move.stock_moves[0].raw_material_production_id

    @api.multi
    def _compute_product_type(self):
        circulate_location = self.env["stock.location"].search([("is_circulate_location", "=", True)], limit=1)
        semi_finished_location = self.env["stock.location"].search([("is_semi_finished_location", "=", True)], limit=1)
        fixed_location_ids = self.env["stock.fixed.putaway.strat"]
        semi_finished_fixed_location_ids = self.env["stock.fixed.putaway.strat"]
        if circulate_location and circulate_location.putaway_strategy_id and circulate_location.putaway_strategy_id.fixed_location_ids:
            fixed_location_ids = circulate_location.putaway_strategy_id.fixed_location_ids
        if semi_finished_location and semi_finished_location.putaway_strategy_id and semi_finished_location.putaway_strategy_id.fixed_location_ids:
            semi_finished_fixed_location_ids = semi_finished_location.putaway_strategy_id.fixed_location_ids
        for sim in self:
            if sim.product_id.categ_id.id in fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "semi-finished"  # 半成品流转
            elif sim.product_id.categ_id.id in semi_finished_fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "real_semi_finished"  # 半成品
            else:
                sim.product_type = "material"

    @api.multi
    def _compute_bom_line_id(self):
        for sim_move in self:
            boms, lines = sim_move.production_id.bom_id.explode(sim_move.production_id.product_id,
                                                                sim_move.production_id.product_qty)
            if sim_move.stock_moves:
                for bom_line, datas in lines:
                    if bom_line.product_id.id == sim_move.product_id.id:
                        sim_move.bom_line_id = bom_line.id

    @api.multi
    def _compute_remaining_qty(self):
        for sim_move in self:
            remaining_qty = sim_move.suggest_qty - sim_move.quantity_done
            sim_move.remaining_qty = remaining_qty if remaining_qty > 0 else 0

    product_id = fields.Many2one('product.product', )
    production_id = fields.Many2one('mrp.production')
    stock_moves = fields.One2many('stock.move', compute=_compute_stock_moves)
    raw_material_production_id = fields.Many2one('mrp.production', compute=_compute_raw_material_production_id)
    procurement_id = fields.Many2one('procurement.order', 'Procurement', compute=_compute_procurement_id)
    production_state = fields.Selection(related='production_id.state', readonly=True)

    quantity_done = fields.Float(default=0, compute=_compute_quantity_done)
    product_uom_qty = fields.Float(compute=_default_product_uom_qty)
    qty_available = fields.Float(compute=_default_qty_available)
    virtual_available = fields.Float(compute=_default_virtual_available)
    suggest_qty = fields.Float(compute=_default_suggest_qty)
    quantity_available = fields.Float(compute=_compute_quantity_available, )
    return_qty = fields.Float(compute=_compute_return_qty)
    over_picking_qty = fields.Float()
    quantity_ready = fields.Float()
    area_id = fields.Many2one(related='product_id.area_id')
    product_type = fields.Selection(string="物料类型", selection=[('semi-finished', '流转品'),
                                                              ('material', '原材料'),
                                                              ('real_semi_finished', '半成品')],
                                    required=False, compute="_compute_product_type")
    is_prepare_finished = fields.Boolean(u"是否备货完成")

    bom_line_id = fields.Many2one(comodel_name='mrp.bom.line', compute='_compute_bom_line_id')

    remaining_qty = fields.Float(string=u"待领数量", compute='_compute_remaining_qty')


class ReturnMaterialLine(models.Model):
    _name = 'return.material.line'

    @api.multi
    def _compute_product_type(self):
        circulate_location = self.env["stock.location"].search([("is_circulate_location", "=", True)], limit=1)
        semi_finished_location = self.env["stock.location"].search([("is_semi_finished_location", "=", True)], limit=1)
        fixed_location_ids = self.env["stock.fixed.putaway.strat"]
        semi_finished_fixed_location_ids = self.env["stock.fixed.putaway.strat"]
        if circulate_location and circulate_location.putaway_strategy_id and circulate_location.putaway_strategy_id.fixed_location_ids:
            fixed_location_ids = circulate_location.putaway_strategy_id.fixed_location_ids
        if semi_finished_location and semi_finished_location.putaway_strategy_id and semi_finished_location.putaway_strategy_id.fixed_location_ids:
            semi_finished_fixed_location_ids = semi_finished_location.putaway_strategy_id.fixed_location_ids
        for sim in self:
            if sim.product_id.categ_id.id in fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "semi-finished"  # 半成品流转
            elif sim.product_id.categ_id.id in semi_finished_fixed_location_ids.mapped("category_id").ids:
                sim.product_type = "real_semi_finished"  # 半成品
            else:
                sim.product_type = "material"

    product_id = fields.Many2one('product.product')
    return_qty = fields.Float('Return Quantity', readonly=False)
    return_id = fields.Many2one('mrp.return.material')
    product_type = fields.Selection(string="物料类型", selection=[('semi-finished', '流转品'),
                                                              ('material', '原材料'),
                                                              ('real_semi_finished', '半成品')],
                                    required=False, compute="_compute_product_type")


    @api.multi
    def create_scraps(self):
        if self[0].return_id.production_id.process_id.is_rework:  # 重工
            return
        if len(self) > 0:
            total_qty = 0
            for fd in self[0].return_id.production_id.qc_feedback_ids:
                total_qty += fd.qty_produced
            boms, lines = self[0].return_id.production_id.bom_id.explode(self[0].return_id.production_id.product_id,
                                                                         total_qty)

        scrap_env = self.env["production.scrap"]
        for line in self:
            uom_qty = 0
            for bom_line, datas in lines:
                if bom_line.product_id.id == line.product_id.id:
                    uom_qty = datas['qty']
                    break
            done_move = line.return_id.production_id.sim_stock_move_lines.filtered(
                lambda x: x.product_id.id == line.product_id.id)
            if uom_qty == 0:
                continue
            if done_move and len(done_move) == 1:
                done_qty = done_move.quantity_done
                return_qty = done_move.return_qty
            else:
                continue
            scrap_qty = done_qty - uom_qty - return_qty
            if scrap_qty <= 0:
                continue

            scrap_env += self.env["production.scrap"].create({
                'production_id': line.return_id.production_id.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_id.uom_id.id,
                'scrap_qty': scrap_qty
            })
        scrap_env.do_scrap()

class HrEmployeeExtend(models.Model):
    _inherit = 'hr.employee'

    is_worker = fields.Boolean('Is Worker', default=False)
    now_mo_id = fields.Many2one('mrp.production')


# 每个工人所处在的生产线
class LLWorkerLine(models.Model):
    _name = 'worker.line'

    @api.multi
    def _compute_amount_of_money(self):
        for one in self:
            one.amount_of_money = one.unit_price * one.xishu

    @api.multi
    def _compute_line_state(self):
        for line in self:
            if line.worker_time_line_ids:
                worker_time_line_ids_sorted = sorted(line.worker_time_line_ids, key=lambda d: d.start_time)
                line.line_state = worker_time_line_ids_sorted[len(worker_time_line_ids_sorted) - 1].state
            else:
                line.line_state = 'online'

    @api.multi
    def _compute_spent_time(self):
        for line in self:
            line.spent_time = line.cal_worker_spent_time() / 3600.0

    worker_id = fields.Many2one('hr.employee')
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    unit_price = fields.Float(related='production_id.unit_price', string='Unit Price')
    mo_type = fields.Selection(related='production_id.mo_type', string='Mo Type')
    xishu = fields.Float(default=1.0, string='Rate')
    amount_of_money = fields.Float(compute=_compute_amount_of_money)
    worker_time_line_ids = fields.One2many('worker.time.line', 'worker_line_id')
    spent_time = fields.Float(compute='_compute_spent_time')
    line_state = fields.Selection(
        [
            ('online', 'Normal'),
            ('offline', 'On Leave'),
            ('outline', 'Exit'),
        ], compute=_compute_line_state)

    def create_time_line(self):
        self.env['worker.time.line'].create({
            'worker_line_id': self.id,
            'start_time': fields.datetime.now(),
        })

    def get_newest_time_line(self):
        worker_time_line_ids_sorted = sorted(self.worker_time_line_ids, key=lambda d: d.start_time)
        return worker_time_line_ids_sorted[len(worker_time_line_ids_sorted) - 1]

    @api.multi
    def change_worker_state(self, state):
        for line in self:
            if not line.worker_time_line_ids:
                continue
            else:
                new_time_line = line.get_newest_time_line()
                if new_time_line.state != state:  # 若状态改变
                    if state == 'outline':
                        new_time_line.worker_id.now_mo_id = None
                    else:
                        new_time_line.worker_id.now_mo_id = new_time_line.production_id.id
                    new_time_line.offline_set_time()
                    self.env['worker.time.line'].create({
                        'start_time': fields.datetime.now(),
                        'worker_line_id': line.id,
                        'state': state,
                    })

    # 计算每个工人的所花费的时间
    # @api.multi
    def cal_worker_spent_time(self):
        # for worker_line in self:
        sum_time = 0
        for time_line in self.worker_time_line_ids:
            if time_line.state == 'online' and time_line.end_time:
                sum_time += time_line.cal_interval_of_time_line()

        return sum_time


class LLWorkerTimeLine(models.Model):
    _name = 'worker.time.line'

    start_time = fields.Datetime(default=fields.datetime.now())
    end_time = fields.Datetime()
    state = fields.Selection(
        [
            ('online', 'Normal'),
            ('offline', 'On leave'),
            ('outline', 'Exit'),
        ], default='online')

    worker_line_id = fields.Many2one('worker.line')
    worker_id = fields.Many2one(related='worker_line_id.worker_id', string="Worker")
    production_id = fields.Many2one(related='worker_line_id.production_id', string='Manufacturing Order')

    def offline_set_time(self):
        self.end_time = fields.datetime.now()

    def cal_interval_of_time_line(self):
        return (fields.Datetime.from_string(self.end_time) - fields.Datetime.from_string(self.start_time)).seconds


class MrpQcFeedBack(models.Model):
    _name = 'mrp.qc.feedback'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def _compute_qc_rate(self):
        for qc in self:
            if qc.qty_produced:
                qc.qc_rate = qc.qc_test_qty / qc.qty_produced * 100
            else:
                qc.qc_rate = 0

    @api.multi
    def _compute_qc_fail_rate(self):
        for qc in self:
            if qc.qc_test_qty != 0:
                qc.qc_fail_rate = qc.qc_fail_qty / qc.qc_test_qty * 100
            else:
                qc.qc_fail_rate = 0

    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)
    name = fields.Char('Name', index=True, required=True)
    production_id = fields.Many2one('mrp.production', ondelete='restrict')
    qty_produced = fields.Float()
    qc_test_qty = fields.Float(string='Sampling Quantity')
    qc_rate = fields.Float(compute='_compute_qc_rate')
    qc_fail_qty = fields.Float('NG Quantity')
    qc_fail_rate = fields.Float('Defect Rate', compute='_compute_qc_fail_rate')
    qc_note = fields.Text(string='Note')
    qc_img = fields.Binary(string='Quality Inspection Image')

    product_id = fields.Many2one('product.product', related='production_id.product_id')

    qc_imgs = fields.One2many(comodel_name="qc.feedback.img", inverse_name="feedback_id", string="品检图片",
                              required=False, )

    feedback_backorder_id = fields.Many2one("mrp.qc.feedback", u"返工于")
    state = fields.Selection(string=u"状态", selection=[('draft', u'等待品检'),
                                                      ('qc_ing', u'品检中'),
                                                      ('qc_success', u'等待入库'),
                                                      ('qc_fail', u'品检失败'),
                                                      ('check_to_rework', u'已确认返工'),
                                                      ('alredy_post_inventory', u'已入库')], required=False,
                             default='draft')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mrp.qc.feedback') or 'New'
        if not vals.get("production_id"):
            raise UserError(u"缺少对应的生产单ID")
        return super(MrpQcFeedBack, self).create(vals)

    @api.multi
    def unlink(self):
        for qc in self:
            if qc.state not in ["draft"]:
                raise UserError(u"无法删除品检单据")
        return super(MrpQcFeedBack, self).unlink()

    # 等待品捡 -> 品捡中
    def action_start_qc(self):
        self.state = "qc_ing"

    # 品捡中 -> 品捡完成
    def action_qc_success(self):
        if self.qc_test_qty <= 0:
            raise UserError(u"品检数量不能为0")
        self.state = "qc_success"

        if self.production_id.state in ['waiting_rework', 'waiting_inspection_finish']:
            self.production_id.state = self.production_id.compute_order_state()

    # 品捡中 -> 品捡失败
    def action_qc_fail(self):
        if self.qc_test_qty <= 0:
            raise UserError(u"品检数量不能为0")
        self.state = "qc_fail"
        if self.production_id.state in ['waiting_rework', 'waiting_inspection_finish']:
            self.production_id.state = self.production_id.compute_order_state()

    # 品捡成功 -> 已入库
    def action_post_inventory(self):
        if self.state == 'alredy_post_inventory':
            raise UserError(u"该单据已入库,无需再重复入库")
        if hasattr(self.production_id, "outside_type"):
            if self.production_id.outside_type in ['outsourcing',
                                                   'all_outside'] and not self.production_id.mo_invoice_count:
                if self.production_id.outside_type == 'outsourcing':
                    self.production_id._prepare_invoice(self.production_id.outsourcing_supplier_id, self.qty_produced)
                else:
                    self.production_id._prepare_invoice(self.production_id.supplier_id, self.qty_produced)
        mrp_product_produce = self.env['mrp.product.produce'].with_context({'active_id': self.production_id.id})
        produce = mrp_product_produce.create({
            'product_qty': self.qty_produced,
            'production_id': self.production_id.id,
            'product_uom_id': self.production_id.product_uom_id.id,
            'product_id': self.production_id.product_id.id,
        })
        produce.do_produce_and_post_inventory()

        self.state = "alredy_post_inventory"

    def action_back_state(self):
        if self.state == 'alredy_post_inventory':
            self.state = 'qc_success'

    # 品捡失败 -> 返工
    def action_check_to_rework(self):
        if self.production_id.state in ["waiting_rework", "done"]:

            self.state = "check_to_rework"
            p_time = self.env["production.time.record"].create({
                'production_id': self.production_id.id,
                'start_time': fields.Datetime.now(),
                'record_type': 'rework'
            })
            self.production_id.state = "progress"
            self.production_id.feedback_on_rework = self
            if 'confirm_rework_replan_mo' in dir(self.production_id):
                self.production_id.confirm_rework_replan_mo()
        else:
            raise UserError(u"请先完成生产单,才能进行返工")

    @api.model
    def _needaction_domain_get(self):
        """ Returns the domain to filter records that require an action
            :return: domain or False is no action

        """
        state = self._context.get('state')

        return [('state', '=', state)]


class MrpQcFeedBackImg(models.Model):
    _name = "qc.feedback.img"

    qc_img = fields.Binary(u"品检图片")
    feedback_id = fields.Many2one("mrp.qc.feedback")


class MultiHandleWorker(models.TransientModel):
    _name = 'multi.handle.worker'

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        employees = self.env['hr.employee'].search([('id', 'in', active_ids)])
        for em in employees:
            em.is_worker = True


class StockComfirmationExtend(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        # 分拣 和 正常过程都只记录选择
        if self.pick_id.state in ["picking",
                                  "validate"] and self.pick_id.picking_type_code == 'incoming':  # 如果是处于分拣流程则只记录一下选择
            if self.pick_id.state == 'validate':
                self.pick_id.write({
                    'state': 'waiting_in'
                })
            self.pick_id.is_cancel_backorder = cancel_backorder
            return {'type': 'ir.actions.act_window_close'}
        else:
            return super(StockComfirmationExtend, self)._process(cancel_backorder)


class StcokPickingExtend(models.Model):
    _inherit = 'stock.picking'

    qc_note = fields.Text(string='Quality Inspection Image')
    qc_img = fields.Binary()
    post_img = fields.Binary()
    post_area_id = fields.Many2one('stock.location.area')
    express_img = fields.Binary("物流图片")
    qc_result = fields.Selection(string=u"品检结果", selection=[('no_result', u'为以前的品检单,无品检结果记录'),
                                                            ('fail', u'品检失败'),
                                                            ('success', u'品检通过'), ], default='no_result', )
    transfer_way = fields.Selection(string=u'入库方式',
                                    selection=[('draft', u'未选择'),
                                               ('all', u'全部入库'),
                                               ('part', u'仅良品入库,不良品退回')],
                                    default='draft',
                                    copy=False)

    state = fields.Selection(selection_add=[
        ('picking', u'分拣中')])

    is_picking_process = fields.Boolean(string=u'是否进入分拣流程', default=False, copy=False)
    is_cancel_backorder = fields.Boolean(string=u'是否创建欠单', copy=False)

    # @api.multi
    # def do_new_transfer(self):
    #     for pick in self:
    #         if pick.is_picking_process:#如果是分拣流程,则不做处理先记录下来
    #             pick.is_create_backorder

    @api.multi
    def do_new_transfer(self):
        for pick in self:
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
            # In draft or with no pack operations edited yet, ask if we can just do everything
            if pick.state not in ["picking"]:  # 去分拣 不需要做此判断
                if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                    # If no lots when needed, raise error
                    picking_type = pick.picking_type_id
                    if (picking_type.use_create_lots or picking_type.use_existing_lots):
                        for pack in pick.pack_operation_ids:
                            if pack.product_id and pack.product_id.tracking != 'none':
                                raise UserError(
                                        _(
                                            'Some products require lots/serial numbers, so you need to specify those first!'))
                    raise UserError(u"此次入库数量为0, 请选择全部入库或者退回!")
                # view = self.env.ref('stock.view_immediate_transfer')
                # wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})
                # # TDE FIXME: a return in a loop, what a good idea. Really.
                # return {
                #     'name': _('Immediate Transfer?'),
                #     'type': 'ir.actions.act_window',
                #     'view_type': 'form',
                #     'view_mode': 'form',
                #     'res_model': 'stock.immediate.transfer',
                #     'views': [(view.id, 'form')],
                #     'view_id': view.id,
                #     'target': 'new',
                #     'res_id': wiz.id,
                #     'context': self.env.context,
                # }

            # Check backorder should checpurk for other barcodes
            if pick.check_backorder():
                view = self.env.ref('stock.view_backorder_confirmation')
                wiz = self.env['stock.backorder.confirmation'].create({'pick_id': pick.id})
                # TDE FIXME: same reamrk as above actually
                return {
                    'name': _('Create Backorder?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.backorder.confirmation',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            for operation in pick.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if operation.qty_done > 0:
                    operation.write({'product_qty': operation.qty_done})
                else:
                    pack_operations_delete |= operation
            if pack_operations_delete:
                pack_operations_delete.unlink()

            if pick.picking_type_code == 'incoming':
                pick.is_cancel_backorder = True
                pick.state = 'waiting_in'
            else:
                pick.do_transfer()
        return

    @api.multi
    def to_stock(self):
        for pick in self:
            if all(move.state not in ["done", "cancel"] for move in pick.move_lines):
                # if pick.move_lines.filtered(lambda x: x.state not in ["done", "cancel"]):
                confirmation = self.env["stock.backorder.confirmation"].create({
                    'pick_id': pick.id
                })
                confirmation._process(cancel_backorder=pick.is_cancel_backorder)
            # 既有完成又有可用的单子, 肯定有问题的!!!
            elif any(move.state in ["done"] for move in pick.move_lines) and any(
                            move.state == "assigned" for move in pick.move_lines):
                raise UserError(u"库存异动单异常,请联系管理员解决")
            if sum(pick.pack_operation_product_ids.mapped("qty_done")) == 0:
                raise UserError(u"出货数量不能全部为0")
        return super(StcokPickingExtend, self).to_stock()

    # 分拣完成
    @api.multi
    def action_picking_done(self):
        # self.is_picking_process = False
        self.state = 'waiting_in'

    @api.multi
    def action_check_pass(self):
        self.write({
            'qc_result': 'success'
        })
        return super(StcokPickingExtend, self).action_check_pass()

    @api.multi
    def action_check_fail(self):
        self.write({
            'qc_result': 'fail'
        })
        return super(StcokPickingExtend, self).action_check_fail()

    def confirm_transfer_way(self):
        if any([x.rejects_qty > 0.0 for x in self.pack_operation_ids]):  # 若有一个不良品大于0
            return self.action_view_choose_transfer_way()
        else:
            return self.do_new_transfer()

    # 分拣
    def to_picking(self):
        if any([x.rejects_qty > 0.0 for x in self.pack_operation_ids]):  # 若有一个不良品大于0
            # self.is_picking_process = True
            context = dict(self._context)
            context.update({'is_all_transfer_in': False})
            self.with_context(context).choose_transfer_way()
            self.state = 'picking'
            return self.do_new_transfer()
        else:
            raise UserError(u"没有不良品无法进入分拣流程.")

    def action_view_choose_transfer_way(self):
        view = self.env.ref('linkloving_mrp_extend.view_choose_transfer_way')
        return {
            'name': u'选择入库方式',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.transfer.way',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_picking_id': self.id, },
        }

    def choose_transfer_way(self):
        is_all = self._context.get("is_all_transfer_in")
        last_transfer_way = self.transfer_way
        if last_transfer_way == 'part':
            for pack in self.pack_operation_product_ids:
                pack.qty_done = pack.qty_done + pack.rejects_qty

        if is_all:  # 全部入库
            self.transfer_way = 'all'
        else:
            self.transfer_way = 'part'
        # if not self.picking_id.check_backorder():  # 此条件是货全都收全了, 所以要提前修改数量
        if self.transfer_way == 'part':
            for pack in self.pack_operation_product_ids:
                pack.qty_done = pack.qty_done - pack.rejects_qty


class stock_transfer_way(models.TransientModel):
    _name = 'stock.transfer.way'

    picking_id = fields.Many2one("stock.picking")

    def choose_transfer_way(self):
        self.picking_id.choose_transfer_way()
        # is_all = self._context.get("is_all_transfer_in")
        # last_transfer_way = self.picking_id.transfer_way
        # if last_transfer_way == 'part':
        #     for pack in self.picking_id.pack_operation_product_ids:
        #         pack.qty_done = pack.qty_done + pack.rejects_qty
        #
        # if is_all:  # 全部入库
        #     self.picking_id.transfer_way = 'all'
        # else:
        #     self.picking_id.transfer_way = 'part'
        # # if not self.picking_id.check_backorder():  # 此条件是货全都收全了, 所以要提前修改数量
        # if self.picking_id.transfer_way == 'part':
        #     for pack in self.picking_id.pack_operation_product_ids:
        #         pack.qty_done = pack.qty_done - pack.rejects_qty

        return self.picking_id.do_new_transfer()


#
# class StockBackorderConfirmation(models.TransientModel):
#     _inherit = 'stock.backorder.confirmation'
#
#     def qty_done_recompute_transfer_way(self):
#         pass
#         # if self.pick_id.transfer_way == 'part':
#         #     for pack in self.pick_id.pack_operation_product_ids:
#         #         pack.qty_done = pack.qty_done - pack.rejects_qty
#
#     @api.multi
#     def process(self):
#         self.qty_done_recompute_transfer_way()
#         return super(StockBackorderConfirmation, self).process()
#
#     @api.multi
#     def process_cancel_backorder(self):
#         self.qty_done_recompute_transfer_way()
#         return super(StockBackorderConfirmation, self).process_cancel_backorder()


class StockPackOperationExtend(models.Model):
    _inherit = 'stock.pack.operation'

    @api.multi
    def _compute_receivied_qty(self):
        for pack in self:
            if pack.picking_id.transfer_way == 'part':  # and pack.picking_id.state in ["waiting_in", "done"]
                pack.receivied_qty = pack.qty_done + pack.rejects_qty
            else:
                pack.receivied_qty = pack.qty_done

    rejects_qty = fields.Float(string=u"不良品", default=0)
    receivied_qty = fields.Float(string=u'收到的数量', compute='_compute_receivied_qty',
                                 digits=dp.get_precision('Product Unit of Measure'))
    # accept_qty = fields.Float(string=u'良品', compute='_compute_accept_qty')


class ProcurementOrderExtend(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrderExtend, self)._prepare_mo_vals(bom)
        # 解析原单据
        self.parse_origin_and_update_dic(res)

        res.update({'state': 'draft',
                    'process_id': bom.process_id.id,
                    'unit_price': bom.process_id.unit_price,
                    'mo_type': bom.mo_type,
                    'hour_price': bom.hour_price,
                    'in_charge_id': bom.process_id.partner_id.id,
                    'product_qty': self.product_qty if self.not_base_on_available else self.get_actual_require_qty(),
                    # 'date_planned_start': fields.Datetime.to_string(self._get_date_planned_from_today()),
                    # 'date_planned_finished':
                    })
        return res

    def _get_date_planned_from_today(self):
        format_date_planned = fields.Datetime.from_string(fields.Datetime.now())
        date_planned = format_date_planned - relativedelta(days=self.product_id.produce_delay or 0.0)
        date_planned = date_planned - relativedelta(days=self.company_id.manufacturing_lead)
        return date_planned

    def parse_origin_and_update_dic(self, dict):
        # 解析原单据
        if self.origin:
            origin_names = self.origin.split(":")
            sale_ret = self.env["sale.order"].search([("name", "in", origin_names)], limit=1)
            mo_ret = self.env["mrp.production"].search([("name", "in", origin_names)], limit=1)

            if sale_ret:
                dict.update({'origin_sale_id': sale_ret.id})
            if mo_ret:
                dict.update({'origin_mo_id': mo_ret.id})

    @api.multi
    def _prepare_purchase_order_line(self, po, supplier):
        self.ensure_one()
        product_new_qty = self.product_qty if self.not_base_on_available else self.get_actual_require_qty()
        procurement_uom_po_qty = self.product_uom._compute_quantity(product_new_qty, self.product_id.uom_po_id)
        res = super(ProcurementOrderExtend, self)._prepare_purchase_order_line(po, supplier)

        self.parse_origin_and_update_dic(res)
        res.update({
            "product_qty": procurement_uom_po_qty
        })
        return res

    def get_draft_po_qty(self, product_id):
        pos = self.env["purchase.order"].search([("state", "in", ("make_by_mrp", "draft", "to approve"))])
        chose_po_lines = self.env["purchase.order.line"]
        total_draft_order_qty = 0
        for po in pos:
            for po_line in po.order_line:
                if po_line.product_id.id == product_id.id:
                    chose_po_lines += po_line
                    total_draft_order_qty += po_line.product_qty
        return total_draft_order_qty

    def get_actual_require_qty(self):
        cur = datetime.datetime.now()
        # print "-------------start time: %s" % cur
        if not self.rule_id:
            all_parent_location_ids = self._find_parent_locations()
            self.rule_id = self._search_suitable_rule([('location_id', 'in', all_parent_location_ids.ids)])
        extra_qty = 0
        if self.rule_id.action == "manufacture":
            OrderPoint = self.env['stock.warehouse.orderpoint'].search([("product_id", "=", self.product_id.id)],
                                                                       limit=1)
            if OrderPoint.product_min_qty != 0 or OrderPoint.product_max_qty != 0:
                extra_qty = self.product_id.outgoing_qty - self.product_id.incoming_qty - self.product_id.qty_available
        elif self.rule_id.action == "buy":
            extra_qty = self.get_draft_po_qty(self.product_id)
        sss = self.product_qty + self.product_id.outgoing_qty - self.product_id.incoming_qty - self.product_id.qty_available - extra_qty
        actual_need_qty = 0
        if sss > 0:
            actual_need_qty = sss

        cur = datetime.datetime.now()
        # print "-------------end time: %s" % cur
        return actual_need_qty


class MultiSetMTO(models.TransientModel):
    _name = 'multi.set.mto'

    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        is_checked = context.get('is_checked', [])
        products = self.env['product.template'].search([('id', 'in', active_ids)])
        insert_type = 4 if is_checked else 2
        for product in products:
            product.route_ids = [(insert_type, self.env.ref('stock.route_warehouse0_mto').id)]


class purchase_order_extend(models.Model):
    _inherit = "purchase.order"

    @api.depends("origin")
    @api.multi
    def _compute_first_so_number(self):
        for order in self:
            if order.origin:
                origin_group = order.origin.split(",")
                if origin_group:
                    first_group = origin_group[0].split(":")
                    if first_group:
                        order.first_so_number = first_group[0]
                    else:
                        order.first_so_number = ''
                else:
                    order.first_so_number = ''
            else:
                order.first_so_number = ''

    first_so_number = fields.Char(compute="_compute_first_so_number", string=u'so单号', store=True)

    @api.multi
    def change_state_to_rfq(self):
        for po in self:
            po.sudo().write({
                'state': 'draft',
            })
            self._cr.execute("update purchase_order SET create_uid = %d where id = %d" % (self.env.user.id, po.id))

        print('test')

    def unlink_cancel_po(self):
        po_canceled = self.env["purchase.order"].search([("state", "=", "cancel")])
        mo_canceled = self.env["mrp.production"].search([("state", "=", "cancel")])
        po_canceled.unlink()
        mo_canceled.unlink()
        # self._cr.execute("select count(id) from stock_move where state ='cancel'")
        # row = self._cr.fetchone()
        # self._cr.execute("delete from stock_move where state = 'cancel' limit 10")
        # row1 = self._cr.fetchone()
        # print datetime.datetime.now()
        stock_moves = self.env["stock.move"].search([("state", "=", "cancel")], limit=10000, offset=0)
        stock_moves.unlink()
        # print datetime.datetime.now()

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ["cancel", "make_by_mrp"]:
                raise UserError(
                    _('In order to delete a purchase order, you must cancel it first.') + ('%s' % self.name))
        super(models.Model, self).unlink()  ###注意 fixme


class StockLocationExtend(models.Model):
    _inherit = "stock.location"

    is_circulate_location = fields.Boolean(u"是否是流转库")
    is_semi_finished_location = fields.Boolean(u"是否是半成品库")
    user_ids = fields.Many2many('res.users')

    def get_semi_finished_location_by_user(self, user_id):
        locations = self.env["stock.location"].search([('user_ids', 'in', [user_id]),
                                                       ])
        return locations


class ProductCategoryExtend(models.Model):
    _inherit = 'product.category'

    fixed_location_ids = fields.One2many("stock.fixed.putaway.strat", "category_id")


class ProductPutawayExtend(models.Model):
    _inherit = 'product.putaway'

    location_ids = fields.One2many(comodel_name="stock.location", inverse_name="putaway_strategy_id", string="",
                                   required=False, )


class ProductionScrap(models.Model):
    _name = 'production.scrap'

    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id

    def _get_default_location_id(self):
        return self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id

    production_id = fields.Many2one('mrp.production', string=u'生产单')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure',
        required=True, states={'done': [('readonly', True)]})
    scrap_qty = fields.Float(u'报废数量')
    # scrap_line_ids = fields.One2many('production.scrap.line', 'scrap_id')
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'production')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', default=_get_default_scrap_location_id,
        domain="[('scrap_location', '=', True)]", states={'done': [('readonly', True)]})

    def _prepare_move_values(self, ):
        self.ensure_one()
        return {
            'name': 'Scrap %s' % self.production_id.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.scrap_qty,
            'quantity_done': self.scrap_qty,
            'location_id': self.location_id.id,
            'location_dest_id': self.scrap_location_id.id,
            'production_id': self.production_id.id,
            'state': 'confirmed',
            'origin': 'Scrap %s' % self.production_id.name,
            'is_scrap': True
        }

    @api.multi
    def do_scrap(self):
        for scrap in self:
            move = self.env["stock.move"].create(scrap._prepare_move_values())
            move.action_done()


# class ProductionScrapLine(models.Model):
#     _name = 'production.scrap.line'
#
#     scrap_id = fields.Many2one('production.scrap')
#     product_id = fields.Many2one('product.product', string=u'产品')
#     product_uom_id = fields.Many2one(
#         'product.uom', 'Unit of Measure',
#         required=True, states={'done': [('readonly', True)]})


class MaterialRemark(models.Model):
    _name = 'material.remark'

    content = fields.Text(string="备注", required=True, )
    type = fields.Selection(string=u"类型", selection=[('material', '备料反馈'), ('production', '生产反馈'), ],
                            required=False,
                            default='material')

    @api.multi
    def name_get(self):
        res = []
        for remark in self:
            res.append((remark.id, remark.content))
        return res


class orderpoint_multi_create_wizard(models.TransientModel):
    _name = 'orderpoint.multi.create.wizard'

    min_qty = fields.Float(string=u"最小存货数量", default=0)
    max_qty = fields.Float(string=u"最大存货数量", default=0)

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        products = self.env['product.template'].browse(active_ids)
        pps = products.mapped("product_variant_id")
        self.create_reorder_rule(pps, min_qty=self.min_qty, max_qty=self.max_qty)

    def create_reorder_rule(self, pps, min_qty=0.0, max_qty=0.0, qty_multiple=1.0, overwrite=False):
        swo_obj = self.env['stock.warehouse.orderpoint']
        for rec in pps:
            reorder_rules = swo_obj.search([('product_id', '=', rec.id)])
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


class multi_force_assign(models.TransientModel):
    _name = 'multi.force.assign'

    @api.multi
    def action_ok(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        pickings = self.env['stock.picking'].browse(active_ids)
        pickings.filtered(lambda x: x.state not in ['done', 'cancel', 'draft']).force_assign()
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"强制可用成功",
                "text": u"强制可用成功",
                "sticky": False
            }
        }

    @api.multi
    def action_multi_unreserve(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        pickings = self.env['stock.picking'].browse(active_ids)
        pickings.filtered(lambda x: x.state not in ['done', 'cancel', 'draft']).do_unreserve()
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"取消保留成功",
                "text": u"取消保留成功",
                "sticky": False
            }
        }
