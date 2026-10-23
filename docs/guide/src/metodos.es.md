Cada **precio de proveedor** tiene una forma de cálculo; el mismo servicio puede calcularse distinto con proveedores
distintos (por ejemplo, HAN por kg tasable de la AWB en un handler y con factor 333 en otro). Mínimo y máximo se
aplican siempre al **total de la línea**; el resultado se redondea a céntimos. Ejemplos con importes ilustrativos.

## 1. Precio por unidad

Precio × cantidad en la base de cobro (contenedores, BL, kg, m³, horas…).

- 3 contenedores × 200 € = **600 €**.
- «Por 100 kg o fracción», mínimo 20 €: 450 kg → 5 unidades × 3 € = 15 € → **20 €** (mínimo).

## 2. El mayor de dos bases

Se calculan dos importes y se toma el mayor (típico del grupaje: toneladas o m³).

- 2,5 t × 20 €/t = 50 € frente a 4 m³ × 10 €/m³ = 40 € → **50 €**.

## 3. Tramos

Se busca el tramo cuyo «hasta» (incluido) contiene la cantidad. Cada tramo tiene un importe fijo y/o un precio por
unidad que multiplica **toda** la cantidad. «Hasta 0» es el tramo abierto. Por encima del último tramo cerrado no hay
precio (se consulta al proveedor).

| Hasta | Fijo | Por kg |
|---|---|---|
| 100 kg | 50 € | — |
| 500 kg | — | 0,40 € |
| 1.000 kg | — | 0,30 € |

- 100 kg → **50,00 €**; 101 kg → 101 × 0,40 = **40,40 €**; 1.001 kg → **sin precio**.
- Opción «No inferior al tramo anterior»: 501 kg → 501 × 0,30 = 150,30 € < 500 × 0,40 = 200 € → **200,00 €**.
- Opción «Precio del tramo por contenedor»: el importe del tramo se multiplica por los contenedores.

## 4. Porcentaje

Tasa % sobre una base: valor de la mercancía, impuestos del DUA o **coste de otros servicios del mismo proveedor**
en la misma moneda (combustible o seguro sobre el transporte).

- Seguro 5 % del transporte 300,00 € = **15,00 €** (mínimo 1 €).

## 5. Por día con periodo libre

Cantidad por periodo (contenedores, 100 kg…) × precio de cada periodo cobrado. Se calcula con el **periodo real** (inicio
y fin con fecha y hora) cuando se conoce, y si no con una **estimación en días**.

- **Cómo se cuentan los días** (dato de cada precio): **periodos de 24 h** desde el inicio («por 24 horas»: una parte de
  periodo cuenta como periodo entero) o **días naturales** con el día de entrada y el de salida («por día», «se
  contabiliza el día de entrada y el de salida»). Ejemplo: lunes 10:00 → sábado 10:00 = 120 h = 5 periodos de 24 h,
  pero 6 días naturales.
- **Días libres descontados**: solo se pagan los periodos después del periodo libre.
- **Umbral**: superado el periodo libre, se paga **desde el inicio** (habitual en almacenes de aeropuerto). Las horas
  libres se comparan con las **horas exactas**: 48 h 00 min es libre; 48 h 01 min se cobra entera.
- **Tramos**: por número de día desde el inicio («del día 5 al 7»), por días después del periodo libre («5 días a X,
  después Y») o todos los días al tramo que alcanza la estancia completa.
- **Mínimo**: sobre la estancia (total de la línea) o, si el documento dice «/día», sobre cada día cobrado. Una
  estancia dentro del periodo libre cuesta 0, nunca el mínimo.
- **Excepciones por día de la semana**, si el documento las da: inicio en **viernes y salida el lunes** → otro periodo
  libre (WFS: 72 h); inicio en **sábado** → libre hasta el **lunes incluido** (por fecha, no 72 h: sábado 09:00 →
  martes 08:00 son 71 h y se cobran). Dependen del día de salida: solo se aplican con el periodo real; la estimación de
  la oferta no las supone y lo dice. «Viernes +1 día libre» (cualquier salida) existe para documentos que lo digan así.
- **Lecturas sin decidir**: si un documento puede leerse de dos maneras y el negocio no ha decidido (periodos de 24 h o
  días naturales, tramo en los días siguientes o en toda la estancia, «por 100 kg» con o sin fracción), el precio lo
  marca «sin decidir». El sistema calcula todas las lecturas: si dan el mismo importe, hay coste automático; si no, la
  línea queda **«No se calcula automáticamente»** con todos los importes, y se escribe el coste a mano (factura o
  presupuesto del proveedor).

Ejemplo (importes ilustrativos): 7 días libres, «5 días a 30 €, después 80 €», 15 días, 1 contenedor: días 8-12 =
5 × 30 = 150; días 13-15 = 3 × 80 = 240 → **390 €**. Umbral de 48 h, 500 kg por 100 kg a 10 € por periodo: NOA lunes
10:00 → retirada miércoles 10:00 → **0 €**; miércoles 10:01 → 3 × 5 × 10 = **150 €**. Tramos sin decidir (10 € hasta 7
días, 20 € después), 10 días: día a día 7 × 5 × 10 + 3 × 5 × 20 = 650 €; toda la estancia 10 × 5 × 20 = 1.000 € →
coste manual hasta decidir.

- Los días de la oferta se indican una vez en la pestaña Envío y valen para todos los servicios por tiempo (DEM, OCU,
  ALM); una línea puede tener su propia estimación. Sin **días indicados** la línea dice «Faltan datos del envío»;
  0 días indicados es una estimación válida.
- En «Probar precios» se pueden escribir el **inicio y el fin del periodo** (hora de Madrid; Canarias, hora de
  Canarias) para ver el coste real con las excepciones.

> En la oferta el resultado es una **estimación**; con el inicio y el fin reales el sistema recalcula el coste del
> periodo, y la factura del proveedor es la que cuenta en contabilidad. Guía completa del almacenaje aéreo:
> [ALM paso a paso](#/almacenaje).
