Guion de la **prueba completa con Ángel y Cristina** antes de la prueba en vivo. Todo se hace en
**https://system.bosscontinental.com** con registros **[PRUEBA]**: se puede confirmar, facturar, pagar y cerrar sin
miedo. Odoo no envía nada fuera (correo desactivado durante las pruebas). Las observaciones se escriben en la hoja
**prueba-completa** (columnas amarillas).

## Cómo se organiza

| Parte | Quién | Qué | Tiempo |
|---|---|---|---|
| 1 | Ángel | Tarifas, oferta, precio de venta, IVA, facturas y cobros | 1 h 30 |
| 2 | Cristina | Expediente, estados, aduana, documentos, consolidación y cierre | 1 h 30 |
| 3 | Los dos | Las preguntas pendientes (abajo) | 30 min |

## Escenarios

| # | Escenario | Dónde | Qué comprobar |
|---|---|---|---|
| 1 | Oferta de importación marítima FCL desde la plantilla | Ventas → Nueva oferta, plantilla «IMB FOB» | Con unas 6 entradas (cliente, plantilla, naviera, puerto de origen, ETA, contenedor) los precios salen; al elegir el puerto se rellena su país; [[Confirmar]] abre un expediente |
| 2 | Aprobar la tarifa WFS | Tarifas y proveedores → Tarifas y documentos, filtro «Pendiente de aprobación» | [[Aprobar]]; después una importación aérea toma el coste de WFS sola |
| 3 | Un expediente de punta a punta | **E260181** (importación FCL) | Seguir el **Siguiente paso** con [[Ir]]: proveedores y costes → pedidos → En tránsito → ATA (Llegado) → aduana → Entregado → orden de transporte → factura (suplidos aparte) → facturas de proveedor → valoraciones → [[Cerrar operaciones]] → datos congelados → cierre económico |
| 4 | Importación aérea | **E260182** | Handler propuesto; ALM por días; AWB house en borrador (⋮ → Imprimir) |
| 5 | Exportación marítima | **E260183** | BL house en borrador → [[Emitir HBL]] → número y fecha |
| 6 | Consolidación | **E260231** con **E260232** y **E260233** | Reparto de costes, margen de cada casa y consolidado, manifiesto del máster, HBL de cada casa |
| 7 | Grupaje de un agente | **E260184** | En negocio de agente se factura al agente (el ordenante) |
| 8 | Mis expedientes | Expedientes | Abre en «Mis expedientes» y «En curso»; filtros «Necesitan acción», «Pendiente en operaciones», «Por facturar o cerrar»; vista tablero |

Las páginas [Cierre](#/cierre), [Consolidaciones](#/consolidacion) y [Documentos de transporte](#/documentos)
explican cada parte.

## Preguntas para la llamada

| Quién | Pregunta |
|---|---|
| Ángel | Tarifa WFS: aprobar o devolver (punto 38) |
| Ángel | Demoras de importación: ¿terminan en la recogida en puerto o en la devolución del vacío? (punto 17) |
| Ángel | Desde el 01/01/2027: ¿SII o VERI*FACTU? |
| Ángel | Plazos de 75 y 90 días de Odoo 17: ¿se siguen usando? (la ley permite 60 días entre empresas) |
| Ángel y Cristina | Expedientes DAP/DDP: ¿se abren al aceptar o al llegar los documentos? |
| Cristina | Almacenaje (ALM): ¿su correo del 25/09 o la cláusula de las ofertas? |
| Cristina | Revisar las 7 plantillas de oferta y sus precios |
