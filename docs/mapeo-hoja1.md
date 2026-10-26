# Mapeo de Hoja1 («Plan detallado previsiones») con el sistema · Hoja1 mapping

**Revisión del 26/10/2026 (noche).** boss20 y boss20_uat con boss_services 20.0.1.3.0, boss_pricing 20.0.1.6.0,
boss_pricing_sale 20.0.1.7.0, boss_expediente 20.0.1.7.0 (código del commit `7143284`, desplegado el 26/10).
Mandato de Belal (26/10): ejecutar literalmente lo que pide el Excel sin volver a consultarle, con las referencias
confirmadas; las aprobaciones de tarifas siguen siendo de Cristina.

**Fuente.** `Boss Continental - IT\NEW ODOO\Plan detallado previsiones.xlsx` (autora Cristina, creado el 02/10/2026;
**última modificación: Belal, 26/10/2026 13:30**, que añadió la celda F6 «Note» sin requisito). Dos hojas visibles:
`Hoja1` (12 celdas de requisito, A7:E10) y `Explicaciones previsiones` (respuestas de Cristina, A3:A148). La copia
`… estado 07-10-2026 By Belal.xlsx` (hoja «Plan original») coincide celda a celda salvo F6. Las cabeceras «s45/s46,
Octubre/Noviembre, 5–9 y 12–16» corresponden al 5–16 de octubre (semanas ISO 41–42).

**Estados** (una fila puede tener varios aspectos):
- **Hecho** — lo que pide la celda está implementado y probado (prueba automática en el servidor, comprobación en
  boss20_uat o en la interfaz desde Chrome).
- **Hecho, falta aprobación** — tarifa cargada desde el documento del proveedor, esperando la aprobación de Cristina
  (una tarifa sin aprobar nunca valora una oferta).
- **Bloqueado: sin documento** — el documento no existe en ninguna de las fuentes buscadas (lista al final).
- **Parcial** — una parte hecha; lo que falta está dicho.

**Pruebas comunes:** Odoo 36/36 en BD desechable del servidor (boss_services, boss_pricing, boss_pricing_sale,
boss_expediente) y 20/20 de boss_expediente tras el último cambio; motor 23/23 en el servidor
(`dev/server_test.sh --engine`); ciclo completo `dev/uat_e2e.py` **64/64** y escenarios `dev/uat_scenarios.py` **31/31** en
boss20_uat (evidencias con el commit en `docs/evidencias/`); recorrido en la interfaz desde Chrome en boss20 (S00031 →
E260015, 26/10).

## Fila 7 · «Configuración forma de cálculo 20 códigos principales»

La celda pide **configurar la forma de cálculo** de cada código; los precios los pide la fila 10.

| Id | Celda | Texto literal | Forma de cálculo en el sistema | Estado | Prueba | Precio real (documento) |
|---|---|---|---|---|---|---|
| H1-01 | B7 | «T3 tax» | T3 por tonelada (exacta o «o fracción») o por tipo de contenedor; T3-PAD por contenedor (Explicaciones A100–A108) | Hecho | Motor (unidades, redondeo por fracción); R2 MSC | MSC T3-PAD 01/09/2026: Hecho, falta aprobación. Hapag y T3 de grupaje: Bloqueado: sin documento |
| H1-02 | B7 | «FAD» | Por despacho (DUA) y número de contenedores: Aducex 66 € con 1 contenedor / 75 € con 2+; Ramos Vila 66 € + 26 € por contenedor adicional hasta 170 € (A111–A118, A33). El operador elige el agente (A33) | Hecho | Motor `test_customs_clearance_by_number_of_containers` (servidor, 23/23) | Tarifas Aducex y Ramos Vila cargadas desde las respuestas de Cristina (`dev/setup_fad_tariffs.py`): Hecho, falta aprobación. «59 € por partida» (A120): a confirmar con Laura según la propia celda, no cargado |
| H1-03 | B7 | «DEX» | Por juego de documentos/partida, igual en FCL, LCL y aéreo (A122–A125) | Hecho | Motor; S3 (UAT) | Agente de exportación: Bloqueado: sin documento (solo MSC «servicios MSC» 37 €/DUA, que no es el agente) |
| H1-04 | B7 | «THC-LCL» | El mayor de toneladas × precio y m³ × precio (A42–A44, A87) | Hecho | Motor `max_of_bases`; S2 (UAT): cantidad W/M 4,5 | CFS Transglory: Bloqueado: sin documento (carpeta vacía) |
| H1-05 | B7 | «THC-FCL» | Por contenedor, tamaño y tipo | Hecho | S1 y ciclo E2E (UAT); Chrome S00031 (180 € 20' DV, 240 € 40' HC) | MSC 01/09/2026: Hecho, falta aprobación. Otras navieras: solo licitación Leroy (THC, hoja «THC Y POSICIONADOS»), no cargada como THC general |
| H1-06 | B7 | «PFT» | PFT-AIR €/kg, PFT-FCL €/contenedor, PFT-LCL €/m³ con mínimo y máximo (A141); el agente puede no conocerse al cotizar (A51–A52) | Hecho | Motor | Acuerdos con agentes: Bloqueado: sin documento |
| H1-07 | B7 | «ROHS» (código ROH, A55) | Por documento; el agente de aduanas dice cuántos y el operativo los mete a mano (A55–A56) | Hecho | Motor; S2 (SOI por documento) | Precio por documento: Bloqueado: sin documento (solo PrevAdder y facturas de Odoo 17) |
| H1-08 | B7 | «SOI» | Ídem | Hecho | S2 (UAT) | Ídem |
| H1-09 | B7 | «INS» | Ídem | Hecho | Motor | Ídem |
| H1-10 | B7 | «SAN» | Ídem | Hecho | Motor | Ídem |
| H1-11 | B7 | «VET» | Coste manual por documento como SAN: coste del veterinario + 20 % del handler (WFS ítem 54; propuesta del 07/10 aplicada, P16) | Hecho | Migración boss_services 20.0.1.3.0 desplegada | Coste real del veterinario: se escribe en cada expediente (no hay tarifa) |
| H1-12 | C7 | «(*) GLO (cntr) gastos locales estandar que tarifican por contenedor» | GLO-CCC por contenedor | Hecho | R5; S1 (UAT) | MSC 01/09/2026: Hecho, falta aprobación |
| H1-13 | C7 | «GLO (doc) gastos locales estandar que tarifican por contenedor» (sic: la celda repite «por contenedor»; la fila es la de los GLO por documento) | GLO y GLO-LOG por documento/unidad; ninguno se propone solo en la plantilla (propuesta 07/10 aplicada) | Hecho | Plantilla [DEMO] IMB FOB sin GLO por documento | Partidas por B/L de MSC (págs. 4 y 13–14) en el documento: Parcial (no cargadas como GLO por documento) |
| H1-14 | C7 | «ej MSC import Far East tiene un GLO que aplica por TEU que hay que asociar a paises de Far East» | GLO-FUELEU por TEU con condición de país de origen | Hecho | S1 (UAT): 2×20' + 1×40' = 4 TEU × 25 € [DEMO] | MSC FuelEU: China (gastos locales) + resto de la lista propuesta del 07/10 (Hong Kong, Taiwán, Japón, Corea del Sur, Vietnam, Tailandia, Malasia, Singapur, Indonesia, Filipinas, Camboya; `dev/setup_fueleu_far_east.py`): Hecho, falta aprobación |
| H1-15 | D7 | «DEM» | Por tiempo y contenedor: días libres, tramos; **periodo propio de cada tarifa** (MSC: llegada del buque → devolución del vacío, p.18; Hapag: descarga → devolución) con fechas de cada contenedor | Hecho | Prueba `test_each_time_service_follows_its_own_period_events`; E2E (DEM 20' 60 €, 40' 390 €); Chrome E260015 | MSC, Hapag, CMA (documentos) y ONE, Maersk, OOCL, MSC (licitación Leroy, solo ese cliente): Hecho, falta aprobación |
| H1-16 | D7 | «OCU» | Por tiempo y contenedor; MSC: llegada del buque → salida del lleno (p.17) | Hecho | Misma prueba (OCU 40 €) | MSC VLC/BCN y licitación Leroy (ONE, Maersk, OOCL, MSC): Hecho, falta aprobación |
| H1-17 | D7 | «DET» | Por tiempo y contenedor: retirada del vacío → entrada del lleno (MSC exportación p.10); dentro de DEM cuando va combinada (Hapag MHD/DTD); propuesta 07/10 aplicada (P09) | Hecho | Migración desplegada; regla por defecto en el código con la fuente | Detention de exportación MSC: el documento existe (p.10) pero es de exportación; no cargado |
| H1-18 | E7 | «TTE-FCL» | Por tramos / por contenedor | Hecho | E2E (precio [DEMO] por contenedor) | Transportista de contenedor: Bloqueado: sin documento (solo `pricing terrestre.ods` de 2023, obsoleto) |
| H1-19 | E7 | «CES» | Por contenedor, puerto e importación/exportación, solo FCL (A96–A97) | Hecho | S4 (sin precio → no se valora a 0) | CES por naviera: Bloqueado: sin documento (el PDF MSC 01/09 no la trae) |
| H1-20 | E7 | «TTE-CON (convencional)» | Tramos por kg tasable (factor 333) y provincia | Hecho | R12; `dev/setup_ireneo_2026.py` comprueba la tarifa base contra el PDF (28/28 escalones, 15 provincias) | IRENEO zona 3: 2025; 2026 a precios 2025 hasta el 14/07 (Ángel 14/10/2026, referencia de Odoo 19); +10 % desde el 15/07/2026 (carta de IRENEO del 14/07/2026, identificada por SHA-256): Hecho, falta aprobación |

## Fila 8 · «Configuración campos expedientes»

| Id | Celda | Texto literal | En el sistema | Estado | Prueba |
|---|---|---|---|---|---|
| H1-21 | C8 | «campos ATA, fecha y hora NOA en los E» | ATA, NOA, FOH, ATD, recogida y entrega reales con fecha y hora; además descarga del buque y vaciado LCL | Hecho | Pruebas del servidor; Chrome: E260015 ATA «Nov 10, 8:00 AM» guardada y releída |
| H1-22 | D8 | «Añadir fechas necesarias para que todos los conceptos configurados hasta esta semana se puedan calcular automáticamente» | Fechas de cada contenedor (retirada del vacío, entrada del lleno, salida del lleno, devolución del vacío); cada servicio por tiempo toma el inicio y el fin de **su** tarifa o, si no los indica, los de su servicio (ALM aéreo NOA/ATA → retirada; ALM LCL vaciado → retirada; DEM llegada → devolución del vacío; OCU llegada → salida del lleno; exportación FOH/entrada del lleno → salida; DET retirada del vacío → entrada del lleno); periodo escrito a mano respetado | Hecho | `test_each_time_service_follows_its_own_period_events` (servidor); E2E 64/64; Chrome E260015 |

## Fila 9 · «Configuración asociacion de aerolíneas con handlings en cada aeropuerto»

| Id | Celda | Texto literal | En el sistema | Estado | Prueba |
|---|---|---|---|---|---|
| H1-23 | B9 | «Crear campos dentro de los handling o de las aerolíneas que permitan asociarlos entre ellos» | Tabla «Aerolíneas y handlers» (aerolínea, aeropuerto, handler, prefijo AWB, origen) | Hecho | Prueba del servidor; Chrome: menú con 47 relaciones |
| H1-24 | C9 | «Añadir campo aerolinea y handling en los expedientes estando emparejados entre ellos y con el campo de aeropuerto» | Campo Handler del expediente propuesto u ofrecido según aerolínea y aeropuerto; los servicios HAN/ALM/AWB/ETX/X-R lo toman como proveedor | Hecho | Prueba del servidor; S7 (UAT); Chrome: Cathay → WFS, Qatar → Iberia |

## Fila 10 · «Alimentación del sistema»

| Id | Celda | Texto literal | En el sistema | Estado |
|---|---|---|---|---|
| H1-25 | B10 | «conceptos HAN, ETX, ALM, AWB para Importación aérea de 2 almacenes de handling» | WFS importación MAD/BCN 01/06/2026: HAN (ítem 12), ALM (ítem 1), AWB (ítem 10), **ETX (ítem 49, 31 €/AWB, solo importación; cargado el 26/10 desde el PDF identificado)** | WFS: Hecho, falta aprobación. 2.º handler: **Bloqueado: sin documento** (Swissport es el candidato con más compras en Odoo 17; Cristina habla de 5 handlers en Explicaciones A9–A14) |
| H1-26 | C10 | «Extraer listado de aerolinea/ aeropuerto/handling ⏎⏎ Asociación de todas las aerolineas utilizadas hasta la fecha según registros de Odoo con su handling correspondiente» | Odoo 17 `x_handlingconfig`: 48 filas, 47 activas cargadas (MAD 30, BCN 13, AGP 2, VLC 1, BIO 1; la #29 archivada duplicaba una activa) | Hecho (Cristina puede validar la lista). Odoo 19 tenía además 49 pares sacados del código de PrevAdder (incluidos 6 de Alicante), no de los registros de Odoo |
| H1-27 | D10 | «conceptos HAN, ETX, ALM, AWB para Exportación aérea de los mismos 2 almacenes de handling ya cargados» | WFS exportación: ALM (ítem 1), X-R, **HAN exportación (ítem 12, cargado el 26/10)**. ETX: el documento de WFS dice «solo aplicable a la mercancía de importación» y Cristina (07/10) «solo aplica a importación»: no existe en exportación. AWB de exportación: el documento no tiene cargo (solo FWB/FHL si no llega el mensaje) | WFS: Hecho, falta aprobación (ETX y AWB no aplican según el documento). 2.º handler: Bloqueado: sin documento |
| H1-28 | E10 | «Cargar tarifas de OCU/DEM/DET para importación con ONE, MSK, ZIM, OOCL, MSC » | MSC (gastos locales 01/09/2026: DEM y OCU VLC/BCN); ONE, Maersk, OOCL y MSC de la licitación Leroy Merlin 2025/2026 (`dev/setup_leroy_dd.py`, solo para ese cliente); DET de importación no existe en MSC (Hapag la incluye en DEM) | MSC general y Leroy: Hecho, falta aprobación. ONE/Maersk/OOCL para cualquier cliente y **ZIM**: Bloqueado: sin documento |

## Requisitos de la hoja «Explicaciones previsiones»

| Celda | Requisito (Cristina, 28/09/2026) | En el sistema | Estado |
|---|---|---|---|
| A9–A14 | Handlers: WFS, Swissport, IAS, Iberia, SAASA; cada aerolínea va a un handler; costes de los 5 en importación y exportación | Asociación aerolínea ↔ handler; WFS cargado | Parcial: 4 handlers sin documento de tarifa |
| A16–A21 | Transporte interior: «B) TTE – Transporte THIS ONE» | TTE-CON / TTE-FCL | Hecho |
| A23–A26 | GLO = gasto de naviera por contenedor que no sea T3, BL, CES ni DEM/OCU/DET; CES = cesión | Catálogo GLO-*; CES | Hecho. ¿Vender THC + GLO como un concepto? (A25) sin respuesta en el Excel: no se agrupa |
| A27–A37 | FAD: el operador elige el agente; Ramos Vila «66 + 4 x 26 = 170» | Tarifas FAD por número de contenedores | Hecho, falta aprobación |
| A39–A46 | THC LCL por tonelada y por m³ | THC-LCL mayor de dos bases | Hecho (A46 pide la línea exacta de una tarifa: no hay tarifa) |
| A48–A52 | PFT: agente conocido o no al cotizar | PFT con proveedor opcional | Hecho |
| A54–A57 | ROH/SOI/INS/SAN por documento; el operativo mete las previsiones a mano | Unidad «documento», cantidad escrita | Hecho |
| A78–A83 | HAN, ETX, AWB, ALM (almacenaje aéreo **y LCL**) | ALM LCL con vaciado → retirada | Hecho |
| A87 | THC LCL por RT | Mayor de dos bases | Hecho |
| A90–A94 | BL máster por expediente, pagado a la naviera | BL por expediente | Hecho |
| A96–A97 | CES por contenedor, puerto e imp./exp., solo FCL | CES por contenedor con alcance de puerto y sentido | Hecho (sin documento de precio) |
| A100–A108 | T3: LCL por tonelada o fracción / exacta; FCL por tipo de contenedor o por tonelada + gestión | Métodos por unidad con redondeo opcional | Hecho |
| A111–A120 | FAD (ver H1-02) | — | Hecho, falta aprobación; 59 €/P a confirmar con Laura |
| A122–A125 | DEX por juego de documentos | DEX por DUA | Hecho |
| A131 | «Movimiento contenedor: per RT» (A24 decía por contenedor) | Contradicción en el propio Excel: GLO por contenedor (A23–A24) | Parcial: la contradicción no la resuelve el Excel |
| A135–A136 | Transporte: por contenedor; LCL y aéreo por envío, kg, km o ciudad + kg | TTE-FCL por contenedor; TTE-CON por kg y provincia | Hecho |
| A139 | FS: porcentaje sobre el transporte, semanal o mensual | FS método porcentaje sobre servicios del mismo proveedor | Hecho (sin tarifa de FS real) |
| A141 | PFT por kg / contenedor / m³ con mín. y máx. | PFT-AIR/FCL/LCL | Hecho |
| A145 | Cristina quiere meter ella los costes de WFS, Swissport, IAG e IB | Espacio «Tarifas y proveedores» con alta de precios y PDF | Hecho (herramienta) |

«PREVISIONES» (A6) es el título del bloque: el **coste previsto automático** de cada expediente. Ningún libro define un
informe con columnas; la lista de deseos `Nuevo Odoo.xlsx` (hoja «previsiones» A14–A15) pide previsiones estimadas que se
marquen como confirmadas al llegar los documentos: implementado como **«Previsión»** de cada servicio a comprar
(Estimada → Recalculada → Pedida → Confirmada por la factura) y el informe **Expedientes → Previsión de costes**
(pivote por proveedor y previsión), comprobado en Chrome en boss20.

## Resumen y progreso

| Estado | Requisitos de Hoja1 (28) |
|---|---|
| Hecho | 25 (H1-01 a H1-24: forma de cálculo, campos y asociación; H1-26: lista) |
| … de ellos con tarifa real cargada que espera la aprobación de Cristina | H1-01, 02, 05, 12, 14, 15, 16, 20 |
| Parcial (bloqueado por documentos que no existen) | 3: H1-25 y H1-27 (2.º handler), H1-28 (ZIM; ONE/Maersk/OOCL solo para Leroy) |

**Método del porcentaje** (declarado): cada celda de requisito vale 1; «Hecho» = 1; «Hecho, falta aprobación» = 1 para
lo que pide la celda (cargar o configurar) porque la aprobación es una decisión humana fuera del sistema; «Parcial» = la
fracción hecha (H1-25 y H1-27: 1 de 2 handlers = 0,5; H1-28: 4 de 5 navieras, solo para un cliente en 3 de ellas = 0,5).
Resultado: (25 + 0,5 + 0,5 + 0,5) / 28 = **26,5 / 28 ≈ 95 %** de lo que el Excel pide hacer en el sistema. Lo que no
depende del sistema: **0 de 24 tarifas [MUESTRA] aprobadas** (decisión de Cristina).

## Documentos que no existen (búsqueda del 26/10/2026)

Buscado en: `NEW ODOO`, árbol `Boss Continental - IT`, `Boss Continental - OPERACIONES` (aéreo, navieras, Leroy),
`Documents\costs`, `.research` (01–08), `BossOdoo19` (docs, data-src), base de datos de Odoo 19 (`boss_uat`), Odoo 17
(solo lectura). No se encontró: tarifa de un segundo handler (Swissport, IAS, Iberia, SAASA); D&D general de ONE, Maersk,
ZIM y OOCL (solo licitación de Leroy y cálculos antiguos de OOCL de 2022); ZIM en cualquier forma; tarifas de Aducex y
Ramos Vila como documento del proveedor (se usan las cifras de Cristina en el Excel); agente de exportación (DEX); gastos
locales de Hapag; tarifa del CFS (Transglory); acuerdos PFT; precios por documento de ROH/SOI/INS/SAN; CES por naviera;
transporte de contenedor y FS vigentes.
