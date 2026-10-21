For each line the system applies **one single rule**, the same on every screen:

1. Prices of the **same service and charge basis**.
2. **Valid** on the planned date of the shipment (all versions, not only the latest approved one).
3. **Approved**. If only unapproved prices fit → "Price waiting for approval".
4. That **fit the shipment**: direction, mode, load type, carrier, port, country, province, customer, container size and
   type. If a price needs an empty datum → "Missing shipment data" (nothing is guessed).
5. **Priority** (lower wins).
6. Within the same tariff, the **newest version**.
7. The **most specific**: a price with more conditions (e.g. for one customer) wins over the general one.
8. If several are still left → **"Several prices apply"**. Never the cheapest nor the first.
