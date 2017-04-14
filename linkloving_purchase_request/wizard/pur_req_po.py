# -*- coding: utf-8 -*-
from email import utils

import datetime

from odoo import models, fields, api, _
from odoo.tools import float_compare, DEFAULT_SERVER_DATE_FORMAT
import odoo.addons.decimal_precision as dp


class pur_req_po_line(models.TransientModel):
    _name = "pur.req.po.line"
    _rec_name = 'product_id'

    wizard_id = fields.Ma('pur.req.po', string="Wizard")
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                               required=True)
    product_qty_remain = fields.Float('Quantity Remain',
                                      digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    price_unit = fields.Float('Unit Price', digits_compute=dp.get_precision('Product Price'))
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    date_required = fields.Date('Date Required', required=True)
    inv_qty = fields.Float('Inventory')
    req_reason = fields.Char('Reason and use', size=64)
    req_line_id = fields.Many2one('pur.req.line', 'Purchase Requisition')

    uom_po_qty = fields.Float('PO Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                              required=True)
    uom_po_qty_remain = fields.Float('PO Quantity Remain',
                                     digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    uom_po_price = fields.Float('PO Unit Price', digits_compute=dp.get_precision('Product Price'))
    uom_po_id = fields.Many2one('product.uom', 'PO Unit of Measure', required=True)
    uom_po_factor = fields.Float('UOM Ratio', digits=(12, 4))

    supplier_prod_name = fields.Char(string='Supplier Product Name')

    @api.multi
    def _check_product_qty(self):
        for line in self:
            #            if line.product_qty > line.product_qty_remain:
            #                raise osv.except_osv(_('Warning!'), _("Product '%s' max po quantity is %s, you can not purchae %s"%(line.product_id.default_code + '-' + line.product_id.name, line.product_qty_remain, line.product_qty)))
            if line.uom_po_qty > line.uom_po_qty_remain:
                pass
        return True

    _constraints = [(_check_product_qty, 'Product quantity exceeds the remaining quantity', ['product_qty'])]

    def onchange_lead(self, cr, uid, ids, change_type, changes_value, context=None):
        date_order = fields.date.context_today(self, cr, uid, context=context)
        res = {'value': {}}
        if change_type == 'date_required':
            supplier_delay = datetime.strptime(changes_value, DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime(
                date_order, DEFAULT_SERVER_DATE_FORMAT)
            res['value'] = {'supplier_delay': supplier_delay.days}
        if change_type == 'supplier_delay':
            date_required = datetime.strptime(date_order, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(
                days=changes_value)
            date_required = datetime.strftime(date_required, DEFAULT_SERVER_DATE_FORMAT)
            res['value'].update({'date_required': date_required})
        return res






class pur_req_po(osv.osv_memory):
    _name = 'pur.req.po'
    _description = 'Requisition\'s Purchase Order'
    _columns = {
        'line_ids': fields.one2many('pur.req.po.line', 'wizard_id', 'Prodcuts'),
        'partner_id': fields.many2one('res.partner', 'Supplier', required=True, domain=[('supplier', '=', True)]),
    }

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        line_data = []
        if context is None:
            context = {}
        res = super(pur_req_po, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        req_obj = self.pool.get('pur.req')
        req = req_obj.browse(cr, uid, record_id, context=context)
        partner_id = None
        if req:
            uom_obj = self.pool.get('product.uom')
            for line in req.line_ids:
                if not line.generated_po:
                    uom_po_qty = uom_obj._compute_qty_obj(cr, uid, line.product_uom_id, line.product_qty_remain,
                                                          line.product_id.uom_po_id, context=context)
                    print 'line', line
                    # uom_po_factor = line.product_id.uom_po_factor/line.product_uom_id.factor_display
                    line_data.append({'product_id': line.product_id.id,
                                      'product_qty_remain': line.product_qty_remain,
                                      'product_qty': line.product_qty_remain,
                                      'product_uom_id': line.product_uom_id.id,
                                      'price_unit': line.product_id.standard_price,

                                      'uom_po_qty_remain': uom_po_qty,
                                      'uom_po_qty': uom_po_qty,
                                      'uom_po_id': line.product_id.uom_po_id.id,
                                      # 'uom_po_price':line.product_id.uom_po_price,
                                      # 'uom_po_factor':uom_po_factor,

                                      'inv_qty': line.product_id.qty_available,
                                      'date_required': line.date_required,
                                      'req_line_id': line.id,
                                      'req_reason': line.req_reason,
                                      })
                    if partner_id == None:
                        partner_id = line.product_id.seller_id.id

            res.update({'line_ids': line_data, 'partner_id': partner_id})
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        """
         Creates view dynamically and adding fields at runtime.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view with new columns.
        """
        if context is None:
            context = {}
        res = super(pur_req_po, self).view_init(cr, uid, fields_list, context=context)
        record_id = context and context.get('active_id', False)
        if record_id:
            req_obj = self.pool.get('pur.req')
            req = req_obj.browse(cr, uid, record_id, context=context)
            if req.state == 'draft':
                raise osv.except_osv(_('Warning!'),
                                     _("You may only generate purchase orders based on confirmed requisitions!"))
            valid_lines = 0
            for line in req.line_ids:
                if not line.generated_po:
                    valid_lines += 1
            if not valid_lines:
                raise osv.except_osv(_('Warning!'), _("No available products need to generate purchase order!"))
        return res

    def onchange_partner(self, cr, uid, ids, partner_id, lines, context):
        resu = {'value': {}}
        prod_supp_obj = self.pool.get('product.supplierinfo')
        line_rets = []
        for line in lines:
            if not line[2]:
                continue
            line_dict = line[2]
            # update the product supplier info
            prod_supp_ids = prod_supp_obj.search(cr, uid, [('product_tmpl_id', '=', line_dict['product_id']),
                                                           ('name', '=', partner_id)])
            if prod_supp_ids and len(prod_supp_ids) > 0:
                prod_supp = prod_supp_obj.browse(cr, uid, prod_supp_ids[0], context=context)
                line_dict.update({'supplier_prod_name': prod_supp.product_name})
            else:
                line_dict.update({'supplier_prod_name': ''})
            line_rets.append(line_dict)
        resu['value']['line_ids'] = line_rets
        return resu

    def _create_po(self, cr, uid, ids, context=None):
        record_id = context and context.get('active_id', False) or False
        data = self.browse(cr, uid, ids, context=context)[0]
        req = self.pool.get('pur.req').browse(cr, uid, record_id, context=None);
        po_data = {'origin': req.name, 'req_id': record_id, 'partner_id': data.partner_id.id,
                   'warehouse_id': req.warehouse_id.id, 'notes': req.remark, 'company_id': req.company_id.id,
                   'lines': []}
        po_lines = []
        for line in data.line_ids:
            po_line = {'product_id': line.product_id.id, 'product_qty': line.uom_po_qty,
                       'product_uom': line.uom_po_id.id,
                       'req_line_id': line.req_line_id.id, 'date_planned': line.date_required,
                       'price_unit': line.uom_po_price,
                       'name': (line.req_reason or ''),
                       'supplier_prod_name': line.supplier_prod_name, }
            # add the move_dest_id for the po_line
            procurement_id = line.req_line_id.procurement_ids and line.req_line_id.procurement_ids[0] or False
            if procurement_id:
                if procurement_id.move_id:
                    po_line.update({'move_dest_id': procurement_id.move_id.id})

            po_lines.append(po_line);
        po_data['lines'] = po_lines
        # call purchase.oder to generate order
        ret_po = self.pool.get('purchase.order').new_po(cr, uid, [po_data], context=context)
        # set req status to in_purchase
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'pur.req', record_id, 'pur_req_purchase', cr)
        # the 'po_id','po_line_id' should be pushed in the purchase.order.make_po() method
        return po_data['new_po_id']

    def create_view_po(self, cr, uid, ids, context=None):
        record_id = context and context.get('active_id', False) or False
        self._create_po(cr, uid, ids, context=context)
        return {
            'domain': "[('req_id', 'in', [" + str(record_id) + "])]",
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': context,
        }

    def create_po(self, cr, uid, ids, context=None):
        self._create_po(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
