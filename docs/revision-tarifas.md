# Revisión de tarifas para Cristina · Tariff review for Cristina (P19, P28)

Estado leído en boss20 el 26/10/2026 (`dev/tariff_review_probe.py`, solo lectura, sin importes). Son las 10 tarifas
cargadas desde documentos reales de proveedor ([MUESTRA]); las tarifas [DEMO] (importes ilustrativos, solo para clientes
DEMO) no están aquí. **Ninguna está aprobada** y nadie la aprueba en nombre de Cristina: aprobar es su clic en
Tarifas → Esperando aprobación → «Aprobar», con el PDF delante. Los importes están en Odoo y en el PDF, no en este
documento. Las tarifas IRENEO 2025 **no se prorrogan**: sus fechas no se cambian.

Cómo revisar cada tarifa: abrir el documento del proveedor, comprobar en Odoo cada precio (página, unidad, condición de
tamaño o tipo, días libres, tramos, mínimo) y el ámbito («Se aplica a»), comparar con el ejemplo de referencia de
`docs/ejemplos-referencia.md` y decidir: **Aprobar**, **Devolver a borrador** con la corrección anotada, o **No aprobar**
(documento caducado o sustituido).

Ojo: 8 de las 10 llegaron a «Esperando aprobación» por la importación sin la casilla «Ámbito revisado» (solo las dos de
WFS la tienen), y el botón «Aprobar» no la exige. Antes de aprobar, revisar el ámbito de cada una.

| # | Proveedor | Tarifa en Odoo | Documento | Validez | Servicios (unidad · condición · página) | Ámbito | Observaciones | Decisión pedida |
|---|---|---|---|---|---|---|---|---|
| 1 | MSC | [MUESTRA] MSC gastos locales importación (origen China) 09-12/2026 | MSC Tarifas gastos locales carga seca 2026, edición 01/09-31/12/2026 | 01/09/2026 – 31/12/2026 | THC (contenedor, p.12) · T3-PAD (contenedor 20'/40'/45', p.12) · BL (expediente, p.12) · GLO-CCC (contenedor DV/HC, p.12) · GLO-FUELEU (TEU, p.12) · DEM (contenedor 20'/40'/45' DV/HC, 7 días libres, tramos relativos, p.18) | Importación · marítimo FCL · origen China · naviera MSC · cualquier cliente | Ámbito no marcado «revisado». FuelEU limitado a China hasta tener la lista «Lejano Oriente» (P24). Caduca el 31/12/2026: pedir la edición siguiente | Aprobar / devolver; confirmar el ámbito «origen China» |
| 2 | MSC | [MUESTRA] MSC ocupación importación Valencia 09-12/2026 | Ídem | 01/09/2026 – 31/12/2026 | OCU (contenedor 20'/40' DV, 4 días libres, tramos por número de día, p.17) | Importación · marítimo FCL · Valencia · MSC | Solo contenedor DV: comprobar si el documento da otro precio para HC o reefer. Ámbito no marcado «revisado» | Aprobar / devolver |
| 3 | MSC | [MUESTRA] MSC ocupación importación Barcelona 09-12/2026 | Ídem | 01/09/2026 – 31/12/2026 | OCU (contenedor 20'/40' DV, 5 días libres, tramos por número de día, p.17) | Importación · marítimo FCL · Barcelona · MSC | Ídem | Aprobar / devolver |
| 4 | CMA CGM | [MUESTRA] CMA CGM demoras+detención importación Standard | CMA CGM D&D Tariffs Spain, vigente desde 01/03/2025 | Desde 01/03/2025, sin fin | DEM (contenedor 20'/40'/45' DV/HC, 7 días libres, tramos por número de día, p.1) | Importación · marítimo FCL · naviera CMA CGM | Documento de 2025 sin fecha de fin: confirmar que sigue vigente en 2026. Ámbito no marcado «revisado» | Confirmar vigencia; aprobar / devolver |
| 5 | Hapag-Lloyd | [MUESTRA] Hapag-Lloyd demoras+detención importación (MHD/DTD) | Hapag-Lloyd Spain Import D&D, vigente desde 01/10/2025 | Desde 01/10/2025, sin fin | DEM (contenedor 20'/40' DV/HC, 7 días libres, tramos relativos, p.1) | Importación · marítimo FCL · naviera Hapag-Lloyd | Sin precio para 45'. Confirmar vigencia en 2026. Ámbito no marcado «revisado» | Confirmar vigencia; aprobar / devolver |
| 6 | WFS | [MUESTRA] WFS importación MAD/BCN desde 01/06/2026 | WFS España Tarifas de servicios de carga V 2026-02, desde 01/06/2026 | Desde 01/06/2026, sin fin | ALM (expediente, 48 h libres, periodos de 24 h, por 100 kg o fracción, tramos por número de día, mínimo por estancia, p.5 punto 1) · AWB (guía aérea, p.6 punto 10) · HAN (kg tasable, p.6 punto 12) | Importación · aéreo · MAD y BCN | Lecturas de ALM P40, P41, P29 y P42 aplicadas por la aprobación de Belal del 23/10; solo carga general (la especial es P44) | Aprobar / devolver; ratificar las lecturas de ALM |
| 7 | WFS | [MUESTRA] WFS exportación PNS MAD/BCN desde 01/06/2026 | Ídem | Desde 01/06/2026, sin fin | ALM (ídem, p.5 punto 1) · X-R (guía aérea, tramos por peso, p.7 punto 19) | Exportación · aéreo · MAD y BCN | Ídem | Aprobar / devolver; ratificar las lecturas de ALM |
| 8 | IRENEO | [MUESTRA] IRENEO MAD exportación Barajas 2025 | IRENEO MAD Tarifas 2025 | 01/01/2025 – 31/12/2025 (**caducada**) | HAN (kg tasable aéreo, tramos, p.4 y p.16) · X-R (guía aérea, p.5) | Exportación · aéreo | No vale para envíos de 2026 | No aprobar ni prorrogar; pedir a IRENEO la tarifa 2026 o una confirmación escrita (P28) |
| 9 | IRENEO | [MUESTRA] IRENEO MAD recogidas en terminal 2025 | Ídem | 01/01/2025 – 31/12/2025 (**caducada**) | HAN (kg tasable aéreo, p.7) | Importación · aéreo | Ídem | Ídem |
| 10 | IRENEO | [MUESTRA] IRENEO distribución nacional zona 3 2025 | Ídem | 01/01/2025 – 31/12/2025 (**caducada**) | TTE-CON (kg tasable terrestre, tramos, p.6-7 y p.16) · SEG (porcentaje por expediente, p.16) | Importación y exportación · cualquier modo · 15 provincias de la zona 3 | Ídem; el recargo de combustible (FS) no está en esta tarifa | Ídem |

**Confirmación escrita encontrada el 26/10/2026** (carta de IRENEO del 14/07/2026 adjunta al correo «Actualización del
Recargo por Combustible conforme a RDL 9/2026»): las tarifas de **transporte** suben un 10 % desde el 15/07 (de 2026; la
carta pone 2025 por errata). Con ella se crea una **tarifa nueva** de IRENEO con validez desde el 15/07/2026: TTE-CON de
2025 × 1,10, documento = la carta + la tarifa 2025; la de 2025 no se modifica. HAN y X-R (handling) no están en la carta:
solo con confirmación de Cristina.

## Qué se activa al aprobar · What approval turns on

Hoy 13 servicios de tarifa tienen precio en estos documentos (de 50): THC, T3-PAD, BL, GLO-CCC, GLO-FUELEU, DEM, OCU,
ALM, AWB, HAN, X-R, TTE-CON y SEG. Aprobar **no** activa por sí solo el coste automático de los 13. Un servicio tiene
coste automático en una oferta solo cuando se cumplen todas estas condiciones:

1. **Aprobada**: una tarifa que lo incluye está aprobada.
2. **Vigente**: la fecha del envío (ETA en importación, ETD en exportación, P04) está dentro de su validez. Con las fechas
   actuales, SEG y TTE-CON (solo en IRENEO 2025) no tienen ningún precio vigente para 2026, y HAN de exportación tampoco
   (solo IRENEO): como máximo quedarían 11 servicios, y solo dentro del ámbito de cada tarifa.
3. **Aplicable**: el ámbito y las condiciones coinciden con el envío (sentido, modo, tipo de carga, puerto, país de
   origen, naviera, tamaño y tipo de contenedor, provincia) y los datos del envío que pide el precio están rellenos
   (contenedores, peso tasable de la AWB, días…). Ejemplos: THC de MSC solo en importaciones FCL con origen China; OCU solo
   en Valencia o Barcelona y contenedor DV; ALM de WFS solo en MAD y BCN.
4. **Sin conflicto**: no hay otra tarifa aprobada que aplique al mismo caso con otro precio (si la hay, el resultado es
   «conflicto» y se elige a mano).
5. **Probado**: tras aprobar, se prueba el escenario que le corresponde (el ejemplo de referencia de
   `docs/ejemplos-referencia.md`) con un presupuesto en borrador de un cliente que no sea DEMO, que no se envía; el coste
   debe coincidir con el del ejemplo. Las tarifas reales nunca dan precio a clientes DEMO, ni las DEMO a clientes reales.

Mientras tanto, el coste de esos servicios en una oferta real es «pendiente de aprobación» o «sin tarifa», y se escribe a
mano con su justificante. Los otros 37 servicios de tarifa no tienen ningún documento cargado (26/10/2026): AMS, CAU,
CES, DAP, DAP-CON, DEX, DOC, ENS, EUR1, EXW, EXW-AIR, EXW-FCL, EXW-LCL, FAD, FAR, FS, FUM, GLO, GLO-LOG, INS, MEN,
OAL-CON, OAL-PAL, PAL, PAR, PFT-AIR, PFT-FCL, PFT-LCL, POT, ROH, SAN, SOI, T3, THC-LCL, TRA, TTE-FCL y VGM (documentos que
faltan en `docs/fuentes.md`).
