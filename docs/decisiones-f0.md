# Decisiones F0 del plan «expediente completo» (28/10/2026)

Preguntas que bloquean las fases del plan (`docs/plan-expediente-completo.md`), agrupadas por persona y por etapa del expediente. **Nada de esto está decidido**: «Hoy en Odoo 17» es material para la pregunta, no la regla, y «Mientras tanto» es lo que hace Odoo 20 hasta la respuesta (estado explícito, nunca una suposición). Cada respuesta se registra con nombre y fecha en `docs/preguntas-abiertas.md`.

| Persona | Preguntas | Prioridad alta | Primera fecha límite |
|---|---|---|---|
| Ángel | 82 | 36 | 04/11/2026 |
| Cristina | 123 | 25 | 30/10/2026 |
| Belal | 26 | 12 | 30/10/2026 |

## Ángel
### Etapa 0 Partes y datos maestros
**F0-A01 · alta · antes del 04/11/2026** — ¿Cargamos en Odoo 20 las condiciones de pago que usa hoy Odoo 17 y cada cliente y proveedor migrado conserva la suya?

- Por qué: Sin condiciones de pago, las facturas de los contactos migrados no tienen el vencimiento correcto. Bloquea la carga de contactos (F2) y la facturación (F9).
- Opciones: Sí: todas las de Odoo 17 y cada contacto con la suya / Sí, pero Ángel revisa antes la lista y quita las que no se usan / No: se definen de nuevo (Ángel da la lista)
- Hoy en Odoo 17: Hoy en Odoo 17 hay 15 condiciones de pago, desde pago inmediato hasta 90 días y fin de mes siguiente.
- Mientras tanto: Odoo 20 todavía no tiene las de 6, 20, 60, 75 y 90 días. Los contactos se cargan sin condición de pago propia y quedan marcados como pendientes de Ángel; no se asigna ninguna por suposición.
- Bloquea: F2, F9

**F0-A02 · alta · antes del 04/11/2026** — ¿Se traen desde Odoo 17 las cuentas bancarias de los proveedores?

- Por qué: Sin ellas no se puede pagar a proveedores por transferencia o remesa desde Odoo 20. Forma parte del alcance de la migración de contactos que fija Belal (F2).
- Opciones: Sí, de todos los proveedores migrados / Solo de los proveedores que se pagan por transferencia o remesa / No: se dan de alta a mano cuando haga falta
- Hoy en Odoo 17: Hoy en Odoo 17 los proveedores llevan una forma de pago (transferencia, remesa…) y, los que se pagan por banco, su cuenta bancaria.
- Mientras tanto: Los proveedores se cargan sin cuenta bancaria; el pago por banco queda pendiente de esta decisión. Los números de cuenta nunca salen de Odoo.
- Bloquea: F2, F8 · con Belal

**F0-A03 · alta · antes del 05/11/2026** — ¿Se copian a Odoo 20 los límites de crédito que tienen hoy los clientes en Odoo 17?

- Por qué: El aviso de crédito de la oferta y del expediente solo funciona si el cliente tiene límite. Bloquea la carga de contactos (F2) y el control al abrir el expediente (F5).
- Opciones: Sí, tal cual / Sí, después de que Ángel los revise / No: se fijan de nuevo en Odoo 20 / No se usan límites de crédito
- Hoy en Odoo 17: Hoy en Odoo 17 algunos clientes tienen límite de crédito (ligado al seguro de crédito) y no se abre un expediente si el cliente lo supera.
- Mientras tanto: Los contactos se cargan sin límite de crédito propio, así que el aviso de crédito no salta para ellos; pendiente de Ángel.
- Bloquea: F2, F5, F9

**F0-A04 · alta · antes del 06/11/2026** — ¿Qué niveles de reclamación de cobro quiere en Odoo 20?

- Por qué: Define cómo se reclaman los cobros a los clientes migrados. Se cargan con los contactos (F2) y se usan en el cobro (F9).
- Opciones: Uno solo a los 7 días del vencimiento, como hoy / Los tres niveles estándar de Odoo / Otros niveles que indicará Ángel
- Hoy en Odoo 17: Hoy en Odoo 17 hay un solo nivel de reclamación, «7 días».
- Mientras tanto: Quedan los tres niveles estándar de Odoo sin uso; no se envía ningún recordatorio (la tarea automática está apagada hasta el arranque).
- Bloquea: F2, F9

### Etapa 1 Oferta
**F0-A00 · alta · antes del 04/11/2026** — Los suplidos (aranceles ARA, IVA de importación, etc.), ¿se facturan al cliente por el importe exacto pagado, sin el margen por defecto? Y si BOSS cobra algo por adelantar ese dinero, ¿se factura aparte como honorario propio (no como suplido)?

- Por qué: Hoy la regla general «venta = coste + 20 %» se aplica también a los suplidos: en la prueba del 28/10 unos aranceles de 500 € salieron a 600 € y hubo que corregir la venta a mano a 500 €. Un suplido es dinero del cliente que BOSS adelanta; si lleva margen deja de ser suplido. Bloquea la oferta (F3) y la factura (F9).
- Opciones: Sí: suplidos siempre al importe exacto; el adelanto de fondos, si se cobra, es un honorario aparte / Sí al importe exacto, y no se cobra nada por adelantar / Otra regla (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 los suplidos (conceptos ARA, IVA, PLA, DUM) van en factura de impuestos con «0% EXEMPT NS».
- Mientras tanto: La regla de venta por defecto no se cambia sin su respuesta: el operativo teclea la venta del suplido igual al coste. No se generaliza ningún cambio a otros servicios.
- Bloquea: F3, F9

**P17 (ya abierta) · alta · antes del 04/11/2026** — ¿Confirma que, para un cliente español, los servicios exentos (fletes, gastos de terminal, transporte internacional…) se facturan como «exento por el artículo 22», y que a los clientes de Canarias, Ceuta y Melilla se les factura como «no sujeto por localización»?

- Por qué: Decide el IVA y la casilla del 303 de casi todas las facturas a clientes españoles. Afecta a la legalidad de la primera factura real (F4) y a las ofertas (F3).
- Opciones: Sí, las dos reglas / Sí la del artículo 22; Canarias, Ceuta y Melilla de otra forma (indicar) / No: como hoy en Odoo 17 (sujeto al 0 %)
- Hoy en Odoo 17: Hoy en Odoo 17 esos servicios llevan «0% S» (sujeto al 0 %), que se declara en otra casilla del 303.
- Mientras tanto: Odoo 20 lo aplica así como propuesta aprobada por Belal el 23/10, marcada como pendiente de ratificación de Ángel.
- Bloquea: F3, F4

**P17-NS (ya abierta) · alta · antes del 04/11/2026** — ¿Qué IVA llevan la caución (CAU) y el quebranto bancario (QBR) cuando el cliente es español?

- Por qué: Mientras no se decida, ninguna oferta con caución o quebranto a un cliente español se puede confirmar (F3) ni facturar (F4).
- Opciones: Sujeto al 0 %, como hoy en Odoo 17 / No sujeto / Exento (indicar el artículo) / 21 % / Distinto para cada uno (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 la caución y el quebranto llevan «0% S» (sujeto al 0 %).
- Mientras tanto: «IVA pendiente» en esas líneas: la oferta no se puede enviar ni confirmar.
- Bloquea: F3, F4

**P11 (ya abierta) · alta · antes del 05/11/2026** — ¿Confirma que los gastos de terminal (THC) llevan todos el mismo IVA de servicio exento, sin separar ninguna parte al 21 %?

- Por qué: El THC está en casi todas las importaciones marítimas; su IVA debe ser correcto en la primera factura real (F4).
- Opciones: Sí, todo exento / No: una parte va al 21 % (indicar cuál)
- Mientras tanto: Se aplica «todo exento» como propuesta aprobada por Belal el 23/10, pendiente de ratificación de Ángel.
- Bloquea: F3, F4

**M2-D (ya abierta) · alta · antes del 06/11/2026** — Para estimar los aranceles en la oferta según el código de la mercancía, ¿de dónde salen los porcentajes?

- Por qué: Solo afecta a la estimación de aranceles en la oferta (F3), que hoy se teclea; la respuesta decide si hay que construir una tabla o una consulta.
- Opciones: Se teclean en cada oferta, como ahora / De una tabla propia que mantiene BOSS / De la base oficial TARIC de la UE (consulta externa) / Los da el agente de aduanas en cada caso
- Mientras tanto: El código de la mercancía se guarda y la estimación de aranceles se teclea; no se calcula nada.
- Bloquea: F3

**M2-G (ya abierta) · alta · antes del 06/11/2026** — Cuando todavía no se conoce la fecha de salida, ¿confirma que el flete se cotiza con el precio vigente el día de la oferta?

- Por qué: Decide qué versión de la tarifa de flete se usa en ofertas sin fecha de salida (F3). Ya está aplicado: solo falta confirmarlo.
- Opciones: Sí / No: el flete queda sin precio hasta conocer la salida / Se usa la fecha de salida prevista que dé el cliente
- Mientras tanto: Se aplica así y la línea de la oferta lo explica; queda pendiente de confirmación de Ángel.
- Bloquea: F3

**M2-J (ya abierta) · alta · antes del 06/11/2026** — En los precios por kilo, ¿le vale ver dos decimales como mínimo y hasta cuatro cuando el precio los tiene, o prefiere que esos precios se expresen «por 100 kg»?

- Por qué: Ya está aplicado en ofertas y tarifas (F3); solo falta confirmarlo.
- Opciones: Vale así (mínimo dos, hasta cuatro) / Pasar esos precios a «por 100 kg»
- Mientras tanto: Aplicado: mínimo dos decimales y cuatro solo si el valor los tiene; pendiente de confirmación de Ángel.
- Bloquea: F3

**P01/P02-a (ya abierta) · media · antes del 11/11/2026** — ¿Hay un margen mínimo por oferta o por expediente? Si lo hay, ¿cuál es?

- Por qué: Sin este valor, un expediente con margen bajo o negativo se factura y se cierra sin que nadie lo revise (F10).
- Opciones: No hay margen mínimo / Sí: un porcentaje (indicar) / Sí: un importe mínimo por expediente (indicar) / Distinto por tráfico o por cliente (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 un aviso de margen bloquea la factura y el cierre hasta que un responsable lo desbloquea con motivo.
- Mientras tanto: Sin margen mínimo: ninguna oferta ni expediente avisa por margen bajo; queda pendiente.
- Bloquea: F10 · con Cristina

**P03-a (ya abierta) · media · antes del 11/11/2026** — Para un coste en dólares, ¿confirma que se convierte a euros con el tipo de cambio del día de la oferta y que ese tipo queda fijo al aceptarla?

- Por qué: Fija el coste y el margen en euros de todos los fletes en dólares; condiciona el control de facturas de proveedor (F8) y la facturación (F9).
- Opciones: Sí / No: tipo del día de la factura del proveedor / No: tipo que fije la naviera para el expediente
- Hoy en Odoo 17: Hoy en Odoo 17 cada expediente guarda los tipos diarios del BCE en su «fecha importante» y, si se quiere, el tipo de la naviera.
- Mientras tanto: Ajuste «tipo del día de la oferta, fijo al aceptar», aprobado por Belal el 23/10 y pendiente de ratificación de Ángel.
- Bloquea: F8, F9, F13

**P43-D11 (ya abierta) · media · antes del 13/11/2026** — El precio único de venta del almacenaje aéreo (ALM), ¿lleva el mismo IVA que hoy tiene el almacenaje en la tabla de IVA de BOSS (21 %), sin ninguna regla especial?

- Por qué: Se necesita para construir la venta única de almacenaje del aéreo (F11).
- Opciones: Sí / No (indicar el IVA)
- Mientras tanto: No hay precio de venta automático de almacenaje: se teclea y lleva el IVA de la tabla de BOSS; la regla queda pendiente.
- Bloquea: F11

**P44-IVA (ya abierta) · media · antes del 13/11/2026** — Si se crea el servicio propio de almacén fuera del aeropuerto que pidió Cristina (por palé, metro cúbico, entradas y salidas), ¿qué IVA lleva?

- Por qué: Hace falta para crear ese servicio con su IVA en el aéreo (F11).
- Opciones: 21 %, como el almacenaje del aeropuerto en la tabla de IVA de BOSS / Depende del tráfico o del cliente (indicar la regla) / Otro IVA (indicar)
- Mientras tanto: El servicio no se crea hasta que Cristina lo apruebe y Ángel fije su IVA; ese coste se teclea a mano.
- Bloquea: F11 · con Cristina

### Etapa 2 Apertura
**F0-A05 · media · antes del 11/11/2026** — Si un cliente supera su límite de crédito, ¿qué pasa al abrir su expediente?

- Por qué: Sin control, se puede abrir y operar un envío de un cliente por encima de su riesgo (F5).
- Opciones: Solo un aviso / No se abre hasta que lo autorice un responsable (indicar quién) / No se abre hasta que el saldo baje del límite
- Hoy en Odoo 17: Hoy en Odoo 17 no se puede crear el expediente si el cliente supera su límite de crédito.
- Mientras tanto: En la oferta solo sale el aviso de crédito estándar de Odoo 20 (punto 36 de la reunión del 27/10); al abrir el expediente no se comprueba nada; pendiente de Ángel.
- Bloquea: F5

**M2-C (ya abierta) · media · antes del 11/11/2026** — En una oferta de tarifas (precios por contenedor sin cantidades), ¿cuándo se abre el expediente: al aceptar el cliente la oferta o cuando hace la reserva con los contenedores?

- Por qué: Decide cuándo nace el expediente de los clientes con oferta de tarifas y qué pasa con la petición de reserva del portal (F5).
- Opciones: Al aceptar la oferta (como ahora en Odoo 20) / Al hacer la reserva con los contenedores
- Hoy en Odoo 17: Hoy en Odoo 17 el expediente se crea con un botón desde la oferta y existe un pre-expediente que no se puede facturar.
- Mientras tanto: Al aceptar se piden los contenedores y se abre el expediente; la regla figura como pendiente de Ángel.
- Bloquea: F5 · con Cristina

### Etapa 5 Destino y aduana
**P18 (ya abierta) · alta · antes del 04/11/2026** — ¿Confirma estas cuentas para los suplidos: IVA de importación 419001 al facturar al cliente y 419003 en la factura del agente; aranceles 419002 y 419004; antidumping 419005 en los dos sentidos; impuesto del plástico 419006 y 419007?

- Por qué: Sin estas cuentas no se pueden registrar la factura del agente de aduanas ni la refacturación de los suplidos al cliente (F4, F7, F9).
- Opciones: Sí, este mapa / Una sola pareja de cuentas (repercutido y soportado) para todos / Otras cuentas (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 se usan las subcuentas 419001 a 419007 (pasivo corriente, no conciliables).
- Mientras tanto: Aplicado en boss20 el 26/10 por mandato de Belal para sustituir la cuenta 419000, que no servía; pendiente de ratificación de Ángel.
- Bloquea: F4, F7, F9

**F0-A06 · alta · antes del 06/11/2026** — En los despachos de importación, ¿con qué garantía se pagan los impuestos a la aduana (la 031, la garantía de BOSS o la del cliente) y en qué casos se cobra caución (CAU) al cliente?

- Por qué: Decide cuándo se cotiza la caución (F3) y qué se registra en el bloque de aduana del expediente (F7).
- Opciones: Caución solo cuando se usa la garantía de BOSS / Caución siempre que BOSS paga los impuestos por cuenta del cliente, con cualquier garantía / Se decide por cliente (indicar) / Otra regla (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 cada partida guarda el tipo de garantía. En la hoja «Nuevo Odoo», Cristina dejó escrito como requisito (no como decisión) que la forma de pago de los impuestos (garantía 031 o de BOSS) sale de la ficha del cliente y que con ella se generan la venta y la compra de la caución.
- Mientras tanto: El expediente no registra qué garantía se usa; la caución se añade a mano y queda sin precio aprobado; pendiente.
- Bloquea: F3, F7 · con Cristina

### Etapa 6 Entrega y contenedores
**F0-A07 · media · antes del 11/11/2026** — ¿Un expediente puede pasar a «Entregado» sin estar facturado al cliente?

- Por qué: Es una de las condiciones de la etapa de entrega (F7).
- Opciones: Sí: la facturación va aparte / No: debe estar facturado, como hoy en Odoo 17 / Sí, pero con un aviso
- Hoy en Odoo 17: Hoy en Odoo 17 no se pasa a Entregado si el expediente no está facturado; además se exige la fecha de descarga y el levante cuando BOSS lleva la aduana.
- Mientras tanto: El paso a «Entregado» no comprueba nada; la condición queda pendiente de Cristina y Ángel.
- Bloquea: F7 · con Cristina

### Etapa 7 Proveedores
**P30-a (ya abierta) · alta · antes del 04/11/2026** — ¿Confirma que la factura de un proveedor se puede contabilizar al llegar, pero no se puede pagar hasta que ese servicio esté facturado al cliente (salvo costes que asume BOSS y fletes pagados por adelantado)?

- Por qué: Es la regla central del pago a proveedores (F8).
- Opciones: Sí / Solo avisar, sin bloquear el pago / Bloquear también la contabilización
- Hoy en Odoo 17: Hoy en Odoo 17 no existe ese bloqueo; es un requisito escrito por Cristina en «Nuevo Odoo».
- Mientras tanto: Ajuste «Bloquear el pago (contabilizar permitido)», aprobado por Belal el 23/10, pendiente de ratificación de Ángel y Cristina.
- Bloquea: F8 · con Cristina

**A01 (ya abierta) · alta · antes del 05/11/2026** — ¿Qué IVA de compra lleva cada tipo de factura de proveedor: naviera española, handler, agente de aduanas (honorarios y suplidos), agente extranjero y transportista?

- Por qué: Un IVA de compra mal elegido descuadra el 303. Bloquea la base contable (F4) y el registro de facturas de proveedor (F8).
- Opciones: Una tabla fija por tipo de proveedor que da Ángel / El mismo criterio que hoy en Odoo 17 / Lo elige quien registra según el documento, sin regla
- Hoy en Odoo 17: Hoy en Odoo 17 la factura de suplidos del agente de aduanas lleva «0% EXEMPT INC OP» y una factura de naviera «0% S INC».
- Mientras tanto: Lo elige quien registra la factura, sin regla; en las pruebas hay facturas de una naviera española con IVA intracomunitario, que no corresponde. Pendiente de Ángel.
- Bloquea: F4, F8

**P37-b (ya abierta) · alta · antes del 05/11/2026** — ¿Qué cuentas de gasto usa Odoo 20 para cada familia de servicio y para las comisiones? ¿Las mismas que hoy en Odoo 17 (una cuenta 607 por familia, con 607400 para el flete y 607401 para el profit share, y 623008 para comisiones)?

- Por qué: Sin estas cuentas el coste de cada expediente cae en una cuenta genérica y no se puede comparar con Odoo 17 ni cerrar el mes por familia (F4, F8, F13).
- Opciones: Las mismas que en Odoo 17 / Las de Odoo 17 con cambios (indicar) / Otras cuentas (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el coste de cada familia de servicio va a su cuenta del grupo 607 (por ejemplo 607400 gastos por flete y 607401 profit share) y las comisiones a 623008.
- Mientras tanto: Todas las facturas de proveedor van a la cuenta genérica de compras 600000; no se usa en facturas reales hasta que Ángel decida.
- Bloquea: F4, F8, F13

**P33 (ya abierta) · media · antes del 06/11/2026** — ¿Confirma que los servicios de proveedores se compran con pedido de compra y que los suplidos (IVA y aranceles del DUA) se registran directamente con la factura del agente de aduanas, sin pedido?

- Por qué: Define cómo entra el coste en el expediente (F7, F8). Ya está aplicado: falta confirmarlo.
- Opciones: Sí / No: los suplidos también con pedido / No: sin pedidos de compra, como hoy en Odoo 17
- Hoy en Odoo 17: Hoy en Odoo 17 no se usa la app de Compras: las facturas de proveedor se registran directamente contra las previsiones del expediente.
- Mientras tanto: Funciona así como propuesta aprobada por Belal el 23/10, pendiente de ratificación de Cristina y Ángel.
- Bloquea: F7, F8 · con Cristina

**F0-A08 · media · antes del 11/11/2026** — ¿Se impide contabilizar la factura de un proveedor que se paga por transferencia o remesa si no tiene cuenta bancaria registrada?

- Por qué: Evita facturas de proveedor que luego no se pueden pagar por banco (F8).
- Opciones: Sí, bloquear, como hoy en Odoo 17 / Solo avisar / No comprobar
- Hoy en Odoo 17: Hoy en Odoo 17 no se puede confirmar la factura de un proveedor con forma de pago transferencia o remesa sin cuenta bancaria.
- Mientras tanto: No se comprueba nada; pendiente de Ángel.
- Bloquea: F8

**F0-A09 · media · antes del 11/11/2026** — ¿Cómo se tratan los pagos a un proveedor antes de recibir su factura (por ejemplo, proformas del DUA o del handling)?

- Por qué: Sin esto, los aranceles y el handling pagados antes de la llegada no cuentan en el coste ni en lo pagado del expediente (F8).
- Opciones: Anticipo ligado al expediente, sin esperar a facturar al cliente / Anticipo ligado al expediente, solo si el servicio ya está facturado al cliente / No se paga nada antes de la factura
- Hoy en Odoo 17: Hoy en Odoo 17 se pagan desde el banco proformas de proveedor (DUA, handling de AWB) antes de que llegue la factura.
- Mientras tanto: No hay circuito: un pago anticipado no queda ligado al expediente ni a la regla de pago; pendiente de Ángel.
- Bloquea: F8

**F0-A10 · media · antes del 11/11/2026** — En Odoo 20, ¿quién revisa las facturas de proveedor que llegan sin expediente o que no cuadran con lo previsto?

- Por qué: El coste real y el margen definitivo dependen de que cada factura llegue a su expediente (F8).
- Opciones: Contabilidad (Ángel), con una lista de control en Odoo / El operativo del expediente / Contabilidad las detecta y el operativo las resuelve
- Hoy en Odoo 17: Hoy en Odoo 17 se lleva en un proyecto «Facturas de proveedores» que gestiona Ángel, con etapas como «No sabemos expediente», «No cuadran previsiones» y «Reclamada».
- Mientras tanto: No hay lista de control; cada factura se registra a mano desde el pedido o como coste sin pedido; pendiente.
- Bloquea: F8

**F0-A11 · media · antes del 11/11/2026** — ¿Quiere que Odoo 20 lea automáticamente las facturas de proveedor (OCR), sabiendo que cada PDF se envía a un servicio externo de Odoo?

- Por qué: Ahorra tecleo y enlaza la factura con su pedido y su expediente, pero envía datos fuera. Se diseña en F8 y solo se activaría en el arranque (F15).
- Opciones: Sí, desde el arranque / Más adelante / No
- Hoy en Odoo 17: Hoy en Odoo 17 no hay lectura automática: las facturas se teclean.
- Mientras tanto: Desactivado; las facturas se teclean y no sale ningún dato.
- Bloquea: F8, F15 · con Belal

**F0-A12 · baja · antes del 11/11/2026** — ¿Quiere un buzón de correo para facturas de proveedor que cree la factura en borrador en Odoo al recibirla?

- Por qué: Depende de la infraestructura de correo que decide Belal; se diseña con las facturas de proveedor (F8) y solo se activaría en el arranque (F15).
- Opciones: Sí, desde el arranque / Más adelante / No
- Hoy en Odoo 17: Hoy en Odoo 17 las facturas de proveedor se registran a mano y se siguen en el proyecto «Facturas de proveedores».
- Mientras tanto: Sin buzón ni servidor de correo: no entra ningún correo en Odoo 20.
- Bloquea: F8, F15 · con Belal

**P03-b (ya abierta) · media · antes del 11/11/2026** — Cuando la factura de un proveedor en dólares llega con otro tipo de cambio que el previsto, ¿la diferencia se trata como diferencia de cambio, separada de la diferencia de precio?

- Por qué: Sin separarlas, cada expediente con flete en dólares queda bloqueado o mal explicado al cerrar (F8, F10).
- Opciones: Sí, aparte y sin bloquear el cierre del expediente / Sí, aparte, pero hay que revisarla antes de cerrar / No: todo junto como diferencia a revisar
- Hoy en Odoo 17: Hoy en Odoo 17 el expediente guarda los tipos diarios del BCE y puede fijar además el tipo de la naviera.
- Mientras tanto: La diferencia mezcla precio y tipo de cambio: todo flete en dólares aparece «a revisar»; pendiente de Ángel.
- Bloquea: F8, F10

**P30-b (ya abierta) · media · antes del 11/11/2026** — Si una factura de proveedor tiene varios servicios y solo uno está sin facturar al cliente, ¿se retiene el pago de toda la factura o solo el de ese servicio?

- Por qué: Decide si contabilidad puede hacer pagos parciales a proveedores (F8).
- Opciones: Toda la factura / Solo el importe de ese servicio (se paga el resto)
- Mientras tanto: Se retiene toda la factura; pendiente de Ángel y Cristina.
- Bloquea: F8 · con Cristina

**P30-c (ya abierta) · media · antes del 11/11/2026** — ¿La retención del pago debe valer también cuando contabilidad paga conciliando directamente el extracto del banco o casando apuntes a mano?

- Por qué: Si no, un pago conciliado desde el banco se salta la regla (F8).
- Opciones: Sí, por cualquier camino / No, solo al registrar el pago desde la factura
- Mientras tanto: Solo se controla el pago registrado desde la factura o desde el asistente de pagos; la conciliación bancaria y la manual no lo comprueban todavía (hueco conocido).
- Bloquea: F8 · con Cristina

**P30-d (ya abierta) · media · antes del 11/11/2026** — Si un proveedor envía un abono, ¿se puede aplicar a una factura suya que sigue retenida por esta regla?

- Por qué: Completa el alcance de la regla de pago a proveedores (F8).
- Opciones: Sí, el abono se aplica siempre / No: la factura sigue retenida hasta facturar al cliente
- Mientras tanto: Los abonos de proveedor no se comprueban; la regla queda pendiente de Ángel y Cristina.
- Bloquea: F8 · con Cristina

**P32 (ya abierta) · media · antes del 11/11/2026** — ¿Confirma que las facturas de proveedor de servicios se controlan por lo realmente prestado (lo que el operativo marca como hecho) y no por lo pedido?

- Por qué: Decide cuándo se puede registrar la factura del proveedor de un pedido (F8).
- Opciones: Sí, por lo prestado / No, por lo pedido
- Hoy en Odoo 17: Hoy en Odoo 17 la factura se casa con las previsiones de compra del expediente, sin pedidos de compra.
- Mientras tanto: Funciona por lo prestado como propuesta aprobada por Belal el 23/10, pendiente de ratificación de Ángel.
- Bloquea: F8

**P39 (ya abierta) · baja · antes del 20/11/2026** — ¿Se registran en Odoo 20 los gastos pequeños de empleados o con tarjeta de empresa (taxis, mensajería, tasas pagadas con tarjeta) imputándolos al expediente?

- Por qué: Si se dan, faltarían en el coste real y el margen del expediente (F17, fase condicional).
- Opciones: Sí, los pagados por empleados y con tarjeta / Solo los pagados con tarjeta de empresa / No
- Mientras tanto: Propuesta aprobada por Belal el 23/10, pendiente de ratificación de Ángel: sin la app de Gastos (no está instalada); esos gastos no llegan al coste del expediente.
- Bloquea: F17 · con Belal

### Etapa 8 Factura al cliente
**P45-a (ya abierta) · alta · antes del 04/11/2026** — ¿Debe BOSS enviar sus facturas a la AEAT desde el 1/1/2027? Si es así, ¿por SII o por VERI*FACTU?

- Por qué: Puede ser obligatorio para la primera factura real del 1/1/2027 y el plazo legal no está verificado (lo confirma Ángel o el asesor). Bloquea la preparación en modo de pruebas (F4) y el arranque (F15).
- Opciones: Sí, por SII (indicar desde cuándo) / Sí, por VERI*FACTU (indicar desde cuándo) / Todavía no es obligatorio (indicar desde cuándo lo será) / Lo confirma el asesor fiscal (indicar fecha de respuesta)
- Hoy en Odoo 17: Hoy en Odoo 17 no hay SII ni VERI*FACTU instalados.
- Mientras tanto: Ningún módulo instalado en Odoo 20; nada se envía a la AEAT.
- Bloquea: F4, F15

**F0-A13 · alta · antes del 05/11/2026** — ¿Qué mención legal debe imprimir la factura cuando un servicio lleva IVA 0 % a un cliente de fuera de la UE (exportación o transporte internacional)?

- Por qué: Una factura con IVA 0 % debe indicar el motivo de la exención; hoy ese caso sale sin texto. Afecta a la primera factura real (F4, F9).
- Opciones: El texto que indique Ángel o el asesor / El mismo texto del artículo 22 que ya sale en las facturas exentas a clientes españoles
- Mientras tanto: Ese IVA no tiene mención: la factura sale sin el motivo del 0 % y no se usa en facturas reales hasta tenerla.
- Bloquea: F4, F9

**F0-A14 · alta · antes del 05/11/2026** — ¿Qué mención legal debe imprimir la factura cuando el servicio no está sujeto al IVA español por ser para Canarias, Ceuta o Melilla?

- Por qué: La factura debe explicar por qué no lleva IVA; hoy ese caso sale sin texto (F4, F9).
- Opciones: El texto que indique Ángel o el asesor / Ninguna mención
- Mientras tanto: La factura sale sin mención para ese caso; pendiente de Ángel.
- Bloquea: F4, F9

**F0-A15 · alta · antes del 05/11/2026** — ¿Qué mención debe imprimir la factura en los suplidos (IVA y aranceles pagados en nombre del cliente)?

- Por qué: La factura debe dejar claro que los suplidos no forman parte de la base del IVA (F4, F9).
- Opciones: El texto que indique Ángel o el asesor / Ninguna: basta con mostrarlos aparte, fuera de la base imponible
- Mientras tanto: Sin mención y sin sección propia de suplidos en la factura; pendiente de Ángel.
- Bloquea: F4, F9

**P37-a (ya abierta) · alta · antes del 05/11/2026** — ¿Qué cuentas de ingreso usa Odoo 20 para cada familia de servicio? ¿Las mismas que hoy en Odoo 17 (705001 flete terrestre, 705002 aduana, 705003 gastos locales, 705004 flete, 705005 profit share, 705006 locales extraordinarios, 705007 seguro y courier, 705008 almacén y 705009 consultoría)?

- Por qué: Sin estas cuentas la venta de cada expediente cae en una cuenta genérica y no hay cuenta de resultados por familia (F4, F13).
- Opciones: Las mismas que en Odoo 17 / Las de Odoo 17 con cambios (indicar) / Otras cuentas (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 la venta de cada familia de servicio va a su cuenta, de 705001 a 705009.
- Mientras tanto: Toda la venta va a la cuenta genérica 700000; no se usa en facturas reales hasta que Ángel decida.
- Bloquea: F4, F13

**F0-A16 · alta · antes del 06/11/2026** — ¿Qué debe ir al pie de la factura: los datos de inscripción en el Registro Mercantil y algún texto de condiciones de pago o condiciones generales?

- Por qué: Son datos legales y comerciales de la factura; hoy no sale ninguno (F4, F9).
- Opciones: Solo la inscripción en el Registro Mercantil / Inscripción y un texto de condiciones de pago (lo da Ángel) / Inscripción y condiciones generales (las da Ángel)
- Mientras tanto: La factura sale sin pie legal ni condiciones; pendiente de Ángel.
- Bloquea: F4, F9

**F0-A17 · alta · antes del 06/11/2026** — ¿Qué cuenta bancaria de BOSS se imprime en las facturas a clientes: una sola, o una para euros y otra para dólares?

- Por qué: Sin cuenta, el cliente no sabe dónde pagar (F4, F9). El número de cuenta lo introduce Ángel directamente en Odoo; no se envía por correo ni por chat.
- Opciones: Una sola cuenta en euros para todas / Una para euros y otra para dólares, según la moneda de la factura / Según el cliente (indicar la regla)
- Hoy en Odoo 17: Hoy en Odoo 17 las facturas imprimen una cuenta bancaria de BOSS.
- Mientras tanto: La factura sale sin cuenta bancaria; pendiente de Ángel.
- Bloquea: F4, F9

**F0-A18 · alta · antes del 06/11/2026** — Desde el 1/1/2027, ¿qué numeración llevan en Odoo 20 las facturas, los abonos y las facturas de proveedor?

- Por qué: La primera factura real debe seguir una serie continua que no choque con la de Odoo 17 (F4 la prepara, F15 la activa).
- Opciones: Los formatos de hoy con el año 27: «F27 MM-NNNN» (serie mensual), «FR27 NNNN» y «BILL/2027/MM/NNNN» / Esos formatos para facturas y abonos; las de proveedor con el formato de Odoo 20 / Formato nuevo (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 las facturas son «F26 MM-NNNN» (serie mensual), los abonos «FR26 NNNN» y las facturas de proveedor «BILL/2026/MM/NNNN».
- Mientras tanto: Odoo 20 numera solo en pruebas con su formato estándar (por ejemplo INV/2026/00001); la serie definitiva se prepara y se activa en el arranque cuando Ángel decida.
- Bloquea: F4, F15

**F0-A19 · alta · antes del 06/11/2026** — ¿Factura BOSS algún servicio con IVA reducido (10 % o 4 %)? Si es así, ¿cuáles y en qué casos?

- Por qué: Si existen, la primera factura real con esos servicios llevaría un IVA incorrecto (F4).
- Opciones: No, nunca / Sí (indicar servicios y casos)
- Hoy en Odoo 17: Hoy en Odoo 17 la creación de facturas contempla líneas al 4 % y al 10 %; no se ha comprobado si se usan.
- Mientras tanto: La tabla de IVA de BOSS no tiene tipos reducidos; ningún servicio los usa hasta que Ángel lo indique.
- Bloquea: F4

**P31 (ya abierta) · alta · antes del 06/11/2026** — ¿Confirma que no se puede contabilizar la factura de un cliente de España (o sin país) que no tenga NIF u otra identificación, que a los clientes extranjeros se les factura sin exigir NIF y que una dirección incompleta solo avisa?

- Por qué: Decide qué datos del cliente son obligatorios para la primera factura real (F4, F9).
- Opciones: Sí, así / Además, bloquear si falta la dirección / Exigir también NIF a los clientes de la UE
- Hoy en Odoo 17: Hoy en Odoo 17 se bloquea a los clientes de España o sin país que no tienen NIF; a los extranjeros no.
- Mientras tanto: Funciona así como propuesta aprobada por Belal el 23/10, pendiente de ratificación de Ángel.
- Bloquea: F4, F9

**P45-b (ya abierta) · alta · antes del 06/11/2026** — ¿Factura BOSS a alguna administración pública que exija factura electrónica (Facturae)?

- Por qué: Si es así, esas facturas no se podrían emitir desde Odoo 20 sin prepararlo antes (F4, F15).
- Opciones: Sí (indicar a quién) / No
- Hoy en Odoo 17: Hoy en Odoo 17 está instalado el módulo de Facturae; no se ha comprobado si se usa.
- Mientras tanto: Facturae no está instalado en Odoo 20; pendiente de Ángel.
- Bloquea: F4, F15

**F0-A20 · alta · antes del 11/11/2026** — ¿Qué fecha lleva la factura al cliente: el día en que se emite, o una fecha del envío (por ejemplo, la llegada en importación o la salida en exportación), como hace hoy Odoo 17?

- Por qué: La fecha decide el periodo de IVA y el mes de la venta de la primera factura real (F9, F10).
- Opciones: El día de emisión / Una fecha del envío (indicar cuál) / Otra regla (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 la factura toma como fecha la «fecha importante» del expediente.
- Mientras tanto: La factura lleva la fecha del día en que se contabiliza (comportamiento estándar de Odoo); la regla queda pendiente de Ángel.
- Bloquea: F9, F10

**F0-A21 · media · antes del 11/11/2026** — ¿Los suplidos se facturan en una factura aparte de los servicios, como hoy, o en la misma factura con una sección propia?

- Por qué: Decide cómo se construye la facturación de las importaciones con despacho (F9).
- Opciones: Factura aparte, como hoy / Misma factura con una sección de suplidos / Según el cliente (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 los suplidos van en una factura aparte de tipo «impuestos», solo con el IVA 0 % de suplidos y con su propio vencimiento.
- Mientras tanto: Servicios y suplidos salen en la misma factura, sin sección propia; pendiente de Ángel.
- Bloquea: F9

**F0-A22 · media · antes del 11/11/2026** — Si los suplidos van en factura aparte, ¿usan la misma serie de numeración que las facturas de servicios o una propia?

- Por qué: Decide el diario y la numeración de las facturas de suplidos (F9).
- Opciones: La misma serie, como hoy / Una serie propia (indicar formato)
- Hoy en Odoo 17: Hoy en Odoo 17 las facturas de suplidos usan la misma serie mensual que el resto.
- Mientras tanto: Una sola serie para todo; pendiente de Ángel.
- Bloquea: F9

**F0-A23 · media · antes del 11/11/2026** — ¿Los suplidos tienen, para cada cliente, un vencimiento distinto del de los servicios?

- Por qué: Los suplidos son dinero que adelanta BOSS; su vencimiento afecta a la tesorería (F9).
- Opciones: Sí: cada cliente con su vencimiento de suplidos, copiado de Odoo 17 / No: el mismo vencimiento que los servicios
- Hoy en Odoo 17: Hoy en Odoo 17 cada cliente puede tener una condición de pago aparte para las facturas de impuestos (por ejemplo 30 días frente a 60 días de los servicios).
- Mientras tanto: Mismo vencimiento que los servicios; pendiente de Ángel.
- Bloquea: F9

**F0-A24 · media · antes del 11/11/2026** — ¿Las facturas de suplidos cuentan en la declaración anual de operaciones con terceros (modelo 347)?

- Por qué: Afecta a los importes declarados por cliente en el 347 (F9).
- Opciones: Sí, como hoy / No, se excluyen
- Hoy en Odoo 17: Hoy en Odoo 17 la factura de suplidos se marca como operación normal para el 347.
- Mientras tanto: Odoo 20 las cuenta como cualquier otra factura; pendiente de Ángel.
- Bloquea: F9

**F0-A25 · media · antes del 11/11/2026** — ¿Se impide facturar a un cliente que no tiene condición de pago configurada?

- Por qué: Evita facturas con un vencimiento equivocado (F9).
- Opciones: Sí, como hoy en Odoo 17 / No: se factura con pago inmediato / Solo avisar
- Hoy en Odoo 17: Hoy en Odoo 17 no se genera la factura si el cliente (creado desde el 01/02/2025) no tiene configurados los días de pago.
- Mientras tanto: No se comprueba; sin condición, el vencimiento es la fecha de la factura (estándar de Odoo). Pendiente de Ángel.
- Bloquea: F9

**F0-A26 · media · antes del 11/11/2026** — ¿Se piden anticipos o proformas a los clientes (por ejemplo, para pagar aranceles e IVA antes del despacho)?

- Por qué: Si se usan, el cobro y el reparto por expediente tienen que contemplarlos (F9).
- Opciones: Sí, con factura de anticipo / Sí, con proforma sin valor fiscal / No
- Mientras tanto: No hay circuito de anticipos; una factura de anticipo no se reparte al expediente. Pendiente de Ángel.
- Bloquea: F9

**P03-c (ya abierta) · media · antes del 11/11/2026** — ¿Quiere fijar un tipo de cambio por expediente (por ejemplo, el de la naviera) que se use en todas sus facturas, como hoy en Odoo 17 en marítimo?

- Por qué: Decide con qué tipo se factura en euros un flete en dólares (F8, F9).
- Opciones: Sí, obligatorio en marítimo antes de facturar / Sí, opcional / No: tipo del BCE de cada fecha
- Hoy en Odoo 17: Hoy en Odoo 17 un expediente marítimo no se puede facturar sin fijar su tipo de cambio (el de la naviera o el del BCE de su fecha).
- Mientras tanto: No hay tipo por expediente: se usa el tipo de Odoo de cada fecha; pendiente de Ángel.
- Bloquea: F8, F9

**P03-d (ya abierta) · media · antes del 11/11/2026** — ¿A quién se factura en dólares?

- Por qué: Sin esta regla no se puede facturar en dólares a los agentes (F9, F13).
- Opciones: A los agentes extranjeros cuando el flete está en dólares / Siempre en euros / Lo decide el comercial en cada oferta
- Hoy en Odoo 17: Hoy en Odoo 17 algunas facturas a agentes salen en dólares.
- Mientras tanto: La factura sale en la moneda del pedido (hoy todo en euros); no se puede elegir otra. Pendiente de Ángel.
- Bloquea: F9, F13

**P03-e (ya abierta) · media · antes del 11/11/2026** — Cuando una oferta en dólares se factura en euros, ¿se añade una línea de quebranto bancario (QBR)? Si es así, ¿con qué porcentaje y sobre qué importe?

- Por qué: Hoy se cobra en las facturas en euros de fletes en dólares; sin la regla no se puede reproducir (F9, F13).
- Opciones: Sí, 1 % sobre el flete en dólares / Sí, con otro porcentaje o base (indicar) / No se cobra quebranto
- Hoy en Odoo 17: Hoy en Odoo 17 la factura en euros lleva una línea «QUEBRANTO BANCARIO» de alrededor del 1 % del flete en dólares (deducido de una factura; la base no está confirmada).
- Mientras tanto: No hay línea de quebranto. La propuesta aprobada por Belal el 23/10 (quebranto solo cuando una oferta en dólares se factura en euros) está pendiente de ratificación de Ángel, y el porcentaje sin decidir.
- Bloquea: F9, F13

**P03-f (ya abierta) · baja · antes del 11/11/2026** — En una factura en euros de un flete en dólares, ¿debe verse también el importe original en dólares de cada línea?

- Por qué: Es un dato de presentación de la factura (F9).
- Opciones: Sí / No
- Hoy en Odoo 17: Hoy en Odoo 17 cada línea de la factura en euros guarda el importe original en dólares (no se ha comprobado si se imprime).
- Mientras tanto: Solo se muestra el importe en euros; pendiente de Ángel.
- Bloquea: F9

**F0-A27 · media · antes del 13/11/2026** — Cuando BOSS factura un reparto de beneficio (profit share) a un agente extranjero, ¿qué IVA lleva?

- Por qué: Necesario para liquidar los expedientes de agente (F13).
- Opciones: El mismo que hoy en Odoo 17 («0% EX S») / Otro (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el profit share facturado a un agente lleva «0% EX S» y va a la cuenta 705005.
- Mientras tanto: No se factura profit share en Odoo 20; pendiente de Ángel.
- Bloquea: F13

### Etapa 9 Cobros y pagos
**F0-A81 · alta · antes del 04/11/2026** — P30 impide EMITIR el pago de una factura de proveedor antes de facturar el servicio al cliente. Si el pago ya ha salido del banco (por ejemplo, un cargo directo de la naviera), ¿le parece bien que al conciliar el extracto Odoo lo registre y lo marque como «pagado antes de facturar al cliente» en la factura y en el expediente, en lugar de impedir la conciliación?

- Por qué: Impedir la conciliación dejaría la contabilidad distinta del banco real. Lo implementado el 28/10: el asistente de pago sigue bloqueado; la conciliación de un movimiento real se acepta, deja una nota en la factura y en el expediente y aparece en «Pendiente» hasta que se facture al cliente.
- Opciones: Sí: registrar y marcar (lo implementado) / No: tampoco se puede conciliar hasta facturar al cliente / Registrar y además avisar a una persona (indicar quién)
- Hoy en Odoo 17: Hoy en Odoo 17 no hay ningún bloqueo de pago.
- Mientras tanto: Se aplica «registrar y marcar», sin bloquear la conciliación, hasta su respuesta.
- Bloquea: F8 · con Cristina

**F0-A28 · alta · antes del 06/11/2026** — ¿Qué cuentas bancarias de BOSS (banco y moneda) se llevan en Odoo 20 desde el arranque?

- Por qué: Sin diarios bancarios no se pueden registrar cobros y pagos, y los de dólares no tienen dónde ir (F4, F8, F9).
- Opciones: Todas las de hoy en Odoo 17 / Solo las que siguen activas (indicar) / Una en euros y una en dólares para empezar
- Hoy en Odoo 17: Hoy en Odoo 17 hay varios diarios bancarios en euros y en dólares, de varios bancos.
- Mientras tanto: Solo existe un diario bancario genérico sin cuenta; cobros y pagos en dólares no tienen diario. Pendiente de Ángel.
- Bloquea: F4, F8, F9

**F0-A29 · media · antes del 11/11/2026** — ¿Cómo entran los movimientos del banco en Odoo 20: conexión automática con los bancos o importación de extractos en fichero?

- Por qué: Decide cómo se concilian cobros y pagos (F9) y qué se activa en el arranque (F15); la conexión automática envía datos a un servicio externo.
- Opciones: Conexión automática desde el arranque / Ficheros de extracto / Ficheros al principio y conexión después
- Hoy en Odoo 17: Hoy en Odoo 17 hay conexión automática con tres bancos.
- Mientras tanto: Sin conexión ni importación: en las pruebas los movimientos se teclean.
- Bloquea: F9, F15 · con Belal

**F0-A30 · media · antes del 11/11/2026** — ¿Qué apuntes automáticos quiere al conciliar el banco (comisiones bancarias en euros y en dólares, retenciones…)?

- Por qué: Agiliza la conciliación de cobros y pagos (F9).
- Opciones: Los mismos que hoy en Odoo 17 / Solo comisiones bancarias / Ángel da la lista
- Hoy en Odoo 17: Hoy en Odoo 17 hay apuntes automáticos para comisiones bancarias en euros y en dólares y para una retención fiscal de un banco.
- Mientras tanto: Solo los dos estándar de Odoo (traspasos internos y comisiones bancarias); pendiente de Ángel.
- Bloquea: F9

**F0-A31 · media · antes del 11/11/2026** — ¿Los pagos a proveedores se harán con remesas generadas en Odoo 20 (fichero SEPA que se sube al banco) o desde la banca, conciliando después en Odoo?

- Por qué: Define el último paso del ciclo de proveedores (F8) y cómo se cierra el expediente.
- Opciones: Remesas SEPA desde Odoo 20 / Desde la banca, y en Odoo solo se concilia / Pagos uno a uno
- Hoy en Odoo 17: Hoy en Odoo 17 hay una marca de remesa en el contacto pero ningún módulo de remesas; probablemente se pagan desde la banca (sin comprobar).
- Mientras tanto: Solo pagos registrados a mano; el fichero de remesa se puede generar pero nunca se envía.
- Bloquea: F8

**F0-A32 · media · antes del 13/11/2026** — Con un agente que es a la vez cliente y proveedor, ¿se compensan sus facturas a cobrar y a pagar y se liquida solo la diferencia?

- Por qué: Afecta a la liquidación de los expedientes de agente (F13).
- Opciones: Sí, se compensan / No, cada una se cobra y se paga aparte / Solo con acuerdo escrito del agente
- Mientras tanto: Cada factura se cobra y se paga por separado; no hay compensación. Pendiente de Ángel.
- Bloquea: F13

### Etapa 10 Cierre operativo
**P01/P02-b (ya abierta) · media · antes del 11/11/2026** — Si un expediente queda por debajo del margen mínimo, ¿qué pasa y quién lo desbloquea?

- Por qué: Evita facturar y cerrar expedientes con margen bajo sin revisión (F10).
- Opciones: Solo un aviso / No se puede facturar ni cerrar hasta que lo desbloquee Cristina con motivo / No se puede facturar ni cerrar hasta que lo desbloquee Ángel con motivo / No se puede facturar ni cerrar hasta que lo desbloquee el comercial responsable
- Hoy en Odoo 17: Hoy en Odoo 17 un aviso de margen impide facturar y cerrar hasta que se desbloquea con motivo; el aviso llega a Cristina.
- Mientras tanto: Sin aviso ni bloqueo por margen; pendiente de Ángel y Cristina.
- Bloquea: F10 · con Cristina

### Etapa 11 Cierre financiero y de mes
**F0-A33 · alta · antes del 06/11/2026** — ¿Cómo y cuándo se bloquean los periodos contables en Odoo 20, y quién lo hace?

- Por qué: Protege los meses cerrados de cambios; el procedimiento se escribe con la base contable (F4) y se aplica en el cierre de mes (F10).
- Opciones: Cada mes, el día X del mes siguiente (indicar X y quién) / Cada trimestre, al presentar el IVA / Con el mismo ritmo que hoy en Odoo 17 (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el periodo y el IVA están bloqueados hasta el 30/09/2026 y el ejercicio hasta el 31/12/2025; las facturas de un mes se siguen emitiendo a primeros del siguiente antes de bloquear.
- Mientras tanto: Ninguna fecha de bloqueo en Odoo 20; pendiente de Ángel.
- Bloquea: F4, F10

**F0-A34 · media · antes del 11/11/2026** — ¿El cierre financiero de un expediente exige que todo esté cobrado y pagado?

- Por qué: Define cuándo el margen de un expediente es definitivo y ya no se toca (F10).
- Opciones: Sí, cobrado y pagado / Cobrado, sin exigir pagado / Solo facturado (cliente y proveedores)
- Hoy en Odoo 17: Hoy en Odoo 17 no hay cierre financiero; la lista de ayuda «Cierre automático» propone los expedientes entregados hace más de 14 días, con todo lo comprado y vendido facturado y beneficio positivo.
- Mientras tanto: El cierre financiero exige la lista «Pendiente» vacía y no mira cobros ni pagos; pendiente de Ángel.
- Bloquea: F10

**F0-A35 · media · antes del 11/11/2026** — ¿Quién puede reabrir un expediente cerrado financieramente?

- Por qué: Después del cierre financiero no se debe contabilizar nada sobre el expediente salvo que alguien autorizado lo reabra (F10).
- Opciones: Solo Ángel / Ángel y Cristina / Todo el equipo de contabilidad
- Hoy en Odoo 17: Hoy en Odoo 17 no hay cierre financiero; tras el cierre operativo solo unos pocos usuarios pueden modificar el expediente.
- Mientras tanto: Hoy solo pueden reabrir los usuarios con permiso de administrador de contabilidad (control técnico añadido el 28/10, no una decisión); pendiente de Ángel.
- Bloquea: F10

**F0-A36 · media · antes del 11/11/2026** — Al cierre de mes, ¿se periodifican los costes ya prestados sin factura del proveedor y la venta prestada sin facturar?

- Por qué: Pone el coste y la venta de cada expediente en el mes correcto (F10).
- Opciones: Sí, costes y ventas / Solo costes / No
- Hoy en Odoo 17: Hoy en Odoo 17 existe la cuenta 607800 «Compras pendientes de recibir factura de proveedor»; no se ha comprobado su uso mensual.
- Mientras tanto: No se periodifica nada; pendiente de Ángel.
- Bloquea: F10

**F0-A37 · media · antes del 11/11/2026** — ¿Quiere un aviso a fin de mes a cada operativo con sus expedientes sin facturar o sin cerrar, con copia a Ángel?

- Por qué: Permite comprobar que todo el mes está facturado y cerrado antes del cierre contable (F10).
- Opciones: Sí, mensual (indicar el día) / Sí, pero semanal / No
- Hoy en Odoo 17: Hoy en Odoo 17 un correo mensual «CIERRE MENSUAL» pide a cada responsable facturar y cerrar sus expedientes, con copia a Ángel.
- Mientras tanto: Solo la lista «Pendiente» de cada expediente; no hay aviso mensual. Durante las pruebas un aviso sería una tarea en Odoo, sin correo.
- Bloquea: F10 · con Cristina

**F0-A38 · media · antes del 11/11/2026** — Si llega la factura de un proveedor con fecha de un mes ya bloqueado, ¿con qué fecha contable se registra?

- Por qué: Decide cómo entran las facturas tardías sin tocar meses cerrados (F10).
- Opciones: En el primer día abierto, conservando la fecha de la factura / Se desbloquea el mes y se registra con su fecha / Con la fecha de recepción
- Hoy en Odoo 17: Hoy en Odoo 17 la fecha contable de la factura de proveedor es la fecha de la factura.
- Mientras tanto: Como no hay fechas de bloqueo, se registra con la fecha de la factura; pendiente de Ángel.
- Bloquea: F10

**F0-A80 · alta · antes del 11/11/2026** — Cuando un expediente está cerrado financieramente, ¿se impide contabilizar nuevas facturas o abonos sobre él hasta que un responsable de contabilidad lo reabra?

- Por qué: Antes del 28/10 se podía contabilizar sobre un expediente cerrado, lo que dejaba sin sentido el cierre y su reapertura reservada al responsable. Implementado el 28/10: se rechaza con el mensaje «reábralo primero».
- Opciones: Sí, bloquear (lo implementado) / Solo avisar, sin bloquear / Bloquear solo las facturas de cliente
- Hoy en Odoo 17: Hoy en Odoo 17 un expediente cerrado no admite cambios salvo para el grupo gestor.
- Mientras tanto: Se bloquea hasta su respuesta; se puede pasar a «solo avisar» sin perder datos.
- Bloquea: F10

**P38 (ya abierta) · media · antes del 11/11/2026** — ¿El margen del expediente debe descontar un coste interno por los servicios propios de BOSS (despacho, gestión, operativa)? Si es así, ¿con qué importe?

- Por qué: Decide si el margen definitivo es beneficio neto o margen tras costes externos (F10).
- Opciones: No: margen tras costes externos, como ahora / Sí: un importe por servicio (indicar) / Sí: un porcentaje (indicar)
- Mientras tanto: El margen es «tras costes externos» (no es beneficio neto), como propuesta aprobada por Belal el 23/10, pendiente de ratificación de Ángel.
- Bloquea: F10

**F0-A39 · media · antes del 13/11/2026** — ¿Se mantiene la comisión al recomendador de clientes? Si es así, ¿con qué regla?

- Por qué: Si existe, es un coste de esos expedientes que hoy no aparece en el coste ni en el margen de Odoo 20 (F13).
- Opciones: Sí, con la misma regla de Odoo 17 / Sí, con otra regla (indicar) / No
- Hoy en Odoo 17: Hoy en Odoo 17 un informe calcula para cada expediente cerrado de un cliente recomendado un 40 % de (beneficio − 95 €) y se registra como factura del recomendador en la cuenta 623008 Comisiones; es código, no una regla aprobada.
- Mientras tanto: No existe en Odoo 20: la comisión no entra en el coste ni en el margen; pendiente de Ángel.
- Bloquea: F13

**P45-c (ya abierta) · media · antes del 13/11/2026** — ¿Qué declaraciones de impuestos se preparan desde Odoo 20 a partir de enero de 2027 (IVA 303, intracomunitarias 349, resumen anual 390, operaciones con terceros 347)?

- Por qué: Decide qué informes fiscales hay que comprobar antes del arranque (F15).
- Opciones: Todas desde Odoo 20 / Solo algunas (indicar) / Las prepara la gestoría fuera de Odoo
- Hoy en Odoo 17: Hoy en Odoo 17 está instalado el módulo de informes fiscales españoles.
- Mientras tanto: Odoo 20 ya prepara borradores de 303, 347, 349 y 390 con su tarea automática; nada se presenta.
- Bloquea: F15

### Etapa P Proyecto y arranque
**F0-A40 · alta · antes del 04/11/2026** — ¿Con qué base de datos arranca BOSS el 1/1/2027: la base de Odoo 20 que se usa ahora para las pruebas, anulando antes todo lo de prueba, o una base nueva y limpia?

- Por qué: La base actual ya tiene facturas, abonos y pagos de prueba de 2026 y números gastados; si pasa a ser la base real, quedarían en los libros. Bloquea la instalación de SII o VERI*FACTU (F4), las pruebas que contabilizan (F1, F14) y el arranque (F15).
- Opciones: La base actual, anulando antes los registros de prueba por las vías de Odoo / Una base nueva y limpia
- Mientras tanto: La base actual sigue como base de trabajo y de pruebas; no se instala SII ni VERI*FACTU hasta que Ángel y Belal decidan.
- Bloquea: F1, F4, F14, F15 · con Belal

**F0-A41 · alta · antes del 04/11/2026** — Hasta el arranque, ¿se pueden contabilizar en la base actual de Odoo 20 facturas, abonos y pagos de prueba?

- Por qué: Hay dos instrucciones que se contradicen: la norma de trabajo del 27/10 lo permite y la prueba contable prevista para Ángel lo prohíbe antes del 1/1. Bloquea el modo que contabiliza de la prueba de punta a punta (F1) y la prueba contable (F14).
- Opciones: Sí, y se anulan antes del arranque / Sí, porque se arrancará en una base nueva / No: las comprobaciones que contabilizan se deshacen siempre al terminar
- Mientras tanto: Las comprobaciones automáticas se deshacen al terminar y los recorridos en pantalla se paran antes de contabilizar, hasta que Ángel y Belal decidan.
- Bloquea: F1, F14 · con Belal

**F0-A42 · alta · antes del 06/11/2026** — Desde el 1/1/2027, ¿toda la contabilidad nueva (facturas, cobros, pagos y bancos) se lleva solo en Odoo 20?

- Por qué: Si una parte siguiera en Odoo 17, cambiarían la base legal de la factura, los bancos y los cobros que se preparan ahora (F4, F9) y el arranque (F15). Hay dos supuestos distintos: el hito del 26/10 (Odoo 20 único sistema) y el criterio de migración heredado de Odoo 19 (facturas y contabilidad se quedan en Odoo 17 salvo que Ángel decida otra cosa).
- Opciones: Sí, todo en Odoo 20 / Facturas en Odoo 20 y contabilidad general en Odoo 17 unos meses / Otra (indicar)
- Mientras tanto: El plan supone Odoo 20 como único sistema desde el 1/1/2027 (hito aprobado por Belal el 26/10) y la contabilidad de 2026 y anteriores en Odoo 17 en solo lectura; queda pendiente de la confirmación de Ángel.
- Bloquea: F4, F9, F15

**F0-A43 · alta · antes del 20/11/2026** — Si hay que enviar facturas a la AEAT desde el arranque, ¿quién aporta el certificado electrónico de la empresa y en qué fecha se pasa del modo de pruebas al envío real?

- Por qué: La primera factura real lo necesitaría con certificado (F15). El certificado lo carga Ángel o el asesor directamente en Odoo; no se envía por correo ni por chat.
- Opciones: Ángel lo carga en Odoo antes del arranque y el envío real empieza el 1/1/2027 / Lo gestiona el asesor fiscal (indicar fecha) / No hace falta todavía, porque no hay envío obligatorio desde el arranque
- Mientras tanto: Si se instala SII o VERI*FACTU, funciona en modo de pruebas, sin certificado y sin envío.
- Bloquea: F15

**F0-A44 · media · antes del 20/11/2026** — ¿Cómo se cargan los saldos de apertura en Odoo 20 el 1/1/2027?

- Por qué: Sin saldos de apertura, el balance y los bancos de Odoo 20 no cuadran con Odoo 17 (F15).
- Opciones: Asiento de apertura con el balance de cierre de 2026, provisional y ajustado tras cerrar 2026 / Solo saldos de bancos, clientes y proveedores / Otra forma (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 existe un diario de apertura.
- Mientras tanto: Odoo 20 no tiene asiento de apertura; no se carga nada hasta que Ángel decida.
- Bloquea: F15

**F0-A45 · media · antes del 20/11/2026** — Las facturas de 2026 pendientes de cobro o de pago el 1/1/2027, ¿se cobran y se pagan en Odoo 20 o en Odoo 17?

- Por qué: Decide si hay que migrarlas y cómo se cierran los expedientes que tengan facturas en los dos sistemas (F15).
- Opciones: Se migran una a una a Odoo 20 / Se cobran y se pagan en Odoo 17 hasta liquidarlas / Saldo por cliente y proveedor en Odoo 20
- Mientras tanto: No se migra ninguna factura pendiente; pendiente de Ángel.
- Bloquea: F15

**F0-A46 · media · antes del 20/11/2026** — Las facturas de clientes y de proveedores con fecha de diciembre de 2026 que se emitan o se reciban en enero de 2027, ¿se registran en Odoo 17 o en Odoo 20?

- Por qué: Evita números duplicados y facturas de 2026 repartidas entre los dos sistemas en el arranque (F15).
- Opciones: En Odoo 17 hasta cerrar 2026 / En Odoo 20 desde el 1/1, con fecha de diciembre / Las de clientes en Odoo 17 y las de proveedores en Odoo 20
- Hoy en Odoo 17: Hoy en Odoo 17 las facturas de un mes se siguen emitiendo a primeros del mes siguiente antes de bloquear el periodo (por ejemplo, facturas de septiembre numeradas en octubre).
- Mientras tanto: Sin regla; pendiente de Ángel.
- Bloquea: F15

## Cristina
### Etapa 0 Partes y datos maestros
**F0-C01 · alta · antes del 04/11/2026** — ¿Qué personas de BOSS necesitan usuario en Odoo 20 para las pruebas y el arranque, y qué papel tiene cada una (comercial, operativo, compras o aprobador de tarifas)? Los usuarios de contabilidad los indica Ángel.

- Por qué: Sin su propio usuario, usted no puede aprobar tarifas y operaciones no puede probar el expediente. Hoy solo existen dos usuarios internos.
- Opciones: Envío la lista de personas con su papel / Primero yo y un operativo para las pruebas; el resto antes del 1/12 / Otra (indicar)
- Mientras tanto: Solo hay dos usuarios internos (Belal y Ángel). De las 22 tarifas aprobadas, 21 las aprobó Belal por delegación y 1 Ángel, solo para pruebas. Nada se aprueba en su nombre.
- Bloquea: F2, F3, F14

**F0-C02 · alta · antes del 04/11/2026** — Al traer los contactos de Odoo 17, ¿qué papel tiene en Odoo 20 cada tipo de contacto (Cliente, Agente, Proveedor, Cliente + Proveedor, expedidor o destinatario español o extranjero, Acreedor) y cada marca (agente, naviera, agente de aduanas, transportista terrestre, aerolínea)?

- Por qué: Sin esta correspondencia no se pueden elegir bien las partes del expediente: ordenante, expedidor, destinatario, agente, transportista y agente de aduanas. Y sin contactos migrados no se puede abrir ningún expediente real. Qué contactos se migran (tipos y antigüedad) lo decide Belal aparte.
- Opciones: Uno a uno, igual que en Odoo 17 (Belal prepara la tabla y yo la reviso) / Con cambios (indicar cuáles)
- Hoy en Odoo 17: Hoy en Odoo 17 cada contacto tiene un tipo, varias marcas de papel, un código interno y un KAM. Entre ellos hay contactos que en realidad son lugares (códigos postales, ciudades).
- Mientras tanto: Solo hay 2 clientes y 8 proveedores reales. Hasta su respuesta, los papeles de los contactos migrados quedan como «pendiente de decisión», sin asignar ninguno por suposición.
- Bloquea: F2

**R-A3 (ya abierta) · alta · antes del 04/11/2026** — En un expediente de agente, ¿el ordenante tiene que ser un contacto de tipo Agente (y en uno de cliente de BOSS, de tipo Cliente), como comprueba Odoo 17?

- Por qué: Decide si el sistema rechaza o solo avisa cuando el ordenante no tiene el tipo esperado. Afecta a la migración de contactos y a las ofertas de agente.
- Opciones: Sí: comprobar y no dejar seguir / Solo avisar / No comprobar
- Hoy en Odoo 17: Hoy en Odoo 17 el expediente de agente guarda el ordenante, el agente y a quién se factura, y comprueba que el ordenante sea de tipo Agente.
- Mientras tanto: Se guarda si el negocio es de BOSS o del agente, y el código de tráfico. El tipo de contacto del ordenante no se comprueba («pendiente de decisión»).
- Bloquea: F2, F3

**P20 (ya abierta) · media · antes del 11/11/2026** — ¿El operativo debe ver los precios de venta? ¿Y el comercial debe ver el coste de proveedor y el margen?

- Por qué: Fija los permisos de las pantallas de oferta y de expediente. Si se decide tarde, habrá que cambiar permisos con los usuarios ya trabajando.
- Opciones: Todos los usuarios de ventas ven venta, coste y margen (como ahora) / El comercial ve la venta y el margen, pero no el coste de proveedor / El operativo no ve la venta / Otra (indicar)
- Mientras tanto: Se aplica el estándar de Odoo por rol: los usuarios de ventas ven la venta y el coste de la oferta, compras ve el lado proveedor, y el gestor comercial y contabilidad lo ven todo.
- Bloquea: F6

**P35 (ya abierta) · media · antes del 11/11/2026** — Dentro del expediente, ¿quién puede ver las facturas de proveedor y el coste real?

- Por qué: Al reunir documentos y facturas en el expediente hay que saber quién ve cada cosa. Si se hace mal, un comercial vería los costes de proveedor.
- Opciones: Solo compras, contabilidad y el gestor comercial (como ahora) / También el operativo del expediente / También el comercial del expediente / Otra (indicar)
- Mientras tanto: Las facturas de proveedor y el coste real solo los ven compras, contabilidad y el gestor comercial.
- Bloquea: F6

**P35-B (ya abierta) · media · antes del 11/11/2026** — ¿Cada comercial debe ver solo sus propios clientes, ofertas y expedientes, o los de todo BOSS?

- Por qué: Es el requisito escrito de su documento «Nuevo Odoo» (hoja CRM) que acompaña a la pregunta P35, y no está confirmado. Cambia los permisos de todo el equipo comercial.
- Opciones: Solo los suyos / Los suyos y los de su equipo / Todos
- Mientras tanto: Cada usuario ve lo que le da su permiso estándar de Ventas. No hay ninguna regla propia de BOSS por comercial («pendiente de decisión»).
- Bloquea: F6

**F0-C04 · media · antes del 13/11/2026** — ¿Es correcta la lista de qué handler atiende a cada aerolínea en cada aeropuerto? Viene de Odoo 17 y tiene 47 combinaciones: Madrid 30, Barcelona 13, Málaga 2, Valencia 1 y Bilbao 1.

- Por qué: La oferta y el expediente aéreo proponen el handler a partir de esta lista, así que conviene validarla antes de las pruebas de importación aérea.
- Opciones: Correcta / Correcta con cambios (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 esta relación está en una tabla de configuración de handling (48 filas, una de ellas archivada).
- Mientras tanto: Odoo 20 propone el handler según esa lista sin validar; el operativo puede cambiarlo.
- Bloquea: F11

**F0-C05 · media · antes del 13/11/2026** — Belal preparará la correspondencia entre los conceptos de Odoo 17 y los 77 servicios de Odoo 20. ¿La revisa y valida usted, o la persona que designe?

- Por qué: Sin esa correspondencia no se pueden migrar los servicios pendientes de los expedientes abiertos ni comprobar las sumas por concepto contra Odoo 17.
- Opciones: La reviso yo cuando esté preparada / La revisa otra persona (indicar papel)
- Hoy en Odoo 17: Hoy en Odoo 17 cada línea de previsión lleva un concepto (por ejemplo flete, THC o transporte).
- Mientras tanto: No hay correspondencia validada y no se migra ningún servicio pendiente.
- Bloquea: F15

### Etapa 1 Oferta
**F0-C06 · alta · antes del 06/11/2026** — ¿Quién reúne los documentos de tarifa que faltan, y para qué fecha? Faltan: segundo handler aéreo, Iberia, demoras de ONE, Maersk, ZIM y OOCL, gastos locales de Hapag-Lloyd, CFS de grupaje, despacho de exportación y despacho aéreo, acuerdos de profit share, inspecciones, CES, transporte de contenedor y recargo de combustible.

- Por qué: Faltan documentos de 39 servicios. Sin ellos, cada oferta real necesita teclear el coste a mano.
- Opciones: Lo coordino yo con operaciones para el (fecha) / Lo hace (persona o papel) para el (fecha)
- Mientras tanto: Esos servicios salen como «Sin precio de proveedor»: se teclea el coste con motivo o se añade el precio desde la oferta.
- Bloquea: F3, F11, F12

**F0-C07 · alta · antes del 06/11/2026** — De esos servicios, ¿cuáles no tendrán nunca tarifa fija y se cotizarán siempre caso por caso con el proveedor (por ejemplo, el camión o el arrastre)?

- Por qué: Así se marcan como «coste a petición», en lugar de quedarse esperando un documento que no va a llegar.
- Opciones: Indico la lista / Ninguno: todos tendrán tarifa
- Mientras tanto: Si hay un proveedor elegido sin precio, la línea queda como «Coste a petición». Los demás costes desconocidos necesitan el motivo de un responsable.
- Bloquea: F3

**F0-C08 · alta · antes del 06/11/2026** — ¿Los servicios de una plantilla cambian según el Incoterm (por ejemplo, EXW añade la recogida y los gastos en origen, y DAP o DDP quitan la entrega), o los ajusta el operativo a mano?

- Por qué: Decide si hace falta una plantilla por Incoterm o basta con una por caso.
- Opciones: Sí: indico qué cambia con cada Incoterm / No: una plantilla por caso y el operativo ajusta
- Hoy en Odoo 17: Hoy, según su hoja de procesos, EXW, FOB y FCA se cotizan; DAP y DDP abren expediente con los documentos; y CFR y CIF no llevan oferta.
- Mientras tanto: Hay una plantilla por caso y el Incoterm de la plantilla se copia a la oferta.
- Bloquea: F3

**F0-C09 · alta · antes del 06/11/2026** — ¿Qué servicios lleva «siempre» y cuáles «a veces» una oferta de exportación marítima FCL, de grupaje (LCL) de importación y de exportación, y de transporte terrestre?

- Por qué: Sin estas plantillas no hay servicios propuestos para esos casos, que nunca se han probado en Odoo 20.
- Opciones: Exportación FCL (propuesta para revisar): siempre recogida, THC, BL, T3, despacho de exportación, honorarios, flete y los gastos de naviera que van con el THC; a veces CES, demoras, ocupación, VGM, AMS/ENS, EUR1, fumigación, seguro y quebranto / Indico la lista de cada caso / Indico primero la de exportación FCL; las de grupaje y terrestre más adelante (indicar fecha)
- Mientras tanto: No hay plantilla de exportación marítima, grupaje ni terrestre: los servicios se añaden a mano.
- Bloquea: F3, F12

**F0-C11 · media · antes del 06/11/2026** — El documento de ocupación de MSC no tiene columna para el 40' HC. ¿Se usa la del 40' DV?

- Por qué: Hoy un 40' HC no tiene precio de ocupación.
- Opciones: Sí, la del 40' DV / No: pido el precio a MSC
- Mientras tanto: El 40' HC sale como «Sin precio de proveedor» en la ocupación.
- Bloquea: F3 (solo la ocupación del 40' HC de MSC)

**F0-C12 · media · antes del 06/11/2026** — En las entregas en la provincia de Madrid, IRENEO cobra por zona MAD o MAD-EXT (según el código postal y un radio de 30 km). ¿Puede conseguir de IRENEO, o confirmar usted, la zona de cada población?

- Por qué: Sin esas zonas, las entregas en Madrid no tienen precio de transporte.
- Opciones: Pido la lista a IRENEO / La confirmo yo (envío la lista)
- Mientras tanto: Las entregas en la provincia de Madrid salen como «Sin precio de proveedor».
- Bloquea: F3 (solo entregas en Madrid), F12

**F0-C13 · media · antes del 06/11/2026** — En el almacén G-5 de IRENEO, ¿los 5 días libres se descuentan siempre, o al superarlos se cobra desde el día 1?

- Por qué: Con 10 días de estancia, una lectura da el doble que la otra.
- Opciones: Se descuentan / Al superarlos, se cobra desde el día 1 / Lo confirmo con IRENEO
- Mientras tanto: El precio está marcado como «A consultar» (cargado como «descontados»), así que la oferta sale «A consultar».
- Bloquea: F3 (solo el almacén G-5), F11

**F0-C14 · media · antes del 06/11/2026** — Las facturas reales de MSC de septiembre y octubre cobran menos THC de importación por contenedor que su tarifa vigente. ¿Hay un acuerdo o una edición distinta con MSC?

- Por qué: El coste previsto sale algo mayor que lo que MSC factura, y eso desvirtúa el margen.
- Opciones: Hay un acuerdo: envío el documento / Vale la tarifa publicada / Lo pregunto a MSC
- Mientras tanto: Vale el documento de la tarifa: el coste previsto de THC es algo mayor que lo facturado.
- Bloquea: F3 (solo el THC de importación de MSC)

**F0-C15 · media · antes del 06/11/2026** — Las condiciones de demoras y ocupaciones de la licitación de Leroy Merlin terminaron el 31/05/2026. ¿Hay condiciones para 2026-27?

- Por qué: Sin ellas, los envíos de este cliente usan las tarifas públicas de cada naviera.
- Opciones: Sí: envío el documento / No: se usan las tarifas públicas
- Mientras tanto: Desde junio de 2026 se usan las tarifas públicas de la naviera.
- Bloquea: F3 (solo envíos de Leroy Merlin)

**F0-C16 · media · antes del 06/11/2026** — El recargo FuelEU de la naviera, ¿se repercute al cliente o lo asume BOSS?

- Por qué: En una factura real reciente no se cobró al cliente. Hace falta una regla comercial.
- Opciones: Se repercute siempre / No se repercute / Depende del cliente (indicar)
- Hoy en Odoo 17: Hoy, en una factura real de octubre de 2026, el FuelEU no se cobró al cliente.
- Mientras tanto: En la oferta de prueba va «Sin cargo» y su coste cuenta en el margen. Se decide a mano en cada oferta.
- Bloquea: F3 (solo ofertas con FuelEU)

**F0-C17 · media · antes del 06/11/2026** — En el despacho de importación hay dos agentes de aduanas con precio. ¿La oferta propone uno por defecto, o el operativo elige siempre?

- Por qué: El 28/09 usted indicó que elige el operativo; en la revisión con Ángel se planteó proponer uno por defecto.
- Opciones: El operativo elige siempre / Proponer uno por defecto (indicar cuál y en qué casos)
- Mientras tanto: La línea pide elegir uno de los dos agentes con precio.
- Bloquea: F3 (solo ratificación: hoy elige el operativo) · con Ángel

**F0-C18 · media · antes del 06/11/2026** — Al recotizar una oferta ya aceptada, ¿la «venta aceptada» y el «margen en la aceptación» del expediente deben conservar los valores originales, o mostrar los recotizados?

- Por qué: Cambia las cifras «en la aceptación» del resumen del expediente; en una prueba, la venta y el margen bajaron después de recotizar.
- Opciones: Conservar los originales y mostrar los nuevos aparte / Mostrar los recotizados (como ahora)
- Mientras tanto: Se muestran los recotizados; los originales quedan en el historial de precios.
- Bloquea: F3 (no bloquea: solo cambia qué cifra se muestra)

**F0-C19 · media · antes del 06/11/2026** — En «Recotizar», ¿la casilla «Recalcular el coste» debe venir marcada en todas las líneas, o desmarcada?

- Por qué: Hoy, para cambiar un solo precio, hay que desmarcar las líneas una a una.
- Opciones: Marcada (como ahora) / Desmarcada
- Mientras tanto: Viene marcada en todas las líneas.
- Bloquea: F3 (no bloquea: solo cambia un valor por defecto)

**F0-C20 · baja · antes del 06/11/2026** — ¿Necesita en Odoo 20 la oferta en formato corto que usan hoy, o bastan la oferta normal y la oferta de tarifas por unidad (sin totales)?

- Por qué: Si la necesita, entra en la fase de oferta; si no, queda fuera del plan.
- Opciones: Bastan las de Odoo 20 / Necesito el formato corto (envío un ejemplo)
- Hoy en Odoo 17: Hoy en Odoo 17 las ofertas spot se imprimen en un formato corto.
- Mientras tanto: Queda fuera del plan; se usan la oferta normal y la oferta de tarifas.
- Bloquea: F3 (opcional)

**M2-A (ya abierta) · alta · antes del 06/11/2026** — En sus Excel de venta, ¿qué servicios tienen un precio de venta fijo (el mismo aunque cambie la naviera) y cuáles varían con el coste? ¿Puede enviar esos Excel para cargarlos?

- Por qué: Sin esos precios, la venta sale de «coste + 20 %» o se teclea, y las pruebas no tienen precios reales que se puedan repetir.
- Opciones: Envío los Excel y marco fijo o variable en cada servicio / Todos tienen precio fijo / Todos varían con el coste
- Hoy en Odoo 17: Hoy se cotiza con sus Excel de venta, fuera de Odoo 17.
- Mientras tanto: La venta sale de «coste + 20 %» (ajuste puesto por indicación de Belal, sin su aprobación) o se teclea. No hay ningún precio fijo de venta cargado.
- Bloquea: F3

**M2-B (ya abierta) · media · antes del 06/11/2026** — Para aprobar una tarifa, ¿es obligatorio adjuntar el documento del proveedor?

- Por qué: Hoy es obligatorio por defecto. Si decide otra cosa, solo cambia un ajuste.
- Opciones: Sí, siempre (como ahora) / No es obligatorio / Obligatorio salvo excepciones (indicar)
- Mientras tanto: El ajuste «Documento del proveedor obligatorio» está activo, pendiente de su ratificación.
- Bloquea: F3 (solo ratificación: ya funciona con la regla aplicada)

**M2-E (ya abierta) · media · antes del 06/11/2026** — ¿Hay que limitar qué proveedores pueden prestar cada servicio (por ejemplo, qué camioneros, o una naviera que también hace el transporte), o vale cualquier proveedor con un aviso si no tiene tarifa?

- Por qué: Una lista por servicio evita elegir proveedores equivocados, pero alguien tiene que mantenerla.
- Opciones: Cualquier proveedor, con aviso (como ahora) / Lista de proveedores por servicio (indicar)
- Mientras tanto: Se acepta cualquier proveedor, con un aviso si no tiene tarifa del servicio.
- Bloquea: F3 (solo ratificación: ya funciona con la regla aplicada) · con Ángel

**M2-H (ya abierta) · media · antes del 06/11/2026** — Si se elige un proveedor que no tiene precio para ese servicio (por ejemplo, el camión caso por caso), ¿la oferta se puede aceptar como «coste a petición» sin autorización de un responsable, mientras los demás costes desconocidos sí la necesitan?

- Por qué: Funciona así desde la revisión del 28/10. Falta su confirmación.
- Opciones: Sí, como ahora / También necesita la autorización de un responsable / Otra (indicar)
- Mientras tanto: Aplicado así, pendiente de su ratificación. El expediente muestra el coste como desconocido hasta que se teclea.
- Bloquea: F3 (solo ratificación: ya funciona con la regla aplicada)

**P01 (ya abierta) · alta · antes del 06/11/2026** — ¿Qué clientes tienen precios pactados propios? Sus listas se cargarían antes de las pruebas con clientes reales.

- Por qué: La oferta real y las pruebas comerciales usan la lista de cada cliente. Sin esas listas, todo sale de la venta general.
- Opciones: Envío la lista de clientes con sus precios / Ninguno: todos con la venta general
- Mientras tanto: La venta sale de la lista general o se teclea. Solo un cliente tiene lista propia, creada en pruebas.
- Bloquea: F3, F14

**P09 (ya abierta) · alta · antes del 06/11/2026** — Sobre la detención (DET): ¿lleva código propio cuando la naviera la factura aparte (como MSC), y va dentro de la demora (DEM) cuando la naviera cobra las dos juntas (como Hapag-Lloyd)?

- Por qué: Cambia cómo se cotiza y cómo se casa la factura de la naviera.
- Opciones: Sí, así / Siempre con código propio / Siempre dentro de DEM
- Hoy en Odoo 17: Hoy en Odoo 17 no existe el concepto DET.
- Mientras tanto: DET está configurado como código propio, por contenedor y día. Es la propuesta del 07/10, aplicada por decisión de Belal y pendiente de su ratificación.
- Bloquea: F3, F12

**P10 (ya abierta) · alta · antes del 06/11/2026** — Usted indicó que la tasa energética (ETX) solo se aplica en importación, que se compra al handler por AWB máster y que se vende una vez por expediente. Para dejarla lista falta confirmar: ¿es solo de importación aérea, el «Recargo de mantenimiento del servicio» de WFS (punto 49 de su tarifa) es ese coste, y la cobran solo WFS, Iberia y Swissport?

- Por qué: El punto 49 de WFS se asignó a ETX sin su confirmación. Si no es ese coste, las ofertas de importación aérea con WFS llevarían un importe que no corresponde.
- Opciones: Sí a las tres cosas / El punto 49 de WFS no es ETX (indicar qué es) / Otro handler también la cobra, o también se aplica fuera del aéreo (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 existe «ETX – Energy tax». En el programa de previsiones la cobran WFS, Iberia y Swissport; DHL, IAS y ACL no.
- Mientras tanto: ETX está configurada así para pruebas, con el punto 49 de WFS como coste y pendiente de su confirmación. Como la tarifa de WFS espera aprobación, la línea sale «pendiente de aprobación».
- Bloquea: F3, F11

**P13 (ya abierta) · alta · antes del 06/11/2026** — Para la caución (CAU) y el seguro (SEG), ¿qué porcentajes, tasas por país y mínimos se aplican, y de qué documento salen?

- Por qué: Sin valores aprobados, la oferta no calcula ni la CAU ni el SEG.
- Opciones: Envío los valores con su documento / Se cotizan siempre caso por caso
- Mientras tanto: El método por porcentaje existe, pero no hay valores aprobados: CAU y SEG no tienen coste calculado.
- Bloquea: F3 · con Ángel

**P16 (ya abierta) · alta · antes del 06/11/2026** — De los servicios sin definir (VET, GT3, DES, VAC, POS, IMO, DVD, GAV y DUM), ¿cuáles se usan de verdad, con su unidad de cobro, proveedor y documento, y cuáles se retiran?

- Por qué: Mientras no se definan, estos servicios no se pueden cotizar ni migrar sin coste manual.
- Opciones: Para cada uno: se usa (unidad, proveedor y documento) o se retira / VET como inspección veterinaria por documento, igual que SAN (propuesta del 07/10, sin confirmar)
- Hoy en Odoo 17: Hoy en Odoo 17 VET existe como «Veterinaria».
- Mientras tanto: GT3, DES, VAC, POS, IMO, DVD, GAV y DUM salen como «Pendiente de decisión»; se puede poner un coste manual. VET ya se cotiza con coste manual, por documento como SAN: es la propuesta del 07/10, aplicada para pruebas y pendiente de su confirmación.
- Bloquea: F3

**P19 (ya abierta) · alta · antes del 06/11/2026** — Hay 22 tarifas de proveedor aprobadas solo para pruebas (21 por delegación de Belal y 1 por Ángel), y las de WFS y el recargo FuelEU de MSC esperan aprobación. ¿Las revisa y aprueba usted con su usuario, o designa a otra persona?

- Por qué: La oferta real debe salir de tarifas aprobadas por usted. Hoy solo 13 de los 52 servicios con tarifa tienen un precio aprobado, y solo para pruebas.
- Opciones: Las reviso y apruebo yo / Las apruebo yo y designo a otra persona (indicar papel) para cuando no esté / Designo a otra persona (indicar papel) y yo reviso después
- Mientras tanto: Las tarifas están aprobadas por delegación solo para pruebas. WFS y FuelEU salen como «pendiente de aprobación».
- Bloquea: F3, F11

**P24 (ya abierta) · alta · antes del 06/11/2026** — ¿Es correcta esta lista de países de «Lejano Oriente» para el recargo FuelEU de MSC: China, Hong Kong, Taiwán, Japón, Corea del Sur, Vietnam, Tailandia, Malasia, Singapur, Indonesia, Filipinas y Camboya?

- Por qué: Sin la lista confirmada, una importación de MSC desde fuera de China no tiene FuelEU calculado.
- Opciones: Correcta / Con cambios (indicar)
- Mientras tanto: La lista es la propuesta del 07/10. Una importación MSC desde Vietnam o Corea sale como «Precio pendiente de aprobación».
- Bloquea: F3

**P24-B (ya abierta) · alta · antes del 06/11/2026** — ¿Qué tráficos se consideran «short sea», con un THC distinto del general?

- Por qué: Forma parte de la pregunta P24, junto con la lista de Lejano Oriente, y completa la lectura de los gastos portuarios.
- Opciones: Indico los tráficos o países / No hay THC distinto para short sea
- Mientras tanto: No hay lista de tráficos short sea («pendiente de decisión»).
- Bloquea: F3

**P28 (ya abierta) · alta · antes del 06/11/2026** — En 2026, ¿el handling de IRENEO (manipulación y rayos X en aéreo) sigue con los precios de 2025? Para el transporte ya está la carta de IRENEO con la subida desde el 15/07/2026.

- Por qué: La carta solo cubre el transporte. Sin confirmar el handling, esos precios no se pueden aprobar para 2026.
- Opciones: Sí, con los precios de 2025 / No: pido la tarifa 2026 a IRENEO
- Mientras tanto: La tarifa IRENEO 2026 está aprobada solo para pruebas, por delegación de Belal (transporte con la subida de la carta desde el 15/07). El handling sigue con los precios de 2025, sin confirmar.
- Bloquea: F3, F12

**P29 (ya abierta) · alta · antes del 06/11/2026** — Tramos de WFS «hasta 7 días / más de 7»: si la estancia pasa de 7 días, ¿el precio alto se aplica solo a los días siguientes o a toda la estancia?

- Por qué: El documento no lo dice y, en estancias largas, la diferencia es grande.
- Opciones: Solo a los días siguientes (como ahora) / A toda la estancia / Lo confirmo con una factura real de más de 7 días
- Mientras tanto: El precio alto se aplica solo a los días siguientes (propuesta aprobada por Belal el 23/10, pendiente de su ratificación).
- Bloquea: F3, F11

**P34 (ya abierta) · baja · antes del 06/11/2026** — ¿Hace falta para el arranque el precio cerrado para varios envíos (tipo licitación de Leroy)? Si hace falta, ¿para qué clientes, con qué duración y con qué cantidades máximas?

- Por qué: Hoy cada envío de un acuerdo se cotiza y se acepta por separado. Construirlo antes del 1/1 quitaría tiempo a otras fases.
- Opciones: Después del arranque / Para el 1/1 (indicar clientes, duración y cantidades)
- Hoy en Odoo 17: Hoy en Odoo 17 existe un acuerdo por cliente, tráfico, rutas e Incoterm, con ofertas y validez encadenadas.
- Mientras tanto: Cada envío se cotiza por separado. Una oferta aceptada puede repartirse entre varios expedientes.
- Bloquea: F3 (opcional)

**P40 (ya abierta) · alta · antes del 06/11/2026** — Almacenaje de WFS «por 24 horas»: ¿se cuentan periodos de 24 h desde la llegada, o días naturales?

- Por qué: Si la salida es a una hora anterior a la de llegada, las dos lecturas dan importes distintos (de lunes a las 10:00 a viernes a las 10:00 son 4 periodos o 5 días). Las fuentes se contradicen y la pregunta del 25/09 quedó sin respuesta.
- Opciones: Periodos de 24 h desde la llegada (como ahora) / Días naturales / Lo confirmo con una factura real de WFS
- Mientras tanto: Se aplican periodos de 24 h (propuesta aprobada por Belal el 23/10, pendiente de su ratificación). La tarifa de WFS sigue esperando aprobación.
- Bloquea: F3, F11

**P41 (ya abierta) · alta · antes del 06/11/2026** — Almacenaje de WFS «por 100 kg»: ¿se cobra por cada 100 kg o fracción, o en proporción al peso?

- Por qué: Usted habló el 08/09 de «fracción de 100 kg» y la edición de WFS de 2025 también lo decía, pero la de 2026 no lo dice.
- Opciones: Por 100 kg o fracción (como ahora) / En proporción al peso
- Mientras tanto: Se aplica «o fracción» (propuesta aprobada por Belal el 23/10, pendiente de su ratificación).
- Bloquea: F3, F11

**P42 (ya abierta) · alta · antes del 06/11/2026** — El mínimo de almacenaje de WFS (puntos 1 a 3 del documento), ¿se aplica por estancia de la AWB o por día?

- Por qué: En esos puntos el documento no indica la unidad del mínimo, y eso cambia el importe de los envíos pequeños.
- Opciones: Por estancia de la AWB (como ahora) / Por día
- Mientras tanto: Se aplica el mínimo por estancia (propuesta aprobada por Belal el 23/10, pendiente de su ratificación).
- Bloquea: F3, F11

**R-S1 (ya abierta) · alta · antes del 06/11/2026** — ¿Son correctas las listas de servicios «siempre» y «a veces» propuestas para las tres plantillas actuales: importación aérea FOB, importación marítima FCL FOB y exportación aérea?

- Por qué: La plantilla rellena el caso y propone los servicios de cada oferta. Hoy estas listas son una propuesta sin validar.
- Opciones: Correctas / Con cambios (indicar servicio por servicio)
- Hoy en Odoo 17: Hoy en Odoo 17 la oferta se apoya en una plantilla de gastos locales y en sus Excel de venta.
- Mientras tanto: Las tres plantillas están cargadas como propuesta. Al aplicar una plantilla solo se añaden los servicios que faltan, con un aviso.
- Bloquea: F3

**R2-A1 (ya abierta) · media · antes del 06/11/2026** — Cuando se teclea el coste de un flete para una oferta, ¿debe guardarse también como precio reutilizable para esa ruta y semana?

- Por qué: Decide si los fletes tecleados alimentan las tarifas o se quedan solo en esa oferta.
- Opciones: Siempre como precio reutilizable / Solo cuando el comercial lo elige (como ahora) / Nunca: solo en la línea
- Mientras tanto: Hay dos caminos: un coste manual que se queda solo en la línea, o un precio semanal con ruta y validez creado desde la oferta, que se guarda como versión de la tarifa.
- Bloquea: F3 (solo ratificación: ya funciona con la regla aplicada) · con Ángel

**R2-A2 (ya abierta) · media · antes del 06/11/2026** — El flete semanal que se teclea desde una oferta, ¿queda aprobado al introducirlo, o tiene que esperar a que lo apruebe un aprobador de tarifas?

- Por qué: En la segunda reunión Ángel pidió que no tuviera que esperar aprobación (pensando en los casos de madrugada). Falta su ratificación como responsable de tarifas.
- Opciones: Aprobado al introducirlo, con el autor registrado (como ahora) / Debe esperar a un aprobador / Aprobado al introducirlo solo para algunos usuarios (indicar)
- Mientras tanto: El ajuste «Fletes aprobados al introducirlos» está activo, solo para fletes tecleados desde una oferta.
- Bloquea: F3 (solo ratificación: ya funciona con la regla aplicada) · con Ángel

**R2-A3 (ya abierta) · alta · antes del 06/11/2026** — En los servicios cuya venta varía con el coste, ¿vale «coste + 20 %» como venta propuesta por defecto (siempre editable), o qué porcentaje prefiere?

- Por qué: El 20 % lo indicó Belal después de hablar con Ángel. Falta su confirmación como responsable de precios.
- Opciones: +20 % para todos / Otro porcentaje (indicar) / Un porcentaje distinto por grupo de servicio (indicar) / Sin venta por defecto: siempre pactada o tecleada
- Mientras tanto: Está activo «coste + 20 %» en la tarifa general; el precio tecleado o el pactado tienen prioridad. Pendiente de su ratificación.
- Bloquea: F3

**R2-A6 (ya abierta) · media · antes del 06/11/2026** — ¿Se usa el transporte terrestre convencional, el que se cobra por peso tasable, en envíos de contenedor completo (FCL)? Si se usa, el volumen tendría que verse también en las ofertas FCL.

- Por qué: Ese transporte se cobra por peso tasable, que necesita el volumen, y hoy en las ofertas FCL el volumen no se muestra.
- Opciones: No: en FCL siempre se usa el transporte de contenedor / Sí, a veces: mostrar el volumen también en FCL
- Mientras tanto: En las ofertas FCL el volumen sigue oculto («pendiente de decisión»).
- Bloquea: F3 (solo FCL con transporte convencional)

**P21 (ya abierta) · baja · antes del 11/11/2026** — Además de la oferta por envío y de la oferta de tarifas por unidad, ¿hacen falta ofertas de tarifa por ruta válidas para varios envíos (por ejemplo, un FCL mensual Shanghái–Valencia)?

- Por qué: Cambia cómo se organiza la oferta y cómo se acepta.
- Opciones: No: bastan las actuales / Sí (indicar el caso)
- Mientras tanto: Una oferta corresponde a un envío. Existe la oferta de tarifas por unidad (20', 40', 40' HC), sin total.
- Bloquea: F6

**P22 (ya abierta) · baja · antes del 11/11/2026** — Para ofrecer alternativas (por ejemplo, dos navieras), ¿se hacen varias ofertas dentro de la misma oportunidad, o una sola oferta con secciones opcionales?

- Por qué: Decide cómo ve el cliente las alternativas.
- Opciones: Varias ofertas en la misma oportunidad (como ahora) / Una oferta con secciones opcionales
- Mientras tanto: Varias ofertas dentro de la misma oportunidad (estándar de Odoo).
- Bloquea: F6

**P23 (ya abierta) · baja · antes del 11/11/2026** — ¿Qué validez lleva una oferta por defecto? ¿Y se puede aceptar una oferta ya caducada?

- Por qué: Fija la fecha de fin de cada oferta y si se puede aceptar una ya vencida.
- Opciones: 15 días; una oferta caducada no se acepta sin recotizarla / 30 días; una oferta caducada no se acepta sin recotizarla / Otra (indicar los días y qué pasa al caducar)
- Hoy en Odoo 17: Hoy en Odoo 17 una tarea pasa a perdidas las ofertas fuera de validez, y no se abre expediente de una oferta vencida hace más de 15 días.
- Mientras tanto: Validez estándar de Odoo, sin ninguna regla propia de BOSS («pendiente de decisión»).
- Bloquea: F6

**P26 (ya abierta) · baja · antes del 11/11/2026** — ¿Se fusionan los códigos que se propuso juntar (CSM, CSA y CST; AMS y ENS; inspecciones), o se mantienen separados?

- Por qué: Cambia el catálogo de servicios y la correspondencia para la migración.
- Opciones: Se mantienen separados (como ahora) / Se fusionan (indicar cuáles)
- Mientras tanto: Se mantienen los códigos originales.
- Bloquea: F6

**P05 (ya abierta) · baja · antes del 13/11/2026** — ¿Se puede enviar al cliente una oferta con algún coste todavía pendiente, solo con un aviso (como ahora)?

- Por qué: Ya funciona así; falta su ratificación.
- Opciones: Sí, solo con aviso / No: bloquear el envío
- Mientras tanto: Hay aviso pero no bloqueo; solo bloquean el IVA pendiente y la venta sin indicar. Pendiente de su ratificación.
- Bloquea: F14

**P06 (ya abierta) · baja · antes del 13/11/2026** — Si la tarifa de un proveedor cambia mientras una oferta sigue dentro de su validez, ¿se mantiene el precio ofertado al cliente, o se recotiza la oferta?

- Por qué: Hoy una tarifa nueva no cambia las ofertas aceptadas y, para cambiarlas, se recotizan con motivo. Falta su ratificación.
- Opciones: Se mantiene; solo se recotiza con motivo (como ahora) / Se recotiza siempre que cambie la tarifa / Otra (indicar)
- Mientras tanto: Una tarifa nueva no cambia las ofertas aceptadas; para cambiar una hay que recotizarla con motivo. Pendiente de su ratificación.
- Bloquea: F14

**P07 (ya abierta) · baja · antes del 13/11/2026** — ¿Solo el gestor comercial puede recotizar una oferta aceptada, y siempre con motivo (como ahora)?

- Por qué: Ya funciona así; falta su ratificación.
- Opciones: Sí / También el comercial de la oferta / Otra (indicar)
- Mientras tanto: Solo el gestor comercial recotiza, y con motivo. Pendiente de su ratificación.
- Bloquea: F14

**P11 (ya abierta) · baja · antes del 13/11/2026** — Los gastos portuarios (PAD), ¿se cotizan dentro de T3 (como ahora) o dentro de los gastos de naviera (GLO)? ¿Y se presentan al cliente aparte o junto al THC, como «THC + gastos portuarios»?

- Por qué: Ya se cotizan dentro de T3; falta su ratificación y decidir la presentación. El IVA del THC lo decide Ángel aparte.
- Opciones: Dentro de T3 (como ahora) y presentados aparte / Dentro de T3 y presentados junto al THC como «THC + gastos portuarios» / Dentro de GLO (indicar cómo se presentan)
- Mientras tanto: T3-PAD se cotiza dentro de T3, pendiente de su ratificación.
- Bloquea: F14

**P12 (ya abierta) · baja · antes del 13/11/2026** — Las demoras, ocupaciones, VGM y gastos de naviera (GLO), ¿se venden con un precio tecleado o pactado? ¿Y el profit share no se vende nunca, como dijo el 29/09?

- Por qué: Ya funciona así; falta su ratificación. Ojo: lo que decida sobre los expedientes de agente puede cambiar lo del profit share.
- Opciones: Sí, como ahora / Con cambios (indicar)
- Mientras tanto: Configurado así, pendiente de su ratificación.
- Bloquea: F14

**P43 (ya abierta) · media · antes del 13/11/2026** — Para la venta única de almacenaje aéreo (ALM), ¿qué regla vale en las ofertas nuevas?

- Por qué: Las fuentes dan tres versiones y ninguna está confirmada. Hasta que se decida, el sistema no propone venta de ALM.
- Opciones: La del 25/09: 48 h libres; al superarlas, por día y por 100 kg o fracción desde la llegada; desde el 8.º día, otro importe para toda la estancia; con mínimo / La de las ofertas actuales: 3 días libres (4 si llega en viernes), cambio de importe el día 10 y variante si llega con DHL / Depende del handler o del cliente (indicar) / Mayor coste del proveedor + porcentaje (indicar)
- Hoy en Odoo 17: Hoy las ofertas de importación aérea imprimen 3 días libres y otro importe desde el día 10 (con una variante si llega con DHL), y el programa de previsiones calcula lo mismo.
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P43-D2 (ya abierta) · media · antes del 13/11/2026** — Para la venta de ALM, ¿qué peso se usa: el bruto, el tasable que figura en la AWB, o el tasable calculado (1 m³ = 167 kg)?

- Por qué: El número de unidades de 100 kg cambia según el peso elegido, y con él el importe.
- Opciones: Peso bruto / Peso tasable de la AWB / Peso tasable calculado (1 m³ = 167 kg)
- Hoy en Odoo 17: Hoy el programa de previsiones cobra por 100 kg o fracción del peso tasable.
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P43-D3 (ya abierta) · media · antes del 13/11/2026** — En la venta de almacenaje, ¿un «día» es un periodo de 24 h desde la llegada, o un día natural?

- Por qué: La regla no lo dice, y la compra a WFS está pendiente de la misma lectura.
- Opciones: Periodos de 24 h desde la llegada / Días naturales
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P43-D4 (ya abierta) · media · antes del 13/11/2026** — ¿El mínimo de venta de ALM es por estancia o por día? ¿Se cobra aunque la mercancía salga dentro de las horas libres?

- Por qué: La regla del 25/09 no da la unidad del mínimo.
- Opciones: Por estancia, y no se cobra dentro de las horas libres / Por estancia, y se cobra también dentro de las horas libres / Por día
- Hoy en Odoo 17: Hoy las ofertas aplican un mínimo por estancia.
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P43-D5 (ya abierta) · media · antes del 13/11/2026** — Para el umbral de «8 días o más», ¿el día de llegada cuenta como día 1? Si se cuentan periodos de 24 h, ¿son 8 periodos?

- Por qué: Un día más multiplica el importe, porque el precio de larga estancia se aplica a toda la estancia.
- Opciones: Sí, el día de llegada es el día 1 / No, se empieza a contar al día siguiente
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P43-D6 (ya abierta) · media · antes del 13/11/2026** — ¿Cuándo empieza y cuándo termina la estancia? En importación, ¿de la llegada (NOA) a la recogida? En exportación, ¿de la entrega al handler a la salida del vuelo?

- Por qué: Así lo indicó en un correo del 25/09; la versión anterior usaba la entrada y la salida del almacén.
- Opciones: Sí, así / Con otros eventos (indicar)
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P43-D7 (ya abierta) · media · antes del 13/11/2026** — ¿La regla de venta de ALM se aplica solo al aéreo o también al grupaje marítimo (LCL)? ¿En todos los aeropuertos o solo en Madrid y Barcelona?

- Por qué: Según un correo del 28/09, ALM cubre aéreo y LCL, pero la regla no lo dice.
- Opciones: Solo aéreo, en todos los aeropuertos / Solo aéreo, en Madrid y Barcelona / Aéreo y LCL
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11

**P44 (ya abierta) · media · antes del 13/11/2026** — ¿Se cargan las tarifas de almacenaje especial del handler (frío, mercancía peligrosa, mercancía valiosa, animales vivos) para que la oferta las aplique según el tipo de carga?

- Por qué: La tarifa de ALM de WFS que está cargada es solo para carga general.
- Opciones: Sí, todas / Solo algunas (indicar) / No: se escriben a mano
- Mientras tanto: Con carga especial, el coste se escribe a mano.
- Bloquea: F11 · con Ángel

**P44-B (ya abierta) · media · antes del 13/11/2026** — ¿Se crea un código propio para el almacén fuera del aeropuerto? Si se crea, ¿con qué unidades de cobro (palé, m³, entradas y salidas)?

- Por qué: Lo pidió el 08/10 y forma parte de la pregunta P44. El IVA y las unidades se cierran con Ángel.
- Opciones: Sí (indicar unidades) / No
- Mientras tanto: No se crea ningún código sin aprobación.
- Bloquea: F11 · con Ángel

**P43-D12 (ya abierta) · baja · antes del 20/11/2026** — Si la estancia real dura más que la cotizada, ¿la venta queda fija y el exceso se refactura aparte con motivo, o se recalcula la venta?

- Por qué: En Odoo 20 la venta nunca cambia sola.
- Opciones: Venta fija y exceso refacturado con motivo / Se recalcula la venta
- Mientras tanto: La venta no cambia sola; el exceso se puede refacturar como coste adicional con motivo.
- Bloquea: F11 (no bloquea el inicio), F14

**P43-D13 (ya abierta) · baja · antes del 20/11/2026** — La carga especial (frío, peligrosa, valiosa), ¿tiene su propia venta de ALM o sigue la misma regla?

- Por qué: La regla de venta no habla de la carga especial.
- Opciones: Misma regla / Venta propia (indicar) / Siempre tecleada
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11 (no bloquea el inicio), F14

**P43-D14 (ya abierta) · baja · antes del 20/11/2026** — ¿Desde qué fecha vale la regla de venta de ALM, hasta cuándo y en qué moneda?

- Por qué: En las pruebas del proyecto anterior se cargó desde el 25/09/2026, sin fecha de fin y en EUR, pero nunca se confirmó.
- Opciones: Desde el 25/09/2026, sin fin, en EUR / Otra (indicar)
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11 (no bloquea el inicio), F14

**P43-D8 (ya abierta) · baja · antes del 20/11/2026** — El mínimo de venta de ALM del 25/09 es menor que el mínimo que cobra WFS. ¿Se acepta vender por debajo del coste en estancias pequeñas, o la venta no puede bajar nunca del coste?

- Por qué: Afecta al margen de los envíos pequeños, y por eso lo deciden usted y Ángel.
- Opciones: Se acepta / La venta no baja nunca del coste
- Mientras tanto: El sistema no propone venta de ALM: se teclea («pendiente de decisión»).
- Bloquea: F11 (no bloquea el inicio), F14 · con Ángel

### Etapa 2 Apertura
**F0-C22 · media · antes del 11/11/2026** — Además de Abierto, En tránsito, Entregado y Operaciones cerradas, ¿quiere los estados «Llegado» y «Pendiente de cierre», como en Odoo 17?

- Por qué: Los estados ordenan todo el ciclo y sus condiciones. Sin «Llegado» no se ve qué expedientes están en destino pendientes de aduana o de entrega.
- Opciones: Añadir Llegado y Pendiente de cierre (como Odoo 17) / Añadir solo Llegado / Mantener los cuatro actuales
- Hoy en Odoo 17: Hoy en Odoo 17 hay cinco etapas: Pendiente de salida, En tránsito, Llegado, Entregado y Pendiente de cierre.
- Mientras tanto: Cuatro estados (más Cancelado) que se cambian sin ninguna condición («pendiente de decisión»).
- Bloquea: F5, F7, F10, F11, F12

**F0-C23 · media · antes del 11/11/2026** — ¿Cómo se asigna el operativo responsable de un expediente: a mano al abrirlo, o automáticamente por cliente y tráfico, como en Odoo 17?

- Por qué: Sin operativo no hay cola de trabajo ni avisos por persona. Hoy el responsable es el comercial de la oferta.
- Opciones: A mano al abrir el expediente / Automático por cliente y tráfico (tabla que mantiene operaciones) / Automático por tráfico, con excepciones por cliente
- Hoy en Odoo 17: Hoy en Odoo 17 hay una tabla que asigna el operativo por cliente y tráfico, y el expediente guarda por separado el operativo y el KAM.
- Mientras tanto: El responsable del expediente es el comercial de la oferta; la figura del operativo no existe («pendiente de decisión»).
- Bloquea: F5, F10

**F0-C24 · media · antes del 11/11/2026** — Para la importación marítima FCL, que es la primera que se va a construir, ¿valida esta lista de hitos, o la acorta? Antes de la salida: envío confirmado, instrucciones recibidas, booking emitido y confirmado, mercancía lista, recogida hecha, mercancía en puerto, documentos de aduana y poder recibidos, aduana presentada y despachada, instrucciones de embarque (SI) presentadas y buque salido. En tránsito: pre-alerta recibida y enviada, documentos de aduana recibidos, revisados y enviados, aduana autorizada y llegada a puerto. En destino: aduana presentada, levante, facturado, entrega gestionada y entregado. Después: facturas de proveedor recibidas y revisadas, y cobros y pagos hechos.

- Por qué: Cada hito sería una tarea del operativo al abrir el expediente, y es lo que indica qué falta en cada envío.
- Opciones: Valido la lista tal cual / Lista más corta (tacho los que sobran) / Otra lista (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 existen estas cuatro listas de subhitos (13, 9, 5 y 5 pasos). En un expediente reciente de 2026 estaban vacías, así que no consta que se sigan usando.
- Mientras tanto: El expediente no tiene hitos ni tareas («pendiente de decisión»).
- Bloquea: F5

**F0-C25 · media · antes del 11/11/2026** — ¿Qué hitos son obligatorios, es decir, impiden pasar al estado siguiente si no están hechos?

- Por qué: Separa la lista de ayuda de los controles de verdad. Demasiados hitos obligatorios frenarían al operativo.
- Opciones: Ninguno: los hitos solo sirven de guía / Los que marque en la lista / Todos
- Hoy en Odoo 17: Hoy en Odoo 17, al completar el último paso de cada lista, el expediente pasa a la etapa siguiente.
- Mientras tanto: No hay hitos, y ningún cambio de estado tiene condiciones.
- Bloquea: F5, F7, F10

**F0-C26 · media · antes del 11/11/2026** — ¿Todos los hitos los hace el operativo del expediente, o algunos los hace otra persona (comercial, compras, administración)?

- Por qué: Cada hito se asigna como tarea a una persona, así que hay que saber a quién.
- Opciones: Todos el operativo / Algunos otra persona (indicar cuáles y quién)
- Hoy en Odoo 17: Hoy en Odoo 17 la factura al cliente la prepara el operativo y la revisa administración, y las facturas de proveedor las registra administración.
- Mientras tanto: El expediente no tiene tareas asignadas.
- Bloquea: F5

**F0-C27 · media · antes del 11/11/2026** — ¿Qué datos operativos debe tener todo expediente? Marque los que procedan: fecha de mercancía lista, fecha de booking, seguro (pedido, emitido o sin seguro), quién lleva el transporte, quién contrata el flete, fecha de entrega planificada y fecha de la última revisión.

- Por qué: Sin ellos no se pueden calcular sus indicadores (de mercancía lista a salida, o llegados sin entrega planificada) ni los avisos de supervisión.
- Opciones: Todos los de la lista / Solo algunos (indicar) / Añadir otros (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el expediente tiene todos esos datos y guarda el historial de cambios de ETD y ETA.
- Mientras tanto: Solo existen la ETD, la ETA y el historial de sus cambios; el resto queda «pendiente de decisión».
- Bloquea: F5

**M2-I (ya abierta) · media · antes del 11/11/2026** — Para grupajes y consolidaciones (un BL o AWB máster con varias houses y costes compartidos), ¿qué forma prefiere: un expediente máster con expedientes hijos, o un expediente con varias partidas dentro, como en Odoo 17?

- Por qué: Si elige partidas, la aduana y los documentos tendrán que ir en la partida; por eso se diseñan desde ahora para poder moverlos. Consta una indicación suya del 17/09 (máster = expediente, house = partida), pero no se ha encontrado por escrito.
- Opciones: Expediente máster con expedientes hijos / Partidas dentro del expediente (como Odoo 17) / Después del arranque; mientras tanto, un expediente por house con las referencias del máster
- Hoy en Odoo 17: Hoy en Odoo 17 cada expediente tiene partidas (aduana, expedidor y destinatario, HBL, Incoterm, contenedores); casi todos tienen una sola.
- Mientras tanto: Cada expediente equivale a una partida; no hay nada construido para consolidar.
- Bloquea: F16, F6, F7 · con Belal

**F0-C28 · media · antes del 13/11/2026** — ¿Qué hitos llevan la importación aérea y la exportación aérea (por ejemplo: NOA, recogida en el handler, entrega al handler, salida del vuelo)?

- Por qué: La exportación aérea forma parte de la aceptación final y nunca se ha recorrido en Odoo 20.
- Opciones: Indico la lista de cada una / La de marítimo adaptada (Belal la prepara y yo la reviso)
- Hoy en Odoo 17: Hoy en Odoo 17 las listas de subhitos se hicieron para la importación marítima; no está comprobado cómo se usan en aéreo.
- Mientras tanto: Sin hitos («pendiente de decisión»).
- Bloquea: F11

**F0-C29 · media · antes del 13/11/2026** — ¿Qué hitos llevan la exportación marítima FCL, el grupaje (LCL) y el transporte terrestre?

- Por qué: Son tráficos que nunca se han ejecutado en Odoo 20.
- Opciones: Indico la lista de cada uno / La de importación marítima adaptada (Belal la prepara y yo la reviso)
- Hoy en Odoo 17: Hoy en Odoo 17 no hay listas propias para exportación, grupaje ni terrestre: las de importación marítima se adaptan según el sentido.
- Mientras tanto: Sin hitos («pendiente de decisión»).
- Bloquea: F12

**F0-C30 · baja · antes del 20/11/2026** — En una consolidación, ¿con qué base se reparten los costes del máster entre las houses: peso tasable, volumen, peso bruto o a partes iguales?

- Por qué: Solo hace falta si se construye la consolidación.
- Opciones: Peso tasable / Volumen / Peso bruto / A partes iguales / Según el caso (a mano)
- Hoy en Odoo 17: Hoy en Odoo 17 existe una herramienta que reparte líneas entre partidas.
- Mientras tanto: Se reparte a mano entre expedientes.
- Bloquea: F16 · con Ángel

### Etapa 3 Reserva y salida
**F0-C31 · media · antes del 11/11/2026** — ¿Qué tiene que cumplirse para pasar un expediente a «En tránsito»?

- Por qué: Hoy se puede marcar «En tránsito» sin fecha de salida, así que el estado no es fiable.
- Opciones: Como en Odoo 17: ETD o ATD pasada, sin números de contenedor provisionales, que no sea preexpediente, seguro confirmado o emitido, y expedidor y destinatario reales / Solo la ATD informada / Distinto según el tráfico (indicar) / Otra lista (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 se exige la ETD o ATD pasada, ningún contenedor provisional, que no sea un preexpediente, el seguro confirmado o emitido, y expedidor y destinatario reales.
- Mientras tanto: El paso a «En tránsito» no tiene condiciones («pendiente de decisión»).
- Bloquea: F5

**F0-C32 · media · antes del 11/11/2026** — ¿Es obligatorio tener la confirmación del proveedor (su referencia o su acuse en el pedido) antes de pasar a «En tránsito»?

- Por qué: Hoy el paso «el proveedor confirma» no deja rastro en ningún pedido.
- Opciones: Sí, en todos los pedidos / Solo en el transporte principal (naviera o aerolínea) / No: solo se anota
- Mientras tanto: El pedido admite la referencia del proveedor, pero no se exige.
- Bloquea: F5, F8

**F0-C33 · media · antes del 11/11/2026** — ¿Valida un catálogo fijo de tipos de evento del envío? Propuesta: booking enviado y confirmado, pre-alerta recibida y enviada, borradores aprobados, documentos de aduana enviados, despacho, levante, entrega programada, entrega hecha, vacío devuelto, retraso, incidencia, aviso de llegada, y entrada y salida de almacén.

- Por qué: Con tipos fijos, los eventos quedan ligados a las fechas, se publican igual en el portal y sirven para los indicadores.
- Opciones: Valido la lista / Con cambios (indicar)
- Mientras tanto: Los eventos son texto libre (por ejemplo «Salida» o «Booking confirmado») y no están ligados a las fechas.
- Bloquea: F5

**F0-C34 · media · antes del 11/11/2026** — ¿Qué tipos de evento se publican por defecto al cliente en el portal? El operativo podrá cambiarlo en cada caso.

- Por qué: Decide qué ve el cliente en «Mis envíos» sin trabajo extra del operativo.
- Opciones: Salida, llegada, levante y entrega / Ninguno: siempre a mano / Otra lista (indicar)
- Mientras tanto: No se publica nada por defecto: el personal publica a mano cada evento.
- Bloquea: F5, F6

**F0-C35 · media · antes del 11/11/2026** — ¿En qué hitos se prepara un aviso al cliente o al agente (por ejemplo: levante, entrega programada, entrega hecha, cambio de ETD o ETA), y a quién va dirigido?

- Por qué: Sin esto se perdería lo que hoy se avisa al agente. Durante las pruebas no se envía ningún correo: el aviso quedaría como tarea con el correo preparado.
- Opciones: Como en Odoo 17: al agente en el levante, la entrega programada y la entrega hecha / También al cliente (indicar hitos) / Ninguno
- Hoy en Odoo 17: Hoy en Odoo 17, solo en los tráficos de agente, se crea una tarea con un correo preparado para el agente en el levante, la entrega programada y la entrega hecha; además, cada cambio de fechas deja una nota.
- Mientras tanto: No hay avisos, y el correo saliente está desactivado durante las pruebas.
- Bloquea: F5, F7

**F0-C36 · media · antes del 13/11/2026** — En exportación, ¿qué datos necesita el expediente? Marque los que procedan: fechas de corte (documentos, instrucciones de embarque (SI), VGM, entrega del contenedor lleno y grupaje), tipo de BL y forma de liberación (original, SWB, télex) y BL máster verificado.

- Por qué: Sin cortes ni SI/VGM no se puede llevar una exportación marítima.
- Opciones: Todos los de la lista / Solo algunos (indicar) / Añadir otros (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el expediente tiene esos cortes y la marca de BL máster verificado, y hay un aviso para los cortes y fechas que faltan.
- Mientras tanto: Estos datos no existen; la exportación marítima no se ha ejecutado nunca en Odoo 20.
- Bloquea: F12

### Etapa 4 Documentos
**F0-C37 · media · antes del 11/11/2026** — ¿Valida esta lista de tipos de documento del expediente? Booking, CR, factura comercial, packing list, certificados, orden de aduana, despacho, MBL, HBL, MAWB, HAWB, aviso de llegada, pre-DUA, DUA, factura, factura de proveedor, Entréguese, Admítase, levante, DAE, oferta al cliente, oferta de proveedor, H1 y orden de transporte.

- Por qué: Sin tipos no se puede filtrar, ni decidir qué llega al portal, ni exigir un documento en un paso (por ejemplo, el levante antes de entregar).
- Opciones: Valido la lista / Con cambios (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 existe esta lista (23 tipos más la orden de transporte), pero casi ningún documento reciente está clasificado.
- Mientras tanto: Los documentos se adjuntan al expediente sin tipo.
- Bloquea: F6

**F0-C38 · media · antes del 11/11/2026** — ¿Qué documentos son obligatorios en cada etapa (por ejemplo, el levante antes de «Entregado», o el BL antes de «En tránsito»)?

- Por qué: De esto dependen las condiciones de los estados, las del cierre y la lista «Pendiente».
- Opciones: Indico documento y etapa / Ninguno es obligatorio
- Mientras tanto: Ningún documento es obligatorio.
- Bloquea: F6, F7, F10

**F0-C39 · media · antes del 11/11/2026** — ¿Qué documentos ve el cliente en el portal: solo los que el operativo publica uno a uno (como ahora), o algunos tipos que se publican siempre (por ejemplo HBL, aviso de llegada, DUA y levante, y su factura)?

- Por qué: El cliente solo debe ver los de su propio envío; los documentos del máster pueden llevar datos de otros clientes.
- Opciones: Solo los que publica el operativo / Algunos tipos siempre (indicar)
- Mientras tanto: Solo lo que el personal publica a mano, y solo del envío del propio cliente.
- Bloquea: F6

**F0-C40 · media · antes del 11/11/2026** — ¿Quiere pedir desde el expediente documentos al cliente o al agente (factura comercial, packing list, certificados), con un enlace de subida y una fecha límite? Si es así, ¿qué documentos y en qué momento?

- Por qué: Hoy estos documentos se reclaman fuera de Odoo y el expediente no muestra qué falta. El envío de los correos se activaría en el arranque.
- Opciones: Sí (indicar documentos y momento) / No: se siguen pidiendo fuera de Odoo
- Mientras tanto: No existe; los documentos se piden fuera de Odoo.
- Bloquea: F6

**F0-C42 · media · antes del 11/11/2026** — Además de la orden de transporte, ¿cuáles de estos documentos debe emitir Odoo 20 para el arranque, y en qué orden: confirmación de booking, instrucciones de embarque (SI), pre-alerta, delivery order, carátula del expediente y listado de mercancía?

- Por qué: Cada documento es trabajo de desarrollo; sin un orden de prioridad no cabe todo antes del 1/1.
- Opciones: Indico la lista en orden de prioridad / Ninguno para el arranque
- Hoy en Odoo 17: Hoy en Odoo 17 salen del sistema la orden de transporte, el HBL, la AWB y su etiqueta, el manifiesto de carga y el listado de mercancía.
- Mientras tanto: Ninguno de esos documentos existe en Odoo 20; se hacen fuera.
- Bloquea: F7, F12

**F0-C43 · baja · antes del 11/11/2026** — ¿Hace falta para el arranque el seguimiento automático con navieras y aerolíneas, o basta con registrar los eventos a mano y a partir de las fechas?

- Por qué: No existe ni en Odoo 17 ni en Odoo 20, y el plan lo deja fuera del 1/1.
- Opciones: Basta a mano (fuera del 1/1) / Hace falta (indicar navieras o aerolíneas)
- Hoy en Odoo 17: Hoy en Odoo 17 no hay seguimiento automático.
- Mientras tanto: Los eventos se registran a mano o a partir de las fechas.
- Bloquea: F6

**P10-A (ya abierta) · media · antes del 11/11/2026** — En el portal, ¿una empresa de un grupo puede ver los envíos de otra entidad legal del mismo grupo (por ejemplo, de su filial)?

- Por qué: Hoy cada contacto solo ve los envíos de su propia empresa. Abrirlo obliga a definir los grupos.
- Opciones: No (como ahora) / Sí, cuando BOSS lo conceda para ese grupo
- Mientras tanto: No: cada contacto ve solo los envíos de su propia empresa.
- Bloquea: F6 · con Belal

**P10-B (ya abierta) · media · antes del 11/11/2026** — En el portal, ¿qué puede ver el expedidor o el destinatario que no es el ordenante del envío?

- Por qué: Hoy solo el ordenante ve el envío.
- Opciones: Nada (como ahora) / Solo el seguimiento (fechas y eventos) / El seguimiento y los documentos publicados
- Mientras tanto: Nada: solo el ordenante ve el envío.
- Bloquea: F6

**F0-C44 · media · antes del 13/11/2026** — ¿BOSS seguirá emitiendo desde Odoo 20 las AWB (house y máster) y sus etiquetas? Si es así, ¿con qué datos de los bultos (piezas, medidas, peso, clase de tarifa, mercancía peligrosa, valor declarado)?

- Por qué: Sin esos datos bien ordenados no se puede generar la AWB. Si no hace falta, se ahorra ese trabajo.
- Opciones: Sí, con esos datos / Sí, con otros datos (indicar) / No: se hacen fuera de Odoo
- Hoy en Odoo 17: Hoy en Odoo 17 se emiten AWB house y máster (unas 200) y sus etiquetas; a veces la descripción de la carga va escrita a mano en la plantilla.
- Mientras tanto: No existe en Odoo 20.
- Bloquea: F11

**F0-C45 · media · antes del 13/11/2026** — ¿BOSS emite sus propios HBL como NVOCC y el manifiesto de carga? ¿Deben salir de Odoo 20 desde el 1/1?

- Por qué: Depende también de cómo se lleven las consolidaciones.
- Opciones: Sí, desde el 1/1 / Sí, pero después del arranque / No
- Hoy en Odoo 17: Hoy en Odoo 17 se emiten HBL (unos 280) y manifiestos de carga.
- Mientras tanto: No existe en Odoo 20.
- Bloquea: F12, F16

### Etapa 5 Destino y aduana
**F0-C47 · media · antes del 11/11/2026** — ¿Qué datos de aduana debe registrar el expediente? Marque los que procedan: número de DUA, canal (verde, naranja, rojo), fecha de admisión, fecha de levante, fecha de envío de documentos al agente de aduanas, tipo de garantía y si la aduana la lleva BOSS.

- Por qué: El despacho es la mayor parte de «En tránsito» y «Llegado». Sin el levante registrado no puede haber condición de entrega ni aviso al agente.
- Opciones: Todos los de la lista / Solo algunos (indicar) / Añadir otros (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 la partida tiene el DUA y su fichero, canal, admisión, levante, documentos enviados, retraso de aduana, tipo de garantía y estado aduanero.
- Mientras tanto: Solo existen la referencia del DUA y el agente de aduanas («pendiente de decisión»).
- Bloquea: F7

**F0-C48 · media · antes del 11/11/2026** — ¿Qué estados de aduana quiere seguir: pendiente, documentos enviados, presentado y levante, u otros?

- Por qué: Permiten ver en qué punto está cada despacho y avisar a tiempo.
- Opciones: Pendiente, documentos enviados, presentado y levante / Los de Odoo 17: pendiente, documentos enviados y gestionado / Otros (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el estado aduanero puede ser Pendiente, Documentos enviados o Gestionado.
- Mientras tanto: No hay estado de aduana.
- Bloquea: F7

**F0-C49 · media · antes del 11/11/2026** — Si existe el estado «Llegado», ¿qué tiene que cumplirse para pasar a él: que haya pasado la ATA, como en Odoo 17, u otra cosa?

- Por qué: Solo aplica si decide tener el estado «Llegado».
- Opciones: ATA informada y ya pasada / Otra condición (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17, si la ATA está vacía se copia la ETA, y se exige que la ATA haya pasado.
- Mientras tanto: El estado «Llegado» no existe.
- Bloquea: F7

**F0-C50 · media · antes del 11/11/2026** — ¿Debe Odoo 20 emitir el aviso de llegada al cliente? Si es así, ¿con qué datos?

- Por qué: Es un documento operativo que hoy se hace fuera del sistema.
- Opciones: Sí (indicar los datos o enviar un ejemplo) / No para el arranque
- Hoy en Odoo 17: Hoy en Odoo 17 el aviso de llegada se guarda como documento, pero no lo emite el sistema.
- Mientras tanto: No existe en Odoo 20.
- Bloquea: F7

### Etapa 6 Entrega y contenedores
**F0-C51 · media · antes del 11/11/2026** — ¿Qué tiene que cumplirse para pasar a «Entregado»? Por ejemplo: levante cuando BOSS lleva la aduana, fecha de descarga en importación, y fecha y hora de entrega informadas y ya pasadas cuando BOSS hace el transporte.

- Por qué: Hoy se puede marcar «Entregado» sin ATA, sin entrega y sin levante, así que el estado no sirve para el cierre. Si además tiene que estar facturado lo deciden Ángel y usted aparte.
- Opciones: Todo lo anterior (como Odoo 17, sin contar la factura) / Solo la fecha de entrega / Distinto según el tráfico (indicar) / Otra lista (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 se exige estar facturado, la fecha de descarga en importación (en aéreo se toma la ETA), el levante si la aduana la lleva BOSS y la fecha de entrega ya pasada, salvo que no haya transporte.
- Mientras tanto: El paso a «Entregado» no tiene condiciones («pendiente de decisión»).
- Bloquea: F7

**F0-C53 · media · antes del 11/11/2026** — ¿Qué debe llevar la orden de transporte al camionero? Marque lo que proceda: direcciones completas de recogida y entrega, persona de contacto, franja horaria, contenedores con precinto, terminal o depósito (Entréguese/Admítase), notas de entrega, peso y bultos, y referencias.

- Por qué: Es el documento operativo más usado. Sin él, el tramo terrestre no se puede ordenar desde Odoo 20.
- Opciones: Todo lo de la lista / Solo algunos (indicar) / Añadir otros (envío una OT de ejemplo)
- Hoy en Odoo 17: Hoy en Odoo 17 la OT (más de 1.700 emitidas) lleva origen y destino con dirección, contenedores con precinto, fecha y hora de entrega, notas, referencias, expedidor y destinatario, y días de retraso.
- Mientras tanto: El pedido al transportista solo imprime nombre y ciudad de recogida y de entrega; la OT se hace fuera de Odoo 20.
- Bloquea: F7

**F0-C54 · media · antes del 11/11/2026** — ¿La orden de transporte se emite desde el pedido de compra al transportista, o desde el expediente?

- Por qué: Decide dónde la busca el operativo y cómo se archiva.
- Opciones: Desde el pedido al transportista / Desde el expediente
- Hoy en Odoo 17: Hoy en Odoo 17 la OT es un documento propio, ligado al expediente o a la partida.
- Mientras tanto: La OT no existe en Odoo 20.
- Bloquea: F7

**F0-C55 · media · antes del 11/11/2026** — ¿Con cuántos días de antelación al último día libre de un contenedor hay que avisar al operativo para que lo devuelva? ¿Y a quién más?

- Por qué: Hoy la demora solo aparece cuando ya es un coste.
- Opciones: (indicar días) al operativo / (indicar días) al operativo y al comercial
- Mientras tanto: No hay último día libre ni aviso; la demora solo se ve al recalcular el coste.
- Bloquea: F7

### Etapa 7 Proveedores
**P33 (ya abierta) · media · antes del 11/11/2026** — ¿Qué costes se piden al proveedor con pedido de compra, y cuáles se registran sin pedido (como los derechos e IVA del DUA)?

- Por qué: Ya funciona así; falta su ratificación y la de Ángel.
- Opciones: Como ahora: pedido para los servicios de proveedor y suplidos sin pedido / Otra regla (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 no se usan pedidos de compra: se registran previsiones y después la factura del proveedor.
- Mientras tanto: Pedido para los servicios de proveedor y suplidos sin pedido, pendiente de ratificación.
- Bloquea: F8 · con Ángel

### Etapa 8 Factura al cliente
**F0-C56 · media · antes del 13/11/2026** — Cuando un expediente se factura a varias partes (por ejemplo, el flete al agente y los gastos locales al destinatario), ¿cómo prefiere hacerlo: con un segundo pedido de venta dentro del mismo expediente, o indicando en cada línea a quién se factura?

- Por qué: Hoy un expediente factura a un solo cliente; otro pagador obliga a hacer otra oferta.
- Opciones: Segundo pedido de venta en el mismo expediente / Indicar en cada línea a quién se factura
- Hoy en Odoo 17: Hoy en Odoo 17 cada línea de venta lleva su entidad y se hace una factura por entidad.
- Mientras tanto: Un solo cliente por expediente; otro pagador necesita otra oferta.
- Bloquea: F13

**F0-C57 · media · antes del 13/11/2026** — ¿El expediente debe registrar si el flete es prepaid o collect? ¿Y eso decide a quién se factura el flete?

- Por qué: Sin ese dato no se puede facturar desde el expediente el flete collect ni la nota de cargo al agente.
- Opciones: Sí, y decide a quién se factura / Sí, solo como dato / No
- Hoy en Odoo 17: Hoy en Odoo 17 el expediente guarda si es prepaid o collect y a quién se factura.
- Mientras tanto: Ese dato no existe.
- Bloquea: F12, F13

**F0-C58 · media · antes del 13/11/2026** — ¿Cómo se liquida el profit share con el agente: se le vende, va como línea negativa en la factura al agente ordenante, el abono del agente se registra como ingreso, o depende del caso?

- Por qué: Sin esto no se puede liquidar un expediente de agente: el reparto no aparece ni en la venta, ni en el margen, ni en el resumen.
- Opciones: Según el caso, como en Odoo 17 (los cuatro casos) / Solo algunos de esos casos (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 se dan cuatro casos: factura del agente de origen con profit share, abono del agente, factura de BOSS al agente con el profit share como ingreso, y línea negativa en la factura al agente ordenante.
- Mientras tanto: El profit share solo se compra, nunca se vende. No hay ningún expediente de agente en Odoo 20.
- Bloquea: F13

**F0-C59 · media · antes del 13/11/2026** — ¿Hace falta una factura que agrupe varios expedientes (por ejemplo, la facturación periódica a un cliente)?

- Por qué: Cambia cómo se hace la factura y cómo se imprime.
- Opciones: Sí (indicar para qué clientes) / No: una factura por expediente
- Hoy en Odoo 17: Hoy en Odoo 17 existe una facturación masiva que junta varios expedientes.
- Mientras tanto: Una factura por expediente.
- Bloquea: F13

### Etapa 9 Cobros y pagos
**P30 (ya abierta) · media · antes del 11/11/2026** — Su requisito escrito dice que no se pague ni se contabilice una factura de proveedor si el servicio no está facturado al cliente. ¿Qué quería evitar: el pago, la contabilización o las dos cosas? ¿Y siguen valiendo las excepciones del coste que asume BOSS y del flete pagado por adelantado a un agente?

- Por qué: El alcance contable lo decide Ángel, pero el requisito es suyo: hace falta saber qué quería decir antes de que él lo ratifique.
- Opciones: Solo el pago (como ahora), con esas excepciones / La contabilización y el pago, con esas excepciones / Solo avisar, sin bloquear / Otra (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el pago no se bloquea por este motivo.
- Mientras tanto: La factura de proveedor se puede contabilizar, pero su pago queda bloqueado hasta facturar al cliente (propuesta aprobada por Belal el 23/10, pendiente de ratificar por Ángel y por usted).
- Bloquea: F8 · con Ángel

### Etapa 10 Cierre operativo
**F0-C60 · media · antes del 11/11/2026** — ¿Qué tiene que cumplirse para el cierre operativo? Por ejemplo: estar «Entregado», hitos y documentos obligatorios hechos, toda la venta facturada, ningún aviso de margen pendiente y valoraciones hechas.

- Por qué: Hoy un expediente se cierra sin condiciones y sigue siendo editable, así que el cierre no sirve para el cierre de mes.
- Opciones: Todo lo anterior (como Odoo 17) / Solo estar Entregado y con la venta facturada / Otra lista (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 el cierre operativo exige estar Entregado o Pendiente de cierre, toda la venta facturada, ningún aviso de margen sin desbloquear y las valoraciones hechas.
- Mientras tanto: El cierre operativo es un botón sin condiciones («pendiente de decisión»).
- Bloquea: F10

**F0-C61 · media · antes del 11/11/2026** — ¿Quién puede hacer el cierre operativo, y quién puede reabrir o cambiar datos de un expediente cerrado?

- Por qué: Después del cierre, los datos del envío tienen que quedar fijos, porque de ellos dependen los costes y la comisión.
- Opciones: Cierra el operativo y solo el gestor puede reabrir / Cierra el operativo o el gestor, y solo yo puedo reabrir / Otra (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 cierra el operativo del expediente (o dos usuarios autorizados) y, una vez cerrado, solo informática puede modificarlo.
- Mientras tanto: Cualquiera puede cerrar y reabrir, y un expediente cerrado sigue siendo editable.
- Bloquea: F10

**F0-C62 · media · antes del 11/11/2026** — ¿Quiere un cierre comercial, aparte del operativo, que haga el comercial?

- Por qué: Odoo 17 separa los dos cierres; Odoo 20 tiene un cierre operativo y un cierre financiero.
- Opciones: Sí, como en Odoo 17 / No: bastan el cierre operativo y el financiero
- Hoy en Odoo 17: Hoy en Odoo 17 hay un cierre comercial aparte que hace el comercial.
- Mientras tanto: No existe el cierre comercial.
- Bloquea: F10

**F0-C63 · media · antes del 11/11/2026** — ¿En qué plazo debe cerrarse operativamente un expediente entregado: una semana después de la entrega, a final del mes de la fecha importante, u otro?

- Por qué: Aparece en su documento de requisitos, pero sin confirmar. De esto dependen los avisos de expedientes sin cerrar.
- Opciones: Una semana después de la entrega / A final del mes de la fecha importante / Otro (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 un aviso señala los expedientes entregados que llevan más de 14 días sin cerrar, y otro a final de mes pide facturar y cerrar.
- Mientras tanto: No hay plazo ni aviso.
- Bloquea: F10

**F0-C64 · media · antes del 11/11/2026** — ¿Qué avisos de supervisión quiere, y con qué umbrales? Por ejemplo: ETA pasada sin ATA, expediente sin revisar durante N días, cortes, mercancía lista, ETD o seguro sin informar, y venta pendiente de facturar a final de mes.

- Por qué: Sin avisos, los expedientes atascados pasan desapercibidos. La propuesta es que en Odoo 20 sean tareas para el operativo, sin correo.
- Opciones: Los de Odoo 17, con sus umbrales / Solo algunos (indicar cada uno con su umbral)
- Hoy en Odoo 17: Hoy en Odoo 17 llegan correos con: avisos de cortes, mercancía lista, ETD y seguro (lunes, miércoles y viernes); expedientes sin revisar más de 2 días laborables (7 para el comercial); entregados sin cerrar más de 14 días; pendientes de facturar y de cerrar a final de mes; y un resumen semanal de cierres.
- Mientras tanto: No hay avisos programados.
- Bloquea: F10

**F0-C65 · media · antes del 11/11/2026** — ¿Quién recibe cada aviso: el operativo, el comercial (KAM), usted en copia?

- Por qué: Cada aviso se asigna como tarea a una persona.
- Opciones: El operativo, conmigo en copia / El operativo y el comercial / Otra (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 los avisos llegan por correo a cada operativo; el de fin de mes va con copia a Ángel, y el resumen semanal de cierres va al KAM con copia a usted.
- Mientras tanto: No hay avisos.
- Bloquea: F10

**F0-C66 · baja · antes del 11/11/2026** — ¿Hay que valorar a clientes y proveedores al cerrar el expediente, como en Odoo 17?

- Por qué: Si se mantiene, pasa a ser un requisito del cierre; si no, queda fuera del plan.
- Opciones: Sí, obligatorio para cerrar / Sí, opcional / No
- Hoy en Odoo 17: Hoy en Odoo 17 el cierre operativo exige las valoraciones desde el 01/03/2025.
- Mientras tanto: No existen valoraciones.
- Bloquea: F10

**F0-C67 · baja · antes del 11/11/2026** — ¿Las incidencias del envío deben registrar coste, horas, causa, acción correctora y estado, para poder restarlas del margen?

- Por qué: Permite medir las incidencias y lo que cuestan. Si no lo pide, queda fuera del plan.
- Opciones: Sí / No: basta una nota
- Hoy en Odoo 17: Hoy en Odoo 17 la incidencia guarda coste, horas, solución, acción preventiva, departamento y estado.
- Mientras tanto: Las incidencias son un evento de texto libre.
- Bloquea: F10

### Etapa 11 Cierre financiero y de mes
**F0-C68 · media · antes del 11/11/2026** — ¿Con qué criterios quiere ver la rentabilidad de varios expedientes juntos: por mes, cliente, comercial, operativo o tráfico?

- Por qué: Hoy el margen solo se ve expediente por expediente. El informe se construye junto con el cierre.
- Opciones: Por todos esos criterios / Solo por algunos (indicar)
- Mientras tanto: Las cifras se ven en cada expediente, y el análisis contable solo incluye lo contabilizado.
- Bloquea: F10 · con Ángel

### Etapa P Proyecto y arranque
**F0-C69 · alta · antes del 30/10/2026** — Si no da tiempo a todo antes del 1/1, ¿qué tráficos tienen que estar en Odoo 20 desde el 1/1 y cuáles pueden seguir unas semanas en Odoo 17: expedientes de agente (profit share, fletes collect, varios pagadores), exportación marítima, grupaje (LCL), terrestre y consolidaciones?

- Por qué: Con un solo desarrollador el plan completo no cabe antes del 1/1. Belal decide la capacidad y necesita saber qué tráficos son imprescindibles para el arranque.
- Opciones: Todos tienen que estar en Odoo 20 el 1/1 / Importación marítima FCL y aéreo el 1/1; el resto puede seguir unas semanas en Odoo 17 / Otra combinación (indicar)
- Mientras tanto: No está decidido qué tráficos entran antes del 1/1. El orden del plan pone primero la importación marítima FCL y el aéreo; ningún tráfico queda fuera por suposición.
- Bloquea: F0, F12, F13, F16 · con Belal

**F0-C70 · alta · antes del 30/10/2026** — Los clientes de almacén (entradas, palés, almacenaje mensual), ¿deben llevarse en Odoo 20 desde el 1/1, o siguen en Odoo 17?

- Por qué: El almacén está fuera del plan actual. Si tiene que entrar el 1/1, es trabajo nuevo y cambia la capacidad.
- Opciones: Siguen en Odoo 17 por ahora / Tienen que estar en Odoo 20 el 1/1
- Hoy en Odoo 17: Hoy en Odoo 17 las entradas de almacén crean previsiones de compra y de venta, y hay un recordatorio mensual de almacenaje.
- Mientras tanto: Fuera del plan; la gestión de almacén no está instalada en Odoo 20.
- Bloquea: F0, F15 · con Belal

**F0-C71 · media · antes del 13/11/2026** — ¿Quién de operaciones repite cada prueba con envíos reales: importación marítima FCL, importación y exportación aéreas, exportación marítima y terrestre, y la prueba comercial?

- Por qué: La aceptación de cada tráfico la tienen que dar las personas de BOSS antes del 1/12.
- Opciones: Indico persona o papel para cada prueba
- Mientras tanto: Las pruebas no tienen responsable asignado.
- Bloquea: F14

**F0-C72 · media · antes del 13/11/2026** — ¿Qué cuenta como «envío real representativo» para dar por buena una prueba (por ejemplo, un cliente migrado, una naviera con tarifa aprobada y un caso de los últimos meses)?

- Por qué: Evita dar por buena una prueba hecha solo con datos de demostración.
- Opciones: Lo del ejemplo / Otro criterio (indicar)
- Mientras tanto: Las pruebas se hacen con registros de prueba, sin un criterio de envío representativo.
- Bloquea: F14

**F0-C73 · media · antes del 20/11/2026** — ¿Qué expediente de Odoo 17 cuenta como «abierto» el 1/1 y pasa a Odoo 20: todos los no cerrados, o solo los que aún no han llegado (pendientes de salida y en tránsito)?

- Por qué: Sin esto, el primer día los envíos en curso no tendrían expediente en Odoo 20.
- Opciones: Todos los no cerrados de 2026 / Solo los pendientes de salida y en tránsito; el resto se termina en Odoo 17 / Otro criterio (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 hay entre 500 y 1.000 expedientes pendientes de salida, menos de 100 en tránsito y más de 200 en cada una de las demás etapas, incluidos algunos antiguos sin cerrar.
- Mientras tanto: No se migra ningún expediente hasta que usted decida.
- Bloquea: F15 · con Belal

**F0-C74 · media · antes del 20/11/2026** — De cada expediente abierto que pase a Odoo 20, ¿qué datos deben llegar: etapa, partes, contenedores, referencias, fechas y servicios pendientes de comprar o de facturar? ¿Falta o sobra algo?

- Por qué: Fija el alcance de la migración y cómo se comprueba después contra Odoo 17.
- Opciones: Todo lo de la lista / Menos (indicar) / Más (indicar)
- Mientras tanto: No se migra ningún expediente hasta que usted decida.
- Bloquea: F15 · con Belal

**P36 (ya abierta) · media · antes del 20/11/2026** — A partir del 1/1/2027, ¿los expedientes nuevos se numeran desde E270001, o se continúa la numeración de Odoo 17? En ningún caso se puede repetir un número de Odoo 17.

- Por qué: Las pruebas han gastado números: si no se cambia nada, el primer expediente de 2027 sería el E270109, y los E26 de Odoo 20 coinciden con los de Odoo 17.
- Opciones: E27 desde el 0001 / Continuar la numeración de Odoo 17 / Otra (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 los expedientes se numeran con E, el año y 4 cifras (por ejemplo E261280).
- Mientras tanto: Numeración E26xxxx de pruebas; el cambio se hace en el arranque.
- Bloquea: F15 · con Belal

## Belal
### Etapa 0 Partes y datos maestros
**F0-B01 · alta · antes del 30/10/2026** — ¿Desde qué antigüedad de actividad se migra un contacto? Los demás se consultarían solo en Odoo 17.

- Por qué: Hay unos 21.600 contactos activos y no se ha medido cuántos tienen uso reciente; migrarlos todos alarga la carga y la limpieza de duplicados. Bloquea la carga de contactos (F2).
- Opciones: Con actividad desde el 1/1/2025 / Con actividad desde el 1/1/2024 / Todos los activos, sin límite de antigüedad / Otra fecha (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 hay expedientes de las series E21 a E26. No se ha medido cuántos contactos tienen actividad reciente.
- Mientras tanto: No se migra nada. El histórico sigue consultable en Odoo 17 y el criterio figura como «pendiente de decisión».
- Bloquea: F2, F15

**R-A4 (ya abierta) · alta · antes del 30/10/2026** — ¿Qué contactos de Odoo 17 se pasan a Odoo 20 para el arranque (qué tipos de contacto) y van con sus direcciones de entrega y recogida (almacenes)?

- Por qué: Sin clientes, agentes, navieras, transportistas y agentes de aduanas reales no se puede abrir ningún expediente real; hoy boss20 solo tiene 2 clientes y 8 proveedores reales. La oferta elige la entrega entre las direcciones del destinatario y la recogida entre las del expedidor, y el transporte terrestre se tarifica según esa dirección. Bloquea la carga de contactos (F2), la operación en pruebas (F14) y el arranque (F15).
- Opciones: Todos los tipos con actividad (clientes, proveedores, agentes, cliente + proveedor, expedidores y destinatarios españoles y extranjeros, acreedores), con todas sus direcciones de entrega y recogida / Solo clientes, proveedores, agentes y transportistas, con sus direcciones; expedidores, destinatarios y acreedores se crean cuando hagan falta / Solo clientes, proveedores, agentes y transportistas, sin direcciones: las direcciones se crean al hacer cada oferta / Otra selección (indicar qué tipos y si van con sus direcciones)
- Hoy en Odoo 17: Hoy en Odoo 17 hay unos 21.600 contactos activos. El tipo se marca con 8 valores (Pendiente, Cliente, Agente, Proveedor, Cliente + Proveedor, Shipper/Consignee extranjero, Shipper/Consignee español y Acreedor) y con casillas de rol (agente, transportista, agente de aduanas, camionero, aerolínea, expedidor/destinatario, proveedor).
- Mientras tanto: No se carga ningún contacto ni dirección de Odoo 17. boss20 sigue con los contactos dados de alta a mano, las direcciones se crean desde la oferta y la migración figura como «pendiente de decisión de Belal».
- Bloquea: F2, F14, F15

**F0-B02 · alta · antes del 04/11/2026** — Los contactos de Odoo 17 que en realidad son lugares (ciudades o códigos postales con el tipo «Pendiente»), ¿se dejan fuera de la migración?

- Por qué: Hay lugares mezclados con empresas: si se migran, ensucian la búsqueda de clientes y proveedores en las ofertas. Afecta a la carga de contactos (F2).
- Opciones: Sí, se excluyen todos / Se revisan uno a uno antes de decidir / Se migran igual
- Hoy en Odoo 17: Hoy en Odoo 17 hay contactos tipo lugar con el tipo «Pendiente», por ejemplo «338 - Huai An City» o «08510 - RODA DE TER».
- Mientras tanto: No se carga ninguno. La lista de contactos tipo lugar se prepara solo para revisarla.
- Bloquea: F2

**F0-B04 · alta · antes del 04/11/2026** — ¿Se migran desde Odoo 17 las cuentas bancarias de los proveedores?

- Por qué: Sin la cuenta bancaria del proveedor no se pueden preparar pagos ni remesas desde Odoo 20. Son datos sensibles y Ángel tiene que estar de acuerdo con la carga. Bloquea F2 y después los pagos (F8).
- Opciones: Sí, de todos los proveedores migrados / Solo de los proveedores con facturas en 2026 / No; se dan de alta a mano la primera vez que se paga
- Hoy en Odoo 17: Hoy en Odoo 17 una automatización impide contabilizar la factura de un proveedor que cobra por transferencia o remesa si no tiene cuenta bancaria. No está verificado, pero las remesas parecen hacerse fuera de Odoo.
- Mientras tanto: No se carga ninguna cuenta bancaria. El pago a proveedores queda «pendiente de decisión» y nunca se envía nada al banco.
- Bloquea: F2, F8, F15 · con Ángel

**F0-B05 · alta · antes del 04/11/2026** — Al migrar, ¿se agrupan en una misma familia las distintas empresas de un mismo transportista (por ejemplo, las cinco de MSC) para que compartan sus tarifas?

- Por qué: Si una tarifa o una factura llega a nombre de MSC Suiza o MSC EE. UU. y no está en la familia MSC, no casa con las tarifas de MSC. Hoy ningún contacto tiene familia. Afecta a F2.
- Opciones: Sí, todas las navieras y aerolíneas que tengan varias empresas / Solo MSC por ahora; las demás cuando aparezcan / No agrupar: cada empresa con sus propias tarifas
- Hoy en Odoo 17: Hoy en Odoo 17 MSC son cinco contactos separados: España SLU, España Madrid, Portugal, Suiza y EE. UU.
- Mientras tanto: Ningún contacto tiene familia, así que las tarifas solo casan con la empresa exacta del documento.
- Bloquea: F2

**M2-F (ya abierta) · alta · antes del 04/11/2026** — ¿Se ponen todos los usuarios de BOSS en español, para que los números y las fechas salgan a la española (2.500,00)?

- Por qué: Ángel pidió los números a la española para su prueba, y hoy los usuarios están en inglés con el formato de EE. UU. Afecta a la creación de usuarios por rol (F2) y a la sesión de prueba con Ángel.
- Opciones: Sí, todos en español / Cada usuario elige su idioma / Español para todos salvo quien pida inglés
- Mientras tanto: Cada usuario conserva su idioma actual (inglés) y no se cambia el de nadie sin decisión.
- Bloquea: F2

### Etapa 1 Oferta
**F0-B06 · baja · antes del 13/11/2026** — Un expediente marítimo con forma de carga «terrestre» (caso E260010), ¿es un caso válido o el sistema debe impedirlo?

- Por qué: Hoy el sistema acepta esa combinación sin avisar, y no se sabe si es un error de datos o un caso real. Hay que saberlo antes de probar exportación, grupaje y terrestre (F12).
- Opciones: Impedirlo: el modo y la forma de carga deben coincidir / Avisar sin impedir / Es un caso válido (explicar cuál)
- Mientras tanto: El sistema la acepta como hoy, sin aviso ni bloqueo, y E260010 queda como caso por revisar.
- Bloquea: F12

### Etapa 4 Documentos
**F0-B07 · media · antes del 11/11/2026** — La carpeta de documentos de cada expediente, ¿se construye como un módulo aparte o dentro del módulo que hoy imprime los documentos?

- Por qué: Decide cómo se organiza el archivo por expediente y cómo se garantiza que el cliente solo vea lo publicado. Bloquea el diseño de F6.
- Opciones: Módulo aparte (propuesta del plan: separa archivo e impresión) / Dentro del módulo de impresión de documentos
- Hoy en Odoo 17: Hoy en Odoo 17 cada adjunto de un expediente o de una partida se archiva automáticamente en la carpeta «Expedientes».
- Mientras tanto: No hay carpeta por expediente. Los documentos se adjuntan al expediente y el portal publica solo lo que se elige, como hoy.
- Bloquea: F6

**F0-B08 · media · antes del 11/11/2026** — ¿Cómo deben llegar al expediente los correos y documentos de navieras, agentes y clientes?

- Por qué: Define el diseño del archivo de documentos (F6) y la infraestructura de correo que hace falta en el arranque (F15). Cambia la forma de trabajar de los operativos, por eso Cristina tiene que estar de acuerdo.
- Opciones: Una dirección de correo por expediente / Una dirección por carpeta o tipo de documento / Desde Outlook, con el complemento de Odoo / Subida manual por el operativo
- Hoy en Odoo 17: Hoy en Odoo 17 no hay dirección de correo por expediente. Las ofertas se envían desde Outlook y el correo se sube al registro.
- Mientras tanto: No hay entrada de correo: los documentos se suben a mano al expediente.
- Bloquea: F6, F15 · con Cristina

**F0-B09 · baja · antes del 20/11/2026** — ¿Se migran a Odoo 20 los documentos históricos de los expedientes de Odoo 17 (unos 49.700)?

- Por qué: Un expediente nuevo puede necesitar documentos de uno antiguo (envíos repetidos, reclamaciones, inspecciones), pero migrarlos todos es un trabajo grande del arranque (F15).
- Opciones: No: se consultan en Odoo 17 en solo lectura (propuesta del plan) / Solo los de los expedientes que sigan abiertos el 1/1 / Todos
- Hoy en Odoo 17: Hoy en Odoo 17 la carpeta «Expedientes» guarda unos 49.700 documentos desde enero de 2024, enlazados al expediente o a la partida; pocos tienen tipo.
- Mientras tanto: No se migra ningún documento: siguen en Odoo 17.
- Bloquea: F15

### Etapa 7 Proveedores
**F0-B10 · media · antes del 06/11/2026** — ¿Se activa ya en boss20 la descarga diaria automática de los tipos de cambio del Banco Central Europeo?

- Por qué: Los costes en dólares se pasan a euros con el tipo del día, pero la tarea diaria está apagada y el tipo está parado en el último cargado. Las desviaciones y las facturas en USD saldrían con tipos viejos (F8, F9).
- Opciones: Sí, ya (es una llamada externa que solo descarga tipos públicos) / Solo a partir del arranque / No; los tipos se cargan a mano
- Hoy en Odoo 17: Hoy en Odoo 17 los tipos llegan cada día del BCE y cada expediente guarda los tipos de su fecha importante y, si se quiere, los de la naviera.
- Mientras tanto: La tarea diaria sigue apagada. El sistema usa el último tipo cargado y los tipos se cargan a mano cuando hace falta.
- Bloquea: F8, F9

### Etapa P Proyecto y arranque
**F0-B11 · alta · antes del 30/10/2026** — El plan completo necesita unas 790 horas (estimación del plan) y un solo desarrollador tiene unas 270 hasta el 31/12. ¿Qué salida eliges?

- Por qué: Incluso el mínimo para arrancar (entre 450 y 575 h) no cabe. Sin esta decisión, cada fase se planifica sobre una fecha que no se puede cumplir. Afecta al orden y a las fechas de F5 a F16.
- Opciones: Segundo desarrollador / Arranque por tráficos: el 1/1 funciona en Odoo 20 solo lo que se elija en F0-B13; el resto sigue unas semanas en Odoo 17 / Mover la fecha de arranque (indicar la nueva) / Una mezcla (indicar)
- Mientras tanto: Se sigue el orden recomendado (F1, luego F2 y F4, luego F5 a F10) con las fechas actuales. Las fases de tráficos, agentes, consolidación y gastos quedan «pendiente de decisión de Belal», sin fecha comprometida.
- Bloquea: F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15, F16

**F0-B12 · alta · antes del 30/10/2026** — En las semanas del 2 al 15 de noviembre faltan unas 59 h y 43 h de desarrollo. ¿Qué se hace?

- Por qué: En esas semanas coinciden los contactos, la base legal de la factura y el ciclo del expediente. Si no se decide, la entrega del 20/11 quedará incompleta sin saber qué falta.
- Opciones: Aplazar a diciembre la factura en euros de ofertas en dólares (quebranto), el almacenaje especial y el precio para varios envíos, y los informes de rentabilidad, con el acuerdo de Ángel y Cristina en lo que es de cada uno / Aceptar una entrega parcial el 20/11 / Cubrirlo con un segundo desarrollador / Otra cosa (indicar)
- Mientras tanto: Las tareas siguen planificadas como hoy, con el déficit a la vista. No se aplaza nada sin tu decisión.
- Bloquea: F2, F3, F4, F5

**F0-B13 · alta · antes del 30/10/2026** — ¿Qué tiene que funcionar obligatoriamente en Odoo 20 el 1/1/2027?

- Por qué: Con la capacidad actual no cabe todo. Esta decisión fija qué fases se terminan antes del arranque y cuáles después, y qué se prueba en diciembre (F14). Los agentes (F0-B17), las consolidaciones (M2-I, de Cristina) y los gastos de empleados (P39, de Ángel) se deciden aparte.
- Opciones: Solo el núcleo: importación marítima FCL con DUA, aéreo (importación y exportación), proveedores, facturación, cobros, pagos y cierres / El núcleo más la exportación marítima, el grupaje y el terrestre / Otra combinación (indicar)
- Mientras tanto: Solo lo que el plan llama núcleo mínimo se planifica con fecha. Lo demás queda sin fecha y marcado «pendiente de decisión de Belal».
- Bloquea: F11, F12, F14, F15

**F0-B14 · alta · antes del 30/10/2026** — ¿Aceptas que la red de seguridad del proyecto sean las comprobaciones que se ejecutan en boss20, y que las pruebas internas de los módulos (sin ejecutar desde el 27/10) queden solo como referencia?

- Por qué: Hoy no hay ninguna prueba de punta a punta que funcione sobre lo desplegado, y cuatro módulos no tienen pruebas propias. F1 construye esa prueba en boss20.
- Opciones: Sí / No: hay que volver a ejecutar también las pruebas de los módulos (requiere una excepción a la política del 27/10)
- Mientras tanto: Se aplica la política del 27/10: solo comprobaciones en boss20. Las pruebas de los módulos no se ejecutan.
- Bloquea: F1

**F0-B15 · alta · antes del 30/10/2026** — Hasta que se decida la base de producción, ¿las pruebas pueden seguir contabilizando en boss20 facturas, abonos y pagos marcados como prueba?

- Por qué: Tu política del 27/10 lo permite, pero la tarea del escenario contable de Ángel dice «nunca en los libros reales de boss20 antes del 1/1». Cada prueba contabilizada deja asientos de 2026 y gasta numeración si boss20 acaba siendo la base real.
- Opciones: Sí, como permite la política del 27/10 / No: las comprobaciones se deshacen al terminar y los recorridos en pantalla paran antes de contabilizar / Sí, pero solo hasta una fecha (indicar)
- Mientras tanto: Las comprobaciones automáticas se deshacen al terminar y no dejan asientos. Los recorridos en pantalla paran antes de contabilizar.
- Bloquea: F1, F14 · con Ángel

**F0-B16 · alta · antes del 04/11/2026** — ¿boss20 será la base de producción desde el 1/1/2027, anulando antes las pruebas, o se arranca en una base nueva y limpia?

- Por qué: boss20 ya tiene facturas, abonos y pagos de prueba de 2026 y 108 números de expediente gastados. Si se activa VERI*FACTU en una base que luego es la real, su cadena de registros empezaría con facturas de prueba. Bloquea VERI*FACTU o SII en modo de pruebas (F4) y el arranque (F15).
- Opciones: boss20, anulando antes las pruebas contabilizadas por las vías normales de Odoo / Una base nueva y limpia con la configuración de boss20 / Decidirlo antes de la operación en pruebas (indicar fecha)
- Mientras tanto: boss20 sigue como base de desarrollo y pruebas. No se instala VERI*FACTU ni SII y no se activa nada con efectos externos.
- Bloquea: F1, F4, F14, F15 · con Ángel

**F0-B17 · media · antes del 06/11/2026** — ¿La liquidación de los expedientes de agente (profit share, fletes collect o prepaid, varios pagadores en un expediente) entra antes del 1/1/2027?

- Por qué: Es una fase grande que compite por la misma capacidad. Si no entra, hay que saber dónde se llevan esos expedientes en enero (F13, F14).
- Opciones: Sí, antes del arranque / No: los expedientes de agente siguen unas semanas en Odoo 17 después del 1/1 / Solo una parte (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 BOSS factura el profit share al agente (o lo pone en negativo en su factura) en USD y registra los abonos de los agentes.
- Mientras tanto: La fase queda sin fecha comprometida. Un expediente de agente se puede crear, pero su profit share no se liquida en Odoo 20.
- Bloquea: F13, F14 · con Cristina

**F0-B19 · media · antes del 11/11/2026** — Los expedientes que sigan abiertos el 1/1, ¿se pasan a Odoo 20 o se terminan en Odoo 17?

- Por qué: Si se terminan en Odoo 17, habrá dos sistemas a la vez y cierres con facturas repartidas entre ambos. Si se pasan, hacen falta la migración y su ensayo (F15). Qué cuenta como expediente «abierto» lo decide Cristina aparte.
- Opciones: Se pasan todos a Odoo 20, con lo pendiente de comprar y de facturar / Se terminan en Odoo 17 (los dos sistemas conviven unas semanas) / Depende del tráfico (indicar)
- Mientras tanto: No se carga ningún expediente; solo se prepara la lectura de Odoo 17. La decisión figura como «pendiente de decisión de Belal y Cristina».
- Bloquea: F15 · con Cristina

**F0-B21 · media · antes del 11/11/2026** — ¿Dónde se ensaya la migración de los expedientes abiertos: en boss20 deshaciendo todo al terminar, o en una copia temporal en el servidor como excepción a la política del 27/10?

- Por qué: La tarea de ensayo habla de una copia local, y la política del 27/10 prohíbe copias y pruebas locales. Un ensayo deshecho al final puede medir mal los tiempos del cambio (F15).
- Opciones: En boss20, deshaciendo todo al terminar / En una copia temporal en el servidor, borrada al terminar (sería una excepción a la política del 27/10) / Otra opción (indicar)
- Mientras tanto: Se aplica la política vigente: el ensayo se hace en boss20 deshaciendo todo al terminar, sin ninguna copia.
- Bloquea: F15

**F0-B22 · media · antes del 11/11/2026** — ¿Por qué servidor y con qué dominio enviará Odoo 20 los correos de BOSS (ofertas, facturas, avisos, portal)?

- Por qué: Sin servidor de salida no sale ningún correo desde Odoo 20. Se diseña ahora (F6) y se activa en el arranque (F15).
- Opciones: El proveedor de correo actual de BOSS, con su dominio (indicar cuál) / Un servicio de envío aparte, con el dominio de BOSS / Otro (indicar)
- Hoy en Odoo 17: Hoy Odoo 17 está alojado en la plataforma de Odoo y usa sus direcciones genéricas de respuesta y de rebote; las ofertas se envían desde Outlook.
- Mientras tanto: boss20 no tiene servidor de correo y no se envía nada a clientes ni a proveedores.
- Bloquea: F6, F15

**F0-B23 · media · antes del 11/11/2026** — ¿Qué dominio usarán las direcciones de entrada de Odoo 20 (por ejemplo, para recibir facturas de proveedor o documentos de un expediente)?

- Por qué: Sin un dominio de entrada no funciona ninguna dirección que reciba correo en Odoo. Ángel decide aparte si las facturas de proveedor entran por correo. Afecta al diseño de F6 y al arranque (F15).
- Opciones: Un subdominio solo para Odoo / El dominio principal de BOSS, con buzones que Odoo lee / Ninguna entrada de correo de momento
- Hoy en Odoo 17: Hoy en Odoo 17 no hay servidor de correo entrante propio y la dirección del proyecto «Facturas de proveedores» está inactiva; esas facturas se controlan en ese proyecto, con una tarea por factura.
- Mientras tanto: No hay entrada de correo: facturas y documentos se suben a mano.
- Bloquea: F6, F15

**F0-B24 · media · antes del 13/11/2026** — Cuando la base tenga datos reales, ¿se hacen copias de seguridad automáticas de la base y de sus ficheros? ¿Desde cuándo?

- Por qué: La regla de trabajo actual prohíbe las copias, pero con datos reales una avería sin copia haría perder contactos, expedientes y contabilidad. El calendario prevé copias diarias con restauración probada antes de la entrega del 20/11, la operación en pruebas las pide para empezar, y el cambio (F15) necesita un plan de vuelta atrás.
- Opciones: Sí, diarias, guardadas fuera del servidor y con restauración probada, desde que haya datos reales (contactos migrados y operación en pruebas) / Sí, diarias, guardadas fuera del servidor y con restauración probada, solo desde el arranque del 1/1 / Sí, diarias en el mismo servidor / No
- Hoy en Odoo 17: Hoy Odoo 17 está alojado en la plataforma de Odoo; no se ha comprobado su política de copias.
- Mientras tanto: Sigue la regla actual: no se hace ninguna copia, y la tarea de copias automáticas queda «pendiente de decisión».
- Bloquea: F14, F15

**F0-B25 · media · antes del 20/11/2026** — ¿En qué fecha se activa el envío real de correo desde Odoo 20?

- Por qué: Durante las pruebas no debe salir nada a clientes ni a proveedores, y la activación tiene que estar en la lista de control del arranque (F15).
- Opciones: El 1/1/2027, con el arranque / Al empezar la operación en pruebas, solo a direcciones internas de BOSS / Otra fecha (indicar)
- Mientras tanto: El correo sigue apagado y no sale ningún correo de boss20.
- Bloquea: F15

**F0-B26 · media · antes del 20/11/2026** — En el arranque, ¿cómo se activan las tareas automáticas que hoy están apagadas (18 tareas programadas, sincronización bancaria, reclamación de cobros y, si no se ha activado antes, la de tipos de cambio)?

- Por qué: Al activarlas empiezan los envíos automáticos, y algunas mandan datos a servicios externos (banco, reclamaciones). Hoy están apagadas para que nada salga durante las pruebas (F15). La de tipos de cambio se decide antes en F0-B10.
- Opciones: Todas el 1/1, con una lista de control firmada por Belal y Ángel / Escalonadas durante la primera semana, una a una con la lista de control / Otra opción (indicar)
- Hoy en Odoo 17: Hoy en Odoo 17 hay tareas programadas que envían avisos por correo a los operativos (expedientes sin revisar, entregados y sin cerrar, pendientes de facturar o de cerrar a fin de mes).
- Mientras tanto: Todas siguen apagadas en boss20.
- Bloquea: F15 · con Ángel

**F0-B27 · media · antes del 20/11/2026** — ¿Cuándo se deja de registrar operaciones nuevas en Odoo 17?

- Por qué: Desde ese momento todo se registra en Odoo 20. La carga final de diferencias y la conciliación del arranque dependen de esa hora (F15). La lista de control del cambio la aprueban también Cristina (operaciones) y Ángel (contabilidad).
- Opciones: El 31/12/2026 a las 18:00 (propuesta del calendario) / Otra fecha y hora (indicar)
- Mientras tanto: La hora del calendario es solo una propuesta y figura como «pendiente de decisión».
- Bloquea: F15 · con Cristina

