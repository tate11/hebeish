from openerp import fields, models, api, exceptions, _
from odoo.exceptions import UserError
import math



class purchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    sale_production_id = fields.Many2one('sale.order', string="Source Document")


class purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    sale_production_id = fields.Many2one('sale.order', string="Source Document")

class production_sale_order(models.Model):
    _name = 'production.sale.order'

    sale_order_id = fields.Many2one('sale.order','Sale Order')
    production_id = fields.Many2one('mrp.production','MO')
    customer_id = fields.Many2one(related='sale_order_id.partner_id',string='Customer',readonly=True)
    project_name = fields.Char(related='sale_order_id.project_name',string='Project',readonly=True)
    customer_po = fields.Char(related='sale_order_id.x_customer_po',string='Customer PO',readonly=True)
    qty_to_produce = fields.Float('Quantity',readonly=True)
    status = fields.Selection(related='sale_order_id.state',string='Status',readonly=True)


class mrp_production_inherit(models.Model):
    _inherit = 'mrp.production'

    sale_production_id = fields.Many2one('sale.order', string="Source Document")
    sale_order_ids = fields.One2many('production.sale.order','production_id', string="Sales Orders")
    customer_reference = fields.Char('Customer',copy=False, readonly=True)

    @api.model
    def _update_product_to_produce(self, production, qty):
        production_move = production.move_finished_ids.filtered(lambda x:x.product_id.id == production.product_id.id and x.state not in ('done', 'cancel'))
        if production_move:
            production_move.write({'product_uom_qty': qty})
        else:
            production_move = production._generate_finished_moves()
            production_move = production.move_finished_ids.filtered(lambda x : x.state not in ('done', 'cancel') and production.product_id.id == x.product_id.id)
            production_move.write({'product_uom_qty': qty})


    @api.multi
    def change_product_qty(self, qty_to_update):
        for production in self:
            qty_to_update = qty_to_update + production.product_qty
            produced = sum(production.move_finished_ids.mapped('quantity_done'))
            if qty_to_update < produced:
                raise UserError(_("You have already processed %d. Please input a quantity higher than %d ") % (produced, produced))
            production.write({'product_qty': qty_to_update})
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')),
                                                                          production.product_uom_id)
            factor = production.product_uom_id._compute_quantity(production.product_qty - qty_produced,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            for line, line_data in lines:
                production._update_raw_move(line, line_data)
            operation_bom_qty = {}
            for bom, bom_data in boms:
                for operation in bom.routing_id.operation_ids:
                    operation_bom_qty[operation.id] = bom_data['qty']
            self._update_product_to_produce(production, production.product_qty - qty_produced)
            moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves.do_unreserve()
            moves.action_assign()
            for wo in production.workorder_ids:
                operation = wo.operation_id
                if operation_bom_qty.get(operation.id):
                    cycle_number = math.ceil(
                        operation_bom_qty[operation.id] / operation.workcenter_id.capacity)  # TODO: float_round UP
                    wo.duration_expected = (operation.workcenter_id.time_start +
                                            operation.workcenter_id.time_stop +
                                            cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
                if production.product_id.tracking == 'serial':
                    quantity = 1.0
                else:
                    quantity = wo.qty_production - wo.qty_produced
                    quantity = quantity if (quantity > 0) else 0
                wo.qty_producing = quantity
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                # assign moves; last operation receive all unassigned moves
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(
                    lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(lambda
                                                                           move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_lot_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
                if wo.move_raw_ids.filtered(
                        lambda x: x.product_id.tracking != 'none') and not wo.active_move_lot_ids:
                    wo._generate_lot_ids()
            return {}


class stock_location_route_inherit(models.Model):
    _inherit = 'stock.location.route'

    is_mts = fields.Boolean(default=False)
