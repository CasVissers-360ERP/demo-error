# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    invoice_payment_count = fields.Integer(
        string='Invoice Payments',
        compute='_compute_invoice_payment_count'
    )
    # new changes 
    pos_invoice_payment_ids = fields.One2many(
        'account.payment',
        'pos_session_id',
        string='POS Invoice Payments',
        domain=[('payment_type', '=', 'inbound')],
    )

    # invoice_payment_amount_cash = fields.Monetary(
    #     string='Invoice Payment - Cash',
    #     compute='_compute_invoice_payment_amounts',
    #     currency_field='currency_id'
    # )
    
    # invoice_payment_amount_bank = fields.Monetary(
    #     string='Invoice Payment - Bank',
    #     compute='_compute_invoice_payment_amounts',
    #     currency_field='currency_id'
    # )

    # new changes
    @api.depends('payment_method_ids', 'order_ids', 'cash_register_balance_start', 'pos_invoice_payment_ids')
    def _compute_cash_balance(self):
        """Override to include cash invoice payments in the expected cash balance.

        The base _compute_cash_balance only counts POS order payments and manual
        cash-in/out statement lines.  Invoice payments created as account.payment
        are invisible to it, so the server computes a lower expected balance than
        the actual cash in the drawer and _post_statement_difference posts a
        spurious 'Cash Difference Gain' entry at session close.

        NOTE: account.payment states are draft / in_process / paid / canceled /
        rejected  — there is NO 'posted' state on account.payment.
        """
        super()._compute_cash_balance()
        for session in self:
            if not session.config_id.enable_invoice_payment:
                continue
            cash_payment_method = session.payment_method_ids.filtered('is_cash_count')[:1]
            if not cash_payment_method:
                continue
            invoice_payment_cash = sum(
                p.amount
                for p in session.pos_invoice_payment_ids
                if p.state in ('in_process', 'paid') and p.journal_id.type == 'cash'
            )
            if invoice_payment_cash:
                session.cash_register_balance_end += invoice_payment_cash
                session.cash_register_difference = (
                    session.cash_register_balance_end_real - session.cash_register_balance_end
                )

    @api.depends('statement_line_ids')
    def _compute_invoice_payment_count(self):
        """Count invoice payments made during this session"""
        for session in self:
            invoice_payments = self.env['account.payment'].search_count([
                ('pos_session_id', '=', session.id),
                ('payment_type', '=', 'inbound')
            ])
            session.invoice_payment_count = invoice_payments

    # @api.depends('statement_line_ids')
    # def _compute_invoice_payment_amounts(self):
    #     """Compute invoice payment amounts by journal type"""
    #     for session in self:
    #         invoice_payments = self.env['account.payment'].search([
    #             ('pos_session_id', '=', session.id),
    #             ('payment_type', '=', 'inbound')
    #         ])
            
    #         # Group by journal type
    #         cash_amount = sum(p.amount for p in invoice_payments if p.journal_id.type == 'cash')
    #         bank_amount = sum(p.amount for p in invoice_payments if p.journal_id.type == 'bank')
            
    #         session.invoice_payment_amount_cash = cash_amount
    #         session.invoice_payment_amount_bank = bank_amount

    def action_view_invoice_payments(self):
        """Open list view of invoice payments for this session"""
        self.ensure_one()
        return {
            'name': 'Invoice Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('pos_session_id', '=', self.id), ('payment_type', '=', 'inbound')],
            'context': {'create': False}
        }

    @api.model
    def _load_pos_data_models(self, config_id):
        """Add account.move and account.journal to loaded models"""
        data = super()._load_pos_data_models(config_id)
        config = self.env['pos.config'].browse(config_id)
        if config.enable_invoice_payment:
            data += ['account.move', 'account.journal']
        return data

    def _loader_params_pos_config(self):
        """Add invoice payment fields to pos.config loader"""
        result = super()._loader_params_pos_config()
        result['search_params']['fields'] += ['enable_invoice_payment', 'invoice_payment_journal_ids']
        return result

    @api.model
    def register_invoice_payment(self, session_id, invoice_ids, journal_id, amount):
        """Register payment for invoices using standard payment flow"""
        try:
            _logger.info('POS register_invoice_payment: session=%s invoice_ids=%s journal_id=%s amount=%s',
                         session_id, invoice_ids, journal_id, amount)
            # Get session
            session = self.browse(session_id).exists()
            if not session:
                return {'error': 'Invalid session'}
            
            # Get invoices - ensure they are posted and have amounts due
            invoices = self.env['account.move'].browse(invoice_ids).filtered(
                lambda inv: inv.state == 'posted' and inv.amount_residual > 0
            )
            
            if not invoices:
                return {'error': 'No valid unpaid invoices found'}
            
            # Ensure all invoices are from the same partner
            partners = invoices.mapped('partner_id')
            if len(partners) > 1:
                return {'error': 'Cannot pay invoices from different partners in one transaction'}
            
            # Validate journal
            journal = self.env['account.journal'].browse(journal_id).exists()
            if not journal:
                return {'error': 'Invalid journal'}
            
            partner = partners[0]
            
            # Calculate total amount residual
            total_residual = sum(invoices.mapped('amount_residual'))
            
            # Validate payment amount
            if amount <= 0:
                return {'error': 'Payment amount must be greater than zero'}
            
            # Create payment values
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner.id,
                'amount': amount,
                'currency_id': invoices[0].currency_id.id,
                'journal_id': journal_id,
                'date': fields.Date.context_today(self),
                'memo': f"POS Payment - {', '.join(invoices.mapped('name'))}",
                'pos_session_id': session.id,  # Link to session
            }
            
            # Get available payment method line
            payment_method_line = journal._get_available_payment_method_lines('inbound')
            if payment_method_line:
                payment_vals['payment_method_line_id'] = payment_method_line[0].id
            else:
                return {'error': f'No inbound payment method available for journal {journal.name}'}
            
            # Create payment
            payment = self.env['account.payment'].create(payment_vals)

            # Ensure the payment is linked to the session (safety in case of overrides)
            payment.pos_session_id = session.id

            # ---------------------------------------------------------------
            # Enterprise / accountant outstanding-account fix
            # ---------------------------------------------------------------
            # In Enterprise (with account_accountant / accountant installed),
            # account.payment.create() does NOT force outstanding_account_id.
            # It relies on payment_method_line_id.payment_account_id being
            # configured on the journal.  When that is missing, outstanding_account_id
            # stays False, _generate_journal_entry() is skipped entirely (it
            # filters `lambda p: not p.move_id and p.outstanding_account_id`),
            # no journal entry is created, reconciliation silently fails, and
            # the payment name falls back to the generic ir.sequence → "PAY00001".
            # Fix: mirror Community behaviour and force the outstanding account via
            # chart-template lookup whenever it is not already set.
            # ---------------------------------------------------------------
            if not payment.outstanding_account_id:
                try:
                    outstanding_account = payment._get_outstanding_account(payment.payment_type)
                    if outstanding_account:
                        payment.outstanding_account_id = outstanding_account.id
                        _logger.info(
                            'POS register_invoice_payment: forced outstanding_account_id=%s '
                            'on payment %s (Enterprise accountant compatibility)',
                            outstanding_account.id, payment.id,
                        )
                except Exception:
                    _logger.warning(
                        'POS register_invoice_payment: could not resolve outstanding account '
                        'for payment %s; journal entry creation may be skipped in Enterprise',
                        payment.id, exc_info=True,
                    )

            # Post the payment
            payment.action_post()

            # Verify that a journal entry was actually created (guard against silent skips)
            if not payment.move_id:
                _logger.error(
                    'POS register_invoice_payment: payment %s has no move_id after action_post(); '
                    'outstanding_account_id=%s  -- reconciliation will not happen',
                    payment.id, payment.outstanding_account_id,
                )
                return {'error': (
                    'Payment was created but no journal entry was generated. '
                    'Please ensure the journal\'s inbound payment method line has an '
                    '"Outstanding Receipts Account" configured.'
                )}
            
            # Reconcile the payment with invoices
            # Get the receivable line from the payment's journal entry (move_id)
            payment_line = payment.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable') 
                and not l.reconciled
            )
            
            # Get unreconciled receivable lines from invoices
            invoice_lines = invoices.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' 
                and not l.reconciled
            )
            
            # Reconcile lines
            if payment_line and invoice_lines:
                (payment_line + invoice_lines).reconcile()
            
            # Get which invoices were fully/partially paid
            paid_info = []
            for invoice in invoices:
                invoice.invalidate_recordset(['amount_residual', 'payment_state'])
                paid_info.append({
                    'name': invoice.name,
                    'amount_paid': invoice.amount_total - invoice.amount_residual,
                    'amount_remaining': invoice.amount_residual,
                    'fully_paid': invoice.payment_state == 'paid'
                })
            
            result = {
                'success': True,
                'payment_id': payment.id,
                'payment_name': payment.name,
                'invoices_paid': paid_info,
                'total_residual': total_residual,
                'amount_paid': amount
            }
            _logger.info('POS register_invoice_payment done: payment_id=%s invoices=%s amount_paid=%s residual_after=%s',
                         payment.id, paid_info, amount, invoices.mapped('amount_residual'))
            return result
            
        except Exception as e:
            import traceback
            _logger.exception('POS register_invoice_payment error')
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    def get_closing_control_data(self):
        """Override to include invoice payments in closing data"""
        result = super().get_closing_control_data()
        
        # Get invoice payments made during this session using pos_session_id
        invoice_payments = self.sudo().env['account.payment'].search([
            ('pos_session_id', '=', self.id),
            ('payment_type', '=', 'inbound')
        ])

        _logger.info('POS closing invoice payments: session=%s ids=%s amounts=%s states=%s',
                     self.id,
                     invoice_payments.ids,
                 invoice_payments.mapped('amount'),
                 invoice_payments.mapped('state'))

        # Important: do NOT mix payments from other sessions; rely strictly on pos_session_id link
        
        total_invoice_payment_amount = sum(invoice_payments.mapped('amount'))
        
        # Group invoice payments by journal type
        invoice_payments_by_type = {}
        for payment in invoice_payments:
            journal_type = payment.journal_id.type
            if journal_type not in invoice_payments_by_type:
                invoice_payments_by_type[journal_type] = []
            invoice_payments_by_type[journal_type].append(payment)
        
        # Calculate amounts by type
        invoice_payment_cash = sum([p.amount for p in invoice_payments_by_type.get('cash', [])])
        invoice_payment_bank = sum([p.amount for p in invoice_payments_by_type.get('bank', [])])
        
        _logger.info('POS closing invoice payments by type: cash=%s bank=%s',
                     invoice_payment_cash, invoice_payment_bank)
        
        # Add invoice payment information and include ONLY CASH in balance (bank goes directly to bank)
        if result.get('default_cash_details') is not None:
            # Always expose the key so the template can render consistently
            result['default_cash_details']['invoice_payment_amount'] = total_invoice_payment_amount
            result['default_cash_details']['invoice_payment_amount_cash'] = invoice_payment_cash
            result['default_cash_details']['invoice_payment_amount_bank'] = invoice_payment_bank
            # Add ONLY CASH invoice payments to the total cash balance (bank goes to bank account)
            result['default_cash_details']['amount'] += invoice_payment_cash
            
            # NOTE: Do NOT add invoice payments to 'moves' list
            # Invoice payments are shown separately and should not be part of "Cash In/Out" breakdown
        else:
            # If no cash details (no cash control) still expose invoice payments
            result['invoice_payment_amount'] = total_invoice_payment_amount
        
        return result
