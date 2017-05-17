# -*- coding: utf-8 -*-
import json
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BomUpdateWizard(models.TransientModel):
    _name = "bom.update.wizard"
    postfix = fields.Char(string=u'后缀')

    @api.multi
    def bom_line_update(self):
        context = self._context
        main_bom_id = int(context.get('bom_id'))
        postfix = self.postfix
        update = context.get('update')
        vals = context.get('back_datas')
        line_obj = self.env['mrp.bom.line']
        bom_obj = self.env['mrp.bom']
        product_tmpl_obj = self.env['product.template']
        products = {}
        temp_product_id = False

        if not update:
            for val in vals:
                product_id = val.get('product_id')
                parents = val.get('parents')
                to_update_bom_line_ids = parents.split(',')
                for line in to_update_bom_line_ids:
                    line = int(line)
                    if line != main_bom_id:
                        line_id = self.env['mrp.bom.line'].browse(int(line))
                        if not products.get(line_id.product_id):
                            old_product_tmpl_id = line_id.product_id
                            default_code = get_next_default_code(old_product_tmpl_id.default_code)
                            new_product_tmpl_id = line_id.product_id.product_tmpl_id.copy(
                                {'name': old_product_tmpl_id.name + postfix,
                                 'default_code': default_code})
                            new_bom_id = line_id.bom_id.copy()
                            new_bom_id.product_tmpl_id = new_product_tmpl_id.id
                            products.update({
                                line_id.product_id: {
                                    'new_product_tmpl_id': new_product_tmpl_id.id,
                                    'new_bom_id': new_bom_id.id
                                }
                            })
                        else:
                            new_product_tmpl_id = product_tmpl_obj.browse(
                                products.get(line_id.product_id).get('new_product_tmpl_id'))
                            new_bom_id = bom_obj.browse(products.get(line_id.product_id).get('new_bom_id'))


                    else:
                        bom_id = bom_obj.browse(line)
                        old_product_tmpl_id = bom_id.product_tmpl_id
                        if not products.get('bom'):
                            default_code = get_next_default_code(old_product_tmpl_id.default_code)
                            new_product_tmpl_id = old_product_tmpl_id.copy({'name': old_product_tmpl_id.name + postfix,
                                                                            'default_code': default_code})
                            new_bom_id = bom_id.copy()
                            new_bom_id.product_tmpl_id = new_product_tmpl_id.id
                            products.update({
                                'bom': {
                                    'new_product_tmpl_id': new_product_tmpl_id.id,
                                    'new_bom_id': new_bom_id.id
                                }
                            })
                        else:
                            new_product_tmpl_id = product_tmpl_obj.browse(
                                products.get('bom').get('new_product_tmpl_id'))
                            new_bom_id = bom_obj.browse(products.get('bom').get('new_bom_id'))
                    if temp_product_id:
                        tmp_id = product_tmpl_obj.browse(temp_product_id)

                        update_bom_line_copy(new_bom_id, tmp_id.product_variant_ids[0].id, line_id.product_id)

                    if product_id:
                        line_obj.create({
                            'product_id': int(product_id),
                            'bom_id': new_bom_id.id,
                        })
                        product_id = False

                    temp_product_id = new_product_tmpl_id.id

    @api.multi
    def get_product_id_version(self):
        pass


def update_bom_line_copy(new_bom_id, new_product_id, old_product_id):
    if new_product_id:
        for line in new_bom_id.bom_line_ids:
            if line.product_id.id == old_product_id.id:
                line.product_id = new_product_id


def get_next_default_code(default_code):
    if not default_code:
        raise UserError(u'产品没有对应料号')

    raw_version = default_code.split('.')[-1]
    # 取前10位
    prefix = default_code[0:11]
    # FIXME:GET CORRECT VERSION
    version = ('000' + str(int(raw_version) + 1))[-3:]
    new_code = prefix + str(int(version) + 1)
    return new_code


if __name__ == '__main__':
    aaa = '001'
    abcv = int(aaa, base=3) + 1
    ddd = '000' + str(abcv)
    ac = '010'
    ccc = ('000' + str(int(ac) + 1))[-3:]
    print ccc
