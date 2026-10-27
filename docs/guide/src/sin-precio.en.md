When a line has no cost, the system says **exactly what is missing** and offers the right button on the line itself.
No new service is created and no zero is used.

| What is missing | Button on the line | What opens |
|---|---|---|
| A shipment datum | — | The explanation names the field; complete it in the Shipment tab |
| The supplier tariff | ⊕ [[Añadir precio de proveedor]] | Price form pre-filled from the quotation (route included) |
| This week's freight (manual-amount service) | ⊕ [[Añadir precio de proveedor]] | The same form, with **one week** of validity and the route (origin and destination port) |
| The approval | ☑ Review the supplier price | The tariff; an approver clicks [[Aprobar]] |
| A choice between two tariffs | ☑ Review the supplier price | The tariffs involved, to set a priority |
| The service definition | ? Open the service | The service and its pending question |

## Add the missing price

![Add supplier price from the quotation](img/05-anadir-precio-proveedor.png)

1. The form arrives with the **service, charge basis, container size and type**, the supplier (the quotation
   carrier), the scope (direction, mode, load type, **Spanish port and port abroad**, country) and the tariff date.
   For a freight (manual amount) the proposed validity is **one week**: a carrier's offer is valid for days, not a
   year.
2. Enter the **unit price**, minimum/maximum if any, the **page** of the document and attach the **supplier document**
   (PDF). You can add it to an existing draft tariff (which already has its PDF) or create a new one. With an
   existing tariff its scope is shown on one line: tick **Tariff scope reviewed** if it matches the document.
3. [[Guardar precio]] (Save price): the price is stored in the tariff (never on the quotation) and sent for approval.
   The line becomes "Price waiting for approval".
4. An approver opens the tariff from the same line and clicks [[Aprobar]]. On closing, the quotation reloads and the
   line is **Priced**, without typing anything again.

> Prices with brackets, percentages or days open the full tariff form (with the same pre-filled values).

## Other cases

- **Freight and services priced by a supplier offer** (FMI, FME, FAI, FAE): two ways. Type the **manual cost** and
  its reference (offer number) for this quotation only; or save the weekly offer as a **supplier price** with its route
  (Shanghai → Valencia) and its week (⊕ on the line): once approved it prices every quotation of that route that
  week, and earlier prices stay as history. Outside the route or the week the line is a manual amount again.
- **Supplier without a price for that service** (e.g. WFS on an ocean freight): a warning says so when it is chosen;
  the line stays «No supplier price» until one exists.
- **BOSS own service** (CSM, CSA…): executed by BOSS, no supplier and no cost; none has to be entered.
- **Time-based services** (DEM, OCU, ALM): on the quotation the cost is an **estimate** with the assumed days
  (Shipment tab). The actual cost is only known when the period ends, in the shipment file.
- **Expired price**: the explanation says there are prices of the service but none valid on the planned date: ask
  the supplier for the current document (new tariff version) or check the date.
- **Only demo prices**: the explanation says so; a real customer is never priced with them.
- **Conflict**: when two tariffs with the same scope apply, the line does not pick the cheapest; an approver sets the
  **priority** or a tariff is narrowed (e.g. by carrier or port).
