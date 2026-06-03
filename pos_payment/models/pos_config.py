# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_invoice_payment = fields.Boolean(
        string='Enable Invoice Payment',
        default=True,
        help='Allow registering payments for invoices from POS'
    )
    invoice_payment_journal_ids = fields.Many2many(
        'account.journal',
        string='Invoice Payment Journals',
        domain=[('type', 'in', ['bank', 'cash'])],
        help='Journals available for invoice payments in POS'
    )
