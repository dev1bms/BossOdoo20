Una **consolidación** es un envío con **un documento máster** (MBL o MAWB) y **varias casas** (HBL o HAWB), cada una
de un cliente. En Odoo 20 el máster es un expediente y cada casa es otro expediente enlazado a él (ADR-013).

## Cómo se monta

1. Cada casa nace de su oferta aceptada, como cualquier expediente: su cliente, su carga, su aduana y su factura.
2. El **máster** es un expediente con el transportista, el buque o vuelo, el booking, el MBL/MAWB, las fechas y los
   contenedores, y con las compras compartidas (flete, gastos locales, transporte del contenedor).
3. En cada casa, el campo **Expediente máster** la cuelga del máster; o desde el máster, [[Nueva casa]] crea una casa
   con el mismo caso y ruta.

## Qué hace el sistema

- Los datos de transporte del máster (transportista, buque, viaje, booking, MBL/MAWB, fechas) **se copian a las casas**
  y siguen sus cambios. Un aviso azul en la casa lo recuerda.
- Los servicios que el máster compra (por ejemplo el flete o los THC) quedan en las casas como **comprados en el
  máster**: no se piden dos veces.
- Las compras compartidas se **reparten** entre las casas por peso tasable (W/M), peso bruto, volumen, partes iguales o
  a mano (campo **Costes compartidos repartidos por** del máster). Cada casa ve su parte y su margen con ella; el
  máster ve el **margen consolidado** de todas.
- [[En tránsito]] del máster lleva sus casas abiertas; la ATA del máster las pone en **Llegado**.
- El cierre económico va en orden: el máster no se cierra mientras una casa siga abierta.
- Cada casa imprime su **BL o AWB house** y el máster el **manifiesto de carga**: ver [Documentos de transporte](#/documentos).

## Ejemplo en el sistema

**E260231** es un máster [PRUEBA] (un contenedor de 40' HC, modelo de un expediente real de Odoo 17) con dos casas,
**E260232** y **E260233**. La explicación con dibujos del antes y el después está en `docs/consolidaciones.html`.
