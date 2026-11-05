"""Phase 1 security settings on boss20 (tracker P1-14, audit of 05/11/2026). Commits.
- public sign-up closed: «auth_signup.invitation_scope» = b2b (invitation only);
- administrator rights removed from inactive users;
- two-factor login: reported only. Enforcing «employee_required» before every internal user has enrolled an
  authenticator app would lock them out, because the fallback code goes by e-mail and boss20 has no mail server.
    dev/server_shell.sh setup_phase1_security.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
ICP = env["ir.config_parameter"].sudo()  # noqa: F821
before = ICP.get_str("auth_signup.invitation_scope")
ICP.set_str("auth_signup.invitation_scope", "b2b")
print(f"OUT signup scope: {before!r} -> {ICP.get_str('auth_signup.invitation_scope')!r}")

admin_group = env.ref("base.group_system")  # noqa: F821
inactive_admins = env["res.users"].with_context(active_test=False).search(  # noqa: F821
    [("active", "=", False), ("group_ids", "in", admin_group.id)])
for user in inactive_admins:
    user.write({"group_ids": [(3, admin_group.id)]})
print(f"OUT inactive users stripped of administration: {len(inactive_admins)} ({', '.join(inactive_admins.mapped('login'))})")

internal = env["res.users"].search([("share", "=", False), ("id", "!=", 1)])  # noqa: F821
enrolled = internal.filtered(lambda u: u.totp_enabled)
print(f"OUT two-factor: policy {ICP.get_str('auth_totp.policy')!r}; enrolled {len(enrolled)} of {len(internal)} internal "
      f"users ({', '.join(enrolled.mapped('login')) or 'none'}); enforcement left off until everyone has enrolled")
print(f"OUT administrators now: {', '.join(internal.filtered(lambda u: admin_group in u.all_group_ids).mapped('login'))}")
env.cr.commit()  # noqa: F821
