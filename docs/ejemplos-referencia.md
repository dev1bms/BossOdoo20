# Ejemplos de referencia · Reference examples

Resultados calculados **a mano** desde los documentos de proveedor (independientes del código) y comparados
con `boss.pricing`. Los importes reales están en el fichero privado `samples-private/samples.json` (fuera de Git).
Prueba: `addons/boss_pricing/tests/test_references.py`; en el servidor sin cambios: `dev/verify_references.py`.

**Resultado (21/10/2026):** 43 ejemplos, 0 diferencias en la base de pruebas y en `boss20` (con rollback).

| Ref. | Proveedor y página | Servicio | Mecánica comprobada |
|---|---|---|---|
| R1 | MSC 09/2026 p.12 | THC | Precio por contenedor, igual para cualquier tamaño; una línea por tamaño/tipo |
| R2 | MSC p.12 | T3-PAD | Precio distinto por tamaño (20'/40'/45') |
| R3 | MSC p.12 | GLO-FUELEU | Por TEU (20' = 1, 40' = 2), origen China |
| R4 | MSC p.12 | BL | Una vez por expediente |
| R5 | MSC p.12 | GLO-CCC | Solo equipo Dry (DV/HC) |
| R8, R9 | MSC p.18 | DEM | Días libres + «5 días a X, después Y» (tramos relativos), por tamaño |
| R11, R12 | MSC p.17 | OCU | Tramos por número de día (posicionales), por puerto (Valencia, Barcelona) |
| R16 | Hapag import p.1 | DEM | 3 tramos relativos; día 23 añade un día del último tramo |
| R18 | CMA p.1 | DEM | Tramos posicionales |
| R01–R04 | WFS 2026 p.5 | ALM | Franquicia 48 h como umbral (48 h = 0; 49 h = desde el día 1), por 100 kg, mínimo, tramo de 7 días |
| R06 | WFS p.6 | HAN | € por kg tasable de la AWB con mínimo |
| R09a | WFS p.6 | AWB | Fijo por AWB |
| R10c | WFS p.7 | X-R | Tramos por peso sobre toda la cantidad, mínimo y máximo |
| R07 | IRENEO MAD 2025 p.7 | HAN | kg tasable con factor 333, mínimo |
| R08 | IRENEO p.4, p.16 | HAN (paquete export) | Tramos fijos y por kg, tramo abierto, «no inferior al tramo anterior» |
| R10a | IRENEO p.5 | X-R | Por kg real con mínimo y máximo |
| R12 | IRENEO p.6-7, p.16 | TTE-CON | Zona por provincia, tramos, regla del tramo anterior; > 3.000 kg sin precio |
| SEG | IRENEO p.16 | SEG | Porcentaje del transporte del mismo proveedor, con mínimo |

**Diferencias con Odoo 19 explicadas:** sus valores «golden» de THC, FuelEU, BL, CCC y DEM usan la edición MSC de enero, caducada; el «Logistics fee» de importación no existe en ninguna edición (solo
exportación). WFS: Odoo 19 cuenta días naturales donde el documento dice periodos de 24 h (MAD/BCN) y aplica la regla
del viernes a cualquier viernes (el documento exige retirada el lunes).
