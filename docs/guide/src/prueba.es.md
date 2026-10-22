Recorrido completo en **https://system.bosscontinental.com** con datos de prueba marcados **[DEMO]** (cliente,
naviera, transportista y handler ficticios, precios ficticios). El cliente de prueba no tiene correo: no se envía nada a
nadie.

## Qué hay preparado

| Dato | Contenido |
|---|---|
| Clientes | [DEMO] Cliente Ejemplo, S.L. (Valencia) y [DEMO] Cliente UE Ejemplo GmbH (Hamburgo), con la lista de precios «[DEMO] … acuerdo de precios»: THC pactado a 230 € por contenedor; DEM coste + 15 % con margen mínimo de 30 € por contenedor; resto coste + 15 % |
| Tarifas | [DEMO] Naviera Ejemplo (THC por contenedor, DEM por día), [DEMO] Transportista Ejemplo (transporte por contenedor y recargo de combustible del 8 %), [DEMO] Handler Aéreo Ejemplo (ALM con 48 h y regla del sábado, HAN por kg). **Enviadas a aprobación, sin aprobar** |
| Oportunidades | «[DEMO] Importación 2x20' + 1x40'HC Shanghái - Valencia», «[DEMO] Importación 1x40'HC Shanghái - Valencia para cliente UE» y «[DEMO] Importación aérea 500 kg Shanghái - Madrid» |
| Sin precio a propósito | CES (cesión de contenedor): para probar «Añadir precio de proveedor» |

![Tarifas de prueba enviadas a aprobación](img/18-prueba-tarifas.png)

## Pasos que necesitan a una persona concreta

| Paso | Quién | Dónde |
|---|---|---|
| A. Aprobar las tres tarifas [DEMO] (revisar documento y precios) | **Belal** (aprobador) | Ventas › Productos › Tarifas de proveedor › abrir › [[Aprobar]] |
| B. Decidir el impuesto de EX para clientes españoles (P17) | **Ángel** | Después, una fila en Ventas › Configuración › Tabla de IVA BOSS |
| C. Aprobar el precio de CES añadido desde la oferta | **Belal** | Desde la línea (icono de revisar) o la lista de tarifas |

El IVA de NR, de clientes de la UE y de terceros países y de los suplidos ya está en la tabla. Sin el paso B, la oferta
del **cliente español** se queda en «IVA pendiente» solo por THC (EX) y no se puede enviar ni confirmar: es lo esperado.
La oferta del **cliente UE** llega hasta la aceptación.

## Recorrido marítimo (FCL)

1. **CRM** › oportunidad «[DEMO] Importación 2x20'…» › [[Nuevo presupuesto]].
2. Pestaña **[[Envío]]**: Importación · Marítimo · FCL · naviera «[DEMO] Naviera Ejemplo» · puerto ESVLC · país China ·
   fecha prevista 04/11/2026 · contenedores 2 × 20' DV y 1 × 40' HC · días 12.
3. [[Añadir servicios]]: THC, DEM, TTE-FCL, FS y CES → una línea por tamaño de contenedor.
4. **Coste**: THC 150 € y 200 € por contenedor; DEM estimación 12 días (7 libres): 5 × 30 € por contenedor; transporte
   320 € por contenedor; FS 8 % del transporte del mismo transportista; CES **Sin precio**.
5. **Venta** (columna Venta): THC 230 € «Precio pactado»; el resto «Sobre el coste previsto» (+15 %); DEM 180 € porque
   aplica el margen mínimo de 30 € por contenedor.
6. **CES**: icono [[Añadir precio de proveedor]] → 45 € por contenedor, página 3, adjuntar un PDF cualquiera de prueba →
   [[Guardar precio]] → «Pendiente de aprobación» → paso C → CES con coste y venta.
7. **IVA**: DEM, transporte, FS y CES (NR, cliente de Valencia, importación de China) → 21% S; THC (EX, cliente
   español) → **IVA pendiente** con el motivo. [[Enviar]] o [[Confirmar]] dicen que solo falta el IVA de THC.

## Recorrido con cliente de la UE (hasta la aceptación)

1. Oportunidad «[DEMO] Importación 1x40'HC … para cliente UE» › [[Nuevo presupuesto]] › Envío como el anterior con
   1 × 40' HC y días 10.
2. [[Añadir servicios]]: THC, DEM, TTE-FCL y FS. IVA de todas las líneas: **0% UE S** (EX por ser cliente de la UE).
3. **[[Confirmar]]** (no use Enviar con clientes reales) → precios congelados, foto en **Historial de precios** con
   el impuesto de cada línea, botón [[Recotizar]].

![Oferta aceptada de un cliente de la UE](img/13-oferta-aceptada.png)

## Recorrido aéreo

1. Oportunidad «[DEMO] Importación aérea 500 kg…» › [[Nuevo presupuesto]] › Envío: Importación · Aéreo · aeropuerto
   MAD · país China · fecha 04/11/2026 (miércoles) · peso tasable (AWB) 500.
2. [[Añadir servicios]]: ALM y HAN. ALM dice **«Faltan datos del envío: días»** hasta que se indican días; HAN toma
   500 kg de la AWB: 500 × 0,08 € = 40 €.
3. Días 4 → ALM 4 periodos × 5 (100 kg) × 10 € = 200 € (superadas las 48 h se cobra desde el día 1).
4. Fecha 07/11/2026 (sábado) y días 3 → ALM 0 € (libre hasta el lunes incluido).

![Oferta aérea de prueba: ALM y HAN](img/19-prueba-aereo.png)

## Comprobado en el servidor

El recorrido completo se ha ejecutado en el servidor con un comercial y un aprobador de prueba, dentro de una
transacción que se deshace al final (la base no cambia): 28 comprobaciones correctas, incluida la aceptación de la
oferta del cliente UE con la tabla de IVA real.
