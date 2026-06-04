# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _release_pos_stock_bookings(self):
        """Release the stock booked while the order(s) were being built."""
        uuids = [order.uuid for order in self if order.uuid]
        if not uuids:
            return
        reservations = (
            self.env["stock.reservation"]
            .sudo()
            .search(
                [
                    ("pos_order_uuid", "in", uuids),
                    ("state", "!=", "cancel"),
                ]
            )
        )
        reservations.release_reserve()

    @api.model
    def _process_order(self, order, existing_order):
        order_id = super()._process_order(order, existing_order)
        # Once the order is saved/validated it ships its own stock, so the
        # temporary booking is released to avoid double-holding the stock.
        self.browse(order_id)._release_pos_stock_bookings()
        return order_id
