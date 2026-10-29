# Migración de contactos (F2) — análisis de solo lectura, 28/10/2026

Estado: **análisis, no aprobado**. Nada se ha cargado. Alcance y mapeo dependen de F0-B01, F0-B02, F0-C02, R-A3, F0-A02/F0-B04 (ver `docs/paquetes-aprobacion-f0.md`). Comprobado a mano: campo `x_studio_type` (ir.model.fields 18028) y los ejemplos 57786 y 54130, que son direcciones de entrega hijas de una empresa, no contactos «lugar».


No se ha escrito nada en ningún sitio. En Odoo 17 solo he usado lecturas por MCP y en boss20 solo `SELECT`. Aquí no aparecen nombres de personas, NIF ni IBAN.

**Lo principal:** de los 21.695 contactos activos de Odoo 17, solo unos 1.300 tienen documentos contables y 746 aparecen como ordenantes. El alcance medido el 29/10 es de **1.295 contactos principales** (sección 2), no los 21.695. Además, la idea de que «PENDIENTE» son lugares no se sostiene.

**Límite de la herramienta:** `search_records` solo admite un filtro de texto parcial sobre un campo. No acepta dominios, `search_count` ni agrupaciones, y `list_contacts` y `list_invoices` dan error. Los totales los he sacado de `ir.model.count` y el resto paginando hasta el último registro. No se pueden cruzar condiciones (tipo y NIF, actividad y año), así que esos cruces quedan abiertos.

## 1. Números

| Medida (Odoo 17, solo activos) | Valor | Cómo se midió |
|---|---|---|
| Contactos activos | **21.695** (21.921 con archivados) | paginación sobre `id`; `ir.model` 85 `count` |
| Empresas / hijos (con padre) | **10.729 / 10.935** | `is_company`=true; `parent_id` informado |
| Tipo de dirección | contacto ≈13.530 · factura ≈5.420 · entrega ≈2.515 · otra 218 | `type` (cifras con ±30) |
| x_studio_type (campo 18028) | Cliente 2.236 · Cliente+Proveedor 142 · Proveedor 1.600 · Acreedor 377 · Agente 1.966 · Expedidor/destinatario extranjero 3.355 · español 1.058 · PENDIENTE 1.478 · sin tipo ≈9.480 | valores exactos («Cliente» incluye C+P, así que se ha restado) |
| Marcas de papel `x_studio_is_*` | carrier 117 · airline 653 · customs_agent 41 · trucker 558 · provider 1.307 · agent 69 · shipperconsignee 79 | valor `true` |
| Con actividad desde 2024 | **1.321** con al menos un asiento (la contabilidad de Odoo 17 empieza en 09/2024: F24 09-, RBILL/2024/09) · **746** ordenantes de expediente (cualquier año, 20.792 expedientes desde E22) | `invoice_ids` y `x_studio_expedientes_orderer` informados |
| Pedidos de venta estándar | 5 en todo Odoo 17 (no se usan; las ofertas viven en `x_quotations`) | `ir.model` 473 |
| Con NIF informado | 8.978 (incluye los hijos, que heredan el NIF) | `vat` con al menos un carácter |
| NIF duplicado | 205 contactos marcados; es un mínimo porque el cálculo almacenado no se recalcula | `x_studio_duplicated_vat` |
| `x_studio_spanish_nif` | 1 (no se usa) | |
| Cuentas bancarias | **671** activas (674 con archivadas), de **650** contactos | `res.partner.bank`; `bank_ids` |
| Condiciones de pago de cliente (incluye hijos) | Inmediato >1.000 · 30 días 1.001–3.000 · 25 días 41–80 · 60 días 39 · 15 días 17 · 6 días 4 · 20 días 2 · 45 días 2 · 75 y 90 días: 0 | `property_payment_term_id` por nombre |
| Condiciones de pago de proveedor | 30 días 301–1.000; Inmediato >40 y 60 días >40; 6/15/45 días con pocos (1–40); 75/90 sin medir | `property_supplier_payment_term_id` |
| Transportistas con varias entidades | MSC 5 (23762, 23022, 23493, 23733, 54705) · CMA CGM 7 · Maersk 6 · COSCO 4 · OOCL 3 · HMM 3 · Hapag, ONE, ZIM, Yang Ming 1 cada uno | búsqueda por nombre |
| Usuarios internos activos | 15 (incluye una cuenta genérica de ventas) | `res.users` sin acceso compartido |
| **boss20** (SQL) | 140 contactos / 132 activos · 35 empresas · 43 hijos · 5 con `customer_rank`>0 (3 sin [PRUEBA]/[DEMO]) · 56 con `supplier_rank`>0 · 63 nombres «PRUEBA» · 7 [DEMO] · `ref` informado en 59, ninguno numérico (aún no hay ids de Odoo 17) · 0 cuentas bancarias · 0 con `boss_carrier_group_id` · papeles: carrier 43, handler 8, customs_broker 3, agent 2, haulier 2 · 4 internos (3 en en_US, 1 en es_ES) · 0 usuarios de portal · condiciones de pago: 11 (faltan 6, 20 y 60 días) | psql de solo lectura |

**Hallazgos que cambian supuestos de F0:**
- **PENDIENTE no son lugares.** La muestra de 5 de 10 leídos: los 5 son hijos (3 direcciones de entrega y 2 personas). Es el valor por defecto desde el 22/04/2024 para los contactos nuevos sin clasificar.
- **Los «lugares» son hijos de tipo entrega** con nombre de código postal o ciudad (unos 2.515). Los ejemplos 57786 y 54130 del plan son eso: uno PENDIENTE y otro sin tipo.
- **Marcas de MSC.** Las 5 entidades tienen tipo Proveedor, pero 23022 y 23493 no llevan la marca de naviera. La marca `is_carrier` no basta para formar la familia.
- **Marcas mezcladas.** `is_carrier` incluye camioneros y algunas personas físicas, y `is_airline`/`is_provider` incluyen unas 600 aerolíneas de catálogo IATA sin actividad.

## 2. Alcance medido (29/10/2026; propuesta, pendiente de aprobación)

Medido en Odoo 17 con búsquedas de solo lectura. Cada conjunto se ha comprobado contra el total que da Odoo. La
contabilidad de Odoo 17 empieza en 09/2024, así que «con documento contable» equivale a «con actividad desde 2024».

| Conjunto (contactos principales activos) | 2024 | 2025 | 2026 | 2024–2026 |
|---|---:|---:|---:|---:|
| Con factura o abono de cliente (F, FR) | 288 | 291 | 182 | **518** |
| Con factura o abono de proveedor (BILL, RBILL) | 468 | 476 | 251 | **823** |
| Ordenantes de expediente (E24–E26) | 180 | 135 | 94 | **272** |
| Cliente y proveedor a la vez | | | | 69 |
| Ordenantes sin ningún documento contable | | | | 21 |
| **Unión (activos)** | | | | **1.293** |
| Archivados con facturas en Odoo 17 (se cargan archivados) | | | | **2** |
| **Contactos principales en el alcance** | | | | **1.295** |
| Hijos activos de esos contactos (direcciones y personas; 735 contactos tienen alguno) | | | | **2.404** |
| **Total de registros a cargar** | | | | **3.699** |
| Cuentas bancarias de esos contactos (no se cargan hasta que Ángel decida) | | | | 577 |

- **Saldos abiertos:** todo saldo abierto está en una factura o abono desde 09/2024, así que ya está dentro de la unión.
- **Archivados:** de los 226 archivados, 3 tienen documentos o expedientes; 2 entran (facturas) y 1 no (solo
  expedientes de 2023). Se cargan **archivados**, nunca se excluyen por estar archivados.
- **Hijos:** se cargan **todos** los hijos de los contactos del alcance (direcciones de entrega y factura y personas),
  sin excluir ninguno por ciudad, código postal o falta de teléfono o email. Un hijo con nombre de lugar es una
  dirección de entrega válida.
- **Fuera del alcance (se quedan en Odoo 17, consultables):** los contactos sin documento ni expediente desde 2024,
  incluido el catálogo IATA sin actividad.
- **Diferencia con la medición del 28/10:** había 1.321 contactos con algún apunte y aquí 1.272 tienen factura o
  abono; los 49 restantes no tienen factura
  F/FR/BILL/RBILL (sin comprobar: asientos de otros diarios u otra numeración). Se revisan en la carga real: si alguno
  tiene saldo, entra.
- **No medido con estas herramientas:** contactos que solo aparecen como agente, expedidor o destinatario de un
  expediente sin factura propia. Se miden en la exportación real (necesita acceso de solo lectura a Odoo 17 desde el
  servidor).

## 3. Destino de cada campo (Odoo 17 → Odoo 20)

| Odoo 17 | Odoo 20 | Nota |
|---|---|---|
| `name`, `is_company`, `type`, `street`, `street2`, `zip`, `city`, `email`, `website`, `company_registry` | igual | copia directa |
| `country_id`, `state_id` | igual | por nombre (es/en); lo que no casa se lista |
| `phone` | `phone` | |
| `mobile` | `boss_mobile` (campo «Móvil» en boss_expediente) | Odoo 20 no tiene móvil; **no se mezcla con el teléfono** |
| `lang` | `lang` | solo idiomas instalados; si no, se lista como descartado |
| `comment` | `comment` | las notas se conservan tal cual |
| `vat` | `vat` | normalizado (sin espacios ni puntos); los hijos heredan el del padre. Si Odoo lo rechaza, se carga sin él y se lista para decidir |
| `parent_id` | `parent_id` | por el vínculo del padre |
| `x_studio_code` (código comercial) | `ref` | solo si `ref` está vacío; si ya tiene valor, se conserva y el código se lista |
| `x_studio_type` + marcas `x_studio_is_*` | `customer_rank`, `supplier_rank`, `boss_role_ids` | propuesta F0-C02 (no aprobada) |
| `property_payment_term_id`, `property_supplier_payment_term_id` | igual | por nombre o días; falta «60 días» en boss20 (se lista) |
| 5 entidades MSC | `boss_carrier_group_id` → cabecera «Mediterranean Shipping Company (MSC)» | F0-B05 (decidida) |
| `credit_limit`, nivel de reclamación, `x_studio_payment_type`, `x_studio_remesa`, cuentas bancarias | — | **no se cargan** hasta que Ángel decida (F0-A02, F0-A03, F0-B04) |
| `x_studio_kam` | — | **no se carga** hasta la lista de usuarios (W08, F0-C01) |
| `x_studio_secret`, tokens, imágenes, mensajes | — | **descartados**: datos técnicos o sensibles sin uso en Odoo 20 |

Todo dato descartado o no cargado sale en el registro de la carga con su motivo.

## 4. Vínculo, duplicados y repetición

- **Vínculo estable:** un identificador externo de Odoo por contacto, `o17_partner.res_partner_<id de Odoo 17>`,
  independiente de `ref` y de los códigos comerciales, que nunca se sobrescriben.
- **Contactos que ya están en boss20** (navieras, proveedores): se **enlazan**, no se duplican. Orden de búsqueda:
  1. referencia «O17:<id>» puesta a mano antes en boss20 (así están MSC España y WFS);
  2. NIF del contacto principal, con o sin prefijo de país (boss20 guarda «ESB…», Odoo 17 «B…»);
  3. nombre normalizado exacto, solo entre empresas sin NIF.
  En un contacto enlazado solo se rellenan los campos vacíos; las diferencias se listan, nada se sobrescribe.
- **Sin fusión automática:** dos contactos de Odoo 17 con el mismo NIF se cargan los dos y se listan para revisión.
  Tampoco se fusiona por nombre parecido.
- **Repetir la carga** no crea ni cambia nada: el vínculo encuentra el mismo destino.

## 5. Ensayo con muestra (29/10/2026, boss20, transacción deshecha)

Muestra de 14 contactos reales: una empresa con sus 4 hijos (entrega con nombre de lugar, factura sin nombre, dos
personas), un proveedor ya presente en boss20, las 5 entidades de MSC (una ya en boss20), un par con el mismo NIF y un
archivado que es cliente y proveedor. Resultado: **16 comprobaciones correctas, 0 fallos**
(`docs/evidencias/20261029_0921_check_migration_sample_boss20_febb56be3a72.txt`).

- 12 creados y 2 enlazados a contactos existentes (MSC España y WFS), sin duplicados.
- Dos ejecuciones seguidas: la segunda no crea ni cambia nada.
- Ningún otro contacto de boss20 cambia; en los enlazados no se sobrescribe ningún valor.
- El ensayo detectó y corrigió dos fallos del cargador antes de la evidencia: no reconocía la referencia «O17:» ya
  puesta en boss20 ni el NIF con prefijo «ES», y habría duplicado MSC España y WFS.

## 6. Excepciones que necesitan decisión

- **Registros genéricos con facturas:** «ACREEDORES DIVERSOS», «ACREEDORES VARIOS», «HOTELES VARIOS», «GASOLINERAS
  VARIAS», «RESTAURANTES VARIOS», «AYUNTAMIENTOS VARIOS» y un contacto llamado «TEST» con factura de 2024. Están en el
  alcance porque tienen documentos; propuesta: cargarlos como están (Ángel decide si se mantienen en Odoo 20).
- **Condición de pago «60 días»** no existe en boss20: propuesta, crearla antes de la carga (paquete 8, F0-A01).
- **Carga real:** requiere aprobar el alcance (F0-B01) y un acceso de solo lectura a Odoo 17 desde el servidor para la
  exportación completa; la muestra se leyó con la herramienta de consulta, que no sirve para 1.295 contactos y sus
  hijos de una vez.
