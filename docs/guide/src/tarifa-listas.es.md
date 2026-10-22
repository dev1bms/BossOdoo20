Una sola entrada para precios, tarifas, servicios y proveedores: la app **Tarifas y proveedores** del menú principal.
Usa los mismos datos que las ofertas (productos de servicio, contactos, tarifas de proveedor) y el mismo cálculo.

| Menú | Qué hay |
|---|---|
| **Precios** | Pantalla principal: un precio de proveedor por fila |
| **Tarifas y documentos** | Cada documento de proveedor con su vigencia, alcance, versión y aprobación |
| **Servicios** | Los productos de servicio de BOSS con sus proveedores, cálculos y estado |
| **Proveedores** | Contactos con tarifas (navieras, handlings, transportistas, almacenes…) |
| **Probar tarifa** | El cálculo de una línea de oferta sobre un envío que se teclea |

## Precios

Cada fila: código y servicio, proveedor, **a qué se aplica** (sentido, modo, carga, puertos, tamaño y tipo de
contenedor, cliente), **precio con su unidad** (p. ej. «260 EUR / Contenedor», «0,05 EUR / kg tasable · mín. 20 EUR» o
el resumen de los tramos), «hasta» y el **estado**: Vigente, Vence pronto (30 días), Vencida, Sustituida por una versión
nueva, Borrador, Pendiente de aprobación. Botones de la fila: probar, abrir el documento, copiar (solo en borrador).

- La búsqueda acepta **servicio o código**, **proveedor**, **tarifa o documento** y **puerto**.
- Al entrar se ven los precios **vigentes**, **borradores** y **pendientes**. Quitando filtros se ve todo; «Vencidas»
  y «Tarifas archivadas» dan el histórico.
- Filtros de sentido, modo y carga incluyen los precios que valen para cualquiera (campo vacío en la tarifa).
- Agrupar por proveedor, servicio, tarifa o aprobación.

[[Nuevo]] abre el formulario del precio por secciones: **servicio, proveedor y origen** (la tarifa en borrador da
proveedor, documento, moneda, vigencia y alcance), **a qué se aplica**, **cálculo** (solo los campos de la forma
elegida; al cambiarla se borran los valores que ya no aplican) y un **ejemplo vivo** calculado con el motor: un envío
ilustrativo (2 contenedores, 500 kg, 2 m³, 10 días desde un miércoles) con sus pasos, o lo que falta para calcularlo.

## Tarifa con varios servicios

Una tarifa = un documento: proveedor, PDF, moneda, vigencia y alcance se ponen una vez y valen para todas sus líneas.
Antes de enviarla a aprobación, un aviso lista lo que falta (precios, PDF, referencia) y los **precios repetidos**
(mismo servicio, base y contenedor), que darían conflicto. Bajo el aviso se dice qué campos del alcance están
**vacíos = se aplica a cualquiera**, para no confundirlos con un dato olvidado. Cambiar el modo de transporte borra una
forma de carga de otro modo (p. ej. FCL al pasar a aéreo).

## Servicios y proveedores

**Servicios** muestra, por servicio: origen del coste, formas de cálculo usadas (pueden cambiar según el proveedor),
proveedores, precios vigentes y por aprobar, y el estado: Con precio, Sin precio de proveedor, Por aprobar, Precios
vencidos, No se calcula con tarifas. El producto tiene los botones **Precios de proveedor** y **Guía**. Un servicio
nuevo es un producto nuevo: buscar antes de crearlo (no se duplica por proveedor).

**Proveedores** lista los contactos con tarifas: tarifas, servicios, precios por aprobar y vencidos o por vencer. En
la ficha del contacto, los botones **Tarifas de proveedor** y **Precios de proveedor**. Un proveedor no es por fuerza
el transportista: el transportista del envío solo cambia en la oferta.

## Probar tarifa

Mismo cálculo que una línea de oferta, sin guardar nada. Se elige servicio y base de cobro, proveedor (vacío =
cualquiera), los datos del envío y las medidas. Resultado: estado, cantidad, coste, el precio usado y **por qué**
(vigente en la fecha, se aplica al envío, el más específico, la versión más nueva), o qué falta, qué precios están
pendientes o en conflicto.

- **Simular borradores**: una tarifa sin aprobar cuenta como aprobada solo en esta prueba. Las ofertas nunca la usan.
- **Cliente** o **lista de precios** (opcional): precio de venta por unidad, venta y beneficio, con la regla de la
  lista de precios.
- Se abre desde el menú, desde una fila de **Precios** (con su alcance y simulación si está en borrador), desde la
  tarifa y desde el icono ⓘ de una línea de oferta (servicio, proveedor y envío de la línea).

## Desde una oferta

En el icono ⓘ de una línea: [[Probar tarifa]], [[Añadir precio de proveedor]] cuando no hay precio y [[Revisar el
precio de proveedor]] cuando está pendiente o en conflicto. El precio se guarda en una tarifa del **proveedor de la
línea**; tras aprobarlo la oferta se recalcula sola. Las líneas aceptadas no cambian (solo con [[Recotizar]]).
