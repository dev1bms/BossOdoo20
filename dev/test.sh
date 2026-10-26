#!/usr/bin/env bash
# Throw-away Odoo 20 tests on local Docker (tmpfs database; never the server database).
#   dev/test.sh init                    start the stack, build the template DB once (~6 min)
#   dev/test.sh run <modules> [tags]    fresh copy of the template, install modules, run tests
#   dev/test.sh pot <module>            print the module's translation template (after a run)
#   dev/test.sh shell <script>          run an odoo shell script from dev/ on boss_test
#   dev/test.sh install <modules>       install modules on boss_test (e.g. the localization, like the server)
#   dev/test.sh update <modules>        update modules (and translations) on boss_test
#   dev/test.sh serve                   serve boss_test on http://localhost:8069 (UI checks; no crons, mail or internet)
#   dev/test.sh uat                     new boss_test like boss20 with the [DEMO] cycle, isolated (accounting session)
#   dev/test.sh down                    destroy containers, database and volumes
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1
DC="docker compose -f compose.test.yml"
DEPS="sale_management,sale_crm,sale_margin,mail"
ARGS="--db_host=db --db_user=odoo --db_password=odoo --data-dir=/var/lib/odoo
      --addons-path=/opt/odoo-src/odoo/addons,/mnt/extra-addons"
case "${1:-}" in
  init)
    $DC up -d db
    $DC run --rm -T odoo $ARGS -d boss_tpl -i "$DEPS" --load-language=es_ES,ar_001 \
      --stop-after-init --log-level=warn
    ;;
  run)
    MODULES="${2:?modules}"
    TAGS="${3:-$(echo "$MODULES" | sed 's/[^,]*/\/&/g')}"
    $DC exec -T db sh -c "dropdb -U odoo --if-exists boss_test && createdb -U odoo -T boss_tpl boss_test"
    $DC run --rm -T --entrypoint sh odoo -c \
      "rm -rf /var/lib/odoo/filestore/boss_test; cp -r /var/lib/odoo/filestore/boss_tpl /var/lib/odoo/filestore/boss_test"
    $DC run --rm -T odoo $ARGS -d boss_test -i "$MODULES" --test-enable --test-tags="$TAGS" \
      --stop-after-init --log-level=test
    ;;
  pot)
    $DC run --rm -T --entrypoint sh odoo -c "printf '[options]\ndb_host=db\ndb_user=odoo\ndb_password=odoo\naddons_path=/opt/odoo-src/odoo/addons,/mnt/extra-addons\ndata_dir=/var/lib/odoo\n' > /tmp/t.conf && python3 /opt/odoo-src/setup/odoo i18n export -c /tmp/t.conf -d boss_test -l pot -o - ${2:?module} 2>/dev/null"
    ;;
  shell)
    $DC run --rm -T -v "$(pwd):/mnt/dev:ro" --entrypoint sh odoo -c "printf '[options]\ndb_host=db\ndb_user=odoo\ndb_password=odoo\naddons_path=/opt/odoo-src/odoo/addons,/mnt/extra-addons\ndata_dir=/var/lib/odoo\n' > /tmp/t.conf && python3 /opt/odoo-src/setup/odoo shell -c /tmp/t.conf -d boss_test --no-http < /mnt/dev/${2:?script}"
    ;;
  install)
    docker rm -f boss20test-web >/dev/null 2>&1 || true
    $DC run --rm -T odoo $ARGS -d boss_test -i "${2:?modules}" --stop-after-init --log-level=warn
    ;;
  update)
    docker rm -f boss20test-web >/dev/null 2>&1 || true
    $DC run --rm -T odoo $ARGS -d boss_test -u "${2:?modules}" --i18n-overwrite --stop-after-init --log-level=warn
    ;;
  serve)
    # nothing leaves the machine: no scheduled jobs, SMTP and HTTP(S) to a closed local port
    $DC run -d --rm --name boss20test-web -p 127.0.0.1:8069:8069 -e HTTP_PROXY=http://127.0.0.1:9 \
      -e HTTPS_PROXY=http://127.0.0.1:9 -e NO_PROXY=db,localhost,127.0.0.1 odoo $ARGS -d boss_test \
      --db-filter=^boss_test$ --http-port=8069 --max-cron-threads=0 --smtp=127.0.0.1 --smtp-port=9
    ;;
  uat)
    docker rm -f boss20test-web >/dev/null 2>&1 || true
    $DC exec -T db sh -c "dropdb -U odoo --if-exists boss_test && createdb -U odoo -T boss_tpl boss_test"
    $DC run --rm -T --entrypoint sh odoo -c \
      "rm -rf /var/lib/odoo/filestore/boss_test; cp -r /var/lib/odoo/filestore/boss_tpl /var/lib/odoo/filestore/boss_test"
    $DC run --rm -T odoo $ARGS -d boss_test -i boss_expediente,accountant,l10n_es_reports,contacts \
      --stop-after-init --log-level=warn
    for script in uat_isolate local_chart local_lang_es setup_vat_mapping server_trial local_demo_suppliers \
                  demo_meeting demo_cycle setup_decisions_2310 uat_customers uat_isolate; do
      echo "== $script"; bash ./test.sh shell "$script.py"
    done
    ;;
  down)
    docker rm -f boss20test-web >/dev/null 2>&1 || true
    $DC down -v --remove-orphans
    ;;
  *)
    sed -n '2,9p' "$0"
    exit 2
    ;;
esac
