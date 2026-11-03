# Hoja de ruta — BOSS en Odoo 20 (boss20)

Fecha: 03/11/2026 (revisada el mismo día por indicación de Belal) · Sustituye como guía de trabajo a
`docs/plan-expediente-completo.md` (queda como fondo).
Prioridad de Belal (03/11): que Odoo 20 funcione con eficiencia, facilidad y claridad siguiendo el orden de trabajo
de BOSS. La migración de datos está en pausa: lo cargado se queda (4.213 contactos, ADR-012) y no se migra nada más.

**Regla de trabajo (Belal, 03/11).** No se pregunta nada a Cristina ni a Ángel antes de revisar todo el sistema y todas
las fuentes: casi todo está documentado (Odoo 19, carpeta «NEW ODOO», Odoo 17, las reuniones). Lo que está escrito se
aplica con su fuente; lo que no está escrito toma la práctica de Odoo 17 o la norma (reversible y documentado); solo
queda para reunión lo esencial que no está en ninguna parte y cuyo error tendría consecuencias legales o económicas.
El idioma de la interfaz no es una tarea: Belal y otros usuarios trabajan con formato español sobre la interfaz en
inglés.

**Cómo leer la tabla.** «Funciona hoy» es solo lo probado en boss20: arnés de extremo a extremo
`dev/check_file_e2e.py` (última evidencia `docs/evidencias/20261103_1209_check_file_e2e_boss20_2342252c1235.txt`:
70 pasos correctos, 0 fallos, 19 huecos declarados), los 65 puntos de las reuniones con Ángel
(`docs/angel-meetings-status.html`) y lo visto en Chrome el 03/11. Esfuerzo: **S** (menos de un día), **M** (1 a 3
días), **L** (más de 3 días).

## 1. El ciclo de BOSS, paso a paso

| # | Paso | Funciona hoy en boss20 (prueba) | Falta para el uso diario | Dónde está ya la regla | Esf. |
|---|---|---|---|---|---|
| 1 | **Oferta** | Ruta, ETD/ETA, carga, contenedores, peso tasable, tarifas por versión, flete semanal aprobado al entrar, venta = tarifa del cliente, precio tecleado o coste + 20 %, oferta de tarifas sin total (arnés 0–1) | Precios de venta generales y por cliente; plantillas EMB, LCL y carretera; regla ALM; aviso de margen mínimo | Odoo 17: plantilla «Standard» (THC, T3, BL, CSM, FAD; Cristina, 05/03/2026) y 9 plantillas por cliente (`x_quotation_local_line`); servicios «siempre / a veces» R-S1 y F0-C09; ALM: regla de Cristina del 25/09 aprobada por Belal el 23/10; margen: 12 reglas por grupo de Odoo 17 (`x_profit_group_rules`) | M |
| 2 | **Aceptación** | Confirmar crea un expediente, una vez, con su cuenta analítica y una necesidad de compra por servicio (arnés 2); validez 30 días configurada | Oferta caducada: no se acepta sin prorrogar | Odoo 17: 30 días en la compañía, la oferta caducada pasa a perdida y se puede prorrogar (`x_spot`); apertura del expediente: EXW/FOB/FCA al aceptar, DAP/DDP al recibir documentos (Cristina, «Nuevo Odoo» › procesos A4:A10) | S |
| 3 | **Apertura del expediente y responsable** | Expediente con «Siguiente paso» e «Ir», cabecera con los botones que sirven, «Pendiente» (entregado el 03/11) | Operativo responsable por cliente y tráfico; plan de hitos por tráfico; carpeta de documentos (F6) | Odoo 17: tabla `x_operative_assign` (414 filas cliente × tráfico → operativo); hitos: Cristina, «Nuevo Odoo» › Hoja1 A13/A19 y subetapas de Odoo 17 | M |
| 4 | **Reserva y salida** | Solicitudes de presupuesto por proveedor y moneda, confirmadas con la referencia del proveedor; ATD; «En tránsito» (arnés 3–4) | Aviso al pasar a «En tránsito» sin ETD/ATD, MBL/MAWB o contenedor real | Práctica de Odoo 17 (F0-C31, F0-C38): se aplica como aviso, no como bloqueo | S |
| 5 | **Llegada, aduana y entrega** | «Entregado», ATA, NOA, descarga, fechas de contenedor; almacenaje y demoras desde los eventos (arnés 5) | DUA con canal y levante; orden de transporte al transportista; condiciones de «Entregado» | Cristina por escrito, «Nuevo Odoo» › OPS- exptes A42 (levante si BOSS despacha, fecha y hora de entrega si BOSS transporta) y A73 (HBL liberado o SWB antes de la orden de transporte) | M |
| 6 | **Facturas de proveedor y coste real** | Factura desde el pedido, derechos sin pedido, factura en USD, abono, diferencias a revisar, coste real exacto (arnés 6) | Diferencia en USD separada en precio y tipo de cambio | Cristina, OPS- exptes A49 (cambio de la naviera); diario de diferencias de cambio de Odoo 17 | S |
| 7 | **Factura al cliente (servicios y suplidos)** | Facturar los servicios elegidos, en parcial; suplidos al importe pagado (F0-A00); líneas con el expediente; tabla de IVA; NIF exigido (arnés 8) | Suplidos en factura aparte; series; cuenta bancaria en la factura; menciones legales; fecha de factura | IVA: reglas de Ángel del 31/08 (`BossOdoo19/docs/iva_rules.md`), punto 35 «OK»; suplidos aparte: Odoo 17 «NORMAL or TAX, since we don't mix»; series de Odoo 17 (F26 MM-NNNN, rectificativas FR26 NNNN); cuentas: diarios bancarios de Odoo 17; menciones: notas de los impuestos de Odoo 20 (art. 20, 22, 23/24, Directiva art. 196) | M |
| 8 | **Cobros y pagos** | Cobros y pagos conciliados; el pago al proveedor espera a la factura al cliente (P30, Belal 23/10); cobrado y pagado por expediente (arnés 7, 9) | Diarios bancarios (EUR y USD); plazos 6, 20, 60, 75 y 90 días; límites de crédito; reclamación | Odoo 17: 9 diarios bancarios, 15 plazos de pago, límites de crédito por cliente, un nivel de reclamación a los 7 días; remesas a proveedores con RemesaFiller («Registro automatizaciones» › CONTABILIDAD A3) | S–M |
| 9 | **Cierre operativo y financiero** | Cierre operativo; el financiero espera a revisar diferencias; solo el administrador contable reabre; margen final exacto (arnés 10) | Condiciones del cierre operativo; informe de margen por usuario, cliente y tráfico | Cristina por escrito: todo facturado, sin aviso de margen, a más tardar una semana después de la entrega (OPS- exptes A65/A69, «Facturacion» A2); margen por usuario, cliente y tráfico (CR-O11) | M |

Otros tráficos sin probar de extremo a extremo (huecos S2–S7): exportación aérea, importación aérea con NOA y handler,
exportación marítima FCL, grupaje LCL, carretera/nacional, negocio de agente en USD. Se prueban en la tarea 2.

## 2. Tareas, en orden

Primero la eficiencia y la claridad: menos clics, estados claros y ninguna pantalla sin salida. Cada regla se aplica
con su fuente escrita; ninguna se inventa.

1. **Expediente: siguiente paso claro — entregado el 03/11.** Línea «Siguiente paso» con el botón «Ir», cabecera con
   solo los botones que sirven, acciones ocasionales en el menú «Acción» y columna en la lista (boss_expediente
   20.0.1.17.0, commit `2342252`). Arnés 70/0 con 17 comprobaciones nuevas
   (`docs/evidencias/20261103_1209_check_file_e2e_boss20_2342252c1235.txt`); visto en Chrome en E260038 (cabecera de
   10 a 6 botones, «Ir» abre los servicios sin proveedor; lista de 25 expedientes en 341 ms); español comprobado.
2. **Expedientes [PRUEBA] de casos reales.** Importación marítima FCL (modelo E260883 de Odoo 17), importación aérea
   (E260167), grupaje LCL de importación y exportación marítima, con los contactos reales de boss20 y sin importes
   reales; cada uno se recorre con «Siguiente paso».
   *Hecho cuando* existan en boss20, cada paso esté hecho o anotado y los huecos S3–S5 del arnés pasen a comprobaciones.
   **Entregado el 03/11** (`dev/sample_real_cases.py`, evidencia
   `docs/evidencias/20261103_1421_sample_real_cases_boss20_3481dc1135fd.txt`: 4 pasos correctos, 0 fallos). En boss20,
   aceptados y con su siguiente paso: E260181 importación FCL (Aguilera, Xingang → Valencia, 20' + 40' HC, MSC), E260182
   importación aérea (Cofitel, Cantón → Madrid, Qatar Airways, WFS), E260183 exportación LCL (Leroy Merlin, Algeciras →
   Conakry, MSC), E260184 importación LCL de agente (Publiship, Hong Kong → Valencia). Cada uno se recorre con «Siguiente
   paso» hasta el cierre financiero dentro de una transacción deshecha. Dos tandas anteriores se cancelaron en Odoo
   (E260171–E260178): un precio ficticio puesto por unidad y, después, el 40' HC sin líneas (defecto corregido en la
   tarea 3). Cubre los huecos S3 (sin NOA ni almacenaje) y S5; S4 (exportación FCL) sigue abierto. Lo que aprendimos
   para la tarea 3:
   - las tarifas de cliente (p. ej. Cofitel) no tienen la regla general «coste + 20 %» de respaldo: el flete con coste
     manual queda sin precio de venta;
   - el precio de venta debe poder variar por tamaño de contenedor (THC 20' y 40' en la plantilla «Standard»);
   - sin plantilla (exportación marítima, LCL) el expediente queda sin incoterm ni «BOSS gestiona»;
   - la tarifa WFS (punto 38) sigue pendiente de aprobación: sin ella la importación aérea solo se acepta con el motivo
     del responsable comercial;
   - no hay tarifas LCL ni de exportación marítima en boss20: esos costes van «a consultar».
3. **Oferta rápida con los precios de BOSS.** Precios de venta de la plantilla «Standard» de Odoo 17 en la tarifa
   general y las 9 plantillas por cliente como tarifas de cliente; plantillas por tráfico (R-S1, F0-C09); aviso de
   margen mínimo con las 12 reglas de Odoo 17; regla ALM del 25/09.
   *Hecho cuando* una oferta IMB FCL salga de la plantilla con todos sus precios en menos de 10 clics y el arnés lo
   compruebe.
   **Entregado en parte el 03/11** (boss_pricing_sale 20.0.1.18.1):
   - precio de venta por tamaño de contenedor y lista de cliente que cae en la general «coste + 20 %»
     (`docs/evidencias/20261103_1422_check_pricelist_chain_boss20_123a36db16d7.txt`, 12/0);
   - precios de venta de Odoo 17 cargados (`dev/load_sale_prices.py`, datos privados en `.research/`): plantilla
     «Standard» en la tarifa general (THC y T3 por tamaño, BL, CSM, FAD) y 8 plantillas de cliente como listas propias,
     49 reglas; al repetirlo no cambia nada. Fuera, con su motivo: T3 por fórmula de toneladas, CSM por contenedor, GLO
     en USD, transporte por expediente, THC de TCP (dos plantillas que no coinciden);
   - plantillas nuevas: exportación FCL (EMB), grupaje de importación (IMB LCL FOB) y de exportación (EMB LCL),
     carretera (TTE), según la propuesta F0-C09 sacada de las ofertas reales;
   - aviso de margen mínimo por grupo de servicios con la regla base de Odoo 17 (10 % del coste, 10 de tolerancia;
     suplidos exactos); solo avisa;
   - defectos corregidos al probar: con un 20' y un 40' HC el 40' se quedaba sin líneas; al cambiar 40' DV a 40' HC en
     pantalla quedaban dos juegos de líneas;
   - arnés 70/0 (`20261103_1421_check_file_e2e_boss20_3481dc1135fd.txt`), con su cliente [PRUEBA] en una lista
     [PRUEBA] para que los precios reales no salgan en la evidencia.
   Pendiente: la regla ALM (Cristina elige entre su correo del 25/09 y la cláusula de las ofertas, en la llamada); las
   12 reglas de margen por tráfico y las excepciones por cliente de Odoo 17; elegir el puerto no rellena su país y
   buscar «MSC» no muestra la naviera de grupo; una oferta IMB FCL desde la plantilla lleva hoy unas 12 entradas, no
   menos de 10 (visto en Chrome).
4. **Bandeja del operativo.** Operativo propuesto desde la tabla de Odoo 17 (cliente × tráfico), filtros «Mis
   expedientes · necesitan acción» y actividades por hito.
   *Hecho cuando* cada usuario abra Odoo y vea sus expedientes ordenados por lo que tiene que hacer.
   **Entregado en parte el 03/11** (boss_expediente 20.0.1.18.0, commit `2a2c650`; evidencia
   `docs/evidencias/20261103_1431_check_work_queue_boss20_2a2c65062fe7.txt`, 10/0; arnés 70/0
   `20261103_1431_check_file_e2e_boss20_2a2c65062fe7.txt`): menú «Mi trabajo» con el tablero por estado (cada tarjeta con
   su siguiente paso y su responsable; visto en Chrome), filtros «Necesitan acción», «Pendiente en operaciones» y «Por
   facturar o cerrar», y la tabla «Operativos por cliente y tráfico»: al abrir un expediente, el operativo de su cliente
   para su tráfico pasa a ser el responsable (con nota en el historial); sin él, quien lo abrió.
   Pendiente: cargar las 414 filas de Odoo 17 (`x_operative_assign`) necesita los usuarios de los operativos en boss20
   (hoy solo hay 4 usuarios internos) y leer Odoo 17 por lotes (la conexión de solo lectura del servidor está vacía);
   actividades por hito (lista de Cristina en «Nuevo Odoo» › Hoja1 A13/A19).
5. **Estados con sus condiciones, aduana y entrega.** Avisos de «En tránsito» y «Entregado» y condiciones del cierre
   tal como Cristina las escribió; DUA con canal y levante; orden de transporte al transportista.
   *Hecho cuando* el arnés recorra esos avisos y el DUA y la orden de transporte queden en el expediente.
   **Entregado el 03/11** (boss_expediente 20.0.1.19.0, boss_documents 20.0.1.1.0, commit `48bd227`; arnés 77/0 con 15
   huecos en vez de 19, `docs/evidencias/20261103_1443_check_file_e2e_boss20_48bd227435fd.txt`; muestras 4/0; documentos
   19/0):
   - pestaña «Aduana» del expediente: DUA, agente, garantía de los impuestos (aval de BOSS, del cliente o pago 031),
     canal (verde, naranja, rojo), documentación completa, envío al agente, admisión y levante (Odoo 17 y Cristina,
     «Nuevo Odoo» › OPS- exptes A32–A36); estado del HBL (originales, liberado, sea waybill; A39);
   - «Entregado» exige lo que Cristina escribió y Odoo 17 aplicaba: ATA y descarga del buque en importación, levante si
     BOSS despacha, fecha y hora de recogida o entrega si BOSS transporta (A42) y HBL liberado o sea waybill antes de
     entregar una importación marítima (A73); el siguiente paso dice qué falta;
   - «En tránsito» sin ATD, reserva, BL/AWB máster o números de contenedor avisa y lo anota en el historial, sin
     bloquear (práctica de Odoo 17; el paquete 3 solo obliga lo que Cristina escribió);
   - «Orden de transporte»: PDF para el transportista (recogida, entrega, contenedores, mercancía; sin precios ni la
     referencia del cliente), solo con transportista elegido y, en importación marítima, con el HBL liberado. Se imprime,
     nunca se envía desde Odoo. Visto en Chrome en E260181 (aviso claro mientras el HBL no está liberado).
   Pendiente: el estado «Llegado» (F0-C22) y los avisos al cliente; generar el texto para el agente de aduanas (A37).
6. **Factura y cobro como en Odoo 17.** Diarios bancarios EUR y USD con sus cuentas, plazos de pago que faltan, límites
   de crédito, un nivel de reclamación, series F/FR, suplidos en factura aparte, cuenta bancaria y menciones legales en
   el PDF, fecha de factura según la norma.
   *Hecho cuando* la factura [PRUEBA] lleve todo eso y el arnés cobre y pague por los diarios reales.
   **Entregado en parte el 03/11** (boss_expediente 20.0.1.20.0, commit `1b36bd6`; arnés 80/0 con 14 huecos,
   `docs/evidencias/20261103_1523_check_file_e2e_boss20_1b36bd6c73c3.txt`; muestras 4/0):
   - los suplidos (derechos, IVA de importación…) se facturan aparte de los servicios, en la misma serie, con la
     mención «Suplidos: importes pagados en nombre y por cuenta del cliente, no incluidos en la base imponible (art.
     78.Tres.3º de la Ley 37/1992)» y el número de DUA (práctica de Odoo 17; F0-A21, F0-A22, F0-A15);
   - plazos de pago de Odoo 17 que faltaban: 6, 20 y 60 días (`dev/setup_finance_o17.py`);
   - los 9 diarios bancarios de Odoo 17 (Santander, Popular, Caixabank, Bankinter, WCA; EUR y USD), sin número de
     cuenta: **el IBAN de cada diario lo teclea Belal o Ángel** (Contabilidad › Configuración › Diarios); con él, la
     factura imprime la cuenta de cobro.
   Pendiente: 75 y 90 días (Odoo 17 los tiene, pero la Ley 3/2004 fija 60 días como máximo entre empresas: pregunta
   para Ángel); series F/FR de Odoo 17 al arrancar 2027 (F0-A18); límites de crédito y vencimiento propio de los
   suplidos por cliente (datos de Odoo 17, misma lectura por lotes que los operativos); un nivel de reclamación a los 7
   días (no se toca mientras pueda enviar correos a clientes reales); fecha de la operación en la factura (F0-A20).
7. **Cierre y margen.** Cierre operativo con las condiciones de Cristina e informe de margen por usuario, cliente y
   tráfico.
   *Hecho cuando* un expediente se cierre una semana después de la entrega y su margen salga en el informe.
8. **Consolidaciones (un máster, varias casas).** El máster (MBL/MAWB) es el expediente y cada casa (HBL/HAWB) una
   partida (Cristina, «Plan detallado previsiones» › Explicaciones previsiones A120 y A92); reparto de costes del
   máster a mano, como en Odoo 17.
   *Hecho cuando* un expediente con tres casas se facture por casa y su margen sume el del máster.

Las tareas 3, 4 y 6 copian configuración de Odoo 17 (precios de venta, tabla de operativos, diarios, plazos, límites,
reglas de margen), no expedientes ni saldos: necesitan el visto bueno de Belal porque la migración está en pausa.

## 3. Qué dicen las fuentes de lo que se iba a preguntar

**Respondido por escrito (se aplica con su fuente).** Tabla de IVA (Ángel 31/08; punto 35 «OK»); suplidos al importe
pagado y en factura aparte (F0-A00, Odoo 17); cuentas de suplidos 419xxx (P18, Odoo 17); quién se factura en negocio de
agente (Ángel 28/10, punto 22); coste a consultar del transporte (Ángel 27/10, M2-19); flete con la última tarifa
disponible (Ángel, M2-G); condiciones de «Entregado» y del cierre (Cristina, «Nuevo Odoo»); partidas (Cristina 28/09);
visibilidad por comercial y de costes (Cristina CRM A19, P35); aprobación de tarifas (Belal 09/10).

**No escrito: práctica de Odoo 17 o norma (reversible).** Precios de venta («Standard» y plantillas por cliente);
operativo por cliente y tráfico; margen mínimo (12 reglas); validez y caducidad de la oferta; series de factura;
diarios bancarios, plazos, límites de crédito y reclamación; avisos de «En tránsito»; IVA de CAU y QBR a cliente
español como en Odoo 17 («0 % S»); fecha de factura = fecha de expedición con la fecha de la operación aparte
(RD 1619/2012, art. 6); dos decimales con cuatro solo en precios por kg; estimación de derechos tecleada (no hay tabla
TARIC).

**Para una reunión (dos preguntas legales).** SII o VERI*FACTU desde el 01/01/2027 (P45-a): obligación legal que no
consta en ninguna fuente; Odoo 20 trae los dos módulos sin instalar, mientras tanto no se instala ni se envía nada. Y si
los plazos de 75 y 90 días de Odoo 17 siguen en uso (la Ley 3/2004 fija 60 días como máximo entre empresas).

---

## English summary

Roadmap of 03/11/2026, revised the same day on Belal's instruction: nothing is asked of Cristina or Ángel before the
whole system and every source have been reviewed. The review (Odoo 19 docs, the «NEW ODOO» folder, Odoo 17 production,
the meeting notes) found the rules already written or practised in Odoo 17: selling prices (Odoo 17 «Standard» and nine
customer templates), operator per customer and traffic (414 rows), minimum margin (12 group rules), status and close
conditions (Cristina's «Nuevo Odoo» workbook), VAT table (Ángel 31/08), suplidos, invoice series, banks, payment terms.
One meeting question remains: SII or VERI*FACTU. The UI language is not a task. Items: (1) next step on the file —
delivered; (2) [PRUEBA] files from real cases; (3) fast quotation with BOSS's prices; (4) operator work queue;
(5) status conditions, customs and delivery; (6) invoicing and collection as in Odoo 17; (7) close and margin report;
(8) consolidations. Items 3, 4 and 6 copy configuration from Odoo 17 and need Belal's go-ahead (migration paused).
