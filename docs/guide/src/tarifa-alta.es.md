Una **tarifa** = un documento del proveedor: su vigencia, a qué se aplica y sus precios. Se introduce una vez y la
usan todas las ofertas en cuanto un aprobador la aprueba. Tarifas y proveedores › **Tarifas y documentos** ›
[[Nuevo]]. **Un PDF con varias secciones** (importación, exportación, transporte por zonas…) **sigue siendo una sola
tarifa**: cada precio lleva el alcance de su sección.

## Paso a paso

1. **Cabecera**: nombre (proveedor + qué cubre + edición, p. ej. «MSC gastos locales importación 09-12/2026»),
   **proveedor** (quién factura a BOSS; no tiene por qué ser la naviera), **documento** (el PDF), **referencia del
   documento** (título y edición), **moneda**, **válida desde / hasta** («hasta» vacío = hasta una versión nueva).
2. Pestaña **Se aplica a**: rellene solo lo que limita **todo** el documento (sentido, modo, forma de carga,
   transportista, puertos, países, provincias, cliente). Los campos vacíos muestran «Cualquier …»: valen para todo.
   Cuando el alcance coincida con el documento, marque **Alcance revisado**. Bajo el título aparece el resumen en una
   línea.
3. Pestaña **Precios** › [[Añadir una línea]] por cada servicio del documento ([[Guardar y nuevo]] para seguir con
   el siguiente). Cada precio es un **servicio del catálogo en una base de cobro**; un proveedor nuevo nunca crea un
   servicio nuevo.
4. En cada precio, elija la **forma de cálculo**: solo aparecen sus campos, y junto a cada importe su unidad
   («EUR por Contenedor», «EUR por 100 kg tasable … y día»). El **ejemplo vivo** calcula un envío ilustrativo con el
   motor de precios.
5. **Sección del documento**: en el precio, grupo **Se aplica a**, rellene solo lo que esa sección limita (sentido,
   modo, forma de carga, puertos, países, provincias); vacío = «Como la tarifa». **Este precio se aplica a** lo muestra
   en una línea, y la lista de precios lo enseña en la columna **Se aplica a**. Un precio puede restringir la tarifa,
   nunca ampliarla.
6. El aviso amarillo **Antes de enviar a aprobación** lista lo que falta, y también dos precios del mismo servicio y
   unidad que se aplicarían a los mismos envíos (estarían en conflicto: restrinja «Se aplica a» en uno).
   [[Enviar a aprobación]].
7. Un aprobador revisa con el PDF y pulsa [[Aprobar]]. Desde ese momento los precios cotizan y ya no cambian: un
   cambio es una **nueva versión**.

![Tarifa aprobada: resumen del alcance y precios con su unidad](img/22-tarifa-aprobada.png)

![Borrador: lo que falta antes de enviar y el alcance con «Cualquier …»](img/23-tarifa-borrador-alcance.png)

## Tres ejemplos

| Documento | Forma de cálculo | Qué poner |
|---|---|---|
| MSC: THC por contenedor | Precio por unidad | Base de cobro Contenedor, tamaño 40', tipo HC si el documento distingue, **precio unitario** (EUR por Contenedor) |
| WFS: almacenaje por peso y día | Por día con periodo libre | Se cobra por **kg tasable de la guía aérea**, tamaño de unidad 100, **o fracción**; horas libres 48; modo «superado, se cobra desde el día 1»; tramos de días («Hasta» = número de día, 0 = sin límite) |
| IRENEO: transporte por tramos de peso | Tramos | Se cobra por **kg tasable (factor del documento)**, factor 333; tramos «Hasta» en kg con importe fijo o precio por kg. El tramo que contiene la cantidad total la cobra entera |

**Un documento con secciones** (IRENEO «Tarifas MAD»): una tarifa «IRENEO Tarifas MAD 2026» sin sentido ni modo en
la cabecera. El paquete de exportación Barajas y la inspección X-R llevan *Exportación · Aéreo*; la recogida en
terminal, *Importación · Aéreo*; la distribución nacional de zona 3, sus provincias; el almacenaje de exportación,
*Exportación · Aéreo · MAD*. Dos precios del mismo servicio (manipulación de importación y de exportación) conviven
porque su alcance no se solapa. Cuando el proveedor cambia un precio, **nueva versión** de la misma tarifa con su
fecha.

![Precio por días: unidades junto a cada importe y ejemplo del motor](img/24-precio-tiempo.png)

![Precio por tramos de peso con factor volumétrico](img/25-precio-tramos.png)

## Cero, vacío y demostración

- **Un precio sin importe es un precio que falta**, nunca gratis: la tarifa no se envía hasta que tenga importe, esté
  marcado **A consultar** o **Sin coste (cero confirmado)**.
- **Mínimo / máximo** se aplican al coste de **toda la línea de oferta**; 0 = sin mínimo / máximo.
- Al cambiar la forma de cálculo, los valores que dejan de aplicar se borran y un aviso dice cuáles (Descartar los
  recupera).
- **Tarifa de demostración** (cinta «Demo»): solo cotiza clientes marcados como **Cliente de demostración**; nunca un
  cliente real, aunque no exista otro precio. Solo un aprobador marca clientes de demostración.

## Cargar muchas tarifas

Las tarifas de muestra se cargaron con el **importador** (fichero estructurado con proveedor, documento, página,
vigencia, alcance y precios). Es idempotente, nunca aprueba y marca el alcance como revisado porque el fichero lo
declara. Ver [Mantenimiento](#/mantenimiento).
