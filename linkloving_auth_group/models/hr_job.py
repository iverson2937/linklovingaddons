# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from collections import defaultdict, MutableMapping, OrderedDict

#
# Functions for manipulating boolean and selection pseudo-fields
#
from odoo.addons.base.res.res_users import parse_m2m
from odoo.tools import partition


class HrJob(models.Model):
    _inherit = 'hr.job'

    groups_id = fields.Many2many('res.groups')

    def get_application_groups(self, domain):
        """ Return the non-share groups that satisfy ``domain``. """
        return self.search(domain + [('share', '=', False)])

    @api.model
    def get_groups_by_application(self):
        """ Return all groups classified by application (module category), as a list::

                [(app, kind, groups), ...],

            where ``app`` and ``groups`` are recordsets, and ``kind`` is either
            ``'boolean'`` or ``'selection'``. Applications are given in sequence
            order.  If ``kind`` is ``'selection'``, ``groups`` are given in
            reverse implication order.
        """

        def linearize(app, gs):
            # determine sequence order: a group appears after its implied groups
            order = {g: len(g.trans_implied_ids & gs) for g in gs}
            # check whether order is total, i.e., sequence orders are distinct
            print order
            print len(set(order.itervalues()))
            print gs
            print len(set(order.itervalues()))
            if len(set(order.itervalues())) == len(gs):
                return (app, 'selection', gs.sorted(key=order.get))
            else:
                return (app, 'boolean', gs)

        # classify all groups by application
        by_app, others = defaultdict(self.browse), self.browse()
        for g in self.get_application_groups([]):
            print '------------------------------------------------------'
            print g.name
            print g.category_id
            if g.category_id:
                by_app[g.category_id] += g
            else:
                others += g
        # build the result
        res = []
        for app, gs in sorted(by_app.iteritems(), key=lambda (a, _): a.sequence or 0):
            res.append(linearize(app, gs))
        if others:
            res.append((self.env['ir.module.category'], 'boolean', others))
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(HrJob, self).fields_get(allfields, attributes=attributes)
        print res
        # add reified groups fields
        print self.env['res.groups'].sudo().get_groups_by_application()
        print '______________________________________'
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

    @api.model
    def default_get(self, fields):
        group_fields, fields = partition(is_reified_group, fields)
        fields1 = (fields + ['groups_id']) if group_fields else fields
        values = super(HrJob, self).default_get(fields1)
        self._add_reified_groups(group_fields, values)
        print values, 'ddddddddddddddd'
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
