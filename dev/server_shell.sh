#!/usr/bin/env bash
# Run an odoo shell script from dev/ on the BOSS Odoo 20 server database (boss20; BOSS_DB=boss20_uat for the UAT copy), never Odoo 17/19.
#   dev/server_shell.sh <script.py> [private-data-file ...]
# The optional data files (real data, outside Git) are copied to a private folder, mounted read-only as
# /tmp/boss/<name> and deleted afterwards; the script receives their names in the environment variable BOSS_FILES
# (separated by "|") and must open exactly the file it expects. The script decides whether it commits or rolls back.
set -euo pipefail
cd "$(dirname "$0")/.."
SCRIPT="${1:?script}"
shift
HOST=boss@100.87.98.15
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST"
$SSH 'cd ~/BossOdoo20 && grep -qxF "db_name = boss20" config/odoo.conf && grep -qE "^dbfilter = \^boss20(\(_uat\)\?)?[$]$" config/odoo.conf \
      && docker compose ps --format "{{.Name}}" | grep -qx bossodoo20-odoo-1' \
  || { echo "Refusing: ~/BossOdoo20 is not the BOSS Odoo 20 environment"; exit 1; }
TMP=$($SSH 'mkdir -p ~/tmp && d=$(mktemp -d ~/tmp/boss-shell-XXXX) && chmod 755 $d && echo $d')
FILES=""
for DATA in "$@"; do
  NAME=$(basename "$DATA")
  $SSH "cat > '$TMP/$NAME' && chmod 644 '$TMP/$NAME'" < "$DATA"
  FILES="${FILES:+$FILES|}$NAME"
done
$SSH "cd ~/BossOdoo20 && docker compose run --rm -T -e BOSS_FILES='$FILES' -v $TMP:/tmp/boss:ro odoo shell \
      -c /etc/odoo/odoo.conf -d ${BOSS_DB:-boss20} --no-http --log-level=warn; rc=\$?; rm -rf $TMP; exit \$rc" < "dev/$SCRIPT"
