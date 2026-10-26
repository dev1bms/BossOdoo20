#!/usr/bin/env bash
# Deploy the committed BOSS addons to the Odoo 20 environment (never Odoo 17/19).
#   dev/deploy.sh install boss_services,boss_pricing,boss_pricing_sale
#   dev/deploy.sh update  boss_pricing_sale
# Target: boss@100.87.98.15:~/BossOdoo20 (compose project bossodoo20, DB boss20, system.bosscontinental.com).
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:?install|update}"
MODULES="${2:?modules}"
HOST=boss@100.87.98.15
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST"

# 1. Identity of the environment, checked every time.
$SSH 'cd ~/BossOdoo20 && grep -qxF "db_name = boss20" config/odoo.conf && grep -qE "^dbfilter = \^boss20(\(_uat\)\?)?[$]$" config/odoo.conf \
      && docker compose ps --format "{{.Name}}" | grep -qx bossodoo20-odoo-1' \
  || { echo "Refusing to deploy: ~/BossOdoo20 is not the BOSS Odoo 20 environment"; exit 1; }
[ -z "$(git status --porcelain -- addons)" ] || { echo "Refusing to deploy: uncommitted changes in addons/"; exit 1; }

# 2. Ship the committed addons (only boss_* folders are ours in ~/BossOdoo20/addons).
git archive --format=tar HEAD addons | $SSH 'set -e; cd ~/BossOdoo20; rm -rf /tmp/boss-addons; mkdir /tmp/boss-addons;
  tar -x -C /tmp/boss-addons; for d in /tmp/boss-addons/addons/boss_*; do rm -rf "addons/$(basename "$d")"; cp -r "$d" addons/; done;
  rm -rf /tmp/boss-addons; ls addons'

# 3. Install or update with the web stopped (RAM is shared with Odoo 19), then start it again.
FLAG=$([ "$MODE" = install ] && echo "-i" || echo "-u")
$SSH "cd ~/BossOdoo20 && LOG=deploy_\$(date +%Y%m%d_%H%M%S).log && docker compose stop odoo >/dev/null 2>&1 \
  && (docker compose run --rm -T odoo -c /etc/odoo/odoo.conf -d boss20 $FLAG $MODULES --stop-after-init --no-http \
      < /dev/null > \$LOG 2>&1; echo \"exit \$?\" >> \$LOG); docker compose start odoo >/dev/null 2>&1; \
  grep -E 'ERROR|CRITICAL|Traceback' \$LOG | head -5; tail -2 \$LOG; echo log: ~/BossOdoo20/\$LOG"
$SSH "cd ~/BossOdoo20 && docker compose exec -T db psql -U odoo -d boss20 -Atc \
  \"select name, state, latest_version from ir_module_module where name like 'boss%' order by name\""
