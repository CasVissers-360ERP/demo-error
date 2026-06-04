# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockReservation(models.Model):
    _inherit = "stock.reservation"

    pos_order_uuid = fields.Char(
        string="POS Order UUID",
        index=True,
        copy=False,
        help="UUID of the in-progress POS order this stock was booked for.",
    )
    pos_line_uuid = fields.Char(
        string="POS Order Line UUID",
        index=True,
        copy=False,
        help="UUID of the POS order line this stock was booked for.",
    )
