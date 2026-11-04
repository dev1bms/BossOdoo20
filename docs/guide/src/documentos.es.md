Los documentos de transporte se imprimen desde el expediente. Odoo **no envía nada**: el operativo imprime o copia y
envía.

## Dónde están

Pulse **⋮** junto al número del expediente → **Imprimir**:

| Documento | De qué expediente | Qué es |
|---|---|---|
| **Conocimiento de embarque house (HBL)** | marítimo que no es máster | El BL que BOSS emite como NVOCC |
| **Conocimiento aéreo house (HAWB)** | aéreo que no es máster | El AWB house de BOSS, con el número del AWB máster |
| **Manifiesto de carga** | máster (o envío único) | Una línea por casa: expedidor, destinatario, bultos, peso, mercancía, totales |

Si se pide un documento que el expediente no tiene (un HBL de un aéreo, el manifiesto de una casa), sale una página
que dice por qué y desde dónde imprimirlo. Se imprimen **en inglés** para cualquier usuario: son documentos
internacionales.

## BL y AWB house: borrador y emisión

- Mientras no se emite, el documento sale con **BORRADOR** arriba: es para que el expedidor lo revise.
- [[Emitir HBL]] o [[Emitir HAWB]] (cabecera del expediente) comprueba que estén expedidor, destinatario, puertos,
  buque o vuelo, bultos, peso, mercancía y flete (prepaid o collect); en FCL, el número de cada contenedor; en aéreo, el
  AWB máster. Si falta algo, lo dice. Después pone el número (el del expediente, salvo que se escriba otro) y la fecha
  de emisión, y el botón desaparece.
- **Flete pagadero**: se propone desde el incoterm (C y D: prepaid; E y F: collect) y se puede cambiar en **Referencias
  y fechas**, junto con **Marcas y números**.
- Originales: 3; si el BL es **sea waybill**, «express», cero originales.
- En una casa LCL, los contenedores y precintos que imprime son los de su máster.
- **Un documento emitido no cambia**: al emitir se guarda su PDF en el expediente y cada reimpresión da esa copia,
  aunque después cambien los datos. Para corregirlo: [[Reemitir documento house]] con el motivo; se emite uno nuevo
  (emisión 2, 3…) con la fecha de hoy, las copias anteriores quedan en los adjuntos y el motivo en el historial.
- El BL lleva la cláusula «RECEIVED by the Carrier…» y la declaración de exceso de valor del BL de Odoo 17. Si las
  marcas o la mercancía no caben en su casilla, se imprime «AS PER ATTACHED SHEET» y una hoja aparte con el texto.
- El **AWB emitido** es el juego IATA de Odoo 17: tres originales (verde para el transportista, rojo para el
  destinatario, azul para el expedidor) y siete copias, cada una con el aviso y las condiciones de contrato al dorso
  (20 páginas). El borrador es una sola página.

## Orden de transporte

[[Orden de transporte]] (cabecera): PDF para el transportista con la recogida, la entrega, los contenedores y la
mercancía, sin precios ni la referencia del cliente. Pide el transportista elegido y, en importación marítima con
entrega, el HBL liberado o sea waybill (Cristina).

## Datos para el agente de aduanas

Pestaña **Aduana** → **Datos para el agente de aduanas** y el botón [[Copiar]]: partes con NIF y EORI, DUA, ruta, buque,
MBL/HBL, contenedores con precinto, mercancía (TARIC, bultos, peso, volumen), valor de la mercancía, garantía, y el
**flete, THC, T3 y seguro** vendidos al cliente para el valor en aduana (Cristina, A37). Sale en el idioma del agente
(español por defecto). Quien no ve la venta lo recibe sin importes.
