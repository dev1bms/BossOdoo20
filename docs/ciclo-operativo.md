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

## Decisiones tomadas en esta fase (técnicas)
- Expediente propio (no `project`), una cuenta analítica por expediente, necesidades de compra explícitas (ADR-005).
- Pedido de compra: borrador por proveedor y moneda; confirmación y envío por una persona.
- Control de facturas de proveedor de servicios BOSS «según cantidades recibidas» (servicio prestado), reversible en
  el producto; pendiente de confirmar por Ángel (A8).

## Bloqueos y decisiones de negocio abiertas
Ver `docs/preguntas-abiertas.md` (Cristina C1–C7, Ángel A1–A8). No bloquean el desarrollo: las cuentas quedan como
están, el IVA de compra lo elige quien registra la factura según el documento del proveedor.

Aplicadas y pendientes de confirmar:
- Ángel: el NIF y la dirección del cliente son obligatorios para contabilizar una factura de servicios BOSS (clientes
  empresa). En Odoo 20 «es empresa» = tiene NIF.
- Ángel / Cristina: la factura de proveedor de un servicio del expediente se contabiliza después de facturarlo al
  cliente (requisito de Cristina, «Nuevo Odoo», hoja Facturación A3), salvo coste «cubierto» o «lo asume BOSS».
- Ángel (A8): control de facturas de proveedor por cantidades pedidas (estándar) o recibidas (servicio prestado):
  es un ajuste del producto, sin código.
- Numeración E26xxxx: igual que Odoo 19; mantenerla o reiniciarla al arrancar sigue abierto (Q6).

Pendiente técnico: recalcular el coste previsto del expediente con los datos reales (hoy se muestran las diferencias
con la oferta y el coste se corrige en la línea del servicio a comprar o en el pedido).

Último commit desplegado: ver `git log` (commits locales; no hay remoto configurado).
