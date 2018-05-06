# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.base.ir.ir_mail_server import extract_rfc2822_addresses
from odoo.exceptions import UserError
import re


class ResUserExtend(models.Model):
    _inherit = 'res.users'

    mail_server = fields.Many2one('ir.mail_server', string=u'Send Mail Server')

    # fetch_mail_server = fields.Many2one('fetchmail.server', string=u'Fetch Mail Server')


class ir_mail_server(models.Model):
    """发送邮件之前, 根据 smtp_from 查找对应的 smtp 服务器, 如果找不到对应,保留原状."""
    _inherit = "ir.mail_server"

    smtp_host = fields.Char(string='SMTP Server', required=True, help="Hostname or IP of SMTP server",
                            default=lambda self: self.env['ir.config_parameter'].get_param('smtp_sever_host'))

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False, ):

        smtp_from = message['Return-Path'] or message['From']
        assert smtp_from, "The Return-Path or From header is required for any outbound email"

        # The email's "Envelope From" (Return-Path), and all recipient addresses must only contain ASCII characters.
        from_rfc2822 = extract_rfc2822_addresses(smtp_from)
        assert len(
            from_rfc2822) == 1, "Malformed 'Return-Path' or 'From' address - it may only contain plain ASCII characters"
        smtp_from = from_rfc2822[0]

        #################################################
        # patch: 首先查找 smtp_from 对应的 smtp 服务器
        # 要求 定义 Outgoing Mail Servers 时候, 确保 Description(name) 字段的值 为对应的 邮件发送账户(完整的eMail地址)
        # 本模块以此 为 邮件的发送者 查找 smtp 服务器
        # 需要为系统中 每个可能发送邮件的账户 按以上要求设置一个 服务器
        if self.env.user.mail_server:
            mail_server_ids = self.search([('id', '=', self.env.user.mail_server.id)], order='sequence', limit=1)
            if mail_server_ids:
                mail_server_id = mail_server_ids[0].id

        res = super(ir_mail_server, self).send_email(message,
                                                     mail_server_id,
                                                     smtp_server,
                                                     smtp_port,
                                                     smtp_user,
                                                     smtp_password,
                                                     smtp_encryption,
                                                     smtp_debug
                                                     )
        return res


class AutoSmtpMailMail(models.Model):
    _inherit = 'mail.mail'

    char_filter = fields.Char(string=u'需要过滤的邮件地址')

    @api.model
    def message_new(self, message_dict, custom_values):
        # received 收到

        print message_dict

        partner_ids = set()
        kwargs_partner_ids = message_dict.pop('partner_ids', [])
        for partner_id in kwargs_partner_ids:
            if isinstance(partner_id, (list, tuple)) and partner_id[0] == 4 and len(partner_id) == 2:
                partner_ids.add(partner_id[1])
            if isinstance(partner_id, (list, tuple)) and partner_id[0] == 6 and len(partner_id) == 3:
                partner_ids |= set(partner_id[2])
            elif isinstance(partner_id, (int, long)):
                partner_ids.add(partner_id)
            else:
                pass  # we do not manage anything else

        # 根据 用户绑定的收件服务器 来获取Email

        self.env['res.users'].search([('login', 'ilike', message_dict.get('to').split("<")[-1].split(">")[0])])

        partner_ids.add(3624)

        val = {
            'subject': message_dict.get('subject'),
            'body_html': message_dict.get('body'),
            'body': message_dict.get('body'),
            'email_from': message_dict.get('email_from').split("<")[-1].split(">")[0],
            'email_to': message_dict.get('to').split("<")[-1].split(">")[0],
            'email_cc': message_dict.get('cc'),
            'author_id': message_dict.get('author_id'),
            'date': message_dict.get('date'),
            # 'message_type': 'email',
            # 'attachment_ids': message_dict.get('attachments'),
            'message_id': message_dict.get('message_id'),
            'partner_ids': [(4, pid) for pid in partner_ids],
            'state': 'received',
        }
        new_msg = self.sudo(self.env.user.id).create(val)
        return new_msg

    @api.multi
    def send(self, auto_commit=False, raise_exception=False):

        for self_one in self:
            par_list = self.env['res.partner']

            for partner_one in self_one.recipient_ids:
                for child_one in partner_one.child_ids:
                    if child_one.email:
                        par_list += child_one

                self_one.recipient_ids = par_list

        return super(AutoSmtpMailMail, self).send(auto_commit=False, raise_exception=True)

    @api.multi
    def send_get_email_dict(self, partner=None):
        res = super(AutoSmtpMailMail, self).send_get_email_dict(partner)

        res['body'] = (res.get('body') + "<br/><p>" + self.create_uid.signature + "</p>").replace('src="', 'src="' +
                                                                                                  self.sudo().env[
                                                                                                      'ir.config_parameter'].get_param(
                                                                                                      'web.base.url'))

        return res

    @api.multi
    def send_get_mail_to(self, partner=None):

        email_to = super(AutoSmtpMailMail, self).send_get_mail_to(partner)

        filter_list = self.char_filter.split(',') if self.char_filter else False

        email_to_one = email_to

        if str(email_to).find('<') >= 0 and str(email_to).find('>') >= 0:
            email_to_one = str(email_to)[str(email_to).find('<') + 1:str(email_to).find('>')].split(';')

        for email_one in email_to_one:
            run_email = True

            if filter_list:
                for q in filter_list:
                    if q:
                        if str(email_one).find(q) == 0:
                            email_to = str(email_to[0]).replace(
                                email_one + (';' if str(email_to).find(';') == 0 else ''), '')
                            run_email = False
            if run_email:
                if len(email_one) > 7:
                    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",
                                email_one) == None:
                        raise UserError('Email 有误' + str(email_one))
                else:
                    raise UserError('Email 有误' + str(email_one))

        return [email_to] if type(email_to) == str else email_to


class EmailSendStatistics(models.Model):
    _name = 'email.send.statistics'

    name = fields.Char(u'邮件标题')
    request_type = fields.Selection([('subscribe', u'订阅'), ('read', u'读取')], string=u'请求类型')
    is_subscribe = fields.Boolean(u'是否退订', default=True)
    email = fields.Char(u'Email')


class EmailAddressee(models.Model):
    _name = 'll.email.addressee'

    name = fields.Char(u'邮件标题')
    body = fields.Html(u'Email')
