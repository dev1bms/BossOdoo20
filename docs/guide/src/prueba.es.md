Recorrido completo en **https://system.bosscontinental.com** con datos de prueba marcados **[DEMO]** (cliente,
naviera, transportista y handler ficticios, precios ficticios). El cliente de prueba no tiene correo: no se envía nada a
nadie.

## Qué hay preparado

| Dato | Contenido |
|---|---|
| Cliente | [DEMO] Cliente Ejemplo, S.L. (Valencia), con su lista de precios «[DEMO] … acuerdo de precios»: THC pactado a 230 € por contenedor; DEM coste + 15 % con margen mínimo de 30 € por contenedor; resto coste + 15 % |
| Tarifas | [DEMO] Naviera Ejemplo (THC por contenedor, DEM por día), [DEMO] Transportista Ejemplo (transporte por contenedor y recargo de combustible del 8 %), [DEMO] Handler Aéreo Ejemplo (ALM con 48 h y regla del sábado, HAN por kg). **Enviadas a aprobación, sin aprobar** |
| Oportunidades | «[DEMO] Importación 2x20' + 1x40'HC Shanghái - Valencia» y «[DEMO] Importación aérea 500 kg Shanghái - Madrid» |
| Sin precio a propósito | CES (cesión de contenedor): para probar «Añadir precio de proveedor» |

![Tarifas de prueba enviadas a aprobación](img/18-prueba-tarifas.png)

## Pasos que necesitan a una persona concreta

| Paso | Quién | Dónde |
|---|---|---|
| A. Aprobar las tres tarifas [DEMO] (revisar documento y precios) | **Belal** (aprobador) | Ventas › Productos › Tarifas de proveedor › abrir › [[Aprobar]] |
| B. Elegir el impuesto de Odoo para NR, EX y NS | **Ángel** (decisión), lo introduce Belal | Ventas › Configuración › Ajustes › IVA de los servicios BOSS |
| C. Aprobar el precio de CES añadido desde la oferta | **Belal** | Desde la línea (icono de revisar) o la lista de tarifas |

Sin el paso B la oferta llega hasta el final pero **no se puede enviar ni confirmar** (IVA pendiente): es lo esperado.

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
7. [[Enviar]] o [[Confirmar]]: sin el paso B, mensaje con el IVA pendiente línea a línea. Con el paso B: **[[Confirmar]]**
   (no use Enviar con clientes reales) → precios congelados, foto en **Historial de precios**, botón [[Recotizar]].

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
transacción que se deshace al final (la base no cambia): 20 comprobaciones correctas, incluida la aceptación con una
asignación de IVA **temporal** solo para probarla.
