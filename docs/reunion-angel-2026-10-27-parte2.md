# Reunión con Ángel y Cristina (27/10/2026), parte 2: requisitos, auditoría y cambios

Fuente: transcripción (voz a texto, con errores: «cheaper» = shipper, «Societa» = Susaeta, el cliente del ejemplo). Cada
decisión lleva la cita que la sostiene. Parte 1 y ADR-006: `docs/reunion-angel-2026-10-27.md`. Decisiones técnicas:
`docs/adr/007-supplier-cost-from-the-quotation.md`.

## 1. P0: el error al pulsar «Confirmar» en S00034

**Reproducido** (`.research/probe_p0.py`, transacción deshecha; registro del servidor 13:20:49 UTC: «S00034 is not ready
to send or accept», sin traza). No es un fallo de Odoo: es la **comprobación de la oferta antes de aceptar** (ADR-004),
que listaba 7 servicios con toda la traza de IVA de cada uno («so much error»). Hipótesis estudiadas:

| Hipótesis | Evidencia | Resultado |
|---|---|---|
| H1 Comprobación de la oferta (IVA pendiente / venta sin precio) | `action_confirm` lanza `UserError` con 7 líneas; en el registro, aviso a las 13:20:49 | **Causa** |
| H2 Límite de crédito (banner «susaeta ha alcanzado su límite de 850 €») | Odoo 20 solo avisa (`partner_credit_warning`); no hay bloqueo en `sale` ni en `account` | Rechazada |
| H3 Coste desconocido sin motivo (`_boss_check_costs`) | No se llega: la comprobación de IVA/venta salta antes | Rechazada |
| H4 Traza de error (excepción de programación) | Ninguna `Traceback` en el registro de 11:00 a 14:00 | Rechazada |

**Causa raíz**: el contacto «susaeta», creado en la reunión, **no tiene país** (ni NIF): la zona de IVA del cliente es
desconocida y las 8 líneas quedan «IVA pendiente» (la tabla de IVA sí resuelve EX/cliente español → Art. 22: S00032 y
S00033 se aceptaron). Además, 4 servicios sin precio de venta (T3-PAD, CSM, TTE-FCL, GLO-CCC).
**Cambio**: el mensaje se agrupa por causa y dice qué hacer («IVA pendiente en 8 servicios porque el cliente «susaeta»
no tiene país: póngalo en el contacto»; «falta precio de venta en 4 servicios: …»), y el aviso amarillo de la oferta
dice lo mismo. La regla (no se acepta con IVA pendiente ni venta sin precio) no cambia.
**Límite de crédito**: Belal puso 850 € al cliente durante la demo «para probar»; el total 4.775 € supera el límite y
Odoo lo avisa, sin bloquear. No se toca el límite de ningún cliente.

## 2. Requisitos

| Cita | Requisito | Estado | Antes | Cambio | Prueba |
|---|---|---|---|---|---|
| «The orderer is the one who hires us… If it's import, it's the consignee. If it's export, it's the shipper» | Negocio BOSS: ordenante = destinatario (importación) o expedidor (exportación); con agente, no se copia | Confirmado | Nada propuesto | Propuesta automática solo si el campo está vacío (ADR-007 §6) | `check_quote_flow` 1, 2, 3 |
| «The file comes from the quotation… the quotation creates a file» | El expediente se crea al aceptar; no se elige antes | Confirmado (ya era así) | Campo «File» en la oferta confundía | Etiqueta «Vincular a un expediente existente» con ayuda | 8 |
| «It's coming just the sales, not the buying. The buying… in the shipment» | Líneas = venta; coste de compra visible y trazable, y pasa al expediente | Confirmado (ya era así) | Coste por línea con explicación y origen | Origen con validez y alcance («Source: … valid from … to …, applies to …») | 1, 8 |
| «Where do I say the number of containers… let's put two. It should change» | 1×40' → 2×40' persiste; por contenedor ×2, por envío ×1 | Confirmado (ya era así) | Funciona en servidor; en la demo la fila no se había guardado | Comprobado en formulario y en Chrome | 1 |
| «Check for WFS. But WFS is not for flete… Will coming alert for you» | Proveedor sin precio para ese servicio: aviso inmediato | Confirmado | «Sin precio de proveedor» sin aviso | Aviso al elegir el proveedor (ADR-007 §7) | 7 |
| «This service it's supplied by boss, not supplier» | Servicio propio sin proveedor | Confirmado (ya era así) | «Ejecutado por BOSS», coste 0 justificado | Sin cambio; no se fuerza proveedor | 6 |
| «Write the new price every week… from here, wizard, small wizard… only for one origin port, one destination port and… valid for a week» | Coste de flete semanal desde la oferta, por ruta, con validez, al motor | Confirmado (Cristina y Ángel) | Asistente solo sin tarifa; sin puerto extranjero en el alcance | Puerto extranjero en tarifas y precios; asistente en servicios de importe manual con ruta y 7 días (ADR-007 §1-3) | 5 |
| «Se quedan en el sistema, los históricos» | Los costes antiguos no se pierden ni cambian | Confirmado (ya era así, ADR-002/003) | Tarifas aprobadas inmutables; ofertas aceptadas congeladas | Comprobado: nueva tarifa y archivo de la anterior no tocan la oferta aceptada | 9 |
| «I think you are putting the rates inside of the services instead of inside of the suppliers… Perfect. That was everything» | Acceso por proveedor (MSC → sus tarifas) además de por servicio | Confirmado (ya existe) | Contacto › pestaña «Tarifas de proveedor», botones «Tarifas» y «Precios»; menú Proveedores | Sin cambio; documentado en la guía | Chrome |
| «MSC sends… one PDF with 20 pages… go into the MSC profile and change all» | Actualizar la tarifa entera de un proveedor | Confirmado (ya existe) | «Nueva versión» de la tarifa; importador | Sin cambio | — |
| «I'm not active the rule… 20%» | Venta = coste + 20 % **no activa** | Abierto (margen sobre venta ≠ recargo sobre coste) | Nada activo | Nada activo | — |
| «What is fiscal position?» | Posición fiscal | Aclarado | Estándar de Odoo | Las líneas BOSS toman el impuesto de la tabla de IVA de BOSS (ADR-004); la posición fiscal no interviene en ellas | 8 |
| «Credit limit» | Límite de crédito | Aclarado | Aviso de Odoo | Sin cambio | — |
| «Oh so much error» | Mensaje de aceptación | Confirmado | 7 líneas con traza | Agrupado por causa (§1) | 8, 8b |

## 3. Auditoría de lo que ya existía (verificado en boss20)

- Oferta → aceptación → expediente: `action_confirm` congela las líneas, guarda la instantánea y abre **un** expediente
  (`_boss_open_files`); repetir Confirmar no abre otro. No crea pedidos de compra ni facturas: los costes a comprar
  quedan en el expediente «a pedir».
- Coste de compra por línea: `boss_cost_amount`, estado, explicación con fuente (tarifa, versión, proveedor, documento,
  página); venta en `price_unit` con origen (`boss_sale_status`). El 253 de la demo = THC de MSC (tarifa «MSC gastos
  locales importación (origen China) 09-12/2026», p. 12).
- Por proveedor: Contactos › MSC › pestaña «Tarifas de proveedor» (y Tarifas y proveedores › Proveedores).
- Contenedores 1×40' → 2×40': persiste y recalcula cantidades (servidor). En la demo la fila no estaba guardada.
- S00011, S00014, S00028 (parte 1): borradores del cliente [DEMO], nunca enviados, sin instantánea. Sus costes
  cambiaron al recalcularse con las tarifas de hoy (WFS en espera de aprobación; tarifas DEMO borradas y secciones de
  IRENEO archivadas por mandato de Belal). Un borrador se recalcula al editarse (ADR-003); no procede restaurar.

## 4. Abierto (no se implementa como regla)

| # | Tema | Situación |
|---|---|---|
| R2-A1 | ¿Un coste tecleado solo para una oferta debe también guardarse como tarifa reutilizable? | Hoy: coste manual en la línea o tarifa desde el asistente (dos vías) |
| R2-A2 | ¿Quién aprueba las tarifas semanales de flete? (P19) | Hoy: aprobador de tarifas (Ángel, Belal); el asistente las deja en borrador o las envía |
| R2-A3 | Venta por defecto: ¿+20 % sobre el coste o 20 % de margen sobre la venta? | Nada activo |
| R2-A4 | Ordenante de un expediente de agente (B17) | Se guarda B/A; sin validación del tipo de contacto |

## 5. Pruebas

`dev/check_quote_flow.py` (boss20, todo deshecho al terminar) y recorrido en Chrome con cliente [PRUEBA]: §6 del
informe final y `docs/evidencias/`.
