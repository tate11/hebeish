from openerp import fields, models, api, exceptions
import datetime


class mrp_production_inherit(models.Model):
    _inherit = 'mrp.production'

    check_procurement = fields.Boolean(string="Procurement Checked")

    @api.multi
    def procurement_action(self):
        for rec in self:
            vendor_list = []
            rfq_list = []
            vals = {}
            product_template_id = self.env['product.template'].search([('id', '=', rec.product_id.product_tmpl_id.id)])
            product_bill_material = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_template_id.id)])

            for line in rec.move_raw_ids:
                product = self.env['product.product'].browse(line.product_id.id)

                for vendor in product.seller_ids:
                    vendor_id = vendor.name.id
                    vendor_list.append(vendor_id)

                rfq_ids = self.env['purchase.order'].search(
                    [('partner_id', '=', vendor_list[0])])

                for component in product_bill_material.bom_line_ids:
                    if component.product_id.id == product.id:
                        if product.virtual_available > (component.product_qty * rec.product_qty) - product.virtual_available:
                            pass
                        else:
                            for route in product.route_ids:
                                if route.name == 'Buy':
                                    if product.virtual_available < 0:
                                        if rfq_ids:
                                            for rfq in rfq_ids:
                                                rfq_list.append(rfq.state)
                                                if rfq.state == 'draft':
                                                    rfq.write({'order_line':[(0, 0, {'product_id': product.id,
                                                                       'product_qty': line.product_uom_qty,
                                                                       'product_uom': product.uom_id.id,
                                                                       'price_unit': product.lst_price,
                                                                       'name': product.name,
                                                                       'date_planned': datetime.datetime.now(),
                                                                        'mrp_production_id':rec.id,
                                                                       })]
                                                               })
                                                    break

                                        if 'draft' not in rfq_list:
                                            if rfq_ids:
                                                if vendor_list[0]:
                                                    res = self.env['purchase.order'].create({
                                                        'partner_id': vendor_list[0],
                                                        'order_line': [(0, 0, {'product_id': product.id,
                                                                               'product_qty': line.product_uom_qty,
                                                                               'product_uom': product.uom_id.id,
                                                                               'price_unit': product.lst_price,
                                                                               'name': product.name,
                                                                               'date_planned': datetime.datetime.now(),
                                                                               'mrp_production_id': rec.id,
                                                                               })]
                                                    })
                                                break
                                        if not rfq_ids:
                                            if vendor_list[0]:
                                                res = self.env['purchase.order'].create({
                                                    'partner_id': vendor_list[0],
                                                    'order_line': [(0, 0, {'product_id': product.id,
                                                                           'product_qty': line.product_uom_qty,
                                                                           'product_uom': product.uom_id.id,
                                                                           'price_unit': product.lst_price,
                                                                           'name': product.name,
                                                                           'date_planned': datetime.datetime.now(),
                                                                           'mrp_production_id': rec.id,
                                                                           })]
                                            })
                                            break


                                    elif product.virtual_available > 0:
                                        if rfq_ids:
                                            for rfq in rfq_ids:
                                                rfq_list.append(rfq.state)
                                                if rfq.state == 'draft':
                                                    rfq.write({'order_line':[(0, 0, {'product_id': product.id,
                                                                       'product_qty': (component.product_qty * rec.product_qty) - product.virtual_available,
                                                                       'product_uom': product.uom_id.id,
                                                                       'price_unit': product.lst_price,
                                                                       'name': product.name,
                                                                       'date_planned': datetime.datetime.now(),
                                                                       'mrp_production_id': rec.id,
                                                                    })]

                                                               })

                                        if 'draft' not in rfq_list:
                                            if rfq_ids:
                                                if vendor_list[0]:
                                                    res = self.env['purchase.order'].create({
                                                        'partner_id': vendor_list[0],
                                                        'order_line': [(0, 0, {'product_id': product.id,
                                                                               'product_qty': line.product_uom_qty,
                                                                               'product_uom': product.uom_id.id,
                                                                               'price_unit': product.lst_price,
                                                                               'name': product.name,
                                                                               'date_planned': datetime.datetime.now(),
                                                                               'mrp_production_id': rec.id,
                                                                               })]
                                                    })
                                                break
                                        if not rfq_ids:
                                            if vendor_list[0]:
                                                res = self.env['purchase.order'].create({
                                                    'partner_id': vendor_list[0],
                                                    'order_line': [(0, 0, {'product_id': product.id,
                                                                           'product_qty': (
                                                                                          component.product_qty * rec.product_qty) - product.virtual_available,
                                                                           'product_uom': product.uom_id.id,
                                                                           'price_unit': product.lst_price,
                                                                           'name': product.name,
                                                                           'date_planned': datetime.datetime.now(),                                                                           'mrp_production_id': rec.id,
                                                                           'mrp_production_id': rec.id,
                                                                           })]
                                                })
                                            break
                vendor_list = []
                rfq_list = []
        rec.check_procurement = True


