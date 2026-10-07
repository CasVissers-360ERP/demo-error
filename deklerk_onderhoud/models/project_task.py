from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    planning_visit_ref = fields.Char(
        string="Bezoek-ID planningstool",
        copy=False,
        index="btree_not_null",
        help="Uniek ID waarmee de planningstool een voltooid bezoek terugmeldt; voorkomt dubbele taken.",
    )

    _planning_visit_ref_uniq = models.Constraint(
        "unique (planning_visit_ref)",
        "Dit bezoek-ID van de planningstool bestaat al.",
    )
