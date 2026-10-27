Walk-through tested on boss20 on 27/10/2026 with two real cases: the air import of **COFITEL, S.A.** (quotation
[S00032](https://system.bosscontinental.com/odoo/sales/32), accepted, file E260016) and the FCL import of
**AGUILERA EXTINCION, S.L.** with one 20' DV and one 40' HC (quotation [S00033](https://system.bosscontinental.com/odoo/sales/33), accepted, file E260017).
Supplier and sale amounts are confidential: they are not in this guide but inside Odoo (tariffs, pricelist and the
internal note of each quotation, which says where every figure comes from).

Rule: **the cost comes from the supplier tariff** (approved, valid and applying to the shipment), **the sale price
comes from the customer's pricelist or is typed by the salesperson**, and anything missing is always shown with its
reason; a zero never means "free" by default.

## 1. Use an existing service or create one

| | |
|---|---|
| Menu | Tariffs and suppliers › **Services** (or Sales › Products › Products, filter BOSS services) |
| Records used | [HAN] airport handling, [FMI] sea freight import, [THC]… |
| What to do | Search by code first. Only if missing: [[New]], type **Service**, code, name, **Unit** (= charge basis), BOSS pricing tab |
| Result | The service appears in «Add services» and in templates |
| Check | The service form shows **Suppliers**, **Valid prices** and **Readiness** |

A new supplier **never** creates a new service: its price is added to the existing service.

## 2. Unit and calculation of the service

| | |
|---|---|
| Menu | Service form › **BOSS pricing** tab |
| Fields | **Cost source**: supplier tariff, manual amount (agent's freight offer), BOSS own fee (no cost), pending business decision. **Calculation**: price per unit, brackets, per day with free period, percent of a base, the higher of two bases. **Unit** |
| Real examples | HAN: air chargeable kg · AWB and ETX: air waybill · THC, CCC, PAD: container · FuelEU: TEU · FAD: customs declaration · FAI and FMI: manual amount · CSA and CSM: own fee |
| Result | On the quotation, the quantity comes from the shipment (chargeable kg, containers, TEU) |
| Check | In S00033 FuelEU gets 1 TEU on the 20' and 2 TEU on the 40' |

## 3. Supplier and its link with services

| | |
|---|---|
| Menu | Tariffs and suppliers › **Suppliers** (or Contacts) |
| Records used | WORLDWIDE FLIGHT SERVICES (handler), MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U. (carrier), ADUCEX, S.L. and RAMOS VILA, S.L. (customs brokers), SINOTECH LOGISTICS (origin agent), BARBICAN LOGISTIC (haulier) |
| Fields | Legal name, VAT, address (copied from Odoo 17), **Logistics roles** |
| Link with the service | Its **tariff**: each tariff belongs to one supplier and covers one or more services. A service may have several suppliers (FAD: Aducex and Ramos Vila) |
| Check | On the service form, field **Suppliers** |

For air, **Files › Airlines and handlers** proposes each airline's handler per airport (Qatar at MAD → Iberia, from
Odoo 17). The user may change it on the line (step 9).

## 4. Enter a real tariff with its document

| | |
|---|---|
| Menu | Tariffs and suppliers › **Tariffs and documents** › [[New]] |
| Records used | «WFS importación MAD/BCN desde 01/06/2026», «MSC gastos locales importación (origen China) 09-12/2026», «ADUCEX, S.L. FAD importación FCL» |
| Header | Name, **Supplier**, **Supplier document** (PDF), **Document reference**, currency, **Valid from / Valid to** |
| Applies to tab | Only what the document limits: direction, mode, load type, carrier, ports, countries abroad, provinces, customer. Empty = any. Tick **Scope reviewed** |
| Prices tab | One line per service: service, **charge basis**, **calculation**, **priced on**, unit price, minimum, maximum, brackets / day tiers, free days, container size and types, **page** of the document |
| Result | The line shows its **Price**, its **Calculation** and an **Example** computed by the engine |
| Check | The example equals the hand calculation from the PDF |

## 5. Review, approve and check it can be used

| | |
|---|---|
| Buttons | [[Send for approval]] (the yellow «Before sending» notice lists what is missing) → an approver checks the PDF → [[Approve]] |
| Result | **Approved**: it prices quotations from then on. Changing an approved price = **new version** |
| Check | Tariffs and suppliers › **Test pricing**: choose service, shipment and date, compare with your hand calculation |

On 27/10/2026, 24 tariffs were approved under **Belal's delegation for trials**, after comparing every line with its
document (each tariff's chatter says what was checked and fixed). That is not Cristina's or Ángel's approval. A tariff
whose scope has no source stays **waiting for approval** (MSC FuelEU "Far East without China": the country list is a
proposal).

## 6. Sale price and its source

| Source | When | How | On the line |
|---|---|---|---|
| **Customer pricelist** (standard Odoo) | Stable agreement with a customer | Sales › Products › **Pricelists** › [[New]]: one rule per service, **Fixed price**, the unit is filled with the service's unit. On the customer: Sales & Purchase tab › **Pricelist** | **Agreed price (pricelist)** |
| **Typed by the salesperson** | Freight and charges of each shipment, per-shipment brackets | **Unit price** column | **Entered by a person** |
| Markup on cost | Margin rule in a pricelist | Rule **Based on** = expected cost of the line | Rule price |
| **Free of charge** | Sold inside another service | Optional column **Free of charge** | **Free of charge** |

Record used: pricelist «COFITEL, S.A. · venta importación aérea (oferta 05570 y factura F26 10-0011)» (AWB, CSA,
ETX) with its source in the chatter. In S00033 CCC is **free of charge** because it is sold inside THC.

Per-shipment prices on a per-kg line (handling by weight brackets, pickup per shipment): type the per-kg price that
gives the bracket amount (amount ÷ kg; prices have 4 decimals). **If the weight changes, type it again**: the per-kg
price does not follow the brackets.

## 7. Templates

| | |
|---|---|
| Menu | Sales › Configuration › Sales orders › **Templates** |
| Records | **IAB FOB · Air import FOB · fixed services** (FAI, HAN, AWB, CSA, FAD, ETX, TTE-CON) · **IMB FOB · Sea import FCL · fixed services** (FMI, THC, BL, GLO-CCC, T3-PAD, FAD, CSM, TTE-FCL) · **EAB · Air export · fixed services** |
| Use | On the quotation: Other Info tab › **Template** |
| Result | One line per service; container services, one per size and type; quantities from the shipment |
| Chosen again | Nothing is deleted: only missing services are added and a notice says which («Template applied without removing anything») |
| Terms | The template **Terms and conditions** = text for the customer (quotation and invoices). Internal notes go to the chatter |

Sometimes-needed services (origin pickup EXW-AIR, FuelEU, storage, inspections, insurance…) are added with
[[Add services]]. A service already there is not duplicated («Not added twice»); for a second supplier of the same
service, choose that supplier in the wizard.

## 8. Quotation with several services

1. Sales › Orders › Quotations › [[New]] › **Customer** (pricelist and payment term come from the customer).
2. **Shipment** tab: direction, mode, load type, **Spanish port / airport**, **Country abroad**, **Inland province**,
   **Carrier**, **Planned date** (picks the tariff version), gross weight, volume, **Chargeable weight (AWB, kg)** for
   air, **Goods value**, **Containers** (size, type, quantity) for FCL, Incoterm, BOSS handles…
3. Other Info › **Template** → **Order Lines** tab.
4. Cost: **Priced** (tariff), **Manual amount** (type the **Manual cost**, e.g. the agent's freight converted to EUR)
   or the notices of step 10. The ⓘ icon explains each line.
5. Sale: from the pricelist or typed (step 6). Save; reopen: everything is kept.
6. [[Preview]]: what the customer sees (no costs, no internal notes).
7. [[Confirm]]: order locked and **file** created (S00032 → E260016). Not confirmed while a sale price is missing or a
   cost is missing without reason.

Currency: the quotation is in EUR. A USD cost or price is converted at the ECB rate loaded in Odoo (Accounting ›
Configuration › Settings, Currencies: automatic ECB rates) and the reference goes to the internal note.

## 9. Change the supplier or the shipment and check the recalculation

| Change | Tested | What happens |
|---|---|---|
| Supplier of the line (**Supplier** column) | S00032: HAN, AWB and ETX from Iberia (no tariff) to WFS | From «No supplier price» to «Priced» with WFS's tariff |
| Two suppliers with a price | S00033: FAD | Without supplier: **Several prices apply** («choose the supplier on the line»). With Ramos Vila or with Aducex, each with its cost: the difference shows when switching |
| Weight | S00032: 172 → 350 kg and back | Quantities and tariff costs recompute; the chatter keeps each total. Check typed per-kg sale prices (step 6) |
| Containers | S00033: 20' DV + 40' HC | THC, CCC, PAD, FuelEU and haulage, one line per size with its price |

After acceptance, a price change goes through [[Re-price]] with a reason (kept in the pricing history).

## 10. Notices: missing price, tariff not applying or in conflict

| Notice on the line | Meaning | What to do |
|---|---|---|
| **No supplier price** | No approved, valid tariff applies to this shipment (or the one there is belongs to another supplier, scope or date) | ⓘ says why; [[Add supplier price]] with its document, choose another supplier, or (sales manager) **Accepted without cost because** with the reason |
| **Price waiting for approval** | A price exists but is not approved | Approve it (step 5) |
| **Several prices apply** | Two tariffs apply equally | Choose the supplier on the line; same supplier: narrow the scope or set a priority |
| **Shipment data missing** | The shipment lacks something the tariff needs (date, weight, containers) | Complete the Shipment tab |
| **Manual amount** | Cost per offer (freight) | Type the **Manual cost** |
| **Sale price missing** | Price 0 with no pricelist | Type it, or tick **Free of charge** if it is included in another |

Real exceptions shown by the test: air customs clearance (brokers have FCL tariffs only), delivery in Madrid (no
Barbican tariff; IRENEO's zone for 28140 not confirmed), the origin agent's pickup, MSC haulage, and the FuelEU sale
in S00033 («Free of charge» as in the real invoice; pending business decision).
