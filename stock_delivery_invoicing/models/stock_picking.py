# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_count = fields.Integer(string='Number of invoices', compute='_get_invoice_count', readonly=True)

    @api.multi
    def _get_invoice_count(self):
        for order in self:
            order.update({
                'invoice_count': len(self.env['account.invoice'].sudo().search([('picking_id', '=', order.id)])),
            })

    @api.multi
    def action_view_invoices(self):
        invoices = self.env['account.invoice'].sudo().search([('picking_id', '=', self.id)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_create_invoice(self):
        for picking in self:
            invoices_ids = picking.action_invoice_create()
            invoices = self.env['account.invoice'].browse(invoices_ids)
            # invoices.action_invoice_open()


    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        self.ensure_one()
        invoice_vals = self._prepare_invoice()
        invoice = self.env['account.invoice'].create(invoice_vals)
        for line in self.move_lines:
            invoice_line_vals = self._prepare_invoice_line(line, invoice.id)
            self.env['account.invoice.line'].create(invoice_line_vals)
        invoice.compute_taxes()
        return invoice


    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_("You must first select a Customer for Contract %s!") %self.name)
        journal = self.env['account.journal'].search([('type', '=', 'sale'),('company_id', '=', self.company_id.id)],limit=1)
        if not journal:
            raise ValidationError(_("Please define a sale journal for the company '%s'.") %(self.company_id.name or '',))
        currency = (
            self.partner_id.property_product_pricelist.currency_id or
            self.company_id.currency_id
        )
        invoice_vals = ({
            # 'reference': self.name,
            'type': 'out_invoice',
            'partner_id': self.partner_id.address_get(['invoice'])['invoice'],
            'currency_id': currency.id,
            'journal_id': journal.id,
            'date_invoice': self.min_date,
            'origin': self.name,
            'company_id': self.company_id.id,
            'picking_id': self.id,
            'user_id': self.partner_id.user_id.id,
        })
        return invoice_vals


    @api.model
    def _prepare_invoice_line(self, line, invoice_id):
        self.ensure_one()
        res = {}
        account = line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (line.product_id.name, line.product_id.id, line.product_id.categ_id.name))

        fpos = self.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        invoice_line_vals = ({
            'account_id': account.id,
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': line.product_uom_qty,
            # 'uom_id': line.product_uom_id.id,
            'name': line.name,
            # 'account_analytic_id': contract.id,
            'price_unit': line.product_id.list_price,
            # 'discount': line.discount,
        })
        return invoice_line_vals