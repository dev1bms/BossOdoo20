#!/usr/bin/env bash
# Run a UAT check script on the server and keep its output as evidence tied to the tested commit.
#   dev/uat_run.sh <script.py> [boss20_uat|boss20]
# The script prints «CHECK PASS|FAIL <name>: expected … got …» lines and a final «RESULT n passed, m failed».
# Evidence: docs/evidencias/<date>_<script>_<db>_<commit>.txt with the commit tested (HEAD, must be pushed and deployed),
# the module versions installed in that database and the full output. Exit status = the script's (failures -> 1).
set -euo pipefail
cd "$(dirname "$0")/.."
SCRIPT="${1:?script}"
DB="${2:-boss20_uat}"
COMMIT=$(git rev-parse --short=12 HEAD)
[ -z "$(git status --porcelain -- addons)" ] || { echo "Refusing: uncommitted changes in addons/"; exit 1; }
[ "$(git rev-parse HEAD)" = "$(git rev-parse '@{u}')" ] || { echo "Refusing: HEAD not pushed"; exit 1; }
mkdir -p docs/evidencias
OUT="docs/evidencias/$(date +%Y%m%d_%H%M)_${SCRIPT%.py}_${DB}_${COMMIT}.txt"
VERSIONS=$(ssh -o BatchMode=yes boss@100.87.98.15 "docker exec bossodoo20-db-1 psql -U odoo -d $DB -Atc \
  \"select name||' '||latest_version from ir_module_module where name like 'boss%' and state='installed' order by 1\"" | tr '\n' ' ')
{
  echo "# Evidence: dev/$SCRIPT on $DB"
  echo "# Date: $(date '+%Y-%m-%d %H:%M %Z')"
  echo "# Commit tested: $COMMIT ($(git log -1 --format=%s | cut -c1-100))"
  echo "# Installed on $DB: $VERSIONS"
  echo
} > "$OUT"
set +e
BOSS_DB="$DB" bash dev/server_shell.sh "$SCRIPT" 2>&1 | grep -vE "^WARNING|Container .* (Creating|Created|Starting|Started)|^$" >> "$OUT"
RC=${PIPESTATUS[0]}
set -e
echo "# Exit status: $RC" >> "$OUT"
grep -E "^CHECK FAIL|^RESULT" "$OUT" || true
echo "evidence: $OUT"
exit "$RC"
