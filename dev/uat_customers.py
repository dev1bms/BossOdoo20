"""Local copy only (boss_test): fictitious [DEMO] customers for the VAT cases of the accounting session (Canary
Islands, Ceuta, third country) and a fictitious Spanish tax ID with a valid check digit for case C2. Idempotent."""
from stdnum.es import cif

assert env.cr.dbname == "boss_test", env.cr.dbname  # noqa: F821
Partner = env["res.partner"]  # noqa: F821
es = env.ref("base.es")  # noqa: F821


def nif(seed):
    """Fictitious CIF with a valid check digit (the Spanish localization checks the format)."""
    return "ES" + next(c for n in range(seed, seed + 1000) for d in "0123456789" if cif.is_valid(c := f"B{n:07d}{d}"))


def state(code):
    return env["res.country.state"].search([("country_id", "=", es.id), ("code", "=", code)], limit=1)  # noqa: F821


for name, values in (
        ("[DEMO] Cliente Canarias", {"country_id": es.id, "state_id": state("GC").id, "vat": nif(7600000),
                                     "city": "Las Palmas de Gran Canaria", "zip": "35001"}),
        ("[DEMO] Cliente Ceuta", {"country_id": es.id, "state_id": state("CE").id, "vat": nif(5100000),
                                  "city": "Ceuta", "zip": "51001"}),
        ("[DEMO] Cliente Suiza", {"country_id": env.ref("base.ch").id, "city": "Basel", "zip": "4001"})):  # noqa: F821
    if not Partner.search([("name", "=", name)]):
        Partner.create(dict(values, name=name, is_company=True, boss_demo=True, street="Calle Ejemplo 1 [DEMO]"))
env.cr.commit()  # noqa: F821
print("UAT customers", Partner.search([("name", "in", ("[DEMO] Cliente Canarias", "[DEMO] Cliente Ceuta",
                                                        "[DEMO] Cliente Suiza"))]).mapped("name"),
      "| fictitious NIF for C2:", nif(1234567))
