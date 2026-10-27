# Ciclo operativo y financiero · Operational and financial cycle

Mandato de Belal (23/10/2026). Diseño: [ADR-005](adr/005-operational-and-financial-cycle.md). Este fichero es el
plan, los criterios de aceptación y el registro de progreso (un solo sitio; `plan-implementacion.md` apunta aquí).

## Objetivo
Contacts → CRM (cuando hace falta) → Quotation → Sales Order → Expediente → Purchase Orders → Customer Invoices /
Vendor Bills → Expenses / Credits → coste y rentabilidad. Odoo estándar lleva contactos, ventas, compras, facturas,
contabilidad, analítica y actividades; BOSS añade tarifas, datos del envío, enlaces y resúmenes.

## Criterios de aceptación (desde la interfaz publicada)
1. Crear cliente y proveedor con sus datos; aparecen en Clientes / Proveedores antes de su primer documento.
2. Empezar por CRM o por un presupuesto directo; los datos del envío pasan de la oportunidad al presupuesto.
3. Datos del envío y servicios; quién ejecuta cada servicio (BOSS o proveedor).
4. Coste y venta comprensibles y trazables (tarifa, documento, página, explicación).
5. Precio que falta por el camino adecuado, con aprobación.
6. Confirmar con el acuerdo guardado (foto); coste desconocido de un servicio de proveedor bloquea.
7. Expediente: datos, referencias, fechas, eventos, documentos y enlaces.
8. Pedidos de compra desde el expediente: borradores revisables, sin duplicados, confirmación humana.
9. Facturas de cliente y de proveedor.
10. Parciales, varias facturas, abonos, coste adicional.
11. Coste y rentabilidad correctos y qué falta.
12. Guía igual a las pantallas y ejemplos reproducibles (MSC, WFS, IRENEO, servicio propio).

## Plan por fases
| Fase | Resultado | Depende de | Verificación |
|---|---|---|---|
| F1 Base | habilidades, revisión, ADR-005, este plan | — | ficheros en el repo |
| F2 Contactos y CRM | roles, datos que faltan, oportunidad → presupuesto, repetir envío | F1 | test + navegador |
| F3 Ejecución y foto | BOSS / proveedor por línea, tipo de coste, bloqueo de coste desconocido, foto ampliada | F2 | test |
| F4 Expediente | modelo, creación al confirmar (una vez), analítica, partes, carga, referencias, eventos | F3 | test |
| F5 Compras | necesidades, RFQ sin duplicados, parcial, cancelación, cambio de proveedor, servicio prestado | F4 | test |
| F6 Facturas y rentabilidad | facturación por servicios, parciales, abonos, extras, bloqueo de IVA al registrar, resumen | F5 | test con asientos registrados (BD local) |
| F7 Interfaz y permisos | vistas, menús, grupos, traducción ES, 1366/1920 | F6 | navegador |
| F8 Entrega | despliegue, ejemplos DEMO, verificación en el servidor, guía ES/EN | F7 | navegador en boss20 |

## Registro de progreso
| Fecha | Qué | Dónde | Verificado |
|---|---|---|---|
| 23/10 | Habilidades `odoo-code-tracer` y `verification-before-completion` instaladas (fuentes en `.interface-design/system.md`) | `.claude/skills/` (local, fuera de Git) | lectura de SKILL.md |
| 23/10 | Revisión: boss20 tiene purchase + sale_purchase, sin project / hr_expense / stock; Odoo 17 sin compras | ADR-005 | consultas de lectura |
| 23/10 | Quién ejecuta cada servicio (BOSS / proveedor), tipo de coste, coste desconocido bloquea la aceptación (excepción con motivo por responsable de ventas), servicio añadido tras aceptar solo por acción explícita, foto con base de compra | `boss_pricing_sale` 20.0.1.6.0 | tests Odoo + migración comprobada en boss20 (S00009, S00013) |
| 23/10 | Contactos (cliente/proveedor al instante, roles logísticos, EORI, datos que faltan), oportunidad → oferta con ruta, alcance, partes, carga, contenedores y servicios pedidos; oferta repetida recotiza | `boss_expediente` | tests Odoo |
| 23/10 | Expediente: número E26xxxx, abierto una vez al aceptar (o vinculado a uno preliminar), cuenta analítica, partes, ruta, carga, contenedores, referencias, fechas, eventos, diferencias con la oferta, cierre operativo y económico separados | `boss_expediente` | tests Odoo + navegador boss20 1366/1920 |
| 23/10 | Compras: servicios a comprar con su propia base, solicitudes de presupuesto por proveedor y moneda sin duplicados (bloqueo de fila), precio protegido, «Marcar como prestado», cambio de proveedor solo sin pedido activo | `boss_expediente` | tests Odoo (pedido confirmado + factura de proveedor contabilizada en BD local) |
| 23/10 | Facturas: por servicios elegidos (hitos), segunda factura, abono, coste adicional refacturado con motivo y foto; bloqueos al contabilizar (IVA pendiente, NIF/dirección del cliente, impuesto de la factura de proveedor, factura de proveedor antes de facturar al cliente) | `boss_expediente` | tests Odoo con asientos en BD local |
| 23/10 | Rentabilidad: venta acordada, coste aceptado, compras comprometidas, coste real, pendiente, previsto, margen en la aceptación y tras costes externos, facturado, cobrado, pagado, pendiente | `boss_expediente` | tests Odoo + navegador boss20 |
| 23/10 | Ejemplos [DEMO] en boss20 (sin contabilizar ni confirmar compras): E260001 MSC marítimo (factura borrador solo THC, coste adicional OCU refacturado), E260002 WFS aéreo, E260004 IRENEO terrestre, E260003 solo servicio BOSS | `dev/demo_cycle.py` | salida del script en boss20 |
| 23/10 | Corrección: un recargo en % creado junto a su servicio base (oferta repetida) se calcula sobre él | `boss_pricing_sale` | tests Odoo + IRENEO en boss20 |
| 23/10 (2ª ronda) | Recalcular coste previsto con datos del expediente (contenedores, pesos, días por servicio, fechas reales, proveedor) con el mismo motor; historial de recálculos; venta y foto intactas; pedido confirmado marcado «a revisar» | `boss_expediente` 20.0.1.1.0 | test ALM 5→9 días (75→175 €) y 2º contenedor (THC 240→480 €); boss20 E260002 (AWB 500→620 kg, ALM +3 días) |
| 23/10 (2ª ronda) | Añadir un servicio tras la aceptación (BOSS o proveedor), con motivo y foto; fuera del margen en la aceptación | `boss_pricing_sale` 20.0.1.7.0 | test + boss20 E260003 (CSA 45 €) |
| 23/10 (2ª ronda) | Una oferta, varios expedientes (reparto de cantidades, nunca más de lo aceptado; facturación y analítica por expediente) | `boss_expediente` | test + boss20 E260009/E260010 |
| 23/10 (2ª ronda) | Reglas al contabilizar revisadas con las fuentes (P30 aviso por defecto, P31 identificación según Odoo 17 y la localización); suplidos sin pedido de compra; acceso por rol y compañía; cifras con su origen | `boss_expediente` | tests (23 métodos: 0 fallos) |
| 23/10 (2ª ronda) | Rendimiento medido en Chrome visible con sesión normal: 0,95–1,47 s hasta poder usar el formulario o la lista (5 cargas); una primera carga tras el despliegue 8,2 s (hueco de 4 s sin red ni tareas largas, no repetido). Las esperas de 20–50 s eran del panel de navegador interno oculto (`requestAnimationFrame` no se ejecuta). Descartado: el tour de bienvenida (comparación local con y sin tour, también con el paso 2 guardado) | — | `dev/perf_probe.py`, medidas en Chrome |
| 26/10 | Comprobación de boss20 solo lectura (estado de las tarifas, servicios, ajustes, asientos); hoja de pruebas para Ángel; copia local aislada para contabilizar y pagar (`dev/test.sh uat`, sin tareas, correo ni servicios en línea); revisión de tarifas para Cristina; especificación de la venta de ALM (P43) con los valores del 25/09 leídos en Odoo 19 | `docs/pruebas-angel.md`, `docs/revision-tarifas.md`, `docs/especificacion-alm-venta.md` | `dev/readiness_probe.py`, `dev/tariff_review_probe.py`, ensayo `dev/uat_dryrun.py` en la copia local (deshecho al terminar): dos defectos, D-1 y D-2 |

## Decisiones tomadas en esta fase (técnicas)
- Expediente propio (no `project`), una cuenta analítica por expediente, necesidades de compra explícitas (ADR-005).
- Pedido de compra: borrador por proveedor y moneda; confirmación y envío por una persona.
- Control de facturas de proveedor de servicios BOSS «según cantidades recibidas» (servicio prestado), reversible en
  el producto: propuesta aprobada por Belal el 23/10/2026 y aplicada a todos los servicios BOSS; pendiente de
  ratificación por Ángel (P32).

## Plan de lanzamiento (26/10/2026)

Hitos aprobados por Belal el 26/10/2026: entrega completa el **20/11/2026**, operación en pruebas hasta el **1/12/2026**, corrección y preparación del cambio del 2 al 31/12, Odoo 20 único sistema el **1/1/2027** (sustituyen al 30/11). El plan semanal (sprints S43 19–25 oct → cambio definitivo 1–8 ene; 99 tareas con estado, evidencia, responsable y dependencias) está en https://task.bosscontinental.com (`dev/boss_tasks/seed_launch.py`, siembra idempotente). Mapeo de Hoja1 de «Plan detallado previsiones»: `docs/mapeo-hoja1.md` (28 requisitos: 0 completos, 23 parciales, 5 no implementados).

### Capacidad frente a trabajo planificado (26/10/2026)

Horas estimadas de Belal por semana (sin contar lo ya hecho) frente a 7 h útiles por día laborable; las tareas de
Cristina y Ángel son esperas de decisión o datos, no horas de desarrollo:

| Semana | Capacidad | Planificado | Diferencia | Acción |
|---|---|---|---|---|
| S44 26 oct–1 nov | 35 h | 33 h | — | F01 adelantada a esta semana |
| S45 2–8 nov (4 días) | 28 h | 87 h | **−59 h** | Falta capacidad: decidir (Belal) entre segundo desarrollador, mover B02/B04/P02 a la estabilización con su aprobación, o aceptar entrega parcial |
| S46 9–15 nov (4 días) | 28 h | 71 h | **−43 h** | Ídem; N06 solo si Ángel decide que aplica |
| S47 16–20 nov | 35 h | 40 h | −5 h | Ajustable |
| S48–S53 (pruebas, estabilización, cambio) | 28–35 h | 3–32 h | — | Holgura para incidencias |

Lo que amenaza el 20/11, con el responsable y la acción: capacidad de S45–S46 (Belal: decidir antes del 30/10);
documentos de tarifa (D01, Cristina/operaciones antes del 4/11); decisiones de Cristina C02 (antes del 4/11) y de
Ángel A02–A04 (antes del 6/11); alcance de la migración (N01, Belal, 30/10). Cada retraso de una semana en D01 o C02
desplaza D02, B01, B03 y la verificación de Hoja1 una semana.

Defectos: D-1 corregido en código con prueba el 26/10 (despliegue W09 pendiente); D-2 mapa de cuentas propuesto a
Ángel (`docs/cuentas-suplidos.md`), cambio en boss20 bloqueado hasta su aprobación (W10).

## Plan de las decisiones aprobadas el 23/10/2026

Decisiones y estado por pregunta: `docs/preguntas-abiertas.md` («Aprobadas el 23/10/2026», publicada en la guía,
«Decisiones pendientes»). Son propuestas **aprobadas por Belal**; ninguna está ratificada todavía por Ángel (finanzas,
IVA, cuentas) ni por Cristina (servicios, precios, operaciones): la columna «Ratificación» de ese fichero dice de quién
depende cada una. Fases:

| Fase | Qué | Dónde (estructura del proyecto) | Estado |
|---|---|---|---|
| A | IVA P17 (Art.22; Canarias, Ceuta y Melilla «0% S NS», zona CAN), tipo de cambio P03, pago de facturas de proveedor P30, control por cantidades prestadas P32, suplidos en 419000 P18 (no funciona, defecto D-2), lecturas WFS P40/P41/P29/P42 | `boss_pricing_sale` (`vat_rules`), `boss_expediente` (ajuste de compañía, control de compra), configuración en boss20 (`dev/setup_vat_mapping.py`, `dev/setup_decisions_2310.py`) | Hecho (pendiente de ratificación de Ángel y Cristina, cada uno en su ámbito) |
| B1 | Venta única de ALM por tiempo (P43) con los valores del 25/09 | `boss_pricing`: una tarifa de **venta** con el mismo motor por tiempo (franquicia, tramos por número de día, mínimo) y una regla de lista de precios que la usa; ADR-006 | Valores del 25/09 encontrados en Odoo 19 (nunca anotados como confirmados); especificación con 14 puntos por decidir (`docs/especificacion-alm-venta.md`); espera a Cristina (D1–D7) |
| B2 | QBR (P03): factura en EUR de una oferta en USD con el tipo de la naviera y la línea de quebranto | `boss_expediente` (asistente «Facturar servicios»: moneda de la factura) y servicio QBR | Falta el porcentaje de QBR aprobado (Odoo 19 usaba 1 %, sin confirmar) |
| B3 | ETX (compra por AWB máster, venta por expediente) y DET (código propio) (P10, P09) | `boss_services` (servicios, unidades) | Con el documento del proveedor |
| B4 | Almacenaje especial y almacén fuera del aeropuerto (P44) | `boss_pricing` (condición de tipo de carga) y `boss_services` (código nuevo) | Tras las tarifas y la aprobación del código |
| B5 | Acuerdo de precio para varios envíos (P34) | `boss_expediente` sobre el reparto entre expedientes | Tras los datos de Cristina |
| C | Aprobación de tarifas (P19), IRENEO 2026 (P28), precios por cliente y margen mínimo (P01/P02), lista Lejano Oriente (P24), servicios por definir (P16), CAU/SEG (P13), cuentas por categoría (P37) | Pantallas existentes (tarifas, listas de precios, servicios, ajustes contables) | Pendiente de Cristina / Ángel |

## Decisiones y requisitos citados

### Factura de proveedor y facturación al cliente (P30)

Texto de Cristina en «Nuevo Odoo.xlsx» (autora y última edición Cristina de Santisteban, 02/10/2026; la hoja no tiene
columnas de prioridad, estado, responsable ni fecha: es un **requisito escrito**, no una decisión confirmada):

- «Facturacion»!A3: «No permite pagar a proveedores o contabilizar facturas si eso no está facturado o como mínimo la
  línea puesta en caso de que sea un flete que se pague por adelantado a un agente».
- «Facturacion y costes»!A11: «no se puede soportar una factura ni pagar si no está facturado dicho concepto al cliente
  (evitar que se paguen facturas sin haber facturado)».
- Relacionado: «OPS- exptes»!A69 (cerrar contra previsiones y soportar después las facturas que cuadren sin reabrir),
  «Incidencias»!B9 (único texto sobre un coste que asume BOSS).

Práctica anterior: Odoo 17 casaba la factura de proveedor con las previsiones antes de contabilizarla (FactReader) y
pagaba por remesas; no hay constancia de un bloqueo por falta de factura al cliente. Odoo 19 lo dejó en el plan
(S5b) sin construir.

Qué se distingue en Odoo 20:

| Aspecto | Comportamiento |
|---|---|
| Orden de trabajo (facturar al cliente antes de soportar la del proveedor) | Aviso en la factura de proveedor («Antes de contabilizar o pagar») y en «Pendiente» del expediente |
| Bloqueo de contabilización y de pago | Solo si la compañía elige «Bloquear» (Ajustes › Ventas); por defecto «Solo avisar» mientras P30 siga abierta |
| «Facturado» | Factura de cliente **contabilizada** de esa línea (un borrador no cuenta); una factura parcial basta (concepto facturado) |
| Coste que asume BOSS o cubierto por el precio | Sin aviso: no se espera factura al cliente |
| Flete pagado por adelantado a un agente | Marcar «Pagado por adelantado» en el servicio: basta con la línea de venta (excepción de A3) |
| Factura de proveedor que llega antes o mucho después | Se registra siempre; con «Bloquear» queda en borrador hasta facturar al cliente. La obligación de registrar las facturas recibidas en plazo es una cuestión contable para Ángel antes de activar el bloqueo |

### Datos del cliente para contabilizar (P31)

- Ángel, reglas de IVA (31/08, `iva_rules.md`): «Falta una zona ⇒ PENDIENTE ← nunca se adivina».
- Odoo 17 (asistente de facturas, lectura de auditoría): bloquea «Any billable entity with country = Spain … or no
  country and no VAT/NIF»; no bloquea clientes extranjeros sin NIF.
- No hay decisión de Ángel sobre NIF de clientes UE (lo cubre el IVA pendiente), particulares, Ceuta/Melilla ni
  dirección.
- Odoo 20: bloquea el IVA pendiente y el cliente de España (o sin país) sin NIF ni otra identificación de la
  localización española (pasaporte, NIE, certificado de residencia, otro); la dirección se muestra como dato que falta.

### Una oferta, varios expedientes

- Propietario, 26/08/2026 (actas de Odoo 19, sin nombre): «one accepted quotation MAY create multiple Expedientes …
  Each creation allocates part (or all) of the accepted quantities/amounts; retries and concurrent users can never
  duplicate an allocation or exceed the accepted totals».
- Odoo 20: cada línea aceptada se reparte entre expedientes («Mover servicios a otro expediente»); la suma nunca supera
  la cantidad aceptada, cada expediente factura su parte y la analítica se reparte en proporción.

## Bloqueos y decisiones de negocio abiertas
Ver `docs/preguntas-abiertas.md`: las propuestas aprobadas por Belal el 23/10/2026 con su ratificación pendiente, y
«Cuestiones contables y fiscales sin decidir». No bloquean el desarrollo: mientras siguen abiertas, el sistema hace lo
que dice cada fila, sin suponer la respuesta.

Comportamiento actual en boss20 (propuestas aprobadas por Belal el 23/10/2026, **no ratificadas** todavía):
- Factura de proveedor de un servicio del expediente antes de facturarlo al cliente (P30; requisito de Cristina en
  «Nuevo Odoo», hoja Facturación A3): **se puede contabilizar**; lo que se bloquea es su **pago**, hasta que la factura
  de cliente de ese servicio esté contabilizada. Excepciones: coste «cubierto», «lo asume BOSS» o flete pagado por
  adelantado. Ajuste de la compañía «Factura de proveedor antes de la factura de cliente» = «Bloquear el pago
  (contabilizar permitido)»; las otras opciones son «Solo avisar» y «Bloquear contabilización y pago». Ratifican Ángel
  y Cristina.
- Datos del cliente para contabilizar (P31): un cliente de España (o sin país) sin NIF ni otra identificación de la
  localización no se puede facturar (contabilizar); la dirección que falta solo se avisa. Ratifica Ángel.
- Control de facturas de proveedor (P32): cantidades recibidas (servicio prestado) en todos los servicios BOSS.
  Ratifica Ángel.
- Suplidos (P18): configurados el 23/10 en la cuenta 419000, que en Odoo es **a pagar**: no funciona (defecto D-2).
  Odoo 17 usa subcuentas 419001–419007 de pasivo corriente. Decide Ángel.
- Numeración de expedientes E26xxxx, como en Odoo 19 (P36). Ratifica Cristina.

Cuestiones contables y fiscales **sin decidir** (sin respuesta supuesta; detalle en `docs/preguntas-abiertas.md`): IVA
de los NS que no son suplidos para un cliente español (CAU, QBR), cuentas por categoría (P37), QBR (P03), margen mínimo
(P01/P02), caución y seguro (P13), coste interno de los servicios propios (P38), SII o VeriFactu (P45).

Defectos conocidos (encontrados el 26/10 en el ensayo de la copia local, **sin corregir**):
- **D-1** Una factura de proveedor creada desde el pedido lleva todas sus líneas, también las de cantidad 0 (servicios
  aún no prestados: Odoo 20 las incluye siempre). El bloqueo de pago (P30) las cuenta y el pago sigue bloqueado aunque
  lo facturado ya esté facturado al cliente. Corrección propuesta: no contar las líneas de cantidad 0
  (`boss_expediente/models/account_move.py`, `_boss_bill_needs`) con su prueba. Mientras tanto, borrar esas líneas
  antes de contabilizar.
- **D-2** Configuración del 23/10 (P18, `dev/setup_decisions_2310.py`): ARA, IVA, PLA y DUM tienen la cuenta 419000, que
  en el plan de Odoo (y en Odoo 17) es **a pagar**. Odoo rechaza la factura del agente («debe tener una fecha de
  vencimiento») y la factura al cliente («es de tipo por pagar, pero se está utilizando en una operación de venta»),
  también en boss20. Odoo 17 usa subcuentas propias de pasivo corriente (419001–419007, repercutido y soportado por
  concepto). Corrección: decisión de Ángel sobre las cuentas; mientras tanto, volver a las cuentas de la categoría
  (estado anterior al 23/10). Es un cambio contable en boss20: necesita el visto bueno de Belal.

Pendiente técnico (fase B): QBR, venta única de ALM (P43; especificación en `docs/especificacion-alm-venta.md`), ETX y
DET, almacenaje especial, acuerdo de precio para varios envíos. El coste previsto ya se recalcula con los datos del
expediente (ver registro).

## Despliegue y comprobaciones

| Qué | Referencia | Fecha | Evidencia |
|---|---|---|---|
| Último despliegue en boss20 | `8ec4a2c`: boss_pricing_sale y boss_expediente (boss_expediente 20.0.1.3.0; instalados también boss_pricing 20.0.1.5.0, boss_pricing_sale 20.0.1.7.0, boss_services 20.0.1.2.0) | 23/10/2026 | `dev/deploy.sh` |
| Configuración de las decisiones del 23/10 | `dev/setup_vat_mapping.py`, `dev/setup_decisions_2310.py` | 23/10/2026 | salida de los scripts en boss20 |
| Guía publicada | `0192e66` (`?v=20261023g`) | 23/10/2026 | doc.bosscontinental.com/new |
| Pruebas automáticas (BD desechable, nunca boss20) | `8ec4a2c`: motor 21/21; Odoo 27 métodos (boss_expediente 13, boss_pricing_sale 13, boss_pricing 1): 0 fallos | 23/10/2026 | `dev/test.sh run`, `python -m unittest` |
| Comprobación de boss20 **solo lectura** (no es una prueba) | Versiones instaladas iguales a `8ec4a2c`; 77 servicios BOSS activos con control «cantidades recibidas»; compañía con «tipo del día de la oferta» y «Bloquear el pago»; tabla de IVA con 6 filas (Art.22 y CAN incluidas); 0 asientos contabilizados; 10 tarifas de documentos reales esperando aprobación, ninguna aprobada; sin módulos SII ni VeriFactu; sin servidor de correo saliente | 26/10/2026 | `dev/readiness_probe.py` (sin escritura, rollback) |
| Ensayo de la hoja de pruebas en la copia local aislada (una transacción deshecha al terminar) | C1–C6 y C8 dan el resultado de `docs/pruebas-angel.md`; C7 falla por D-2; el pago de C5 falla con líneas de cantidad 0 (D-1) | 26/10/2026 | `dev/uat_dryrun.py` |

| Despliegue en boss20 (tarde) | `6d12dd3` → `966ebb0`: boss_expediente **20.0.1.5.0** (fechas con hora y periodo real, aerolíneas ↔ handlers, previsión de costes, D-3, D-4); logs `deploy_20261026_162943.log` y `deploy_20261026_164957.log`, exit 0 | 26/10/2026 | `dev/deploy.sh update boss_expediente` |
| Pruebas de Odoo en BD desechable del servidor | boss_expediente 18/18 en verde para `9a87b94`, la corrección del formulario + D-3, y `966ebb0` (BD boss20_test_162239, _164023, _164514) | 26/10/2026 | `dev/server_test.sh boss_expediente` |
| Entorno UAT persistente | `boss20_uat` creado en el servidor (dbfilter `^boss20(_uat)?$`), aislado (crons 0, sin correo, IAP a puerto cerrado), módulos 20.0.1.5.0; ciclo C1–C8 ejecutado y guardado; escenarios S1–S6; usuarios por rol | 26/10/2026 | `dev/server_uat.sh build`, `dev/uat_cycle.py`, `dev/uat_scenarios.py`, `dev/uat_users.py`; `docs/escenario-uat.md` |
| Configuración en boss20 | Cuentas de suplidos 419001–419007 (D-2, Ángel ratifica); tarifa «IRENEO distribución nacional zona 3 2026 (+10 % transporte, carta 14/07/2026)» esperando aprobación con la carta adjunta | 26/10/2026 | `dev/setup_suplidos_accounts.py` (con `dev/apply-on-boss20.txt`), `dev/setup_ireneo_2026.py` |
| Despliegue en boss20 (27/10) | `1958bb0` boss_expediente 20.0.1.8.0 (D-7, D-8); boss_pricing_sale 20.0.1.8.0 → 20.0.1.8.2 (D-9); logs `deploy_20261027_090237.log`, `_090615`, `_090754` y el último, exit 0 | 27/10/2026 | `dev/deploy.sh update` |
| Ciclo contable en Chrome en boss20 | S00031/E260015 de punta a punta; margen final 240 € | 27/10/2026 | `docs/escenario-uat.md` |
| Comprobación desde Chrome en boss20 | Menú «Aerolíneas y handlers» (47 relaciones por aeropuerto); «Previsión de costes» (pivote por proveedor y estado); E260011: Cathay → WFS, Qatar → Iberia (handling); S00025 con 4 TEU y THC por tamaño | 26/10/2026 | capturas de la sesión del 26/10 |

Remoto: https://github.com/dev1bms/BossOdoo20 (privado), `main` al día (último commit del 26/10 por la tarde).

## Punto de reanudación (27/10/2026)

**Política desde el 27/10 (Belal):** todo el trabajo, las pruebas y las comprobaciones se hacen en **boss20** en el
servidor; nada en el equipo local, ninguna base desechable ni copia (`dev/server_test.sh`, `boss20_test_*` y
`boss20_uat` ya no se usan; dbfilter `^boss20$`). En boss20 se permite crear, modificar y borrar registros de prueba,
confirmar ventas y compras, ejecutar servicios, contabilizar facturas de cliente y proveedor, abonos, registrar pagos y
casar, aunque se consuman números y queden asientos de prueba; anular o borrar solo por las vías de Odoo. Actualizar
módulos y ajustes, desplegar y reiniciar sin pedir permiso de nuevo. Comunicaciones externas desactivadas
(`dev/boss20_isolate.py`). Odoo 17 y 19 solo lectura. Nada de esto convierte una propuesta o una tarifa en decisión
aprobada por Cristina o Ángel.

Desplegado en boss20 (27/10, tarde): boss_services 20.0.1.3.0, boss_pricing **20.0.1.7.0**, boss_pricing_sale
**20.0.1.9.2**, boss_expediente 20.0.1.8.0. Ciclo contable recorrido en Chrome (S00031/E260015, `docs/escenario-uat.md`).

**Precios y plantillas con datos reales (27/10, mandato de Belal):** copia de seguridad de boss20 y de su filestore en
`~/backups/boss20-20261027_0944*` antes de limpiar; 8 tarifas DEMO borradas y 9 archivadas, lista de precios [DEMO]
archivada (`dev/cleanup_demo_pricing.py`); proveedores con sus datos legales de Odoo 17 (`dev/setup_real_suppliers.py`);
clientes COFITEL y AGUILERA EXTINCION (`dev/setup_real_customers.py`); 24 tarifas aprobadas por delegación de Belal
para pruebas tras comparar cada línea con su documento (`dev/approve_verified_tariffs.py`; informes privados
`.research/verify_sea.md`, `verify_air.md`; 30/30 cálculos manuales iguales al motor,
`.research/evidencia_tarifas_20261027_1058.txt`); plantillas por caso sin [DEMO] (`dev/setup_templates.py`); lista de
precios de COFITEL creada en Chrome; precisión de precio 4 decimales; tipos del BCE cargados. Ofertas probadas en
Chrome: **S00032** (COFITEL, aérea, aceptada → E260016) y **S00033** (AGUILERA, FCL 20'+40', aceptada → E260017; FuelEU «Sin cargo»
como en la factura real F26 10-0072, a decidir por ventas). E260017 completo hasta facturas: pedidos P00007 (PORTEVER), P00008 (MSC), P00009 (ADUCEX)
confirmados; servicios prestados salvo el arrastre (sin coste); factura al cliente INV/2026/00004 y de proveedor
FACTURA/2026/10/0003–0005 contabilizadas, sin pagos; D-13 corregido (boss_expediente 20.0.1.8.1). Defectos D-10, D-11 corregidos; D-12 documentado como limitación; excepciones en
`docs/preguntas-abiertas.md`. Inicio rápido publicado: doc.bosscontinental.com/new/#/inicio-rapido (`?v=20261027b`).

**Un documento de proveedor = una tarifa (27/10, aprobado por Belal; enmienda de ADR-002):** cada precio puede restringir el alcance de su tarifa (sentido, modo, forma de carga, puertos, países, provincias), nunca ampliarlo; «Antes de enviar a aprobación» avisa de dos precios del mismo servicio que se solapan. boss_pricing **20.0.1.8.2**, boss_pricing_sale **20.0.1.9.3**; `dev/check_line_scope.py` 9/9 (`docs/evidencias/20261027_1241_check_line_scope_boss20_590c98e6226a.txt`). IRENEO consolidado en **«IRENEO Tarifas MAD 2026»** (`dev/setup_ireneo_2026_document.py`): versión 1 desde 01/01/2026 (recogidas, paquete de exportación y X-R, zona 3, almacén G-5 «A consultar», y el almacenaje de exportación p.4 dado de alta en Chrome) y versión 2 desde 15/07/2026 (zona 3 +10 %, carta de 14/07/2026), aprobadas por delegación de Belal para pruebas; las 5 tarifas por sección de 2026 archivadas. Comprobación privada 34/34 (`.research/evidencia_tarifas_20261027_1252.txt`). Guía «Introducir una tarifa» e Inicio rápido actualizados (`?v=20261027d`).

**WFS de nuevo (27/10, decisión de Belal):** T6 y T7 borradas definitivamente desde el servidor (la interfaz no borra
tarifas aprobadas); 10 líneas de oferta (S00010, S00014, S00027, S00032) y 3 costes de E260016 perdieron el enlace al
precio. Valores guardados antes en `.research/wfs_T6_T7_before_delete.txt`. Nueva **«WFS Tarifas MAD/BCN desde
01/06/2026»** dada de alta en Chrome (7 precios con «Se aplica a» importación/exportación, 0 diferencias con las
anteriores), **esperando aprobación** (Belal o Ángel). Hasta entonces los precios de WFS salen «pendiente de
aprobación» (4 casos de la comprobación privada fallan por eso).

**Reunión con Ángel (27/10) → ADR-006** (`docs/reunion-angel-2026-10-27.md`): el envío como **origen → destino**
(país, puerto/aeropuerto, dirección, lugar), **ETD y ETA**, «Ordenante» y **negocio de BOSS o del agente** con código de
tráfico (IMB, IMA…), **la plantilla es el caso** (rellena sentido, modo, carga, incoterm, negocio, lo que gestiona
BOSS), **peso tasable aéreo** = mayor del bruto y volumen × 167, almacenaje estimado 0, contenedores solo donde aplican,
semana desde el lunes. Puerto español, país extranjero, provincia y fecha de tarifa se **derivan** (precios e IVA sin
cambios: 38 ofertas y expedientes con los mismos datos de precio antes y después). boss_pricing_sale **20.0.1.10.0**,
boss_expediente **20.0.1.9.0**; 9.496 puertos y aeropuertos (de Odoo 17 vía Odoo 19); `dev/check_route_cases.py` 36/36
(`docs/evidencias/20261027_1420_check_route_cases_boss20_70dc926985e1.txt`). Abiertas R-A1…R-A5 y R-S1 en
`docs/preguntas-abiertas.md`.

Cobertura técnica de Hoja1 (`docs/mapeo-hoja1.md`: 25 hechas, 3 parciales por documentos que no existen) **no es** el
avance del proyecto: para usarlo en producción faltan las aprobaciones de negocio (24 tarifas activas para pruebas
por delegación de Belal, ninguna aprobada todavía por Cristina; cuentas de suplidos y P30/P32 por ratificar por Ángel), los documentos que faltan y la decisión de
Cristina sobre la venta y el margen «en la aceptación» tras una recotización.

Pendiente de personas: aprobación de tarifas (Cristina); ratificación de suplidos, P30 y P32 (Ángel). Pendiente de
documentos: 2.º handler, D&D general de ONE/Maersk/OOCL y cualquier tarifa de ZIM, agente de exportación, Hapag gastos
locales, CFS, PFT, ROH/SOI/INS/SAN, CES, transporte de contenedor y FS.
