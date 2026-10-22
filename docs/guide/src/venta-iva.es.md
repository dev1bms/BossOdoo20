## Precio de venta

El precio de venta es el **precio unitario** estándar de la línea. Su estado (columna **Venta**) es independiente del
estado del coste (columna **Coste**): una línea puede tener el coste calculado y la venta pendiente, o al revés.

| Origen | Cómo se configura | Estado «Venta» |
|---|---|---|
| Precio pactado con el cliente | Lista de precios del cliente, regla **Precio fijo** por servicio y **base de cobro** | Precio pactado |
| Sobre el coste de la línea | Lista de precios del cliente, regla **Recargo** «% sobre **Coste previsto de la línea (BOSS)**», o **Margen sobre la venta (%)**; opcionales: redondeo, importe añadido y margen mínimo/máximo | Sobre el coste previsto |
| Lo escribe el comercial | Teclear el precio unitario (manda sobre la lista) | Indicado por una persona |
| Sin cargo | Marcar «Sin cargo» (precio 0 intencionado) | Sin cargo (confirmado) |
| — | Precio 0 sin marcar, o regla sobre un coste que aún no se conoce | **Falta precio de venta** |

En el detalle de la línea (icono ⓘ de la columna Coste), el bloque **Cómo se fija el precio de venta** dice la lista,
la regla y el cálculo: «Lista de precios Cliente X, regla «Coste previsto de la línea + 15 %»: el coste previsto de
150,00 € por Contenedor da 180,00 €. Se aplica el margen mínimo de 30,00 € por unidad».

![Detalle de la línea: cómo se calcula el coste y cómo se fija la venta](img/16-detalle-venta.png)

### Reglas sobre el coste

![Regla de lista de precios sobre el coste previsto de la línea](img/17-regla-coste.png)

- **Recargo** = (venta − coste) / coste; **margen** = (venta − coste) / venta. Ejemplo ilustrativo con coste 100 €:
  recargo 20 % → 120 €; margen 20 % → 125 €. Se usa uno u otro, no los dos.
- El **margen mínimo** de Odoo es **por unidad de la base de cobro** (contenedor, expediente, kg…). En servicios por kg
  conviene no usarlo (15 € por kg sería absurdo). Un mínimo por línea u oferta es una decisión pendiente (P02).
- Si el coste aún no se conoce (sin tarifa, pendiente de aprobación, faltan datos), la venta queda **«falta»**: nunca se
  calcula sobre un coste cero.
- En un borrador, cuando cambia un dato del envío o se aprueba una tarifa, se recalculan el coste y la venta que
  depende de él; un precio tecleado por una persona se respeta y una oferta aceptada no cambia.
- Los precios por kg conservan sus decimales (0,092 € por kg × 500 kg = 46,00 €); el importe de la línea se redondea a
  céntimos.

> Política comercial: no hay una regla general de venta aprobada; los precios se pactan por cliente (Cristina). Las
> reglas de cada cliente las crea un gestor comercial. La venta unificada de ALM y el margen mínimo están pendientes
> (ver [Decisiones](#/preguntas)).

## IVA

El IVA de cada línea sale de las **reglas de IVA de BOSS** (Ángel, 31/08/2026):

1. Clase base del servicio: **NS** (no sujeto) y **EX** (exento) son definitivas.
2. **NR**: según origen → destino (zonas PRO península y Baleares, CAN Canarias, COM resto UE, TER terceros países);
   solo siguen NR PRO→PRO, CAN→PRO, COM→PRO, COM→COM, TER→PRO y TER→COM; el resto pasa a EX.
3. Si sigue NR, según el **cliente**: PRO mantiene NR; CAN, COM y TER pasan a EX.
4. Si falta una zona, el IVA queda **pendiente**.

El impuesto de Odoo sale de la **Tabla de IVA BOSS** según la clase y la zona del cliente (ver
[IVA y monedas](#/iva-moneda)): NR → 21% S; EX de un cliente de la UE → 0% UE S; EX de un cliente de un tercer país →
0% EX S; suplidos (NS) → 0% Exent NS. El detalle de la línea dice el porqué («base NR · TER→PRO: NR · cliente PRO:
NR · 21% S (fuente)»). EX de clientes españoles o canarios, CAU, QBR y Ceuta/Melilla siguen **pendientes** (P17).

## La oferta no se envía ni se confirma si…

… alguna línea tiene **IVA pendiente** o **falta precio de venta**. El sistema lo explica línea a línea:

![Envío bloqueado con la lista de lo que falta](img/06-envio-bloqueado.png)
