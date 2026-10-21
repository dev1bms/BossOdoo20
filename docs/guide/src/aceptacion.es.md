## Enviar

[[Enviar]] usa el correo estándar de Odoo (plantilla, PDF de la oferta, firma en línea si está activada). Antes,
el sistema comprueba IVA y precios de venta (paso 6).

## Aceptar

Cuando el cliente acepta, pulse [[Confirmar]] (o el cliente firma en el portal). En ese momento:

- Se **congelan** todas las líneas: cantidades, unidades, precios, costes, impuestos. Ni un cambio de tarifa ni de los
  datos del envío las modifica.
- Se guarda una **foto** en la pestaña **Historial de precios**: datos del envío, contenedores, política de moneda y,
  por línea, venta, coste, moneda, tipo de cambio (si se usó), tarifa, versión, documento, página, IVA y explicación.

![Oferta aceptada: precios congelados e historial](img/13-oferta-aceptada.png)

## Recotizar

Un gestor comercial pulsa [[Recotizar]]: indica el **motivo**, puede recalcular costes con las tarifas vigentes y
escribir precios de venta nuevos. Se guarda otra foto con los valores anteriores, la fecha y el usuario, y el motivo
queda en el historial del pedido.

![Recotizar una oferta aceptada](img/14-recotizar.png)

## Después (fases siguientes)

La foto aceptada es la base comercial del **expediente** (operaciones) y de la **factura**: el coste previsto de cada
línea se comparará con las facturas de proveedor (coste real). Los servicios por tiempo pasan de estimación a coste real
con las fechas del expediente.
