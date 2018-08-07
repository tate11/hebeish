# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import tools
from openerp import models, fields


class StockAnalysis(models.Model):
    _name = 'stock.analysis'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Location', readonly=True)
    qty = fields.Float(string='Qty', readonly=True)
    incoming_qty = fields.Float(string='Incoming Qty', readonly=True)
    outgoing_qty = fields.Float(string='Outgoing Qty', readonly=True)
    package_id = fields.Many2one(
        'stock.quant.package', string='Package', readonly=True)
    in_date = fields.Datetime('Incoming Date', readonly=True)
    categ_id = fields.Many2one(
        'product.category', string='Category', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute(
            """CREATE or REPLACE VIEW %s as (
            SELECT
                quant.id AS id,
                quant.product_id AS product_id,
                quant.location_id AS location_id,
                (SELECT SUM(h.quantity) FROM stock_history h,
                                stock_move m WHERE h.move_id=m.id
                                AND h.product_id=quant.product_id AND h.location_id=quant.location_id
                                GROUP BY h.product_id)
                        AS qty,
                (SELECT SUM(h.quantity)
                                FROM stock_history h, stock_move m
                                WHERE h.move_id=m.id AND
                                h.product_id=quant.product_id AND h.location_id=quant.location_id AND h.quantity > 0
                                GROUP BY h.product_id)
                        AS incoming_qty,
                (SELECT SUM(h.quantity)
                                FROM stock_history h, stock_move m
                                WHERE h.move_id=m.id AND
                                h.product_id=quant.product_id AND h.location_id=quant.location_id AND h.quantity < 0
                                GROUP BY h.product_id)
                        AS outgoing_qty,
                quant.package_id AS package_id,
                quant.in_date AS in_date,
                quant.company_id,
                template.categ_id AS categ_id
            FROM stock_quant AS quant
            JOIN product_product prod ON prod.id = quant.product_id
            JOIN product_template template
                ON template.id = prod.product_tmpl_id
            )"""
            % (self._table)
        )
