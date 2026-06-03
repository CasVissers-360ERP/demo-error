# -*- coding: utf-8 -*-

from odoo import models, api


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data):
        """Define domain for loading invoices in POS"""
        return [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ]

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Define fields to load for POS"""
        return [
            'id', 'name', 'partner_id', 'amount_total', 'amount_residual',
            'invoice_date', 'invoice_date_due', 'currency_id', 'payment_state',
            'invoice_origin', 'ref', 'move_type'
        ]
