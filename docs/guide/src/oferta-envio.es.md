En la pestaña **[[Envío]]** se describe el envío una sola vez, como lo cuenta el cliente: **origen → destino**. Las
líneas toman de aquí lo que necesitan los precios: nada se vuelve a escribir.

![Pestaña Envío de la oferta](img/02-oferta-envio.png)

**Empiece por la plantilla (el caso).** «Plantilla (caso)» —por ejemplo *IMB FOB · Importación marítima FCL*— rellena
el sentido, el modo, la forma de carga, el incoterm, de quién es el cliente, lo que gestiona BOSS y los servicios.
Todo se puede cambiar después.

| Bloque | Campos | Para qué se usa |
|---|---|---|
| Caso | Negocio de (cliente de BOSS / cliente del agente), Sentido, Modo, Forma de carga, Incoterm | Eligen las tarifas. **Tráfico** se calcula: IMB = importación marítima, cliente de BOSS; IMA = la encarga un agente para su cliente |
| Transportista | Transportista principal (naviera o aerolínea), BOSS gestiona (recogida, aduanas, transporte principal, entrega) | Tarifas de esa naviera o aerolínea. El camionero es el proveedor de la recogida o entrega |
| Origen (izquierda) | Expedidor, país, puerto/aeropuerto, dirección de recogida, lugar, **ETD** | En exportación, España es el origen: el puerto de origen es el puerto español y la dirección de recogida da la provincia |
| Destino (derecha) | Destinatario, país, puerto/aeropuerto, dirección de entrega, lugar, **ETA** | En importación, España es el destino: el puerto de destino es el puerto español y la dirección de entrega da la provincia |
| Carga | Peso bruto, volumen, palés, valor | Servicios por kg, tonelada, m³, W/M o palé. Todo es opcional: se puede completar después en el expediente |
| Estimaciones | Días de almacenaje (0 por defecto), derechos de aduana | Servicios por tiempo y porcentajes |

- **El lado extranjero nunca es España** y el lado español se pone en España al elegir el sentido.
- **Direcciones**: un cliente con varios almacenes (p. ej. Leroy Merlin) tiene una dirección de entrega por almacén;
  elija la que toca. Si no tiene, créela desde el mismo campo («Crear y editar»): queda como dirección del cliente.
- **Fechas**: ETD (salida del puerto de origen) y ETA (llegada al de destino). La fecha clave —ETA en importación, ETD
  en exportación— es la **fecha de tarifa**: elige la versión de cada tarifa de proveedor. La «Entrega final al
  cliente» de la cabecera es otra cosa: la entrega en el almacén, que puede ser semanas después de la ETA.
- **Peso tasable aéreo**: el mayor del peso bruto y el peso volumen (volumen × 167 kg/m³). Mientras no hay guía aérea
  (AWB), los precios «por kg tasable de la AWB» lo usan y la explicación dice «ESTIMADO»; al escribir el peso de la
  AWB, manda ese.
- **Puertos y aeropuertos**: los de todo el mundo (lista de Odoo 17). En marítimo solo se proponen puertos; en aéreo,
  aeropuertos.

> Si falta un dato que una tarifa necesita, la línea lo dice («Complete en la oferta: Transportista principal»), sin
> inventar el valor.
