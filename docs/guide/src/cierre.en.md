From the delivered file to the closed file: states, conditions, ratings, frozen data and the margin report.

## States

[[In transit]] → **Arrived** → [[Delivered]] → [[Close operations]] → [[Close financially]].

- **In transit**: when the actual departure (ATD), the booking, the master B/L or AWB or the container numbers are
  missing, it warns and writes it in the history, but does not block (Odoo 17 practice).
- **Arrived** (an Odoo 17 stage): typing the **ATA** in **References and dates** moves the file to Arrived by itself.
  In a consolidation, the houses arrive with their master.
- **Delivered** asks for what Cristina wrote and Odoo 17 enforced: on an import the ATA and the vessel discharge; the
  customs release when BOSS clears; the pickup or delivery date and time when BOSS transports; and on a sea import
  with delivery, the house B/L released or a sea waybill. When something is missing, the message says it. The day of
  the delivery is kept.
- **Close operations** asks for: everything invoiced to the customer, no margin warning without the reason written by
  a sales manager («Closed with a low margin because») and the **ratings** done. Not every supplier bill is needed:
  the file closes against the forecast and late bills are recorded without reopening.
- **Close financially** (accounting): everything invoiced, costs billed or closed, variances reviewed and nothing in
  draft. Only the accounting administrator reopens it.

The **Next step** line at the top of the file says what is due at each moment, and the [[Go]] button does it or opens
what is missing. One week after the delivery it warns: Cristina asks to close within a week.

## Ratings

Before closing operations, the **customer** and **every supplier** the file bought from (confirmed orders and bills)
are rated from **0** (very bad) to **10** (excellent), with a comment if wanted. It is the Odoo 17 scale.

- The parties to rate appear in the **Ratings** tab when the file is marked **Delivered**, or with
  [[List the parties to rate]].
- Pressing [[Close operations]] without the ratings does not close the file: a notice says who is still to rate.
- The **average** of each party shows on its contact (tab **Sales & Purchase**) and in the **Rating** column of
  **Services to buy**: it helps to choose a supplier.
- It is a setting: **Settings → Sales → Ratings required to close operations** (on, as in Odoo 17).

## Frozen data

Once operations are closed (or the file cancelled), the shipment data is **read-only**: parties, route, cargo,
references, dates, customs and the house document. If someone tries to change it, Odoo refuses and says the file must
be reopened. Still open: the services and late supplier bills, the containers (their dates compute demurrage), the
responsible and the ratings. To correct: [[Reopen]], a sales manager only, with a reason kept in the history (as in Odoo
17); a file closed financially is first reopened financially.

## Margin by file

**Shipment files → Margin by file** (sales managers and accounting): agreed sale, expected cost and margin and the
final margin, by responsible, salesperson, customer, traffic and month, in list, pivot or graph. It is refreshed when
opened; the margin of a financially closed file stays fixed.

## Reminders

They are Odoo **activities** (bell and «My activities»); no e-mail is sent.

- **Container free days** (F0-C55): every morning, for each container whose demurrage, storage or detention is running
  and which is not returned or picked up yet, the operator gets an activity **3 working days before the last free
  day** and another **on that day**; on the **first day with a cost**, one for the salesperson. The last free day comes
  from the supplier price, with the same calculation as the cost. Setting: **Container free-time alert** (0 switches it
  off).
- **Month close** (F0-A37, like the Odoo 17 «CIERRE MENSUAL» e-mail): on the last day of the month each responsible
  gets an activity on every file with services to invoice or delivered and not closed; the person in the setting
  **Month-close reminder: copy to** (Ángel) gets the summary by responsible.
- **Operation date** on the invoice (F0-A20 as reviewed, RD 1619/2012 art. 6): the invoice keeps its issue date and,
  apart, the operation date of the file (arrival of an import, departure of an export).
