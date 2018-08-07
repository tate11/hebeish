# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class workorderPause(models.TransientModel):

    """ Ask a reason for the workorder pause."""
    _name = 'work.order.pause'
    _description = __doc__

    reason_id = fields.Many2one(
        'work.order.pause.reason',
        string='Reason',
        required=True)

    @api.multi
    def confirm_pause(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        order_ids = self._context.get('active_ids')
        if order_ids is None:
            return act_close
        assert len(order_ids) == 1, "Only 1 workorder ID expected"
        workorder = self.env['mrp.workorder'].browse(order_ids)
        workorder.pause_reason_id = self.reason_id.id
        workorder.end_previous()
        return act_close
