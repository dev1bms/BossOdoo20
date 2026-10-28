# Matriz de cumplimiento de la reunión con Ángel y Cristina (27/10/2026)

Una fila por punto de la lista de revisión de Belal (42). Estado: **CERRADO** (código + prueba + pantalla cuando
aplica), **PARCIAL** (hecho con una condición pendiente), **ABIERTO** (no hecho) o **DECISIÓN** (necesita a Ángel o
Cristina). Evidencia: ruta de código, nombre de la comprobación (`dev/check_*.py`, salida en `docs/evidencias/`) y
registro visto en Chrome. Comprobado el 27/10/2026 sobre boss20; el código posterior al commit `2b572c7` se probó
montado en boss20 sin desplegar (`dev/server_shell_wip.sh`) y **se desplegó el 27/10 a las 16:08 con la aprobación
de Belal** (commit `064891c`; las filas marcadas «WIP» están ya en boss20: `check_chargeable_weight` 38/38 y
`check_meeting_matrix` 23/23 sobre el código desplegado, `docs/evidencias/20261027_1608_*_064891c6ae9d.txt`).

| # | Punto | Estado | Evidencia (código → prueba → pantalla) |
|---|---|---|---|
| 1 | Origen y destino (país, puerto, lugar) | CERRADO | `boss_shipment_route.py`; `check_route_cases` E1/E2 (36/36); Chrome S00080, S00162 (chatter con los 12 campos) |
| 2 | Dirección de entrega manual si el cliente no tiene | CERRADO | «Crear y editar» desde el campo crea un contacto de entrega del cliente (contexto `default_parent_id`/`default_type`); `check_meeting_matrix` 2 |
| 3 | Elegir uno de varios almacenes (Leroy) | CERRADO | `check_meeting_matrix` 3 (dos almacenes del mismo cliente); Chrome S00162: «[PRUEBA] Almacén Zaragoza» elegido entre Alcalá y Zaragoza, provincia Zaragoza derivada |
| 4 | Transporte terrestre según el almacén y su precio | CERRADO (tarifa real) | `check_meeting_matrix` 4: IRENEO zona 3, 666 kg tasables → 205,44 € en Zaragoza; cambio a València sigue en zona 3; cambio a Alcalá (Madrid) → sin precio (zonas MAD no cargadas, nada inventado) |
| 5 | Exportación Zaragoza → Barcelona → Túnez | CERRADO | `check_route_cases` E2 (puerto ESBCN, país TN, provincia Z, fecha ETD); coste terrestre export: misma tarifa IRENEO (zona por provincia, importación/exportación) |
| 6 | Puerto extranjero en el precio | CERRADO | `foreign_port_ids` tarifa y línea, clave `foreign_port_id`; `check_quote_flow` 5 (Shanghái sí, Ningbo no) |
| 7 | Transportista principal vs terrestre | IMPLEMENTADO · pantalla pendiente | Principal = `boss_carrier_id`; terrestre = proveedor de la línea TTE-* → `boss_haulier_id` en la oferta y `haulier_id` del expediente; `check_meeting_matrix` 7 |
| 8 | ETD y ETA separados, fecha clave por sentido | CERRADO | `boss_etd`/`boss_eta`, `boss_planned_date` derivada; `check_route_cases` E1/E2; Chrome S00162 (ETA 16/11) |
| 9 | Entrega final distinta de ETA y opcional | CERRADO | S00080 y S00162 aceptadas con «Entrega final al cliente» vacía |
| 10 | Fecha clave como fecha de tarifa | CERRADO (regla P04, Ángel 16/10) | ADR-003 §1 y ADR-006 §2; A5 cerrada (fecha de vaciado nunca elige tarifa, ADR-006 enm. 2); flete por ETD (ADR-009) |
| 11 | País extranjero ≠ España / provincia interior | CERRADO (WIP 2) | Import/export: lado extranjero nunca España (E2); **cruzado (X)** y **nacional (N)** añadidos sin forzar España (`check_route_cases` E8/E9; ADR-006 enmienda 2) |
| 12 | Incoterm + lugar convenido | CERRADO | `incoterm_location` en el grupo Caso; `check_meeting_matrix` 12; campo «Incoterm Location» visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| 13 | Plantilla = caso | PARCIAL + DECISIÓN | Rellena sentido, modo, carga, incoterm, negocio, alcance (`check_quote_flow` 1); datos de IAB/IMB/EAB son propuesta (R-S1, Cristina) |
| 14 | Contenedor según servicio | CERRADO | Celdas tamaño/tipo solo en líneas por contenedor/TEU (`boss_quantity_source`); en precios de tarifa ocultos para aéreo/grupaje/terrestre; S00311: tamaño 40' solo en líneas por contenedor, vacío en BL (por expediente); visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| 15 | 1×40' → 2×40' | CERRADO | `check_quote_flow` 1; Chrome S00080 (cantidad 2 guardada y reabierta), S00162 |
| 16 | Datos de carga opcionales, sin cero oculto | CERRADO | Medidas a 0 = desconocidas (`_required` del motor); `check_meeting_matrix` 16 (SEG sin valor → sin coste inventado); `check_chargeable_weight` (volumen desconocido → nada) |
| 17 | Almacenaje 0 por defecto; estimaciones | CERRADO | `check_meeting_matrix` 17: 15 días → demora MSC 485 € estimada; 0 días → 0; derechos de aduana en la oferta y el expediente |
| 18 | Peso real/volumen/tasable 167/333/1000 | CERRADO (desplegado) + WIP | Desplegado `a5c5f4e`; corrección WIP: el tramo terrestre de un envío marítimo usa 333 (unidad `chargeable_road_kg`); `check_chargeable_weight` 38/38 |
| 19 | W/M marítimo, IRENEO 333, AWB | CERRADO | `check_chargeable_weight` (W/M = 1000; factor del documento manda; FCL sin kg); `check_meeting_matrix` 4 (IRENEO) |
| 20 | «Super cubic meter» | CERRADO | Ángel (27/10, vía Belal): no existe; solo el metro cúbico (base m³ y W/M ya existentes) |
| 21 | Ordenante → destinatario/expedidor | CERRADO | `_boss_apply_orderer_party`; `check_quote_flow` 1/2; `check_meeting_matrix` 21 (override respetado); Chrome S00162 |
| 22 | Negocio de agente | CERRADO | `check_quote_flow` 3 (IMA, agente no copiado como parte); a quién se factura en el caso agente = ordenante (B17 abierta para validación de tipo de contacto) |
| 23 | La oferta crea el expediente | CERRADO | Chrome S00080 → E260025 y **S00162 → E260038 sin ningún sckript**; `check_quote_flow` 8 (sin duplicado) |
| 24 | Venta en líneas, compra trazable al expediente | CERRADO | Chrome S00162: precio unitario vs coste unitario por línea; expediente con costes a comprar; `check_quote_flow` 8 |
| 25 | Proveedor → tarifas (MSC) | CERRADO | Contacto › pestaña «Tarifas de proveedor», botones Tarifas/Precios (`workspace_views.xml`); Ángel: «Perfect» |
| 26 | Proveedor sin precio para el servicio (WFS en flete) | CERRADO | Aviso `_onchange_boss_supplier_id`; `check_quote_flow` 7 |
| 27 | Servicio propio sin proveedor | CERRADO | `boss_execution = boss`; `check_quote_flow` 6; Chrome CSM coste 0 justificado |
| 28 | Origen del 253 | CERRADO | ⓘ de la línea: «Source: MSC gastos locales importación (origen China) 09-12/2026 v1 (MSC), valid from …, document … page 12, applies to …»; `check_meeting_matrix` 28 |
| 29 | PDF de MSC de 20 páginas | CERRADO | «Nueva versión» copia las 10 líneas, se cambia lo que cambia, documento nuevo y alcance revisado; `check_meeting_matrix` 29 |
| 30 | Asistente de coste semanal | CERRADO | `boss_supplier_price_wizard` con ruta y una semana; `check_quote_flow` 5; desde el 28/10 el flete se aprueba al introducirlo (ajuste, ADR-009) y se guarda como versión de la misma tarifa |
| 31 | Históricos intactos | CERRADO | `check_meeting_matrix` 31 (S00033 igual tras versión nueva); `check_quote_flow` 9; `check_chargeable_weight` 5 |
| 32 | Venta estable / «PP» | CERRADO | Ángel (27/10, vía Belal): «PP» no existe; venta = lista del cliente, tecleada o coste + % (fila 33) |
| 33 | +20 % | CERRADO (WIP 2) | Belal 27/10: ajuste «Venta por defecto: coste + 20 %» (una regla en la tarifa por defecto; tecleado gana; 0 desactiva); `check_default_markup` 22/22; ADR-008 |
| 34 | Confirmar S00034 | PARCIAL | Causa y mensaje agrupado (ADR-007); S00034 es de Ángel y no se toca: necesita país y NIF en «susaeta», 4 precios de venta y coste o motivo en FMI/T3-PAD/TTE-FCL |
| 35 | Posición fiscal / impuestos | CERRADO | `check_meeting_matrix` 35: cliente español EX→Art.22, NR→21 %; UE con NIF → 0 % UE; tercer país → 0 % EX; Canarias → 0 % S NS; sin país → pendiente; la posición fiscal de la oferta no cambia los impuestos BOSS |
| 36 | Límite de crédito | CERRADO | Solo aviso de Odoo 20 (`partner_credit_warning`); banner visible en S00162; sin tocar límites |
| 37 | Oferta completa solo por pantalla | CERRADO | S00162: cliente, plantilla, MSC, ruta, almacén, ETA, peso, contenedor, servicios, precios, proveedor, coste manual y Confirmar tecleados en Chrome → E260038 |
| 38 | WFS en espera | DECISIÓN | Tarifa 58 «WFS Tarifas MAD/BCN» con 7 precios y documento, esperando aprobación (Belal o Ángel) |
| 39 | X/N y LCL fecha clave | CERRADO (WIP 2) | R-A2: sentidos cruzado/nacional; R-A5: fecha clave = ETA import, ETD resto, nunca la fecha de vaciado (ADR-006 enmienda 2) |
| 40 | Migración de contactos Odoo 17 | ABIERTO | R-A4: inventario y mapeo pendientes |
| 41 | PP, MSF, One, OCL, FBA | CERRADO | MSF = MSC, One = ONE (Ocean Network Express), OCL = OOCL (navieras); FBA probablemente «aéreo» (transcripción); PP no existe (Ángel 27/10) |
| 42 | Mapa fuente → código → prueba → pantalla | CERRADO | Esta matriz |

## Segunda reunión: siete fragmentos recuperados (transcripción entregada por Belal el 28/10/2026; ADR-009)

Estado el 28/10 con el código **y el XML** montados en boss20 (`dev/check_meeting2.py`, 69/69 tras la segunda revisión
de Belal: vistas y documento del cliente cargados en la transacción por `dev/wip_bootstrap.py`). Estados: **CERRADO** =
visto en pantalla; **IMPLEMENTADO · pantalla pendiente** = código y prueba en boss20, falta verlo en Chrome tras el
despliegue; **PARCIAL**; **DECISIÓN**. **Desplegado el 28/10 a las 11:26** (commit `f96dbb3`, aprobación de Belal); `check_meeting2` 69/69 sobre el código desplegado; CERRADO = visto en Chrome (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`).

| # | Punto (fragmento) | Estado | Evidencia (código → prueba → pantalla) |
|---|---|---|---|
| M2-1 | La plantilla FOB rellena el incoterm FOB (1) | CERRADO | Ya lo hacía: `check_route_cases` E1, `check_meeting2` 5; Chrome S00311 («[FOB] FREE ON BOARD» desde la plantilla) |
| M2-2 | Entrega final al cliente es estimada, meses después (1) | CERRADO | Etiqueta «Final delivery to the client (estimate)», opcional; `check_meeting2` 3 (tras el despliegue) |
| M2-3 | Un transportista comercial, varias entidades legales (MSC España, Suiza, USA) (1) | IMPLEMENTADO · pantalla pendiente | `res.partner.boss_carrier_group_id` «Pertenece al transportista»; las tarifas casan por familia, la línea/compra/factura conservan la entidad legal; `check_meeting2` 4 y 6. Dato: al migrar los contactos (R-A4) MSC Suiza/USA se marcan como parte de MSC |
| M2-4 | Dirección de entrega con el destinatario, recogida con el expedidor; la cabecera sobra (1, 2) | CERRADO | Cabecera: direcciones de factura y entrega ocultas (Odoo las sigue rellenando); recogida elegida entre las direcciones del **expedidor**, entrega entre las del **destinatario**; ambas opcionales; `check_meeting2` 3 y 5; cabecera sin direcciones de factura ni entrega en S00311; visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| M2-5 | Tipo de bulto (cajas, palés, jaulas, bultos, botellas, sacos) y código de la mercancía (2) | CERRADO | `boss_package_type` (taxonomía de la partida de Odoo 17) y `boss_hs_code` en oportunidad, oferta y expediente; `check_meeting2` 5; campos «Type of unit» y «Goods code (HS)» en la pestaña Envío de S00311; visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| M2-6 | Aranceles según valor y código de la mercancía (2) | DECISIÓN | Sin tabla de aranceles por código (TARIC): la estimación se teclea; el código queda registrado. Pendiente de Ángel: fuente de los tipos |
| M2-7 | FCL: sitio claro para los contenedores (2) | CERRADO | Encabezado «Contenedores del envío (tamaño, tipo, cantidad)» sobre la lista |
| M2-8 | «Valencia, Shenzhen» se lee al revés (2) | CERRADO | Asistente: origen arriba, destino debajo; ámbito de la tarifa «CNSZX → ESVLC»; nombre de la tarifa con la ruta; `check_meeting2` 6 y 8; asistente: origen CNSHA arriba, destino ESVLC debajo; ⓘ «CNSHA → ESVLC»; visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| M2-9 | Validez del flete desde esta semana; dos semanas si hace falta (2) | CERRADO | `valid_from` = hoy, `valid_to` = +6 días, editables; `check_meeting2` 8; asistente: válido 28/10 → 03/11; visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| M2-10 | Flete en USD con cambio (2) | CERRADO | Tarifa 98 de Ángel en USD → coste en EUR al cambio de la fecha de la oferta (política «rate_quotation»); `check_meeting2` 7 |
| M2-11 | Números a la española, dos decimales en todo (2) | PARCIAL | Dos decimales mínimos en precio de venta, coste de compra y precios de proveedor (4 solo si el valor los tiene; `check_meeting2` 3). Coma decimal y punto de millar = idioma del usuario (es_ES): **decisión de Belal** poner a los usuarios de BOSS en español (los dos usuarios actuales están en en_US) |
| M2-12 | Documento del proveedor ¿obligatorio? Preguntar a Cristina; fácil de quitar (2) | IMPLEMENTADO · pantalla pendiente + DECISIÓN | Ajuste «Documento del proveedor obligatorio» (por defecto activo = ADR-002); `check_meeting2` 2 y 8. Cristina decide |
| M2-13 | Wendy a las 4 de la mañana no puede esperar una aprobación (2) | CERRADO | Ajuste «Fletes aprobados al introducirlos» (activo): probado con un **usuario real de tarifas no aprobador** (`[PRUEBA] Wendy`): teclea el flete, queda aprobado por ella con nota, la oferta se valora al momento y la confirma sola; un comercial sin derechos de tarifas no abre el asistente; con el ajuste apagado su flete espera y no puede aprobarlo; `check_meeting2` 8 y 13; asistente con aviso «approved on entry», tarifa 169 aprobada al momento y la oferta valorada sin recargar; visto en Chrome 28/10 (`docs/evidencias/20261028_1135_chrome_despliegue_reunion2.md`, `20261028_1140_chrome_asistente_flete_prueba.md`) |
| M2-14 | Una tarifa por ruta, precios sucesivos (1/11, 8/11, 13/11, 17/11), el más nuevo vigente (3) | IMPLEMENTADO · pantalla pendiente | El asistente crea **versiones** de la misma tarifa; el motor elige la versión más nueva vigente en la fecha; historial intacto; aceptadas sin cambios; precio de diciembre adelantado no toca noviembre; `check_meeting2` 8 |
| M2-15 | El flete marítimo y aéreo toma siempre la salida (ETD) (4) | CERRADO | `product.template.boss_tariff_date` = salida en FMI/FMI-LCL/FME/FME-LCL/FAI/FAE (migración); sin ETD, la fecha de la oferta; explicación en la línea; `check_meeting2` 1 y 7; `check_quote_flow` 5 adaptado |
| M2-16 | Venta independiente del proveedor: THC 180 (MSC) / 190 (CMA) → 210 (4, 5) | CERRADO | Precio fijo del servicio en la lista general (regla por producto) manda sobre «coste + 20 %»; cambiar de naviera cambia el coste y el margen, no la venta; el precio tecleado sobrevive; `check_meeting2` 9. **Las cifras son de Cristina (Excel): pendientes** |
| M2-17 | La plantilla tiene los precios de venta (Excel de Cristina) (5) | DECISIÓN | Mecanismo listo (lista de precios general = tarifas de venta); faltan los Excel y qué servicios son fijos o variables |
| M2-18 | «Unit price / unit cost» confunden (6) | CERRADO | «Precio de venta (unitario)» y «Coste de compra (unitario)» |
| M2-19 | Transporte terrestre caso por caso: mantener la línea, aceptar, teclear el coste en el expediente (6) | IMPLEMENTADO · pantalla pendiente | «Coste a petición» en la línea, **solo** cuando el proveedor nombrado no tiene precio del servicio (revisión 2): datos de envío que faltan, precio pendiente de aprobación, conflicto o flete sin oferta siguen su camino; se acepta sin excepción de responsable y el expediente lo muestra como desconocido hasta teclearlo; `check_meeting2` 10. Matiza B22 (Cristina, M2-H) |
| M2-20 | Proveedor que haga el servicio (camionero, o la naviera) (6) | PARCIAL | Cualquier proveedor con aviso si no tiene tarifa del servicio; sin lista de servicios por proveedor (decisión) |
| M2-21 | Al cliente se envían tarifas por unidad (20', 40', 40'HC, B/L), no un total (6) | IMPLEMENTADO · pantalla pendiente + DECISIÓN | «Oferta de tarifas»: líneas 20' DV / 40' DV / 40' HC valoradas para 1 unidad cada una; documento con la base («Container 40' HC») sin importes ni total, sin precios de compra, margen ni notas internas; el documento normal conserva cantidades y totales; la aceptación espera los contenedores **solo en ofertas de tarifas** y nombra las alternativas no reservadas para quitarlas (papelera de la línea) o editar el tipo; `check_meeting2` 12 (documento renderizado con el XML montado). Decisión M2-C: ¿expediente al aceptar la lista (hoy) o al booking? |
| M2-22 | Resumen como Odoo 17: compra/venta por grupo, pendiente vs definitivo, pendiente vs facturado (7) | CERRADO | Grupos = categorías de Odoo 17; tabla en la pestaña Resumen; probada con el ciclo de facturación (factura de proveedor contabilizada → coste real sin contar dos veces; factura parcial de cliente y abono parcial → facturado / por facturar; totales = cifras del expediente); `check_meeting2` 11; el ciclo completo con pagos sigue en `dev/uat_e2e.py` |
| M2-23 | Un expediente y una partida en la misma página (7) | PARCIAL + DECISIÓN | Un expediente = una página con carga, contenedores y referencias máster/house: cubre el caso de una partida. Una consolidación (un máster, varias houses, costes compartidos) no tiene objeto máster en Odoo 20: «varias partidas = varios expedientes» era lectura del implementador, no decisión. Opciones A (expediente máster + hijos) / B (partida dentro del expediente, forma de Odoo 19): M2-I, antes de cualquier cambio |

Pruebas del cierre: `dev/check_meeting_matrix.py` (23/23), `dev/check_chargeable_weight.py` (38/38),
`dev/check_quote_flow.py` (40/40), `dev/check_route_cases.py` (36/36; 53/53 con los casos cruzado y nacional),
`dev/check_default_markup.py` (22/22), `dev/check_meeting2.py` (69/69). «WIP 2» = segunda tanda del 27/10 por la tarde (X/N, fecha clave, +20 %),
**desplegada a las 16:43** (commit `5cf2918`); el 20 % está activado en Ajustes y visto en S00311
(`docs/evidencias/20261027_1646_chrome_s00311_venta_coste_mas_20.md`).

## Portal de clientes (Belal, 28/10/2026; ADR-010) — **instalado 28/10 12:10**; `check_portal` 46/46, `check_portal_http` 25/25

| # | Punto | Estado | Evidencia |
|---|---|---|---|
| P-1 | Costes, márgenes, proveedores, tarifas y compras nunca llegan al cliente (también por RPC, exportación, informes) | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | 24 campos de línea y 4 de oferta solo internos; `check_portal` 1: 9/9 con un usuario portal real (lectura, `fields_get`, búsqueda, exportación rechazadas); regresiones 69/39/53/23/38/22 |
| P-2 | Roles concedidos por BOSS (seguimiento, comercial, apoderado) y alcance por entidad legal | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | Restricciones `ir.access` (Odoo 20); `check_portal` 2–3, 9 y `check_portal_http` 0–2, 9 |
| P-3 | Compras del cliente-proveedor visibles en el portal estándar | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | Comprobado hoy visible (`check_portal` 1); `boss_portal` lo cierra (`check_portal` 3) |
| P-4 | Oferta de tarifas en portal, lista, correo y PDF sin total; sin firma ni pago | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | `check_portal_qweb` 4/4 contra las plantillas de Odoo 20; `check_portal` 4; `check_portal_http` 3–4 |
| P-5 | Aceptar/firmar/pagar solo apoderado; el enlace con token solo ve | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | `check_portal` 4, `check_portal_http` 4 |
| P-6 | Petición de reserva revisada por BOSS (sin confirmar, sin expediente, sin factura) | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | `check_portal` 5, `check_portal_http` 5; el momento del expediente sigue siendo M2-C |
| P-7 | Mis envíos con fechas estimadas ≠ reales, eventos y documentos publicados | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | `check_portal_qweb` 4/4; `check_portal` 6–7; `check_portal_http` 6–7 |
| P-8 | Enlace de seguimiento sin acceso, revocable, sin partes ni documentos | PROBADO (ORM + HTTP) · pantalla del cliente pendiente | `check_portal` 8, `check_portal_http` 8 |
| P-9 | Seguimiento automático (MSC, BFirst…) | DECISIÓN | No existe en Odoo 17 ni 20; `docs/portal-seguimiento-integraciones.md` |

