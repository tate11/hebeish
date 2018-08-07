import datetime
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_image = fields.Binary('Report Image')
