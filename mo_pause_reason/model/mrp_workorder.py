# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError



class mrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    pause_reason_id = fields.Many2one(
        'work.order.pause.reason',
        string="Pause Reason",
        readonly=True,
        ondelete="restrict")

class mrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    pause_reason_id = fields.Many2one(
        'work.order.pause.reason',
        string="Pause Reason",
        readonly=True,
        ondelete="restrict")

    @api.multi
    def end_previous(self, doall=False):
        """
        @param: doall:  This will close all open time lines on the open work orders when doall = True, otherwise
        only the one of the current user
        """
        # TDE CLEANME
        timeline_obj = self.env['mrp.workcenter.productivity']
        domain = [('workorder_id', 'in', self.ids), ('date_end', '=', False)]
        if not doall:
            domain.append(('user_id', '=', self.env.user.id))
        for timeline in timeline_obj.search(domain, limit=None if doall else 1):
            wo = timeline.workorder_id
            if timeline.loss_type != 'productive':
                timeline.write({'date_end': fields.Datetime.now()})
            else:
                maxdate = fields.Datetime.from_string(timeline.date_start) + relativedelta(minutes=wo.duration_expected - wo.duration)
                enddate = datetime.now()
                if maxdate > enddate:
                    timeline.write({'date_end': enddate})
                else:
                    timeline.write({'date_end': maxdate})
                    loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'performance')], limit=1)
                    if not len(loss_id):
                        raise UserError(_("You need to define at least one unactive productivity loss in the category 'Performance'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
                    timeline.copy({'date_start': maxdate, 'date_end': enddate, 'loss_id': loss_id.id})
            # print pause_reason
            timeline.write({'pause_reason_id':timeline.workorder_id.pause_reason_id.id})
            print timeline


class WorkOrderPauseReason(models.Model):
    _name = 'work.order.pause.reason'
    _description = 'Work Order Pause Reason'

    name = fields.Char('Reason', required=True, translate=True)
