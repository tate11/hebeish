# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def _compute_default_routing(self):
        for production in self:
            if production.bom_id.routing_id.operation_ids:
                production.routing_id = production.bom_id.routing_id.id
            else:
                production.routing_id = False

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
    def write(self, vals):
        res = super(MrpProduction, self).write(vals)
        if 'bom_id' in vals.keys():
            self.move_raw_ids.action_cancel()
            self.move_raw_ids.unlink()
            self._generate_moves()
        return res

    def _workorders_create(self, bom, bom_data):
        res = super(MrpProduction, self)._workorders_create(bom, bom_data)
        if self.routing_id.operation_ids:
            res.update({'workcenter_id': self.routing_id.operation_ids[0].workcenter_id.id})
        return res
