# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    picking_id = fields.Many2one('stock.picking',string='Picking')
