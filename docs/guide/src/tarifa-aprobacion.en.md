## States

| State | Who | What can be done |
|---|---|---|
| Draft | Tariff user | Edit everything; [[Enviar a aprobación]] (needs the document and at least one price) |
| Waiting for approval | Approver | [[Aprobar]] (with confirmation) or [[Volver a borrador]] |
| Approved | — | Used by quotations; **cannot be modified** |

Only **approved** tariffs price quotations. Waiting ones show on the quotation as "Price waiting for approval" with
their amount in the explanation, but they do not count.

## Updating a tariff

An approved tariff is not edited: [[Nueva versión]] (New version) creates a draft copy with the same name and
version + 1. Change the prices, the "valid from" date and the new document, then approve. Versions coexist:

- Each shipment uses the version valid on its **planned date** (ETA import / ETD export).
- If two versions of the same tariff are valid, the newest wins.
- Accepted quotations keep the tariff and version they used (snapshot) even when newer versions exist.

## Priority and conflicts

When two **different** tariffs with the same scope apply, the quotation shows "Several prices apply" and does not
choose. An approver changes the **priority** of one of them (recorded in the tariff history) or narrows its scope.
A more specific price (e.g. for one customer) wins over the general one without a conflict.

## Archiving

Approved tariffs are never deleted: they are **archived** (they stop pricing and keep their history).
