El **expediente** reúne todo lo de un envío: quién, ruta, carga, referencias, fechas, servicios, compras, facturas y
rentabilidad. Está en la aplicación **Expedientes** (y en **Ventas → Pedidos → Expedientes**).

## Cuándo se abre

- Al **confirmar** una oferta con servicios BOSS se abre su expediente (número **E26xxxx**). Si se vuelve a confirmar o
  se repite la acción, no se abre otro.
- Si el envío empieza **antes** de la oferta (prealerta, documentos recibidos), cree el expediente a mano desde
  **Expedientes**: queda como **preliminar**. Cuando se acepte la oferta, elija ese expediente en el campo
  **Expediente** de la oferta (pestaña **Envío**).
- Un servicio vendido **después** va en una oferta nueva vinculada: botón [[Vender otro servicio]] del expediente.
- Un acuerdo para varios envíos: cada envío es una oferta repetida (Duplicar) y por tanto su propio expediente.

## Qué contiene

- **Quién**: cliente contratante, responsable, cargador, consignatario, agente, transportista; en **Referencias y
  fechas**, notify, transportista terrestre y agente de aduanas.
- **Ruta**: sentido, modo, tipo de carga, incoterm, origen y destino, puerto, país y lo que hace BOSS (recogida,
  aduana en origen, transporte principal, aduana en destino, entrega).
- **Carga**: mercancía, bultos, peso, volumen, palés y un renglón por contenedor con número, precinto, recogida del
  lleno y devolución del vacío.
- **Referencias y fechas**: booking, BL master/house (o AWB), buque/vuelo, viaje, DUA; ETD/ETA previstas y ATD/ATA
  reales en campos distintos.
- **Eventos**: hitos, incidencias y notas con fecha y usuario; además el chatter con actividades y adjuntos.

Los datos del expediente se copian **una vez** de la oferta aceptada. Después cada uno guarda lo suyo: la oferta lo
pactado, el expediente lo real. En **Resumen → Diferencias con la oferta** se ve qué cambió (contenedores, pesos,
transportista, fechas). Nada se sincroniza solo.

## Estados y cierre

[[En tránsito]] → [[Entregado]] → [[Cerrar operaciones]]. El cierre **económico** es aparte:
[[Cerrar económicamente]] solo se permite con todo facturado, todos los costes facturados o cerrados, diferencias
revisadas y nada en borrador. El aviso amarillo **Pendiente** dice qué falta.

## Cuenta analítica

Cada expediente tiene su cuenta analítica (plan **Expedientes**). Se pone sola en las líneas de venta, en las de compra
y, desde ellas, en las facturas. Así el coste y el ingreso de cada envío se leen de la contabilidad, sin importes
escritos a mano.
