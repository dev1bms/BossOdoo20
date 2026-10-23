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

## Decisiones tomadas en esta fase (técnicas)
- Expediente propio (no `project`), una cuenta analítica por expediente, necesidades de compra explícitas (ADR-005).
- Pedido de compra: borrador por proveedor y moneda; confirmación y envío por una persona.
- Control de facturas de proveedor de servicios BOSS «según cantidades recibidas» (servicio prestado), reversible en
  el producto; pendiente de confirmar por Ángel (A8).

## Bloqueos y decisiones de negocio abiertas
Ver `docs/preguntas-abiertas.md` (Cristina C1–C7, Ángel A1–A8). No bloquean el desarrollo: las cuentas quedan como
están, el IVA de compra lo elige quien registra la factura según el documento del proveedor.

Último commit desplegado: —
