Cada línea busca el **precio de proveedor aprobado** que corresponde al servicio, su base de cobro, el envío y la
fecha prevista. El resultado se ve en la columna **Coste**; el icono ⓘ abre la explicación.

![Explicación del cálculo de una línea](img/04-detalle-calculo.png)

La explicación muestra el cálculo («1 × 200,00 € por Contenedor = 200,00 €»), la tarifa con su versión, el proveedor,
la vigencia, el **documento y la página**. El coste unitario va al campo estándar de coste de Odoo, así que el
margen de la línea y de la oferta son los de Odoo.

## Estados del coste

| Estado | Significa | Qué hacer |
|---|---|---|
| Cotizado | Hay un precio aprobado y se ha calculado | — |
| Faltan datos del envío | Falta un dato que la tarifa necesita (naviera, fecha, contenedores, peso…) | Completar la pestaña Envío |
| Sin precio de proveedor | Ninguna tarifa aprobada se aplica | [[Añadir precio de proveedor]] (ver paso 5) |
| Precio pendiente de aprobación | Hay un precio introducido sin aprobar | Lo aprueba un aprobador |
| A consultar | El documento dice «a consultar» | Pedir precio al proveedor |
| Varios precios aplican | Dos tarifas con el mismo alcance | Elegir naviera, acotar una tarifa o fijar prioridad |
| No se cotiza automáticamente | Servicio pendiente de decisión | Coste manual si hace falta |
| Importe manual | Servicio que se cotiza por oferta (flete) o a coste (suplidos) | Escribir el coste unitario y su referencia |
| Otra moneda, sin política | La tarifa está en otra moneda que la oferta | Ver [IVA y monedas](#/iva-moneda) |

> Un coste **cero** solo aparece cuando está justificado (honorario propio, o días dentro del periodo libre); nunca
> por falta de precio.
