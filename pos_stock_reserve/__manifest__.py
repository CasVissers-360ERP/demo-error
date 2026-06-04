# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "POS Stock Reservation",
    "summary": "Book (reserve) stock from a POS order line before completing the order",
    "version": "18.0.1.0.0",
    "author": "360ERP",
    "category": "Point of Sale",
    "license": "AGPL-3",
    "depends": ["point_of_sale", "stock_reserve"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_stock_reserve/static/src/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
}
