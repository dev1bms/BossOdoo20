The **Summary** tab of the file computes everything from documents, in company currency and untaxed except where stated.
No amount is typed. **Drafts** (customer invoices, RFQs, vendor bills) are shown apart and **are not counted**.

| Figure | Where it comes from |
|---|---|
| Agreed sale | Part of this file in the confirmed sales (services added later included) |
| Accepted sale / Added after acceptance | The first with what the quotation accepted; the second with what was added with a reason |
| Invoiced / To invoice | **Posted** customer invoices minus credit notes; what is left |
| Collected (with taxes) | What was collected of those invoices |
| Expected cost at acceptance | Supplier cost of the accepted lines, the one of the quotation when accepted |
| Committed purchases | **Confirmed** purchase orders |
| Actual cost | **Posted** vendor bills and receipts minus credit notes (analytic account of the file) |
| Cost still expected | What is ordered or expected and not billed yet (the latest data: order or recalculation) |
| Forecast final cost | Actual cost + cost still expected. An order and its bill are never counted twice |
| Margin at acceptance | Accepted sale − expected cost at acceptance |
| Forecast margin after external costs | Agreed sale − forecast final cost. **Not final** while a cost is not billed or unknown |
| Final margin after external costs | Only when **Costs complete**: agreed sale − actual cost |

**Where the figures come from** (sales managers and accounting) breaks every figure down per service. Example E260001
[DEMO]:

- Agreed sale 1,385 € = accepted 1,225 € (S00009) + 160 € of port occupancy added with a reason.
- Expected cost at acceptance 1,010 € = THC 180 + 240, BL 60, DEM 90 + 90, ARA 350.
- **Margin at acceptance 215 €** = 1,225 − 1,010.
- Forecast final cost 1,130 € = actual cost 0 € (nothing posted) + still expected 1,130 € (the accepted 1,010 € + 120 €
  of extra occupancy).
- **Forecast margin 255 €** = 1,385 − 1,130: **not final** (no cost billed yet).
- Not counted: the draft customer invoice (560 €) and the RFQ not confirmed.

**Own services**: the margin is **after external costs**; BOSS staff work is not a cost here, so it is not the net
profit.

**Variances**: on each service to buy, **Variance** = billed − ordered (or expected). It is reviewed by ticking
**Variance reviewed** with a note; the sale price never changes by itself.

## Who sees what

Figures are computed with all documents, but each one is only shown to who can see those documents in Odoo (standard
until Cristina decides, P35):

| Role | Files | Figures |
|---|---|---|
| Salesperson | Own files (responsible or salesperson of the order) | Sale, invoiced, collected, cost and margin at acceptance (those of the quotation) |
| Purchasing / operations | All | Committed purchases, actual cost, still expected, forecast final, paid |
| Sales manager, accounting | All | Everything, with forecast or final margin and "Where the figures come from" |
| Another company | None | — |
