What BOSS management can change without programming: values that change over time, rules of the file statuses and
data of the services. It is managed from **Settings** (`/odoo/settings`) and from the tables its links open.

> The column **Current value** is the boss20 value on 4/11/2026: for the new settings it is what the system did before
> the setting existed. The sale and margin percentages are not published in this guide: they are in Settings.

## Where they are

**Settings** has three BOSS tabs, one per area:

| Tab | What is set |
|---|---|
| **BOSS · Pricing** | Supplier tariffs, selling price and margin, shipment measures, VAT |
| **BOSS · Files** | Opening, status conditions, closing and reminders |
| **BOSS · Documents** | House B/L and AWB, customer invoice |

Each setting explains under its name what it does and where the rule comes from. After a change, click [[Save]] at the
top; [[Discard]] undoes what is not saved.

## BOSS · Pricing

![Settings › BOSS · Pricing › Supplier tariffs](img/45-ajustes-tarifas-proveedor.png)

### Supplier tariffs

| Setting | Current value | What it does |
|---|---|---|
| **Supplier document required** | On | A tariff is not sent for approval without the supplier's document attached: every price is traceable. |
| **Freight rates approved on entry** | On | The weekly freight typed from a quotation is approved by whoever enters it: an urgent quotation never waits for an approver. Off: it waits for a tariff approver. |
| **Validity of a freight rate entered from a quotation** · Days | 7 | Days the weekly freight is valid from its start. |
| **Warn before a tariff expires** · Days | 30 | A price expiring within those days shows «Expires soon» in the lists and in the filter of the same name. |
| **Supplier cost in another currency** | Odoo exchange rate of the quotation date | What to do when the supplier price is in another currency than the quotation. The other option, «Do not convert», leaves the cost pending. |

Links: **Supplier tariffs** and **Supplier prices**.

Example: a shipping line changes its freight every two weeks and BOSS wants a typed rate to last that long →
**Validity…** = 14. Rates already entered keep their dates.

### Selling price and margin

![Settings › BOSS · Pricing › Selling price and margin, Shipment measures](img/46-ajustes-precio-margen-medidas.png)

| Setting | What it does |
|---|---|
| **Default sale price of BOSS services** · Cost + % | Proposed sale = expected cost + this %, as a rule of the default pricelist. A customer's agreed price and a price typed on the line come first. 0 switches it off. |
| **Minimum margin without a rule** · % of the cost | Minimum margin of a group or service without its own rule (Odoo 17 base rule). |
| **Minimum margin without a rule** · Tolerance (amount) | A margin up to this **amount** (not a %) below the minimum is accepted without a warning. |

Links: **Pricelists**, **Quotation templates**, **Minimum margins** and **Minimum margin exceptions**. The rules by
service group, shipment type and customer are in the last two tables (see [Sale price and VAT](#/venta-iva)). On the
quotation the minimum margin **warns**, it never blocks. At the operational close a low margin needs a reason, as set by
the condition **Low margin explained** (see below).

### Shipment measures

| Setting | Current value | What it does |
|---|---|---|
| **Volume weight factors (kg per m³)** · Air | 167 | Chargeable weight = the higher of the gross weight and volume × factor. |
| … · Road | 333 | For every road leg, whatever the main mode. |
| … · Sea | 1000 | 1 t = 1 m³ (W/M). |

A supplier document stating its own factor keeps it. Links: **Ports and airports** and **Services**.

> A new factor applies to the quotations and files whose measures or mode are entered or changed afterwards; those
> already recorded keep their chargeable weight. Changing it is Ángel's decision.

### VAT

**VAT of BOSS services** opens the **BOSS VAT table**: the Odoo tax of each case (VAT class of the service and customer
zone). A case without a tax leaves the VAT pending and the quotation cannot be sent or confirmed. Accounting keeps it
(see [VAT and currencies](#/iva-moneda)).

## BOSS · Files

### Opening a file

- **Who works on a file**: links to **Operators by customer and traffic** (operator proposed on opening), **Airlines and
  handlers** (the handler of each airline at each airport) and **Logistic roles**.
- **Consolidations: shared costs split by** — current value **Chargeable weight (W/M)**; also gross weight, volume,
  equal parts or a manual share. Proposed on each new master; the master can change it.

### Status conditions

![Settings › BOSS · Files › Status conditions](img/47-ajustes-condiciones-estado.png)

Each condition has one of three levels:

| Level | What happens when the data is missing |
|---|---|
| **Required (stops the step)** | The step is not done. A message says what is missing. |
| **Warning only** | The step is done and a note stays in the file history with what was missing, the user and the time. |
| **Not checked** | The step is done silently and the data no longer shows in the **Next step**. |

| Step | Condition | Current value | When it applies |
|---|---|---|---|
| **To leave («In transit»)** | ATD · Booking · Master B/L or AWB · Container numbers | Warning only | Booking and master on sea and air; numbers on FCL with containers without a number |
| **To deliver («Delivered»)** | ATA (import) · Vessel discharge · Customs release · Pickup date and time · Delivery date and time · House B/L released | Required | ATA on an import; discharge on a sea import; release when BOSS clears customs; dates when BOSS picks up or delivers; house B/L on a sea import with delivery |
| **To close operations** | Every service invoiced · Low margin explained | Required | Every file |

Examples:

- **Required**: «ATD» set to Required. A file without an actual departure does not go «In transit» and the message
  reads «E26… cannot leave yet, it lacks: ATD (actual departure) (required in Settings › BOSS · Files).»
- **Warning only**: «House B/L released» set to Warning only. The file goes «Delivered» and its history keeps, with the
  user and the time, «Delivered without: house B/L released or sea waybill. A warning: complete them when they are
  known.»
- **Not checked**: «Vessel discharge» set to Not checked, for a port where BOSS does not record the discharge. It is
  neither asked for nor listed in the next step.

A level change applies to the steps done afterwards: a file that already left or was delivered does not go back.

### Closing a file

| Setting | Current value | What it does |
|---|---|---|
| **Ratings required to close operations** | On | The customer and every supplier are rated 0 to 10 before operations close. |
| **Days to close after the delivery** · Days | 7 | After those days the next step says the file must be closed and it shows in the filter «Delivered, due to close». |
| **Supplier bill before the customer invoice** | Block payment (posting allowed) | What happens to a supplier bill of a service not yet invoiced to the customer. |

### Reminders (Odoo activities, no e-mail)

| Setting | Current value | What it does |
|---|---|---|
| **Container free-time alert** · Working days | 3 | Activity to the operator that many days before the last free day of each container, another on that day and one to the salesperson on the first day with a cost. 0 switches it off. |
| **Month-close reminder** | The chosen person | On the last day of the month each responsible gets an activity per file still to invoice or close; this person gets the summary. Empty: no summary. |

## BOSS · Documents

![Settings › BOSS · Documents](img/48-ajustes-documentos.png)

| Setting | Current value | What it does |
|---|---|---|
| **Original house B/Ls** · Originals | 3 | Originals printed on the house B/L. A sea waybill prints «express», zero. |
| **Place of issue** | Empty = the company's city | Place printed on the house B/L and AWB. |
| **Operation date on the invoice** | On | The invoice keeps its issue date and prints the operation date of the file apart: arrival of an import, departure otherwise (RD 1619/2012 art. 6). Off: empty unless typed. |
| **Mention of amounts paid on behalf** | Empty = standard wording | Text of the invoice re-invoicing duties, import VAT and other amounts paid on behalf (art. 78.Tres.3º Ley 37/1992), in the customer's language. |

They apply to the documents printed after the change; a PDF already sent does not change.

## Services and Incoterms

### Create a new service

**Pricing & Suppliers → Services** has no New button: a BOSS service starts from a similar one.

1. Open the most similar service (for example DEM for another demurrage) and use **⚙ → Duplicate**.
2. Change the **Name** and the **Internal Reference** (the service code).
3. Tab **BOSS pricing**, group **How it is priced**:
   - **Cost source**: supplier tariff, manual amount, BOSS own fee or pending business decision.
   - **Calculation method**, **Tariff date**, **Summary group**, **VAT class** and **Paid on behalf**.
   - **Bought from**: *Any supplier*; *The air handler of the file* (follows the handler of the airline at the airport,
     such as HAN, ALM or AWB); *The haulier (road leg)*, whose supplier is the inland carrier of the quotation and the
     file.
   - **Counts for the customs value as**: Freight, THC, T3 or Insurance. The marked services are listed in **Data for
     the customs broker** on the file.
4. For a time-based service, add its **Default period** lines (they are not copied by Duplicate).
5. The supplier tariffs of the service are entered afterwards (see [Enter a tariff](#/tarifa-alta)).

![DEM service › BOSS pricing: «Bought from», «Counts for the customs value as» and «Default period»](img/49-servicio-periodo-por-defecto.png)

### Default period of a time-based service

On a service with the calculation method **Per day with free period** (storage, demurrage, occupancy, detention), the
table **Default period (time-based services)** says where the period starts and ends when the supplier price does not
say it:

| Direction | Load type | The period starts at | The period ends at |
|---|---|---|---|
| Import | Empty = any | Arrival of the vessel or flight (ATA) | Empty container returned (each container) |
| Export | Empty | Full container at the terminal (each container) | Actual departure (ATD) |

- A line with a load type (for example LCL) wins over the line without a load type of the same direction.
- A line without events means «no period»: the cost is typed.
- When the period runs per container («each container» events), the service gets the **free-time alerts**.

Example: a shipping line counts demurrage from the vessel discharge and its tariff does not say it. On DEM, change the
import line to **Vessel discharge** → **Empty container returned**. It applies to the calculations done afterwards.

### Incoterms

![Accounting › Configuration › Incoterms: column «Freight»](img/50-incoterms-flete.png)

**Accounting → Configuration → Incoterms** (the menu only shows in **developer mode**: Settings → Developer Tools →
Activate the developer mode), column **Freight**, editable in the list: *Prepaid* when the seller pays the main carriage (C and
D terms) or *Collect* when the buyer pays it (E and F terms). It is proposed as **Freight payable** on the house B/L of
the file and used by the minimum margin rules (for example LCL local charges prepaid). Accounting keeps the Incoterms.

> A change of the freight of an Incoterm is proposed to the files that take that Incoterm afterwards; existing files keep
> their freight payable. The current values follow Incoterms 2020: there is no need to touch them.

## Security and good practice

### Who can change the settings

- Opening and saving **Settings** needs the **Administration: Settings** right. The values are stored on the company,
  which only users with an **Administration** right can change: a user without it neither sees the menu nor can change
  a setting another way.
- The linked tables have their own rights: **Minimum margins**, **Minimum margin exceptions** and **Default period** are
  kept by sales managers; the **BOSS VAT table** and the **Incoterms** by accounting managers; the tariffs by tariff
  approvers.
- Today the four internal users of boss20 are administrators. When the operators' accounts are created, give them only
  the groups of their work (Sales, Purchase, Accounting), never **Administration**.

### What a change affects

- A setting applies **from the moment it is saved**, to the steps, calculations and prints done afterwards: it does not
  change a file that already left, was delivered or closed, nor a posted invoice, nor an accepted quotation (its frozen
  copy; see [Closing the file](#/cierre)). Neither a volume factor nor the freight of an Incoterm rewrites data already
  recorded.
- Each change of level of a condition is kept in the company's history (Settings → Companies → the company): who, when,
  previous and new level.
- A zero or negative value where it makes no sense (factor, validity days, originals) is refused with a message.
- The status of a file and its financial close change only with its buttons, which check the conditions; neither an
  import nor another program can skip them.

### Before switching a condition off

- **Every service invoiced** and **Low margin explained** protect the result of the file. On *Warning only* or *Not
  checked*, operations can close with services not invoiced or with a low margin without a written reason. The
  **financial close** still requires everything invoiced and the month-close reminder still lists those files, but the
  control comes later. Changing them is a management decision (Cristina, Ángel).
- The check that **amounts paid on behalf** are re-invoiced exactly (art. 78.Tres.3º Ley 37/1992) is always required: the
  level of **Low margin explained** does not change it. The financial close does not look at the margin again.
- The **Delivered** conditions Cristina wrote (customs release, house B/L released, dates) prevent goods being marked
  delivered without clearance or without the B/L released: do not switch them off without her approval.
- Prefer **Warning only** to **Not checked**: the step is done anyway, but the history keeps a record.

### How to check a change before adopting it

1. Write down the current value (this page gives it) and the reason for the change.
2. Change the setting and click [[Save]].
3. Try it on a **[PRUEBA]** file or quotation, never on a real one: for example move a test file to «In transit» or
   «Delivered» and read the message or the history.
4. If the result is not the expected one, set the previous value back and save.
