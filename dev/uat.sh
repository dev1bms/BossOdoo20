#!/usr/bin/env bash
# Isolated, persistent UAT copy for the meetings (local Docker, project boss20uat, DB boss_uat, http://localhost:8070).
# Fictitious [DEMO] data only; nothing leaves the machine (no crons, SMTP and HTTP(S) to a closed port). dev/test.sh
# never touches it (other compose project and volumes).
#   dev/uat.sh build     create boss_uat like boss20 (modules, Spanish chart, VAT table, [DEMO] cycle, templates)
#   dev/uat.sh shell <script>   run an odoo shell script from dev/ on boss_uat
#   dev/uat.sh serve     serve on http://localhost:8070 (stop: dev/uat.sh stop)
#   dev/uat.sh update <modules>  update modules after a deploy of new code
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1
DC="docker compose -f compose.uat.yml"
ARGS="--db_host=db --db_user=odoo --db_password=odoo --data-dir=/var/lib/odoo
      --addons-path=/opt/odoo-src/odoo/addons,/mnt/extra-addons"
CONF="printf '[options]\ndb_host=db\ndb_user=odoo\ndb_password=odoo\naddons_path=/opt/odoo-src/odoo/addons,/mnt/extra-addons\ndata_dir=/var/lib/odoo\n' > /tmp/t.conf"
case "${1:-}" in
  build)
    $DC up -d db
    $DC run --rm -T odoo $ARGS -d boss_uat -i boss_expediente,accountant,l10n_es_reports,contacts \
      --load-language=es_ES --without-demo=all --stop-after-init --log-level=warn
    for script in uat_isolate local_chart local_lang_es setup_vat_mapping server_trial local_demo_suppliers \
                  demo_meeting demo_cycle setup_decisions_2310 uat_customers setup_templates uat_isolate; do
      echo "== $script"; bash ./uat.sh shell "$script.py"
    done
    ;;
  shell)
    $DC run --rm -T -v "$(pwd):/mnt/dev:ro" -e BOSS_UAT=1 --entrypoint sh odoo -c "$CONF && python3 /opt/odoo-src/setup/odoo shell -c /tmp/t.conf -d boss_uat --no-http < /mnt/dev/${2:?script}"
    ;;
  update)
    docker rm -f boss20uat-web >/dev/null 2>&1 || true
    $DC run --rm -T odoo $ARGS -d boss_uat -u "${2:?modules}" --stop-after-init --log-level=warn
    ;;
  serve)
    $DC run -d --rm --name boss20uat-web -p 127.0.0.1:8070:8069 odoo $ARGS -d boss_uat --db-filter=^boss_uat$ \
      --http-port=8069 --max-cron-threads=0 --smtp=127.0.0.1 --smtp-port=9
    ;;
  stop)
    docker rm -f boss20uat-web >/dev/null 2>&1 || true
    ;;
  *)
    sed -n '2,9p' "$0"
    exit 2
    ;;
esac
