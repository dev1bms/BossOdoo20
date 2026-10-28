# Migración de contactos (F2) — análisis de solo lectura, 28/10/2026

Estado: **análisis, no aprobado**. Nada se ha cargado. Alcance y mapeo dependen de F0-B01, F0-B02, F0-C02, R-A3, F0-A02/F0-B04 (ver `docs/paquetes-aprobacion-f0.md`). Comprobado a mano: campo `x_studio_type` (ir.model.fields 18028) y los ejemplos 57786 y 54130, que son direcciones de entrega hijas de una empresa, no contactos «lugar».


No se ha escrito nada en ningún sitio. En Odoo 17 solo he usado lecturas por MCP y en boss20 solo `SELECT`. Aquí no aparecen nombres de personas, NIF ni IBAN.

**Lo principal:** de los 21.695 contactos activos de Odoo 17, solo unos 1.300 tienen documentos contables y 746 aparecen como ordenantes. Recomiendo migrar unos 2.000–3.500 contactos principales más sus hijos útiles, no los 21.695. No he podido medir la cifra exacta: queda como primer paso del ensayo. Además, la idea de que «PENDIENTE» son lugares no se sostiene.

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

## 2. Alcance recomendado (N01; depende de F0-B01 y F0-B02, aún no aprobadas)

- **Contactos principales:** empresas y personas sin padre citadas desde el 1/1/2024 en un expediente (ordenante, agente, naviera, aerolínea, expedidor, destinatario, agente de aduanas, camionero, «facturar a»), en un asiento contable o en una oferta. Se suman los que tengan un expediente abierto o saldo pendiente al corte.
  - Estimación: **≈2.000–3.500** (mínimo: unión de 1.321 con asiento y 746 ordenantes, más los citados en las partidas).
  - El catálogo IATA sin actividad (≈600) y el resto, hasta ≈10.700, se quedan en Odoo 17.
- **Hijos de los contactos principales:**
  - Personas de contacto: sí, con su email y teléfono. Es lo mínimo necesario por RGPD.
  - Direcciones de factura: solo si su dirección es distinta de la del padre. Las ≈5.400 «Invoice Address» suelen ser copias.
  - Direcciones de entrega: solo las que use un expediente abierto o una oferta; el resto se queda en Odoo 17.
  - Estimación de hijos: **≈1,0–1,5 por cada contacto principal**.
- **Exclusiones:** archivados (226); contactos sin padre ni actividad; lugares como contacto principal; registros con `x_studio_secret`.
- **Cuentas bancarias** (hasta 671): solo si Ángel aprueba F0-A02/F0-B04, solo de proveedores dentro del alcance y copiadas de Odoo a Odoo, sin que pasen por chat ni por ficheros.
- **Condiciones de pago:** crear 6, 20 y 60 días en boss20. Antes de crear 75 y 90 días hay que medir si algún proveedor las usa.

## 3. Mapeo de campos Odoo 17 → Odoo 20

- **Copia directa:** `name`, `is_company`, `type`, `street`, `street2`, `zip`, `city`, `state_id` (por código), `country_id` (por código), `email`, `phone`, `lang`, `website`, `comment`, `company_registry`.
  - `vat` va normalizado (sin espacios ni guiones, en mayúsculas).
  - `parent_id` se resuelve con el mapa de ids.
- **Campos sin destino directo:**
  - `mobile` no existe en el modelo base de Odoo 20 (lo he comprobado en `base/models/res_partner.py`); va a `phone` si este está vacío.
  - `x_studio_code` va a `ref` solo si no choca con el id de Odoo 17. Si no, va a una nota.
- **Trazabilidad:** `ref` = id de Odoo 17 (hoy ningún `ref` de boss20 es numérico, así que no hay choques). Así la carga es idempotente.
- **`x_studio_kam` → `user_id`** por correspondencia de usuarios (depende de W08 / F0-C01).
- **`x_studio_type` → `boss_is_customer`/`boss_is_supplier` (`customer_rank`/`supplier_rank`) y `boss_role_ids`** (depende de F0-C02):
  - Cliente → cliente; Cliente+Proveedor → los dos; Proveedor y Acreedor → proveedor; Agente → papel `agent` (más cliente o proveedor según su uso).
  - Expedidor/destinatario → papeles `shipper` y `consignee`, sin rango.
  - PENDIENTE y sin tipo → se deducen del uso (proveedor si tiene facturas de proveedor). Si no hay uso, quedan «pendiente de decisión».
  - Las marcas dan papeles: carrier y airline → `carrier`; customs_agent → `customs_broker`; trucker → `haulier`. Los papeles `handler`, `notify`, `warehouse` e `insurer` no tienen origen en Odoo 17.
  - La validación del ordenante sigue R-A3: al principio solo avisa (no aprobado).
- **`boss_carrier_group_id`:** una lista de variantes por transportista que se revisa antes de cargar. Las 5 entidades de MSC apuntan a una matriz de MSC (F0-B05 está decidida). Cuál es la matriz y qué pasa con las otras familias lo decide Cristina.
- **Pagos y crédito:** `property_payment_term_id` / `property_supplier_payment_term_id` por nombre (los 6, 20 y 60 días necesitan creación). `credit_limit`, nivel de reclamación y `x_studio_payment_type`/`x_studio_remesa` solo si Ángel decide (pendiente).

## 4. Riesgos y ensayo

- **Duplicados:** 205 marcados como mínimo, y hay variantes de sucursal (Maersk, CMA CGM, COSCO).
  - Clave 1: NIF normalizado del contacto principal (los hijos se ignoran).
  - Clave 2: nombre normalizado. Las coincidencias aproximadas van a una lista de revisión y nunca se fusionan solas.
- **Lugares:** se filtran los hijos de entrega cuyo nombre parece un código postal o ciudad y que no tienen email ni teléfono.
- **RGPD:** ≈13.500 personas de contacto.
  - Se migran solo las de contactos dentro del alcance, sin notas libres.
  - Los ficheros intermedios se quedan en el servidor, fuera de Git y del chat.
  - Las cuentas bancarias solo pasan de Odoo a Odoo.
- **Ensayo en boss20, en una transacción que se deshace al final (política 27/10):**
  1. Modo de medición: recuentos exactos por SQL de solo lectura en Odoo 17 (unión de actividad, PENDIENTE sin NIF, valores de NIF repetidos).
  2. Carga completa y recuentos por tipo, papel y familia comparados con `docs/migracion.md`.
  3. Comparación campo a campo de 20 contactos con `read_record`.
  4. Comprobaciones SQL: 0 NIF duplicados entre empresas; las 5 entidades de MSC en la misma familia.
  5. Una segunda ejecución crea 0 registros.
  6. Rollback; la carga real solo cuando haya aprobación.

## 5. Pendiente

- Recuento exacto del alcance (unión de las partes de expediente y partida desde 2024 con asientos y saldos): requiere SQL o XML-RPC de solo lectura sobre Odoo 17.
- Corregir la premisa de F0-B02: los lugares son hijos de entrega, no PENDIENTE.
- Decisiones abiertas: F0-C02 y R-A3 (Cristina), F0-A02/F0-B04 y crédito/reclamación (Ángel), W08 (lista de los 15 usuarios con su papel; idioma es_ES).
- Medir el uso de 75 y 90 días en proveedores.
- Elegir la matriz de cada familia de transportista.
- Destino de las ≈600 aerolíneas IATA sin actividad.
- Destino de `mobile`.
- Por qué boss20 tiene 56 proveedores sin marca de prueba cuando el plan dice 8: los 43 transportistas del catálogo explican la diferencia.
