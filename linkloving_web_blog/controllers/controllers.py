# -*- coding: utf-8 -*-
import json

from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from pyquery import PyQuery as pq
from odoo.addons.website.models.website import slug, unslug
from odoo import http, fields, _
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_blog.controllers.main import WebsiteBlog

import base64


class LinklovingWebBlog(http.Controller):
    @http.route('/blog/new_blog_index', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def new_blog_index_show(self, **kw):

        print http.request.env['blog.blog'].search([])

        values = {
            'type_data_all': http.request.env['blog.blog'].search([]),
        }
        return request.render("linkloving_web_blog.web_blog_show", values)

    @http.route('/blog/get_blog_detailed_type_list', type='json', auth='public', website=True, csrf=False)
    def get_blog_detailed_type_list(self, **kw):

        blog_general = request.env['blog.blog'].search([('name', '=', kw.get('blog_type_general_id'))])

        return {'data': [detailed_one.name for detailed_one in blog_general.blog_tag_ids]}

    @http.route('/blog/new_blog_create_index', type='http', auth='public', website=True, csrf=False)
    def new_blog_create_index_show(self, **kw):
        fields_one = http.request.env['blog.blog'].search([])
        fields_two = http.request.env['blog.tag'].search([])
        # field = fields.search([('model', '=', '')])
        values = {
            'type_list_one': [field.name for field in fields_one],
            'type_list_two': [field.name for field in fields_two],
        }

        return request.render("linkloving_web_blog.web_blog_create_show", values)

    @http.route('/blog/init', type='http', auth='public', csrf=False)
    def init_blog_show(self, **kw):

        chat_category = self.env.ref('website_menu.menu_news')

        bolog_name = ['公告栏', '发布文章']
        bolog_url = ['/blog/new_blog_index', '/blog/new_blog_create_index']

        for a in range(0, len(bolog_name)):
            request.env['website.menu'].create({
                'name': bolog_name[a],
                'url': bolog_url[a],
                'parent_id': request.website.menu_id.id,
                'website_id': request.website.id,
            })

        return http.local_redirect('/blog/new_blog_index')

    @http.route('/blog/update_blog_show', type='http', auth='public', csrf=False)
    def update_blog_show(self, **kw):
        result_data = http.request.env['blog.post'].search([('name', '=', '22222222222222')])
        values = {
            'updata_data': result_data
        }

        return request.render("linkloving_web_blog.web_blog_create_show", values)

    @http.route('/blog/create_blog_post_index', type='http', auth='public', website=True, csrf=False)
    def create_blog_post_index_show(self, **kw):
        # request.env.user.partner_id.id
        Model = request.env['blog.post']
        Model_Attachment = request.env['ir.attachment']

        # if not kw.get('name'):
        #     values = request.params.copy()
        #     values['error'] = _("Wrong login/password")
        #     return request.render('linkloving_web_blog.web_blog_create_show', values)

        content = pq(kw.get('content'))
        for a_html in content('img'):
            # attachment_one = Model_Attachment.search([('datas', '=', pq(a_html).attr('src').split('base64,')[1])])
            # if not attachment_one:
            attachment_one = Model_Attachment.create({
                'res_model': u'blog.post',
                'name': pq(a_html).attr('data-filename') if pq(a_html).attr('data-filename') else u"截图",
                'datas': pq(a_html).attr('src').split('base64,')[1] if pq(a_html).attr('src').split('base64,') else  pq(
                    a_html).attr('src'),
                'datas_fname': pq(a_html).attr('data-filename') if pq(a_html).attr('data-filename') else u"截图",
                'public': True,
            })
            pq(a_html).attr('src', '/web/image/' + str(attachment_one.id))

        attach = Model.create({
            'blog_id': http.request.env['blog.blog'].search([('name', '=', kw.get('blog_id'))]).id,
            'name': kw.get('name'),
            'subtitle': kw.get('subtitle'),
            'tag_ids': http.request.env['blog.tag'].search(
                [('name', '=', kw.get('blog_tag_type_id'))]).id,
            'content': content,
        })
        print attach

        # return http.local_redirect('/blog/new_blog_index') jump_blog_succeed

        return request.render("linkloving_web_blog.jump_blog_succeed", "")

    @http.route(['/blog/get_blog_data_lists'], type='json', auth='public', website=True, csrf=False)
    def get_blog_data_lists(self, **kw):
        blog_type_id = kw.get('blog_type_id')
        is_parent = kw.get('is_Parent')
        is_search = kw.get('is_search')
        search_body = kw.get('search_body')
        is_hot = kw.get('is_hot')

        blog_model = request.env['blog.post']
        domain = [('website_published', '=', True)]
        result_hot = False
        if is_search:

            author_list = [author.id for author in request.env['res.partner'].search([('name', 'ilike', search_body)])]

            if author_list:
                domain.append('|')
                domain.append(('author_id', 'in', author_list))

            domain.append(('name', 'ilike', search_body))

        elif is_hot:
            result_hot = blog_model.search(domain, limit=10, order='visits desc')
        else:
            if is_parent:
                domain.append(('tag_ids', '=', int(blog_type_id)))
            else:
                domain.append(('blog_id', '=', int(blog_type_id)))

        result = result_hot if result_hot else blog_model.search(domain)
        # result = blog_model.search(domain)
        data = []

        for res in result:
            res_one = {
                'blog_post_id': res.id,
                'blog_post_name': res.create_uid.name,
                'blog_id': res.blog_id.id,
                'name': res.name,
                'blog_type_one': res.blog_id.id,
                'blog_type_two': res.tag_ids.id,
            }

            data.append(res_one)

        return {'data': data}

    @http.route([
        '''/blog/<model("blog.blog"):blog>/post1/<model("blog.post", "[('blog_id','=',blog[0])]"):blog_post>''',
    ], type='http', auth="public", website=True, csrf=False)
    def blog_post(self, blog, blog_post, tag_id=None, page=1, enable_editor=None, **post):

        BlogPost = request.env['blog.post']

        values = {
            'blog': blog,
            'blog_post': blog_post,
        }

        print blog, blog_post

        response = request.render("linkloving_web_blog.blog_post_complete_is_me", values)

        request.session[request.session.sid] = request.session.get(request.session.sid, [])
        if not (blog_post.id in request.session[request.session.sid]):
            request.session[request.session.sid].append(blog_post.id)
            # Increase counter
            blog_post.sudo().write({
                'visits': blog_post.visits + 1,
            })
        return response

    @http.route('/blog/create_attachment', type='http', auth='public', website=True, csrf=False)
    def create_attachment_index(self, **kw):

        Model_Attachment = request.env['ir.attachment']

        content = kw.get('content')
        file_name = kw.get('file')

        attachment_one = Model_Attachment.create({
            'res_model': u'blog.post',
            'name': file_name,
            'datas': content.split('base64,')[1] if content.split('base64,') else content,
            'datas_fname': file_name,
            'public': True,
        })
        return str(attachment_one.id)

    @http.route('/blog/blog_all_publish', type='json', auth='public', website=True, csrf=False)
    def blog_all_publish(self, **kw):

        # blog_general = request.env['blog.blog'].search([('name', '=', kw.get('blog_type_general_id'))])

        Model = request.env['blog.post']

        blog_checkbox_list = kw.get('blog_checkbox_list')

        blog_publish = kw.get('blog_publish')

        blog_publish_type = ''

        if blog_publish in (1, 2) and blog_checkbox_list:
            if blog_publish == 1:
                blog_publish_type = True
            elif blog_publish == 2:
                blog_publish_type = False

            for post_id in blog_checkbox_list:
                print int(post_id)

                record = Model.browse(int(post_id))

                values = {}
                if 'website_published' in Model._fields:
                    # values['website_published'] = not record.website_published
                    values['website_published'] = blog_publish_type
                record.write(values)

                # return bool(record.website_published)

        return {'data': 'ok'}


class WebsiteBlogLinkLoving(WebsiteBlog, http.Controller):
    @http.route([
        '/blog/<model("blog.blog"):blog>',
        '/blog/<model("blog.blog"):blog>/page/<int:page>',
        '/blog/<model("blog.blog"):blog>/tag/<string:tag>',
        '/blog/<model("blog.blog"):blog>/tag/<string:tag>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def blog(self, blog=None, tag=None, page=1, **opt):
        """ Prepare all values to display the blog.

        :return dict values: values for the templates, containing

         - 'blog': current blog
         - 'blogs': all blogs for navigation
         - 'pager': pager of posts
         - 'active_tag_ids' :  list of active tag ids,
         - 'tags_list' : function to built the comma-separated tag list ids (for the url),
         - 'tags': all tags, for navigation
         - 'state_info': state of published/unpublished filter
         - 'nav_list': a dict [year][month] for archives navigation
         - 'date': date_begin optional parameter, used in archives navigation
         - 'blog_url': help object to create URLs
        """
        date_begin, date_end, state = opt.get('date_begin'), opt.get('date_end'), opt.get('state')
        published_count, unpublished_count = 0, 0

        BlogPost = request.env['blog.post']

        Blog = request.env['blog.blog']
        blogs = Blog.search([], order="create_date asc")

        # build the domain for blog post to display
        domain = []
        # retrocompatibility to accept tag as slug
        active_tag_ids = tag and map(int, [unslug(t)[1] for t in tag.split(',')]) or []
        if active_tag_ids:
            domain += [('tag_ids', 'in', active_tag_ids)]
        if blog.id == 1:
            domain += [('blog_id', 'in', [blog_one.id for blog_one in blogs])]
        else:
            domain += [('blog_id', '=', blog.id)]

        if date_begin and date_end:
            domain += [("post_date", ">=", date_begin), ("post_date", "<=", date_end)]

        if request.env.user.has_group('website.group_website_designer'):
            count_domain = domain + [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            published_count = BlogPost.search_count(count_domain)
            unpublished_count = BlogPost.search_count(domain) - published_count

            if state == "published":
                domain += [("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())]
            elif state == "unpublished":
                domain += ['|', ("website_published", "=", False), ("post_date", ">", fields.Datetime.now())]
        else:
            domain += [("post_date", "<=", fields.Datetime.now())]

        blog_url = QueryURL('', ['blog', 'tag'], blog=blog, tag=tag, date_begin=date_begin, date_end=date_end)

        blog_posts = BlogPost.search(domain, order="post_date desc")
        pager = request.website.pager(
            url=request.httprequest.path.partition('/page/')[0],
            total=len(blog_posts),
            page=page,
            step=self._blog_post_per_page,
            url_args=opt,
        )
        pager_begin = (page - 1) * self._blog_post_per_page
        pager_end = page * self._blog_post_per_page
        blog_posts = blog_posts[pager_begin:pager_end]

        all_tags = blog.all_tags()[blog.id]

        # function to create the string list of tag ids, and toggle a given one.
        # used in the 'Tags Cloud' template.
        def tags_list(tag_ids, current_tag):
            tag_ids = list(tag_ids)  # required to avoid using the same list
            if current_tag in tag_ids:
                tag_ids.remove(current_tag)
            else:
                tag_ids.append(current_tag)
            tag_ids = request.env['blog.tag'].browse(tag_ids).exists()
            return ','.join(map(slug, tag_ids))

        values = {
            'blog': blog,
            'blogs': blogs,
            'main_object': blog,
            'tags': all_tags,
            'state_info': {"state": state, "published": published_count, "unpublished": unpublished_count},
            'active_tag_ids': active_tag_ids,
            'tags_list': tags_list,
            'blog_posts': blog_posts,
            'blog_posts_cover_properties': [json.loads(b.cover_properties) for b in blog_posts],
            'pager': pager,
            'nav_list': self.nav_list(blog),
            'blog_url': blog_url,
            'date': date_begin,
        }
        response = request.render("website_blog.blog_post_short", values)
        return response

    @http.route([
        '''/blog/<model("blog.blog"):blog>/post/<model("blog.post", "[('blog_id','=',blog[0])]"):blog_post>''',
    ], type='http', auth="public", website=True)
    def blog_post(self, blog, blog_post, tag_id=None, page=1, enable_editor=None, **post):
        """ Prepare all values to display the blog.

        :return dict values: values for the templates, containing

         - 'blog_post': browse of the current post
         - 'blog': browse of the current blog
         - 'blogs': list of browse records of blogs
         - 'tag': current tag, if tag_id in parameters
         - 'tags': all tags, for tag-based navigation
         - 'pager': a pager on the comments
         - 'nav_list': a dict [year][month] for archives navigation
         - 'next_post': next blog post, to direct the user towards the next interesting post
        """
        BlogPost = request.env['blog.post']
        date_begin, date_end = post.get('date_begin'), post.get('date_end')

        pager_url = "/blogpost/%s" % blog_post.id

        pager = request.website.pager(
            url=pager_url,
            total=len(blog_post.website_message_ids),
            page=page,
            step=self._post_comment_per_page,
            scope=7
        )
        pager_begin = (page - 1) * self._post_comment_per_page
        pager_end = page * self._post_comment_per_page
        comments = blog_post.website_message_ids[pager_begin:pager_end]

        tag = None
        if tag_id:
            tag = request.env['blog.tag'].browse(int(tag_id))
        blog_url = QueryURL('', ['blog', 'tag'], blog=blog_post.blog_id, tag=tag, date_begin=date_begin,
                            date_end=date_end)

        if not blog_post.blog_id.id == blog.id:
            return request.redirect("/blog/%s/post/%s" % (slug(blog_post.blog_id), slug(blog_post)))

        tags = request.env['blog.tag'].search([])

        # Find next Post
        all_post = BlogPost.search([('blog_id', '=', blog.id)])

        index_blog = self.env.ref('website_menu.menu_news')

        if blog.id == index_blog.id:
            blogs = BlogPost.search([], order="post_date desc")
            all_post = BlogPost.search([('blog_id', 'in', [blog_one.id for blog_one in blogs])])

        if not request.env.user.has_group('website.group_website_designer'):
            all_post = all_post.filtered(lambda r: r.post_date <= fields.Datetime.now())

        if blog_post not in all_post:
            return request.redirect("/blog/%s" % (slug(blog_post.blog_id)))

        # should always return at least the current post
        all_post_ids = all_post.ids
        current_blog_post_index = all_post_ids.index(blog_post.id)
        nb_posts = len(all_post_ids)
        next_post_id = all_post_ids[(current_blog_post_index + 1) % nb_posts] if nb_posts > 1 else None
        next_post = next_post_id and BlogPost.browse(next_post_id) or False

        previous_post_id = all_post_ids[(current_blog_post_index - 1) % nb_posts] if nb_posts > 1 else None
        previous_post = previous_post_id and BlogPost.browse(previous_post_id) or False

        values = {
            'tags': tags,
            'tag': tag,
            'blog': blog,
            'blog_post': blog_post,
            'blog_post_cover_properties': json.loads(blog_post.cover_properties),
            'main_object': blog_post,
            'nav_list': self.nav_list(blog),
            'enable_editor': enable_editor,
            'next_post': next_post,
            'previous_post': previous_post,
            'next_post_cover_properties': json.loads(next_post.cover_properties) if next_post else {},
            'date': date_begin,
            'blog_url': blog_url,
            'pager': pager,
            'comments': comments,
        }
        response = request.render("website_blog.blog_post_complete", values)

        request.session[request.session.sid] = request.session.get(request.session.sid, [])
        if not (blog_post.id in request.session[request.session.sid]):
            request.session[request.session.sid].append(blog_post.id)
            # Increase counter
            blog_post.sudo().write({
                'visits': blog_post.visits + 1,
            })
        return response
