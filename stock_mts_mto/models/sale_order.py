from openerp import fields, models, api, exceptions
import datetime
from odoo.tools.translate import _


class sale_order_inherit(models.Model):
    _inherit = 'sale.order'

    @api.depends('state')
    def _get_order_count(self):
        for order in self:
            purchases = self.env['purchase.order'].sudo().search([('sale_production_id', '=', order.id)])
            purchase_lines = self.env['purchase.order.line'].sudo().search([('sale_production_id', '=', order.id)])
            manufactures = self.env['mrp.production'].sudo().search([('sale_production_id', '=', order.id)])
            manufacture_lines = self.env['production.sale.order'].sudo().search([('sale_order_id', '=', order.id)])
            for line in purchase_lines:
                if line.order_id not in purchases:
                    purchases += line.order_id
            for line in manufacture_lines:
                if line.production_id not in manufactures:
                    manufactures += line.production_id
            order.update({
                'purchase_order_count': len(purchases),
                'manufacture_order_count': len(manufactures),
            })

    purchase_order_count = fields.Integer(string='# of purchases', compute='_get_order_count', readonly=True)
    manufacture_order_count = fields.Integer(string='# of manufactures', compute='_get_order_count', readonly=True)


    @api.multi
    def action_view_purchase_order(self):
        purchases = self.env['purchase.order'].sudo().search([('sale_production_id', '=', self.id)])
        purchase_lines = self.env['purchase.order.line'].sudo().search([('sale_production_id', '=', self.id)])
        for line in purchase_lines:
            if line.order_id.sale_production_id != self.id:
                purchases += line.order_id
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif len(purchases) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchases.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.multi
    def action_view_manufacture_order(self):
        manufactures = self.env['mrp.production'].sudo().search([('sale_production_id', '=', self.id)])
        manufacture_lines = self.env['production.sale.order'].sudo().search([('sale_order_id', '=', self.id)])
        for line in manufacture_lines:
            if line.production_id not in manufactures:
                manufactures += line.production_id
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        if len(manufactures) > 1:
            action['domain'] = [('id', 'in', manufactures.ids)]
        elif len(manufactures) == 1:
            action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = manufactures.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.multi
    def get_procurement_method(self, line):
        procurement_method = ''
        is_mts = False
        for route in line.product_id.route_ids:
            for pull in route.pull_ids:
                if pull.action == 'buy':
                    procurement_method = 'buy'
                elif pull.action == 'manufacture':
                    procurement_method = 'manufacture'
        for route in line.product_id.route_ids:
            if route.is_mts:
                return procurement_method


    @api.multi
    def action_confirm(self):
        for record in self:
            for line in record.order_line:
                procurement_method = record.get_procurement_method(line)
                if line.product_uom_qty > line.product_id.virtual_available:
                    if procurement_method == 'buy':
                        record.create_po_procurement_order(line)
                    elif procurement_method == 'manufacture':
                        record.create_mo_procurement_order(line)
        return super(sale_order_inherit, self).action_confirm()


    @api.multi
    def get_order_virtual_quantity(self, line, from_mo=False):
        if from_mo:
            mo_virtual_qty = line.product_id.virtual_available + line.product_uom_qty
            if mo_virtual_qty < 0:
                virtual_qty = 0
            else:
                virtual_qty = mo_virtual_qty
        else:
            if line.product_id.virtual_available < 0:
                virtual_qty = 0
            else:
                virtual_qty = line.product_id.virtual_available
        return virtual_qty

    @api.multi
    def create_po_procurement_order(self,line,from_mo=False):
        for vendor in line.product_id.seller_ids:
            virtual_qty = self.get_order_virtual_quantity(line,from_mo)
            rfq = self.env['purchase.order'].sudo().search([('partner_id', '=', vendor.name.id), ('state', '=', 'draft')],
                                                    order="id desc", limit=1)
            if line.product_id.description_sale:
                product_desc = line.product_id.description_sale
            else:
                product_desc = line.product_id.name
            vals = {'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty - virtual_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'price_unit': line.product_id.standard_price,
                    'name': product_desc,
                    'date_planned': datetime.datetime.now(),
                    'sale_production_id': self.id,
                    }
            origin = self.name + ": Buy -> CustomersMTO"
            if rfq:
                rfq.write({'origin': origin, 'order_line': [(0, 0, vals)]})
            else:
                seq_id = self.env['ir.sequence'].search([('code','=','purchase.order'),('company_id','=',self.company_id.id)]).id
                seq = 'New'
                if seq_id:
                    seq = self.env['ir.sequence'].get_id(seq_id)
                type_obj = self.env['stock.picking.type']
                types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', self.company_id.id)])
                if not types:
                    types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
                self.env['purchase.order'].sudo().create({
                    'partner_id': vendor.name.id,
                    'origin': origin,
                    'name': seq,
                    'sale_production_id': self.id,
                    'company_id': self.company_id.id,
                    'picking_type_id': types[:1].id,
                    'order_line': [(0, 0, vals)]
                })
            break

    @api.multi
    def create_mo_procurement_order(self,line,from_mo=False):
        virtual_qty = self.get_order_virtual_quantity(line,from_mo)
        product_bom_id = self.env['mrp.bom'].sudo().search([('product_id', '=', line.product_id.id)], order="id desc", limit=1)
        prod_id = product_bom_id
        produc_tmpl_bom_id = self.env['mrp.bom'].sudo().search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)], order="id desc", limit=1)
        if product_bom_id:
           prod_id = product_bom_id
        elif produc_tmpl_bom_id:
           prod_id = produc_tmpl_bom_id

        if prod_id:
            ref = self.name + ":Manufacture -> CustomersMTO"
            customer = self.partner_id.name
            mrp = self.env['mrp.production'].search([('product_id','=',line.product_id.id),('company_id','=',self.company_id.id),('state','=','confirmed')],limit=1)
            if mrp:
                mrp.change_product_qty(line.product_uom_qty - virtual_qty)
                add_source = True
                add_customer = True
                for sale_line in mrp.sale_order_ids:
                    if sale_line.sale_order_id.id == self.id:
                        add_source = False
                        add_customer = False
                if mrp.origin and add_source:
                    ref = mrp.origin + ', ' + ref
                if mrp.customer_reference and add_customer:
                    customer = mrp.customer_reference + ', ' + customer
            else:
                picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'mrp_operation'),('warehouse_id.company_id', '=',self.company_id.id)],limit=1).id
                seq_id = self.env['ir.sequence'].search([('code', '=', 'mrp.production'), ('company_id', '=', self.company_id.id)]).id
                seq = 'New'
                if seq_id:
                    seq = self.env['ir.sequence'].get_id(seq_id)
                mrp = self.env['mrp.production'].sudo().create({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty - virtual_qty,
                    'product_uom_id': line.product_id.uom_id.id,
                    'bom_id': prod_id.id,
                    'name': seq,
                    'company_id': self.company_id.id,
                    'picking_type_id': picking_type_id,
                    'sale_production_id': self.id,
                })
            mrp.write({'origin': ref, 'customer_reference': customer})
            add_ref = True
            for sale_line in mrp.sale_order_ids:
                if sale_line.sale_order_id.id == self.id:
                    add_ref = False
            if add_ref:
                sale_log_vals = {'sale_order_id': self.id, 'qty_to_produce': line.product_uom_qty - virtual_qty, }
                mrp.write({'sale_order_ids': [(0, 0, sale_log_vals)]})

            for mrp_line in mrp.move_raw_ids:
                virtual_qty = self.get_order_virtual_quantity(mrp_line, True)
                if mrp_line.product_uom_qty > virtual_qty:
                    procurement_method = self.get_procurement_method(mrp_line)
                    if procurement_method == 'buy':
                        self.create_po_procurement_order(mrp_line,True)
                    elif procurement_method == 'manufacture':
                        self.create_mo_procurement_order(mrp_line,True)

    @api.multi
    def action_cancel(self):
        for record in self:
            rfqs = self.env['purchase.order'].sudo().search([('sale_production_id', '=', record.id)])
            for rfq in rfqs:
                rfq.button_cancel()
            rfq_lines = self.env['purchase.order.line'].sudo().search([('sale_production_id', '=', record.id)])
            for line in rfq_lines:
                if line.order_id not in rfqs:
                    line.unlink()
            mos = self.env['mrp.production'].sudo().search([('sale_production_id', '=', record.id),('state','!=','cancel')], limit=1)
            for mo in mos:
                if mo.product_qty <= sum(line.qty_to_produce for line in self.env['production.sale.order'].sudo().search([('production_id', '=', mo.id),('sale_order_id','=',record.id),('status','!=','cancel')])):
                    mo.action_cancel()
            mos_lines = self.env['production.sale.order'].sudo().search([('sale_order_id', '=', record.id),('status','!=','cancel')])
            for line in mos_lines:
                if line.production_id not in mos:
                    if line.production_id.product_qty <= line.qty_to_produce:
                        line.production_id.action_cancel()
                    else:
                        line.production_id.change_product_qty(-line.qty_to_produce)
        return super(sale_order_inherit, self).action_cancel()