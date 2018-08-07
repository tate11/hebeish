from odoo import api, fields, models, _

class MrpRouting(models.Model):
    _inherit="mrp.routing"

    source_location_id = fields.Many2one(comodel_name='stock.location', string='Source Location')
    destination_location_id = fields.Many2one(comodel_name='stock.location', string='Destination Location')

class MrpProduction(models.Model):
    _inherit="mrp.production"

    location_src_id = fields.Many2one(
        'stock.location', 'Raw Materials Location',
        compute="_get_default_location_src_id",
        readonly=True, required=True,store=True,
        states={'confirmed': [('readonly', False)]},
        help="Location where the system will look for components.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Finished Products Location',
        compute="_get_default_location_dest_id",
        readonly=True, required=True,store=True,
        states={'confirmed': [('readonly', False)]},
        help="Location where the system will stock the finished products.")

    @api.model
    @api.depends('routing_id')
    def _get_default_location_src_id(self):
        for mo in self:
            mo.location_src_id = mo.routing_id.source_location_id
        # print self._context
        # location = False
        # if self._context.get('routing_id'):
        #     location = self.env['mrp.routing'].browse(
        #         self.env.context['routing_id']).source_location_id
        # else:
        #     if self._context.get('default_picking_type_id'):
        #         location = self.env['stock.picking.type'].browse(
        #             self.env.context['default_picking_type_id']).default_location_src_id
        #     if not location:
        #         location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        # raise Warning(self._context)
        # return location and location.id or False

    @api.model
    @api.depends('routing_id')
    def _get_default_location_dest_id(self):
        for mo in self:
            mo.location_dest_id = mo.routing_id.destination_location_id
        # print self._context
        # location = False
        # if self._context.get('routing_id'):
        #     location = self.env['mrp.routing'].browse(
        #         self.env.context['routing_id']).destination_location_id
        # else:
        #     if self._context.get('default_picking_type_id'):
        #         location = self.env['stock.picking.type'].browse(
        #             self.env.context['default_picking_type_id']).default_location_dest_id
        #     if not location:
        #         location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        # raise Warning(self._context)
        # return location and location.id or False
