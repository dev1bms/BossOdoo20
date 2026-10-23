Las facturas son las estándar de Odoo, hechas desde las líneas aceptadas. El expediente añade elegir qué se factura
y los avisos antes de contabilizar.

## Facturar por servicios (hitos)

[[Facturar servicios]] en el expediente muestra los servicios por facturar de sus pedidos. Deje marcados los que se
facturan ahora (por ejemplo solo el flete y los gastos de origen) y pulse **Crear factura en borrador**. Los demás
quedan por facturar para una segunda factura.

- **Parcial**: para facturar parte de una cantidad, cámbiela en la factura en borrador.
- **Varias facturas**: repita la acción; cada factura lleva la cuenta analítica del expediente.
- **Varios expedientes en una factura**: en **Ventas → Pedidos**, seleccione los pedidos del mismo cliente y use la
  acción estándar de crear factura.

## Antes de contabilizar

Una factura de cliente no se contabiliza si:

- una línea tiene el **IVA pendiente** (tabla de IVA BOSS) o no tiene impuesto;
- al cliente le falta el **NIF** o la **dirección**.

## Abonos

El abono es el estándar (**Factura rectificativa** desde la factura contabilizada). El servicio abonado vuelve a quedar
por facturar y el expediente resta el abono de lo facturado.

## Coste adicional tras la aceptación

En **Servicios y costes** añada una línea (tipo **Coste adicional**): servicio, proveedor, cantidad, unidad, coste
previsto y motivo, y diga quién lo asume:

| El coste adicional | Qué pasa |
|---|---|
| Cubierto por el precio acordado | Se compra; no se factura aparte. |
| Refacturar al cliente | Un responsable de ventas pulsa el icono ↗ (**Refacturar al cliente**): precio de venta y motivo. Se añade **una** línea al pedido aceptado y queda una foto «Servicio añadido tras la aceptación». |
| Necesita aprobación del cliente | Pendiente de decidir; su factura de proveedor no se contabiliza hasta entonces. |
| Lo asume BOSS | Se compra y resta margen. |
| En disputa con el proveedor | Su factura de proveedor no se contabiliza hasta resolverlo. |

Nadie puede añadir una línea a un pedido aceptado por otro camino: los demás precios aceptados no cambian.
