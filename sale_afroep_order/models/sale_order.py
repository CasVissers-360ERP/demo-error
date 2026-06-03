# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

# Reservation states that still hold stock (i.e. are not released/cancelled).
ACTIVE_RESERVE_STATES = (
    "confirmed",
    "waiting",
    "partially_available",
    "assigned",
)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    has_afroep_line = fields.Boolean(
        compute="_compute_afroep", string="Has Afroep Lines"
    )
    afroep_reservation_count = fields.Integer(
        compute="_compute_afroep", string="Afroep Reservations"
    )

    @api.depends(
        "order_line.is_afroep_line",
        "order_line.reservation_ids",
        "order_line.reservation_ids.state",
    )
    def _compute_afroep(self):
        for order in self:
            order.has_afroep_line = bool(
                order.order_line.filtered("is_afroep_line")
            )
            order.afroep_reservation_count = len(order.order_line.reservation_ids)

    def action_view_afroep_reservations(self):
        """Smart-button action: list the stock reservations of this order."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock_reserve.action_stock_reservation_tree"
        )
        action["domain"] = [("sale_line_id", "in", self.order_line.ids)]
        action["context"] = {}
        return action

    def _check_afroep_reserve_products(self):
        """A reserve product is required so we can reserve on confirmation."""
        for order in self:
            missing = order.order_line.filtered(
                lambda line: line.is_afroep_line
                and not line.afroep_reserve_product_id
            )
            if missing:
                names = "\n".join(
                    "- %s" % line.product_id.display_name for line in missing
                )
                raise UserError(
                    _(
                        "These afroep (call-off) lines need a product to reserve "
                        "before the order can be confirmed:\n%s"
                    )
                    % names
                )

    def action_confirm(self):
        self._check_afroep_reserve_products()
        res = super().action_confirm()
        # Stock is reserved only once the order is confirmed, never while it is
        # still a quotation.
        for order in self:
            for line in order.order_line.filtered("is_afroep_line"):
                line._create_afroep_reservation()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_afroep_line = fields.Boolean(
        compute="_compute_is_afroep_line",
        store=True,
        string="Afroep Line",
        help="The product of this line is configured as an afroep (call-off) product.",
    )
    afroep_reserve_product_id = fields.Many2one(
        "product.product",
        string="Reserve Product",
        domain="[('is_storable', '=', True)]",
        copy=False,
        help="The storable product that is reserved in the warehouse when this "
        "afroep (call-off) line is confirmed. Its stock is held until drawn "
        "down by later outgoing moves to the customer.",
    )

    @api.depends("product_id", "product_id.is_afroep_product")
    def _compute_is_afroep_line(self):
        for line in self:
            line.is_afroep_line = bool(line.product_id.is_afroep_product)

    def _active_afroep_reservations(self):
        """Reservations of this line that still hold stock."""
        return self.reservation_ids.filtered(
            lambda r: r.state in ACTIVE_RESERVE_STATES
        )

    def _prepare_afroep_reservation_vals(self):
        """Reservation values for an afroep line.

        The reserved product is the one chosen on the line (not the afroep
        product being sold). Source is the main warehouse stock location,
        destination the virtual reservation location defined by ``stock_reserve``.
        """
        self.ensure_one()
        reserve_product = self.afroep_reserve_product_id
        location_id = self.order_id.warehouse_id.lot_stock_id
        location_dest = self.env.ref(
            "stock_reserve.stock_location_reservation", raise_if_not_found=False
        )
        return {
            "product_id": reserve_product.id,
            "product_uom": reserve_product.uom_id.id,
            "product_uom_qty": self.product_uom_qty,
            "name": f"{self.order_id.name} ({reserve_product.display_name})",
            "location_id": location_id.id,
            "location_dest_id": location_dest.id if location_dest else False,
            "price_unit": self.price_unit,
            "sale_line_id": self.id,
        }

    def _create_afroep_reservation(self):
        """Create and confirm the reservation for the chosen reserve product."""
        self.ensure_one()
        if not self.is_afroep_line or not self.afroep_reserve_product_id:
            return self.env["stock.reservation"]
        if self._active_afroep_reservations():
            return self.env["stock.reservation"]
        reservation = self.env["stock.reservation"].create(
            self._prepare_afroep_reservation_vals()
        )
        reservation.reserve()
        return reservation

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Afroep lines stay in stock: no delivery is procured on confirmation."""
        lines = self.filtered(lambda line: not line.is_afroep_line)
        return super(SaleOrderLine, lines)._action_launch_stock_rule(
            previous_product_uom_qty
        )
