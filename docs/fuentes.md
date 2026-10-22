# Índice de fuentes · Source index (revisión 21/10/2026)

Lectura completa, solo lectura. Los extractos con precios reales están en `.research/` (fuera de Git).
Read in full, read-only. Extracts with real prices live in `.research/` (outside Git).

## Carpeta compartida «NEW ODOO» (SharePoint IT)

| Fichero | Contenido útil | Estado |
|---|---|---|
| Calculadora_IVA_conceptos_BOSS.xlsx | Reglas de IVA de Ángel (NS/EX/NR, zonas, capas), 85 conceptos, lista oculta de 252 países→zona | Leído (hojas ocultas incl.). Sin correspondencia con impuestos de Odoo (P17) |
| Conceptos_e_IVA_BOSS_2026-10-09.xlsx | Mismos 85 conceptos y clases | Leído; duplica la calculadora |
| Conceptos_Odoo19_estado_configuracion_2026-10-13.xlsx | Estado de configuración por concepto en Odoo 19 | Leído; histórico |
| COSTO_VENTA_MULTINIVEL.xlsx | Ofertas vs coste de un cliente (Multinivel Ibérica): precios tecleados, recargos ×1,06–×1,30, margen sobre venta | Leído; práctica, no regla aprobada (P01) |
| Nuevo Odoo.xlsx | Requisitos de Cristina (USD/EUR, QBR, facturación) | Leído |
| Plan detallado previsiones.xlsx (+ estado 07-10) | Respuestas de Cristina 28/09, plan 02/10, casos E260237-40 | Leído; base de reglas aprobadas |
| IA TASKS.xlsx, Registro automatizaciones…xlsx | Reglas: mismo código en compra y venta, previsiones confirmadas, cierre semanal | Leído |
| DRY - Gastos Locales 2026.pdf | MSC gastos locales **edición enero 2026 (caducada)** | Leído; la vigente es la de septiembre (carpeta costs) |
| IRENEO/TARIFAS MAD 2025.pdf, TARIFAS BCN TRC 2025.pdf | Agente de handling/transporte MAD y BCN 2025 | Leídos; vigencia 2026 sin confirmar (P28) |
| IRENEO/*.msg (3) | Tarifas BCN 2025, recargo de combustible (porcentaje y fecha en conflicto), cambio de almacén | Leídos (lector OLE propio) |
| Cargo tracking OOCL….msg | Aviso de seguimiento | Leído; sin precios |

## Documentos de proveedores en otras carpetas

| Documento | Vigencia | Uso |
|---|---|---|
| MSC «DRY - Gastos Locales 2026 - DRY desde 01.09» (costs) | 01/09–31/12/2026 | **Vigente**; muestras THC, PAD, CCC, FuelEU, BL, DEM, OCU |
| MSC edición febrero 2026 (Operaciones/Navieras) | Caducada | Comparada |
| Hapag-Lloyd importación / exportación D&D | Desde 01/10/2025 | Muestra DEM |
| CMA CGM D&D Spain | Desde 01/03/2025 | Muestra DEM |
| WFS España V 2026-02 (costs) | Desde 01/06/2026 | **Vigente**; muestras ALM, HAN, AWB, PNS |
| Avisos MSC LWS, IMO 2022, CMA no-show 2021, ONE PSS, AWS | Varios | Leídos; recargos o caducados |

**No encontrados:** gastos locales de Hapag y CMA (THC/T3/BL/CES), tarifas de ONE, Maersk, COSCO, OOCL, ZIM,
Yang Ming, ARKAS; consolidadores LCL (carpetas vacías → sin muestra de THC-LCL); agentes de aduanas (Aducex,
Ramos Vila); transportistas distintos de IRENEO; segundo handler aéreo; aseguradora; precios ROH/SOI/INS/SAN.

## Proyecto Odoo 19 (solo conocimiento)

Leídos: `docs/agents/*` (contexto, decisiones, personas, fuentes), `BOSS_DECISION_LOG.md`, `iva_rules.md`,
`PREVADDER_TARIFAS_2025.md`, `CRISTINA_REQUIREMENTS_MATRIX.md`, actas de tareas (IRENEO, reunión Ángel 16/10,
guía por servicio, pricing center), `services.json`, `service_decisions.py`, `x_concept_export.json`,
código de cálculo (`boss_rates/tariff_line.py`, `boss_pricing/engine.py`, asistentes) y pruebas «golden».
Hallazgo: varios valores «golden» de Odoo 19 usan la edición MSC de enero (caducada); ver `ejemplos-referencia.md`.

## Odoo 17 producción (solo lectura, 22/10/2026)

- Compañía (`res.company`): datos legales, EUR, plan `es_pymes`.
- Acción de servidor 1232 «Create Invoice» (asistente de facturación): impuesto de cada línea según la clase de IVA, el
  tipo de cliente (España / UE / tercer país) y el tipo de factura (NORMAL / TAX).
- Conceptos (`x_concept`, exportados en Odoo 19 `data-src/x_concept_export.json`): tipo NORMAL/TAX/CREDITOR, IVA por
  defecto, marca «IVA intracomunitario».
- Impuestos usados por la acción 1232 y sus casillas del 303 (etiquetas de las líneas de reparto).

## Odoo 20 y trabajo previo

`KICKOFF_PROMPT.md`, spike `boss_spike_adr002` (7 pruebas), borrador ADR y propuesta de catálogo de la sesión del
21/10, código fuente de Odoo 20 (comprobado campo a campo).
