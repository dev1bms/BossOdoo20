# Decisiones de negocio · Business decisions (revisión 22/10/2026)

Preguntas que cambian un cálculo o un comportamiento. Revisadas contra Odoo 19 (`docs/agents/DECISIONS.md`,
`BOSS_DECISION_LOG.md`, `iva_rules.md`, actas), la carpeta NEW ODOO y Odoo 17 producción (solo lectura).
Mientras una pregunta sigue abierta el sistema hace lo que dice la última columna; nunca usa un valor inventado.
Importes de los ejemplos ilustrativos; las cifras reales de proveedor están en `.research/` (fuera de Git).
Questions that change a calculation or behaviour, reviewed against the previous projects; open ones are ordered
by impact. Amounts are illustrative.

## Cerradas con respuesta documentada · Closed

| Id | Pregunta | Respuesta | Fuente | En el sistema |
|---|---|---|---|---|
| P04 | ¿Qué fecha elige la versión de tarifa? | Importación ETA, exportación ETD | Ángel, reunión 16/10 (acta Odoo 19 `2026-10-18-reunion-angel-16-10.md`) | Fecha prevista del envío. Excepciones por proveedor: no hay ninguna escrita |
| P08 | ¿Qué tipos de contenedor tienen precio propio? | Es un dato de cada documento, no una decisión | Documentos MSC/Hapag/CMA; ejemplo T3 por tipo (Cristina 28/09) | Condición por tamaño y tipo en cada precio |
| P15 | ¿Cómo cuentan los días libres de WFS? | Umbral: superados, se cobra desde el día 1 | Cristina 08/09 (decisión B20) y documento WFS 2026 | ALM con modo «umbral» y periodos de 24 h. Para navieras manda cada documento (ver P29) |
| P25 | AWB/BL: ¿máster por expediente o house? | Máster por expediente; los house son la excepción (≈10 %) | Cristina 28/09 (Plan detallado previsiones, «Explicaciones previsiones») | BL y AWB una vez por expediente; DOC para el house |
| P27 | Compañía de Odoo 20: datos, moneda, país, plan contable | Los de Odoo 17 producción: Boss Continental S.L., EUR, España, PGC PYMEs 2008 | `res.company` de Odoo 17 (lectura 22/10) | Configurada en `boss20` (`dev/setup_company.py`) |

## Abiertas por impacto · Open, by impact

| # | Id | Pregunta | Qué bloquea hoy | Servicios | Propuesta práctica | Quién | Mientras tanto |
|---|---|---|---|---|---|---|---|
| 1 | P17 | **IVA**: impuesto de Odoo para cada clase NR / EX / NS, y zona de Ceuta y Melilla | **Toda oferta**: no se puede enviar ni confirmar con IVA pendiente | Todos | Elegir entre los impuestos del PGC PYMEs ya instalados (en Odoo 17 se usan «21% S», «0% EX S» y «0% EXEMPT NS») y dar los artículos de exención | Ángel | IVA «pendiente»; las reglas de clase (Ángel, 31/08) sí funcionan |
| 2 | P19 | **Aprobar las tarifas** de muestra/reales tras revisarlas | Cálculo automático en el servidor (ninguna tarifa aprobada) | THC, T3-PAD, BL, GLO-CCC, GLO-FUELEU, DEM, OCU, ALM, HAN, AWB, X-R | Revisar cada tarifa con su PDF y ejemplos (`ejemplos-referencia.md`) y pulsar «Aprobar» | Cristina (o Belal) | Precio «pendiente de aprobación» |
| 3 | P03 | **Cambio de moneda** para costes en USD y regla del **QBR** | Costes en USD en ofertas en EUR | FMI/FME/FAI/FAE en USD, cualquier tarifa en USD, QBR | Tipo de Odoo del día de la oferta, congelado al aceptar; QBR si la oferta en USD se factura en EUR (requisito de Cristina en «Nuevo Odoo.xlsx») | Ángel | Línea «Otra moneda, sin política»; QBR pendiente |
| 4 | P28 | ¿Las tarifas **IRENEO 2025** siguen vigentes en 2026? ¿Qué recargo de combustible y desde cuándo? | Transporte terrestre y aéreo de IRENEO en 2026 | TTE-CON, FS, SEG, HAN y X-R de IRENEO | Pedir a IRENEO la tarifa 2026 o una confirmación escrita | Cristina | Muestras con vigencia 2025: no se aplican a envíos de 2026 |
| 5 | — | **Documentos de tarifa que faltan** (no es una decisión) | Precio automático de esos servicios | CES, GLO, T3, DOC, ENS/AMS, VGM, FAD, DEX, TRA, EUR1, inspecciones, almacén, TTE-FCL, THC-LCL, agentes | Reunir los PDF vigentes (lista en `fuentes.md`) y cargarlos | Cristina / operaciones | «Sin precio de proveedor» → «Añadir precio de proveedor» desde la oferta |
| 6 | P01 · P02 | **Precio de venta**: ¿reglas por cliente (coste + %, margen)? ¿Margen mínimo y quién aprueba vender por debajo? | Venta automática | Todos los vendibles | El mecanismo existe (lista de precios del cliente con precio fijo, recargo sobre coste, margen sobre venta y margen mínimo). Falta decidir valores por cliente | Cristina (+ Ángel para el mínimo) | Venta pactada en la lista del cliente o tecleada; nunca una regla sin aprobar |
| 7 | — | **Venta unificada de ALM** (aprobada como concepto, Cristina 08/10): valores | Venta automática de ALM | ALM | Fijar el importe o la regla en la lista general | Cristina | Venta tecleada |
| 8 | P13 | **Parámetros derivados**: caución (CAU) y seguro (SEG): porcentajes, tasas por país y mínimos | Cálculo de CAU y SEG | CAU, SEG | Cargar cada valor como tarifa con su documento | Cristina + Ángel | Método porcentaje disponible; sin valores aprobados |
| 9 | P16 | Servicios sin definición | Esos servicios | VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM | Definir los de uso real (unidad, proveedor, documento) y retirar el resto | Cristina | «Pendiente de decisión», coste manual posible |
| 10 | P18 | **Suplidos**: producto y tratamiento contable al facturar | Facturación (fase 2) | ARA, IVA, PLA, DUM | Venta = coste del DUA (práctica Odoo 17); confirmar cuenta e impuesto | Ángel | Importe manual a coste, clase NS |
| 11 | P24 | Lista de países «Lejano Oriente» (FuelEU) y tráficos «short sea» de THC | FuelEU fuera de China | GLO-FUELEU, THC | Lista escrita por Cristina | Cristina | Muestra MSC limitada a origen China |
| 12 | P11 | PAD bajo T3 o GLO; presentación «THC + gastos portuarios»; IVA de THC (todo EX o una parte NR) | Presentación e IVA de THC | THC, T3-PAD, GLO | Mantener T3-PAD; Ángel decide si se divide el IVA de THC | Cristina + Ángel | T3-PAD cotiza; IVA según la clase EX del servicio |
| 13 | P10 | ETX (WFS punto 49): concepto y unidad | ETX | ETX | Compra por AWB máster, venta por expediente (Cristina 08/10); falta confirmar el concepto | Cristina | «Pendiente de decisión» |
| 14 | P09 | DET: ¿código propio o dentro de DEM? | Detención facturada aparte | DET, DEM | Propio cuando el proveedor lo factura aparte | Cristina | DET «pendiente de decisión» |
| 15 | P29 | Tramos de días WFS «hasta 7 / más de 7»: ¿por posición del día o toda la estancia? | Importe de ALM largo | ALM | Lectura literal (posicional) salvo que WFS diga otra cosa | Cristina | Posicional (configurable en cada precio). Ejemplo ilustrativo: 10 días a 10 €/20 € → 7×10 + 3×20 = 130 € o 10×20 = 200 € |
| 16 | P12 | Servicios de coste (DEM, OCU, VGM, PFT, GLO): ¿se venden y cómo? | Venta de esos servicios | DEM, OCU, VGM, GLO, PFT | DEM/OCU/VGM/GLO vendibles con venta tecleada o pactada; PFT nunca se vende (Cristina 29/09) | Cristina | Así configurado |
| 17 | P05 | ¿Enviar una oferta con un coste aún pendiente? | — | Todos | Aviso, sin bloqueo | Cristina | Se bloquean solo IVA pendiente y venta sin indicar |
| 18 | P06 · P07 | Tarifa que cambia durante la validez; ¿quién recotiza una oferta aceptada? | — | Todos | Recotizar con motivo, solo gestor comercial (propuesta del propietario 26/08: cambios con motivo) | Cristina | Así implementado |
| 19 | P14 | Factor de peso tasable cuando el documento no lo dice | Peso tasable sin AWB | Aéreo y terrestre | Peso tasable de la AWB o factor escrito en la tarifa | Cristina | Así implementado |
| 20 | P20–P23 · P26 | Visibilidad de coste/margen, ofertas por ruta, alternativas, validez, fusiones de códigos | — | — | Estándar de Odoo hasta decidir | Cristina | Estándar de Odoo; códigos originales |
