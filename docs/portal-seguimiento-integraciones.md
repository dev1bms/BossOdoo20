# Seguimiento automático de envíos — situación y siguiente fase (28/10/2026)

**Situación.** No hay ninguna integración de seguimiento en Odoo 20 ni en Odoo 17 (producción, lectura 28/10: ningún
modelo, campo ni tarea programada de MSC Track & Trace, BFirst ni otro proveedor). La primera versión del portal
(ADR-010) muestra solo lo que BOSS registra en el expediente: ETD/ETA, ATD/ATA, entrega, contenedores y los eventos que
el personal publica. No se muestra «seguimiento en directo» ni posición.

**Punto de extensión preparado.** Los eventos del expediente (`boss.expediente.event`) ya separan lo interno
(`note`) de lo publicado (`portal_published` + `portal_text`). Una integración futura escribiría eventos y fechas reales
(ATD, ATA, descarga, retirada, devolución del vacío) en el expediente con su fuente; el portal no cambia.

**Lo que hace falta decidir antes de construirla** (no se activa nada en esta fase):
- Proveedor por modo: navieras (MSC Track & Trace / DCSA, Maersk, Hapag, CMA), agregadores (p. ej. BFirst u otros),
  aéreo (AWB por aerolínea o agregador). Quién paga la suscripción y con qué cuenta.
- Identificador de consulta por envío: número de B/L máster, de contenedor o de AWB; quién lo introduce y cuándo.
- Qué eventos pasan solos al cliente y cuáles revisa operaciones antes de publicarse.
- Frecuencia de consulta y qué hacer con datos contradictorios (el dato de operaciones manda).
- Datos personales y contrato con el proveedor (encargo de tratamiento).

Responsables: Belal (proveedor y coste), Cristina (qué ve el cliente), operaciones (revisión de eventos).
