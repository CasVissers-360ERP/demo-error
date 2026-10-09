# Copyright 2026 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


{
    "name": "De Klerk - HR signalering",
    "summary": "Dagelijkse signalering: verjaardagen, jubilea, salariswijzigingen en verlopende certificaten",
    "description": """
Vult de standaard HR-signalering aan (aflopende contracten, automatiseringsregels voor proeftijd en
indiensttreding) met wat standaard niet kan omdat het jaarlijks terugkeert of versies vergelijkt:

* verjaardag binnen 7 dagen
* jubileum (12,5 / 25 / 40 jaar in dienst) binnen 30 dagen
* salariswijziging (nieuwe contractversie met ander salaris) binnen 30 dagen
* certificaat (vaardigheid van een certificeringstype) verloopt binnen 60 dagen

Elke signalering is een to-do activiteit op de medewerker voor de HR-verantwoordelijke.
""",
    "version": "20.0.1.0.1",
    "category": "Human Resources/Employees",
    "author": "360 ERP",
    "license": "LGPL-3",
    "depends": ["hr_skills"],
    "data": ["data/ir_cron.xml"],
    "installable": True,
}
