# Revisión completa: peticiones de Ángel (reuniones del 27/10/2026) frente a lo desplegado en boss20 — 28/10/2026

Fuentes: `docs/reunion-angel-2026-10-27.md` (parte 1), `docs/reunion-angel-2026-10-27-parte2.md`, los siete fragmentos
de la segunda reunión entregados por Belal el 28/10, el mensaje de Teams de Ángel sobre pesos, y la matriz
`docs/matriz-reunion-2026-10-27.md` (65 puntos: 42 de la lista de revisión + 23 de los fragmentos).

## 1. ¿Lo desplegado es lo programado?
Sí. Los 156 ficheros de los seis módulos BOSS en boss20 son idénticos byte a byte al commit `b0f79fc` (comparación
md5 del contenido de Git con el servidor, 28/10) y las versiones instaladas coinciden con los manifiestos
(boss_services 20.0.1.4.0, boss_pricing 20.0.1.11.0, boss_pricing_sale 20.0.1.15.0, boss_expediente 20.0.1.13.0,
boss_web 20.0.1.0.0, boss_portal 20.0.1.0.3). Pruebas sobre ese código: 69 + 39 + 53 + 23 + 38 + 22 + 46 (+ 25 HTTP),
todas en verde (`docs/evidencias/20261028_12*_d86fa93e6b8d.txt`).

## 2. Estado de los 65 puntos
| Estado | Puntos | % |
|---|---|---|
| CERRADO (código + prueba + visto en pantalla) | 50 | 77 % |
| IMPLEMENTADO, falta verlo en pantalla | 6 (7 transportista terrestre, M2-3 familia de transportista, M2-12 documento obligatorio, M2-14 versiones sucesivas, M2-19 coste a petición, M2-21 oferta de tarifas) | 9 % |
| PARCIAL | 5 (13 plantillas = propuesta, 34 S00034 de Ángel, M2-11 formato español, M2-20 proveedores por servicio, M2-23 partidas) | 8 % |
| DECISIÓN de Ángel/Cristina | 3 (38 WFS por aprobar, M2-6 aranceles por código, M2-17 precios de venta de Cristina) | 5 % |
| ABIERTO | 1 (40 migración de contactos de Odoo 17) | 2 % |

Avance técnico (cerrado + implementado): **56/65 = 86 %**. Contando los parciales a medias: **90 %**. Lo que falta es
casi todo decisión o dato del negocio, no programación.

## 3. Lo que Ángel encontrará en una prueba real (datos de boss20 el 28/10)
- Flujo importación marítima FCL con la plantilla «IMB FOB»: completo — plantilla → ruta → contenedores → costes →
  venta (+20 %) → confirmar → expediente → compras → facturas → resumen por grupo. Precios aprobados reales: 13 de
  los 52 servicios con tarifa (THC, BL, GLO-CCC, T3-PAD, DEM, OCU, FAD, HAN, TTE-CON, ALM, FMI…).
- En «IMB FOB»: FAD tiene dos agentes de aduanas con precio (ADUCEX y RAMOS VILA): la línea pide elegir proveedor
  (no es error, pero conviene un proveedor por defecto: decisión). TTE-FCL no tiene tarifa: «Coste a petición».
  CSM es honorario BOSS: su venta se teclea.
- Solo hay plantillas para importación aérea (IAB), importación marítima FCL (IMB) y exportación aérea (EAB): no hay
  plantilla de exportación marítima, grupaje (LCL) ni terrestre.
- Venta: solo «coste + 20 %»; los precios fijos de venta de Cristina (sus Excel) no están cargados.
- Clientes reales en boss20: 2; proveedores reales: 8 (la migración de contactos de Odoo 17 está pendiente).
- Ángel y Belal tienen la interfaz en inglés (fechas y números al estilo de EE. UU.); Ángel pidió números a la
  española: cambiar su idioma a español es un clic, con su permiso.
- Tarifa WFS (58) en espera de aprobación; S00034 (de Ángel) sigue sin poder confirmarse por sus datos (cliente sin
  país, 4 ventas sin precio).
- Correo saliente: no hay servidor configurado (nada sale a clientes ni proveedores durante las pruebas).

## 4. ¿Está listo para que Ángel pruebe?
Sí, para el caso que usó en la reunión (importación marítima FCL de un cliente BOSS) de punta a punta, y para los
cambios de la segunda reunión (flete por ETD, flete semanal aprobado al introducirlo, versiones por ruta, oferta de
tarifas, coste a petición, resumen por grupo). No todavía para operar con clientes reales: faltan los precios de venta
de Cristina, las plantillas de los demás casos y los contactos de Odoo 17.

## 5. Propuesta de siguiente paso
1. **Sesión de prueba guiada con Ángel (1 h)** con un guion de 10 pasos sobre un caso real suyo (ver §6), con su usuario
   en español; anotar cada diferencia como punto nuevo de la matriz.
2. **Cristina**: sus Excel de venta → precios fijos por servicio en la lista general; validar las plantillas
   (R-S1) y decidir qué servicios son fijos y cuáles variables (M2-17); ¿documento del proveedor obligatorio? (M2-B).
3. **Ángel**: aprobar o rechazar WFS 58; proveedor por defecto de FAD; momento del expediente en una oferta de
   tarifas (M2-C); aranceles por código (M2-D).
4. **Belal**: migración de contactos y direcciones de Odoo 17 (R-A4), condición para operar con clientes reales.
5. Después, piloto del portal con un cliente de confianza (ADR-010).

## 6. Guion propuesto para la prueba de Ángel
1. Nueva oferta › plantilla IMB FOB: comprobar sentido, modo, carga, incoterm FOB y servicios.
2. Ordenante, destinatario propuesto, origen (puerto extranjero), destino ESVLC, almacén de entrega.
3. ETD y ETA; contenedores 2 × 40'.
4. Líneas: coste y venta por línea (ⓘ: origen del precio; flete por ETD).
5. Flete sin precio › ⊕: precio de esta semana (aprobado al introducirlo) → la línea se valora sola.
6. FAD: elegir agente; TTE-FCL: «Coste a petición»; CSM: teclear la venta.
7. Cambiar la venta de una línea a mano; cambiar de naviera y ver que la venta fija no cambia.
8. Confirmar → expediente; pestaña Resumen por grupo.
9. Crear compras, factura de proveedor, factura parcial al cliente → Resumen pendiente/definitivo y facturado.
10. Oferta de tarifas 20'/40'/40' HC: PDF sin total.
