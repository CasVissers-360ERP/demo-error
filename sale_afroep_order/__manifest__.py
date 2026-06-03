# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Afroep (Call-off) Order",
    "summary": "Sell call-off (afroep) products that stay reserved in the warehouse "
    "and are drawn down by later stock moves",
    "version": "18.0.1.1.0",
    "author": "360ERP",
    "category": "Sales/Warehouse",
    "license": "AGPL-3",
    "depends": ["stock_reserve_sale"],
    "data": [
        "views/product_views.xml",
        "views/sale_order_views.xml",
    ],
    "demo": [
        "demo/product_demo.xml",
    ],
    "installable": True,
    "auto_install": False,
}
