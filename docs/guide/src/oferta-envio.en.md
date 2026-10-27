In the **[[Envío]]** (Shipment) tab the shipment is described once, as the customer tells it: **origin →
destination**. Lines take from here what prices need: nothing is typed twice.

![Shipment tab of the quotation](img/02-oferta-envio.png)

**Start with the template (the case).** «Template (case)» —e.g. *IMB FOB · Sea import FCL*— fills direction, mode,
load type, incoterm, whose client, what BOSS handles and the services. Everything can be changed afterwards.

| Block | Fields | Used for |
|---|---|---|
| Case | Business of (BOSS client / agent's client), Direction, Mode, Load type, Incoterm | Choose the tariffs. **Traffic** is computed: IMB = sea import, BOSS client; IMA = ordered by an agent for its client |
| Carrier | Main carrier (shipping line or airline), BOSS handles (pickup, customs, main carriage, delivery) | Tariffs of that line or airline. The haulier is the supplier of the pickup or delivery |
| Origin (left) | Shipper, country, port/airport, pickup address, place, **ETD** | On an export Spain is the origin: the origin port is the Spanish port and the pickup address gives the province |
| Destination (right) | Consignee, country, port/airport, delivery address, place, **ETA** | On an import Spain is the destination: the destination port is the Spanish port and the delivery address gives the province |
| Cargo | Gross weight, volume, pallets, value | Services per kg, tonne, m³, W/M or pallet. All optional: they can be completed later on the file |
| Estimates | Days in storage (0 by default), customs duties | Time-based services and percentages |

- **The side abroad is never Spain**, and the Spanish side is set to Spain when the direction is chosen.
- **Addresses**: a customer with several warehouses (e.g. Leroy Merlin) has one delivery address each; choose the
  right one. If there is none, create it from the field («Create and edit»): it becomes an address of the customer.
- **Dates**: ETD (departure from the origin port) and ETA (arrival at the destination). The key date —ETA for an
  import, ETD for an export— is the **tariff date**: it picks the version of each supplier tariff. «Final delivery to
  the client» in the header is something else: delivery at the warehouse, possibly weeks after the ETA.
- **Air chargeable weight**: the higher of the gross weight and the volume weight (volume × 167 kg/m³). Until there is
  an air waybill (AWB), prices «per chargeable kg of the AWB» use it and the explanation says «ESTIMATED»; once the AWB
  weight is entered, it rules.
- **Ports and airports**: worldwide (Odoo 17 list). Sea shipments offer ports; air shipments, airports.

> When a tariff needs data that is empty, the line says so ("Fill in on the quotation: Main carrier") instead of
> inventing a value.
