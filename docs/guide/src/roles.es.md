Los permisos se asignan en **Ajustes › Usuarios** con los grupos estándar de Ventas y dos grupos de BOSS.

| Rol | Grupos | Puede |
|---|---|---|
| Comercial | Ventas: usuario | Oportunidades, ofertas, datos del envío, precio de venta, ver costes y su explicación |
| Comercial que da de alta precios | + Tarifas de proveedor: usuario | Además, crear tarifas y precios **en borrador** y enviarlos a aprobación |
| Aprobador de tarifas | Tarifas de proveedor: aprobador | Aprobar tarifas, cambiar la prioridad de una tarifa aprobada |
| Gestor comercial | Ventas: administrador | Recotizar ofertas aceptadas (con motivo), ajustes de Ventas |

Reglas que el sistema aplica en el servidor (también en importaciones e integraciones):

- Una tarifa se crea siempre en **borrador**; solo un aprobador la aprueba, con un clic.
- Los precios de una tarifa enviada o aprobada **no se pueden modificar**; un cambio es una **nueva versión**.
- Solo se borran tarifas en borrador; las aprobadas se archivan.
- Una línea de una oferta aceptada solo cambia con [[Recotizar]].

> Quién aprueba tarifas y quién ve costes y márgenes son decisiones abiertas (P19, P20 en
> [Decisiones pendientes](#/preguntas)). Por defecto el administrador es aprobador.
