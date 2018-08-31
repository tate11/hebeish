# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from datetime import datetime, timedelta


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.multi
    def get_journal_dashboard_datas(self):
        currency = self.currency_id or self.company_id.currency_id
        number_to_reconcile = last_balance = account_sum = 0
        ac_bnk_stmt = []
        title = ''
        number_draft = number_waiting = number_late = 0
        sum_draft = sum_waiting = sum_late = 0.0
        if self.type in ['bank', 'cash']:
            last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids)],
                                                                       order="date desc, id desc", limit=1)
            last_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0
            # Get the number of items to reconcile for that bank journal
            self.env.cr.execute("""SELECT COUNT(DISTINCT(statement_line_id)) 
                            FROM account_move where statement_line_id 
                            IN (SELECT line.id 
                                FROM account_bank_statement_line AS line 
                                LEFT JOIN account_bank_statement AS st 
                                ON line.statement_id = st.id 
                                WHERE st.journal_id IN %s and st.state = 'open')""", (tuple(self.ids),))
            already_reconciled = self.env.cr.fetchone()[0]
            self.env.cr.execute("""SELECT COUNT(line.id) 
                                FROM account_bank_statement_line AS line 
                                LEFT JOIN account_bank_statement AS st 
                                ON line.statement_id = st.id 
                                WHERE st.journal_id IN %s and st.state = 'open'""", (tuple(self.ids),))
            all_lines = self.env.cr.fetchone()[0]
            number_to_reconcile = all_lines - already_reconciled
            # optimization to read sum of balance from account_move_line
            account_ids = tuple(filter(None, [self.default_debit_account_id.id, self.default_credit_account_id.id]))
            if account_ids:
                amount_field = 'balance' if (
                        not self.currency_id or self.currency_id == self.company_id.currency_id) else 'amount_currency'
                query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s AND date <= %%s;""" % (
                    amount_field,)
                self.env.cr.execute(query, (account_ids, fields.Date.today(),))
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('sum') != None:
                    account_sum = query_results[0].get('sum')
        # TODO need to check if all invoices are in the same currency than the journal!!!!
        elif self.type in ['sale', 'purchase']:
            title = _('Bills to pay') if self.type == 'purchase' else _('Invoices owed to you')
            # optimization to find total and sum of invoice that are in draft, open state
            query = """SELECT state, amount_total, currency_id AS currency, type, is_proforma FROM account_invoice WHERE journal_id = %s AND state NOT IN ('paid', 'cancel');"""
            self.env.cr.execute(query, (self.id,))
            query_results = self.env.cr.dictfetchall()
            today = datetime.today()
            query = """SELECT amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND date < %s AND state = 'open';"""
            self.env.cr.execute(query, (self.id, today))
            late_query_results = self.env.cr.dictfetchall()
            for result in query_results:
                if result['type'] in ['in_refund', 'out_refund']:
                    factor = -1
                else:
                    factor = 1
                cur = self.env['res.currency'].browse(result.get('currency'))
                if result.get('state') in ['draft', 'proforma', 'proforma2'] and result.get('is_proforma') != True:
                    number_draft += 1
                    sum_draft += cur.compute(result.get('amount_total'), currency) * factor
                elif result.get('state') == 'open':
                    number_waiting += 1
                    sum_waiting += cur.compute(result.get('amount_total'), currency) * factor
            for result in late_query_results:
                if result['type'] in ['in_refund', 'out_refund']:
                    factor = -1
                else:
                    factor = 1
                cur = self.env['res.currency'].browse(result.get('currency'))
                number_late += 1
                sum_late += cur.compute(result.get('amount_total'), currency) * factor

        difference = currency.round(last_balance - account_sum) + 0.0
        return {
            'number_to_reconcile': number_to_reconcile,
            'account_balance': formatLang(self.env, currency.round(account_sum) + 0.0, currency_obj=currency),
            'last_balance': formatLang(self.env, currency.round(last_balance) + 0.0, currency_obj=currency),
            'difference': formatLang(self.env, difference, currency_obj=currency) if difference else False,
            'number_draft': number_draft,
            'number_waiting': number_waiting,
            'number_late': number_late,
            'sum_draft': formatLang(self.env, currency.round(sum_draft) + 0.0, currency_obj=currency),
            'sum_waiting': formatLang(self.env, currency.round(sum_waiting) + 0.0, currency_obj=currency),
            'sum_late': formatLang(self.env, currency.round(sum_late) + 0.0, currency_obj=currency),
            'currency_id': currency.id,
            'bank_statements_source': self.bank_statements_source,
            'title': title,
        }


class ProformaAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    proforma_number = fields.Char()
    is_proforma = fields.Boolean(string='Proforma')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', compute='get_sale_order')

    @api.multi
    @api.depends('origin')
    def get_sale_order(self):
        for rec in self:
            if rec.origin:
                sale_order_obj = self.env['sale.order'].sudo().search([('name', '=', rec.origin)], limit=1)
                if sale_order_obj:
                    rec.sale_order_id = sale_order_obj.id

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

    proforma_invoice_count = fields.Integer(string='# of Proforma Invoices', compute='_get_proforma_invoiced',
                                            readonly=True)

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids), ('is_proforma', '=', False), ('type', '!=', 'proforma')]
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
            action['domain'] = [('id', 'in', invoices.ids), ('is_proforma', '=', True), ('type', '=', 'proforma')]
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
                [('id', 'in', invoice_ids.ids), ('is_proforma', '=', False), ('type', '!=', 'proforma')])
            order.update({
                'invoice_count': len(set(refund_ids.ids)) + res_count,
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.depends('state', 'order_line.invoice_status')
    def _get_proforma_invoiced(self):
        for rec in self:
            invoices = rec.mapped('invoice_ids')
            res_count = self.env['account.invoice'].search_count(
                [('id', 'in', invoices.ids), ('is_proforma', '=', True), ('type', '=', 'proforma')])
            rec.proforma_invoice_count = res_count

    @api.multi
    def action_proforma(self):
        for rec in self:
            proforma_inv_data = self._prepare_invoice()
            proforma_inv_data.update({'is_proforma': True, 'type': 'proforma'})
            proforma_invoice = self.env['account.invoice'].create(proforma_inv_data)
            for line in rec.order_line:
                vals = line._prepare_invoice_line(line.product_uom_qty)
                vals.update({'invoice_id': proforma_invoice.id, 'sale_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)
            proforma_invoice.compute_taxes()
            proforma_invoice.action_date_assign()
