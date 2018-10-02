# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_code = fields.Char(string='Code', copy=False)

    _sql_constraints = [
        ('partnercode_unique', 'unique(partner_code)', 'Code already exists!')
    ]
