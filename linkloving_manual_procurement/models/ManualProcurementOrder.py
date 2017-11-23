# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError


class ManualProcurementOrder(models.Model):
    _name = 'manual.procurement.order'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    @api.model
    def _default_procurement_line_ids(self):
        selected_product_ids = self._context.get("selected_product_ids")
        if selected_product_ids:
            p_s = self.env["product.template"].search([("id", "in", selected_product_ids)])
            lines = []
            for l in p_s:
                obj = self.env['manual.procurement.line'].create({
                    'product_id': l.product_variant_ids[0].id,
                    'qty_ordered': 0,
                })
                lines.append(obj.id)
            return lines

    @api.depends('procurement_line_ids', 'procurement_line_ids.procurement_id',
                 'procurement_line_ids.procurement_id.production_id',
                 'procurement_line_ids.procurement_id.production_id.state')
    @api.multi
    def _compute_state(self):
        for order in self:
            all_production_ids = order.procurement_line_ids.mapped("procurement_id").mapped("production_id")
            if not all_production_ids:  # 如果没有条目 就不做操作
                return
            if all(p.state == 'done' for p in all_production_ids):
                order.state = 'done'

    name = fields.Char(string=u'单号', readyonly=True)
    alia_name = fields.Char(string=u'别名')
    date_excepted = fields.Date(string=u'期望完成日期')
    remark = fields.Text(string=u'备注')

    state = fields.Selection(string=u'状态', selection=[('draft', u'草稿'),
                                                      ('confirmed', u'已确认'),
                                                      ('cancel', u'取消'),
                                                      ('done', u'完成'), ],
                             default='draft',
                             compute='_compute_state',
                             store=True)

    procurement_line_ids = fields.One2many(comodel_name='manual.procurement.line', inverse_name='manual_order_id',
                                           string=u'产品明细', default=_default_procurement_line_ids)

    procurement_group_id = fields.Many2one("procurement.group", string=u'补货组')

    company_id = fields.Many2one(
            'res.company', string='Company', required=True, default=_get_default_company_id)

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ["draft", "cancel"]:
                raise UserError(u"只能删除草稿或者取消状态的单据")
        return super(ManualProcurementOrder, self).unlink()

    @api.model
    def default_get(self, fields_list):
        return super(ManualProcurementOrder, self).default_get(fields_list)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('manual.procurement.order') or '/'
        return super(ManualProcurementOrder, self).create(vals)

    def action_confirm_procurement(self):
        if not self.procurement_line_ids:
            raise UserError(u'请添加产品明细')
        if self.state == 'draft':
            self.procurement_group_id = self.env["procurement.group"].create({'name': self.name,
                                                                              'manual_order_id': self.id}).id
            self.procurement_line_ids.confirm_to_make_mo()
            self.write({
                'state': 'confirmed'
            })

    def action_cancel_procurement(self):
        if self.state == 'done':
            raise UserError(u'已完成的单据无法取消')
        if self.state == 'confirmed':
            self.procurement_line_ids.action_cancel()

        self.state = 'cancel'


class ManualProcurementLine(models.Model):
    _name = 'manual.procurement.line'

    product_id = fields.Many2one("product.product", string=u'产品')

    qty_done = fields.Float(string=u'完成数量', default=0, readonly=True, compute='_compute_qty_done')
    qty_ordered = fields.Float(string=u'需求数量', default=0)
    qty_available = fields.Float(related="product_id.qty_available", readonly=True)

    inner_code = fields.Char(string=u'国内简码', related='product_id.inner_code', readonly=True)
    inner_spec = fields.Char(string=u'国内型号', related='product_id.inner_spec', readonly=True)

    manual_order_id = fields.Many2one('manual.procurement.order', readonly=True)
    # state =  fields.Selection(related="production_id")
    procurement_id = fields.Many2one('procurement.order')

    state = fields.Selection(related="procurement_id.production_id.state", string=u'制造单状态')

    @api.multi
    def _compute_qty_done(self):
        for line in self:
            if line.procurement_id.production_id:
                line.qty_done = line.procurement_id.production_id.qty_produced

    def show_product_detail(self):
        return {
            'name': self.product_id.name,
            'type': 'ir.actions.client',
            'tag': 'product_detail',
            'product_id': self.product_id.product_tmpl_id.id
        }

    @api.multi
    def action_cancel(self):
        self.procurement_id.action_cancel()

    @api.multi
    def confirm_to_make_mo(self):
        ProcurementOrder = self.env["procurement.order"]
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        for line in self:
            ProcurementOrderSudo = ProcurementOrder.sudo()
            if line.qty_ordered == 0:
                raise UserError(u"%s 需求数量不能为0" % line.product_id.name)

            procurement = ProcurementOrderSudo.create({
                'name': 'INT: %s' % (self.env.user.login),
                'date_planned': line.manual_order_id.date_excepted,
                'product_id': line.product_id.id,
                'product_qty': line.qty_ordered,
                'product_uom': line.product_id.uom_id.id,
                'warehouse_id': warehouse.id,
                'location_id': warehouse.lot_stock_id.id,
                'company_id': warehouse.company_id.id,
                'manual_procurement_line_id': line.id,
                'not_base_on_available': True,  # 计算的时候是否要加上库存
                'origin': line.manual_order_id.name,
                'group_id': line.manual_order_id.procurement_group_id.id,
            })
            line.procurement_id = procurement.id
        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"完成",
                "text": u"完成",
                "sticky": False
            }
        }


class ProcurementGroupExtend(models.Model):
    _inherit = 'procurement.group'

    manual_order_id = fields.Many2one('manual.procurement.order')


class ProcurementOrderManualExtend(models.Model):
    _inherit = 'procurement.order'
    not_base_on_available = fields.Boolean(default=False)
    manual_order_id = fields.Many2one('manual.procurement.order', string=u'生产需求单')
    manual_procurement_line_id = fields.Many2one('manual.procurement.line')

    # def _prepare_mo_vals(self, bom):
    #     res = super(ProcurementOrderManualExtend, self)._prepare_mo_vals(bom)
    #
    #     res.update({'state': 'draft',
    #                 'process_id': bom.process_id.id,
    #                 'unit_price': bom.process_id.unit_price,
    #                 'mo_type': bom.mo_type,
    #                 'hour_price': bom.hour_price,
    #                 'in_charge_id': bom.process_id.partner_id.id,
    #                 'product_qty': self.product_qty if self.not_base_on_available else self.get_actual_require_qty(),
    #                 # 'date_planned_start': fields.Datetime.to_string(self._get_date_planned_from_today()),
    #                 # 'date_planned_finished':
    #                 })
    #     return res
