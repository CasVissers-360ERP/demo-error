/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PaymentRegisterPopup extends Component {
    static template = "pos_payment.PaymentRegisterPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        invoices: { type: Array, optional: true },
        totalAmount: { type: Number, optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        title: _t("Register Payment"),
        invoices: [],
        totalAmount: 0,
    };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            selectedJournalId: null,
            paymentAmount: this.props.totalAmount,
            isProcessing: false,
        });

        // Get available payment journals
        this.paymentJournals = this.getPaymentJournals();
        if (this.paymentJournals.length > 0) {
            this.state.selectedJournalId = this.paymentJournals[0].id;
        }
    }

    getPaymentJournals() {
        // Get journals from loaded data using Odoo 18 ORM
        const allJournals = this.pos.data.models['account.journal']?.getAll() || [];
        
        // Only show journals that are specifically selected in config
        if (this.pos.config.invoice_payment_journal_ids && 
            this.pos.config.invoice_payment_journal_ids.length > 0) {
            // Convert Base objects to IDs
            const configJournalIds = this.pos.config.invoice_payment_journal_ids.map(j => j.id);
            return allJournals.filter(
                j => configJournalIds.includes(j.id)
            );
        }
        
        // If nothing selected, return empty array
        return [];
    }

    get selectedJournal() {
        return this.paymentJournals.find(j => j.id === this.state.selectedJournalId);
    }

    onJournalChange(ev) {
        this.state.selectedJournalId = parseInt(ev.target.value);
    }

    onAmountChange(ev) {
        const value = parseFloat(ev.target.value);
        this.state.paymentAmount = isNaN(value) ? 0 : value;
    }

    async confirm() {
        if (!this.state.selectedJournalId) {
            this.notification.add(_t("Please select a payment journal"), {
                type: "warning",
            });
            return;
        }

        if (this.state.paymentAmount <= 0) {
            this.notification.add(_t("Payment amount must be greater than zero"), {
                type: "warning",
            });
            return;
        }

        if (this.state.paymentAmount > this.props.totalAmount) {
            const proceed = await this.dialog.add(ConfirmationDialog, {
                title: _t("Overpayment Warning"),
                body: _t("The payment amount is greater than the total invoice amount. Do you want to continue?"),
            });
            if (!proceed) {
                return;
            }
        }

        this.state.isProcessing = true;

        try {
            const invoiceIds = this.props.invoices.map(inv => inv.id);
            const result = await this.pos.registerInvoicePayment(
                invoiceIds,
                this.state.selectedJournalId,
                this.state.paymentAmount
            );

            if (result.error) {
                this.notification.add(result.error, {
                    type: "danger",
                });
            } else {
                this.notification.add(
                    _t("Payment registered successfully: %s", result.payment_name),
                    {
                        type: "success",
                    }
                );
                this.props.close();
            }
        } catch (error) {
            this.notification.add(
                _t("Error registering payment: %s", error.message || error),
                {
                    type: "danger",
                }
            );
        } finally {
            this.state.isProcessing = false;
        }
    }

    cancel() {
        this.props.close();
    }
}
