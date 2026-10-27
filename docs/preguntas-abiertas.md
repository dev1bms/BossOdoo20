# Decisiones de negocio · Business decisions (revisión 23/10/2026)

Preguntas que cambian un cálculo o un comportamiento. Revisadas contra Odoo 19 (`docs/agents/DECISIONS.md`,
`BOSS_DECISION_LOG.md`, `iva_rules.md`, actas), la carpeta NEW ODOO y Odoo 17 producción (solo lectura).
Mientras una pregunta sigue abierta el sistema hace lo que dice la última columna; nunca usa un valor inventado.
Importes de los ejemplos ilustrativos; las cifras reales de proveedor están en `.research/` (fuera de Git).
Questions that change a calculation or behaviour, reviewed against the previous projects; open ones are ordered
by impact. Amounts are illustrative.

## Aprobadas el 23/10/2026 · Approved on 23/10/2026

El 23/10/2026 **Belal aprobó** las propuestas de respuesta a las preguntas abiertas y el sistema funciona así desde
entonces. **Ninguna ha sido ratificada todavía por Ángel ni por Cristina**: cada decisión de su ámbito (Ángel: finanzas,
IVA, cuentas; Cristina: servicios, precios, operaciones) queda «pendiente de ratificación» hasta que la confirmen, con
fecha y fuente. Si un responsable decide otra cosa, se cambia el ajuste o el dato, no se interpreta.
Plan de implantación en tres fases, sobre la estructura del proyecto (servicios, tarifas, oferta, expediente; Odoo
estándar primero): **A** configuración o código pequeño (hecho), **B** desarrollo, **C** datos que solo pueden dar las
personas (el sistema ya los admite). Ninguna tarifa real se aprueba en nombre de Cristina.

| Id | Decisión aprobada por Belal | Fase | Estado en el sistema | Ratificación |
|---|---|---|---|---|
| P17 | IVA de un cliente español en servicios EX: «0% Exent Art.22» (exento art. 22, 303 [60]). Canarias, Ceuta y Melilla: «0% S NS» (no sujeta por localización, 303 [120]); Ceuta y Melilla en la zona CAN | A | Hecho: tabla de IVA BOSS y reglas de zona. Sigue abierto: NS que no son suplidos (CAU, QBR) de cliente español | Ángel: pendiente |
| P03 | Coste en otra moneda: tipo de Odoo del día de la oferta, congelado al aceptar. QBR solo cuando una oferta en USD se factura en EUR | A + B | Tipo de cambio hecho (ajuste de la compañía). QBR: fase B (Odoo factura en la moneda del pedido; hay que diseñar la factura en EUR de un pedido en USD) | Ángel: pendiente |
| P30 | La factura de proveedor **se puede contabilizar** a su llegada; lo que espera es su **pago**, hasta que la factura de cliente del servicio esté contabilizada (excepciones: coste que asume BOSS o cubierto, flete pagado por adelantado) | A | Hecho: ajuste «Bloquear el pago (contabilizar permitido)», por defecto. El ajuste admite también «Solo avisar» y «Bloquear contabilización y pago» | Ángel y Cristina: pendiente |
| P32 | Factura de proveedor de servicios por cantidades **prestadas** | A | Hecho: servicios BOSS con control «cantidades recibidas»; botón «Marcar como prestado» en el expediente | Ángel: pendiente |
| P18 · P37 | Suplidos (ARA, IVA, PLA, DUM) en una cuenta propia de suplidos (propuesta: 419000); el resto de cuentas por categoría las fija Ángel | A + C | Configurado el 23/10 en 419000, pero en Odoo es una cuenta **a pagar**: impide registrar la factura del agente y facturar el suplido al cliente (comprobado el 26/10 en la copia local; boss20 tiene la misma configuración, defecto D-2, sin corregir). Odoo 17 no usa la 419000 sino las subcuentas 419001–419007 (pasivo corriente). Resto de cuentas: sin decidir | Ángel: pendiente |
| P40 | WFS «por 24 horas»: periodos de 24 h desde la llegada | A | Hecho en los precios WFS [MUESTRA] (siguen pendientes de aprobación, P19) | Cristina: pendiente |
| P41 | WFS «por 100 kg»: por 100 kg **o fracción** | A | Hecho, ídem | Cristina: pendiente |
| P29 | Tramos WFS: el precio alto solo en los días siguientes (por número de día) | A | Hecho, ídem | Cristina: pendiente |
| P42 | Mínimo de WFS por estancia de la AWB | A | Hecho, ídem | Cristina: pendiente |
| P31 · P38 · P39 · P11 (IVA de THC) | Se confirma lo que ya hace el sistema: NIF u otra identificación del cliente de España para contabilizar (dirección solo aviso); margen «tras costes externos» (sin coste interno); sin «Gastos» de Odoo; IVA de THC todo EX | A | Sin cambios: ya implantado | Ángel: pendiente |
| P33 · P35 · P36 · P05 · P06 · P07 · P11 (PAD) · P12 · P14 | Se confirma lo que ya hace el sistema: pedido de compra para servicios de proveedor y suplidos sin pedido; visibilidad estándar por rol; numeración E26xxxx; oferta con coste pendiente con aviso; recotizar solo el gestor con motivo; PAD bajo T3; DEM/OCU/VGM/GLO vendibles y PFT nunca; peso tasable de la AWB o de la tarifa | A | Sin cambios: ya implantado | Cristina: pendiente (P33 también Ángel) |
| P43 | Venta única de ALM con los valores del 25/09 (por 100 kg o fracción y día superadas 48 h; mínimo; desde el 8.º día otro precio desde el día 1) | B | Falta: los importes del 25/09 (Odoo 19, condiciones de almacenaje de clientes) y la regla de venta por tiempo. Especificación: `docs/especificacion-alm-venta.md` | Cristina: pendiente |
| P10 · P09 | ETX: compra por AWB máster y venta por expediente. DET: código propio cuando el proveedor lo factura aparte | B | Configurar los dos servicios (unidades y forma de cotizar) con el documento del proveedor | Cristina: pendiente |
| P44 | Almacenaje especial con condición de tipo de carga; código nuevo para el almacén fuera del aeropuerto | B + C | Falta: tarifas especiales y aprobación del código | Cristina y Ángel: pendiente |
| P19 | Cristina revisa cada tarifa con su PDF y los ejemplos y la aprueba | C | Pendiente de Cristina. Tabla de revisión: `docs/revision-tarifas.md` | Cristina |
| P28 | Pedir a IRENEO la tarifa 2026 o una confirmación escrita | C | Pendiente de Cristina. Las tarifas IRENEO 2025 no se prorrogan | Cristina |
| P01 · P02 | Precios pactados por cliente en su lista de precios; margen mínimo con el valor que fije Ángel | C | Mecanismo listo; faltan los valores | Cristina (precios) y Ángel (mínimo) |
| P24 | Lista de países «Lejano Oriente» (FuelEU) y tráficos «short sea» | C | Pendiente de Cristina | Cristina |
| P16 | Definir los servicios de uso real (unidad, proveedor, documento) y retirar el resto | C | Pendiente de Cristina | Cristina |
| P34 | Precio cerrado para varios envíos: clientes, duración y cantidades máximas de cada acuerdo | C + B | Pendiente de Cristina; después, el acuerdo en el sistema | Cristina |
| P13 | Caución (CAU) y seguro (SEG): cada valor como tarifa con su documento | C | Pendiente de Cristina + Ángel | Cristina y Ángel |
| R-A2 | Tráficos cruzados (X) y nacionales (N) de Odoo 17 (`x_traficos`) | C | Odoo 20 solo tiene importación y exportación | Cristina |
| R-A3 | Ordenante de un expediente de agente (B17 de Odoo 19): validar tipo de contacto Agente / Cliente como Odoo 17 | C | Se guarda «Negocio de» (B/A) y el código de tráfico; sin validación del tipo de contacto | Cristina |
| R-A4 | Migración de contactos y direcciones de entrega desde Odoo 17 | C | Se crean a mano (Belal: «I will migrate all the users») | Belal |
| R-A5 | Fecha clave de un LCL de importación (Odoo 17: fecha de vaciado) | C | En la oferta, la ETA; en el expediente ya existe la fecha de vaciado | Cristina |
| R2-A1 | ¿Un coste de flete tecleado solo para una oferta debe guardarse también como precio reutilizable (ruta y semana)? (reunión parte 2) | C | Dos vías: coste manual en la línea o precio semanal desde ⊕ con ruta y validez | Cristina y Ángel |
| R2-A2 | ¿Quién aprueba los precios semanales de flete? (P19) | C | Aprobador de tarifas; el asistente los deja en borrador o los envía a aprobación | Ángel |
| R2-A3 | Venta por defecto: ¿+20 % sobre el coste o 20 % de margen sobre la venta? | C | Nada activo; venta de la lista del cliente o tecleada | Cristina y Ángel |
| R2-A4 | «Super cubic meter» (Ángel: «I will explain that on Teams later») | C | Sin dato; nada implementado | Ángel |
| R2-A5 | «PP» en las plantillas de venta («menos el PP que se pone caso por caso»): ¿flete prepagado (prepaid)? ¿otra cosa? | C | Sin definir; la venta se teclea o viene de la lista del cliente | Cristina / Ángel |
| R2-A6 | ¿Se usa el transporte convencional por kg tasable (TTE-CON) en envíos FCL? Si sí, el volumen debe verse también en FCL | C | En FCL el volumen está oculto en la pestaña Envío | Cristina |
| R-S1 | Caso de las plantillas IAB FOB, IMB FOB, EAB (sentido, modo, carga, incoterm, cliente de BOSS) y lo que gestiona BOSS deducido de sus servicios | C | Cargado como **propuesta** (`dev/setup_templates.py`); se cambia en la plantilla | Cristina |

### Cuestiones contables y fiscales sin decidir · Open accounting and tax questions

Ninguna tiene una respuesta supuesta: mientras sigan abiertas, el sistema hace lo que dice la última columna.

| Id | Cuestión | Quién | Mientras tanto (en el sistema) |
|---|---|---|---|
| P17 (parte) | IVA de los servicios NS que no son suplidos (CAU, QBR) para un cliente español | Ángel | «IVA pendiente»: la oferta no se puede enviar ni confirmar |
| P18 | Cuentas de los suplidos, de venta y de compra, por concepto. 419000 no sirve (cuenta a pagar, D-2); Odoo 17 usa 419001 IVA repercutido, 419002 aranceles repercutidos, 419003 IVA soportado, 419004 aranceles soportados, 419005 antidumping, 419006 y 419007 plástico repercutido y soportado | Ángel | ARA, IVA, PLA y DUM en 419000: su factura de proveedor y su facturación al cliente no se pueden registrar |
| P37 | Cuentas de ingreso y gasto por servicio o categoría | Ángel | Las de la categoría del producto; nada inventado |
| P03 (QBR) | Porcentaje del quebranto y cómo se factura en EUR un pedido en USD (diferencia de cambio) | Ángel | Odoo factura en la moneda del pedido; sin línea QBR |
| P01 · P02 | Valor del margen mínimo y quién aprueba vender por debajo | Ángel (+ Cristina) | Sin margen mínimo |
| P13 | Porcentajes, tasas y mínimos de caución (CAU) y seguro (SEG) | Cristina + Ángel | Sin valores aprobados |
| P38 | Coste interno de los servicios propios de BOSS | Ángel | Margen «tras costes externos»: no es beneficio neto |
| P45 | Envío de facturas a la AEAT (SII o VeriFactu) y declaraciones que debe preparar Odoo 20 desde el arranque | Ángel | Ningún módulo SII ni VeriFactu instalado en boss20 (comprobado el 26/10/2026); nada se envía |

### Defectos conocidos (26/10/2026) · Known defects

| Id | Defecto | Estado |
|---|---|---|
| D-1 | Una factura de proveedor creada desde el pedido lleva todas sus líneas, también las de cantidad 0 (servicios no prestados), y el bloqueo de pago (P30) las contaba | Corregido con prueba y **desplegado en boss20 el 26/10** (W09); comprobado en boss20_uat: la factura de MSC con 4 líneas a 0 se paga tras facturar al cliente (`dev/uat_cycle.py`, C5) |
| D-2 | Los suplidos (ARA, IVA, PLA, DUM) en la cuenta 419000, que es **a pagar**: ni la factura del agente ni la factura al cliente se pueden crear, también en boss20 | Mapa de cuentas como Odoo 17 (419001–419007, pasivo corriente) **aplicado en boss20 y boss20_uat el 26/10** por mandato de Belal (W10); Ángel lo ratifica o corrige (A02). Comprobado en boss20_uat: factura del agente de ARA en 419004 y factura al cliente en 419002 (C7) |
| D-3 | El bloqueo de pago de la factura de proveedor (P30) solo actuaba en el botón «Registrar pago» de la factura; el asistente de pagos abierto desde una lista o un extracto lo saltaba | Encontrado en boss20_uat el 26/10 (C4); corregido con prueba (el asistente también se rechaza) y desplegado en boss20 y boss20_uat el 26/10 |
| D-4 | Odoo 20 copia todas las líneas del pedido en la factura: un pedido sin nada prestado creaba una factura de ceros | Encontrado en boss20_uat el 26/10 (C3); ahora «Crear factura» se rechaza con el aviso «ningún servicio marcado como prestado» (prueba; desplegado el 26/10) |
| D-5 | Tras un abono al cliente del servicio, el pago de la factura del proveedor quedaba retenido para siempre (el bloqueo P30 contaba lo facturado neto) | Encontrado en boss20_uat el 26/10 (ciclo E2E); ahora basta con que el servicio se haya facturado una vez (prueba; desplegado el 26/10, `da0e263`) |
| D-6 | Las plantillas de oferta tenían en inglés un nombre antiguo distinto del español: con la interfaz en inglés no se encontraban por «IMB FOB» | Encontrado en Chrome el 26/10; nombres «[DEMO] <caso> …» en los dos idiomas (`dev/setup_templates.py`) |
| D-7 | La nota interna de las plantillas («Plantilla de servicios que aplican SIEMPRE…») iba en «Términos y condiciones»: Odoo la copia a la oferta y a las facturas del cliente | Encontrado en Chrome en boss20 el 27/10 (INV/2026/00002, RINV/2026/00001). Las plantillas ya no llevan nota (`dev/setup_templates.py`, `1958bb0`); quitada de las plantillas y de S00024/S00025/S00027/S00031 en boss20; comprobado en Chrome: una oferta nueva desde «IMB FOB» sale sin nota. Las facturas ya contabilizadas (INV/2026/00001–00003, RINV/2026/00001) la conservan: son de prueba |
| D-8 | El «margen final» se calculaba con la venta acordada aunque un abono la había reducido (E260015: 315 € en lugar de 240 €) y se llamaba final con 75 € todavía por facturar | Encontrado en Chrome en boss20 el 27/10. Ahora el margen es definitivo solo con los costes completos **y** nada por facturar, y se calcula con lo facturado neto de abonos; si no, el resumen dice qué falta («facturarlo, o recotizar el servicio si no se va a facturar»). boss_expediente 20.0.1.8.0 (`1958bb0`); comprobado en Chrome: E260015 margen final 240 € = 3.090 − 2.850 |
| D-9 | «Recotizar» no funcionaba desde la interfaz: «Missing required field Sale Line» y, corregido eso, «prohibido modificar… en un pedido bloqueado»; además un precio 0 recotizado quedaba como «precio de venta que falta» | Encontrado en Chrome en boss20 el 27/10. La fila envía su línea, el asistente desbloquea el pedido solo para el cambio y lo vuelve a bloquear, y un 0 puesto con motivo queda «sin cargo». boss_pricing_sale 20.0.1.8.2 (`fix(pricing_sale)` ×3); comprobado en Chrome en S00031 (BL a 0 € con motivo, pedido sigue bloqueado) |
| D-10 | Una regla de lista de precios de un servicio BOSS mostraba «por <unidad>» junto al precio pero dejaba la unidad vacía, y al guardar daba «debe indicar su base de cobro» | Encontrado en Chrome en boss20 el 27/10 (lista de COFITEL). La regla toma la unidad del servicio (boss_pricing_sale 20.0.1.9.1); comprobado en Chrome |
| D-11 | «Añadir servicios» añadía otra vez un servicio que ya estaba en la oferta (HAN, con el handler propuesto) sin avisar | Encontrado en Chrome en boss20 el 27/10 (S00032). No se añade si ya existe con la misma unidad, grupo de contenedor y proveedor, y avisa «No se añade dos veces»; con otro proveedor sí (segundo proveedor a propósito). 20.0.1.9.2; comprobado en Chrome (S00032 y S00033: solo añadió el FMI 40' que faltaba) |
| D-12 (limitación) | Un precio de venta por envío o por tramo en una línea por kg (manipulación de COFITEL por tramos, recogida por envío) se escribe como precio por kg: si cambia el peso, el importe crece en proporción y no sigue el tramo | Comprobado en Chrome (S00032, 172 → 350 kg). Se documenta en el Inicio rápido: volver a escribir el precio tras cambiar el peso. Odoo no tiene precio de venta por tramo de envío en una línea por kg; solucionarlo sería una función nueva (decisión de Belal) |
| D-13 | Un servicio con coste desconocido (arrastre de MSC) dejaba de estar «desconocido» al confirmarse su pedido a 0 € (lo crea así «Crear solicitudes»): el expediente decía «costes completos» y «margen final» sin ese coste | Encontrado en Chrome en boss20 el 27/10 (E260017). Sigue desconocido mientras el pedido esté a 0 y no haya factura; boss_expediente 20.0.1.8.1; comprobado en Chrome: «2 servicios con coste desconocido», margen «NO DEFINITIVO» |

También el 27/10: aplicar o cambiar una plantilla en una oferta con líneas ya no borra nada (Odoo estándar borraba todas
las líneas): añade solo los servicios que faltan y avisa (boss_pricing_sale 20.0.1.9.0, comprobado en Chrome); la
precisión de «Precio del producto» pasa a 4 decimales (precios reales por kg con 3 decimales); tipos del BCE cargados
con el proveedor estándar de Odoo.

### Excepciones de tarifas y precios (27/10/2026) · Tariff exceptions

| Excepción | Efecto concreto | Quién o qué la resuelve |
|---|---|---|
| THC de importación MSC: la tarifa 01/09–31/12/2026 (p.12) y las facturas reales de MSC de 09–10/2026 no coinciden (las facturas cobran menos por contenedor) | El coste previsto de THC es algo mayor que lo que MSC factura | Preguntar a MSC si hay un acuerdo o edición distinta; hasta entonces vale el documento |
| MSC FuelEU «Lejano Oriente sin China»: la lista de países es una propuesta (P24) | Una importación MSC desde Vietnam, Corea… sale «Precio pendiente de aprobación» | Cristina confirma la lista |
| Licitación Leroy Merlin 2025/26 (demoras y ocupaciones ONE, Maersk, OOCL, MSC): aprobada hasta el 31/05/2026 | Los envíos de Leroy desde 06/2026 usan las tarifas públicas de la naviera | Condiciones 2026-27 de Leroy |
| Ocupación MSC: el documento no tiene columna para 40' HC (A5) | 40' HC sale «Sin precio de proveedor» en ocupación | Cristina decide si el 40' HC usa la columna del 40' DV |
| IRENEO: las zonas MAD y MAD-EXT van por código postal y radio de 30 km; no están cargadas | Entregas en la provincia de Madrid: «Sin precio de proveedor» | IRENEO o Cristina confirman la zona de cada población; luego se cargan (p.2) |
| ALM de IRENEO (almacén G-5, «Tarifas MAD 2025» p.15): desde el 27/10 es un precio de «IRENEO Tarifas MAD 2026» (Importación · Aéreo · Carga aérea · MAD) marcado **A consultar**; el documento no dice si los 5 días libres se descuentan o, superados, se cobra desde el día 1 (cargado como «descontados») | La oferta sale «A consultar» para el almacenaje G-5; con 10 días la diferencia entre lecturas es el doble | IRENEO o Cristina confirman la lectura; luego nueva versión de la tarifa sin «A consultar» |
| Iberia (handling) y otros handlers: sin documento de tarifa | Qatar en MAD propone Iberia: sin precio hasta cambiar a WFS | Documento de tarifas de Iberia |
| Despacho aéreo (Aducex, Ramos Vila): solo hay respuesta de Cristina para FCL | FAD aéreo sin precio | Tarifa o confirmación del agente de aduanas |
| Agente en origen (SINOTECH), transportistas de Madrid (Barbican), arrastre MSC | Coste aceptado sin tarifa, con motivo, por un responsable de ventas | Cotización de cada envío o documento de tarifas |
| Impuesto de compra de las facturas de MSC: las de E260015 (26–27/10) se contabilizaron con «0% UE S» (intracomunitario), que no corresponde a un proveedor español; las de E260017 con «0% S Exent NS» (no sujeto, como Odoo 17) | Solo datos de prueba | Ángel fija el impuesto de compra por tipo de factura (A01) |
| Venta del FuelEU (la factura real de AGUILERA no lo cobra) | En S00033 (aceptada → E260017) va «Sin cargo» para reproducir el caso real; su coste cuenta en el margen | Decisión comercial: repercutirlo o no |

Observaciones para decidir (Cristina): tras una recotización, «Venta aceptada» y «Margen en la aceptación» del expediente muestran los precios recotizados (E260015: 3.005 → 2.930 € y 545 → 470 €); los precios aceptados originales siguen en el «Historial de precios». ¿Deben quedarse congelados los de la aceptación? Y en «Recotizar», «Recalcular el coste» viene marcado en todas las líneas: para cambiar solo un precio hay que desmarcarlas.

Siguen abiertas (no estaban entre las propuestas): P20–P23 · P26.
Las tablas siguientes conservan el contexto de cada pregunta.

## Cerradas con respuesta documentada · Closed

| R-A1 | Peso real, peso volumen y peso tasable | **Ángel, Teams 27/10/2026**: aéreo 1 CBM = 167 kg, terrestre 333, marítimo 1000; tasable = el mayor; proveedores cobran a BOSS y BOSS al cliente por peso tasable | Implementado: enmienda de ADR-006, `dev/check_chargeable_weight.py` |
|---|---|---|---|

| Id | Pregunta | Respuesta | Fuente | En el sistema |
|---|---|---|---|---|
| P04 | ¿Qué fecha elige la versión de tarifa? | Importación ETA, exportación ETD | Ángel, reunión 16/10 (acta Odoo 19 `2026-10-18-reunion-angel-16-10.md`) | Fecha prevista del envío. Excepciones por proveedor: no hay ninguna escrita |
| P08 | ¿Qué tipos de contenedor tienen precio propio? | Es un dato de cada documento, no una decisión | Documentos MSC/Hapag/CMA; ejemplo T3 por tipo (Cristina 28/09) | Condición por tamaño y tipo en cada precio |
| P15 | ¿Cómo cuentan las horas libres de WFS? | Umbral en horas reales: 48 h 00 min es libre; superadas, se cobra desde el NOA/FOH incluido, no solo el exceso | Cristina 08/09 (decisión B20, «48,0 h no supera, 49 h sí») y documento WFS 2026 p.5 punto 1 | ALM en modo «umbral» con las horas exactas del periodo real. **Cómo se cuentan los periodos cobrados (24 h o días naturales) sigue abierto: P40** |
| P25 | AWB/BL: ¿máster por expediente o house? | Máster por expediente; los house son la excepción (≈10 %) | Cristina 28/09 (Plan detallado previsiones, «Explicaciones previsiones») | BL y AWB una vez por expediente; DOC para el house |
| P27 | Compañía de Odoo 20: datos, moneda, país, plan contable | Los de Odoo 17 producción: Boss Continental S.L., EUR, España, PGC PYMEs 2008 | `res.company` de Odoo 17 (lectura 22/10) | Configurada en `boss20` (`dev/setup_company.py`) |
| P17 (parte) | Impuesto de Odoo de NR, EX de clientes UE y de terceros países, y NS de suplidos | NR → «21% S»; EX cliente UE → «0% UE S»; EX cliente de tercer país → «0% EX S»; NS suplidos → «0% Exent NS» | Reglas de Ángel 31/08 (B01/B02) + acción 1232 «Create Invoice» de Odoo 17 + naturaleza legal en la localización (ADR-004) | Tabla de IVA BOSS en `boss20` (`dev/setup_vat_mapping.py`) |

## Contexto de las preguntas · Context of the questions

| # | Id | Pregunta | Qué bloquea hoy | Servicios | Propuesta práctica | Quién | Mientras tanto |
|---|---|---|---|---|---|---|---|
| 1 | P17 | **IVA de un cliente español o canario** para servicios EX (y NS que no son suplidos: CAU, QBR); zona de Ceuta y Melilla | Ofertas de clientes de España con servicios EX (THC, T3, fletes, SEG…): no se pueden enviar ni confirmar | THC, T3, T3-PAD, FMI, FME, FAI, FAE, SEG, DEX, EXW, GAV, DVD, SAD; CAU, QBR | Ángel las llama exentas; Odoo 17 usa «0% S» (sujeta al 0 %, casilla 150). Elegir: impuesto exento con su artículo (21/22 → «Exento Art.22», casilla 60…) o la práctica de Odoo 17; Canarias: «no sujeta por localización» (casilla 120). Ejemplo: THC de una importación de China para un cliente de Valencia | Ángel | IVA «pendiente» solo en esos casos; NR, clientes UE y de terceros países y suplidos ya tienen su impuesto (ADR-004) |
| 2 | P19 | **Aprobar las tarifas** de muestra/reales tras revisarlas | Cálculo automático en el servidor (ninguna tarifa aprobada) | THC, T3-PAD, BL, GLO-CCC, GLO-FUELEU, DEM, OCU, ALM, HAN, AWB, X-R | Revisar cada tarifa con su PDF y ejemplos (`ejemplos-referencia.md`) y pulsar «Aprobar» | Cristina (o Belal) | Precio «pendiente de aprobación» |
| 3 | P03 | **Cambio de moneda** para costes en USD y regla del **QBR** | Costes en USD en ofertas en EUR | FMI/FME/FAI/FAE en USD, cualquier tarifa en USD, QBR | Tipo de Odoo del día de la oferta, congelado al aceptar; QBR si la oferta en USD se factura en EUR (requisito de Cristina en «Nuevo Odoo.xlsx») | Ángel | Línea «Otra moneda, sin política»; QBR pendiente |
| 4 | P28 | ¿Las tarifas **IRENEO 2025** siguen vigentes en 2026? ¿Qué recargo de combustible y desde cuándo? | Transporte terrestre y aéreo de IRENEO en 2026 | TTE-CON, FS, SEG, HAN y X-R de IRENEO | Pedir a IRENEO la tarifa 2026 o una confirmación escrita | Cristina | Muestras con vigencia 2025: no se aplican a envíos de 2026 |
| 5 | — | **Documentos de tarifa que faltan** (no es una decisión) | Precio automático de esos servicios | CES, GLO, T3, DOC, ENS/AMS, VGM, FAD, DEX, TRA, EUR1, inspecciones, almacén, TTE-FCL, THC-LCL, agentes | Reunir los PDF vigentes (lista en `fuentes.md`) y cargarlos | Cristina / operaciones | «Sin precio de proveedor» → «Añadir precio de proveedor» desde la oferta |
| 6 | P01 · P02 | **Precio de venta**: ¿reglas por cliente (coste + %, margen)? ¿Margen mínimo y quién aprueba vender por debajo? | Venta automática | Todos los vendibles | El mecanismo existe (lista de precios del cliente con precio fijo, recargo sobre coste, margen sobre venta y margen mínimo). Falta decidir valores por cliente | Cristina (+ Ángel para el mínimo) | Venta pactada en la lista del cliente o tecleada; nunca una regla sin aprobar |
| 7 | P43 | **Precio de venta único de ALM**: Cristina (08/10, transmitido por Belal; original no visto) dijo que ALM tiene un precio de venta único para todos los clientes (no se negocia), solo ALM; los valores quedan pendientes. «Mayor coste de proveedor + %» es una **propuesta** (Belal 08/10), no aprobada y sin porcentaje. ¿Valen los valores que dio el 25/09 (precio por 100 kg o fracción y día desde la llegada, superadas 48 h; mínimo; desde el 8.º día otro precio desde el día 1; registrados en Odoo 19, condiciones de almacenaje de clientes)? | Venta automática de ALM | ALM | Confirmar valores y regla; entonces se construye la regla de venta por tiempo (hoy no existe: una lista de precios por expediente no la expresa, y «coste + %» del proveedor elegido no es lo pedido) | Cristina | Venta tecleada; el sistema no propone precio de venta de ALM |
| 8 | P13 | **Parámetros derivados**: caución (CAU) y seguro (SEG): porcentajes, tasas por país y mínimos | Cálculo de CAU y SEG | CAU, SEG | Cargar cada valor como tarifa con su documento | Cristina + Ángel | Método porcentaje disponible; sin valores aprobados |
| 9 | P16 | Servicios sin definición | Esos servicios | VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM | Definir los de uso real (unidad, proveedor, documento) y retirar el resto | Cristina | «Pendiente de decisión», coste manual posible |
| 10 | P18 | **Suplidos**: producto y tratamiento contable al facturar | Facturación (fase 2) | ARA, IVA, PLA, DUM | Venta = coste del DUA (práctica Odoo 17); confirmar cuenta e impuesto | Ángel | Importe manual a coste, clase NS |
| 11 | P24 | Lista de países «Lejano Oriente» (FuelEU) y tráficos «short sea» de THC | FuelEU fuera de China | GLO-FUELEU, THC | Lista escrita por Cristina | Cristina | Muestra MSC limitada a origen China |
| 12 | P11 | PAD bajo T3 o GLO; presentación «THC + gastos portuarios»; IVA de THC (todo EX o una parte NR) | Presentación e IVA de THC | THC, T3-PAD, GLO | Mantener T3-PAD; Ángel decide si se divide el IVA de THC | Cristina + Ángel | T3-PAD cotiza; IVA según la clase EX del servicio |
| 13 | P10 | ETX: concepto y unidad | ETX | ETX | **Concepto (26/10/2026)**: ETX es la «Tasa Energética» que BOSS vende por envío (oferta real a Cofitel 05570, 03/02/2026, «Gastos en Madrid»); en Odoo 17 existe como «ETX – ENERGY TAX» (IVA por defecto NR). Compra: Cristina 08/10, por AWB máster; el documento de compra que lo respalda está por confirmar (WFS 2026 punto 49 «Recargo de Mantenimiento del Servicio», por AWB, solo importación, se asignó a ETX sin confirmar). Antes de dar el precio por listo faltan: ámbito (¿solo importación?, ¿todos los handlers?), unidad de compra y venta, proveedor y tarifa | Cristina | «Pendiente de decisión» |
| 14 | P09 | DET: ¿código propio o dentro de DEM? | Detención facturada aparte | DET, DEM | Propio cuando el proveedor lo factura aparte | Cristina | DET «pendiente de decisión» |
| 15 | P29 | Tramos de días WFS «hasta 7 / más de 7»: ¿el precio alto solo en los días siguientes o en toda la estancia? El documento no lo dice; la regla de venta que Cristina dio el 25/09 usa toda la estancia («8 días o más … desde el día 1»), pero es venta, no la compra a WFS | Importe de ALM de más de 7 días | ALM | Confirmar con WFS o con una factura real de más de 7 días | Cristina | «Sin decidir» en el precio: hasta 7 periodos se calcula; más, coste manual con los dos importes. Ejemplo ilustrativo: 500 kg, 10 días a 10 €/20 € por 100 kg → 650 € o 1.000 € |
| 16 | P12 | Servicios de coste (DEM, OCU, VGM, PFT, GLO): ¿se venden y cómo? | Venta de esos servicios | DEM, OCU, VGM, GLO, PFT | DEM/OCU/VGM/GLO vendibles con venta tecleada o pactada; PFT nunca se vende (Cristina 29/09) | Cristina | Así configurado |
| 17 | P05 | ¿Enviar una oferta con un coste aún pendiente? | — | Todos | Aviso, sin bloqueo | Cristina | Se bloquean solo IVA pendiente y venta sin indicar |
| 18 | P06 · P07 | Tarifa que cambia durante la validez; ¿quién recotiza una oferta aceptada? | — | Todos | Recotizar con motivo, solo gestor comercial (propuesta del propietario 26/08: cambios con motivo) | Cristina | Así implementado |
| 19 | P14 | Factor de peso tasable cuando el documento no lo dice | Peso tasable sin AWB | Aéreo y terrestre | Peso tasable de la AWB o factor escrito en la tarifa | Cristina | Así implementado: WFS dice «peso cargable indicado en el AWB» (p.4); sin ese peso, «Faltan datos del envío» (nunca 167 ni 333 supuestos). IRENEO escribe su factor (333; 167 en ADT) |
| 20 | P20–P23 · P26 | Visibilidad de coste/margen, ofertas por ruta, alternativas, validez, fusiones de códigos | — | — | Estándar de Odoo hasta decidir | Cristina | Estándar de Odoo; códigos originales |
| 21 | P40 | WFS MAD/BCN «por 24 horas»: ¿periodos de 24 h desde el NOA o días naturales? Hay pruebas contrarias: el documento (p.5) dice «por 24 horas»; un script de Odoo 19 del 10/09 dice «Cristina confirmó que WFS cuenta días naturales»; la pregunta del 25/09 («¿4 periodos de 24 h o 5 días?») no tiene respuesta | Importe de ALM cuando la hora de salida es anterior a la de llegada | ALM | Confirmar con una factura real de WFS o con WFS | Cristina | «Sin decidir» en el precio: si las dos cuentas coinciden se calcula; si no, coste manual con los dos importes. Ejemplo ilustrativo: lunes 10:00 → viernes 10:00 (96 h), 500 kg a 10 €: 4 periodos = 200 € o 5 días = 250 € |
| 22 | P41 | WFS 2026 «por 100 kg» sin «o fracción»: ¿proporcional o por fracción de 100 kg? Cristina (08/09) habló de «fracción de 100 kg» y la edición WFS 2025 decía «por fracción»; la de 2026 no | ALM con peso que no es múltiplo de 100 | ALM | Confirmar con WFS | Cristina | «Sin decidir» en el precio. Ejemplo ilustrativo: 450 kg, 3 días a 10 €: 135 € o 150 € |
| 23 | P42 | WFS puntos 1–3: el mínimo no imprime unidad (los puntos 4–5 dicen «AWB/día», el 6 «por expedición») | ALM de envíos pequeños | ALM | Por estancia de la AWB (cuando WFS quiere por día lo escribe) | Cristina | Mínimo por estancia; el precio tiene «Mínimo por día» para documentos que lo digan |
| 24 | P44 | Almacenaje especial del handler (frío 36 h, peligrosas, valiosas, animales vivos: WFS puntos 2–6) y almacén fuera del aeropuerto (palé, m³, entradas y salidas: código propio, Cristina 08/10; IVA y unidades con Ángel) | Coste de esas estancias | ALM y código nuevo | Cargar las tarifas especiales con una condición de tipo de carga y crear el código de almacén cuando se aprueben | Cristina + Ángel | La tarifa ALM de WFS es de carga general: en carga especial se escribe el coste a mano. No se crean códigos sin aprobar |

## Ciclo operativo: expediente, compras y facturación · Operational cycle (23/10/2026)

Textos y fuentes completos en `docs/ciclo-operativo.md` («Decisiones y requisitos citados»). Etiquetas: **A** decisión
confirmada, **R** requisito escrito por Cristina en «Nuevo Odoo.xlsx» (sin fecha, prioridad ni estado), **C**
práctica observada de Odoo 17/19, **B** abierta.

| Id | Pregunta | Fuente y estado | Quién | Mientras tanto (en el sistema) |
|---|---|---|---|---|
| P30 | ¿Se impide **contabilizar o pagar** una factura de proveedor antes de facturar el servicio al cliente, o es solo el orden de trabajo? | R: «Facturacion» A3, «Facturacion y costes» A11 (con excepción: flete pagado por adelantado a un agente). Odoo 17/19 no lo bloqueaban (C) | Cristina + Ángel | Desde el 23/10 (propuesta aprobada por Belal, pendiente de Ángel y Cristina): la factura de proveedor se puede contabilizar; su pago se bloquea hasta que la factura de cliente del servicio esté contabilizada (aviso en la factura y en el expediente) |
| P31 | **Datos del cliente** obligatorios para contabilizar una factura | C: Odoo 17 bloqueaba clientes de España (o sin país) sin NIF; no bloqueaba extranjeros. A: zona que falta → IVA pendiente (Ángel 31/08). Sin decisión sobre dirección | Ángel | Bloqueo: IVA pendiente y cliente de España sin NIF u otra identificación de la localización; dirección solo se avisa |
| P32 | Control de facturas de proveedor de servicios: ¿cantidades **pedidas o prestadas**? | B | Ángel | Desde el 23/10 (propuesta aprobada por Belal, pendiente de Ángel): cantidades recibidas (prestadas) en todos los servicios BOSS; «Marcar como prestado» en el expediente; es un ajuste del producto |
| P33 | ¿Qué costes van con **pedido de compra** y cuáles como previsión? | B10 (Cristina + Ángel), abierta | Cristina + Ángel | Pedido para servicios de proveedor; los suplidos (derechos e IVA del DUA) sin pedido, como en Odoo 17/19 (C) |
| P34 | ¿Precio cerrado para **varios envíos** (tipo Leroy)? | B (acta 26/08, opción B). A?: una oferta aceptada puede abrir varios expedientes repartiendo sus cantidades (propietario, 26/08) | Cristina | Reparto de cantidades entre expedientes («Mover servicios a otro expediente»); un acuerdo de precios para envíos futuros no está decidido |
| P35 | ¿Quién ve **costes, márgenes y facturas** del expediente? | R: «cada comercial ve solo sus clientes» (CRM A19); costes/márgenes sin decisión (P20) | Cristina | Estándar de Odoo por rol: comercial su expediente, la venta y el coste de la oferta; compras el lado proveedor; gestor comercial y contabilidad todo |
| P36 | Numeración de expedientes al arrancar: ¿continuar Odoo 19 o nueva? | B (Q6) | Belal + Cristina | E26xxxx (formato de Odoo 19) |
| P37 | Cuentas de ingreso y gasto por servicio; suplidos | B (P18) | Ángel | Las de la categoría de producto; nada inventado |
| P38 | Coste interno de los servicios propios de BOSS | Sin decisión | Ángel | Margen «tras costes externos»: no es beneficio neto |
| P39 | ¿Gastos de empleados (tiques, taxis) imputados a expedientes? | Sin requisito ni práctica documentada | Belal + Ángel | No instalado. Si se usa «Gastos» de Odoo, el gasto con la cuenta analítica del expediente cuenta como coste real (recibo `in_receipt`) |
