# -*- coding: utf-8 -*-



from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_cancel(self):
        """ Cancels the moves and if all moves are cancelled it cancels the picking. """
        # TDE DUMB: why is cancel_procuremetn in ctx we do quite nothing ?? like not updating the move ??

        for move in self:
            if move.state == 'done':
                _logger.warning("Could not find view object with view_id '%s'", move.id)
                print move.id, 'ddddddddddddddddddddddddddddddddddddddddddddd'
        if any(move.state == 'done' for move in self):
            _logger.warning("Cddddddddddddddddddddd '%s'", move.id)
            raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))

        procurements = self.env['procurement.order']
        for move in self:
            if move.reserved_quant_ids:
                move.quants_unreserve()
            if self.env.context.get('cancel_procurement'):
                if move.propagate:
                    pass
                    # procurements.search([('move_dest_id', '=', move.id)]).cancel()
            else:
                if move.move_dest_id:
                    if move.propagate and move.move_dest_id.state != 'done':
                        move.move_dest_id.action_cancel()
                    elif move.move_dest_id.state == 'waiting':
                        # If waiting, the chain will be broken and we are not sure if we can still wait for it (=> could take from stock instead)
                        move.move_dest_id.write({'state': 'confirmed'})
                if move.procurement_id:
                    procurements |= move.procurement_id

        self.write({'state': 'cancel', 'move_dest_id': False})
        if procurements:
            procurements.check()
        return True
