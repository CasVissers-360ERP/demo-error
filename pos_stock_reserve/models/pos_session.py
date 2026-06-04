# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import UserError

# Reservation states that still hold stock (i.e. are not released/cancelled).
ACTIVE_RESERVE_STATES = ("confirmed", "waiting", "partially_available", "assigned")


class PosSession(models.Model):
    _inherit = "pos.session"

    def _pos_active_reservations(self, line_uuid):
        """Active reservation(s) booked for the given POS order line."""
        return (
            self.env["stock.reservation"]
            .sudo()
            .search(
                [
                    ("pos_line_uuid", "=", line_uuid),
                    ("state", "in", list(ACTIVE_RESERVE_STATES)),
                ]
            )
        )

    def _check_pos_booking_access(self):
        self.ensure_one()
        if not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise UserError(_("Only Point of Sale users can book stock."))
        if self.state != "opened":
            raise UserError(_("Stock can only be booked from an open POS session."))

    def book_stock_line(self, line_uuid, order_uuid, product_id, qty):
        """Reserve ``qty`` of ``product_id`` for an in-progress POS order line.

        Returns the reservation id and its state so the UI can reflect whether
        the stock is fully held. Idempotent per line: re-booking returns the
        existing reservation.
        """
        self._check_pos_booking_access()
        existing = self._pos_active_reservations(line_uuid)
        if existing:
            reservation = existing[0]
            return {"reservation_id": reservation.id, "state": reservation.state}

        product = self.env["product.product"].browse(product_id).sudo()
        if not product.exists():
            raise UserError(_("The product to book no longer exists."))
        location = self.config_id.picking_type_id.default_location_src_id
        location_dest = self.env.ref(
            "stock_reserve.stock_location_reservation", raise_if_not_found=False
        )
        reservation = (
            self.env["stock.reservation"]
            .sudo()
            .create(
                {
                    "product_id": product.id,
                    "product_uom": product.uom_id.id,
                    "product_uom_qty": qty,
                    "name": f"POS {self.name} ({product.display_name})",
                    "location_id": location.id,
                    "location_dest_id": location_dest.id if location_dest else False,
                    "pos_order_uuid": order_uuid,
                    "pos_line_uuid": line_uuid,
                }
            )
        )
        reservation.reserve()
        return {"reservation_id": reservation.id, "state": reservation.state}

    def unbook_stock_line(self, line_uuid):
        """Release any active reservation booked for the given POS order line."""
        self._check_pos_booking_access()
        self._pos_active_reservations(line_uuid).release_reserve()
        return True
