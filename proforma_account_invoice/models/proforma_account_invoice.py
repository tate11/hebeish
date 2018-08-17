# -*- coding: utf-8 -*-
from odoo import api, models,fields,_
from odoo.exceptions import UserError,ValidationError


class ProformaAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    proforma_number = fields.Char()
    is_proforma = fields.Boolean(string='Proforma')

    @api.model
    def create(self, vals):
        if vals.get('is_proforma') == True and vals.get('type') == 'proforma':
            vals['proforma_number'] = self.env['ir.sequence'].next_by_code('proforma.seq.num') or '/'
            
        return super(ProformaAccountInvoice, self).create(vals)   

    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Refund'),
            'in_refund': _('Vendor Refund'),
            'proforma': _('Proforma'),
        }
        result = []
        for inv in self:
            result.append((inv.id, "%s %s" % (inv.number or TYPES[inv.type], inv.name or '')))
        return result

    type = fields.Selection(selection_add=[('proforma', 'Proforma')])


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    proforma_invoice_count = fields.Integer(string='# of Proforma Invoices', compute='_get_proforma_invoiced', readonly=True)

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids),('is_proforma','=',False),('type','!=','proforma')]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_view_proforma_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('proforma_account_invoice.proforma_invoice_view').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids),('is_proforma','=',True),('type','=','proforma')]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('proforma_account_invoice.proforma_invoice_form_view').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    # =============================================================
    # ==== override computed function to change invoice_count =====
    @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(
                lambda r: r.type in ['out_invoice', 'out_refund'])
            refunds = invoice_ids.search([('origin', 'like', order.name)])
            invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
            # Search for refunds as well
            refund_ids = self.env['account.invoice'].browse()
            if invoice_ids:
                for inv in invoice_ids:
                    refund_ids += refund_ids.search(
                        [('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False),
                         ('journal_id', '=', inv.journal_id.id)])

            line_invoice_status = [line.invoice_status for line in order.order_line]

            if order.state not in ('sale', 'done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'

            res_count = self.env['account.invoice'].search_count(
                [('id', 'in', invoice_ids.ids), ('is_proforma', '=', False),('type','!=','proforma')])
            order.update({
                'invoice_count': len(set(refund_ids.ids)) + res_count,
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.depends('state', 'order_line.invoice_status')
    def _get_proforma_invoiced(self):
        for rec in self:
            invoices = rec.mapped('invoice_ids')
            res_count = self.env['account.invoice'].search_count([('id','in',invoices.ids),('is_proforma','=',True),('type','=','proforma')])
            rec.proforma_invoice_count = res_count

    @api.multi
    def action_proforma(self):
        for rec in self:
            proforma_inv_data = self._prepare_invoice()
            proforma_inv_data.update({'is_proforma':True,'type':'proforma'})
            proforma_invoice = self.env['account.invoice'].create(proforma_inv_data)
            for line in rec.order_line :
                vals = line._prepare_invoice_line(line.product_uom_qty)
                vals.update({'invoice_id': proforma_invoice.id, 'sale_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)
            proforma_invoice.compute_taxes()
            proforma_invoice.action_date_assign()



