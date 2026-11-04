Lo que la dirección de BOSS puede cambiar sin programar: valores que cambian con el tiempo, reglas de los estados del
expediente y datos de los servicios. Se gestiona desde **Ajustes** (`/odoo/settings`) y desde las tablas que se abren
con sus enlaces.

> Las capturas son de la interfaz en inglés; entre paréntesis va el nombre en inglés de cada ajuste. La columna **Valor
> actual** es el de boss20 el 4/11/2026: en los ajustes nuevos coincide con lo que el sistema hacía antes de existir el
> ajuste. Los porcentajes de venta y margen no se publican en esta guía: se ven en Ajustes.

## Dónde están

En **Ajustes** hay tres pestañas de BOSS, una por área:

| Pestaña | Qué se configura |
|---|---|
| **BOSS · Tarifas y precios** (BOSS · Pricing) | Tarifas de proveedor, precio de venta y margen, medidas del envío, IVA |
| **BOSS · Expedientes** (BOSS · Files) | Apertura, condiciones de estado, cierre y avisos |
| **BOSS · Documentos** (BOSS · Documents) | BL y AWB house, factura al cliente |

Cada ajuste explica debajo de su nombre qué hace y de dónde sale la regla. Tras cambiar algo, pulse [[Guardar]] (Save)
arriba; [[Descartar]] (Discard) deshace lo no guardado.

## BOSS · Tarifas y precios

![Ajustes › BOSS · Tarifas y precios › Tarifas de proveedor](img/45-ajustes-tarifas-proveedor.png)

### Tarifas de proveedor

| Ajuste | Valor actual | Qué hace |
|---|---|---|
| **Documento del proveedor obligatorio** (Supplier document required) | Activado | Una tarifa no se envía a aprobar sin el documento del proveedor adjunto: todo precio es trazable. |
| **Fletes aprobados al introducirlos** (Freight rates approved on entry) | Activado | El flete semanal tecleado desde una oferta queda aprobado por quien lo introduce: una oferta urgente no espera a un aprobador. Desactivado: espera a un aprobador de tarifas. |
| **Validez de una tarifa de flete introducida desde una oferta** (Validity of a freight rate entered from a quotation) · Días | 7 | Días de validez del flete semanal desde su inicio. |
| **Avisar antes de que caduque una tarifa** (Warn before a tariff expires) · Días | 30 | Un precio que caduca dentro de esos días sale como «Caduca pronto» en las listas y en el espacio de trabajo. |
| **Coste de proveedor en otra moneda** (Supplier cost in another currency) | Tipo de cambio de Odoo de la fecha de la oferta | Qué hacer si el precio del proveedor está en otra moneda que la oferta. La otra opción, «No convertir», deja el coste pendiente. |

Enlaces: **Tarifas de proveedor** y **Precios de proveedor**.

Ejemplo: una naviera cambia el flete cada dos semanas y BOSS quiere que la tarifa tecleada valga ese tiempo →
**Validez…** = 14. Las tarifas ya introducidas conservan sus fechas.

### Precio de venta y margen

![Ajustes › BOSS · Tarifas y precios › Precio de venta y margen y Medidas del envío](img/46-ajustes-precio-margen-medidas.png)

| Ajuste | Qué hace |
|---|---|
| **Venta por defecto de los servicios BOSS** (Default sale price of BOSS services) · Coste + % | Venta propuesta = coste previsto + este %, como regla de la lista de precios por defecto. Mandan antes el precio pactado del cliente y el precio tecleado en la línea. 0 lo desactiva. |
| **Margen mínimo sin regla** (Minimum margin without a rule) · % del coste | Margen mínimo de un grupo o servicio sin regla propia (regla base de Odoo 17). |
| **Margen mínimo sin regla** · Tolerancia | Se acepta sin aviso un margen hasta este importe por debajo del mínimo. |

Enlaces: **Listas de precios**, **Plantillas de oferta**, **Márgenes mínimos** y **Excepciones de margen mínimo**. Las
reglas por grupo de servicios, tipo de envío y cliente están en esas dos últimas tablas (ver
[Precio de venta e IVA](#/venta-iva)). En la oferta el margen mínimo **avisa**, no bloquea. En el cierre operativo, un
margen bajo pide un motivo según la condición **Margen bajo justificado** (ver más abajo).

### Medidas del envío

| Ajuste | Valor actual | Qué hace |
|---|---|---|
| **Factores de peso volumétrico (kg por m³)** (Volume weight factors) · Aéreo | 167 | Peso tasable = el mayor entre peso bruto y volumen × factor. |
| … · Terrestre | 333 | Para todo tramo por carretera, sea cual sea el modo principal. |
| … · Marítimo | 1000 | 1 t = 1 m³ (W/M). |

Un documento de proveedor que indique su propio factor lo conserva. Enlaces: **Puertos y aeropuertos** y **Servicios**.

> Cambiar un factor recalcula el peso tasable de **todas** las ofertas y expedientes con medidas, también los cerrados
> (ver «A qué afecta un cambio» más abajo). Hágalo solo con el visto bueno de Ángel.

### IVA

**IVA de los servicios BOSS** abre la **Tabla de IVA BOSS**: el impuesto de Odoo de cada caso (clase de IVA del
servicio y zona del cliente). Un caso sin impuesto deja el IVA pendiente y la oferta no se puede enviar ni confirmar.
La mantiene contabilidad (ver [IVA y monedas](#/iva-moneda)).

## BOSS · Expedientes

### Apertura del expediente

- **Quién trabaja en un expediente** (Who works on a file): enlaces a **Operativos por cliente y tráfico** (operativo
  propuesto al abrir), **Aerolíneas y handlers** (handler de cada aerolínea en cada aeropuerto) y **Roles logísticos**.
- **Consolidaciones: costes compartidos repartidos por** (Consolidations: shared costs split by) — valor actual **Peso
  tasable (W/M)**; también peso bruto, volumen, partes iguales o parte manual. Se propone en cada máster nuevo; el
  máster puede cambiarlo.

### Condiciones de estado

![Ajustes › BOSS · Expedientes › Condiciones de estado](img/47-ajustes-condiciones-estado.png)

Cada condición tiene uno de tres niveles:

| Nivel | Qué pasa si falta el dato |
|---|---|
| **Obligatorio (detiene el paso)** (Required) | El paso no se hace. Un mensaje dice qué falta. |
| **Solo aviso** (Warning only) | El paso se hace y queda una nota en el historial del expediente con lo que faltaba, el usuario y la hora. |
| **No se comprueba** (Not checked) | El paso se hace sin decir nada y el dato deja de aparecer en el **Siguiente paso**. |

| Paso | Condición | Valor actual | Cuándo se aplica |
|---|---|---|---|
| **Para salir («En tránsito»)** | ATD · Booking · BL o AWB máster · Números de contenedor | Solo aviso | Booking y máster en marítimo y aéreo; números en FCL con contenedores sin número |
| **Para entregar («Entregado»)** | ATA (importación) · Descarga del buque · Levante aduanero · Fecha y hora de recogida · Fecha y hora de entrega · BL house liberado | Obligatorio | ATA en importación; descarga en importación marítima; levante si BOSS despacha; fechas si BOSS recoge o entrega; BL house en importación marítima con entrega |
| **Para cerrar operaciones** | Todo facturado · Margen bajo justificado | Obligatorio | Todo expediente |

Ejemplos:

- **Obligatorio**: «ATD» en Obligatorio. Un expediente sin salida real no pasa a «En tránsito» y el mensaje dice
  «E26… aún no puede salir, le falta: ATD (salida real) (obligatorio en Ajustes › BOSS · Expedientes).»
- **Solo aviso**: «BL house liberado» en Solo aviso. El expediente pasa a «Entregado» y en su historial queda, con el
  usuario y la hora, «Entregado sin: HBL liberado o sea waybill. Es un aviso: complételos cuando se conozcan.»
- **No se comprueba**: «Descarga del buque» en No se comprueba, para un puerto donde BOSS no registra la descarga. Ni se
  pide ni aparece en el siguiente paso.

Un cambio de nivel vale para los pasos que se hagan después: un expediente que ya salió o se entregó no vuelve atrás.

### Cierre del expediente

| Ajuste | Valor actual | Qué hace |
|---|---|---|
| **Valoraciones obligatorias para el cierre operativo** (Ratings required to close operations) | Activado | Hay que valorar de 0 a 10 al cliente y a cada proveedor antes de cerrar operaciones. |
| **Días para cerrar tras la entrega** (Days to close after the delivery) · Días | 7 | Pasados esos días, el siguiente paso avisa de que el expediente debe cerrarse. |
| **Factura de proveedor antes de la de cliente** (Supplier bill before the customer invoice) | Bloquear el pago (contabilizar permitido) | Qué pasa con una factura de proveedor de un servicio aún no facturado al cliente. |

### Avisos (actividades de Odoo, sin correo)

| Ajuste | Valor actual | Qué hace |
|---|---|---|
| **Aviso de días libres del contenedor** (Container free-time alert) · Días laborables | 3 | Actividad al operativo esos días antes del último día libre de cada contenedor, otra ese día y una al comercial el primer día con coste. 0 lo desactiva. |
| **Aviso de cierre de mes** (Month-close reminder) | La persona elegida | El último día del mes cada responsable recibe una actividad por expediente pendiente de facturar o cerrar; esta persona, el resumen. Vacío: sin resumen. |

## BOSS · Documentos

![Ajustes › BOSS · Documentos](img/48-ajustes-documentos.png)

| Ajuste | Valor actual | Qué hace |
|---|---|---|
| **Originales del BL house** (Original house B/Ls) · Originales | 3 | Originales impresos en el BL house. Un sea waybill imprime «express», cero. |
| **Lugar de emisión** (Place of issue) | Vacío = ciudad de la compañía | Lugar impreso en el BL y el AWB house. |
| **Fecha de la operación en la factura** (Operation date on the invoice) | Activado | La factura conserva su fecha de emisión e imprime aparte la fecha de la operación del expediente: llegada en importación, salida en el resto (RD 1619/2012 art. 6). Desactivado: vacía salvo que se teclee. |
| **Mención de los suplidos** (Mention of amounts paid on behalf) | Vacío = texto estándar | Texto de la factura que refactura aranceles, IVA de importación y otros suplidos (art. 78.Tres.3º Ley 37/1992), en el idioma del cliente. |

Estos ajustes se aplican a los documentos que se impriman después del cambio; un PDF ya enviado no cambia.

## Servicios e Incoterms

### Crear un servicio nuevo

En **Tarifas y proveedores → Servicios** no hay botón Nuevo: un servicio BOSS nace de otro parecido.

1. Abra el servicio más parecido (por ejemplo DEM para otra demora) y use **⚙ → Duplicar**.
2. Cambie **Nombre** y **Referencia interna** (el código del servicio).
3. Pestaña **Precios BOSS** (BOSS pricing), grupo **Cómo se cotiza**:
   - **Origen del coste** (Cost source): tarifa de proveedor, importe manual, honorario propio de BOSS o pendiente de
     decisión de negocio.
   - **Forma de cálculo** (Calculation method), **Fecha de tarifa** (Tariff date), **Grupo del resumen**, **Clase de
     IVA** (VAT class) y **Suplido** (Paid on behalf).
   - **Se compra a** (Bought from): *Cualquier proveedor*; *El handler aéreo del expediente* (sigue al handler de la
     aerolínea en el aeropuerto, como HAN, ALM o AWB); *El transportista terrestre (tramo por carretera)*, cuyo
     proveedor es el transportista de la oferta y del expediente.
   - **Cuenta para el valor en aduana como** (Counts for the customs value as): Flete, THC, T3 o Seguro. Los servicios
     marcados salen en **Datos para el agente de aduanas** del expediente.
4. Si es un servicio por tiempo, añada sus líneas de **Periodo por defecto** (no se copian al duplicar).
5. Las tarifas de proveedor del servicio se introducen después (ver [Introducir una tarifa](#/tarifa-alta)).

![Servicio DEM › Precios BOSS: «Se compra a», «Cuenta para el valor en aduana como» y «Periodo por defecto»](img/49-servicio-periodo-por-defecto.png)

### Periodo por defecto de un servicio por tiempo

En un servicio con forma de cálculo **Por día con periodo libre** (almacenaje, demoras, ocupación, detención), la tabla
**Periodo por defecto (servicios por tiempo)** dice dónde empieza y termina el periodo cuando el precio del proveedor no
lo indica:

| Sentido | Forma de carga | El periodo empieza en | El periodo termina en |
|---|---|---|---|
| Importación | Vacío = cualquiera | Llegada del buque o vuelo (ATA) | Contenedor vacío devuelto (cada contenedor) |
| Exportación | Vacío | Contenedor lleno en la terminal (cada contenedor) | Salida real (ATD) |

- Una línea con forma de carga (por ejemplo LCL) manda sobre la línea sin forma de carga del mismo sentido.
- Una línea sin eventos significa «sin periodo»: el coste se teclea.
- Si el periodo corre por contenedor (eventos «cada contenedor»), el servicio recibe los **avisos de días libres**.

Ejemplo: una naviera cuenta la demora desde la descarga del buque y su tarifa no lo indica. En DEM, cambie la línea de
importación a **Descarga del buque** → **Contenedor vacío devuelto**. Vale para los cálculos que se hagan después.

### Incoterms

![Contabilidad › Configuración › Incoterms: columna «Flete»](img/50-incoterms-flete.png)

**Contabilidad → Configuración → Incoterms**, columna **Flete** (Freight): *Prepaid (en origen)* si el vendedor paga el
transporte principal (términos C y D) o *Collect (en destino)* si lo paga el comprador (términos E y F). Se propone como
**Flete pagadero** en el BL house del expediente y lo usan las reglas de margen mínimo (por ejemplo, gastos locales de
grupaje prepaid). Los Incoterms los mantiene contabilidad.

> Cambiar el flete de un Incoterm vuelve a proponerlo en **todos** los expedientes con ese Incoterm, también en los que
> alguien cambió a mano y en los cerrados (ver «A qué afecta un cambio» más abajo). Los valores actuales siguen las
> reglas Incoterms 2020: no hace falta tocarlos.

## Seguridad y buenas prácticas

### Quién puede cambiar los ajustes

- Abrir y guardar **Ajustes** exige el permiso **Administración: Ajustes**. Los valores se guardan en la compañía, que
  solo modifican los usuarios con permiso de **Administración**: un usuario sin él no ve el menú ni puede cambiar un
  ajuste por otra vía.
- Las tablas enlazadas tienen sus propios permisos: **Márgenes mínimos**, **Excepciones de margen mínimo** y
  **Periodo por defecto** los mantienen los jefes de ventas; la **Tabla de IVA BOSS** y los **Incoterms**, los jefes de
  contabilidad; las tarifas, los aprobadores de tarifas.
- Hoy los cuatro usuarios internos de boss20 son administradores. Al crear las cuentas de los operativos, deles solo los
  grupos de su trabajo (Ventas, Compras, Contabilidad), nunca **Administración**.

### A qué afecta un cambio

- La mayoría de los ajustes valen **desde que se guardan**, para los pasos, cálculos e impresiones que se hagan después:
  no cambian un expediente que ya salió, se entregó o se cerró, ni una factura emitida, ni una oferta aceptada (su copia
  congelada; ver [Cierre del expediente](#/cierre)).
- Dos excepciones cambian datos ya guardados:
  - **Factores de peso volumétrico**: se recalcula el peso tasable de todas las ofertas y expedientes, también los
    cerrados. Los importes ya facturados no cambian, pero un reparto de consolidación o un documento que se imprima
    después usará el peso nuevo.
  - **Flete de un Incoterm**: se vuelve a proponer el flete pagadero en todos los expedientes con ese Incoterm.
- Cambie estos dos solo con el visto bueno de dirección y anote el valor anterior.

### Antes de desactivar una condición

- **Todo facturado** y **Margen bajo justificado** protegen el resultado del expediente. En *Solo aviso* o *No se
  comprueba* se pueden cerrar operaciones con servicios sin facturar o con un margen bajo sin motivo escrito. El **cierre
  económico** sigue exigiendo todo facturado y el aviso de cierre de mes sigue listando esos expedientes, pero el control
  llega más tarde. Cambiarlos es una decisión de dirección (Cristina, Ángel).
- Las condiciones de **Entregado** que escribió Cristina (levante, BL house liberado, fechas) evitan dar por entregada
  una mercancía sin despacho o sin el BL liberado: no las desactive sin su visto bueno.
- Prefiera **Solo aviso** a **No se comprueba**: el paso se hace igual, pero queda constancia en el historial.

### Cómo comprobar un cambio antes de darlo por bueno

1. Anote el valor actual (esta página lo indica) y el motivo del cambio.
2. Cambie el ajuste y pulse [[Guardar]].
3. Pruébelo en un expediente u oferta **[PRUEBA]**, nunca en uno real: por ejemplo, pase un expediente de prueba a
   «En tránsito» o «Entregado» y mire el mensaje o el historial.
4. Si el resultado no es el esperado, vuelva al valor anterior y guarde.
