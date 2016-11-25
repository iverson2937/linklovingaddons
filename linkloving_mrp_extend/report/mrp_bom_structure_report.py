# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class BomStructureReport(models.AbstractModel):
    _inherit = 'report.mrp.report_mrpbomstructure'

    def get_children(self, object, level=0):
        result = []

        def _get_rec(object, level, qty=1.0):
            for l in object:
                res = {}
                res['pname'] = l.product_id.name_get()[0][1]
                res['pcode'] = l.product_id.default_code
                res['pqty'] = l.product_qty * qty
                res['uname'] = l.product_uom_id.name
                res['level'] = level
                res['code'] = l.bom_id.code
                res['product_specs'] = l.product_id.product_specs
                result.append(res)
                if l.child_line_ids:
                    if level < 6:
                        level += 1
                    _get_rec(l.child_line_ids, level, qty=res['pqty'])
                    if level > 0 and level < 6:
                        level -= 1
            return result

        children = _get_rec(object, level)

        return children
