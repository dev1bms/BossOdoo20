#!/usr/bin/env bash
# Throw-away Odoo 20 tests on local Docker (tmpfs database; never the server database).
#   dev/test.sh init                    start the stack, build the template DB once (~6 min)
#   dev/test.sh run <modules> [tags]    fresh copy of the template, install modules, run tests
#   dev/test.sh pot <module>            print the module's translation template (after a run)
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
  down)
    $DC down -v --remove-orphans
    ;;
  *)
    sed -n '2,6p' "$0"
    exit 2
    ;;
esac
