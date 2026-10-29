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
  metodo_obtencion?: "automatico" | "semiautomatico" | "manual";
  avance_pct?: number;
  notas?: string;
  en_indice?: boolean;    // macro/gestión/política/vida: integra el índice paramétrico (false = contexto)
  puntaje_itcm?: number;  // macro: puntaje 0-100 aplicado en el ITCM
  puntaje_itcg?: number;  // gestión: puntaje 0-100 aplicado en el ITCG
  puntaje_itcp?: number;  // política: puntaje 0-100 aplicado en el ITCP
  indice_itvc?: number;   // vida: índice común; tarifas usa umbrales 10%/5% por rubro (ADR-0235)
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
  // Serie mensual de la dimensión (ADR-0233): [periodo, puntaje]. Sale de la
  // reconstrucción histórica, del mismo resultado del motor que arma la serie
  // del índice — no de una segunda agregación. Ausente cuando la dimensión no
  // tiene componentes con historia mensual reconstruible.
  serie?: [string, number][];
}
export interface IndiceParametrico {
  serie_mensual?: [string, number][];
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
  // Encabezado de las series por dimensión (ADR-0233): los textos y el período
  // cubierto. Su ausencia significa que ninguna dimensión llegó al mínimo de
  // meses, y entonces la sección entera no se dibuja.
  dimensiones_serie?: { titulo: string; sub: string; escala: string; base100: boolean;
                        desde: string; hasta: string; n: number;
                        n_dimensiones: number; nota: string };
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
//
// La SIGLA no se muestra (ADR-0340): queda como identificador —la matriz de
// validación cruzada marca su fila con ella— y para la capa metodológica de
// las fichas. Lo que lee el lector es `corto`, el nombre llano del índice en
// minúscula, para ir a mitad de frase («pesa 12% del índice político»);
// `Corto` es el mismo con mayúscula inicial, para títulos y chips. Tienen que
// coincidir con config.NOMBRES_PUBLICOS: tests/test_siglas_publicas.py lo
// verifica.
export interface IndiceInfo {
  sigla: string;
  corto: string;
  Corto: string;
  fichaId: string;
  nombre: string;
  descripcion: string;
  base100?: boolean;  // índice de seguimiento base 100 (sin techo: no mostrar "/100")
  data: IndiceParametrico;
}
export function indiceDe(c: Cinturon): IndiceInfo | null {
  if (c.itcm) return {
    sigla: "ITCM",
    corto: "índice macroeconómico",
    Corto: "Índice macroeconómico",
    fichaId: "itcm",
    nombre: "Índice de Tensión del Cinturón Macroeconómico",
    descripcion: "0 = cinturón severamente apretado, 100 = aflojado. Pondera cinco dimensiones.",
    data: c.itcm,
  };
  if (c.itcg) return {
    sigla: "ITCG",
    corto: "índice de gestión",
    Corto: "Índice de gestión",
    fichaId: "itcg",
    nombre: "Índice de Tensión del Cinturón de Gestión",
    descripcion: "0 = se prometen reformas y no se ejecutan; 100 = agenda ejecutándose. Pondera cinco dimensiones.",
    data: c.itcg,
  };
  if (c.itvc) return {
    sigla: "ITCIS",
    corto: "índice de impacto social",
    Corto: "Índice de impacto social",
    fichaId: "itvc",
    base100: true,   // índice de seguimiento sin techo en 100 (no mostrar "/100")
    nombre: "Índice de Tensión del Cinturón de Impacto Social",
    descripcion: "100 = el arranque del mandato para la mayoría de los componentes; servicios públicos usa una escala construida con umbrales internacionales por rubro. Más de 100 es mejora; menos, deterioro.",
    data: c.itvc,
  };
  if (c.itcp) return {
    sigla: "ITCP",
    corto: "índice político",
    Corto: "Índice político",
    fichaId: "itcp",
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
  // Clave del cinturón que produjo ese barbarismo (ADR-0237). Opcional: lo
  // agrega `publicar.recomputar_barbarismo()` desde ago-2026, así que un
  // snapshot anterior no lo trae y `cinturonDominante()` lo deriva.
  cinturon_dominante?: string | null;
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
// El inverso de `tensionDeDimension`: en qué valor del ÍNDICE cae cada corte
// de color. La web no muestra la tensión como número (ADR-0337), así que para
// explicar el color se lo dice en la escala del índice, que sí se publica. Sale
// de los cortes del snapshot: no hay un umbral escrito acá.
export function indiceDeTension(tension: number, base100: boolean): number {
  return base100 ? 100 - (tension - 5) * 5 : 100 - tension * 10;
}
/** "verde con 60 o más, amarillo de 40 a 60, naranja de 20 a 40 y rojo por
    debajo de 20" — en la escala del índice del cinturón. */
export function coloresEnIndice(base100: boolean): string {
  const tramos = tramosSemaforo();
  if (!tramos.length) return "";
  const v = (t: number) => num(indiceDeTension(t, base100));
  const partes = tramos.map((t, i) =>
    i === 0 ? `${t.color} con ${v(t.hasta)} o más`
    : i === tramos.length - 1 ? `${t.color} por debajo de ${v(t.desde)}`
    : `${t.color} de ${v(t.hasta)} a menos de ${v(t.desde)}`);
  return partes.slice(0, -1).join(", ") + " y " + partes.at(-1);
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
export type Bucket = "fresco" | "rezagado" | "placeholder";
export function bucketDeIndicador(ind: Indicador): Bucket {
  if (ind.estado === "sin_universo") return ind.desactualizado ? "rezagado" : "fresco";
  if (ind.estado === "placeholder" || ind.valor === null) return "placeholder";
  if (ind.desactualizado) return "rezagado";
  return "fresco";
}

// Devuelve los indicadores de un cinturón ordenados: fresco → rezagado → placeholder
export function indicadoresOrdenados(c: Cinturon): { key: string; ind: Indicador; bucket: Bucket }[] {
  const orden: Record<Bucket, number> = { fresco: 0, rezagado: 1, placeholder: 2 };
  return Object.entries(c.indicadores)
    .map(([key, ind]) => ({ key, ind, bucket: bucketDeIndicador(ind) }))
    .sort((a, b) => orden[a.bucket] - orden[b.bucket]);
}

// Etiquetas legibles por clave de indicador
export const LABELS: Record<string, string> = {
  // macro
  ipc_total: "Inflación del mes", reservas_bcra: "Reservas netas",
  idc: "Capacidad prestable", badlar: "Tasa de plazo fijo de bancos privados grandes",
  emae_ia: "Actividad económica (frente a un año atrás)",
  emae_difusion: "Amplitud del crecimiento (sectores en alza)",
  ipi_manufacturero: "Producción industrial (frente a un año atrás)",
  actividad_tributaria: "Actividad tributaria (impuesto al valor agregado + impuesto al cheque)",
  ipc_nucleo: "Inflación núcleo", pobreza_indec: "Pobreza (oficial, Instituto Nacional de Estadística y Censos)",
  cuenta_corriente: "Cuenta corriente",
  saldo_comercial_12m: "Saldo comercial (últimos 12 meses)",
  saldo_comercial_12m_usd: "Saldo comercial en dólares (últimos 12 meses)", recaudacion: "Base imponible real (nación + Ingresos Brutos interjurisdiccionales)",
  tcrm: "Tipo de cambio real",
  tcr_terminos_intercambio: "Tipo de cambio real y términos del intercambio",
  terminos_intercambio: "Términos del intercambio",
  rem_ipc_12m: "Inflación esperada a 12 meses",
  idm: "Brecha de crecimiento real entre el dinero total (M3) y el dinero de uso diario (M2)",
  desequilibrio_monetario: "Liquidez en pesos y presión compradora de divisas",
  iai: "Inversión física", icip: "Pagos de servicios digitales y productividad",
  credito_privado: "Crédito privado real en pesos",
  costo_financiamiento_tesoro: "Costo real del financiamiento del Tesoro",
  resultado_primario: "Resultado primario del Estado nacional",
  prestamos_privados: "Préstamos al sector privado", base_monetaria: "Base monetaria",
  tc_mayorista: "Tipo de cambio mayorista",
  // politica
  votometro_ventaja_lla: "Ventaja de La Libertad Avanza sobre el Partido Justicialista", ratio_dnu: "Decretos de necesidad y urgencia por ley",
  brecha_obra_publica: "Brecha de expectativas: obra pública frente a privada",
  apoyo_empresario: "Postura pública de la industria",
  apoyo_comercio: "Postura pública del comercio",
  apoyo_campo: "Postura pública del campo",
  apoyo_construccion: "Postura pública de la construcción",
  desafios_legislativos: "Normas desafiadas en el recinto",
  insistencias_vetos: "Vetos que el Congreso dio vuelta",
  rechazos_decretos: "Decretos derogados por el Congreso",
  conflictividad_nacional: "Conflictividad social (país)",
  jornadas_individuales_no_trabajadas_12m: "Intensidad de los paros",
  movilizacion_cepa: "Tensión social (Centro de Economía Política Argentina)", iaf_transferencias: "Armonía federal (transferencias)",
  transferencias_no_automaticas: "Transferencias no automáticas a provincias",
  eficacia_legislativa: "Eficacia legislativa de proyectos maduros", cohesion_bloque: "Cohesión del bloque oficialista (ambas cámaras)",
  cohesion_bloque_senado: "Cohesión del bloque de La Libertad Avanza (Senado, fusionado)",
  votos_sobre_bancas: "Votos ajenos al aprobar leyes",
  rotacion_gabinete: "Rotación del gabinete",
  gobernadores_alineamiento: "Alineamiento de gobernadores (retirado)", veto_quorum: "Sesiones caídas por falta de quórum",
  alineamiento_senadores_prov: "Alineamiento de senadores por provincia",
  adhesion_reformas_provincial: "Provincias adheridas al régimen de grandes inversiones",
  comisiones_caidas: "Comisiones sin sanción",
  derrotas_legislativas: "Derrotas legislativas del Ejecutivo",
  bloqueo_sostenido: "Bloqueo legislativo sostenido",
  // impacto social (claves de publicar.py)
  brecha_salario_cbt: "Salario real frente a la canasta básica", ipc_alimentos: "Inflación de alimentos",
  endeudamiento_familiar: "Endeudamiento de consumo", mora_familias: "Mora de las familias",
  carga_servicio_deuda_hogares: "Carga del servicio de deuda",
  icg_utdt: "Confianza en el Gobierno",
  peso_tarifas: "Canasta de servicios públicos / salario", alquiler_real: "Alquiler real (INDEC)", alquiler_udesa_real: "Alquiler real (Universidad de San Andrés – Mercado Libre)", pobreza_nowcast: "Pobreza (estimación mensual)", indice_lider: "Índice líder (anticipa el ciclo)",
  consumo_carne_vacuna: "Consumo de carne vacuna per cápita",
  consumo_carnes_total: "Consumo total de carnes per cápita", consumo_carnes_otras: "Consumo de carne aviar y porcina per cápita", informalidad: "Informalidad laboral (asalariados sin ningún aporte)", ocupacion_eph: "Ocupación (Encuesta Permanente de Hogares)",
  mortalidad_pymes: "Empleadores activos de pequeñas y medianas empresas", trabajo_independiente: "Peso del trabajo independiente", despacho_cemento: "Construcción",
  subocupacion_demandante: "Subocupación demandante", inseguridad: "Victimización",
  icc_utdt: "Confianza del consumidor", sentimiento_digital: "Sentimiento digital (Trends)",
  motorizacion_total: "Motorización total",
  tasa_homicidios: "Tasa de homicidios dolosos", tasa_robos: "Tasa de robos (rapiñas)",
  ratio_motos_autos: "Ratio motos/autos",
  patentamiento_motos: "Patentamiento de motos", patentamiento_autos: "Patentamiento de autos",
  consumo_supermercados: "Ventas en supermercados",
  desocupacion: "Desocupación",
  // gestion
  cepo_mulc: "Brecha cambiaria", privatizaciones: "Privatizaciones (etapas)",
  concesiones_infraestructura: "Concesiones viales", reduccion_estado: "Empleados de la administración nacional",
  reestructuracion_organismos: "Reestructuración de organismos", rigi_inversiones: "Grandes inversiones aprobadas",
  cobertura_judicial: "Cobertura de cargos judiciales",
  produccion_legislativa: "Producción legislativa del Congreso",
  judicializacion: "Densidad de menciones cautelares en sumarios del Sistema Argentino de Información Jurídica",
  velocidad_resolucion: "Tasa de resolución de la Corte",
  paralisis_denuncias: "Actividad de las comisiones de control",
  empleo_registrado: "Empleo registrado privado",
  desregulacion_normativa: "Desregulación normativa", apertura_comercial: "Impuestos sobre el comercio exterior",
  gasto_funcionamiento: "Gasto de funcionamiento", masa_salarial: "Masa salarial pública",
  asistencia_directa: "Planes sin intermediarios", fal_modernizacion_laboral: "Fondo de Asistencia Laboral",
  libertad_opcion_salud: "Implementación de la libre elección de cobertura de salud", protocolo_antipiquetes: "Reducción de cortes de calle en la Ciudad",
  litigiosidad_laboral: "Juicios por riesgos del trabajo (Superintendencia de Riesgos del Trabajo)", siniestralidad_laboral: "Siniestralidad laboral (Superintendencia de Riesgos del Trabajo)", juicios_trabajo_capital: "Juicios en la Justicia del Trabajo (Capital)", alertas_manifestacion: "Alertas de manifestación (Gobierno de la Ciudad de Buenos Aires)",
  protestas_caba: "Protestas en la Ciudad de Buenos Aires (Proyecto de Datos de Ubicación y Eventos de Conflictos Armados)",
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
  if (ind.estado === "sin_universo") return ind.desactualizado ? `sin universo · consulta a ${ind.fecha_dato}` : "sin universo";
  if (b === "placeholder") return "— pendiente";
  if (b === "rezagado") return `dato a ${ind.fecha_dato}`;
  return null;
}

// Unidad CORTA por indicador para mostrar junto al valor. La unidad larga de
// informe.json (descriptiva) va al atributo title de la fila — si se mostrara
// entera desborda la card. Sólo para indicadores con valor numérico.
export const UNIDADES_CORTAS: Record<string, string> = {
  // macro
  ipc_total: "%", reservas_bcra: "millones de dólares", idc: "frente a un mes normal (0)", badlar: "%", emae_ia: "% frente a un año atrás",
  emae_difusion: "% sectores",
  ipi_manufacturero: "% frente a un año atrás (promedio de 3 meses)", actividad_tributaria: "% interanual real",
  ipc_nucleo: "%", cuenta_corriente: "millones de dólares", pobreza_indec: "%",
  saldo_comercial_12m: "% del comercio", saldo_comercial_12m_usd: "millones de dólares", recaudacion: "base 100 = fines de 2023", tcrm: "diciembre de 2015 = 100", rem_ipc_12m: "%",
  tcr_terminos_intercambio: "puntos", terminos_intercambio: "2004 = 100",
  idm: "puntos porcentuales", desequilibrio_monetario: "puntos de tensión (más alto = peor)",
  iai: "% frente a un año atrás", icip: "% interanual", credito_privado: "% real frente a un año atrás", costo_financiamiento_tesoro: "% real", resultado_primario: "% de la recaudación",
  prestamos_privados: "% mensual", base_monetaria: "% mensual", tc_mayorista: "% mensual",
  // politica
  votometro_ventaja_lla: "puntos porcentuales", ratio_dnu: "decretos por ley publicada", movilizacion_cepa: "índice",
  brecha_obra_publica: "puntos porcentuales",
  apoyo_empresario: "saldo",
  apoyo_comercio: "saldo",
  apoyo_campo: "saldo",
  apoyo_construccion: "saldo",
  desafios_legislativos: "normas",
  insistencias_vetos: "vetos (12 meses)",
  rechazos_decretos: "decretos (12 meses)",
  conflictividad_nacional: "% frente a 2023",
  jornadas_individuales_no_trabajadas_12m: "jornadas en 12 meses",
  iaf_transferencias: "% real", transferencias_no_automaticas: "% real frente a 2023", eficacia_legislativa: "%", cohesion_bloque: "%",
  cohesion_bloque_senado: "%", votos_sobre_bancas: "% de la cámara", rotacion_gabinete: "salidas en 12 meses",
  gobernadores_alineamiento: "%", veto_quorum: "%", comisiones_caidas: "%",
  alineamiento_senadores_prov: "%", adhesion_reformas_provincial: "%",
  derrotas_legislativas: "derrotas en 12 meses",
  bloqueo_sostenido: "% en pie",
  // impacto social
  brecha_salario_cbt: "canastas", ipc_alimentos: "% mensual", endeudamiento_familiar: "billones de pesos",
  mora_familias: "%",
  carga_servicio_deuda_hogares: "%",
  icg_utdt: "0-5",
  peso_tarifas: "% salario", alquiler_real: "índice (fines de 2023 = 100)", alquiler_udesa_real: "índice (fines de 2023 = 100)", pobreza_nowcast: "%", indice_lider: "índice", consumo_carne_vacuna: "kg por habitante", consumo_carnes_total: "kg por habitante", consumo_carnes_otras: "kg por habitante", informalidad: "%", ocupacion_eph: "puntos porcentuales frente a 2023", mortalidad_pymes: "empleadores", trabajo_independiente: "%",
  despacho_cemento: "índice", subocupacion_demandante: "% de la población económicamente activa", inseguridad: "% hogares", icc_utdt: "índice",
  sentimiento_digital: "puntos", patentamiento_motos: "unidades", patentamiento_autos: "unidades",
  motorizacion_total: "cada 1.000 habitantes",
  tasa_homicidios: "cada 100.000 habitantes", tasa_robos: "cada 100.000 habitantes",
  ratio_motos_autos: "motos/auto",
  consumo_supermercados: "índice",
  // gestion (insumos del ITCG)
  cepo_mulc: "% sobre el dólar mayorista", reduccion_estado: "% frente a diciembre de 2023", apertura_comercial: "% del intercambio",
  cobertura_judicial: "% cubierto",
  produccion_legislativa: "leyes sancionadas (12 meses)",
  judicializacion: "% de sumarios",
  velocidad_resolucion: "% resuelto",
  paralisis_denuncias: "sesiones (12 meses)",
  empleo_registrado: "miles",
  desregulacion_normativa: "artículos", reestructuracion_organismos: "%",
  gasto_funcionamiento: "% real", masa_salarial: "% real",
  rigi_inversiones: "% de la cartera", privatizaciones: "%", concesiones_infraestructura: "%",
  fal_modernizacion_laboral: "de avance", asistencia_directa: "de 100",
  protocolo_antipiquetes: "% menos que en 2023", libertad_opcion_salud: "de avance",
  litigiosidad_laboral: "% interanual", siniestralidad_laboral: "% frente al año anterior", juicios_trabajo_capital: "% frente a un año atrás", alertas_manifestacion: "alertas por mes",
  protestas_caba: "eventos en 12 meses",
};

// Unidad "larga" para la ficha del modal (campo "Unidad"). Normalizada y
// consistente, independiente del estado del cache de cada colector. Describe
// SOLO la unidad de medida; la metodología vive en "Cómo se calcula".
export const UNIDADES_LARGAS: Record<string, string> = {
  // macro
  ipc_total: "% mensual", reservas_bcra: "Millones de dólares",
  idc: "Desvíos estándar frente a su historia (σ)",
  badlar: "% anual", emae_ia: "% interanual",
  emae_difusion: "% de los 15 sectores del estimador mensual de actividad que crecen interanualmente",
  ipi_manufacturero: "% interanual (promedio de 3 meses)",
  actividad_tributaria: "% interanual real (compuesto 0,6×impuesto al valor agregado + 0,4×impuesto al cheque)",
  ipc_nucleo: "% mensual",
  pobreza_indec: "% de personas (medición oficial semestral)",
  cuenta_corriente: "millones de dólares (acumulado 4 trimestres)",
  saldo_comercial_12m: "% del comercio (exportaciones + importaciones, acumulado de 12 meses)",
  saldo_comercial_12m_usd: "Millones de dólares (acumulado de 12 meses)",
  recaudacion: "índice de base imponible real desestacionalizada, 100 = 4º trimestre de 2023",
  tcrm: "Índice (base diciembre de 2015 = 100)", rem_ipc_12m: "% anual esperado",
  tcr_terminos_intercambio: "Puntaje (0–100)", terminos_intercambio: "Índice (base 2004=100)",
  idm: "Puntos porcentuales (brecha interanual real)",
  desequilibrio_monetario: "Puntos de tensión (0–100; más alto es peor)",
  iai: "% interanual (índice ponderado)", icip: "% interanual (índice ponderado)",
  credito_privado: "% interanual real (deflactado por inflación)",
  costo_financiamiento_tesoro: "% real anual (tasa efectiva de colocación menos inflación esperada)",
  resultado_primario: "% de la recaudación (resultado primario acumulado 12 meses)",
  prestamos_privados: "% mensual", base_monetaria: "% mensual", tc_mayorista: "% mensual",
  // politica
  votometro_ventaja_lla: "Puntos porcentuales", ratio_dnu: "decretos de necesidad y urgencia publicados por ley publicada",
  brecha_obra_publica: "Puntos porcentuales de brecha",
  apoyo_empresario: "Saldo de apoyos y críticas (−1 a +1)",
  apoyo_comercio: "Saldo de apoyos y críticas (−1 a +1)",
  apoyo_campo: "Saldo de apoyos y críticas (−1 a +1)",
  apoyo_construccion: "Saldo de apoyos y críticas (−1 a +1)",
  desafios_legislativos: "Normas desafiadas (12 meses)",
  insistencias_vetos: "Vetos insistidos por las dos cámaras (últimos 12 meses)",
  rechazos_decretos: "Decretos de necesidad y urgencia y delegados derogados por las dos cámaras (últimos 12 meses)",
  movilizacion_cepa: "Índice (0–100)",
  conflictividad_nacional: "% de variación frente a 2023 (eventos de protesta y disturbios en el país, acumulado de 12 meses)",
  jornadas_individuales_no_trabajadas_12m: "Jornadas individuales no trabajadas por paros (acumulado de 12 meses)",
  iaf_transferencias: "% interanual real",
  transferencias_no_automaticas: "% de variación real frente a 2023 (transferencias no automáticas, acumulado de 12 meses)",
  eficacia_legislativa: "% de proyectos",
  cohesion_bloque: "% de votos (Rice bicameral: Diputados 65% + Senado 35%)",
  cohesion_bloque_senado: "% de votos (Senado — fusionado en el compuesto bicameral)",
  votos_sobre_bancas: "% de las bancas de la cámara que votan a favor sin ser del bloque oficialista (leyes aprobadas; Diputados 65% + Senado 35%)",
  rotacion_gabinete: "Salidas de rango ministerial (acumulado de 12 meses)",
  gobernadores_alineamiento: "% de gobernadores (retirado)", veto_quorum: "% de sesiones",
  alineamiento_senadores_prov: "% de votos de senadores de otros bloques que acompañan al oficialismo (promedio entre provincias)",
  adhesion_reformas_provincial: "% de jurisdicciones adheridas (sobre 24)",
  comisiones_caidas: "% de proyectos",
  derrotas_legislativas: "Derrotas en el recinto (vetos insistidos + decretos rechazados, acumulado de 12 meses)",
  bloqueo_sostenido: "% de normas desafiadas en el recinto que siguen en pie (últimos 12 meses)",
  // impacto social
  brecha_salario_cbt: "Canastas", ipc_alimentos: "% mensual",
  endeudamiento_familiar: "Billones de pesos", mora_familias: "% de la cartera en situación irregular",
  carga_servicio_deuda_hogares: "% de la masa salarial registrada comprometida en servicios de deuda",
  icg_utdt: "Índice de 0 a 5 (más es más confianza)",
  peso_tarifas: "% del salario registrado promedio", alquiler_real: "índice (fines de 2023 = 100)", alquiler_udesa_real: "índice (fines de 2023 = 100)", pobreza_nowcast: "% de personas en hogares pobres", indice_lider: "Índice (nivel)",
  consumo_carne_vacuna: "kg por habitante por año", consumo_carnes_total: "kg por habitante por año (vacuna + aviar + porcina)", consumo_carnes_otras: "kg por habitante por año (aviar + porcina)",
  informalidad: "% de asalariados",
  ocupacion_eph: "Diferencia de la tasa de empleo contra el mismo trimestre de 2023 (puntos porcentuales)",
  mortalidad_pymes: "Empleadores de hasta 50 trabajadores con cobertura de una aseguradora de riesgos del trabajo",
  trabajo_independiente: "% del empleo registrado que son autónomos o monotributistas del régimen general (sin monotributo social)", despacho_cemento: "Índice", subocupacion_demandante: "% de la población económicamente activa",
  inseguridad: "% de hogares víctimas (últimos 12 meses)", icc_utdt: "Índice",
  sentimiento_digital: "Índice (100 = 4º trimestre de 2023)",
  patentamiento_motos: "Unidades",
  patentamiento_autos: "Unidades (autos 0km inscriptos en el mes)",
  motorizacion_total: "Vehículos 0km (autos + motos) por cada 1.000 habitantes, acumulado de 12 meses",
  tasa_homicidios: "Homicidios dolosos por cada 100.000 habitantes (tasa oficial del Sistema Nacional de Información Criminal, anual)",
  tasa_robos: "Robos, excluidos los agravados por lesiones o muertes, por cada 100.000 habitantes (tasa oficial del Sistema Nacional de Información Criminal, anual)",
  ratio_motos_autos: "Motos patentadas por cada auto patentado, acumulado móvil de 12 meses",
  consumo_supermercados: "Índice de ventas a precios constantes (2017 = 100, desestacionalizado)",
  // gestion
  cepo_mulc: "% de brecha", privatizaciones: "% de avance (etapas 0-4)",
  concesiones_infraestructura: "% de km de las etapas licitadas con adjudicación publicada (no toma de posesión)", reduccion_estado: "% de variación frente a diciembre de 2023",
  reestructuracion_organismos: "% de avance", rigi_inversiones: "% de la inversión de la cartera del régimen de grandes inversiones ya aprobada",
  cobertura_judicial: "% de cargos de juez habilitados con juez designado",
  produccion_legislativa: "leyes sancionadas en los últimos 12 meses, sin las vetadas en su totalidad",
  judicializacion: "sumarios con medida cautelar sobre el total, jurisdicción Federal + Nacional",
  velocidad_resolucion: "expedientes resueltos sobre ingresados en el año (Corte Suprema)",
  paralisis_denuncias: "sesiones documentadas de las comisiones de Acusación y Disciplina en 12 meses",
  empleo_registrado: "Miles de asalariados registrados del sector privado",
  desregulacion_normativa: "Artículos modificados o eliminados desde diciembre de 2023 (volumen, no importancia)", apertura_comercial: "% del intercambio (alícuota efectiva)",
  gasto_funcionamiento: "% de variación real: promedio de los últimos 12 meses frente al promedio de 2023", masa_salarial: "% de variación real frente a 2023",
  asistencia_directa: "Unidades de gestión dadas de baja (Resolución 84/2024) — 0 o 100", fal_modernizacion_laboral: "Avance de la puesta en marcha del Fondo (0–100)",
  libertad_opcion_salud: "Avance de la libre elección por hitos (0–100)", protocolo_antipiquetes: "% de reducción de cortes en la Ciudad de Buenos Aires frente a 2023, dato del año 2025 (no mide la aplicación del protocolo)",
  litigiosidad_laboral: "% variación (12 meses frente a los 12 meses previos)",
  siniestralidad_laboral: "% variación del índice de incidencia de accidentes y enfermedades laborales con baja (por mil cubiertos), del período acumulado del año contra el mismo período del año anterior",
  juicios_trabajo_capital: "% variación de los juicios entrados (12 meses frente a los 12 meses previos, por semestre)",
  alertas_manifestacion: "Alertas únicas en el mes (avisos del transporte público porteño)",
  protestas_caba: "Eventos de protesta (acumulado de 12 meses)",
};

// Unidad de la SERIE del gráfico cuando difiere de la unidad de la card
// (pares card/serie con semántica distinta, las excepciones G3 del gate).
// Sin entrada, el gráfico usa la unidad corta de la card.
export const UNIDADES_SERIE: Record<string, string> = {
  protestas_caba: "eventos por mes",      // card = acumulado 12m; serie = eventos por mes
  rigi_inversiones: "millones de dólares aprobados", // card = % del pipeline; serie = inversión aprobada acumulada
  // ADR-0217/ADR-0322/ADR-0392: la card publica el nivel per cápita de SAGYP
  // (kg/hab) y la serie es ese mismo consumo en índice base-100 = 4T-2023,
  // que es lo que puntúa. Sin esta
  // línea el gráfico rotulaba el índice como kilos: mostraba "95 kg/hab" al
  // lado de una card que decía 114,45 kg/hab, para el MISMO mes. ADR-0322
  // separó el compuesto en vacuna y el resto (aviar+porcina); las dos heredan
  // la misma excepción.
  consumo_carne_vacuna: "índice (100 = 4º trimestre de 2023)",
  consumo_carnes_total: "índice (100 = 4º trimestre de 2023)",
  consumo_carnes_otras: "índice (100 = 4º trimestre de 2023)",
  // ADR-0224: mismo caso. La card publica el NIVEL —vehículos 0km por cada mil
  // habitantes, que es el número que le dice algo al lector— y la serie el
  // índice base-100 que es lo que puntúa. Acá las dos salen de la MISMA
  // descarga de la DNRPA: es sólo un cambio de unidad, no de fuente.
  motorizacion_total: "índice (100 = 4º trimestre de 2023)",
};

// Datos duros de migración real. Acompañaban a indice_intencion_migratoria
// como contraste en el modal; ese indicador salió con el cinturón de espíritu
// de época (ADR-0205). El mapa queda porque el bloque `contexto_duro` es
// genérico y estas etiquetas son las únicas que hay escritas — si nadie lo usa
// en unos meses, se borra.
export const CONTEXTO_DURO_META: Record<string, { label: string; freq: "mensual" | "anual"; nota?: string }> = {
  eeuu_niv: { label: "Estados Unidos — visas de no inmigrante emitidas a argentinos", freq: "mensual", nota: "incluye turismo y negocios" },
  eeuu_iv: { label: "Estados Unidos — visas de inmigrante (residencia permanente)", freq: "mensual" },
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
  if (ind.estado === "sin_universo") return { texto: "Sin universo", unidad: "", titulo: typeof ind.detalle_txt === "string" ? ind.detalle_txt : "Sin denominador para calcular la tasa" };
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

// Qué cinturón produjo el riesgo dominante, con su nombre público y su score.
//
// El nombre del barbarismo NO alcanza para encontrarlo: `politica` y
// `vida_cotidiana` comparten "político" (BARBARISMO_MAP en config.py). En
// agosto de 2026 la portada decía "Riesgo dominante: Político" con Impacto
// social en 6,1 y Política en 3,3 y verde — el lector buscaba la card
// Política y el veredicto parecía contradecir a su propia tabla (ADR-0237).
//
// La fuente es el campo publicado. El fallback existe sólo para snapshots
// anteriores a ago-2026 (el archivo), y es exacto, no aproximado: el
// dominante es el de mayor score, y entre los que comparten su barbarismo el
// de mayor score ES el de mayor score de todos.
export interface Dominante { key: string; nombre: string; slug: string; score: number; }

export function cinturonDominante(inf: Informe): Dominante | null {
  if (!inf.barbarismo_activo) return null;
  const meta = (key: string) => CINTURONES.find(c => c.key === key);
  const arma = (key: string): Dominante | null => {
    const m = meta(key), c = (inf.cinturones as Record<string, Cinturon>)[key];
    return m && c ? { key, nombre: m.nombre, slug: m.slug, score: c.score } : null;
  };
  if (inf.cinturon_dominante) return arma(inf.cinturon_dominante);
  const candidatos = Object.entries(inf.cinturones)
    .filter(([, c]) => c.barbarismo_riesgo === inf.barbarismo_activo);
  if (!candidatos.length) return null;
  return arma(candidatos.reduce((a, b) => (b[1].score > a[1].score ? b : a))[0]);
}

// Indicadores que representan un NIVEL en escala 0–100 (porcentaje de algo o
// índice 0–100) y admiten una barra de progreso. Se excluyen variaciones
// (% m/m, % i.a., % real), ratios y conteos, donde una barra 0–100 no aplica.
export const BARRA_0_100 = new Set<string>([
  "eficacia_legislativa", "cohesion_bloque", "alineamiento_senadores_prov",
  "adhesion_reformas_provincial", "veto_quorum", "comisiones_caidas", "movilizacion_cepa",
  "informalidad", "subocupacion_demandante", "sentimiento_digital", "icc_utdt", "indice_intencion_migratoria",
  "mora_familias", "carga_servicio_deuda_hogares",
]);

function clamp100(n: number): number { return Math.max(0, Math.min(100, n)); }

export type Visual =
  | { tipo: "sparkline" }
  | { tipo: "barra"; pct: number; avance: boolean }
  | { tipo: "numero" };

// Decide el mejor visual para un indicador: serie histórica → sparkline;
// avance de reforma o nivel 0–100 → barra; en otro caso → número grande.
export function visualDe(key: string, ind: Indicador): Visual {
  if (ind.estado === "sin_universo") return { tipo: "numero" };
  if (typeof ind.avance_pct === "number") return { tipo: "barra", pct: clamp100(ind.avance_pct), avance: true };
  if ((series[key] ?? []).length >= 2) return { tipo: "sparkline" };
  if (BARRA_0_100.has(key) && typeof ind.valor === "number") return { tipo: "barra", pct: clamp100(ind.valor), avance: false };
  return { tipo: "numero" };
}

// Badge honesto del origen del dato.
export function badgeEstado(ind: Indicador): "Automático" | "Semiautomático" | "Carga manual" | "Estimación" | "Sin universo" {
  if (ind.estado === "sin_universo") return "Sin universo";
  if (ind.estado === "placeholder" || ind.valor === null) return "Estimación";
  if (ind.metodo_obtencion === "manual") return "Carga manual";
  if (ind.metodo_obtencion === "semiautomatico") return "Semiautomático";
  return "Automático";
}

// ── Período del dato para el chip de la card ─────────────────────────────
// Reemplaza al rótulo "Automático" (que no informaba nada al lector): el chip
// muestra a qué período corresponde el dato. Mensuales → "jun 2026";
// trimestrales EPH → "1T 2026" (fecha_dato = inicio del trimestre relevado);
// anuales → el año del dato. Para los indicadores de ventana móvil viva
// (ratio_dnu, derrotas, cepo, etc.) fecha_dato es la fecha de la corrida y el
// mes corriente ES el período correcto ("dato al día"). Dos excepciones con
// dato anual: veto_quorum (período legislativo en curso = año calendario de
// la corrida). iaf_transferencias dejó de serlo (ADR-0353): son 12 meses
// móviles y su fecha_dato es el fin del último mes con IPC, así que sigue la
// regla mensual de abajo.
const MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun",
                      "jul", "ago", "sep", "oct", "nov", "dic"];
const PERIODO_TRIMESTRAL = new Set(["informalidad", "ocupacion_eph", "subocupacion_demandante"]);
const PERIODO_ANUAL = new Set(["veto_quorum", "protocolo_antipiquetes"]);

export function periodoDato(key: string, ind: Indicador): string {
  const f = String(ind.fecha_dato ?? "");
  const anio = parseInt(f.slice(0, 4), 10);
  if (!anio) return "—";
  if (PERIODO_ANUAL.has(key)) return String(anio);
  const mes = parseInt(f.slice(5, 7), 10);
  if (!mes) return String(anio);
  if (key === "brecha_obra_publica") return `expect. ${MESES_CORTOS[mes - 1]} ${anio}`;
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
