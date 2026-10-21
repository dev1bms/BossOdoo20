# Plan de implementación · Implementation plan (orden por dependencias y valor)

## Hecho (fase 1) · Done
1. Catálogo de 78 servicios con identidad de Odoo 17, clase de IVA, códigos anteriores y forma de cotizar.
2. Tarifas de proveedor con documento, vigencia, versiones, prioridad, aprobación (bloqueada en servidor).
3. Motor: por unidad, mayor de dos bases, tramos, porcentaje, por día (libres, umbral, tramos posicionales/relativos).
4. Oferta desde CRM: datos del envío, añadir servicios, coste explicado, alta de precio que falta, IVA por reglas,
   bloqueo de envío/confirmación, congelación, foto y recotización con motivo.
5. 10 tarifas de muestra (MSC, Hapag, CMA, WFS, IRENEO) y 43 ejemplos de referencia: 0 diferencias.

## Siguiente · Next (en este orden)
1. **Decisiones P17 y P27** (Ángel/Belal): compañía en EUR y localización española, impuestos NR/EX/NS. Sin ellas
   las ofertas reales no se pueden enviar (bloqueo intencionado).
2. **Aprobar las tarifas de muestra** que sigan vigentes (Cristina) y cargar las de uso diario con el importador.
3. **Zonas y precios por cliente**: tarifas de transportistas por zona (provincias) y listas de precios pactados
   por cliente (P01, P15).
4. **Reglas de venta** si se aprueba P01: recargo/margen por servicio con confirmación humana.
5. **Expediente (operaciones)**: abrir el expediente desde la oferta aceptada (foto = base comercial), fechas reales
   y coste real de servicios por tiempo (DEM, OCU, ALM: estimado → real).
6. **Facturación**: factura desde las líneas aceptadas, facturas parciales/múltiples, abonos, coste real por
   facturas de proveedor y cuenta analítica por expediente.
7. **Más métodos solo si un documento lo exige**: tramos de dos dimensiones (kg × km, IRENEO BCN), mínimo por
   contenedor, regla «viernes con retirada el lunes», condición de mercancía peligrosa.
