## Pruebas

- Motor sin Odoo: `python -m unittest discover -s addons/boss_pricing/engine/tests -t addons/boss_pricing`.
- Odoo en una base desechable (Docker local, se borra al terminar): `dev/test.sh init` una vez y
  `dev/test.sh run boss_pricing_sale "/boss_pricing,/boss_pricing_sale"`.
- **Ejemplos de referencia**: 43 casos calculados a mano desde los documentos de proveedor (MSC, Hapag, CMA, WFS,
  IRENEO) se comparan con el cálculo. Los importes reales están en un fichero privado, nunca en el repositorio.

## Despliegue

`dev/deploy.sh update <módulos>`: comprueba que el destino es el entorno BOSS de Odoo 20, envía solo lo confirmado
en Git, actualiza con el servicio web parado y lo vuelve a arrancar. Nunca toca Odoo 17 ni Odoo 19.

## Tarifas en bloque

El importador (`boss.tariff._boss_import_tariffs`) crea tarifas desde un fichero estructurado: proveedor, documento,
página, vigencia, alcance y precios. Es idempotente (clave fija por tarifa; nunca reescribe lo existente), adjunta el
PDF, envía a aprobación y **nunca aprueba**. `dev/verify_references.py` comprueba los ejemplos en una base sin cambiarla
(todo se deshace al final).

## Traducciones

Textos fuente en inglés; español en `i18n/es.po` de cada módulo (`dev/test.sh pot <módulo>` y `dev/po_merge.py`).
