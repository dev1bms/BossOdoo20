Almacenaje aéreo (**ALM**): qué cubre el sistema, qué datos necesita, cómo se calcula la compra y la venta, y qué sigue
pendiente de una decisión. Importes **ilustrativos** (los precios reales de proveedor no se publican).

## Estado a 23/10/2026

| Caso | Documento del proveedor | En el sistema | Estado |
|---|---|---|---|
| WFS MAD/BCN importación, carga general | WFS V 2026-02 (desde 01/06/2026) p.5 punto 1 | Tarifa de muestra pendiente de aprobar | **Automático en parte**: solo cuando las lecturas sin decidir (P29, P40, P41) dan el mismo importe |
| WFS MAD/BCN exportación, carga general | Mismo punto (precios y mínimo de exportación) | Tarifa de muestra pendiente de aprobar | **Automático en parte**, como la importación (FOH → ETD) |
| WFS VLC | p.5 (por día natural, 3 días; viernes con salida el lunes, 4) | Sin tarifa | Mecánica lista (días naturales); falta tarifa |
| WFS frío, peligrosas, valiosas, animales vivos | Puntos 2–6 (otras horas libres, precios y mínimos) | Sin condición de tipo de carga | **Coste manual** (P44) |
| IRENEO almacén MAD/BCN | Tarifas 2025 (por 100 kg o fracción y día natural, 333 kg/m³) | Sin tarifa | Vigencia 2026 sin confirmar (P28) |
| Almacén fuera del aeropuerto (palé, m³, entrada/salida) | — | No es ALM | Código propio pendiente de Cristina y Ángel (P44) |
| Almacenaje incluido en un paquete (p. ej. IRENEO exportación: 3 días naturales dentro del handling) | IRENEO p.4 | El paquete es HAN | Los días incluidos se escriben como franquicia en la tarifa ALM de ese proveedor (así lo dice IRENEO): solo se cobran los días después. Sin esa tarifa no hay control automático: no añadir ALM por los días del paquete |
| Almacenaje en puerto (contenedores) | Navieras | DEM / OCU / DET | No es ALM |

Venta: **sin regla automática**. Cristina (08/10) pidió un precio de venta único de ALM para todos los clientes; los
valores no están aprobados (P43). Mientras tanto, el precio de venta se escribe en la línea.

## 1. Qué datos necesita

| Dato | Dónde | Para qué |
|---|---|---|
| Peso cargable de la AWB | Oferta, pestaña Envío; expediente | WFS cobra sobre «el peso cargable indicado en el AWB». Sin él: «Faltan datos del envío» (nunca se supone 167 ni 333) |
| Aeropuerto, sentido y fecha prevista | Oferta, pestaña Envío | Eligen la tarifa (MAD/BCN, importación o exportación) y su versión |
| Días de almacenaje (estimación) | Oferta, pestaña Envío (o la línea) | Estimación del coste en la oferta. Sin indicar: falta el dato; 0 indicado es una estimación válida |
| Inicio y fin del periodo | Expediente, línea ALM (y «Probar precios») | Coste del periodo real: importación NOA → retirada; exportación FOH (entrada en almacén) → ETD (Cristina 25/09) |

Las horas se escriben en hora de Madrid (Canarias: hora de Canarias). El sistema resta los dos momentos en horas
exactas, también con el cambio de hora.

## 2. Cómo se define la tarifa

En el precio del proveedor (Tarifas y proveedores → Precios), servicio ALM, base de cobro **Expediente**:

| Campo | WFS MAD/BCN carga general | Por qué |
|---|---|---|
| Cálculo | Por día con periodo libre | — |
| Se cobra sobre | Peso cargable de la AWB · tamaño 100 | «por 100 kg» |
| O fracción / sin decidir | «O fracción» sin marcar · **«O fracción sin decidir»** marcado | 2026 no dice «o fracción» (P41) |
| Días contados como | **Sin decidir** (24 h o días naturales) | «por 24 horas» frente a la nota del 10/09 (P40) |
| Horas libres | 48 · modo **Umbral** | «Franquicia de 48 horas … se facturará desde el NOA, incluido» |
| Libre si viernes a lunes | 72 | «viernes y salida en lunes, 72 horas» |
| Sábado hasta lunes | Marcado | «en sábado, franquicia hasta el lunes incluido» |
| Tramos | Hasta 7 · Más (0) · modo **Sin decidir** | «Hasta 7 días / Más de 7 días» (P29) |
| Mínimo | El del documento · «Mínimo por día» sin marcar | Sin unidad impresa: por estancia (P42) |

Cuando Cristina decida una lectura, se cambia ese campo en una **nueva versión** de la tarifa y el cálculo pasa a ser
automático en todos los casos.

![Precio ALM de demostración: horas libres, viernes a lunes, sábado hasta lunes y las tres lecturas «sin decidir»](img/29-alm-precio.png)

**Qué se muestra y qué se calcula.** La línea de la oferta y del expediente es **1 Expediente** con el importe total del
almacenaje; el cálculo interno es «unidades de 100 kg × periodos × precio». El total se calcula una vez y no se vuelve a
multiplicar al pasar a la venta ni al pedido de compra (1 × total).

## 3. Cómo se calcula la compra

Tarifa ilustrativa con los mismos campos que la de WFS (lecturas sin decidir incluidas): 500 kg = 5 unidades, 10 € por unidad y periodo hasta 7, 20 € después, 48 h libres, mínimo 50 €.

| Llegada (NOA) → salida | Horas | Resultado | Por qué |
|---|---|---|---|
| lun 10:00 → mié 10:00 | 48 h 00 | **0 €** | No supera 48 h (libre de verdad: no se cobra el mínimo) |
| lun 10:00 → mié 10:01 | 48 h 01 | **150 €** | Superadas: desde el NOA, 3 periodos (y 3 días naturales) × 5 × 10 |
| vie 09:00 → lun 08:00 | 71 h | **0 €** | Viernes con salida el lunes: 72 h libres |
| vie 09:00 → lun 10:00 | 73 h | **200 €** | Supera 72 h: 4 periodos desde el NOA |
| vie 09:00 → dom 11:00 | 50 h | **150 €** | Sale en domingo: valen las 48 h |
| sáb 09:00 → lun 23:59 | 63 h | **0 €** | Sábado: libre hasta el lunes incluido |
| sáb 09:00 → mar 08:00 | 71 h | **sin precio automático** | Fuera de la excepción: 3 periodos de 24 h (150 €) o 4 días naturales (200 €), P40 |
| lun 10:00 → jue 22/10 10:00 | 240 h | **sin precio automático** | 10 periodos: día a día 650 €; toda la estancia 1.000 € (y con días naturales, otros dos importes), P29 |
| 80 kg, lun 10:00 → jue 09:00 | 71 h | **mínimo** | Todas las lecturas quedan por debajo del mínimo |

Con «sin precio automático» la línea dice **«No se calcula automáticamente»**, muestra cada importe posible y se
escribe el coste a mano (factura o presupuesto del proveedor). En la oferta, una línea así no se acepta sin coste: es un
servicio de proveedor con coste desconocido.

**Estimación de la oferta.** Con días, sin horas: 48 h libres = hasta 2 días; las excepciones de viernes y sábado no se
suponen (dependen del día de salida) y la explicación lo dice. Ejemplo: llegada prevista en sábado, 3 días → se estima
cobrado; con el periodo real se aplicará la excepción si sale el lunes.

![Oferta: estimación de 3 días desde un viernes; la excepción del viernes no se supone y se dice](img/30-alm-oferta-estimacion.png)

![Oferta de 10 días: «No se cotiza automáticamente», un importe por lectura que lo cambia (aquí, los tramos)](img/31-alm-sin-precio-automatico.png)

![Probar tarifa con el periodo real: viernes 09:00 → lunes 10:00 = 73 h, 72 h superadas, 4 periodos desde el inicio](img/32-alm-probar-periodo-real.png)

## 4. Venta

- La venta de ALM **no se calcula sola**: no hay valores aprobados del precio único (P43). Se escribe el precio de venta
  en la línea (o se usa una lista de precios del cliente si tuviera uno pactado).
- El precio aceptado no cambia aunque cambie la estancia: la diferencia de coste se ve en el expediente y se decide
  (reclamar al cliente con «Refacturar», o la asume BOSS).
- «Mayor coste de proveedor + %» es una propuesta sin aprobar: el sistema no la aplica.

## 5. De la oferta a la factura: tres importes distintos

| Importe | Dónde | Qué es |
|---|---|---|
| **Estimación** | Oferta (y foto al aceptar) | Días supuestos; no es un coste real |
| **Calculado con el periodo real** | Expediente, pestaña «Servicios y costes», tras «Recalcular coste previsto» | Inicio y fin reales con la tarifa; queda en «Recálculos de coste» con sus datos |
| **Coste contable** | Factura del proveedor contabilizada | Lo que cuenta en la rentabilidad final |

Pasos:

1. **Oferta**: indicar peso cargable, aeropuerto y días estimados; ALM muestra la estimación y sus supuestos.
2. **Aceptar**: se guarda la foto de la oferta (coste, venta y días) y se abre el expediente con la necesidad de compra.
3. **Expediente**, pestaña «Servicios y costes»: en la línea ALM escribir **Inicio del periodo** (NOA o FOH) y **Fin del
   periodo** (retirada o ETD) y pulsar **Recalcular coste previsto**. Cambian el coste previsto y los días; la venta
   aceptada no; el cambio queda en «Recálculos de coste». Si las lecturas sin decidir dan importes distintos, el coste
   previsto no cambia y el recálculo muestra todos los importes: escribir el «Coste unitario previsto» a mano.
4. **Compra**: «Crear solicitudes de presupuesto» crea una sola línea ALM por expediente (1 × total) al proveedor; si
   la solicitud sigue en borrador, el recálculo la actualiza; si el pedido ya está confirmado, no lo cambia y lo marca
   «Pedido a revisar».
5. **Factura del proveedor**: desde el pedido. Solo cuentan las facturas **contabilizadas** (un borrador no es coste);
   un abono rebaja el importe facturado. El expediente compara lo facturado con lo pedido o previsto («Diferencia»).
6. **Diferencia**: si la factura es mayor por más días, «Refacturar al cliente» con motivo, o dejarla como asumida
   por BOSS («Diferencia revisada» y su nota). Recalcular otra vez no crea costes, pedidos ni recálculos repetidos.

![Expediente: línea ALM con inicio y fin del periodo, días contados y coste previsto](img/33-alm-expediente-periodo.png)

![Recálculos de coste: 150 → 0 (viernes a lunes, 71 h), 0 → 200 (73 h) y «sin cálculo automático» al alargarse la estancia](img/34-alm-recalculos.png)

Capturas de la base de pruebas local con datos [DEMO] (importes ficticios; la moneda de esa base es USD).

## 6. Qué es automático y qué necesita una persona

- Automático: elegir la tarifa, contar horas y días, la franquicia de 48 h, las excepciones de viernes y sábado con las
  fechas reales, el mínimo, el historial de recálculos, el aviso de pedido a revisar y la comparación con la factura.
- Necesita una persona: aprobar la tarifa (P19), escribir el coste cuando las lecturas sin decidir difieren, la venta de
  ALM (P43), la carga especial (P44) y decidir qué se hace con una diferencia.
- Necesita una decisión de Cristina: P29 (tramos), P40 (24 h o días naturales), P41 (fracción de 100 kg), P42 (unidad
  del mínimo), P43 (venta única), P44 (almacenajes especiales y almacén fuera del aeropuerto).

## 7. Pruébelo usted mismo ([DEMO] en el servidor)

Registros ficticios (cliente, handler y precios [DEMO]; nada contabilizado ni enviado):

| Registro | Qué muestra |
|---|---|
| [Tarifa [DEMO] Handler ALM 2026](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/29) | Los campos de la sección 2 con lecturas «sin decidir» |
| [Oferta S00020](https://system.bosscontinental.com/odoo/action-sale.action_quotations_with_onboarding/20) | Aceptada: estimación de 3 días desde un viernes (150) y venta tecleada (180) |
| [Expediente E260011](https://system.bosscontinental.com/odoo/action-boss_expediente.boss_expediente_action/11) | Periodo viernes 16/10 09:00 → lunes 19/10 08:00 (0), 10:00 (200), solicitud P00004; alargado al 26/10 (sin cálculo automático) |
| [Oferta S00021](https://system.bosscontinental.com/odoo/action-sale.action_quotations_with_onboarding/21) | 10 días: «No se cotiza automáticamente» con los dos importes |

Pasos para probar:

1. En **E260011**, pestaña «Servicios y costes», cambie el **Fin del periodo** de la línea ALM (por ejemplo, lunes
   19/10 08:00) y pulse **Recalcular coste previsto**: el coste previsto pasa a 0 y aparece un recálculo nuevo.
2. Cambie el fin a **domingo 18/10 11:00** (50 h, sale en domingo): se cobra (valen las 48 h).
3. Pruebe un **sábado**: inicio sábado 17/10 09:00 y fin lunes 19/10 23:00 → 0; fin martes 20/10 10:00 → cobrado.
4. En **Tarifas y proveedores → Probar tarifa**, servicio ALM, aeropuerto MAD, cliente [DEMO], peso AWB 500 y el
   inicio y fin del periodo: el mismo cálculo sin guardar nada.
5. En **S00021**, botón de detalle de la línea ALM: los importes de cada lectura sin decidir.

## 8. Cómo se ha comprobado

- Motor, sin Odoo: 21 pruebas con importes calculados a mano (48 h 00 / 48 h 01, 120 h = 5 periodos o 6 días, cambio
  de hora, viernes → lunes / domingo / martes, sábado → lunes / martes, tramos de 7, 8 y 10 días, mínimo por estancia y
  por día, «o fracción» en 100, 100,01, 400 y 401 kg, factor 333, datos que faltan o incoherentes).
- Odoo (base de pruebas desechable): oferta, «Probar tarifa» con el periodo real, expediente con periodo, recálculos
  sin duplicados, solicitud y pedido, factura de proveedor en borrador (no cuenta) y contabilizada, abono, y un usuario
  de operaciones que no puede cambiar ni aprobar una tarifa.
- Ejemplos de referencia del documento WFS (importes privados, no publicados): 57 ejemplos sin diferencias en la base
  de pruebas y en el servidor (con deshacer).
