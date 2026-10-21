Una **tarifa** = un documento del proveedor, su vigencia y a qué se aplica. Ventas › Productos ›
**Tarifas de proveedor** › [[Nuevo]].

![Tarifa de proveedor](img/07-tarifa.png)

## Cabecera

| Campo | Qué poner |
|---|---|
| Nombre | Proveedor + qué cubre + edición, p. ej. «MSC gastos locales importación 09-12/2026» |
| Proveedor | Quién factura a BOSS |
| Documento del proveedor | El **PDF** recibido (obligatorio para enviar a aprobación) |
| Referencia del documento | Título y edición del PDF |
| Moneda | La del documento (EUR, USD…) |
| Válida desde / hasta | Las del documento; «hasta» vacío = hasta que empiece otra versión |
| Prioridad | Normalmente 10; un número menor gana cuando dos tarifas se aplican al mismo envío |

## Se aplica a (vacío = cualquiera)

Sentido, modo de transporte, forma de carga, **transportista**, **puertos**, **países en el extranjero**,
**provincias** (zonas de transportistas) y **cliente** (precio pactado solo para ese cliente: gana a los generales).

## Precios

Cada línea es **un servicio en una base de cobro**: servicio, base de cobro (contenedor, BL, expediente, kg…),
tamaño y tipos de contenedor si el documento distingue, **forma de cálculo**, importes, mínimo/máximo, «a consultar»
y **página** del documento. Al abrir una línea se ven los parámetros de su forma de cálculo:

![Precio por días con periodo libre y tramos](img/08-precio-tiempo.png)

Las formas de cálculo se explican en [Las cinco formas de cálculo](#/metodos).

## Cargar muchas tarifas

Las tarifas de muestra se cargaron con el **importador** (fichero estructurado con proveedor, documento, página,
vigencia, alcance y precios). Es idempotente: no duplica ni pisa cambios hechos a mano, y nunca aprueba. Ver
[Mantenimiento](#/mantenimiento).
