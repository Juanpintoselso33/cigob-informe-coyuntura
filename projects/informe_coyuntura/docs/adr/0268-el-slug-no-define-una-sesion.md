---
madr: 4
id: '0268'
estado: 'aceptado'
fecha: 2026-08-26
cinturon: 'politica'
indice: 'ITCP'
indicadores: [paralisis_denuncias]
archivos: ['scripts/politica.py', 'data/politica/denuncias_comisiones_universo.json', 'tests/test_politica_judicial.py', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
corrige: ['0134', '0170']
relacionado: ['0045', '0168']
ambito: 'Cinturón político (ITCP) · dimensión Poder judicial · universo de sesiones de las comisiones de control'
origen: 'Reverificación 69/69 del 26-ago-2026: el extractor contaba una forma de URL, no el universo que la card declaraba'
---

# ADR-0268 — El slug no define una sesión

## Contexto y planteo del problema

`paralisis_denuncias` decía contar cuántas veces sesionaron las comisiones de
Acusación y Disciplina, pero el extractor sólo aceptaba slugs de la forma
`sesiono-la-comision-...-N`. El número final no es un número oficial suficiente
para validar cobertura: WordPress lo usa para desambiguar títulos repetidos.

El criterio omitía dos clases completas de reuniones:

- notas que cubren una jornada con varias comisiones, aunque el título y el
  cuerpo dicen expresamente que la comisión objetivo sesionó;
- notas cuyo título destaca el resultado de la sesión. El extractor dejaba
  fuera las reuniones de Acusación del **6-ago-2025**, **17-mar-2026** y
  **28-may-2026**, precisamente las que resolvieron avanzar contra magistrados;
  las dos últimas integran la ventana vigente.

El valor publicado era 7. El inventario completo de la misma fuente da 14 en
los doce meses calendario de septiembre de 2025 a agosto de 2026.

## Factores de decisión

- La definición pública cuenta sesiones de las dos comisiones, no títulos con
  una convención particular de WordPress.
- Una nota puede documentar inequívocamente una sesión aunque el título destaque
  su resultado o agrupe varias comisiones.
- La unidad necesita una clave de deduplicación estable para que republicaciones
  o categorías compartidas no inflen el total.
- Corregir el universo no autoriza a recalibrar las bandas mirando el resultado.

## Opciones consideradas

1. Conservar sólo las sesiones con slug numerado.
2. Contar toda sesión documentada, deduplicada por fecha y comisión, y excluir
   actos que no son sesiones.
3. Agregar únicamente las tres sesiones sustantivas detectadas por la auditoría
   y mantener fuera las reuniones extraordinarias o publicadas junto con otras
   comisiones.

## Decisión

La unidad estadística es **una comisión que sesiona en una fecha**.

Se incluyen:

- sesiones ordinarias, tengan o no número en el slug;
- sesiones extraordinarias;
- sesiones cuyo título destaca un dictamen o una remoción, cuando el cuerpo
  afirma explícitamente que la decisión se tomó en sesión;
- sesiones publicadas en una nota que agrupa varias comisiones y sesiones
  conjuntas con otro órgano.

La decisión sobre reuniones conjuntas es deliberada: el indicador suma la
actividad de dos comisiones, no la cantidad de artículos. Si una nota documenta
que Acusación y Disciplina sesionaron, aporta dos eventos, uno por comisión. Si
una de ellas sesionó junto con una tercera comisión, aporta un evento para la
comisión objetivo.

Se excluyen:

- audiencias testimoniales y audiencias del artículo 20, porque son actos de
  una causa y no sesiones de comisión;
- noticias del Jurado de Enjuiciamiento, que es otro órgano aunque la causa se
  haya originado en Acusación.

La clave de deduplicación es **fecha + comisión**. Dos notas sobre una misma
reunión no pueden inflar el conteo.

Se elige la opción 2: es la única que coincide con la unidad declarada y aplica
un criterio general antes de mirar qué puntaje produce.

## Pros y contras de las opciones

### 1 · Sólo slugs numerados

- Bueno: clasificación simple y fácil de reproducir.
- Malo: confunde una convención editorial con el universo y omite sesiones
  confirmadas por el contenido institucional.

### 2 · Toda sesión documentada y deduplicada *(elegida)*

- Bueno: responde a la definición publicada, incorpora reuniones sustantivas y
  explicita cómo tratar notas agrupadas y duplicadas.
- Malo: depende de clasificar texto institucional; se mitiga con inventario
  versionado, fixture y pruebas de inclusión y exclusión.

### 3 · Sólo las tres omisiones indiscutibles

- Bueno: corrige el mínimo comprobado con un cambio pequeño.
- Malo: deja fuera reuniones igualmente documentadas sólo por ser conjuntas o
  extraordinarias y conserva un universo metodológicamente incoherente.

## Más información

### Resultado

En la ventana publicada a agosto de 2026 hay **14 sesiones**:

| Comisión | Sesiones |
|---|---:|
| Acusación | 8 |
| Disciplina | 6 |
| **Total** | **14** |

El inventario con fecha, tipo, identificador y URL queda versionado en
`data/politica/denuncias_comisiones_universo.json`. Es un contraste auditable;
el runtime sigue leyendo la API viva.

La serie reconstruida cambia de rango 2–7 a **13–18**. Las bandas no se
recalibran contra el resultado observado: eso violaría ADR-0045 y mezclaría una
corrección del universo con una decisión normativa. Con las anclas conceptuales
vigentes, 14 sesiones recibe 10 puntos. La falta de discriminación histórica
que ahora queda visible requiere una decisión editorial separada si se desea
rediseñar el componente.

### Consecuencias

- La cifra responde a la definición pública y deja de depender del estilo del
  título o de la URL.
- Las sesiones que producen resultados sustantivos ya no desaparecen por
  haber sido tituladas con su resultado.
- El extractor publica el inventario de la ventana y el criterio de reuniones
  conjuntas junto con la card, de modo que el total se puede auditar.
- Queda corregida la afirmación de ADR-0134/0170 de que la numeración secuencial
  validaba la cobertura completa. Validaba una subclase editorial, no todas las
  sesiones.

### Confirmación

Un fixture reproduce 16 reuniones alrededor del borde de la ventana —14
vigentes—, tres audiencias/noticias que deben excluirse y una nota duplicada.
Las regresiones fijan los tres eventos sustantivos omitidos, las publicaciones
agrupadas, la sesión extraordinaria, la deduplicación, el total mensual, el
límite exacto de doce meses, el rechazo de menciones retrospectivas y la
exposición del inventario en la card.
