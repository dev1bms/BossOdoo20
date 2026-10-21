# Estándar de Odoo frente a desarrollo propio · Standard vs custom

| Necesidad | Estándar de Odoo 20 usado | Desarrollo BOSS | Motivo (evidencia) |
|---|---|---|---|
| Servicio | `product.product` tipo servicio, código, categoría, traducciones | Campos de origen del coste, método, clase de IVA, códigos anteriores | Hoja de servicio BOSS |
| Base de cobro | `uom.uom` (unidades independientes) | Origen de la cantidad | Odoo convierte unidades sin relación 1:1 sin avisar (spike T4b) |
| Oportunidad → oferta | CRM, `sale_crm` «Nuevo presupuesto», etapas, actividades | — | Estándar suficiente |
| Datos del envío | — | Pestaña «Envío» en la oferta (dirección, modo, forma, puerto, país, provincia, contenedores, pesos, días) | No existe en Odoo |
| Precio de proveedor | — (`product.supplierinfo` no sirve) | Tarifa con documento, página, vigencia, versión, aprobación y condiciones | supplierinfo elige el más barato entre unidades e ignora condiciones (T5) |
| Cálculo | — | Motor único en Python puro + `boss.pricing` | Métodos por tramos, porcentaje, tiempo, mínimos por línea |
| Coste en la oferta | `sale_margin` (coste unitario, margen) | Coste calculado y explicado por línea | El coste estándar es uno por producto |
| Precio de venta | Lista de precios (precios pactados), precio tecleado | Guardas: unidad obligatoria y sin solapes; cero ≠ gratis | Fallback silencioso y conflictos silenciosos (T2, T3) |
| IVA | Impuestos y posiciones fiscales | Reglas de Ángel (NS/EX/NR, zonas, cliente) → impuesto configurado | Las reglas no se expresan con posiciones fiscales simples |
| Moneda | Monedas y tipos de Odoo | Política de conversión explícita | No sumar monedas sin política |
| Aceptación | Confirmar pedido | Congelación + foto + recotizar con motivo | Odoo recalcula pedidos confirmados (T7c/d) |
| Permisos | `ir.access`, grupos de Ventas | Grupos «usuario de tarifas» y «aprobador»; bloqueos en servidor | Aprobación humana obligatoria |
| Documentos | Adjuntos (`ir.attachment`), chatter | Documento y página en cada tarifa | Trazabilidad |
| Importación | — | Importador idempotente de tarifas (JSON) | Muestras y cargas futuras |
