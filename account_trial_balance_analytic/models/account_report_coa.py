# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class report_account_coa_analytic(models.AbstractModel):
    _inherit = "account.coa.report"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.coa'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'state': context_id.all_entries and 'all' or 'posted',
            'cash_basis': context_id.cash_basis,
            'hierarchy_3': context_id.hierarchy_3,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'periods_number': context_id.periods_number,
            'periods': [[context_id.date_from, context_id.date_to]] + context_id.get_cmp_periods(),
            'analytic_account_ids': context_id.analytic_account_ids,
            'analytic_tag_ids': context_id.analytic_tag_ids,
        })
        return self.with_context(new_context)._lines(line_id)

class AccountReportTypeInherit(models.Model):
    _inherit = "account.report.type"

    @api.model_cr
    def init(self):
        rec = super(AccountReportTypeInherit, self).init()
        self._cr.execute(""" update account_report_type set analytic = True""")
    # analytic = fields.Boolean('Reports enable the analytic filter', default=True)