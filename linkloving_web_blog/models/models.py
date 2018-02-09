# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class LinkLovingBlogPost(models.Model):
    _inherit = "blog.post"

    tag_ids = fields.Many2one('blog.tag', string='Tags')
    keyword = fields.Char(string=u'关键字')
    visits = fields.Integer('No of Views', default=0)

    where_is_look = fields.Boolean(string='是否需要设置访问权限', defalut=False)

    where_user_look = fields.Many2many('res.users', string=u'谁可以看')
    where_user_team_look = fields.Many2many('crm.team')

    # @api.model
    # def create(self, vals):
    #     post_id = super(LinkLovingBlogPost, self).create(vals)
    #     return post_id

    @api.onchange('where_is_look')
    def _onchange_where_is_look(self):
        self.where_user_look = []
        self.where_user_team_look = []

    @api.onchange('where_user_team_look')
    def _onchange_where_user_team_look(self):
        # self.where_user_look += self.where_user_team_look.member_ids

        my_all_line = self.where_user_look
        all_temp_line = []
        for user_team in self.where_user_team_look:
            all_temp_line += user_team.member_ids

            for user_team_one in user_team.member_ids:
                if not user_team_one in my_all_line:
                    self.where_user_look += user_team_one

        for my_all_line_one in my_all_line:
            if not my_all_line_one in all_temp_line:
                self.where_user_look = self.where_user_look - my_all_line_one

    @api.multi
    def website_publish_button_new(self):
        # if self.env.user.has_group('website.group_website_publisher') and self.website_url != '#':
        #     return self.open_website_url()
        for self_one in self:
            if self_one.where_is_look:
                if not self_one.where_user_look:
                    raise UserError(u'不能发布,请联系作者设置本文章访问人员')
            self.write({'website_published': not self.website_published})
            # return self.write({'website_published': not self.website_published})


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
        # self.write_website_nenu(res)
        return res

    @api.multi
    def write(self, vals):

        if vals.get('is_all_blog'):
            blog_list = self.env['blog.blog'].search([('is_all_blog', '=', True)])
            if blog_list:
                raise UserError(u'已经存在主目录类别')

        res = super(LinkLovingBlogBlog, self).write(vals)
        # self.write_website_nenu(self)
        return res

    @api.multi
    def unlink(self):

        # if self.is_all_blog:
        #     res_list = self.env['blog.blog'].search([]) - self
        #     if res_list:
        #         index_blog = self.env.ref('website_blog.menu_news')
        #         index_blog.write({'url': '/blog/' + str(res_list[0].id)})

        res = super(LinkLovingBlogBlog, self).unlink()

        return res

    def write_website_nenu(self, res):
        if res.is_all_blog:
            index_blog = self.env.ref('website_blog.menu_news')
            index_blog.write({'url': '/blog/' + str(res.id)})


class LinkLovingBlogTag(models.Model):
    _inherit = 'blog.tag'

    tag_parent_id = fields.Many2one('blog.blog', string=u'父级')


class WebBlogTemporary(models.Model):
    _name = "web.blog.temporary"

    post_type = fields.Selection([('published', u'发布'), ('unpublished', u'取消发布')], string=u'操作类型', default='published')

    @api.multi
    def set_web_blog_published(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        Model = self.env['blog.post']
        post_type = True if self.post_type == 'published' else False
        for post_id in active_ids:
            print int(post_id)
            record = Model.browse(int(post_id))
            values = {}
            if 'website_published' in Model._fields:
                values['website_published'] = post_type
            record.write(values)

        return {'type': 'ir.actions.act_window_close'}
