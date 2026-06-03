/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { PaymentRegisterPopup } from "@pos_payment/app/popups/payment_register_popup/payment_register_popup";
import { useService } from "@web/core/utils/hooks";

export class InvoiceListPopup extends Component {
    static template = "pos_payment.InvoiceListPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        invoices: { type: Array, optional: true },
        partner: { optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        title: _t("Select Invoices"),
        invoices: [],
    };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            selectedInvoices: {},
        });
    }

    toggleInvoice(invoice) {
        if (this.state.selectedInvoices[invoice.id]) {
            delete this.state.selectedInvoices[invoice.id];
        } else {
            this.state.selectedInvoices[invoice.id] = invoice;
        }
    }

    isSelected(invoice) {
        return !!this.state.selectedInvoices[invoice.id];
    }

    getSelectedInvoices() {
        return Object.values(this.state.selectedInvoices);
    }

    getTotalAmount() {
        return this.getSelectedInvoices().reduce((sum, inv) => sum + inv.amount_residual, 0);
    }

    getFormattedDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString();
    }

    getPaymentStateLabel(state) {
        const labels = {
            'not_paid': 'Not Paid',
            'partial': 'Partially Paid',
        };
        return labels[state] || state;
    }

    confirm() {
        const selectedInvoices = this.getSelectedInvoices();
        
        if (selectedInvoices.length === 0) {
            this.notification.add(_t("Please select at least one invoice"), {
                type: "warning",
            });
            return;
        }

        // Show payment register popup
        this.dialog.add(PaymentRegisterPopup, {
            title: _t("Register Payment"),
            invoices: selectedInvoices,
            totalAmount: this.getTotalAmount(),
            getPayload: () => {},
        });

        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
