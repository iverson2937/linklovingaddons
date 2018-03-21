# -*- coding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    version = fields.Integer(u'版本号', default=1)


class MrpEcoOrder(models.Model):
    _name = 'mrp.eco.order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = u"变更单"

    name = fields.Char(u'单号', copy=False, required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', u'负责人', default=lambda self: self.env.user)
    effectivity = fields.Selection([
        ('asap', u'立即'),
        ('date', u'根据时间')], string=u'何时生效?',  # Is this English ?
            default='asap', required=True)  # TDE: usefull ?

    effectivity_date = fields.Datetime(u'生效时间', track_visibility="onchange")
    eco_line_ids = fields.One2many(comodel_name="mrp.eco.line",
                                   inverse_name="eco_order_id",
                                   string=u"变更明细行", track_visibility="onchange"
                                   )

    state = fields.Selection([
        ('draft', u'草稿'),
        ('progress', u'等待至选定日生效'),
        ('done', u'完成')], string=u'状态',
            copy=False, default='draft', required=True, track_visibility="onchange")
    note = fields.Text(u'备注')

    bom_eco_ids = fields.One2many(comodel_name="mrp.bom.eco",
                                  inverse_name="eco_order_id",
                                  string=u"变更的BOM", )

    bom_eco_count = fields.Integer(string=u'变更的BOM单据数量', compute='_compute_bom_eco_count')

    @api.multi
    def _compute_bom_eco_count(self):
        for eco in self:
            eco.bom_eco_count = len(eco.bom_eco_ids)

    @api.multi
    def action_change_apply(self):
        self.ensure_one()
        # for eco in self:
        if self.effectivity == 'asap':
            new_bom_ecos = self.make_mrp_bom_ecos()
            new_bom_ecos.apply_to_bom()
            msg = "应用成功,已生成报告并通知到相关人员"
        elif self.effectivity == 'date':
            self.state == 'progress'
            msg = "设置成功, 将于指定日期生效"

        return {
            "type": "ir.actions.client",
            "tag": "action_notify",
            "params": {
                "title": u"设置成功",
                "text": msg,
                "sticky": False
            }
        }

    @api.model
    def create(self, vals):
        prefix = self.env['ir.sequence'].next_by_code('mrp.eco.order') or ''
        vals['name'] = '%s%s' % (prefix and '%s: ' % prefix or '', vals.get('name', ''))
        eco = super(MrpEcoOrder, self).create(vals)
        return eco

    def action_view_bom_eco(self):
        self.ensure_one()

        return {
            'name': u'变更的BOM',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom.eco',
            'view_mode': 'form',
            'view_type': 'form',
            # 'view_id': view.id,
            'views': [[False, 'tree'], [False, 'form']],
            'target': 'current',
            'domain': [('id', 'in', self.bom_eco_ids.ids)]
        }

    @api.multi
    def make_mrp_bom_ecos(self):
        mrp_bom_eco = self.env["mrp.bom.eco"]
        new_bom_ecos = self.env["mrp.bom.eco"]
        for eco in self:
            if eco.bom_eco_count > 0:
                raise UserError(u"已经生成BOM变更单,无法操作")

            same_bom_eco_line = {}
            for eco_line in eco.eco_line_ids:
                if same_bom_eco_line.get(eco_line.bom_id.id):
                    same_bom_eco_line[eco_line.bom_id.id] += eco_line
                else:
                    same_bom_eco_line[eco_line.bom_id.id] = eco_line
            for bom_id in same_bom_eco_line.keys():
                current_ver = same_bom_eco_line[bom_id][0].bom_id.version
                bom_eco_val = {
                    'eco_order_id': eco.id,
                    'user_id': eco.user_id.id,
                    'company_id': eco.company_id.id,
                    'effectivity': eco.effectivity,
                    'effectivity_date': eco.effectivity_date,
                    'old_version': current_ver,
                    'new_version': current_ver + 1,
                    'bom_id': bom_id,
                    'note': eco.note,
                    'bom_change_ids': [(6, 0, same_bom_eco_line[bom_id].ids)]
                }
                new_bom_ecos += mrp_bom_eco.create(bom_eco_val)
        return new_bom_ecos


class MrpEcoLine(models.Model):
    _name = 'mrp.eco.line'
    _description = u"变更明细行"
    # _inherit = ['mail.thread', 'ir.needaction_mixin']

    # name = fields.Char('Reference', copy=False, required=True)
    # user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    # company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    eco_order_id = fields.Many2one('mrp.eco.order', ondelete="restrict")
    effectivity = fields.Selection(related="eco_order_id.effectivity", string=u'何时生效?',  # Is this English ?
                                   default='asap')  # TDE: usefull ?
    effectivity_date = fields.Datetime(u'生效时间', related="eco_order_id.effectivity_date")

    # product_tmpl_id = fields.Many2one('product.template', "Product")
    bom_id = fields.Many2one(
            'mrp.bom', u"物料清单", ondelete="restrict", required=True)

    bom_line_id = fields.Many2one('mrp.bom.line',
                                  string=u'明细行',
                                  domain="[('bom_id', '=', bom_id)]")
    operate_type = fields.Selection(selection=[('add', u'新增'),
                                               ('remove', u'移除此项'),
                                               ('update', u'更新配比')],
                                    string=u'操作')
    new_product_qty = fields.Float(
            u'更新后的配比',
            digits=dp.get_precision('Product Unit of Measure'),
            default=1.0)
    new_product_id = fields.Many2one(
            'product.product', u'更新后的产品', )

    bom_eco_id = fields.Many2one(comodel_name="mrp.bom.eco", ondelete="restrict")


class MrpBomEco(models.Model):
    _name = 'mrp.bom.eco'
    _description = u'BOM 变更单'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    old_version = fields.Integer(string=u'变更前的版本号')
    new_version = fields.Integer(string=u'变更后的版本号')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', u'负责人', default=lambda self: self.env.user)
    # name = fields.Char('Reference', copy=False, required=True)
    # user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    # company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    eco_order_id = fields.Many2one('mrp.eco.order', ondelete="restrict", track_visibility="onchange")
    effectivity = fields.Selection([
        ('asap', u'立即'),
        ('date', u'根据时间')], string=u'何时生效?',  # Is this English ?
            default='asap', required=True, track_visibility="onchange")  # TDE: usefull ?
    effectivity_date = fields.Datetime(u'生效时间')
    bom_id = fields.Many2one(
            'mrp.bom', u"物料清单", ondelete="restrict", required=True)

    bom_change_ids = fields.One2many(comodel_name='mrp.eco.line', inverse_name='bom_eco_id', string=u'BOM变更明细')
    note = fields.Text(u'备注')

    @api.onchange("bom_id")
    def _onchange_bom_id(self):
        self.old_version = self.bom_id.version,
        self.new_version = self.bom_id.version + 1,

    @api.multi
    def _check_bom_line(self):
        """
        检查是否有在同一个bom里同时操作一个bomline的
        :return:
        """
        for bom_eco in self:
            bom_ids = bom_eco.bom_change_ids.mapped('bom_id')
            if len(bom_ids) != len(bom_eco.bom_change_ids):
                return False
        return True

    @api.multi
    def apply_to_bom(self):
        if not self._check_bom_line():
            raise UserError(u'不能在一张变更单中,同时变更一个物料')
        bom_line_obj = self.env['mrp.bom.line']
        for bom_eco in self:
            bom_to_apply = bom_eco.bom_id
            for bom_change in bom_eco.bom_change_ids:
                if bom_change.operate_type == 'add':
                    bom_line_obj.create({
                        'bom_id': bom_to_apply.id,
                        'product_id': bom_change.new_product_id.id,
                        'product_qty': bom_change.new_product_qty,
                    })
                elif bom_change.operate_type == 'update':
                    bom_change.bom_line_id.product_qty = bom_change.new_product_qty
                elif bom_change.operate_type == 'remove':
                    bom_change.bom_line_id.unlink()
