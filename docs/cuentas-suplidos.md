# Cuentas de los suplidos (ARA, IVA, PLA, DUM) · Propuesta para Ángel (D-2)

Preparado el 26/10/2026 por decisión de Belal (W04-2): mapa de cuentas, corrección y pruebas hechas **en local**;
el cambio contable en boss20 solo se aplica cuando Ángel apruebe este mapa (tarea BOSS20-W10).

## Por qué

La configuración del 23/10 (P18) puso los cuatro suplidos en la cuenta **419000**, que en el plan contable de Odoo es
**a pagar** (`liability_payable`, conciliable). Odoo rechaza con ella la factura del agente de aduanas («debe tener
una fecha de vencimiento») y la factura al cliente («es de tipo por pagar, pero se está utilizando en una operación de
venta»). Comprobado el 26/10 en la copia local (ensayo deshecho) y en una prueba automática
(`test_paid_on_behalf_on_current_liability_accounts`). boss20 tiene hoy esa configuración: la fila ARA del
expediente [DEMO] E260001 no se puede facturar.

## Cómo lo hace Odoo 17 (leído el 26/10/2026, solo lectura)

| Cuenta | Nombre en Odoo 17 | Tipo |
|---|---|---|
| 419000 | Payables for profit-sharing agreements (Acreedores por operaciones en común) | A pagar, conciliable |
| 419001 | SUPLIDOS IVA REPERCUTIDO IMPORT | Pasivo corriente, no conciliable |
| 419002 | SUPLIDOS ARANCELES REPERCUTIDOS IMPORT | Pasivo corriente, no conciliable |
| 419003 | SUPLIDOS IVA SOPORTADO IMPORT | Pasivo corriente, no conciliable |
| 419004 | SUPLIDOS ARANCELES SOPORTADOS IMPORT | Pasivo corriente, no conciliable |
| 419005 | ANTI DUMPING | Pasivo corriente |
| 419006 | IMPUESTO SOBRE PLASTICO NO REUTILIZABLE REPERCUTIDO | Pasivo corriente |
| 419007 | IMPUESTO SOBRE PLASTICO NO REUTILIZABLE SOPORTADO | Pasivo corriente |

(El tipo de 419005–419007 se infiere del patrón de las otras; conviene que Ángel lo confirme.)

## Mapa propuesto (producto → cuenta de ingreso al facturar al cliente / cuenta de gasto en la factura del agente)

| Servicio | Al cliente (repercutido) | Con el agente (soportado) |
|---|---|---|
| IVA (IVA de importación pagado por el agente) | 419001 | 419003 |
| ARA (aranceles) | 419002 | 419004 |
| DUM (antidumping) | 419005 | 419005 |
| PLA (impuesto del plástico) | 419006 | 419007 |

Impuesto de la línea al cliente: «0% Exent NS» (tabla de IVA BOSS, suplidos). Impuesto de compra en la factura del
agente: el que figure en su documento (decisión de Ángel, A01).

## Preguntas para Ángel

1. ¿Es este el mapa correcto, o prefiere una única pareja de cuentas (repercutido / soportado) para los cuatro?
2. ¿Los nombres de las cuentas en Odoo 20 copian los de Odoo 17 o los normalizamos (minúsculas, «importación»)?
3. ¿Las cuentas 419001–419007 se crean en boss20 con el mismo código (sí, salvo que indique otro)?
4. ¿Conciliables? Odoo 17 las tiene no conciliables; se propone igual.

## Aplicación

- Script `dev/setup_suplidos_accounts.py` (idempotente): crea las cuentas y asigna el mapa. En la copia local ya; en
  boss20 solo con `--approved-by-angel` tras su respuesta.
- Prueba automática en `boss_expediente/tests/test_file_followup.py`: con 419000 falla; con el mapa, la factura del
  agente y la del cliente se crean y contabilizan.
