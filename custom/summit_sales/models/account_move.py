from odoo import fields, models

from .summit_season import ORDER_TYPES


class AccountMove(models.Model):
    _inherit = "account.move"

    summit_order_type = fields.Selection(ORDER_TYPES, string="Order Type", tracking=True)
    summit_season_id = fields.Many2one("summit.season", string="Season", tracking=True)
