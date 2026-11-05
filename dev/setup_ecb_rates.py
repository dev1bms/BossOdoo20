"""Daily exchange rates from the European Central Bank on boss20 (tracker P1-19, audit of 05/11/2026). Commits.
Sets the company to the ECB provider with a daily update and runs one update now; prints the USD rates before and
after (rates are public data, not BOSS prices).
    dev/server_shell.sh setup_ecb_rates.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
company = env.company  # noqa: F821
usd = env["res.currency"].with_context(active_test=False).search([("name", "=", "USD")], limit=1)  # noqa: F821
latest = lambda: [(r.name.isoformat(), round(1 / r.rate, 4)) for r in usd.rate_ids.sorted("name", reverse=True)[:3]]  # noqa: E731
print(f"OUT before: provider {company.currency_provider!r}, interval {company.currency_interval_unit!r}, "
      f"next {company.currency_next_execution_date}, USD active {usd.active}, latest EUR->USD {latest()}")
if not usd.active:
    usd.active = True
company.write({"currency_provider": "ecb", "currency_interval_unit": "daily"})
company.update_currency_rates()
env.cr.commit()  # noqa: F821
company.invalidate_recordset()
print(f"OUT after: provider {company.currency_provider!r}, interval {company.currency_interval_unit!r}, "
      f"next {company.currency_next_execution_date}, latest EUR->USD {latest()}")
cron = env.ref("currency_rate_live.ir_cron_update_currency_rates", raise_if_not_found=False)  # noqa: F821
print(f"OUT cron: {cron and cron.name!r} active {cron and cron.active} next call {cron and cron.nextcall}")
