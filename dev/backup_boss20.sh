#!/usr/bin/env bash
# Encrypted backup of the BOSS Odoo 20 production database and filestore, kept on the server (tracker P1-16,
# exception to the «no backups» rule approved by Belal on 05/11/2026 for databases that hold real data).
#   backup_boss20.sh [daily|predeploy]      (installed on the server as ~/bin/backup_boss20.sh; cron runs «daily»)
# Layout: ~/backups/boss20/{daily,weekly,monthly,predeploy}/boss20_<tag>_<timestamp>.tar.gz.enc + .sha256
# Retention: 7 daily, 4 weekly (Sunday copy), 12 monthly (first-of-month copy), 5 predeploy.
# Encryption: AES-256-CBC (PBKDF2) with the key file ~/backups/boss20/.key — keep a copy of that key in the password
# manager: without it the backups cannot be read. Decrypt and list:
#   openssl enc -d -aes-256-cbc -pbkdf2 -pass file:$HOME/backups/boss20/.key -in <file> | tar -tzf - | head
set -euo pipefail
TAG="${1:-daily}"
ROOT=~/backups/boss20
COMPOSE=~/BossOdoo20/compose.yml
KEY=$ROOT/.key
TS=$(date +%Y%m%d_%H%M%S)
LOG=$ROOT/backup.log
mkdir -p "$ROOT"/{daily,weekly,monthly,predeploy}
umask 077
[ -s "$KEY" ] || { openssl rand -hex 32 > "$KEY"; echo "$(date '+%F %T') new key file $KEY: save it in the password manager" >> "$LOG"; }
TMP=$(mktemp -d "$ROOT/.tmp_XXXX")
trap 'rm -rf "$TMP"' EXIT

docker compose -f "$COMPOSE" exec -T db pg_dump -U odoo -Fc boss20 > "$TMP/boss20.dump"
docker cp bossodoo20-odoo-1:/var/lib/odoo/filestore/boss20 "$TMP/filestore"
cat > "$TMP/MANIFEST.txt" <<EOF
database: boss20 (pg_dump custom format, PostgreSQL 16)
filestore: /var/lib/odoo/filestore/boss20
taken: $(date '+%F %T %Z') tag $TAG host $(hostname)
version: $(cat ~/BossOdoo20/VERSION 2>/dev/null || echo unknown)
restore: pg_restore -U odoo -d <newdb> boss20.dump ; copy filestore/ to /var/lib/odoo/filestore/<newdb>
EOF

case "$TAG" in daily) DIR=$ROOT/daily;; predeploy) DIR=$ROOT/predeploy;; *) echo "tag: daily|predeploy"; exit 2;; esac
OUT="$DIR/boss20_${TAG}_$TS.tar.gz.enc"
tar -C "$TMP" -cf - . | gzip -6 | openssl enc -aes-256-cbc -pbkdf2 -salt -pass "file:$KEY" -out "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
# integrity: the archive decrypts and lists
openssl enc -d -aes-256-cbc -pbkdf2 -pass "file:$KEY" -in "$OUT" | tar -tzf - > /dev/null

if [ "$TAG" = daily ]; then
  [ "$(date +%u)" = 7 ] && cp "$OUT" "$OUT.sha256" "$ROOT/weekly/"
  [ "$(date +%d)" = 01 ] && cp "$OUT" "$OUT.sha256" "$ROOT/monthly/"
fi
prune() { (ls -1t "$1"/*.enc 2>/dev/null || true) | tail -n +"$(( $2 + 1 ))" | while read -r f; do rm -f "$f" "$f.sha256"; done; }
prune "$ROOT/daily" 7; prune "$ROOT/weekly" 4; prune "$ROOT/monthly" 12; prune "$ROOT/predeploy" 5
echo "$(date '+%F %T') OK $TAG $(du -h "$OUT" | cut -f1) $OUT" >> "$LOG"
echo "OK $OUT"
