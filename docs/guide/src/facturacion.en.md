Invoices are standard Odoo invoices made from the accepted lines. The file adds choosing what is invoiced and the checks
before posting.

## Invoice by services (milestones)

[[Invoice services]] on the file lists the services still to invoice in its orders. Keep ticked those invoiced now (for
example only freight and origin charges) and click **Create draft invoice**. The others stay to invoice for a second
invoice.

- **Partial**: to invoice part of a quantity, change it on the draft invoice.
- **Several invoices**: repeat the action; each invoice carries the file's analytic account.
- **Several files on one invoice**: in **Sales → Orders**, select the orders of the same customer and use the standard
  create invoice action.

## Before posting

A customer invoice is not posted if:

- a line has its **VAT pending** (BOSS VAT table; rule of Ángel: a missing zone is never guessed) or no tax;
- the customer is in **Spain (or has no country)** and has no **NIF** nor another identification of the Spanish
  localization (passport, foreign ID, residence certificate): Odoo 17 practice, confirmed 23/10/2026 (P31). A
  foreign customer without VAT number is not blocked here (an EU business customer without VAT number already leaves the
  VAT pending). A missing address is shown on the contact, not blocking.

Each file invoices **its part** of a shared line: the invoice carries the quantity and the analytic account of the
file.

## Credit notes

The credit note is the standard one (**Credit Note** from the posted invoice). The credited service is to invoice again
and the file subtracts the credit note from what was invoiced.

## Extra cost after acceptance

In **Services and costs** add a line (kind **Extra cost**): service, supplier, quantity, unit, expected cost and reason,
and say who bears it:

| The extra cost is | What happens |
|---|---|
| Covered by the agreed price | It is bought; not invoiced separately. |
| Re-invoice to the customer | A sales manager clicks the ↗ icon (**Re-invoice to the customer**): sale price and reason. **One** line is added to the accepted order and a "Service added after acceptance" snapshot is kept. |
| Needs customer approval | To be decided; its vendor bill is not posted until then. |
| BOSS bears it | It is bought and reduces the margin. |
| Disputed with the supplier | Its vendor bill is not posted until settled. |

No one can add a line to an accepted order any other way: the other accepted prices do not change.
