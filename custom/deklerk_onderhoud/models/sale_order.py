# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    po_status = fields.Selection(
        [
            ("received", "PO ontvangen"),
            ("pending", "PO volgt nog"),
            ("not_needed", "Geen PO nodig"),
        ],
        string="PO-status",
        tracking=True,
        help="'PO volgt nog' na bevestiging: na 14 dagen een herinnering voor de accountmanager.",
    )
