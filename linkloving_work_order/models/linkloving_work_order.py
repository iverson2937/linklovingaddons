# -*- coding: utf-8 -*-

from odoo import models, fields, api


class linkloving_work_order(models.Model):
    _name = 'linkloving.work.order'

    order_number = fields.Char()

    name = fields.Char()

    assign_uid = fields.Many2one('res.users')

    effective_department_ids = fields.Many2many('hr.department', 'linkloving_work_order_department_rel',
                                                'work_order_id', 'department_id', 'Department id', ondelete='cascade')

    priority = fields.Integer()

    description = fields.Text()

    issue_state = fields.Selection([
        ('unaccept', '未指定受理人'),
        ('process', '受理中'),
        ('check', '待审核'),
        ('done', '已完成'),
        ('draft', '草稿'),
    ], default='unaccept')

    assign_time = fields.Datetime()

    finish_time = fields.Datetime()

    attachments = fields.One2many(comodel_name="linkloving.work.order.image", inverse_name="work_order_id",
                                  string="工单图片", required=False, )

    tag_ids = fields.Many2many('linkloving.work.order.tag', 'linkloving_work_order_tag_rel', 'work_order_id', 'tag_id',
                               'Tags')

    brand_ids = fields.Many2many('product.category.brand', 'product_category_brand_rel', 'work_order_id', 'brand_id',
                                 'Brand id', ondelete='cascade')

    area_ids = fields.Many2many('hr.department', 'hr_department_work_order_rel', 'work_order_id', 'department_id',
                                'Department id', ondelete='cascade')

    category_ids = fields.Many2many('product.category', 'product_category_rel', 'work_order_id', 'category_id',
                                    'Category id', ondelete='cascade')

    @api.model
    def create(self, vals):
        if not vals.get('order_number'):
            vals['order_number'] = self.env['ir.sequence'].next_by_code('work.order.number') or '/'
        return super(linkloving_work_order, self).create(vals)
