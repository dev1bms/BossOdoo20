# Ciclo operativo y financiero · Operational and financial cycle

Mandato de Belal (23/10/2026). Diseño: [ADR-005](adr/005-operational-and-financial-cycle.md). Este fichero es el
plan, los criterios de aceptación y el registro de progreso (un solo sitio; `plan-implementacion.md` apunta aquí).

## Objetivo
Contacts → CRM (cuando hace falta) → Quotation → Sales Order → Expediente → Purchase Orders → Customer Invoices /
Vendor Bills → Expenses / Credits → coste y rentabilidad. Odoo estándar lleva contactos, ventas, compras, facturas,
contabilidad, analítica y actividades; BOSS añade tarifas, datos del envío, enlaces y resúmenes.

## Criterios de aceptación (desde la interfaz publicada)
1. Crear cliente y proveedor con sus datos; aparecen en Clientes / Proveedores antes de su primer documento.
2. Empezar por CRM o por un presupuesto directo; los datos del envío pasan de la oportunidad al presupuesto.
3. Datos del envío y servicios; quién ejecuta cada servicio (BOSS o proveedor).
4. Coste y venta comprensibles y trazables (tarifa, documento, página, explicación).
5. Precio que falta por el camino adecuado, con aprobación.
6. Confirmar con el acuerdo guardado (foto); coste desconocido de un servicio de proveedor bloquea.
7. Expediente: datos, referencias, fechas, eventos, documentos y enlaces.
8. Pedidos de compra desde el expediente: borradores revisables, sin duplicados, confirmación humana.
9. Facturas de cliente y de proveedor.
10. Parciales, varias facturas, abonos, coste adicional.
11. Coste y rentabilidad correctos y qué falta.
12. Guía igual a las pantallas y ejemplos reproducibles (MSC, WFS, IRENEO, servicio propio).

## Plan por fases
| Fase | Resultado | Depende de | Verificación |
|---|---|---|---|
| F1 Base | habilidades, revisión, ADR-005, este plan | — | ficheros en el repo |
| F2 Contactos y CRM | roles, datos que faltan, oportunidad → presupuesto, repetir envío | F1 | test + navegador |
| F3 Ejecución y foto | BOSS / proveedor por línea, tipo de coste, bloqueo de coste desconocido, foto ampliada | F2 | test |
| F4 Expediente | modelo, creación al confirmar (una vez), analítica, partes, carga, referencias, eventos | F3 | test |
| F5 Compras | necesidades, RFQ sin duplicados, parcial, cancelación, cambio de proveedor, servicio prestado | F4 | test |
| F6 Facturas y rentabilidad | facturación por servicios, parciales, abonos, extras, bloqueo de IVA al registrar, resumen | F5 | test con asientos registrados (BD local) |
| F7 Interfaz y permisos | vistas, menús, grupos, traducción ES, 1366/1920 | F6 | navegador |
| F8 Entrega | despliegue, ejemplos DEMO, verificación en el servidor, guía ES/EN | F7 | navegador en boss20 |

## Registro de progreso
| Fecha | Qué | Dónde | Verificado |
|---|---|---|---|
| 23/10 | Habilidades `odoo-code-tracer` y `verification-before-completion` instaladas (fuentes en `.interface-design/system.md`) | `.claude/skills/` (local, fuera de Git) | lectura de SKILL.md |
| 23/10 | Revisión: boss20 tiene purchase + sale_purchase, sin project / hr_expense / stock; Odoo 17 sin compras | ADR-005 | consultas de lectura |
| 23/10 | Quién ejecuta cada servicio (BOSS / proveedor), tipo de coste, coste desconocido bloquea la aceptación (excepción con motivo por responsable de ventas), servicio añadido tras aceptar solo por acción explícita, foto con base de compra | `boss_pricing_sale` 20.0.1.6.0 | tests Odoo + migración comprobada en boss20 (S00009, S00013) |
| 23/10 | Contactos (cliente/proveedor al instante, roles logísticos, EORI, datos que faltan), oportunidad → oferta con ruta, alcance, partes, carga, contenedores y servicios pedidos; oferta repetida recotiza | `boss_expediente` | tests Odoo |
| 23/10 | Expediente: número E26xxxx, abierto una vez al aceptar (o vinculado a uno preliminar), cuenta analítica, partes, ruta, carga, contenedores, referencias, fechas, eventos, diferencias con la oferta, cierre operativo y económico separados | `boss_expediente` | tests Odoo + navegador boss20 1366/1920 |
| 23/10 | Compras: servicios a comprar con su propia base, solicitudes de presupuesto por proveedor y moneda sin duplicados (bloqueo de fila), precio protegido, «Marcar como prestado», cambio de proveedor solo sin pedido activo | `boss_expediente` | tests Odoo (pedido confirmado + factura de proveedor contabilizada en BD local) |
| 23/10 | Facturas: por servicios elegidos (hitos), segunda factura, abono, coste adicional refacturado con motivo y foto; bloqueos al contabilizar (IVA pendiente, NIF/dirección del cliente, impuesto de la factura de proveedor, factura de proveedor antes de facturar al cliente) | `boss_expediente` | tests Odoo con asientos en BD local |
| 23/10 | Rentabilidad: venta acordada, coste aceptado, compras comprometidas, coste real, pendiente, previsto, margen en la aceptación y tras costes externos, facturado, cobrado, pagado, pendiente | `boss_expediente` | tests Odoo + navegador boss20 |
| 23/10 | Ejemplos [DEMO] en boss20 (sin contabilizar ni confirmar compras): E260001 MSC marítimo (factura borrador solo THC, coste adicional OCU refacturado), E260002 WFS aéreo, E260004 IRENEO terrestre, E260003 solo servicio BOSS | `dev/demo_cycle.py` | salida del script en boss20 |
| 23/10 | Corrección: un recargo en % creado junto a su servicio base (oferta repetida) se calcula sobre él | `boss_pricing_sale` | tests Odoo + IRENEO en boss20 |
| 23/10 (2ª ronda) | Recalcular coste previsto con datos del expediente (contenedores, pesos, días por servicio, fechas reales, proveedor) con el mismo motor; historial de recálculos; venta y foto intactas; pedido confirmado marcado «a revisar» | `boss_expediente` 20.0.1.1.0 | test ALM 5→9 días (75→175 €) y 2º contenedor (THC 240→480 €); boss20 E260002 (AWB 500→620 kg, ALM +3 días) |
| 23/10 (2ª ronda) | Añadir un servicio tras la aceptación (BOSS o proveedor), con motivo y foto; fuera del margen en la aceptación | `boss_pricing_sale` 20.0.1.7.0 | test + boss20 E260003 (CSA 45 €) |
| 23/10 (2ª ronda) | Una oferta, varios expedientes (reparto de cantidades, nunca más de lo aceptado; facturación y analítica por expediente) | `boss_expediente` | test + boss20 E260009/E260010 |
| 23/10 (2ª ronda) | Reglas al contabilizar revisadas con las fuentes (P30 aviso por defecto, P31 identificación según Odoo 17 y la localización); suplidos sin pedido de compra; acceso por rol y compañía; cifras con su origen | `boss_expediente` | tests (23 métodos: 0 fallos) |
| 23/10 (2ª ronda) | Rendimiento medido en Chrome visible con sesión normal: 0,95–1,47 s hasta poder usar el formulario o la lista (5 cargas); una primera carga tras el despliegue 8,2 s (hueco de 4 s sin red ni tareas largas, no repetido). Las esperas de 20–50 s eran del panel de navegador interno oculto (`requestAnimationFrame` no se ejecuta). Descartado: el tour de bienvenida (comparación local con y sin tour, también con el paso 2 guardado) | — | `dev/perf_probe.py`, medidas en Chrome |

## Decisiones tomadas en esta fase (técnicas)
- Expediente propio (no `project`), una cuenta analítica por expediente, necesidades de compra explícitas (ADR-005).
- Pedido de compra: borrador por proveedor y moneda; confirmación y envío por una persona.
- Control de facturas de proveedor de servicios BOSS «según cantidades recibidas» (servicio prestado), reversible en
  el producto; pendiente de confirmar por Ángel (P32).

## Decisiones y requisitos citados

### Factura de proveedor y facturación al cliente (P30)

Texto de Cristina en «Nuevo Odoo.xlsx» (autora y última edición Cristina de Santisteban, 02/10/2026; la hoja no tiene
columnas de prioridad, estado, responsable ni fecha: es un **requisito escrito**, no una decisión confirmada):

- «Facturacion»!A3: «No permite pagar a proveedores o contabilizar facturas si eso no está facturado o como mínimo la
  línea puesta en caso de que sea un flete que se pague por adelantado a un agente».
- «Facturacion y costes»!A11: «no se puede soportar una factura ni pagar si no está facturado dicho concepto al cliente
  (evitar que se paguen facturas sin haber facturado)».
- Relacionado: «OPS- exptes»!A69 (cerrar contra previsiones y soportar después las facturas que cuadren sin reabrir),
  «Incidencias»!B9 (único texto sobre un coste que asume BOSS).

Práctica anterior: Odoo 17 casaba la factura de proveedor con las previsiones antes de contabilizarla (FactReader) y
pagaba por remesas; no hay constancia de un bloqueo por falta de factura al cliente. Odoo 19 lo dejó en el plan
(S5b) sin construir.

Qué se distingue en Odoo 20:

| Aspecto | Comportamiento |
|---|---|
| Orden de trabajo (facturar al cliente antes de soportar la del proveedor) | Aviso en la factura de proveedor («Antes de contabilizar o pagar») y en «Pendiente» del expediente |
| Bloqueo de contabilización y de pago | Solo si la compañía elige «Bloquear» (Ajustes › Ventas); por defecto «Solo avisar» mientras P30 siga abierta |
| «Facturado» | Factura de cliente **contabilizada** de esa línea (un borrador no cuenta); una factura parcial basta (concepto facturado) |
| Coste que asume BOSS o cubierto por el precio | Sin aviso: no se espera factura al cliente |
| Flete pagado por adelantado a un agente | Marcar «Pagado por adelantado» en el servicio: basta con la línea de venta (excepción de A3) |
| Factura de proveedor que llega antes o mucho después | Se registra siempre; con «Bloquear» queda en borrador hasta facturar al cliente. La obligación de registrar las facturas recibidas en plazo es una cuestión contable para Ángel antes de activar el bloqueo |

### Datos del cliente para contabilizar (P31)

- Ángel, reglas de IVA (31/08, `iva_rules.md`): «Falta una zona ⇒ PENDIENTE ← nunca se adivina».
- Odoo 17 (asistente de facturas, lectura de auditoría): bloquea «Any billable entity with country = Spain … or no
  country and no VAT/NIF»; no bloquea clientes extranjeros sin NIF.
- No hay decisión de Ángel sobre NIF de clientes UE (lo cubre el IVA pendiente), particulares, Ceuta/Melilla ni
  dirección.
- Odoo 20: bloquea el IVA pendiente y el cliente de España (o sin país) sin NIF ni otra identificación de la
  localización española (pasaporte, NIE, certificado de residencia, otro); la dirección se muestra como dato que falta.

### Una oferta, varios expedientes

- Propietario, 26/08/2026 (actas de Odoo 19, sin nombre): «one accepted quotation MAY create multiple Expedientes …
  Each creation allocates part (or all) of the accepted quantities/amounts; retries and concurrent users can never
  duplicate an allocation or exceed the accepted totals».
- Odoo 20: cada línea aceptada se reparte entre expedientes («Mover servicios a otro expediente»); la suma nunca supera
  la cantidad aceptada, cada expediente factura su parte y la analítica se reparte en proporción.

## Bloqueos y decisiones de negocio abiertas
Ver `docs/preguntas-abiertas.md` (P30–P39 del ciclo). No bloquean el desarrollo: las cuentas quedan como
están, el IVA de compra lo elige quien registra la factura según el documento del proveedor.

Aplicadas y pendientes de confirmar:
- Ángel: el NIF y la dirección del cliente son obligatorios para contabilizar una factura de servicios BOSS (clientes
  empresa). En Odoo 20 «es empresa» = tiene NIF.
- Ángel / Cristina: la factura de proveedor de un servicio del expediente se contabiliza después de facturarlo al
  cliente (requisito de Cristina, «Nuevo Odoo», hoja Facturación A3), salvo coste «cubierto» o «lo asume BOSS».
- Ángel (P32): control de facturas de proveedor por cantidades pedidas (estándar) o recibidas (servicio prestado):
  es un ajuste del producto, sin código.
- Numeración E26xxxx: igual que Odoo 19; mantenerla o reiniciarla al arrancar sigue abierto (Q6).

Pendiente técnico: ninguno conocido en el ciclo; el coste previsto se recalcula con los datos del expediente (ver registro).

Último commit desplegado: `fdb4cbd` (main con la revisión ALM fusionada; boss_expediente 20.0.1.2.0, boss_pricing 20.0.1.5.0, boss_pricing_sale 20.0.1.7.0), 23/10/2026. Guía publicada desde `b388a67` (`?v=20261023f`). Commits locales: no hay remoto.

Pruebas en `fdb4cbd`: motor 21/21; Odoo 27 métodos (boss_expediente 13, boss_pricing_sale 13, boss_pricing 1 de referencias con las muestras privadas actualizadas): 0 fallos.
