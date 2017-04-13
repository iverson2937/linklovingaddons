# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import netsvc

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
from openerp.addons.ydit_base import utils


class pur_req(osv.osv):
    _name = "pur.req"
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

    _columns = {
        'name': fields.char('Requisition#', size=32, required=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True, readonly=True,
                                        states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'Requester', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
        'date_request': fields.datetime('Requisition Date', required=True, readonly=True,
                                        states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
        'remark': fields.text('Remark'),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True,
                                      states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
        'line_ids': fields.one2many('pur.req.line', 'req_id', 'Products to Purchase', readonly=True,
                                    states={'draft': [('readonly', False)], 'rejected': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'New'), ('confirmed', 'Confirmed'), ('approved', 'Approved'), ('rejected', 'Rejected'),
             ('in_purchase', 'In Purchasing'), ('done', 'Purchase Done'), ('cancel', 'Cancelled')],
            'Status', track_visibility='onchange', required=True, ),
        #        'po_ids' : fields.one2many('purchase.order','req_id','Related PO'),
        # once user did merging PO, then one PO may have multi requestions, so change this field to a function field
        'po_ids': fields.function(_req_pos, type='one2many', relation='purchase.order', string='Related PO'),
        'full_gen_po': fields.function(_full_gen_po, string='All products generated PO', type='boolean',
                                       help="It indicates that this requsition's all lines generated PO"),
    }
    _defaults = {
        #        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'pur.req'),
        'name': lambda obj, cr, uid, context: '/',
        #        'warehouse_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
        'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id,
        'date_request': lambda *args: time.strftime('%Y-%m-%d %H:%M:%S'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'pur.req',
                                                                                                 context=c),
        'state': 'draft',
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Order Reference must be unique!'),
    ]

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'po_ids': [],
            'name': self.pool.get('ir.sequence').get(cr, uid, 'pur.req'),
        })
        return super(pur_req, self).copy(cr, uid, id, default, context)

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'pur.req') or '/'
        order = super(pur_req, self).create(cr, uid, vals, context=context)
        return order

    def wkf_confirm_req(self, cr, uid, ids, context=None):
        for req in self.browse(cr, uid, ids, context=context):
            if not req.line_ids:
                raise osv.except_osv(_('Error!'),
                                     _('You cannot confirm a purchase requisition order without any product line.'))

        self.write(cr, uid, ids, {'state': 'confirmed'})
        return True

    def wkf_cancel_req(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for req in self.browse(cr, uid, ids, context=context):
            for po in req.po_ids:
                if po.state not in ('cancel'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase requisition.'),
                        _('First cancel all purchase orders related to this purchase order.'))
                #            for po in req.po_ids:
                #                wf_service.trg_validate(uid, 'purchase.order', po.id, 'purchase_cancel', cr)

        self.write(cr, uid, ids, {'state': 'cancel'})

        # cancel related procurement orders
        self.cancel_req_procurements(cr, uid, ids, context=context)

        return True

    def unlink(self, cr, uid, ids, context=None):
        pur_reqs = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in pur_reqs:
            if s['state'] in ['draft', 'cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'),
                                     _('In order to delete a purchase requisition, you must cancel it first.'))
        # cancel related procurement orders
        self.cancel_req_procurements(cr, uid, ids, context=context)

        # automatically sending subflow.delete upon deletion
        wf_service = netsvc.LocalService("workflow")
        for id in unlink_ids:
            wf_service.trg_validate(uid, 'pur.req', id, 'pur_req_cancel', cr)

        return super(pur_req, self).unlink(cr, uid, unlink_ids, context=context)

    def cancel_req_procurements(self, cr, uid, ids, context=None):
        # get related procurement ids
        req_line_ids = self.pool['pur.req.line'].search(cr, uid, [('req_id', 'in', ids)], context=context)
        proc_ids = self.pool['procurement.order'].search(cr, uid, [('pur_req_line_id', 'in', req_line_ids)],
                                                         context=context)
        # do related procurement order's cancel
        self.pool['procurement.order'].cancel(cr, uid, proc_ids)
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            # Deleting the existing instance of workflow for requisition
            wf_service.trg_delete(uid, 'pur.req', p_id, cr)
            wf_service.trg_create(uid, 'pur.req', p_id, cr)
        return True

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


pur_req()


class pur_req_line(osv.osv):
    _name = "pur.req.line"
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

    _columns = {
        'req_id': fields.many2one('pur.req', 'Purchase Requisition', ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                    required=True),
        'product_uom_id': fields.many2one('product.uom', 'Product UOM', required=True),
        'inv_uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom',
                                     string='Inventory UOM', readonly=True),
        'date_required': fields.date('Date Required', required=True),
        'inv_qty': fields.float('Inventory'),
        'req_emp_id': fields.many2one('hr.employee', 'Employee'),
        'req_dept_id': fields.related('req_emp_id', 'department_id', type='many2one', relation='hr.department',
                                      string='Department', readonly=True),
        'req_reason': fields.char('Reason and use', size=64),
        'company_id': fields.related('req_id', 'company_id', type='many2one', relation='res.company', String='Company',
                                     store=True, readonly=True),
        'po_lines_ids': fields.one2many('purchase.order.line', 'req_line_id', 'Purchase Order Lines', readonly=True),
        'generated_po': fields.function(_po_info, multi='po_info', string='PO Generated', type='boolean',
                                        help="It indicates that this products has PO generated"),
        'product_qty_remain': fields.function(_po_info, multi='po_info', string='Qty Remaining', type='float',
                                              digits_compute=dp.get_precision('Product Unit of Measure')),
        'procurement_ids': fields.one2many("procurement.order", 'pur_req_line_id', 'Procurements'),
        'po_info': fields.function(_po_info, multi='po_info', type='char', string='PO Quantity', readonly=True),
        'req_ticket_no': fields.char('Requisition Ticket#', size=10),
        'order_warehouse_id': fields.related('req_id', 'warehouse_id', type='many2one', relation='stock.warehouse',
                                             string='Warehouse', readonly=True),
        'order_user_id': fields.related('req_id', 'user_id', type='many2one', relation='res.users', string='Requester',
                                        readonly=True),
        'order_date_request': fields.related('req_id', 'date_request', type='datetime', string='Requisition Date',
                                             readonly=True),
        'order_state': fields.related('req_id', 'state', type='selection', string='Status', readonly=True,
                                      selection=[('draft', 'New'), ('confirmed', 'Confirmed'), ('approved', 'Approved'),
                                                 ('rejected', 'Rejected'), ('in_purchase', 'In Purchasing'),
                                                 ('done', 'Purchase Done'), ('cancel', 'Cancelled')]),

    }
    _rec_name = 'product_id'

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        """ Changes UoM,inv_qty if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        value = {'product_uom_id': '', 'inv_qty': ''}
        res = {}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            value = {'product_qty': 1.0, 'inv_qty': prod.qty_available}
            uom = prod.uom_po_id or prod.uom_id
            value.update({'product_uom_id': uom.id, 'inv_uom_id': prod.uom_id.id})
            # - set a domain on product_uom
            domain = {'product_uom_id': [('category_id', '=', uom.category_id.id)]}
            res['domain'] = domain
            res['value'] = value
        return res

    _defaults = {
        'product_qty': lambda *a: 1.0,
    }

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
        res = super(pur_req_line, self).copy_data(cr, uid, id, default, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        procurement_ids = self.pool.get('procurement.order').search(cr, uid, [('pur_req_line_id', 'in', ids)],
                                                                    context=context)
        self.pool.get('procurement.order').action_cancel(cr, uid, procurement_ids)
        return super(pur_req_line, self).unlink(cr, uid, ids, context=context)


pur_req_line()


class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _columns = {
        'req_id': fields.many2one('pur.req', 'Purchase Requisition', readonly=True)
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'req_id': False,
        })
        res = super(purchase_order, self).copy_data(cr, uid, id, default, context)
        return res

    def new_po(self, cr, uid, pos, context=None):
        """
        Create New RFQ from requisition
        """
        if context is None:
            context = {}
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        warehouse_obj = self.pool.get('stock.warehouse')
        product_obj = self.pool.get('product.product')
        pricelist_obj = self.pool.get('product.pricelist')
        for po_data in pos:
            assert po_data['partner_id'], 'Supplier should be specified'
            assert po_data['warehouse_id'], 'Warehouse should be specified'
            supplier = res_partner.browse(cr, uid, po_data['partner_id'], context=context)
            warehouse = warehouse_obj.browse(cr, uid, po_data['warehouse_id'], context=context)

            if not po_data.has_key('location_id'):
                po_data['location_id'] = warehouse.wh_input_stock_loc_id.id
            if not po_data.has_key('pricelist_id'):
                supplier_pricelist = supplier.property_product_pricelist_purchase or False
                po_data['pricelist_id'] = supplier_pricelist.id
            if not po_data.has_key('fiscal_position'):
                po_data[
                    'fiscal_position'] = supplier.property_account_position and supplier.property_account_position.id or False
            if not po_data.has_key('company_id'):
                company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order',
                                                                               context=context)
                po_data['company_id'] = company_id
            # add the default value of notes
            po_data.update(purchase_order.default_get(cr, uid, ['notes'], context=context))
            new_po_id = purchase_order.create(cr, uid, po_data)
            # assign the new po id to po data, then the caller call get the new po's info
            po_data['new_po_id'] = new_po_id
            pricelist_id = po_data['pricelist_id'];
            for line in po_data['lines']:
                product = product_obj.browse(cr, uid, line['product_id'], context=context)
                # taxes
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                taxes_id = [(6, 0, taxes)]

                line.update({'order_id': new_po_id, 'taxes_id': taxes_id})

                # set the line description
                name = product.name
                if product.description_purchase:
                    name += '\n' + product.description_purchase
                if line.get('name'):
                    name += '\n' + line.get('name')
                line.update({'name': name})

                # unit price
                if not line.has_key('price_unit'):
                    price_unit = seller_price = \
                    pricelist_obj.price_get(cr, uid, [pricelist_id], product.id, line['product_qty'], False,
                                            {'uom': line['product_uom']})[pricelist_id]
                    line['price_unit'] = price_unit
                new_po_line_id = purchase_order_line.create(cr, uid, line, context=context)
                line['new_po_line_id'] = new_po_line_id

        return pos


class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    _columns = {
        'req_line_id': fields.many2one('pur.req.line', 'Purchase Requisition', readonly=True)}

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'req_line_id': False,
        })
        res = super(purchase_order_line, self).copy_data(cr, uid, id, default, context)
        return res

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
