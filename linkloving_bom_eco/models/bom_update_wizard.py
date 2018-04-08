# -*- coding: utf-8 -*-
import json
import re
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    def set_bom_line_product_bom_released(self):
        eco_ids = self.bom_id.eco_ids.filtered(lambda x: x.state != 'done')
        if eco_ids:
            for eco in eco_ids:
                eco.bom_apply()

        return super(MrpBomLine, self).set_bom_line_product_bom_released()


class BomUpdateWizard(models.TransientModel):
    _inherit = "bom.update.wizard"

    @api.model
    def bom_line_save(self, params, main_bom_id):
        line_obj = self.env['mrp.bom.line']
        bom_obj = self.env['mrp.bom']
        product_id_obj = self.env['product.product']
        bom_eco_obj = self.env['mrp.bom.eco']
        eco_line_obj = self.env['mrp.eco.line']
        eco_lines = []

        for val in params:
            product_id = int(val.get('productid'))
            parents = val.get('parents')
            input_changed_value = val.get('input_changed_value')
            last_bom_line_id = val.get('pId')
            qty = val.get('qty')
            name = val.get('name')
            modify_type = val.get('modify_type')
            product_specs = val.get('product_specs')

            to_update_bom_line_ids = parents
            line = int(to_update_bom_line_ids[0])
            if line != main_bom_id:
                line_id = self.env['mrp.bom.line'].browse(int(line))
                if line_id.product_id.product_tmpl_id.bom_ids:
                    bom_id = line_id.product_id.product_tmpl_id.bom_ids
                else:
                    bom_id = self.env['mrp.bom'].create({
                        'product_tmpl_id': line_id.product_id.product_tmpl_id.id
                    })
            else:
                bom_id = bom_obj.browse(line)

            if modify_type == 'add':
                # 创建一个产品并且添加一个bom_line
                if input_changed_value:
                    product_tmpl_id = product_id_obj.browse(int(product_id)).product_tmpl_id
                    new_name = self.get_new_product_name(name, '')
                    default_code = self.get_next_default_code(product_tmpl_id.default_code)
                    new_pl_id = product_tmpl_id.copy({'name': new_name, 'default_code': default_code})
                    product_id = new_pl_id.product_variant_ids[0].id

                if product_id:
                    line_obj.create({
                        'product_id': int(product_id),
                        'product_qty': qty,
                        'is_highlight': True,
                        'bom_id': bom_id.id,
                    })
                    # 此为修改bom，需要删除一个bom_line

                vals = {
                    'new_product_id': product_id,
                    'bom_id': bom_id.id,
                    'operate_type': 'add'
                }
                eco_lines.append(vals)
            elif modify_type == 'edit':
                product_tmpl_id = product_id_obj.browse(product_id).product_tmpl_id
                if input_changed_value:

                    new_name = self.get_new_product_name(name, '')
                    default_code = self.get_next_default_code(product_tmpl_id.default_code)
                    new_pl_id = product_tmpl_id.copy({'name': new_name, 'default_code': default_code})
                    product_id = new_pl_id.product_variant_ids[0].id
                else:
                    product_tmpl_id.write({
                        'name': name,
                        'product_specs': product_specs
                    })
                    # 只是修改名名称和规格 继续下一个循环

                currnet_bom_line_id = line_obj.browse(int(val.get('id')))
                #

                delete_vals = {
                    'bom_id': bom_id.id,
                    'product_id': currnet_bom_line_id.product_id.id,
                    'operate_type': 'delete'

                }
                if product_id:
                    currnet_bom_line_id.write({
                        'product_id': int(product_id),
                        'product_qty': qty,
                        'is_highlight': True,
                    })
                if product_id == currnet_bom_line_id.product_id:

                    add_vals = {
                        'bom_id': bom_id.id,
                        'product_id': product_id,
                        'operate_type': 'add'
                    }
                    delete_vals = {
                        'bom_id': bom_id.id,
                        'product_id': currnet_bom_line_id.product_id.id,
                        'operate_type': 'remove'
                    }
                    eco_lines.append(add_vals)
                    eco_lines.append(delete_vals)
                else:
                    print 'sssssssssssssssssssssssssssssssssss'
                    update_val = {
                        'bom_id': bom_id.id,
                        'product_id': product_id,
                        'operate_type': 'update',
                        'new_product_qty': qty
                    }
                    eco_lines.append(update_val)


            # 直接删除line无需添加
            elif modify_type == 'delete':
                del_bom_line_id = line_obj.browse(val.get('id'))
                old_product_id = del_bom_line_id.product_id
                delete_vals = {
                    'bom_id': bom_id.id,
                    'product_id': del_bom_line_id.product_id.id,
                    'operate_type': 'remove'

                }
                update_bom_line_delete(bom_id, old_product_id)

                eco_lines.append(delete_vals)
            for line in eco_lines:
                bom_id = line.get('bom_id')
                bom_obj_id = bom_obj.browse(bom_id)
                product_id = line.get('product_id')
                operate_type = line.get('operate_type')
                new_product_qty = line.get('new_product_qty')
                bom_eco_id = bom_eco_obj.search([('state', '=', 'draft'), ('bom_id', '=', bom_id)])
                if bom_eco_id:
                    line_id = bom_eco_id.filtered(
                        lambda x: x.product_id.id == product_id and x.operate_type == operate_type)
                    if not line_id:
                        eco_line_obj.create({
                            'bom_id': bom_id,
                            'product_id': product_id,
                            'operate_type': operate_type,
                            'new_product_qty': new_product_qty,
                            'bom_eco_id': bom_eco_id.id
                        })
                    else:
                        line_id.write({
                            'new_product_qty': new_product_qty,
                        })

                else:
                    bom_eco_obj.create({
                        'bom_id': bom_id,
                        'old_version': bom_obj_id.verion,
                        'new_version': bom_obj_id.verion + 1,
                        'bom_change_ids': [(0, 0, {
                            'bom_id': bom_id,
                            'product_id': product_id,
                            'operate_type': operate_type,
                            'new_product_qty': new_product_qty,
                        })]
                    })

            # eco_order_obj.create({
            #     'eco_line_ids':
            #         [(0, 0, {
            #             'bom_id': line.get('bom_id'),
            #             'product_id': line.get('product_id'),
            #             'operate_type': line.get('operate_type'),
            #             'new_product_qty': line.get('new_product_qty'),
            #         }) for line in eco_lines]
            #
            # })

        return {}


def update_bom_line_delete(new_bom_id, old_product_id):
    for line in new_bom_id.bom_line_ids:
        if line.product_id.id == old_product_id.id:
            line.unlink()
