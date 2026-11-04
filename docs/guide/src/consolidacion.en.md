A **consolidation** is a shipment with **one master document** (MBL or MAWB) and **several houses** (HBL or HAWB),
each for a customer. In Odoo 20 the master is a file and every house is another file linked to it (ADR-013).

## How it is set up

1. Each house comes from its accepted quotation, like any file: its customer, cargo, customs and invoice.
2. The **master** is a file with the carrier, vessel or flight, booking, MBL/MAWB, dates and containers, and with the
   shared purchases (freight, local charges, container haulage).
3. On each house, the field **Master file** hangs it from the master; or from the master, [[New house]] creates a
   house with the same case and route.

## What the system does

- The master's transport data (carrier, vessel, voyage, booking, MBL/MAWB, dates) is **copied to the houses** and
  follows its changes. A blue notice on the house says so.
- The services the master buys (for example the freight or the THC) show on the houses as **bought on the master**:
  they are not ordered twice.
- The shared purchases are **split** between the houses by chargeable weight (W/M), gross weight, volume, equal parts
  or by hand (field **Shared costs split by** on the master). Each house sees its share and its margin with it; the
  master sees the **consolidated margin** of all.
- [[In transit]] on the master moves its open houses; the master's ATA marks them **Arrived**.
- The financial close goes in order: the master cannot close while a house is still open.
- Each house prints its **house B/L or AWB** and the master the **cargo manifest**: see [Transport documents](#/documentos).

## Example on the system

**E260231** is a [PRUEBA] master (one 40' HC container, modelled on a real Odoo 17 file) with two houses, **E260232**
and **E260233**. The explanation with drawings of the before and after is in `docs/consolidaciones.html`.
