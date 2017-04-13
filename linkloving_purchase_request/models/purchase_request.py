# -*- coding: utf-8 -*-
from email import utils

from odoo import models, fields, api, _
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


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

    name = fields.Char('Requisition#', size=32, required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'Requester', required=True, readonly=True,
                              states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]})
    date_request = fields.Datetime('Requisition Date', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]})
    remark = fields.Text('Remark'),
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]})
    line_ids = fields.One2many('pur.req.line', 'req_id', 'Products to Purchase', readonly=True,
                               states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]})
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
    _name = "purchase.request.line"
    _description = "Purchase Requisition Line"
    _rec_name = 'product_id'

    def _generated_po(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for req_line in self.browse(cursor, user, ids, context=context):
            generated_po = False
            if req_line.po_lines_ids:
                for po_line in req_line.po_lines_ids:
                    if po_line.state != 'cancel':
                        generated_po = True
                        break
            res[req_line.id] = generated_po
        return res

    def _po_info(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the requisition related PO info.
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)
        for req_line in self.browse(cr, uid, ids, context=context):
            generated_po = False
            req_qty = req_line.product_qty
            po_qty = 0
            product_qty_remain = req_line.product_qty
            po_qty_str = ''
            if req_line.po_lines_ids:
                uom_obj = self.pool.get('product.uom')
                for po_line in req_line.po_lines_ids:
                    if po_line.state != 'cancel':
                        ctx_uom = context.copy()
                        ctx_uom['raise-exception'] = False
                        uom_po_qty = uom_obj._compute_qty_obj(cr, uid, po_line.product_uom, po_line.product_qty, \
                                                              req_line.product_uom_id, context=ctx_uom)
                        po_qty += uom_po_qty
                        po_qty_str += ((po_qty_str or '') and '; ') + '%s(%s)@%s' % (
                            po_line.product_qty, uom_po_qty, po_line.order_id.name)
                        #                po_finished = float_compare(po_qty, req_qty, precision_rounding=req_line.product_uom_id.rounding)
                po_finished = float_compare(req_qty, po_qty, precision_rounding=1)
                generated_po = (po_finished <= 0)
                if generated_po:
                    product_qty_remain = 0
                else:
                    product_qty_remain = req_qty - po_qty
            res[req_line.id]['generated_po'] = generated_po
            res[req_line.id]['product_qty_remain'] = product_qty_remain
            res[req_line.id]['po_info'] = po_qty_str
        return res

    req_id = fields.Many2one('purchase.request', 'Purchase Requisition', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Many2one('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                  required=True)
    product_uom_id = fields.Many2one('product.uom', 'Product UOM', required=True)
    nv_uom_id = fields.Many2one('product.uom', relation='product.uom',
                                string='Inventory UOM', readonly=True)
    date_required = fields.Date('Date Required', required=True)
    inv_qty = fields.Float('Inventory')
    req_emp_id = fields.Many2one('hr.employee', 'Employee')
    req_dept_id = fields.Many2one('hr.department', string='Department', readonly=True)
    req_reason = fields.Char('Reason and use'),
    # company_id = fields.Many2one('req_id', 'company_id', type='many2one', relation='res.company', String='Company',
    #                          store=True, readonly=True)
    po_lines_ids = fields.One2many('purchase.order.line', 'req_line_id', 'Purchase Order Lines', readonly=True)
    # generated_po = fields.Boolean(_po_info, multi='po_info', string='PO Generated', type='boolean',
    #                               help="It indicates that this products has PO generated")
    # product_qty_remain = fields.Float(_po_info, multi='po_info', string='Qty Remaining', type='float',
    #                                   digits_compute=dp.get_precision('Product Unit of Measure'))
    procurement_ids = fields.One2many("procurement.order", 'pur_req_line_id', 'Procurements')
    # po_info = fields.Char(_po_info, multi='po_info', type='char', string='PO Quantity', readonly=True)
    req_ticket_no = fields.Char('Requisition Ticket#', size=10)

    order_state = fields.Selection(related='order_id.state', string='Status', readonly=True,
                                   selection=[('draft', 'New'), ('confirmed', 'Confirmed'), ('approved', 'Approved'),
                                              ('rejected', 'Rejected'), ('in_purchase', 'In Purchasing'),
                                              ('done', 'Purchase Done'), ('cancel', 'Cancelled')])

    _rec_name = 'product_id'

    @api.multi
    def onchange_product_id(self):
        """ Changes UoM,inv_qty if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        value = {'product_uom_id': '', 'inv_qty': ''}
        res = {}
        prod = self.product_id
        value = {'product_qty': 1.0, 'inv_qty': prod.qty_available}
        uom = prod.uom_po_id or prod.uom_id
        value.update({'product_uom_id': uom.id, 'inv_uom_id': prod.uom_id.id})
        # - set a domain on product_uom
        domain = {'product_uom_id': [('category_id', '=', uom.category_id.id)]}
        res['domain'] = domain
        res['value'] = value
        return res

    def onchange_product_uom(self, cr, uid, ids, product_id, uom_id, context=None):
        """
        onchange handler of product_uom.
        """
        res = {}
        if not uom_id:
            return {'value': {'product_uom_id': False}}
        # - check that uom and product uom belong to the same category
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        prod_uom = product.uom_po_id or product.uom_id
        uom = self.pool.get('product.uom').browse(cr, uid, uom_id, context=context)
        if prod_uom.category_id.id != uom.category_id.id:
            if self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _(
                    'Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = prod_uom.id

        # - set a domain on product_uom
        domain = {'product_uom_id': [('category_id', '=', prod_uom.category_id.id)]}
        res['domain'] = domain
        res['value'] = {'product_uom_id': uom_id}
        return res

    def _check_product_uom_group(self, cr, uid, context=None):
        group_uom = self.pool.get('ir.model.data').get_object(cr, uid, 'product', 'group_uom')
        res = [user for user in group_uom.users if user.id == uid]
        return len(res) and True or False

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'po_lines_ids': [],
        })
        res = super(PurchaseRequestLine, self).copy_data(default)
        return res

    def unlink(self):
        ids = []
        procurement_ids = self.env('procurement.order').search([('pur_req_line_id', 'in', ids)])
        self.env['procurement.order'].action_cancel(procurement_ids)
        return super(PurchaseRequestLine, self).unlink()
