# -*- coding: utf-8 -*-
import time

import datetime

from odoo.exceptions import UserError
from odoo import models, fields, api


class MaterialRequest(models.Model):
    _name = 'material.request'

    name = fields.Char(string=u'系统流水号', readonly=True, default=u'新建')

    my_create_date = fields.Date(string=u"创建时间", default=fields.datetime.now())

    my_create_uid = fields.Many2one('res.users', string=u"创建人")

    picking_cause = fields.Text(string=u'领料原因')
    delivery_date = fields.Date(string=u'交货日期')
    remark = fields.Text(string=u'备注')
    picking_type = fields.Selection([('pick_type', u'产线领用'), ('proofing', u'工程领用')], string=u'领料类型',
                                    default='pick_type')
    Materials_development_way = fields.Selection(
        [('U-Line', u'物流发料'), ('Engineer_Dept', u'产线直接领用')], string=u'发料方式')
    picking_state = fields.Selection(
        [('canceled', u'已取消'), ('to_submit', u'待提交'), ('submitted', u'已提交'), ('to_approved', u'待审批'),
         ('review_ing', u'审核中'), ('approved_finish', u'等待领料'),
         ('finish_pick', u'完成'), ('Refused', u'已拒绝')], string=u'领料状态', default='to_submit')
    # 参考商品    one2many
    reference_product_template_ids = fields.Many2many('product.template')
    line_ids = fields.One2many('material.request.line', 'request_id', copy=True)

    review_id = fields.Many2one("review.process",
                                string=u'待...审核',
                                readonly=True, copy=False)

    review_process_line_ids = fields.One2many("review.process.line", string=u'审核流程',
                                              related='review_id.review_line_ids'
                                              )

    who_review_now = fields.Many2one("res.partner",
                                     related='review_id.who_review_now'
                                     )
    who_review_now_id = fields.Integer(string=u'待...审核',
                                       related='review_id.who_review_now.user_ids.id'
                                       )

    # 审核人列表
    review_i_approvaled_val = fields.Many2many('res.users')

    stock_picking_ids = fields.One2many('stock.picking', 'material_request_order_id')

    delivery_count = fields.Integer(compute='_compute_delivery_count')

    def _get_btn_show(self):

        if self.env.user.id == self.create_uid.id:
            self.btn_show = True
        else:
            self.btn_show = False

    btn_show = fields.Boolean(compute=_get_btn_show)

    def _get_approve_check(self):

        if self.env.user.id == self.who_review_now.user_ids.id:
            self.approve_check = True
        else:
            self.approve_check = False

    approve_check = fields.Boolean(compute=_get_approve_check)

    @api.multi
    def _compute_delivery_count(self):
        for order in self:
            order.delivery_count = len(order.stock_picking_ids)

    @api.multi
    def action_send_to_review(self):
        if not self.review_id:
            self.review_id = self.env["review.process"].create_review_process('material.request', self.id)

    @api.multi
    def write(self, vals):

        # if vals.get('line_ids'):
        #     for vals_line in vals.get('line_ids'):
        #         if type(vals_line[2]) == dict:
        #             if not vals_line[2].get('reference_bom'):
        #                 if not vals_line[2].get('quantity_done'):
        #                     if vals_line[1]:
        #                         product_one1 = self.env['material.request.line'].browse(vals_line[1])
        #                         qty_vals = product_one1.product_id.qty_available
        #                         if qty_vals < 0 or qty_vals < vals_line[2].get('product_qty'):
        #                             raise UserError(u"库存不足： '%s' " % product_one1.product_id.name)
        #                         if vals_line[2].get('product_qty') <= 0:
        #                             raise UserError(u"产品  '%s'  申请数量不能为0" % product_one1.product_id.name)
        #                     else:
        #                         product_one2 = self.env['product.product'].browse(vals_line[2].get('product_id'))
        #                         qty_vals = vals_line[2].get('qty_available') if vals_line[2].get(
        #                             'qty_available') else product_one2.qty_available
        #                         if qty_vals < 0 or qty_vals < vals_line[2].get('product_qty'):
        #                             raise UserError(u"库存不足： '%s' " % product_one2.name)
        #                         if vals_line[2].get('product_qty') <= 0:
        #                             raise UserError(u"产品  '%s'  申请数量不能为0" % product_one2.name)
        #                 else:
        #                     lin_ids_one = self.env['material.request.line'].browse(vals_line[1])
        #                     if lin_ids_one:
        #                         if vals_line[2].get('quantity_done') > lin_ids_one.product_qty:
        #                             raise UserError(u"产品  '%s'  领料数量不能大于需求数量" % lin_ids_one.product_id.name)
        null_add = True
        if vals.get('line_ids'):
            for vals_line in vals.get('line_ids'):
                if type(vals_line[2]) == dict and vals_line[2].get('reference_bom'):
                    null_add = False
                    break

        res = super(MaterialRequest, self).write(vals)

        if not vals.get('name'):

            # if not self.line_ids:
            #     raise UserError(u"订单行 不能为空！")

            if null_add and not vals.get('picking_state'):
                for line_one in self.line_ids:

                    if not vals.get('qty_available'):
                        if line_one.quantity_done > line_one.qty_available:
                            raise UserError(u"库存不足： '%s' " % line_one.product_id.name)
                    else:
                        if line_one.qty_available < 0 or line_one.qty_available < line_one.product_qty:
                            raise UserError(u"库存不足： '%s' " % line_one.product_id.name)
                        if line_one.product_qty <= 0:
                            raise UserError(u"产品  '%s'  申请数量不能为0" % line_one.product_id.name)

            if vals.get('line_ids'):
                for bom_one in vals.get('line_ids'):
                    if type(bom_one[2]) == dict:
                        if not bom_one[2].get('request_id') and not bom_one[2].get('reference_bom'):
                            line_one = self.env['material.request.line'].browse(bom_one[1])
                            line_one.write({'request_id': self.id})

        return res

    @api.model
    def create(self, vals):

        if vals.get('line_ids'):
            for vals_line in vals.get('line_ids'):
                product_one1 = self.env['product.product'].browse(vals_line[2].get('product_id'))
                qty_vals = vals_line[2].get('qty_available') if vals_line[2].get(
                    'qty_available') else product_one1.qty_available
                if qty_vals < 0 or qty_vals < vals_line[2].get('product_qty'):
                    raise UserError(u"库存不足： '%s' " % product_one1.name)
                if vals_line[2].get('product_qty') <= 0:
                    raise UserError(u"产品  '%s'  申请数量不能为0" % product_one1.name)
        # else:
        #     raise UserError(u" 订单行 不能为空！ ")

        res = super(MaterialRequest, self).create(vals)
        if len(res.name) < 3:
            res.write({'name': 'PD' + str(int(time.time()))})
        if vals.get('line_ids'):
            for bom_one in vals.get('line_ids'):
                if not bom_one[2].get('request_id'):
                    line_one = self.env['material.request.line'].browse(bom_one[1])
                    line_one.write({'request_id': res.id})
        return res

    @api.onchange('reference_product_template_ids')
    def onchange_reference_product_template_ids(self):

        my_all_line = [all_line if type(all_line.id) == int else '' for all_line in self.line_ids]
        while '' in my_all_line:
            my_all_line.remove('')
        all_temp_line = []
        for product_temp_one in self.reference_product_template_ids:
            all_temp_line += [all_temp_line_one.product_id.id for all_temp_line_one in
                              product_temp_one.bom_ids.bom_line_ids]
            for product_one in product_temp_one.bom_ids.bom_line_ids:
                if not product_one.product_id.id in [my_all_line_temp_one.product_id.id for my_all_line_temp_one in
                                                     my_all_line]:
                    self.line_ids = self.line_ids + self._create_material_line(product_one.product_id.id,
                                                                               product_one.product_id.inner_spec,
                                                                               product_one.product_id.inner_code,
                                                                               product_one.product_id.uom_id.name)
        for my_all_line_one in my_all_line:
            if not my_all_line_one.product_id.id in all_temp_line:
                self.line_ids = self.line_ids - my_all_line_one

    def _create_material_line(self, product_id, inner_spec, inner_code, uom_id):
        line_ine = self.env['material.request.line'].create({
            'product_id': product_id,
            'inner_spec': inner_spec,
            'inner_code': inner_code,
            'uom_id': uom_id,
        })
        return line_ine

    @api.multi
    def click_btn_delivery(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('stock_picking_ids')
        if pickings:
            if len(pickings) > 1:
                action['domain'] = [('id', 'in', pickings.ids)]
            elif pickings:
                action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
                action['res_id'] = pickings.id
        return action

    @api.multi
    def btn_click_state_chenge(self):
        # [('to_submit', u'待提交'), ('submitted', u'已提交'), ('to_approved', u'待审批'), ('approved_finish', u'已审批')],

        self.action_send_to_review()
        btn_context = self._context.get('btn_context', False)
        view_show = False
        if btn_context in ('to_submit', 'canceled', 'Refused'):
            view_show = True

        new_picking_type = ''
        project_line_pass_show = False

        if self.picking_type == 'pick_type':
            new_picking_type = 'picking_review_line'
        elif self.picking_type == 'proofing':
            new_picking_type = 'picking_review_project'

        if self.env['final.review.partner'].search([('final_review_partner_id', '=', self.env.user.partner_id.id),
                                                    ('review_type', '=', new_picking_type)]):
            project_line_pass_show = True

        return {
            'name': '新建',
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': False,
            'res_model': 'review.process.wizard',
            'domain': [],
            'context': {'view_show': view_show, 'review_type_two': self.picking_type,
                        'project_line_pass_show': project_line_pass_show,
                        'default_material_requests_id': self.id, 'review_type': 'picking_review'},
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def btn_click_state_chenge_cancel(self):
        # [('to_submit', u'待提交'), ('submitted', u'已提交'), ('to_approved', u'待审批'), ('approved_finish', u'已审批')],
        # self.action_send_to_review()

        self.picking_state = 'canceled'

        self.action_cancel('取消审核')

    def action_cancel(self, remark):

        for parnter_line_one in self.review_process_line_ids:
            if parnter_line_one.partner_id == self.who_review_now:
                parnter_line_one.write({
                    'review_time': fields.datetime.now(),
                    'state': 'review_canceled',
                    'remark': remark
                })
                # 新建一个 审核条目 指向最初的人
                self.env["review.process.line"].create({
                    'partner_id': self.create_uid.partner_id.id,
                    'review_id': self.review_id.id,
                    'last_review_line_id': parnter_line_one.id,
                    'review_order_seq': parnter_line_one.review_order_seq + 1,
                })

    @api.multi
    def btn_click_show_product_line(self):
        view = self.env.ref('linkloving_material_request.approval_project_picking_form_lines')

        return {'type': 'ir.actions.act_window',
                'res_model': 'material.request',
                'view_mode': 'form',
                'view_id': view.id,
                'res_id': self.id,
                'context': {'picking_mode': 'first_commit'},
                'target': 'new'}

    def btn_click_picking_material(self):

        self.btn_click_product_out()
        # self.picking_state = 'wait_verify'
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def btn_click_product_out(self):

        is_num = True

        for one_line in self.line_ids:
            if one_line.quantity_done > 0:
                is_num = False

        if is_num and self.line_ids:
            raise UserError(" 领料数量不能全为 0 ,请确认!")

        picking_out_material = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref(
                'linkloving_material_request.stock_location_engineering_material_request').id,
            'material_request_order_id': self.id,
            'origin': self.name,
            'note': self.remark,
            'Materials_development_way': self.Materials_development_way,
            'partner_id': self.create_uid.partner_id.id,
            'picking_type': self.picking_type,
        })

        for one_line in self.line_ids:
            move = self.env['stock.move'].create({
                'name': '工程领料',
                'product_id': one_line.product_id.id,
                'product_uom_qty': one_line.quantity_done if one_line.quantity_done else 0,
                'product_uom': one_line.product_id.uom_id.id,
                'picking_id': picking_out_material.id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': self.env.ref(
                    'linkloving_material_request.stock_location_engineering_material_request').id,
                'date': self.my_create_date,
                'raw_material_id': self.id,
                'origin': self.name,
                'suggest_qty': one_line.quantity_done,
                'move_order_type': 'project_picking',
            })
            move.action_done()

        self.picking_state = 'finish_pick'
        # return {'type': 'ir.actions.empty'}

    def open_product_select_window(self):
        return {'type': 'ir.actions.act_window',
                'res_model': 'temp.material.request',
                'view_mode': 'form',
                'context': '{"order_id":%s}' % (self.id),
                # 'res_id': self.product_tmpl_id.id,
                'target': 'new'}


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'

    def _compute_reserve_qty_material(self):
        stock_quant = self.env["stock.quant"].sudo()
        for material_line in self:
            material_line.reserve_qty = sum(stock_quant.search(
                [('product_id', '=', material_line.product_id.id), ('reservation_id', '!=', False),
                 ('location_id', '=',
                  self.env['stock.location'].sudo().search([('usage', '=', 'internal')], limit=1).id)]).mapped('qty'))

    def _compute_quantity_available_material(self):
        for mate_one in self:
            mate_one.quantity_available = mate_one.qty_available - mate_one.reserve_qty

    reserve_qty = fields.Float(compute=_compute_reserve_qty_material, string=u'保留数量')

    request_id = fields.Many2one('material.request')
    product_id = fields.Many2one('product.product')

    qty_available = fields.Float(related='product_id.qty_available', string=u'库存')

    quantity_available = fields.Float(string=u'系统可用', compute=_compute_quantity_available_material)

    product_qty = fields.Float(string=u'需求数量')

    quantity_done = fields.Float(string=u'领料数量')

    inner_code = fields.Char()
    inner_spec = fields.Char()
    uom_id = fields.Char(related='product_id.uom_id.name')
    reference_bom = fields.Char(string=u'参考BOM')

    # inner_code = fields.Char(related='product_id.product_tmpl_id.inner_code')
    # inner_spec = fields.Char(related='product_id.inner_spec')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.inner_code = self.product_id.inner_code
        self.inner_spec = self.product_id.inner_spec


class MaterialStockPicking(models.Model):
    _inherit = "stock.picking"

    material_request_order_id = fields.Many2one('material.request')
    Materials_development_way = fields.Selection(
        [('U-Line', u'产线直接领用'), ('Engineer_Dept', u'工程部直接领用')], string=u'发料方式')
    picking_type = fields.Selection([('pick_type', u'产线领用'), ('proofing', u'工程领用')], string=u'领料类型')


class MaterialRequestStockMove(models.Model):
    _inherit = 'stock.move'
    raw_material_id = fields.Many2one('material.request')


class TempMaterialRequest(models.Model):
    _name = "temp.material.request"

    product_ids = fields.Many2many('product.product', string='产品', )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)

    def create_order_line_model(self):
        sale_order_obj = self.env['material.request']
        order_id = self._context.get('order_id')
        new_order = sale_order_obj.browse(order_id)
        new_order.line_ids = self.create_order_line(order_id)
        return {'type': 'ir.actions.act_window_close',
                }

    def create_order_line(self, order_id):
        material_order = self.env['material.request'].browse(order_id)

        material_line_obj = self.env['material.request.line']
        material_lines = []
        for product_tmpl_id in self.product_ids:
            already_exist = False
            for line in material_order.line_ids:
                if line.product_id == product_tmpl_id:
                    already_exist = True
            if not already_exist:
                # material_request_line = material_line_obj.create({
                #     'quantity_done': 0.0,
                #     'product_qty': 0.0,
                #     'product_id': product_tmpl_id.id,
                #     'qty_available': product_tmpl_id.qty_available,
                # })
                # material_lines.append(material_request_line.id)
                material_lines.append(
                    [0, False, {u'product_id': product_tmpl_id.id, u'product_qty': 1, u'reference_bom': 0}])

        return material_lines
