---
madr: 4
id: '0351'
estado: 'aceptado'
fecha: 2026-10-10
cinturon: 'transversal'
archivos: ['web/src/pages/[slug].astro']
relacionado: ['0031', '0075', '0092', '0099', '0233', '0336']
ambito: 'Web · qué secciones muestra la página de cada cinturón'
origen: 'Juan, 10-oct-2026: corrección del informe mensual'
---

# ADR-0351 — La página del cinturón sin las secciones de validación

## Contexto y planteo del problema

La página de cada cinturón había ido sumando, debajo de los indicadores, seis
secciones que examinan el índice en lugar de mostrar la coyuntura: la
evolución por dimensión (ADR-0233), la validación externa (y, para gestión, la
explicación de por qué no la tiene, ADR-0336), la validación cruzada
(ADR-0031), la consistencia interna (ADR-0075), el rezago del índice
(ADR-0092) y las fechas de los datos (ADR-0099). Juan pidió sacarlas de las
cuatro páginas como corrección del informe mensual.

## Factores de decisión

- El informe mensual se lee como un informe de coyuntura: lo que va en la
  página es el estado del cinturón y sus indicadores.
- Los cálculos detrás de esas secciones siguen sirviendo para auditar el
  método y no se tienen que perder.

## Opciones consideradas

1. Sacar las seis secciones de la página y dejar intactos los cálculos.
2. Sacarlas y borrar también los cálculos y los datos que las alimentan.

## Decisión

Opción 1. Las seis secciones salen de la página de los cuatro cinturones,
junto con los detalles que abrían (las ventanas de validación externa y
cruzada). Quedan, en este orden: el índice y sus dimensiones, los indicadores,
la robustez, la lectura por partes o el punto de partida donde corresponde,
las fuentes y la nota metodológica.

No se toca nada del cálculo. `validacion_externa.py` sigue corriendo,
`publicar.py` sigue escribiendo la validación en el snapshot, y la
consistencia, los rezagos y las series por dimensión siguen en
`output/` y en BigQuery. La metodología puede seguir citándolos.

### Consecuencias

- Buena: la página del cinturón queda más corta y centrada en la coyuntura.
- Mala: el lector ya no ve en la página los contrastes del índice. Siguen
  disponibles en los archivos de salida y en BigQuery.

### Confirmación

En el seguimiento diario, las páginas `/macro/`, `/politica/`, `/vida/` y
`/gestion/` no muestran ninguno de esos seis títulos, y la ventana de
robustez abre sin errores en la consola.

## Pros y contras de las opciones

### Opción 1

- Bueno, porque es reversible: volver a mostrar una sección es una edición
  de la página.
- Malo, porque quedan cálculos que hoy no se ven en la web.

### Opción 2

- Bueno, porque deja menos código.
- Malo, porque borra herramientas de auditoría del método que siguen siendo
  útiles fuera de la web.

## Más información

ADR-0031, ADR-0075, ADR-0092, ADR-0099, ADR-0233 y ADR-0336 describen las
secciones que se sacan.
