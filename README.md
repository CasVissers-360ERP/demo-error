# demo-error

Odoo 20 maatwerk voor de De Klerk demo, ingericht volgens de 360ERP-repostructuur
([360ERP/oca-addons-repo-template](https://github.com/360ERP/oca-addons-repo-template), Odoo 20.0).

| Map | Inhoud |
|---|---|
| `custom/deklerk_onderhoud` | Onderhoudsgegevens op de contractregel voor de externe planningstool (locatie, contractvorm, bezoeken p.j., normtijd via klantklasse A/B/C, kleine route), uniek bezoek-ID + bezoekrapport op taken, jaarlijkse indexatie per klant, logistiek per locatie, contactrollen, PO-status. |
| `custom/deklerk_hr` | Dagelijkse HR-signalering: verjaardagen, jubilea (12,5/25/40 jaar), salariswijzigingen, verlopende certificaten. |

## Pre-commit

```
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
