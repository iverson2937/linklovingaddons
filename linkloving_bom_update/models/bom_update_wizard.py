# -*- coding: utf-8 -*-
import json
import re
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BomUpdateWizard(models.TransientModel):
    _name = "bom.update.wizard"
    postfix = fields.Char(string=u'后缀')
    partner_id = fields.Many2one('res.partner', domain=[('customer', '=', True), ('is_company', '=', True)])

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.postfix = self.partner_id.customer_alias

    @api.multi
    def bom_line_update(self):
        context = self._context
        main_bom_id = int(context.get('bom_id'))
        postfix = self.postfix if self.postfix else ''
        partner_id = self.partner_id
        update = context.get('update')
        vals = context.get('back_datas')
        line_obj = self.env['mrp.bom.line']
        bom_obj = self.env['mrp.bom']
        product_tmpl_obj = self.env['product.template']
        product_id_obj = self.env['product.product']
        products = {}

        if not update:
            for val in vals:
                temp_new_product_id = temp_old_product_id = False
                product_id = val.get('productid')
                parents = val.get('parents')
                modify_type = val.get('modify_type')
                input_changed_value = val.get('input_changed_value')
                name = val.get('name')
                product_specs = val.get('product_specs')
                last_bom_line_id = int(val.get('id'))
                qty = val.get('qty')
                to_update_bom_line_ids = parents
                old_line_id = False

                for line in to_update_bom_line_ids:
                    line = int(line)
                    if line != main_bom_id:
                        old_line_id = self.env['mrp.bom.line'].browse(line)
                        if not products.get(old_line_id.product_id):
                            old_product_tmpl_id = old_line_id.product_id
                            default_code = self.get_next_default_code(old_product_tmpl_id.default_code)
                            new_product_tmpl_id = old_line_id.product_id.product_tmpl_id.copy(
                                {'name': self.get_new_product_name(old_product_tmpl_id.name, postfix),
                                 'default_code': default_code})
                            new_bom_id = old_line_id.product_id.product_tmpl_id.bom_ids[0].copy(
                                {"product_tmpl_id": new_product_tmpl_id.id})
                            products.update({
                                old_line_id.product_id: {
                                    'new_product_tmpl_id': new_product_tmpl_id.id,
                                    'new_bom_id': new_bom_id.id
                                }
                            })
                        else:
                            new_product_tmpl_id = product_tmpl_obj.browse(
                                products.get(old_line_id.product_id).get('new_product_tmpl_id'))
                            new_bom_id = bom_obj.browse(products.get(old_line_id.product_id).get('new_bom_id'))
                    else:
                        bom_id = bom_obj.browse(line)
                        old_product_tmpl_id = bom_id.product_tmpl_id
                        if not products.get('bom'):
                            default_code = self.get_next_default_code(old_product_tmpl_id.default_code)
                            new_product_tmpl_id = old_product_tmpl_id.copy(
                                {'name': self.get_new_product_name(old_product_tmpl_id.name, postfix),
                                 'default_code': default_code})
                            new_bom_id = bom_id.copy({'product_tmpl_id': new_product_tmpl_id.id})
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

                    # 循环把copy的new bom 中的bom line 的 product_id 为就产品的bom line 替换掉
                    if temp_new_product_id:
                        tmp_id = product_tmpl_obj.browse(temp_new_product_id)
                        update_bom_line_copy(new_bom_id, tmp_id.product_variant_ids[0].id, temp_old_product_id)
                    if new_product_tmpl_id and old_line_id:
                        temp_new_product_id = new_product_tmpl_id.id
                        temp_old_product_id = old_line_id.product_id.id

                    if modify_type == 'add':
                        if input_changed_value:
                            product_tmpl_id = product_id_obj.browse(product_id).product_tmpl_id
                            new_name = self.get_new_product_name(input_changed_value, postfix)
                            default_code = self.get_next_default_code(product_tmpl_id.default_code)
                            new_pl_id = product_tmpl_id.copy({'name': new_name, 'default_code': default_code})
                            product_id = new_pl_id.product_variant_ids[0].id
                        if product_id:
                            line_obj.create({
                                'product_id': product_id,
                                'is_highlight': True,
                                'product_qty': qty,
                                'bom_id': new_bom_id.id,
                            })
                            product_id = False
                            input_changed_value = False
                            # 此为修改bom，需要删除一个bom_line
                    elif modify_type == 'edit':
                        old_product_id = line_obj.browse(last_bom_line_id).product_id
                        if input_changed_value:
                            product_tmpl_id = product_id_obj.browse(product_id).product_tmpl_id
                            new_name = self.get_new_product_name(name, postfix)
                            default_code = self.get_next_default_code(product_tmpl_id.default_code)
                            new_pl_id = product_tmpl_id.copy(
                                {'name': new_name, 'default_code': default_code, 'product_specs': product_specs})
                            # 如果修改一个半成品替换的话，需拷贝bom
                            if product_tmpl_id.bom_ids:
                                product_tmpl_id.bom_ids[0].copy({'product_tmpl_id': new_pl_id.id})
                            product_id = new_pl_id.product_variant_ids[0].id
                        if product_id:
                            line_obj.create({
                                'product_id': product_id,
                                'is_highlight': True,
                                'product_qty': qty,
                                'bom_id': new_bom_id.id,
                            })
                            product_id = False
                            input_changed_value = False
                            update_bom_line_delete(new_bom_id, old_product_id)
                        elif product_id and old_product_id.id == product_id:
                            update_bom_line_update(new_bom_id, old_product_id, qty)
                    elif modify_type == 'del':
                        old_product_id = line_obj.browse(int(last_bom_line_id)).product_id
                        update_bom_line_delete(new_bom_id, old_product_id)
            return {
                'type': 'ir.actions.client',
                'tag': 'new_bom_update',
                'target': 'current',
                'bom_id': new_bom_id.id
            }
        else:
            # 修改bOM
            for val in vals:
                product_id = val.get('productid')
                if product_id:
                    product_id = int(product_id)
                parents = val.get('parents')
                input_changed_value = val.get('input_changed_value')
                last_bom_line_id = val.get('id')
                qty = val.get('qty')
                modify_type = val.get('modify_type')

                to_update_bom_line_ids = parents.split(',')
                line = int(to_update_bom_line_ids[0])
                if line != main_bom_id:
                    line_id = self.env['mrp.bom.line'].browse(int(line))
                    bom_id = line_id.product_id.product_tmpl_id.bom_ids[0]
                else:
                    bom_id = bom_obj.browse(line)

                if modify_type == 'add':
                    if input_changed_value:
                        product_tmpl_id = product_id_obj.browse(int(product_id)).product_tmpl_id
                        new_name = self.get_new_product_name(input_changed_value, postfix)
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
                        product_id = False
                        # 此为修改bom，需要删除一个bom_line
                elif modify_type == 'edit':
                    product_tmpl_id = product_id_obj.browse(product_id).product_tmpl_id
                    if input_changed_value:

                        new_name = self.get_new_product_name(input_changed_value, postfix)
                        default_code = self.get_next_default_code(product_tmpl_id.default_code)
                        new_pl_id = product_tmpl_id.copy({'name': new_name, 'default_code': default_code})
                        if product_tmpl_id.bom_ids:
                            product_tmpl_id.bom_ids[0].copy({'product_tmpl_id': new_pl_id.id})
                        product_id = new_pl_id.product_variant_ids[0].id

                    last_bom_line_id = line_obj.browse(int(last_bom_line_id))
                    if product_id:
                        last_bom_line_id.write({
                            'product_id': int(product_id),
                            'product_qty': qty,
                            'is_highlight': True,
                        })

                # 直接删除line无需添加
                elif modify_type == 'del':
                    old_product_id = line_obj.browse(last_bom_line_id).product_id
                    update_bom_line_delete(bom_id, old_product_id)
            return {
                'type': 'ir.actions.client',
                'tag': 'bom_update',
                'bom_id': main_bom_id
            }

    @api.multi
    def create_cancel(self):
        main_bom_id = int(self._context.get('bom_id'))
        return {
            'type': 'ir.actions.client',
            'tag': 'bom_update',
            'bom_id': main_bom_id
        }

    def get_next_default_code(self, default_code):
        if not default_code:
            raise UserError(u'产品没有对应料号')
        codes = default_code.split('.')
        customer_code = codes[2]
        if self.partner_id:
            if not self.partner_id.customer_code:
                raise UserError(u'该客户未定义客户号码')
            customer_code = self.partner_id.customer_code

        spec = codes[0:2]
        spec.append(customer_code)
        prefix = '.'.join(spec)
        products = self.env['product.template'].search([('default_code', 'ilike', prefix)])
        if not products:
            return prefix + ".A"
        versions = []

        for product in products:
            if len(product.default_code.split('.')) > 3:
                versions.append(product.default_code.split('.')[-1])
        if not versions:
            return prefix + ".B"
        new_version = chr(ord(max(versions)) + 1)
        spec.append(new_version)
        new_code = '.'.join(spec)
        return new_code

    @staticmethod
    def get_new_product_name(old_name, postfix):
        new_name = ''
        old = re.findall(ur"\{(.*?)\}", old_name)

        if old and len(old) == 1:
            new_name = old_name.replace(old[0], postfix)
        elif len(old) > 1:
            UserError(u'产品名称不规范，找不到想要的版本')
        else:
            if postfix:
                new_name = old_name + '{' + postfix + '}'
            else:
                new_name = old_name
        return new_name


def update_bom_line_copy(new_bom_id, new_product_id, old_product_id):
    if new_product_id:
        for line in new_bom_id.bom_line_ids:
            if line.product_id.id == old_product_id:
                line.product_id = new_product_id
                line.is_highlight = True
                return True


def update_bom_line_delete(new_bom_id, old_product_id):
    for line in new_bom_id.bom_line_ids:
        if line.product_id.id == old_product_id.id:
            line.unlink()


def update_bom_line_update(new_bom_id, old_product_id, qty):
    for line in new_bom_id.bom_line_ids:
        if line.product_id.id == old_product_id.id:
            line.product_qty = qty


if __name__ == '__main__':
    aaa = '001'
    abcv = int(aaa, base=3) + 1
    ddd = '000' + str(abcv)
    ac = '010'
    ccc = ('000' + str(int(ac) + 1))[-3:]
    print ccc

    a = u"p<123adf>zzz"
    b = re.findall(ur"[^(<]+(?=[>）])", a)
    print b

    a = '1.2.3.4'

    b = a.split('.')
    c = b[0:2]
    c.append(3)

    D = ['A', 'B']
    print chr(ord('a') + 1)
