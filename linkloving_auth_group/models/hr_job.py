# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from itertools import chain, repeat
from collections import defaultdict, MutableMapping, OrderedDict

#
# Functions for manipulating boolean and selection pseudo-fields
#
from odoo.addons.base.res.res_users import parse_m2m
from odoo.tools import partition


def name_boolean_group(id):
    return 'in_group_' + str(id)


def name_selection_groups(ids):
    return 'sel_groups_' + '_'.join(map(str, ids))


def is_boolean_group(name):
    return name.startswith('in_group_')


def is_selection_groups(name):
    return name.startswith('sel_groups_')


def is_reified_group(name):
    return is_boolean_group(name) or is_selection_groups(name)


def get_boolean_group(name):
    return int(name[9:])


def get_selection_groups(name):
    return map(int, name[11:].split('_'))


class HrJob(models.Model):
    _inherit = 'hr.job'

    groups_id = fields.Many2many('res.groups')

    @api.model
    def create(self, values):
        values = self._remove_reified_groups(values)
        user = super(HrJob, self).create(values)
        group_multi_company = self.env.ref('base.group_multi_company', False)
        if group_multi_company and 'company_ids' in values:
            if len(user.company_ids) <= 1 and user.id in group_multi_company.users.ids:
                group_multi_company.write({'users': [(3, user.id)]})
            elif len(user.company_ids) > 1 and user.id not in group_multi_company.users.ids:
                group_multi_company.write({'users': [(4, user.id)]})
        return user

    @api.multi
    def write(self, values):
        values = self._remove_reified_groups(values)
        res = super(HrJob, self).write(values)
        group_multi_company = self.env.ref('base.group_multi_company', False)
        if group_multi_company and 'company_ids' in values:
            for user in self:
                if len(user.company_ids) <= 1 and user.id in group_multi_company.users.ids:
                    group_multi_company.write({'users': [(3, user.id)]})
                elif len(user.company_ids) > 1 and user.id not in group_multi_company.users.ids:
                    group_multi_company.write({'users': [(4, user.id)]})
        return res

    def _remove_reified_groups(self, values):
        """ return `values` without reified group fields """
        add, rem = [], []
        values1 = {}

        for key, val in values.iteritems():
            if is_boolean_group(key):
                (add if val else rem).append(get_boolean_group(key))
            elif is_selection_groups(key):
                rem += get_selection_groups(key)
                if val:
                    add.append(val)
            else:
                values1[key] = val

        if 'groups_id' not in values and (add or rem):
            # remove group ids in `rem` and add group ids in `add`
            values1['groups_id'] = zip(repeat(3), rem) + zip(repeat(4), add)

        return values1

    @api.model
    def default_get(self, fields):
        group_fields, fields = partition(is_reified_group, fields)
        fields1 = (fields + ['groups_id']) if group_fields else fields
        values = super(HrJob, self).default_get(fields1)
        self._add_reified_groups(group_fields, values)
        return values

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        # determine whether reified groups fields are required, and which ones
        fields1 = fields or self.fields_get().keys()
        group_fields, other_fields = partition(is_reified_group, fields1)

        # read regular fields (other_fields); add 'groups_id' if necessary
        drop_groups_id = False
        if group_fields and fields:
            if 'groups_id' not in other_fields:
                other_fields.append('groups_id')
                drop_groups_id = True
        else:
            other_fields = fields

        res = super(HrJob, self).read(other_fields, load=load)

        # post-process result to add reified group fields
        if group_fields:
            for values in res:
                self._add_reified_groups(group_fields, values)
                if drop_groups_id:
                    values.pop('groups_id', None)
        return res

    def _add_reified_groups(self, fields, values):
        """ add the given reified group fields into `values` """
        gids = set(parse_m2m(values.get('groups_id') or []))
        for f in fields:
            if is_boolean_group(f):
                values[f] = get_boolean_group(f) in gids
            elif is_selection_groups(f):
                selected = [gid for gid in get_selection_groups(f) if gid in gids]
                values[f] = selected and selected[-1] or False

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(HrJob, self).fields_get(allfields, attributes=attributes)
        # add reified groups fields
        for app, kind, gs in self.env['res.groups'].sudo().get_groups_by_application():
            if kind == 'selection':
                # selection group field
                tips = ['%s: %s' % (g.name, g.comment) for g in gs if g.comment]
                res[name_selection_groups(gs.ids)] = {
                    'type': 'selection',
                    'string': app.name or _('Other'),
                    'selection': [(False, '')] + [(g.id, g.name) for g in gs],
                    'help': '\n'.join(tips),
                    'exportable': False,
                    'selectable': False,
                }
            else:
                # boolean group fields
                for g in gs:
                    res[name_boolean_group(g.id)] = {
                        'type': 'boolean',
                        'string': g.name,
                        'help': g.comment,
                        'exportable': False,
                        'selectable': False,
                    }
        return res
