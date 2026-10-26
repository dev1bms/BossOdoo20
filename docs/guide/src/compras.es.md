BOSS compra a proveedores los servicios que no hace él mismo. Cada compra externa va en un **pedido de compra** de Odoo.

## Quién ejecuta cada servicio

En la oferta, la columna **Por** de cada línea dice quién lo hace:

- **Proveedor**: se compra. Su coste viene de la tarifa de proveedor (o se escribe en **Coste manual**).
- **BOSS**: lo hace BOSS (consignación, gestión propia, camión propio). No hay coste de proveedor ni nada que comprar.

El servicio da el valor por defecto (los honorarios BOSS, «BOSS»; el resto, «Proveedor»); en un servicio mixto se
cambia en la línea antes de aceptar.

Una oferta **no se acepta** si un servicio de proveedor tiene el coste **desconocido**. Solo un responsable de ventas
puede aceptarla igualmente, escribiendo el motivo en **Aceptado sin coste porque**; el expediente lo muestra como coste
desconocido hasta que llegue la factura del proveedor.

## Servicios a comprar

![Servicios y costes del expediente E260001 [DEMO]](img/31-expediente-servicios.png)

Al aceptar, cada servicio de proveedor pasa a la pestaña **Servicios y costes** del expediente con su propia **base de
compra**: proveedor, cantidad, unidad y moneda de la tarifa del proveedor, y el coste previsto. La venta no se toca y
nunca se convierte una base en otra (contenedores, kg, W/M…).

El proveedor se puede cambiar mientras no haya pedido; con pedido, cancele primero ese pedido.

## Solicitudes de presupuesto

[[Crear solicitudes de presupuesto]] prepara **borradores**, uno por proveedor y moneda, solo con lo que queda por
pedir. Pulsar dos veces no duplica nada (y dos usuarios a la vez tampoco: el segundo recibe un aviso). El precio es
el coste previsto de BOSS; Odoo no lo sustituye por el coste del producto. Los servicios sin proveedor se avisan.

Nada se confirma ni se envía solo: una persona revisa el borrador, ajusta si hace falta y pulsa **Confirmar pedido**
en el pedido de compra.

## Servicio prestado

Cuando el proveedor ha hecho el servicio, pulse el icono ✓ (**Marcar como prestado**) en la línea: la cantidad
recibida pasa a ser la pedida. Si la política de control de facturas del producto es «cantidades recibidas», solo se
factura lo prestado: los servicios BOSS tienen el control «cantidades recibidas» (propuesta aprobada por Belal el 23/10/2026, P32; pendiente de ratificación por Ángel).

## Factura de proveedor

Se crea desde el pedido de compra (**Crear factura**), con su cuenta analítica, solo cuando hay algún servicio
**marcado como prestado** (si no, el sistema lo dice en vez de crear una factura de ceros). Odoo copia todas las líneas
del pedido: las no prestadas van con cantidad 0 y no cuentan. Antes de contabilizarla, cada línea de servicio BOSS
necesita el **impuesto que figura en la factura del proveedor** (también 0 %).

**Orden de trabajo** (propuesta aprobada por Belal el 23/10/2026, P30; pendiente de ratificación por Ángel y Cristina): la factura de proveedor se **contabiliza a tiempo**; su **pago**
espera a que el servicio esté en una factura de cliente **contabilizada**. Mientras tanto la factura de proveedor muestra
un aviso amarillo («Antes de contabilizar o pagar») y el expediente lo lista; registrar el pago se bloquea, tanto desde
el botón de la factura como desde el asistente de pagos de una lista o un extracto. Las líneas de cantidad 0 no
retienen el pago. Un abono al cliente posterior no retiene para siempre el pago al proveedor: el servicio ya se
facturó una vez (el proveedor sigue siendo acreedor). Ajuste:
**Ajustes › Ventas › Factura de proveedor antes de la de cliente** = «Bloquear el pago (contabilizar permitido)». Sin
aviso: coste cubierto por el precio o que asume BOSS; **Pagado por adelantado** (flete pagado a un agente: basta la
línea de venta).

Un coste sin pedido (gasto, tique) se registra con [[Coste sin pedido de compra]]: la factura de proveedor queda
en la cuenta analítica del expediente.

## Suplidos: derechos e IVA del DUA

Los importes pagados en nombre del cliente (ARA, IVA, PLA del DUA) no se piden con solicitud de presupuesto: el agente
de aduanas los paga y los factura al coste. El servicio queda **Facturado sin pedido de compra**, con el agente de
aduanas del expediente como proveedor y el estado «Factura sin pedido esperada». Su factura se registra con
[[Coste sin pedido de compra]] y se casa con el servicio por producto y cuenta analítica (sin contarse dos veces).

Cuentas (como en Odoo 17, aplicadas el 26/10/2026; Ángel las ratifica): subcuentas de **419** de pasivo corriente, una
para lo repercutido al cliente y otra para lo soportado del agente: IVA 419001 / 419003, aranceles (ARA) 419002 /
419004, antidumping (DUM) 419005, impuesto del plástico (PLA) 419006 / 419007. La factura al cliente del suplido va
exenta (no sujeto).

## Pedidos parciales, cancelados y cambio de proveedor

- **Parcial**: reduzca la cantidad en la solicitud antes de confirmarla; lo que falta vuelve a
  [[Crear solicitudes de presupuesto]].
- **Cancelado**: la cantidad de un pedido cancelado vuelve a estar por pedir.
- **Otro proveedor**: cancele el pedido activo, cambie el proveedor del servicio y pulse [[Recalcular coste previsto]]:
  se aplica la tarifa del nuevo proveedor.
- **Otra base de compra**: antes de pedir, la unidad de compra del servicio puede ser distinta de la de venta (vendido
  por envío, comprado por kg): la venta no cambia y nunca se convierte una unidad en otra.
