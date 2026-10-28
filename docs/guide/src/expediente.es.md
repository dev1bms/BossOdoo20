El **expediente** reúne todo lo de un envío: quién, ruta, carga, referencias, fechas, servicios, compras, facturas y
rentabilidad. Está en la aplicación **Expedientes** (y en **Ventas → Pedidos → Expedientes**).

## Cuándo se abre

- Al **confirmar** una oferta con servicios BOSS se abre su expediente (número **E26xxxx**). Si se vuelve a confirmar o
  se repite la acción, no se abre otro.
- Si el envío empieza **antes** de la oferta (prealerta, documentos recibidos), cree el expediente a mano desde
  **Expedientes**: queda como **preliminar**. Cuando se acepte la oferta, elija ese expediente en el campo
  **Expediente** de la oferta (pestaña **Envío**).
- Un servicio vendido **después** va en una oferta nueva vinculada: botón [[Vender otro servicio]] del expediente.
- Una oferta aceptada puede repartirse entre **varios expedientes** (por ejemplo, un contenedor en otro buque):
  [[Mover servicios a otro expediente]] (ver más abajo).

## Qué contiene

![Resumen del expediente E260001 [DEMO]](img/30-expediente-resumen.png)

- **Quién**: cliente contratante, responsable, cargador, consignatario, agente, transportista y, en aéreo, **handler**
  (ver «Aerolínea y handler»); en **Referencias y fechas**, notify, transportista terrestre y agente de aduanas.
- **Ruta**: sentido, modo, tipo de carga, incoterm, origen y destino, puerto, país y lo que hace BOSS (recogida,
  aduana en origen, transporte principal, aduana en destino, entrega).
- **Carga**: mercancía, bultos, peso, volumen, palés y un renglón por contenedor con número, precinto, recogida del
  lleno y devolución del vacío.
- **Referencias y fechas**: booking, BL master/house (o AWB), buque/vuelo, viaje, DUA; ETD/ETA previstas y, con
  **fecha y hora**, las reales: ATD, ATA, NOA (aviso de llegada del handler), FOH (mercancía recibida en la terminal,
  exportación), recogida real y entrega real.
- **Eventos**: hitos, incidencias y notas con fecha y usuario; además el chatter con actividades y adjuntos.

Los datos del expediente se copian **una vez** de la oferta aceptada. Después cada uno guarda lo suyo: la oferta lo
pactado, el expediente lo real. En **Resumen → Diferencias con la oferta** se ve qué cambió (contenedores, pesos,
transportista, fechas). Nada se sincroniza solo.

## Estados y cierre

[[En tránsito]] → [[Entregado]] → [[Cerrar operaciones]]. El cierre **económico** es aparte:
[[Cerrar económicamente]] solo se permite con todo facturado, todos los costes facturados o cerrados, diferencias
revisadas y nada en borrador. El aviso amarillo **Pendiente** dice qué falta.

## Cuenta analítica

Cada expediente tiene su cuenta analítica (plan **Expedientes**). Se pone sola en las líneas de venta, en las de compra
y, desde ellas, en las facturas. Así el coste y el ingreso de cada envío se leen de la contabilidad, sin importes
escritos a mano.

## Recalcular el coste previsto con los datos reales

Cuando cambian los datos del envío (contenedores en **Carga**, peso, volumen, peso de la AWB, fechas reales ATA/ATD,
proveedor) o los **días** de un servicio por tiempo (columna **Días** en **Servicios y costes**: almacenaje, demoras,
ocupación), pulse [[Recalcular coste previsto]]. Se usa el mismo cálculo que en la oferta, ahora con los datos del
expediente:

- cada servicio a comprar toma la cantidad y el coste nuevos; la pestaña **Recálculos de coste** guarda antes/después,
  usuario, fecha, datos usados y la explicación del cálculo;
- la **venta aceptada y su foto no cambian** (para cobrar más está [[Añadir un servicio]] o Refacturar);
- las solicitudes de presupuesto en borrador se actualizan; un pedido ya confirmado no se toca: el servicio queda con
  **Pedido a revisar** y el coste final previsto usa el dato más reciente.

Ejemplo: ALM cotizado con 5 días (2 libres, 25 €/día → 75 €); el contenedor se retira el día 9 → 175 €. Un segundo
contenedor de 40' en **Carga** → THC 2 × 240 € = 480 €.

![Recálculos de coste del expediente WFS [DEMO]: AWB 500 → 620 kg y almacenaje 3 días más](img/32-expediente-recalculos.png)

## Fechas reales y periodo de los servicios por tiempo

Cristina (26/10/2026): ATA y recogida real con fecha y hora, y el sistema calcula las fechas. Cada servicio por tiempo
(ALM, DEM, OCU, DET) toma su periodo de **los hechos que dice su tarifa** (campos «El periodo empieza en» y «El periodo
termina en» del precio de proveedor) o, si la tarifa no los dice, de los de su servicio. Al guardar una fecha del
expediente o de un contenedor, el coste previsto se recalcula solo (motivo «Cambio de fechas del expediente» en
**Recálculos de coste** y un evento):

| Servicio | Empieza | Termina | Fuente |
|---|---|---|---|
| ALM aéreo importación | NOA (o ATA si no hay NOA) | Retirada (recogida real) | Cristina 25/09; WFS «desde el NOA» |
| ALM aéreo exportación | FOH | Salida real (ATD) | Cristina 25/09 (ETD; se usa la real cuando existe) |
| ALM grupaje importación | Vaciado (LCL) | Retirada | Cristina 25/09 |
| DEM importación | Llegada del buque (ATA); Hapag: descarga del buque | Devolución del vacío **de cada contenedor** | MSC p.18; Hapag MHD/DTD |
| OCU importación | Llegada del buque | Salida del lleno **de cada contenedor** | MSC p.17 |
| DET exportación | Retirada del vacío de cada contenedor | Entrada del lleno en la terminal | MSC p.10 |

Las fechas de cada contenedor están en **Carga** (retirada del vacío, entrada del lleno, salida del lleno, devolución
del vacío). Si los contenedores tienen fechas distintas, cada uno se valora con su periodo y el coste es la suma (el
recálculo lo detalla «Por contenedor: …»). La columna «Periodo según» de **Servicios y costes** dice qué hechos se
usan. Si una persona escribe el periodo en la línea del servicio, se marca **Periodo escrito a mano** y las fechas ya no
lo cambian. La venta aceptada no cambia.

![Expediente E260015: demoras por contenedor tras guardar ATA y las fechas de los contenedores](img/43-periodo-por-contenedor.png)

## Aerolínea y handler (aéreo)

**Expedientes → Aerolíneas y handlers** dice qué handler atiende a cada aerolínea en cada aeropuerto (cargada de la
configuración de Odoo 17 el 26/10/2026: MAD, BCN, VLC, AGP, BIO; la mantienen compras y el jefe de ventas). En un
expediente aéreo:

- con **un** handler conocido para la aerolínea y el aeropuerto, el campo **Handler** se rellena solo;
- con **varios** (por ejemplo, una aerolínea servida por WFS o por Iberia en Madrid), no se elige por usted: el campo
  solo ofrece esos handlers;
- sin ninguno registrado, se elige libremente entre los contactos con rol «Handling aéreo / terminal»;
- al cambiar de aerolínea o aeropuerto, el handler anterior se sustituye por el nuevo si solo hay uno.

HAN, ALM, AWB, ETX y X-R se compran al handler: en la oferta, la línea toma el handler como proveedor cuando es único
(solo su tarifa la valora); en el expediente, los servicios aún no pedidos pasan al handler elegido y su coste se
recalcula (motivo «Cambio de handler»).

## Resumen por grupo de servicio

La pestaña **Resumen** empieza con la tabla del «Resumen» de Odoo 17: una fila por **grupo de servicio** (Flete,
Transporte terrestre, Gastos locales, Aduana, Almacenaje y almacén, Seguro y mensajería, Profit share, Aranceles e
impuestos suplidos; el grupo es la categoría del producto) y la fila Total, con **venta acordada, facturada y por
facturar**, **coste pendiente** (servicios aún sin factura de proveedor), **coste real** (facturas y abonos de proveedor
contabilizados), **coste previsto** y **margen previsto**. Moneda de la compañía, sin impuestos. La fila Total cuadra con
las cifras de debajo (venta acordada, coste previsto, margen previsto). Solo responsables de ventas y contabilidad.

## Previsión de costes

**Expedientes → Previsión de costes** (también vista pivote y gráfico en **Servicios a comprar**) suma el coste previsto
de los servicios a comprar de los expedientes abiertos, por proveedor y **previsión**: *Estimada (oferta)* → *Recalculada
con los datos del expediente* → *Pedida al proveedor* → *Confirmada por la factura del proveedor*. Así se ve qué
previsiones son aún estimaciones y cuáles ya confirmó un documento («Nuevo Odoo», hoja previsiones). Se agrupa también
por servicio, expediente, cliente o estado.

![Previsión de costes por proveedor y previsión](img/44-prevision-costes.png)

## Una oferta, varios expedientes

[[Mover servicios a otro expediente]] lleva una parte de las cantidades aceptadas a otro expediente del mismo cliente
(nuevo o existente). La pestaña **Servicios vendidos** muestra la parte de cada línea en este expediente: la suma de
todos los expedientes nunca supera lo aceptado, el precio no cambia, cada expediente factura su parte y la cuenta
analítica de la línea se reparte en proporción. Un servicio ya pedido al proveedor se reduce antes en su pedido.

![Servicios vendidos: parte de la oferta en este expediente](img/33-servicios-vendidos.png)

![Mover servicios a otro expediente](img/34-mover-servicios.png)

## Añadir un servicio después de aceptar

[[Añadir un servicio]] (gestor comercial) añade al pedido aceptado un servicio nuevo con su precio y el motivo: hecho
por **BOSS** (sin coste de proveedor) o por un **proveedor** (pasa a servicios a comprar). Las líneas aceptadas y su
foto no cambian; queda otra foto «Servicio añadido tras la aceptación» y la línea no cuenta en el margen en la
aceptación.

![Añadir un servicio tras la aceptación](img/35-anadir-servicio.png)
