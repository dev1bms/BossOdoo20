#!/usr/bin/env bash
# Run Odoo tests on the BOSS server (boss20 is the testing server; no Odoo runs on the local machine, Belal 26/10/2026).
#   dev/server_test.sh boss_expediente            tests of one module (dependencies installed, their tests not run)
#   dev/server_test.sh boss_pricing,boss_pricing_sale,boss_expediente
# The committed HEAD of addons/ goes to a temporary folder; a throw-away database boss20_test_<time> is created,
# tested and dropped. The boss20 database, its addons folder and the running web are never touched.
#   dev/server_test.sh --engine                   pure-Python engine tests of boss_pricing (never run locally either)
set -euo pipefail
cd "$(dirname "$0")/.."
MODULES="${1:?modules}"
if [ "$MODULES" = "--engine" ]; then
  git archive --format=tar HEAD addons/boss_pricing | ssh -o BatchMode=yes -o ConnectTimeout=15 boss@100.87.98.15     'set -e; D=$(mktemp -d ~/tmp/boss-engine-XXXX); tar -x -C $D --strip-components=1; chmod -R a+rX $D;
     cd ~/BossOdoo20 && docker compose run --rm -T -v $D:/mnt/engine:ro --entrypoint python3 odoo        -m unittest discover -s /mnt/engine/boss_pricing/engine/tests -t /mnt/engine/boss_pricing 2>&1 | tail -4;
     rm -rf $D'
  exit 0
fi
TAGS=$(echo "$MODULES" | sed 's/[^,]*/\/&/g')
HOST=boss@100.87.98.15
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST"
$SSH 'cd ~/BossOdoo20 && grep -qxF "db_name = boss20" config/odoo.conf && docker compose ps --format "{{.Name}}" | grep -qx bossodoo20-odoo-1' \
  || { echo "Refusing: ~/BossOdoo20 is not the BOSS Odoo 20 environment"; exit 1; }
[ -z "$(git status --porcelain -- addons)" ] || { echo "Refusing: uncommitted changes in addons/"; exit 1; }
git archive --format=tar HEAD addons | $SSH 'set -e; rm -rf ~/tmp/boss-test-addons; mkdir -p ~/tmp/boss-test-addons;
  tar -x -C ~/tmp/boss-test-addons --strip-components=1; chmod -R a+rX ~/tmp/boss-test-addons'
$SSH "cd ~/BossOdoo20 && DB=boss20_test_\$(date +%H%M%S) && LOG=~/tmp/test_\$DB.log && \
  (docker compose run --rm -T -v ~/tmp/boss-test-addons:/mnt/extra-addons:ro odoo -c /etc/odoo/odoo.conf -d \$DB \
     -i $MODULES --test-enable --test-tags '$TAGS' --stop-after-init --no-http --log-level=test < /dev/null > \$LOG 2>&1; \
   echo \"exit \$?\" >> \$LOG); \
  docker compose exec -T db dropdb -U odoo --if-exists \$DB; rm -rf ~/BossOdoo20/filestore/\$DB 2>/dev/null; \
  grep -E 'odoo.tests.result|FAIL:|ERROR: ' \$LOG | tail -8; tail -1 \$LOG; echo log: \$LOG"
