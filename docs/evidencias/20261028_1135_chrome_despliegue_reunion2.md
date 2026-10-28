# Despliegue de la reunión 2 (ADR-009) en boss20, 28/10/2026 11:26 — comprobación en Chrome

Aprobado por Belal («موافقتك على النشر», 28/10). Servidor sin actividad de usuarios (idle guard: SAFE). Commit
`f96dbb3`: boss_services 20.0.1.4.0 (migración de grupos y fecha de tarifa), boss_pricing 20.0.1.11.0,
boss_pricing_sale 20.0.1.13.0, boss_expediente 20.0.1.12.0. Log sin errores; el aviso «Two fields (service_name,
product_id) … same label: Service» ya salía en el despliegue del 27/10 (no es nuevo). Web 200. Guía v=20261028a.

Sobre el código desplegado: `check_meeting2` **69/69** (`docs/evidencias/20261028_1127_check_meeting2_boss20_f96dbb3b1c80.txt`),
incluido el documento del cliente renderizado (oferta de tarifas 20' DV / 40' DV / 40' HC sin importes ni total;
documento normal con totales). Migración en datos reales: todos los servicios BOSS con grupo (0 en «Otros»); FMI/FAI
con fecha de tarifa «salida»; ajustes: aprobación al introducir activa, documento obligatorio activo, coste + 20 %.

| Pantalla (Chrome, usuario de Belal) | Observado |
|---|---|
| S00311 cabecera | Sin «Invoice Address» ni «Delivery Address»; «Final delivery to the client (estimate)» |
| S00311 pestaña Envío | Casilla «Rate quotation (no quantities)» en Caso; encabezado «CONTAINERS OF THE SHIPMENT (SIZE, TYPE, QUANTITY)» |
| S00311 líneas | Columnas «Selling price (unit)» y «Buying cost (unit)» |
| S00311 ⓘ de FMI | «Tariff date 10/27/2026: the quotation date, until the ETD is known (freight rates take the departure).» (origen CNSHA: sigue sin flete aprobado para esa ruta, correcto) |
| E260038 pestaña Summary | Tabla por grupo: Freight 1.800 / 1.500 / 300; Local charges 515 / 409 / 106; Customs 120 / 66 / 54; Total 2.435 venta, 1.975 coste previsto, 460 margen = cifras del expediente |

No visto todavía en pantalla: el asistente ⊕ (origen/destino, nueva versión, aprobación al introducir), el campo
«Pertenece al transportista» en el contacto, el PDF descargado desde Chrome. Las fechas salen en formato en_US
porque los usuarios están en inglés (decisión M2-F).
