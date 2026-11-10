# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Summit Sales: order type and season",
    "summary": "At Once / Quickstrike / Futures and season on sales orders and invoices",
    "author": "360 ERP",
    "website": "https://github.com/CasVissers-360ERP/demo-error",
    "version": "20.0.1.0.0",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": ["sale_management", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/summit_season_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
