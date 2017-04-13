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
# from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare
from openerp import workflow

import logging


class cron_job(osv.osv_memory):
    _inherit = "cron.job"

    def pur_req_state_update(self, cr, uid, context=None):
        _logger = logging.getLogger(__name__)
        _logger.info('#########pur_req_state_update  begin##########')
        pur_req_obj = self.pool.get('pur.req')
        procurement_order_obj = self.pool.get('procurement.order')
        # wf_service = netsvc.LocalService("workflow")

        pur_req_ids = pur_req_obj.search(cr, uid, [('state', '=', 'in_purchase')], context=context)
        uom_obj = self.pool.get('product.uom')
        if context is None:
            context = {}
        for pur_req in pur_req_obj.browse(cr, uid, pur_req_ids, context=context):
            pur_req_received = True
            for pur_req_line in pur_req.line_ids:
                if not pur_req_line.generated_po:
                    pur_req_received = False
                    continue
                pur_req_line_received = True
                rec_qty = 0
                # check the pur_req's po line receiving status
                for po_line in pur_req_line.po_lines_ids:
                    if po_line.state in ('approved', 'done', 'done_except'):
                        if po_line.receive_qty != po_line.product_qty:
                            break
                        else:
                            ctx_uom = context.copy()
                            ctx_uom['raise-exception'] = False
                            # convert the po quantity the req quantity
                            uom_po_qty = uom_obj._compute_qty_obj(cr, uid, po_line.product_uom, po_line.product_qty, \
                                                                  pur_req_line.product_uom_id, context=ctx_uom)
                            rec_qty += uom_po_qty
                req_finished = float_compare(pur_req_line.product_qty, rec_qty, precision_rounding=1)
                pur_req_line_received = (req_finished <= 0)
                # if all po lines are received then trigger the related procurement order to go 'ready' state
                if pur_req_line_received:
                    pro_ids = procurement_order_obj.search(cr, uid, [('pur_req_line_id', '=', pur_req_line.id)],
                                                           context=context)
                    for pro_id in pro_ids:
                        # wf_service.trg_validate(uid, 'procurement.order', pro_id, 'pur_req_done', cr)
                        workflow.trg_validate(uid, 'procurement.order', pro_id, 'pur_req_done', cr)
                else:
                    pur_req_received = False
            # if all of req lines were received, then po.req will go to done state
            if pur_req_received:
                # wf_service.trg_validate(uid, 'pur.req', pur_req.id, 'pur_req_done', cr)
                workflow.trg_validate(uid, 'pur.req', pur_req.id, 'pur_req_done', cr)
        _logger.info('#########pur_req_state_update  end##########')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
