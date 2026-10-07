from odoo import fields, models

# Norm minutes per unit (VE) per customer class; A-customers get more attention per unit.
NORM_MINUTES_PER_UNIT = {"a": 4.0, "b": 3.2, "c": 2.5}
DEFAULT_NORM_MINUTES_PER_UNIT = NORM_MINUTES_PER_UNIT["b"]


class ResPartner(models.Model):
    _inherit = "res.partner"

    abc_class = fields.Selection(
        [("a", "A-klant"), ("b", "B-klant"), ("c", "C-klant")],
        string="Klantklasse",
        help="Bepaalt de normtijd per VE op onderhoudscontracten (A: 4,0 / B: 3,2 / C: 2,5 min per VE).",
    )
