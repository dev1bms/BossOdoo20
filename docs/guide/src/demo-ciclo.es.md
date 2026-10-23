En el sistema hay expedientes de ejemplo, solo con clientes y tarifas **[DEMO]** (importes ilustrativos). Nada está
contabilizado ni confirmado a un proveedor: las compras son solicitudes en borrador y las facturas, borradores. El
servidor no tiene correo saliente. Se rehacen con `dev/demo_cycle.py` (no duplica; los números saltados son de intentos
anteriores anulados).

| Expediente | Ejemplo | Qué enseña |
|---|---|---|
| E260001 | MSC marítimo, 1×20' + 1×40'HC Shanghái → Valencia (S00009) | Solicitud a MSC con THC, BL y demoras; factura en borrador **solo de los THC** (hito); ocupación de muelle extra refacturada con motivo; los derechos (ARA, suplido) los paga y factura el agente de aduanas **sin pedido de compra**. Margen en la aceptación 215 €, previsto 255 € (ver «Coste y rentabilidad») |
| E260002 | WFS aéreo, 500 kg Shanghái → Madrid (repetición de S00010) | **Recálculo con datos reales**: AWB definitiva 620 kg y retirada 3 días más tarde → el handling y el almacenaje suben; la venta no cambia y el margen previsto pasa a negativo: es la señal para refacturar o negociar |
| E260004 | IRENEO terrestre, entrega en Madrid (repetición de S00011) | Transporte por tramos y recargo de combustible en % sobre el transporte |
| E260003 | Solo consignación BOSS (S00018) | Sin compras; **CSA añadido tras la aceptación** con motivo: cuenta en la venta (135 €), no en el margen en la aceptación (90 €) |
| E260009 + E260010 | Una oferta, dos expedientes (S00019, repetición de S00009) | El contenedor de 40' viaja en otro buque: sus servicios (THC y demoras de 40') pasan a E260010; cada expediente con su parte de venta (825 € / 400 €), de coste y su factura |

Lo que solo puede verse en la base de pruebas (no se contabiliza en los libros reales): pedido confirmado, factura de
proveedor contabilizada, abono de cliente, recibo sin pedido y su efecto en el coste real y el margen. Las pruebas
automáticas de `boss_expediente` lo comprueban en una base desechable.
