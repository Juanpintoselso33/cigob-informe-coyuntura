# Tanda A — Una paleta, un significado

Sweep adversarial sobre producción encontró que la capa de semáforo compite
con usos previos de la misma paleta. Esta tanda arregla la colisión visual y
la accesibilidad del punto. La tanda B (aparte) mete el color en el modal y
en la ficha.

## Decisión de diseño que gobierna todo

**Los tokens `--verde` / `--amarillo` / `--naranja` / `--rojo` y sus `-soft`
pasan a significar una sola cosa en todo el sitio: el semáforo.** Cualquier
otro elemento que hoy los use sin ser semáforo, sale de la paleta.

## A1 — El badge de frescura sale de la paleta semáforo

`web/public/overrides.css:97-99`:

```css
.cg-tile-badge.auto   { background: var(--verde-soft);    color: #14532D; border-color: #BBF7D0; }
.cg-tile-badge.manual { background: var(--amarillo-soft); color: #713F12; border-color: #FDE68A; }
.cg-tile-badge.estim  { background: var(--bg-page);       color: var(--muted); }
```

El badge dice frescura y origen del dato (fecha si es automático, "Carga
manual", "Estimación"), **no** desempeño. Hoy es la píldora verde el elemento
más grande y llamativo de la card, y el punto del semáforo —8px— es el más
chico. Un indicador de carga manual con buen desempeño muestra punto verde y
píldora amarilla, y se lee como contradictorio.

**Qué hacer:** los tres estados pasan a un tratamiento neutro. Ya se
distinguen por su texto ("MAY 2026" vs "Carga manual" vs "Estimación"), así
que el color no está aportando nada que el texto no diga. Usá los neutros que
el sitio ya tiene (`--bg-page`, `--muted`, y el gris de borde de las cards);
no inventes tokens nuevos. `manual` y `estim` pueden quedar apenas más
marcados que `auto` si te parece —son la excepción y conviene notarlos— pero
con peso tipográfico o borde, **no con hue semántico**.

Revisá si `.cg-tile-badge` se usa en otro lado antes de tocarlo.

## A2 — El punto del semáforo deja de ser inaccesible

`web/src/components/IndicadorTile.astro`. Hoy:

```astro
<span class:list={["cg-tile-dot", `sem-${color}`]} title={ind.semaforo?.por_que ?? undefined} aria-hidden="true"></span>
```

`aria-hidden` más `title` es lo peor de los dos mundos: invisible para lectores
de pantalla e inalcanzable en touch. Y el color es el **único** portador de esa
información en la card: el número no permite deducirlo sin conocer los
umbrales.

**Qué hacer:**

- Sacar `aria-hidden`. El punto pasa a `role="img"` con un `aria-label` que
  nombre el color y, si existe, el porqué: p. ej. `Semáforo: naranja — 47,5
  kg/hab cae en el tramo que corresponde a Naranja, a 2,5 del corte más
  cercano.` Armalo del `semaforo.color` y `semaforo.por_que` publicados.
- Subir el punto de 8px a 10px y darle un borde interior sutil
  (`box-shadow: inset 0 0 0 1px rgba(0,0,0,.15)` o equivalente) para que no se
  pierda contra el fondo claro de la card.
- Los cuatro hues actuales son muy parecidos en luminancia (verde #16A34A ≈
  0,36 · amarillo #CA8A04 ≈ 0,32 · naranja #EA580C ≈ 0,28 · rojo #DC2626 ≈
  0,22), lo que los vuelve difíciles de separar con deuteranopia — el par
  verde/naranja es justo el que falla. **No cambies los hues** (ya están en
  producción y en el genoma); el problema se resuelve con la leyenda de A3 y
  con el texto de la tanda B.

## A3 — Leyenda de los cuatro colores

Hoy no existe ninguna: `grep` sobre `web/src/` no devuelve nada. Cuatro colores
en producción sin ningún lugar que diga qué significan. El naranja es el que
más lo necesita: verde/amarillo/rojo son convención universal, naranja no.

**Qué hacer:** un componente chico y reutilizable, `SemaforoLeyenda.astro`,
que liste los cuatro con su nombre y su lectura, y lo más importante, **de
dónde sale el corte** — que es lo que lo hace creíble:

- 🟢 Verde — tensión ≤ 4
- 🟡 Amarillo — tensión ≤ 6
- 🟠 Naranja — tensión ≤ 8
- 🔴 Rojo — tensión > 8

Con una línea en llano explicando que no es una escala nueva: es la misma
tensión 0-10 que el informe ya publica, partida en cuatro tramos.

**Los números de los cortes tienen que salir del snapshot, no escribirse en el
template.** `publicar.py` ya publica `semaforo` en todos lados; si los cortes
no están expuestos como dato, agregalos al snapshot desde
`parametrica.CORTES_SEMAFORO` (es la única fuente de verdad y ningún `.ts` ni
`.astro` puede tener 4/6/8 escritos — hay un test que lo verifica).

Ubicalo donde el lector se topa con los colores por primera vez: la portada
(`web/src/pages/index.astro` / el bloque de cinturones) y la página de cada
cinturón (`web/src/pages/[slug].astro`), arriba de la grilla de indicadores.
Que no grite: es una nota de lectura, no un panel.

## A4 — Las dimensiones se pintan en el genoma pero no en su encabezado

En la página de cinturón, la fila "Ingresos y consumo · 110,5 · pesa 37% · 5
indicadores" es texto plano, aunque esa dimensión **ya tiene color publicado**
(`indice.dimensiones[k].semaforo.color`) y aparece coloreada en el genoma de
la portada. Agregale el mismo punto que usan las cards, con su `aria-label`.

## Restricciones

- Trabajar desde `F:\dev\trabajo\CIGOB\Analisis CIGOB\projects\informe_coyuntura`.
- Prosa y copy en **castellano**.
- Los cortes viven sólo en `parametrica.CORTES_SEMAFORO`. Ningún `.ts` ni
  `.astro` puede tener 4/6/8, 60/40/20 ni 105/95/85 escritos —
  `tests/test_web_semaforo.py` lo verifica y tiene dientes.
- No tocar bandas, pesos, índices, `UMBRALES` ni `_estado()`.
- `web/public/` es el fuente; `web/dist/` es salida de build.
- **Nunca `git add -A` ni `git add .`** — el repo vive en OneDrive y un add a
  ciegas commitea snapshots viejos sobre los buenos.
- **No regenerar ni commitear el snapshot.** Si regenerás para verificar,
  restaurá `output/*`, `web/src/data/*` y `data/historico/*` byte a byte y
  probalo con `git status --short`.

## Verificación

`npx tsc --noEmit`, `npm run build`, `python -m pytest tests -q`.

Fallo preexistente y ajeno, no tuyo:
`test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
(tiene pineado −1,07 y la fuente da −2,0). Cualquier otra cosa es nueva.

**Mirá el resultado renderizado**, no sólo el código: construí y abrí la página
de un cinturón. Contá qué es lo más llamativo de una card ahora — si sigue
siendo el badge, A1 no se logró.
