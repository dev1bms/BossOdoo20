# Hoja de ruta — BOSS en Odoo 20 (boss20)

Fecha: 03/11/2026 · Sustituye como guía de trabajo a `docs/plan-expediente-completo.md` (queda como fondo).
Prioridad de Belal (03/11): que Odoo 20 funcione con eficiencia, facilidad y claridad siguiendo el orden de trabajo
de BOSS. La migración de datos está en pausa: lo cargado se queda (4.213 contactos, ADR-012) y no se migra nada más.

**Cómo leer las tablas.** «Funciona hoy» es solo lo probado en boss20: arnés de extremo a extremo
`dev/check_file_e2e.py` (evidencia `docs/evidencias/20261103_1135_check_file_e2e_boss20_10335dcc1069.txt`: 53 pasos
correctos, 0 fallos, 19 huecos declarados), el estado de los 65 puntos de las reuniones con Ángel
(`docs/angel-meetings-status.html`) y lo visto en Chrome el 03/11. «Falta» indica quién lo pidió. Esfuerzo: **S**
(menos de un día), **M** (1 a 3 días), **L** (más de 3 días). «Decide» se rellena solo cuando la regla de negocio no
está aprobada. Las propuestas de `docs/paquetes-aprobacion-f0.md` siguen sin aprobar mientras nadie diga lo contrario.

## 1. El ciclo de BOSS, paso a paso

| # | Paso | Funciona hoy en boss20 (prueba) | Falta para el uso diario (quién lo pidió) | Esf. | Decide |
|---|---|---|---|---|---|
| 1 | **Oferta** | Ruta, fechas ETD/ETA, carga, contenedores, peso tasable, tarifas por versión, flete semanal desde la oferta aprobado al entrar, venta = tarifa del cliente, precio tecleado o coste + 20 %, oferta de tarifas sin total (arnés 0–1; puntos 1–37 y M2 cerrados) | Precios de venta fijos de Cristina (M2-16, M2-17); validar las plantillas IAB/IMB/EAB y crear EMB, LCL y carretera (punto 13); regla ALM (P43); aprobar o rechazar la tarifa WFS (punto 38); IVA de CAU/QBR (P17-NS); zonas de Madrid de IRENEO (punto 4); usuarios en español para ver 2.500,00 (M2-11: hoy solo Cristina está en español) | S (código) | Cristina (precios, plantillas, ALM); Ángel (IVA, WFS); Belal (idioma) |
| 2 | **Aceptación** | Confirmar crea un expediente, una vez, con su cuenta analítica y una necesidad de compra por servicio; los bloqueos se agrupan por causa (arnés 2; puntos 23, 34) | Validez de la oferta 30 días y oferta caducada no aceptable (P23); oferta de tarifas: abrir el expediente al aceptar o al hacer la reserva (M2-C) | S | Cristina (P23); Ángel (M2-C) |
| 3 | **Apertura del expediente y responsable** | Expediente con partes, ruta, carga, referencias y «Pendiente» calculado; responsable = el comercial (arnés 2) | **Pantalla**: 10 botones a la vez en la cabecera y un «Pendiente» sin enlaces, no dice cuál es el siguiente paso (visto en E260038, 03/11); operativo por tráfico y plan de hitos (hueco F5; F0-C23 propone la tabla de Odoo 17); carpeta de documentos (hueco F6); 10 de los 25 expedientes activos son restos de la prueba del portal | M | Cristina (operativo por tráfico) |
| 4 | **Reserva y salida** | Solicitudes de presupuesto por proveedor y moneda, confirmadas con la referencia del proveedor; ATD y recogida real; «En tránsito» (arnés 3–4) | Condiciones de «En tránsito» (MBL/MAWB, reserva, contenedor: hueco S1, F0-C38, F0-C31/C32); hoy se acepta sin datos | M | Cristina |
| 5 | **Llegada, aduana y entrega** | «Entregado», ATA, NOA, descarga, fechas de contenedor; almacenaje, demoras y ocupación desde los eventos (arnés 5) | Estado del DUA, canal y levante (hueco F7); orden de transporte al transportista desde Odoo (F7); condiciones de «Entregado» (levante si BOSS hace la aduana, fecha de entrega si BOSS transporta: paquete 3); estado «Llegado» (F0-C22) | M | Cristina |
| 6 | **Facturas de proveedor y coste real** | Factura desde el pedido, derechos sin pedido, factura en USD, abono de proveedor, diferencias a revisar, coste real exacto (arnés 6) | Diferencia en USD separada en precio y tipo de cambio (P03); IVA de compras (A01); pagos de proformas como anticipo (F0-A09) | M | Ángel |
| 7 | **Factura al cliente (servicios y suplidos)** | Facturar los servicios elegidos, en parcial; suplidos al importe pagado sin margen (F0-A00 aprobado); líneas con el expediente; tabla de IVA de BOSS; NIF exigido (arnés 8; punto 35) | Derechos en factura aparte o sección (F0-A21); menciones legales del 0 %, IBAN de la empresa y series (hueco F4, F0-A13/A14/A15); SII o VERI*FACTU (P45-a); un pedido por pagador, prepagado/debido (F0-C56–C58) | M | Ángel |
| 8 | **Cobros y pagos** | Cobros y pagos conciliados; el pago al proveedor espera a que el cliente esté facturado (P30); un movimiento ya hecho se registra y se marca; cobrado y pagado por expediente (arnés 7, 9) | Cuentas bancarias y diarios (F0-A28), límites de crédito, plazos 6/60/75 días (Ángel); remesas SEPA (hueco F8, contradice F0-A31 «pagos desde la banca»); reclamación de cobros (F0-A04) | S–M | Ángel |
| 9 | **Cierre operativo y financiero** | Cierre operativo; el financiero espera a revisar diferencias; solo el administrador contable reabre; nada se contabiliza en un expediente cerrado; margen final exacto (arnés 10) | Condiciones del cierre operativo y congelar datos (hueco F10, F0-C61); bloquear o solo avisar al contabilizar en cerrado (F0-A80); fechas de bloqueo trimestrales (F0-A33); margen por usuario, cliente y tráfico (Cristina CR-O11) | M | Cristina (operativo); Ángel (financiero) |

Otros tráficos sin probar de extremo a extremo (huecos S2–S7): exportación aérea, importación aérea con NOA y handler,
exportación marítima FCL, grupaje LCL, carretera/nacional, negocio de agente en USD. Se prueban con los expedientes
[PRUEBA] de la tarea 3.

## 2. Próximas tareas, en orden

Primero la eficiencia y la claridad de las pantallas: menos clics, estados claros, textos en español y ninguna
pantalla sin salida. No se inventa ninguna regla de negocio: lo que no está decidido se muestra como pendiente.

1. **Expediente: siguiente paso claro.** El expediente dice en una línea cuál es el siguiente paso, quién lo hace y
   cuántas cosas faltan, con un solo botón «Ir» que abre exactamente lo que hay que hacer (servicios sin proveedor,
   pedidos por confirmar, facturar…). La cabecera solo enseña los botones que sirven en ese momento y la lista de
   expedientes muestra la columna «Siguiente paso». Es una guía y no bloquea nada.
   *Hecho cuando* esté instalado en boss20, se vea en Chrome en un expediente [PRUEBA] (en español y en inglés), un
   script de comprobación recorra todos los pasos de un expediente sin fallos y la evidencia esté en `docs/evidencias/`.
2. **Español para todos y una lista limpia.** Poner en español los usuarios de BOSS (M2-11; Belal lo confirma),
   cancelar los 10 expedientes que quedan de la prueba del portal y hacer que esa prueba deshaga lo que crea.
   *Hecho cuando* Ángel y el resto vean 2.500,00 y textos en español, y la lista «En curso» no tenga restos de pruebas.
3. **Expedientes [PRUEBA] de casos reales.** Importación marítima FCL (modelo E260883 de Odoo 17), importación aérea
   (E260167), grupaje LCL de importación y exportación marítima, con los contactos reales de boss20, sin importes
   reales. Cada uno se recorre con el siguiente paso de la tarea 1.
   *Hecho cuando* los cuatro existan en boss20, cada paso esté hecho o anotado como hueco y los huecos S3–S5 del arnés
   pasen a comprobaciones.
4. **Bandeja de trabajo del operativo.** Operativo responsable propuesto por cliente y tráfico (tabla de Odoo 17,
   F0-C23, que Cristina confirma), filtros «Mis expedientes · necesitan acción» y actividades de Odoo para los hitos.
   *Hecho cuando* cada usuario abra Odoo y vea sus expedientes ordenados por lo que tiene que hacer.
5. **Aduana y entrega en el expediente.** Estado del DUA, canal, levante y orden de transporte al transportista
   (huecos F7), con los campos que proponga Cristina.
   *Hecho cuando* el DUA y la orden de transporte se registren en el expediente y el arnés lo compruebe.
6. **Oferta rápida por caso.** Plantillas por tráfico con los precios de venta de Cristina (puntos 13, M2-16, M2-17)
   y una lista «qué falta para enviar» arriba de la oferta, igual que en la tarifa.
   *Hecho cuando* una oferta IMB FCL se haga desde la plantilla en menos de 10 clics con todos los precios.
7. **Datos de factura para Ángel.** IBAN de la empresa, series, menciones legales del 0 % y derechos en sección
   aparte, en cuanto Ángel conteste F4 y F0-A21.
   *Hecho cuando* el PDF de la factura de prueba tenga todo lo que pide Ángel y él lo dé por bueno.
8. **Cierre y margen.** Condiciones del cierre operativo (Cristina) e informe de margen por usuario, cliente y
   tráfico.
   *Hecho cuando* Cristina cierre un expediente en una semana desde la entrega y vea su margen en un informe.

## Decisiones que esperan a los responsables (no bloquean las tareas 1–4)

- **Cristina:** precios de venta y plantillas; operativo por tráfico; condiciones de «En tránsito», «Entregado» y del
  cierre; validez 30 días (P23); usuarios y permisos.
- **Ángel:** IVA de CAU/QBR; tarifa WFS; derechos en factura aparte; menciones legales, IBAN y series; SII o
  VERI*FACTU; bancos, plazos de pago y límites de crédito; F0-A80/A81; 360 empresas que Odoo 20 muestra como persona
  (sin NIF).
- **Belal:** idioma español para los usuarios de BOSS; capacidad y fecha de arranque por tráfico (F0-B11).

---

## English summary

Roadmap of 03/11/2026, ordered by BOSS's operational sequence (quotation → acceptance → file → booking → arrival,
customs, delivery → supplier bills → customer invoice → collection and payments → close). What works today is taken
only from checks run on boss20 (end-to-end harness 53/0 with 19 declared gaps, Ángel's 65 meeting points, Chrome on
03/11). The main gaps are business decisions (Cristina: selling prices, templates, operator per traffic, status
conditions; Ángel: invoice data, VAT of CAU/QBR, banks) and screen clarity. Next items, in order: (1) guided next step
on the shipment file, (2) Spanish for every BOSS user and a clean file list, (3) [PRUEBA] files modelled on real
Odoo 17 cases, (4) operator work queue, (5) customs and delivery on the file, (6) fast quotation per case, (7) invoice
data for Ángel, (8) close and margin report. Data migration stays paused.
