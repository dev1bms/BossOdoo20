#!/usr/bin/env bash
# Persistent UAT database on the BOSS server: boss20_uat, same code and settings as boss20, fictitious [DEMO] data,
# external connections off (no crons, no mail server, online services to a closed port). Used for the accounting
# cycle (posting, payments) that must never touch boss20. Never dropped by dev/server_test.sh (own name).
#   dev/server_uat.sh build      create boss20_uat, install the modules, seed it, allow it in dbfilter, restart Odoo
#   dev/server_uat.sh seed       re-run the seed scripts only (idempotent)
#   dev/server_uat.sh update <modules>   update modules on boss20_uat after a deploy (dev/deploy.sh updates boss20 only)
# Access: https://system.bosscontinental.com/web?db=boss20_uat (fictitious company, users of the seed).
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=boss@100.87.98.15
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST"
MODULES="boss_expediente,accountant,l10n_es_reports,contacts"
SEED="uat_isolate local_chart local_lang_es setup_vat_mapping server_trial local_demo_suppliers demo_meeting demo_cycle
      setup_decisions_2310 setup_suplidos_accounts uat_customers uat_users setup_templates uat_isolate"
case "${1:-}" in
  build)
    $SSH "cd ~/BossOdoo20 && LOG=~/tmp/uat_build_\$(date +%Y%m%d_%H%M%S).log && \
      docker compose run --rm -T odoo -c /etc/odoo/odoo.conf -d boss20_uat -i $MODULES --without-demo \
        --load-language=es_ES --stop-after-init --no-http --log-level=warn < /dev/null > \$LOG 2>&1; \
      echo \"exit \$?\" >> \$LOG; tail -2 \$LOG"
    "$0" seed
    $SSH 'cd ~/BossOdoo20 && grep -q "^dbfilter = ^boss20(_uat)?\$" config/odoo.conf \
      || sed -i "s/^dbfilter = .*/dbfilter = ^boss20(_uat)?\$/" config/odoo.conf; grep "^dbfilter" config/odoo.conf; \
      docker compose restart odoo >/dev/null 2>&1; sleep 25; docker compose ps --format "{{.Name}} {{.Status}}" | grep odoo-1'
    ;;
  seed)
    for script in $SEED; do echo "== $script"; BOSS_DB=boss20_uat bash dev/server_shell.sh "$script.py" 2>&1 \
      | grep -vE "WARNING|Container|^$" | tail -4; done
    ;;
  update)
    $SSH "cd ~/BossOdoo20 && docker compose run --rm -T odoo -c /etc/odoo/odoo.conf -d boss20_uat -u ${2:?modules} \
      --stop-after-init --no-http --log-level=warn < /dev/null 2>&1 | grep -E 'ERROR|CRITICAL' | head -3; echo updated"
    ;;
  *) sed -n '2,9p' "$0"; exit 2;;
esac
