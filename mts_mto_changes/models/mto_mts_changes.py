from openerp import fields, models, api, exceptions
import datetime


class mrp_production_inherit(models.Model):
    _inherit = 'mrp.production'

    check_procurement = fields.Boolean(string="Procurement Checked")

    @api.multi
    def procurement_action(self):
        for rec in self:
            vendor_list = []
            product_template_id = self.env['product.template'].search([('id', '=', rec.product_id.product_tmpl_id.id)])
            # product_bill_material = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_template_id.id)])
            product_bill_material = self.env['mrp.bom'].search([('product_id', '=', rec.product_id.id)])
            # raise Warning(str(product_bill_material))
            for line in rec.move_raw_ids:
                product = self.env['product.product'].browse(line.product_id.id)
                # raise Warning(str(product.seller_ids))

                for vendor in product.seller_ids:
                    vendor_id = vendor.name.id
                    # raise Warning(str(vendor_id))
                    vendor_list.append(vendor_id)
                    # raise Warning(str(vendor_list[0]))

                for component in product_bill_material.bom_line_ids:
                    if component.product_id.id == product.id:
                        if product.virtual_available > (component.product_qty * rec.product_qty) - product.virtual_available:
                            pass
                        else:
                            for route in product.route_ids:
                                if route.name == 'Buy':
                                    if product.virtual_available < 0:
                                        vals = {
                                            'partner_id': vendor_list[0],
                                            'order_line': [(0, 0, {'product_id': product.id,
                                                                   'product_qty': -1 * (product.virtual_available),
                                                                   'product_uom': 1,
                                                                   'price_unit': product.lst_price,
                                                                   'name': product.name,
                                                                   'date_planned': datetime.datetime.now(),
                                                                   })]
                                        }
                                    elif product.virtual_available > 0:
                                        vals = {
                                            'partner_id': vendor_list[0],
                                            'order_line': [(0, 0, {'product_id': product.id,
                                                                   'product_qty': (component.product_qty * rec.product_qty) - product.virtual_available,
                                                                   'product_uom': 1,
                                                                   'price_unit': product.lst_price,
                                                                   'name': product.name,
                                                                   'date_planned': datetime.datetime.now(),
                                                                   })]
                                        }
                                    if vendor_list[0]:
                                        self.env['purchase.order'].create(vals)
                                    break
                                elif route.name == 'Manufacture':
                                    template_id3 = self.env['product.template'].search([('id', '=',component.product_id.product_tmpl_id.id)])
                                    # mrp_production_id3 = self.env['mrp.bom'].search([('product_tmpl_id', '=', template_id3.id)])
                                    mrp_production_id3 = self.env['mrp.bom'].search([('product_id', '=', component.product_id.id)])
                                    res = self.env['mrp.production'].create(
                                        {'product_id': component.product_id.id,
                                         'product_uom_id': 1,
                                         'bom_id': mrp_production_id3.id,
                                         'check_procurement':True,
                                         'product_qty':(component.product_qty * rec.product_qty) - product.virtual_available,
                                         })

                                    vendor_list2 = []
                                    prod_template_id = self.env['product.template'].search([('id', '=', product.product_tmpl_id.id)])
                                    # prod_bill_of_material = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod_template_id.id)])
                                    prod_bill_of_material = self.env['mrp.bom'].search([('product_id', '=', product.id)])
                                    for compon in prod_bill_of_material.bom_line_ids:
                                        for seller_id in compon.product_id.seller_ids:
                                            vendor_id2 = seller_id.name.id
                                            vendor_list2.append(vendor_id2)

                                        for rou in compon.product_id.route_ids:
                                            if compon.product_id.virtual_available > ((compon.product_qty * (component.product_qty * rec.product_qty)) - compon.product_id.virtual_available):
                                                pass
                                            else:
                                                if rou.name == 'Buy':
                                                    if compon.product_id.virtual_available < 0:
                                                        vals = {
                                                            'partner_id': vendor_list2[0],
                                                            'order_line': [(0, 0, {'product_id': compon.product_id.id,
                                                                                   'product_qty': -1 * (compon.product_id.virtual_available) ,
                                                                                   'product_uom': 1,
                                                                                   'price_unit': 0,
                                                                                   'name': compon.product_id.name,
                                                                                   'date_planned': datetime.datetime.now(),
                                                                                   })]
                                                        }
                                                    elif compon.product_id.virtual_available > 0:
                                                        vals = {
                                                            'partner_id': vendor_list2[0],
                                                            'order_line': [(0, 0, {'product_id': compon.product_id.id,
                                                                                   'product_qty': (
                                                                                                  compon.product_qty * (
                                                                                                  component.product_qty * rec.product_qty)) - compon.product_id.virtual_available,
                                                                                   'product_uom': 1,
                                                                                   'price_unit': 0,
                                                                                   'name': compon.product_id.name,
                                                                                   'date_planned': datetime.datetime.now(),
                                                                                   })]
                                                        }
                                                    if vendor_list2[0]:
                                                        self.env['purchase.order'].create(vals)
                                                    break

                                                elif rou.name == 'Manufacture':
                                                    template_id4 = self.env['product.template'].search([('id', '=',compon.product_id.product_tmpl_id.id)])
                                                    # mrp_production_id4 = self.env['mrp.bom'].search([('product_tmpl_id', '=', template_id4.id)])
                                                    mrp_production_id4 = self.env['mrp.bom'].search([('product_id', '=', compon.product_id.id)])
                                                    res = self.env['mrp.production'].create(
                                                                                            {
                                                                                            'product_id': compon.product_id.id,
                                                                                            'product_uom_id': 1,
                                                                                            'bom_id': mrp_production_id4.id,
                                                                                            'product_qty': (compon.product_qty * (component.product_qty * rec.product_qty)) - compon.product_id.virtual_available,
                                                                                            'check_procurement': True,

                                                                                            })
                                                    vendor_list3 = []
                                                    prod_template_id2 = self.env['product.template'].search([('id', '=', compon.product_id.product_tmpl_id.id)])
                                                    # prod_bill_of_material2 = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod_template_id2.id)])
                                                    prod_bill_of_material2 = self.env['mrp.bom'].search([('product_id', '=', compon.product_id.id)])
                                                    for compon2 in prod_bill_of_material2.bom_line_ids:
                                                        for seller_id in compon2.product_id.seller_ids:
                                                            vendor_id3 = seller_id.name.id
                                                            vendor_list3.append(vendor_id3)

                                                        for rou2 in compon2.product_id.route_ids:
                                                            if compon2.product_id.virtual_available > ((compon2.product_qty * (compon.product_qty * (component.product_qty * rec.product_qty))) - compon2.product_id.virtual_available):
                                                                pass
                                                            else:
                                                                print"(str(rou2.name))", (str(rou2.name))
                                                                if rou2.name == 'Buy':
                                                                    if compon2.product_id.virtual_available < 0:
                                                                        vals = {
                                                                            'partner_id': vendor_list3[0],
                                                                            'order_line': [
                                                                                (0, 0, {'product_id': compon2.product_id.id,
                                                                                        'product_qty': -1 * (compon2.product_id.virtual_available),
                                                                                        'product_uom': 1,
                                                                                        'price_unit': 0,
                                                                                        'name': compon2.product_id.name,
                                                                                        'date_planned': datetime.datetime.now(),
                                                                                        })]
                                                                        }
                                                                    elif compon2.product_id.virtual_available > 0:
                                                                        vals = {
                                                                            'partner_id': vendor_list3[0],
                                                                            'order_line': [
                                                                                (0, 0,
                                                                                 {'product_id': compon2.product_id.id,
                                                                                  'product_qty': (
                                                                                                 compon2.product_qty * (
                                                                                                 compon.product_qty * (
                                                                                                 component.product_qty * rec.product_qty))) - compon2.product_id.virtual_available,
                                                                                  'product_uom': 1,
                                                                                  'price_unit': 0,
                                                                                  'name': compon2.product_id.name,
                                                                                  'date_planned': datetime.datetime.now(),
                                                                                  })]
                                                                        }
                                                                    if vendor_list3[0]:
                                                                        self.env['purchase.order'].create(vals)
                                                                    break
                                                                elif rou2.name == 'Manufacture':
                                                                    template_id = self.env['product.template'].search(
                                                                        [('id', '=', compon2.product_id.product_tmpl_id.id)])

                                                                    mrp_production_id = self.env['mrp.bom'].search(
                                                                        [('product_tmpl_id', '=', template_id.id)])
                                                                    # raise Warning(str(mrp_production_id.id))
                                                                    res = self.env['mrp.production'].create(
                                                                        {'product_id': compon2.product_id.id,
                                                                         'product_uom_id': 1,
                                                                         'bom_id': mrp_production_id.id,
                                                                         'check_procurement': True,
                                                                         'product_qty':(compon2.product_qty * (compon.product_qty * (component.product_qty * rec.product_qty))) - compon2.product_id.virtual_available,
                                                                         })
                                                                    vendor_list4 = []
                                                                    prod_template_id3 = self.env['product.template'].search(
                                                                        [('id', '=', compon2.product_id.product_tmpl_id.id)])

                                                                    # prod_bill_of_material3 = self.env['mrp.bom'].search(
                                                                    #     [('product_tmpl_id', '=', prod_template_id3.id)])
                                                                    prod_bill_of_material3 = self.env['mrp.bom'].search(
                                                                        [(
                                                                         'product_id', '=', compon2.product_id.id)])

                                                                    for compon3 in prod_bill_of_material3.bom_line_ids:
                                                                        for seller_id in compon3.product_id.seller_ids:
                                                                            vendor_id4 = seller_id.name.id
                                                                            vendor_list4.append(vendor_id4)

                                                                        for rou3 in compon3.product_id.route_ids:
                                                                            if compon3.product_id.virtual_available > ((compon3.product_qty * (compon2.product_qty * (compon.product_qty * (component.product_qty * rec.product_qty)))) - compon3.product_id.virtual_available):
                                                                                pass
                                                                            else:
                                                                                print"(str(rou3.name))", (str(rou3.name))
                                                                                if rou3.name == 'Buy':
                                                                                    if compon3.product_id.virtual_available < 0:
                                                                                        vals = {
                                                                                            'partner_id': vendor_list4[0],
                                                                                            'order_line': [
                                                                                                (0, 0,
                                                                                                 {'product_id': compon3.product_id.id,
                                                                                                  'product_qty': -1 * (compon3.product_id.virtual_available),
                                                                                                  'product_uom': 1,
                                                                                                  'price_unit': 0,
                                                                                                  'name': compon3.product_id.name,
                                                                                                  'date_planned': datetime.datetime.now(),
                                                                                                  })]
                                                                                        }
                                                                                    elif compon3.product_id.virtual_available > 0:
                                                                                        vals = {
                                                                                            'partner_id': vendor_list4[
                                                                                                0],
                                                                                            'order_line': [
                                                                                                (0, 0,
                                                                                                 {
                                                                                                     'product_id': compon3.product_id.id,
                                                                                                     'product_qty': (
                                                                                                                    compon3.product_qty * (
                                                                                                                    compon2.product_qty * (
                                                                                                                    compon.product_qty * (
                                                                                                                    component.product_qty * rec.product_qty)))) - compon3.product_id.virtual_available,
                                                                                                     'product_uom': 1,
                                                                                                     'price_unit': 0,
                                                                                                     'name': compon3.product_id.name,
                                                                                                     'date_planned': datetime.datetime.now(),
                                                                                                     })]
                                                                                        }
                                                                                    if vendor_list4[0]:
                                                                                        self.env['purchase.order'].create(vals)
                                                                                    break
                                                                                elif rou3.name == 'Manufacture':
                                                                                    template_id2 = self.env[
                                                                                        'product.template'].search(
                                                                                        [('id', '=',
                                                                                          compon3.product_id.product_tmpl_id.id)])

                                                                                    # mrp_production_id2 = self.env['mrp.bom'].search(
                                                                                    #     [('product_tmpl_id', '=', template_id2.id)])
                                                                                    mrp_production_id2 = self.env[
                                                                                        'mrp.bom'].search(
                                                                                        [('product_id', '=',
                                                                                          compon3.product_id.id)])

                                                                                    # raise Warning(str(mrp_production_id.id))
                                                                                    res = self.env['mrp.production'].create(
                                                                                        {'product_id': compon3.product_id.id,
                                                                                         'product_uom_id': 1,
                                                                                         'bom_id': mrp_production_id2.id,
                                                                                         'check_procurement': True,
                                                                                         'product_qty':(compon3.product_qty * (compon2.product_qty * (compon.product_qty * (component.product_qty * rec.product_qty)))) - compon3.product_id.virtual_available,
                                                                                         })

                                                                                    vendor_list5 = []
                                                                                    prod_template_id4 = self.env[
                                                                                        'product.template'].search(
                                                                                        [('id', '=',
                                                                                          compon2.product_id.product_tmpl_id.id)])

                                                                                    # raise Warning(str(prod_template_id2.name))
                                                                                    # prod_bill_of_material4 = self.env[
                                                                                    #     'mrp.bom'].search(
                                                                                    #     [('product_tmpl_id', '=',
                                                                                    #       prod_template_id4.id)])

                                                                                    prod_bill_of_material4 = self.env[
                                                                                        'mrp.bom'].search(
                                                                                        [('product_id', '=',
                                                                                          compon2.product_id.id)])

                                                                                    for compon4 in prod_bill_of_material4.bom_line_ids:
                                                                                        # raise Warning(str(compon.product_id.seller_ids))
                                                                                        for seller_id in compon4.product_id.seller_ids:
                                                                                            # raise Warning(str(seller_id))
                                                                                            vendor_id5 = seller_id.name.id
                                                                                            vendor_list5.append(vendor_id5)

                                                                                        for rou4 in compon4.product_id.route_ids:
                                                                                            if compon4.product_id.virtual_available > ((compon4.product_qty * (compon3.product_qty * (compon2.product_qty * (compon.product_qty * (component.product_qty * rec.product_qty))))) - compon4.product_id.virtual_available):
                                                                                                pass
                                                                                            else:
                                                                                                print"(str(rou4.name))", (
                                                                                                    str(rou4.name))
                                                                                                if rou4.name == 'Buy':
                                                                                                    if compon4.product_id.virtual_available < 0:
                                                                                                        vals = {
                                                                                                            'partner_id': vendor_list5[0],
                                                                                                            'order_line': [
                                                                                                                (0, 0,
                                                                                                                 {
                                                                                                                     'product_id': compon4.product_id.id,
                                                                                                                     'product_qty': -1 * (compon4.product_id.virtual_available),
                                                                                                                     'product_uom': 1,
                                                                                                                     'price_unit': 0,
                                                                                                                     'name': compon4.product_id.name,
                                                                                                                     'date_planned': datetime.datetime.now(),
                                                                                                                 })]
                                                                                                        }
                                                                                                    elif compon4.product_id.virtual_available > 0:
                                                                                                        vals = {
                                                                                                            'partner_id':
                                                                                                                vendor_list5[
                                                                                                                    0],
                                                                                                            'order_line': [
                                                                                                                (0, 0,
                                                                                                                 {
                                                                                                                     'product_id': compon4.product_id.id,
                                                                                                                     'product_qty': (
                                                                                                                                    compon4.product_qty * (
                                                                                                                                    compon3.product_qty * (
                                                                                                                                    compon2.product_qty * (
                                                                                                                                    compon.product_qty * (
                                                                                                                                    component.product_qty * rec.product_qty))))) - compon4.product_id.virtual_available,
                                                                                                                     'product_uom': 1,
                                                                                                                     'price_unit': 0,
                                                                                                                     'name': compon4.product_id.name,
                                                                                                                     'date_planned': datetime.datetime.now(),
                                                                                                                 })]
                                                                                                        }
                                                                                                    if vendor_list5[0]:
                                                                                                        self.env['purchase.order'].create(
                                                                                                        vals)
                                                                                                    break

                                                                                    # raise Warning(str("d,osjdfnjdaskNAJSDFDSA"))

                vendor_list = []
                vendor_list2 = []
                vendor_list3 = []
                vendor_list4 = []
                vendor_list5 = []
            rec.check_procurement = True
