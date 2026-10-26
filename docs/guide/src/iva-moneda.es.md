## Compañía

La compañía del sistema está configurada con los datos de Odoo 17 producción: **Boss Continental S.L.**, España,
moneda **EUR** y plan contable **PGC PYMEs 2008** (localización española de Odoo, con sus impuestos). Las listas de
precios están activadas: una **Tarifa general (EUR)** sin precios y, si se pactan, una lista por cliente.

## IVA de los servicios BOSS

Dos pasos:

1. **Clase de IVA** de la línea, con las reglas de Ángel (31/08/2026): **NS** = no sujeto por naturaleza (nunca IVA),
   **EX** = exento, **NR** = lleva IVA; un NR pasa a EX según origen/destino y según la zona del cliente
   ([detalle](#/venta-iva)).
2. **Impuesto de Odoo**: la **Tabla de IVA BOSS** (Ventas › Configuración › Tabla de IVA BOSS, o desde Ajustes) da el
   impuesto de cada caso: clase × zona del cliente × suplido o no. Cada fila dice su **fuente**.

![Tabla de IVA BOSS](img/20-tabla-iva.png)

| Caso | Impuesto | Fuentes |
|---|---|---|
| NR (cliente de la península o Baleares) | 21% S | Ángel: NR lleva IVA · Odoo 17: NR = 21 % → «21% S» · casillas 303 [07]/[09] |
| EX, cliente de la UE | 0% UE S | Ángel: cliente UE → EX · Odoo 17: cliente UE → «0% EU S» · no sujeta por localización, 303 [59] y 349 |
| EX, cliente de un tercer país | 0% EX S | Ángel: cliente de tercer país → EX · Odoo 17: «0% EX S» · no sujeta por localización, 303 [120] |
| NS de un suplido (ARA, IVA, PLA, DUM) | 0% Exent NS | Ángel: no sujeto por naturaleza · Odoo 17: factura de impuestos con «0% EXEMPT NS» · no se declara |

«Odoo 17» es su asistente de facturación (acción «Create Invoice»), que elige el impuesto por clase, tipo de cliente
y tipo de factura. Solo hay fila cuando las reglas de Ángel, Odoo 17 y la naturaleza legal del impuesto coinciden.

### Aprobados por Belal el 23/10/2026, pendientes de ratificación por Ángel (P17)

| Caso | Impuesto | Fuente |
|---|---|---|
| EX de un cliente **español** (península y Baleares) | 0% Exent Art.22 | Exento art. 22 LIVA, 303 [60] (propuesta aprobada por Belal) |
| EX de un cliente de **Canarias, Ceuta o Melilla** (zona CAN) | 0% S NS | No sujeta por reglas de localización, 303 [120] |

### Caso que sigue pendiente

| Caso | Por qué | Ejemplo |
|---|---|---|
| NS que **no es suplido** (CAU, QBR) de un cliente español | Odoo 17 los factura en factura normal con el 0 % según el cliente, no como no sujetos | Caución del aval aduanero |

En ese caso la línea dice «IVA pendiente» con el motivo, y la oferta no se puede enviar ni confirmar.

## Coste de proveedor en otra moneda

- **No convertir** (por defecto): una línea con tarifa en otra moneda queda «Otra moneda, sin política» y no suma al
  coste de la oferta.
- **Tipo de cambio de Odoo de la fecha de la oferta**: se convierte con el tipo de Odoo; el tipo usado se guarda en la
  foto al aceptar.

> Política aprobada por Belal el 23/10/2026, pendiente de ratificación por Ángel (P03): tipo de cambio de Odoo de la fecha de la oferta, activo en el servidor. El
> quebranto bancario (QBR) se cobra solo cuando una oferta en USD se factura en EUR: en desarrollo (fase B).
