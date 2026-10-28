"""Shell for work-in-progress addons on boss20 (run by dev/server_shell_wip.sh inside the odoo container).

Loads the registry from the mounted WIP addons, then INSIDE ONE TRANSACTION (Postgres rolls DDL back too):
  1. creates the columns and tables of the models the WIP code adds or changes (registry.init_models);
  2. loads the XML of the BOSS modules (views, wizards, QWeb reports, menus, data) in update mode, so the views and
     the customer documents of the WIP code can be checked (arch, rendered PDF HTML);
  3. runs the script given on stdin with `env`, like `odoo shell`.
Nothing is committed: the database keeps the schema, views and data of the deployed code. Security CSV files are not
reloaded (access rules of the deployed code apply).
    python3 wip_bootstrap.py -c /etc/odoo/odoo.conf -d boss20 --addons-path=... --no-http --log-level=warn
"""
import ast
import os
import sys

sys.path.insert(0, "/opt/odoo-src")

import odoo  # noqa: E402
from odoo import api  # noqa: E402
from odoo.modules.registry import Registry  # noqa: E402
from odoo.service import server  # noqa: E402
from odoo.tools import config, convert_file  # noqa: E402

WIP_ADDONS = "/mnt/wip-addons"
STANDARD_MODELS = ("res.partner", "res.company", "res.users", "product.template", "product.product", "product.category",
                   "sale.order", "sale.order.line", "sale.order.template", "crm.lead", "res.config.settings",
                   "purchase.order", "purchase.order.line", "account.move", "account.move.line", "uom.uom",
                   "product.pricelist.item")

config.parse_config(sys.argv[1:], setup_logging=True)
server.start(preload=[], stop=True)
dbname = config["db_name"][0]
assert dbname == "boss20", dbname
registry = Registry(dbname)
with registry.cursor() as cr:
    names = [n for n in registry.models if n.startswith("boss.")] + [n for n in STANDARD_MODELS if n in registry.models]
    registry.init_models(cr, names, {"models_to_check": True}, install=False)
    env = api.Environment(cr, api.SUPERUSER_ID, {})
    loaded = []
    for module in sorted(os.listdir(WIP_ADDONS)):
        manifest = os.path.join(WIP_ADDONS, module, "__manifest__.py")
        if not module.startswith("boss_") or not os.path.exists(manifest):
            continue
        with open(manifest, encoding="utf-8") as fp:
            data = ast.literal_eval(fp.read()).get("data", [])
        for filename in data:
            if filename.endswith(".xml"):
                convert_file(env, module, filename, {}, mode="update")
                loaded.append(f"{module}/{filename}")
    env.flush_all()  # the writes of ir.ui.view already invalidated the view and template caches of this transaction
    print(f"WIP: schema synced for {len(names)} models, {len(loaded)} XML files loaded in the transaction")
    env = api.Environment(cr, api.SUPERUSER_ID, env["res.users"].context_get())
    local_vars = {"env": env, "odoo": odoo, "openerp": odoo, "self": env.user, "__name__": "__main__"}
    try:
        exec(sys.stdin.read(), local_vars)
    finally:
        cr.rollback()
