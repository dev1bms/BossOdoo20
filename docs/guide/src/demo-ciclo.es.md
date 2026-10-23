En el sistema hay cuatro expedientes de ejemplo, solo con clientes y tarifas **[DEMO]** (importes ilustrativos). Nada
está contabilizado ni confirmado a un proveedor: las compras son solicitudes en borrador y las facturas, borradores. El
servidor no tiene correo saliente. Se rehacen con `dev/demo_cycle.py` (no duplica).

| Expediente | Ejemplo | Qué enseña |
|---|---|---|
| E260001 | MSC marítimo, 1×20' + 1×40'HC Shanghái → Valencia (pedido S00009) | Solicitud a MSC con THC, BL y demoras; factura en borrador **solo de los THC** (hito); coste adicional de ocupación de muelle refacturado al cliente con motivo; derechos (suplido) sin proveedor todavía. |
| E260002 | WFS aéreo, 500 kg Shanghái → Madrid (repetición de S00010) | Handling por kg tasable, AWB y almacenaje estimado comprados a WFS. |
| E260004 | IRENEO terrestre, entrega en Madrid (repetición de S00011) | Transporte por tramos y recargo de combustible en % sobre el transporte. |
| E260003 | Solo consignación BOSS (S00018) | Sin compras: el margen tras costes externos es la venta. |

Lo que solo puede verse en la base de pruebas (no se contabiliza en los libros reales): pedido confirmado, factura de
proveedor contabilizada, abono de cliente y su efecto en el coste real y el margen. Las pruebas automáticas del módulo
`boss_expediente` lo comprueban en una base desechable.
