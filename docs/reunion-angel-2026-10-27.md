# Reunión con Ángel (27/10/2026): requisitos, diferencias y plan

Fuente: transcripción de la reunión Belal–Ángel del 27/10/2026 (revisión en pantalla de una oferta FCL de importación en
boss20). Contrastada con Odoo 17 en producción (solo lectura: `x_spot` = oferta, `x_dashboard` = expediente,
`x_partidas`, `x_traficos`, `x_puertos`) y con el proyecto Odoo 19 (`boss.location`, `boss.traffic`, decisión B13).
Ángel pidió entender el negocio antes de implementar: lo que sigue separa lo que dijo (confirmado), lo que se deduce
(supuesto, marcado) y lo que queda abierto. Nada abierto se implementa como regla.

## 1. Conocimiento del negocio explicado por Ángel

- **Peso tasable**: hay peso real y peso volumen (un m³ de plumas pesa poco). El proveedor factura por **el mayor de
  los dos**. En aéreo el factor es **167 kg por m³** («For air shipment, yes»). Odoo 17 lo calcula igual
  (`x_dashboard.x_studio_chargeable_weight`: marítimo 1000, aéreo 167, terrestre 333).
- **Origen y destino**: un envío se describe como origen → destino (país, puerto o aeropuerto, lugar), no como
  «importación + país en el extranjero». Ejemplo de exportación: recogida en Zaragoza, camión a Barcelona, barco a
  Túnez. Ejemplo de importación: China → Valencia → entrega en Madrid (Susaeta). Zaragoza no tiene puerto: el puerto es
  Valencia o Barcelona y el tramo terrestre llega a la dirección.
- **Lado español a la derecha en importación y a la izquierda en exportación**: el destino de una importación y el
  origen de una exportación son España.
- **Dirección de entrega / recogida**: si el cliente indica dónde, la provincia (y el precio del transporte) sale de
  esa dirección. Un cliente con varios almacenes (Leroy Merlin) elige uno; si no tiene dirección, se escribe a mano.
- **Fechas**: ETD (salida del puerto de origen) y ETA (llegada al puerto de destino) son **dos campos distintos y se
  necesitan los dos**. En importación la fecha importante es la llegada; en exportación, la salida. La «fecha de
  entrega» de la oferta es la entrega final al cliente (puede quedar vacía; la mercancía puede esperar semanas en el
  puerto después de la ETA).
- **Transportista principal** = naviera o aerolínea. El transportista terrestre es el camionero.
- **Contenedores**: casi nunca van paletizados (se llenan como una pared de carga). El peso bruto de un contenedor
  completo importa poco en la oferta; el valor de la mercancía casi nunca se conoce al ofertar.
- **Cualquier dato se puede poner en la oferta o más tarde en el expediente**.
- **Almacenaje estimado: siempre 0** (99,9 %), salvo que el cliente diga que la carga esperará.
- **Quién encarga («order», ordenante)**: puede ser nuestro cliente o un **agente** (un transitario como BOSS en otro
  país). Los agentes son socios, no clientes, aunque a menudo se les factura. La 3.ª letra del código de tráfico lo
  dice: **B = cliente de BOSS, A = cliente del agente** (IMB, IMA…). Odoo 17: `x_dashboard.x_studio_ordenante`
  («Orderer»), facturar a = ordenante.
- **La plantilla de oferta es el caso**: al elegir «importación FCL» los datos del envío deben venir rellenos
  (sentido, modo, tipo de carga, incoterm) y la plantilla dice qué gestiona BOSS (recogida, aduanas, transporte
  principal, entrega).
- **La semana empieza el lunes.**

## 2. Requisitos

| # | Requisito | Estado | Implementación |
|---|---|---|---|
| R1 | Envío como origen y destino (país, puerto/aeropuerto, dirección, lugar); puerto en el extranjero | Confirmado | Modelo común `boss.shipment.route` (oferta y oportunidad) y mismos campos en el expediente; puerto español, país en el extranjero y provincia se **derivan** (ADR-006) |
| R2 | Lado español: derecha en importación, izquierda en exportación | Confirmado | Formulario en dos columnas Origen / Destino |
| R3 | Provincia calculada de la dirección de entrega (importación) o recogida (exportación); varias direcciones por cliente; dirección manual si no hay | Confirmado | Direcciones = contactos de tipo entrega del cliente (como Odoo 17); se pueden crear desde la oferta |
| R4 | País en el extranjero sin España | Confirmado | El lado extranjero nunca es España; el lado español se pone en España |
| R5 | ETD y ETA, dos campos; fecha clave: ETA (importación), ETD (exportación) | Confirmado | `boss_etd`, `boss_eta`; la «fecha de tarifa» se deriva (antes «Fecha prevista», un solo campo) |
| R6 | «Customer» → «Ordered by» (quien encarga: cliente o agente) | Confirmado | Etiqueta «Ordered by» / «Ordenante» en oferta y expediente |
| R7 | Negocio BOSS o del agente (B/A) y código de tráfico | Confirmado (B13) | `boss_business` + `boss_traffic_code` (IMB, EAB, IMA…) en plantilla, oferta, oportunidad y expediente |
| R8 | La plantilla rellena el caso (sentido, modo, carga, incoterm, B/A) y lo que gestiona BOSS | Confirmado | Campos de caso en `sale.order.template`; se aplican al elegir la plantilla |
| R9 | Transportista = principal (naviera/aerolínea) | Confirmado | Etiqueta «Main carrier»; el camionero es el proveedor del servicio de transporte |
| R10 | Peso tasable aéreo = mayor de bruto y volumen × 167 | Confirmado | Peso volumen y tasable calculados; sin AWB, los precios «por kg tasable de la AWB» usan el tasable estimado y la explicación lo dice |
| R11 | Almacenaje estimado 0 por defecto; quitar la casilla «Días indicados» | Confirmado | Casilla fuera de la pantalla; 0 días por defecto |
| R12 | Tamaño/tipo de contenedor solo donde aplica | Confirmado | Ocultos en precios y en «Probar tarifa» para aéreo, grupaje y terrestre |
| R13 | Incoterm visible en el caso | Confirmado | Incoterm en la cabecera del envío y en la plantilla |
| R14 | Datos de carga opcionales en la oferta, completables en el expediente | Confirmado | Ya opcionales; el expediente recibe el valor de la mercancía y los derechos estimados |
| R15 | Semana desde el lunes | Confirmado | Idiomas activos con lunes como primer día |
| R16 | «Delivery date» = entrega final al cliente | Confirmado (aclaración) | Etiqueta «Final delivery to the client» |

## 3. Supuestos (deducidos, a confirmar)

| # | Supuesto | Por qué | Quién confirma |
|---|---|---|---|
| S1 | Los datos de caso de las tres plantillas actuales: IAB FOB = importación · aéreo · carga aérea · FOB · cliente BOSS; IMB FOB = importación · marítimo · FCL · FOB · cliente BOSS; EAB = exportación · aéreo · carga aérea · cliente BOSS, sin incoterm | Salen del código (IAB/IMB/EAB, B13) y del nombre | Cristina |
| S2 | Lo que gestiona BOSS en cada plantilla se deduce de sus servicios (FAD → aduana en destino, TTE → entrega o recogida, flete → transporte principal) | Ángel: «in the template it must select what BOSS handles» | Cristina |
| S3 | Puertos en el extranjero = los 9.528 puertos y aeropuertos de Odoo 17 (`x_puertos`, ya pasados a Odoo 19) | Ángel: «Let's see the Odoo 17. If you copy this, it's perfect» | — (datos maestros) |

## 4. Abierto (no se implementa como regla)

| # | Tema | Situación |
|---|---|---|
| A1 | Factor de peso tasable **terrestre** (333) y marítimo (1000) generales | **Resuelta** el 27/10 (mensaje de Ángel en Teams): aéreo 167, terrestre 333, marítimo 1000 kg por m³; peso tasable = el mayor del real y el volumen; los proveedores cobran a BOSS y BOSS cobra al cliente por peso tasable. Implementado (enmienda de ADR-006) |
| A2 | Tráficos cruzados (X) y nacionales (N) | Existen en Odoo 17 (`x_traficos`: XMA/XMB, NTB…); Odoo 20 solo tiene importación y exportación |
| A3 | ¿Quién es el ordenante en un expediente de agente? (B17 de Odoo 19, abierta) | Se guarda B/A; validar el tipo de contacto (Agente / Cliente) como Odoo 17 queda pendiente |
| A4 | Migración de contactos y direcciones de Odoo 17 | Belal: «I will migrate all the users». Hoy hay que crearlos; Odoo propone empresas de internet que no son clientes |
| A5 | Fecha clave de un LCL de importación (Odoo 17 usa la fecha de vaciado) | En la oferta se usa la ETA; en el expediente ya existe la fecha de vaciado |

## 5. Diferencias encontradas (antes de este cambio)

1. La oferta tenía «Puerto español» + «País en el extranjero»: sin puerto extranjero ni orden origen → destino.
2. Un solo campo «Fecha prevista» (ETA o ETD según el sentido).
3. La provincia se elegía a mano; no había dirección de entrega/recogida (solo texto libre).
4. «Customer» en la oferta; no se distinguía cliente BOSS de cliente de agente.
5. La plantilla solo traía servicios: había que volver a escribir sentido, modo, incoterm.
6. Peso tasable de la AWB obligatorio para precios aéreos por kg: sin AWB, «faltan datos».
7. Casilla «Días indicados» y almacenaje «sin indicar» por defecto.
8. Tamaño y tipo de contenedor visibles en precios aéreos.
9. Solo 12 puertos (todos españoles).
10. Semana desde el domingo en inglés.

## 6. Plan y pruebas

1. ADR-006 (modelo de datos del envío). 2. Modelo común de ruta + oferta + plantilla. 3. Expediente y oportunidad.
4. Pantallas y traducciones. 5. Datos en boss20: puertos, plantillas, lunes. 6. Despliegue en boss20 (no es
producción: producción sigue siendo Odoo 17). 7. Pruebas en boss20 con casos reales:

| Caso | Datos | Resultado esperado |
|---|---|---|
| E1 Importación FCL (plantilla IMB FOB) | Ordenante cliente BOSS; Shanghái → Valencia; entrega en un almacén de Madrid; 1×40' HC; ETA | Sentido/modo/carga/FOB/B desde la plantilla; código IMB; puerto español ESVLC, país CN, provincia Madrid derivados; precios marítimos como antes |
| E2 Exportación marítima | Recogida en Zaragoza; Barcelona → Túnez; ETD | Puerto español ESBCN, país TN, provincia Zaragoza; fecha de tarifa = ETD |
| E3 Importación aérea sin AWB (plantilla IAB FOB) | 500 kg, 4 m³ (4 × 167 = 668 kg) | Tasable 668 kg; HAN de WFS (cuando se apruebe) / IRENEO sobre 668 kg con la explicación «estimado» |
| E4 Cliente del agente | Mismo caso con «Agent's client» | Código IMA |
| E5 Expediente | Aceptar E1 | El expediente recibe origen/destino, direcciones, ETD/ETA, B/A |
| E6 Datos antiguos | Ofertas y expedientes existentes | Puerto/país/provincia/fecha sin cambios; origen/destino rellenados por la migración |
