
from odoo import api, fields, models, _
from random import randint


class product_template_inherit(models.Model):
    _inherit = 'product.template'

    barcode = fields.Char('Barcode', readonly=True, store=True)

    @api.model
    def create(self, vals):
        random_barcode = (randint(1000000000000, 9999999999999))
        barcode_exist = self.env['product.template'].search([('barcode', '=', random_barcode)])
        while barcode_exist:
            random_barcode = (randint(1000000000000, 9999999999999))
            barcode_exist = self.env['product.template'].search([('barcode', '=', random_barcode)])

        vals['barcode'] = str(random_barcode)
        return super(product_template_inherit, self).create(vals)

    @api.model
    def product_generate_barcode(self):
        for record in self.env['product.template'].search([('barcode','=',False)]):
            random_barcode = (randint(1000000000000, 9999999999999))
            barcode_exist = self.env['product.template'].search([('barcode', '=', random_barcode)])
            while barcode_exist:
                random_barcode = (randint(1000000000000, 9999999999999))
                barcode_exist = self.env['product.template'].search([('barcode', '=', random_barcode)])

            record.update({'barcode': str(random_barcode)})