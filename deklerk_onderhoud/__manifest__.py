{
    "name": "De Klerk - Onderhoudscontracten",
    "summary": "Onderhoudsgegevens op de verkoopregel voor de externe planningstool",
    "description": """
Legt per contractregel vast wat de externe planningstool nodig heeft om onderhoud te plannen:
onderhoudslocatie, contractvorm, bezoeken per jaar, normtijd (via klantklasse A/B/C) en kleine route.
De planningstool meldt voltooide bezoeken terug als taak (met uniek bezoek-ID) + urenregel
op het project van het contract; zo ontstaat de marge per klant.
""",
    "version": "20.0.1.0.0",
    "category": "Sales/Sales",
    "author": "360 ERP",
    "license": "LGPL-3",
    "depends": ["sale_project"],
    "data": [
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
}
