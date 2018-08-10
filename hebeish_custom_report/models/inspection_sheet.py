# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class InspectionSheet(models.Model):

    _name = "inspection.sheet"
    _inherit = ['mail.thread']

    name = fields.Char('name', readonly=True)

    report_template = fields.Selection([('humidity_test', 'Raw Material Humidity Test'),
                                        ('melt_flow_rate', 'Raw Material Melt Flow Rate'),
                                        ('material_density', 'Material Density Test Report'),
                                        ('pipe_periodic', 'Pipe Periodic Examination Report'),
                                        ('pipe_heat', 'Pipe Heat Reversion Test'),
                                        ('final_dimension_weight', 'Final Product Dimension & Weight Test'),
                                        ('pipe_general', 'Pipe General Test'),
                                        ('micro_duct_pipe', 'HDPE MicroDuct Pipes')])
    acc_to = fields.Char('Acc to')
    mrp_id = fields.Many2one('mrp.production',string="Manufacturing Order")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_first_approval', 'Waiting First Approval'),
        ('waiting_second_approval', 'Waiting Second Approval'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    certificate_no = fields.Char('Certificate No',copy=False)
    product_code = fields.Many2one('product.product',string='Product Code')
    product_description = fields.Char('Product Description')
    diameter = fields.Char('Diameter')

    # batch_no = fields.Char('Batch No')
    customer_name = fields.Char('Customer Name')
    project_name = fields.Char('Project Name')

    issue_date = fields.Datetime('Date of Issue', readonly=True, default=lambda self: fields.datetime.now())
    production_date = fields.Datetime('Production Date')
    raw_material = fields.Char('Raw Material')
    material_type = fields.Char('Type of PE Material')
    batch_no = fields.Integer('Batch No')
    po_no = fields.Integer('PO No')

    test_temperature = fields.Char('Test Temperature')
    time_interval = fields.Char('Time Interval')
    load_piston = fields.Char('Load on Piston')


    w1_result = fields.Float('W1', digits=dp.get_precision('Quality Reports'))
    w1_result_label = fields.Float('W1', digits=dp.get_precision('Quality Reports'),compute='compute_final_w1_w2')
    w1_result_label2 = fields.Float('W1', digits=dp.get_precision('Quality Reports'),compute='compute_final_w1_w2')
    w2_result = fields.Float('W2', digits=dp.get_precision('Quality Reports'))
    w2_result_label = fields.Float('W2', digits=dp.get_precision('Quality Reports'),compute='compute_final_w1_w2')
    final_w1_w2 = fields.Float('Final', digits=dp.get_precision('Quality Reports'),compute='compute_final_w1_w2')
    final_w1_w2_label = fields.Float('Final', digits=dp.get_precision('Quality Reports'),compute='compute_final_w1_w2')

    m1_result = fields.Float('M1', digits=dp.get_precision('Quality Reports'))
    m1_result_label = fields.Float('M1', digits=dp.get_precision('Quality Reports'),compute='compute_final_m1_m2')
    m1_result_label2 = fields.Float('M1', digits=dp.get_precision('Quality Reports'),compute='compute_final_m1_m2')
    m2_result = fields.Float('M2', digits=dp.get_precision('Quality Reports'))
    m2_result_label = fields.Float('M2', digits=dp.get_precision('Quality Reports'),compute='compute_final_m1_m2')
    final_m1_m2 = fields.Float('Final Result', digits=dp.get_precision('Quality Reports'),compute='compute_final_m1_m2')
    final_m1_m2_label = fields.Float('Final Result', digits=dp.get_precision('Quality Reports'),compute='compute_final_m1_m2')

    melt_flow_rate = fields.One2many('melt.flow', 'sheet_id', string='')
    total = fields.Float('Total', digits=dp.get_precision('Quality Reports'), compute='compute_total')
    final_result = fields.Float('Final Result', digits=dp.get_precision('Quality Reports'), compute='compute_total')
    final_result_mean = fields.Float('Mean Value', digits=dp.get_precision('Quality Reports'), compute='compute_total')
    final_result_label = fields.Float('Final Result', digits=dp.get_precision('Quality Reports'), compute='compute_total')


    thickness = fields.Char('Thickness')
    l0_1 = fields.Float('1', digits=dp.get_precision('Quality Reports'),)
    l0_2 = fields.Float('2', digits=dp.get_precision('Quality Reports'),)
    l0_3 = fields.Float('3', digits=dp.get_precision('Quality Reports'),)

    l1_1 = fields.Float('1', digits=dp.get_precision('Quality Reports'),)
    l1_2 = fields.Float('2', digits=dp.get_precision('Quality Reports'),)
    l1_3 = fields.Float('3', digits=dp.get_precision('Quality Reports'),)

    e1 = fields.Float('E1 (%)', digits=dp.get_precision('Quality Reports'),compute='compute_e')
    e2 = fields.Float('E2 (%)', digits=dp.get_precision('Quality Reports'),compute='compute_e')
    e3 = fields.Float('E3 (%)', digits=dp.get_precision('Quality Reports'),compute='compute_e')
    total_e = fields.Float('Total (%)',compute='compute_e', digits=dp.get_precision('Quality Reports'),)

    periodic_intervals = fields.One2many('periodic.interval','sheet_id',string='')
    total_qty_tested = fields.Float('Total Quantity Tested', digits=dp.get_precision('Quality Reports'),)
    accepted_qty = fields.Float('(A)= Accepted Quantity', digits=dp.get_precision('Quality Reports'),)
    rejected_qty = fields.Float('(R)= Rejected Quantity', digits=dp.get_precision('Quality Reports'),)


    final_dimension_weight = fields.One2many('final.dimension.weight','sheet_id',string='')
    d_max = fields.Float('D Max')
    d_min = fields.Float('D Min')
    d_max_label = fields.Float('D Max', compute='compute_dmax_dmin')
    d_max_label1 = fields.Float('D Max', compute='compute_dmax_dmin')
    d_min_label = fields.Float('D Min', compute='compute_dmax_dmin')
    d_min_label1 = fields.Float('D Min', compute='compute_dmax_dmin')
    d_final = fields.Float('D Final', compute='compute_dmax_dmin')
    pipe_general = fields.One2many('pipe.general','sheet_id',string='')

    dimensions = fields.Char('Dimensions')
    test_date = fields.Datetime('Test Date')
    operator_name = fields.Char('Operator Name')
    pressure_class = fields.Char('Pressure Class')
    work_order_number = fields.Char('Work Order Number')
    date_work_order = fields.Datetime('Date of Work Order')
    work_order_qty = fields.Char('Work Order Qty')
    delivered_qty = fields.Char('Delivered Qty')

    micro_duct_pipe = fields.One2many('micro.duct.pipe','report_id','Test Results')

    first_approved_by = fields.Many2one('res.users', string='First Approved')
    second_approved_by = fields.Many2one('res.users', string='Second Approved')
    get_data_from_messages = fields.Char(string='Get Data From Messages', compute='get_approval_users_from_messages')

    @api.multi
    def get_approval_users_from_messages(self):
        for sheet in self:
            if sheet.state == 'approved':
                if not sheet.first_approved_by or not sheet.second_approved_by:
                    for message in sheet.message_ids:
                        for track in message.tracking_value_ids:
                            if track.old_value_char == 'Waiting First Approval' and track.new_value_char == 'Waiting Second Approval':
                                fuser = self.env['res.users'].search(
                                    [('partner_id', '=', track.mail_message_id.author_id.id)])
                                sheet.write({'first_approved_by': fuser.id})

                            elif track.old_value_char == 'Waiting Second Approval' and track.new_value_char == 'Approved':
                                secuser = self.env['res.users'].search(
                                    [('partner_id', '=', track.mail_message_id.author_id.id)])
                                sheet.write({'second_approved_by': secuser.id})

    @api.onchange('product_code')
    def onchange_product_code(self):
        for each in self:
            each.product_description = each.product_code.description_sale

    @api.onchange('l0_1','l0_2','l0_3','l1_1','l1_2','l1_3')
    def compute_e(self):
        for record in self:
            if record.l0_1:
                record.e1 = (record.l0_1 - record.l1_1)*100/ record.l0_1
            if record.l0_2:
                record.e2 = (record.l0_2 - record.l1_2)*100/ record.l0_2
            if record.l0_3:
                record.e3 = (record.l0_3 - record.l1_3)*100/ record.l0_3
            record.total_e = record.e1 + record.e2 + record.e3

    @api.onchange('d_max','d_min')
    def compute_dmax_dmin(self):
        for record in self:
            record.d_max_label = record.d_max
            record.d_max_label1 = record.d_max
            record.d_min_label = record.d_min
            record.d_min_label1 = record.d_min
            record.d_final = record.d_max - record.d_min

    @api.onchange('melt_flow_rate')
    def compute_total(self):
        for record in self:
            total =0
            count=0
            for line in record.melt_flow_rate:
                total += line.result
                count+=1
            record.total = total
            if count:
                record.final_result = 600 *(total/count)/240
                record.final_result_label = 600 *(total/count)/240
                record.final_result_mean = total/count

    @api.onchange('w1_result','w2_result')
    def compute_final_w1_w2(self):
        for record in self:
            if record.w1_result:
                record.final_w1_w2 = (record.w1_result-record.w2_result)/record.w1_result
                record.w1_result_label = record.w1_result
                record.w1_result_label2 = record.w1_result
                record.w2_result_label = record.w2_result
                record.final_w1_w2_label = (record.w1_result-record.w2_result)/record.w1_result

    @api.onchange('m1_result','m2_result')
    def compute_final_m1_m2(self):
        for record in self:
            if record.m1_result:
                record.final_m1_m2 = (record.m1_result-record.m2_result)/record.m1_result
                record.m1_result_label = record.m1_result
                record.m1_result_label2 = record.m1_result
                record.m2_result_label = record.m2_result
                record.final_m1_m2_label = (record.m1_result-record.m2_result)/record.m1_result


    @api.onchange("report_template")
    def set_acc_to(self):
        if self.report_template == "humidity_test":
            self.acc_to = 'DIN 8074/8075'
        elif self.report_template == "melt_flow_rate":
            self.acc_to = 'ISO 1133/ DIN 53735'
        elif self.report_template == "material_density":
            self.acc_to = 'DIN 53479'
        elif self.report_template == "pipe_periodic":
            self.acc_to = 'DIN 8075'
        elif self.report_template == "pipe_heat":
            self.acc_to = 'DIN 8075'
        elif self.report_template == "pipe_general":
            self.acc_to = 'DIN 8074/8075'
        elif self.report_template == "final_dimension_weight":
            self.acc_to = 'DIN 8074, Sec. 6; 8075, Sec. 5.3'

    @api.multi
    def action_submit(self):
        for order in self:
            order.state = 'waiting_first_approval'
        return True

    @api.multi
    def action_first_approval(self):
        for order in self:
            order.write({'state': 'waiting_second_approval', 'first_approved_by': self._uid})
        return True

    @api.multi
    def action_second_approval(self):
        for order in self:
            order.write({'state': 'approved', 'second_approved_by': self._uid})
            sequence = self.env['ir.sequence'].sudo().next_by_code('inspection.sheet')
            order.certificate_no = sequence
            order.name = sequence
        return True

    @api.multi
    def action_cancel(self):
        for order in self:
            order.state = 'cancel'
        return True

    @api.multi
    def action_draft(self):
        for order in self:
            order.state = 'draft'
        return True

class MicroDuctPipe(models.Model):
    _name = 'micro.duct.pipe'

    name = fields.Selection([('test1','MFR (gm/10min.)@ 5 KG'),
                             ('test2','Density (Kg/m3)'),
                             ('test3','Tensile Strength MPA'),
                             ('test4','Elongation %'),
                             ('test5','Crush Test'),
                             ('test6','Pressure test @ 1.5X'),
                             ('test7','Ball Pass Test'),
                             ('test8','Kink Test'),
                             ('test9','Weight gm/m'),
                             ('test10','Coil length m'),
                             ('test11','OD mm'),
                             ('test12','Thickness mm'),
                             ('test13','Ovality mm'),
                            ],string='Test')
    result = fields.Char('Result')
    test_result = fields.Boolean('Accept/Reject')
    report_id = fields.Many2one('inspection.sheet')


class MeltFlow(models.Model):

    _name = "melt.flow"

    result = fields.Float('Result', digits=dp.get_precision('Quality Reports'),)
    sheet_id = fields.Many2one('inspection.seet')

class PeriodicTimeInterval(models.Model):

    _name = "periodic.interval"

    work_order = fields.Char('Work Order')
    product_code = fields.Char('Product Code')
    production_description = fields.Char('Production Description')
    sheet_id = fields.Many2one('inspection.seet')

    a1 = fields.Char('A')
    a2 = fields.Char('A')
    a3 = fields.Char('A')
    a4 = fields.Char('A')
    a5 = fields.Char('A')
    a6 = fields.Char('A')

    r1 = fields.Char('R')
    r2 = fields.Char('R')
    r3 = fields.Char('R')
    r4 = fields.Char('R')
    r5 = fields.Char('R')
    r6 = fields.Char('R')


class FinalDimensionWeight(models.Model):

    _name = "final.dimension.weight"

    thickness = fields.Char('Thickness (mm)')
    diameter = fields.Char('Diameter (mm)')
    sample_date = fields.Date('Sample Date')
    sample_weight = fields.Char('Sample Weight (Grm)')
    sample_from = fields.Datetime('From', default=lambda self: fields.datetime.now())
    sample_to = fields.Datetime('To')
    period = fields.Char('Period')
    sheet_id = fields.Many2one('inspection.seet')


class PipeGeneral(models.Model):

    _name = "pipe.general"

    test = fields.Selection([('melt_flow', 'Melt Flow Index'),
                                        ('density', ' Density'),
                                        ('oxidation', 'Oxidation'),
                                        ('hydrostatic_pressure', 'Hydrostatic Pressure Test'),
                                        ('dimensional_check', 'Dimensional Check'),
                                        ('surface_condition', 'Surface Condition')], string='Test')
    standard = fields.Char('Standard')
    condition = fields.Char('Conditions')
    result = fields.Char('Results')
    unit = fields.Char('Unit')
    sheet_id = fields.Many2one('inspection.seet')

class mrp_production_inherits(models.Model):

    _inherit = "mrp.production"

    report_ids = fields.One2many('inspection.sheet','mrp_id',string='Quality Reports')

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        if not self.report_ids:
            raise UserError(_('You should provide all related quality reports.'))
        return super(mrp_production_inherits, self).button_mark_done()


    @api.multi
    def post_inventory(self):
        self.ensure_one()
        if not self.report_ids:
            raise UserError(_('You should provide all related quality reports.'))
        return super(mrp_production_inherits, self).post_inventory()