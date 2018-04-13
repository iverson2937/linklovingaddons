# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.base.ir.ir_mail_server import extract_rfc2822_addresses
from odoo.exceptions import UserError
import re
import logging
import xmlrpclib
import email

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60


class ResUserExtend(models.Model):
    _inherit = 'res.users'

    mail_server = fields.Many2one('ir.mail_server', string=u'Send Mail Server')

    fetch_mail_server = fields.Many2one('fetchmail.server', string=u'Fetch Mail Server')


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

    state = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('exception', 'Delivery Failed'),
        ('cancel', 'Cancelled'),
        ('draft', '草稿箱'),
        ('deleted', '已删除'),
        ('flag', '标记邮件'),
        ('junk', '垃圾邮件'),
        ('unseen', '未读邮件'),
    ], 'Status', readonly=True, copy=False, default='outgoing')

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


class AutoSmtpFetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    @api.model
    def _fetch_mails1(self, is_all):
        """ Method called by cron to fetch mails from servers """
        print '开始收取邮件'

        return self.search([('state', '=', 'done'), ('type', 'in', ['pop', 'imap'])]).fetch_mail1()

    @api.multi
    def fetch_mail1(self):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.type, server.name)
            additionnal_context['fetchmail_server_id'] = server.id
            additionnal_context['server_type'] = server.type
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            if server.type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    for state_type in ['(Seen)', '(UNSEEN)']:

                        result, data = imap_server.search(None, state_type)
                        for num in data[0].split():
                            res_id = None
                            result, data = imap_server.fetch(num, '(RFC822)')
                            imap_server.store(num, '-FLAGS', '\\Seen')
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(
                                    server.object_id.model, data[0][1], save_original=server.original,
                                    strip_attachments=(not server.attach))
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.type, server.name,
                                             exc_info=True)
                                failed += 1
                            if res_id and server.action_id:
                                server.action_id.with_context({
                                    'active_id': res_id,
                                    'active_ids': [res_id],
                                    'active_model': self.env.context.get("thread_model", server.object_id.model)
                                }).run()
                            imap_server.store(num, '+FLAGS', '\\Seen')
                            self._cr.commit()
                            count += 1
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count,
                                     server.type,
                                     server.name, (count - failed), failed)


                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type,
                                 server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
            elif server.type == 'pop':
                try:
                    while True:
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = '\n'.join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(
                                    server.object_id.model, message, save_original=server.original,
                                    strip_attachments=(not server.attach))
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.type, server.name,
                                             exc_info=True)
                                failed += 1
                            if res_id and server.action_id:
                                server.action_id.with_context({
                                    'active_id': res_id,
                                    'active_ids': [res_id],
                                    'active_model': self.env.context.get("thread_model", server.object_id.model)
                                }).run()
                            self.env.cr.commit()
                        if num_messages < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num_messages,
                                     server.type, server.name, (num_messages - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type,
                                 server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})
        return True


class AutoSmtpMailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = str(message.data)
        # Warning: message_from_string doesn't always work correctly on unicode,
        # we must use utf-8 strings here :-(
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        msg_txt = email.message_from_string(message)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg = self.message_parse(msg_txt, save_original=save_original)
        if strip_attachments:
            msg.pop('attachments', None)

        if msg.get('message_id'):  # should always be True as message_parse generate one if missing
            existing_msg_ids = self.env['mail.message'].search([('message_id', '=', msg.get('message_id'))])
            if existing_msg_ids:
                _logger.info(
                    'Ignored mail from %s to %s with Message-Id %s: found duplicated Message-Id during processing',
                    msg.get('from'), msg.get('to'), msg.get('message_id'))
                return False

        # find possible routes for the message
        routes = self.message_route(msg_txt, msg, model, thread_id, custom_values)
        thread_id = self.message_route_process(msg_txt, msg, routes)
        return thread_id

    @api.model
    def message_route_process(self, message, message_dict, routes):
        self = self.with_context(attachments_mime_plainxml=True)  # import XML attachments as text
        # postpone setting message_dict.partner_ids after message_post, to avoid double notifications
        partner_ids = message_dict.pop('partner_ids', [])
        thread_id = False
        for model, thread_id, custom_values, user_id, alias in routes or ():
            if model:
                Model = self.env[model]
                # model  里面一定有 message_new 方法 否则抛出下面异常
                if not (thread_id and hasattr(Model, 'message_update') or hasattr(Model, 'message_new')):
                    raise ValueError(
                        "Undeliverable mail with Message-Id %s, model %s does not accept incoming emails" %
                        (message_dict['message_id'], model)
                    )

                # disabled subscriptions during message_new/update to avoid having the system user running the
                # email gateway become a follower of all inbound messages
                MessageModel = Model.sudo(user_id).with_context(mail_create_nosubscribe=True, mail_create_nolog=True)
                if thread_id and hasattr(MessageModel, 'message_update'):
                    MessageModel.browse(thread_id).message_update(message_dict)
                else:
                    # if a new thread is created, parent is irrelevant
                    message_dict.pop('parent_id', None)
                    MessageModel.message_new(message_dict, custom_values)
            else:
                if thread_id:
                    raise ValueError(
                        "Posting a message without model should be with a null res_id, to create a private message.")
                Model = self.env['mail.thread']
                MailModel = self.env['mail.mail'].sudo(user_id).with_context(mail_create_nosubscribe=True,
                                                                             mail_create_nolog=True)
                MailModel.message_new(message_dict, custom_values)
            if not hasattr(Model, 'message_post'):
                Model = self.env['mail.thread'].with_context(thread_model=model)
            internal = message_dict.pop('internal', False)
            new_msg = Model.browse(thread_id).sudo().message_post(
                subtype=internal and 'mail.mt_note' or 'mail.mt_comment', **message_dict)

            if partner_ids:
                # postponed after message_post, because this is an external message and we don't want to create
                # duplicate emails due to notifications
                new_msg.write({'partner_ids': partner_ids})
        return thread_id
