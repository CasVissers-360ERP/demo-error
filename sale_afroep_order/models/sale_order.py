# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

# Context flag that suppresses automatic reservation creation (e.g. while
# copying/importing orders) if ever needed by other modules.
SKIP_AUTO_AFROEP = "skip_auto_afroep_reservation"

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
    can_reserve_afroep = fields.Boolean(
        compute="_compute_afroep",
        string="Can Reserve Afroep",
        help="True when the order is a quotation with afroep lines that still "
        "need a stock reservation.",
    )

    @api.depends(
        "state",
        "order_line.is_afroep_line",
        "order_line.afroep_reserve_product_id",
        "order_line.reservation_ids",
        "order_line.reservation_ids.state",
    )
    def _compute_afroep(self):
        for order in self:
            afroep_lines = order.order_line.filtered("is_afroep_line")
            order.has_afroep_line = bool(afroep_lines)
            order.can_reserve_afroep = order.state in (
                "draft",
                "sent",
            ) and any(
                line.afroep_reserve_product_id
                and not line._active_afroep_reservations()
                for line in afroep_lines
            )

    def action_reserve_afroep(self):
        """Create a stock reservation for every afroep line that needs one."""
        self.order_line._ensure_afroep_reservation()
        return True

    def _check_afroep_reservations(self):
        """Block confirmation when an afroep line has no active reservation."""
        for order in self:
            missing = order.order_line.filtered(
                lambda line: line.is_afroep_line
                and not line._active_afroep_reservations()
            )
            if missing:
                names = "\n".join(
                    "- %s" % line.product_id.display_name for line in missing
                )
                raise UserError(
                    _(
                        "This order has afroep (call-off) lines without a stock "
                        "reservation. Set a product to reserve and reserve the "
                        "stock before confirming:\n%s"
                    )
                    % names
                )

    def action_confirm(self):
        self._check_afroep_reservations()
        # Keep afroep reservations alive across confirmation; stock_reserve_sale
        # would otherwise release every reservation in action_confirm.
        return super(
            SaleOrder, self.with_context(keep_afroep_reservation=True)
        ).action_confirm()


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
        help="The storable product that is reserved in the warehouse for this "
        "afroep (call-off) line. Its stock is held until drawn down by later "
        "outgoing moves to the customer.",
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

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._ensure_afroep_reservation()
        return lines

    def write(self, vals):
        res = super().write(vals)
        # When a line gets an afroep product or its reserve product changes,
        # (re)synchronise the reservation.
        if "product_id" in vals or "afroep_reserve_product_id" in vals:
            self._ensure_afroep_reservation()
        return res

    def _ensure_afroep_reservation(self):
        """(Re)create the reservation for every afroep line that needs one."""
        if self.env.context.get(SKIP_AUTO_AFROEP):
            return
        for line in self:
            if line.is_afroep_line:
                line._sync_afroep_reservation()

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

    def _sync_afroep_reservation(self):
        """Ensure exactly one active reservation for the chosen reserve product.

        Releases a stale reservation if the reserve product changed, and creates
        a new one when none is active yet. Only acts on draft/sent quotations.
        """
        self.ensure_one()
        if not self.is_afroep_line:
            return self.env["stock.reservation"]
        reserve_product = self.afroep_reserve_product_id
        active = self._active_afroep_reservations()
        # Release reservations that no longer match the chosen reserve product.
        stale = active.filtered(lambda r: r.product_id != reserve_product)
        if stale:
            stale.release_reserve()
            active -= stale
        if not reserve_product or self.order_id.state not in ("draft", "sent"):
            return self.env["stock.reservation"]
        if active:
            return active
        reservation = self.env["stock.reservation"].create(
            self._prepare_afroep_reservation_vals()
        )
        reservation.reserve()
        return reservation

    def release_stock_reservation(self):
        """Do not release afroep reservations while confirming the order."""
        lines = self
        if self.env.context.get("keep_afroep_reservation"):
            lines = self.filtered(lambda line: not line.is_afroep_line)
        return super(SaleOrderLine, lines).release_stock_reservation()

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Afroep lines stay in stock: no delivery is procured on confirmation."""
        lines = self.filtered(lambda line: not line.is_afroep_line)
        return super(SaleOrderLine, lines)._action_launch_stock_rule(
            previous_product_uom_qty
        )
