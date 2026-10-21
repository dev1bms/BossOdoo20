Esta guía explica el sistema de precios de BOSS en Odoo 20 tal como está implantado. Trabaja con las pantallas
estándar de **CRM** y **Ventas**; lo propio de BOSS se añade en ellas.

> Todos los importes, clientes y proveedores de las imágenes y ejemplos son **ilustrativos** (por ejemplo
> «Naviera Ejemplo»). Los precios reales de proveedor están en Odoo, con su documento, y no se publican aquí.

## El ciclo en siete pasos

1. **Oportunidad** en CRM con el cliente y lo que pide.
2. **Oferta** creada desde la oportunidad, con los **datos del envío** (pestaña [[Envío]]).
3. **Servicios**: botón [[Añadir servicios]]; una línea por servicio y, si va por contenedor, por tamaño y tipo.
4. **Coste**: cada línea busca el precio de proveedor aprobado y explica el cálculo.
5. **Precio que falta**: el sistema dice qué falta (dato del envío, tarifa, aprobación, decisión) y abre el formulario
   adecuado; al guardar se vuelve a la oferta.
6. **Venta e IVA**: precio de venta por línea, margen y recargo, IVA según las reglas de BOSS.
7. **Enviar y aceptar**: al confirmar se congelan los precios y se guarda una **foto** del cálculo. Cualquier cambio
   posterior se hace con [[Recotizar]], indicando el motivo.

## Principios

- **Un servicio = un producto** de Odoo con su código (THC, BL, DEM…). Ver [Catálogo de servicios](#/catalogo).
- **El precio de proveedor está en una tarifa**, con su documento, página, vigencia y aprobación. Nunca se teclea en la
  oferta. Ver [Introducir una tarifa](#/tarifa-alta).
- **Un único cálculo** para todas las pantallas; el resultado siempre dice su estado: cotizado, faltan datos, sin precio,
  pendiente de aprobación, a consultar, varios precios, importe manual, otra moneda.
- **Cero no es gratis**: un precio de venta a cero es «falta precio» salvo que se marque «Sin cargo».
- **Nada se adivina**: una regla de negocio sin decidir queda como «pendiente de decisión». Ver
  [Decisiones pendientes](#/preguntas).

## Dónde está cada cosa

| Qué | Menú |
|---|---|
| Oportunidades | CRM |
| Ofertas y pedidos | Ventas › Pedidos |
| Tarifas de proveedor | Ventas › Productos › Tarifas de proveedor |
| Precios de proveedor (todas las líneas) | Ventas › Productos › Precios de proveedor |
| Servicios | Ventas › Productos › Productos (filtro «Servicios BOSS») |
| Puertos y aeropuertos | Ventas › Configuración › Puertos y aeropuertos |
| IVA de servicios y moneda | Ajustes › Ventas › Precio |
