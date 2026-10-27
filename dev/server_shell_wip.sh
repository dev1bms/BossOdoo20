#!/usr/bin/env bash
# Run an odoo shell script from dev/ on boss20 with the LOCAL, UNCOMMITTED addons (work in progress) mounted from a
# private folder on the server, without touching ~/BossOdoo20/addons nor the running web (no deploy, no restart, no
# module update: only Python-level changes can be tried this way; new fields or views need a real deploy).
#   dev/server_shell_wip.sh <script.py> [private-data-file ...]
set -euo pipefail
cd "$(dirname "$0")/.."
SCRIPT="${1:?script}"
shift
HOST=boss@100.87.98.15
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST"
$SSH 'cd ~/BossOdoo20 && grep -qxF "db_name = boss20" config/odoo.conf && docker compose ps --format "{{.Name}}" | grep -qx bossodoo20-odoo-1' \
  || { echo "Refusing: ~/BossOdoo20 is not the BOSS Odoo 20 environment"; exit 1; }
TMP=$($SSH 'mkdir -p ~/tmp && d=$(mktemp -d ~/tmp/boss-wip-XXXX) && chmod 755 $d && mkdir $d/addons $d/data && echo $d')
tar -c -C addons $(ls addons | grep '^boss_') | $SSH "tar -x -C $TMP/addons && chmod -R a+rX $TMP/addons"
FILES=""
for DATA in "$@"; do
  NAME=$(basename "$DATA")
  $SSH "cat > '$TMP/data/$NAME' && chmod 644 '$TMP/data/$NAME'" < "$DATA"
  FILES="${FILES:+$FILES|}$NAME"
done
$SSH "cd ~/BossOdoo20 && docker compose run --rm -T -e BOSS_FILES='$FILES' -v $TMP/addons:/mnt/wip-addons:ro -v $TMP/data:/tmp/boss:ro odoo shell \
      -c /etc/odoo/odoo.conf -d boss20 --addons-path=/opt/odoo-src/odoo/addons,/mnt/wip-addons --no-http --log-level=warn; rc=\$?; rm -rf $TMP; exit \$rc" < "dev/$SCRIPT"
