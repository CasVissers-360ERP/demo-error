/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    /**
     * Register payment for invoices
     * @param {Array<number>} invoiceIds - List of invoice IDs
     * @param {number} journalId - Payment journal ID
     * @param {number} amount - Payment amount
     * @returns {Promise<Object>} Payment registration result
     */
    async registerInvoicePayment(invoiceIds, journalId, amount) {
        console.log('POS registerInvoicePayment called', {
            sessionId: this.session.id,
            invoiceIds,
            journalId,
            amount,
        });
        
        try {
            const result = await this.env.services.orm.call(
                'pos.session',
                'register_invoice_payment',
                [this.session.id, invoiceIds, journalId, amount]
            );
            
            console.log('POS registerInvoicePayment result', result);
            return result;
        } catch (error) {
            console.error('POS registerInvoicePayment RPC error', error);
            return {
                error: error.message || _t("Failed to register payment")
            };
        }
    },
});
