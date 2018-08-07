from openerp import fields, models, api, exceptions


class purchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    mrp_production_id = fields.Many2one('mrp.production', string="Source Document")
