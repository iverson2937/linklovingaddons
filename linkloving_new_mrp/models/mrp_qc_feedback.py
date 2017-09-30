# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class NewMRPQCFeedback(models.Model):
    _inherit = 'mrp.qc.feedback'

    line_ids = fields.One2many('mrp.qc.feedback.line', 'feedback_id')
    is_multi_output = fields.Boolean(related='production_id.is_multi_output')
    is_random_output = fields.Boolean(related='production_id.is_random_output')
    rule_id = fields.Many2one('mrp.product.rule', related='production_id.rule_id')

    def update_lines(self, lines):
        for line in lines:
            self.env['mrp.qc.feedback.line'].browse(line.get('line_id')).write({
                'qc_fail_qty': line.get('qc_fail_qty'),
                'qc_test_qty': line.get('qc_test_qty'),
                'qc_note': line.get('qc_note')
            })

    # 品捡中 -> 品捡完成
    def action_qc_success(self):

        if self.is_multi_output or self.is_random_output:

            if any(line.qc_test_qty for line in self.line_ids) <= 0:
                raise UserError('品检数量不能为0')
            self.state = "qc_success"
            if self.production_id.state in ['waiting_rework', 'waiting_inspection_finish']:
                self.production_id.state = self.production_id.compute_order_state()
            return True

        else:
            return super(NewMRPQCFeedback, self).action_qc_success()

    def action_qc_fail(self):
        if self.is_multi_output or self.is_random_output:

            if any(line.qc_test_qty for line in self.line_ids) <= 0:
                raise UserError('品检数量不能为0')
            self.state = "qc_fail"

            if self.production_id.state in ['waiting_rework', 'waiting_inspection_finish']:
                self.production_id.state = self.production_id.compute_order_state()
            return True
        else:
            return super(NewMRPQCFeedback, self).action_qc_fail()

    def action_post_inventory(self):
        if self.is_multi_output or self.is_random_output:
            for line in self.line_ids:
                line.finished_move_id.action_done()
            self.state = 'alredy_post_inventory'
            return True
        else:
            return super(NewMRPQCFeedback, self).action_post_inventory()


class MRPQCFeedbackLine(models.Model):
    _name = 'mrp.qc.feedback.line'
    feedback_id = fields.Many2one('mrp.qc.feedback')
    state = fields.Selection(string=u"状态", selection=[('draft', u'等待品检'),
                                                      ('qc_ing', u'品检中'),
                                                      ('qc_success', u'等待入库'),
                                                      ('qc_fail', u'品检失败'),
                                                      ('check_to_rework', u'已确认返工'),
                                                      ('alredy_post_inventory', u'已入库')], required=False,
                             related='feedback_id.state')
    product_id = fields.Many2one('product.product')
    finished_move_id = fields.Many2one('stock.move')
    suggest_qty = fields.Float(string=u'需求数量')
    qty_produced = fields.Float()
    qc_test_qty = fields.Float(string='Sampling Quantity')
    qc_rate = fields.Float(compute='_compute_qc_rate')
    qc_fail_qty = fields.Float('不良品数量')
    qc_fail_rate = fields.Float('不良率', compute='_compute_qc_fail_rate')
    qc_note = fields.Text(string='Note')
    qc_img = fields.Binary(string='Quality Inspection Image')

    @api.multi
    def _compute_qc_rate(self):
        for qc in self:
            qc.qc_rate = qc.qc_test_qty / qc.qty_produced * 100

    @api.multi
    def _compute_qc_fail_rate(self):
        for qc in self:
            if qc.qc_test_qty != 0:
                qc.qc_fail_rate = qc.qc_fail_qty / qc.qc_test_qty * 100
            else:
                qc.qc_fail_rate = 0
