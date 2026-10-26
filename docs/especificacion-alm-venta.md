# Venta única de ALM (P43) · Single ALM sale price — especificación

Borrador para decisión, 26/10/2026 (fase B1 de `docs/ciclo-operativo.md`). **Nada está implementado** y nada se ha
cambiado en boss20. Los importes reales del 25/09 están en `.research/alm-venta-valores.md` (fuera de Git); aquí solo hay
la regla y ejemplos con importes **ilustrativos**.

## Fuentes (Odoo 19, solo lectura)

| Qué | Fuente | Estado |
|---|---|---|
| La regla con sus importes | Reunión con Cristina del 25/09/2026, transmitida por Belal el mismo día como «la regla de Cristina» (transcripción de la sesión de Odoo 19, 25/09 15:21 UTC); commit `fe9ff91` de Odoo 19; `boss_sales/models/customer_storage_terms.py` | Implantada en Odoo 19 (pruebas) el 25/09 como condición general de almacenaje; **borrada el 08/10** con los precios de prueba |
| Precio único, no negociable, solo ALM | Cristina en la reunión del 08/10/2026 («los clientes no lo negocian») | Sin valores ese día |
| Registro de decisiones de Odoo 19 | `docs/agents/DECISIONS.md` (líneas 88, 175, 646) | Nunca anotada como confirmada; desde el 08/10 «valores pendientes de Cristina» |
| Odoo 20 | P43, propuesta aprobada por Belal el 23/10/2026: usar los valores del 25/09 | Pendiente de ratificación por Cristina |

Ninguna fuente dice que los valores del 25/09 estén sustituidos, pero tampoco que estén confirmados.

## Regla (texto de la fuente, sin importes)

1. 48 horas libres desde la llegada.
2. Superadas las 48 h, se cobra un **importe normal** por día y por 100 kg o fracción **desde el día de llegada** (no solo
   el exceso).
3. Hay un **mínimo** (la fuente no dice si es por estancia, por día o por AWB).
4. Si la mercancía queda 8 días o más, se cobra un **importe de larga estancia** por día y 100 kg o fracción **desde el
   día 1** (toda la estancia, no solo desde el día 8).
5. Un único precio de venta para todos los clientes, solo para ALM.

## Dos reglas de venta en las fuentes · Two sale rules in the sources (26/10/2026)

La página oficial de la guía ([Almacenaje](https://doc.bosscontinental.com/new/#/srv-alm), estado a 23/10) dice que la venta
de ALM **no se calcula sola** porque los valores del precio único (P43) no están aprobados. Las fuentes dan dos reglas
distintas; los importes están en `.research/` (fuera de Git):

| | Regla A (25/09/2026) | Regla B (oferta real a Cofitel, 03/02/2026) |
|---|---|---|
| Fecha | 25/09/2026, reunión con Cristina (transmitida por Belal); cargada en Odoo 19 ese día, borrada el 08/10 | 03/02/2026, propuesta 05570 (y correo de septiembre 2026 con la misma plantilla de condiciones) |
| Cliente | Todos (precio único, Cristina 08/10: «los clientes no lo negocian») | Cofitel, S.A. (condiciones generales impresas en toda oferta de ese tipo) |
| Handler / aeropuerto | No dice | MAD; handler no indicado; **variante propia si la carga llega con DHL** (menos días libres, otro importe y mínimo) |
| Franquicia | 48 horas desde la llegada | 3 días; con DHL, 2 días |
| Cambio de importe | Desde el 8.º día, toda la estancia | Desde el día 10 (incluido) |
| Unidad | Por día y 100 kg o fracción | Por día y 100 kg o fracción |
| Mínimo | Sí (unidad no dicha) | Sí, por estancia (importe distinto con DHL) |
| Cobro desde la llegada si se supera la franquicia | Sí | Sí |

**Origen de la regla B (26/10, código C# PrevAdder `Utils.cs` 1673–1699, configuración «ALMACENAJES AEREO VENTA»):** 3 días libres (4 si la llegada es en viernes), por 100 kg o fracción del peso tasable, un importe hasta el día 10 y otro después, mínimo, contados desde la llegada. El texto de las condiciones generales de las ofertas no lo genera Odoo 17 ni el C#: vive en el Excel de ofertas de Cristina (`COSTO_VENTA_MULTINIVEL.xlsx`, hoja `IAB FOB`), donde una versión dice «a partir del día 20». La compra en PrevAdder ya variaba por handler (WFS 3/4 días, Swissport 3, Iberia 4 importación / 2 exportación, IAS y ACL 3/4 con corte en el día 20).

Hipótesis para Cristina (ninguna confirmada): (a) la oferta de febrero es anterior a la regla del 25/09 y la plantilla de
condiciones del programa de ofertas no se actualizó; (b) la regla depende del handler (la variante DHL lo sugiere) y la
del 25/09 es la de WFS; (c) la regla depende del cliente o del tipo de oferta. Decisión necesaria antes de B01: qué regla
vale, desde cuándo, y si cambia por handler o por cliente (D1, D7, D9 de la tabla siguiente).

## Puntos que necesitan decisión

Mientras no se decidan, el sistema no propone precio de venta de ALM (venta tecleada, como hoy).

| # | Punto | Por qué hay duda | Quién |
|---|---|---|---|
| D1 | ¿Siguen valiendo los importes del 25/09? | Nunca anotados como confirmados; borrados el 08/10; Odoo 19 los da por pendientes desde entonces | Cristina |
| D2 | ¿Qué peso? Bruto, tasable de la AWB (como el coste, P14) o tasable con factor | La regla dice solo «100 kg o fracción»; Odoo 19 usaba el tasable aéreo con factor 167 | Cristina |
| D3 | ¿Qué es un «día»? Periodos de 24 h desde la llegada (como el coste de WFS, P40) o días naturales | La regla no lo dice; Odoo 19 contaba días naturales | Cristina |
| D4 | ¿El mínimo es por estancia (AWB o expediente) o por día? ¿Se aplica si la estancia queda dentro de las 48 h? | La fuente no da la unidad; Odoo 19 lo aplicaba a la estancia y no dentro de la franquicia | Cristina |
| D5 | «8 días o más»: ¿cuenta el día de llegada como día 1? ¿Y con periodos de 24 h, 8 periodos? | La fuente dice «desde el día 1» para el importe, no cómo se cuentan los 8 días | Cristina |
| D6 | Inicio y fin de la estancia: importación llegada (NOA) → recogida; exportación entrega al handler → salida del vuelo | Correo de Cristina del 25/09 sobre los eventos de ALM; la condición de Odoo 19 usaba entrada y salida de almacén | Cristina |
| D7 | Alcance: ¿solo aéreo o también grupaje marítimo (LCL)? ¿Todos los aeropuertos o solo MAD y BCN? | Correo del 28/09: ALM cubre aéreo y LCL; la regla no lo dice | Cristina |
| D8 | El mínimo de venta del 25/09 es **menor** que el mínimo de compra de WFS: una estancia pequeña se vende por debajo del coste. ¿Se acepta o la venta nunca baja del coste? | Comparación con la tarifa WFS 2026 cargada en Odoo 19 | Cristina (+ Ángel, margen mínimo P01/P02) |
| D9 | ¿La regla del 25/09 sustituye a la de Odoo 17 (otros importes, 3 días libres, otro precio desde el día 10)? | **Una oferta real a Cofitel del 03/02/2026 (propuesta 05570, vista el 26/10) sigue usando la regla antigua**, con una variante para llegadas con DHL (2 días libres). No hay fuente que diga que se sustituyó | Cristina |
| D10 | Propuesta de 08/10 «mayor coste de proveedor + %», no aprobada | Belal eligió el 23/10 los valores del 25/09; falta que Cristina lo ratifique | Cristina |
| D11 | IVA: ALM sigue la tabla de IVA BOSS de su clase (NR según las reglas de Ángel) | La regla no lo menciona | Ángel |
| D12 | Estancia real más larga que la cotizada: la venta queda fija al aceptar y el exceso se refactura con motivo («Refacturar un coste adicional»), o la venta se recalcula | En Odoo 20 la venta nunca cambia sola | Cristina |
| D13 | Carga especial (frío, peligrosa, valiosa…) | No la cubre la regla (P44) | Cristina |
| D14 | Validez: desde el 25/09/2026, sin fin, en EUR | Así se cargó en Odoo 19 | Cristina |

## Ejemplos con importes ilustrativos

Importe normal 10 € y larga estancia 20 € por día y 100 kg o fracción, mínimo 40 € por estancia. **No son los importes
reales.**

| # | Envío | Lectura | Resultado |
|---|---|---|---|
| E1 | 500 kg, lunes 10:00 → miércoles 10:00 (48 h) | Dentro de la franquicia | 0 € |
| E2 | 500 kg, lunes 10:00 → miércoles 11:00 (49 h) | 3 periodos de 24 h o 3 días naturales, 5 unidades | 3 × 5 × 10 = 150 € |
| E3 | 500 kg, lunes 10:00 → jueves 09:00 (71 h) | D3: 3 periodos de 24 h / 4 días naturales | 150 € / 200 € |
| E4 | 80 kg, lunes 10:00 → jueves 10:00 (72 h) | 1 unidad; 3 periodos (30 €) o 4 días (40 €); mínimo 40 € | 40 € en las dos lecturas |
| E5 | 500 kg, 7 días / 8 días | Desde el día 8, toda la estancia al importe de larga estancia | 7 × 5 × 10 = 350 € / 8 × 5 × 20 = 800 € |
| E6 | 300 kg brutos, 2,5 m³, 3 días | D2: bruto 3 unidades / tasable con factor 167 (417,5 kg) 5 unidades | 90 € / 150 € |

E5 muestra el salto de la regla: un día más multiplica el importe. Si el importe alto se aplicara solo desde el día 8, el
de 8 días sería 7 × 5 × 10 + 1 × 5 × 20 = 450 €; la fuente dice «desde el día 1».

## Diseño propuesto (cuando se decida)

Con la estructura del proyecto y sin un segundo motor:

1. **Tarifa de venta** en `boss_pricing`: una tarifa con el tipo «venta» (sin proveedor, de BOSS), con su documento (la
   regla firmada por Cristina), validez y aprobación como cualquier tarifa. Su línea ALM usa el método por tiempo que ya
   existe y ya calcula el coste de WFS: franquicia de 48 h en modo umbral, unidad de 100 kg con «o fracción», periodo de
   24 h o día natural (D3), tramo hasta el día 7 y tramo abierto con «toda la estancia al tramo alcanzado», mínimo por
   estancia o por día (D4).
2. **Regla de venta** en `boss_pricing_sale`: una base nueva de lista de precios, «Tarifa de venta BOSS», usada por una
   regla de la lista general solo para ALM. El precio sale del mismo cálculo y de los mismos datos del envío que el coste
   (peso, días u horas), con su explicación y un estado explícito («faltan datos del envío», «pendiente de aprobación»).
   Un precio pactado en la lista de un cliente no se usaría para ALM (precio único).
3. **Aceptación**: el precio queda en la foto de la aceptación como cualquier otro; tras aceptar solo cambia por el camino
   que se decida en D12.
4. **Pruebas mínimas**: los ejemplos E1–E6 en las pruebas del motor y una oferta con ALM en las pruebas de Odoo.
5. **ADR-006**: tarifa de venta con el mismo motor frente a otras opciones (regla de lista de precios, «coste + %»).

Sin las respuestas D1–D7 no se puede construir; D8–D14 pueden decidirse después sin rehacer el diseño.
