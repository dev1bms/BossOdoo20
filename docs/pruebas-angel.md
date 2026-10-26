# Sesión de pruebas con Ángel · Accounting test session (90 min)

Hoja preparada el 26/10/2026. Objetivo: que Ángel compruebe el comportamiento contable y fiscal del ciclo
(oferta → expediente → compras → facturas → pagos → rentabilidad) y decida qué ratifica de lo aprobado por Belal el
23/10/2026 en su ámbito. Solo datos **[DEMO]** ficticios: ningún cliente, proveedor ni importe real.

Cada caso separa **qué hace el sistema** (se comprueba) de **qué decide Ángel** (sección final). Los resultados
esperados se comprobaron el 26/10/2026 con un ensayo en la copia local que se deshace al terminar (`dev/uat_dryrun.py`,
sin dejar nada guardado) y con lecturas de boss20 (`dev/uat_records_probe.py`, solo lectura).

## Entornos

| Entorno | Qué se hace | Qué no se hace | Preparación |
|---|---|---|---|
| **boss20** — https://system.bosscontinental.com (base de datos boss20) | Mirar ofertas, expedientes, pedidos y facturas [DEMO]; abrir borradores | **No** contabilizar facturas, **no** registrar pagos, **no** confirmar pedidos de compra, **no** tocar diarios, secuencias, numeración ni ajustes contables. Hoy no hay ningún asiento contabilizado en boss20 | Usuario de Ángel creado por Belal (Ajustes → Usuarios) con Facturación/Contabilidad, Ventas y Compras; para ver el ajuste del caso C4 hace falta acceso a Ajustes |
| **Copia local aislada** — http://localhost:8069 (base de datos `boss_test`, en el ordenador de Belal; compañía ficticia «Empresa Ejemplo S.L. [DEMO]», plan PGC PYMEs, misma tabla de IVA y mismos ajustes que boss20) | Contabilizar, registrar pagos, abonos, marcar servicios como prestados | Nada sale del ordenador: sin tareas programadas (0 activas, servidor sin hilos de cron), sin servidor de correo (SMTP a un puerto cerrado), servicios en línea de Odoo (IAP: OCR de facturas, autocompletar empresas, SMS, tipos de cambio) apuntando a un puerto cerrado y proxy HTTP(S) muerto | `dev/test.sh uat` (≈20 min, la víspera o antes de la sesión) y `dev/test.sh serve`; se usa por pantalla compartida. **No** ejecutar `dev/test.sh run` entre la preparación y la sesión: recrea `boss_test`. Al terminar: `dev/test.sh down` |

Mismos ejemplos en los dos entornos, con otros números:

| Ejemplo | boss20 | Copia local |
|---|---|---|
| Oferta de cliente español (borrador) | S00012 | S00004 |
| Oferta MSC aceptada, cliente UE | S00009 → expediente E260001 | S00001 → expediente E260001 |
| Pedido de compra (borrador) a MSC | P00001 (MSC [MUESTRA]) | P00001 (MSC [DEMO]) |
| Envío aéreo WFS | S00016 → E260002 | S00005 → E260002 |
| Clientes para zonas de IVA | — | [DEMO] Cliente Canarias, [DEMO] Cliente Ceuta, [DEMO] Cliente Suiza |

## Agenda

| Min | Caso | Entorno |
|---|---|---|
| 0–5 | Entornos y reglas de la sesión | — |
| 5–20 | C1 IVA de cada caso | boss20 + local |
| 20–27 | C2 Datos del cliente para contabilizar | local |
| 27–37 | C3 Factura de proveedor por cantidad prestada | boss20 + local |
| 37–45 | C4 Factura de proveedor: contabilizar sí, pagar todavía no | local |
| 45–53 | C5 Factura de cliente por servicios elegidos y pago al proveedor | boss20 + local |
| 53–61 | C6 Facturación parcial y abono | local |
| 61–68 | C7 Suplidos sin pedido de compra | boss20 + local |
| 68–78 | C8 Rentabilidad | boss20 + local |
| 78–90 | Decisiones de Ángel | — |

Defectos conocidos antes de la sesión (encontrados en el ensayo del 26/10, sin corregir):
- **D-1** Una factura de proveedor creada desde el pedido lleva **todas** las líneas del pedido, también las de cantidad
  0 (servicios aún no prestados). El bloqueo de pago las cuenta: el pago sigue bloqueado aunque el servicio facturado ya
  esté facturado al cliente. Mientras tanto: borrar las líneas de cantidad 0 antes de contabilizar (C3).
- **D-2** Los suplidos (ARA, IVA, PLA, DUM) tienen desde el 23/10 la cuenta 419000, que en el plan de Odoo es de tipo
  **a pagar**. Con ella no se puede crear la factura del agente de aduanas ni facturar el suplido al cliente, **también
  en boss20**. Odoo 17 no usa la 419000 sino subcuentas 419001–419007 de pasivo corriente (C7). Decisión de Ángel.

---

## C1 · IVA de cada caso (15 min)

**Objetivo**: comprobar que cada línea lleva el impuesto de Odoo que dicen las reglas de Ángel (31/08) y lo aprobado el
23/10 (P17), y que un caso sin decidir queda «IVA pendiente» en vez de adivinarse.
**Entorno**: boss20 (pasos 1–2, solo mirar) y copia local (pasos 3–5).
**Requisitos**: ninguno.
**Registros**: boss20 S00012 y S00009; local S00004 y los clientes de zona.

**Pasos**
1. boss20 → Ventas → S00012 ([DEMO] Cliente Ejemplo, S.L., Valencia; importación China → Valencia): ver la columna de
   impuestos de cada línea y el detalle de IVA de la línea.
2. boss20 → S00009 ([DEMO] Cliente UE Ejemplo GmbH, Alemania, con NIF intracomunitario): ver los impuestos.
3. Local → S00004 → Acción → Duplicar → cambiar el cliente por **[DEMO] Cliente Canarias** → guardar → ver impuestos.
   Repetir con **[DEMO] Cliente Ceuta** y **[DEMO] Cliente Suiza**.
4. Local → otra copia de S00004 (cliente español) → «Añadir servicios» → CAU (caución) → ver el IVA de la línea CAU.
5. Intentar confirmar esa copia.

**Resultado esperado**
| Paso | Línea | Impuesto |
|---|---|---|
| 1 | THC (EX, cliente península) | «0% Exent Art.22» |
| 1 | DEM (NR: China → España, cliente español) | «21% S» |
| 2 | THC, BL, DEM, OCU (EX, cliente UE) | «0% UE S» |
| 2 | ARA (suplido, NS) | «0% Exent NS» |
| 3 | Canarias y Ceuta: THC y DEM (zona CAN; DEM pasa a EX) | «0% S NS» |
| 3 | Suiza: THC y DEM (tercer país; DEM pasa a EX) | «0% EX S» |
| 4 | CAU (NS que no es suplido, cliente español) | Sin impuesto: «IVA pendiente» (decisión abierta) |
| 5 | — | No se confirma: «… no está lista para enviar o aceptar: [CAU] …: … sin impuesto de Odoo para la clase NS y la zona de cliente PRO en la tabla de IVA BOSS (decisión pendiente)» |

**Resultado real**:

**Observaciones**:

---

## C2 · Datos del cliente para contabilizar (7 min)

**Objetivo**: una factura de un cliente de España sin NIF (ni otra identificación) no se contabiliza; con NIF sí. La
dirección que falta solo se avisa (P31).
**Entorno**: copia local.
**Requisitos**: S00004 en borrador; el cliente [DEMO] Cliente Ejemplo, S.L. no tiene NIF.
**Registro**: S00004 → su expediente nuevo.

**Pasos**
1. S00004 → Confirmar → se abre un expediente nuevo (E2600xx).
2. Expediente → «Facturar servicios» → todas las líneas → crear → borrador de factura (THC «0% Exent Art.22», DEM
   «21% S»).
3. Confirmar (contabilizar) la factura.
4. Abrir el cliente y escribir el NIF ficticio que imprime `dev/uat_customers.py` al preparar la copia; volver a la
   factura y confirmar.

**Resultado esperado**
- Paso 3: «Borrador de factura (S000xx) no se puede contabilizar: - cliente [DEMO] Cliente Ejemplo, S.L. de España sin
  NIF ni otra identificación».
- Paso 4: factura contabilizada con número de la serie de ventas (INV/2026/…).

**Resultado real**:

**Observaciones**:

---

## C3 · Factura de proveedor por cantidad prestada (10 min)

**Objetivo**: con el control «cantidades recibidas» (P32) solo se factura lo que el proveedor ha prestado; la factura de
proveedor lleva el impuesto del documento del proveedor.
**Entorno**: boss20 (paso 1, solo mirar) y copia local (pasos 2–7).
**Requisitos**: ninguno.
**Registros**: P00001 y E260001.

**Pasos**
1. boss20 → producto THC → pestaña Compra: «Política de control» = cantidades recibidas (los 77 servicios BOSS activos
   están así desde el 23/10).
2. Local → E260001 → pedido P00001 (MSC [DEMO]) → Confirmar pedido.
3. Botón de crear la factura de proveedor del pedido («Crear factura»).
4. Cancelar ese borrador. Volver a E260001 → pestaña «Servicios y costes» → en las dos líneas THC, botón ✓ «Marcar como
   prestado».
5. P00001 → «Crear factura».
6. **Defecto D-1**: borrar las líneas con cantidad 0 (BL, DEM, OCU).
7. Fecha de factura y referencia del proveedor ([DEMO] MSC-0001) → Confirmar sin impuesto; después elegir el impuesto
   de compra que corresponda al documento del proveedor y confirmar (eso se hace en C4).

**Resultado esperado**
- Paso 3: un borrador con **todas** las cantidades a 0 (nada prestado todavía).
- Paso 5: THC 1 + 1 (180 € + 240 €); BL, DEM y OCU con cantidad 0.
- Paso 7 sin impuesto: «… no se puede contabilizar: - [THC] …: elija el impuesto que figura en la factura del
  proveedor (incluido 0 %)».

**Resultado real**:

**Observaciones** (¿qué impuesto de compra corresponde a una THC facturada por una naviera?):

---

## C4 · Factura de proveedor: contabilizar sí, pagar todavía no (8 min)

**Objetivo**: la factura de proveedor de un servicio del expediente **se contabiliza** a su llegada; su **pago** se
bloquea hasta que la factura de cliente de ese servicio esté contabilizada (P30, ajuste «Bloquear el pago (contabilizar
permitido)»).
**Entorno**: copia local (boss20 solo para ver el ajuste).
**Requisitos**: C3 hecho; la factura de cliente de THC de E260001 sigue en borrador.
**Registro**: la factura de proveedor de C3.

**Pasos**
1. (boss20) Ajustes → Ventas, junto a las listas de precios → «Factura de proveedor antes de la de cliente» = «Bloquear el pago
   (contabilizar permitido)». Las otras opciones: «Solo avisar» y «Bloquear contabilización y pago».
2. Local → factura de proveedor de C3: leer el aviso «Comprobaciones de la factura de proveedor».
3. Elegir el impuesto de compra y Confirmar.
4. «Pagar» (registrar pago).

**Resultado esperado**
- Paso 2: «E260001 · [THC] …: aún no facturado al cliente».
- Paso 3: contabilizada (FACTURA/2026/10/…).
- Paso 4: «FACTURA/2026/10/… ([DEMO] MSC-0001) aún no se puede pagar: - E260001 · [THC] …: aún no facturado al
  cliente».
- Excepciones (opcional): un coste «Cubierto por el precio acordado», «Lo asume BOSS» o «Pagado por adelantado» no
  bloquea el pago.

**Resultado real**:

**Observaciones**:

---

## C5 · Factura de cliente por servicios elegidos y pago al proveedor (8 min)

**Objetivo**: facturar al cliente solo algunos servicios (hito) con el impuesto y la cuenta de ingreso correctos; después
el pago al proveedor queda libre.
**Entorno**: boss20 (paso 1, solo mirar) y copia local (pasos 2–3).
**Requisitos**: C4 hecho.
**Registro**: E260001, borrador de factura de THC.

**Pasos**
1. boss20 → E260001 → Facturas: borrador solo con las dos THC, sin número todavía.
2. Local → mismo borrador → Confirmar.
3. Volver a la factura de proveedor de C4 → «Pagar» (registrar pago) → diario de banco → Crear pago.

**Resultado esperado**
- Paso 1: 560 € sin impuestos, dos líneas THC con «0% UE S» y cuenta 700000.
- Paso 2: contabilizada (INV/2026/…).
- Paso 3: el pago se registra. Con el defecto D-1 (líneas de cantidad 0 sin borrar) seguiría bloqueado por BL, DEM y
  OCU.

**Resultado real**:

**Observaciones**:

---

## C6 · Facturación parcial y abono (8 min)

**Objetivo**: facturar parte de una cantidad y anular una factura con un abono; el expediente lleva la cuenta de lo
facturado y de lo que falta.
**Entorno**: copia local.
**Requisitos**: C5 hecho.
**Registros**: E260002 (HAN 500 kg) y la factura de THC de C5.

**Pasos**
1. E260002 → «Facturar servicios» → HAN → crear → en el borrador cambiar la cantidad de 500 a 300 kg → Confirmar.
2. E260002 → pestaña «Servicios vendidos» y «Resumen».
3. Factura de THC de C5 → «Factura rectificativa» (abono) → Confirmar el abono.
4. E260001 → «Resumen».

**Resultado esperado**
- Paso 2: HAN «Facturado en este expediente» 300, «Por facturar en este expediente» 200; Facturado 17,25 €, Por
  facturar 276 €.
- Paso 3: abono (RINV/2026/…) de 560 €.
- Paso 4: Facturado 0 €: el abono se resta.

**Resultado real**:

**Observaciones**:

---

## C7 · Suplidos sin pedido de compra (7 min)

**Objetivo**: los derechos del DUA (ARA) los paga el agente de aduanas y los factura a coste, sin pedido de compra; al
cliente se le refacturan con «0% Exent NS». Comprobar la cuenta (P18).
**Entorno**: boss20 (pasos 1–2, solo mirar) y copia local (pasos 3–4).
**Requisitos**: ninguno.
**Registros**: E260001, servicio ARA, [DEMO] Agente de Aduanas Ejemplo.

**Pasos**
1. boss20 → producto ARA → pestaña Contabilidad: cuentas de ingreso y gasto.
2. boss20 → E260001 → «Servicios y costes»: ARA sin pedido, estado «Factura sin pedido esperada».
3. Local → E260001 → «Coste sin pedido de compra» → proveedor [DEMO] Agente de Aduanas Ejemplo, línea ARA 350 €.
4. Local → E260001 → «Facturar servicios» → ARA.

**Resultado esperado hoy (defecto D-2)**
- Paso 1: 419000 «Acreedores por operaciones en común» en ingreso y gasto (configurado el 23/10).
- Paso 3: «Cualquier apunte contable en «419000 Acreedores por operaciones en común» (a pagar) debe tener una fecha
  de vencimiento.»
- Paso 4: «La cuenta 419000 Acreedores por operaciones en común es de tipo por pagar, pero se está utilizando en una
  operación de venta.»

**Resultado esperado cuando Ángel decida las cuentas**: factura del agente sin pedido, en la cuenta de suplidos y con la
cuenta analítica del expediente; el servicio pasa a facturado; su pago espera a la factura de cliente de ARA (como C4);
la línea de cliente lleva «0% Exent NS» y la cuenta de suplidos de venta.

**Resultado real**:

**Observaciones**:

---

## C8 · Rentabilidad (10 min)

**Objetivo**: las cifras del expediente salen solo de documentos; los borradores no cuentan; el margen no es definitivo
mientras queda coste por facturar.
**Entorno**: boss20 (paso 1) y copia local (paso 2).
**Requisitos**: en local, C3–C6 hechos.
**Registro**: E260001.

**Pasos**
1. boss20 → E260001 → «Resumen» y «Dónde salen las cifras».
2. Local → E260001 → «Resumen».

**Resultado esperado**
- Paso 1: Venta acordada 1.385 € (aceptada 1.225 € + 160 € añadidos con motivo); coste en la aceptación 1.010 €;
  coste final previsto 1.130 €; **Margen en la aceptación 215 €**; **Margen previsto tras costes externos 255 €**, no
  definitivo; no cuentan la factura de cliente en borrador (560 €) ni las solicitudes de presupuesto (780 €).
- Paso 2: coste real 420 € (las dos THC facturadas por MSC), coste aún previsto 710 €, coste final previsto 1.130 €,
  facturado 0 € (tras el abono de C6); margen previsto 255 €; sin margen definitivo porque los costes no están completos.

**Resultado real**:

**Observaciones** (¿el margen «tras costes externos» le sirve, o necesita coste interno, P38?):

---

## Decisiones de Ángel

Aprobadas por Belal el 23/10/2026; el sistema ya funciona así, salvo lo que se indica. Ninguna está ratificada todavía.

| Id | Qué hace hoy el sistema | Caso | Ratifica / Cambia / Pendiente | Nota |
|---|---|---|---|---|
| P17 | EX de cliente español «0% Exent Art.22»; Canarias, Ceuta y Melilla «0% S NS» (zona CAN) | C1 | | |
| P31 | No se contabiliza la factura de un cliente de España sin NIF ni otra identificación; la dirección solo se avisa | C2 | | |
| P32 | Facturas de proveedor por cantidades prestadas en todos los servicios BOSS | C3 | | |
| P30 | Factura de proveedor contabilizable; pago bloqueado hasta la factura de cliente (con Cristina) | C4, C5 | | |
| P18 · P37 | Suplidos en 419000 (cuenta **a pagar**: no funciona, D-2). Odoo 17 usa 419001 IVA repercutido, 419002 aranceles repercutidos, 419003 IVA soportado, 419004 aranceles soportados, 419005 antidumping, 419006 y 419007 plástico repercutido y soportado (pasivo corriente) | C7 | | |
| P03 | Coste en otra moneda al tipo de Odoo del día de la oferta, congelado al aceptar | — | | |
| P11 | IVA de THC todo EX | C1 | | |
| P38 | Margen «tras costes externos», sin coste interno | C8 | | |
| P39 | Sin «Gastos» de Odoo para gastos de empleados | — | | |
| P33 | Pedido de compra para servicios de proveedor; suplidos sin pedido (con Cristina) | C3, C7 | | |

Cuestiones abiertas, sin respuesta supuesta (el sistema hace lo que dice la columna):

| Id | Cuestión | Hoy | Respuesta de Ángel |
|---|---|---|---|
| P17 | IVA de NS que no son suplidos (CAU, QBR) para cliente español | «IVA pendiente» (C1) | |
| P18 · P37 | Cuentas de suplidos (venta y compra, por concepto) y de ingreso y gasto por categoría | 419000 (D-2); resto, las de la categoría | |
| — | Impuesto de compra de cada tipo de factura de proveedor (naviera, handler, agente de aduanas) | Lo elige quien registra la factura | |
| P03 | Porcentaje de QBR y factura en EUR de un pedido en USD | Sin QBR | |
| P01 · P02 | Margen mínimo y quién aprueba vender por debajo | Sin mínimo | |
| P13 | Caución (CAU) y seguro (SEG): porcentajes, tasas y mínimos | Sin valores | |
| P45 | SII o VeriFactu y declaraciones desde el arranque | Nada instalado; nada se envía | |
| — | Dónde se hacen las pruebas con asientos antes del arranque (boss20 no tiene ninguno) | Copia local aislada | |

Firma / fecha:
