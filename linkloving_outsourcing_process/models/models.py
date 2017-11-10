# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PlanMoWizard(models.TransientModel):
    _inherit = 'plan.mo.wizard'

    outsourcing_supplier_id = fields.Many2one(comodel_name="res.partner", string=u'外协加工商')


class MrpProductionExtend(models.Model):
    _inherit = 'mrp.production'

    outsourcing_supplier_id = fields.Many2one(comodel_name="res.partner", string=u'外协加工商')
    outsourcing_order_ids = fields.One2many(comodel_name="outsourcing.process.order", inverse_name="production_id",
                                            string=u'外协单')


class MrpProductionProduceExtend(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        qc_direct = self._context.get("qc_direct")  # 是否直接去QC, 外协完成之后的动作
        if not qc_direct:
            for mo in self:
                if mo.production_id.outsourcing_supplier_id:  # 外协
                    return self.outsourcing_process_produce()
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
        })
        order_draft.unlink()
        return feedback


class OutsouringPorcessOrder(models.Model):
    _name = 'outsourcing.process.order'

    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id, string=u'公司')
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
