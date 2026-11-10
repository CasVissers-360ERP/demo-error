# demo-error

Odoo 20 demo for Summit Distribution (Benelux distribution office for Nike tennis/padel and Nike SB skate,
working with sales agents per country). Follows the 360ERP repo structure
([360ERP/oca-addons-repo-template](https://github.com/360ERP/oca-addons-repo-template), Odoo 20.0).

| Path | Content |
|---|---|
| `custom/summit_sales` | Order type (At Once / Quickstrike / Futures) and season on sales orders, copied to the invoice. Seasons under Sales > Configuration. |
| `360_ai_client` | Submodule 360ERP/360_ai_client (20.0): Maatje (`ai_x360_client_install`). |

## Odoo.sh

Odoo.sh only puts the repository root and submodules on the addons path. Modules in `custom/` therefore have a
root symlink (`summit_sales -> custom/summit_sales`). New module: `ln -s custom/<module> <module>`.
The private submodule needs the Odoo.sh deploy key on 360ERP/360_ai_client.

## Pre-commit

```
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
