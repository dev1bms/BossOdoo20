"""Build the user guide data (docs/guide/data/*.js) from docs/guide/src and the module data.

    python dev/build_guide.py

Service pages are generated from boss_services (single source of names, units, methods, VAT class) plus the
supplier conditions below. Public site: only illustrative amounts, no supplier prices.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dev"))
from po_merge import parse  # noqa: E402

GUIDE = ROOT / "docs" / "guide"
ADDON = ROOT / "addons" / "boss_services"

FAMILIES = {
    "srv-maritimo": "FMI FMI-LCL FME FME-LCL THC THC-LCL GLO GLO-CCC GLO-LOG GLO-FUELEU T3 T3-PAD BL DOC CES VGM COR ENS AMS POT",
    "srv-tiempo": "DEM OCU ALM",
    "srv-aereo": "FAI FAE HAN AWB X-R",
    "srv-aduanas": "FAD DEX CAU EUR1 TRA SAD ROH SOI INS SAN FAR",
    "srv-terrestre": "TTE-CON TTE-FCL FS PAR FTT",
    "srv-agentes": "EXW EXW-AIR EXW-FCL EXW-LCL DAP DAP-CON PFT-AIR PFT-FCL PFT-LCL",
    "srv-almacen": "OAL-CON OAL-PAL PAL FUM MEN",
    "srv-propios": "CSM CSA CST SEG GLL ARA PLA IVA",
}
FAMILY_OF = {code: fam for fam, codes in FAMILIES.items() for code in codes.split()}

# Supplier conditions read from the documents and owners' answers (no prices: public site).
NOTES = {
    "THC": ("MSC: mismo precio para cualquier tamaño; varía por tráfico (short sea), Canarias y servicio ferroviario de Sevilla. Venta según cliente (Cristina).",
            "MSC: same price for any size; it varies by trade (short sea), Canaries and the Seville rail service. Sale price depends on the customer (Cristina)."),
    "THC-LCL": ("El mayor de toneladas × precio y m³ × precio (Cristina 28/09). No hay tarifa de consolidador disponible todavía.",
                "The larger of tonnes × price and m³ × price (Cristina 28/09). No consolidator tariff available yet."),
    "T3": ("Por tonelada (exacta o «o fracción» según el documento) o por tipo de contenedor; distinta en importación y exportación (Cristina 28/09).",
           "Per tonne (exact or «or fraction» as the document says) or per container type; different for import and export (Cristina 28/09)."),
    "T3-PAD": ("MSC: por tamaño 20'/40'/45'; en importación «T-3 incluido».", "MSC: per size 20'/40'/45'; import says «T-3 included»."),
    "GLO": ("Todo cargo fijo de naviera que no es T3, BL/DOC, CES ni DEM/OCU/DET; las líneas se suman (Cristina 28/09).",
            "Every fixed carrier charge that is not T3, BL/DOC, CES or DEM/OCU/DET; the lines add up (Cristina 28/09)."),
    "GLO-CCC": ("MSC: importación, solo equipo Dry (otro precio para reefer no operativo).", "MSC: import, Dry equipment only (another price for non-operating reefers)."),
    "GLO-LOG": ("MSC: solo en exportación.", "MSC: export only."),
    "GLO-FUELEU": ("MSC: por TEU en importaciones desde el Lejano Oriente (lista de países pendiente, P24).",
                   "MSC: per TEU on imports from the Far East (country list pending, P24)."),
    "BL": ("Una vez por expediente (máster). MSC: precio EDI más bajo solo si booking e instrucciones van por EDI.",
           "Once per shipment (master). MSC: lower EDI price only when booking and instructions go through EDI."),
    "DEM": ("MSC: días libres y «5 días a X, después Y» por tamaño (Dry, Special, IMO). Hapag: demora y detención juntas, periodos tras los días libres. CMA: días naturales, tramos por número de día. Inicio y fin según cada naviera (p. ej. llegada del buque → devolución del vacío).",
            "MSC: free days then «5 days at X, then Y» per size (Dry, Special, IMO). Hapag: demurrage and detention combined, periods after free days. CMA: calendar days, tiers by day number. Start and end events per carrier (e.g. vessel arrival → empty return)."),
    "OCU": ("MSC: por grupo de puertos, tramos por número de día («del día 5 al 7»), columnas 20'DV y 40'DV.",
            "MSC: per port group, tiers by day number («day 5 to 7»), 20'DV and 40'DV columns."),
    "ALM": ('WFS MAD/BCN, carga general (V 2026-02 desde 01/06/2026, p.5 punto 1): por 100 kg del peso cargable de la AWB y por 24 horas, desde el NOA (importación) o el FOH (exportación) hasta la retirada (importación) o la ETD (exportación; eventos de Cristina 25/09). 48 h libres en horas reales; superadas, se cobra desde el NOA/FOH incluido (Cristina 08/09, B20). Viernes con salida el lunes: 72 h; sábado: libre hasta el lunes incluido (con las fechas reales; la estimación de la oferta no las supone). Mínimo propio de importación y de exportación, por estancia (el documento no imprime la unidad, P42). **Sin decidir:** periodos de 24 h o días naturales (P40), precio de «más de 7 días» en los días siguientes o en toda la estancia (P29), «por 100 kg» con o sin fracción (P41): si dan importes distintos no hay coste automático y se muestran todos. Solo carga general: frío, peligrosas, valiosas y animales vivos (puntos 2–6) tienen otros periodos y precios: coste manual. La franquicia exige el handling básico pagado. IRENEO 2025 (por 100 kg o fracción y día natural, cuentan entrada y salida): vigencia 2026 sin confirmar (P28), no cargada. Almacén fuera del aeropuerto (palé, m³, entrada/salida): código propio pendiente de Cristina y Ángel, no se cotiza con ALM. Guía: [ALM paso a paso](#/almacenaje).',
            'WFS MAD/BCN, general cargo (V 2026-02 from 01/06/2026, p.5 item 1): per 100 kg of the AWB chargeable weight and per 24 hours, from the NOA (import) or FOH (export) to the pickup (import) or the ETD (export; events from Cristina 25/09). 48 h free in real hours; once exceeded, charged from the NOA/FOH included (Cristina 08/09, B20). Friday with a Monday exit: 72 h; Saturday: free until Monday included (with the actual dates; the quotation estimate does not assume them). Own minimum for import and for export, per stay (the document prints no unit, P42). **Not decided:** 24-hour periods or calendar days (P40), the «more than 7 days» price on the following days or on the whole stay (P29), «per 100 kg» with or without fraction (P41): when they give different amounts there is no automatic cost and all of them are shown. General cargo only: cold room, dangerous, valuable goods and live animals (items 2–6) have other periods and prices: manual cost. The free period requires the basic handling paid. IRENEO 2025 (per 100 kg or fraction and calendar day, entry and exit days counted): 2026 validity unconfirmed (P28), not entered. Warehouse storage outside the airport (pallet, m³, entry/exit): its own code is pending Cristina and Ángel, not quoted with ALM. Guide: [ALM step by step](#/almacenaje).'),
    "HAN": ("WFS: por kg tasable de la AWB con mínimo por AWB. IRENEO: por kg tasable (factor 333) con mínimo; paquete de exportación por tramos con «no inferior al tramo anterior».",
            "WFS: per AWB chargeable kg with a minimum per AWB. IRENEO: per chargeable kg (factor 333) with a minimum; export package by brackets with «not below the previous bracket»."),
    "AWB": ("WFS: por AWB en importación (gestión DATA/DOCS).", "WFS: per AWB on imports (DATA/DOCS handling)."),
    "X-R": ("WFS PNS: tramos por kg con mínimo y máximo por AWB. IRENEO: por kg real con mínimo y máximo.",
            "WFS PNS: brackets per kg with minimum and maximum per AWB. IRENEO: per real kg with minimum and maximum."),
    "TTE-CON": ("IRENEO: por zona (provincias) y tramos de peso tasable (factor 333), «no inferior al tramo anterior», tabla cerrada a 3.000 kg.",
                "IRENEO: per zone (provinces) and chargeable-weight brackets (factor 333), «not below the previous bracket», table closed at 3,000 kg."),
    "FS": ("% sobre el transporte del mismo transportista (Cristina 28/09). IRENEO: porcentaje y fecha pendientes (P28).",
           "% of the same haulier's transport (Cristina 28/09). IRENEO: rate and date pending (P28)."),
    "SEG": ("IRENEO: porcentaje sobre el transporte con mínimo por expedición, en mercancía no asegurada por el cliente. Otras tasas pendientes (P13).",
            "IRENEO: percentage of transport with a minimum per shipment, for goods not insured by the customer. Other rates pending (P13)."),
    "CAU": ("% de los impuestos del DUA con mínimo; valores pendientes (P13).", "% of the declaration duties with a minimum; values pending (P13)."),
    "FAD": ("Por DUA; algunos agentes por contenedores (base + adicionales con tope). Sin tarifa vigente disponible.",
            "Per declaration; some brokers per containers (base + extra with a cap). No current tariff available."),
    "PFT-AIR": ("Coste pactado con el agente; nunca se vende como línea (Cristina 28-29/09).", "Cost agreed with the agent; never sold as a line (Cristina 28-29/09)."),
    "CSM": ("Honorario propio de BOSS: sin coste; venta según el honorario de BOSS.", "BOSS own fee: no cost; sale per BOSS fee."),
}
NOTES["PFT-FCL"] = NOTES["PFT-LCL"] = NOTES["PFT-AIR"]
NOTES["CSA"] = NOTES["CST"] = NOTES["CSM"]

EXAMPLES = {  # illustrative amounts only
    ("per_unit", "container"): ("2 contenedores de 20' × 100,00 € = 200,00 €", "2 containers of 20' × 100.00 € = 200.00 €"),
    ("per_unit", "teu"): ("1 × 20' + 1 × 40' = 3 TEU × 10,00 € = 30,00 €", "1 × 20' + 1 × 40' = 3 TEU × 10.00 € = 30.00 €"),
    ("per_unit", "shipment"): ("1 expediente × 50,00 € = 50,00 €", "1 shipment × 50.00 € = 50.00 €"),
    ("per_unit", "doc"): ("2 documentos × 30,00 € = 60,00 €", "2 documents × 30.00 € = 60.00 €"),
    ("per_unit", "kg"): ("500 kg × 0,05 € = 25,00 € (mínimo 2,00 €)", "500 kg × 0.05 € = 25.00 € (minimum 2.00 €)"),
    ("per_unit", "m3"): ("3 m³ × 20,00 € = 60,00 €", "3 m³ × 20.00 € = 60.00 €"),
    ("per_unit", "ton"): ("2,3 t × 3,00 € = 6,90 € (9,00 € si el documento dice «o fracción»)", "2.3 t × 3.00 € = 6.90 € (9.00 € if the document says «or fraction»)"),
    ("per_unit", "pallet"): ("4 palés × 15,00 € = 60,00 €", "4 pallets × 15.00 € = 60.00 €"),
    ("per_unit", "hour"): ("2 horas × 50,00 € = 100,00 €", "2 hours × 50.00 € = 100.00 €"),
    ("max_of_bases", None): ("máx(2,5 t × 20 €; 4 m³ × 10 €) = 50,00 €", "max(2.5 t × 20 €; 4 m³ × 10 €) = 50.00 €"),
    ("brackets", None): ("1.200 kg en el tramo «hasta 1.500»: 1.200 × 0,18 € = 216,00 € (y nunca menos que el tramo anterior si el documento lo dice)",
                         "1,200 kg in the «up to 1,500» bracket: 1,200 × 0.18 € = 216.00 € (never below the previous bracket when the document says so)"),
    ("time", "container"): ("15 días, 7 libres, «5 días a 30 €, después 80 €»: 390,00 € por contenedor (estimación)",
                            "15 days, 7 free, «5 days at 30 €, then 80 €»: 390.00 € per container (estimate)"),
    ("time", None): ("500 kg, umbral 48 h, 10 € por 100 kg y periodo de 24 h: NOA lunes 10:00 → retirada miércoles 10:00 "
                     "(48 h) = 0,00 €; miércoles 10:01 (48 h 01 min) = 3 × 5 × 10 = 150,00 €, desde el NOA",
                     "500 kg, 48 h threshold, 10 € per 100 kg and 24-hour period: NOA Monday 10:00 → pickup Wednesday 10:00 "
                     "(48 h) = 0.00 €; Wednesday 10:01 (48 h 01 min) = 3 × 5 × 10 = 150.00 €, from the NOA"),
    ("percent", None): ("5 % de 300,00 € = 15,00 €", "5 % of 300.00 € = 15.00 €"),
    ("manual", None): ("Coste de la oferta del proveedor: 1.000,00 € (con su referencia)", "Cost of the supplier offer: 1,000.00 € (with its reference)"),
    ("none", None): ("Sin coste; venta según el honorario de BOSS", "No cost; sale per BOSS fee"),
}
UOM_KIND = {"uom_container": "container", "uom_teu": "teu", "uom_shipment": "shipment", "uom_bl": "doc", "uom_awb": "doc",
            "uom_declaration": "doc", "uom_document": "doc", "uom_kg_gross": "kg", "uom_kg_air": "kg", "uom_kg_road": "kg",
            "uom_ton": "ton", "uom_m3": "m3", "uom_wm": "m3", "uom_pallet": "pallet", "uom_hour": "hour"}
MODE = {"tariff": ("Tarifa de proveedor (cálculo automático)", "Supplier tariff (automatic calculation)"),
        "manual": ("Importe manual (oferta del proveedor o a coste)", "Manual amount (supplier offer or at cost)"),
        "own": ("Honorario propio de BOSS (sin coste)", "BOSS own fee (no cost)"),
        "pending": ("Pendiente de decisión de negocio", "Pending business decision")}
METHOD = {"per_unit": ("Precio por unidad", "Price per unit"), "max_of_bases": ("El mayor de dos bases", "Larger of two bases"),
          "brackets": ("Tramos", "Brackets"), "time": ("Por día con periodo libre", "Per day with free period"),
          "percent": ("Porcentaje de una base", "Percentage of a base"), "manual": ("Importe manual", "Manual amount"),
          "none": ("Sin coste", "No cost")}
INPUTS = {"container": ("Contenedores (tamaño, tipo, cantidad), naviera, puerto y fecha prevista", "Containers (size, type, quantity), carrier, port and planned date"),
          "teu": ("Contenedores (tamaño), naviera, país de origen y fecha prevista", "Containers (size), carrier, origin country and planned date"),
          "shipment": ("Sentido, modo, naviera/proveedor y fecha prevista", "Direction, mode, carrier/supplier and planned date"),
          "doc": ("Número de documentos en la línea, sentido y fecha prevista", "Number of documents on the line, direction and planned date"),
          "kg": ("Peso bruto y volumen (o peso tasable de la AWB), aeropuerto/provincia y fecha prevista", "Gross weight and volume (or AWB chargeable weight), airport/province and planned date"),
          "ton": ("Peso bruto o contenedores, puerto y fecha prevista", "Gross weight or containers, port and planned date"),
          "m3": ("Peso bruto y volumen, fecha prevista", "Gross weight and volume, planned date"),
          "pallet": ("Palés, fecha prevista", "Pallets, planned date"), "hour": ("Horas en la línea", "Hours on the line")}
METHOD_INPUTS = {
    "time": ("Días de estancia estimados (pestaña Envío, Estimaciones), contenedores o peso tasable de la AWB, proveedor y fecha prevista; "
             "en la oferta el resultado es una estimación. Con el inicio y el fin reales del periodo (expediente o «Probar tarifa») se "
             "calcula el periodo real",
             "Estimated days of stay (Shipment tab, Estimates), containers or AWB chargeable weight, supplier and planned date; "
             "on the quotation the result is an estimate. With the actual start and end of the period (file or «Test pricing») the "
             "actual period is computed"),
    "percent": ("La base del porcentaje: valor de la mercancía, impuestos del DUA o coste de otros servicios del mismo proveedor en la oferta",
                "The percentage base: goods value, declaration duties or cost of other services of the same supplier on the quotation"),
    "max_of_bases": ("Peso bruto y volumen, proveedor y fecha prevista", "Gross weight and volume, supplier and planned date"),
    "brackets": ("La cantidad de los tramos (peso, peso tasable o contenedores), zona o provincia si la tarifa la usa, y fecha prevista",
                 "The bracket quantity (weight, chargeable weight or containers), zone or province when the tariff uses it, and planned date"),
}
VAT = {"NS": ("NS - no sujeto (nunca IVA)", "NS - not subject (never VAT)"), "EX": ("EX - exento", "EX - exempt"),
       "NR": ("NR - reglas de origen/destino y cliente", "NR - origin/destination and customer rules")}


def po_map(path):
    out = {}
    for comments, msgid, msgstr in parse(path):
        for c in comments:
            m = re.match(r"#: (model(?:_terms)?):([\w.]+),(\w+):boss_services\.(\w+)", c)
            if m:
                out[(m.group(2), m.group(3), m.group(4))] = (msgid, msgstr)
    return out


def services():
    po = po_map(ADDON / "i18n" / "es.po")
    uoms = {r.get("id"): r for r in ET.parse(ADDON / "data" / "uom_data.xml").getroot()}
    uom_name = {xid: (po.get(("uom.uom", "name", xid), ("", ""))[1] or rec.findtext("field[@name='name']"),
                      rec.findtext("field[@name='name']")) for xid, rec in uoms.items()}
    out = []
    for rec in ET.parse(ADDON / "data" / "product_data.xml").getroot():
        if rec.get("model") != "product.template":
            continue
        f = {fld.get("name"): fld for fld in rec}
        xid = rec.get("id")
        val = lambda n: (f[n].text or "").strip() if n in f else ""  # noqa: E731
        ref = lambda n: f[n].get("ref") if n in f else None  # noqa: E731
        extra = re.findall(r"ref\('(\w+)'\)", f["uom_ids"].get("eval", "")) if "uom_ids" in f else []
        name_en = val("name")
        desc_en = val("description")
        out.append({
            "xid": xid, "code": val("default_code"), "name": {"es": po.get(("product.template", "name", xid), ("", ""))[1] or name_en, "en": name_en},
            "desc": {"es": po.get(("product.template", "description", xid), ("", ""))[1] or desc_en, "en": desc_en},
            "uom": ref("uom_id"), "extra": extra, "mode": val("boss_pricing_mode"), "method": val("boss_cost_method"),
            "question": val("boss_open_question"), "vat": val("boss_vat_class"), "o17": val("boss_o17_concept_code"),
            "legacy": val("boss_legacy_codes"), "replaced": ref("boss_replaced_by_id"),
            "sale": f["sale_ok"].get("eval") != "False", "active": "active" not in f,
        })
    return out, uom_name


def service_page(s, uom_name, by_xid):
    pages = {}
    for i, lang in enumerate(("es", "en")):
        L = lambda pair: pair[i]  # noqa: E731
        kind = UOM_KIND.get(s["uom"], "shipment")
        units = ", ".join(uom_name[u][i] for u in [s["uom"]] + s["extra"] if u in uom_name)
        example = EXAMPLES.get((s["method"], kind)) or EXAMPLES.get((s["method"], None)) or EXAMPLES[("per_unit", kind)]
        rows = [
            (("Código", "Code"), f"**{s['code']}**"),
            (("Origen del coste", "Cost source"), L(MODE[s["mode"]])),
            (("Forma de cálculo habitual", "Usual calculation method"), f"[{L(METHOD.get(s['method'], ('—', '—')))}](#/metodos)"),
            (("Bases de cobro", "Charge bases"), units),
            (("Clase de IVA", "VAT class"), L(VAT.get(s["vat"], ("—", "—")))),
            (("Concepto de Odoo 17", "Odoo 17 concept"), s["o17"] or "—"),
        ]
        if s["legacy"]:
            rows.append((("Códigos anteriores", "Former codes"), s["legacy"]))
        if s["replaced"]:
            rows.append((("Sustituido por", "Replaced by"), f"[{by_xid[s['replaced']]['code']}](#/srv-{by_xid[s['replaced']]['code'].lower()})"))
        if s["question"]:
            rows.append((("Pregunta abierta", "Open question"), f"[{s['question']}](#/preguntas)"))
        body = [L(("**Qué es.** ", "**What it is.** ")) + s["desc"][lang], "",
                L(("| Dato | Valor |", "| Item | Value |")), "|---|---|"] + [f"| {L(k)} | {v} |" for k, v in rows] + [""]
        needs = L(METHOD_INPUTS.get(s["method"]) or INPUTS.get(kind, INPUTS["shipment"]))
        body += [L(("## Datos que necesita", "## Data it needs")), needs + ".", ""]
        cost = {"tariff": ("Precio aprobado de la tarifa del proveedor que encaja con el envío ([qué precio se elige](#/seleccion)). Si falta, [Añadir precio de proveedor](#/sin-precio).",
                           "Approved price of the supplier tariff that fits the shipment ([which price is chosen](#/seleccion)). If missing, [Add supplier price](#/sin-precio)."),
                "manual": ("Se escribe el **coste manual** en la línea con su referencia (oferta del proveedor, DUA).",
                           "Type the **manual cost** on the line with its reference (supplier offer, customs declaration)."),
                "own": ("Sin coste de proveedor (justificado).", "No supplier cost (justified)."),
                "pending": ("No se cotiza automáticamente hasta decidir la pregunta abierta; se puede escribir un coste manual.",
                            "Not priced automatically until the open question is decided; a manual cost can be typed.")}[s["mode"]]
        import service_matrix as matrix  # noqa: PLC0415 (matrix imports this module)
        sale = matrix.sale(s, i) + (" ([" + L(("venta e IVA", "sale and VAT")) + "](#/venta-iva))." if s["sale"] else ".")
        body += [L(("## Compra (coste)", "## Purchase (cost)")), L(cost), "", L(("## Venta", "## Sale")), sale, ""]
        status, evidence = matrix.status(s)
        missing = {
            "auto": ("Calculado y comprobado con el documento del proveedor; la tarifa debe aprobarla una persona antes de usarse.",
                     "Computed and checked against the supplier document; a person must approve the tariff before use."),
            "partial": ("Automático solo cuando las lecturas del documento sin decidir dan el mismo importe (estancias libres, "
                        "hasta 7 periodos, peso en cientos de kg o mínimo); si no, coste manual con todos los importes a la "
                        "vista hasta que Cristina decida. La tarifa debe aprobarla una persona.",
                        "Automatic only when the document readings not decided give the same amount (free stays, up to 7 "
                        "periods, weight in hundreds of kg or the minimum); otherwise a manual cost with every amount shown "
                        "until Cristina decides. A person must approve the tariff."),
            "doc": ("Falta el **documento de tarifa** del proveedor: cuando llegue, se introduce y se aprueba (no hace falta programar nada).",
                    "The supplier **tariff document** is missing: once received it is entered and approved (no programming needed)."),
            "loaded": ("El documento existe; falta introducir la tarifa y aprobarla.", "The document exists; the tariff is still to be entered and approved."),
            "2025": ("Comprobado con el documento de 2025; para envíos de 2026 hace falta la tarifa 2026 o una confirmación ([P28](#/preguntas)).",
                     "Checked against the 2025 document; 2026 shipments need the 2026 tariff or a confirmation ([P28](#/preguntas))."),
            "manual": ("Importe manual por naturaleza (oferta del proveedor o DUA).", "Manual amount by nature (supplier offer or customs declaration)."),
            "own": ("Honorario propio, sin coste de proveedor.", "Own fee, no supplier cost."),
            "decision": ("Depende de una [decisión de negocio](#/preguntas); hasta entonces, coste manual.",
                         "Depends on a [business decision](#/preguntas); meanwhile a manual cost."),
            "inactive": ("Retirado.", "Retired."),
        }[status]
        body += [L(("## Estado", "## Status")), f"**{matrix.LABELS[lang][status]}**. {L(missing)}",
                 "", L(("Evidencia: ", "Evidence: ")) + evidence + "."]
        if s["code"] in matrix.LIMITS:
            body += ["", L(("Límite: ", "Limit: ")) + L(matrix.LIMITS[s["code"]]) + "."]
        body += [""]
        body += [L(("## Ejemplo (importes ilustrativos)", "## Example (illustrative amounts)")), L(example) + ".", ""]
        if s["code"] in NOTES:
            body += [L(("## Condiciones de los proveedores y decisiones", "## Supplier conditions and decisions")), L(NOTES[s["code"]]), ""]
        steps = {"tariff": ("Tarifa de proveedor con este servicio, su base de cobro y la página del documento ([introducir una tarifa](#/tarifa-alta)); en la oferta, [Añadir servicios](#/anadir-servicios).",
                            "Supplier tariff with this service, its charge basis and the document page ([enter a tariff](#/tarifa-alta)); on the quotation, [Add services](#/anadir-servicios)."),
                 "manual": ("En la oferta, añadir el servicio y escribir el coste manual y su referencia.",
                            "On the quotation, add the service and type the manual cost and its reference."),
                 "own": ("En la oferta, añadir el servicio e indicar el precio de venta.", "On the quotation, add the service and set the sale price."),
                 "pending": ("Esperar la decisión; mientras tanto, coste manual si la oferta lo necesita.",
                             "Wait for the decision; meanwhile a manual cost if the quotation needs it.")}[s["mode"]]
        body += [L(("## Configurar y usar", "## Set up and use")), L(steps)]
        pages[lang] = "\n".join(body)
    return pages


def main():
    manifest = json.loads((GUIDE / "src" / "manifest.json").read_text(encoding="utf-8"))
    pages = []
    for p in manifest["pages"]:
        body = {}
        for lang in ("es", "en"):
            src = GUIDE / "src" / f"{p['id']}.{lang}.md"
            body[lang] = src.read_text(encoding="utf-8") if src.is_file() else ""
        pages.append({**p, "body": body})
    # Spanish decisions page = docs/preguntas-abiertas.md without its title and English summary lines.
    lines = (ROOT / "docs" / "preguntas-abiertas.md").read_text(encoding="utf-8").splitlines()[1:]
    start = next(i for i, ln in enumerate(lines) if ln.startswith("Questions that change"))
    end = next(i for i in range(start, len(lines)) if not lines[i].strip())
    next(p for p in pages if p["id"] == "preguntas")["body"]["es"] = "\n".join(lines[:start] + lines[end:]).strip()
    import service_matrix as matrix  # noqa: PLC0415
    for lang in ("es", "en"):
        next(p for p in pages if p["id"] == "matriz")["body"][lang] = matrix.page(lang)
    srv, uom_name = services()
    by_xid = {s["xid"]: s for s in srv}
    service_pages = []
    for s in sorted(srv, key=lambda s: s["code"]):
        section = "srv-pendientes" if s["mode"] == "pending" and s["code"] != "FTT" else FAMILY_OF.get(s["code"], "srv-almacen")
        title = {lang: f"{s['code']} · {s['name'][lang].split(' (')[0]}" for lang in ("es", "en")}
        service_pages.append({"id": f"srv-{s['code'].lower()}", "section": section, "title": title,
                              "body": service_page(s, uom_name, by_xid)})
    order = [sec["id"] for sec in manifest["sections"]]
    service_pages.sort(key=lambda p: (order.index(p["section"]), p["id"]))
    data = GUIDE / "data"
    data.mkdir(exist_ok=True)
    (data / "pages.js").write_bytes(("window.GUIDE_SECTIONS = " + json.dumps(manifest["sections"], ensure_ascii=False) +
                                     ";\nwindow.GUIDE_PAGES = " + json.dumps(pages, ensure_ascii=False) + ";\n").encode("utf-8"))
    (data / "services.js").write_bytes(("window.GUIDE_SERVICE_PAGES = " + json.dumps(service_pages, ensure_ascii=False) + ";\n").encode("utf-8"))
    missing = [f"{p['id']}.{lang}" for p in pages for lang in ("es", "en") if not p["body"][lang]]
    print(f"{len(pages)} pages, {len(service_pages)} service pages; missing sources: {missing or 'none'}")


if __name__ == "__main__":
    main()
