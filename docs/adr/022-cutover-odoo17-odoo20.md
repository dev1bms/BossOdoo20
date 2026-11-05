# ADR-022 · Cambio de Odoo 17 a Odoo 20 (corte) · Cut-over from Odoo 17 to Odoo 20

Estado: **borrador aplicado por defecto** (05/11/2026, tarea P2-11 del seguimiento oficial). Las reglas vienen de las
decisiones ya documentadas (F0-C73, F0-A42, F0-A44, F0-A45, F0-B09, F0-B19, F0-B27) y de la decisión de Belal del
05/11/2026 («boss20 es la base de producción; nunca una base nueva»). Cristina, Ángel y Santos lo ratifican en bloque
con la lista de reglas (P3-03); mientras tanto es lo que se construye y se ensaya.

## Decisión

1. **Base de producción: boss20**, la base actual. No se crea ninguna base nueva ni copia. Antes del arranque se anulan
   por las vías de Odoo las facturas, abonos y pagos de prueba, se archivan los registros [PRUEBA] y se dejan fijadas
   las series de 2027 (tarea P3-04).
2. **Arranque por tráficos** (F0-B11 opción b): primero importación marítima FCL; cada tráfico siguiente entra cuando
   un caso real suyo se ha recorrido hasta el cierre financiero con usuarios de su papel (P2-20, P4-08…).
3. **Contabilidad nueva solo en Odoo 20 desde la fecha de arranque de cada tráfico** (F0-A42); 2026 y años anteriores
   quedan en Odoo 17 en solo lectura.
4. **Expedientes abiertos** (F0-C73, F0-B19): pasan a Odoo 20 todos los no cerrados operativamente con actividad en
   2026 (pendientes de salida con booking o fecha prevista, en tránsito, llegados, entregados y pendientes de cierre),
   con etapa, partes, contenedores, referencias, fechas y lo pendiente de comprar y de facturar. Los preexpedientes sin
   actividad y los antiguos sin cerrar se revisan en una lista aparte antes del corte. Solo se migran los adjuntos de
   los expedientes que pasan abiertos (F0-B09); el histórico (≈49.700 documentos) se consulta en Odoo 17.
5. **Saldos de apertura** (F0-A44, F0-A45): asiento de apertura con el balance de cierre de 2026 de Odoo 17,
   provisional en el arranque y ajustado al cerrar 2026 (diario «Opening Seat» como en Odoo 17); las partidas abiertas
   de clientes y proveedores se cargan una a una con su número y fechas originales, para que la conciliación y los
   vencimientos sigan iguales.
6. **Corte de Odoo 17** (F0-B27): se deja de registrar operaciones nuevas en Odoo 17 para cada tráfico el día en que
   ese tráfico arranca en Odoo 20, a las 18:00 tras la última operación del día; Odoo 17 pasa a solo lectura para
   ese tráfico. El cierre total de Odoo 17 a transacciones nuevas llega cuando el último tráfico ha pasado (opción C
   de la auditoría: no antes del 01/04/2027).
7. **Odoo 17 nunca se borra**: queda en solo lectura, accesible, al menos durante todo 2027.
8. **Numeración**: boss20 numera los expedientes de 2026 desde E269001 (por encima de cualquier número de Odoo 17) y
   los de 2027 desde E270001 (P36).

## Ensayo y evidencia

- El guion de corte (P3-12) se ensaya en boss20 dentro de una transacción que se deshace, con conciliación por
  expediente y por cuenta contra los saldos de Odoo 17 leídos en el momento del ensayo.
- La lista go/no-go (P2-21) y los criterios de vuelta atrás acompañan a este ADR.

## Consecuencias

- Mientras un tráfico siga en Odoo 17, sus facturas salen de Odoo 17; si en 2027 Odoo 17 sigue facturando, necesita
  también el sistema de envío a la AEAT que se decida (VERI*FACTU o SII).
- Las herramientas externas acopladas a Odoo 17 (≈15) se deciden una a una antes del cierre total (P4-15).

---

**English summary.** boss20 stays the production database (no new database). Go-live is traffic by traffic, sea FCL
import first; new accounting only in Odoo 20 from each traffic's start; open files with 2026 activity move to Odoo 20
with their attachments; opening entry from the 2026 closing balance and open items one by one with original numbers
and dates; Odoo 17 closes to new transactions per traffic at 18:00 of its start day and stays read-only, never
deleted; files numbered E269001+ in 2026 and E270001+ from 2027. Applied as a documented default, ratified in block
with the rules list (P3-03).
