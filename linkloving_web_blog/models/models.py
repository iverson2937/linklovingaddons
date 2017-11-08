# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


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

    blog_tag_ids = fields.Many2many('blog.tag', 'tag_parent_id', string=u'详细分类')
    is_all_blog = fields.Boolean(string=u'是否是总博文标签', default=False)

    @api.model
    def create(self, vals):

        if vals.get('is_all_blog'):
            blog_list = self.env['blog.blog'].search([('is_all_blog', '=', True)])
            if blog_list:
                raise UserError(u'已经存在主目录类别')

        res = super(LinkLovingBlogBlog, self).create(vals)
        self.write_website_nenu(res)
        return res

    @api.multi
    def write(self, vals):

        if vals.get('is_all_blog'):
            blog_list = self.env['blog.blog'].search([('is_all_blog', '=', True)])
            if blog_list:
                raise UserError(u'已经存在主目录类别')

        res = super(LinkLovingBlogBlog, self).write(vals)
        self.write_website_nenu(self)
        return res

    @api.multi
    def unlink(self):

        if self.is_all_blog:
            res_list = self.env['blog.blog'].search([]) - self
            if res_list:
                index_blog = self.env.ref('website_blog.menu_news')
                index_blog.write({'url': '/blog/' + str(res_list[0].id)})

        res = super(LinkLovingBlogBlog, self).unlink()

        return res

    def write_website_nenu(self, res):
        if res.is_all_blog:
            index_blog = self.env.ref('website_blog.menu_news')
            index_blog.write({'url': '/blog/' + str(res.id)})


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
