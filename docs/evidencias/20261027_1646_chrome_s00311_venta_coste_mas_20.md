# Venta por defecto = coste + 20 % activada desde Ajustes (boss20, 27/10/2026 16:42–16:47)

Código desplegado: `5cf2918` (boss_pricing 20.0.1.10.0, boss_pricing_sale 20.0.1.12.0, boss_expediente 20.0.1.11.0),
desplegado con la aprobación de Belal con el servidor en reposo (143 min desde la última actividad de Ángel). Guía
publicada v=20261027i. Todo lo de abajo se hizo en Chrome con el usuario de Belal; queda el registro de prueba S00311.

| Paso en pantalla | Resultado observado |
|---|---|
| Ajustes › Ventas › «Default sale price of BOSS services» › Cost + **20** › Guardar | Al recargar, el campo lee **20.00** |
| Servidor (`server_shell`) | Regla 27 en «Tarifa general (EUR)»: `markup` 20 %, etiqueta «Coste previsto de la línea + 20 %» |
| Nueva oferta: «[PRUEBA] Susaeta Ediciones (recorrido)», plantilla IMB FOB, MSC, China / CNSHA → ESVLC, ETA 16/11, 1 × 40' DV | Lista de precios de la oferta: Tarifa general (EUR) |
| Pestaña Líneas tras guardar (S00311) | THC coste 253 → **venta 303,60**; BL 79 → **94,80**; GLO-CCC 27 → **32,40**; T3-PAD 50 → **60,00**; las cuatro con «From the expected cost (pricelist rule)». FMI (importe manual sin teclear), FAD (varios precios), TTE-FCL (sin precio de proveedor) y CSM (honorario BOSS con coste 0) → «Sale price missing»: nada se calcula sobre un coste desconocido o cero |
| Aviso «Pricing to complete» | «No supplier price: 1 · Several prices apply: 1 · Manual amount: 1 · Sale price missing: 4» |
| Total | 490,80 € sin IVA; margen 17 % (81,80 €) |

Comprobaciones sobre el código desplegado: `check_default_markup` 22/22 y `check_route_cases` 53/53
(`docs/evidencias/20261027_16*_check_*_boss20_5cf2918*.txt`).

Nota de uso: un honorario propio de BOSS (CSM) tiene coste 0 justificado, así que «coste + 20 %» no le pone precio:
el precio de venta de los honorarios propios se teclea o se acuerda en la lista del cliente.
