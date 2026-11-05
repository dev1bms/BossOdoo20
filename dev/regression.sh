#!/usr/bin/env bash
# Regression of the installed version on boss20 (go-live tracker P2-16): runs the check scripts that protect the
# delivered work, each with its evidence file (dev/uat_run.sh), and prints one line per script and a final verdict.
#   dev/regression.sh            # the standard set
#   dev/regression.sh fast       # the quick set (no end-to-end file cycle)
# Exit status 1 if any script fails. HEAD must be committed, pushed and deployed (uat_run.sh checks the first two).
set -uo pipefail
cd "$(dirname "$0")/.."
FAST=(check_phase1_guards.py check_role_guards.py check_quote_flow.py check_default_markup.py check_rate_matrix.py
      check_status_conditions.py check_settings.py check_house_doc_lock.py check_portal_qweb.py)
FULL=("${FAST[@]}" check_file_e2e.py check_file_consolidation.py check_file_close.py check_route_cases.py
      check_vat_import_freight.py check_margin_rules.py)
SET=("${FULL[@]}"); [ "${1:-}" = fast ] && SET=("${FAST[@]}")
COMMIT=$(git rev-parse --short=12 HEAD)
echo "regression on boss20 · commit $COMMIT · $(date '+%F %H:%M') · ${#SET[@]} scripts"
FAILED=0; SUMMARY=()
for S in "${SET[@]}"; do
  [ -f "dev/$S" ] || { SUMMARY+=("MISSING $S"); FAILED=1; continue; }
  OUT=$(bash dev/uat_run.sh "$S" boss20 2>&1); RC=$?
  LINE=$(echo "$OUT" | grep -E "^RESULT" | tail -1)
  [ $RC -eq 0 ] && STATUS=PASS || { STATUS=FAIL; FAILED=1; }
  SUMMARY+=("$STATUS $S: ${LINE:-no RESULT line} ($(echo "$OUT" | grep -o 'docs/evidencias/[^ ]*' | tail -1))")
  echo "${SUMMARY[-1]}"
done
echo; echo "REGRESSION $([ $FAILED -eq 0 ] && echo PASSED || echo FAILED) · commit $COMMIT · $(printf '%s\n' "${SUMMARY[@]}" | grep -c '^PASS') of ${#SET[@]} passed"
exit $FAILED
