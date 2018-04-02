# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def write(self, vals):
        for line in self:
            if line.period_id.state == 'done' and 'full_reconcile_id' not in vals:
                raise UserError('不可以修改一个结账的分录')
        return super(AccountMoveLine, self).write(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.period_id.state == 'done':
                raise UserError('不可以删除一个结账的分录')
        return super(AccountMoveLine, self).unlink()

    def _query_get_period(self, context=None):
        fiscalyear_obj = self.env['account.fiscalyear']
        fiscalperiod_obj = self.env['account.period']
        account_obj = self.env['account.account']
        fiscalyear_ids = []
        context = dict(context or {})
        initial_bal = context.get('initial_bal', False)
        company_clause = " "
        query = ''
        query_params = {}
        # if context.get('company_id'):
        #     company_clause = " AND " +obj+".company_id = %(company_id)s"
        #     query_params['company_id'] = context['company_id']
        if not context.get('fiscalyear'):
            if context.get('all_fiscalyear'):
                # this option is needed by the aged balance report because otherwise, if we search only the draft ones, an open invoice of a closed fiscalyear won't be displayed
                fiscalyear_ids = fiscalyear_obj.search([])
            else:
                fiscalyear_ids = fiscalyear_obj.search([('state', '=', 'draft')])
        else:
            # for initial balance as well as for normal query, we check only the selected FY because the best practice is to generate the FY opening entries
            fiscalyear_ids = context['fiscalyear']
            if isinstance(context['fiscalyear'], (int, long)):
                fiscalyear_ids = [fiscalyear_ids]

        query_params['fiscalyear_ids'] = tuple(fiscalyear_ids) or (0,)
        state = context.get('state', False)
        where_move_state = ''
        where_move_lines_by_date = ''
        obj = ''

        if context.get('date_from') and context.get('date_to'):
            query_params['date_from'] = context['date_from']
            query_params['date_to'] = context['date_to']
            if initial_bal:
                where_move_lines_by_date = " AND " + obj + ".move_id IN (SELECT id FROM account_move WHERE date < %(date_from)s)"
            else:
                where_move_lines_by_date = " AND " + obj + ".move_id IN (SELECT id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s)"

        if state:
            if state.lower() not in ['all']:
                query_params['state'] = state
                where_move_state = " AND " + obj + ".move_id IN (SELECT id FROM account_move WHERE account_move.state = %(state)s)"
        if context.get('period_from') and context.get('period_to') and not context.get('periods'):
            if initial_bal:
                period_company_id = fiscalperiod_obj.browse(context['period_from'], context=context).company_id.id
                first_period = \
                fiscalperiod_obj.search([('company_id', '=', period_company_id)], order='date_start', limit=1)[0]
                context['periods'] = fiscalperiod_obj.build_ctx_periods(first_period, context['period_from'])
            else:
                context['periods'] = fiscalperiod_obj.build_ctx_periods(context['period_from'], context['period_to'])
        if 'periods_special' in context:
            periods_special = ' AND special = %s ' % bool(context.get('periods_special'))
        else:
            periods_special = ''
        if context.get('periods'):
            query_params['period_ids'] = tuple(context['periods'])
            if initial_bal:
                query = obj + ".state <> 'draft' AND " + obj + ".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s" + periods_special + ")" + where_move_state + where_move_lines_by_date
                period_ids = fiscalperiod_obj.search([('id', 'in', context['periods'])], order='date_start', limit=1)
                if period_ids and period_ids[0]:
                    first_period = fiscalperiod_obj.browse(period_ids[0], context=context)
                    query_params['date_start'] = first_period.date_start
                    query = obj + ".state <> 'draft' AND " + obj + ".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s AND date_start <= %(date_start)s AND id NOT IN %(period_ids)s" + periods_special + ")" + where_move_state + where_move_lines_by_date
            else:
                query = obj + ".state <> 'draft' AND " + obj + ".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s AND id IN %(period_ids)s" + periods_special + ")" + where_move_state + where_move_lines_by_date
        else:
            query = obj + ".state <> 'draft' AND " + obj + ".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s" + periods_special + ")" + where_move_state + where_move_lines_by_date

        if context.get('chart_account_id'):
            child_ids = account_obj._get_children_and_consol([context['chart_account_id']], context=context)
            query_params['child_ids'] = tuple(child_ids)
            query += ' AND ' + obj + '.account_id IN %(child_ids)s'

        query += company_clause
        return self._cr.mogrify(query, query_params)

    def _get_period(self):
        """
        Return  default account period value
        """
        account_period_obj = self.env['account.period']
        ids = account_period_obj.search([('state', '!=', 'done')])
        period_id = False
        if ids:
            period_id = ids[0]
        return period_id

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                related='move_id.period_id',
                                domain=[('state', '!=', 'done')], copy=False,
                                store=True,
                                required=True,
                                default=_get_period,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                readonly=False)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.multi
    def button_cancel(self):
        for move in self:
            if move.period_id.state=='done':
                raise UserError('不可以取消一个完成会计区间的分录')
        return super(AccountMove, self).button_cancel()

    def _get_period(self):
        """
        Return  default account period value
        """
        account_period_obj = self.env['account.period']
        ids = account_period_obj.search([('state', '!=', 'done')])
        period_id = False
        if ids:
            period_id = ids[0]
        return period_id

    period_id = fields.Many2one('account.period', string=u'会计区间',
                                domain=[('state', '!=', 'done')], copy=False,
                                required=True,
                                help="Keep empty to use the period of the validation(invoice) date.",
                                default=_get_period
                                )
