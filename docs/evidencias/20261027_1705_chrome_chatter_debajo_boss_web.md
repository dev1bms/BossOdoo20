# Chatter debajo del formulario (boss_web) en boss20, 27/10/2026 16:55–17:05

Petición de Belal (27/10, captura de E260015): el chatter a la derecha se lleva casi la mitad de la pantalla y los
formularios de BOSS necesitan el ancho. Módulo aparte **`boss_web`** (20.0.1.0.0, depende solo de `mail`, sin
modelos): un parche de `FormRenderer.mailLayout` (nunca «SIDE_CHATTER») y una hoja de estilo para que en pantallas
XXL el formulario fluya en columna (el estándar lo pone en fila). Instalado con `dev/deploy.sh install boss_web`
(commit `a9ea6e1`) y corregido con `dev/deploy.sh update boss_web` (commit `f205099`), servidor en reposo 160 min.

| Pantalla (Chrome, 1600 px de ancho = XXL de Odoo) | Antes | Después |
|---|---|---|
| E260038 (expediente) | Hoja 619 px, chatter 981 px a la derecha | **Hoja 1400 px** (el máximo estándar), chatter **debajo** (a 2435 px del alto de la página), flujo en columna |
| S00311 (oferta) | — | Hoja 1400 px, chatter debajo (a 1818 px) |
| Consola | — | `odoo.loader.failed` vacío; módulo `@boss_web/chatter_below_form` cargado |

Primera versión (solo JS) dejó el chatter sin la clase `o-aside` pero aún al lado: el `FormRenderer` estándar es
`d-flex flex-nowrap` en XXL y `o_xxl_form_view` pone la vista en fila; la hoja de estilo de `f205099` lo corrige
solo cuando el chatter es hijo directo del renderer y no está «aside» (las vistas previas de adjuntos conservan su
fila).
