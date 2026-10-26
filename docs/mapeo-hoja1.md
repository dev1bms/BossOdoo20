# Mapeo de Hoja1 («Plan detallado previsiones») con el sistema · Hoja1 mapping

**Revisión del 26/10/2026.** Entorno comprobado: boss20 (https://system.bosscontinental.com), módulos instalados
iguales al commit `8ec4a2c` (boss_services 20.0.1.2.0, boss_pricing 20.0.1.5.0, boss_pricing_sale 20.0.1.7.0,
boss_expediente 20.0.1.3.0); código local en `e04500f` (main). Lecturas de boss20 **solo lectura**
(`dev/hoja1_probe.py`, `dev/tariff_review_probe.py`, `dev/readiness_probe.py`, deshechas al terminar). Ningún dato de
boss20 se ha cambiado para esta revisión. El fichero de Cristina no se ha modificado.

**Fuente.** `Boss Continental - IT\NEW ODOO\Plan detallado previsiones.xlsx`, hoja `Hoja1` (creado por Cristina el
02/10/2026 10:38; última modificación de Belal 08/10/2026 12:28). Hay otra copia, `Plan detallado previsiones - estado
07-10-2026 By Belal.xlsx`, hoja `Plan original`: **idéntica celda a celda** (comprobado el 26/10) y con tres hojas de
estado del 07/10 (Odoo 19). La versión de referencia es la de Cristina (Hoja1). Hoja1 tiene 12 celdas de contenido
(A7:E10), sin filas ni columnas ocultas, sin comentarios. Las cabeceras dicen «s45/s46, Octubre/Noviembre, días
5–9 y 12–16»: son los días 5–8 de octubre de 2026 (semanas ISO 41–42); el error de etiqueta ya estaba anotado el 21/10.

**Estados.** *Completo* = la operación funciona en boss20 con datos reales y está probada. *Parcial* = configurado o
funcionando con muestras, pero falta tarifa real aprobada, un dato o una decisión. *No implementado* = no existe en
el sistema o depende de una decisión no tomada. *No verificado* = no se ha podido comprobar el comportamiento.
Tener un campo o una opción en pantalla no cuenta como «Completo».

**Pruebas comunes** (aplican a varias filas): motor de cálculo 21/21 pruebas unitarias (`addons/boss_pricing/engine/tests`);
prueba de referencias R1–R27 con las muestras reales privadas en una BD desechable (`boss_pricing` tests, 23/10/2026,
0 fallos); ofertas [DEMO] en boss20 (S00009–S00021) con tarifas [DEMO]; ensayo de la hoja de Ángel en la copia local
(26/10, deshecho). Ninguna tarifa real está aprobada (10 esperando aprobación, P19): **por eso ninguna fila de la 7 a
la 10 puede ser «Completo» hoy**.

## Requisitos (28) · Requirements

Tareas: códigos de https://task.bosscontinental.com (columna «Tareas»; enlaces en la sección final).

### Fila 7 · «Configuración forma de cálculo 20 códigos principales» (A7:E7)

| Id | Celda | Texto original | Dónde en el sistema | Estado | Probado | Evidencia | Falta / decisión | Tareas |
|---|---|---|---|---|---|---|---|---|
| H1-01 | B7 | «T3 tax» | Servicio T3 (tasa portuaria, por unidad) y T3-PAD (PAD con T3 incluido, por contenedor y tamaño) en Tarifas → Servicios; motor `per_unit` | Parcial | Motor; R2 (T3-PAD MSC p.12) en BD desechable | boss20: T3 modo tarifa, sin precio real; T3-PAD con precio MSC (esperando aprobación, válido 09–12/2026) | Aprobación MSC (Cristina); gastos locales Hapag y otras navieras; T3 de grupaje (proveedor y precio) | BOSS20-D01, BOSS20-D02, BOSS20-C01 |
| H1-02 | B7 | «FAD» | Servicio FAD (despacho de importación, por despacho) | Parcial | Motor (`per_unit`) | boss20: configurado, sin tarifa (Aducex, Ramos Vila). Cristina 28/09: el operador elige el agente, sin elección automática | Tarifas Aducex y Ramos Vila (caso varias partidas) | BOSS20-D01, BOSS20-D02 |
| H1-03 | B7 | «DEX» | Servicio DEX (despacho de exportación) | Parcial | Motor | boss20: configurado, sin tarifa | Quién despacha la exportación y su tarifa por DUA | BOSS20-D01 |
| H1-04 | B7 | «THC-LCL» | Servicio THC-LCL, método «mayor de dos bases» (t × precio, m³ × precio) | Parcial | Motor (`max_of_bases`) | boss20: configurado, sin tarifa (CFS Transglory) | Tarifa del CFS | BOSS20-D01 |
| H1-05 | B7 | «THC-FCL» | Servicio THC por contenedor; tarifa [MUESTRA] MSC gastos locales (origen China) | Parcial | R1 en BD desechable; ofertas [DEMO] S00009/S00012 en boss20 | boss20: precio MSC esperando aprobación; THC de Hapag y otras navieras sin cargar | Aprobación (Cristina); gastos locales Hapag | BOSS20-C01, BOSS20-D01 |
| H1-06 | B7 | «PFT» | PFT-AIR (€/kg), PFT-FCL (€/contenedor), PFT-LCL (€/m³ con mín./máx.); nunca se venden (P12) | Parcial | Motor | boss20: tres servicios configurados, sin acuerdos de agentes | Acuerdos PFT de los agentes en origen | BOSS20-D01 |
| H1-07 | B7 | «ROHS» | Servicio ROH (por documento) | Parcial | Motor | boss20: configurado, sin precio | Proveedor y precio por documento | BOSS20-D01 |
| H1-08 | B7 | «SOI» | Servicio SOI (inspección SOIVRE, por documento) | Parcial | Motor | Ídem | Ídem | BOSS20-D01 |
| H1-09 | B7 | «INS» | Servicio INS (por documento) | Parcial | Motor | Ídem | Ídem | BOSS20-D01 |
| H1-10 | B7 | «SAN» | Servicio SAN (por documento) | Parcial | Motor | Ídem | Ídem | BOSS20-D01 |
| H1-11 | B7 | «VET» | Servicio VET: modo «pendiente de decisión» (P16) | No implementado | — | boss20: `boss_pricing_mode = pending`, pregunta P16 | Cristina: ¿inspección veterinaria en PIF por documento como SAN? proveedor y precio | BOSS20-C02 |
| H1-12 | C7 | «GLO (cntr) gastos locales estandar que tarifican por contenedor» | Servicio GLO-CCC (por contenedor DV/HC), tarifa MSC p.12 | Parcial | R5 en BD desechable | boss20: precio MSC esperando aprobación | Aprobación; otras navieras | BOSS20-C01, BOSS20-D01 |
| H1-13 | C7 | «GLO (doc) gastos locales estandar que tarifican por [documento]» | Servicios GLO (genérico) y GLO-LOG por unidad; sin tarifa | Parcial | Motor | boss20: configurados, sin precio real; el 07/10 Cristina tenía pendiente decidir qué GLO por documento se proponen solos | Decisión de Cristina + documento | BOSS20-C02, BOSS20-D01 |
| H1-14 | C7 | «MSC import Far East tiene un GLO que aplica por TEU que hay que asociar a paises de Far East» | Servicio GLO-FUELEU por TEU; tarifa MSC limitada a origen China (P24) | Parcial | R3 en BD desechable | boss20: precio MSC esperando aprobación; condición de origen solo China | Lista de países «Lejano Oriente» (Cristina, P24) | BOSS20-C02, BOSS20-C01 |
| H1-15 | D7 | «DEM» | Servicio DEM, método por tiempo (días libres, tramos relativos o por número de día); tarifas MSC, CMA CGM, Hapag-Lloyd | Parcial | R8/R9 (MSC), R16 (Hapag), R18 (CMA) en BD desechable; recálculo en expediente (test ALM 5→9 días; E260002) | boss20: tres tarifas esperando aprobación | Aprobación; vigencia 2026 de CMA y Hapag (documentos de 2025) | BOSS20-C01 |
| H1-16 | D7 | «OCU» | Servicio OCU por tiempo; MSC Valencia (4 días libres) y Barcelona (5) | Parcial | R11/R12 | boss20: dos tarifas esperando aprobación | Aprobación; HC/reefer | BOSS20-C01 |
| H1-17 | D7 | «DET» | Servicio DET: modo «pendiente de decisión» (P09) | No implementado | — | boss20: `pending`; Hapag la cobra dentro de DEM; MSC detention de exportación sin cargar | Cristina: ¿código propio o dentro de DEM? Documento MSC export | BOSS20-C02, BOSS20-B03 |
| H1-18 | E7 | «TTE-FCL» | Servicio TTE-FCL, método por tramos (`brackets`) | Parcial | Motor | boss20: configurado, sin tarifa | Tarifa de transporte de contenedor | BOSS20-D01 |
| H1-19 | E7 | «CES» | Servicio CES por unidad (ejemplo de «sin precio de proveedor» en la guía) | Parcial | Motor; paso «Añadir precio de proveedor» de la guía | boss20: configurado, sin tarifa (MSC 01/09 no la trae) | Tarifa de cesión por naviera | BOSS20-D01 |
| H1-20 | E7 | «TTE-CON (convencional)» | Servicio TTE-CON, tramos por kg tasable y provincia; IRENEO zona 3 2025 y **versión 2026** (`dev/setup_ireneo_2026.py`: líneas de transporte × 1,10 desde el 15/07/2026, documento = carta de IRENEO del 14/07/2026) | Parcial | R12 (IRENEO p.6-7,16) | boss20: tarifa 2025 caducada; versión 2026 enviada a aprobación con la carta adjunta (26/10) | Aprobación de Cristina de la versión 2026 (el handling HAN/X-R aéreo no lo cubre la carta: P28 reducida a eso) | BOSS20-C03 |

### Fila 8 · «Configuración campos expedientes» (A8:D8)

| Id | Celda | Texto original | Dónde en el sistema | Estado | Probado | Evidencia | Falta / decisión | Tareas |
|---|---|---|---|---|---|---|---|---|
| H1-21 | C8 | «campos ATA, fecha y hora NOA en los E» | Expediente: ATA, NOA, Recogida real, ATD, FOH, Entrega real con **fecha y hora** (`Datetime`); el periodo real de cada servicio por tiempo (ALM, DEM, OCU) se rellena desde ellas (importación: NOA o ATA → Recogida; exportación: FOH → ATD) salvo que una persona lo haya tecleado (`period_manual`) | Completo (pendiente de verificar en boss20) | Test `test_file_dates_set_the_actual_period_and_recompute` (servidor, BD desechable, commit d86cded/2feb285) | boss20: pendiente de despliegue de 20.0.1.5.0 | Verificación en boss20 (V01) | BOSS20-F01 |
| H1-22 | D8 | «Añadir fechas necesarias para que todos los conceptos configurados hasta esta semana se puedan calcular automáticamente» | Al cambiar ATA/NOA/FOH/ATD/Recogida el expediente recalcula el coste previsto con el motor (evento en el historial, motivo «File dates changed»); la fecha de tarifa es la real (ATA/ATD) o la estimada | Parcial | Mismo test que H1-21 | Funciona para los códigos con tarifa aprobada; sin tarifas aprobadas no hay cálculo real | Aprobación de tarifas (C01) + verificación (V01) | BOSS20-F01, BOSS20-C01 |

### Fila 9 · «Configuración asociación de aerolíneas con handlings en cada aeropuerto» (A9:C9)

| Id | Celda | Texto original | Dónde en el sistema | Estado | Probado | Evidencia | Falta / decisión | Tareas |
|---|---|---|---|---|---|---|---|---|
| H1-23 | B9 | «Crear campos dentro de los handling o de las aerolíneas que permitan asociarlos entre ellos» | Modelo `boss.airline.handler` (aerolínea, aeropuerto, handler, código AWB, origen del dato), menú Expedientes → «Aerolíneas y handlers» (compras / jefe de ventas), lista editable, agrupada por aeropuerto | Completo (pendiente de verificar en boss20) | Test `test_handler_of_the_airline_at_the_airport` (servidor) | boss20: pendiente de despliegue | Verificación en boss20 (V01); Cristina valida la lista (C04) | BOSS20-F02 |
| H1-24 | C9 | «Añadir campo aerolinea y handling en los expedientes estando emparejados entre ellos y con el campo de aeropuerto» | Expediente: `handler_id` (solo aéreo) propuesto desde la asociación al crear el expediente o cambiar aerolínea/aeropuerto; con varios handlers conocidos el campo solo ofrece esos y el usuario elige; las necesidades HAN/ALM/AWB/ETX/X-R toman el handler como proveedor; en la oferta, la línea de esos servicios toma el handler como proveedor cuando hay uno solo | Completo (pendiente de verificar en boss20) | Mismo test | boss20: pendiente de despliegue | Verificación en boss20 (V01) | BOSS20-F02 |

### Fila 10 · «Alimentación del sistema» (A10:E10)

| Id | Celda | Texto original | Dónde en el sistema | Estado | Probado | Evidencia | Falta / decisión | Tareas |
|---|---|---|---|---|---|---|---|---|
| H1-25 | B10 | «conceptos HAN, ETX, ALM, AWB para Importación aérea de 2 almacenes de handling» | Tarifa [MUESTRA] WFS importación MAD/BCN: HAN, ALM, AWB; ETX pendiente de decisión (P10); 2.º handler sin cargar | Parcial | R01–R06, R09a (WFS) en BD desechable; recálculo ALM en E260002 | boss20: WFS esperando aprobación; ETX `pending`; ningún segundo handler | Aprobación WFS; ETX = «Tasa Energética» del handler, vendida por envío (oferta real a Cofitel del 03/02/2026); falta su coste de compra (por AWB máster, Cristina 08/10) y el documento; documento del 2.º handler (IAS o SAASA) | BOSS20-C01, BOSS20-B03, BOSS20-D03 |
| H1-26 | C10 | «Extraer listado de aerolinea/ aeropuerto/handling. Asociación de todas las aerolineas utilizadas hasta la fecha según registros de Odoo con su handling correspondiente» | Leído de Odoo 17 (`x_handlingconfig`, 47 filas, 26/10/2026) y cargado como datos del módulo: 37 aerolíneas, 6 handlers (WFS, Swissport, Iberia, IAS, ACL, Groundforce) con `ref` O17:id, 46 relaciones en MAD, BCN, VLC, AGP, BIO (`data/boss_airline_handler_data.xml`) | Completo (pendiente de validar) | Carga en BD desechable del servidor | boss20: pendiente de despliegue | Cristina valida la lista (C04): la fila archivada #29 de Odoo 17 duplicaba una activa y no se carga | BOSS20-F03 |
| H1-27 | D10 | «conceptos HAN, ETX, ALM, AWB para Exportación aérea de los mismos 2 almacenes de handling ya cargados» | Tarifa [MUESTRA] WFS exportación PNS: ALM y X-R; sin HAN ni AWB de exportación; ETX pendiente | Parcial | R01–R05, R10c | boss20: WFS exportación esperando aprobación | HAN y AWB de exportación de WFS (documento), ETX, 2.º handler | BOSS20-D03, BOSS20-C01 |
| H1-28 | E10 | «Cargar tarifas de OCU/DEM/DET para importación con ONE, MSK, ZIM, OOCL, MSC» | DEM/OCU de MSC cargadas (y CMA CGM, Hapag-Lloyd fuera de la lista); ONE, MSK, ZIM, OOCL sin cargar; DET pendiente | Parcial | R8–R18 | boss20: 1 de las 5 navieras pedidas; 2 adicionales | Documentos D&D de ONE, MSK, ZIM y OOCL; decisión DET | BOSS20-D02, BOSS20-C02 |

## Resumen · Summary

| Estado | Requisitos |
|---|---|
| Completo (pendiente de verificar en boss20) | 4 (H1-21, H1-23, H1-24, H1-26) |
| Parcial | 22 (H1-01 a H1-10, H1-12 a H1-16, H1-18 a H1-20, H1-22, H1-25, H1-27, H1-28) |
| No implementado | 2 (H1-11, H1-17) |
| No verificado | 0 |

Lo que convierte un «Parcial» en «Completo» es, en casi todos los casos, **un documento del proveedor y la aprobación
de Cristina** (P19), no desarrollo: el motor, los métodos y el expediente ya están. Las excepciones que sí son
desarrollo eran H1-21 (NOA/ATA con hora), H1-23/H1-24 (aerolínea ↔ handler) y H1-26 (extracción de Odoo 17): hechas el
26/10/2026 (commits 593c320, d86cded, 2feb285), a la espera de despliegue y verificación en boss20. Quedan las decisiones
H1-11, H1-13, H1-14, H1-17.

## Qué falta exactamente por requisito · What is missing, by kind

Tipos: **desarrollo**, **datos**, **documentos**, **decisión/aprobación**, **prueba** (toda falta termina con la prueba del escenario y la verificación en boss20, tareas D04, V01 y Q03).

| Id | Qué falta |
|---|---|
| H1-01 | Documentos (Hapag, T3 grupaje) + aprobación (MSC) + prueba de escenario |
| H1-02 | Documentos (Aducex, Ramos Vila) + aprobación + prueba |
| H1-03 | Documentos (agente export) + aprobación + prueba |
| H1-04 | Documentos (CFS) + aprobación + prueba |
| H1-05 | Aprobación (MSC) + documentos (otras navieras) + prueba de escenario |
| H1-06 | Datos (acuerdos PFT) + aprobación + prueba |
| H1-07 | Documentos + aprobación + prueba |
| H1-08 | Documentos + aprobación + prueba |
| H1-09 | Documentos + aprobación + prueba |
| H1-10 | Documentos + aprobación + prueba |
| H1-11 | Decisión (Cristina, P16) + desarrollo/configuración (B05) + prueba |
| H1-12 | Aprobación (MSC) + prueba |
| H1-13 | Decisión (Cristina) + documentos + prueba |
| H1-14 | Datos (lista Lejano Oriente) + aprobación + prueba |
| H1-15 | Aprobación (3 navieras) + confirmación de vigencia 2026 + prueba |
| H1-16 | Aprobación + prueba |
| H1-17 | Decisión (Cristina, P09) + documento MSC export + desarrollo (B03) + prueba |
| H1-18 | Documentos + aprobación + prueba |
| H1-19 | Documentos + aprobación + prueba |
| H1-20 | E7 | «TTE-CON (convencional)» | Servicio TTE-CON, tramos por kg tasable y provincia; IRENEO zona 3 2025 y **versión 2026** (`dev/setup_ireneo_2026.py`: líneas de transporte × 1,10 desde el 15/07/2026, documento = carta de IRENEO del 14/07/2026) | Parcial | R12 (IRENEO p.6-7,16) | boss20: tarifa 2025 caducada; versión 2026 enviada a aprobación con la carta adjunta (26/10) | Aprobación de Cristina de la versión 2026 (el handling HAN/X-R aéreo no lo cubre la carta: P28 reducida a eso) | BOSS20-C03 |
| H1-21 | C8 | «campos ATA, fecha y hora NOA en los E» | Expediente: ATA, NOA, Recogida real, ATD, FOH, Entrega real con **fecha y hora** (`Datetime`); el periodo real de cada servicio por tiempo (ALM, DEM, OCU) se rellena desde ellas (importación: NOA o ATA → Recogida; exportación: FOH → ATD) salvo que una persona lo haya tecleado (`period_manual`) | Completo (pendiente de verificar en boss20) | Test `test_file_dates_set_the_actual_period_and_recompute` (servidor, BD desechable, commit d86cded/2feb285) | boss20: pendiente de despliegue de 20.0.1.5.0 | Verificación en boss20 (V01) | BOSS20-F01 |
| H1-22 | D8 | «Añadir fechas necesarias para que todos los conceptos configurados hasta esta semana se puedan calcular automáticamente» | Al cambiar ATA/NOA/FOH/ATD/Recogida el expediente recalcula el coste previsto con el motor (evento en el historial, motivo «File dates changed»); la fecha de tarifa es la real (ATA/ATD) o la estimada | Parcial | Mismo test que H1-21 | Funciona para los códigos con tarifa aprobada; sin tarifas aprobadas no hay cálculo real | Aprobación de tarifas (C01) + verificación (V01) | BOSS20-F01, BOSS20-C01 |
| H1-23 | B9 | «Crear campos dentro de los handling o de las aerolíneas que permitan asociarlos entre ellos» | Modelo `boss.airline.handler` (aerolínea, aeropuerto, handler, código AWB, origen del dato), menú Expedientes → «Aerolíneas y handlers» (compras / jefe de ventas), lista editable, agrupada por aeropuerto | Completo (pendiente de verificar en boss20) | Test `test_handler_of_the_airline_at_the_airport` (servidor) | boss20: pendiente de despliegue | Verificación en boss20 (V01); Cristina valida la lista (C04) | BOSS20-F02 |
| H1-24 | C9 | «Añadir campo aerolinea y handling en los expedientes estando emparejados entre ellos y con el campo de aeropuerto» | Expediente: `handler_id` (solo aéreo) propuesto desde la asociación al crear el expediente o cambiar aerolínea/aeropuerto; con varios handlers conocidos el campo solo ofrece esos y el usuario elige; las necesidades HAN/ALM/AWB/ETX/X-R toman el handler como proveedor; en la oferta, la línea de esos servicios toma el handler como proveedor cuando hay uno solo | Completo (pendiente de verificar en boss20) | Mismo test | boss20: pendiente de despliegue | Verificación en boss20 (V01) | BOSS20-F02 |
| H1-25 | Aprobación (WFS) + decisión ETX (B03) + documento 2.º handler (D03) + prueba |
| H1-26 | C10 | «Extraer listado de aerolinea/ aeropuerto/handling. Asociación de todas las aerolineas utilizadas hasta la fecha según registros de Odoo con su handling correspondiente» | Leído de Odoo 17 (`x_handlingconfig`, 47 filas, 26/10/2026) y cargado como datos del módulo: 37 aerolíneas, 6 handlers (WFS, Swissport, Iberia, IAS, ACL, Groundforce) con `ref` O17:id, 46 relaciones en MAD, BCN, VLC, AGP, BIO (`data/boss_airline_handler_data.xml`) | Completo (pendiente de validar) | Carga en BD desechable del servidor | boss20: pendiente de despliegue | Cristina valida la lista (C04): la fila archivada #29 de Odoo 17 duplicaba una activa y no se carga | BOSS20-F03 |
| H1-27 | Documentos (HAN/AWB export WFS, 2.º handler) + aprobación + prueba |
| H1-28 | Documentos (ONE, MSK, ZIM, OOCL) + decisión DET + aprobación + prueba |

## Tareas en la plataforma · Tasks

Tareas creadas el 26/10/2026 en https://task.bosscontinental.com (plan `seed_launch`, 99 tareas; plan semanal en https://task.bosscontinental.com/gantt/):

| Código | Tarea | Enlace |
|---|---|---|
| BOSS20-C01 | Cristina: revisión y aprobación de las 10 tarifas de muestra (P19) y ratificación de las lecturas WFS | https://task.bosscontinental.com/tareas/220/ |
| BOSS20-C02 | Cristina: decisiones pendientes de servicios (VET, GLO por documento, Lejano Oriente, DET, ETX, ALM D1–D7, numeración) | https://task.bosscontinental.com/tareas/221/ |
| BOSS20-C03 | Cristina: tarifa IRENEO 2026 o confirmación escrita (P28) | https://task.bosscontinental.com/tareas/222/ |
| BOSS20-D01 | Reunir los documentos de tarifa que faltan (lista del 07/10) | https://task.bosscontinental.com/tareas/223/ |
| BOSS20-D02 | Cargar y enviar a aprobación las tarifas recibidas (lote 1: navieras y aduanas) | https://task.bosscontinental.com/tareas/226/ |
| BOSS20-D03 | Cargar el segundo handler aéreo y los códigos de exportación aérea | https://task.bosscontinental.com/tareas/236/ |
| BOSS20-B03 | Fase B3: ETX y DET | https://task.bosscontinental.com/tareas/230/ |
| BOSS20-F01 | Campos NOA y ATA con fecha y hora en el expediente | https://task.bosscontinental.com/tareas/227/ |
| BOSS20-F02 | Aerolínea y handling en el expediente, emparejados con el aeropuerto | https://task.bosscontinental.com/tareas/228/ |
| BOSS20-F03 | Extraer de Odoo 17 la lista aerolínea / aeropuerto / handling | https://task.bosscontinental.com/tareas/224/ |
| BOSS20-B05 | VET: configurar tras la decisión de Cristina, con ejemplo de referencia | https://task.bosscontinental.com/tareas/276/ |
| BOSS20-V01 | Verificación en boss20 de Hoja1 filas 8–10 (NOA/ATA, aerolínea↔handler, lista Odoo 17) | https://task.bosscontinental.com/tareas/277/ |
| BOSS20-X01 | Excepción de coste manual para servicios sin tarifa en la entrega: aprobación de Belal | https://task.bosscontinental.com/tareas/275/ |
