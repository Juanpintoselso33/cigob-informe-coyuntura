import informeRaw from "../data/informe.json";
import seriesRaw from "../data/series.json";
import { num } from "./formato.ts";

// `num` vive en formato.ts (sin import de informe.json/series.json) para que
// los <script> client-side puedan formatear números sin arrastrar el
// snapshot completo al bundle del navegador -- ver el comentario de cabecera
// de formato.ts. Acá se reexporta para no tocar los ~15 archivos que ya
// hacen `import { num } from "../lib/datos.ts"` en frontmatter (build time,
// donde arrastrar el snapshot no importa: ya está importado igual).
export { num };

export interface Indicador {
  valor: number | string | null;
  unidad: string;
  fuente: string;
  fecha_dato: string;
  desactualizado: boolean;
  estado?: string;        // "placeholder" cuando aplica
  avance_pct?: number;
  notas?: string;
  en_indice?: boolean;    // macro/gestión/política/vida: integra el índice paramétrico (false = contexto)
  puntaje_itcm?: number;  // macro: puntaje 0-100 aplicado en el ITCM
  puntaje_itcg?: number;  // gestión: puntaje 0-100 aplicado en el ITCG
  puntaje_itcp?: number;  // política: puntaje 0-100 aplicado en el ITCP
  indice_itvc?: number;   // vida: índice base-100 del componente (100 = 4T-2023)
  [k: string]: unknown;
}
export interface DimensionIndice {
  nombre: string;
  peso: number;
  puntaje: number;
  critica?: boolean;   // bajo el umbral crítico: el resto del índice no la compensa (ADR-0020)
  // Semáforo de 4 colores (ADR-0181): igual forma que el de indicador/índice,
  // pero sin `tension`/`umbrales`/`por_que` propios -- la dimensión solo
  // publica el color (ver publicar._semaforos).
  semaforo?: { color?: string; tension?: number | null; umbrales?: unknown; unidad?: string | null; por_que?: string | null };
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
  // Validación externa (ADR-0019 D6): serie mensual del índice junto a su
  // variable externa de contraste, con los textos de la sección armados por
  // publicar (título, explicación, leyendas, conclusión) y el modo de escala
  // del gráfico ("rebase100" | "minmax_inv").
  validacion?: { r_niveles: number; r_diferencias: number; n: number;
                 pares: [string, number, number][]; plot: string;
                 titulo: string; sub: string; serie_label: string;
                 externa_label: string; trans_label: string; conclusion: string;
                 // Panel de estadísticas externas (ADR-0159): sólo en los cinturones
                 // socioeconómicos, que no tienen serie de referencia única.
                 panel?: { perfil: { estadistica: string; etiqueta: string; propia: boolean;
                                     r_niveles: number; r_diferencias: number | null; n: number }[];
                           niveles: { convergente: number; discriminante: number; brecha: number };
                           diferencias: { convergente: number; discriminante: number; brecha: number };
                           n_propias: number; n_ajenas: number } };
  // Consistencia interna (auditoría de consistencia macro, jul-2026): cuánta
  // información realmente distinta aporta cada componente del índice, medida
  // como correlación entre los puntajes mensuales de todos los pares. Solo
  // macro por ahora; el tipo es genérico para poder extenderlo.
  redundancia?: { n_indicadores: number; n_pares: number; r_abs_medio: number;
                  share_altos: number; share_bajos: number; umbral: number;
                  pares_cruzados: number;
                  diferencias?: { n_pares: number; r_abs_medio: number | null;
                                  share_altos: number | null };
                  top: { a: string; b: string; r: number; cruzado: boolean;
                         por_diseno?: string | null }[];
                  titulo: string; sub: string; conclusion: string };
}
export interface Cinturon {
  score: number;
  estado: string;         // estable | en_tension | tensionado
  barbarismo_riesgo: string;
  indicadores: Record<string, Indicador>;
  alerta: string | null;
  score_explicacion?: string;
  itcm?: IndiceParametrico;  // solo macro
  itcg?: IndiceParametrico;  // solo gestión
  itcp?: IndiceParametrico;  // solo política
  itvc?: IndiceParametrico;  // solo impacto social (base 100 = 4T-2023)
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
    descripcion: "0 = cinturón severamente apretado, 100 = aflojado. Pondera seis dimensiones.",
    data: c.itcm,
  };
  if (c.itcg) return {
    sigla: "ITCG",
    nombre: "Índice de Tensión del Cinturón de Gestión",
    descripcion: "0 = se prometen reformas y no se ejecutan; 100 = agenda ejecutándose. Pondera cinco dimensiones.",
    data: c.itcg,
  };
  if (c.itvc) return {
    sigla: "ITCIS",
    base100: true,   // índice de seguimiento sin techo en 100 (no mostrar "/100")
    nombre: "Índice de Tensión del Cinturón de Impacto Social",
    descripcion: "100 = el arranque del mandato (4º trimestre de 2023). Más de 100 es mejora; menos, deterioro.",
    data: c.itvc,
  };
  if (c.itcp) return {
    sigla: "ITCP",
    nombre: "Índice de Tensión del Cinturón Político",
    descripcion: "0 = mínimo capital político, 100 = máximo. Capacidad de gobernar, no popularidad.",
    data: c.itcp,
  };
  return null;
}
export interface Informe {
  schema_version: string;
  generated_at: string;
  period: string;
  score_global: number;
  cinturones: Record<"macro" | "politica" | "vida_cotidiana" | "gestion", Cinturon>;
  barbarismo_activo: string;
  alerta_multicinturon: boolean;
  flags: string[];
  // Cortes de parametrica.CORTES_SEMAFORO (ADR-0181), expuestos para que la
  // leyenda de los 4 colores (SemaforoLeyenda.astro) arme su texto sin
  // repetirlos a mano -- `hasta: null` en el último tramo es rojo, sin techo.
  // Opcional: lo agrega `publicar._semaforos()` desde ago-2026, así que un
  // snapshot generado con una versión anterior del pipeline (el commiteado
  // hoy, entre esta rama y la próxima corrida) todavía no lo trae —
  // SemaforoLeyenda.astro no debe asumir que está.
  semaforo_cortes?: { color: ColorSemaforo; hasta: number | null }[];
}

export const informe = informeRaw as unknown as Informe;

// Ventana de PRESENTACIÓN de las series: todos los gráficos arrancan en
// dic-2023 (asunción — la ventana del mandato que evalúa el informe). Es un
// recorte solo visual: los cálculos del pipeline (rebases base 4T-2023,
// sumas móviles, validaciones) usan la historia completa de series.json.
// Excepción documentada: protestas_caba muestra 2018→hoy porque su razón de
// ser es comparar el nivel de protesta contra la era pre-mandato. pobreza_indec
// va por lo mismo (ADR-0114): es semestral, y con el recorte perdía el punto de
// julio de 2023 —la última lectura previa al traspaso— que es justamente la
// referencia contra la que se lee la serie.
const SERIE_DESDE = "2023-12-01";
const SERIE_COMPLETA = new Set(["protestas_caba", "pobreza_indec"]);
const seriesTodas = seriesRaw as Record<string, { fecha: string; valor: number }[]>;
export const series = Object.fromEntries(
  Object.entries(seriesTodas).map(([k, pts]) => [
    k, SERIE_COMPLETA.has(k) ? pts : pts.filter(p => p.fecha >= SERIE_DESDE),
  ]),
) as Record<string, { fecha: string; valor: number }[]>;

// Orden y metadatos de presentación de los cinturones (mapeo a clases .cg-cint--*)
export const CINTURONES = [
  { key: "macro",          slug: "macro",    nombre: "Macroeconomía",     sub: "El motor económico" },
  { key: "politica",       slug: "politica", nombre: "Política",          sub: "El tablero de poder" },
  { key: "vida_cotidiana", slug: "vida",     nombre: "Impacto social",    sub: "El bolsillo y la calle" },
  { key: "gestion",        slug: "gestion",  nombre: "Gestión",           sub: "La capacidad de ejecutar" },
] as const;

// Edición mensual: "2026-07" → "Julio 2026" (la entrega del informe es
// mensual; el día de la corrida queda solo como dato de frescura).
const MESES_LARGO = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
export function mesLegible(period: string): string {
  const m = /^(\d{4})-(\d{2})/.exec(period);
  return m ? `${MESES_LARGO[+m[2] - 1]} ${m[1]}` : period;
}

export type ColorSemaforo = "verde" | "amarillo" | "naranja" | "rojo";

// El color LO CALCULA parametrica.py y viaja en el snapshot (ADR-0181). Acá
// solo se lee: si el cliente lo recalculara, habría dos definiciones del corte
// y se desincronizarían sin que falle nada. Hasta agosto de 2026 esta función
// calculaba 3 colores en el cliente, con una vara distinta para el ITCIS
// base-100 (verde a tensión 6) que para los índices 0-100 (verde a tensión 4).
// El contrato son 4 colores, no 5: no hay "sin dato" acá adentro. Si falta el
// bloque `semaforo` esta función devuelve "amarillo" igual, PERO eso no debe
// leerse como que corresponde pintar amarillo — el llamador que le importa la
// diferencia (p. ej. IndicadorTile con asistencia_directa: TDPS saturado,
// fuera del índice, sin `semaforo`) tiene que chequear `x.semaforo?.color`
// ANTES de llamar y decidir no pintar nada, en vez de confiar en este
// fallback como si fuera un color real.
export function semaforoDe(x: { semaforo?: { color?: string } } | null | undefined): ColorSemaforo {
  const c = x?.semaforo?.color;
  return c === "verde" || c === "amarillo" || c === "naranja" || c === "rojo"
    ? c
    : "amarillo";
}

// Texto accesible del punto del semáforo (Tanda A, revisión de coherencia UI,
// ago-2026): el color es el ÚNICO portador de esa lectura en la card -- antes
// el punto iba `aria-hidden` con el "por qué" solo en un `title` (invisible a
// lectores de pantalla, inalcanzable en touch). Nombra el color y, si el
// snapshot lo trae (solo el semáforo de INDICADOR lo tiene: el de dimensión e
// índice no calcula `por_que`, ver publicar._semaforos), la misma frase que
// antes iba en el tooltip.
export function semaforoAriaLabel(
  semaforo?: { color?: string; por_que?: string | null } | null,
): string {
  const color = semaforo?.color;
  if (!color) return "Semáforo";
  return semaforo?.por_que ? `Semáforo: ${color} — ${semaforo.por_que}` : `Semáforo: ${color}`;
}

// ── Escala de tensión y color, para las barras ───────────────────────────────
// El semáforo de 4 colores vive sobre la TENSIÓN 0-10 y sus cortes se publican
// en `informe.semaforo_cortes` (parametrica.CORTES_SEMAFORO, ADR-0181). Los
// índices, las dimensiones y los indicadores ya traen su `semaforo.color`
// calculado; el CINTURÓN no —publica `score` (que ya es tensión 0-10) y un
// `estado` de tres valores—, así que su color se deriva acá.
//
// Derivarlo NO contradice la regla de "el color lo calcula el pipeline": los
// CORTES siguen siendo los del snapshot y esta función solo los aplica. Lo que
// estaría mal es escribir 4/6/8 en el front, y eso es justamente lo que esto
// evita. Si `semaforo_cortes` no viene (snapshot viejo), devuelve null y el
// llamador decide no pintar, en vez de inventar un color.
export const TENSION_MAX = 10;

export function colorPorTension(
  tension: number | null | undefined,
  cortes = informe.semaforo_cortes,
): ColorSemaforo | null {
  if (tension == null || !Number.isFinite(tension) || !cortes?.length) return null;
  for (const corte of cortes) {
    if (corte.hasta === null || tension <= corte.hasta) return corte.color;
  }
  return cortes[cortes.length - 1].color;
}

// Tramos de la barra, en tensión 0-10, listos para dibujar. Cierra el último
// corte abierto contra TENSION_MAX para que la pista tenga un final.
export interface TramoSemaforo { color: ColorSemaforo; desde: number; hasta: number; }

export function tramosSemaforo(cortes = informe.semaforo_cortes): TramoSemaforo[] {
  if (!cortes?.length) return [];
  const out: TramoSemaforo[] = [];
  let desde = 0;
  for (const corte of cortes) {
    const hasta = corte.hasta ?? TENSION_MAX;
    out.push({ color: corte.color, desde, hasta });
    desde = hasta;
  }
  return out;
}

// Cómo se dice el color en voz alta. El color no puede ser el único canal
// (daltonismo, impresión en gris, lector de pantalla), así que toda barra
// muestra además esta etiqueta y la posición del marcador.
export const LECTURA_SEMAFORO: Record<ColorSemaforo, string> = {
  verde: "Sin tensión relevante",
  amarillo: "Tensión moderada",
  naranja: "Tensión alta",
  rojo: "Tensión crítica",
};

// Peor dimensión (la que más tensión aporta) del índice de un cinturón.
// La comparación entre índices de escala distinta (bandas 0-100 vs ITCIS
// base-100) se hace en TENSIÓN equivalente, con las fórmulas publicadas.
export function tensionDeDimension(puntaje: number, base100: boolean): number {
  return base100 ? 5 - (puntaje - 100) * 0.2 : (100 - puntaje) / 10;
}
export interface PeorDim {
  key: string; nombre: string; puntaje: number; peso: number;
  base100: boolean; critica: boolean; tension: number;
}
export function peorDimension(c: Cinturon): PeorDim | null {
  const idx = indiceDe(c);
  if (!idx) return null;
  let peor: PeorDim | null = null;
  for (const [key, d] of Object.entries(idx.data.dimensiones) as [string, any][]) {
    const t = tensionDeDimension(d.puntaje, !!idx.base100);
    if (!peor || t > peor.tension) {
      peor = { key, nombre: d.nombre, puntaje: d.puntaje,
               peso: d.peso_efectivo ?? d.peso, base100: !!idx.base100,
               critica: !!d.critica, tension: t };
    }
  }
  return peor;
}

// Indicadores publicados con rezago declarado (desactualizado=true) en todo
// el informe — insumo de la línea de frescura honesta del hero.
export function indicadoresRezagados(inf: Informe): number {
  let n = 0;
  for (const c of Object.values(inf.cinturones))
    for (const i of Object.values(c.indicadores)) if (i.desactualizado) n++;
  return n;
}

// Semáforo del cinturón a partir de su estado. Son 3 colores porque `estado`
// tiene exactamente 3 valores ("estable" | "en_tension" | "tensionado",
// _estado() en publicar.py/generar_informe.py) -- no confundir con el
// semáforo de 4 colores de indicadores/índices (parametrica.CORTES_SEMAFORO,
// ADR-0181), que es un concepto aparte y sigue separado a propósito. El
// mapeo espeja generar_informe.py:192 (estable=verde, en_tension=amarillo,
// tensionado=rojo); antes comparaba contra "critico"/"alerta", valores que
// _estado() nunca emite, así que "tensionado" caía siempre en el default y
// ningún cinturón podía pintarse rojo.
export function verdictDeCinturon(estado: string): "verde" | "amarillo" | "rojo" {
  if (estado === "estable") return "verde";
  if (estado === "tensionado") return "rojo";
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
  emae_difusion: "Amplitud del crecimiento (sectores en alza)",
  ipi_manufacturero: "Producción industrial (IPI i.a.)",
  ipc_nucleo: "Inflación núcleo", pobreza_indec: "Pobreza (oficial, INDEC)",
  cuenta_corriente: "Cuenta corriente",
  saldo_comercial_12m: "Saldo comercial 12m", recaudacion: "Base imponible real (nación + provincias)",
  tcrm: "Tipo de cambio real (TCRM)", rem_ipc_12m: "Expectativas inflación (REM 12m)",
  idm: "Exceso de pesos sobre la demanda (IDM)",
  desequilibrio_monetario: "Dolarización dentro y fuera del sistema",
  iai: "Inversión física (IAI)", icip: "Capitalización digital (ICIP)",
  credito_privado: "Crédito privado real",
  costo_financiamiento_tesoro: "Costo real del financiamiento del Tesoro",
  resultado_primario: "Resultado primario del Estado nacional",
  prestamos_privados: "Préstamos al sector privado", base_monetaria: "Base monetaria",
  tc_mayorista: "Tipo de cambio mayorista",
  // politica
  votometro_ventaja_lla: "Ventaja LLA−PJ (Votómetro)", ratio_dnu: "Ratio DNU / leyes",
  brecha_obra_publica: "Brecha de expectativas: obra pública vs. privada",
  apoyo_empresario: "Postura pública de las cámaras empresarias",
  desafios_legislativos: "Normas desafiadas en el recinto",
  conflictividad_nacional: "Conflictividad social (país)",
  movilizacion_cepa: "Tensión social (CEPA, interno)", iaf_transferencias: "Armonía federal (transferencias)",
  eficacia_legislativa: "Eficacia parlamentaria", cohesion_bloque: "Cohesión del bloque LLA (bicameral)",
  cohesion_bloque_senado: "Cohesión del bloque LLA (Senado, fusionado)",
  rotacion_gabinete: "Rotación del gabinete",
  gobernadores_alineamiento: "Alineamiento de gobernadores (retirado)", veto_quorum: "Sesiones caídas por falta de quórum",
  alineamiento_senadores_prov: "Alineamiento de senadores por provincia",
  adhesion_reformas_provincial: "Adhesión provincial al RIGI",
  comisiones_caidas: "Comisiones sin sanción",
  derrotas_legislativas: "Derrotas legislativas del Ejecutivo",
  bloqueo_sostenido: "Bloqueo legislativo sostenido",
  // impacto social (claves de publicar.py)
  brecha_salario_cbt: "Salario real vs. canasta", ipc_alimentos: "Inflación de alimentos",
  endeudamiento_familiar: "Endeudamiento de consumo", mora_familias: "Mora de las familias",
  peso_tarifas: "Peso de tarifas (regulados)", alquiler_real: "Costo real del alquiler", pobreza_nowcast: "Pobreza (estimación mensual)", indice_lider: "Índice líder (anticipa el ciclo)",
  consumo_carne: "Consumo de carne vacuna per cápita",
  consumo_carnes_total: "Consumo total de carnes per cápita", informalidad: "Informalidad laboral",
  mortalidad_pymes: "Empleadores PyME activos", despacho_cemento: "Construcción (ISAC)",
  pluriempleo: "Subocupación demandante", inseguridad: "Victimización (IVI)",
  icc_utdt: "Confianza del consumidor (ICC)", sentimiento_digital: "Sentimiento digital (Trends)",
  patentamiento_motos: "Patentamiento de motos", desocupacion: "Desocupación",
  // gestion
  cepo_mulc: "Brecha cambiaria (cepo)", privatizaciones: "Privatizaciones (etapas)",
  concesiones_infraestructura: "Concesiones viales", reduccion_estado: "Dotación del Estado (APN)",
  reestructuracion_organismos: "Reestructuración de organismos", rigi_inversiones: "Inversiones RIGI",
  cobertura_judicial: "Cobertura de cargos judiciales",
  produccion_legislativa: "Producción legislativa del Congreso",
  judicializacion: "Judicialización de la agenda",
  velocidad_resolucion: "Velocidad de resolución de la Corte",
  paralisis_denuncias: "Actividad de las comisiones de control",
  empleo_registrado: "Empleo registrado privado",
  desregulacion_normativa: "Desregulación normativa", apertura_comercial: "Apertura comercial (alícuota)",
  gasto_funcionamiento: "Gasto de funcionamiento", masa_salarial: "Masa salarial pública",
  asistencia_directa: "Asistencia directa (TDPS)", fal_modernizacion_laboral: "Fondo de Asistencia Laboral",
  libertad_opcion_salud: "Libertad de opción en salud", protocolo_antipiquetes: "Orden público (piquetes)",
  litigiosidad_laboral: "Litigiosidad laboral (SRT)", alertas_manifestacion: "Alertas de manifestación (GCBA)",
  protestas_caba: "Protestas en CABA (ACLED)",
};
export function label(key: string): string {
  return LABELS[key] ?? key.replace(/_/g, " ");
}

// Formato de valor: números con separador es-AR; strings tal cual; null → "—"
const NF_COMPACT = new Intl.NumberFormat("es-AR", { notation: "compact", maximumFractionDigits: 1 });

export function formatValor(valor: unknown): string {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor === "number") return num(valor);
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
  emae_difusion: "% sectores",
  ipi_manufacturero: "% i.a.", ipc_nucleo: "%", cuenta_corriente: "US$ M", pobreza_indec: "%",
  saldo_comercial_12m: "US$ M", recaudacion: "base 100", tcrm: "índice", rem_ipc_12m: "%",
  idm: "pp", desequilibrio_monetario: "pts",
  iai: "% i.a.", icip: "% i.a.", credito_privado: "% i.a. real", costo_financiamiento_tesoro: "% real", resultado_primario: "% de la recaudación",
  prestamos_privados: "% m/m", base_monetaria: "% m/m", tc_mayorista: "% m/m",
  // politica
  votometro_ventaja_lla: "pp", ratio_dnu: "ratio", movilizacion_cepa: "índice",
  brecha_obra_publica: "pp",
  apoyo_empresario: "saldo",
  desafios_legislativos: "normas",
  conflictividad_nacional: "% vs 2023",
  iaf_transferencias: "% real", eficacia_legislativa: "%", cohesion_bloque: "%",
  cohesion_bloque_senado: "%", rotacion_gabinete: "salidas 12m",
  gobernadores_alineamiento: "%", veto_quorum: "%", comisiones_caidas: "%",
  alineamiento_senadores_prov: "%", adhesion_reformas_provincial: "%",
  derrotas_legislativas: "derrotas 12m",
  bloqueo_sostenido: "% en pie",
  // impacto social
  brecha_salario_cbt: "canastas", ipc_alimentos: "% m/m", endeudamiento_familiar: "bill. $",
  mora_familias: "%",
  peso_tarifas: "% m/m", alquiler_real: "% m/m", pobreza_nowcast: "%", indice_lider: "índice", consumo_carne: "kg/hab", consumo_carnes_total: "kg/hab", informalidad: "%", mortalidad_pymes: "empleadores",
  despacho_cemento: "índice", pluriempleo: "%", inseguridad: "% hogares", icc_utdt: "índice",
  sentimiento_digital: "pts", patentamiento_motos: "u.",
  // gestion (insumos del ITCG)
  cepo_mulc: "%", reduccion_estado: "%", apertura_comercial: "%",
  cobertura_judicial: "% cubierto",
  produccion_legislativa: "leyes (12m)",
  judicializacion: "% de sumarios",
  velocidad_resolucion: "% resuelto",
  paralisis_denuncias: "sesiones (12m)",
  empleo_registrado: "miles",
  desregulacion_normativa: "artículos", reestructuracion_organismos: "%",
  gasto_funcionamiento: "% real", masa_salarial: "% real",
  rigi_inversiones: "% de la cartera", privatizaciones: "%", concesiones_infraestructura: "%",
  fal_modernizacion_laboral: "actos", asistencia_directa: "%",
  protocolo_antipiquetes: "%", libertad_opcion_salud: "%",
  litigiosidad_laboral: "% i.a.", alertas_manifestacion: "alertas/mes",
  protestas_caba: "eventos 12m",
};

// Unidad "larga" para la ficha del modal (campo "Unidad"). Normalizada y
// consistente, independiente del estado del cache de cada colector. Describe
// SOLO la unidad de medida; la metodología vive en "Cómo se calcula".
export const UNIDADES_LARGAS: Record<string, string> = {
  // macro
  ipc_total: "% mensual", reservas_bcra: "Millones de USD",
  idc: "Desvíos estándar vs. su historia (σ)",
  badlar: "% anual", emae_ia: "% interanual",
  emae_difusion: "% de los 15 sectores del EMAE que crecen interanualmente",
  ipi_manufacturero: "% interanual (promedio 3 meses)", ipc_nucleo: "% mensual",
  pobreza_indec: "% de personas (medición oficial semestral)",
  cuenta_corriente: "millones de dólares (acumulado 4 trimestres)",
  saldo_comercial_12m: "Millones de USD (acum. 12 meses)",
  recaudacion: "índice de base imponible real desestacionalizada, 100 = 4º trimestre de 2023",
  tcrm: "Índice (base dic-2015=100)", rem_ipc_12m: "% anual esperado",
  idm: "Puntos porcentuales (brecha i.a. real)",
  desequilibrio_monetario: "Puntos de tensión (0–100)",
  iai: "% interanual (índice ponderado)", icip: "% interanual (índice ponderado)",
  credito_privado: "% interanual real (deflactado por IPC)",
  costo_financiamiento_tesoro: "% real anual (tasa efectiva de colocación menos inflación esperada)",
  resultado_primario: "% de la recaudación (resultado primario acumulado 12 meses)",
  prestamos_privados: "% mensual", base_monetaria: "% mensual", tc_mayorista: "% mensual",
  // politica
  votometro_ventaja_lla: "Puntos porcentuales", ratio_dnu: "DNUs por ley",
  brecha_obra_publica: "Puntos porcentuales de brecha",
  apoyo_empresario: "Saldo de apoyos y críticas (−1 a +1)",
  desafios_legislativos: "Normas desafiadas (12 meses)",
  movilizacion_cepa: "Índice (0–100)",
  conflictividad_nacional: "% de variación vs 2023 (eventos de protesta y disturbios en el país, acum. 12 meses)",
  iaf_transferencias: "% interanual real",
  eficacia_legislativa: "% de proyectos",
  cohesion_bloque: "% de votos (Rice bicameral: Diputados 65% + Senado 35%)",
  cohesion_bloque_senado: "% de votos (Senado — fusionado en el compuesto bicameral)",
  rotacion_gabinete: "Salidas de rango ministerial (acum. 12 meses)",
  gobernadores_alineamiento: "% de gobernadores (retirado)", veto_quorum: "% de sesiones",
  alineamiento_senadores_prov: "% de votos de senadores no-LLA que acompañan a LLA (promedio entre provincias)",
  adhesion_reformas_provincial: "% de jurisdicciones adheridas (sobre 24)",
  comisiones_caidas: "% de proyectos",
  derrotas_legislativas: "Derrotas en el recinto (vetos insistidos + decretos rechazados, acum. 12 meses)",
  bloqueo_sostenido: "% de normas desafiadas en el recinto que siguen en pie (últimos 12 meses)",
  // impacto social
  brecha_salario_cbt: "Canastas", ipc_alimentos: "% mensual",
  endeudamiento_familiar: "Billones de pesos", mora_familias: "% de la cartera en situación irregular",
  peso_tarifas: "% mensual", alquiler_real: "% mensual", pobreza_nowcast: "% de personas en hogares pobres", indice_lider: "Índice (nivel)",
  consumo_carne: "kg por habitante/año", consumo_carnes_total: "kg por habitante/año (vacuna + aviar + porcina)",
  informalidad: "% de asalariados",
  mortalidad_pymes: "Empleadores de hasta 50 trabajadores con cobertura de ART", despacho_cemento: "Índice", pluriempleo: "% de ocupados",
  inseguridad: "% de hogares víctimas (últimos 12 meses)", icc_utdt: "Índice",
  sentimiento_digital: "Índice (0–100)",
  patentamiento_motos: "Unidades",
  // gestion
  cepo_mulc: "% de brecha", privatizaciones: "% de avance (etapas 0-4)",
  concesiones_infraestructura: "% de km adjudicados (RFC)", reduccion_estado: "% de variación vs dic-2023",
  reestructuracion_organismos: "% de avance", rigi_inversiones: "% de la inversión de la cartera RIGI ya aprobada",
  cobertura_judicial: "% de cargos de juez habilitados con juez designado",
  produccion_legislativa: "leyes sancionadas en los últimos 12 meses",
  judicializacion: "sumarios con medida cautelar sobre el total, jurisdicción Federal + Nacional",
  velocidad_resolucion: "expedientes resueltos sobre ingresados en el año (CSJN)",
  paralisis_denuncias: "sesiones ordinarias de las comisiones de Acusación y Disciplina en 12 meses",
  empleo_registrado: "Miles de asalariados registrados del sector privado (SIPA)",
  desregulacion_normativa: "Artículos modificados o eliminados desde dic-2023", apertura_comercial: "% del intercambio (alícuota efectiva)",
  gasto_funcionamiento: "% de variación real vs 2023", masa_salarial: "% de variación real vs 2023",
  asistencia_directa: "% del gasto social sin intermediación", fal_modernizacion_laboral: "Actos fundamentales cumplidos (0–100)",
  libertad_opcion_salud: "% de usuarios de prepagas con derivación directa", protocolo_antipiquetes: "% de reducción de cortes vs 2023",
  litigiosidad_laboral: "% variación (12m vs 12m previos)",
  alertas_manifestacion: "Alertas únicas en el mes (GTFS-RT)",
  protestas_caba: "Eventos de protesta (acum. 12 meses, ACLED)",
};

// Unidad de la SERIE del gráfico cuando difiere de la unidad de la card
// (pares card/serie con semántica distinta, las excepciones G3 del gate).
// Sin entrada, el gráfico usa la unidad corta de la card.
export const UNIDADES_SERIE: Record<string, string> = {
  protestas_caba: "eventos/mes",       // card = acumulado 12m; serie = eventos por mes
  rigi_inversiones: "US$ M aprobados", // card = % del pipeline; serie = inversión aprobada acumulada
};

// Datos duros de migración real. Acompañaban a indice_intencion_migratoria
// como contraste en el modal; ese indicador salió con el cinturón de espíritu
// de época (ADR-0205). El mapa queda porque el bloque `contexto_duro` es
// genérico y estas etiquetas son las únicas que hay escritas — si nadie lo usa
// en unos meses, se borra.
export const CONTEXTO_DURO_META: Record<string, { label: string; freq: "mensual" | "anual"; nota?: string }> = {
  eeuu_niv: { label: "EE.UU. — visas de no inmigrante emitidas a argentinos", freq: "mensual", nota: "incluye turismo y negocios" },
  eeuu_iv: { label: "EE.UU. — visas de inmigrante (residencia permanente)", freq: "mensual" },
  canada_pr: { label: "Canadá — nuevos residentes permanentes argentinos", freq: "mensual", nota: "la fuente redondea a múltiplos de 5" },
  espana_nacionalidad: { label: "España — nacionalidad española otorgada a argentinos", freq: "anual" },
  italia_aire: { label: "Italia — ciudadanía italiana otorgada a argentinos", freq: "anual" },
  chile_residencia: { label: "Chile — residencias definitivas otorgadas a argentinos", freq: "anual" },
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
  "eficacia_legislativa", "cohesion_bloque", "alineamiento_senadores_prov",
  "adhesion_reformas_provincial", "veto_quorum", "comisiones_caidas", "movilizacion_cepa",
  "informalidad", "pluriempleo", "sentimiento_digital", "icc_utdt", "indice_intencion_migratoria",
  "mora_familias",
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

// ── Período del dato para el chip de la card ─────────────────────────────
// Reemplaza al rótulo "Automático" (que no informaba nada al lector): el chip
// muestra a qué período corresponde el dato. Mensuales → "jun 2026";
// trimestrales EPH → "1T 2026" (fecha_dato = inicio del trimestre relevado);
// anuales → el año del dato. Para los indicadores de ventana móvil viva
// (ratio_dnu, derrotas, cepo, etc.) fecha_dato es la fecha de la corrida y el
// mes corriente ES el período correcto ("dato al día"). Dos excepciones con
// fecha de corrida pero dato anual: iaf_transferencias (variación dic-dic del
// último año calendario completo — el año viene del campo `periodo` del
// colector, "2025 vs 2024") y veto_quorum (período legislativo en curso =
// año calendario de la corrida).
const MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun",
                      "jul", "ago", "sep", "oct", "nov", "dic"];
const PERIODO_TRIMESTRAL = new Set(["informalidad", "pluriempleo"]);
const PERIODO_ANUAL = new Set(["veto_quorum", "protocolo_antipiquetes"]);

export function periodoDato(key: string, ind: Indicador): string {
  const f = String(ind.fecha_dato ?? "");
  const anio = parseInt(f.slice(0, 4), 10);
  if (!anio) return "—";
  if (key === "iaf_transferencias") {
    const p = String(ind.periodo ?? "");
    return /^\d{4}/.test(p) ? p.slice(0, 4) : String(anio - 1);
  }
  if (PERIODO_ANUAL.has(key)) return String(anio);
  const mes = parseInt(f.slice(5, 7), 10);
  if (!mes) return String(anio);
  if (PERIODO_TRIMESTRAL.has(key)) return `${Math.floor((mes - 1) / 3) + 1}T ${anio}`;
  return `${MESES_CORTOS[mes - 1]} ${anio}`;
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
