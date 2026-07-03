import informeRaw from "../data/informe.json";
import seriesRaw from "../data/series.json";

export interface Indicador {
  valor: number | string | null;
  unidad: string;
  fuente: string;
  fecha_dato: string;
  desactualizado: boolean;
  estado?: string;        // "placeholder" cuando aplica
  avance_pct?: number;
  notas?: string;
  en_indice?: boolean;    // macro/gestión/vida: integra el índice paramétrico (false = contexto)
  puntaje_itcm?: number;  // macro: puntaje 0-100 aplicado en el ITCM
  puntaje_itcg?: number;  // gestión: puntaje 0-100 aplicado en el ITCG
  indice_itvc?: number;   // vida: índice base-100 del componente (100 = 4T-2023)
  [k: string]: unknown;
}
export interface DimensionIndice {
  nombre: string;
  peso: number;
  puntaje: number;
  critica?: boolean;   // bajo el umbral crítico: el resto del índice no la compensa (ADR-0020)
  indicadores: Record<string, { puntaje_banda: number; puntaje_aplicado: number; peso_efectivo: number }>;
}
export interface IndiceParametrico {
  valor: number;          // 0-100, mayor = menos tensión (cinturón aflojado)
  banda: string;
  banda_legible: string;
  dimensiones: Record<string, DimensionIndice>;
  ajustes_aplicados: { indicador: string; de: number; a: number; justificacion: string }[];
  // Rango de robustez p05-p95 (Monte Carlo sobre pesos y umbrales, ADR-0019)
  // + histograma de la simulación para el gráfico de distribución
  robustez?: { p05: number; p95: number; tension_rango: [number, number];
               dominante: { indicador: string; indice_sin: number } | null;
               n_draws: number; metodo: string;
               hist?: number[]; hist_min?: number; hist_max?: number };
  // Validación externa (ADR-0019 D6, hoy solo ITVC): serie mensual del índice
  // recalculado sin su componente circular, junto a la variable externa.
  validacion?: { r_niveles: number; r_diferencias: number; n: number;
                 pares: [string, number, number][]; contra: string };
}
export interface Cinturon {
  score: number;
  estado: string;         // estable | en_tension | critico
  barbarismo_riesgo: string;
  indicadores: Record<string, Indicador>;
  alerta: string | null;
  score_explicacion?: string;
  itcm?: IndiceParametrico;  // solo macro
  itcg?: IndiceParametrico;  // solo gestión
  itvc?: IndiceParametrico;  // solo vida cotidiana (base 100 = 4T-2023)
}

// Índice paramétrico del cinturón (si tiene): sigla, nombre y descripción
// para que la página de detalle lo renderice de forma genérica.
export interface IndiceInfo {
  sigla: string;
  nombre: string;
  descripcion: string;
  base100?: boolean;  // índice de seguimiento base 100 (sin techo: no mostrar "/100")
  data: IndiceParametrico;
}
export function indiceDe(c: Cinturon): IndiceInfo | null {
  if (c.itcm) return {
    sigla: "ITCM",
    nombre: "Índice de Tensión del Cinturón Macroeconómico",
    descripcion: "Índice de Tensión del Cinturón Macroeconómico (paramétrica CIGOB, may-2026). " +
      "0 = cinturón severamente apretado, 100 = aflojado. Pondera seis dimensiones; " +
      `la tensión del cinturón es (100 − ITCM) / 10.`,
    data: c.itcm,
  };
  if (c.itcg) return {
    sigla: "ITCG",
    nombre: "Índice de Tensión del Cinturón de Gestión",
    descripcion: "Índice de Tensión del Cinturón de Gestión (paramétrica CIGOB, jul-2026). " +
      "0 = el gobierno promete reformas pero no las ejecuta; 100 = agenda de reformas " +
      "ejecutándose. Pondera cinco dimensiones; la tensión del cinturón es (100 − ITCG) / 10.",
    data: c.itcg,
  };
  if (c.itvc) return {
    sigla: "ITVC",
    base100: true,   // índice de seguimiento sin techo en 100 (no mostrar "/100")
    nombre: "Índice de Tensión del Cinturón de Vida Cotidiana",
    descripcion: "Índice de seguimiento base 100 (paramétrica CIGOB, jul-2026): cada componente " +
      "se rebasea a 100 = promedio del 4º trimestre de 2023 (el arranque del mandato). " +
      "Más de 100 = mejora acumulada de la vida cotidiana; menos de 100 = deterioro. " +
      "Pondera cinco dimensiones; la tensión del cinturón es 5 − (ITVC − 100) × 0,2.",
    data: c.itvc,
  };
  return null;
}
export interface Informe {
  schema_version: string;
  generated_at: string;
  period: string;
  score_global: number;
  cinturones: Record<"macro" | "politica" | "vida_cotidiana" | "gestion" | "espiritu_epoca", Cinturon>;
  barbarismo_activo: string;
  alerta_multicinturon: boolean;
  flags: string[];
}

export const informe = informeRaw as unknown as Informe;
export const series = seriesRaw as Record<string, { fecha: string; valor: number }[]>;

// Orden y metadatos de presentación de los cinturones (mapeo a clases .cg-cint--*)
export const CINTURONES = [
  { key: "macro",          slug: "macro",    nombre: "Macroeconomía",     sub: "El motor económico" },
  { key: "politica",       slug: "politica", nombre: "Política",          sub: "El tablero de poder" },
  { key: "vida_cotidiana", slug: "vida",     nombre: "Vida cotidiana",    sub: "El bolsillo y la calle" },
  { key: "gestion",        slug: "gestion",  nombre: "Gestión",           sub: "La capacidad de ejecutar" },
  { key: "espiritu_epoca", slug: "espiritu", nombre: "Espíritu de época", sub: "El humor social" },
] as const;

// Semáforo del cinturón a partir de su estado
export function verdictDeCinturon(estado: string): "verde" | "amarillo" | "rojo" {
  if (estado === "estable") return "verde";
  if (estado === "critico" || estado === "alerta") return "rojo";
  return "amarillo"; // en_tension
}

// Clasificación de un indicador para el orden de display
export type Bucket = "fresco" | "manual" | "placeholder";
export function bucketDeIndicador(ind: Indicador): Bucket {
  if (ind.estado === "placeholder" || ind.valor === null) return "placeholder";
  if (ind.desactualizado) return "manual";
  return "fresco";
}

// Devuelve los indicadores de un cinturón ordenados: fresco → manual → placeholder
export function indicadoresOrdenados(c: Cinturon): { key: string; ind: Indicador; bucket: Bucket }[] {
  const orden: Record<Bucket, number> = { fresco: 0, manual: 1, placeholder: 2 };
  return Object.entries(c.indicadores)
    .map(([key, ind]) => ({ key, ind, bucket: bucketDeIndicador(ind) }))
    .sort((a, b) => orden[a.bucket] - orden[b.bucket]);
}

// Etiquetas legibles por clave de indicador
export const LABELS: Record<string, string> = {
  // macro
  ipc_total: "Inflación mensual (IPC)", reservas_bcra: "Reservas netas",
  idc: "Capacidad prestable (IdC)", badlar: "Tasa BADLAR",
  emae_ia: "Actividad económica (EMAE i.a.)",
  saldo_comercial_12m: "Saldo comercial 12m", recaudacion: "Recaudación tributaria",
  tcrm: "Tipo de cambio real (TCRM)", rem_ipc_12m: "Expectativas inflación (REM 12m)",
  idm: "Desequilibrio monetario (IDM)",
  iai: "Inversión física (IAI)", icip: "Capitalización digital (ICIP)",
  credito_privado: "Crédito privado real",
  prestamos_privados: "Préstamos al sector privado", base_monetaria: "Base monetaria",
  tc_mayorista: "Tipo de cambio mayorista",
  // politica
  votometro_ventaja_lla: "Ventaja LLA−PJ (Votómetro)", ratio_dnu: "Ratio DNU / leyes",
  movilizacion_cepa: "Tensión social (CEPA)", iaf_transferencias: "Armonía federal (transferencias)",
  eficacia_legislativa: "Eficacia parlamentaria", cohesion_bloque: "Cohesión del bloque LLA",
  gobernadores_alineamiento: "Alineamiento de gobernadores", veto_quorum: "Sesiones caídas por quórum",
  comisiones_caidas: "Comisiones sin sanción",
  // vida cotidiana (claves de publicar.py)
  brecha_salario_cbt: "Salario real vs. canasta", ipc_alimentos: "Inflación de alimentos",
  endeudamiento_familiar: "Endeudamiento de consumo", peso_tarifas: "Peso de tarifas (regulados)",
  consumo_carne: "Consumo de carne per cápita", informalidad: "Informalidad laboral",
  mortalidad_pymes: "Actividad industrial (IPI)", despacho_cemento: "Construcción (ISAC)",
  pluriempleo: "Subocupación demandante", inseguridad: "Hechos delictivos (SNIC)",
  icc_utdt: "Confianza del consumidor (ICC)", sentimiento_digital: "Sentimiento digital (Trends)",
  patentamiento_motos: "Patentamiento de motos", desocupacion: "Desocupación",
  // espíritu de época (comparte icc_utdt y sentimiento_digital con vida)
  clima_electoral: "Clima electoral (Votómetro)",
  // gestion
  cepo_mulc: "Brecha cambiaria (cepo)", privatizaciones: "Privatizaciones (etapas)",
  concesiones_infraestructura: "Concesiones viales", reduccion_estado: "Dotación del Estado (APN)",
  reestructuracion_organismos: "Reestructuración de organismos", rigi_inversiones: "Inversiones RIGI",
  desregulacion_normativa: "Desregulación normativa", apertura_comercial: "Apertura comercial (alícuota)",
  gasto_funcionamiento: "Gasto de funcionamiento", masa_salarial: "Masa salarial pública",
  asistencia_directa: "Asistencia directa (TDPS)", fal_modernizacion_laboral: "Fondo de Cese Laboral",
  libertad_opcion_salud: "Libertad de opción en salud", protocolo_antipiquetes: "Orden público (piquetes)",
  litigiosidad_laboral: "Litigiosidad laboral (SRT)", alertas_manifestacion: "Alertas de manifestación (GCBA)",
  protestas_caba: "Protestas en CABA (ACLED)",
};
export function label(key: string): string {
  return LABELS[key] ?? key.replace(/_/g, " ");
}

// Formato de valor: números con separador es-AR; strings tal cual; null → "—"
const NF = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });
const NF_COMPACT = new Intl.NumberFormat("es-AR", { notation: "compact", maximumFractionDigits: 1 });
export function formatValor(valor: unknown): string {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor === "number") return NF.format(valor);
  return String(valor);
}

// Capitaliza la primera letra (para barbarismos: "gerencial" → "Gerencial").
export function cap(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

// Aclaración chica para buckets no-frescos
export function aclaracion(b: Bucket, ind: Indicador): string | null {
  if (b === "placeholder") return "— pendiente";
  if (b === "manual") return `dato a ${ind.fecha_dato}`;
  return null;
}

// Unidad CORTA por indicador para mostrar junto al valor. La unidad larga de
// informe.json (descriptiva) va al atributo title de la fila — si se mostrara
// entera desborda la card. Sólo para indicadores con valor numérico.
export const UNIDADES_CORTAS: Record<string, string> = {
  // macro
  ipc_total: "%", reservas_bcra: "US$ M netas", idc: "índice", badlar: "%", emae_ia: "% i.a.",
  saldo_comercial_12m: "US$ M", recaudacion: "% i.a. real", tcrm: "índice", rem_ipc_12m: "%",
  idm: "pp", iai: "% i.a.", icip: "% i.a.", credito_privado: "% i.a. real",
  prestamos_privados: "% m/m", base_monetaria: "% m/m", tc_mayorista: "% m/m",
  // politica
  votometro_ventaja_lla: "pp", ratio_dnu: "ratio", movilizacion_cepa: "índice",
  iaf_transferencias: "% real", eficacia_legislativa: "%", cohesion_bloque: "%",
  gobernadores_alineamiento: "%", veto_quorum: "%", comisiones_caidas: "%",
  // vida cotidiana
  brecha_salario_cbt: "canastas", ipc_alimentos: "% m/m", endeudamiento_familiar: "bill. $",
  peso_tarifas: "% m/m", consumo_carne: "kg/hab", informalidad: "%", mortalidad_pymes: "% m/m",
  despacho_cemento: "índice", pluriempleo: "%", inseguridad: "hechos", icc_utdt: "índice",
  sentimiento_digital: "pts", patentamiento_motos: "u.",
  // espíritu de época
  clima_electoral: "pp",
  // gestion (insumos del ITCG)
  cepo_mulc: "%", reduccion_estado: "%", apertura_comercial: "%",
  desregulacion_normativa: "%", reestructuracion_organismos: "%",
  gasto_funcionamiento: "% real", masa_salarial: "% real",
  rigi_inversiones: "% del pipeline", privatizaciones: "%", concesiones_infraestructura: "%",
  fal_modernizacion_laboral: "índice", asistencia_directa: "%",
  protocolo_antipiquetes: "%", libertad_opcion_salud: "%",
  litigiosidad_laboral: "% i.a.", alertas_manifestacion: "alertas/mes",
  protestas_caba: "eventos 12m",
};

// Unidad "larga" para la ficha del modal (campo "Unidad"). Normalizada y
// consistente, independiente del estado del cache de cada colector. Describe
// SOLO la unidad de medida; la metodología vive en "Cómo se calcula".
export const UNIDADES_LARGAS: Record<string, string> = {
  // macro
  ipc_total: "% mensual", reservas_bcra: "Millones de USD", idc: "Índice (~1,0)",
  badlar: "% anual", emae_ia: "% interanual",
  saldo_comercial_12m: "Millones de USD (acum. 12 meses)", recaudacion: "% interanual real",
  tcrm: "Índice (base dic-2015=100)", rem_ipc_12m: "% anual esperado",
  idm: "Puntos porcentuales (brecha i.a. real)",
  iai: "% interanual (índice ponderado)", icip: "% interanual (índice ponderado)",
  credito_privado: "% interanual real (deflactado por IPC)",
  prestamos_privados: "% mensual", base_monetaria: "% mensual", tc_mayorista: "% mensual",
  // politica
  votometro_ventaja_lla: "Puntos porcentuales", ratio_dnu: "DNUs por ley",
  movilizacion_cepa: "Índice (0–100)", iaf_transferencias: "% interanual real",
  eficacia_legislativa: "% de proyectos", cohesion_bloque: "% de votos",
  gobernadores_alineamiento: "% de gobernadores", veto_quorum: "% de sesiones",
  comisiones_caidas: "% de proyectos",
  // vida cotidiana
  brecha_salario_cbt: "Canastas", ipc_alimentos: "% mensual",
  endeudamiento_familiar: "Billones de pesos", peso_tarifas: "% mensual",
  consumo_carne: "kg por habitante/año", informalidad: "% de asalariados",
  mortalidad_pymes: "% mensual", despacho_cemento: "Índice", pluriempleo: "% de ocupados",
  inseguridad: "Hechos por año", icc_utdt: "Índice", sentimiento_digital: "Índice (0–100)",
  patentamiento_motos: "Unidades",
  // espíritu de época
  clima_electoral: "Puntos porcentuales",
  // gestion
  cepo_mulc: "% de brecha", privatizaciones: "% de avance (etapas 0-4)",
  concesiones_infraestructura: "% de km adjudicados (RFC)", reduccion_estado: "% de variación vs dic-2023",
  reestructuracion_organismos: "% de avance", rigi_inversiones: "% de inversión aprobada / pipeline",
  desregulacion_normativa: "% de avance", apertura_comercial: "% del intercambio (alícuota efectiva)",
  gasto_funcionamiento: "% de variación real vs 2023", masa_salarial: "% de variación real vs 2023",
  asistencia_directa: "% del gasto social sin intermediación", fal_modernizacion_laboral: "Índice 0–100",
  libertad_opcion_salud: "% de usuarios de prepagas con derivación directa", protocolo_antipiquetes: "% de reducción de cortes vs 2023",
  litigiosidad_laboral: "% variación (12m vs 12m previos)",
  alertas_manifestacion: "Alertas únicas en el mes (GTFS-RT)",
  protestas_caba: "Eventos de protesta (acum. 12 meses, ACLED)",
};

export interface Presentacion { texto: string; unidad: string; titulo: string; }

// Decide qué mostrar en la columna de valor sin desbordar:
// - valor numérico → el número + unidad corta
// - valor no numérico pero hay avance_pct → el avance (% avance)
// - nada usable → "—"
// La descripción larga (o el texto de estado) queda en `titulo` (tooltip).
export function presentacion(key: string, ind: Indicador): Presentacion {
  if (typeof ind.valor === "number") {
    // Números muy grandes (ej. cantidad de hechos delictivos) en notación compacta.
    const texto = Math.abs(ind.valor) >= 1e6 ? NF_COMPACT.format(ind.valor) : formatValor(ind.valor);
    return { texto, unidad: UNIDADES_CORTAS[key] ?? "", titulo: ind.unidad ?? "" };
  }
  if (typeof ind.avance_pct === "number") {
    const detalle = typeof ind.valor === "string" ? ind.valor : (ind.unidad ?? "");
    return { texto: formatValor(ind.avance_pct), unidad: "% avance", titulo: detalle };
  }
  return { texto: "—", unidad: "", titulo: ind.unidad ?? "" };
}

// Conteo de cinturones "rojos" (para hero + tensión)
export function cinturonesRojos(inf: Informe): number {
  return Object.values(inf.cinturones).filter(c => verdictDeCinturon(c.estado) === "rojo").length;
}

// Indicadores que representan un NIVEL en escala 0–100 (porcentaje de algo o
// índice 0–100) y admiten una barra de progreso. Se excluyen variaciones
// (% m/m, % i.a., % real), ratios y conteos, donde una barra 0–100 no aplica.
export const BARRA_0_100 = new Set<string>([
  "eficacia_legislativa", "cohesion_bloque", "gobernadores_alineamiento",
  "veto_quorum", "comisiones_caidas", "movilizacion_cepa",
  "informalidad", "pluriempleo", "sentimiento_digital", "icc_utdt",
]);

function clamp100(n: number): number { return Math.max(0, Math.min(100, n)); }

export type Visual =
  | { tipo: "sparkline" }
  | { tipo: "barra"; pct: number; avance: boolean }
  | { tipo: "numero" };

// Decide el mejor visual para un indicador: serie histórica → sparkline;
// avance de reforma o nivel 0–100 → barra; en otro caso → número grande.
export function visualDe(key: string, ind: Indicador): Visual {
  if (typeof ind.avance_pct === "number") return { tipo: "barra", pct: clamp100(ind.avance_pct), avance: true };
  if ((series[key] ?? []).length >= 2) return { tipo: "sparkline" };
  if (BARRA_0_100.has(key) && typeof ind.valor === "number") return { tipo: "barra", pct: clamp100(ind.valor), avance: false };
  return { tipo: "numero" };
}

// Badge honesto del origen del dato.
export function badgeEstado(ind: Indicador): "Automático" | "Carga manual" | "Estimación" {
  if (ind.estado === "placeholder" || ind.valor === null) return "Estimación";
  if (ind.desactualizado) return "Carga manual";
  return "Automático";
}

// ── Helpers para las páginas de detalle por cinturón ──────────────────
export type CinturonMeta = (typeof CINTURONES)[number];

export function cinturonPorSlug(slug: string): CinturonMeta | undefined {
  return CINTURONES.find(c => c.slug === slug);
}

// Indicadores de un cinturón que tienen serie histórica (>=2 puntos), con su slug
// de color, para los mini-charts de evolución de la página de detalle.
export function indicadoresConSerie(c: Cinturon): string[] {
  return Object.keys(c.indicadores).filter(k => (series[k] ?? []).length >= 2);
}

// Fuentes únicas de un cinturón (para la sección de fuentes de su página).
export function fuentesDeCinturon(c: Cinturon): string[] {
  return [...new Set(
    Object.values(c.indicadores).map(i => i.fuente).filter(Boolean) as string[]
  )].sort();
}
