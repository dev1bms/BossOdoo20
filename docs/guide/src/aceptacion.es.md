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

## Después

Al aceptar se abre el **expediente** del envío (ver «El expediente»). La foto aceptada es su base comercial: cada
servicio de proveedor pasa a **Servicios y costes** con su coste previsto, para pedirlo al proveedor y compararlo con su
factura (coste real). Un servicio de proveedor con coste **desconocido** impide aceptar, salvo motivo escrito por un
responsable de ventas. Un servicio añadido después de aceptar solo entra con **Refacturar al cliente** (motivo y foto) o
en una oferta nueva vinculada al expediente.
