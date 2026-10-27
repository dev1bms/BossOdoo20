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
| 7 | Transportista principal vs terrestre | CERRADO (WIP) | Principal = `boss_carrier_id`; terrestre = proveedor de la línea TTE-* → `boss_haulier_id` en la oferta y `haulier_id` del expediente; `check_meeting_matrix` 7 |
| 8 | ETD y ETA separados, fecha clave por sentido | CERRADO | `boss_etd`/`boss_eta`, `boss_planned_date` derivada; `check_route_cases` E1/E2; Chrome S00162 (ETA 16/11) |
| 9 | Entrega final distinta de ETA y opcional | CERRADO | S00080 y S00162 aceptadas con «Entrega final al cliente» vacía |
| 10 | Fecha clave como fecha de tarifa | CERRADO (regla P04, Ángel 16/10) | ADR-003 §1 y ADR-006 §2; nota A5 (LCL: Odoo 17 usa la fecha de vaciado) sigue abierta |
| 11 | País extranjero ≠ España / provincia interior | CERRADO (WIP 2) | Import/export: lado extranjero nunca España (E2); **cruzado (X)** y **nacional (N)** añadidos sin forzar España (`check_route_cases` E8/E9; ADR-006 enmienda 2) |
| 12 | Incoterm + lugar convenido | CERRADO (WIP) | `incoterm_location` en el grupo Caso; `check_meeting_matrix` 12 |
| 13 | Plantilla = caso | PARCIAL + DECISIÓN | Rellena sentido, modo, carga, incoterm, negocio, alcance (`check_quote_flow` 1); datos de IAB/IMB/EAB son propuesta (R-S1, Cristina) |
| 14 | Contenedor según servicio | CERRADO (WIP) | Celdas tamaño/tipo solo en líneas por contenedor/TEU (`boss_quantity_source`); en precios de tarifa ocultos para aéreo/grupaje/terrestre |
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
| 30 | Asistente de coste semanal | CERRADO | `boss_supplier_price_wizard` con ruta y una semana; `check_quote_flow` 5; aprobación sigue siendo paso aparte (R2-A2) |
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

Pruebas del cierre: `dev/check_meeting_matrix.py` (23/23), `dev/check_chargeable_weight.py` (38/38),
`dev/check_quote_flow.py` (40/40), `dev/check_route_cases.py` (36/36; 53/53 con los casos cruzado y nacional),
`dev/check_default_markup.py` (22/22). «WIP 2» = segunda tanda del 27/10 por la tarde (X/N, fecha clave, +20 %),
probada montada en boss20 y pendiente de despliegue.
