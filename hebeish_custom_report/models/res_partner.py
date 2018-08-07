# -*- coding: utf-8 -*-

import logging
from odoo.osv import expression
from odoo import api, fields, models, _

class ResPartner(models.Model):

    _inherit = "res.partner"

    partner_code = fields.Char(string='Code',copy=False)

    _sql_constraints = [
        ('partnercode_unique', 'unique(partner_code)', 'Code already exists!')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('partner_code', 'ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()