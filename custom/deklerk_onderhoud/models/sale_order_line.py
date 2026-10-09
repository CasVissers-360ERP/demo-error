# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .res_partner import DEFAULT_NORM_MINUTES_PER_UNIT, NORM_MINUTES_PER_UNIT


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    maintenance_type = fields.Selection(
        related="product_id.maintenance_type", store=True
    )
    maintenance_location_id = fields.Many2one(
        "res.partner",
        string="Onderhoudslocatie",
        domain="[('commercial_partner_id', '=', order_partner_commercial_id)]",
        index="btree_not_null",
        help="Adres waar het onderhoud plaatsvindt; de planningstool plant per locatie.",
    )
    order_partner_commercial_id = fields.Many2one(
        related="order_id.partner_id.commercial_partner_id"
    )
    visits_per_year = fields.Integer(
        string="Bezoeken p.j.",
        compute="_compute_visits_per_year",
        store=True,
        readonly=False,
        precompute=True,
    )
    norm_minutes_per_unit = fields.Float(
        string="Normtijd per VE (min)",
        compute="_compute_norm_minutes_per_unit",
        store=True,
        readonly=False,
        precompute=True,
        digits=(16, 2),
    )
    norm_hours_per_visit = fields.Float(
        string="Normtijd per bezoek (u)",
        compute="_compute_norm_hours_per_visit",
        store=True,
        digits=(16, 2),
        help="Aantal VE (hoeveelheid) x normtijd per VE.",
    )
    small_route = fields.Boolean(string="Kleine route")
    planning_note = fields.Text(
        string="Instructies planning",
        help="Bijv. openingstijden, watertappunt, toegang; wordt meegegeven aan de planningstool.",
    )

    @api.depends("product_id")
    def _compute_visits_per_year(self):
        for line in self:
            line.visits_per_year = line.product_id.visits_per_year

    @api.depends("order_id.partner_id.commercial_partner_id.abc_class", "product_id")
    def _compute_norm_minutes_per_unit(self):
        for line in self:
            abc = line.order_id.partner_id.commercial_partner_id.abc_class
            line.norm_minutes_per_unit = (
                NORM_MINUTES_PER_UNIT.get(abc, DEFAULT_NORM_MINUTES_PER_UNIT)
                if line.product_id.maintenance_type
                else 0.0
            )

    @api.depends("product_uom_qty", "norm_minutes_per_unit")
    def _compute_norm_hours_per_visit(self):
        for line in self:
            line.norm_hours_per_visit = (
                line.product_uom_qty * line.norm_minutes_per_unit / 60
            )

    @api.constrains("maintenance_location_id", "order_id")
    def _check_maintenance_location(self):
        for line in self.filtered("maintenance_location_id"):
            if (
                line.maintenance_location_id.commercial_partner_id
                != line.order_id.partner_id.commercial_partner_id
            ):
                raise ValidationError(
                    self.env._(
                        "Onderhoudslocatie %(location)s hoort niet bij klant %(customer)s.",
                        location=line.maintenance_location_id.display_name,
                        customer=line.order_id.partner_id.commercial_partner_id.display_name,
                    )
                )
