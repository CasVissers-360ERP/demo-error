# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import tagged

from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon


@tagged("post_install", "-at_install")
class TestPosStockReserve(TestPointOfSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.pos_config.warehouse_id
        cls.stock_loc = cls.pos_config.picking_type_id.default_location_src_id

        cls.book_product = cls.env["product.product"].create(
            {
                "name": "Bookable Product",
                "type": "consu",
                "is_storable": True,
                "available_in_pos": True,
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.book_product.id,
                "location_id": cls.stock_loc.id,
                "quantity": 100.0,
            }
        )

    def setUp(self):
        super().setUp()
        self.pos_config.open_ui()
        self.session = self.pos_config.current_session_id
        if self.session.state != "opened":
            self.session.set_opening_control(0, None)

    def test_book_creates_reservation(self):
        res = self.session.book_stock_line(
            "line-uuid-1", "order-uuid-1", self.book_product.id, 10.0
        )
        reservation = self.env["stock.reservation"].browse(res["reservation_id"])
        self.assertTrue(reservation.exists())
        self.assertEqual(res["state"], "assigned")
        self.assertEqual(reservation.product_id, self.book_product)
        self.assertEqual(reservation.product_uom_qty, 10.0)
        self.assertEqual(reservation.location_id, self.stock_loc)
        self.assertEqual(reservation.pos_order_uuid, "order-uuid-1")
        self.assertEqual(reservation.pos_line_uuid, "line-uuid-1")
        self.assertEqual(self.book_product.virtual_available, 90.0)

    def test_book_is_idempotent_per_line(self):
        first = self.session.book_stock_line(
            "line-uuid-2", "order-uuid-2", self.book_product.id, 5.0
        )
        second = self.session.book_stock_line(
            "line-uuid-2", "order-uuid-2", self.book_product.id, 5.0
        )
        self.assertEqual(first["reservation_id"], second["reservation_id"])
        reservations = self.env["stock.reservation"].search(
            [("pos_line_uuid", "=", "line-uuid-2")]
        )
        self.assertEqual(len(reservations), 1)

    def test_unbook_releases_reservation(self):
        res = self.session.book_stock_line(
            "line-uuid-3", "order-uuid-3", self.book_product.id, 8.0
        )
        reservation = self.env["stock.reservation"].browse(res["reservation_id"])
        self.assertEqual(self.book_product.virtual_available, 92.0)

        self.session.unbook_stock_line("line-uuid-3")

        self.assertEqual(reservation.state, "cancel")
        self.assertEqual(self.book_product.virtual_available, 100.0)

    def test_release_on_order_completion(self):
        order_uuid = "order-uuid-4"
        res = self.session.book_stock_line(
            "line-uuid-4", order_uuid, self.book_product.id, 12.0
        )
        reservation = self.env["stock.reservation"].browse(res["reservation_id"])
        self.assertEqual(reservation.state, "assigned")

        # Simulate the server-side completion hook: an order carrying that uuid.
        order = self.env["pos.order"].create(
            {
                "session_id": self.session.id,
                "uuid": order_uuid,
                "amount_total": 0.0,
                "amount_tax": 0.0,
                "amount_paid": 0.0,
                "amount_return": 0.0,
            }
        )
        order._release_pos_stock_bookings()

        self.assertEqual(reservation.state, "cancel")
        self.assertEqual(self.book_product.virtual_available, 100.0)
