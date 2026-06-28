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
  gestion: "#4338CA", espiritu: "#9D174D",
};
export function colorDe(slug?: string): string {
  return (slug && COLOR_CINTURON[slug]) || "#4998DB";
}

export interface Punto { fecha: string; valor: number; }

function aTimestamp(fecha: string): number {
  const p = fecha.split("-");
  return Date.UTC(+p[0], p[1] ? +p[1] - 1 : 0, p[2] ? +p[2] : 1);
}
function esMensual(serie: Punto[]): boolean {
  return serie.every(p => { const d = p.fecha.split("-"); return d.length < 3 || d[2] === "01"; });
}

// Gráfico de línea/área para una serie temporal, con tooltip en hover.
export function timeChart(el: HTMLElement, serie: Punto[], opts: { color?: string; nombre?: string; unidad?: string } = {}) {
  const color = opts.color ?? "#4998DB";
  const vals = serie.map(p => p.valor);
  const cruzaCero = Math.min(...vals) < 0 && Math.max(...vals) > 0;
  const xfmt = esMensual(serie) ? "MMM yyyy" : "dd MMM yy";
  const chart = new ApexCharts(el, {
    chart: { type: "area", height: 260, width: "100%", fontFamily: FONT,
             toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: true, speed: 450 } },
    series: [{ name: opts.nombre ?? "Valor", data: serie.map(p => ({ x: aTimestamp(p.fecha), y: p.valor })) }],
    colors: [color],
    stroke: { curve: "smooth", width: 2.5 },
    fill: { type: "gradient", gradient: { shadeIntensity: 0.4, opacityFrom: 0.42, opacityTo: 0.04, stops: [0, 100] } },
    dataLabels: { enabled: false },
    markers: { size: 0, hover: { size: 5 }, strokeColors: "#fff", colors: [color] },
    xaxis: { type: "datetime", tooltip: { enabled: false },
             labels: { datetimeUTC: true, style: { colors: COL.muted, fontSize: "11px" } },
             axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { formatter: (v: number) => NF.format(v), style: { colors: COL.muted, fontSize: "11px" } } },
    grid: { borderColor: COL.grid, strokeDashArray: 4, xaxis: { lines: { show: false } }, padding: { left: 8, right: 12, top: 0 } },
    tooltip: { theme: "light", x: { format: xfmt },
               y: { formatter: (v: number) => `${NF.format(v)}${opts.unidad ? ` ${opts.unidad}` : ""}` } },
    annotations: cruzaCero ? { yaxis: [{ y: 0, borderColor: COL.zero, strokeDashArray: 3 }] } : {},
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
export function componentesDe(key: string, comp: Record<string, number>): { nombre: string; valor: number }[] {
  const LBL: Record<string, Record<string, string>> = {
    idc: { precio: "Precio (BADLAR real)", volumen: "Volumen (depósitos)", asignacion: "Asignación (crédito)" },
    iai: { isac: "Construcción (ISAC)", bk_importados: "Bienes de capital", patentamientos_comerciales: "Patentamientos" },
    icip: { servicios_tech: "Servicios tech", productividad: "Productividad" },
  };
  const lbl = LBL[key] ?? {};
  return Object.entries(comp)
    .filter(([, v]) => typeof v === "number")
    .map(([k, v]) => ({ nombre: lbl[k] ?? k, valor: v }));
}
