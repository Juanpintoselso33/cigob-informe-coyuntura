// Título y descripción de cada página para Google y para la vista previa al
// compartir (ADR-0442). Reglas:
//   - Título único por página, de hasta 60 caracteres con la marca (tope duro
//     65): lo que la gente escribe en el buscador va primero, « | CiGob» al final.
//   - Descripción de 120 a 155 caracteres, con el dato y su mes cuando lo hay.
//   - El rótulo de la card no cambia: el término de búsqueda es aparte (BUSQUEDA).
//   - La tensión va en palabras, nunca con número (ADR-0337).
// Los topes se controlan en el build: un título largo o repetido lo hace fallar.
import { informe, CINTURONES, label, presentacion, periodoDato, indiceDe, colorPorTension, LECTURA_SEMAFORO } from "./datos.ts";
import { DESCRIPCIONES } from "./descripciones.ts";
import { FICHAS, type FichaIndice } from "./fichas.ts";

export const MARCA = " | CiGob";
const TOPE_TITULO = 65;
const TOPE_DESCRIPCION = 155;

/** Lo que se busca en Google para cada ficha de indicador. Sin entrada, se usa
 *  el rótulo de la card (con «en Argentina» si entra). */
export const BUSQUEDA: Record<string, string> = {
  // Macroeconomía
  ipc_total: "Inflación mensual en Argentina (IPC del INDEC)",
  reservas_bcra: "Reservas netas del BCRA: qué son y cuánto hay",
  reservas_brutas: "Reservas brutas del BCRA: último dato",
  meta_reservas_fmi: "Meta de reservas con el FMI: cuánto se cumplió",
  idc: "Capacidad prestable de los bancos en Argentina",
  emae_ia: "Actividad económica en Argentina (EMAE del INDEC)",
  emae_difusion: "Sectores de la economía en alza (EMAE por sector)",
  ipi_manufacturero: "Producción industrial en Argentina (IPI del INDEC)",
  saldo_comercial_12m: "Saldo comercial de Argentina en 12 meses",
  actividad_tributaria: "Recaudación real de IVA e impuesto al cheque",
  recaudacion: "Recaudación real en Argentina: base imponible",
  tcrm: "Tipo de cambio real multilateral (BCRA)",
  terminos_intercambio: "Términos del intercambio de Argentina (INDEC)",
  rem_ipc_12m: "Inflación esperada a 12 meses (REM del BCRA)",
  desequilibrio_monetario: "Liquidez en pesos y demanda de dólares",
  iai: "Inversión en Argentina: construcción y maquinaria",
  credito_privado: "Crédito privado en pesos en términos reales",
  resultado_primario: "Resultado primario del Estado nacional",
  costo_financiamiento_tesoro: "Tasa real de la deuda en pesos del Tesoro",
  // Política
  cobertura_judicial: "Vacantes judiciales: cargos cubiertos en Argentina",
  produccion_legislativa: "Producción legislativa del Congreso argentino",
  judicializacion: "Medidas cautelares en la jurisprudencia (SAIJ)",
  velocidad_resolucion: "Tasa de resolución de la Corte Suprema",
  paralisis_denuncias: "Actividad de las comisiones de control del Congreso",
  votometro_ventaja_lla: "Encuestas: ventaja de La Libertad Avanza sobre el PJ",
  insistencias_vetos: "Vetos que el Congreso dio vuelta (insistencias)",
  rechazos_decretos: "Decretos rechazados o derogados por el Congreso",
  desafios_legislativos: "Normas del Ejecutivo desafiadas en el Congreso",
  brecha_obra_publica: "Obra pública frente a privada: expectativas",
  apoyo_empresario: "Qué dice la industria del Gobierno (UIA)",
  apoyo_campo: "Qué dice el campo del Gobierno: SRA, CRA y Coninagro",
  apoyo_comercio: "Qué dice el comercio del Gobierno (CAC)",
  apoyo_construccion: "Qué dice la construcción del Gobierno (CAMARCO)",
  ratio_dnu: "Decretos de necesidad y urgencia por cada ley",
  conflictividad_nacional: "Protestas y conflictividad social en Argentina",
  jornadas_individuales_no_trabajadas_12m: "Paros en Argentina: jornadas no trabajadas",
  iaf_transferencias: "Transferencias a provincias: armonía federal",
  transferencias_no_automaticas: "Transferencias no automáticas a las provincias",
  eficacia_legislativa: "Leyes del Ejecutivo aprobadas por el Congreso",
  cohesion_bloque: "Cohesión del bloque oficialista en el Congreso",
  votos_sobre_bancas: "Cuántos diputados votan las leyes del Gobierno",
  alineamiento_senadores_prov: "Cómo votan los senadores de cada provincia",
  adhesion_reformas_provincial: "Provincias adheridas al RIGI",
  // Gestión
  cepo_mulc: "Brecha cambiaria en Argentina: CCL y mayorista",
  apertura_comercial: "Retenciones y aranceles sobre el comercio exterior",
  desregulacion_normativa: "Desregulación: artículos modificados o eliminados",
  reduccion_estado: "Empleados públicos nacionales: cuánto bajó la planta",
  gasto_funcionamiento: "Gasto de funcionamiento del Estado nacional",
  masa_salarial: "Masa salarial del sector público nacional",
  reestructuracion_organismos: "Organismos públicos disueltos o cerrados",
  fal_modernizacion_laboral: "Fondo de Asistencia Laboral (Ley 27.802): avance",
  litigiosidad_laboral: "Juicios por riesgos del trabajo en Argentina (SRT)",
  siniestralidad_laboral: "Siniestralidad laboral en Argentina: qué significa",
  juicios_trabajo_capital: "Juicios en la Justicia del Trabajo de la Capital",
  privatizaciones: "Privatizaciones de empresas públicas: avance",
  rigi_inversiones: "RIGI: grandes inversiones aprobadas",
  concesiones_infraestructura: "Concesiones viales: rutas nacionales adjudicadas",
  asistencia_directa: "Planes sociales sin intermediarios",
  protocolo_antipiquetes: "Cortes de calle en la Ciudad: cuánto bajaron",
  libertad_opcion_salud: "Libre elección de obra social y prepaga: avance",
  // Impacto social
  empleo_registrado: "Empleo registrado privado en Argentina",
  brecha_salario_cbt: "Salario frente a la canasta básica total",
  ipc_alimentos: "Precio de los alimentos frente a la inflación",
  mora_familias: "Morosidad de las familias con bancos y tarjetas",
  icg_utdt: "Índice de Confianza en el Gobierno (Di Tella)",
  carga_servicio_deuda_hogares: "Deuda de los hogares: cuánto del salario se lleva",
  alquiler_real: "Alquileres en términos reales: contratos vigentes",
  alquiler_udesa_real: "Precio real de los alquileres publicados",
  peso_tarifas: "Tarifas de servicios públicos frente al salario",
  consumo_carne_vacuna: "Consumo de carne vacuna por habitante en Argentina",
  consumo_carnes_total: "Consumo total de carne por habitante en Argentina",
  consumo_carnes_otras: "Consumo de pollo y cerdo por habitante",
  pobreza_nowcast: "Pobreza en Argentina: estimación mensual",
  ocupacion_eph: "Tasa de empleo en Argentina (EPH del INDEC)",
  informalidad: "Trabajo informal en Argentina (EPH del INDEC)",
  mortalidad_pymes: "Cierre de pymes: empleadores activos",
  trabajo_independiente: "Trabajo independiente en Argentina: su peso",
  despacho_cemento: "Despacho de cemento y construcción en Argentina",
  subocupacion_demandante: "Subocupación demandante en Argentina",
  inseguridad: "Victimización: hogares que sufrieron un delito",
  tasa_homicidios: "Tasa de homicidios en Argentina (SNIC)",
  tasa_robos: "Tasa de robos en Argentina (SNIC)",
  icc_utdt: "Índice de Confianza del Consumidor (Di Tella)",
  sentimiento_digital: "Sentimiento digital: búsquedas en Google Trends",
  motorizacion_total: "Patentamientos de autos y motos por habitante",
  ratio_motos_autos: "Motos por cada auto patentado en Argentina",
  consumo_supermercados: "Ventas en supermercados en Argentina (INDEC)",
};

/** Títulos y descripciones de las páginas fijas. */
export const PAGINAS = {
  metodologia: {
    title: "Metodología del Monitor del Plan de Gobierno" + MARCA,
    description: "Cómo se mide la tensión del plan de gobierno: los cuatro índices, sus dimensiones, las fuentes de cada indicador y las fichas metodológicas completas.",
  },
  glosario: {
    title: "Glosario del Monitor del Plan de Gobierno" + MARCA,
    description: "Los términos del Monitor del Plan de Gobierno explicados en llano: cinturón, dimensión, índice, ponderación, normalización, gobernabilidad y más.",
  },
  equipo: {
    title: "Equipo del Monitor del Plan de Gobierno" + MARCA,
    description: "Quiénes hacen el Monitor del Plan de Gobierno en la Fundación CiGob: la coordinación, el desarrollo y los colaboradores de la medición mensual.",
  },
  archivo: {
    title: "Archivo mes a mes del Monitor del Plan de Gobierno" + MARCA,
    description: "Todos los meses publicados del Monitor del Plan de Gobierno, con la tensión de cada cinturón, para comparar cómo evolucionó el plan de Milei.",
  },
};

const CINT_NOMBRE: Record<string, string> = {
  macro: "Macroeconomía", politica: "Política", vida_cotidiana: "Impacto social", gestion: "Gestión",
};
const TITULO_CINTURON: Record<string, string> = {
  macro: "Economía argentina mes a mes: tensión macroeconómica",
  politica: "Gobernabilidad de Milei: tensión política",
  vida_cotidiana: "Impacto social del plan de Milei: bolsillo y calle",
  gestion: "Reformas del gobierno de Milei: cuánto avanzan",
};
const TEMA_CINTURON: Record<string, string> = {
  macro: "Inflación, reservas, actividad, cuentas públicas y crédito",
  politica: "Congreso, provincias, Justicia, conflicto social y apoyo del sector privado",
  vida_cotidiana: "Salario, pobreza, empleo, consumo, alquileres, tarifas y seguridad",
  gestion: "Desregulación, tamaño del Estado, privatizaciones, inversiones y reformas laborales",
};

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
function mesDe(iso: string): string {
  const [y, m] = iso.split("-");
  return `${MESES[+m - 1]} de ${y}`;
}
const mesEdicion = mesDe(informe.period);

function tensionEnPalabras(tension: number | null | undefined): string | null {
  const color = colorPorTension(tension);
  return color ? LECTURA_SEMAFORO[color].toLowerCase() : null;
}

function primeraOracion(texto: string): string {
  const t = texto.replace(/\s+/g, " ").trim();
  const m = /^.+?[.!?](\s|$)/.exec(t);
  return (m ? m[0] : t).trim();
}

/** Arma la descripción: la base y, de las colas posibles, la primera que entra. */
function ajustar(base: string, colas: string[]): string {
  const b = base.replace(/\s+/g, " ").trim();
  for (const cola of colas.filter(c => c.trim())) {
    const s = `${b} ${cola}`.trim();
    if (s.length <= TOPE_DESCRIPCION) return s;
  }
  if (b.length <= TOPE_DESCRIPCION) return b;
  const corte = b.slice(0, TOPE_DESCRIPCION - 1);
  return corte.slice(0, corte.lastIndexOf(" ")).replace(/[,;:]$/, "") + "…";
}

const COLA_FICHA = "Qué mide, de qué fuente sale y cuánta tensión suma al plan de gobierno.";
const COLA_FICHA_CORTA = "Qué mide y de qué fuente sale.";
const COLA_CON_QUE = "Fuente, método y tensión que suma al plan de gobierno.";
const COLA_CON_QUE_CORTA = "Fuente y método.";

/** El período que representa el dato, dicho entero: el mismo criterio que el
 *  chip de la card (periodoDato), más los anuales que cierran el 31 de
 *  diciembre y los acumulados del año. Un trimestre o un año no se nombran con
 *  su primer o su último mes. */
const ACUMULADO_DEL_ANIO = new Set(["siniestralidad_laboral"]);
const TRIMESTRES = ["primer", "segundo", "tercer", "cuarto"];
function periodoEnTexto(id: string, ind: any): string {
  const f = String(ind.fecha_dato ?? "");
  if (/^\d{4}-12-31/.test(f)) return `año ${f.slice(0, 4)}`;
  if (ACUMULADO_DEL_ANIO.has(id)) return `acumulado a ${mesDe(f)}`;
  const p = periodoDato(id, ind);
  const t = /^(\d)T (\d{4})$/.exec(p);
  if (t) return `${TRIMESTRES[+t[1] - 1]} trimestre de ${t[2]}`;
  if (/^\d{4}$/.test(p)) return `año ${p}`;
  if (id === "brecha_obra_publica") return `expectativas a ${mesDe(f)}`;
  return mesDe(f);
}

/** El valor con su unidad, para leerse de corrido en una oración (en la card
 *  la unidad va aparte y puede ser telegráfica: «2,04 0-5», «−0,3 saldo»). */
function valorEnTexto(texto: string, unidad: string): string {
  const u = unidad.trim();
  if (!u) return texto;
  if (u.includes("=")) return `${texto} (${u})`;
  if (u === "0-5") return `${texto} en una escala de 0 a 5`;
  if (u === "saldo") return `saldo de ${texto}`;
  if (u === "de avance") return `${texto} sobre 100 de avance`;
  if (u === "índice") return `índice de ${texto}`;
  const pctDe: Record<string, string> = { "% salario": "% del salario", "% hogares": "% de los hogares", "% sectores": "% de los sectores" };
  return `${texto} ${pctDe[u] ?? u}`;
}

function tituloFicha(id: string): string {
  const f = FICHAS[id];
  if (f.tipo !== "indicador") {
    const fx = f as FichaIndice;
    const c = (informe.cinturones as any)[f.cinturon];
    const sigla = c ? indiceDe(c)?.sigla : null;
    return `${sigla ? `${sigla}: ` : ""}${fx.nombreLargo}${MARCA}`;
  }
  const termino = BUSQUEDA[id];
  if (termino) return termino + MARCA;
  const conPais = `${label(id)} en Argentina${MARCA}`;
  return !label(id).includes("(") && conPais.length <= 60 ? conPais : label(id) + MARCA;
}

function descripcionFicha(id: string): string {
  const f = FICHAS[id];
  const c = (informe.cinturones as any)[f.cinturon];
  if (f.tipo !== "indicador") {
    const fx = f as FichaIndice;
    const sigla = c ? indiceDe(c)?.sigla : null;
    const lectura = tensionEnPalabras(c?.score);
    const base = lectura
      ? `${sigla ?? fx.nombreLargo}, ${mesEdicion}: ${lectura}.`
      : `${fx.nombreLargo}.`;
    return ajustar(base, [primeraOracion(fx.resumen), "Cómo se calcula, qué indicadores lo componen y con qué pesos."]);
  }
  const ind = c?.indicadores?.[id];
  const que = DESCRIPCIONES[id]?.que ?? "";
  // El rótulo de la card, sin la aclaración entre paréntesis: el término de
  // búsqueda ya está en el título.
  const nombre = label(id).replace(/\s*\([^)]*\)/g, "").trim();
  const pres = ind ? presentacion(id, ind) : null;
  if (pres && typeof ind.valor === "number" && ind.fecha_dato) {
    const periodo = periodoEnTexto(id, ind);
    const valor = valorEnTexto(pres.texto, pres.unidad ?? "");
    const q = primeraOracion(que);
    return ajustar(`${nombre}: ${valor}, ${periodo}.`, [q && `${q} ${COLA_CON_QUE}`, q && `${q} ${COLA_CON_QUE_CORTA}`, q, COLA_FICHA, COLA_FICHA_CORTA]);
  }
  // Sin dato vigente (indicadores retirados o en pausa): lo que mide.
  const q = primeraOracion(que);
  return ajustar(`${nombre}.`, [q && `${q} ${COLA_CON_QUE}`, q && `${q} ${COLA_CON_QUE_CORTA}`, q, COLA_FICHA, COLA_FICHA_CORTA]);
}

export interface Seo { title: string; description: string }

export function seoFicha(id: string): Seo {
  return { title: tituloFicha(id), description: descripcionFicha(id) };
}

export function seoCinturon(key: string): Seo {
  const c = (informe.cinturones as any)[key];
  const lectura = tensionEnPalabras(c?.score);
  const nombre = CINT_NOMBRE[key];
  const base = lectura ? `${nombre}, ${mesEdicion}: ${lectura}.` : `${nombre}.`;
  return {
    title: TITULO_CINTURON[key] + MARCA,
    description: ajustar(base, [
      `${TEMA_CINTURON[key]}: cada indicador con su dato, su fuente y su tensión, medido por la Fundación CiGob.`,
      `${TEMA_CINTURON[key]}, medidos mes a mes por la Fundación CiGob.`,
      `${TEMA_CINTURON[key]}.`,
    ]),
  };
}

export function seoPortada(): Seo {
  const lectura = tensionEnPalabras(informe.score_global);
  const mes = mesEdicion[0].toUpperCase() + mesEdicion.slice(1);
  const base = lectura ? `${mes}: el plan de gobierno de Milei, con ${lectura}.` : `${mes}.`;
  return {
    title: "Monitor del Plan de Gobierno de Milei, mes a mes" + MARCA,
    description: ajustar(base, [
      "Cuánta tensión enfrenta en la economía, el impacto social, la política y la gestión, medida mes a mes por la Fundación CiGob.",
      "Economía, impacto social, política y gestión, medidas mes a mes por la Fundación CiGob.",
      "Economía, impacto social, política y gestión, medidas por la Fundación CiGob.",
    ]),
  };
}

// ── Guardas del build: un título largo o repetido no se publica ──────────
{
  const todos: [string, string][] = [
    ["portada", seoPortada().title],
    ...Object.entries(PAGINAS).map(([k, v]) => [k, v.title] as [string, string]),
    ...CINTURONES.map(c => [c.slug, seoCinturon(c.key).title] as [string, string]),
    ...Object.keys(FICHAS).map(id => [id, tituloFicha(id)] as [string, string]),
  ];
  const largos = todos.filter(([, t]) => t.length > TOPE_TITULO);
  if (largos.length) throw new Error(`Títulos de más de ${TOPE_TITULO} caracteres: ${largos.map(([k, t]) => `${k} (${t.length})`).join(", ")}`);
  const vistos = new Map<string, string>();
  const repetidos: string[] = [];
  for (const [k, t] of todos) {
    if (vistos.has(t)) repetidos.push(`${vistos.get(t)} y ${k}: «${t}»`);
    vistos.set(t, k);
  }
  if (repetidos.length) throw new Error(`Títulos repetidos: ${repetidos.join("; ")}`);
  const sobrantes = Object.keys(BUSQUEDA).filter(id => !FICHAS[id]);
  if (sobrantes.length) throw new Error(`BUSQUEDA tiene ids sin ficha: ${sobrantes.join(", ")}`);
}
