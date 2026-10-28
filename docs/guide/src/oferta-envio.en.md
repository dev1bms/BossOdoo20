In the **[[Envío]]** (Shipment) tab the shipment is described once, as the customer tells it: **origin →
destination**. Lines take from here what prices need: nothing is typed twice.

![Shipment tab of the quotation](img/02-oferta-envio.png)

**Start with the template (the case).** «Template (case)» —e.g. *IMB FOB · Sea import FCL*— fills direction, mode,
load type, incoterm, whose client, what BOSS handles and the services. Everything can be changed afterwards.

| Block | Fields | Used for |
|---|---|---|
| Case | Business of (BOSS client / agent's client), Direction, Mode, Load type, Incoterm and its **named place** | Choose the tariffs. **Traffic** is computed: IMB = sea import, BOSS client; IMA = ordered by an agent for its client |
| Carrier | Main carrier (shipping line or airline), **Inland carrier** (shown only: the supplier of the road transport line, carried to the file), BOSS handles (pickup, customs, main carriage, delivery) | Tariffs of that line or airline; the haulier is chosen on the TTE line |
| Origin (left) | Shipper, country, port/airport, pickup address, place, **ETD** | On an export Spain is the origin: the origin port is the Spanish port and the pickup address gives the province |
| Destination (right) | Consignee, country, port/airport, delivery address, place, **ETA** | On an import Spain is the destination: the destination port is the Spanish port and the delivery address gives the province |
| Cargo | Gross weight, volume, pallets, value | Services per kg, tonne, m³, W/M or pallet. All optional: they can be completed later on the file |
| Estimates | Days in storage (0 by default), customs duties | Time-based services and percentages |

- **Spain is proposed, never forced**: on an import or export the Spanish side is set to Spain when the direction is
  chosen and the side abroad is never Spain; a **National** shipment has both sides in Spain; a **Cross-trade** (neither
  origin nor destination in Spain) fills nothing, and only supplier prices without a Spanish port or country in their
  scope apply. The traffic code says it: IMB, EAB, **XMB**, **NTB**…
- **Addresses**: a customer with several warehouses (e.g. Leroy Merlin) has one delivery address each; choose the
  right one. If there is none, create it from the field («Create and edit»): it becomes an address of the customer.
- **Dates**: ETD (departure from the origin port) and ETA (arrival at the destination). The key date —ETA for an
  import, ETD for an export, a cross-trade or a national shipment— is the **tariff date**: it picks the version of each
  supplier tariff. The unloading date of an LCL (on the file) never picks a tariff. **Exception (Ángel, 27/10): ocean
  and air freight always take the departure (ETD)**, import or export; while the ETD is unknown, the quotation date
  (the rate available today). The ⓘ of the line says which date was used.
- **Addresses and parties**: the invoice address is the orderer's fiscal address and the delivery address lives with
  the consignee in this tab (the header does not show them). The **pickup** address is chosen among the
  **shipper's** addresses; the **delivery** address among the **consignee's** (its warehouses). Both may stay empty.
- **Carrier**: name the commercial carrier (e.g. MSC) even if another legal entity of the group invoices (MSC Spain,
  MSC Switzerland): on each entity's contact, «Part of carrier». Tariffs apply to the whole family; the line, the
  purchase and the bill keep the legal entity.
- **Cargo**: packages with their **type of unit** (cartons, pallets, crates, packages, bottles, bags) and the
  **goods code (HS)**, carried to the file; the duties stay a typed estimate.
- **Rate quotation** (box in the Case group): the client asks for 20', 40' and 40'HC rates without saying how many
  containers ship. Leave the containers empty: each per-container line is priced for **one** container of the size
  on the line, the PDF shows «per Container 40'» and no total, and the client calculates. Before accepting, enter the
  actual containers: the file needs them.
- **Cost on request**: a trucker quoting case by case has no tariff. Choose the supplier, tick «Cost on request» on
  the line (optional column) and type the selling price: the quotation is accepted and the cost is typed in the file
  when the supplier answers.
- **Freight rate from the quotation (⊕)**: valid from today, one week (extendable); if the supplier already has a
  tariff for that route and service, the rate is saved as a **new version** of the same tariff (earlier rates stay as
  history; the newest one valid on the date is used). Rates typed this way are **approved on entry** by whoever types
  them (Sales setting), so nobody waits for an approver in another time zone; the supplier document is required while
  the «Supplier document required» setting is on. «Final delivery to
  the client» in the header is something else: delivery at the warehouse, possibly weeks after the ETA.
- **Real, volume and chargeable weight** (Ángel, 27/10/2026): volume weight = m³ × factor of the mode (**air 167,
  road 333, sea 1000** kg/m³); chargeable weight = **the higher** of gross and volume weight. Suppliers charge BOSS on
  the chargeable weight and BOSS charges the customer on it: services «per chargeable kg» take that quantity. Both
  measures are needed; with one unknown nothing is assumed (weight-based prices say «missing data»). For air, until
  there is an air waybill (AWB), prices «per chargeable kg of the AWB» use the chargeable weight and the explanation
  says «ESTIMATED»; once the AWB weight is entered, it rules. A supplier document with its own factor keeps it.
- **Ports and airports**: worldwide (Odoo 17 list). Sea shipments offer ports; air shipments, airports.
- **Containers**: [[Añadir una línea]] and **choose the size** (20'/40'/45'): the row only stays once something is
  chosen; then type and quantity. Per-container services take the size and quantity (2 × 40' → quantity 2; per
  shipment, 1), also when the containers are entered after the template.
- **Orderer and parties**: in BOSS business the orderer is proposed as consignee (import) or shipper (export); it can
  be changed. In an agent's business nothing is copied: the agent orders, the shipper and consignee are others.
- **Accept**: when something is missing, the message groups it by cause (sale price missing; VAT pending because the
  customer has no country…) and says what to do. Acceptance opens **one** file with the costs to buy; «Link to an
  existing file» is only for a file opened before (pre-alert).

> When a tariff needs data that is empty, the line says so ("Fill in on the quotation: Main carrier") instead of
> inventing a value.
