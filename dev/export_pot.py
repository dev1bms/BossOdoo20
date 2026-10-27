"""Print the translation templates (.pot) of the BOSS modules from boss20, between markers, so that po_merge.py can
update i18n/es.po without running Odoo locally (policy 27/10/2026).
    dev/server_shell.sh export_pot.py > out.txt"""
import io

from odoo.tools.translate import trans_export

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
for module in ("boss_services", "boss_pricing", "boss_pricing_sale", "boss_expediente"):
    buffer = io.BytesIO()
    trans_export(False, [module], buffer, "po", env)  # noqa: F821
    print(f"=====POT {module}")
    print(buffer.getvalue().decode("utf-8"))
    print(f"=====END {module}")
env.cr.rollback()  # noqa: F821
