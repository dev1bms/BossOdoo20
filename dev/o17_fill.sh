#!/usr/bin/env bash
# Run ON the BOSS server (not through this repo's wrappers), once, to fill the Odoo 17 read configuration.
# The values are typed at hidden prompts: they appear in no command line, no history, no log and no chat.
#   bash o17_fill.sh
set -euo pipefail
umask 077
CONF="$HOME/.config/bossodoo/odoo17_read.conf"
mkdir -p "$(dirname "$CONF")"; chmod 700 "$(dirname "$CONF")"
read -r -p "Odoo 17 URL (https://...): " URL
read -r -p "Database name: " DB
read -r -p "Login of the authorised user: " LOGIN
read -rs -p "API key (hidden): " KEY; echo
O17_URL="$URL" O17_DB="$DB" O17_LOGIN="$LOGIN" O17_KEY="$KEY" python3 - "$CONF" <<'PY'
import os, sys
path = sys.argv[1]
vals = {"url": os.environ["O17_URL"], "db": os.environ["O17_DB"], "login": os.environ["O17_LOGIN"], "api_key": os.environ["O17_KEY"]}
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as fp:
    fp.write("[odoo17]\n" + "".join(f"{k} = {v}\n" for k, v in vals.items()))
os.chmod(path, 0o600)
PY
echo "Saved to $CONF (mode $(stat -c %a "$CONF")). Values are not shown."
