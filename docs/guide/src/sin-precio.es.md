Cuando una línea no tiene coste, el sistema dice **exactamente qué falta** y ofrece el botón adecuado en la propia
línea. No se crea un servicio nuevo ni se pone un cero.

| Qué falta | Botón en la línea | Qué se abre |
|---|---|---|
| Un dato del envío | — | La explicación indica el campo; se completa en la pestaña Envío |
| La tarifa del proveedor | ⊕ [[Añadir precio de proveedor]] | Formulario de precio, rellenado con los datos de la oferta (ruta incluida) |
| Un flete de esta semana (servicio de importe manual) | ⊕ [[Añadir precio de proveedor]] | El mismo formulario, con **una semana** de validez y la ruta (puerto de origen y de destino) |
| La aprobación | ☑ Revisar el precio | La tarifa; un aprobador pulsa [[Aprobar]] |
| Decidir entre dos tarifas | ☑ Revisar el precio | Las tarifas implicadas, para fijar prioridad |
| La definición del servicio | ? Abrir el servicio | La ficha del servicio y su pregunta pendiente |

## Añadir el precio que falta

![Añadir precio de proveedor desde la oferta](img/05-anadir-precio-proveedor.png)

1. El formulario llega con el **servicio, la base de cobro, el tamaño y tipo de contenedor**, el proveedor (la
   naviera de la oferta), el alcance (sentido, modo, forma de carga, **puerto español y puerto extranjero**, país) y
   la fecha de tarifa. En un flete (importe manual) la validez propuesta es **una semana**: la oferta de la naviera vale
   días, no un año.
2. Indique el **precio unitario**, mínimo/máximo si los hay, la **página** del documento y adjunte
   el **documento del proveedor** (PDF). Puede añadirlo a una tarifa en borrador existente (que ya tiene su PDF) o
   crear una nueva. Con una tarifa existente se muestra su alcance en una línea: marque **Alcance de la tarifa
   revisado** si coincide con el documento.
3. [[Guardar precio]]: el precio se guarda en la tarifa (nunca en la oferta) y se envía a aprobación. La línea pasa a
   «Precio pendiente de aprobación».
4. Un aprobador abre la tarifa desde la misma línea y pulsa [[Aprobar]]. Al cerrar, la oferta se recarga y la línea
   aparece **Cotizada**, sin volver a escribir nada.

> Precios con tramos, porcentajes o por días abren el formulario completo de tarifa (con las mismas propuestas).

## Otros casos

- **Flete y servicios por oferta del proveedor** (FMI, FME, FAI, FAE): dos vías. Se escribe el **coste manual** y su
  referencia (número de oferta) solo para esta oferta; o se guarda la oferta semanal como **precio de proveedor** con
  su ruta (Shanghái → Valencia) y su semana (⊕ en la línea): aprobado, cotiza todas las ofertas de esa ruta esa
  semana, y los precios anteriores quedan como histórico. Fuera de la ruta o de la semana, la línea vuelve a importe
  manual.
- **Proveedor sin precio para ese servicio** (p. ej. WFS en un flete marítimo): al elegirlo, un aviso lo dice; la
  línea queda «Sin precio de proveedor» hasta que exista uno.
- **Servicio propio de BOSS** (CSM, CSA…): ejecutado por BOSS, sin proveedor ni coste; no hay que poner ninguno.
- **Servicios por tiempo** (DEM, OCU, ALM): en la oferta el coste es una **estimación** con los días supuestos
  (pestaña Envío). El coste real solo se conoce al terminar el periodo, en el expediente.
- **Precio vencido**: la explicación dice que hay precios del servicio pero ninguno vigente en la fecha prevista:
  pida el documento actual al proveedor (nueva versión de la tarifa) o revise la fecha.
- **Solo precios de demostración**: la explicación lo dice; un cliente real nunca se cotiza con ellos.
- **Conflicto**: si dos tarifas con el mismo alcance aplican, la línea no elige la más barata; un aprobador fija la
  **prioridad** o se acota una tarifa (por ejemplo, por naviera o puerto).
