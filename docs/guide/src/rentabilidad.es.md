La pestaña **Resumen** del expediente calcula todo desde los documentos, en la moneda de la compañía y sin impuestos
salvo donde se indica. No se escribe ningún importe a mano. Los **borradores** (facturas de cliente, solicitudes de
presupuesto, facturas de proveedor) se muestran aparte y **no cuentan**.

| Cifra | De dónde sale |
|---|---|
| Venta acordada | Parte de este expediente en las ventas confirmadas (incluidos los servicios añadidos después) |
| Venta aceptada / Añadido tras la aceptación | La primera con lo aceptado en la oferta; la segunda con lo añadido con motivo |
| Facturado / Por facturar | Facturas de cliente **contabilizadas** menos abonos; lo que falta |
| Cobrado (con impuestos) | Lo cobrado de esas facturas |
| Coste previsto en la aceptación | Coste de proveedor de las líneas aceptadas, el de la oferta al aceptarla |
| Compras comprometidas | Pedidos de compra **confirmados** |
| Coste real | Facturas de proveedor y recibos **contabilizados** menos abonos (cuenta analítica del expediente) |
| Coste aún previsto | Lo pedido o previsto que aún no tiene factura de proveedor (el dato más reciente: pedido o recálculo) |
| Coste final previsto | Coste real + coste aún previsto. Nunca suma dos veces un pedido y su factura |
| Margen en la aceptación | Venta aceptada − coste previsto en la aceptación |
| Margen previsto tras costes externos | Venta acordada − coste final previsto. **No es definitivo** mientras quede un coste sin facturar o desconocido |
| Margen final tras costes externos | Solo cuando **Costes completos**: venta acordada − coste real |

**Dónde salen las cifras** (gestor comercial y contabilidad) desglosa cada cifra servicio a servicio. Ejemplo
E260001 [DEMO]:

- Venta acordada 1.385 € = aceptada 1.225 € (S00009) + 160 € de ocupación de muelle añadida con motivo.
- Coste previsto en la aceptación 1.010 € = THC 180 + 240, BL 60, DEM 90 + 90, ARA 350.
- **Margen en la aceptación 215 €** = 1.225 − 1.010.
- Coste final previsto 1.130 € = coste real 0 € (nada contabilizado) + aún previsto 1.130 € (los 1.010 € aceptados +
  120 € de la ocupación extra).
- **Margen previsto 255 €** = 1.385 − 1.130: **no es definitivo** (ningún coste facturado aún).
- No cuentan: la factura de cliente en borrador (560 €) ni la solicitud de presupuesto sin confirmar.

**Servicios propios**: el margen es **tras costes externos**; el trabajo del personal de BOSS no es un coste aquí, así
que no es el beneficio neto.

**Diferencias**: en cada servicio a comprar, **Diferencia** = facturado − pedido (o previsto). Se revisa marcando
**Diferencia revisada** con una nota; el precio de venta nunca cambia solo.

## Quién ve qué

Las cifras se calculan con todos los documentos, pero cada una solo la ve quien puede ver esos documentos en Odoo
(estándar de Odoo por rol, confirmado por Belal el 23/10/2026, pendiente de ratificación por Cristina, P35):

| Rol | Expedientes | Cifras |
|---|---|---|
| Comercial | Los suyos (responsable o comercial del pedido) | Venta, facturado, cobrado, coste y margen en la aceptación (los de la oferta) |
| Compras / operaciones | Todos | Compras comprometidas, coste real, aún previsto, final previsto, pagado |
| Gestor comercial, contabilidad | Todos | Todo, con el margen previsto o final y «Dónde salen las cifras» |
| Otra compañía | Ninguno | — |
