Un contacto de Odoo es **una sola ficha por empresa o persona**, sea cliente, proveedor o ambos. No se duplica para
cada papel.

## Cliente y proveedor

En la pestaña **Ventas y compras** de la ficha:

- **Cliente** y **Proveedor** son dos casillas. Al marcarlas, el contacto aparece en seguida en **Clientes** o en
  **Proveedores**, antes de su primer documento. También se marcan solas con la primera venta o compra.
- Un contacto puede ser cliente y proveedor a la vez (filtro **Cliente y proveedor** en la búsqueda).

## Roles logísticos y aduanas

En la misma pestaña:

- **Roles logísticos**: cargador, consignatario, notify, agente en el extranjero, transportista (naviera / aerolínea),
  transportista terrestre, handling aéreo / terminal, agente de aduanas, almacén, aseguradora. Son valores fijos (no
  etiquetas libres) y sirven para buscar.
- **EORI**: número de operador económico para aduanas.

En cada persona de contacto, **Contacto para** indica si es comercial, de operaciones o de contabilidad. La dirección
de facturación es la de tipo **Factura** de Odoo.

## Datos que faltan

Se puede crear un contacto **preliminar** con solo el nombre y hacerle ofertas. Si es cliente o proveedor, la ficha
muestra en amarillo **Falta para facturar**: NIF, dirección (calle, ciudad, país) y correo.

La factura de un cliente de **España (o sin país)** no se contabiliza sin NIF u otra identificación de la localización
española (práctica de Odoo 17, confirmada el 23/10/2026; P31). La dirección que falta se avisa, sin bloquear.
