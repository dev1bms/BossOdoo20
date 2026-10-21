Tres módulos propios sobre los estándar de Odoo 20 (Producto, CRM, Ventas, `sale_margin`, Contabilidad); no se modifica
el código de Odoo.

| Módulo | Responsabilidad |
|---|---|
| `boss_services` | Catálogo: servicios (productos), bases de cobro (unidades independientes), identidad de Odoo 17, clase de IVA |
| `boss_pricing` | Tarifas de proveedor (documento, vigencia, versiones, aprobación), **motor de cálculo** en Python puro y servicio único `boss.pricing`, importador de tarifas |
| `boss_pricing_sale` | Datos del envío en la oferta, coste/venta/IVA por línea, alta de precio desde la oferta, congelación, foto y recotización |

- **Un único cálculo**: `boss.pricing.price_cost()` elige el precio (regla de [selección](#/seleccion)) y aplica su
  forma de cálculo; `explain()` lo explica. CRM, ofertas y, más adelante, expedientes lo llaman igual.
- **Diferencias de servicios = datos**: las cinco formas de cálculo son genéricas; cada tarifa guarda sus parámetros.
- **Decisiones de diseño** documentadas en ADR (repositorio, `docs/adr`).

## Añadir una forma de cálculo

1. Función nueva en `boss_pricing/engine/methods.py` (parámetros → importe y pasos) y en `METHODS`.
2. Campos de parámetros en el precio de proveedor y en su formulario.
3. Texto de explicación en `boss.pricing._explain_step`.
4. Pruebas del motor (sin Odoo) y, si hay documento, un ejemplo de referencia.
