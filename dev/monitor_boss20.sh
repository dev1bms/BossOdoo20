#!/usr/bin/env bash
# Monitoring of the BOSS Odoo 20 server (go-live tracker P2-14). Installed as ~/bin/monitor_boss20.sh, cron every
# 10 minutes («check») and once a day («digest»). No mail server: the results go to a private status folder on the
# server (~/backups/boss20/status/) and, when a check fails, to an Odoo activity for Belal.
#   monitor_boss20.sh check | digest
set -uo pipefail
ROOT=~/backups/boss20
SITE=~/backups/boss20/status
LOG=$ROOT/monitor.log
mkdir -p "$ROOT" "$SITE"
NOW=$(date '+%F %T')
PROBLEMS=()

# 1. web answers
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -m 20 http://127.0.0.1:8020/web/health || echo 000)
[ "$HTTP" = 200 ] || PROBLEMS+=("web health $HTTP")
# 2. containers
for C in bossodoo20-odoo-1 bossodoo20-db-1; do
  docker ps --format '{{.Names}}' | grep -qx "$C" || PROBLEMS+=("container $C down")
done
# 3. disk and memory
DISK=$(df --output=pcent / | tail -1 | tr -dc '0-9')
[ "$DISK" -lt 85 ] || PROBLEMS+=("disk ${DISK}%")
MEMAVAIL=$(awk '/MemAvailable/ {printf "%d", $2/1024}' /proc/meminfo)
[ "$MEMAVAIL" -gt 300 ] || PROBLEMS+=("memory available ${MEMAVAIL} MB")
# 4. errors in the Odoo log, last 10 minutes
ERRORS=$(docker logs --since 10m bossodoo20-odoo-1 2>&1 | grep -cE ' ERROR | CRITICAL ' || true)
[ "$ERRORS" -lt 5 ] || PROBLEMS+=("$ERRORS errors in 10 min")
# 5. backup of today
ls "$ROOT"/daily/boss20_daily_$(date +%Y%m%d)_*.enc >/dev/null 2>&1 || [ "$(date +%H)" -lt 4 ] || PROBLEMS+=("no backup today")

STATUS=OK; [ ${#PROBLEMS[@]} -eq 0 ] || STATUS=PROBLEM
echo "$NOW $STATUS web=$HTTP disk=${DISK}% mem=${MEMAVAIL}MB errors10m=$ERRORS ${PROBLEMS[*]:-}" >> "$LOG"
cat > "$SITE/status.json" <<EOF
{"checked":"$NOW","status":"$STATUS","web":$HTTP,"disk_pct":$DISK,"mem_available_mb":$MEMAVAIL,"errors_10min":$ERRORS,"problems":"${PROBLEMS[*]:-}"}
EOF

if [ "${1:-check}" = digest ] || [ "$STATUS" = PROBLEM ]; then
  DAY=$(docker logs --since 24h bossodoo20-odoo-1 2>&1 | grep -E ' ERROR | CRITICAL ' | sed -E 's/^[0-9-]+ [0-9:,]+ [0-9]+ //' | cut -c1-160 | sort | uniq -c | sort -rn | head -15)
  {
    echo "<!doctype html><meta charset=utf-8><title>BOSS Odoo 20 · status</title>"
    echo "<style>body{font:14px system-ui;margin:24px;max-width:900px}pre{background:#f4f4f1;padding:12px;border-radius:8px;white-space:pre-wrap}.ok{color:#0a7f0a}.bad{color:#c00}</style>"
    echo "<h1>BOSS Odoo 20 · server status</h1><p>Checked $NOW · <b class=$([ $STATUS = OK ] && echo ok || echo bad)>$STATUS</b> ${PROBLEMS[*]:-}</p>"
    echo "<p>web /web/health: $HTTP · disk: ${DISK}% · memory available: ${MEMAVAIL} MB · errors last 10 min: $ERRORS</p>"
    echo "<h2>Errors in the last 24 h (count · message)</h2><pre>${DAY:-none}</pre>"
    echo "<h2>Last 30 checks</h2><pre>$(tail -30 "$LOG")</pre>"
    echo "<h2>Backups</h2><pre>$(tail -5 "$ROOT/backup.log" 2>/dev/null)</pre>"
  } > "$SITE/status.html"
fi

# an Odoo activity for Belal when something fails (at most one every 6 hours)
MARK=$ROOT/.monitor_alerted
if [ "$STATUS" = PROBLEM ] && { [ ! -f "$MARK" ] || [ $(( $(date +%s) - $(stat -c %Y "$MARK") )) -gt 21600 ]; }; then
  touch "$MARK"
  cd ~/BossOdoo20 && docker compose run --rm -T odoo shell -c /etc/odoo/odoo.conf -d boss20 --no-http --log-level=error <<PY >/dev/null 2>&1
user = env["res.users"].search([("login", "=", "balswerki@bidatia.com")], limit=1) or env.ref("base.user_admin")
env["mail.activity"].create({"res_model_id": env["ir.model"]._get_id("res.users"), "res_id": user.id, "user_id": user.id,
    "activity_type_id": env.ref("mail.mail_activity_data_todo").id, "summary": "Servidor boss20: ${PROBLEMS[*]:-}",
    "note": "monitor_boss20.sh $NOW: ${PROBLEMS[*]:-}. Detalle en ~/backups/boss20/status/status.html"})
env.cr.commit()
PY
fi
exit 0
