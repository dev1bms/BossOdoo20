Recorrido probado en boss20 el 27/10/2026 con dos casos reales: la importación aérea de **COFITEL, S.A.** (oferta
[S00032](https://system.bosscontinental.com/odoo/sales/32), aceptada, expediente E260016) y la importación FCL de
**AGUILERA EXTINCION, S.L.** con un 20' DV y un 40' HC (oferta [S00033](https://system.bosscontinental.com/odoo/sales/33), aceptada, expediente E260017).
Los importes de proveedor y de venta son confidenciales: no están en esta guía, sino dentro de Odoo (tarifas,
lista de precios y la nota interna de cada oferta, que dice de dónde sale cada cifra).

Regla de fondo: **el coste sale de la tarifa del proveedor** (aprobada, vigente y que se aplica al envío), **la venta
sale de una lista de precios del cliente o la escribe el comercial**, y lo que falta se ve siempre con su motivo; un
cero nunca significa «gratis» por defecto.

## 1. Usar un servicio existente o crear uno nuevo

| | |
|---|---|
| Menú | Tarifas y proveedores › **Servicios** (o Ventas › Productos › Productos, filtro Servicios BOSS) |
| Registro usado | [HAN] Manipulación en terminal aérea, [FMI] Flete marítimo importación, [THC]… |
| Qué hacer | Buscar primero por código. Solo si no existe: [[Nuevo]], tipo **Servicio**, código, nombre, **Unidad** (= base de cobro), pestaña Precios BOSS |
| Resultado | El servicio aparece en «Añadir servicios» y en las plantillas |
| Comprobación | La ficha muestra **Proveedores**, **Precios vigentes** y **Estado** del servicio |

Un proveedor nuevo **no** crea un servicio nuevo: se añade su precio al servicio que ya existe.

## 2. Unidad y forma de cálculo del servicio

| | |
|---|---|
| Menú | Ficha del servicio › pestaña **Precios BOSS** |
| Campos | **Origen del coste**: Tarifa de proveedor, Importe manual (flete por oferta del agente), Honorario propio de BOSS (sin coste), Pendiente de decisión de negocio. **Forma de cálculo**: Precio por unidad, Tramos, Por día con periodo libre, Porcentaje de una base, El mayor de dos bases. **Unidad** |
| Ejemplos reales | HAN: kg tasable aéreo · AWB y ETX: Guía aérea (AWB) · THC, CCC, PAD: Contenedor · FuelEU: TEU · FAD: Despacho (DUA) · FAI y FMI: Importe manual · CSA y CSM: Honorario propio |
| Resultado | En la oferta, la cantidad sale del envío (kg tasable, contenedores, TEU) |
| Comprobación | En S00033 el FuelEU sale con 1 TEU en el 20' y 2 TEU en el 40' |

## 3. Proveedor y su relación con los servicios

| | |
|---|---|
| Menú | Tarifas y proveedores › **Proveedores** (o Contactos) |
| Registro usado | WORLDWIDE FLIGHT SERVICES (handler), MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U. (naviera), ADUCEX, S.L. y RAMOS VILA, S.L. (agentes de aduanas), SINOTECH LOGISTICS (agente en origen), BARBICAN LOGISTIC (transporte) |
| Campos | Nombre legal, NIF, dirección (se copiaron de Odoo 17), **Roles logísticos** (naviera, handler, transportista, agente de aduanas…) |
| Cómo se relaciona con el servicio | Con su **tarifa**: cada tarifa es de un proveedor y cubre uno o varios servicios. Un servicio puede tener varios proveedores (FAD: Aducex y Ramos Vila) |
| Comprobación | En la ficha del servicio, campo **Proveedores** |

En aéreo, **Expedientes › Aerolíneas y handlers** propone el handler de cada aerolínea en cada aeropuerto (Qatar en
MAD → Iberia, según Odoo 17). El usuario puede cambiarlo en la línea (paso 9).

## 4. Introducir una tarifa real con su documento

| | |
|---|---|
| Menú | Tarifas y proveedores › **Tarifas y documentos** › [[Nuevo]] |
| Registro usado | «WFS importación MAD/BCN desde 01/06/2026», «MSC gastos locales importación (origen China) 09-12/2026», «ADUCEX, S.L. FAD importación FCL» |
| Campos de cabecera | Nombre, **Proveedor**, **Documento del proveedor** (el PDF), **Referencia del documento** (título y edición), Moneda, **Válida desde / Válida hasta** |
| Pestaña Se aplica a | Solo lo que dice el documento: Sentido, Modo de transporte, Forma de carga, Transportista / naviera, Puertos, Países en el extranjero, Provincias (interior), Cliente. Vacío = cualquiera. Marque **Alcance revisado** |
| Pestaña Precios | Una línea por servicio: Servicio, **Base de cobro**, **Forma de cálculo**, **Se cobra por**, Precio unitario, Mínimo, Máximo, Tramos / tramos de días, Días libres, Tamaño y Tipos de contenedor, **Página** del documento |
| Resultado | La línea muestra su **Precio**, su **Cálculo** y un **Ejemplo** calculado con el motor |
| Comprobación | El ejemplo coincide con la cuenta hecha a mano con el PDF |

Ejemplos del documento: WFS punto 12 (manipulación por kg tasable de la AWB, con mínimo por AWB); MSC p.12 (THC por
contenedor; PAD distinto para 20' y 40'; FuelEU por TEU); ocupación MSC p.17 (tramos de días por tamaño).

## 5. Revisar, aprobar y comprobar que se puede usar

| | |
|---|---|
| Botones | [[Enviar a aprobación]] (el aviso amarillo «Antes de enviar» dice lo que falta) → un aprobador revisa con el PDF → [[Aprobar]] |
| Resultado | Estado **Aprobada**: cotiza desde ese momento. Cambiar un precio aprobado = **nueva versión** |
| Comprobación | Tarifas y proveedores › **Probar tarifa**: elija servicio, envío y fecha y compare con su cálculo manual |

El 27/10/2026 se aprobaron 24 tarifas por **delegación de Belal para pruebas**, tras comparar cada línea con su
documento (el chatter de cada tarifa dice qué se comprobó y qué se corrigió). Eso no es la aprobación de Cristina ni
de Ángel. Una tarifa cuyo alcance no tiene fuente sigue **esperando aprobación** (MSC FuelEU «Lejano Oriente sin
China»: la lista de países es una propuesta).

## 6. Precio de venta y su origen

| Origen | Cuándo | Cómo | En la línea |
|---|---|---|---|
| **Lista de precios del cliente** (Odoo estándar) | Acuerdo estable con un cliente | Ventas › Productos › **Listas de precios** › [[Nuevo]]: una regla por servicio, **Precio fijo**, la unidad se rellena sola con la del servicio. En el cliente: pestaña Ventas y compras › **Lista de precios** | **Precio pactado (lista de precios)** |
| **Escrito por el comercial** | Flete y gastos de cada envío, tramos por envío | Columna **Precio unitario** de la línea | **Indicado por una persona** |
| Margen sobre el coste | Regla de margen en una lista de precios | Regla con **Basado en** = coste previsto de la línea | Precio de la regla |
| **Sin cargo** | Se vende dentro de otro servicio | Columna opcional **Sin cargo** | **Sin cargo** |

Registro usado: lista «COFITEL, S.A. · venta importación aérea (oferta 05570 y factura F26 10-0011)» (AWB, CSA,
ETX) con su origen en el chatter. En S00033 el CCC va **Sin cargo** porque se vende dentro del THC.

Precios por envío en una línea por kg (manipulación por tramos de peso, recogida por envío): se escribe el precio
por kg que da el importe del tramo (importe ÷ kg; los precios tienen 4 decimales). **Si cambia el peso, vuelva a
escribirlo**: el precio por kg no sigue los tramos.

## 7. Plantillas

| | |
|---|---|
| Menú | Ventas › Configuración › Pedidos de venta › **Plantillas** |
| Registros | **IAB FOB · Importación aérea FOB · servicios fijos** (FAI, HAN, AWB, CSA, FAD, ETX, TTE-CON) · **IMB FOB · Importación marítima FCL · servicios fijos** (FMI, THC, BL, GLO-CCC, T3-PAD, FAD, CSM, TTE-FCL) · **EAB · Exportación aérea · servicios fijos** |
| Uso | En la oferta: pestaña Otra Información › **Plantilla** |
| Resultado | Una línea por servicio; los servicios por contenedor, una por tamaño y tipo; cantidades desde el envío |
| Si se vuelve a elegir | No se borra nada: se añaden solo los que faltan y un aviso dice cuáles («Plantilla aplicada sin quitar nada») |
| Condiciones | **Términos y condiciones** de la plantilla = texto para el cliente (aparece en la oferta y en las facturas). Las notas internas van en el chatter |

Los servicios a veces necesarios (recogida en origen EXW-AIR, FuelEU, almacenaje, inspecciones, seguro…) se añaden
con [[Añadir servicios]]. Si un servicio ya está, no se duplica («No se añade dos veces»); para un segundo
proveedor del mismo servicio, elija ese proveedor en el asistente.

## 8. Oferta con varios servicios

1. Ventas › Pedidos › Presupuestos › [[Nuevo]] › **Cliente** (la lista de precios y el plazo de pago llegan del cliente).
2. Pestaña **Envío**: Sentido, Modo de transporte, Forma de carga, **Puerto / aeropuerto español**, **País en el
   extranjero**, **Provincia interior** (entrega), **Transportista**, **Fecha prevista** (elige la versión de la
   tarifa), Peso bruto (kg), Volumen (m³), **Peso tasable (AWB, kg)** en aéreo, **Valor de la mercancía**,
   **Contenedores** (tamaño, tipo, cantidad) en FCL, Incoterm, BOSS se encarga de…
3. Otra Información › **Plantilla** → pestaña **Líneas del pedido**.
4. Coste: **Cotizado** (de tarifa), **Importe manual** (escriba **Coste manual**, p. ej. el flete del agente
   convertido a EUR) o los avisos del paso 10. El icono ⓘ explica el cálculo línea a línea.
5. Venta: de la lista de precios o escrita (paso 6). Guarde; vuelva a abrir: todo sigue igual.
6. [[Vista previa]]: lo que ve el cliente (sin costes ni notas internas).
7. [[Confirmar]]: pedido bloqueado y **expediente** creado (S00032 → E260016). No se confirma si falta un precio de
   venta o un coste sin motivo.

Moneda: la oferta va en EUR. Un coste o precio en USD se convierte con el tipo del BCE cargado en Odoo
(Contabilidad › Configuración › Ajustes, sección Monedas: tipos automáticos del BCE) y la referencia se anota en la nota interna.

## 9. Cambiar proveedor o datos del envío y comprobar el recálculo

| Cambio | Probado | Qué pasa |
|---|---|---|
| Proveedor de la línea (columna **Proveedor**) | S00032: HAN, AWB y ETX de Iberia (sin tarifa) a WFS | Pasan de «Sin precio de proveedor» a «Cotizado» con la tarifa de WFS |
| Dos proveedores con precio | S00033: FAD | Sin proveedor: **Varios precios aplican** («elija el proveedor en la línea»). Con Ramos Vila o con Aducex, cada uno con su coste: la diferencia se ve al cambiarlo |
| Peso | S00032: 172 → 350 kg y vuelta | Cantidades y costes de tarifa se recalculan; el chatter guarda cada total. Revise los precios de venta escritos por kg (paso 6) |
| Contenedores | S00033: 20' DV + 40' HC | THC, CCC, PAD, FuelEU y transporte, una línea por tamaño con su precio |

Después de aceptar, un cambio de precio va por [[Recotizar]] con motivo (queda en el historial de precios).

## 10. Avisos: precio que falta, tarifa que no se aplica o en conflicto

| Aviso en la línea | Significa | Qué hacer |
|---|---|---|
| **Sin precio de proveedor** | Ninguna tarifa aprobada y vigente se aplica a este envío (o la que existe es de otro proveedor, alcance o fecha) | ⓘ dice por qué; [[Añadir precio de proveedor]] con su documento, elegir otro proveedor, o (responsable de ventas) **Aceptado sin coste porque** con el motivo |
| **Precio pendiente de aprobación** | Hay precio pero sin aprobar | Aprobarlo (paso 5) |
| **Varios precios aplican** | Dos tarifas valen por igual | Elegir el proveedor en la línea; si son del mismo proveedor, acotar el alcance o fijar prioridad |
| **Faltan datos del envío** | El envío no da un dato que la tarifa necesita (fecha, peso, contenedores) | Completar la pestaña Envío |
| **Importe manual** | Servicio de coste por oferta (flete) | Escribir **Coste manual** |
| **Falta precio de venta** | Precio 0 sin lista de precios | Escribirlo, o marcar **Sin cargo** si va incluido en otro |

Excepciones reales que muestra la prueba: despacho aéreo (solo hay tarifa FCL de los agentes), entrega en Madrid
(sin tarifa de Barbican; la zona de IRENEO para 28140 está sin confirmar), recogida del agente en origen, arrastre
de MSC y venta del FuelEU (en S00033 va «Sin cargo» como en la factura real; decisión comercial pendiente).
