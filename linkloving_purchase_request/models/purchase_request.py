# -*- coding: utf-8 -*-
from email import utils

from odoo import models, fields, api


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = "Purchase Requisitions"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "name desc"

    def _full_gen_po(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for req in self.browse(cursor, user, ids, context=context):
            full_gen_po = True
            if req.line_ids:
                for req_line in req.line_ids:
                    if not req_line.generated_po:
                        full_gen_po = False
                        break
            res[req.id] = full_gen_po
        return res

    def _req_pos(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the requisition related PO ids.
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = dict.fromkeys(ids, [])
        for req in self.browse(cr, uid, ids, context=context):
            po_ids = []
            for req_line in req.line_ids:
                for po_line in req_line.po_lines_ids:
                    if po_line.order_id.id not in po_ids:
                        po_ids.append(po_line.order_id.id)
            res[req.id] = po_ids
        return res

    name = fields.Char('Requisition#', size=32, required=True),
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
    user_id = fields.many2one('res.users', 'Requester', required=True, readonly=True,
                              states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
    date_request = fields.datetime('Requisition Date', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
    remark = fields.Text('Remark'),
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
    line_ids = fields.One2many('pur.req.line', 'req_id', 'Products to Purchase', readonly=True,
                               states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
    state = fields.Selection(
        [('draft', 'New'),
         ('confirmed', 'Confirmed'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected'),
         ('in_purchase', 'In Purchasing'),
         ('done', 'Purchase Done'),
         ('cancel', 'Cancelled')],
        'Status', track_visibility='onchange', required=True, ),
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Order Reference must be unique!'),
    ]

    def cancel_req_procurements(self):
        # get related procurement ids
        ids = []
        req_line_ids = self.pool['pur.req.line'].search([('req_id', 'in', ids)])
        proc_ids = self.pool['procurement.order'].search([('pur_req_line_id', 'in', req_line_ids)])
        # do related procurement order's cancel
        self.env['procurement.order'].cancel(proc_ids)
        return True

    def action_cancel_draft(self):
        pass

    def _email_notify(self, cr, uid, ids, mail_type, context=None):
        mail_types = {'confirmed': {'action': 'need your approval', 'groups': ['ydit_pur_req.group_pur_req_checker']},
                      'approved': {'action': 'approved, please issue PO',
                                   'groups': ['ydit_pur_req.group_pur_req_buyer']},
                      'rejected': {'action': 'was rejected, please check', 'groups': []},
                      'in_purchase': {'action': 'is in purchasing', 'groups': [], },
                      'done': {'action': 'was done', 'groups': ['ydit_pur_req.group_pur_req_buyer']},
                      'cancel': {'action': 'was cancelled', 'groups': []},
                      }
        model_obj = self.pool.get('ir.model.data')
        if mail_types.get(mail_type, False):
            action_name = mail_types[mail_type]['action']
            group_params = mail_types[mail_type]['groups']
            for order in self.browse(cr, uid, ids, context=context):
                # email to groups
                email_group_ids = []
                for group_param in group_params:
                    grp_data = group_param.split('.')
                    email_group_ids.append(model_obj.get_object_reference(cr, uid, grp_data[0], grp_data[1])[1])
                # email to users
                email_to = None
                if mail_type in (' rejected', 'done', 'cancel'):
                    email_to = order.user_id.email
                email_cc = None
                if mail_type in ('approved', 'in_purchase'):
                    email_cc = order.user_id.email
                # email messages
                email_subject = 'Purchase Requisition: %s %s' % (order.name, action_name)
                email_body = email_subject
                # the current user is the from user
                email_from = self.pool.get("res.users").read(cr, uid, uid, ['email'], context=context)['email']
                # send emails
                utils.email_send_group(cr, uid, email_from, email_to, email_subject, email_body, email_group_ids,
                                       email_cc=email_cc, context=context)


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "name desc"
