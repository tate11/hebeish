# coding=utf-8

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    customer_ref = fields.Char('Customer References',readonly=True,copy=False)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def record_production(self):
        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_('Please set the quantity you produced in the Current Qty field. It can not be 0!'))

        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id:
            raise UserError(_('You should provide a lot for the final product'))

        # Update quantities done on each raw material line
        raw_moves = self.move_raw_ids.filtered(lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.bom_line_id)
        for move in raw_moves:
            if move.unit_factor:
                move.quantity_done += self.qty_producing * move.unit_factor

        # Transfer quantities from temporary to final move lots or make them final
        for move_lot in self.active_move_lot_ids:
            # Check if move_lot already exists
            if move_lot.quantity_done <= 0:  # rounding...
                move_lot.unlink()
                continue
            if not move_lot.lot_id:
                raise UserError(_('You should provide a lot for a component'))
            # Search other move_lot where it could be added:
            lots = self.move_lot_ids.filtered(lambda x: (x.lot_id.id == move_lot.lot_id.id) and (not x.lot_produced_id) and (not x.done_move))
            if lots:
                lots[0].quantity_done += move_lot.quantity_done
                lots[0].lot_produced_id = self.final_lot_id.id
                move_lot.unlink()
            else:
                move_lot.lot_produced_id = self.final_lot_id.id
                move_lot.done_wo = True

        # One a piece is produced, you can launch the next work order
        if self.next_work_order_id.state == 'pending':
            self.next_work_order_id.state = 'ready'
        if self.next_work_order_id and self.final_lot_id and not self.next_work_order_id.final_lot_id:
            self.next_work_order_id.final_lot_id = self.final_lot_id.id

        self.move_lot_ids.filtered(
            lambda move_lot: not move_lot.done_move and not move_lot.lot_produced_id and move_lot.quantity_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not self.next_work_order_id:
            production_move = self.production_id.move_finished_ids.filtered(lambda x: (x.product_id.id == self.production_id.product_id.id) and (x.state not in ('done', 'cancel')))
            for prod_move in production_move:
                if prod_move.product_id.tracking != 'none':
                    move_lot = prod_move.move_lot_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                    if move_lot:
                        move_lot.quantity += self.qty_producing
                    else:
                        move_lot.create({'move_id': prod_move.id,
                                         'lot_id': self.final_lot_id.id,
                                         'quantity': self.qty_producing,
                                         'quantity_done': self.qty_producing,
                                         'workorder_id': self.id,
                                         })
                else:
                    prod_move.quantity_done += self.qty_producing  # TODO: UoM conversion?
        # Update workorder quantity produced
        self.qty_produced += self.qty_producing

        # Set a qty producing
        if self.qty_produced >= self.production_id.product_qty:
            self.qty_producing = 0
        elif self.production_id.product_id.tracking == 'serial':
            self.qty_producing = 1.0
            self._generate_lot_ids()
        else:
            self.qty_producing = self.production_id.product_qty - self.qty_produced
            self._generate_lot_ids()

        self.final_lot_id = False
        if self.qty_produced >= self.production_id.product_qty:
            self.button_finish()

class StockMove(models.Model):
    _inherit = 'stock.move'

    original_production_id = fields.Many2one('mrp.production','Source', readonly=True)
    customer_id = fields.Many2one(related='original_production_id.x_customer_id',string='Customer',readonly=True)
    sale_id = fields.Many2one(related='original_production_id.sale_production_id',string='Sales Order',readonly=True)
    project_name = fields.Char(related='original_production_id.sale_production_id.project_name',string='Project Name',readonly=True)
    customer_po = fields.Char(related='original_production_id.sale_production_id.x_customer_po',string='Customer PO',readonly=True)


class MrpOrderMerge(models.TransientModel):
    _name = 'mrp.order.merge'
    _description = "MRP Production Order Merge"

    production_ids = fields.Many2many('mrp.production', string='Production Order')

    @api.model
    def default_get(self, fields):
        defaults = super(MrpOrderMerge, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)

        domain = [('id', 'in', active_ids), ('state', 'in', ['confirmed'])]
        res = self.env['mrp.production'].search(domain)
        defaults['production_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.multi
    def do_merge(self):
        if not self.production_ids:
            return
        main_production = self.production_ids[0]
        # prima comanda din lista devine comanda principala

        # product_qty = main_production.product_qty
        # for production in self.production_ids:
        #    if production != main_production:
        #        product_qty += production.product_qty
        # main_production.write({'product_qty': product_qty,
        #                       'bom_id': False,
        #                       'product_id': False})
        # main_production.move_finished_ids.write({'product_uom_qty': product_qty})
        # produsul din antet trebui inlocuit cu unul dummy
        # comanda nu mai trebuie sa aiba lista de materiale


        raw_picking = main_production.move_raw_ids[0].picking_id
        finished_picking = main_production.move_finished_ids[0].picking_id
        raw_value = {'raw_material_production_id': main_production.id}
        if raw_picking:
            raw_value['picking_id'] = raw_picking.id
        finished_value = {'production_id': main_production.id}
        if finished_picking:
            finished_value['picking_id'] = finished_picking.id

        updated_qty = main_production.product_qty
        updated_origin = main_production.origin
        updated_customer_ref = main_production.x_customer_id.name
        for production in self.production_ids:
            if production != main_production:
                updated_qty += production.product_qty
                updated_origin += ', ' + str(production.origin)
                if production.x_customer_id.name:
                    updated_customer_ref += ', ' + production.x_customer_id.name
                production.move_raw_ids.write(raw_value)
                finished_value['original_production_id'] = production.id
                # trebuie sa anulez miscarea pentru receptia produsului finit ?
                production.move_finished_ids.write(finished_value)
                production.workorder_ids.write({'production_id': main_production.id})
                production.procurement_ids.write({'production_id': main_production.id})
                production.write({'state': 'cancel'})
                # production.unlink()

        if raw_picking:
            raw_picking.recheck_availability()

        #if finished_picking:
        #    finished_picking.do_propare_partial()

        main_production.write({
                               'product_qty': updated_qty,
                               'origin': updated_origin,
                               'customer_ref': updated_customer_ref,
                               'check_to_done': False})  # comanda este in progres

        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = "[('id','in', " + str(self.production_ids.ids) + ")]"
        return action
