# Paquetes de aprobación F0 (28/10/2026)

Las 152 propuestas por defecto de `docs/decisiones-f0.md` **no están aprobadas**. Se han separado en dos grupos:

- **Rutina técnica** (67): configuración reversible que mantiene el comportamiento aprobado; se aplican sin pedir aprobación (lista al final).
- **Con efecto real**: cambian permisos, bloqueos, cuentas, impuestos, reparto de costes o alcance del arranque. Van en los paquetes de abajo, cada uno con la recomendación y su fuente, para aprobar o corregir en bloque.

Excepción ya aprobada: **F0-A00** (suplidos al importe pagado, sin margen), aprobada por Belal el 28/10 e implantada (boss_pricing_sale 20.0.1.16.0).

Cada fila indica si la fuente se ha comprobado. Las marcadas «la fuente NO lo respalda» o «fuente débil» no deben aprobarse sin revisarlas (resumen al final).

## 1. Bloqueos en contabilidad, pagos y cierre financiero — Bloqueos · responsable: Ángel
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| F0-A80 | Con el expediente cerrado financieramente no se contabiliza ninguna factura ni abono hasta que contabilidad lo reabra. | preguntas-abiertas (pregunta abierta); Odoo 17 grupo gestor | fuente débil | implantado el 28/10 como medida provisional (expediente cerrado: no se contabiliza). Ya está implantado (76ccb67) como medida provisional; la regla de Odoo 17 trata de editar, no de contabilizar. |
| F0-A81 | Un cargo bancario real se concilia siempre y se marca «pagado antes de facturar al cliente»; el asistente de pago sigue bloqueado. | preguntas-abiertas:24 (P30 pendiente); 76ccb67 | fuente débil | implantado el 28/10 como medida provisional (movimiento bancario: se registra y se marca). La fuente es el comportamiento provisional mientras Ángel y Cristina responden. |
| P30-b | Se retiene el pago de toda la factura de proveedor si uno de sus servicios no está facturado al cliente. | preguntas-abiertas (pregunta abierta) | fuente débil | Fuente circular: la línea citada es la propia pregunta, pendiente. |
| P30-d | El abono del proveedor se aplica siempre a su factura retenida, porque no sale dinero. | ciclo-operativo §P30 | fuente comprobada |  |
| F0-A09 | Los pagos de proformas (DUA, handling) se registran como anticipo ligado al expediente, como excepción a P30. | Odoo 17 (texto de la pregunta) | fuente comprobada | Excepción a un bloqueo aprobado. |
| F0-A08 | No se contabiliza la factura de un proveedor que cobra por transferencia o remesa si no tiene cuenta bancaria. | Odoo 17 (texto de la pregunta) | fuente comprobada | Se apoya solo en «Odoo 17 lo hace». |
| F0-A25 | No se factura a ningún cliente sin condición de pago configurada. | Odoo 17 (texto de la pregunta) | fuente débil | Amplía la regla: en Odoo 17 solo afecta a los clientes creados desde el 01/02/2025. |
| P31 | No se contabiliza una factura a un cliente español sin NIF y, además, se exige NIF-IVA a los clientes de la UE con «0% UE S». | ciclo-operativo P31; l10n_es s_iva0_sp_i mod349[S] | fuente comprobada | La primera parte la aprobó Belal; la exigencia de NIF-IVA UE es un bloqueo nuevo. |
| F0-A33 | Ángel bloquea el periodo y el IVA cada trimestre tras el 303, y el ejercicio tras el cierre anual. | Odoo 17 res.company fechas de bloqueo (28/10) | fuente comprobada |  |
| F0-A34 | El cierre financiero exige todo facturado y la lista «Pendiente» vacía, sin exigir cobros ni pagos. | Odoo 17 lista «Cierre automático» | fuente comprobada | Odoo 17 no tiene cierre financiero: el concepto es nuevo. |

## 2. Margen mínimo, venta bajo coste y límite de crédito — Bloqueos · responsable: several
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| P01/P02-a | Margen mínimo orientativo del 10 % por grupo de servicios, con 10 € de tolerancia, que solo avisa. | respuestas-cristina fila 17 (Odoo 17 summary_utils) | fuente comprobada | Contradice P01/P02-b, que hace que ese margen bloquee. |
| P01/P02-b | Con el margen por debajo del mínimo no se factura ni se cierra hasta que Cristina lo desbloquee con un motivo. | 05_sharepoint_excel:477 (Odoo 17: los avisos bloquean la facturación) | fuente comprobada | La fuente lo confirma en Odoo 17, pero respuestas-cristina fila 17 dice «nada aprobado» y Odoo 19 «solo aviso». |
| P43-D8 | La venta de ALM puede quedar por debajo del coste del handler, solo con un aviso interno. | especificacion-alm-venta D8; BossOdoo19 B18 | la fuente NO lo respalda | B18 dice lo contrario: la venta nunca por debajo del coste. |
| F0-A05 | No se abre el expediente de un cliente que supera su límite de crédito, salvo autorización de Ángel con un motivo. | Odoo 17 (texto de la pregunta) | fuente comprobada | Se apoya solo en «Odoo 17 lo hace»; también decide quién autoriza. |

## 3. Condiciones para cambiar de estado el expediente y la oferta — Bloqueos · responsable: several
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| F0-A07 | Se puede pasar a «Entregado» sin facturar, con un aviso; la factura se exige en el cierre operativo. | 03_cycle_requirements:72 | fuente comprobada | Relaja Odoo 17, que exige estar facturado para «Entregado». |
| F0-C31 | «En tránsito» exige ETD o ATD pasada, contenedores reales, seguro resuelto y expedidor y destinatario reales. | decisiones-f0 (Odoo 17) | fuente comprobada | Se apoya solo en «Odoo 17 lo hace». |
| F0-C32 | «En tránsito» exige además la confirmación del booking del transportista principal. | Nuevo Odoo.xlsx (campo de fecha del booking); práctica | fuente débil | Es un bloqueo nuevo que no existe en Odoo 17. |
| F0-C38 | Documentos obligatorios: MBL/MAWB antes de «En tránsito», levante antes de «Entregado» (si la aduana es de BOSS) y HBL liberado antes de la OT. | Nuevo Odoo.xlsx OPS; decisiones-f0 (Odoo 17) | fuente comprobada |  |
| F0-C49 | «Llegado» exige la ATA informada y ya pasada. | decisiones-f0 (Odoo 17) | fuente comprobada | Se apoya solo en «Odoo 17 lo hace». |
| F0-C66 | Las valoraciones del cliente y de los proveedores son obligatorias para el cierre operativo. | decisiones-f0 (Odoo 17 desde 01/03/2025) | fuente comprobada | Se apoya solo en «Odoo 17 lo hace». |
| R-A3 | El ordenante debe ser de tipo Agente o Cliente según el negocio; solo avisa hasta migrar los tipos y después bloquea. | Odoo 17 (texto de la pregunta); B17 | fuente comprobada | Se apoya solo en «Odoo 17 lo hace». |
| F0-B06 | En los expedientes nuevos se impide una forma de carga que no corresponda al modo de transporte. | ciclo-operativo:52 (E260010 es una prueba) | fuente comprobada | Es una restricción nueva, decidida por Belal. |
| P23 | Las ofertas valen 15 días por defecto y una oferta caducada no se acepta sin ampliar la validez o recotizar. | Odoo 17 automatización 197; validez de la compañía = 30 días | fuente débil | Odoo 17 usa 30 días y su regla es otra: no abre expediente de una oferta vencida hace más de 15 días. |
| P03-c | En marítimo, el expediente debe fijar un tipo de cambio antes de facturar en euros un flete en dólares. | 05_sharepoint_excel:95-98 (requisito de Cristina) | fuente comprobada | Es requisito para facturar. |

## 4. Permisos: quién ve qué y quién cierra o reabre — Permisos · responsable: several
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| F0-C01 | Los usuarios se crean desde Odoo 17 conservando su grupo de Ventas; Cristina aprueba tarifas y Belal la sustituye. | Odoo 17 res.groups 21/22; Odoo 19 B29.2 | fuente comprobada |  |
| P20 | Los usuarios de ventas ven la venta, el coste y el margen de la oferta; el operativo ve la venta y compras el lado del proveedor. | preguntas-abiertas P35 (Belal 23/10) | fuente comprobada | Falta que Cristina lo ratifique. |
| F0-A35 | Solo los administradores de contabilidad (Ángel) reabren un expediente cerrado financieramente. | preguntas-abiertas (76ccb67:262) | la fuente NO lo respalda | implantado el 28/10 como control técnico (reabrir: administrador de contabilidad). La fuente dice «control técnico añadido el 28/10, no una decisión». |
| F0-C61 | Cierra el operativo o el gestor; solo Cristina reabre, con motivo, y recibe un aviso en cada cierre. | Nuevo Odoo.xlsx OPS; decisiones-f0 (Odoo 17) | fuente comprobada | Más flexible que Odoo 17, donde solo informática modifica. |
| F0-C34 | En el portal se publican por defecto la salida, la llegada, el levante, la entrega y los cambios de ETD/ETA. | Nuevo Odoo.xlsx notificaciones; ADR-010 decisión 8 | fuente comprobada |  |
| F0-C39 | El cliente ve solo los documentos que publica el operativo, con sugerencia ya marcada para HBL/HAWB, seguro, aviso de llegada, DUA y levante. | ADR-010 decisión 8; Nuevo Odoo.xlsx | fuente comprobada |  |
| P10-A | Una empresa de un grupo no ve los envíos de otra entidad del grupo, salvo concesión manual con autorización escrita. | ADR-010 decisión 2 | fuente comprobada |  |
| P10-B | El expedidor o el destinatario que no es ordenante no tiene cuenta; solo puede recibir el enlace de seguimiento. | ADR-010 decisiones 2 y 9 | fuente comprobada |  |

## 5. Cuentas contables, diarios y conciliación — Cuentas · responsable: Ángel
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| P37-a | Ingresos en las cuentas 705001 a 705009 por familia, asignadas en las categorías de producto. | Odoo 17 (texto de la pregunta) | fuente comprobada |  |
| P37-b | Gastos en las cuentas 607 por familia (607400 flete, 607401 profit share) y comisiones en la 623008. | Odoo 17 (texto de la pregunta) | fuente comprobada |  |
| P03-b | La diferencia de cambio va al diario estándar de diferencias de cambio y no bloquea el cierre. | Odoo 17 diario «Exchange Difference»; PGC NRV 11.ª | fuente comprobada |  |
| F0-A28 | Un diario por cada cuenta bancaria activa de Odoo 17, en EUR y en USD. | Odoo 17 account.journal (28/10) | fuente comprobada |  |
| F0-A30 | Apuntes automáticos de conciliación: comisiones bancarias en EUR y en USD y la retención del banco. | Odoo 17 (texto de la pregunta) | fuente comprobada |  |
| F0-A36 | A fin de mes se periodifican solo los costes prestados sin factura de proveedor, en la 607800. | Odoo 17 cuenta 607800; principio de devengo | fuente débil | No se ha comprobado que Odoo 17 use la 607800 cada mes. |
| F0-A32 | Las facturas a cobrar y a pagar de un agente se compensan solo con una liquidación que el agente acepte. | Código Civil arts. 1195-1196 | fuente débil | No hay fuente de la práctica de BOSS ni de Odoo 17. |

## 6. IVA, modelo 347 y menciones legales en factura — Impuestos · responsable: Ángel
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| A01 | El IVA de compra por defecto, por proveedor o servicio, sigue el criterio de Odoo 17, con la excepción del transporte terrestre de exportación de Ángel. | Odoo 17 account.tax; Odoo 19 iva_rules | fuente comprobada |  |
| P44-IVA | Un almacén propio fuera del aeropuerto llevaría la clase de IVA del ALM (NR). | 05_sharepoint_excel:251; iva_rules (Ángel 31/08) | fuente comprobada | Solo aplica si Cristina crea el servicio. |
| F0-A13 | Nota legal «no sujeta por reglas de localización (art. 69 LIVA)» en el impuesto «0% EX S». | l10n_es s_iva_e (no_sujeto_loc, 303[120], sin nota legal) | fuente comprobada | El texto exacto lo valida Ángel o su asesor. |
| F0-A14 | Nota legal equivalente para Canarias, Ceuta y Melilla en el impuesto «0% S NS». | l10n_es s_iva_ns | fuente comprobada |  |
| F0-A15 | Los suplidos fuera de la base imponible, con la mención del art. 78.Tres.3º y el número de DUA. | LIVA art. 78.Tres.3º; cuentas-suplidos.md | fuente comprobada |  |
| F0-A19 | BOSS no vende con IVA reducido; el 10 % y el 4 % quedan solo para compras. | Odoo 17 apuntes revisados el 28/10 | fuente comprobada |  |
| F0-A20 | La fecha de la factura es la «fecha importante» del envío (llegada o salida). | Odoo 17; RD 1619/2012 art. 11; LIVA art. 75 | la fuente NO lo respalda | El RD 1619/2012 art. 6 exige la fecha de expedición y una fecha de operación aparte si es distinta: no ampara poner fecha anterior a la factura, y choca con VERI*FACTU. |
| F0-A24 | Las facturas de suplidos se excluyen del 347. | DGT V2002-21 vía webs de terceros | fuente débil | Cambia lo que hace hoy Odoo 17; la consulta de la DGT no se ha comprobado en la fuente oficial. |
| F0-A26 | Provisión de fondos sin IVA para aranceles e IVA del despacho, y factura de anticipo con IVA para los servicios propios cobrados por adelantado. | LIVA arts. 75.Dos y 78.Tres.3º | fuente comprobada |  |

## 7. Reparto de costes e ingresos entre pagadores y expedientes — Reparto de costes e ingresos · responsable: several
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| F0-C56 | Un pedido de venta por cada pagador dentro del mismo expediente, con el pagador propuesto según el Incoterm. | decisiones-f0 (Odoo 17: entidad por línea) | fuente comprobada | Cambia el mecanismo de Odoo 17 (que usa una entidad por línea); el resultado es el mismo. |
| F0-C57 | Prepaid o collect decide a quién se factura el flete, y se puede cambiar línea a línea. | decisiones-f0 (Odoo 17) | fuente comprobada |  |
| F0-C08 | El Incoterm decide a quién se factura por defecto (punto de separación). | respuestas-cristina fila 3 | fuente comprobada | Por lo demás, las plantillas son routine. |
| F0-C58 | El profit share se liquida según el caso, con los cuatro casos de Odoo 17 elegidos por el operativo. | decisiones-f0 (Odoo 17) | fuente comprobada | El IVA es de Ángel (F0-A27). |
| F0-C30 | Los costes del máster se reparten entre las houses por peso tasable (aéreo) o W/M (grupaje), y los cobrados por partida van a su partida. | blogs del sector; Ángel 27/10 (tasable) | fuente débil | En Odoo 17 el reparto es manual; la regla automática se apoya en fuentes web. |
| F0-C16 | BOSS absorbe el FuelEU dentro del «THC + gastos portuarios» de precio fijo; no va como línea aparte. | Odoo 17 (17 facturas, solo de proveedor); correo de Cristina 28/09 | fuente comprobada |  |
| F0-A39 | La comisión del recomendador es el 40 % del (beneficio − 95 €) de cada expediente cerrado, en la 623008. | Odoo 17 (informe) | fuente débil | La propia pregunta dice que en Odoo 17 «es código, no una regla aprobada». |

## 8. Migración de datos al 1/1 — Alcance del arranque · responsable: several
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| F0-A01 | Se migran las condiciones de pago en uso y cada contacto conserva la suya; las de 75 y 90 días se marcan para revisión. | Odoo 17 account.payment.term; Ley 3/2004 | fuente comprobada |  |
| F0-A03 | Los límites de crédito de Odoo 17 se copian tal cual. | Odoo 17 (texto de la pregunta) | fuente comprobada | Combinado con F0-A05, bloquea la apertura de expedientes desde el primer día. |
| F0-A44 | Asiento de apertura del 1/1/2027 con el balance de Odoo 17, provisional y ajustado al cierre de 2026. | Odoo 17 diario «Opening Seat» | fuente comprobada |  |
| F0-A45 | Las facturas pendientes de 2026 se migran una a una como partidas abiertas. | F0-A42; práctica estándar | fuente comprobada |  |
| F0-A46 | Los documentos con fecha de diciembre de 2026 se registran en Odoo 17; Odoo 20 solo desde el 1/1/2027. | Odoo 17 práctica de cierre | fuente comprobada | Depende de F0-A20 (fecha de la factura). |
| R-A4 | Se migran todos los tipos de contacto con actividad, con sus direcciones, deduplicados y con revisión de las coincidencias aproximadas. | preguntas-abiertas R-A4; plan F2 | fuente comprobada |  |
| F0-B01 | Se migran los contactos con actividad desde el 1/1/2024, más los que tengan expediente abierto o saldo pendiente. | plan :860/:874; mapeo de Odoo 19 | fuente comprobada | El recuento aún no se ha medido. |
| F0-B02 | Los contactos que en realidad son lugares no se migran. | plan :179; mapeo de Odoo 19 | fuente comprobada |  |
| F0-B09 | Los ≈49.700 documentos históricos no se migran; solo los de los expedientes abiertos. | plan :874; mapeo de Odoo 19 | fuente comprobada |  |
| F0-C02 | Los tipos y marcas de contacto pasan uno a uno a papeles de Odoo 20; Cristina revisa solo las excepciones. | decisiones-f0 R-A4; ADR-009 | fuente comprobada | Alimenta la comprobación de R-A3. |
| P16 | Se mantienen VET, POS, DVD, IMO y DES; se archivan VAC, GT3 y GAV; DUM queda como suplido. | Odoo 17 uso por producto | fuente comprobada | Archivar es reversible. |
| F0-C73 | Pasan a Odoo 20 todos los expedientes no cerrados con actividad en 2026; los antiguos van a una lista de revisión. | decisiones-f0 (volúmenes) | fuente débil | Confianza baja; depende de F0-B19 (que sigue abierta). |
| F0-C74 | De cada expediente abierto se migran etapa, partes, contenedores, referencias, fechas y servicios pendientes, con el número de Odoo 17. | decisiones-f0; mapeo de Odoo 19 | fuente comprobada |  |

## 9. Qué se activa el 1/1 y qué queda para después — Alcance del arranque · responsable: several
| Id | Recomendación | Fuente | Comprobación | Nota |
|---|---|---|---|---|
| F0-B25 | El envío real de correo se activa el 1/1/2027; antes solo se prueba con una cuenta interna. | CLAUDE.md; seed_launch U01 | fuente comprobada |  |
| F0-B26 | Activación escalonada: el 1/1 las tareas internas y del 2 al 8/1 las externas, con lista firmada por Belal y Ángel. | plan :679/:863 | fuente comprobada |  |
| F0-A29 | La sincronización bancaria con los tres bancos de Odoo 17 se activa en el arranque, con la importación de ficheros como alternativa. | Odoo 17 (texto de la pregunta) | fuente comprobada |  |
| F0-A11 | Sin lectura automática (OCR) de facturas de proveedor en el arranque. | Odoo 17; confidencialidad | fuente comprobada |  |
| F0-A12 | Sin buzón de facturas de proveedor hasta resolver F0-B22 y F0-B23. | preguntas-abiertas B22/B23 | fuente comprobada |  |
| P45-b | No se instala Facturae mientras no haya un cliente público. | Odoo 17 módulos y adjuntos (28/10) | fuente comprobada |  |
| F0-A43 | Si VERI*FACTU es obligatorio, Ángel carga el certificado en Odoo y el envío real empieza en la fecha del BOE. | webs de asesorías (RDL 15/2025) | fuente débil | Fuentes secundarias; depende de P45-a. |
| F0-B08 | En el arranque, correo estándar desde el chatter y subida manual; la dirección por expediente, después. | plan :339; mail_alias_mixin | fuente comprobada | Cristina tiene que validar que las ofertas dejen de salir desde Outlook. |
| F0-C42 | En el arranque solo se emiten los documentos que hoy salen de Odoo 17 (OT, HBL, AWB, listado de mercancía, manifiesto). | boss_reports_brief de Odoo 19 | fuente comprobada |  |
| F0-C44 | Las AWB y sus etiquetas salen de Odoo 20 con los datos IATA cuando entre el aéreo; hasta entonces, como hoy. | decisiones-f0 (≈200 AWB) | fuente comprobada |  |
| F0-C45 | Los HBL NVOCC y el manifiesto salen de Odoo 20 cuando entren la exportación marítima y la consolidación. | decisiones-f0 (≈280 HBL) | fuente comprobada |  |
| F0-C40 | La petición de documentos con enlace de subida queda para después del 1/1. | plan :78-87 | fuente comprobada |  |
| F0-C43 | Los eventos se registran a mano en el arranque; el seguimiento automático, después. | portal-seguimiento-integraciones | fuente comprobada |  |
| F0-C50 | Sin aviso de llegada emitido por Odoo en el arranque. | decisiones-f0 (tampoco en Odoo 17) | fuente comprobada |  |
| F0-C20 | Sin oferta en formato corto en el arranque. | ADR-009 decisión 6 | fuente comprobada |  |
| P21 | Sin ofertas de tarifa por ruta; basta la oferta de tarifas por unidad. | ADR-009 decisión 6 | fuente comprobada |  |
| P34 | El precio cerrado para varios envíos queda para después del arranque. | respuestas-cristina fila 16 | fuente comprobada |  |

## Propuestas con fuente débil o que la fuente no respalda
| Id | Responsable | Problema |
|---|---|---|
| F0-A35 | Ángel | La fuente dice expresamente que es un control técnico del 28/10 y no una decisión. |
| F0-A80 | Ángel | Fuente circular (la propia pregunta, con bloqueo provisional ya implantado en 76ccb67); la regla de Odoo 17 trata de editar, no de contabilizar. |
| F0-A81 | Ángel | Fuente circular: el comportamiento provisional mientras Ángel y Cristina responden. |
| P30-b | Ángel | La línea citada es la propia pregunta, pendiente de Ángel y Cristina. |
| P01/P02-a | Ángel | Contradice P01/P02-b (solo aviso o bloqueo); respuestas-cristina fila 17 dice «nada aprobado». |
| P01/P02-b | Ángel | Bloqueo que se apoya solo en Odoo 17; incompatible con P01/P02-a y con «solo aviso» de Odoo 19. |
| P43-D8 | Cristina | Cita B18 de Odoo 19, que dice lo contrario: la venta nunca por debajo del coste. |
| F0-A20 | Ángel | El RD 1619/2012 art. 6 exige la fecha de expedición y una fecha de operación aparte; no ampara fechar la factura con la fecha del envío (y choca con VERI*FACTU). |
| F0-A24 | Ángel | Cambia la práctica de Odoo 17 apoyándose en una consulta de la DGT citada por webs de terceros, sin comprobar en la fuente oficial. |
| F0-A39 | Ángel | Se apoya solo en Odoo 17, cuyo cálculo es «código, no una regla aprobada». |
| F0-A05 | Ángel | Bloqueo que se apoya solo en «Odoo 17 lo hace». |
| F0-A08 | Ángel | Bloqueo que se apoya solo en «Odoo 17 lo hace». |
| F0-A25 | Ángel | Se apoya en Odoo 17 pero lo amplía a todos los clientes (en Odoo 17 solo desde el 01/02/2025). |
| F0-A36 | Ángel | No se ha comprobado que Odoo 17 use la 607800 cada mes. |
| F0-A32 | Ángel | Solo cita el Código Civil; no hay fuente de la práctica de BOSS. |
| F0-A43 | Ángel | Las fechas legales salen de webs de asesorías, no del BOE. |
| F0-C32 | Cristina | Bloqueo nuevo sin precedente en Odoo 17; la fuente es solo un campo de fecha en el Excel. |
| F0-C31 | Cristina | Condiciones de estado que se apoyan solo en «Odoo 17 lo hace». |
| F0-C49 | Cristina | Condición de estado que se apoya solo en «Odoo 17 lo hace». |
| F0-C66 | Cristina | Exigencia para cerrar que se apoya solo en «Odoo 17 lo hace». |
| R-A3 | Cristina | Comprobación que acaba bloqueando y se apoya solo en «Odoo 17 lo hace». |
| P23 | Cristina | 15 días frente a los 30 de Odoo 17; la regla de caducidad de Odoo 17 es otra. |
| F0-C30 | Cristina | La regla automática de reparto se apoya en blogs del sector; en Odoo 17 se reparte a mano. |
| F0-C55 | Cristina | Confianza baja: los días de antelación no tienen fuente de BOSS. |
| F0-C73 | Cristina | Confianza baja y depende de F0-B19, que sigue abierta. |
| P13 | Cristina | Las fuentes se contradicen (0,35 % y 0,60 % en las ofertas frente a una mediana del 0,5 % en Odoo 17). |

**Recomendación sobre F0-A20 (fecha de factura):** no adoptarla. El RD 1619/2012 art. 6 exige la fecha de expedición y, si es distinta, la fecha de la operación aparte; se mantiene la fecha de expedición estándar de Odoo con la fecha de la operación indicada. Revisión: Ángel o el asesor.

## Rutina técnica (se aplica sin aprobación)
F0-A04, M2-D, M2-J, M2-C, F0-A06, F0-A10, F0-A17, F0-A18, F0-A21, F0-A23, P03-d, P03-f, F0-A37, P45-c, F0-B07, F0-B10, F0-B22, F0-B23, F0-C04, F0-C05, F0-C06, F0-C07, M2-A, P01, R-S1, F0-C09, P24, P28, P40, P13, F0-C11, F0-C12, F0-C13, F0-C14, F0-C15, M2-B, R2-A6, R2-A1, M2-E, F0-C18, F0-C19, P22, P26, P43-D3, P43-D4, P43-D5, P43-D7, P43-D12, P43-D13, P43-D14, F0-C22, F0-C23, F0-C24, F0-C25, F0-C26, F0-C28, F0-C29, F0-C33, F0-C48, F0-C54, F0-C55, F0-C59, F0-C64, F0-C65, F0-C68, F0-C71, F0-C72
