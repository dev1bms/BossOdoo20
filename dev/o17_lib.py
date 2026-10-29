"""Read-only client for Odoo 17 over XML-RPC, run ON the BOSS server (stdlib only; prepended by dev/o17_run.sh).

Configuration: a private INI file outside the project and Git, mode 600, written by the owner on the server:
    ~/.config/bossodoo/odoo17_read.conf
        [odoo17]
        url      = <https://host of Odoo 17>
        db       = <database name>
        login    = <login of the authorised user>
        api_key  = <API key of that user>
Values are never printed or logged. The rights of the key are those of the user: nothing here assumes it is read-only,
so the client itself refuses every method that is not a read (see ALLOWED). Errors are reported by kind only.
"""
import configparser
import json
import os
import re
import stat
import sys
import xmlrpc.client

CONFIG = os.environ.get("BOSS_O17_CONFIG", os.path.expanduser("~/.config/bossodoo/odoo17_read.conf"))
EXPORT_DIR = os.path.expanduser("~/o17_export")  # private output folder on the server (mode 700)
ALLOWED = {"search", "search_read", "read", "search_count", "fields_get", "read_group", "name_get", "name_search"}
KEYS = ("url", "db", "login", "api_key")


class O17Error(Exception):
    """An error with a kind that is safe to print (no values)."""

    def __init__(self, kind):
        super().__init__(kind)
        self.kind = kind


def load_config():
    if not os.path.exists(CONFIG):
        raise O17Error("config_missing")
    mode = stat.S_IMODE(os.stat(CONFIG).st_mode)
    if mode & 0o077:
        raise O17Error("config_permissions_too_open")  # must be 600: group/other cannot read it
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(CONFIG)
    if "odoo17" not in cp:
        raise O17Error("config_section_missing")
    values = {k: (cp["odoo17"].get(k) or "").strip() for k in KEYS}
    if any(not v or v.startswith("<") for v in values.values()):
        raise O17Error("config_empty_fields:" + ",".join(k for k, v in values.items() if not v or v.startswith("<")))
    return values


class Client:
    def __init__(self):
        cfg = load_config()
        self.url = cfg["url"].rstrip("/")
        self.db, self.login, self._key = cfg["db"], cfg["login"], cfg["api_key"]
        try:
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
            self.uid = self.common.authenticate(self.db, self.login, self._key, {})
        except Exception as exc:  # network, TLS, protocol: kind only
            raise O17Error("connection_failed:" + type(exc).__name__)
        if not self.uid:
            raise O17Error("authentication_failed")

    def call(self, model, method, args=None, kwargs=None):
        if method not in ALLOWED:
            raise O17Error("blocked_method:" + method)  # the extractor can only read
        try:
            return self.models.execute_kw(self.db, self.uid, self._key, model, method, args or [], kwargs or {})
        except xmlrpc.client.Fault as fault:
            text = str(fault.faultString)
            if "Invalid field" in text:
                m = re.search(r"Invalid field '?([\w.]+)'?", text)
                raise O17Error("invalid_field:" + (m.group(1) if m else "?"))
            if "AccessError" in text or "AccessDenied" in text:
                raise O17Error("access_denied:" + model + "." + method)  # a real permission refusal
            if "does not exist" in text and "model" in text.lower():
                raise O17Error("model_not_found:" + model)
            raise O17Error("fault:" + model + "." + method)
        except Exception as exc:
            raise O17Error("call_failed:" + type(exc).__name__)

    def search_read_all(self, model, domain, fields, batch=500, context=None, order="id"):
        """Page by id so every record is read once, whatever the number of records."""
        out, last = [], 0
        while True:
            dom = [("id", ">", last)] + list(domain)
            rows = self.call(model, "search_read", [dom], {"fields": fields, "limit": batch, "order": order,
                                                            "context": context or {}})
            if not rows:
                return out
            out.extend(rows)
            last = rows[-1]["id"]


def private_path(name):
    os.makedirs(EXPORT_DIR, mode=0o700, exist_ok=True)
    os.chmod(EXPORT_DIR, 0o700)
    return os.path.join(EXPORT_DIR, name)


def write_private(name, data):
    path = private_path(name)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False)
    return path


def read_private(name):
    with open(private_path(name), encoding="utf-8") as fp:
        return json.load(fp)


def fail(exc):
    print("ERROR", exc.kind)
    sys.exit(1)
