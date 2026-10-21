Ajustes › **Ventas** › bloque **Precio**:

![Ajustes de IVA y moneda](img/15-ajustes-iva.png)

## IVA de los servicios BOSS

Un impuesto de Odoo para cada clase que dan las reglas: **NR**, **EX** (exento) y **NS** (no sujeto). Mientras un
impuesto esté vacío, las líneas de esa clase tienen el IVA **pendiente** y la oferta no se puede enviar ni confirmar.

> La elección de los impuestos (y la localización contable española) es una decisión de Ángel (P17).

## Coste de proveedor en otra moneda

- **No convertir** (por defecto): una línea con tarifa en otra moneda queda «Otra moneda, sin política» y no suma al
  coste de la oferta.
- **Tipo de cambio de Odoo de la fecha de la oferta**: se convierte con el tipo de Odoo; el tipo usado se guarda en la
  foto al aceptar.

> La política de cambio y la regla de quebranto bancario (QBR) están pendientes (P03).
