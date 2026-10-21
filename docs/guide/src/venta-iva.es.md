## Precio de venta

El precio de venta es el **precio unitario** estándar de la línea. Puede venir de:

| Origen | Cómo | Estado «Venta» |
|---|---|---|
| Lo escribe el comercial | Teclear el precio unitario | Indicado por una persona |
| Precio pactado con el cliente | Lista de precios del cliente (Ventas › Productos › Listas de precios), por servicio y **base de cobro** | Precio pactado |
| Sin cargo | Marcar «Sin cargo» (precio 0 intencionado) | Sin cargo (confirmado) |
| — | Precio 0 sin marcar | **Falta precio de venta** |

- El **margen** de Odoo es (venta − coste) / venta; el **recargo sobre coste** es (venta − coste) / coste. Ambos se
  ven en la explicación de la línea.
- Las listas de precios de servicios BOSS exigen la base de cobro y no admiten dos precios solapados para el mismo caso.
- Las reglas automáticas de venta (recargo o margen por servicio) y el margen mínimo están pendientes (P01, P02).

## IVA

El IVA de cada línea sale de las **reglas de IVA de BOSS** (Ángel, 31/08/2026):

1. Clase base del servicio: **NS** (no sujeto) y **EX** (exento) son definitivas.
2. **NR**: según origen → destino (zonas PRO península y Baleares, CAN Canarias, COM resto UE, TER terceros países);
   solo siguen NR PRO→PRO, CAN→PRO, COM→PRO, COM→COM, TER→PRO y TER→COM; el resto pasa a EX.
3. Si sigue NR, según el **cliente**: PRO mantiene NR; CAN, COM y TER pasan a EX.
4. Si falta una zona, el IVA queda **pendiente**.

El impuesto de Odoo de cada clase se elige en **Ajustes › Ventas** (ver [IVA y monedas](#/iva-moneda)).

## La oferta no se envía si…

… alguna línea tiene **IVA pendiente** o **falta precio de venta**. El sistema lo explica línea a línea:

![Envío bloqueado con la lista de lo que falta](img/06-envio-bloqueado.png)
