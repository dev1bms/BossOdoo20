# Escenario de prueba de punta a punta · End-to-end test scenario (26/10/2026)

Entorno: **https://system.bosscontinental.com/web?db=boss20_uat** (copia de pruebas en el servidor: mismo código que
boss20, datos [DEMO], sin correo ni conexiones externas; aquí sí se contabiliza y se paga). En boss20 (la base principal)
se puede hacer todo hasta «servicio prestado» con borradores; la contabilidad (facturas contabilizadas, abonos, pagos)
solo en boss20_uat.

Usuarios por rol en boss20_uat (sin contraseña: ponla en Ajustes → Usuarios → «Cambiar contraseña» antes de usarlos):
`uat_ventas` (comercial, introduce precios de proveedor, no los aprueba), `uat_operaciones` (jefe de ventas y compras,
aprueba tarifas), `uat_contabilidad` (facturación, no ve precios de proveedor).

## Escenario nuevo para ti: importación marítima FCL con cliente español

Datos ficticios. Lo esperado está calculado con las tarifas [DEMO] (MSC gastos locales Valencia 2026, cliente español).

| Paso | Dónde y qué hacer | Qué debe pasar |
|---|---|---|
| 1. Cliente y envío | Ventas → Nuevo. Cliente «[DEMO] Cliente Ejemplo, S.L.». Pestaña **Envío**: Importación, Marítimo, FCL, ESVLC, China, transportista «MSC [DEMO]», fecha prevista 10/11/2026, días de almacenaje 10. Contenedores: 1 × 20' DV y 1 × 40' HC | El aviso «Precio por completar» desaparece a medida que completas |
| 2. Servicios | Otra información → Plantilla «[DEMO] IMB FOB». Después «Añadir servicios» → DEM | Una línea por servicio; THC, FMI, GLO-CCC, TTE-FCL y DEM separados por tamaño de contenedor |
| 3. Proveedor, coste y venta | Pestaña Líneas: THC 20' 180 €, THC 40' HC 240 €, DEM 90 € cada uno (10 días − 7 libres = 3 × 30 €). FMI: columna «Coste manual» (activarla en ⚙) 900 € y proveedor MSC. FAD, GLO-CCC, BL, TTE-FCL: «Sin precio de proveedor» (nunca 0): añade su precio desde el icono ⓘ / «Añadir precio de proveedor» y apruébalo con `uat_operaciones`, o bórralas. Pon el precio de venta de las que lo pidan | Cliente español: THC exento art. 22, DEM 21 %; «Confirmar» se rechaza si falta un precio de venta o un IVA |
| 4. Aceptar | «Confirmar» | Pedido de venta bloqueado; se abre el expediente E26xxxx con su cuenta analítica; cada línea con la cuenta analítica del expediente |
| 5. Compras sin duplicar | Expediente → «Crear solicitudes de presupuesto»; púlsalo otra vez | Una solicitud por proveedor; la segunda vez «Nada que pedir» |
| 6. Ejecución real | Referencias y fechas: ATA 10/11/2026 08:00, recogida real 22/11/2026 10:00. Carga: 20' salida del lleno 13/11, devolución del vacío 18/11; 40' HC salida 15/11, devolución 25/11. Confirmar el pedido de MSC. Servicios y costes: ✓ «Marcar como prestado» en THC, BL y FMI | DEM 20' = 60 € (9 días − 7 = 2 × 30); DEM 40' HC = 390 € (16 − 7 = 9: 5 × 30 + 4 × 60); previsión «Recalculada»; evento y chatter con el recálculo; la venta no cambia |
| 7. Factura del proveedor | Compras → pedido de MSC → «Crear factura» → fecha, referencia, impuesto 0 % → Contabilizar. «Registrar pago» | Solo lo prestado (FMI 2 × 900 + THC 180 + 240 + BL 60 = 2.280 €); el pago se rechaza: «aún no facturado al cliente» |
| 8. Factura al cliente | Expediente → «Facturar servicios» → solo THC → Contabilizar; luego otra con el resto | Primera: 560 € (2 × 280); después el pago de MSC ya se puede registrar |
| 9. Abono y coste extra | Factura del resto → «Abono» solo del BL. Servicios y costes → nueva línea OCU 120 € (MSC, motivo) → «Refacturar» 160 € → facturarla | Abono 75 €; el pago a MSC sigue permitido (el BL se facturó); línea de venta de 160 € añadida tras la aceptación |
| 10. Pagos y conciliación | Registrar los pagos (diario Banco) y, en Contabilidad → Banco, casar cada movimiento con su pago o factura | Facturas «Pagado» |
| 11. Rentabilidad | Expediente → Resumen | Facturado = venta − 75 + 160; coste real = 2.280 + 120; margen previsto = facturado − coste previsto; «Previsión de costes» por proveedor y previsión |

El mismo recorrido lo hace `dev/uat_e2e.py` con comprobaciones explícitas (64/64 el 26/10:
`docs/evidencias/20261026_1901_uat_e2e_boss20_uat_da0e263afa94.txt`; registros S00026 / E260013 / INV/2026/00004–00006 /
RINV/2026/00002 en boss20_uat). Los escenarios de oferta (FCL mixto con TEU, LCL con inspección, exportación aérea, tarifa
que falta / en conflicto, cambio de peso, demoras, handler de la aerolínea) están en `dev/uat_scenarios.py` (31/31:
`docs/evidencias/20261026_1903_uat_scenarios_boss20_uat_da0d0b68a13d.txt`).

## Lo que se ha recorrido en la interfaz desde Chrome (boss20, 26/10)

S00031 → E260015: cliente y envío, plantilla «[DEMO] IMB FOB» (encontrada por su código tras corregir el nombre en
inglés, D-6), DEM añadido, coste manual de FMI con proveedor, precios de venta, guardar y volver a abrir (total 3.005 €),
aceptar (pedido bloqueado, expediente E260015), crear solicitudes (P00005) y segunda vez «Nada que pedir», ATA y
recogida con hora, fechas de contenedor (DEM 60 € y 390 €, previsión «Recalculada»), confirmar el pedido (la solicitud en
borrador ya llevaba las demoras recalculadas: 2.460 → 2.730 €), marcar THC como prestados, «Diferencias con la oferta»
(detectó un contenedor añadido por error y quitado), «Previsión de costes». La parte contable (pasos 7–10) no se ha
recorrido en la interfaz: no se puede entrar en boss20_uat desde Chrome sin escribir una contraseña, y en boss20 no se
contabiliza. Esos pasos están comprobados en boss20_uat con `dev/uat_e2e.py`.
