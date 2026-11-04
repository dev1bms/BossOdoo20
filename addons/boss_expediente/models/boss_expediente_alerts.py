import calendar
from datetime import timedelta

from markupsafe import Markup

from odoo import api, fields, models

# Roadmap item 14. Reminders are Odoo activities (no e-mail during the tests; F0-C55, F0-A37).
TIME_CODES_ALERTED = ("DEM", "OCU", "DET")  # services whose cost runs per container after the free days
FREE_DAYS_SEARCH = 120  # days probed after the start of a period to find the first one with a cost


def minus_working_days(day, count):
    """The day `count` working days (Monday to Friday) before `day`."""
    while count > 0:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            count -= 1
    return day


class ResCompany(models.Model):
    _inherit = "res.company"

    boss_free_alert_days = fields.Integer(
        "Container alert: working days before the last free day", default=3,
        help="F0-C55: the operator gets an activity this many working days before the last free day of each container "
             "(demurrage, storage, detention), another on the last free day, and the salesperson one on the first day "
             "with a cost. 0 switches the alerts off.")
    boss_month_close_copy_user_id = fields.Many2one(
        "res.users", "Month-close reminder: copy to",
        help="F0-A37: on the last day of the month every responsible gets an activity on each file still to invoice or "
             "to close; this person gets the summary (Odoo 17 «CIERRE MENSUAL»). Empty: no summary.")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_free_alert_days = fields.Integer(related="company_id.boss_free_alert_days", readonly=False)
    boss_month_close_copy_user_id = fields.Many2one(related="company_id.boss_month_close_copy_user_id", readonly=False)


class BossExpedienteContainer(models.Model):
    _inherit = "boss.expediente.container"

    free_alerts_done = fields.Char(copy=False, help="Container alerts already given (service and stage).")


class BossExpedienteCost(models.Model):
    _inherit = "boss.expediente.cost"

    def _boss_last_free_day(self, container, start):
        """Last day without cost of this per-container service for one container whose period started at `start`:
        the day before the first end date the supplier price charges, asked to the same engine as the cost (free
        days, weekends, day tiers). None when the price does not compute."""
        self.ensure_one()
        file = self.expediente_id
        Pricing = self.env["boss.pricing"]
        inputs = dict(file._boss_inputs(), line_qty=1, container_size=container.size or None,
                      container_type_id=container.container_type_id.id or None, supplier_id=self.partner_id.id or None,
                      containers=[{"size": container.size, "type_id": container.container_type_id.id, "quantity": 1}])
        first = max(0, (self.tariff_line_id.free_days or 0) - 3)
        for days in range(first, FREE_DAYS_SEARCH):
            end = start + timedelta(days=days)
            res = Pricing.price_cost(self.product_id, self.uom_id, dict(inputs, **Pricing._warehouse_period(
                start, end, file.port_id)), self._boss_tariff_date(), file.company_id)
            if res.status != "ok":
                return None
            if res.amount > 0:
                return fields.Datetime.context_timestamp(file, end).date() - timedelta(days=1)
        return None


class BossExpediente(models.Model):
    _inherit = "boss.expediente"

    # --- F0-C55: last free day of the containers ----------------------------------------------------------------

    def _boss_container_alerts_due(self, today):
        """[(container, need, last free day, stage)] due today: «first» N working days before the last free day,
        «last» on it, «late» once a day costs (container still not returned, or picked up, or delivered)."""
        self.ensure_one()
        days_before = self.company_id.boss_free_alert_days
        due = []
        if not days_before:
            return due
        needs = self.cost_ids.filtered(lambda n: not n.closed and n.product_id.default_code in TIME_CODES_ALERTED)
        for need in needs:
            for container, start, end in need._boss_container_periods():
                if not start or end:
                    continue  # not started, or already ended (the cost is then the actual one)
                last_free = need._boss_last_free_day(container, start)
                if not last_free:
                    continue
                done = set((container.free_alerts_done or "").split(","))
                code = need.product_id.default_code
                # the most urgent stage due today; once a stage is given, the earlier ones are no longer sent
                for stage, when in (("late", last_free + timedelta(days=1)), ("last", last_free),
                                    ("first", minus_working_days(last_free, days_before))):
                    if f"{code}-{stage}" in done:
                        break
                    if today >= when:
                        due.append((container, need, last_free, stage))
                        break
        return due

    @api.model
    def _boss_cron_container_alerts(self, today=None):
        """Daily: activities for the containers close to (or past) their last free day."""
        today = today or fields.Date.context_today(self)
        files = self.search([("state", "in", ("in_transit", "arrived", "delivered"))])
        _ = self.env._
        count = 0
        for file in files:
            for container, need, last_free, stage in file._boss_container_alerts_due(today):
                code = need.product_id.default_code
                label = container.number or f"{container.size}' {container.container_type_id.code or ''}"
                order = file.sale_order_ids.filtered(lambda o: o.state == "sale")[:1]
                if stage == "late":
                    user = order.user_id or file.user_id
                    summary = _("%(code)s %(container)s: costs since %(day)s", code=code, container=label,
                                day=(last_free + timedelta(days=1)).strftime("%d/%m/%Y"))
                else:
                    user = file.user_id or order.user_id
                    summary = _("%(code)s %(container)s: last free day %(day)s", code=code, container=label,
                                day=last_free.strftime("%d/%m/%Y"))
                note = _("Return or pick up the container before its free days end (supplier %(supplier)s). The "
                         "date comes from the supplier price, as the cost does.", supplier=need.partner_id.name or "-")
                file.activity_schedule("mail.mail_activity_data_todo", date_deadline=max(last_free, today),
                                       summary=summary, note=note, user_id=(user or self.env.user).id)
                done = [d for d in (container.free_alerts_done or "").split(",") if d] + [f"{code}-{stage}"]
                container.free_alerts_done = ",".join(done)
                count += 1
        return count

    # --- F0-A37: month-end reminder ------------------------------------------------------------------------------

    def _boss_month_close_reason(self):
        """Why this file is in the month-end reminder, or False: services still to invoice once the goods arrived,
        or delivered and operations not closed."""
        self.ensure_one()
        _ = self.env._
        reasons = []
        if self.state in ("arrived", "delivered", "closed") and self.has_to_invoice:
            reasons.append(_("services still to invoice"))
        if self.state == "delivered":
            reasons.append(_("delivered, operations not closed"))
        return ", ".join(reasons) or False

    @api.model
    def _boss_cron_month_close(self, today=None, force=False):
        """On the last day of the month (or when forced): an activity per file still to invoice or to close for its
        responsible, and the summary for the person in copy. Once per file and month."""
        today = today or fields.Date.context_today(self)
        if not force and today.day != calendar.monthrange(today.year, today.month)[1]:
            return 0
        _ = self.env._
        month = today.strftime("%m/%Y")
        summary = _("Month close %s: invoice or close this file", month)
        by_user = {}
        for file in self.search([("state", "in", ("arrived", "delivered", "closed")), ("financial_closed", "=", False)]):
            reason = file._boss_month_close_reason()
            if not reason:
                continue
            user = file.user_id or file.sale_order_ids[:1].user_id or self.env.user
            by_user.setdefault(user, []).append((file, reason))
            if not file.activity_ids.filtered(lambda a: a.summary == summary):
                file.activity_schedule("mail.mail_activity_data_todo", date_deadline=today, summary=summary,
                                       note=reason, user_id=user.id)
        copy = self.env.company.boss_month_close_copy_user_id
        if copy and by_user:
            partner = self.env.company.partner_id
            title = _("Month close %s: files to invoice or close", month)
            if not partner.activity_ids.filtered(lambda a: a.summary == title):
                rows = Markup("").join(
                    Markup("<li><strong>%s</strong>: %s</li>") % (user.name, ", ".join(
                        f"{file.name} ({reason})" for file, reason in files))
                    for user, files in by_user.items())
                partner.activity_schedule("mail.mail_activity_data_todo", date_deadline=today, summary=title,
                                          note=Markup("<ul>%s</ul>") % rows, user_id=copy.id)
        return sum(len(files) for files in by_user.values())

    # --- F0-A20: operation date of the invoice --------------------------------------------------------------------

    def _boss_operation_date(self):
        """Date of the operation of this file, printed on its invoices apart from the issue date (RD 1619/2012 art.
        6): the arrival of an import, the departure otherwise (Odoo 17's «important date»); actual, else estimated."""
        self.ensure_one()
        if self.direction == "import":
            moment = self.ata and fields.Datetime.context_timestamp(self, self.ata).date()
            return moment or self.eta or False
        moment = self.atd and fields.Datetime.context_timestamp(self, self.atd).date()
        return moment or self.etd or False
