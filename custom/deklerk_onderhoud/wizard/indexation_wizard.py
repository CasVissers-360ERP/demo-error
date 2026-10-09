# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from datetime import date

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import UserError

ACTIVE_STATES = ("3_progress", "4_paused")


class DeklerkIndexationWizard(models.TransientModel):
    """Yearly indexation of maintenance contracts: new price = price x (100 + customer %) / 100.

    Applies to all recurring lines (maintenance per VE and lease). A customer is indexed at most once per
    calendar year (last indexation date), and customers with 0 % are skipped.
    """

    _name = "deklerk.indexation.wizard"
    _description = "Indexatie onderhoudscontracten"

    def _default_date(self):
        today = fields.Date.context_today(self)
        return date(today.year if today.month == 1 else today.year + 1, 1, 1)

    def _default_order_ids(self):
        ids = (
            self.env.context.get("active_ids")
            if self.env.context.get("active_model") == "sale.order"
            else None
        )
        domain = [
            ("is_subscription", "=", True),
            ("subscription_state", "in", ACTIVE_STATES),
        ]
        if ids:
            domain.append(("id", "in", ids))
        return self.env["sale.order"].search(domain)

    indexation_date = fields.Date(
        string="Indexatiedatum", required=True, default=_default_date
    )
    order_ids = fields.Many2many(
        "sale.order",
        string="Contracten",
        default=_default_order_ids,
        domain=[
            ("is_subscription", "=", True),
            ("subscription_state", "in", ACTIVE_STATES),
        ],
    )
    result = fields.Html(string="Resultaat", readonly=True, sanitize=False)

    @api.model
    def _new_price(self, price, pct):
        return round(price * (100 + pct) / 100, 2)

    def action_apply(self):
        self.ensure_one()
        if not self.order_ids:
            raise UserError(
                self.env._("Geen actieve onderhoudscontracten geselecteerd.")
            )
        done, skipped = [], []
        indexed_partners = self.env["res.partner"]
        for partner, orders in self.order_ids.grouped(
            lambda o: o.partner_id.commercial_partner_id
        ).items():
            if not partner.indexation_pct:
                skipped.append(
                    self.env._("%s: indexatiepercentage 0", partner.display_name)
                )
                continue
            last = partner.last_indexation_date
            if last and last.year >= self.indexation_date.year:
                skipped.append(
                    self.env._(
                        "%(p)s: al geïndexeerd op %(d)s",
                        p=partner.display_name,
                        d=last.strftime("%d-%m-%Y"),
                    )
                )
                continue
            for order in orders:
                lines = order.order_line.filtered(
                    lambda sol: not sol.display_type
                    and sol.product_id.recurring_invoice
                    and sol.price_unit
                )
                rows = []
                for line in lines:
                    old = line.price_unit
                    line.price_unit = self._new_price(old, partner.indexation_pct)
                    rows.append(
                        Markup("<li>%s: € %.2f → € %.2f</li>")
                        % (line.name.split("\n")[0], old, line.price_unit)
                    )
                order.message_post(
                    body=Markup("<p><b>%s</b></p><ul>%s</ul>")
                    % (
                        self.env._(
                            "Indexatie %(pct)s%% per %(d)s",
                            pct=partner.indexation_pct,
                            d=self.indexation_date.strftime("%d-%m-%Y"),
                        ),
                        Markup("").join(rows),
                    )
                )
                done.append(
                    self.env._(
                        "%(o)s (%(p)s): %(n)s regels +%(pct)s%%",
                        o=order.name,
                        p=partner.display_name,
                        n=len(lines),
                        pct=partner.indexation_pct,
                    )
                )
            indexed_partners |= partner
        indexed_partners.last_indexation_date = self.indexation_date
        self.result = Markup(
            "<p><b>%s</b></p><ul>%s</ul><p><b>%s</b></p><ul>%s</ul>"
        ) % (
            self.env._("Geïndexeerd"),
            Markup("").join(Markup("<li>%s</li>") % escape(d) for d in done)
            or Markup("<li>-</li>"),
            self.env._("Overgeslagen"),
            Markup("").join(Markup("<li>%s</li>") % escape(s) for s in skipped)
            or Markup("<li>-</li>"),
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
