"""Connection check for the Odoo 17 read client. Prints OK, or the kind of error only; never a value.
    dev/o17_run.sh run o17_check.py"""
try:
    client = Client()  # noqa: F821
    version = client.common.version().get("server_version", "?")
    count = client.call("res.partner", "search_count", [[]])
    print("OK authenticated; server", version, "; res.partner readable:", count > 0)
except O17Error as exc:  # noqa: F821
    fail(exc)  # noqa: F821
