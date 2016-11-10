# -*- coding: utf-8 -*-
##############################################################################
#
#    Auto reset sequence by year,month,day
#    Copyright 2013 wangbuke <wangbuke@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta
import pytz

from odoo import api, fields, models, _
from odoo.addons.base.ir.ir_sequence import _alter_sequence, _select_nextval
from odoo.exceptions import UserError
from odoo.osv import osv


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    auto_reset = fields.Boolean('Auto Reset', default=False)
    reset_period = fields.Selection(
        [('year', 'Every Year'), ('month', 'Every Month'), ('woy', 'Every Week'), ('day', 'Every Day'),
         ('h24', 'Every Hour'), ('min', 'Every Minute'), ('sec', 'Every Second')],
        'Reset Period', required=True, default='month')
    reset_time = fields.Char('Name', size=64, help="")
    reset_init_number = fields.Integer('Reset Number', required=True, help="Reset number of this sequence", default=1)


    # def _next(self):
    #     """ Returns the next number in the preferred sequence in all the ones given in self."""
    #     if not self.use_date_range:
    #         return self._next_do()
    #     # date mode
    #     dt = fields.Date.today()
    #     if self._context.get('ir_sequence_date'):
    #         dt = self._context.get('ir_sequence_date')
    #     seq_date = self.env['ir.sequence.date_range'].search([('sequence_id', '=', self.id), ('date_from', '<=', dt), ('date_to', '>=', dt)], limit=1)
    #     if not seq_date:
    #         seq_date = self._create_date_range_seq(dt)
    #     return seq_date.with_context(ir_sequence_date_range=seq_date.date_from)._next()

    def _next(self):

        force_company = self._context.get('force_company')
        if not force_company:
            force_company = self.env['res.users'].browse().company_id.id
        sequences = self.read(
                              ['name', 'company_id', 'implementation', 'number_next', 'prefix', 'suffix', 'padding',
                               'number_increment', 'auto_reset', 'reset_period', 'reset_time', 'reset_init_number'])
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        if seq['implementation'] == 'standard':
            current_time = ':'.join([seq['reset_period'], self._interpolation_dict().get(seq['reset_period'])])
            if seq['auto_reset'] and current_time != seq['reset_time']:
                self._cr.execute("UPDATE ir_sequence SET reset_time=%s WHERE id=%s ", (current_time, seq['id']))
                _alter_sequence(self._cr, 'ir_sequence_%03d' % self.id, seq['number_increment'], seq['reset_init_number'])
                self._cr.commit()
            number_next = _select_nextval(self._cr, 'ir_sequence_%03d' % self.id)
            # self._cr.execute("SELECT nextval('%s')" % seq['name'])
            seq['number_next'] = number_next
        else:
            self._cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            self._cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
        d = self._interpolation_dict()
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix

    def _interpolate(self, s, d):
        return (s % d) if s else ''

    def _interpolation_dict(self):
        now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
        if self._context.get('ir_sequence_date'):
            effective_date = datetime.strptime(self._context.get('ir_sequence_date'), '%Y-%m-%d')
        if self._context.get('ir_sequence_date_range'):
            range_date = datetime.strptime(self._context.get('ir_sequence_date_range'), '%Y-%m-%d')

        sequences = {
            'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
            'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
        }
        res = {}
        for key, format in sequences.iteritems():
            res[key] = effective_date.strftime(format)
            res['range_' + key] = range_date.strftime(format)
            res['current_' + key] = now.strftime(format)

        return res

    # def _alter_sequence(cr, seq_name, number_increment=None, number_next=None):
    #     """ Alter a PostreSQL sequence. """
    #     if number_increment == 0:
    #         raise UserError(_("Step must not be zero."))
    #     cr.execute("SELECT relname FROM pg_class WHERE relkind=%s AND relname=%s", ('S', seq_name))
    #     if not cr.fetchone():
    #         # sequence is not created yet, we're inside create() so ignore it, will be set later
    #         return
    #     statement = "ALTER SEQUENCE %s" % (seq_name,)
    #     if number_increment is not None:
    #         statement += " INCREMENT BY %d" % (number_increment,)
    #     if number_next is not None:
    #         statement += " RESTART WITH %d" % (number_next,)
    #     cr.execute(statement)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
