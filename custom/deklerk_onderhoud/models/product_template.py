# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models

MAINTENANCE_TYPES = [
    ("lease", "Lease"),
    ("vo", "VO"),
    ("to", "TO"),
    ("ho", "HO"),
    ("ko", "KO"),
    ("zijde", "Zijde onderhoud"),
    ("buitenbakken", "Buitenbakken"),
    ("groene_wand", "Groene wand"),
    ("kerst", "Kerst"),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    maintenance_type = fields.Selection(
        MAINTENANCE_TYPES, string="Contractvorm onderhoud"
    )
    visits_per_year = fields.Integer(
        string="Bezoeken per jaar",
        help="Standaardfrequentie; per contractregel aan te passen (bijv. zijde onderhoud 1x, 2x of 4x).",
    )
