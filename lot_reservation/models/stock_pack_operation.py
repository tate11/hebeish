from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare


class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def save(self):
        for pack in self:
            if pack.product_id.tracking != 'none':
                pack.write({'qty_done': sum(pack.pack_lot_ids.mapped('qty'))})
            lot_qty = {}
            Quant = self.env['stock.quant']
            active_id = self.env.context.get('active_id')
            operations = self.env['stock.pack.operation'].browse(active_id)
            for ops in operations:
                for moves in ops.linked_move_operation_ids:
                    if moves.move_id.state not in ('done', 'cancel'):
                        moves.move_id.do_unreserve()

                rounding = pack.product_id.uom_id.rounding
                for pack_lot in pack.pack_lot_ids:
                    lot_qty[pack_lot.lot_id.id] = ops.product_uom_id._compute_quantity(pack_lot.qty, pack.product_id.uom_id)
                for record in ops.linked_move_operation_ids:
                    move_qty = record.qty
                    move = record.move_id
                    # domain = main_domain[move.id]
                    domain = []
                    for lot in lot_qty:
                        if float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(move_qty, 0,precision_rounding=rounding) > 0:
                            qty = min(lot_qty[lot], move_qty)
                            quants = Quant.quants_get_preferred_domain(qty, move, ops=ops, lot_id=lot, domain=domain,preferred_domain_list=[])
                            Quant.quants_reserve(quants, move, record)
                            lot_qty[lot] -= qty
                            move_qty -= qty
        return {'type': 'ir.actions.act_window_close'}