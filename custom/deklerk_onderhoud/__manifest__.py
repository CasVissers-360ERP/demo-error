# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


{
    "name": "De Klerk - Onderhoudscontracten",
    "summary": "Onderhoudsgegevens op de verkoopregel voor de externe planningstool",
    "description": """
Legt per contractregel vast wat de externe planningstool nodig heeft om onderhoud te plannen:
onderhoudslocatie, contractvorm, bezoeken per jaar, normtijd (via klantklasse A/B/C) en kleine route.
De planningstool meldt voltooide bezoeken terug als taak (met uniek bezoek-ID) + urenregel
op het project van het contract; zo ontstaat de marge per klant.

Daarnaast (uit het inrichtingsdocument, vervanging van Synergy-vrije velden en Orbis-taken):
* jaarlijkse indexatie van onderhoudscontracten met een percentage per klant (0 = geen indexatie),
  inclusief lease, met bescherming tegen dubbel indexeren;
* logistiek per locatie (openingstijden, lift/toegang CC-kar, laden en lossen) en de vaste onderhoudsmedewerker;
* contactrollen (aanmelden bezoek, CC werkbon, inkoopcontact, rol klantenportaal);
* PO-status op de offerte;
* bezoekrapport op de terugmelding van de planningstool (herkomst, bemesting, bestrijding, opmerkingen, handtekening).
""",
    "version": "20.0.1.1.0",
    "category": "Sales/Sales",
    "author": "360 ERP",
    "license": "LGPL-3",
    "depends": ["sale_project", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/indexation_wizard_views.xml",
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
}
