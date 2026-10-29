#!/usr/bin/env bash
# Run the Odoo 17 READ client on the BOSS server (the connection details live only in the server's private config file).
#   dev/o17_run.sh init                         create the empty config template (mode 600) if it does not exist
#   dev/o17_run.sh run <script.py> [args...]    run dev/<script.py> after dev/o17_lib.py (stdlib python3 on the server)
#   dev/o17_run.sh put <local file> <name>      copy an ids/spec file (no personal data) into ~/o17_export
#   dev/o17_run.sh get <name> <local file>      copy an export back (ignored folder .research only; personal data)
# Odoo 17 is only read: the client refuses every method that is not a read. Nothing here prints a configuration value.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=boss@100.87.98.15
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST"
CONF='$HOME/.config/bossodoo/odoo17_read.conf'
case "${1:?init|run|put|get}" in
  init)
    $SSH "mkdir -p ~/.config/bossodoo ~/o17_export && chmod 700 ~/.config/bossodoo ~/o17_export \
      && if [ ! -e $CONF ]; then umask 077; printf '[odoo17]\nurl = <fill on the server>\ndb = <fill on the server>\nlogin = <fill on the server>\napi_key = <fill on the server>\n' > $CONF; fi \
      && chmod 600 $CONF && ls -l $CONF | cut -c1-10 && echo 'template ready (values empty)'"
    ;;
  run)
    SCRIPT="${2:?script}"; shift 2
    ARGS=""; for a in "$@"; do ARGS="$ARGS '$a'"; done
    cat dev/o17_lib.py "dev/$SCRIPT" | $SSH "python3 - $ARGS"
    ;;
  put)
    case "${3:?name}" in */*|..*) echo "name must be a plain file name"; exit 1;; esac
    $SSH "umask 077; mkdir -p ~/o17_export && cat > ~/o17_export/$3" < "${2:?local file}"
    ;;
  get)
    case "${2:?name}" in */*|..*) echo "name must be a plain file name"; exit 1;; esac
    case "${3:?local file}" in .research/*) ;; *) echo "personal data may only go to .research/ (ignored by Git)"; exit 1;; esac
    $SSH "cat ~/o17_export/$2" > "$3"
    ;;
  *) echo "usage: init|run|put|get"; exit 1;;
esac
