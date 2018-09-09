# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def _compute_default_routing(self):
        for production in self:
            print("hereeeeeeeeeeeeeeee")
            if production.bom_id.routing_id.operation_ids:
                production.routing_id = production.bom_id.routing_id.id
            else:
                production.routing_id = False

    bom_has_moves = fields.Boolean(compute='has_moves_on_bom')
    outing_id = fields.Many2one(
        'mrp.routing', string='Routing', default=_compute_default_routing,
        help="The list of operations (list of work centers) to produce the finished product. The routing "
             "is mainly used to compute work center costs during operations and to plan future loads on "
             "work centers based on production planning.")

    @api.onchange('bom_id')
    def change_route(self):
        for production in self:
            if production.bom_id.routing_id.operation_ids:
                production.routing_id = production.bom_id.routing_id.id
            else:
                production.routing_id = False

    @api.multi
    @api.depends('move_raw_ids')
    def has_moves_on_bom(self):
        for mo in self:
            mo.has_moves_on_bom = any(mo.move_raw_ids) and mo.state != 'confirmed'
