# Escenario de prueba en boss20_uat · UAT scenario (26/10/2026)

Entorno persistente de pruebas en el servidor: **https://system.bosscontinental.com/web?db=boss20_uat** (mismo código
que boss20, datos ficticios [DEMO], sin conexiones externas: crons parados, sin servidor de correo, servicios en línea
hacia un puerto cerrado). Aquí sí se contabiliza y se paga; **boss20** sigue siendo la base de referencia con borradores
(ofertas, expedientes, pedidos en borrador) y sin asientos.

Usuarios de prueba (sin contraseña: Belal la fija en Ajustes → Usuarios → «Cambiar contraseña»): `uat_ventas`
(comercial + compras + introduce tarifas), `uat_operaciones` (jefe de ventas y compras, aprobador de tarifas),
`uat_contabilidad` (facturación). Con ellos se prueba sin ser administrador; la comprobación de permisos del 26/10
(`dev/ws_perm_check.py`) da: ventas lee precios pero no marca clientes de demostración ni aprueba; contabilidad no lee
precios de proveedor; operaciones aprueba.

## 1. Ciclo completo ya ejecutado (compra → venta → ejecución → factura → rentabilidad)

`dev/uat_cycle.py` ejecutó el 26/10 los casos C1–C8 de `docs/pruebas-angel.md` y dejó los registros:

| Caso | Registros en boss20_uat | Qué mirar |
|---|---|---|
| C1 IVA por caso | S00004 (cliente español: DEM 21 %, THC exento Art. 22), S00001 (cliente UE: 0 % UE), S00010 Canarias y S00011 Ceuta (no sujeto), S00012 Suiza (exento extracomunitario), S00013 con CAU (IVA pendiente: no se puede aceptar) | Ventas → Presupuestos; pestaña «Líneas», columna IVA |
| C2 NIF | E260007 / INV/2026/00001 (400 € + 25,20 €): sin NIF no se contabiliza; con NIF sí | Contabilidad → Facturas de cliente |
| C3 Factura de proveedor por cantidad prestada | P00001 (MSC [DEMO]) confirmado; THC marcados como prestados; FACTURA/2026/11/0001 (420 €) con las líneas no prestadas a cantidad 0 | Compras → P00001 → Facturas |
| C4 Pago bloqueado hasta facturar al cliente | FACTURA/2026/11/0001 contabilizada; «Registrar pago» rechazado mientras el THC no está facturado al cliente | Botón «Registrar pago» de la factura |
| C5 Factura de cliente y pagos | INV/2026/00002 (560 €) contabilizada; después la factura de MSC se paga (en pago) y la del cliente se cobra (en pago) | Expediente E260001 → pestaña «Rentabilidad» |
| C6 Factura parcial y abono | INV/2026/00003 (300 de 500 kg de HAN de E260002); RINV/2026/00001 abono de 560 € | E260002: facturado 17,25 €, por facturar 276 € |
| C7 Suplidos (D-2) | Factura del agente de aduanas de 350 € de ARA en la cuenta **419004** (pasivo corriente), contabilizada; factura al cliente del ARA en **419002**, exento no sujeto | Contabilidad → Facturas → línea ARA |
| C8 Rentabilidad | E260001: venta 1.385 €, coste real 770 €, coste pendiente 360 €, margen previsto 255 €; «por hacer» en la cabecera | Expedientes → E260001 |

Hallazgos corregidos con esta ejecución (desplegados en boss20 y boss20_uat el 26/10): el bloqueo de pago (P30) solo
actuaba en el botón de la factura, no en el asistente de pagos (D-3); un pedido sin nada prestado creaba una factura de
ceros (D-4). Están en `docs/preguntas-abiertas.md`.

## 2. Escenarios de oferta y expediente (en boss20_uat y, como borradores, en boss20)

`dev/uat_scenarios.py` creó el 26/10 (boss20_uat: S00015–S00020 y E260010; boss20: S00025–S00030 y E260014) con el
resultado esperado calculado antes desde las tarifas [DEMO]:

| Escenario | Oferta | Resultado comprobado |
|---|---|---|
| S1 Marítimo FCL mixto 2×20' DV + 1×40' HC, plantilla [DEMO] IMB FOB + GLO-FUELEU por TEU | S00015 / S00025 | THC 20' ×2 a 180 €, THC 40' HC a 240 € (la línea de 300 € es solo frigorífico), BL 60 €, **4 TEU** (2 + 2) × 25 €, FMI coste manual, FAD/TTE-FCL/GLO-CCC sin tarifa (nunca 0 «gratis»), CSM lo hace BOSS |
| S2 LCL 1,8 t / 4,5 m³ + inspección SOIVRE | S00016 / S00026 | THC-LCL por W/M = 4,5; THC-LCL, DOC, FAD y SOI «sin precio de proveedor» con la acción de añadirlo |
| S3 Exportación aérea, plantilla [DEMO] EAB, 350 kg | S00017 / S00027 | TTE-CON, HAN (350 kg), AWB, DEX sin tarifa de exportación; FAE coste manual; CSA lo hace BOSS |
| S4 Falta / caducada / conflicto | S00018 / S00028 (fecha prevista 15/12/2026) | BL: **conflicto** entre dos tarifas aprobadas del mismo alcance (60 € y 70 €; la segunda solo vale en diciembre), sin coste elegido y con la explicación; CES sin tarifa; TTE-CON con la tarifa IRENEO 2025 caducada y sin aprobar: sin precio (nunca se aplica) |
| S5 Aéreo aceptado y cambio de peso | S00019 → E260010 / S00029 → E260014 | HAN 500 kg × 0,05 = 25 € → tras poner 620 kg en el expediente y «Recalcular coste previsto»: 31 € (revisión 25 → 31); la venta sigue a 0,12 €/kg |
| S6 Demoras 12 días × 2 contenedores | S00020 / S00030 | DEM: 12 − 7 días libres = 5 días × 30 €/día = 150 € por contenedor (tramo hasta 5 días), THC 40' DV 2 × 240 € |

Además, en boss20 desde Chrome (26/10): expediente E260011, al elegir la aerolínea «Cathay Pacific Airways» el handler
propuesto es **WFS**; al cambiar a «Qatar Airways», **Iberia (handling)** (tabla Expedientes → «Aerolíneas y handlers»,
47 relaciones leídas de Odoo 17).

## 3. Cómo repetir el ciclo a mano (pasos para Belal, en boss20_uat)

1. **Oferta.** Ventas → Nuevo. Cliente «[DEMO] Cliente UE Ejemplo GmbH». Pestaña Envío: importación, marítimo, FCL,
   ESVLC, China, transportista «MSC [DEMO]», fecha prevista, contenedores. Otra información → Plantilla «[DEMO] IMB FOB».
   Comprobar en Líneas el coste (origen de la tarifa con el icono ⓘ) y poner precio de venta o lista de precios.
2. **Aceptar.** «Confirmar» → se abre el expediente (Expedientes → Expedientes) con las necesidades de compra.
3. **Comprar.** En el expediente «Crear solicitudes de presupuesto» → Compras → confirmar el pedido con `uat_operaciones`.
4. **Ejecutar.** Expediente → pestaña «Servicios y costes»: «Marcar prestado» en lo realizado; poner ATA y Recogida real con
   hora (los servicios por tiempo recalculan su periodo); «Recalcular coste previsto» si cambian pesos o contenedores.
5. **Factura del proveedor.** Compras → pedido → «Crear factura» (solo con algo prestado) → fecha, referencia, impuesto
   de la factura del proveedor → Contabilizar. «Registrar pago» se rechaza hasta facturar al cliente.
6. **Factura al cliente.** Expediente → «Facturar servicios» → elegir las partidas → Contabilizar (el cliente español
   necesita NIF). Después se puede pagar la factura del proveedor y cobrar la del cliente.
7. **Rentabilidad.** Expediente → pestaña «Rentabilidad»: venta, facturado, coste real, pendiente, margen previsto y
   final; «Previsión de costes» (menú Expedientes) agrupa el coste previsto por proveedor.

Reconstruir el entorno desde cero: `dev/server_uat.sh build` (instala, siembra y aísla); tras un despliegue en boss20,
`dev/server_uat.sh update boss_expediente`.
