Para cada línea, el sistema aplica **una única regla**, la misma en todas las pantallas:

1. Precios del **mismo servicio y la misma base de cobro**.
2. **Vigentes** en la fecha prevista del envío (todas las versiones, no solo la última aprobada).
3. **Aprobados**. Si solo hay precios sin aprobar que encajan → «Precio pendiente de aprobación».
4. Que **encajen con el envío**: sentido, modo, forma, naviera, puerto, país, provincia, cliente, tamaño y tipo de
   contenedor. Si un precio necesita un dato vacío → «Faltan datos del envío» (no se adivina).
5. **Prioridad** (número menor gana).
6. Dentro de una misma tarifa, la **versión más nueva**.
7. El **más específico**: un precio con más condiciones (por ejemplo, para un cliente) gana al general.
8. Si aún quedan varios → **«Varios precios aplican»**. Nunca se elige el más barato ni el primero.
