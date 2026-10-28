# Documentos BOSS (boss_documents, ADR-011) en boss20 — 28/10/2026 13:30–15:05

Petición de Belal (28/10): diseño de la factura y de los documentos que salen de BOSS Odoo 20, adecuado al negocio,
a lo pedido por Ángel y Cristina y a la práctica del sector. Despliegue amparado por la política del 27/10
(actualizaciones y despliegues en boss20 sin nueva aprobación); servidor en reposo (SAFE) antes de instalar.

## Punto de partida (leído en boss20 y en Odoo 17)
- boss20: sin plantilla de documento, sin colores, sin pie, sin cuenta bancaria; las unidades (base de cobro) no se
  imprimían (el grupo «Unidades de medida» no tiene usuarios) y ningún dato del envío aparecía en factura ni oferta.
- Odoo 17 (producción): plantilla estándar con la identidad BOSS (verde azulado `#64a8af`, azul marino `#003a5c`,
  Lato), pie «+34 914 90 01 12 boss@bosscontinental.com https://bosscontinental.com/», IBAN Santander en la factura,
  30 días; líneas de texto libre que repiten el número de factura y el cálculo; sin bloque de envío.

## Qué se ha hecho
| Paso | Resultado |
|---|---|
| Módulo `boss_documents` 20.0.1.0.0 → 1.0.3 | Plantilla «Light» + tablas «striped» + colores y fuente de producción + pie de contacto (puesto una sola vez, Ajustes manda después); **bloque de envío** en factura/abono, oferta/pedido y pedido de compra (expediente, oferta, referencia del cliente; Ruta · Transporte · Carga; «Servicios de BOSS: …»); base de cobro siempre impresa junto a la cantidad; sin bloque duplicado de dirección de envío; sin fila duplicada de referencia e incoterm; precio unitario con 2 decimales (4 solo si el valor los tiene) |
| `check_documents` modo WIP (antes de instalar) | 9/9: xpaths válidos sobre Odoo 20, constructor del bloque sobre E260038 y una oferta de tarifas, plantilla del bloque |
| `dev/deploy.sh install boss_documents` | Instalado, log limpio, web 200 |
| `check_documents` modo instalado (1.ª) | 15/16 → **defecto**: el bloque no salía en el PDF: en Odoo 20 un `t-set` dentro del cuerpo de un `t-call` no llega a la plantilla llamada (comprobado con dos renders directos: dentro False / antes True). Corregido (variables antes del `t-call`); además el pedido de compra toma el expediente de su cabecera |
| `check_documents` (2.ª) | 15/16 → la factura creada desde el pedido no encontraba su expediente (solo las líneas del asistente del expediente lo llevan) → busca por la oferta de las líneas. 16/16 |
| PDFs vistos (factura, oferta, pedido de compra) | Seis mejoras: rótulos del bloque sin traducir (Odoo extrae los términos de vistas por elemento, los `span` anidados daban el término con marcado), números en formato inglés («9,850 kg»), precio unitario con 4 decimales («1.800,0000»), destino mezclado con el almacén, referencia e incoterm repetidos, teléfono del pie sin formato. Todo corregido (1.0.3; pie = el de producción) |
| `check_documents` (3.ª, código final de `boss_documents` 1.0.3) | **19/19** (`.research/doc_inst.log`; PDFs en `.research/docs_pdf/`, fuera de Git por llevar precios) |
| Chrome, `/report/html/sale.report_saleorder/162` | Los workers web también lo renderizan: «Expediente E260038 · Oferta S00162», Ruta/Transporte/Carga, «Servicios de BOSS», unidades en cada línea |

Datos de prueba: el expediente E260038 ([PRUEBA]) recibió buque, viaje, B/L, booking, número de contenedor, bultos,
peso, volumen, mercancía y código HS **dentro de la transacción de prueba (deshecha)**; nada queda en boss20 salvo
el pie de empresa (ajuste) y el módulo. No se ha tocado ningún impuesto ni cuenta bancaria.

## Pendiente de Ángel (datos, no código)
Cuenta bancaria a imprimir en la factura (en Odoo 17 sale la de Santander; en boss20 no hay ninguna); textos legales
de los impuestos al 0 % («0% EX S» ya imprime el artículo 22; «0% S NS», «0% UE S» …); texto del plazo de pago;
línea del Registro Mercantil para el pie si la quiere.
