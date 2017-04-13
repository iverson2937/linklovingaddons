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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare

import logging


class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    _columns = {
        'pur_req_line_id': fields.many2one('pur.req.line', 'Purchase Requsition Line'),
        'pur_req_id': fields.related('pur_req_line_id', 'req_id', type="many2one", relation='pur.req',
                                     string='Purchase Requsition', readonly=True),
    }


# def action_pur_req_assign(self, cr, uid, ids, context=None):
#        """ This is action which call from workflow to assign purchase order to procurements
#        @return: True
#        """
#        res = self.make_pur_req(cr, uid, ids, context=context)
#        res = res.values()
#        return len(res) and res[0] or 0
#
#    def _get_purchase_schedule_date(self, cr, uid, procurement, company, context=None):
#        """Return the datetime value to use as Schedule Date (``date_planned``) for the
#           Purchase Order Lines created to satisfy the given procurement.
#
#           :param browse_record procurement: the procurement for which a PO will be created.
#           :param browse_report company: the company to which the new PO will belong to.
#           :rtype: datetime
#           :return: the desired Schedule Date for the PO lines
#        """
#        procurement_date_planned = datetime.strptime(procurement.date_planned, DEFAULT_SERVER_DATETIME_FORMAT)
#        schedule_date = (procurement_date_planned - relativedelta(days=company.po_lead))
#        return schedule_date
#
#    def get_pur_req_id(self, cr, uid, pur_req_vals, context=None):
#        pur_req_obj = self.pool.get('pur.req')
#        domains = [(arg,'=',arg_val) for arg, arg_val in pur_req_vals.items()]
#        domains += [('date_request','>=',time.strftime('%Y-%m-%d 00:00:00')),('date_request','<=',time.strftime('%Y-%m-%d 23:59:59')),]
#        pur_req_ids = pur_req_obj.search(cr, uid, domains, context=context)
#        if pur_req_ids:
#            pur_req_id = pur_req_ids[0]
#        else:
#            pur_req_id = pur_req_obj.create(cr, uid, pur_req_vals, context=context)
#            
#        return pur_req_id  
#            
#    def make_pur_req(self, cr, uid, ids, context=None):
#        """ Make purchase requisition order from procurement
#        @return: New created Purchase Requisition Orders procurement wise
#        """
#        res = {}
#        if context is None:
#            context = {}
#        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
#        uom_obj = self.pool.get('product.uom')
#        prod_obj = self.pool.get('product.product')
#        warehouse_obj = self.pool.get('stock.warehouse')
#        pur_req_line_obj = self.pool.get('pur.req.line')
#        
#        for procurement in self.browse(cr, uid, ids, context=context):
##            res_id = procurement.move_id.id
#            warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
#            if procurement.company_id:
#                company = procurement.company_id
#            uom_id = procurement.product_id.uom_po_id.id
#            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
#            schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)            
#            product = prod_obj.browse(cr, uid, procurement.product_id.id, context=context)
#            pur_req_vals = {
#                'warehouse_id': warehouse_id and warehouse_id[0] or False,
#                'user_id': uid,
#                'company_id': company.id,
#                'state': 'draft'
#            }
#            pur_req_id = self.get_pur_req_id(cr, uid, pur_req_vals, context=context)
#            pur_req_line_vals = {
#                'req_id': pur_req_id,
#                'name': product.partner_ref,
#                'product_qty': qty,
#                'product_id': procurement.product_id.id,
#                'product_uom_id': uom_id,
#                'inv_qty': procurement.product_id.qty_available,
#                'date_required': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
#                'req_reason': 'Procurement [%s] with source %s'%(procurement.id,procurement.origin),
#        #        'req_emp_id': fields.many2one('hr.employee','Employee'),
#        #        'req_dept_id': fields.related('req_emp_id','department_id',type='many2one',relation='hr.department',string='Department',readonly=True),
##                'move_dest_id': res_id,
#            }
#            pur_req_line_id = pur_req_line_obj.create(cr, uid, pur_req_line_vals, context=context)
#            res[procurement.id] = pur_req_line_id
#            self.write(cr, uid, [procurement.id], {'state': 'running', 'pur_req_line_id': pur_req_line_id})
##        self.message_post(cr, uid, ids, body=_("Draft Purchase Order created"), context=context)
#        return res



procurement_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
