# Plan de desarrollo: el expediente completo de principio a fin (BOSS, Odoo 20)

Fecha: 28/10/2026. Pedido por Belal («خطة تطوير كاملة متكاملة للوصول إلى الملف الكامل من البداية للنهاية»).
Estado: **propuesta para decidir**. Nada de este documento es una regla de negocio aprobada: cada regla pendiente
lleva su responsable (Cristina: operaciones, servicios, precios; Ángel: finanzas, IVA; Belal: proyecto).

## Cómo se ha hecho
- Investigación de solo lectura en seis áreas (operaciones, compras, contabilidad, documentos y gastos, proceso real de
  Odoo 17, datos/decisiones/pruebas): código del repositorio, consultas SELECT en boss20, Odoo 17 de producción en solo
  lectura y el proyecto Odoo 19 como conocimiento. **112 huecos** encontrados, cada uno con su evidencia.
- Dos planes independientes (orden del flujo de negocio / orden por riesgo y dependencias), fusionados en uno; una
  revisión de completitud asigna **los 112 huecos** a una fase o los declara fuera de alcance. Ninguno se ha dejado sin tratar.
- Comprobado a mano después (28/10): fecha de arranque 1/1/2027 y déficit de capacidad S45/S46 (`docs/ciclo-operativo.md:66-83`);
  `dev/uat_e2e.py:17` exige `boss20_uat` (no funciona en boss20); contradicción entre CLAUDE.md (se permite contabilizar
  pruebas en boss20) y la tarea T05 (`dev/boss_tasks/seed_launch.py:963`, «nunca en los libros reales de boss20 antes del
  1/1»); `boss_bill_before_invoice = block_payment` en boss20; el impuesto 41 «0% EX S» **no** tiene texto legal (el del
  artículo 22 es del impuesto 72). Las cifras de Odoo 17 (≈21.600 contactos activos, ≈1.300 expedientes E26, 49.697
  documentos) vienen de la investigación y no se han vuelto a contar.
- Investigación completa (con datos de Odoo 17): `.research/e2e_plan_research.json` (fuera de Git).

## Punto de partida (boss20, 28/10/2026)
- El tronco comercial y financiero funciona y está probado: oferta → expediente → necesidades de compra → pedidos →
  facturas de proveedor → facturación de servicios → cuenta analítica por expediente → resumen por grupo → cierre financiero con condiciones.
- Pero **ningún expediente ha recorrido nunca el ciclo entero**: los 18 están en «open», 0 cierres financieros, 0 de
  exportación, LCL o terrestre; los cambios de estado no tienen condiciones; no hay hitos, documentos por expediente,
  gastos, banco, cobros conciliados ni SII/VERI*FACTU; y no hay prueba automática de punta a punta que funcione en boss20.

## Qué significa «expediente completo»
«Expediente completo de principio a fin» en BOSS (Odoo 20, base boss20, repositorio C:/Users/BelalAlswerki/Documents/BossOdoo20) significa que un único boss.expediente recorre las etapas siguientes sin ningún paso fuera de Odoo, dejando datos coherentes y verificables, y que una comprobación con evidencia en boss20 lo demuestra para cada tráfico. El orden es: primero importación marítima FCL con DUA (IMB) y exportación aérea (EAB); después importación aérea (IAB), exportación FCL (EMB), LCL, terrestre y, cuando se decida, agente y consolidación. Punto de partida (SQL 28/10/2026): los 18 expedientes de boss20 están en 'open', 0 tienen cierre financiero, 0 son de exportación, LCL o terrestre, y dev/uat_e2e.py no funciona en boss20.

Etapas:
(0) Partes reales. Ordenante, expedidor, destinatario, agente, transportista, agente de aduanas y transportista terrestre existen como contactos migrados, con rol, país, NIF y familia de transportista. Los proveedores tienen cuenta bancaria y condiciones de pago, y los usuarios tienen su rol.
(1) Oferta. Usa tarifas aprobadas por Cristina y sus precios de venta; el coste manual es una excepción explícita. Ninguna línea queda con IVA 'pending' y la foto de la aceptación queda congelada.
(2) Apertura. Al aceptar se abre un solo expediente (sale_order.py:94-107) con cuenta analítica, operativo asignado, plan de hitos de su tráfico, número según P36 y aviso de crédito según lo que decida Ángel.
(3) Reserva y salida. Pedidos de compra confirmados con la referencia o el acuse del proveedor; booking, MBL/HBL o MAWB/HAWB, buque o vuelo y contenedores con precinto; eventos tipificados ligados a ETD/ATD; paso a «En tránsito» con las condiciones decididas.
(4) Documentos. Todo documento recibido o emitido está en la carpeta del expediente, con su tipo y visible según el rol. Los que faltan se han pedido desde Odoo. Al portal llega solo lo publicado (ADR-010).
(5) Destino. ETA/ATA y llegada coherentes; DUA, canal, levante y estado aduanero registrados. Los suplidos ARA/IVA/PLA/DUM se casan con la factura del agente de aduanas sin pedido de compra y se cuentan una sola vez.
(6) Entrega y contenedores. La orden de transporte sale de Odoo. Están registradas la fecha de entrega y las fechas de los contenedores, con DEM/OCU/DET/ALM recalculados y aviso antes de que termine el tiempo libre. El paso a «Entregado» tiene condiciones.
(7) Proveedores. Cada necesidad queda facturada o cerrada, y cada factura de proveedor lleva el expediente en sus líneas. Las desviaciones se revisan separando precio y tipo de cambio, y los abonos de proveedor están aplicados.
(8) Cliente. Toda la venta acordada está facturada (servicios y suplidos según decida Ángel) con IVA y notas legales correctas, IBAN, serie válida, moneda/QBR según P03 y registro VERI*FACTU o SII según P45, sin envío durante las pruebas.
(9) Cobros y pagos. Se registran en Odoo y se concilian con líneas de extracto; las remesas SEPA solo generan el XML. P30 se respeta por cualquier camino (botón, asistente y conciliación bancaria o manual).
(10) Cierre operativo. Tiene condiciones y congela los datos del envío.
(11) Cierre financiero y de mes. Requiere la lista «Pendiente» vacía y el grupo comprobado en el servidor; después no se puede contabilizar nada sobre el expediente. El margen definitivo queda guardado y aparece en el informe de varios expedientes, y el mes queda protegido por fechas de bloqueo.

Reglas transversales: toda regla no decidida queda como estado explícito 'pending decision' con su responsable (Cristina para operaciones, servicios y precios; Ángel para finanzas e IVA). La práctica de Odoo 17 se presenta como pregunta y nunca como regla. Durante el desarrollo y las pruebas no se envía correo a clientes ni a proveedores, no se presenta nada a la AEAT y no hay transferencias reales.

Criterio de «hecho» por tráfico:
(a) dev/uat_run.sh dev/check_file_e2e.py boss20 termina con «RESULT n passed, 0 failed» y deja la evidencia con el commit desplegado en docs/evidencias/.
(b) Hay un recorrido en Chrome en https://system.bosscontinental.com con registros [PRUEBA] hasta el cierre financiero; los registros persisten y se contabilizan solo si F0 lo permite.
(c) En la operación en pruebas, el responsable que designe Cristina (y Ángel en lo contable) lo repite con datos reales migrados.

Escala de tamaño (estimación de un desarrollador con 28-35 h útiles por semana, sin contar las esperas de decisión): S ≤ 8 h; M 8-30 h; L 30-70 h; XL > 70 h.

## Las fases
Tamaño (un desarrollador, 28-35 h útiles por semana, sin contar esperas de decisión): S ≤ 8 h · M 8-30 h · L 30-70 h · XL > 70 h.

| Fase | Objetivo | Tamaño | Depende de |
|---|---|---|---|
| F0 · Decisiones agrupadas, estrategia de la base de producción y prioridades | Antes de escribir código, convertir cada regla que bloquea el expediente completo en una decisión con responsable, fecha límite y comportamiento provisional. Decidir también si boss20 será la base de producción, porque cada… | S | — |
| F1 · Arnés E2E en boss20 y correcciones que no necesitan decisión | Tener una comprobación repetible sobre el código desplegado que lleve un expediente desde la oferta hasta el cierre y diga exactamente dónde se rompe. Hoy uat_e2e.py exige boss20_uat (línea 17), usa la tarifa [DEMO] 21… | M | F0 (solo para el modo 'post') |
| F2 · Contactos, roles, familias de transportista y usuarios (migración de maestros) | Que el operativo encuentre en boss20 a sus clientes, agentes, navieras, transportistas terrestres y agentes de aduanas reales, con su rol, familia de transportista y datos de pago, y que Cristina y operaciones tengan usuario.… | L | F0 |
| F3 · Oferta con datos reales: tarifas aprobadas, precios de venta, plantillas y servicios pendientes | Que la oferta de un expediente real salga de tarifas aprobadas por Cristina y de sus precios de venta, en lugar de coste + 20 % o importes tecleados. Hoy solo 13 de los 52 servicios de tarifa tienen precio aprobado, 21 de las… | L | F0, F2 (usuario de Cristina y clientes reales) |
| F4 · Base legal y contable de la factura (adelantada: bloquea la primera factura real) | Que la primera factura real de un expediente sea legalmente correcta, vaya a las cuentas correctas y lleve banco y serie válidos. Para ello se prepara ya SII o VERI*FACTU en modo de pruebas. | M | F0 |
| F5 · Apertura, reserva y salida: ciclo de vida operativo | Que desde la oferta aceptada hasta la salida del buque o el vuelo el expediente diga qué falta y quién lo hace: operativo asignado, hitos por tráfico como actividades estándar, eventos tipificados ligados a las fechas,… | L | F1, F0 (decisiones de Cristina y de Ángel) |
| F6 · Documentos del expediente, visibilidad por rol y portal | Que cada documento del envío esté en el expediente por tipo y con visibilidad por rol, que los documentos que faltan se pidan desde Odoo y que el portal siga publicando solo lo elegido. Hoy hay 0 documentos de la app… | M | F1, F5 |
| F7 · Destino: llegada, aduana, entrega y contenedores | Que el tramo de destino quede registrado y controlado: llegada, despacho (DUA, canal y levante), suplidos del agente de aduanas, orden de transporte al transportista terrestre, entrega, devolución del vacío con aviso antes de… | L | F5, F6 |
| F8 · Lado proveedor: facturas recibidas, coste real y pagos a proveedores | Que el coste real del expediente sea cierto y explicable: casado de facturas (diferencias de precio y cantidad, parciales, abonos, USD), control de facturas sin expediente o que no cuadran, P30 sin agujeros y pagos a… | L | F1, F4 |
| F9 · Factura al cliente, suplidos, moneda y cobro | Que toda la venta del expediente se facture como decida Ángel: servicios y suplidos (separados o no, cada uno con su vencimiento), moneda y QBR, menciones legales, IBAN y serie válida. Y que el cobro se concilie y se vea por… | L | F4, F7, F8 |
| F10 · Cierres, cierre de mes, supervisión y rentabilidad entre expedientes | Que el final del expediente sea fiable y nada se quede atascado: - cierre operativo con condiciones y congelación; - cierre financiero que nadie salta y que nada modifica después; - cierre de mes (bloqueos, periodificaciones,… | L | F5, F7, F8, F9 |
| F11 · Aéreo: exportación (EAB) e importación (IAB) | Repetir el expediente completo en aéreo. La exportación aérea no se ha ejecutado nunca en boss20 y es parte de la aceptación final. En importación: NOA/ATA, handler y ALM con periodo real. En exportación: FOH y salida. | L | F3, F5, F7, F10 |
| F12 · Marítimo exportación FCL/LCL, LCL de importación, terrestre y otros sentidos | Que los tráficos que nunca se han ejecutado en boss20 (0 exportaciones, 0 LCL, 0 terrestres) recorran el expediente completo, con los datos que necesita la exportación y los documentos que BOSS emite. | L | F3, F5, F7, F10 |
| F13 · Agentes, profit share y facturación a terceros | Poder liquidar los expedientes de agente (IMA, EAA, IAA) y los fletes collect o prepaid como en producción: PFT en la venta, en el margen y en el resumen; varios pagadores por expediente; abonos de agente. | L | F2, F4, F8, F9, F10 |
| F14 · Operación en pruebas con datos reales y aceptación por tráfico | Que las personas de BOSS repitan el expediente completo con envíos reales representativos, clientes migrados y tarifas aprobadas por Cristina, y den la aceptación por tráfico antes del 1/12. | M | F2, F3, F10, F11, F12 (según lo decidido en F0), F13 (según lo decidido en F0) |
| F15 · Cambio de sistema y arranque del 1/1/2027 | Arrancar con los envíos en curso de Odoo 17 migrados, sin números duplicados, con saldos de apertura correctos y con los efectos externos activados de forma controlada. | XL | F2, F4, F10, F14 |
| F16 · Consolidación máster/house (condicional a M2-I; probablemente después del arranque) | Llevar grupajes y consolidaciones aéreas (un MBL o MAWB con varios HBL o HAWB y costes compartidos) con la opción que elija Cristina. | XL | F0 (M2-I), F5, F6, F7, F13 |
| F17 · Gastos de empleados y tarjeta (condicional a P39) | Si Ángel lo aprueba, que los gastos pequeños pagados por un empleado o con tarjeta lleguen al coste real del expediente sin saltarse la regla de refacturación. | S | F0 (P39), F8 |

## Capacidad: el punto que hay que decidir primero
Con los puntos medios de cada tamaño (S 6 h, M 20 h, L 50 h, XL 100 h) el plan completo suma **≈ 792 h**. El núcleo
mínimo para el arranque (F0-F10, F11 sin AWB, F14 y F15) queda entre **≈ 450 y 575 h**. Un solo desarrollador tiene
**≈ 270 h** del 28/10 al 31/12, y S45-S46 ya van en negativo. **El plan no cabe en el 1/1/2027 tal como está.**
Belal debe elegir en F0 una (o una mezcla) de estas salidas:
1. Segundo desarrollador.
2. Arranque por tráficos: importación FCL y aéreo en Odoo 20 el 1/1; agentes, exportación marítima, LCL, terrestre y
   consolidación siguen en Odoo 17 unas semanas.
3. Mover la fecha de arranque.
Sin esa decisión, cada fase siguiente se planifica sobre una fecha que no se puede cumplir.

## Estado de las fases
| Fase | Estado |
|---|---|
| F0 | En curso: paquetes de preguntas para Ángel, Cristina y Belal (28/10) |
| F1 | **Hecha el 28/10/2026**: arnés `dev/check_file_e2e.py` (S1 35/0, 20 huecos con su fase) y correcciones desplegadas; además se encontró y corrigió que el formulario del expediente no abría (`docs/evidencias/20261028_f1_arnes_e2e.md`) |
| F2-F17 | Pendientes |

## Orden recomendado para empezar
1. **F0 esta semana**: paquetes de preguntas para Ángel y Cristina agrupados por etapa del expediente, con fecha límite;
   decisión de Belal sobre capacidad y sobre la base de producción.
2. **F1 en paralelo, sin esperar decisiones**: la prueba de punta a punta en boss20 (`dev/check_file_e2e.py`) y los
   defectos técnicos que no son reglas de negocio. Es la red de seguridad de todo lo demás.
3. **F2 (contactos) y F4 (base legal y contable)** en cuanto Belal fije el alcance N01 y Ángel conteste P45/P18/P37 y el banco.
4. Después el flujo del expediente en el orden en que lo vive el operativo: F5 → F6 → F7 → F8 → F9 → F10, y los tráficos F11-F13.

## Detalle de cada fase
### F0 · Decisiones agrupadas, estrategia de la base de producción y prioridades — S
**Objetivo.** Antes de escribir código, convertir cada regla que bloquea el expediente completo en una decisión con responsable, fecha límite y comportamiento provisional. Decidir también si boss20 será la base de producción, porque cada prueba que contabiliza deja asientos de 2026 y gasta numeración (hoy E260108). Y fijar qué fases son obligatorias para el 1/1, dada la capacidad real.

**Entregables**
- Paquete de decisiones para Ángel, agrupado por etapa del expediente (ver decisions_by_owner). La práctica de Odoo 17 va como material de la pregunta (acciones 1222, 1232, 1435, 1658; automatización 213).
- Paquete para Cristina, agrupado por etapa: estados y condiciones, hitos, aduana, documentos, OT, exportación, M2-I, PFT y varios pagadores. Material de la pregunta: acciones 1048, 1062, 1109, 1490, 1435 y 1436, x_dashboard_stage 1-5, facet 12 y crons 76/90/92/93 de Odoo 17.
- Decisiones de Belal: capacidad de S45/S46 (−59 h / −43 h, docs/ciclo-operativo.md:73-83); fases obligatorias para el 1/1; alcance de N01 (venció el 30/10); U01 (correo); cron del BCE; dónde se ensaya la migración (N04 dice «copia local», y la política del 27/10 lo prohíbe).
- Resolver la contradicción entre CLAUDE.md:40-43, que permite asientos de prueba en boss20, y T05 (dev/boss_tasks/seed_launch.py:963: «nunca en los libros reales de boss20»).
- Cada punto queda en docs/preguntas-abiertas.md con Id, cuestión, responsable, fecha límite y «mientras tanto», más una tarea en dev/boss_tasks/seed_launch.py enlazada a la fase que bloquea.

**Se reutiliza**
- Formato de docs/preguntas-abiertas.md (Id, cuestión, quién, mientras tanto en el sistema)
- Matriz de la reunión (65 puntos) como índice de lo abierto
- Hallazgos de Odoo 17 y Odoo 19 (DECISIONS.md grupo C), solo como material de pregunta

**Ficheros y módulos:** docs/preguntas-abiertas.md; docs/matriz-reunion-2026-10-27.md; docs/revision-reunion-angel-2026-10-28.md; docs/ciclo-operativo.md; dev/boss_tasks/seed_launch.py

**Decisiones que necesita**
- Ángel + Belal: base de producción (boss20 limpiada o base nueva) y si se sigue contabilizando en boss20
- Belal: capacidad, fases obligatorias para el 1/1, alcance N01, U01, cron del BCE, dónde se ensaya la migración
- Todas las demás decisiones de decisions_by_owner se registran aquí con fecha límite

**Aceptación en boss20**
- Cada decisión de decisions_by_owner está en docs/preguntas-abiertas.md con responsable, fecha límite y comportamiento provisional. Ninguna figura como decidida sin el nombre y la fecha de quien decide.
- Antes de cualquier recorrido que contabilice en boss20 hay una decisión registrada (o una fecha límite) sobre la base de producción.
- La lista de fases obligatorias para el 1/1 está aprobada por Belal y reflejada en las tareas de seed_launch.py.
- Referencia de partida: SELECT boss_bill_before_invoice FROM res_company devuelve 'block_payment'.

### F1 · Arnés E2E en boss20 y correcciones que no necesitan decisión — M
**Objetivo.** Tener una comprobación repetible sobre el código desplegado que lleve un expediente desde la oferta hasta el cierre y diga exactamente dónde se rompe. Hoy uat_e2e.py exige boss20_uat (línea 17), usa la tarifa [DEMO] 21 archivada, una plantilla renombrada y usuarios uat_* inexistentes, y las pruebas Odoo no se ejecutan desde el 27/10. También corregir los defectos técnicos que no son reglas de negocio.

**Entregables**
- dev/check_file_e2e.py (nuevo), con los helpers check(), refused() y pay_and_reconcile() de dev/uat_e2e.py:25-76. Hace assert env.cr.dbname == 'boss20', crea sus datos [PRUEBA] en la propia ejecución (cliente ES con NIF, proveedores, tarifa aprobada, plantilla «IMB FOB · …», usuarios por rol) y usa los campos de ruta actuales en lugar de boss_port_id y boss_planned_date. Rollback por defecto; el modo 'post' solo si F0 lo permite.
- Escenarios declarados: S1 IMB FCL con DUA, S2 EAB, S3 IAB, S4 EMB FCL, S5 LCL importación y exportación, S6 terrestre, S7 agente en USD. Cada paso indica la fase que lo cubre y, hasta entonces, sale como «hueco conocido (Fx)».
- Casos ejecutables desde hoy: factura de proveedor con precio distinto del pedido (variance_to_review bloquea el cierre financiero), abono de proveedor, pedido y factura en USD, factura parcial y suplido ARA sin pedido casado por producto y analítica. Serán la primera evidencia del ciclo de compras en boss20 después del 27/10.
- Vista: ATD visible en importación, cross-trade y nacional, y recogida real visible en exportación (views/boss_expediente_views.xml:314-321). ADR-009 decisión 1 ya tarifica el flete por ATD (_boss_pricing_date, boss_expediente.py:396-405).
- amount_collected y amount_paid prorrateados con account_share, como ya hacen invoiced y actual (boss_expediente.py:844-845 frente a 807-808).
- boss_expediente_id en las líneas de factura de proveedor, tomado de purchase_line_id.order_id.boss_expediente_id o de la analítica del expediente (account_move.py:146-156). Hoy hay 0 líneas así en boss20.
- Comprobación de grupo en el servidor en action_close_financial y action_reopen_financial, con los mismos grupos que ya tiene la vista (views:34-37).
- Documentación: corregir ADR-005:41 y docs/ciclo-operativo.md:129 a 'block_payment'. Añadir una nota de corrección sobre «0% EX S imprime el art. 22» (docs/evidencias/20261028_documentos.md:31-32) sin reescribir la evidencia.
- Nota de política: las 34 pruebas Odoo y las 23 del motor quedan como referencia de casos; la regresión real son los check_*.py en boss20.

**Se reutiliza**
- dev/uat_e2e.py, pasos 1-11
- Patrón de dev/check_meeting2.py (assert boss20, rollback, CHECK PASS|FAIL y RESULT)
- Patrón de usuarios [PRUEBA] de dev/check_portal_http.py
- dev/wip_bootstrap.py y dev/server_shell_wip.sh para probar antes de desplegar
- account_share y with_accounts (boss_expediente.py:85-104)
- Casos de addons/boss_expediente/tests (test_cycle, test_file_followup, test_storage_period:108-114)

**Ficheros y módulos:** dev/check_file_e2e.py (nuevo); dev/uat_e2e.py; dev/uat_run.sh; addons/boss_expediente/models/boss_expediente.py; addons/boss_expediente/models/account_move.py; addons/boss_expediente/views/boss_expediente_views.xml; docs/adr/005-operational-and-financial-cycle.md; docs/ciclo-operativo.md

**Decisiones que necesita**
- Ángel + Belal: modo 'post' en boss20 (decisión de F0)
- Belal: confirmar que la regresión son los check_*.py en boss20 y no las pruebas Odoo

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_e2e.py boss20 deja su evidencia en docs/evidencias/ con el commit desplegado. S1 sale en verde hasta la rentabilidad y el resto aparece como huecos conocidos con su fase.
- Tras la ejecución, SELECT count(*) FROM boss_expediente sigue en 18 y account_move y purchase_order no cambian (rollback). Solo avanzan las secuencias.
- En el script: amount_collected de un expediente con una factura repartida al 50 % es el 50 % del cobro.
- En el script: una factura de proveedor contabilizada desde el pedido lleva boss_expediente_id en sus líneas.
- En el script: action_close_financial por RPC con un usuario [PRUEBA] solo de ventas da AccessError o UserError.
- En el script: con un precio facturado mayor que el pedido salta variance_to_review y el cierre financiero se rechaza; con un abono, el neto facturado es correcto.
- Chrome: ATD visible en E260017 (importación) y recogida real visible en una exportación [PRUEBA].
- check_meeting2, check_portal y check_portal_http siguen en verde.

### F2 · Contactos, roles, familias de transportista y usuarios (migración de maestros) — L
**Objetivo.** Que el operativo encuentre en boss20 a sus clientes, agentes, navieras, transportistas terrestres y agentes de aduanas reales, con su rol, familia de transportista y datos de pago, y que Cristina y operaciones tengan usuario. Hoy hay 2 clientes y 8 proveedores reales, 0 contactos con boss_carrier_group_id y 2 usuarios internos. Sin esto no se puede abrir ningún expediente real. Empieza ya, en paralelo con F1.

**Entregables**
- docs/migracion.md y ADR-012 «Migración de datos», con:
- alcance de N01;
- mapeo de res.partner de Odoo 17: x_studio_type (8 valores, ir.model.fields 18028), banderas is_agent/is_carrier/is_customs_agent/is_trucker/is_airline/is_shipperconsignee/is_provider, x_studio_code, KAM, NIF y país, hacia boss.partner.role y customer_rank/supplier_rank;
- exclusión de los contactos tipo lugar (p. ej. 57786, 54130);
- deduplicación por NIF y nombre;
- id de Odoo 17 en ref.
- dev/migrate_partners.py: lee Odoo 17 en solo lectura, carga de forma idempotente con dev/server_shell.sh. Datos personales e IBAN nunca en Git, en URLs ni en conectores externos.
- Familias de transportista con boss_carrier_group_id (M2-3), incluidas las 5 entidades de MSC (23762, 23022, 23493, 23733, 54705).
- Datos de pago: cuentas bancarias de proveedores (res.partner.bank), condiciones de pago que faltan (6, 20, 60, 75 y 90 días; ids 15, 12, 10, 13 y 16 de Odoo 17) y, según decida Ángel, límites de crédito y nivel de reclamación.
- Mapeo de x_concept (ids 181-365) a los 77 servicios mediante boss_o17_concept_id. Lo necesitan F15 (migración de abiertos) y la conciliación por concepto.
- Usuarios por rol (W08): Cristina, operaciones, compras y contabilidad, con idioma es_ES (M2-11/M2-F).

**Se reutiliza**
- base/wizard/base_partner_merge.py para deduplicar
- res.partner.bank y account.payment.term estándar
- dev/setup_real_customers.py y dev/setup_real_suppliers.py como patrón idempotente
- BossOdoo19/docs/BOSS_MIGRATION_MAPPING.md:26-87, solo como conocimiento
- dev/readiness_probe.py (solo lectura) para medir antes y después

**Ficheros y módulos:** dev/migrate_partners.py (nuevo); docs/migracion.md (nuevo); docs/adr/012-data-migration.md (nuevo); addons/boss_expediente/models/res_partner.py; addons/boss_pricing_sale (boss_carrier_group_id); dev/boss_tasks/seed_launch.py (N01-N03, W08)

**Decisiones que necesita**
- Belal: alcance de N01 (tipos y antigüedad de los contactos; los históricos se quedan en Odoo 17)
- Cristina: R-A3 (mapeo de roles y validación del ordenante agente o cliente) y W08 (quién tiene usuario y con qué rol)
- Ángel: condiciones de pago, límites de crédito y niveles de reclamación que se cargan, y si se migran las cuentas bancarias de proveedores

**Aceptación en boss20**
- SQL: recuentos por tipo en boss20 iguales a los acordados en docs/migracion.md, con las exclusiones explicadas.
- Muestra de 20 contactos comparada campo a campo con read_record de Odoo 17.
- SQL: 0 empresas duplicadas por NIF y todos los clientes españoles con NIF (P31).
- SQL: count(boss_carrier_group_id) > 0 y las 5 entidades de MSC en la misma familia.
- SQL: res_partner_bank de proveedores > 0.
- Una segunda ejecución de dev/migrate_partners.py crea 0 registros.
- Chrome con el usuario de operaciones: una oferta [PRUEBA] encuentra por rol al cliente, la naviera y el agente de aduanas reales, y los números salen en formato español.
- dev/check_file_e2e.py sigue en verde.

### F3 · Oferta con datos reales: tarifas aprobadas, precios de venta, plantillas y servicios pendientes — L
**Objetivo.** Que la oferta de un expediente real salga de tarifas aprobadas por Cristina y de sus precios de venta, en lugar de coste + 20 % o importes tecleados. Hoy solo 13 de los 52 servicios de tarifa tienen precio aprobado, 21 de las 22 tarifas aprobadas lo están por delegación de pruebas (devbms), la tarifa general tiene 1 regla y hay 3 plantillas.

**Entregables**
- Aprobación de tarifas por Cristina con su propio usuario (P19), incluidas WFS (id 58) y FuelEU (id 51).
- Documentos de proveedor para los 39 servicios sin precio (docs/mapeo-hoja1.md:122-130), o marca explícita «sin precio de proveedor» o «coste a petición» (M2-H).
- P16: decidir los 9 servicios en 'pending' (VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM).
- Precios de venta de Cristina (M2-17) en listas de precios estándar (ADR-008), incluidas las listas por cliente.
- Plantillas de oferta que faltan (R-S1): EMB, LCL de importación y exportación, y terrestre.
- Lecturas de tarifa pendientes:
- P10/P09 (ETX/DET), P44, P13 (CAU/SEG), P24, P28 (IRENEO 2026, zonas MAD/MAD-EXT) y P40/P41/P29/P42 (WFS);
- excepciones de preguntas-abiertas.md:101-115.
- Ratificar las reglas de precio que ya están aplicadas (M2-B, M2-H, R2-A1, R2-A2, M2-E, FAD por defecto) y las de Ángel (M2-D TARIC, M2-G flete sin ETD, M2-J decimales). Solo cambian ajustes o datos.
- Decidir si la venta y el margen de la aceptación se congelan al recotizar, y el valor por defecto de «Recalcular el coste» (preguntas-abiertas.md:117).
- Decidir sobre el formato corto x_spot (informe 1718 de Odoo 17) frente a la oferta de tarifas de ADR-009/010.
- P34 (precio cerrado para varios envíos): solo la decisión.

**Se reutiliza**
- Motor y servicio único de casado y cálculo (boss_pricing/engine)
- Listas de precios estándar (ADR-008) y sale.order.template (ADR-006)
- dev/pricing_inventory.py, check_quote_flow, check_route_cases y check_default_markup

**Ficheros y módulos:** dev/approve_verified_tariffs.py; dev/setup_templates.py; addons/boss_services/data/product_data.xml; addons/boss_pricing; addons/boss_pricing_sale; docs/mapeo-hoja1.md; docs/preguntas-abiertas.md

**Decisiones que necesita**
- Cristina: P19, P16, M2-17, R-S1, las lecturas de tarifa pendientes, las reglas de precio por ratificar, la congelación al recotizar, x_spot y P34
- Ángel: M2-D, M2-G y M2-J; P13 (CAU/SEG) junto con Cristina

**Aceptación en boss20**
- SQL: tarifas activas con approved_by = usuario de Cristina; 0 servicios con boss_pricing_mode = 'pending' sin un estado decidido.
- SQL: la lista general tiene más de 1 regla, las listas por cliente están cargadas y sale_order_template incluye EMB, LCL y terrestre.
- dev/uat_run.sh dev/pricing_inventory.py boss20: los servicios de tarifa con precio aprobado pasan de 13/52 a la cifra acordada.
- Una oferta [PRUEBA] IMB a un cliente migrado tiene cada línea 'ok' o con un estado explícito, IVA distinto de 'pending' y venta desde su lista.
- check_quote_flow, check_route_cases y check_meeting2 siguen en verde.

### F4 · Base legal y contable de la factura (adelantada: bloquea la primera factura real) — M
**Objetivo.** Que la primera factura real de un expediente sea legalmente correcta, vaya a las cuentas correctas y lleve banco y serie válidos. Para ello se prepara ya SII o VERI*FACTU en modo de pruebas.

**Entregables**
- P45: l10n_es_edi_verifactu (o l10n_es_edi_sii) con l10n_es_edi_verifactu_test_environment = True, sin certificado y sin envío (l10n_es_edi_verifactu/models/res_company.py:13-17).
- Se instala solo después de la decisión de F0 sobre la base, porque si boss20 pasa a producción la cadena de huellas empezaría con facturas de prueba.
- Comprobar que el QR y la huella se ven en el PDF de boss_documents.
- Facturae (l10n_es_edi_facturae) solo si Ángel confirma que se factura a administraciones; en Odoo 17 está instalado (ir.module.module 553).
- Notas legales en el campo estándar account.tax.invoice_legal_notes de los impuestos 41 '0% EX S', 37 '0% S NS' y 74 '0% EXEMPT NS', con el texto de Ángel. Además, invoice_terms de la compañía y la línea del Registro Mercantil.
- P37: dev/setup_category_accounts.py (idempotente) asigna cuentas de ingreso y gasto a las categorías 117-124. La propuesta, presentada como pregunta, sigue Odoo 17: 705001-705009 y 607100-607900, más 705005/607401 para PFT y 623008 para comisiones.
- Ratificar P18 (419001-419007) y reajustar con dev/setup_suplidos_accounts.py si Ángel cambia algo.
- IVA:
- filas nuevas de boss.vat.tax para NS que no es suplido (CAU y QBR, P17);
- tipos reducidos si Ángel lo indica;
- IVA de compra (A01) con supplier_taxes_id y posiciones fiscales estándar.
- Cuenta bancaria de la compañía, diarios bancarios EUR y USD, IBAN en la factura (partner_bank_id) y modelos de conciliación de comisiones.
- Formato de serie decidido (G03) preparado con sequence.mixin; el cambio efectivo se hace en el arranque (F15).
- Procedimiento escrito de fechas de bloqueo.
- ADR-013 «Cumplimiento español y configuración contable».

**Se reutiliza**
- _boss_check_post (account_move.py:81-108): IVA pendiente y NIF siguen igual
- cron 29 de account_return y l10n_es_reports (303/347/349/390 ya generados en boss20)
- dev/setup_suplidos_accounts.py como patrón
- account/models/sequence_mixin.py:44-45 para la serie mensual

**Ficheros y módulos:** odoo-20.0+e.20261020/odoo/addons/l10n_es_edi_verifactu; odoo-20.0+e.20261020/odoo/addons/l10n_es_edi_sii; addons/boss_pricing_sale/models/vat_rules.py; addons/boss_pricing_sale/models/boss_vat_tax.py; addons/boss_documents/report/invoice_templates.xml; dev/setup_vat_mapping.py; dev/setup_category_accounts.py (nuevo); dev/check_documents.py; docs/adr/013-spanish-compliance-and-accounting-setup.md (nuevo)

**Decisiones que necesita**
- Ángel: P45 y su plazo legal (no verificado: lo confirman Ángel o el asesor), textos legales, P37, P18, P17-NS, A01, tipos reducidos, banco y diarios, G03, política de fechas de bloqueo

**Aceptación en boss20**
- SQL: invoice_legal_notes con texto en los impuestos 37, 41 y 74; cuentas definidas en las categorías 117-124; 1 cuenta bancaria de la compañía; diarios bancarios EUR y USD con bank_account_id.
- dev/uat_run.sh dev/check_documents.py boss20 ampliado (rollback): una factura [PRUEBA] de FCL a un cliente de país tercero lleva el flete en la cuenta acordada (no en 700000) y el PDF imprime la mención de exención y el IBAN.
- Si se instala VERI*FACTU: la factura [PRUEBA] contabilizada tiene su registro pendiente, con el entorno de pruebas activo y ir_mail_server = 0. No sale nada.
- Con una fecha de bloqueo fijada dentro de la transacción, contabilizar con fecha anterior se rechaza.
- Una oferta [PRUEBA] con CAU a un cliente español tiene IVA distinto de 'pending'.
- El cron 29 sigue generando 303 y 349 sin error.

### F5 · Apertura, reserva y salida: ciclo de vida operativo — L
**Objetivo.** Que desde la oferta aceptada hasta la salida del buque o el vuelo el expediente diga qué falta y quién lo hace: operativo asignado, hitos por tráfico como actividades estándar, eventos tipificados ligados a las fechas, confirmación del proveedor registrada y condiciones para pasar a «En tránsito».

**Entregables**
- ADR-014 «Ciclo de vida del expediente: estados, condiciones, hitos y eventos».
- Campo operator_id, distinto de user_id (hoy el comercial de la oferta, sale_order.py:87), con su regla de asignación: a mano o por cliente y tráfico, como x_operative_assign de Odoo 17.
- Barra de estado con los estados decididos (posibles 'arrived' y 'pending_close', como x_dashboard_stage 1-5 de Odoo 17).
- Catálogo boss.expediente.event.type: código, modo y sentido, campo de fecha ligado, estimado o real, y si se publica por defecto. Incluye la sincronización fecha ↔ evento sin bucles (FILE_EVENT_FIELDS y _boss_apply_dates, boss_expediente.py:20-40, 549-607). El portal muestra el nombre del tipo.
- Un mail.activity.plan por tráfico (IMB primero), lanzado al abrir el expediente desde _boss_open_files o create y asignado al operativo. Los datos los carga dev/setup_activity_plans.py tras la decisión de Cristina.
- Condición en action_in_transit (boss_expediente.py:1034) con el patrón de action_close_financial. La propuesta sale de la acción 1048 de Odoo 17 y se presenta como pregunta.
- Confirmación del proveedor con partner_ref y acknowledged estándar, visibles en la necesidad. El coste a petición (M2-H) queda como estado explícito.
- Campos operativos generales aprobados: CRD, fecha de booking, seguro, quién lleva el transporte y fecha de última revisión. El historial de ETD/ETA ya lo da tracking=True.
- Aviso o bloqueo de crédito al abrir el expediente, según Ángel, con el credit_limit estándar.
- M2-C: momento de apertura del expediente en una oferta de tarifas.
- Avisos por hito como actividad con una plantilla de correo preparada sobre boss.expediente, sin envío.

**Se reutiliza**
- mail.activity.mixin, que boss.expediente ya hereda (boss_expediente.py:113)
- mail.activity.plan y el asistente mail.activity.schedule (mail/models/mail_activity_plan.py:11-16; mail/wizard/mail_activity_schedule.py:55-56, 187-205), sin base_automation
- purchase.order acknowledged/action_acknowledge y partner_ref (purchase/models/purchase_order.py:122-124, 194, 672-673)
- portal_published y portal_text de los eventos (boss_portal/models/boss_expediente.py:109-121)
- Subhitos de Odoo 17 (x_stages_seaimport_pen/int, x_arrived_stages, x_delivered_stages) y los 26 tipos de evento de Odoo 19, solo como propuesta

**Ficheros y módulos:** addons/boss_expediente/models/boss_expediente.py; addons/boss_expediente/models/sale_order.py; addons/boss_expediente/data/boss_expediente_event_type_data.xml (nuevo); addons/boss_expediente/views/boss_expediente_views.xml; addons/boss_expediente/security/ir.model.access.csv; addons/boss_expediente/i18n/es.po; addons/boss_portal/models/boss_expediente.py; dev/setup_activity_plans.py (nuevo); dev/check_file_lifecycle.py (nuevo); docs/adr/014-file-lifecycle.md (nuevo)

**Decisiones que necesita**
- Cristina: conjunto de estados y condición de cada paso por tráfico; hitos y quién los hace; catálogo de eventos y su publicación al portal; regla de asignación del operativo; campos operativos; hitos que generan aviso al cliente o al agente
- Ángel: M2-C; aviso o bloqueo de crédito al abrir (Odoo 17 bloqueaba con la acción 1168)

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_lifecycle.py boss20 (rollback) termina sin fallos:
- al confirmar una oferta [PRUEBA] IMB se abre el expediente con operator_id y las actividades del plan asignadas;
- escribir la ATD crea el evento de salida real y borrarla lo quita;
- action_in_transit se rechaza sin las condiciones y se acepta con ellas;
- partner_ref es visible en la necesidad;
- un cliente por encima de su límite recibe el aviso o el bloqueo decidido.
- SQL: SELECT count(*) FROM mail_activity_plan p JOIN ir_model m ON m.id = p.res_model_id WHERE m.model = 'boss.expediente' es mayor o igual que el número de tráficos decididos; boss_expediente_event_type > 0.
- Chrome [PRUEBA]: «Mis envíos» muestra el nombre tipificado del evento publicado.
- dev/check_file_e2e.py S1 avanza hasta la salida.

### F6 · Documentos del expediente, visibilidad por rol y portal — M
**Objetivo.** Que cada documento del envío esté en el expediente por tipo y con visibilidad por rol, que los documentos que faltan se pidan desde Odoo y que el portal siga publicando solo lo elegido. Hoy hay 0 documentos de la app Documentos vinculados a expedientes y 6 adjuntos [PRUEBA].

**Entregables**
- ADR-015 «Documentos del expediente y visibilidad».
- Addon puente boss_expediente_documents, que depende de boss_expediente, documents y documents_account. Se separa de boss_documents, que es solo impresión (ADR-011).
- boss.expediente hereda documents.mixin, con carpeta por expediente bajo «Expedientes».
- La carpeta se crea con el expediente y se renombra con él.
- Botón «Documentos».
- Etiquetas «Tipo de documento» según la lista de Cristina. Punto de partida: los 23 tipos del facet 12 de Odoo 17, más OT.
- _get_documents_domain unido a las facturas de cliente (grupos de venta) y a las de proveedor (solo COST_GROUPS, boss_expediente.py:69-74).
- Petición de documentos con documents.request_wizard, sin correo hasta el arranque. Los documentos obligatorios por etapa alimentan las condiciones de F5, F7 y F10 y la lista «Pendiente».
- Portal: la publicación sigue con portal_attachment_ids de boss_portal. Ninguna carpeta de expediente con access_via_link ni con acceso de partner, y /my/documents no expone expedientes.
- Visibilidad: reglas de registro si Cristina decide P35, P20-P23 y P26 (incluido CRM A19). Revisar COST_GROUPS en los campos de coste y margen y en completeness.
- Entrada de correo (alias por carpeta, alias por expediente o complemento de Outlook): solo el diseño; se activa en F15.

**Se reutiliza**
- documents.mixin (documents/models/documents_mixin.py:10-235)
- Patrón de carpeta por registro de documents_project/models/project_project.py:7-20, 62-105, 119-127
- Adjunto a documento automático: documents/models/ir_attachment.py:137-179
- documents/wizard/documents_request_wizard.py:13-75
- Carpetas por diario de documents_account (filas 9-16 en boss20)
- _boss_user_can, COST_GROUPS y SALE_GROUPS

**Ficheros y módulos:** addons/boss_expediente_documents/ (nuevo); addons/boss_portal/models/boss_expediente.py; addons/boss_portal/controllers/portal.py; addons/boss_expediente/security/; dev/check_file_documents.py (nuevo); dev/check_portal_http.py; docs/adr/015-file-documents.md (nuevo)

**Decisiones que necesita**
- Cristina: tipos de documento, cuáles son obligatorios por etapa y cuáles se publican al cliente; P35, P20-P23 y P26; P10-A/B (grupos de empresas, expedidor o destinatario en el portal)
- Belal: addon puente frente a ampliar boss_documents (decisión técnica en el ADR); diseño de la entrada de correo

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_documents.py boss20 (rollback) termina sin fallos:
- un expediente [PRUEBA] crea su carpeta;
- un adjunto del chatter se convierte en documento con res_model 'boss.expediente' y su etiqueta;
- la factura de proveedor se ve con el grupo de compras y no con el de ventas;
- un documento publicado se descarga por la ruta del portal y uno no publicado da 403.
- SQL: 0 documents_document en carpetas de expediente con access_via_link distinto de 'none'.
- check_portal y check_portal_http en verde; un portal de otro cliente recibe 403.
- Chrome: botón «Documentos» y filtro por tipo en un expediente [PRUEBA].

### F7 · Destino: llegada, aduana, entrega y contenedores — L
**Objetivo.** Que el tramo de destino quede registrado y controlado: llegada, despacho (DUA, canal y levante), suplidos del agente de aduanas, orden de transporte al transportista terrestre, entrega, devolución del vacío con aviso antes de la demora y paso a «Entregado» con condiciones.

**Entregables**
- ADR-016 «Aduana, entrega y orden de transporte», diseñado para que la aduana pueda pasar a una partida si M2-I elige la opción B.
- Bloque de aduana:
- estado (pendiente, documentos enviados, presentado, levante), canal, admisión, levante, documentos enviados al agente, tipo de garantía y si la aduana la gestiona BOSS;
- el DUA va en el customs_ref que ya existe;
- los eventos de aduana están tipificados (F5).
- Condiciones de «Llegado» (si existe) y de action_delivered (boss_expediente.py:1037-1038): levante cuando BOSS lleva la aduana, fecha de entrega y, si Cristina y Ángel lo deciden, estar facturado.
- Orden de transporte (OT) en boss_documents:
- direcciones completas (hoy shipment_block.py:51-55 y 84-89 solo imprimen «nombre, ciudad»), contacto, franja horaria, contenedores con precinto, terminal o depósito (Entréguese/Admítase) y notas;
- sobre el pedido de compra al transportista terrestre o sobre el expediente.
- Aviso de llegada, si Cristina lo incluye.
- Último día libre por contenedor, calculado con los días libres de la tarifa de la necesidad (boss_expediente_cost.py:393-451):
- lista «contenedores en riesgo»;
- ir.cron diaria que crea una actividad para el operativo (sin correo);
- columnas de contenedor visibles según el tráfico (views:294-297).
- Avisos al agente o al cliente en levante, entrega programada y entrega hecha, como actividad con plantilla preparada y sin envío.
- Primer ciclo real de suplidos en boss20: factura [PRUEBA] del agente de aduanas sin pedido («Coste sin pedido de compra», boss_expediente.py:1024-1032) → la necesidad ARA/IVA pasa de awaiting_bill a billed. La refacturación a coste al cliente se hace en F9.
- Fuera de esta fase: el lector de DUA (automatización 183 de Odoo 17). El DUA se teclea.

**Se reutiliza**
- _boss_document_block() y la plantilla boss_documents.shipment_block (ADR-011)
- Cadena fecha → periodo → coste: _boss_period_bounds y _boss_container_periods (boss_expediente_cost.py:439-461)
- Maquinaria de suplidos: need.without_order y _boss_bill_needs (account_move.py:30-44), cuentas 419001-419007
- ir.cron y mail.activity estándar
- Campos de x_partidas de Odoo 17 (DUA, canal, levante, estado aduanero, tipo de garantía), solo como propuesta

**Ficheros y módulos:** addons/boss_expediente/models/boss_expediente.py; addons/boss_expediente/models/boss_expediente_cost.py; addons/boss_expediente/data/ir_cron_data.xml (nuevo); addons/boss_expediente/views/boss_expediente_views.xml; addons/boss_documents/report/transport_order_templates.xml (nuevo); addons/boss_documents/models/shipment_block.py; dev/check_file_destination.py (nuevo); docs/adr/016-customs-delivery-transport-order.md (nuevo)

**Decisiones que necesita**
- Cristina: campos y estados de aduana; condiciones de «Llegado» y «Entregado»; contenido de la OT y del aviso de llegada, y si la OT va sobre el pedido o sobre el expediente; días de antelación del aviso de demora; si hay pre-alerta, delivery order o carátula
- Cristina + Ángel: si «Entregado» exige estar facturado; garantía 031, de BOSS o del cliente, y su efecto en CAU
- Ángel: ratificar P18 (cuentas de suplidos)

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_destination.py boss20 (rollback) termina sin fallos:
- el canal y el levante crean sus eventos;
- action_delivered se rechaza sin levante en un expediente con scope_destination_customs y se acepta con él;
- la factura [PRUEBA] del agente sin pedido pasa ARA a 'billed' y suma una sola vez en amount_cost_actual;
- la cron crea una actividad sobre el contenedor sin devolución dentro del umbral;
- el PDF de la OT (_render_qweb_pdf) contiene contenedor, precinto y dirección completa.
- Chrome: la OT de un expediente [PRUEBA] revisada a la vista.
- dev/check_file_e2e.py S1 en verde hasta la entrega.

### F8 · Lado proveedor: facturas recibidas, coste real y pagos a proveedores — L
**Objetivo.** Que el coste real del expediente sea cierto y explicable: casado de facturas (diferencias de precio y cantidad, parciales, abonos, USD), control de facturas sin expediente o que no cuadran, P30 sin agujeros y pagos a proveedores por banco o remesa sin envío real.

**Entregables**
- ADR-017 «Control de facturas de proveedor, tipo de cambio y P30».
- Casado con la herramienta estándar purchase.bill.line.match (purchase/models/purchase_bill_line_match.py:9-233) en lugar de un lector propio.
- Lista de control «Facturas de proveedor por revisar» con vistas y filtros estándar sobre account.move (borrador, sin expediente o sin analítica, con boss_bill_warning, desviación por revisar). Sustituye el proyecto 9 de Odoo 17 («No sabemos expediente», «No cuadran previsiones»).
- Desviación separada en parte de precio y parte de tipo de cambio (boss_expediente_cost.py:279-302) y política de tipo por expediente según P03.
- P30 en todos los caminos de pago:
- enganche en account.move.line._reconcile_plan / reconcile (account/models/account_move_line.py:3132, 3491), que cubre set_line_bank_statement_line (account_accountant/models/account_bank_statement.py:1720) y la conciliación manual;
- alcance según Ángel: in_invoice/in_refund, y factura entera o por servicio.
- Cuenta bancaria obligatoria del proveedor para contabilizar, si Ángel lo decide (automatización 213 de Odoo 17).
- Remesas SEPA con account_batch_payment y account_iso20022: se genera el XML y nunca se envía.
- Proformas y anticipos a proveedor (pago antes de la factura, con P30 comprobado al conciliar), si Ángel lo aprueba.
- Tipo de cambio: cron 24 de currency_rate_live diaria con el BCE si Belal aprueba la llamada externa; diferencias de cambio en el diario CAMBIO (768000/668000).
- OCR de facturas (account_invoice_extract_purchase): solo el diseño; se activa en F15 si Ángel lo aprueba, porque envía datos a un servicio externo.

**Se reutiliza**
- _boss_check_payment_allowed, _boss_bill_order_problems y AccountPaymentRegister._create_payments (account_move.py:52-73, 110-121, 159-166)
- _boss_posted_billing, _boss_billed_by_purchase_line y _boss_direct_bill_items (boss_expediente_cost.py)
- Abonos estándar (_reverse_moves), account_batch_payment, account_iso20022 y currency_rate_live
- Caso de test_storage_period.py:108-114 (abono por precio con variance de -200)

**Ficheros y módulos:** addons/boss_expediente/models/account_move.py; addons/boss_expediente/models/boss_expediente_cost.py; addons/boss_expediente/views/account_move_views.xml; dev/boss20_isolate.py (solo el cron de tipos, si se aprueba); dev/check_supplier_side.py (nuevo); docs/adr/017-supplier-bill-control-fx-p30.md (nuevo)

**Decisiones que necesita**
- Ángel: P03 (política de tipo por expediente y presentación de la diferencia), ratificación y alcance de P30 (con Cristina), P32, cuenta bancaria obligatoria del proveedor, proformas y anticipos, OCR sí o no
- Belal: reactivar el cron del BCE en boss20
- Cristina: si la confirmación del proveedor es obligatoria antes de «En tránsito»

**Aceptación en boss20**
- dev/uat_run.sh dev/check_supplier_side.py boss20 (rollback) termina sin fallos:
- pedido de 100 y factura de 110 → variance_to_review → cierre financiero rechazado → revisión → aceptado;
- abono de -10 → facturado neto 100;
- factura en USD con un tipo distinto del pedido → la diferencia de cambio sale aparte de la de precio;
- conciliar una línea de extracto [PRUEBA] con una factura bloqueada por P30 da UserError, por el widget y por la conciliación manual, y se permite después de contabilizar la factura al cliente;
- una factura sin expediente aparece en el filtro de control;
- el lote de pagos genera el XML SEPA sin envío.
- SQL, si se aprueba el cron: un tipo de USD nuevo por día laborable en res_currency_rate.
- Chrome: la lista de control muestra una factura [PRUEBA] sin expediente.

### F9 · Factura al cliente, suplidos, moneda y cobro — L
**Objetivo.** Que toda la venta del expediente se facture como decida Ángel: servicios y suplidos (separados o no, cada uno con su vencimiento), moneda y QBR, menciones legales, IBAN y serie válida. Y que el cobro se concilie y se vea por expediente.

**Entregables**
- ADR-018 «Facturación al cliente del expediente».
- «Facturar servicios» (wizard/boss_invoice_services.py:29-55) con separación opcional en factura de servicios y factura de suplidos (productos boss_paid_on_behalf):
- son dos llamadas a _create_invoices con boss_invoice_line_ids;
- diario y serie según Ángel;
- condición de pago de impuestos por cliente, con un campo nuevo en res.partner si Ángel lo confirma (x_studio_payment_terms_taxes en Odoo 17).
- PDF: sección y subtotal de suplidos fuera de la base imponible.
- Moneda de la factura (USD a agentes, o EUR) y línea QBR con el porcentaje y la base de P03; valor original en USD si se decide.
- Fecha de factura (¿la «fecha importante» de Odoo 17?) según Ángel.
- Anticipos y proformas de cliente (sale.advance.payment.inv y el grupo de proformas) compatibles con _boss_check_post y con el reparto, si Ángel los pide.
- Cobro:
- importación de extractos CAMT/CSV [PRUEBA] y conciliación;
- amount_collected correcto por expediente;
- account_followup con los niveles decididos (cron 35 activa solo en F15);
- aviso de crédito estándar.

**Se reutiliza**
- sale.order._create_invoices filtrado por contexto
- _boss_check_post (account_move.py:81-108)
- account.tax.invoice_legal_notes (ADR-011, decisión 7)
- amount_on_behalf (boss_expediente.py:773-922)
- account_followup y account_bank_statement_import_camt/csv (instalados)

**Ficheros y módulos:** addons/boss_expediente/wizard/boss_invoice_services.py y su vista; addons/boss_expediente/models/sale_order.py (_get_invoiceable_lines 125-132); addons/boss_expediente/models/res_partner.py; addons/boss_documents/report/invoice_templates.xml; addons/boss_documents/models/account_move.py; dev/check_customer_invoice.py (nuevo); docs/adr/018-customer-invoicing.md (nuevo)

**Decisiones que necesita**
- Ángel: factura de suplidos separada (diario, serie, condición de pago de impuestos, inclusión en el 347); P03 (QBR y moneda de la factura); fecha de factura; anticipos y proformas de cliente; niveles de reclamación

**Aceptación en boss20**
- dev/uat_run.sh dev/check_customer_invoice.py boss20 (rollback) termina sin fallos:
- un expediente con servicios e IVA/ARA del DUA genera las facturas decididas (una o dos), con los suplidos en 419001/419002, el impuesto 74 y su condición de pago;
- el PDF incluye el IBAN, la nota legal del 0 % usado y el subtotal de suplidos;
- una oferta en USD facturada en EUR lleva la línea QBR al porcentaje decidido (o se factura en USD);
- un cobro conciliado con una línea de extracto [PRUEBA] deja amount_collected igual a la factura.
- Chrome: Ángel revisa el PDF de una factura [PRUEBA] (solo visual, sin envío).

### F10 · Cierres, cierre de mes, supervisión y rentabilidad entre expedientes — L
**Objetivo.** Que el final del expediente sea fiable y nada se quede atascado:
- cierre operativo con condiciones y congelación;
- cierre financiero que nadie salta y que nada modifica después;
- cierre de mes (bloqueos, periodificaciones, lista de pendientes);
- avisos de expedientes atascados;
- margen definitivo comparable entre expedientes.

**Entregables**
- ADR-019 «Cierres, supervisión y rentabilidad».
- action_close_operations (boss_expediente.py:1040-1041) con condiciones: Entregado, hitos y documentos obligatorios hechos, y lo que decida Cristina (p. ej. toda la venta facturada, como la acción 1435 de Odoo 17). Cierre comercial aparte si se decide, y grupo para action_reopen.
- Congelación: write() sobre un expediente cerrado rechaza cambios en los datos del envío, salvo para el grupo gestor (automatización 124 de Odoo 17).
- Cierre financiero firme:
- _boss_check_post rechaza contabilizar facturas, abonos o facturas de proveedor con líneas o analítica de un expediente financial_closed;
- action_create_rfqs y boss.invoice.services se niegan sobre él;
- opcionalmente exige cobrado y pagado;
- guarda una instantánea del margen y de las cifras definitivas (campos store).
- Cierre de mes:
- fechas de bloqueo aplicadas;
- periodificación de lo prestado sin facturar (purchase_accountant action_open_accrual_wizard / account.accrued.orders.wizard);
- lista de expedientes por facturar o por cerrar, por mes.
- Supervisión con ir.cron que crea mail.activity para el operativo, sin correo: ETA pasada sin ATA, entregado y sin cerrar después de N días, sin revisar N días, venta pendiente de facturar a fin de mes.
- Aviso de margen con «Desbloquear» (motivo y quién) que impide facturar y cerrar, solo si se deciden P01/P02.
- Informe de rentabilidad entre expedientes: modelo SQL de solo lectura o instantánea al cerrar, con pivot y gráfico por mes, cliente, comercial, operativo y tráfico, y conciliable con el análisis por cuenta analítica.
- Incidencias con coste y valoraciones al cerrar, solo si Cristina las incluye.

**Se reutiliza**
- Patrones de completeness (boss_expediente.py:901-922) y de action_close_financial (1054-1067)
- Fechas de bloqueo estándar y account_return (cron 29 activa)
- account.accrued.orders.wizard y purchase_accountant
- Plan analítico «Shipment files» (id 2) y vistas pivot de boss.expediente.cost (views:473-505)

**Ficheros y módulos:** addons/boss_expediente/models/boss_expediente.py; addons/boss_expediente/models/account_move.py; addons/boss_expediente/models/purchase_order.py; addons/boss_expediente/wizard/boss_invoice_services.py; addons/boss_expediente/data/ir_cron_data.xml; addons/boss_expediente/views/boss_expediente_views.xml; addons/boss_expediente/report/boss_expediente_margin_report.py (nuevo); dev/check_file_close.py (nuevo); docs/adr/019-closes-supervision-profitability.md (nuevo)

**Decisiones que necesita**
- Cristina: condiciones del cierre operativo, quién cierra y quién reabre, cierre comercial aparte, valoraciones e incidencias al cerrar, umbrales y destinatarios de los avisos
- Ángel: si el cierre financiero exige cobro y pago, quién reabre, fechas de bloqueo, periodificaciones, regla de la «fecha importante», P01/P02 (con Cristina), P38

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_close.py boss20 (rollback) termina sin fallos:
- el cierre operativo se rechaza con un hito obligatorio abierto;
- después de cerrar, cambiar el buque como operativo da UserError y como gestor se permite;
- contabilizar una factura [PRUEBA] de proveedor sobre un expediente financial_closed da UserError;
- con una fecha de bloqueo en la transacción, una fecha anterior se rechaza;
- la cron crea una actividad para un expediente [PRUEBA] con la ETA pasada y sin ATA;
- el margen guardado es igual a amount_margin_final;
- el asistente de periodificación propone lo prestado sin facturar.
- SQL después del despliegue: crons de expediente activas y ningún mail_mail en estado 'sent'.
- dev/check_file_e2e.py S1 completo, de la oferta al cierre financiero, sin fallos.

### F11 · Aéreo: exportación (EAB) e importación (IAB) — L
**Objetivo.** Repetir el expediente completo en aéreo. La exportación aérea no se ha ejecutado nunca en boss20 y es parte de la aceptación final. En importación: NOA/ATA, handler y ALM con periodo real. En exportación: FOH y salida.

**Entregables**
- Planes de hitos y condiciones de IAB y EAB, como datos de F5.
- EAB:
- primer recorrido en boss20: FOH → salida (DEFAULT_PERIOD_EVENTS, boss_expediente.py:30-34) y MAWB/HAWB;
- factura de exportación con 0% EX S y su mención (F4).
- IAB: NOA/ATA, handler propuesto desde «Aerolíneas y handlers» (boss_expediente.py:520-571) y ALM con periodo real.
- Venta de ALM (P43/B1, D1-D14), si Cristina decide.
- WFS (fila 38 de la matriz) y lecturas P40, P41, P29 y P42 aplicadas; ETX (B3) comprobado.
- Solo si BOSS emite HAWB/MAWB y etiquetas desde Odoo 20:
- líneas de bultos estructuradas (piezas, dimensiones, peso, clase de tarifa, mercancía peligrosa o clase IMO, valor declarado), sin texto fijo en la plantilla como la vista 5030 de Odoo 17;
- informes en boss_documents y ADR-020.

**Se reutiliza**
- boss.airline.handler y la propuesta de handler (boss_expediente.py:520-571)
- DEFAULT_PERIOD_EVENTS de ALM
- _boss_document_block()
- Informes 1134, 1143 y 1190 de Odoo 17, solo como referencia del contenido

**Ficheros y módulos:** addons/boss_expediente/models/boss_expediente.py; addons/boss_pricing (B1: venta por tiempo); addons/boss_documents/report/awb_templates.xml (nuevo, condicional); dev/setup_activity_plans.py; dev/check_file_e2e.py (S2, S3); docs/adr/020-air-documents.md (nuevo, condicional)

**Decisiones que necesita**
- Cristina: hitos y condiciones de IAB y EAB; si se emiten HAWB/MAWB y etiquetas y con qué datos de bultos; WFS y sus lecturas; P43 (con Ángel en D8 y D11)

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_e2e.py boss20, escenario S2 EAB (rollback): de la oferta al cierre financiero, sin fallos.
- Escenario S3 IAB: periodo de ALM de la NOA a la recogida recalculado y handler propuesto, sin fallos.
- Si se construye el AWB: el PDF de la HAWB contiene piezas y dimensiones de las líneas estructuradas.
- Chrome: el usuario de operaciones recorre un expediente EAB [PRUEBA].

### F12 · Marítimo exportación FCL/LCL, LCL de importación, terrestre y otros sentidos — L
**Objetivo.** Que los tráficos que nunca se han ejecutado en boss20 (0 exportaciones, 0 LCL, 0 terrestres) recorran el expediente completo, con los datos que necesita la exportación y los documentos que BOSS emite.

**Entregables**
- Campos de exportación aprobados: cut-offs (documentos, SI, VGM, entrega FCL, LCL), flete prepaid o collect, tipo de BL y forma de liberación (OBL, SWB, telex) y BL máster verificado.
- Vista por tráfico: salida del vacío y entrada del lleno visibles en exportación.
- Planes de hitos EMB, LCL y terrestre. Comprobar DET de exportación (del vacío al lleno) y ALM de LCL de importación (del vaciado a la recogida).
- Terrestre: referencia CMR, OT de F7 y tarifa IRENEO 2026 (P28).
- Coherencia entre modo y tipo de carga (caso E260010: marítimo con load_type 'road'), según decida Belal.
- Recorrido mínimo de cross-trade y nacional.
- Confirmación de booking e instrucciones de embarque, y HBL si BOSS lo emite como NVOCC, en boss_documents si Cristina lo decide.
- Las plantillas de F3 en uso.

**Se reutiliza**
- DEFAULT_PERIOD_EVENTS de exportación (boss_expediente.py:35-39) y CONTAINER_EVENT_FIELDS
- OT de F7 y _boss_document_block()
- Campos de Odoo 17 (x_studio_cutoff_datetime, si_cutoff, vgm_cutoff, cargo_ready_date), solo como propuesta

**Ficheros y módulos:** addons/boss_expediente/models/boss_expediente.py; addons/boss_expediente/views/boss_expediente_views.xml; addons/boss_documents/report/ (confirmación de booking y HBL, condicional); dev/setup_templates.py; dev/check_file_e2e.py (S4-S6); docs/adr/014-file-lifecycle.md (ampliación por tráfico)

**Decisiones que necesita**
- Cristina: campos y cut-offs de exportación, hitos de EMB, LCL y terrestre, si se emiten HBL como NVOCC y confirmación de booking, listado de mercancía (LM), P28
- Belal: si marítimo con load_type 'road' es una restricción o un caso válido

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_e2e.py boss20, escenarios S4 EMB FCL, S5 LCL de importación y exportación y S6 terrestre nacional (rollback), sin fallos.
- En el script: DET del vacío al lleno; ALM de LCL del vaciado a la recogida; restricción de coherencia según lo decidido.
- SQL: SELECT direction, load_type, count(*) FROM boss_expediente GROUP BY 1,2 igual antes y después (rollback).
- Chrome: el usuario de operaciones recorre un EMB [PRUEBA].

### F13 · Agentes, profit share y facturación a terceros — L
**Objetivo.** Poder liquidar los expedientes de agente (IMA, EAA, IAA) y los fletes collect o prepaid como en producción: PFT en la venta, en el margen y en el resumen; varios pagadores por expediente; abonos de agente.

**Entregables**
- ADR-021 «Agentes y terceros pagadores».
- Varios pagadores por expediente (hoy sale_order.py:66-71 exige un único cliente): un segundo pedido al agente o al tercero dentro del mismo expediente, o el destinatario de factura por línea, según Cristina. «Facturar servicios» emite una factura por pagador.
- Campo de flete prepaid o collect y destinatario de factura, si no se ha hecho en F12.
- PFT:
- venta al agente o línea negativa en su factura;
- abono del agente como ingreso;
- grupo «Profit share» en el resumen (service_groups.py:27; la categoría ya existe);
- cuentas 705005/607401 si Ángel las decide.
- Comisión del recomendador (PFC), solo si Ángel la aprueba. El 40 % y los 95 € son código de Odoo 17 (acción 1613), no una regla aprobada.
- Factura de varios expedientes (acción 1535 de Odoo 17) y bloque del PDF para facturas que mezclan expedientes, si Cristina lo pide.
- Compensación de saldos con agentes que son a la vez cliente y proveedor, según Ángel.

**Se reutiliza**
- boss.expediente.allocation y el asistente boss.invoice.services
- Productos PFT-AIR, PFT-FCL y PFT-LCL (boss_o17_concept_id 221)
- Abonos estándar y facturas en USD (F8, F9)
- Odoo 17 como casos de prueba: account.move 36839, 36559, 35961 y 36282

**Ficheros y módulos:** addons/boss_expediente/models/sale_order.py; addons/boss_expediente/models/boss_expediente_allocation.py; addons/boss_expediente/wizard/boss_invoice_services.py; addons/boss_services/data/product_data.xml (PFT, 999-1055); addons/boss_services/models/service_groups.py; addons/boss_documents/models/account_move.py; dev/check_file_agent.py (nuevo); docs/adr/021-agents-third-party-billing.md (nuevo)

**Decisiones que necesita**
- Cristina: modelo de PFT, varios pagadores o destinatario por línea, collect o prepaid, factura de varios expedientes
- Ángel: cuentas e IVA del PFT (en Odoo 17, '0% EX S'), comisión PFC, compensación de saldos con agentes
- Belal + Cristina: si esta fase entra antes del 1/1

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_agent.py boss20 (rollback) termina sin fallos:
- IMA [PRUEBA]: flete collect facturado al agente en USD con línea PFT negativa y gastos locales al destinatario en EUR, ambos en el mismo expediente (dos facturas);
- EAA con PFT facturado al agente;
- el resumen muestra la fila «Profit share» y el margen cuadra con el análisis por cuenta analítica.

### F14 · Operación en pruebas con datos reales y aceptación por tráfico — M
**Objetivo.** Que las personas de BOSS repitan el expediente completo con envíos reales representativos, clientes migrados y tarifas aprobadas por Cristina, y den la aceptación por tráfico antes del 1/12.

**Entregables**
- Escenarios T02 (FCL de importación), T03 (aéreo de importación y exportación), T04 (marítimo de exportación y terrestre), T05 (contable) y T06 (comercial) de dev/boss_tasks/seed_launch.py, ampliados con las etapas 0-11 de la definición.
- Registro y corrección de incidencias (T07), informe de cierre (T08) y acta de aceptación (G06).
- Escenario de aceptación final ejecutado (ver final_acceptance).
- Despliegues solo con boss20 inactivo (más de 20 min sin uso por Ángel o Cristina).

**Se reutiliza**
- Todos los dev/check_file_*.py como regresión antes de cada despliegue
- Guiones de docs/escenario-uat.md:22-36 y docs/revision-reunion-angel-2026-10-28.md:59-69

**Ficheros y módulos:** docs/escenario-uat.md; dev/boss_tasks/seed_launch.py (T01-T08); docs/evidencias/

**Decisiones que necesita**
- Cristina: quién ejecuta cada escenario y qué cuenta como «envío real representativo»
- Ángel: si T05 contabiliza en boss20 (decisión de F0)

**Aceptación en boss20**
- Todos los dev/uat_run.sh dev/check_file_*.py boss20 en verde con el commit desplegado.
- T02-T06 registrados por su responsable como «pasa con datos operativos representativos», no solo «pasa con [DEMO]».
- El escenario de aceptación final tiene evidencia en docs/evidencias/.

### F15 · Cambio de sistema y arranque del 1/1/2027 — XL
**Objetivo.** Arrancar con los envíos en curso de Odoo 17 migrados, sin números duplicados, con saldos de apertura correctos y con los efectos externos activados de forma controlada.

**Entregables**
- ADR-022 «Cambio de sistema».
- P36: secuencia de expedientes con use_date_range anual que no choque con la serie E26xxxx de Odoo 17.
- El XML está en noupdate=1 (boss_expediente_data.xml:3), así que el cambio va por script o migración.
- Hoy last_value = 108: sin el cambio, el primer número de 2027 sería E270109.
- Activación de las series de factura decididas en G03 (F4).
- dev/migrate_open_files.py (N04/G02):
- migra los expedientes abiertos de Odoo 17 con su etapa, partes, contenedores, referencias, fechas y servicios pendientes de facturar o de comprar (mapeo de conceptos de F2);
- concilia por expediente;
- el ensayo se hace en rollback sobre boss20 (política del 27/10), salvo excepción aprobada por Belal.
- Saldos de apertura (account_opening_move_id) y partidas abiertas de 2026 según Ángel; Odoo 17 queda en solo lectura (G05).
- Ejecución de la estrategia de base decidida en F0: anular los registros [PRUEBA]/[DEMO] contabilizados por las vías estándar, o base nueva.
- Activación controlada de los efectos externos con una lista de control firmada por Belal:
- servidor de correo y dominio de alias (U01), buzón purchases@ y alias de carpetas;
- las 18 crons de dev/boss20_isolate.py, tipos diarios del BCE, sincronización bancaria y cron 35 de seguimiento;
- VERI*FACTU o SII en producción con certificado (Ángel);
- OCR, si se aprueba;
- cuentas reales de portal.
- Regresión completa del E2E antes del 1/12 y después de cada despliegue.

**Se reutiliza**
- ir.sequence con use_date_range (base/models/ir_sequence.py:151)
- res.company.account_opening_move_id (account/models/company.py:175, 1096)
- Mapeo de F2; tareas N04, G01-G06, S04-S06 e I02-I03 de seed_launch.py
- BossOdoo19/docs/BOSS_MIGRATION_MAPPING.md, solo como conocimiento

**Ficheros y módulos:** addons/boss_expediente/data/boss_expediente_data.xml; addons/boss_expediente/migrations/ (nuevo, si se cambia la secuencia por migración); dev/migrate_open_files.py (nuevo); dev/check_migration_open_files.py (nuevo); dev/boss20_isolate.py (restauración); docs/migracion.md; docs/adr/022-cutover.md (nuevo)

**Decisiones que necesita**
- Cristina (con Belal): P36; qué es un expediente «abierto» el 1/1 y cómo se migra (N04)
- Ángel: dónde vive la contabilidad de 2027; saldos de apertura y cobros y pagos pendientes de 2026; paso de VERI*FACTU o SII a producción
- Belal: dónde se ensaya la migración; fecha de activación del correo; política de copias de la base de producción a partir del arranque (la regla actual de trabajo las prohíbe)

**Aceptación en boss20**
- Script en rollback: un expediente con fecha 2027-01-01 recibe E270001 (o el formato decidido) y no coincide con ningún x_name de Odoo 17; el ir_sequence_date_range de 2027 empieza en 1.
- dev/uat_run.sh dev/check_migration_open_files.py boss20 (rollback): para una muestra de expedientes de Odoo 17, recuentos y sumas pendientes de compra y venta por concepto iguales a Odoo 17 (read_record).
- Lista de control de efectos externos firmada antes de activar cada uno; hasta entonces, ir_mail_server = 0.
- SQL en la base de arranque: 0 asientos contabilizados de expedientes [PRUEBA]/[DEMO], o la limpieza documentada según F0.
- Evidencia del E2E (S1-S6) en verde con el commit de la entrega.

### F16 · Consolidación máster/house (condicional a M2-I; probablemente después del arranque) — XL
**Objetivo.** Llevar grupajes y consolidaciones aéreas (un MBL o MAWB con varios HBL o HAWB y costes compartidos) con la opción que elija Cristina.

**Entregables**
- ADR-023: opción A (expediente máster con expedientes hijos, sobre boss.expediente.allocation y el asistente de división) u opción B (modelo de partida, como x_partidas de Odoo 17).
- Reparto de los costes del máster entre las houses según la base que se decida.
- Si se elige la opción B, mover a la partida la aduana de F7 y la documentación de F6.
- HBL, HAWB/MAWB, etiquetas y manifiesto de carga (informes 1387, 1134, 1190 y 1193 de Odoo 17) con datos estructurados.
- Portal: cada cliente ve solo su house.

**Se reutiliza**
- Asistente «Mover servicios a otro expediente» y boss.expediente.allocation con analítica proporcional
- _boss_document_block()

**Ficheros y módulos:** addons/boss_expediente/wizard/boss_expediente_split.py; addons/boss_expediente/models/boss_expediente_allocation.py; addons/boss_documents; addons/boss_portal; docs/adr/023-consolidation.md (nuevo)

**Decisiones que necesita**
- Cristina (con Belal): M2-I opción A o B; si BOSS emite sus propios HBL como NVOCC

**Aceptación en boss20**
- dev/uat_run.sh dev/check_file_consolidation.py boss20 (rollback): un máster [PRUEBA] con 2 houses reparte el coste compartido y factura cada house a su cliente; check_portal_http confirma que un cliente no ve la house del otro.

### F17 · Gastos de empleados y tarjeta (condicional a P39) — S
**Objetivo.** Si Ángel lo aprueba, que los gastos pequeños pagados por un empleado o con tarjeta lleguen al coste real del expediente sin saltarse la regla de refacturación.

**Entregables**
- Instalar hr_expense sin sale_expense. sale_expense crea una cuenta analítica por pedido y añade líneas de venta fuera de boss_rebill_wizard.
- Distribución analítica del expediente en el gasto (analytic.mixin, hr_expense.py:45-46).
- Incluir en _boss_journal_items (boss_expediente.py:616-624) los asientos de gastos pagados por la empresa (move_type 'entry'), si Ángel lo decide. Hoy solo cuenta in_receipt.
- Refacturación solo con boss.rebill.wizard.

**Se reutiliza**
- hr_expense estándar (in_receipt cuando paga el empleado)
- boss.rebill.wizard
- _boss_journal_items

**Ficheros y módulos:** addons/boss_expediente/models/boss_expediente.py; addons/boss_expediente/wizard/boss_rebill_wizard.py; odoo-20.0+e.20261020/odoo/addons/hr_expense/models/hr_expense.py

**Decisiones que necesita**
- Ángel (con Belal): P39 sí o no, y cómo se tratan los gastos pagados por la empresa

**Aceptación en boss20**
- En una comprobación en rollback: un gasto [PRUEBA] pagado por el empleado con la analítica del expediente, una vez contabilizado, sube el coste real en su importe; uno pagado por la empresa cuenta o no según lo decidido.

## Decisiones por responsable
### Ángel (22)
| Decisión | Bloquea |
|---|---|
| Base de producción: boss20 limpiada o base nueva, y si se sigue contabilizando en boss20. Hay contradicción entre CLAUDE.md:40-43 y T05 en seed_launch.py:963. Decide con Belal. | F1 (modo 'post'), F4 (instalar VERI*FACTU), F14 (recorridos contabilizados), F15 |
| P45: SII o VERI*FACTU, y Facturae si se factura a administraciones. Plazo legal sin verificar: lo confirma Ángel o el asesor. | F4, F15 |
| G03: series de factura de 2027 y su continuidad con F26 MM-NNNN, FR26 y BILL de Odoo 17 | F4, F15 |
| P18: ratificar las cuentas de suplidos 419001-419007 (D-2) | F4, F7, F9 |
| P37: cuentas de ingreso y gasto por categoría, incluidas flete, PFT y comisiones | F4, F8, F13 |
| Textos legales del 0 % (impuestos 41, 37 y 74), condiciones de pago de la compañía y línea del Registro Mercantil | F4, F9 |
| P17-NS (IVA de CAU y QBR para cliente español), tipos reducidos y A01 (IVA de compra por tipo de factura) | F3 (ofertas con CAU), F4, F8 |
| Ratificar P30 (con Cristina) y su alcance: factura entera o por servicio, in_refund, conciliación bancaria incluida. Ratificar también P32. | F8 |
| P03: porcentaje y base del QBR, moneda de factura y política de tipo de cambio por expediente (separar desviación de precio y de tipo) | F8, F9, F13 |
| Bancos: cuenta de la compañía, diarios EUR y USD, conexión bancaria y modelos de conciliación | F4, F8, F9, F15 |
| Cuenta bancaria obligatoria del proveedor para contabilizar; proformas y anticipos de proveedor; prepagos de cliente | F8, F9 |
| Factura de suplidos separada (diario, serie, condición de pago de impuestos) y su inclusión en el 347 | F9 |
| Condiciones de pago, niveles de reclamación, límites de crédito, y aviso o bloqueo de crédito al abrir el expediente | F2, F5, F9 |
| M2-C: el expediente de una oferta de tarifas se abre al aceptarla o al hacer el booking | F5 |
| Cierre financiero: si exige cobro y pago, y quién reabre. Además: fechas de bloqueo, periodificación mensual y regla de la «fecha importante» como fecha de factura. | F10 |
| P01/P02: margen mínimo y aviso con desbloqueo (con Cristina). P38: coste interno. | F10 |
| Si «Entregado» exige estar facturado; garantía 031, de BOSS o del cliente, y su efecto en CAU (con Cristina, P13) | F7, F3 |
| Cuentas e IVA del PFT, comisión PFC y compensación de saldos con agentes | F13 |
| OCR (IAP) y buzón purchases@ sí o no (envían datos a un servicio externo) | F8 (diseño), F15 (activación) |
| Dónde vive la contabilidad de 2027, saldos de apertura y cobros y pagos pendientes de 2026; paso de VERI*FACTU o SII a producción con certificado | F15 |
| P39: gastos de empleados y de tarjeta (con Belal) | F17 |
| M2-D (aranceles por TARIC), M2-G (flete sin ETD), M2-J (decimales en precios «por 100 kg»); ratificar P31, P33 y P11 | F3 (solo confirmación de lo ya aplicado) |

### Cristina (20)
| Decisión | Bloquea |
|---|---|
| Conjunto de estados (¿Llegado? ¿Pendiente de cierre?) y condición de cada paso por tráfico | F5, F7, F10, F11, F12 |
| Hitos y listas de tareas por tráfico, cuáles son obligatorios y quién los hace; catálogo de tipos de evento y cuáles se publican al portal; avisos a cliente o agente por hito | F5, F7, F11, F12 |
| Operativo responsable y regla de asignación (manual o por cliente y tráfico) | F5, F10 (avisos por operativo) |
| Campos operativos mínimos (CRD, fecha de booking, cut-offs, SI/VGM, prepaid/collect, tipo de BL, seguro, quién lleva el transporte, última revisión) | F5, F12 |
| Bloque de aduanas: campos, estados y si el levante condiciona «Entregado» | F7 |
| Contenido de la OT y del aviso de llegada; prioridad de los demás documentos operativos (confirmación de booking, SI, pre-alerta, delivery order, carátula, LM); días de antelación del aviso de demora | F7, F12 |
| Si BOSS emite desde Odoo 20 HAWB/MAWB y etiquetas (y con qué datos de bultos), y si emite HBL propios como NVOCC | F11, F12, F16 |
| Tipos de documento, cuáles son obligatorios por etapa y cuáles se publican al portal | F6, F7, F10 |
| Visibilidad: P35, P20-P23, P26 (quién ve coste y margen) y P10-A/B (grupos de empresas y expedidor o destinatario en el portal) | F6 |
| Cierre operativo: condiciones, quién cierra y reabre, cierre comercial aparte, valoraciones e incidencias con coste; umbrales y destinatarios de los avisos | F10 |
| R-A3 (mapeo de roles y validación del ordenante) y W08 (usuarios de operaciones y sus roles) | F2, F3, F14 |
| P19 (aprobar tarifas, incluidas WFS 58 y FuelEU 51) y documentos de proveedor de los 39 servicios sin precio | F3, F11 |
| P16 (9 servicios pendientes), M2-17 (precios de venta) y R-S1 (plantillas EMB, LCL y terrestre) | F3, F12 |
| Lecturas de tarifa pendientes: P10/P09, P44, P13 (con Ángel), P24, P28, P40/P41/P29/P42 | F3, F11, F12 |
| Ratificar reglas de precio (M2-B, M2-H, R2-A1, R2-A2, M2-E, FAD por defecto); congelación al recotizar; formato corto x_spot; P34 | F3 (solo cambian ajustes o datos) |
| P43: venta de ALM (D1-D14; D8 y D11 con Ángel) | F11 |
| Modelo de PFT, varios pagadores o destinatario por línea, collect o prepaid, factura de varios expedientes | F13 |
| M2-I: consolidación con opción A (máster con hijos) u opción B (partida) | F16; también el diseño de F6 y F7, para que se puedan trasladar |
| P36 (numeración de expedientes, con Belal) y N04 (qué expediente de Odoo 17 está «abierto» el 1/1 y cómo se migra) | F15 |
| Quién ejecuta los escenarios T02-T06 y qué cuenta como «envío real representativo» | F14 |

### Belal (9)
| Decisión | Bloquea |
|---|---|
| Capacidad de S45/S46 (−59 h / −43 h) y fases obligatorias para el 1/1: segundo desarrollador, recorte de alcance, convivencia de tráficos con Odoo 17 o mover la fecha | Todo el plan; orden y fechas de F5-F16 |
| Alcance de N01: qué contactos se migran (tipos, antigüedad, históricos) y si van sus cuentas bancarias (con Ángel) | F2, F15 |
| Dónde se ensaya la migración (N04 dice «copia local» y la política del 27/10 lo prohíbe): rollback en boss20 o excepción aprobada | F15 |
| Infraestructura de correo (U01): dominio de alias, buzón de entrada, servidor saliente, complemento de Outlook y fecha de activación | F6 (diseño), F15 |
| Reactivar el cron del tipo de cambio del BCE en boss20 (llamada externa) | F8, F9 |
| Marítimo con load_type 'road' (E260010): restricción o caso válido | F12 |
| Addon puente boss_expediente_documents o ampliar boss_documents (decisión técnica en el ADR) | F6 |
| La regresión son los check_*.py en boss20; las pruebas Odoo quedan como referencia (política del 27/10) | F1 |
| Migración de los 49.697 documentos históricos de Odoo 17 (la propuesta es dejarla fuera) y política de copias de la base de producción a partir del arranque (la regla actual de trabajo las prohíbe) | F15 |

## Aceptación final
- Expediente A, importación marítima FCL con DUA (IMB), con registros [PRUEBA] en boss20, recorrido en este orden:
- Oferta a un cliente español con NIF: tarifas aprobadas por Cristina, venta desde su lista e IVA sin 'pending'. Aceptación.
- Expediente E… con cuenta analítica, operativo y plan IMB. Solicitudes por proveedor y moneda confirmadas con partner_ref.
- Booking, MBL, HBL, buque y contenedores con precinto. ATD y paso a «En tránsito» con sus condiciones.
- ATA y descarga. DUA, canal y levante. Factura del agente de aduanas sin pedido (ARA/IVA a 'billed', contados una sola vez).
- PDF de la OT. Fecha de entrega, recogida del lleno y devolución del vacío, con DEM/OCU recalculados. Paso a «Entregado» con sus condiciones.
- Facturas de proveedor desde el pedido: una con diferencia de precio revisada y un abono de proveedor.
- P30 bloquea el pago por botón, asistente y conciliación bancaria hasta que se factura al cliente.
- Facturas al cliente (servicios y suplidos según decida Ángel) con mención legal, IBAN, serie decidida y registro VERI*FACTU de prueba si se instala.
- Cobro y pagos registrados en Odoo y conciliados con líneas de extracto [PRUEBA]. El pago a proveedor se hace por remesa SEPA: el XML se genera y no se envía.
- Cierre operativo con condiciones. Cierre financiero con «Pendiente» vacía.
- Una nueva factura de proveedor sobre el expediente se rechaza. El margen definitivo guardado es igual al del formulario y al del informe analítico.
- Expediente B, exportación aérea (EAB), con registros [PRUEBA] en boss20, recorrido en este orden:
- Oferta a un exportador español y expediente con plan EAB.
- Solicitud a la aerolíneas o handler confirmada. FOH y referencias MAWB/HAWB.
- ATD y paso a «En tránsito». Evento de salida publicado y visible en «Mis envíos» del cliente [PRUEBA].
- Factura de proveedor en USD, con la diferencia de cambio contabilizada en CAMBIO y separada de la de precio.
- Factura de exportación al 0 % con su mención legal.
- Cobro y pago registrados en Odoo y conciliados, sin transferencia real.
- Cierre operativo y cierre financiero.
- Los dos expedientes pasan como comprobación automática: dev/uat_run.sh dev/check_file_e2e.py boss20 (escenarios S1 y S2, en rollback) termina con «RESULT n passed, 0 failed» y deja en docs/evidencias/ el fichero con el commit desplegado y las versiones de los módulos. Después, SELECT count(*) FROM boss_expediente no cambia.
- Los dos expedientes se recorren en Chrome en https://system.bosscontinental.com con el usuario de operaciones y con el de contabilidad. Los registros [PRUEBA] persisten y llegan a 'closed' con financial_closed = true solo si F0 autoriza contabilizar en boss20. Si no lo autoriza, el recorrido en Chrome llega hasta antes de contabilizar y la contabilización queda cubierta por el script en rollback.
- Comprobaciones negativas dentro del mismo script:
- un usuario solo de ventas no puede cerrar ni reabrir financieramente por RPC;
- un usuario de ventas no ve la factura de proveedor ni los costes;
- escribir en un expediente cerrado como operativo se rechaza;
- el portal de otro cliente recibe 403 en los documentos del expediente;
- /my/documents no muestra carpetas de expediente.
- Sin efectos externos durante la aceptación:
- ir_mail_server = 0 y ningún mail_mail en estado 'sent' creado durante la ejecución;
- VERI*FACTU/SII en entorno de pruebas sin envío;
- account_online_link = 0;
- remesas SEPA solo como fichero XML.
- Regresión con el mismo commit: check_meeting2, check_quote_flow, check_route_cases, check_meeting_matrix, check_portal, check_portal_http y check_documents en verde.
- Toda regla aún no decidida aparece en los dos expedientes como estado explícito 'pending decision' con su responsable, nunca como valor inventado. Se comprueba contra docs/preguntas-abiertas.md.
- Aceptación de negocio: el operativo que designe Cristina (T02 y T03) y Ángel (T05) repiten los dos casos con contactos migrados y tarifas aprobadas, y lo registran como «pasa con datos operativos representativos» en las tareas de seed_launch.py antes del 1/12.

## Riesgos
- Capacidad (estimación propia, sin verificar): sumando las fases salen unas 800 h, y un solo desarrollador tiene unas 270 h del 28/10 al 31/12 (28-35 h por semana; ya faltan 59 h en S45 y 43 h en S46, docs/ciclo-operativo.md:73-83). Incluso el núcleo mínimo (F0-F10, F11 sin AWB, F14 y F15) ronda las 450 h. Belal debe elegir en F0 entre un segundo desarrollador, que algunos tráficos (agentes, exportación marítima, consolidación) sigan en Odoo 17 después del 1/1, o mover la fecha. Si no decide, el plan no se cumple.
- Cuello de botella de decisiones: casi todas las fases dependen de Cristina (estados, hitos, aduana, documentos, OT, exportación, M2-I, PFT) o de Ángel (P45, P03, P18, P30, P37, suplidos, series, saldos). Cristina todavía no tiene usuario en boss20 (W08), y 21 de las 22 tarifas aprobadas lo están por delegación de pruebas. Mientras no decidan, cada regla queda 'pending decision' y la fase no se puede aceptar. Por eso las preguntas van agrupadas por etapa y con fecha límite.
- Base de producción sin decidir: boss20 ya tiene asientos de prueba (INV/2026/00001-00004, RINV/2026/00001, FACTURA/2026/10/0001-0005, BNK1/2026/00001-00005) y 108 números de expediente gastados. CLAUDE.md permite contabilizar pruebas allí y T05 lo prohíbe. Cada recorrido que contabiliza agrava el problema. Si se instala VERI*FACTU en una base que luego será la real, la cadena de huellas empezaría con facturas de prueba.
- Riesgo legal en el arranque: el plazo de VERI*FACTU o SII para BOSS no está verificado y no hay ningún módulo instalado. Si aplica desde el 1/1/2027, la primera factura real lo necesita, con certificado y configuración (P45).
- Agujero de P30, visto en el código y no reproducido en boss20: la conciliación bancaria (account_bank_statement.py:1720) o la manual pagan una factura de proveedor bloqueada. Hasta F8, el requisito de Cristina no está garantizado.
- Desviaciones falsas en USD: la desviación mezcla precio y tipo de cambio (boss_expediente_cost.py:279-302) y el tipo está parado (un solo USD, del 26/10, con el cron 24 inactivo). Cada expediente con flete en USD bloquearía el cierre financiero hasta que Ángel decida P03.
- Sin red de seguridad automática hasta F1: las 34 pruebas Odoo y las 23 del motor no se ejecutan desde el 27/10, cuatro módulos no tienen pruebas, dev/uat_e2e.py no funciona en boss20 y ningún expediente ha llegado nunca a un cierre.
- Las comprobaciones en rollback gastan números de secuencia (E260038 → E260056 → E260098, last_value 108). Si boss20 pasa a producción, habrá huecos y un arranque desplazado (E270109) hasta resolver P36 en F15.
- Migración de contactos: unos 21.600 contactos activos en Odoo 17, con contactos tipo lugar mezclados y duplicados. Son datos personales (RGPD y NDA: nunca en Git, en URLs ni en conectores externos). N01 venció el 30/10 sin alcance, y sin F2 no hay ningún expediente real posible.
- Migración sin base de ensayo: N04 pide un ensayo en una copia local que la política del 27/10 prohíbe. Hace falta un ensayo en rollback sobre boss20 o una excepción aprobada. No se sabe cuántos de los unos 1.300 expedientes E26 seguirán abiertos el 1/1.
- Confidencialidad: la app Documentos (/my/documents, enlaces, acceso de partner) podría saltarse el alcance de ADR-010, y unir las facturas de proveedor a la vista del expediente sin COST_GROUPS mostraría costes a los comerciales. Por eso la publicación sigue en boss_portal y el puente va en un addon aparte.
- Efectos externos: al reactivar las 18 crons, el IAP, el correo, la sincronización bancaria y el seguimiento de cobros empiezan los envíos automáticos. El OCR y la sincronización bancaria mandan datos a servicios externos. Solo se activan en F15, con una lista de control firmada y la aprobación expresa de Belal y Ángel.
- M2-I sin decidir: si Cristina elige el modelo de partida, la aduana (F7), los documentos (F6) y la facturación habrá que moverlos. Se diseñan para poder trasladarlos.
- Convertir la práctica de Odoo 17 en regla sin aprobación (comisión del 40 % menos 95 €, condiciones de cierre, cuenta bancaria obligatoria, umbrales de los avisos). Son prácticas no verificadas en uso: subhitos, FactReader, remesas fuera de Odoo, frecuencia de varios pagadores. Siempre se presentan como pregunta.
- Convivencia con Odoo 17: si no se migran los expedientes abiertos ni se decide dónde va la contabilidad de 2026, habrá dos sistemas a la vez y cierres financieros con facturas repartidas entre ambos.
- Rendimiento: los importes amount_* no están almacenados (boss_expediente.py:256-311). Con unos 1.300 expedientes al año, las listas, los avisos programados y los informes necesitan la instantánea al cierre o el informe analítico (F10).
- Operación: cada despliegue reinicia la web de boss20. Hay que respetar la regla de desplegar con boss20 inactivo (más de 20 minutos sin uso de Ángel o Cristina) durante las pruebas de diciembre.

## Fuera de alcance
- Almacén: stock.picking, entradas, palés y recordatorio mensual de almacenaje (acción 1505 y crons 95/96 de Odoo 17). stock no está instalado y requiere su propia decisión de Cristina.
- Integración automática de seguimiento con navieras y aerolíneas (P-9; docs/portal-seguimiento-integraciones.md). Los eventos se registran a mano o desde las fechas.
- Lector automático de DUA (automatización 183 de Odoo 17). El DUA y los suplidos se teclean o se casan con la factura del agente de aduanas.
- Migración de los 49.697 documentos históricos de la carpeta «Expedientes» de Odoo 17 y de los expedientes ya cerrados, salvo que Belal decida otra cosa.
- Migración de la contabilidad histórica de Odoo 17, que queda en solo lectura salvo decisión de Ángel.
- Motor de informes x_reports, informes periódicos a clientes (x_clientreport) y KPIs comerciales más allá del informe de rentabilidad de F10.
- Formato corto de oferta x_spot e informe 1718, salvo que Cristina lo pida en F3.
- Valoraciones de clientes y proveedores al cerrar e incidencias de calidad con coste y horas, salvo que Cristina las incluya en F10.
- P34 (precio cerrado para varios envíos, tipo Leroy): solo se registra la decisión; la construcción se hace después del arranque salvo que Cristina la exija.
- Réplica de FactReader: el casado se hace con purchase.bill.line.match estándar.
- base_automation y Studio: las automatizaciones se hacen con código en los addons, ir.cron y mail.activity.plan.
- sale_expense; hr_expense solo si se aprueba P39 (F17).
- Website público (P10-C), Peppol y TicketBAI, salvo decisión expresa.
- Cualquier efecto externo real durante el desarrollo y las pruebas: correo a clientes o proveedores, presentaciones a la AEAT, transferencias o subida de remesas, OCR con IAP real.
- Bases de prueba o copias (boss20_uat, boss20_test_*) y ejecución local de Odoo, Docker o pruebas (política del 27/10).
- Copiar módulos o código de Odoo 19 u Odoo 17: solo se usan como conocimiento.

## Cobertura de los huecos encontrados
112 de 112 huecos tienen fase asignada o están declarados fuera de alcance.

| Área | Hueco | Dónde se cubre |
|---|---|---|
| Ciclo operativo | Los cambios de estado no tienen condiciones (SA 1048/1062/1109/1490 de Odoo 17 sin equivalente) | F5 (En tránsito), F7 (Llegado y Entregado), F10 (cierre operativo) |
| Ciclo operativo | Sin lista de hitos por etapa y tráfico (4 cadenas de subetapas de Odoo 17) | F5 (mecanismo e IMB), F11 (IAB/EAB), F12 (EMB/LCL/terrestre) |
| Ciclo operativo | Modelo de eventos pobre: sin tipos, sin estimado/real, sin enlace con las fechas | F5 |
| Ciclo operativo | Faltan campos operativos (CRD, fecha de booking, cut-offs, SI/VGM, prepaid/collect, seguro, tipo de BL, última revisión) y no se pueden calcular los KPI CR-O1/O3/O4 | F5 (generales), F12 (exportación), F10 (KPI y supervisión) |
| Ciclo operativo | Aduana en un solo campo Char: sin canal, levante, garantía, estado ni lector de DUA | F7. El lector de DUA (automatización 183) queda fuera de alcance para el 1/1 |
| Ciclo operativo | Sin documentos operativos (pre-alerta, confirmación de booking, SI, aviso de llegada, delivery order, OT, carátula, BL/AWB) | F7 (OT y aviso de llegada), F12 (booking, SI, HBL), F11 (AWB), F16 (manifiesto). Pre-alerta, delivery order y carátula: decisión de Cristina en F7 |
| Ciclo operativo | Devolución de contenedores y demora solo como coste: sin último día libre ni aviso | F7 |
| Ciclo operativo | ATD oculta en importación y recogida real oculta en exportación | F1 |
| Ciclo operativo | Consolidación M2-23 (máster/house) | F16 (condicional a M2-I) |
| Ciclo operativo | Sin supervisión (crons de avisos de Odoo 17: 93, 90, 76, 92, 100) | F10 (y F7 para la demora) |
| Ciclo operativo | Cierre operativo débil: el expediente sigue editable y no hay cierre comercial | F10 |
| Ciclo operativo | Incidencias solo como texto: sin coste, horas, causa ni estado | F10 si Cristina las incluye; si no, fuera de alcance |
| Ciclo operativo | Sin avisos al cliente o al agente en los hitos | F5 (mecanismo de actividad con plantilla, sin envío), F7 (levante y entrega), F15 (activación del correo) |
| Ciclo operativo | El responsable es el comercial, no el operativo | F5 |
| Ciclo operativo | Exportación, LCL, cross-trade, nacional y terrestre nunca ejecutados; E260010 incoherente | F11 (EAB), F12 (EMB, LCL, terrestre, cross-trade, nacional, E260010) |
| Ciclo operativo | M2-C: momento de apertura en una oferta de tarifas | F5 (decisión de Ángel) |
| Compras y proveedor | Diferencias en la factura de proveedor (precio, cantidad, parcial, abono, USD) nunca ejercitadas en boss20 | F1 (primeros casos en rollback), F8 |
| Compras y proveedor | La desviación mezcla precio y tipo de cambio | F8 |
| Compras y proveedor | P30 se salta por conciliación bancaria o manual, solo cubre in_invoice y bloquea la factura entera | F8 |
| Compras y proveedor | Profit share y negocio de agentes (PFT de venta, línea negativa, abonos) | F13 |
| Compras y proveedor | Facturar a un tercero (agente, collect o prepaid) | F13 (y F12 para el campo prepaid/collect) |
| Compras y proveedor | Comisión del recomendador PFC | F13 (condicional a Ángel) |
| Compras y proveedor | Pago a proveedores sin preparar (sin cuentas bancarias ni SEPA, sin cuenta obligatoria) | F2 (cuentas de proveedores), F4 (banco de la compañía), F8 (SEPA y cuenta obligatoria) |
| Compras y proveedor | Confirmación del proveedor sin rastro; coste a petición pedido a 0 € | F5 (partner_ref y acknowledged), F3 (decisión M2-H), F8 (casado posterior) |
| Compras y proveedor | Ciclo de suplidos sin pedido nunca ejecutado en boss20 | F1 (rollback), F7 (primer ciclo), F9 (refacturación) |
| Compras y proveedor | Cierres sin control: cierre operativo sin condiciones y nada bloqueado tras el cierre financiero | F1 (grupo en el servidor), F10 |
| Compras y proveedor | Las facturas de proveedor no llevan el expediente en sus líneas | F1 (desde el pedido o la analítica), F8 (filtro «sin expediente») |
| Compras y proveedor | Faltan cuentas por producto (flete, PFT, comisiones) | F4 (P37) |
| Compras y proveedor | Documentación contradictoria sobre el valor por defecto de P30 | F1 |
| Compras y proveedor | Sin evidencia en boss20 del ciclo de compras completo después del 27/10 | F1, F8 |
| Contabilidad y cumplimiento | Los suplidos no salen en una factura de impuestos separada ni en una sección propia del PDF | F9 |
| Contabilidad y cumplimiento | Cuentas de ingreso y gasto por grupo de servicio (P37) | F4 |
| Contabilidad y cumplimiento | Sin cuenta bancaria de la compañía, sin diarios EUR/USD, sin conexión bancaria y sin IBAN en la factura | F4 (cuenta, diarios, IBAN), F9 (importación de extractos), F15 (sincronización) |
| Contabilidad y cumplimiento | SII o VERI*FACTU sin decidir; Facturae ausente | F4 (modo de pruebas), F15 (producción) |
| Contabilidad y cumplimiento | Facturación multimoneda y QBR; tipos parados | F8 (tipos y cron), F9 (factura en USD y línea QBR) |
| Contabilidad y cumplimiento | Sin factura de varios expedientes ni pagador por línea | F13 |
| Contabilidad y cumplimiento | Sin proceso de cierre de mes (bloqueos, periodificación, recordatorios) | F4 (procedimiento de bloqueo), F10 |
| Contabilidad y cumplimiento | Series de factura y continuidad en el cambio | F4 (formato), F15 (activación) |
| Contabilidad y cumplimiento | Proformas y anticipos de proveedor; prepagos de cliente | F8 (proveedor), F9 (cliente); ambos condicionales a Ángel |
| Contabilidad y cumplimiento | Faltan menciones legales en los impuestos 41/37/74 y condiciones de la compañía; la evidencia contradice la base | F4 (datos), F1 (nota de corrección) |
| Contabilidad y cumplimiento | IVA de NS no suplido (CAU, QBR), IVA de compra (A01) y tipos reducidos | F4 |
| Contabilidad y cumplimiento | Condiciones de pago, niveles de reclamación y límites de crédito de Odoo 17 sin cargar | F2 (datos), F9 (seguimiento y aviso), F15 (cron 35) |
| Contabilidad y cumplimiento | Cierre financiero débil: sin grupo en el servidor y se puede contabilizar después | F1 (grupo), F10 (nada contabilizable después) |
| Contabilidad y cumplimiento | Cobrado y pagado sobrevalorados con documentos de varios expedientes | F1 |
| Contabilidad y cumplimiento | Sin informe de rentabilidad entre expedientes (importes no almacenados) | F10 |
| Documentos y gastos | Sin carpeta de la app Documentos por expediente | F6 |
| Documentos y gastos | Sin taxonomía de tipos de documento | F6 |
| Documentos y gastos | Facturas archivadas por diario y no en el expediente; la unión debe respetar COST_GROUPS | F6 |
| Documentos y gastos | Recepción y control de facturas de proveedor (proyecto 9 de Odoo 17) | F8 (lista de control), F15 (buzón purchases@) |
| Documentos y gastos | El OCR no puede funcionar (IAP bloqueado) y las facturas sin pedido necesitan expediente | F8 (diseño y filtro), F15 (activación si Ángel la aprueba) |
| Documentos y gastos | Sin correo entrante al expediente | F6 (diseño), F15 (infraestructura) |
| Documentos y gastos | La publicación en el portal debe seguir en la ruta protegida de boss_portal | F6 |
| Documentos y gastos | Sin petición de documentos al cliente o al agente | F6 |
| Documentos y gastos | Gastos de empleados y tarjeta (P39) | F17 (condicional) |
| Documentos y gastos | Orden de transporte (OT) al transportista terrestre | F7 |
| Documentos y gastos | Documentos de transporte aéreo y marítimo (HAWB/MAWB, etiquetas, HBL, manifiesto, LM) | F11 (AWB y etiquetas, si se decide), F12 (HBL y LM, si se decide), F16 (manifiesto y consolidación) |
| Documentos y gastos | Formato corto de oferta x_spot | F3 (solo decisión de Cristina); fuera de alcance si no lo pide |
| Documentos y gastos | Documentos históricos de Odoo 17 (49.697) sin migrar | Fuera de alcance (decisión de Belal en F0) |
| Documentos y gastos | Infraestructura de correo para producción (dominio de alias, buzón, servidor saliente) | F15 (decisión de Belal en F0) |
| Proceso real Odoo 17 | 5 etapas y 32 subhitos de producción frente a 4 estados sin Llegado ni Pendiente de cierre | F5 (estados y planes), F7, F10 |
| Proceso real Odoo 17 | Condiciones de estado y bloqueo después del cierre | F5, F7, F10 |
| Proceso real Odoo 17 | Bloque de aduanas por expediente o partida | F7 (trasladable a la partida en F16) |
| Proceso real Odoo 17 | Factura de suplidos separada (tipo TAX) | F9 |
| Proceso real Odoo 17 | Aviso de margen con «Desbloquear» | F10 (condicional a P01/P02) |
| Proceso real Odoo 17 | Documentos operativos que hoy salen de Odoo (HBL, AWB, etiqueta, manifiesto, LM, OT, oferta corta) | F7 (OT), F11, F12, F16; oferta corta en F3 (decisión) |
| Proceso real Odoo 17 | Avisos al agente o al cliente en los hitos y tareas por hito | F5, F7 |
| Proceso real Odoo 17 | Control del cierre mensual (fecha importante, informes de fin de mes) | F10 |
| Proceso real Odoo 17 | Control de crédito al abrir el expediente o al facturar | F2 (límites), F5 (al abrir), F9 (al facturar) |
| Proceso real Odoo 17 | Varios destinatarios de factura en un mismo expediente | F13 |
| Proceso real Odoo 17 | Partidas y consolidaciones | F16 (condicional a M2-I) |
| Proceso real Odoo 17 | Entrada de facturas de proveedor (casado, PDF, cuenta bancaria del proveedor) | F8 (casado y control), F6 (PDF en la carpeta), F2 (cuentas bancarias) |
| Proceso real Odoo 17 | Pagos y remesas | F8 |
| Proceso real Odoo 17 | Envío de facturas a la AEAT (SII o VeriFactu) | F4 (modo de pruebas), F15 (producción) |
| Proceso real Odoo 17 | Tipo de cambio por expediente y QBR | F8 (política de tipo), F9 (QBR) |
| Proceso real Odoo 17 | Valoraciones de clientes y proveedores al cerrar e incidencias de calidad | F10 si Cristina las exige; si no, fuera de alcance |
| Proceso real Odoo 17 | Migración de expedientes abiertos y de contactos | F2 (contactos), F15 (expedientes abiertos) |
| Proceso real Odoo 17 | Almacén (stock, entradas, palés, almacenaje mensual) | Fuera de alcance (necesita decisión de Cristina aparte) |
| Datos, decisiones y pruebas | R-A4 / N01-N03: migración de contactos y direcciones | F2 |
| Datos, decisiones y pruebas | Mapeo de roles y tipos de contacto y R-A3 | F2 |
| Datos, decisiones y pruebas | Familias de transportista (M2-3) | F2 |
| Datos, decisiones y pruebas | P16 y mapeo de x_concept a los 77 servicios | F3 (P16), F2 (mapeo de conceptos) |
| Datos, decisiones y pruebas | Expedientes abiertos de Odoo 17 en el cambio (N04/G02) | F15 |
| Datos, decisiones y pruebas | P36: numeración de expedientes sin rango anual y con choque con E26 | F15 (decisión registrada en F0) |
| Datos, decisiones y pruebas | Continuidad de la numeración de facturas | F4, F15 |
| Datos, decisiones y pruebas | Saldos de apertura y dónde vive la contabilidad en 2027 | F15 (decisión de Ángel en F0) |
| Datos, decisiones y pruebas | Estrategia de la base de producción (boss20 ya tiene asientos de prueba) | F0 (decisión), F15 (ejecución) |
| Datos, decisiones y pruebas | Bancos: sin cuenta de la compañía y solo el diario BNK1 | F4 |
| Datos, decisiones y pruebas | Usuarios y roles (W08): Cristina y operaciones sin usuario | F2 |
| Datos, decisiones y pruebas | Reactivar efectos externos (correo y 18 crons) | F15 |
| Datos, decisiones y pruebas | M2-F / M2-11: usuarios en en_US | F2 |
| Datos, decisiones y pruebas | P19: tarifas aprobadas por Cristina (13 de 52) | F3 |
| Datos, decisiones y pruebas | M2-17 precios de venta y P01/P02 margen mínimo | F3 (precios), F10 (margen mínimo) |
| Datos, decisiones y pruebas | R-S1: faltan plantillas de exportación, LCL y terrestre | F3 (datos), F12 (uso) |
| Datos, decisiones y pruebas | P43: venta única de ALM (D1-D14) | F11 |
| Datos, decisiones y pruebas | Servicios y lecturas de tarifa pendientes (P10/P09, P44, P13, P24, P28, P40/P41/P29/P42) | F3 (y F11 para WFS, F12 para IRENEO) |
| Datos, decisiones y pruebas | M2-I / M2-23: consolidaciones | F16 |
| Datos, decisiones y pruebas | P34: precio cerrado para varios envíos | Solo decisión de Cristina (F3). La construcción queda fuera de este plan salvo que Cristina la exija para el 1/1 |
| Datos, decisiones y pruebas | M2-C: apertura al aceptar o al hacer el booking | F5 |
| Datos, decisiones y pruebas | Reglas de precio por ratificar (M2-B, M2-H, R2-A1, R2-A2, M2-E, FAD por defecto) | F3 (decisión; solo cambian ajustes o datos) |
| Datos, decisiones y pruebas | Congelación de venta y margen de la aceptación al recotizar | F3 |
| Datos, decisiones y pruebas | Visibilidad y portal (P20-P23, P26, P35, P10-A/B, P-9) | F6. P-9 (seguimiento automático) fuera de alcance |
| Datos, decisiones y pruebas | P17 (parte): IVA de CAU y QBR para cliente español | F4 |
| Datos, decisiones y pruebas | P18/P37: cuentas de suplidos y por categoría | F4 |
| Datos, decisiones y pruebas | P03: porcentaje de QBR y facturación en EUR de una oferta en USD | F8, F9 |
| Datos, decisiones y pruebas | P45: SII, VeriFactu o Facturae | F4, F15 |
| Datos, decisiones y pruebas | Ratificaciones contables (P30, P31, P32, P33, P11, P38, P39, A01) | F0 (paquete); F8 (P30, P32), F4 (A01), F10 (P38), F17 (P39). P31, P33 y P11 son solo decisión (el comportamiento ya existe) |
| Datos, decisiones y pruebas | Contenido legal de los documentos (ADR-011) y lista de documentos operativos | F4 (menciones), F7 (lista de documentos operativos) |
| Datos, decisiones y pruebas | Otras decisiones de Ángel (M2-D, M2-G, M2-J) | F3 (solo decisión) |
| Datos, decisiones y pruebas | dev/uat_e2e.py no funciona en boss20 | F1 |
| Datos, decisiones y pruebas | El E2E no cubre cierres, eventos, documentos, PDF, USD/QBR, otros tráficos ni cancelación | F1 (arnés), F10 (S1 completo), F11, F12, F13 |
| Datos, decisiones y pruebas | Las pruebas Odoo no se ejecutan desde el 27/10 y cuatro módulos no tienen ninguna | F1 (la regresión pasa a los check_*.py en boss20; decisión de Belal) |
| Datos, decisiones y pruebas | Capacidad: −59 h en S45 y −43 h en S46 | F0 (decisión de Belal) |

