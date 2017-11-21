# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PlanMoWizard(models.TransientModel):
    _inherit = 'plan.mo.wizard'

    outsourcing_supplier_id = fields.Many2one(comodel_name="res.partner", string=u'外协加工商')

    outside_type = fields.Selection(related="process_id.outside_type")

    supplier_id = fields.Many2one(comodel_name="res.partner", string=u'委外供应商')

class MrpProductionExtend(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _compute_count_of_outsourcing_order(self):
        for order in self:
            order.count_of_outsourcing_order = len(order.outsourcing_order_ids)

    outsourcing_supplier_id = fields.Many2one(comodel_name="res.partner", string=u'外协加工商')
    outsourcing_order_ids = fields.One2many(comodel_name="outsourcing.process.order", inverse_name="production_id",
                                            string=u'外协单')
    count_of_outsourcing_order = fields.Integer(compute='_compute_count_of_outsourcing_order')
    outside_type = fields.Selection(related="process_id.outside_type")

    @api.multi
    def _compute_qty_unpost(self):
        res = super(MrpProductionExtend, self)._compute_qty_unpost()
        for production in self:
            outsourcing_orders = production.outsourcing_order_ids.filtered(lambda x: x.state not in ["done"])
            production.qty_unpost += sum(outsourcing_orders.mapped("qty_produced"))

    @api.multi
    def action_view_outsourcing_orders(self):
        return {
            'name': u'外协单',
            'type': 'ir.actions.act_window',
            'res_model': 'outsourcing.process.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.outsourcing_order_ids.ids)],
            'target': 'current',
        }

    @api.multi
    def button_mark_done(self):
        if self.outside_type in ['outsourcing', 'all_outside'] and not self.mo_invoice_count:
            if self.outside_type == 'outsourcing':
                self._prepare_invoice(self.outsourcing_supplier_id)
            else:
                self._prepare_invoice(self.supplier_id)

        return super(MrpProductionExtend, self).button_mark_done()


class MrpProcessExtend(models.Model):
    _inherit = 'mrp.process'

    outside_type = fields.Selection(string=u"外协类型", selection=[('normal', u'正常'),
                                                               ('all_outside', u'委外'),
                                                               ('outsourcing', u'外协'), ],
                                    required=False, default='normal',
                                    )



class MrpProductionProduceExtend(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        qc_direct = self._context.get("qc_direct")  # 是否直接去QC, 外协完成之后的动作
        if not qc_direct:
            for mo in self:
                if mo.production_id.outside_type == 'outsourcing' and mo.production_id.outsourcing_supplier_id:  # 外协
                    return self.outsourcing_process_produce()
                elif mo.production_id.outside_type == 'outsourcing' and not mo.production_id.outsourcing_supplier_id:
                    raise UserError(u"此单据未设置外协供应商")
                else:
                    return super(MrpProductionProduceExtend, mo).do_produce()
        else:
            return super(MrpProductionProduceExtend, self).do_produce()

    # 外协
    def outsourcing_process_produce(self):
        quantity = self.product_qty
        if float_compare(quantity, 0, precision_rounding=self.product_uom_id.rounding) > 0:
            self.outsource_order_create(self.product_qty)  # 产出  生成外协单

        return {'type': 'ir.actions.act_window_close'}

    # 创建外协单, 如果有其他处于等待外协的单据就合并起来
    def outsource_order_create(self, qty_produced):
        draft_sum_qty = qty_produced
        order_draft = self.env["outsourcing.process.order"]
        if self.production_id.outsourcing_order_ids:
            order_draft = self.production_id.outsourcing_order_ids.filtered(lambda x: x.state == 'draft')
            draft_sum_qty += sum(order_draft.mapped("qty_produced"))
        feedback = self.env["outsourcing.process.order"].create({
            'qty_produced': draft_sum_qty,
            'production_id': self.production_id.id,
            'product_id': self.production_id.product_id.id,
            'employee_id': self.production_id.in_charge_id.employee_ids and
                           self.production_id.in_charge_id.employee_ids[0].id,
        })
        order_draft.unlink()
        return feedback


class OutsouringPorcessOrder(models.Model):
    _name = 'outsourcing.process.order'

    process_id = fields.Many2one("mrp.process", related="production_id.process_id", string=u'工序')

    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id, string=u'公司')

    employee_id = fields.Many2one(comodel_name="hr.employee", string=u"产线负责人", required=False, )

    outsourcing_supplier_id = fields.Many2one(comodel_name="res.partner",
                                              related='production_id.outsourcing_supplier_id', string=u'外协加工商')
    po_user_id = fields.Many2one(comodel_name="res.users", related='outsourcing_supplier_id.po_user_id',
                                 string=u'采购负责人')
    name = fields.Char('Name', index=True, required=True, )
    production_id = fields.Many2one('mrp.production', ondelete='restrict', string=u'生产单')
    qty_produced = fields.Float(string=u'数量')

    product_id = fields.Many2one('product.product', related='production_id.product_id', string=u'产品')

    state = fields.Selection(string=u"状态", selection=[('draft', u'等待外协'), ('out_ing', u'外协中'), ('done', u'完成')],
                             required=False,
                             default='draft')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('outsourcing.process.order') or 'New'
        return super(OutsouringPorcessOrder, self).create(vals)

    @api.multi
    def unlink(self):
        for qc in self:
            if qc.state in ['out_ing', 'done']:
                raise UserError(u"无法删除此单据")
        return super(OutsouringPorcessOrder, self).unlink()

    # 草稿 - > 外协中
    def action_draft_to_out(self):
        if self.state == 'draft':
            self.state = 'out_ing'
        else:
            raise UserError(u"状态异常 draft -> outing")

    # 外协 -> 完成
    def action_out_to_done(self):
        context = dict(self._context)
        context.update({
            'qc_direct': True
        })
        produce = self.env["mrp.product.produce"].create({
            'product_qty': self.qty_produced,
            'production_id': self.production_id.id,
            'product_uom_id': self.production_id.product_uom_id.id,
            'product_id': self.production_id.product_id.id,
        })
        produce.with_context(context).do_produce()

        if self.state == 'out_ing':
            self.state = 'done'
        else:
            raise UserError(u"状态异常 out_ing -> done")
