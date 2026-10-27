# Escenario de prueba de punta a punta en boss20 · End-to-end test scenario on boss20 (27/10/2026)

Entorno: **https://system.bosscontinental.com** (base **boss20**, la única que se usa desde el 27/10 por decisión de Belal:
nada en local, nada en bases de prueba; boss20_uat ya no se usa). En boss20 se puede todo con registros de prueba
(«[PRUEBA]», «[DEMO]», «[MUESTRA]»): confirmar, contabilizar, abonar, pagar y casar; los números de documento consumidos y
los asientos de prueba se quedan. Durante las pruebas están desactivadas las comunicaciones externas (`dev/boss20_isolate.py`:
18 tareas programadas paradas, sin servidor de correo, IAP a un puerto cerrado; para restaurar, el mismo script con un fichero
`restore.txt`). Ningún pago es real: los «movimientos bancarios» se crean a mano en el diario Banco.

## Registros recorridos en Chrome (26–27/10) · Records you can open

| Paso | Registro | Qué se ve |
|---|---|---|
| Oferta y aceptación | [S00031](https://system.bosscontinental.com/odoo/action-sale.action_orders/31) | Cliente «[DEMO] Cliente UE Ejemplo GmbH», plantilla «[DEMO] IMB FOB», DEM añadido, coste manual de FMI, aceptada y bloqueada; historial de precios y tres recotizaciones [PRUEBA]; facturación cerrada |
| Expediente | [E260015](https://system.bosscontinental.com/odoo/action-656/15) | Pestaña «Resumen»: venta, facturado, cobrado, coste real, pagado y **margen final 240 €** con la explicación de cada cifra |
| Compras | [P00005](https://system.bosscontinental.com/odoo/action-purchase.purchase_rfq/5), [P00006](https://system.bosscontinental.com/odoo/action-purchase.purchase_rfq/6) | MSC: servicios de la oferta y ocupación extra (OCU 120 €) |
| Facturas de MSC | [FACTURA/2026/10/0001](https://system.bosscontinental.com/odoo/action-account.action_move_in_invoice_type/2) (420 €), [FACTURA/2026/10/0002](https://system.bosscontinental.com/odoo/action-account.action_move_in_invoice_type/7) (2.430 €) | Pagadas; la primera se rechazó al pagar antes de facturar al cliente (P30) |
| Facturas al cliente | [INV/2026/00001](https://system.bosscontinental.com/odoo/action-account.action_move_out_invoice_type/3) (560 €), [INV/2026/00002](https://system.bosscontinental.com/odoo/action-account.action_move_out_invoice_type/4) (2.445 €), [INV/2026/00003](https://system.bosscontinental.com/odoo/action-account.action_move_out_invoice_type/6) (160 €) | Facturación parcial (THC primero), resto, y refacturación de la ocupación |
| Abono | [RINV/2026/00001](https://system.bosscontinental.com/odoo/action-account.action_move_out_refund_type/5) (75 €) | BL cobrado de más; casado con INV/2026/00002 |
| Banco | Contabilidad → Banco → casación (movimientos «[PRUEBA] Cobro …» y «[PRUEBA] Pago …», BNK1/2026/00001–00005) | Cinco movimientos casados con sus pagos PAY00001–00005; todo «Pagado» |

## Pasos para repetirlo con otro cliente

| Paso | Dónde y qué hacer | Qué debe pasar |
|---|---|---|
| 1. Cliente y envío | Ventas → Nuevo. Cliente de prueba. Pestaña **Envío**: Importación, Marítimo, FCL, ESVLC, China, transportista «MSC [MUESTRA]», fecha prevista, días de almacenaje. Contenedores: 1 × 20' DV y 1 × 40' HC | El aviso «Precio por completar» desaparece a medida que completas |
| 2. Servicios | Otra información → Plantilla «IMB FOB». Después «Añadir servicios» → DEM | Una línea por servicio y tamaño; el campo de condiciones queda vacío (D-7) |
| 3. Proveedor, coste y venta | Coste manual donde no hay tarifa aprobada (nunca 0 por defecto), precio de venta de cada línea | «Confirmar» se rechaza si falta un precio de venta o un IVA |
| 4. Aceptar | «Confirmar» | Pedido bloqueado; expediente E26xxxx con su cuenta analítica |
| 5. Compras sin duplicar | Expediente → «Crear solicitudes de presupuesto» dos veces | Una solicitud por proveedor; la segunda vez «Nada que pedir» |
| 6. Ejecución real | Referencias y fechas (ATA, recogida con hora), fechas de cada contenedor; confirmar el pedido; ✓ «Marcar como prestado» | DEM recalculado por contenedor; previsión «Recalculada»; la venta no cambia |
| 7. Factura del proveedor | Compras → lista de pedidos → seleccionar el pedido → «Crear facturas» (Odoo 20 ya no tiene el botón en el formulario del pedido) o «Subir factura»; «Quitar líneas vacías», referencia del proveedor, impuesto → Contabilizar. «Registrar pago» | Solo lo prestado; el pago se rechaza mientras el servicio no se haya facturado al cliente |
| 8. Factura al cliente | Expediente → «Facturar servicios» → elegir servicios → Contabilizar | Facturación parcial; después el pago al proveedor ya se puede registrar |
| 9. Abono y coste extra | Factura → «Nota de crédito» de un servicio con motivo. Servicios y costes → coste extra con motivo → «Refacturar» → facturarlo | El pago al proveedor sigue permitido (D-5); línea de venta añadida tras la aceptación |
| 10. Pagos y conciliación | «Registrar pago» (diario Banco) en cada factura; Contabilidad → Banco → nuevo movimiento con el importe → se casa solo con el pago | Facturas «Pagado» |
| 11. Rentabilidad | Expediente → Resumen | Si queda venta por facturar por un abono, el margen dice «NO DEFINITIVO» y qué falta. Si no se va a volver a facturar: pedido → «Recotizar» (precio 0 con motivo = sin cargo) y ⚙ → «Cerrar facturación». Entonces margen final = facturado neto − coste real |

## Resultado en Chrome (27/10, boss20)

Recorrido completo sobre S00031/E260015: facturas de proveedor y cliente, facturación parcial, abono, coste extra
refacturado, pagos y casación bancaria, rentabilidad. Defectos encontrados y corregidos en el recorrido: D-7 (nota interna
en facturas), D-8 (margen final con la venta acordada) y D-9 («Recotizar» fallaba desde la interfaz); detalle en
`docs/preguntas-abiertas.md`. Cifras finales de E260015: venta acordada 3.090 €, facturado 3.090 €, cobrado 3.090 €,
coste real 2.850 €, pagado 2.850 €, margen final 240 €. Banco: +3.090 − 2.850 = 240 €.

Pruebas anteriores en boss20_uat (26/10, antes de la decisión del 27/10; se conservan como histórico):
`docs/evidencias/20261026_1901_uat_e2e_boss20_uat_da0e263afa94.txt` (64/64) y
`docs/evidencias/20261026_1903_uat_scenarios_boss20_uat_da0d0b68a13d.txt` (31/31).
