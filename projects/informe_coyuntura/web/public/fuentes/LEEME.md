# Fuentes servidas desde el propio sitio

Acá va **una sola**: **Garet Bold**.

El Manual de Marca (21-ago-2026) le da a Garet una función exclusiva —el
logotipo "CiGob", la barra de navegación y la firma del pie— y ninguna otra.
Las otras cuatro familias del manual (Lora, Lato, Inter, Work Sans) están en
Google Fonts y las pide `Layout.astro`; Garet **no está**: es comercial.

## Estado actual: el archivo NO está

`marca.css` ya declara el `@font-face` apuntando a `/fuentes/garet-bold.woff2`.
Mientras ese archivo no exista, el navegador cae al stack de reserva
(`Avenir Next` → `Century Gothic` → `Trebuchet MS`), que conserva el aire
geométrico del logotipo. No hay error, no hay pedido fallido visible, no se
rompe nada: sólo el wordmark se ve con otra letra.

## Para completarlo

1. Conseguir la licencia **web** (`@font-face`) de Garet — la licencia de
   escritorio no alcanza para servirla en un sitio.
2. Dejar el archivo acá como `garet-bold.woff2` (peso 700).
3. Nada más: el `@font-face` ya está escrito y toma el archivo solo.

No commitear la fuente sin confirmar que la licencia cubre uso web.
