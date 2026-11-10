from odoo import fields, models

ORDER_TYPES = [
    ("at_once", "At Once"),
    ("quickstrike", "Quickstrike"),
    ("futures", "Futures"),
]


class SummitSeason(models.Model):
    _name = "summit.season"
    _description = "Season"
    _order = "date_start desc"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Short code, e.g. SP27")
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint("UNIQUE(code)", "The season code must be unique.")
