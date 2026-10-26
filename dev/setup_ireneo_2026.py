"""IRENEO 2026: version of the IRENEO road-transport tariff with the written update of IRENEO (letter of 14/07/2026,
attached to the e-mail «IRENEO SPAIN - Actualización del Recargo por Combustible conforme a RDL 9_2026»): by the
Real Decreto-ley 9/2026 «las tarifas aplicables a los servicios de transporte se incrementarán en un 10%» (the letter
prints «a partir del día 15/07/2025»; letter and PDF are dated 14/07/2026 and the decree is of 2026: from 15/07/2026).

    dev/server_shell.sh setup_ireneo_2026.py .research/ireneo-carta-2026-07-14.pdf "<NEW ODOO>/IRENEO/TARIFAS MAD 2025.pdf"

Both files are identified by their SHA-256 (never «the first PDF of a folder») and checked before anything is written:
- the letter: hash + the sentences that carry the rule (decree, 10 %, transport services, date);
- the base: «TARIFAS MAD 2025.pdf» p.6 «TARIFA DISTRIBUCION NACIONAL», zone-3 column (28 weight steps) and p.7 list of
  zone-3 provinces, compared one by one with the 2025 tariff already in Odoo. Only counts are printed (prices are
  confidential and stay out of Git).
The 2026 version: same scope (15 provinces of zone 3, any direction and mode), valid from 15/07/2026, no end (the letter
gives none); TTE-CON amounts × 1.10 (per-shipment amounts to cents, per-kg prices to 4 decimals); SEG (insurance, %)
unchanged; handling (HAN, X-R) is not transport and is not versioned. The tariff is left WAITING FOR APPROVAL: approval is
Cristina's, never this script's. Idempotent: an existing version waiting for approval with other amounts is set back to
draft, corrected and sent again.

From 01/01/2026 to 14/07/2026 the 2025 prices apply: «TARIFAS MAD 2025.pdf — mismos precios en 2026 (confirmado por
Ángel, 14/10/2026)» (document reference of the IRENEO MAD 2026 tariffs of Odoo 19, boss_uat, quoted in quotation
S03541 of 15/10/2026). So the script also creates, from the same verified document: the zone-3 transport at 2025 prices
for 01/01-14/07/2026, and the handling tariffs (terminal pickups, Barajas export package: not transport, the letter does
not change them) at 2025 prices for 2026. All waiting for Cristina's approval."""
import hashlib
import os
import re
from datetime import date

from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
LETTER = ("ireneo-carta-2026-07-14.pdf", "bb5d0399e878f64b40e2bc4d1b16d7460715c49fa767d32d9bb119bb0ff4eb89")
BASE_PDF = ("TARIFAS MAD 2025.pdf", "71459edc1fe6108f8b1885fcc363f7ad45213d3dba147f67bccf65665ce02e42")
BASE_NAME = "[MUESTRA] IRENEO distribución nacional zona 3 2025"
NAME = "[MUESTRA] IRENEO distribución nacional zona 3 2026 (+10 % transporte, carta 14/07/2026)"
ZONE3 = {"ALICANTE": "A", "BADAJOZ": "BA", "CASTELLON": "CS", "CORDOBA": "CO", "GRANADA": "GR", "HUESCA": "HU",
         "JAEN": "J", "LEON": "LE", "LOGRONO": "LO", "MURCIA": "MU", "OVIEDO": "O", "PAMPLONA": "NA", "VALENCIA": "V",
         "VITORIA": "VI", "ZARAGOZA": "Z"}
STEPS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900,
         1000, 1500, 2000, 2500, 3000]
VALID_FROM = date(2026, 7, 15)


def mounted(name, sha):
    files = [f for f in os.environ.get("BOSS_FILES", "").split("|") if f]
    assert name in files, f"{name} not given (got {files})"
    with open(f"/tmp/boss/{name}", "rb") as handle:
        data = handle.read()
    got = hashlib.sha256(data).hexdigest()
    assert got == sha, f"{name}: SHA-256 {got} is not the expected document"
    return data


def pdf_pages(data):
    import io  # noqa: PLC0415

    from pypdf import PdfReader  # noqa: PLC0415
    return [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]


def number(token):
    return float(token.replace(".", "").replace(",", ".")) if "," in token else float(token)


def plain(text):
    return text.upper().translate(str.maketrans("ÁÉÍÓÚÑ", "AEIOUN"))


# 1. The letter
letter = mounted(*LETTER)
text = " ".join(" ".join(pdf_pages(letter)).split())
for phrase in ("14/07/2026", "Real Decreto-ley 9/2026", "servicios de transporte se incrementarán en un 10%"):
    assert phrase in text, f"letter: «{phrase}» not found"
print("LETTER ok: sha256", LETTER[1][:12], "| decree 9/2026, +10 % on transport services, dated 14/07/2026")

# 2. The base tariff against its source document
pages = pdf_pages(mounted(*BASE_PDF))
# pypdf doubles the letters of the bold title («TTAARRIIFFAA DDIISSTTRRIIBBUUCCIIOONN»)
assert re.search(r"D+I+S+T+R+I+B+U+C+I+O+N+\s+N+A+C+I+O+N+A+L+", plain(pages[5])) and "KILOS" in plain(pages[5]), \
    "p.6 is not the national distribution table"
tokens = re.findall(r"\d+(?:\.\d{3})*(?:,\d+)?", pages[5])
start = next(i for i in range(len(tokens) - 9) if tokens[i] == "10" and "," in tokens[i + 1] and "," in tokens[i + 8])
rows = [tokens[start + 9 * k: start + 9 * k + 9] for k in range(len(STEPS))]
assert [int(r[0]) for r in rows] == STEPS, f"p.6: weight steps not as expected: {[r[0] for r in rows]}"
zone3 = {step: number(row[3]) for step, row in zip(STEPS, rows)}  # columns: kilos, zona 1, zona 2, zona 3...
Tariff = env["boss.tariff"]
base = Tariff.search([("name", "=", BASE_NAME)], limit=1)
assert base, BASE_NAME
tte = base.line_ids.filtered(lambda l: l.product_id.default_code == "TTE-CON")
assert len(tte) == 1
brackets = {int(b.up_to): (b.fixed_amount or b.unit_price) for b in tte.bracket_ids}
same = sum(1 for step in STEPS if abs(brackets.get(step, -1) - zone3[step]) < 0.0005)
assert same == len(STEPS), f"base tariff differs from p.6 zone 3 in {len(STEPS) - same} of {len(STEPS)} steps"
p7 = " ".join(plain(pages[6]).split()) + " "
missing = [city for city in ZONE3 if not re.search(rf"\b{city}\s+3\b", p7)]
assert not missing, f"p.7: not in zone 3: {missing}"
assert set(base.state_ids.mapped("code")) == set(ZONE3.values()), base.state_ids.mapped("code")
print(f"BASE ok: sha256 {BASE_PDF[1][:12]} | p.6 zone 3 = {same}/{len(STEPS)} steps equal to «{BASE_NAME}» | "
      f"p.7 zone 3 = {len(ZONE3)} provinces = tariff provinces")

# 3. The 2026 version
expected = {int(b.up_to): (round(b.fixed_amount * 1.10, 2), round(b.unit_price * 1.10, 4)) for b in tte.bracket_ids}
new = Tariff.search([("name", "=", NAME)], limit=1)
if not new:
    new = base.copy({"name": NAME, "valid_from": VALID_FROM, "valid_to": False})
if new.state == "approved":
    raise SystemExit(f"{NAME} is already approved by {new.approved_by_id.name}: nothing changed")
if new.state == "to_approve":
    new.action_back_to_draft()
new.write({
    "valid_from": VALID_FROM, "valid_to": False, "scope_confirmed": True,
    "document": BinaryBytes(letter, filename=LETTER[0]), "document_name": LETTER[0],
    "document_reference": f"Carta IRENEO 14/07/2026 (RDL 9/2026, +10 % transporte desde 15/07/2026; sha256 "
                          f"{LETTER[1][:12]}) sobre TARIFAS MAD 2025 p.6-7 zona 3 (sha256 {BASE_PDF[1][:12]})",
    "note": "Versión 2026 desde «" + BASE_NAME + "»: TTE-CON × 1,10 según la carta de IRENEO del 14/07/2026 (la carta "
            "pone 15/07/2025 por errata: carta, PDF y decreto son de 2026). SEG sin cambio. HAN y X-R (manipulación) no "
            "son transporte: siguen en las tarifas de 2025. Comprobada contra el documento por dev/setup_ireneo_2026.py.",
})
new_tte = new.line_ids.filtered(lambda l: l.product_id.default_code == "TTE-CON")
for b in new_tte.bracket_ids:
    fixed, unit = expected[int(b.up_to)]
    b.write({"fixed_amount": fixed, "unit_price": unit})
got = {int(b.up_to): (round(b.fixed_amount, 2), round(b.unit_price, 4)) for b in new_tte.bracket_ids}
assert got == expected, "2026 brackets not equal to 2025 × 1.10"
seg = {t: t.line_ids.filtered(lambda l: l.product_id.default_code == "SEG").rate for t in (base, new)}
assert new.state_ids == base.state_ids and seg[new] == seg[base]
new.action_submit()
assert new.state == "to_approve" and not new.approved_by_id
print(f"VERSION ok: «{new.name}» {new.state}, valid from {new.valid_from}, no end, {len(got)} TTE-CON steps = 2025 × 1.10 "
      f"(cents / 4 decimals per kg), SEG unchanged, document = letter; approval left to Cristina")

# 4. 2025 prices in 2026 (Ángel, 14/10/2026): zone 3 until 14/07, handling for the whole year
p7 = " ".join(pages[6].split())
assert "0,040 €/kg" in p7 and "Mínimo 9,00" in p7, "p.7: terminal pickup price not found"
pickup = Tariff.search([("name", "=", "[MUESTRA] IRENEO MAD recogidas en terminal 2025")], limit=1)
han = pickup.line_ids.filtered(lambda l: l.product_id.default_code == "HAN")
assert (round(han.unit_price, 3), round(han.min_amount, 2)) == (0.04, 9.0), "terminal pickup tariff differs from p.7"
print("BASE ok: «[MUESTRA] IRENEO MAD recogidas en terminal 2025» = p.7 «0,040 €/kg (Mínimo 9,00 €)»")
SAME = "Mismos precios que TARIFAS MAD 2025 en 2026 (confirmado por Ángel, 14/10/2026; referencia de las tarifas IRENEO "        f"MAD 2026 de Odoo 19); documento sha256 {BASE_PDF[1][:12]}"
plan = [
    (base, "[MUESTRA] IRENEO distribución nacional zona 3 2026 hasta 14/07 (precios 2025)", date(2026, 1, 1),
     date(2026, 7, 14)),
    (pickup, "[MUESTRA] IRENEO MAD recogidas en terminal 2026 (precios 2025)", date(2026, 1, 1), False),
    (Tariff.search([("name", "=", "[MUESTRA] IRENEO MAD exportación Barajas 2025")], limit=1),
     "[MUESTRA] IRENEO MAD exportación Barajas 2026 (precios 2025)", date(2026, 1, 1), False),
]
base_pdf_data = mounted(*BASE_PDF)
for source, name, valid_from, valid_to in plan:
    assert source, name
    version = Tariff.search([("name", "=", name)], limit=1)
    if version.state == "approved":
        print("approved, not changed:", name)
        continue
    if not version:
        version = source.copy({"name": name})
    if version.state == "to_approve":
        version.action_back_to_draft()
    version.write({"valid_from": valid_from, "valid_to": valid_to, "scope_confirmed": True,
                   "document": BinaryBytes(base_pdf_data, filename=BASE_PDF[0]), "document_name": BASE_PDF[0],
                   "document_reference": SAME,
                   "note": "Precios de «" + source.name + "» sin cambio en 2026 (Ángel, 14/10/2026). Creada por "
                           "dev/setup_ireneo_2026.py; la aprobación es de Cristina."})
    same_prices = all(
        (a.unit_price, a.min_amount, a.max_amount, a.rate) == (b.unit_price, b.min_amount, b.max_amount, b.rate)
        and [(x.up_to, x.unit_price, x.fixed_amount) for x in a.bracket_ids] ==
        [(x.up_to, x.unit_price, x.fixed_amount) for x in b.bracket_ids]
        for a, b in zip(source.line_ids.sorted("id"), version.line_ids.sorted("id")))
    assert same_prices and len(source.line_ids) == len(version.line_ids), name
    version.action_submit()
    print(f"VERSION ok: «{name}» {version.state}, {valid_from} → {valid_to or 'no end'}, "
          f"{len(version.line_ids)} prices = 2025, document = TARIFAS MAD 2025")
env.cr.commit()
