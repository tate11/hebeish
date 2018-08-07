import datetime
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class sale_order_approval(models.Model):
    _inherit = 'sale.order'

    def _get_sales_person(self):
        for order in self:
            sale_person = self.env['res.users'].sudo().browse(order.user_id.id)
            order.sale_person = sale_person.name

    project_name = fields.Char('Project Name')
    sale_person = fields.Char('Salesperson',compute='_get_sales_person')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('waiting_first_approval', 'Waiting First Approval'),
        ('waiting_second_approval', 'Waiting Second Approval'),
        ('approved', 'Approved'),
        ('sent', 'Quotation Sent'),
        ('revised', 'Revised'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def action_submit(self):
        for order in self:
            order.state = 'waiting_first_approval'
        return True

    @api.multi
    def action_first_approval(self):
        for order in self:
            order.state = 'waiting_second_approval'
        return True

    @api.multi
    def action_second_approval(self):
        for order in self:
            order.state = 'approved'
        return True
    
    
    @api.multi
    @api.onchange('date_order')
    def date_order_change(self):
        for line in self.order_line:
            date_1 = datetime.datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S")
            if line.product_uom_qty < line.onhand_qty:
                line.schedule_date = date_1
            else:
                line.schedule_date = date_1 + datetime.timedelta(days=line.customer_lead)


    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            # 'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id
        }
        return invoice_vals


    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    invoice.sudo().write({'user_id':self.user_id and self.user_id.id})
                    references[invoice] = order
                    invoices[group_key] = invoice
                elif group_key in invoices:
                    vals = {}
                    if order.name not in invoices[group_key].origin.split(', '):
                        vals['origin'] = invoices[group_key].origin + ', ' + order.name
                    if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(', '):
                        vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                    invoices[group_key].write(vals)
                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]


class sale_order_line_inherits(models.Model):
    _inherit = 'sale.order.line'

    onhand_qty = fields.Float('Onhand Qty',related='product_id.qty_available')
    schedule_date = fields.Datetime(string="Delivery Date")

    @api.multi
    @api.onchange('customer_lead','product_uom_qty')
    def customer_lead_change(self):
        date_1 = datetime.datetime.strptime(self.order_id.date_order, "%Y-%m-%d %H:%M:%S")
        if self.product_uom_qty < self.onhand_qty:
            self.schedule_date = date_1
        else:
            self.schedule_date = date_1 + datetime.timedelta(days=self.customer_lead)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        # name = product.name_get()[0][1]
        name = ''
        if product.description_sale:
            # name = '\n' + product.description_sale
            name = product.description_sale
        vals['name'] = name

        date_1 = datetime.datetime.strptime(self.order_id.date_order, "%Y-%m-%d %H:%M:%S")
        if self.product_uom_qty < self.onhand_qty:
            vals['schedule_date'] = date_1
        else:
            vals['schedule_date'] = date_1 + datetime.timedelta(days=self.customer_lead)

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product),
                                                                                 product.taxes_id, self.tax_id)
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}