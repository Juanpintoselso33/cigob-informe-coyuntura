---
madr: 4
id: '0102'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'gestion'
indicadores: [rigi_inversiones]
ambito: 'ITCG · `rigi_inversiones` · modal del indicador'
origen: 'Auditoría externa del cinturón de gestión (doc 2), punto 3.6'
---

# ADR-0102 — El RIGI avisa cuando su porcentaje baja por el denominador

## Contexto y planteo del problema

> "El punto más delicado, ya señalado en la propia ficha, es que **el
> denominador es móvil**: cada vez que se anuncia un proyecto grande «en
> evaluación», el porcentaje aprobado puede bajar aunque nada haya empeorado. Es
> un artefacto matemático que conviene explicar cada vez que el indicador
> retrocede, para no leerlo como retroceso de gestión."
>
> "Recomendación: acompañar siempre el % con el monto absoluto aprobado en USD
> (que sí es monótono creciente)."

## Opciones consideradas

- **Emitir `nota_denominador` sólo cuando el caso se da** — elegida: el porcentaje bajó respecto de la lectura anterior *y* la inversión aprobada subió.
- **Avisar siempre** — descartada.

## Decisión

El colector emite `nota_denominador` **sólo cuando el caso se da**: el
porcentaje bajó respecto de la lectura anterior **y** la inversión aprobada
subió. El modal la muestra encabezada por "Por qué bajó sin que nada empeorara".

El caso ocurrió entre junio y julio de 2026 y el aviso, con datos reales, dice:

> El porcentaje bajó de 22,1% a 22,0% y aun así la inversión aprobada **creció**,
> de US$ 27.760M a US$ 31.192M. No es un retroceso: el indicador mide la porción
> aprobada del total, y ese total se agranda cada vez que se presenta un proyecto
> nuevo. Entraron US$ 3.432M de inversión aprobada y, al mismo tiempo, más
> proyectos a la cola de evaluación.

### Lo que el aviso NO hace

**No aparece cuando el retroceso es genuino.** Si el porcentaje baja y el
capital aprobado también, no hay artefacto que explicar y la nota calla. Esa es
la parte que le da valor: un aviso que apareciera siempre sería una disculpa
permanente, y dejaría de informar precisamente cuando el retroceso fuera real.

Tampoco aparece cuando el porcentaje sube, ni cuando no hay lectura anterior
utilizable.

### Consecuencias

- Tres tests cubren los cuatro casos: artefacto, retroceso genuino, mejora y
  ausencia de datos previos.
- La función acepta los valores previos como parámetros para poder probarse sin
  depender del estado del caché; si no se pasan, los toma del snapshot anterior.

## Más información

### Limitaciones

- **El aviso compara contra la lectura anterior**, no contra un máximo
  histórico. Una caída sostenida a lo largo de varios meses, cada uno con
  crecimiento del capital aprobado, generaría el aviso todos los meses — lo cual
  es correcto, pero conviene saber que no acumula.
- El indicador **sigue midiendo la porción aprobada del pipeline**, con el
  problema de fondo intacto: un país que atrae muchos proyectos nuevos puntúa
  peor que uno que no atrae ninguno. El aviso lo explica; no lo corrige.
  Cambiarlo exigiría decidir qué es "el total" de una cartera abierta, que es una
  pregunta sin respuesta obvia.

### Lo que ya estaba resuelto

Dos cosas de la recomendación ya existían y conviene decirlo antes de agregar
nada:

- **El monto absoluto ya se publicaba** en el detalle de la card: "17 proyectos
  aprobados (US$ 31.192M) / 25 en evaluación (US$ 110.883M) → 22,0%".
- **El gráfico del modal ya usa el monto, no el porcentaje.** `UNIDADES_SERIE`
  tiene un override explícito —`rigi_inversiones: "US$ M aprobados"`— con el
  comentario "card = % del pipeline; serie = inversión aprobada acumulada". Se
  verificó antes de tocarlo, en lugar de asumir que estaba mal.

Lo que faltaba no era el dato: era **la explicación en el momento en que hace
falta**.
