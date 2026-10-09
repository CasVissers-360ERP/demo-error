# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    planning_visit_ref = fields.Char(
        string="Bezoek-ID planningstool",
        copy=False,
        index="btree_not_null",
        help="Uniek ID waarmee de planningstool een voltooid bezoek terugmeldt; voorkomt dubbele taken.",
    )

    # visit report, filled by the planning tool when it reports the visit as done
    visit_origin = fields.Selection(
        [
            ("periodic", "Periodiek onderhoud"),
            ("water_check", "Controle watergeefbeurt"),
            ("manual", "Handmatig / ad hoc"),
        ],
        string="Herkomst bezoek",
    )
    visit_fertilized = fields.Boolean(string="Bemest")
    visit_pest_control = fields.Boolean(string="Ongedierte bestreden")
    visit_remarks = fields.Text(string="Bijzonderheden bezoek")
    visit_signed_by = fields.Char(string="Afgetekend door")
    visit_signature = fields.Binary(
        string="Handtekening klant", attachment=True, copy=False
    )

    _planning_visit_ref_uniq = models.Constraint(
        "unique (planning_visit_ref)",
        "Dit bezoek-ID van de planningstool bestaat al.",
    )
