# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAfroepOrder(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.config.settings"].create(
            {"group_stock_multi_locations": True}
        ).set_values()

        cls.partner = cls.env["res.partner"].create({"name": "Afroep Customer"})
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.stock_loc = cls.warehouse.lot_stock_id

        # The afroep "marker" product that is sold on the line (a service).
        cls.afroep_product = cls.env["product.product"].create(
            {
                "name": "Afroep",
                "type": "service",
                "is_afroep_product": True,
            }
        )
        # The storable product actually reserved in the warehouse.
        cls.reserve_product = cls.env["product.product"].create(
            {
                "name": "Steel Bolt M8",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.normal_product = cls.env["product.product"].create(
            {
                "name": "Normal Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        for product in (cls.reserve_product, cls.normal_product):
            cls.env["stock.quant"].create(
                {
                    "product_id": product.id,
                    "location_id": cls.stock_loc.id,
                    "quantity": 100.0,
                }
            )

    def _new_afroep_order(self, qty, reserve_product=None):
        """Order with one afroep line; reserve_product set unless overridden."""
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.afroep_product
            line.product_uom_qty = qty
            if reserve_product is not None:
                line.afroep_reserve_product_id = reserve_product
        return order_form.save()

    def _deliver(self, product, qty):
        """Create, force-done and validate an outgoing move to the customer."""
        move = self.env["stock.move"].create(
            {
                "name": product.display_name,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": qty,
                "location_id": self.stock_loc.id,
                "location_dest_id": self.customer_loc.id,
                "partner_id": self.partner.id,
                "picking_type_id": self.warehouse.out_type_id.id,
            }
        )
        move._action_confirm()
        move.quantity = qty
        move.picked = True
        move._action_done()
        return move

    def test_reservation_auto_created_for_reserve_product(self):
        order = self._new_afroep_order(30, reserve_product=self.reserve_product)
        self.assertTrue(order.order_line.is_afroep_line)
        reservation = order.order_line.reservation_ids
        self.assertEqual(len(reservation), 1)
        self.assertEqual(reservation.state, "assigned")
        # Reservation is for the chosen reserve product, not the afroep marker.
        self.assertEqual(reservation.product_id, self.reserve_product)
        self.assertEqual(reservation.product_uom_qty, 30)
        self.assertEqual(self.reserve_product.virtual_available, 70)

    def _new_afroep_order_orm(self, qty):
        """Build an afroep order without a reserve product, bypassing the form
        (the view requires the reserve product, but other code paths may not)."""
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.afroep_product.id,
                            "product_uom_qty": qty,
                        },
                    )
                ],
            }
        )

    def test_no_reservation_without_reserve_product(self):
        order = self._new_afroep_order_orm(30)
        self.assertFalse(order.order_line.reservation_ids)
        # Confirmation is blocked while no reserve product / reservation exists.
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_set_reserve_product_later_creates_reservation(self):
        order = self._new_afroep_order_orm(30)
        self.assertFalse(order.order_line.reservation_ids)
        order.order_line.afroep_reserve_product_id = self.reserve_product
        reservation = order.order_line.reservation_ids
        self.assertEqual(len(reservation), 1)
        self.assertEqual(reservation.product_id, self.reserve_product)

    def test_reserve_product_change_reservation(self):
        other = self.env["product.product"].create(
            {"name": "Steel Bolt M10", "type": "consu", "is_storable": True}
        )
        self.env["stock.quant"].create(
            {
                "product_id": other.id,
                "location_id": self.stock_loc.id,
                "quantity": 50.0,
            }
        )
        order = self._new_afroep_order(30, reserve_product=self.reserve_product)
        first = order.order_line.reservation_ids
        order.order_line.afroep_reserve_product_id = other
        # Old reservation released, a new one created for the new product.
        self.assertEqual(first.state, "cancel")
        active = order.order_line._active_afroep_reservations()
        self.assertEqual(len(active), 1)
        self.assertEqual(active.product_id, other)

    def test_confirm_persists_and_no_delivery(self):
        order = self._new_afroep_order(30, reserve_product=self.reserve_product)
        reservation = order.order_line.reservation_ids
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertEqual(reservation.state, "assigned")
        # No delivery is generated for the afroep line.
        self.assertFalse(order.picking_ids)

    def test_drawdown_reduces_reservation(self):
        order = self._new_afroep_order(30, reserve_product=self.reserve_product)
        order.action_confirm()
        reservation = order.order_line.reservation_ids
        self.assertEqual(reservation.product_uom_qty, 30)

        # The reserved product (not the afroep marker) is shipped to the customer.
        self._deliver(self.reserve_product, 12)

        self.assertEqual(reservation.state, "assigned")
        self.assertEqual(reservation.product_uom_qty, 18)

    def test_drawdown_full_releases(self):
        order = self._new_afroep_order(30, reserve_product=self.reserve_product)
        order.action_confirm()
        reservation = order.order_line.reservation_ids

        self._deliver(self.reserve_product, 30)

        self.assertEqual(reservation.state, "cancel")
