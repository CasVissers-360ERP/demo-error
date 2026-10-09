# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models

# Norm minutes per unit (VE) per customer class; A-customers get more attention per unit.
NORM_MINUTES_PER_UNIT = {"a": 4.0, "b": 3.2, "c": 2.5}
DEFAULT_NORM_MINUTES_PER_UNIT = NORM_MINUTES_PER_UNIT["b"]
YES_NO_UNKNOWN = [("yes", "Ja"), ("no", "Nee"), ("unknown", "Onbekend")]


class ResPartner(models.Model):
    _inherit = "res.partner"

    abc_class = fields.Selection(
        [("a", "A-klant"), ("b", "B-klant"), ("c", "C-klant")],
        string="Klantklasse",
        help="Bepaalt de normtijd per VE op onderhoudscontracten (A: 4,0 / B: 3,2 / C: 2,5 min per VE).",
    )
    maintenance_employee_id = fields.Many2one(
        "hr.employee",
        string="Onderhoudsmedewerker",
        help="Vaste onderhoudsmedewerker; de accountmanager is de verkoper van de klant.",
    )

    # indexation (on the customer; 0 = no indexation)
    indexation_pct = fields.Float(string="Indexatiepercentage", digits=(5, 2))
    last_indexation_date = fields.Date(
        string="Datum laatste indexatie", readonly=True, copy=False
    )

    # logistics per maintenance location
    opening_hours = fields.Char(string="Openingstijden")
    lift_cc_cart = fields.Selection(
        YES_NO_UNKNOWN, string="Lift groot genoeg voor CC-kar"
    )
    access_cc_cart = fields.Selection(YES_NO_UNKNOWN, string="Toegang pand met CC-kar")
    loading_info = fields.Text(string="Laad- en losmogelijkheden")

    # contact roles
    is_visit_contact = fields.Boolean(
        string="Aanmelden bezoek",
        help="Ontvangt de aanmelding van een onderhoudsbezoek.",
    )
    is_workorder_cc = fields.Boolean(
        string="CC werkbon", help="Ontvangt een kopie van de getekende werkbon."
    )
    is_purchase_contact = fields.Boolean(
        string="Inkoopcontact", help="Bij leveranciers: ontvangt de inkooporders."
    )
    portal_role = fields.Selection(
        [
            ("concierge", "Conciërge"),
            ("facility", "Facilitair manager"),
            ("contract", "Contract manager"),
        ],
        string="Rol klantenportaal",
    )
