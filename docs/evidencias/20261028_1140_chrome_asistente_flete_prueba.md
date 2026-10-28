# Asistente ⊕ «Add supplier price» en Chrome, boss20, 28/10/2026 11:33–11:40 (código desplegado `f96dbb3`)

Oferta de prueba S00311 («[PRUEBA] Susaeta Ediciones (recorrido)», MSC, CNSHA → ESVLC, 1 × 40' DV, ETA 06/11).
Todo tecleado en Chrome con el usuario de Belal.

| Paso | Observado |
|---|---|
| Envío › ETD 30/10/2026, guardar | Chatter «None → Oct 30, 2026 (ETD)»; ⓘ de FMI: «Tariff date 10/30/2026: the departure (ETD) chooses the freight rate.» |
| ⊕ en la línea FMI | Banner verde «Freight rate: approved on entry, usable at once (Sales setting)»; proveedor MSC; válido **28/10 → 03/11** (hoy + 6 días); ámbito: Import · Sea · FCL · transportista MSC · **origen CNSHA arriba, destino ESVLC debajo** · China. Sin banner «New version of»: MSC no tenía tarifa aprobada para esa ruta |
| Datos tecleados | Precio 1.850 USD por contenedor; nombre «[PRUEBA] MSC FMI CNSHA → ESVLC 2026»; documento `prueba_oferta_flete_msc.txt` (ficticio); referencia «[PRUEBA] oferta ficticia MSC 28/10 (no real)»; **«Only this customer» marcado** (la tarifa de prueba no puede valorar a un cliente real) |
| Save price | Sin recargar: FMI «Priced», coste **1.653,56 €** (1.850 USD al cambio de la fecha de la oferta), venta 1.984,27 € (coste + 20 %, regla de la Tarifa general) |
| ⓘ de FMI | «1 x $ 1,850.00 per Container… Source: [PRUEBA] MSC FMI CNSHA → ESVLC 2026 v1 (MSC), valid from 10/28/2026 to 11/03/2026 … only [PRUEBA] Susaeta …, document [PRUEBA] oferta ficticia …» |
| Servidor | Tarifa 169: `approved`, v1, aprobada por Belal Alsweirki 28/10 10:34 UTC, creada por Belal; nota «Approved on entry: freight rate typed from S00311 …»; línea FMI 1.850, 40' |

Hallazgos de pantalla y su corrección (commit `133211a`, **sin desplegar**: el despliegue fue bloqueado por el control de
permisos y espera a Belal); comprobados en boss20 con el código montado (rollback):
1. El asistente mostraba los importes con 4 decimales (0.0000, 1,850.0000) → dos decimales.
2. La venta «coste + 20 %» salía con 3 decimales (1,984.272) → la regla redondea al céntimo (`price_round` 0,01;
   migración 20.0.1.14.0 para la regla 27) → 1.984,27.
3. La ⓘ listaba el ámbito «ESVLC · CNSHA» (puerto español primero, la lectura que Ángel señaló) → «CNSHA → ESVLC».

Registro de prueba que queda en boss20: tarifa 169 (solo para el cliente [PRUEBA]), ETD de S00311.
