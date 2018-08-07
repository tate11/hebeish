from openerp import fields, models, api
import datetime
from datetime import datetime, timedelta

class CompetitorPriceSurvey(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('group_id')
    def get_sale_order_data(self):
        for rec in self:
            sale_order_id = self.env['sale.order'].search([('name', '=', rec.group_id.name)])
            if sale_order_id:
                rec.project_name = sale_order_id.project_name
                rec.customer_po = sale_order_id.x_customer_po

    project_name = fields.Char('Project Name', compute=get_sale_order_data)
    customer_po = fields.Char('Customer PO', compute=get_sale_order_data)

