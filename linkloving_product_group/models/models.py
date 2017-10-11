# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    mo_ids = fields.One2many('mrp.production', 'product_tmpl_id',
                             domain=[('state', 'in', ['draft', 'confirmed', 'waiting_material'])])

    @api.depends('mo_ids')
    def _compute_mo_ids(self):
        for product in self:
            if product.mo_ids:
                product.has_mo = True

    has_mo = fields.Boolean(compute=_compute_mo_ids, store=True)


class ProductCategory(models.Model):
    _inherit = "product.category"

    menu_id = fields.Many2one("ir.ui.menu", )

    @api.multi
    def menu_create(self):
        for category in self:
            if not category.menu_id:
                action_id = self.create_action(category)
                category.menu_id = self.create_menu(category, action_id)
            else:
                category.menu_id.name = category.name

        for category in self:
            if not category.parent_id:
                category.menu_id.parent_id = self.env.ref('linkloving_product_group.group_by_product_category').id
            else:
                category.menu_id.parent_id = category.parent_id.menu_id.id
                # action_id = self.create_action(category)
                # if not category.parent_id:
                #     parent_id = self.env.ref('linkloving_product_group.group_by_product_category')
                # else:
                #     if category.parent_id.menu_id:
                #         parent_id = category.parent_id.menu_id
                #     else:
                #         parent_action_id = self.create_action(category)
                #         category.parent_id.menu_id = self.create_menu(category.parent_id.id, parent_action_id, )
                # category.menu_id = self.create_menu(category.id, action_id, parent_id)

    def create_menu(self, category, action_id):
        return self.env['ir.ui.menu'].create({
            'name': category.name,
            'action': 'ir.actions.act_window,%d' % (action_id.id)
        })

    def create_action(self, category):
        model = 'product.template'
        view_id = self.env.ref('product.product_template_tree_view').id
        val = {
            'name': category.name,
            'res_model': model,
            'view_type': 'form',
            'view_mode': 'tree,form,kanban',
            'domain': '[["categ_id", "child_of", %d]]' % int(category.id),
            'view_id': view_id,
        }
        return self.env['ir.actions.act_window'].create(val)

    @api.model
    def create(self, vals):
        res = super(ProductCategory, self).create(vals)
        action_id = self.create_action(res)
        res.menu_id = self.create_menu(res, action_id).id
        res.menu_id.parent_id = res.parent_id.menu_id.id
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductCategory, self).write(vals)
        if vals.get("parent_id"):
            self.menu_id.parent_id = self.parent_id.menu_id.id
        if vals.get("name"):
            self.menu_id.name = vals.get("name")
            self.menu_id.action.name = vals.get("name")
        return res

    @api.multi
    def unlink(self):
        for category in self:
            if category.menu_id:
                menu_to_unlink = self.env["ir.ui.menu"].search([('parent_id', '=', category.menu_id.id)])
                print(len(menu_to_unlink))
                menu_to_unlink.unlink()

            category.menu_id.unlink()

        return super(ProductCategory, self).unlink()
