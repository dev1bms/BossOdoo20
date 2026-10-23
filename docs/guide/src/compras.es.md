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
factura lo prestado (decisión pendiente de Ángel, A8).

## Factura de proveedor

Se crea desde el pedido de compra (**Crear factura**), con su cuenta analítica. Antes de contabilizarla:

- cada línea de servicio BOSS necesita el **impuesto que figura en la factura del proveedor** (también 0 %);
- el servicio debe estar **ya facturado al cliente** (requisito de Cristina), salvo que el coste adicional esté
  «cubierto por el precio acordado» o «lo asume BOSS». Un coste adicional «necesita aprobación del cliente» o «en
  disputa» se decide antes.

Un coste sin pedido (gasto, tique) se registra con [[Coste sin pedido de compra]]: la factura de proveedor queda
en la cuenta analítica del expediente.
