from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_compare


class StockPackOperationLot(models.Model):
    _inherit = "stock.pack.operation.lot"

    @api.depends('lot_id')
    def get_lot_onhand_qty(self):
        for pack_lot in self:
            total_onhand_qty = 0
            active_id = self.env.context.get('active_pack_operation')
            operation = self.env['stock.pack.operation'].browse(active_id)
            if operation.picking_id.picking_type_id.default_location_src_id:
                product_quants_objects = self.env['stock.quant'].search(
                    [('product_id', '=', operation.product_id.id), ('lot_id', '=', pack_lot.lot_id.id), (
                        'location_id', '=', operation.picking_id.picking_type_id.default_location_src_id.id)])
                for product_quant in product_quants_objects:
                    total_onhand_qty += product_quant.qty
                pack_lot.onhand_qty = total_onhand_qty
            else:
                res = pack_lot.operation_id.product_id._compute_quantities_dict(pack_lot.lot_id.id,
                                                                                self._context.get('owner_id'),
                                                                                self._context.get('package_id'),
                                                                                self._context.get('from_date'),
                                                                                self._context.get('to_date'))
                pack_lot.onhand_qty = res[pack_lot.operation_id.product_id.id]['qty_available']

    onhand_qty = fields.Float(compute="get_lot_onhand_qty", string='QTY on Hand', readonly=True)

    @api.constrains('qty')
    def _check_qty_with_onhand(self):
        for lot in self:
            if lot.operation_id.picking_id.picking_type_id.code != 'incoming':
                if lot.qty > lot.onhand_qty:
                    raise ValidationError("You cannot proceed more than quantity on hand for lot: %s" % lot.lot_id.name)


class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    @api.constrains('pack_lot_ids')
    def check_done_qty(self):
        for record in self:
            if record.pack_lot_ids:
                total_done = sum(record.pack_lot_ids.mapped('qty'))
                if total_done > record.product_qty:
                    raise ValidationError(_('Total done qty in lines must equal ' + str(record.product_qty)))

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
                    lot_qty[pack_lot.lot_id.id] = ops.product_uom_id._compute_quantity(pack_lot.qty,
                                                                                       pack.product_id.uom_id)
                for record in ops.linked_move_operation_ids:
                    move_qty = record.qty
                    move = record.move_id
                    # domain = main_domain[move.id]
                    domain = []
                    for lot in lot_qty:
                        if float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(move_qty,
                                                                                                             0,
                                                                                                             precision_rounding=rounding) > 0:
                            qty = min(lot_qty[lot], move_qty)
                            quants = Quant.quants_get_preferred_domain(qty, move, ops=ops, lot_id=lot, domain=domain,
                                                                       preferred_domain_list=[])
                            Quant.quants_reserve(quants, move, record)
                            lot_qty[lot] -= qty
                            move_qty -= qty
        return {'type': 'ir.actions.act_window_close'}
