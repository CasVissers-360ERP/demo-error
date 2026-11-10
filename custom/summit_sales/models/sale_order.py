from odoo import fields, models

from .summit_season import ORDER_TYPES


class SaleOrder(models.Model):
    _inherit = "sale.order"

    summit_order_type = fields.Selection(
        ORDER_TYPES,
        string="Order Type",
        default="at_once",
        required=True,
        tracking=True,
        help="At Once: from stock. Quickstrike: limited release. "
        "Futures: pre-booked for a coming season.",
    )
    summit_season_id = fields.Many2one("summit.season", string="Season", tracking=True)

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        values.update(
            summit_order_type=self.summit_order_type,
            summit_season_id=self.summit_season_id.id,
        )
        return values
