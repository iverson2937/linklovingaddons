# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import tools


class CrmMailMessage(models.Model):
    _inherit = 'mail.message'

    messages_label_ids = fields.Many2many('message.label', 'message_label_mail_message_type_rel', string='记录类型')

    messages_label_body = fields.Char()

    postil = fields.Text(string='批注')

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
        message_values = self.read([
            'id', 'body', 'date', 'author_id', 'email_from',  # base message fields
            'message_type', 'subtype_id', 'subject',  # message specific
            'model', 'res_id', 'record_name',  # document related
            'channel_ids', 'partner_ids',  # recipients
            'needaction_partner_ids',  # list of partner ids for whom the message is a needaction
            'starred_partner_ids',  # list of partner ids for whom the message is starred
            'messages_label_ids',
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


class CrmMessageLabelStatus(models.Model):
    _name = 'message.order.status'
    name = fields.Char(string=u'订单状态')
    description = fields.Text(string=u'描述')
