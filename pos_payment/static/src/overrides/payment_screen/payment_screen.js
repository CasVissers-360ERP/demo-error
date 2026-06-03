/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async addNewPaymentLine(paymentMethod) {
        // Check if payment method is Customer Account and enable invoice
        if (paymentMethod.type === "pay_later") {
            this.currentOrder.set_to_invoice(true);
        }
        
        return await super.addNewPaymentLine(...arguments);
    }
});
