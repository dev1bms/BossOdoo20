# Brief: SII, VERI\*FACTU y exención de IVA en facturas (BOSS Continental, alta en Odoo 20 el 1/1/2027)

Solo he leído: boe.es, la sede de la AEAT, hacienda.gob.es y el código de Odoo 20. No he editado ningún archivo ni escrito en ninguna base de datos. Saber qué módulos están instalados en Odoo 17 no dice nada sobre la situación legal de BOSS, y aquí no se usa.

## A. Qué exige la ley

- **Quién está obligado al SII.** Los libros registro de IVA se llevan por la sede de la AEAT cuando el periodo de liquidación es mensual según el art. 71.3 (RIVA art. 62.6, introducido por el RD 596/2016). https://www.boe.es/buscar/act.php?id=BOE-A-1992-28925 · https://www.boe.es/buscar/doc.php?id=BOE-A-2016-11575
  - Según el art. 71.3 RIVA, liquidan cada mes:
    1. Quien tuvo un **volumen de operaciones** (art. 121 LIVA) de más de 6.010.121,04 € el año natural anterior. Es volumen de operaciones, no cifra de negocios contable.
    2. Quien adquirió un patrimonio empresarial y, sumado al del transmitente, supera ese importe.
    3. Los inscritos en devolución mensual (art. 30 RIVA, el REDEME).
    4. Los grupos de entidades de IVA.
    5. Los titulares de depósitos fiscales de hidrocarburos.
  - Cualquier otro sujeto pasivo **puede optar** por el SII (art. 62.6 y art. 68 bis RIVA). Según la AEAT, se pide en cualquier momento con el modelo 036 (casillas 143 y 532). Tiene efecto desde el día siguiente al final del periodo de liquidación en que se pidió. https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/manual-gran-empresa/que-consecuencias-tiene-perder-condicion-empresa/suministro-inmediato-informacion-iva/acogerse-sii-forma-voluntaria.html
- **Reglamento de sistemas de facturación (RRSIF, RD 1007/2023).** https://www.boe.es/buscar/act.php?id=BOE-A-2023-24840
  - Art. 3.1: se aplica a los contribuyentes del Impuesto sobre Sociedades, del IRPF con actividad económica, del IRNR con establecimiento permanente y a las entidades en atribución de rentas.
  - Art. 3.3: **no se aplica** a quien lleva los libros registro por el SII (art. 62.6 RIVA).
  - Art. 4: quedan fuera, entre otras, las operaciones hechas mediante establecimientos permanentes en el extranjero.
  - VERI\*FACTU no es una norma aparte. Es una forma de cumplir el RRSIF: un sistema que envía todos los registros a la AEAT (arts. 15 y 16).
  - Las especificaciones técnicas están en la Orden HAC/1177/2024 (texto consolidado al 28/10/2024). https://www.boe.es/buscar/act.php?id=BOE-A-2024-22138
- **Fechas publicadas en el BOE** (disposición final cuarta del RD 1007/2023, en la redacción del RDL 15/2025 BOE-A-2025-24446, convalidado por BOE-A-2025-25695; antes la había cambiado el RD 254/2025, BOE-A-2025-6600):
  - Contribuyentes del Impuesto sobre Sociedades (art. 3.1.a): sistemas adaptados **antes del 1/1/2027**.
  - Resto: antes del 1/7/2027.
  - Fuentes: https://www.boe.es/eli/es/rdl/2025/12/02/15 · https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/nota-informativa-ampliacion-plazo-adaptacion-facturacion.html
- **Aplazamiento anunciado pero no publicado.**
  - El 5/10/2026 el Gabinete de Prensa de Hacienda publicó una «previsión»: aplazar «hasta octubre de 2028» las obligaciones pendientes del RD 1007/2023. https://www.hacienda.gob.es/sgt/gabsehacienda/nota-informativa-verifactu.pdf
  - La sede de la AEAT la enlaza como «Previsión de ampliación del plazo». https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html
  - El 28/10/2026 el texto consolidado del RD 1007/2023 en boe.es tiene como última actualización el **03/12/2025**. No hay ninguna norma de 2026 que lo modifique. Por tanto, **la fecha que hoy obliga legalmente es el 1/1/2027**.
  - La nota no aclara si el aplazamiento alcanza a todos los obligados o solo a las empresas que facturan hasta 8 M€. Eso solo lo dicen artículos de prensa y blogs, no una fuente primaria.

## B. Las dos formas de cumplir el RRSIF (solo si BOSS no está en el SII)

| | VERI\*FACTU | Sin VERI\*FACTU |
|---|---|---|
| Envío a la AEAT | Envío automático y continuo de todos los registros (RD art. 16.1). Mínimo 60 s entre envíos; si falla, reintento al menos cada hora (Orden arts. 16.2 y 16.4). | Ningún envío automático. Los registros solo se entregan si la AEAT los requiere (RD art. 14.2; Orden art. 18). |
| Firma electrónica de los registros | No hace falta; basta la huella o *hash* encadenada (RD art. 16.3). | Obligatoria: XAdES Enveloped con certificado cualificado (RD art. 12; Orden art. 14). |
| Registro de eventos | Se presume que cumple el art. 8 por diseño (RD art. 16.2). | Obligatorio, con un registro resumen cada 6 horas (RD art. 8.3; Orden art. 9). |
| Certificado | Para identificarse al enviar: el propio o el de un tercero con representación o colaboración social (Orden arts. 4 y 5). | Para firmar los registros. |
| QR en la factura | Sí, de 30–40 mm (Orden arts. 20.1 y 21; art. 6.5 del RD 1619/2012). | Sí, igual. |
| Leyenda «VERI\*FACTU» | Sí, o «Factura verificable en la sede electrónica de la AEAT» (Orden art. 20.1.b). | Prohibida. |
| Permanencia | Hasta el 31/12 del año del primer envío (RD art. 16.5; Orden art. 17.2). | — |

## C. Qué hace Odoo 20 (código en `odoo-20.0+e.20261020/odoo/addons`)

- **`l10n_es_edi_sii`** (`__manifest__.py`, `models/res_company.py`):
  - Envía los libros de IVA de facturas emitidas y recibidas (procedimiento G417) al validar la factura.
  - Hacienda destinataria a elegir: AEAT, Gipuzkoa, Bizkaia o Navarra (`l10n_es_sii_tax_agency`).
  - Usa un certificado con `scope='sii'`.
  - `l10n_es_sii_test_env` (modo de pruebas) viene **activado por defecto**.
- **`l10n_es_edi_verifactu`**:
  - Se activa por compañía con `l10n_es_edi_verifactu_required`.
  - `l10n_es_edi_verifactu_test_environment` viene **activado por defecto**. En pruebas apunta a `prewww1/prewww2.aeat.es`; en real, a `www1/www2.agenciatributaria.gob.es` (`models/res_company.py`).
  - Usa un certificado con `scope='verifactu'`.
  - Calcula la huella SHA-256 encadenada y envía los registros en lotes por cron, reintentando los que fallan.
  - Imprime el QR y la palabra «VERI\*FACTU» en la factura (`views/report_invoice.xml`).
  - En ajustes enlaza a la «Declaración Responsable» de Odoo.
- **Odoo 20 no soporta la forma sin VERI\*FACTU.**
  - En `verifactu_document.py:898` declara `'TipoUsoPosibleSoloVerifactu': 'S'`, es decir, que el sistema solo puede usarse como VERI\*FACTU.
  - En ninguno de los dos módulos hay firma XAdES de los registros ni registro de eventos.
  - Por tanto, una empresa fuera del SII que use Odoo estándar tendría que enviar a la AEAT con VERI\*FACTU.

## Qué debe confirmar Ángel o el asesor fiscal

1. **¿BOSS Continental S.L. llevará sus libros de IVA por el SII en 2027?** Es decir:
   - su volumen de operaciones de 2026 (art. 121 LIVA) supera los 6.010.121,04 €, o
   - está inscrita en el REDEME o en un grupo de IVA, o
   - ya está acogida al SII de forma voluntaria (o piensa acogerse).
2. **Si la respuesta es no:** BOSS queda dentro del RRSIF desde el 1/1/2027, salvo que se publique el aplazamiento en el BOE. Con Odoo 20 estándar eso significa VERI\*FACTU. Falta saber qué certificado se usará: el de la empresa o el de un representante o colaborador social.

## Mención de exención de IVA en facturas de importación y exportación (Ley 37/1992)

https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740

- **Art. 21.5º (exportación):** exentos los servicios, incluidos el transporte y las operaciones accesorias, «directamente relacionadas» con exportaciones de bienes fuera de la UE. Deben prestarse a quien exporta, al destinatario, a sus representantes aduaneros o a transitarios y consignatarios que actúen por cuenta de ellos.
- **Art. 21.6º y art. 22.15º:** exentos los intermediarios que actúan en nombre y por cuenta de terceros en operaciones exentas por esos artículos.
- **Art. 64 (importación):** exentos los servicios cuya contraprestación esté incluida en la base imponible de la importación.
  - El art. 83.Uno.b incluye en esa base los gastos accesorios (comisiones, embalaje, transporte, seguro) hasta el primer lugar de destino dentro de la UE.
  - Es decir, el servicio queda exento solo si su importe ha formado parte del DUA de importación.
- **Art. 22:** en lo revisado, los apartados 13º (viajeros) y 14º (Azores/Madeira) no se aplican a la carga de BOSS.
- **Condición:** la mención impresa en cada factura tiene que corresponder a casos documentados (exportación con DUA, servicio incluido en la base de importación) y revisados por Ángel o el asesor. No propongo ningún cambio de texto ni de impuesto sin esa revisión.

## Qué no sabemos

- El volumen de operaciones de BOSS en 2026 y si está en el SII, en el REDEME o en un grupo de IVA. Ningún dato del sistema lo prueba.
- Cuándo se publicará en el BOE el aplazamiento a octubre de 2028, en qué fecha exacta y a quién afectará.
- No he verificado en el BOE el art. 22.Cinco LIVA (servicios a buques y su cargamento) ni el art. 24 LIVA (depósitos y zonas francas), que podrían aplicarse a algunos servicios.
- No he confirmado en fuente primaria si acogerse voluntariamente al SII obliga hoy a liquidar el IVA cada mes. El art. 71.3 RIVA, tal como lo leí, no lo dice.
- Si BOSS tiene ya un certificado de representante válido para el SII o para VERI\*FACTU.
- Si Odoo añadirá la forma sin VERI\*FACTU en una versión posterior. En el código de 20.0+e.20261020 no está.
