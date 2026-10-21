Los servicios son **productos de Odoo de tipo servicio** con su código original (THC, BL, DEM…). Ventas ›
Productos › Productos, filtro **Servicios BOSS**.

![Lista de servicios](img/12-servicios-lista.png)

## Ficha del servicio

La pestaña **Precios BOSS** dice cómo se cotiza:

![Ficha de un servicio](img/11-servicio.png)

| Campo | Significado |
|---|---|
| Origen del coste | **Tarifa de proveedor** (cálculo automático), **Importe manual** (flete por oferta, suplidos), **Honorario propio** (sin coste), **Pendiente de decisión** |
| Forma de cálculo | La habitual; cada precio de proveedor puede usar otra si su documento lo dice |
| Pregunta abierta | Referencia en [Decisiones pendientes](#/preguntas) |
| Clase de IVA | NS, EX o NR (reglas de IVA) |
| Unidad y otras unidades | Bases de cobro posibles del servicio |
| Código y concepto de Odoo 17, códigos anteriores, sustituido por | Trazabilidad e histórico (p. ej. TTE-FCL recoge TCC y TTC; FTT está sustituido por TTE-CON) |
| Descripción | Qué es el servicio y quién lo presta (traducible) |

## Crear o cambiar un servicio

1. Ventas › Productos › [[Nuevo]]: tipo **Servicio**, **código**, nombre (con traducción al inglés si se desea).
2. Unidad = base de cobro principal; otras unidades si se puede cobrar de otra forma (p. ej. AWB o expediente).
3. Pestaña Precios BOSS: origen del coste, forma de cálculo, clase de IVA.
4. Precio de venta del producto: **0** (el precio se indica en cada oferta o en la lista de precios del cliente).

> No se crea un servicio por falta de tarifa: se añade el precio a una tarifa. Un servicio pendiente de decisión
> existe y se puede ofertar con coste manual, pero no tiene fórmula inventada.

Cada servicio tiene su página en esta guía (menú lateral, por familias).
