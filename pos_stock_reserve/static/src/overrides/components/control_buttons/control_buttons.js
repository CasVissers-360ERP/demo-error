/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";

patch(ControlButtons.prototype, {
    async onClickBookStock() {
        const order = this.pos.get_order();
        const line = order?.get_selected_orderline();
        if (!line) {
            this.notification.add(_t("Select an order line first."), { type: "warning" });
            return;
        }
        const sessionId = this.pos.session.id;
        try {
            if (line.uiState.bookedReservationId) {
                await this.env.services.orm.call("pos.session", "unbook_stock_line", [
                    sessionId,
                    line.uuid,
                ]);
                line.uiState.bookedReservationId = false;
                this.notification.add(_t("Stock booking released."), { type: "info" });
            } else {
                const result = await this.env.services.orm.call("pos.session", "book_stock_line", [
                    sessionId,
                    line.uuid,
                    order.uuid,
                    line.product_id.id,
                    line.get_quantity(),
                ]);
                line.uiState.bookedReservationId = result.reservation_id;
                if (result.state === "assigned") {
                    this.notification.add(_t("Stock booked."), { type: "success" });
                } else {
                    this.notification.add(
                        _t("Booked, but the stock is not fully available."),
                        { type: "warning" }
                    );
                }
            }
        } catch (error) {
            this.notification.add(_t("Could not update the stock booking."), { type: "danger" });
            throw error;
        }
    },
});
