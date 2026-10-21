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

Cantidad por día (contenedores, 100 kg…) × precio de cada día cobrado.

- **Días libres descontados**: solo se pagan los días después del periodo libre.
- **Umbral**: superado el periodo libre, se paga **desde el día 1** (habitual en almacenes de aeropuerto). Las horas
  libres cuentan como días completos en la oferta (48 h = 2 días).
- **Tramos**: por número de día desde el inicio («del día 5 al 7»), por días después del periodo libre («5 días a X,
  después Y») o todos los días al tramo que alcanza la estancia completa.

Ejemplo: 7 días libres, «5 días a 30 €, después 80 €», 15 días, 1 contenedor: días 8-12 = 5 × 30 = 150; días 13-15 =
3 × 80 = 240 → **390 €**. Con umbral de 48 h, 500 kg por 100 kg a 10 €/día: 2 días → **0 €**; 3 días → 3 × 5 × 10 =
**150 €**.

> En la oferta el resultado es una **estimación** con los días supuestos; el coste real se conoce al terminar el periodo.
