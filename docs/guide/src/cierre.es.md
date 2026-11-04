Del expediente entregado al expediente cerrado: estados, condiciones, valoraciones, datos congelados e informe de margen.

## Estados

[[En tránsito]] → **Llegado** → [[Entregado]] → [[Cerrar operaciones]] → [[Cerrar económicamente]].

- **En tránsito**: si faltan la salida real (ATD), el booking, el BL o AWB máster o los números de contenedor, avisa y
  lo anota en el historial, pero no bloquea (práctica de Odoo 17).
- **Llegado** (etapa de Odoo 17): al escribir la **ATA** en **Referencias y fechas**, el expediente pasa solo a Llegado.
  En una consolidación, las casas llegan con su máster.
- **Entregado** pide lo que Cristina escribió y Odoo 17 aplicaba: en importación ATA y descarga del buque; el levante
  si BOSS despacha; la fecha y hora de recogida o entrega si BOSS transporta; y en importación marítima con entrega, el
  HBL liberado o sea waybill. Si falta algo, el mensaje lo dice. Se guarda el día de la entrega.
- **Cerrar operaciones** pide: todo facturado al cliente, ningún aviso de margen sin el motivo escrito por un jefe de
  ventas («Cerrado con margen bajo porque») y las **valoraciones** hechas. No hace falta tener todas las facturas de
  proveedor: se cierra contra la previsión y las facturas tardías se registran sin reabrir.
- **Cerrar económicamente** (contabilidad): todo facturado, costes facturados o cerrados, diferencias revisadas y nada
  en borrador. Solo el administrador contable lo reabre.

La línea **Siguiente paso** de arriba del expediente dice en cada momento qué toca y el botón [[Ir]] lo hace o abre lo
que falta. Pasada una semana desde la entrega avisa: Cristina pide cerrar en una semana.

## Valoraciones

Antes de cerrar operaciones se valora al **cliente** y a **cada proveedor** al que se compró (pedidos confirmados y
facturas), de **0** (muy malo) a **10** (excelente), con un comentario si se quiere. Es la escala de Odoo 17.

- Las partes a valorar aparecen en la pestaña **Valoraciones** al marcar **Entregado**, o con
  [[Listar las partes a valorar]].
- Si se pulsa [[Cerrar operaciones]] sin valorar, el expediente no se cierra: un aviso dice a quién falta valorar.
- La **media** de cada parte se ve en su contacto (pestaña **Ventas y compras**) y en la columna **Valoración** de
  **Servicios a comprar**: ayuda a elegir proveedor.
- Es un ajuste: **Ajustes → Ventas → Valoraciones obligatorias para el cierre operativo** (activado, como en Odoo 17).

## Datos congelados

Con las operaciones cerradas (o el expediente cancelado), los datos del envío quedan **en solo lectura**: partes, ruta,
carga, referencias, fechas, aduana y documento house. Si alguien intenta cambiarlos, Odoo lo rechaza y dice que hay que
reabrir. Siguen abiertos: los servicios y las facturas de proveedor tardías, los contenedores (sus fechas calculan
demoras), el responsable y las valoraciones. Para corregir: [[Reabrir]].

## Margen por expediente

**Expedientes → Margen por expediente** (jefes de ventas y contabilidad): venta pactada, coste y margen previstos y el
margen final, por responsable, comercial, cliente, tráfico y mes, en lista, pivote o gráfico. Se recalcula al abrirlo;
el de un expediente cerrado económicamente queda fijo.
