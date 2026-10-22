## Compañía

La compañía del sistema está configurada con los datos de Odoo 17 producción: **Boss Continental S.L.**, España,
moneda **EUR** y plan contable **PGC PYMEs 2008** (localización española de Odoo, con sus impuestos). Las listas de
precios están activadas: una **Tarifa general (EUR)** sin precios y, si se pactan, una lista por cliente.

## IVA de los servicios BOSS

Ajustes › **Ventas** › bloque **Precio**: un impuesto de Odoo para cada clase que dan las reglas: **NR**, **EX**
(exento) y **NS** (no sujeto).

![Ajustes de IVA y moneda](img/15-ajustes-iva.png)

Mientras un impuesto esté vacío, las líneas de esa clase tienen el IVA **pendiente** y la oferta no se puede enviar
ni confirmar.

> **Decisión de Ángel (P17)**: qué impuesto del PGC corresponde a cada clase y con qué artículo de exención. Instalar la
> localización no decide el tratamiento de cada servicio. Como referencia, Odoo 17 usa «21% S», «0% EX S» y
> «0% EXEMPT NS». Ceuta y Melilla: zona pendiente.

## Coste de proveedor en otra moneda

- **No convertir** (por defecto): una línea con tarifa en otra moneda queda «Otra moneda, sin política» y no suma al
  coste de la oferta.
- **Tipo de cambio de Odoo de la fecha de la oferta**: se convierte con el tipo de Odoo; el tipo usado se guarda en la
  foto al aceptar.

> La política de cambio y la regla de quebranto bancario (QBR) están pendientes (P03).
