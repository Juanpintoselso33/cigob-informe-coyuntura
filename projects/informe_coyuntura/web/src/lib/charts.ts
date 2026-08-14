// Charts interactivos (ApexCharts) compartidos por el modal y la home.
// Cada función monta un gráfico en un elemento y devuelve la instancia (para .destroy()).
import ApexCharts from "apexcharts";

const NF = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

const FONT = "Montserrat, system-ui, sans-serif";
const COL = { muted: "#9CA39F", grid: "#ECE6DA", dark: "#1F2A28", zero: "#C9C2B4" };

// Color por slug de cinturón (coincide con --c-* de dashboard.css).
export const COLOR_CINTURON: Record<string, string> = {
  macro: "#1E40AF", politica: "#B91C1C", vida: "#92400E",
  gestion: "#4338CA",
};
export function colorDe(slug?: string): string {
  return (slug && COLOR_CINTURON[slug]) || "#4998DB";
}

export interface Punto { fecha: string; valor: number; }

// Indicadores cuya serie cruza el cero con lectura de signo clara: el área se
// pinta verde del lado "bueno" y roja del "malo". polaridad +1 = positivo es
// bueno (reservas, actividad); −1 = negativo es bueno (IDM: sobran pesos;
// litigiosidad/gasto real: caer es la mejora). Sin entrada → área neutra.
const POLARIDAD_SIGNO: Record<string, 1 | -1> = {
  reservas_bcra: 1, emae_ia: 1, ipi_manufacturero: 1, recaudacion: 1, saldo_comercial_12m: 1,
  idc: 1, credito_privado: 1, iai: 1, icip: 1, resultado_primario: 1,
  // costo_financiamiento_tesoro NO lleva polaridad a propósito: es la única
  // serie de U invertida del tablero (tasa real muy negativa = licuación;
  // muy alta = bola de nieve). Pintar medio gráfico de verde y medio de rojo
  // diría que "más es mejor", que es justo lo contrario de lo que mide.
  idm: -1, litigiosidad_laboral: -1, gasto_funcionamiento: -1, masa_salarial: -1,
  reduccion_estado: -1,
  // vida cotidiana (series que cruzan el cero). endeudamiento_familiar salió
  // de la lista (ADR-0067): su card es el stock nominal en billones (nunca
  // cruza el cero) y la polaridad −1 era la semántica del compuesto viejo
  // deuda×mora — el stock real puro puntúa con signo positivo en el ITVC.
  mortalidad_pymes: 1,
  // política: % var. vs 2023 — caer (menos conflicto en la calle) es la mejora
  conflictividad_nacional: -1,
  // política: % var. real i.a. de transferencias a provincias — el 0 es
  // "crecer igual que la inflación"; arriba las provincias reciben más en
  // términos reales (verde), abajo hay ajuste real (rojo)
  iaf_transferencias: 1,
};
const VERDE_AREA = "#16A34A";
const ROJO_AREA = "#DC2626";

function aTimestamp(fecha: string): number {
  const p = fecha.split("-");
  return Date.UTC(+p[0], p[1] ? +p[1] - 1 : 0, p[2] ? +p[2] : 1);
}
function esMensual(serie: Punto[]): boolean {
  return serie.every(p => { const d = p.fecha.split("-"); return d.length < 3 || d[2] === "01"; });
}

// Gráfico de línea/área para una serie temporal, con tooltip en hover.
export function timeChart(el: HTMLElement, serie: Punto[], opts: { color?: string; nombre?: string; unidad?: string; indicador?: string } = {}) {
  const color = opts.color ?? "#4998DB";
  const vals = serie.map(p => p.valor);
  const cruzaCero = Math.min(...vals) < 0 && Math.max(...vals) > 0;
  const xfmt = esMensual(serie) ? "MMM yyyy" : "dd MMM yy";
  // Área con signo: verde del lado bueno del cero, roja del malo. Se fija el
  // rango del eje Y para que el corte del degradé caiga EXACTO en el cero.
  const pol = POLARIDAD_SIGNO[opts.indicador ?? ""];
  let yMin: number | undefined, yMax: number | undefined, yTicks: number | undefined;
  let fillSigno: any = null;
  if (pol && !cruzaCero && vals.some(v => v !== 0)) {
    // Serie entera de un solo lado del cero: se tiñe del color de ese lado
    // (ej. gasto real i.a. siempre negativo = todo el período en zona verde),
    // más intensa lejos del cero. Sin eje clavado: el cero puede quedar fuera
    // del rango visible.
    const arriba = Math.min(...vals) >= 0;
    const colorLado = (pol === 1) === arriba ? VERDE_AREA : ROJO_AREA;
    fillSigno = { type: "gradient", gradient: { shadeIntensity: 0, opacityFrom: 1, opacityTo: 1,
      colorStops: arriba
        ? [{ offset: 0, color: colorLado, opacity: 0.36 }, { offset: 100, color: colorLado, opacity: 0.14 }]
        : [{ offset: 0, color: colorLado, opacity: 0.14 }, { offset: 100, color: colorLado, opacity: 0.36 }] } };
  }
  if (pol && cruzaCero) {
    // eje con paso "lindo" y el CERO clavado en un tick: el rango se redondea
    // a múltiplos del paso (el cero siempre es múltiplo) y tickAmount recorre
    // el rango de a un paso — así el degradé y la línea del cero coinciden
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const bruto = ((hi - lo) * 1.12) / 5;
    const pow = Math.pow(10, Math.floor(Math.log10(bruto)));
    const paso = [1, 2, 2.5, 5, 10].map(m => m * pow).find(s => s >= bruto)!;
    yMin = Math.floor((lo - (hi - lo) * 0.06) / paso) * paso;
    yMax = Math.ceil((hi + (hi - lo) * 0.06) / paso) * paso;
    yTicks = Math.round((yMax - yMin) / paso);
    // ¡El degradé se pinta sobre la caja de la SERIE (min..max de los datos),
    // no sobre el rango del eje! Calcular el corte con el rango del eje
    // (con padding redondeado) corría el cero y dejaba una banda del color
    // equivocado pegada al eje.
    const zeroPct = (hi / (hi - lo)) * 100;            // posición del cero desde arriba
    const [arriba, abajo] = pol === 1 ? [VERDE_AREA, ROJO_AREA] : [ROJO_AREA, VERDE_AREA];
    // opacidad mínima 0,16 junto al cero: con 0,04 el color se lavaba y la
    // franja pegada al eje quedaba como un resplandor blanco cuando la serie
    // no se aleja mucho del cero
    fillSigno = { type: "gradient", gradient: { shadeIntensity: 0, opacityFrom: 1, opacityTo: 1,
      colorStops: [
        { offset: 0, color: arriba, opacity: 0.36 },
        { offset: zeroPct, color: arriba, opacity: 0.16 },
        { offset: zeroPct, color: abajo, opacity: 0.16 },
        { offset: 100, color: abajo, opacity: 0.36 },
      ] } };
  }
  const chart = new ApexCharts(el, {
    chart: { type: "area", height: 260, width: "100%", fontFamily: FONT,
             toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: true, speed: 450 } },
    series: [{ name: opts.nombre ?? "Valor", data: serie.map(p => ({ x: aTimestamp(p.fecha), y: p.valor })) }],
    colors: [color],
    stroke: { curve: "smooth", width: 2.5 },
    fill: fillSigno ?? { type: "gradient", gradient: { shadeIntensity: 0.4, opacityFrom: 0.42, opacityTo: 0.04, stops: [0, 100] } },
    dataLabels: { enabled: false },
    markers: { size: 0, hover: { size: 5 }, strokeColors: "#fff", colors: [color] },
    xaxis: { type: "datetime", tooltip: { enabled: false },
             labels: { datetimeUTC: true, style: { colors: COL.muted, fontSize: "11px" } },
             axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { min: yMin, max: yMax, tickAmount: yTicks,
             labels: { formatter: (v: number) => NF.format(v), style: { colors: COL.muted, fontSize: "11px" } } },
    grid: { borderColor: COL.grid, strokeDashArray: 4, xaxis: { lines: { show: false } }, padding: { left: 8, right: 12, top: 0 } },
    tooltip: { theme: "light", x: { format: xfmt },
               y: { formatter: (v: number) => `${NF.format(v)}${opts.unidad ? ` ${opts.unidad}` : ""}` } },
    annotations: cruzaCero ? { yaxis: [{ y: 0, borderColor: COL.zero, strokeDashArray: 3 }] } : {},
  } as any);
  chart.render();
  return chart;
}

// Gráfico multilínea para indicadores con series COMPARADAS (ej. TCRM
// multilateral + bilaterales, como lo presenta el BCRA). La primera serie es
// la protagonista (trazo grueso, color del cinturón); las demás acompañan en
// tonos suaves. `refY` dibuja una referencia horizontal punteada con rótulo.
export function multiTimeChart(el: HTMLElement, series: { nombre: string; puntos: Punto[] }[],
                               opts: { color?: string; unidad?: string; refY?: number; refLabel?: string } = {}) {
  const color = opts.color ?? "#4998DB";
  const SUAVES = ["#3E9486", "#C9A227", "#8A8F98"];
  const chart = new ApexCharts(el, {
    chart: { type: "line", height: 280, width: "100%", fontFamily: FONT,
             toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: true, speed: 450 } },
    series: series.map(s => ({ name: s.nombre, data: s.puntos.map(p => ({ x: aTimestamp(p.fecha), y: p.valor })) })),
    colors: [color, ...SUAVES.slice(0, series.length - 1)],
    stroke: { curve: "smooth", width: [3, 1.8, 1.8, 1.8].slice(0, series.length) },
    dataLabels: { enabled: false },
    markers: { size: 0, hover: { size: 4 } },
    legend: { show: true, position: "top", horizontalAlign: "left",
              fontSize: "12px", labels: { colors: COL.dark },
              markers: { width: 9, height: 9, radius: 9 }, itemMargin: { horizontal: 10 } },
    xaxis: { type: "datetime", tooltip: { enabled: false },
             labels: { datetimeUTC: true, style: { colors: COL.muted, fontSize: "11px" } },
             axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { formatter: (v: number) => NF.format(v), style: { colors: COL.muted, fontSize: "11px" } } },
    grid: { borderColor: COL.grid, strokeDashArray: 4, xaxis: { lines: { show: false } }, padding: { left: 8, right: 12, top: 0 } },
    tooltip: { theme: "light", x: { format: "MMM yyyy" }, shared: true,
               y: { formatter: (v: number) => `${NF.format(v)}${opts.unidad ? ` ${opts.unidad}` : ""}` } },
    annotations: opts.refY != null ? { yaxis: [{ y: opts.refY, borderColor: COL.muted, strokeDashArray: 4,
      label: { text: opts.refLabel ?? "", position: "right", textAnchor: "end", offsetY: -5,
               style: { color: COL.muted, background: "rgba(255,255,255,0.85)",
                        fontSize: "10px", padding: { left: 4, right: 4, top: 2, bottom: 2 } } } }] } : {},
  } as any);
  chart.render();
  return chart;
}

// Comparado de DOS series con escalas distintas (índice vs ancla externa) para
// el modal de validación: doble eje Y, tooltip compartido con los valores
// REALES de cada punto (la card estática muestra las series normalizadas;
// acá se ven los números de verdad).
export function dualTimeChart(el: HTMLElement, a: { nombre: string; puntos: Punto[]; unidad?: string },
                              b: { nombre: string; puntos: Punto[]; unidad?: string },
                              opts: { color?: string; ejeBInvertido?: boolean } = {}) {
  const color = opts.color ?? "#3E9486";
  const fmt = (s: { unidad?: string }) => (v: number) =>
    `${NF.format(v)}${s.unidad ? ` ${s.unidad}` : ""}`;
  const chart = new ApexCharts(el, {
    chart: { type: "line", height: 300, width: "100%", fontFamily: FONT,
             toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: true, speed: 450 } },
    series: [
      { name: a.nombre, data: a.puntos.map(p => ({ x: aTimestamp(p.fecha), y: p.valor })) },
      { name: b.nombre, data: b.puntos.map(p => ({ x: aTimestamp(p.fecha), y: p.valor })) },
    ],
    colors: [color, "#64748B"],
    stroke: { curve: "smooth", width: [3, 1.8] },
    dataLabels: { enabled: false },
    markers: { size: 0, hover: { size: 5 }, strokeColors: "#fff" },
    legend: { show: true, position: "top", horizontalAlign: "left",
              fontSize: "12px", labels: { colors: COL.dark },
              markers: { width: 9, height: 9, radius: 9 }, itemMargin: { horizontal: 10 } },
    xaxis: { type: "datetime", tooltip: { enabled: false },
             labels: { datetimeUTC: true, style: { colors: COL.muted, fontSize: "11px" } },
             axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: [
      { seriesName: a.nombre, labels: { formatter: fmt(a), style: { colors: color, fontSize: "11px" } } },
      // ejeBInvertido: para pares de correlación NEGATIVA el
      // eje de la externa se invierte — las curvas co-mueven visualmente como
      // en la tarjeta, pero el tooltip muestra el valor real.
      { seriesName: b.nombre, opposite: true, reversed: !!opts.ejeBInvertido,
        labels: { formatter: fmt(b), style: { colors: "#64748B", fontSize: "11px" } } },
    ],
    grid: { borderColor: COL.grid, strokeDashArray: 4, xaxis: { lines: { show: false } },
            padding: { left: 8, right: 8, top: 0 } },
    tooltip: { theme: "light", shared: true, intersect: false, x: { format: "MMM yyyy" },
               y: [{ formatter: fmt(a) }, { formatter: fmt(b) }] },
  } as any);
  chart.render();
  return chart;
}

// Distribución del Monte Carlo de robustez (modal de detalle): la campana de
// los escenarios simulados como área interactiva — el tooltip dice cuántos
// escenarios cayeron en cada valor del índice; anotaciones en p05/p95, el
// valor publicado y (para índices base-100) la línea del 100.
export function distChart(el: HTMLElement,
                          d: { hist: number[]; hist_min: number; hist_max: number;
                               p05: number; p95: number; valor: number;
                               n_draws: number; base100?: boolean },
                          opts: { color?: string } = {}) {
  const color = opts.color ?? "#3E9486";
  const n = d.hist.length;
  const bw = (d.hist_max - d.hist_min) / n;
  const puntos = d.hist.map((c, i) => ({
    x: Math.round((d.hist_min + (i + 0.5) * bw) * 100) / 100, y: c,
  }));
  const anot = (x: number, texto: string, colorLinea: string, dash = 0) => ({
    x, borderColor: colorLinea, strokeDashArray: dash,
    label: { text: texto, orientation: "horizontal", offsetY: -4,
             style: { color: COL.muted, background: "rgba(255,255,255,0.9)", fontSize: "10px",
                      padding: { left: 4, right: 4, top: 2, bottom: 2 } } },
  });
  const anotaciones: any[] = [
    anot(d.p05, `p05 · ${NF.format(d.p05)}`, COL.muted, 4),
    anot(d.valor, `valor · ${NF.format(d.valor)}`, "#1F2937"),
    anot(d.p95, `p95 · ${NF.format(d.p95)}`, COL.muted, 4),
  ];
  if (d.base100 && 100 >= d.hist_min && 100 <= d.hist_max) {
    anotaciones.push(anot(100, "100 = base", COL.muted, 6));
  }
  const chart = new ApexCharts(el, {
    chart: { type: "area", height: 260, width: "100%", fontFamily: FONT,
             toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: true, speed: 450 } },
    series: [{ name: "Escenarios", data: puntos }],
    colors: [color],
    stroke: { curve: "smooth", width: 2.4 },
    fill: { type: "gradient", gradient: { shadeIntensity: 0.4, opacityFrom: 0.4, opacityTo: 0.05 } },
    dataLabels: { enabled: false },
    markers: { size: 0, hover: { size: 5 }, strokeColors: "#fff" },
    xaxis: { type: "numeric", tickAmount: 6, tooltip: { enabled: false },
             labels: { formatter: (v: number) => NF.format(Math.round(v * 10) / 10),
                       style: { colors: COL.muted, fontSize: "11px" } },
             axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { formatter: (v: number) => String(Math.round(v)),
                       style: { colors: COL.muted, fontSize: "11px" } } },
    grid: { borderColor: COL.grid, strokeDashArray: 4, xaxis: { lines: { show: false } },
            padding: { left: 8, right: 12, top: 12 } },
    tooltip: { theme: "light", intersect: false, shared: true,
               x: { formatter: (v: number) => `${(el.closest("[data-sigla]") as HTMLElement)?.dataset.sigla ?? "índice"} ≈ ${NF.format(Math.round(v * 10) / 10)}` },
               y: { formatter: (v: number) => `${Math.round(v)} de ${d.n_draws.toLocaleString("es-AR")} escenarios` } },
    annotations: { xaxis: anotaciones },
  } as any);
  chart.render();
  return chart;
}

// Mini gráfico (sparkline con tooltip) para las cards de la home.
export function sparkChart(el: HTMLElement, serie: Punto[], opts: { color?: string; nombre?: string; unidad?: string } = {}) {
  const color = opts.color ?? "#4998DB";
  const chart = new ApexCharts(el, {
    chart: { type: "area", height: 92, sparkline: { enabled: true }, fontFamily: FONT, animations: { enabled: true, speed: 400 } },
    series: [{ name: opts.nombre ?? "Valor", data: serie.map(p => ({ x: aTimestamp(p.fecha), y: p.valor })) }],
    colors: [color],
    stroke: { curve: "smooth", width: 2 },
    fill: { type: "gradient", gradient: { opacityFrom: 0.4, opacityTo: 0.04 } },
    tooltip: { theme: "light", x: { format: esMensual(serie) ? "MMM yyyy" : "dd MMM yy" },
               y: { formatter: (v: number) => `${NF.format(v)}${opts.unidad ? ` ${opts.unidad}` : ""}` } },
    xaxis: { type: "datetime" },
  } as any);
  chart.render();
  return chart;
}

// Medidor radial para indicadores sin serie temporal. `fill` (0–100) define cuánto
// se llena el arco; `centerText` el número del centro (si no, "fill%").
export function gaugeChart(el: HTMLElement, fill: number, opts: { color?: string; label?: string; centerText?: string } = {}) {
  const color = opts.color ?? "#4998DB";
  const chart = new ApexCharts(el, {
    chart: { type: "radialBar", height: 260, width: "100%", fontFamily: FONT },
    series: [Math.max(0, Math.min(100, fill))],
    colors: [color],
    plotOptions: { radialBar: {
      hollow: { size: "58%" }, track: { background: COL.grid, strokeWidth: "100%" },
      dataLabels: {
        name: { show: true, offsetY: 24, fontSize: "12px", color: COL.muted, fontWeight: 600 },
        value: { show: true, offsetY: -8, fontSize: "28px", fontWeight: 800, color: COL.dark,
                 formatter: () => opts.centerText ?? `${NF.format(fill)}%` },
      },
    } },
    labels: [opts.label ?? "avance"],
    stroke: { lineCap: "round" },
  } as any);
  chart.render();
  return chart;
}

// Barras horizontales para descomponer un indicador en sus componentes.
export function barChart(el: HTMLElement, items: { nombre: string; valor: number }[], opts: { color?: string; unidad?: string } = {}) {
  const color = opts.color ?? "#4998DB";
  const chart = new ApexCharts(el, {
    chart: { type: "bar", height: 260, width: "100%", fontFamily: FONT, toolbar: { show: false } },
    series: [{ name: "Valor", data: items.map(i => +Number(i.valor).toFixed(2)) }],
    colors: [color],
    plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: "55%", distributed: false } },
    dataLabels: { enabled: true, formatter: (v: number) => NF.format(v),
                  style: { colors: [COL.dark], fontSize: "11px", fontWeight: 700 }, offsetX: 24 },
    xaxis: { categories: items.map(i => i.nombre),
             labels: { formatter: (v: number) => NF.format(v as any), style: { colors: COL.muted, fontSize: "11px" } },
             axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { style: { colors: COL.muted, fontSize: "12px" } } },
    grid: { borderColor: COL.grid, strokeDashArray: 4 },
    tooltip: { theme: "light", y: { formatter: (v: number) => `${NF.format(v)}${opts.unidad ? ` ${opts.unidad}` : ""}` } },
  } as any);
  chart.render();
  return chart;
}

// Etiqueta legible de los componentes según el indicador (para barChart).
// Claves sin mapa (ej. nombres de empresa en privatizaciones) se muestran tal cual.
export function componentesDe(key: string, comp: Record<string, number>): { nombre: string; valor: number }[] {
  const LBL: Record<string, Record<string, string>> = {
    idc: { precio: "Precio (tasa real, σ)", volumen: "Volumen (depósitos i.a., σ)", asignacion: "Asignación (holgura, σ)" },
    iai: { isac: "Construcción (ISAC)", bk_importados: "Bienes de capital", patentamientos_comerciales: "Patentamientos" },
    icip: { servicios_tech: "Servicios tech", productividad: "Productividad" },
    fal_modernizacion_laboral: {
      ley_27802: "Ley 27.802 (Congreso)",
      decreto_408_2026: "Decreto 408/2026 (reglamentación)",
    },
    concesiones_infraestructura: {
      etapa_i: "Etapa I (% adj.)",
      etapa_ii: "Etapa II-A (% adj.)",
      etapa_ii_b: "Etapa II-B (% adj.)",
      etapa_iii: "Etapa III (% adj.)",
    },
  };
  const lbl = LBL[key] ?? {};
  return Object.entries(comp)
    .filter(([, v]) => typeof v === "number")
    .map(([k, v]) => ({ nombre: lbl[k] ?? k, valor: v }));
}
