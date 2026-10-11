---
madr: 4
id: '0354'
estado: 'aceptado'
fecha: 2026-10-11
cinturon: 'transversal'
archivos: ['web/src/pages/[slug].astro', 'web/src/components/SemaforoLeyenda.astro', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0337', '0352']
ambito: 'Web · estructura de la página de cada cinturón'
origen: 'Propuesta de corrección del cinturón de la macro (11-oct-2026), revisada con Juan y extendida a los cuatro cinturones'
---

# ADR-0354 — La página de cada cinturón, según la propuesta de macro

## Contexto y planteo del problema

Llegó una propuesta de corrección de la página del cinturón macro, para usarla
después como molde del resto. Respecto de la página publicada cambiaba el
orden y el encuadre: una introducción del cinturón, «Tensión del cinturón» con
el índice explicado debajo, «Cómo se calcula» antes de las dimensiones y un
título propio para el estado de las dimensiones. Al revisarla aparecieron
cinco problemas que venían, casi todos, de la página:

- el título dice «tensión» y el número va al revés (0 = peor, 100 = mejor):
  60,3 se puede leer como «mucha tensión» cuando es verde;
- la leyenda de colores de macro mostraba entre paréntesis los cortes de
  impacto social (105, 95, 85), una escala que macro no usa;
- varias unidades engañaban fuera de su tarjeta: la liquidez en pesos son
  puntos *de tensión* (más es peor), la capacidad prestable son desvíos contra
  su historia y no un «índice», la base imponible y el tipo de cambio real no
  decían su base, la producción industrial no decía que es un promedio de tres
  meses;
- la ayuda de la dimensión «Actividad económica» nombraba tres indicadores y
  tiene cuatro;
- la propuesta, al reordenar, dejaba dicho «las tarjetas de arriba» para unas
  dimensiones que pasaban a estar abajo.

## Factores de decisión

- Los cuatro cinturones salen de una misma plantilla: lo que se acuerde para
  macro vale para todos, respetando lo propio de cada uno.
- La tensión se lee con el color y su palabra (ADR-0337); el índice es otro
  número, que va al revés.
- Nadie tiene que ver en una página una escala que no le corresponde.

## Opciones consideradas

Para el título, que fue lo único con alternativas reales:

1. Como la propuesta, más la palabra del color junto al valor del índice.
2. Exactamente como la propuesta.
3. Titular «Índice» en vez de «Tensión».

## Decisión

Opción 1, elegida por Juan. En los cuatro cinturones:

- **Cabecera**: la introducción del cinturón (la de macro es la de la
  propuesta; las de política, impacto social y gestión se escribieron con el
  mismo molde, nombrando sus dimensiones), la barra «Tensión del
  cinturón …» sin la palabra del tramo encima, y debajo el texto del índice
  —qué mide, 0 peor y 100 mejor (o 100 = fines de 2023 en impacto social)— que
  termina «Hoy marca 60,3/100: sin tensión relevante». El chip del índice sale
  porque repetía ese valor. Sale la nota editorial de macro del 8-oct.
- **Riesgo y banda**: dejan de mostrarse también en política y gestión, como
  ya pasaba en macro.
- **Cómo se calcula** (ADR-0352) va **antes** de las dimensiones, sin su primer
  párrafo, que ahora está en la cabecera. Conserva el párrafo propio de cada
  cinturón (en macro, que las reservas netas son una estimación de CiGob).
- **Dimensiones**: título «Estado de tensión de cada dimensión del cinturón»,
  con el valor del índice y su descripción debajo.
- **Leyenda de colores**: en la página de un cinturón, sólo la escala de su
  índice. La portada sigue mostrando las dos.
- **Robustez**: nombra el método de Monte Carlo.
- **Unidades** corregidas en macro y la ayuda de Actividad con sus cuatro
  indicadores.

### Consecuencias

- Buena: título, número y color dicen lo mismo, y los cuatro cinturones se
  leen igual.
- Mala: política y gestión pierden el riesgo dominante en la cabecera; sigue
  en la portada.

### Confirmación

En `/macro/`, `/politica/`, `/vida/` y `/gestion/`: la cabecera dice
«Hoy marca …: <tramo>», «Cómo se calcula este número» aparece antes de
«Estado de tensión de cada dimensión del cinturón», no hay chip «Riesgo:», y
la leyenda de macro no muestra «(105 o más)».

## Pros y contras de las opciones

### Opción 1

- Bueno, porque respeta la propuesta y la palabra del tramo evita leer el
  índice como tensión.
- Malo, porque suma una palabra al texto de la cabecera.

### Opción 2

- Bueno, porque es literalmente lo pedido.
- Malo, porque deja el título y el número en sentidos opuestos sin aviso.

### Opción 3

- Bueno, porque el número coincide con el título.
- Malo, porque se aparta de la propuesta y de la metáfora del cinturón.

## Más información

ADR-0337 (la tensión se lee sin número) y ADR-0352 (cómo se calcula, en llano).
