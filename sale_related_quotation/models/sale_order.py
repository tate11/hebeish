import datetime
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_related_quotations(self):
        for order in self:
            quotation_ids = []
            quotation_ids += [quotation.id for quotation in self.env['sale.order'].sudo().search([('related_order_id','=',order.id)])]
            order.related_quotation_ids = quotation_ids

    related_order_id = fields.Many2one('sale.order','Related Order', ondelete="set null")
    related_quotation_ids = fields.One2many('sale.order',compute='_get_related_quotations',string='Related Quotations')
    quotation_count = fields.Integer(string='Related Orders', compute='_compute_quotation_ids')

    def _compute_quotation_ids(self):
        for order in self:
            order.update({
                'quotation_count': len(order.related_quotation_ids),
            })


    @api.multi
    def action_view_related_orders(self):
        self.ensure_one()
        action = self.env.ref('sale.action_quotations')
        list_view_id = self.env.ref('sale.view_quotation_tree').id
        form_view_id = self.env.ref('sale.view_order_form').id
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
        }
        if len(self.related_quotation_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % self.related_quotation_ids.ids
        elif len(self.related_quotation_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = self.related_quotation_ids.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

