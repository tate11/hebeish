# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import models, fields, api

class ScrapReason(models.Model):
    _name = 'scrap.reason'

    name = fields.Char('Reason')

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    scrap_reason_id = fields.Many2one('scrap.reason','Reason', required=True, copy=False)