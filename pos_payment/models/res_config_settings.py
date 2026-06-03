# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_enable_invoice_payment = fields.Boolean(
        related='pos_config_id.enable_invoice_payment',
        readonly=False,
        string="Invoice Payment"
    )
    pos_invoice_payment_journal_ids = fields.Many2many(
        related='pos_config_id.invoice_payment_journal_ids',
        readonly=False,
        string="Payment Journals"
    )
