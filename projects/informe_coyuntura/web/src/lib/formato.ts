// Formateo de números y rangos para pantalla, SIN depender del snapshot
// (informe.json/series.json). Ese es el motivo de que este módulo exista
// separado de datos.ts: datos.ts importa informe.json/series.json completos
// al tope del archivo, así que cualquier <script> client-side que lo
// importara arrastraría el snapshot entero al bundle del navegador —
// además duplicado, porque el modal ya recibe esos mismos datos vía
// <script type="application/json">. IndicadorModal.astro por eso importa
// SOLO de acá, nunca de datos.ts, en su <script> de cliente (ver ese
// archivo). Los usos en frontmatter de páginas .astro (build time) pueden
// seguir importando `num` desde datos.ts, que lo reexporta.
const NF = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });

// ÚNICO formateador de números para pantalla. Antes cada componente tenía su
// propio `coma = n => String(n).replace(".", ",")` —cinco copias— y en los
// lugares donde el número se interpolaba crudo salía con punto: la auditoría
// mobile del 29-jul-2026 encontró el MISMO valor escrito de las dos formas en
// una sola página (`3,2` en la bajada y `3.2` en la card del hero, `47,4` y
// `47.4`, `96.7/100` junto a `96,7`), y `/metodologia/` con punto en todo.
// Dos reglas, las dos son convención del proyecto:
//   · separador decimal es-AR (coma)
//   · menos tipográfico U+2212, no el guion U+002D — igual que las unidades y
//     las anclas que escribe el pipeline (ver politica.py)
// NO usar para el CSV descargable ni para valores que van a `style`/`width`:
// ahí el número tiene que quedar parseable.
export function num(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return "—";
  return NF.format(valor).replace("-", "−");
}

// Un tramo con desde/hasta en null es extremo abierto. Un color puede
// aparecer más de una vez: el indicador de costo de financiamiento del Tesoro
// tiene el óptimo en el medio, así que amarillo y naranja quedan partidos en
// dos tramos, uno a cada lado.
export function rangoLegible(t: { desde: number | null; hasta: number | null }): string {
  // `num()` de acá arriba es el ÚNICO formateador de números para pantalla
  // del proyecto: separador de miles es-AR, coma decimal, menos tipográfico
  // U+2212. Antes esta función tenía su propio `String(x).replace(".", ",")`
  // -- sin separador de miles (desregulación publicaba "≥ 11000" mientras su
  // propia tabla de anclas, dos secciones arriba, mostraba "13.300"), con
  // guion ASCII en vez de U+2212, y sin techo de precisión (el ruido de
  // redondeo de la interpolación salía entero: "≥ 39,2892%").
  if (t.desde === null && t.hasta === null) return "todo el rango";
  if (t.desde === null) return `≤ ${num(t.hasta)}`;
  if (t.hasta === null) return `≥ ${num(t.desde)}`;
  return `${num(t.desde)} – ${num(t.hasta)}`;
}
