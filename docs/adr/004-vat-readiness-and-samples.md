# ADR-004 — VAT treatment, quotation readiness and reference samples

Status: accepted. VAT taxes settled by the sources applied 22/10/2026; open: EX/NS for Spanish and Canary customers,
NS of CAU/QBR, Ceuta/Melilla (P17). P05 (pending costs) open.

## VAT class (Ángel)
- Ángel's rules (final, 31/08/2026; Odoo 19 `docs/iva_rules.md`, decision log B01/B02) are pure functions
  (`boss_pricing_sale/models/vat_rules.py`): **NS** = not subject by the nature of the product (never VAT), **EX** =
  would carry VAT but is exempt (by definition of the product or by the layers), **NR** = carries VAT. NR goes through
  the origin/destination zone pair (EX is final) and the customer zone (PRO keeps NR; CAN, COM, TER → EX). An NR
  becomes EX, never NS. A missing zone is pending, never guessed.
- B02 closed the rules but left «mapear NR/EX/NS a account.tax concretos» pending («necesita los códigos de Ángel»).

## Odoo tax of each case: BOSS VAT table (`boss.vat.tax`)
The tax depends on the class **and** the customer zone (and on whether the amount is paid on behalf), so it is a
table (class × customer zone × kind of service → tax, with its source), not one tax per class. A case without a row
keeps the line VAT **pending**. Rows exist only where three sources agree:

| Case | Odoo 20 tax (es_pymes template) | Ángel | Odoo 17 production (server action 1232 «Create Invoice», read-only) | Legal nature in Odoo 20 |
|---|---|---|---|---|
| NR | 21% S (`s_iva21s`) | NR carries VAT | NR → 21 % → tax «21% S» | subject; 303 [07]/[09] |
| EX, customer COM | 0% UE S (`s_iva0_sp_i`) | customer COM → EX | EU customer, zero rate → «0% EU S» («21% EU S» with zero amount for flagged concepts: same box 59) | not subject by place of supply; 303 [59], 349 |
| EX, customer TER | 0% EX S (`s_iva_e`) | customer TER → EX | third-country customer → «0% EX S», 303 [120] | not subject by place of supply; 303 [120] |
| NS, paid on behalf | 0% Exent NS (`s_iva0_ns`) | NS not subject by nature | concepts of type TAX (ARA, IVA, PLA, DUM) on a tax invoice → «0% EXEMPT NS», no box | not declared (`ignore`) |

Not mapped, with the conflict (Ángel's P17 question):
- **EX for a Spanish (PRO) or Canary (CAN) customer**: Ángel calls it exempt; Odoo 17 uses «0% S», which the
  localization defines as *subject at 0 %* (303 box 150), not exempt and not «not subject». The legal options are an
  exempt tax with its article (art. 21/22 → «Exento Art.22», box 60; art. 20…) or keeping Odoo 17's practice; for
  Canary customers also «not subject by place of supply» (box 120). Example: THC of an import from China for a
  customer in Valencia.
- **NS of services not paid on behalf (CAU, QBR)**: Odoo 17 invoices them on normal invoices with the customer-based
  zero-rate taxes (box 150/59/120), which contradicts «not subject by nature».
- **Ceuta and Melilla**: no zone in the rules.
Product default taxes are not used for BOSS services (they would be a guess). Purchase-side exceptions (TTE) do not
apply to quotations.

## Readiness
A quotation cannot be **sent or confirmed** while a BOSS line has VAT pending or a sale price missing (zero
without «free of charge»). A pending cost only warns (P05 open). The check runs in the server methods, so it
also applies to portal acceptance and RPC.

## Reference samples
- Real supplier tariffs used for validation live in a private file (never in Git). `boss.tariff.
  _boss_import_tariffs()` loads them idempotently (key in `ir.model.data`, existing records never rewritten),
  attaches the PDF and submits them; it never approves.
- Expected results are hand-computed from the documents by an independent reading, then compared with
  `boss.pricing` (test and server check with rollback). Expected values are never changed to make a test pass.
