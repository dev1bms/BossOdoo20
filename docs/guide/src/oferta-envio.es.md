En la pestaña **[[Envío]]** se describe el envío una sola vez, como lo cuenta el cliente: **origen → destino**. Las
líneas toman de aquí lo que necesitan los precios: nada se vuelve a escribir.

![Pestaña Envío de la oferta](img/02-oferta-envio.png)

**Empiece por la plantilla (el caso).** «Plantilla (caso)» —por ejemplo *IMB FOB · Importación marítima FCL*— rellena
el sentido, el modo, la forma de carga, el incoterm, de quién es el cliente, lo que gestiona BOSS y los servicios.
Todo se puede cambiar después.

| Bloque | Campos | Para qué se usa |
|---|---|---|
| Caso | Negocio de (cliente de BOSS / cliente del agente), Sentido, Modo, Forma de carga, Incoterm y su **lugar convenido** | Eligen las tarifas. **Tráfico** se calcula: IMB = importación marítima, cliente de BOSS; IMA = la encarga un agente para su cliente |
| Transportista | Transportista principal (naviera o aerolínea), **Transportista terrestre** (se muestra solo: es el proveedor de la línea de transporte terrestre y pasa al expediente), BOSS gestiona (recogida, aduanas, transporte principal, entrega) | Tarifas de esa naviera o aerolínea; el transportista terrestre se elige en la línea TTE |
| Origen (izquierda) | Expedidor, país, puerto/aeropuerto, dirección de recogida, lugar, **ETD** | En exportación, España es el origen: el puerto de origen es el puerto español y la dirección de recogida da la provincia |
| Destino (derecha) | Destinatario, país, puerto/aeropuerto, dirección de entrega, lugar, **ETA** | En importación, España es el destino: el puerto de destino es el puerto español y la dirección de entrega da la provincia |
| Carga | Peso bruto, volumen, palés, valor | Servicios por kg, tonelada, m³, W/M o palé. Todo es opcional: se puede completar después en el expediente |
| Estimaciones | Días de almacenaje (0 por defecto), derechos de aduana | Servicios por tiempo y porcentajes |

- **España se propone, no se impone**: en importación y exportación el lado español se pone en España al elegir el
  sentido y el lado extranjero nunca es España; en un envío **Nacional** los dos lados son España; en un **Cruzado** (ni
  origen ni destino en España) no se rellena nada y solo aplican precios de proveedor sin puerto español ni país en su
  ámbito. El tráfico lo dice: IMB, EAB, **XMB**, **NTB**…
- **Direcciones**: un cliente con varios almacenes (p. ej. Leroy Merlin) tiene una dirección de entrega por almacén;
  elija la que toca. Si no tiene, créela desde el mismo campo («Crear y editar»): queda como dirección del cliente.
- **Fechas**: ETD (salida del puerto de origen) y ETA (llegada al de destino). La fecha clave —ETA en importación, ETD
  en exportación, cruzado y nacional— es la **fecha de tarifa**: elige la versión de cada tarifa de proveedor. La fecha
  de vaciado de un LCL (en el expediente) nunca elige la tarifa. La «Entrega final al
  cliente» de la cabecera es otra cosa: la entrega en el almacén, que puede ser semanas después de la ETA.
- **Peso real, peso volumen y peso tasable** (Ángel, 27/10/2026): peso volumen = m³ × factor del modo (**aéreo 167,
  terrestre 333, marítimo 1000** kg/m³); peso tasable = **el mayor** del bruto y el volumen. Los proveedores cobran a
  BOSS por peso tasable y BOSS cobra al cliente por peso tasable: los servicios «por kg tasable» toman esa cantidad.
  Hacen falta las dos medidas; con una desconocida no se supone nada (y los precios por peso dicen «faltan datos»).
  En aéreo, mientras no hay guía aérea (AWB), los precios «por kg tasable de la AWB» usan el peso tasable y la
  explicación dice «ESTIMADO»; al escribir el peso de la AWB, manda ese. Un documento de proveedor con su propio factor
  lo conserva.
- **Puertos y aeropuertos**: los de todo el mundo (lista de Odoo 17). En marítimo solo se proponen puertos; en aéreo,
  aeropuertos.
- **Contenedores**: [[Añadir una línea]] y **elija el tamaño** (20'/40'/45'): la fila solo queda cuando se elige algo;
  luego tipo y cantidad. Los servicios por contenedor toman el tamaño y la cantidad (2 × 40' → cantidad 2; por envío,
  1), también si los contenedores se indican después de la plantilla.
- **Ordenante y partes**: en negocio de BOSS, el ordenante se propone como destinatario (importación) o expedidor
  (exportación); se puede cambiar. En negocio de agente no se copia nada: el agente encarga, y el expedidor y el
  destinatario son otros.
- **Aceptar**: si falta algo, el mensaje lo agrupa por causa (precio de venta que falta; IVA pendiente porque el
  cliente no tiene país…) y dice qué hacer. Al aceptar se abre **un** expediente con los costes a comprar; el campo
  «Vincular a un expediente existente» solo sirve para un expediente abierto antes (preaviso).

> Si falta un dato que una tarifa necesita, la línea lo dice («Complete en la oferta: Transportista principal»), sin
> inventar el valor.
