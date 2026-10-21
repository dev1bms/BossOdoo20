# Preguntas de negocio abiertas · Open business questions

Solo decisiones que cambian el cálculo o el comportamiento y que no tienen respuesta documentada.
Cada una indica qué hace hoy el sistema mientras no se decide (nunca un valor inventado).
Only decisions that change a calculation or a behaviour and have no documented answer; each row says what
the system does meanwhile. Fuentes / sources: `docs/fuentes.md`.
Importes de los ejemplos ilustrativos; las cifras reales de proveedor están en `.research/` (fuera de Git).

| Id | Pregunta / question | Ejemplo | Opciones | Recomendación | Quién | Mientras tanto en el sistema |
|---|---|---|---|---|---|---|
| P01 | ¿Puede el sistema **proponer** un precio de venta por regla (recargo % o margen %) que luego confirma una persona? | THC: coste 100 €, ¿proponer 120 € (+20 %)? | a) Nunca, siempre tecleado · b) Propuesta por servicio/cliente que la persona acepta · c) Solo precios pactados por cliente | b) solo para servicios con regla aprobada; distinguiendo recargo (sobre coste) y margen (sobre venta) | Cristina | Venta tecleada o precio pactado en lista de precios; recargo y margen se muestran separados |
| P02 | ¿Margen mínimo? ¿Quién aprueba vender por debajo? ¿Por unidad, línea u oferta? | THC vendido a 95 € con coste 100 € | a) Solo aviso · b) Bloqueo + aprobación del gestor · c) Mínimo por oferta | a) aviso visible hasta fijar valores | Cristina + Ángel | Margen visible por línea y oferta; sin bloqueo |
| P03 | Política de **cambio de moneda** para costes en USD y regla de **QBR** (quebranto bancario) | Flete en USD en una oferta en EUR | a) No convertir (coste pendiente) · b) Tipo de Odoo de la fecha de la oferta · c) Tipo interno fijo | b) con el tipo congelado al aceptar | Ángel | a): la línea queda «Otra moneda, sin política»; QBR en «pendiente de decisión» |
| P04 | ¿Qué fecha elige la **versión de tarifa**? (ETA importación / ETD exportación; excepciones por proveedor) | IRENEO usa ETD también en importación | a) ETA/ETD siempre · b) Por proveedor | a) por defecto; b) solo con evidencia escrita | Ángel / Cristina | Fecha prevista del envío (ETA o ETD) |
| P05 | ¿Se puede **enviar/confirmar** una oferta con un **coste** aún pendiente? | Despacho sin tarifa del agente de aduanas | a) Sí con aviso · b) Bloquear · c) Bloquear salvo excepción del gestor | a) | Cristina | Aviso visible; se bloquean solo IVA pendiente y precio de venta sin indicar |
| P06 | Si la tarifa cambia durante la validez de la oferta, ¿se respeta el precio o se recotiza? | FuelEU sube de X a Y €/TEU | a) Respetar · b) Recotizar con motivo | b) con «Recotizar» (motivo y fecha guardados) | Cristina + Ángel | Ofertas aceptadas nunca cambian solas; borradores con «Actualizar costes» |
| P07 | ¿Quién puede **recotizar** una oferta aceptada? | El cliente acepta un recargo | a) Comercial · b) Gestor comercial · c) Cristina/Ángel | b) | Cristina | Solo administradores de Ventas |
| P08 | Tipos de contenedor que tienen **precio propio** (HC, reefer, OT/FR) | THC 40'HC igual o distinto de 40'DV | a) Según documento de cada proveedor | a) (ya es dato de tarifa) | — | Condición por tamaño y tipo en cada precio |
| P09 | **DET**: ¿código propio o dentro de DEM? | Hapag factura demoras+detención juntas | a) Propio · b) Dentro de DEM | a) cuando el proveedor lo factura aparte | Cristina | DET «pendiente de decisión» |
| P10 | **ETX** (WFS punto 49 «Recargo de mantenimiento»): concepto, unidad y alcance | Importe fijo por AWB en importación | a) ETX por AWB · b) Otro código | a) | Cristina | ETX «pendiente de decisión» |
| P11 | **PAD**: ¿bajo T3 o GLO? Presentación «THC + gastos portuarios»; IVA de THC (todo EX o una parte EX y el resto NR) | PAD distinto para 20' y 40' | — | Mantener T3-PAD y decidir presentación | Cristina + Ángel | T3-PAD cotiza; IVA según clase EX del servicio |
| P12 | Servicios **solo coste** en Odoo 19 pero vendidos en Odoo 17 (DEM, OCU, VGM, PFT, GLO): ¿se venden y cómo? | DEM recobrado al cliente | a) Venta tecleada · b) Repercusión a coste · c) No se vende | a) | Cristina | Se pueden añadir a la oferta; venta tecleada |
| P13 | **Parámetros derivados**: CAU (dos porcentajes distintos en las fuentes, mínimos), SEG (tasas por país, sobre el valor más un recargo) | Caución sobre los impuestos del DUA | — | Cargarlos como tarifas con documento | Cristina + Ángel | Método porcentaje disponible; sin valores cargados |
| P14 | Factores de **peso tasable** cuando el documento no lo dice (aéreo 167, terrestre 333/270) | WFS no indica factor | a) Peso tasable de la AWB · b) Factor estándar | a) (ya implementado para WFS) | Cristina | Base «kg tasable de la AWB» o factor escrito en la tarifa |
| P15 | **Días**: ¿el día de llegada cuenta como día 1? ¿días naturales o periodos de 24 h? (MSC no lo dice; WFS MAD/BCN por 24 h) | 96 h = 4 periodos o 5 días | a) Según cada documento | a) | Cristina | En la oferta se indican días/periodos estimados |
| P16 | Servicios sin definición: VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM | VET con coste en Odoo 17 | Definir o retirar | Definir los de uso real | Cristina | «Pendiente de decisión», coste manual posible |
| P17 | **IVA**: impuesto de Odoo para NR / EX / NS; Ceuta y Melilla; plan contable | Línea NR para cliente peninsular | Elegir impuestos de la localización española | Instalar l10n_es y mapear con Ángel | Ángel | IVA «pendiente» → la oferta no se puede enviar ni confirmar |
| P18 | **Suplidos** (ARA, PLA, IVA): tratamiento contable y de IVA | Arancel pagado por cuenta del cliente | — | Importe manual a coste, clase NS | Ángel | Importe manual |
| P19 | ¿Quién **aprueba tarifas**? | — | a) Belal y Cristina · b) Gestor de precios | a) (regla actual) | Cristina | Grupo «Aprobador» (administrador por defecto) |
| P20 | ¿Quién ve **coste y margen**? | ¿El operador ve la venta? | — | Comercial y gestor | Cristina | Todos los usuarios de Ventas |
| P21 | ¿Una oferta por envío o **ofertas de tarifa** por ruta (varios envíos)? | FCL mensual Shanghái–Valencia | — | Una por envío en fase 1 | Cristina | Una oferta = un envío |
| P22 | **Alternativas** (varias navieras) en un documento | MSC vs CMA | a) Varias ofertas por oportunidad · b) Secciones opcionales | a) | Cristina | Varias ofertas bajo la misma oportunidad (estándar) |
| P23 | **Validez** por defecto y caducidad | 15 días | — | Ajuste estándar de Odoo | Cristina | Validez estándar (30 días en la base de prueba) |
| P24 | Lista de países «**Lejano Oriente**» (FuelEU) y tráficos «short sea» (THC distinto) | Origen Vietnam | — | Lista escrita por Cristina | Cristina | Muestra MSC limitada a origen China |
| P25 | **AWB**: máster por expediente o house por AWB | 2 AWB en un expediente | — | Por AWB (documento WFS) | Cristina | AWB por guía |
| P26 | **Fusiones** propuestas (CSM/CSA/CST, AMS/ENS, inspecciones) | — | — | Mantener códigos hasta decidir | Cristina | Códigos originales |
| P27 | **Compañía** en Odoo 20: nombre, moneda EUR, país, localización | El servidor está en USD | — | Configurar antes del uso real | Belal / Ángel | Sin cambiar (necesita autorización) |
| P28 | Tarifas **IRENEO 2025**: ¿siguen vigentes en 2026? Porcentaje de combustible y fecha (dos valores en las fuentes) | Transporte zona 3 | — | Confirmar con IRENEO | Cristina | Muestras con vigencia 2025 (no aplican hoy) |
| P29 | Tramos de días «Hasta 7 / Más de 7» (WFS): ¿posicional o toda la estancia? | 10 días: 929,10 vs 1.550,00 | a) Posicional · b) Toda la estancia | a) lectura literal | Cristina | Posicional (configurable por precio) |
