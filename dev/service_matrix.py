"""Service readiness matrix (78 services) from the catalogue data + documented evidence. No prices.

    python dev/service_matrix.py        -> docs/matriz-servicios.md (also used by build_guide.py)

Status = what is needed before the service is priced automatically, by cause: a supplier document, a business
decision or a program function. Evidence = reference examples (hand-computed from supplier documents) and tests.
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dev"))
import build_guide as guide  # noqa: E402

# Current supplier documents with reference examples (docs/ejemplos-referencia.md; private samples).
VERIFIED = {
    "THC": "R1 (MSC 09/2026). Solo MSC: de Hapag y CMA no hay documento de gastos locales",
    "T3-PAD": "R2 (MSC). Solo MSC", "GLO-FUELEU": "R3 (MSC). Solo MSC",
    "BL": "R4 (MSC). Solo MSC: de Hapag y CMA no hay documento de gastos locales", "GLO-CCC": "R5 (MSC). Solo MSC", "DEM": "R8, R9 (MSC); R16 (Hapag, documento D&D); R18 (CMA, documento D&D)", "OCU": "R11, R12 (MSC VLC/BCN)",
    "ALM": "R01–R05 (WFS 2026: 48 h, mínimo, tramo de 7 días, periodos de 24 h, sábado, viernes > 72 h)",
    "HAN": "R06 (WFS 2026); R07, R08 (IRENEO 2025)", "AWB": "R09a (WFS 2026)", "X-R": "R10c (WFS 2026); R10a (IRENEO 2025)",
}
DOC_NOT_LOADED = {"GLO-LOG": "Documento MSC 09/2026 (solo exportación): sin muestra cargada"}
ONLY_2025 = {"TTE-CON": "R12 (IRENEO 2025, zona por provincia)", "SEG": "SEG (IRENEO 2025)",
             "FS": "Prueba del motor (porcentaje sobre servicios del mismo proveedor)"}
DECISION = {"P16": "P16 servicio sin definir", "P10": "P10 concepto ETX", "P09": "P09 DET propio o en DEM",
            "P03": "P03 cambio de moneda y QBR"}
DEFINITION = {  # where the service definition comes from, when not (only) the Odoo 17 concept
    "BL": "Odoo 17 DOC; máster por expediente (Cristina 28/09)", "GLO": "Cristina 28/09 (definición de GLO)",
    "GLO-CCC": "Documento MSC 09/2026", "GLO-FUELEU": "Documento MSC 09/2026", "GLO-LOG": "Documento MSC 09/2026",
    "T3-PAD": "Documento MSC; PAD bajo T3 (P11)", "FS": "Cristina 28/09 (% sobre el transporte del mismo transportista)",
    "DET": "Documentos Hapag/MSC D&D (P09)", "TTE-CON": "Odoo 17 TTE; tarifa IRENEO por zonas",
    "TTE-FCL": "Odoo 17 TTE", "PFT-AIR": "Odoo 17 PFT; nunca se vende (Cristina 28-29/09)",
    "ALM": "Odoo 17 ALM; eventos aprobados por Cristina (25/09)", "FTT": "Odoo 19; sustituido por TTE-CON",
}
SALE = {
    "own": ("Honorario BOSS: lista de precios del cliente o tecleado", "BOSS fee: customer pricelist or typed"),
    "suplido": ("A coste del DUA (práctica Odoo 17), tecleado; P18", "At the customs-declaration cost (Odoo 17 practice), typed; P18"),
    "pft": ("No se vende", "Not sold"),
    "alm": ("Venta unificada aprobada como concepto (Cristina 08/10), valores pendientes: lista del cliente o tecleada",
            "Unified sale approved as a concept (Cristina 08/10), values pending: customer pricelist or typed"),
    "client": ("Según cliente (Cristina 08/10): lista del cliente (fija o sobre coste) o tecleada",
               "Per customer (Cristina 08/10): customer pricelist (fixed or on cost) or typed"),
    "default": ("Lista de precios del cliente (fija o sobre coste) o tecleada",
                "Customer pricelist (fixed or on cost) or typed"),
}
LIMITS = {
    "ALM": ("Viernes 72 h solo si sale el lunes: no se aplica en la oferta (día de salida desconocido)",
            "Friday 72 h only with a Monday exit: not applied on the quotation (exit day unknown)"),
    "DEM": ("Una estimación de días por oferta, común a DEM/OCU/ALM", "One days estimate per quotation, shared by DEM/OCU/ALM"),
    "OCU": ("Una estimación de días por oferta, común a DEM/OCU/ALM", "One days estimate per quotation, shared by DEM/OCU/ALM"),
    "THC": ("IVA dividido (parte EX, resto NR) sin decidir (P11)", "Split VAT (part EX, rest NR) not decided (P11)"),
    "QBR": ("Necesita además la política de moneda", "Also needs the currency policy"),
}
LABELS = {
    "es": {"auto": "Automática verificada (falta aprobar la tarifa)", "doc": "Automática: falta documento de tarifa",
           "2025": "Automática: documento 2025, vigencia 2026 sin confirmar (P28)",
           "loaded": "Automática: documento disponible, falta cargar la tarifa", "manual": "Lista con importe manual",
           "own": "Lista: honorario sin coste", "decision": "Bloqueada por decisión", "inactive": "Retirada"},
    "en": {"auto": "Automatic, verified (tariff approval pending)", "doc": "Automatic: tariff document missing",
           "2025": "Automatic: 2025 document, 2026 validity unconfirmed (P28)",
           "loaded": "Automatic: document available, tariff not entered yet", "manual": "Ready with a manual amount",
           "own": "Ready: fee without cost", "decision": "Blocked by a decision", "inactive": "Retired"},
}
HEAD = {
    "es": "| Código | Servicio | Definición (fuente) | Compra | Venta | Condiciones y límites | Estado | Evidencia |",
    "en": "| Code | Service | Definition (source) | Purchase | Sale | Conditions and limits | Status | Evidence |",
}


def status(s):
    if not s["active"]:
        return "inactive", "FTT → TTE-CON"
    if s["mode"] == "pending":
        q = s["question"]
        return "decision", DECISION.get(q, q or "")
    if s["mode"] == "manual":
        return "manual", "Oferta del proveedor o DUA (por naturaleza)"
    if s["mode"] == "own":
        return "own", "Sin coste de proveedor"
    if s["code"] in VERIFIED:
        return "auto", VERIFIED[s["code"]]
    if s["code"] in DOC_NOT_LOADED:
        return "loaded", DOC_NOT_LOADED[s["code"]]
    if s["code"] in ONLY_2025:
        return "2025", ONLY_2025[s["code"]]
    return "doc", "Método probado con otros servicios; sin documento del proveedor"


def sale(s, i):
    code = s["code"]
    if not s["sale"]:
        key = "pft"
    elif s["mode"] == "own":
        key = "own"
    elif code in ("ARA", "IVA", "PLA", "DUM"):
        key = "suplido"
    elif code == "ALM":
        key = "alm"
    elif code in ("THC", "GLO", "GLO-CCC", "GLO-LOG", "GLO-FUELEU", "T3-PAD", "BL"):
        key = "client"
    else:
        key = "default"
    return SALE[key][i]


def rows(lang):
    i = 0 if lang == "es" else 1
    srv, uom_name = guide.services()
    out, counts = [], Counter()
    for s in sorted(srv, key=lambda s: s["code"]):
        st, evidence = status(s)
        counts[st] += 1
        units = ", ".join(uom_name[u][i] for u in [s["uom"]] + s["extra"] if u in uom_name)
        purchase = f"{guide.METHOD.get(s['method'], ('—', '—'))[i]} · {units}"
        if s["mode"] == "manual":
            purchase = ("Importe manual · " if i == 0 else "Manual amount · ") + units
        elif s["mode"] == "own":
            purchase = "—"
        notes = guide.NOTES.get(s["code"], ("", ""))[i]
        limit = LIMITS.get(s["code"], ("", ""))[i]
        cond = " ".join(x for x in (notes, ("Límite: " if i == 0 else "Limit: ") + limit if limit else "") if x) or "—"
        definition = DEFINITION.get(s["code"]) or (f"Odoo 17 {s['o17']}" if s["o17"] else "—")
        name = s["name"][lang].split(" (")[0]
        out.append(f"| [{s['code']}](#/srv-{s['code'].lower()}) | {name} | {definition} | {purchase} | {sale(s, i)} | "
                   f"{cond} | {LABELS[lang][st]} | {evidence} |")
    summary = " · ".join(f"{LABELS[lang][k]}: {counts[k]}" for k in LABELS[lang] if counts[k])
    return summary, [HEAD[lang], "|" + "---|" * 8] + out


def page(lang):
    summary, table = rows(lang)
    intro = {
        "es": ("Estado de los 78 servicios: de dónde sale su definición, cómo se calcula la compra y la venta, sus "
               "condiciones y qué falta para que el precio sea automático. Se distingue lo que falta: un **documento "
               "de tarifa** del proveedor, una **decisión** de negocio o una **función** del programa (hoy ningún "
               "servicio está bloqueado solo por una función). Las tarifas verificadas siguen **pendientes de "
               "aprobación** por una persona."),
        "en": ("Status of the 78 services: where the definition comes from, how purchase and sale are computed, their "
               "conditions and what is missing for an automatic price: a supplier **tariff document**, a business "
               "**decision** or a program **function** (today no service is blocked by a function only). Verified "
               "tariffs still wait for **approval** by a person."),
    }[lang]
    return intro + "\n\n**" + summary + "**\n\n" + "\n".join(table)


def main():
    text = ("# Matriz de servicios · Service matrix\n\nGenerado por `dev/service_matrix.py` desde el catálogo "
            "(`boss_services`) y las evidencias documentadas. Sin precios.\n\n" + page("es") + "\n")
    (ROOT / "docs" / "matriz-servicios.md").write_bytes(text.replace("](#/srv-", "](guide/index.html#/srv-").encode("utf-8"))
    print(rows("es")[0])


if __name__ == "__main__":
    main()
