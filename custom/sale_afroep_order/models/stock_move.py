# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools import float_compare, float_is_zero

from .sale_order import ACTIVE_RESERVE_STATES


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        moves._reduce_afroep_reservation()
        return moves

    def _reduce_afroep_reservation(self):
        """Draw down afroep reservations for goods leaving to the customer.

        Any done outgoing move of a reserved afroep product towards a customer
        location (a real delivery, a manual picking, or a kit component move)
        reduces the matching reservation(s) for that product and customer. The
        reserved product is the one chosen on the afroep sale order line, which
        is not necessarily the afroep product that was sold.
        """
        Reservation = self.env["stock.reservation"]
        for move in self:
            if move.location_dest_id.usage != "customer":
                continue
            # Never let a reservation move draw down a reservation.
            if Reservation.search_count([("move_id", "=", move.id)]):
                continue
            partner = (
                move.picking_id.partner_id
                or move.partner_id
                or move.group_id.partner_id
            )
            if not partner:
                continue
            reservations = Reservation.search(
                [
                    ("product_id", "=", move.product_id.id),
                    ("state", "in", list(ACTIVE_RESERVE_STATES)),
                    ("sale_line_id.is_afroep_line", "=", True),
                    ("sale_line_id.order_partner_id", "=", partner.id),
                ],
                order="date asc, id asc",
            )
            if not reservations:
                continue
            qty = move.product_uom._compute_quantity(
                move.quantity, move.product_id.uom_id
            )
            if float_is_zero(qty, precision_rounding=move.product_id.uom_id.rounding):
                continue
            self._consume_afroep_reservations(reservations, qty)

    @staticmethod
    def _consume_afroep_reservations(reservations, qty):
        """Decrement ``reservations`` (FIFO) by ``qty`` (in the product uom)."""
        for reservation in reservations:
            rounding = reservation.product_id.uom_id.rounding
            if float_compare(qty, 0, precision_rounding=rounding) <= 0:
                break
            # Currently reserved quantity, expressed in the product uom.
            reserved_in_product_uom = reservation.product_uom._compute_quantity(
                reservation.product_uom_qty, reservation.product_id.uom_id
            )
            take = min(reserved_in_product_uom, qty)
            remaining = reserved_in_product_uom - take
            qty -= take
            if float_is_zero(remaining, precision_rounding=rounding):
                reservation.release_reserve()
            else:
                new_qty = reservation.product_id.uom_id._compute_quantity(
                    remaining, reservation.product_uom
                )
                reservation.write({"product_uom_qty": new_qty})
