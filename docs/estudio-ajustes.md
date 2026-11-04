# Estudio: ajustes de BOSS en Odoo 20 (04/11/2026)

Petición de Belal (04/11): que todo lo que cambia con el tiempo se gestione desde **Ajustes** (`/odoo/settings`), con una
pestaña por módulo o grupo homogéneo de parámetros, para que la dirección cambie el sistema sin tocar código.

## 1. Qué hay hoy

Inventario de los siete módulos (`boss_services`, `boss_pricing`, `boss_pricing_sale`, `boss_expediente`,
`boss_documents`, `boss_portal`, `boss_web`), leído el 04/11/2026.

### 1a. Ajustes que ya existen (8), repartidos en dos sitios de la pestaña «Ventas»

| Ajuste | Módulo | Dónde está |
|---|---|---|
| Precio de venta por defecto = coste + % | pricing_sale | Ventas › Listas de precios |
| Tarifas de flete aprobadas al entrar | pricing | Ventas › Listas de precios |
| Documento del proveedor obligatorio | pricing | Ventas › Listas de precios |
| Coste del proveedor en otra moneda (política de cambio) | pricing_sale | Ventas › Listas de precios |
| IVA de los servicios BOSS (enlace a la tabla) | pricing_sale | Ventas › Listas de precios |
| Factura de proveedor antes que la del cliente | expediente | Ventas (detrás del IVA) |
| Aviso de días libres del contenedor (días) | expediente | Ventas (detrás del IVA) |
| Aviso de cierre de mes: copia a | expediente | Ventas (detrás del IVA) |
| Valoraciones obligatorias para el cierre | expediente | Ventas (detrás del IVA) |

Problema: ajustes de operaciones y de cierre dentro de la pestaña **Ventas**, sin orden ni agrupación; nadie los
encuentra sin saber que están ahí.

### 1b. Variables de negocio fijas en el código (cambian con el tiempo: pasan a ajustes)

| Variable | Valor hoy | Dónde | Quién la cambiaría |
|---|---|---|---|
| Días de aviso antes de que caduque una tarifa | 30 | `boss_tariff_line.EXPIRING_DAYS` | Compras |
| Validez de una tarifa de flete semanal al entrar | 7 días | `boss_supplier_price_wizard` (6) | Compras |
| Margen mínimo sin regla y tolerancia | 10 %, 10 € | `boss_margin_policy` | Ángel |
| Factores volumétricos por modo (kg por m³) | aéreo 167, carretera 333, mar 1000 | `boss_shipment_route` | Ángel |
| Días tras la entrega para cerrar (aviso) | 7 | `boss_expediente` (siguiente paso) | Cristina |
| Originales del BL house | 3 (0 si sea waybill) | plantilla HBL | Cristina |
| Lugar de emisión de los documentos house | ciudad de la compañía | plantillas | — |
| Reparto de costes por defecto en una consolidación | peso tasable | `allocation_basis` default | Cristina |
| Texto legal de los suplidos en la factura | art. 78.Tres.3º Ley 37/1992 | `boss_invoice_services` | Ángel |
| Fecha de la operación en la factura | llegada (importación) / salida (resto) | `_boss_operation_date` | Ángel |
| Límites del portal (contenedores por línea, expedientes listados) | 99, 200 | `boss_portal` | técnico (se deja) |
| Días que se exploran para hallar el último día libre | 120 | `boss_expediente_alerts` | técnico (se deja) |

### 1c. Listas de servicios fijas en el código (cambian cuando cambia el catálogo: pasan a datos del servicio)

| Lista | Códigos hoy | Uso | Propuesta |
|---|---|---|---|
| Servicios que se compran al handler aéreo | HAN, ALM, AWB, ETX, X-R | proveedor = handler | casilla «Se compra al handler» en el servicio |
| Servicios de transporte por carretera | TTE-CON, TTE-FCL | proveedor = transportista terrestre | casilla «Tramo terrestre (transportista)» |
| Servicios con aviso de días libres | DEM, OCU, DET | avisos de contenedor | se deduce: servicio por tiempo con eventos de contenedor (sin lista) |
| Gastos que van al valor en aduana | FMI/FME/FAI/FAE, THC, T3, SEG | texto para el agente | casilla «Cuenta para el valor en aduana» |
| Flete que toma la fecha de salida | FMI, FMI-LCL, FME, FME-LCL, FAI, FAE | fecha de tarifa | ya es un campo del servicio (`boss_tariff_date`); la lista solo se usa al instalar |
| Eventos por defecto del periodo (ALM, DEM, OCU, DET) | tabla por servicio y sentido | periodo de servicios por tiempo | campos «Periodo empieza/termina en (importación / exportación)» en el servicio |
| Incoterms prepaid / collect | C y D / E y F | flete del BL, reglas de margen | casilla «El vendedor paga el transporte principal» en el incoterm |

### 1d. Condiciones de estado fijas en el código (reglas de Cristina: pasan a interruptores)

- «En tránsito» avisa si faltan ATD, booking, BL/AWB máster, números de contenedor (aviso, no bloqueo).
- «Entregado» exige: ATA y descarga (importación marítima), levante si BOSS despacha, fecha y hora de recogida o entrega
  si BOSS transporta, HBL liberado en importación marítima con entrega.
- Cierre operativo exige: todo facturado, margen sin aviso o motivo, valoraciones.

El paquete 3 de `docs/paquetes-aprobacion-f0.md` ya pedía esto como **lista de condiciones que Cristina activa**.

### 1e. Lo que ya es dato (se gestiona desde menús, no desde ajustes)

Tarifas y precios de proveedor; listas de precios y plantillas de oferta; tabla de IVA; márgenes mínimos y excepciones;
operativos por cliente y tráfico; aerolíneas y handlers; puertos; tipos de contenedor; roles logísticos; catálogo de
servicios; plazos de pago y diarios; secuencias (E26xxxx); plantilla de documentos (Ajustes › General). Bien así: son
tablas, no interruptores. Lo que falta es **un sitio desde el que llegar a todas**.

### 1f. Lo que se queda en código (estructura, no negocio)

Estados y su orden, los pasos de «Siguiente paso», los campos que se congelan al cierre, los datos que un máster copia a
sus casas, la escala de valoración 0–10, la equivalencia TEU, las zonas de IVA (PRO/CAN/COM/TER), los permisos por
grupo estándar (Ajustes › Usuarios).

## 2. Propuesta

### 2a. Tres pestañas BOSS en Ajustes (una por área homogénea, no una por módulo técnico)

Odoo muestra una pestaña por aplicación; siete pestañas técnicas confundirían. Tres áreas, cada una con bloques:

**BOSS · Tarifas y precios** (`boss_pricing`, `boss_pricing_sale`, `boss_services`)
1. Tarifas de proveedor: documento obligatorio · flete aprobado al entrar · validez de la tarifa semanal · días de
   aviso de caducidad · política de cambio de moneda.
2. Precio de venta: coste + % por defecto · margen mínimo sin regla y tolerancia · enlaces a «Márgenes mínimos»,
   «Excepciones», «Listas de precios», «Plantillas de oferta».
3. Medidas del envío: factores volumétricos aéreo / carretera / mar.
4. IVA: enlace a la tabla de IVA.
5. Servicios: enlaces al catálogo y a los grupos de servicios.

**BOSS · Expedientes** (`boss_expediente`)
1. Apertura: enlaces a «Operativos por cliente y tráfico» y «Aerolíneas y handlers».
2. Estados: interruptores de las condiciones de «En tránsito» (avisar / bloquear / nada) y de «Entregado» (una
   casilla por condición).
3. Cierre: valoraciones obligatorias · días tras la entrega para avisar · factura de proveedor antes que la del cliente.
4. Avisos: días de aviso de los contenedores · copia del cierre de mes.
5. Consolidaciones: reparto de costes por defecto.

**BOSS · Documentos y portal** (`boss_documents`, `boss_portal`)
1. Documentos house: originales del BL · lugar de emisión.
2. Factura: fecha de la operación (llegada / salida / ninguna) · texto legal de los suplidos.
3. Portal: enlaces a los roles de portal y a la plantilla de correo de tarifas.

### 2b. Reglas de diseño

- **Interruptor** (ajuste) solo para un valor único de la compañía que cambia con el tiempo.
- **Tabla** (menú de datos) para listas: precios, reglas, excepciones, equivalencias. Desde Ajustes, un enlace.
- **Campo del servicio** para lo que depende del servicio: así un servicio nuevo se configura sin código.
- Cada ajuste con su ayuda (de dónde sale la regla y quién la decidió) y un valor por defecto igual al actual: al
  desplegar, nada cambia de comportamiento.
- Los interruptores de condiciones de estado nacen con los valores de hoy (lo que Cristina escribió activado, el resto
  desactivado).

### 2c. Fases

| Fase | Contenido | Esfuerzo |
|---|---|---|
| 1 | Las tres pestañas; mover los 8 ajustes; pasar a ajustes las variables de 1b (salvo las técnicas) | M |
| 2 | Las listas de servicios de 1c a campos del servicio y del incoterm | M |
| 3 | Interruptores de las condiciones de estado (1d) | S–M |
| 4 | Enlaces a las tablas (1e), página «Ajustes» en la guía (ES/EN), comprobación con evidencia | S |

Cada fase se despliega sola, con su check y sin cambiar el comportamiento actual por defecto.

---

## English summary

Belal (04/11/2026): every parameter that changes over time must be managed from Settings, one tab per homogeneous
area, so that management changes the system without code. Inventory of the seven modules: 8 settings exist, scattered
in the Sales tab; 12 business variables are fixed in code (tariff expiry warning 30 days, weekly rate validity, default
margin 10 % / 10 € tolerance, volumetric factors 167/333/1000, 7 days to close, HBL originals, place of issue, default
cost split, legal text of paid-on-behalf amounts, operation date rule); 7 service lists are fixed in code (handler
services, road services, free-time alert services, customs-value charges, freight ETD codes, default period events,
prepaid/collect incoterms); the status conditions (in transit, delivered, close) are fixed rules of Cristina. Proposal:
three Settings tabs («BOSS · Pricing», «BOSS · Files», «BOSS · Documents and portal») with blocks; switches for single
company values, data tables for lists (with links from Settings), service fields for anything that depends on the
service; defaults equal to today's behaviour. Four phases, each deployable on its own with its check.
