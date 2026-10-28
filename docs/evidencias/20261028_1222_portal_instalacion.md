# Instalación del portal de clientes (boss_portal, ADR-010) en boss20 — 28/10/2026 12:09–12:21

Aprobado por Belal («موافق، انشر وثبّت boss_portal وشغّل الاختبارات», 28/10). Servidor en reposo antes de cada
despliegue (el único «BUSY» posterior eran los propios usuarios de prueba `prueba_a_appr_*` de la prueba HTTP).

| Paso | Resultado |
|---|---|
| `dev/deploy.sh update boss_pricing_sale,boss_expediente` | 20.0.1.15.0 / 20.0.1.13.0: campos de compra solo internos |
| `dev/deploy.sh install boss_portal` (1.er intento) | **Falló y se deshizo solo**: dos registros con el mismo id externo (`portal_my_shipments`, tarjeta y plantilla). Comprobado después: 0 registros de boss_portal, módulo «uninstalled», sin columnas. Corregido en `c44b69c` |
| `install boss_portal` (2.º intento) | Instalado 20.0.1.0.0, log limpio, web 200 |
| `check_portal` sobre lo desplegado | 45/46: **defecto real** — tras quitar el rol, el usuario seguía viendo ofertas y facturas: Odoo 20 guarda en caché el dominio de acceso evaluado por usuario (`BaseModel._access_domain`). Corregido en `6b3c655` (invalidar la caché al cambiar rol, cliente o empresa del contacto); 46/46 |
| `check_portal_http` (sesiones reales) | 22/25 → diagnóstico: el título sale en español («Tarifas», idioma del cliente), el atributo del total no se emite con valor 0 (bien), y la lectura de la reserva necesitaba una instantánea nueva (artefacto de la prueba); además «Tax Included» bajo «Tarifas» → cambiado a «Precio por unidad de cada línea» (`271d30e`). **25/25** |
| Chrome, enlace de seguimiento de E260038 ([PRUEBA]) | Vista corta: Shanghái → Valencia, salida «Not known yet», llegada «Estimated 11/16/2026 (not confirmed…)», 1 × 40' DV, una novedad publicada; sin cliente, sin HBL, sin documentos, sin la nota interna. Espacio tras «Containers:» corregido (`d86fa93`). Enlace revocado → **404** |
| Código final `d86fa93` | `check_portal` 46/46; regresiones 69/39/53/23/38/22 (`docs/evidencias/20261028_12{19,20}_*_d86fa93e6b8d.txt`) |

Registros de prueba que quedan en boss20 (nombre «[PRUEBA] … Portal HTTP A/B <run>»): clientes, ofertas, un
expediente, sus documentos; los usuarios portal de prueba quedan **archivados y sin rol**. Ninguna invitación enviada,
ninguna cuenta de cliente real activada.

No comprobado todavía en pantalla con un usuario portal en Chrome (las páginas logueadas se comprobaron por HTTP):
Mis envíos, la oferta de tarifas y el formulario de reserva vistos por el cliente.
