# -*- coding: utf-8 -*-
import re

import time

from odoo import models, fields, api
from odoo import tools
from odoo.exceptions import UserError


class CrmMailMessage(models.Model):
    _inherit = 'mail.message'

    messages_label_ids = fields.Many2many('message.label', 'message_label_mail_message_type_rel', string=u'记录类型')

    postil = fields.Text(string=u'批注')
    # sale_order_type = fields.Text(string=u'销售记录类型')

    sale_order_type = fields.Selection(
        [('question', u'问题记录'), ('inspection', u'验货报告'), ('partner_question', u'客户问题记录')], string=u'销售记录类型')

    compyter_body = fields.Text(string=u'内容', compute='get_message_body')

    solution = fields.Text(string=u'解决方案')
    measure = fields.Text(string=u'后续措施')
    anticipated_loss = fields.Float(string=u'预计损失')

    person_in_charge_ids = fields.One2many('order.person.in.charge', 'mail_message_person_id', string=u'责任人')

    def get_message_body(self):
        for message_body in self:
            message_body.compyter_body = filter_tags(message_body.body)

    @api.multi
    def send_message_action(self):
        data = ' '
        for ss in self.messages_label_ids:
            data += (' ' + ss.name)
        self.write({'messages_label_body': data})
        return {'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'view_mode': 'form,tree',
                'view_type': 'form',
                'res_id': self.res_id,
                'target': 'self'}

    @api.multi
    def message_format(self):
        if self:
            if self[0].model == 'res.partner':
                partner_my = self.env['res.partner'].search([('id', '=', self[0].res_id)])
                res_ids = partner_my.ids + partner_my.opportunity_ids.ids

                self = self.env['mail.message'].search(
                    [('model', 'in', ('crm.lead', 'res.partner')), ('res_id', 'in', res_ids)])

        message_values = self.read([
            'id', 'body', 'date', 'author_id', 'email_from',  # base message fields
            'message_type', 'subtype_id', 'subject',  # message specific
            'model', 'res_id', 'record_name',  # document related
            'channel_ids', 'partner_ids',  # recipients
            'needaction_partner_ids',  # list of partner ids for whom the message is a needaction
            'starred_partner_ids',  # list of partner ids for whom the message is starred
            'messages_label_ids',
            'solution', 'anticipated_loss', 'measure',
        ])
        message_tree = dict((m.id, m) for m in self.sudo())
        self._message_read_dict_postprocess(message_values, message_tree)

        # add subtype data (is_note flag, subtype_description). Do it as sudo
        # because portal / public may have to look for internal subtypes
        subtypes = self.env['mail.message.subtype'].sudo().search(
            [('id', 'in', [msg['subtype_id'][0] for msg in message_values if msg['subtype_id']])]).read(
            ['internal', 'description'])
        subtypes_dict = dict((subtype['id'], subtype) for subtype in subtypes)
        for message in message_values:
            message['is_note'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]]['internal']
            message['subtype_description'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]][
                'description']
        return message_values

    @api.model
    def _message_read_dict_postprocess(self, messages, message_tree):
        """ Post-processing on values given by message_read. This method will
            handle partners in batch to avoid doing numerous queries.

            :param list messages: list of message, as get_dict result
            :param dict message_tree: {[msg.id]: msg browse record as super user}
        """
        # 1. Aggregate partners (author_id and partner_ids), attachments and tracking values
        partners = self.env['res.partner'].sudo()
        attachments = self.env['ir.attachment']
        message_label = self.env['message.label']
        trackings = self.env['mail.tracking.value']
        for key, message in message_tree.iteritems():
            if message.author_id:
                partners |= message.author_id
            if message.subtype_id and message.partner_ids:  # take notified people of message with a subtype
                partners |= message.partner_ids
            elif not message.subtype_id and message.partner_ids:  # take specified people of message without a subtype (log)
                partners |= message.partner_ids
            if message.needaction_partner_ids:  # notified
                partners |= message.needaction_partner_ids
            if message.attachment_ids:
                attachments |= message.attachment_ids
            if message.messages_label_ids:
                message_label |= message.messages_label_ids
            if message.tracking_value_ids:
                trackings |= message.tracking_value_ids
        # Read partners as SUPERUSER -> message being browsed as SUPERUSER it is already the case
        partners_names = partners.name_get()
        partner_tree = dict((partner[0], partner) for partner in partners_names)

        # 2. Attachments as SUPERUSER, because could receive msg and attachments for doc uid cannot see
        attachments_data = attachments.sudo().read(['id', 'datas_fname', 'name', 'mimetype'])
        attachments_tree = dict((attachment['id'], {
            'id': attachment['id'],
            'filename': attachment['datas_fname'],
            'name': attachment['name'],
            'mimetype': attachment['mimetype'],
        }) for attachment in attachments_data)

        # messages_label_data = message_label.sudo().read(['id', 'name', 'description', 'message_type_img_id'])
        messages_label_data = message_label.sudo().read(['id', 'name', 'description'])
        messages_label_tree = dict((message_label['id'], {
            'id': message_label['id'],
            'name': message_label['name'],
            'description': message_label['description'],
        }) for message_label in messages_label_data)

        # 3. Tracking values
        tracking_tree = dict((tracking.id, {
            'id': tracking.id,
            'changed_field': tracking.field_desc,
            'old_value': tracking.get_old_display_value()[0],
            'new_value': tracking.get_new_display_value()[0],
            'field_type': tracking.field_type,
        }) for tracking in trackings)

        # 4. Update message dictionaries
        for message_dict in messages:
            message_id = message_dict.get('id')
            message = message_tree[message_id]
            if message.author_id:
                author = partner_tree[message.author_id.id]
            else:
                author = (0, message.email_from)
            partner_ids = []
            if message.subtype_id:
                partner_ids = [partner_tree[partner.id] for partner in message.partner_ids
                               if partner.id in partner_tree]
            else:
                partner_ids = [partner_tree[partner.id] for partner in message.partner_ids
                               if partner.id in partner_tree]

            customer_email_data = []
            for notification in message.notification_ids.filtered(
                    lambda notif: notif.res_partner_id.partner_share and notif.res_partner_id.active):
                customer_email_data.append((partner_tree[notification.res_partner_id.id][0],
                                            partner_tree[notification.res_partner_id.id][1], notification.email_status))

            attachment_ids = []
            for attachment in message.attachment_ids:
                if attachment.id in attachments_tree:
                    attachment_ids.append(attachments_tree[attachment.id])

            messages_label_ids = []
            for message_label in message.messages_label_ids:
                if message_label.id in messages_label_tree:
                    messages_label_ids.append(messages_label_tree[message_label.id])

            tracking_value_ids = []
            for tracking_value in message.tracking_value_ids:
                if tracking_value.id in tracking_tree:
                    tracking_value_ids.append(tracking_tree[tracking_value.id])

            message_dict.update({
                'author_id': author,
                'partner_ids': partner_ids,
                'customer_email_status': (all(d[2] == 'sent' for d in customer_email_data) and 'sent') or
                                         (any(d[2] == 'exception' for d in customer_email_data) and 'exception') or
                                         (any(d[2] == 'bounce' for d in customer_email_data) and 'bounce') or 'ready',
                'customer_email_data': customer_email_data,
                'attachment_ids': attachment_ids,
                'messages_label_ids': messages_label_ids,
                'tracking_value_ids': tracking_value_ids,
            })

        return True

    @api.multi
    def write(self, vals):
        res = super(CrmMailMessage, self).write(vals)
        if self.model == 'crm.lead':

            lead_val = self.env['crm.lead'].browse(self.res_id)
            # 跟进的类行为报价的话 就改变商机状态为 报价
            mail_quote_id = self.env.ref('linkloving_crm.message_label_quote_id1')
            mail_sample_id = self.env.ref('linkloving_crm.message_label_sample_id')
            if self.message_type != 'notification' and vals.get('messages_label_ids'):
                message_label_list = vals.get('messages_label_ids')[0][2]
                if mail_quote_id.id in message_label_list:
                    lead_val.write({'lead_is_quote': True})
                else:
                    lead_val.write({'lead_is_quote': False})
                if mail_sample_id.id in message_label_list:
                    lead_val.write({'lead_is_sample': True})
                else:
                    lead_val.write({'lead_is_sample': False})

        return res

    @api.model
    def create(self, values):

        if values.get('model') == "sale.order":
            sale_order_data = self.env['sale.order'].search([('id', '=', values['res_id'])])
            # if "messages_label_ids" in values and len(values['messages_label_ids']) > 0:
            if values.get('messages_label_ids'):
                if "question" in values['messages_label_ids']:
                    sale_order_data.write({'question_record_count': (sale_order_data.question_record_count + 1)})
                if "inspection" in values['messages_label_ids']:
                    sale_order_data.write({'inspection_report_count': (sale_order_data.inspection_report_count + 1)})
                values['sale_order_type'] = values['messages_label_ids'][0]

        if values.get('model') == "res.partner" or values.get('model') == "crm.lead":
            if values.get('messages_label_ids'):  # needed to compute reply_to
                if str(values.get('messages_label_ids')) in ["[u'inspection']", "[u'question']"]:
                    if values.get('question_subject'):
                        values['sale_order_type'] = 'partner_question'
                else:
                    msg_label_ids = []
                    for item in values['messages_label_ids']:
                        if item not in ["inspection", "question"]:
                            msg_label_ids.append(int(item))
                    values['messages_label_ids'] = [(6, 0, msg_label_ids)]

        if values.get('person_in_charge_value'):
            values['person_in_charge_ids'] = [(0, 0, vals) for vals in values.get('person_in_charge_value')]
        if values.get('question_subject'):
            values['subject'] = values['question_subject']

        message = super(CrmMailMessage, self).create(values)
        # 处理商机状态
        if message.model == 'crm.lead':
            crm_lead_val = self.env['crm.lead'].search([('id', '=', message.res_id)])
            if crm_lead_val.type == 'opportunity':
                for one_type in message.messages_label_ids:
                    stage_val = self.env['crm.stage'].search([('full_name_ids', 'in', one_type.id)])
                    crm_lead_val.write({'stage_id': stage_val.id})

            # 跟进的类行为报价的话 就改变商机状态为 报价
            mail_quote_id = self.env.ref('linkloving_crm.message_label_quote_id1')
            mail_sample_id = self.env.ref('linkloving_crm.message_label_sample_id')

            if message.message_type != 'notification':
                crm_lead_val.write({'lead_is_follow_up': True})
                if mail_quote_id.id in message.messages_label_ids.ids:
                    crm_lead_val.write({'lead_is_quote': True})
                elif mail_sample_id.id in message.messages_label_ids.ids:
                    crm_lead_val.write({'lead_is_sample': True})

        elif message.model == 'res.partner':
            crm_partner_val = self.env['res.partner'].search([('id', '=', message.res_id)])

            if message.message_type != 'notification':
                crm_partner_val.write(
                    {'customer_follow_up_date': time.strftime('%Y-%m-%d', time.localtime(time.time()))})

            mail_connect_id = self.env.ref('linkloving_crm.message_label_connect')
            mail_stage_id = self.env.ref('linkloving_crm.crm_lead_crm_stage')

            #  跟进类型为 建立联系 线索客户 转化潜在客户
            if message.message_type != 'notification':
                if mail_connect_id.id in message.messages_label_ids.ids:
                    if (not crm_partner_val.opportunity_ids) and message.messages_label_ids:
                        if (not (crm_partner_val.company_type == 'person')) and crm_partner_val.customer:
                            if not mail_connect_id.msg_stage_ids:
                                raise UserError(u'请检查阶段是否已绑定记录类型')
                            lead_vals = {
                                'name': "默认商机-" + str(crm_partner_val.name),
                                'partner_id': crm_partner_val.id,
                                'planned_revenue': 0.0,
                                'priority': crm_partner_val.priority,
                                'type': 'opportunity',
                                'stage_id': mail_stage_id.id
                            }
                            self.env['crm.lead'].create(lead_vals)
                            crm_partner_val.write({'crm_is_partner': False})

        return message

    @api.multi
    def unlink(self):

        for mail_data in self:
            if mail_data.model == 'sale.order':
                sale_order_data_item = self.env['sale.order'].search([('id', '=', mail_data['res_id'])])
                if mail_data['sale_order_type'] and "question" in mail_data['sale_order_type']:
                    sale_order_data_item.write(
                        {'question_record_count': (sale_order_data_item.question_record_count - 1)})
                if mail_data['sale_order_type'] and "inspection" in mail_data['sale_order_type']:
                    sale_order_data_item.write(
                        {'inspection_report_count': (sale_order_data_item.inspection_report_count - 1)})

        super(CrmMailMessage, self).unlink()

    def update_message_action(self):
        pass


class Stage(models.Model):
    _inherit = "crm.stage"

    full_name_ids = fields.Many2many('message.label', string=u'名称')


class CrmMessageLabelStatus(models.Model):
    _name = 'message.order.status'
    name = fields.Char(string=u'订单状态')
    description = fields.Text(string=u'描述')


class CrmPersonInCharge(models.Model):
    _name = 'order.person.in.charge'
    person_in_charge = fields.Char(string=u'责任人')
    person_in_charge_proportion = fields.Float(string=u'占比%')

    mail_message_person_id = fields.Many2one('mail.message', string=u'销售订单')


def filter_tags(htmlstr):
    # 先过滤CDATA
    re_cdata = re.compile('//<!\[CDATA\[[^>]*//\]\]>', re.I)  # 匹配CDATA
    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # Script
    re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style
    re_br = re.compile('<br\s*?/?>')  # 处理换行
    re_h = re.compile('</?\w+[^>]*>')  # HTML标签
    re_comment = re.compile('<!--[^>]*-->')  # HTML注释
    s = re_cdata.sub('', htmlstr)  # 去掉CDATA
    s = re_script.sub('', s)  # 去掉SCRIPT
    s = re_style.sub('', s)  # 去掉style
    s = re_br.sub('\n', s)  # 将br转换为换行
    s = re_h.sub('', s)  # 去掉HTML 标签
    s = re_comment.sub('', s)  # 去掉HTML注释
    # 去掉多余的空行
    blank_line = re.compile('\n+')
    s = blank_line.sub('\n', s)
    s = replaceCharEntity(s)  # 替换实体
    return s


def replaceCharEntity(htmlstr):
    CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                     'lt': '<', '60': '<',
                     'gt': '>', '62': '>',
                     'amp': '&', '38': '&',
                     'quot': '"', '34': '"', }

    re_charEntity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_charEntity.search(htmlstr)
    while sz:
        entity = sz.group()  # entity全称，如&gt;
        key = sz.group('name')  # 去除&;后entity,如&gt;为gt
        try:
            htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
            sz = re_charEntity.search(htmlstr)
        except KeyError:
            # 以空串代替
            htmlstr = re_charEntity.sub('', htmlstr, 1)
            sz = re_charEntity.search(htmlstr)
    return htmlstr


def repalce(s, re_exp, repl_string):
    return re_exp.sub(repl_string, s)
