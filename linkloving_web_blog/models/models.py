# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LinkLovingBlogPost(models.Model):
    _inherit = "blog.post"

    # blog_post_type_ids = fields.Many2one('blog.post.broad.heading', string=u'文章分类')
    tag_ids = fields.Many2one('blog.tag', string='Tags')

    # @api.model
    # def create(self, vals):
    #     post_id = super(LinkLovingBlogPost, self).create(vals)
    #     return post_id


class LinkLovingWebsiteMenu(models.Model):
    _inherit = 'website.menu'

    is_blog = fields.Boolean(string=u'是否是所有博客')


class LinkLovingBlogBlog(models.Model):
    _inherit = 'blog.blog'

    blog_tag_ids = fields.One2many('blog.tag', 'tag_parent_id', string=u'详细分类')


class LinkLovingBlogTag(models.Model):
    _inherit = 'blog.tag'

    # name = fields.Char('Name', required=True, translate=True)
    # post_ids = fields.Many2many('blog.post', string='Posts')

    tag_parent_id = fields.Many2one('blog.blog', string=u'父级')


class LinkLovingTypeOne(models.Model):
    _name = 'blog.post.broad.heading'

    name = fields.Char(u'名称')
    detail = fields.Text(string=u'描述')

    # blog_Parent_id = fields.Many2one('blog.post.broad.heading', string=u'上级')
    blog_product_type = fields.Selection([('one_type', u'一级类别'), ('two_type', u'二级类别')], string=u'类型')
    # blog_junior_ids = fields.One2many('blog.post.broad.heading', 'blog_Parent_id', string=u'下级列表')
