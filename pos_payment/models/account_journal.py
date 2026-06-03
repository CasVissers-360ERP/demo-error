# -*- coding: utf-8 -*-

from odoo import models, api


class AccountJournal(models.Model):
    _name = 'account.journal'
    _inherit = ['account.journal', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data):
        """Define domain for loading journals in POS"""
        return [('type', 'in', ['bank', 'cash'])]

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Define fields to load for POS"""
        return ['id', 'name', 'code', 'type']
