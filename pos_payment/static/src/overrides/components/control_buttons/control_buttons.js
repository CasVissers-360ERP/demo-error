/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { InvoiceListPopup } from "@pos_payment/app/popups/invoice_list_popup/invoice_list_popup";

patch(ControlButtons.prototype, {
    async onClickInvoice() {
        const partner = this.pos.get_order()?.get_partner();
        
        // Build domain for unpaid invoices
        let domain = [
            ["move_type", "in", ["out_invoice", "out_refund"]],
            ["state", "=", "posted"],
            ["payment_state", "in", ["not_paid", "partial"]],
            ["currency_id", "=", this.pos.currency.id],
        ];
        
        if (partner) {
            domain.push(["partner_id", "child_of", partner.id]);
        }
        
        // Fetch invoices using ORM
        const invoices = await this.env.services.orm.searchRead(
            "account.move",
            domain,
            ["id", "name", "partner_id", "amount_total", "amount_residual", 
             "invoice_date", "invoice_date_due", "currency_id", "payment_state", 
             "invoice_origin", "ref", "move_type"],
            { 
                limit: 100,
                order: "invoice_date desc"
            }
        );
        
        this.dialog.add(InvoiceListPopup, {
            title: partner ? `Invoices for ${partner.name}` : 'All Unpaid Invoices',
            invoices: invoices,
            partner: partner,
            getPayload: () => {},
        });
    },
});
