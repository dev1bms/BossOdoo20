Demostración en **https://system.bosscontinental.com** con los tres proveedores del sistema (**MSC**, **WFS**, **IRENEO**).
Tarifas, clientes y reglas de venta **[DEMO]**: importes ilustrativos, aprobados solo para esta demostración y limitados
a los clientes [DEMO]; no cotizan ofertas reales: son **tarifas de demostración** (cinta «Demo») y el motor solo las
aplica a **clientes de demostración**, aunque un cliente real no tenga otro precio. Las tarifas [MUESTRA] (documentos reales) siguen pendientes de aprobación.

## Registros

| Qué | Enlace |
|---|---|
| Oportunidad para la oferta en directo | [Reunión con Ángel](https://system.bosscontinental.com/odoo/crm/9) |
| MSC: oportunidad · oferta aceptada · tarifa | [CRM 4](https://system.bosscontinental.com/odoo/crm/4) · [S00009](https://system.bosscontinental.com/odoo/sales/9) · [tarifa 20](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/20) |
| WFS: oportunidad · oferta · tarifa | [CRM 5](https://system.bosscontinental.com/odoo/crm/5) · [S00010](https://system.bosscontinental.com/odoo/sales/10) · [tarifa 22](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/22) |
| IRENEO: oportunidad · oferta · tarifa | [CRM 6](https://system.bosscontinental.com/odoo/crm/6) · [S00011](https://system.bosscontinental.com/odoo/sales/11) · [tarifa 23](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/23) |
| Conflicto de IVA (cliente español) | [CRM 7](https://system.bosscontinental.com/odoo/crm/7) · [S00012](https://system.bosscontinental.com/odoo/sales/12) |
| Oferta hecha desde la interfaz (precio CES añadido, aceptada) | [S00013](https://system.bosscontinental.com/odoo/sales/13) |
| Reglas de venta de los clientes [DEMO] | [Lista de precios](https://system.bosscontinental.com/odoo/action-product.product_pricelist_action2/3) |

## Resultados esperados (cliente UE, IVA 0% UE S)

| Ejemplo | Entrada | Coste | Venta |
|---|---|---|---|
| MSC THC | 1 × 20' DV, 1 × 40' HC | 180 € y 240 € por contenedor (40' RF: 300) | 280 € pactado por contenedor |
| MSC BL | 1 por expediente | 60 € | 75 € (margen 20 % sobre la venta) |
| MSC DEM | 10 días, 7 libres, «5 días a 30 €, después 60 €» | 3 × 30 = 90 € por contenedor | 120 € (coste + 15 % con margen mínimo 30 €) |
| ARA (suplido) | DUA indicado en «Referencia del coste» | 350 € manual | 350 € a coste; IVA 0% Exent NS |
| WFS ALM | AWB 500 kg, 4 días (estimación de la línea), llegada miércoles | 4 × 5 × 10 = 200 € (48 h libres superadas: desde el día 1) | 230 € |
| WFS HAN | 500 kg tasables | 500 × 0,05 = 25 € (mínimo 20 €) | 0,0575 €/kg → 28,75 € |
| WFS AWB | 1 guía | 30 € | 34,50 € |
| IRENEO TTE-CON | Madrid, 450 kg y 1 m³ (factor 333) | tasable 450 kg, tramo «hasta 500» × 0,20 = 90 € | 103,50 € |
| IRENEO FS | 5 % del transporte del mismo proveedor | 4,50 € | 5,18 € |

## Recorrido de 10–15 minutos

1. **Tarifa** (Tarifas y proveedores › Tarifas y documentos): abrir la de MSC: proveedor, documento, vigencia, alcance
   (sentido, modo, puerto, cliente) y precios por tamaño y tipo; estado **Aprobada** con usuario y fecha.
2. **CRM**: abrir [Reunión con Ángel](https://system.bosscontinental.com/odoo/crm/9) › [[Nuevo presupuesto]].
3. **Envío**: Importación · Marítimo · FCL · ESVLC · China · MSC · fecha 04/11/2026 · días 12 · contenedores 2 × 40' HC.
   Guardar.
4. [[Añadir servicios]]: THC, DEM y **VGM**, proveedor **MSC** › Añadir. Resultado: THC 240 € de coste y 280 € de
   venta por contenedor; DEM 5 días × 30 € = 150 € por contenedor; VGM **Sin precio de proveedor**.
5. **Precio que falta**: icono ⊕ de VGM › proveedor MSC ya puesto · nombre «[DEMO] MSC VGM 2026» · 25 € · página 1 ·
   marcar **Solo este cliente** · adjuntar un PDF de prueba › [[Guardar precio]] → «Pendiente de aprobación».
6. **Aprobar**: icono de revisar de la línea › [[Aprobar]] › Aceptar. La línea queda cotizada (25 € → 28,75 €).
7. **Cambio de dato**: días 12 → 15 en Envío › guardar: DEM pasa a 5 × 30 + 3 × 60 = 330 € por contenedor.
8. **Detalle**: icono ⓘ de una línea: cómo se calcula el coste (tarifa, versión, documento, página) y cómo se fija la
   venta (regla de la lista de precios, margen mínimo).
9. [[Confirmar]] → precios congelados, **Historial de precios**; [[Recotizar]] exige el **motivo**.
10. **IVA para Ángel**: abrir [S00012](https://system.bosscontinental.com/odoo/sales/12) › Confirmar: el sistema
    explica que falta el impuesto de THC (EX, cliente español).

## Decisiones para Ángel

| Caso | Hoy | Pregunta |
|---|---|---|
| EX de un cliente español o canario (THC, T3, fletes, SEG…) | IVA pendiente: la oferta no se confirma | ¿Impuesto exento con su artículo (21/22 → «Exento Art.22», casilla 60) o la práctica de Odoo 17 «0% S» (sujeta al 0 %, casilla 150)? ¿Canarias como no sujeta por localización? |
| NS que no son suplidos (CAU, QBR) | IVA pendiente | ¿No sujeto (0% Exent NS) o el 0 % según el cliente como en Odoo 17? |
| Ceuta y Melilla | IVA pendiente | ¿Zona? |
| Cliente UE sin NIF-IVA | IVA pendiente | ¿Se factura con IVA español (no aplica la regla entre empresas)? |
| Suplido sin DUA indicado | IVA pendiente | Confirmar que el DUA a nombre del cliente es la condición |

Ya decidido y aplicado: NR → 21% S; EX de clientes UE con NIF-IVA → 0% UE S; EX de clientes de terceros países →
0% EX S; suplidos con DUA → 0% Exent NS (reglas de Ángel 31/08/2026 y facturación de Odoo 17).

## Límites de esta versión

- Demostración y uso controlado, **no** producción completa: faltan tarifas reales aprobadas, las decisiones de IVA de
  arriba y la política de moneda (los costes en USD quedan «Otra moneda»).
- El margen mínimo es por unidad de la base de cobro; por línea u oferta está pendiente (P02).
- La regla del viernes de WFS (72 h si sale el lunes) no se aplica en la oferta.
- En pantallas de menos de unos 1.900 px de ancho, la tabla de líneas puede necesitar desplazamiento horizontal.
