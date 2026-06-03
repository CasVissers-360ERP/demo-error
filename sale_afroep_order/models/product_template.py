# Copyright 2026 360ERP
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_afroep_product = fields.Boolean(
        string="Afroep Product",
        help="Sales lines with this product become call-off (afroep) lines: "
        "they require a stock reservation before the order can be confirmed, "
        "the goods stay in the warehouse instead of being delivered on "
        "confirmation, and the reservation is drawn down by any later "
        "outgoing stock move of the product to the customer.",
    )
