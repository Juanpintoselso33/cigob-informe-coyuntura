// ── Fichas metodológicas (/metodologia) ─────────────────────────────────────
// El estándar de documentación por indicador del informe. La estructura adapta
// tres referencias de la industria estadística:
//   · el template de metadatos de indicadores ODS (IAEG-SDGs, Naciones Unidas):
//     definición, fuentes, método de cómputo (4.c), limitaciones (4.b),
//     tratamiento de faltantes (4.g);
//   · la ficha metodológica de los institutos de estadística (DANE/INE);
//   · las "data pages" de Our World in Data (última actualización, linaje del
//     dato, "lo que hay que saber para leerlo").
// Para los índices compuestos (ITCM/ITCG/ITCIS) las secciones siguen el
// checklist del Handbook on Constructing Composite Indicators (OCDE/JRC, 2008).
//
// División del trabajo — cada dato vive en UNA sola fuente:
//   · qué mide / qué aporta            → descripciones.ts (compartido con el modal)
//   · fórmula de cómputo               → formulas.ts (compartido con el modal)
//   · valores, puntajes, pesos, bandas → informe.json (runtime: la app es la
//     fuente de verdad; la ficha se reconstruye con cada actualización diaria)
//   · serie histórica y cobertura      → series.json
//   · lo que NO existe en la app (fuente exacta, rezago, limitaciones,
//     faltantes, revisiones, changelog) → este archivo.
//
// Decisión editorial (06-jul-2026): las fichas públicas NO muestran números
// de ADR ni jerga interna — el registro de decisiones es interno; el
// changelog público lleva fecha y descripción en llano (coherente con el
// gate G6 del pipeline).

export interface CambioMetodologico {
  fecha: string;   // "2026-07-03" o "2026-06" si la precisión es mensual
  cambio: string;
}

export interface FuenteFicha {
  organismo: string;    // quién produce el dato original
  operacion: string;    // la operación estadística / serie exacta
  serie?: string;       // identificador técnico de la serie (API)
  url?: string;         // página oficial de la fuente
  acceso: string;       // cómo lo obtiene el informe (automático/manual)
}

// Banda institucional tal como la publica el documento CIGOB, más los puntos
// ancla que usa el motor de interpolación para el ejemplo resuelto.
export interface AnclasFicha {
  bandas: { banda: string; puntaje: number }[];   // la tabla del documento
  puntos: [number, number][];                     // anclas [valor, puntaje], x ascendente
  unidadCorta: string;                            // "% m/m"
  sinEjemplo?: boolean;                           // el valor de la card NO es el insumo de la
                                                  // escala (ej. REM: puntúa el equivalente
                                                  // mensual, la card muestra el anual)
}

export interface FichaIndicador {
  tipo: "indicador";
  id: string;                       // clave técnica en informe.json / series.json
  cinturon: "macro" | "politica" | "vida_cotidiana" | "gestion";
  rezago: string;                   // cuánto tarda la fuente en publicar
  fuente: FuenteFicha;
  transformaciones: string[];       // complemento en llano de la fórmula (ODS 4.c)
  anclas?: AnclasFicha;             // umbrales institucionales → puntaje (paramétricas por bandas)
  incidenciaTexto?: string[];       // cómo entra al índice/score cuando NO hay tabla de anclas
                                    // (componentes B100 de vida, fórmulas 0-10 de política/espíritu)
  dobleUso?: string;                // dónde más participa el dato dentro del sistema
  limitaciones: string[];           // ODS 4.b — declaradas, no escondidas
  faltantes: string;                // ODS 4.g
  revisiones: string;               // política de revisión (fuente y serie propia)
  cambios: CambioMetodologico[];
}

export interface FichaIndice {
  tipo: "indice";
  id: string;                       // "itcm" (clave del bloque en informe.json)
  sigla: string;
  nombreLargo: string;
  base100?: boolean;                // índice de seguimiento base 100 (ITCIS): sin techo,
                                    // tensión = 5 − (valor − 100) × 0,2
  cinturon: "macro" | "gestion" | "vida_cotidiana" | "politica";
  resumen: string;                  // qué es, para el encabezado
  // Secciones = pasos del checklist OCDE/JRC (2008). Los pasos 4 (análisis
  // multivariado) y 8 (vuelta a los datos) no tienen sección propia: su estado
  // se declara en "limitaciones".
  marcoConceptual: string[];        // paso 1
  seleccion: string[];              // paso 2 (la tabla de composición es runtime)
  tratamiento: string[];            // paso 3 (faltantes, overrides, provisorios)
  normalizacion: string[];          // paso 5 (anclas interpoladas)
  agregacion: { latex: string; leyenda: string; parrafos: string[] };  // paso 6
  robustez: string[];               // paso 7 (los números salen de informe.json)
  validacion: string[];             // paso 9
  comunicacion: string[];           // paso 10
  interpretacion: { rango: string; lectura: string }[];
  limitaciones: string[];
  cambios: CambioMetodologico[];
}

export type Ficha = FichaIndicador | FichaIndice;

// Ubica el valor entre las anclas para el ejemplo resuelto de la ficha.
// Devuelve el tramo [x0,y0]→[x1,y1] que lo contiene, o "plano" en los extremos.
export function tramoDeAnclas(puntos: [number, number][], v: number):
  | { plano: true; puntaje: number; borde: number }
  | { plano: false; x0: number; y0: number; x1: number; y1: number; puntaje: number } {
  if (v <= puntos[0][0]) return { plano: true, puntaje: puntos[0][1], borde: puntos[0][0] };
  const last = puntos[puntos.length - 1];
  if (v >= last[0]) return { plano: true, puntaje: last[1], borde: last[0] };
  for (let i = 0; i < puntos.length - 1; i++) {
    const [x0, y0] = puntos[i], [x1, y1] = puntos[i + 1];
    if (v >= x0 && v <= x1) {
      const p = y0 + ((v - x0) / (x1 - x0)) * (y1 - y0);
      return { plano: false, x0, y0, x1, y1, puntaje: Math.round(p * 10) / 10 };
    }
  }
  return { plano: true, puntaje: last[1], borde: last[0] };
}

export const FICHAS: Record<string, Ficha> = {

  // ═══════════════════════════════════════════════════════════════════════
  // Inflación mensual (IPC) — la ficha piloto del estándar
  // ═══════════════════════════════════════════════════════════════════════
  ipc_total: {
    tipo: "indicador",
    id: "ipc_total",
    cinturon: "macro",
    rezago: "El INDEC difunde el IPC de cada mes a mediados del mes siguiente, según su calendario oficial. El informe lo incorpora en forma automática el mismo día de la publicación.",
    fuente: {
      organismo: "INDEC",
      operacion: "Índice de Precios al Consumidor (IPC) — cobertura nacional, nivel general, variación mensual",
      serie: "148.3_INIVELNAL_DICI_M_26 · API de Series de Tiempo de la República Argentina (datos.gob.ar)",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31",
      acceso: "Automático: el dato se extrae de la API pública y se publica sin intervención manual.",
    },
    transformaciones: [
      "Variación porcentual del índice de nivel general contra el mes anterior, tal como la publica el INDEC.",
      "No se aplican ajustes propios: ni desestacionalización, ni promedios, ni recortes.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 1", puntaje: 100 },
        { banda: "1 – 2", puntaje: 85 },
        { banda: "2 – 3", puntaje: 65 },
        { banda: "3 – 5", puntaje: 40 },
        { banda: "> 5", puntaje: 10 },
      ],
      puntos: [[1, 100], [1.5, 85], [2.5, 65], [4, 40], [5, 10]],
      unidadCorta: "% m/m",
    },
    dobleUso: "El IPC participa además como deflactor de otros componentes del sistema: la recaudación real, el crédito privado real, el IDM y la tasa real del IdC. Un error de medición de la fuente se propagaría a esos indicadores.",
    limitaciones: [
      "Mide el promedio nacional del nivel general: no distingue núcleo, regulados y estacionales, ni las diferencias regionales que el propio INDEC publica por separado.",
      "Llega con rezago: al momento de cada informe, el último dato disponible puede tener entre dos y seis semanas de antigüedad. Las expectativas del REM, dentro de la misma dimensión, cubren parcialmente ese hueco.",
      "La variación de un solo mes es sensible a factores puntuales (correcciones tarifarias, estacionalidad de rubros) que no permiten distinguir el dato suelto de la tendencia.",
      "El IPC es además el deflactor de otros tres indicadores del cinturón (recaudación, crédito y tasa real del clima financiero): su peso real en el índice es mayor que su peso nominal, porque un error de medición se propagaría también a ellos. Se documenta como riesgo sistémico en la metodología general del índice.",
    ],
    faltantes: "Si al calcular el índice el dato del mes no está publicado, el indicador queda fuera de esa actualización y los pesos de su dimensión se renormalizan entre los presentes: la ausencia no puntúa ni a favor ni en contra.",
    revisiones: "El INDEC no revisa retroactivamente el IPC publicado: la serie de la fuente es definitiva. Del lado del informe, la serie se reconstruyó hacia atrás hasta julio de 2021 y todo cambio de método propio queda asentado en el historial de cambios (abajo).",
    cambios: [
      {
        fecha: "2026-06",
        cambio: "El indicador deja de promediarse directamente como tensión 0–10 y pasa a puntuar dentro del ITCM según los umbrales institucionales de la paramétrica CIGOB (documento de mayo de 2026).",
      },
      {
        fecha: "2026-07-03",
        cambio: "El puntaje escalonado por banda se reemplaza por interpolación lineal entre anclas: se eliminan los saltos de 15–25 puntos entre valores casi iguales a ambos lados de un umbral. Los umbrales institucionales no cambian.",
      },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // ITCM — ficha del índice compuesto, según el checklist OCDE/JRC (2008)
  // ═══════════════════════════════════════════════════════════════════════
  itcm: {
    tipo: "indice",
    id: "itcm",
    sigla: "ITCM",
    nombreLargo: "Índice de Tensión del Cinturón Macroeconómico",
    cinturon: "macro",
    resumen: "Mide la tensión del cinturón macroeconómico en una escala 0–100: 0 = cinturón severamente apretado (máxima tensión), 100 = aflojado. Trece indicadores en seis dimensiones, con umbrales y pesos de la paramétrica institucional CIGOB.",
    marcoConceptual: [
      "El informe lee la realidad como un sistema de cuatro cinturones que rodean al gobierno (Planificación Estratégica Situacional de Carlos Matus). El cinturón macroeconómico agrupa los indicadores del motor económico: precios, cuentas fiscales y externas, financiamiento, actividad, competitividad e inversión.",
      "El marco, las dimensiones, los umbrales y los pesos provienen de un documento institucional: «Fórmula Paramétrica para la Evaluación del Estado de Tensión — Cinturón de la Macroeconomía» (Fundación CIGOB, mayo de 2026). El índice no estima esos parámetros a partir de los datos: los toma del marco y luego mide — con las herramientas de robustez de abajo — cuánto dependen las conclusiones de esa elección.",
    ],
    seleccion: [
      "Trece indicadores agrupados en seis dimensiones (la tabla de composición de abajo muestra la estructura vigente con los puntajes de hoy). Criterio de selección: fuentes públicas oficiales (INDEC, BCRA, ARCA), extracción automatizable y serie histórica reconstruible al inicio del mandato (diciembre de 2023).",
      "Las variables nominales de seguimiento (préstamos y base monetaria nominales, tipo de cambio mayorista, BADLAR) se extraen como insumo de cálculo pero no se publican como indicadores del cinturón: en un régimen de desinflación, su variación nominal confunde más de lo que informa. La BADLAR entra al índice a través de la tasa real del IdC; el crédito entra deflactado.",
    ],
    tratamiento: [
      "Indicadores faltantes: los pesos se renormalizan entre los presentes, primero dentro de la dimensión y, si una dimensión queda vacía, entre dimensiones. Las ausencias no puntúan ni a favor ni en contra.",
      "Juicio experto: la paramétrica admite ajustes manuales por indicador, siempre con justificación escrita y fecha de vencimiento (un ajuste vencido se ignora solo). Existe además una regla automática para el saldo comercial: si el superávit se explica por contracción de importaciones y no por crecimiento exportador, el puntaje se rebaja con la justificación generada a partir de los números. Todo ajuste activo se publica junto al índice.",
      "Deflactores: los indicadores reales esperan el IPC cerrado. La recaudación real, por ejemplo, se computa como promedio móvil de tres meses sobre meses con IPC publicado, para filtrar el calendario tributario.",
    ],
    normalizacion: [
      "Cada indicador, en su unidad original, se convierte a un puntaje 0–100 mediante los umbrales institucionales del documento CIGOB, leídos como anclas de interpolación: cada banda finita ancla su puntaje en su punto medio, las bandas abiertas en su borde finito; entre anclas el puntaje es lineal y fuera de la primera y la última queda plano.",
      "Hasta julio de 2026 el puntaje era escalonado (toda la banda valía lo mismo). El análisis de sensibilidad midió que esos escalones aportaban el doble de incertidumbre que los pesos y creaban saltos de 15–25 puntos entre valores casi iguales; la interpolación los elimina sin tocar los umbrales institucionales.",
    ],
    agregacion: {
      latex: String.raw`\text{ITCM}=\sum_{\text{6 dimensiones}}\text{peso}_{\text{dim}}\times\Big(\sum_{\text{indicadores}}\text{peso}_{\text{interno}}\times\text{puntaje}_{0\text{–}100}\Big)`,
      leyenda: "Promedio ponderado en dos niveles: primero dentro de cada dimensión (pesos internos), después entre dimensiones (pesos institucionales: 26 / 24 / 16 / 11 / 11 / 12 %).",
      parrafos: [
        "No hay pesos implícitos: la composición completa — dimensiones, pesos, puntajes del mes — se publica en la tabla de abajo y en la página del cinturón.",
        "La agregación es compensatoria: una dimensión buena puede tapar una mala. Por eso el índice incluye el flag de dimensión crítica: si una dimensión cae por debajo de su umbral crítico, se declara junto al valor publicado. La compensación se señaliza, no se corrige.",
      ],
    },
    robustez: [
      "Análisis de sensibilidad Monte Carlo: el índice se recalcula en 1.000 escenarios perturbando los pesos ±20% y los insumos ±5% del rango entre anclas, re-puntuados por la escala interpolada. La banda donde cae el 90% de los escenarios (p05–p95) se publica junto al valor en cada edición.",
      "Se acompaña con un ejercicio leave-one-out: cuánto se movería el índice si se quitara cada componente, para identificar cuál domina la lectura del mes.",
    ],
    validacion: [
      "El índice se reconstruye mes a mes desde diciembre de 2023 y se contrasta contra un ancla externa que nadie del proyecto controla: el Índice Líder de la Universidad Torcuato Di Tella, que resume la marcha de la actividad económica. Se espera correlación positiva — a menor tensión macroeconómica, más actividad.",
      "El ancla se eligió por un criterio explícito: que el co-movimiento aguante en los cambios mes a mes, y no sólo en el nivel. Es la prueba que no se puede satisfacer con la tendencia común del período, que en estos años arrastró a casi todas las series argentinas en la misma dirección. Ambas correlaciones (niveles y cambios mes a mes) se publican en la página del cinturón.",
      "Una salvedad que se publica junto al número: el orden temporal va al revés de lo que sugiere el nombre del índice externo — el ajuste mejora cuando se adelanta el ITCM y empeora cuando se adelanta el líder, así que sirve para validar el mismo mes y no como alerta temprana. El indicador integraba el cinturón de impacto social y se movió acá porque mide el ciclo de la actividad y no una condición de los hogares.",
      "La matriz de validación cruzada verifica además el poder discriminante: que cada índice del informe correlacione más con su ancla propia que con las ajenas (que el ITCM mida lo macroeconómico y no «el humor general»). La matriz completa, con sus límites declarados, se publica en la página del cinturón.",
    ],
    comunicacion: [
      "El resto del informe consume el índice como tensión 0–10: tensión = (100 − ITCM) / 10. Así, los umbrales globales de lectura no cambian: 0–3 estable, 4–6 en tensión, 7–10 tensionado.",
      "Cada indicador del cinturón publica su propia ficha, su fórmula y su tensión equivalente — cómo se leería el cinturón si solo existiera ese indicador —, junto con los ajustes de analista activos, si los hay.",
    ],
    interpretacion: [
      { rango: "0 – 20", lectura: "Severamente apretado" },
      { rango: "21 – 40", lectura: "Apretado" },
      { rango: "41 – 60", lectura: "Moderadamente apretado" },
      { rango: "61 – 80", lectura: "Moderadamente aflojado" },
      { rango: "81 – 100", lectura: "Aflojado" },
    ],
    limitaciones: [
      "Los umbrales y pesos son institucionales, no estimados: representan el juicio del marco CIGOB. El Monte Carlo mide cuánto dependen las conclusiones de esa elección, pero no la sustituye.",
      "El estándar OCDE/JRC prevé un análisis multivariado previo (paso 4: contrastar la estructura teórica con la correlación real entre los indicadores). Ese contraste está pendiente; la validación cruzada lo aproxima por el lado de las anclas externas.",
      "La ventana de validación es corta — los meses del mandato en curso —, por lo que las correlaciones se leen como consistencia, no como prueba.",
      "Riesgo sistémico del deflactor: el IPC no sólo es un indicador del índice, también convierte a términos reales a la recaudación, el crédito y la tasa real del clima financiero. Cerca del 24% del índice depende de que la inflación esté bien medida, de modo que un error del INDEC no movería una fuente sino tres a la vez. (El desequilibrio monetario también usa el IPC, pero compara dos series ya deflactadas y el deflactor se cancela, así que es inmune a ese error y no se cuenta acá.) No es corregible —no hay un deflactor mensual alternativo— pero implica que el índice tiene menos fuentes verdaderamente independientes de las que aparenta. El análisis de robustez lo tiene en cuenta: sortea un único error de inflación por escenario y lo propaga a los indicadores que lo heredan, en vez de tratar cada falla como si fuera de una fuente distinta.",
    ],
    cambios: [
      {
        fecha: "2026-06",
        cambio: "Entra en producción la paramétrica institucional (documento CIGOB de mayo de 2026): el cinturón deja el promedio simple de tensiones y pasa al ITCM de cuatro dimensiones ponderadas con umbrales por tabla.",
      },
      {
        fecha: "2026-06-28",
        cambio: "Se incorporan el IDM (desequilibrio monetario) a la dimensión de estabilidad y el TCRM como quinta dimensión (competitividad externa).",
      },
      {
        fecha: "2026-06-30",
        cambio: "Capítulo inversión: IAI (física) e ICIP (digital) como sexta dimensión. La estructura de pesos queda 26 / 24 / 16 / 11 / 11 / 12 %.",
      },
      {
        fecha: "2026-07-03",
        cambio: "Revisión metodológica: puntaje interpolado entre anclas, flag de dimensión crítica, crédito privado real al índice y variables nominales fuera de la publicación. El valor publicado pasó de 51,7 a 54,7 por el cambio de método, sin cambiar de banda de lectura.",
      },
      {
        fecha: "2026-07-04",
        cambio: "IdC rediseñado por comparación estandarizada contra su propia historia, recaudación como promedio móvil trimestral real y matriz de validación cruzada como tercer pilar de robustez.",
      },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // Macro — resto de los indicadores del ITCM
  // ═══════════════════════════════════════════════════════════════════════
  reservas_bcra: {
    tipo: "indicador",
    id: "reservas_bcra",
    cinturon: "macro",
    rezago: "La planilla de reservas y liquidez del BCRA se publica unas tres semanas después del cierre de cada mes; el informe la incorpora automáticamente.",
    fuente: {
      organismo: "BCRA",
      operacion: "Planilla SDDS «Reservas internacionales y liquidez en moneda extranjera» + Balance Consolidado del BCRA (depósitos del Tesoro en dólares)",
      serie: "Planilla mensual temp{MM}{AA}.pdf + balbcrhis.xls (Balance Consolidado)",
      url: "https://www.bcra.gob.ar/reservas-internacionales-y-base-monetaria/",
      acceso: "Automático: se leen la planilla oficial del mes y el Balance Consolidado; el resultado se valida contra las reservas brutas de la API de estadísticas.",
    },
    transformaciones: [
      "Reservas netas «a secas», el número que sigue el mercado: activos de reserva menos los fondos comprometidos (préstamos y depósitos en divisa, operaciones a término y pases).",
      "Se suman de vuelta los depósitos del Tesoro en dólares y los vencimientos de deuda en divisa a 12 meses, que figuran como pasivos pero no son pasivos del Banco Central para defender el tipo de cambio.",
      "Los tres términos salen de fuentes oficiales: no hay constantes cargadas a mano.",
    ],
    anclas: {
      bandas: [
        { banda: "> 20.000", puntaje: 100 },
        { banda: "15.000 – 20.000", puntaje: 85 },
        { banda: "10.000 – 15.000", puntaje: 70 },
        { banda: "5.000 – 10.000", puntaje: 50 },
        { banda: "0 – 5.000", puntaje: 30 },
        { banda: "≤ 0", puntaje: 10 },
      ],
      puntos: [[0, 10], [2500, 30], [7500, 50], [12500, 70], [17500, 85], [20000, 100]],
      unidadCorta: "M USD netos",
    },
    limitaciones: [
      "«Reservas netas» no es un número único: es un espectro según qué pasivos se descuentan. Otras mediciones más exigentes (o la del FMI) pueden diferir en miles de millones por criterio, no por error.",
      "El dato es a cierre de mes; el número diario que circula en el mercado puede diferir en algunos cientos de millones por la fecha de corte.",
      "El BCRA retira las planillas viejas de su sitio: la serie histórica propia solo llega hasta mediados de 2024 hacia atrás.",
    ],
    faltantes: "Si la planilla no está disponible, el cálculo cae a las reservas brutas de la API menos los últimos drenajes conocidos; si todo falla, se mantiene el último valor disponible, señalado como desactualizado y los pesos del índice se renormalizan.",
    revisiones: "La planilla publicada no se revisa; el informe reconstruye la serie completa releyendo todas las planillas disponibles en cada actualización.",
    cambios: [
      { fecha: "2026-06-26", cambio: "El indicador deja las reservas brutas del documento original y pasa a las netas «a secas», con los tres términos calculados de fuentes oficiales y escala propia." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas en lugar de escalones por banda." },
    ],
  },

  idc: {
    tipo: "indicador",
    id: "idc",
    cinturon: "macro",
    rezago: "El IdC se publica para el último mes con IPC cerrado: unas dos semanas después de mediados del mes siguiente.",
    fuente: {
      organismo: "BCRA (tasa BADLAR, depósitos y préstamos privados) + INDEC (IPC como deflactor)",
      operacion: "Estadísticas monetarias del BCRA: BADLAR bancos privados, depósitos del sector privado y préstamos al sector privado; índice compuesto de elaboración propia",
      serie: "API de Estadísticas Monetarias del BCRA (variables 7, 100 y 117) + IPC 148.3_INIVELNAL_DICI_M_26 (datos.gob.ar)",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp",
      acceso: "Automático: API pública del BCRA y API de series de datos.gob.ar; el índice se calcula en el propio informe.",
    },
    transformaciones: [
      "Tres niveles mensuales: la tasa real que reciben los depositantes (precio), el crecimiento interanual real de los depósitos privados (volumen) y la holgura entre depósitos y préstamos (asignación).",
      "Cada nivel se compara contra toda su propia historia (2018 en adelante) y se expresa en desvíos estándar: 0 es el mes histórico típico.",
      "Combinación 30% precio + 40% volumen + 30% asignación; semáforo: por encima de +0,5 desvíos, capacidad mayor a la habitual; por debajo de −0,5, menor.",
    ],
    anclas: {
      bandas: [
        { banda: "> +1 σ", puntaje: 100 },
        { banda: "+0,5 – +1 σ", puntaje: 85 },
        { banda: "−0,5 – +0,5 σ", puntaje: 60 },
        { banda: "−1 – −0,5 σ", puntaje: 35 },
        { banda: "≤ −1 σ", puntaje: 10 },
      ],
      puntos: [[-1, 10], [-0.75, 35], [0, 60], [0.75, 85], [1, 100]],
      unidadCorta: "σ",
    },
    dobleUso: "Comparte insumos con otros indicadores del sistema: los depósitos privados también entran al IDM, y la tasa BADLAR se sigue extrayendo como insumo aunque no se publique como indicador propio.",
    limitaciones: [
      "Queda una correlación residual entre los componentes de volumen y asignación (ambos usan los depósitos), remanente declarado del rediseño.",
      "Sin pretensión predictiva, y con la validación en contra documentada: sobre más de cien meses, el IdC no anticipa el crédito futuro. Es un descriptor del estado de las condiciones de fondeo, no un pronóstico.",
      "Los desvíos se recalculan contra la historia completa en cada actualización: los puntos históricos pueden moverse levemente entre ediciones.",
    ],
    faltantes: "Si la historia disponible baja de 60 meses o falla algún insumo, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión de financiamiento se renormalizan.",
    revisiones: "Al redefinirse la métrica, el histórico de la versión anterior se purgó: la serie publicada es homogénea. Se regenera completa en cada actualización.",
    cambios: [
      { fecha: "2026-06-26", cambio: "Nace el IdC en reemplazo de la tasa BADLAR dentro de la dimensión de financiamiento, como índice de ratios mensuales." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "Rediseño de la métrica: pasa de ratios mes a mes a niveles estandarizados contra la propia historia, publicados en desvíos estándar." },
    ],
  },

  emae_ia: {
    tipo: "indicador",
    id: "emae_ia",
    cinturon: "macro",
    rezago: "El INDEC publica el EMAE de cada mes hacia fines del segundo mes siguiente: es el indicador simple más rezagado del índice (~2 meses).",
    fuente: {
      organismo: "INDEC",
      operacion: "EMAE — Estimador Mensual de Actividad Económica, variación interanual de la serie original (base 2004)",
      serie: "143.3_ICE_SERVIA_2004_A_25 · API de Series de Tiempo (datos.gob.ar)",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-48",
      acceso: "Automático: API pública de series de tiempo de datos.gob.ar.",
    },
    transformaciones: [
      "La variación interanual viene calculada por la fuente; la única transformación es de formato (fracción a porcentaje).",
    ],
    anclas: {
      bandas: [
        { banda: "> 5", puntaje: 100 },
        { banda: "3 – 5", puntaje: 80 },
        { banda: "0 – 3", puntaje: 60 },
        { banda: "−2 – 0", puntaje: 40 },
        { banda: "−5 – −2", puntaje: 20 },
        { banda: "≤ −5", puntaje: 5 },
      ],
      puntos: [[-5, 5], [-3.5, 20], [-1, 40], [1.5, 60], [4, 80], [5, 100]],
      unidadCorta: "% i.a.",
    },
    dobleUso: "La misma serie se extrae también como insumo de contexto en el cinturón de impacto social.",
    limitaciones: [
      "El EMAE es provisorio y el INDEC lo revisa hacia atrás con cada publicación; la serie del informe absorbe esas revisiones al regenerarse.",
      "Comparte dimensión con el IPI manufacturero, que aporta la segunda lectura de actividad; hasta julio de 2026 era la única variable, y el 11% del índice colgaba de un solo dato.",
    ],
    faltantes: "Si el dato falta, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, la dimensión de actividad queda vacía y su peso se redistribuye entre las demás.",
    revisiones: "La fuente revisa (serie provisoria); el informe regenera la serie completa en cada actualización y puntúa siempre el último dato publicado, sin proyecciones propias.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original como única variable de actividad; su peso de dimensión bajó de 15% a 13% y luego a 11% al incorporarse las dimensiones de competitividad e inversión." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-18", cambio: "Deja de ser la única variable de la dimensión: pasa a pesar 65% junto al IPI manufacturero (35%)." },
      { fecha: "2026-07-25", cambio: "Su peso dentro de la dimensión baja de 80% a 60% al incorporarse la amplitud del crecimiento, que lee la misma fuente en su apertura por sectores." },
    ],
  },

  empleo_registrado: {
    tipo: "indicador",
    id: "empleo_registrado",
    cinturon: "vida_cotidiana",
    rezago: "Los datos del Sistema Integrado Previsional se publican con alrededor de tres meses de rezago: son declaraciones de las empresas que se consolidan y se revisan.",
    fuente: {
      organismo: "Ministerio de Capital Humano — Sistema Integrado Previsional Argentino (SIPA)",
      operacion: "Trabajadores registrados según modalidad ocupacional principal — asalariados del sector privado, en miles de personas",
      serie: "151.1_AARIADODAD_2012_M_31 · API de Series de Tiempo (datos.gob.ar)",
      url: "https://www.argentina.gob.ar/trabajo/estadisticas",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "La card publica el nivel en miles de puestos; el índice del cinturón lo expresa en base 100 contra el promedio del último trimestre de 2023, la misma línea de base que el resto de los componentes.",
      "Se usa la serie con estacionalidad, no la desestacionalizada, porque la comparación es contra una base fija de tres meses y no contra el mes anterior: la estacionalidad de la base y la del mes corriente se compensan.",
      "No se invierte: más empleo registrado es mejor, de modo que el índice sube cuando la situación mejora.",
    ],
    limitaciones: [
      "Cuenta puestos registrados, no personas ocupadas. Un trabajador con dos empleos registrados cuenta dos veces, y todo el empleo no registrado —alrededor de un tercio del total en la Argentina— queda afuera por definición.",
      "Sólo mira al sector privado. El empleo público se publica por separado y no entra: la dimensión describe las condiciones del mercado de trabajo que enfrenta un hogar, y el tamaño del Estado ya se mide en el cinturón de gestión. Sumarlo acá haría que una reducción de la planta estatal empeorara este cinturón al mismo tiempo que mejora el otro, con el mismo dato.",
      "Las declaraciones se revisan hacia atrás durante varios meses, de modo que los últimos puntos de la serie pueden moverse.",
      "Un puesto registrado no dice nada sobre el salario que paga: el indicador no captura si el empleo que queda está mejor o peor remunerado que el que se perdió.",
    ],
    faltantes: "Si falta el dato, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el peso se redistribuye entre los otros tres componentes de la dimensión.",
    revisiones: "La fuente revisa sus series al consolidar declaraciones; el informe regenera la serie completa en cada actualización.",
    cambios: [
      { fecha: "2026-07-25", cambio: "Entra al índice como componente principal de la dimensión de empleo, con el treinta y cinco por ciento. Hasta entonces la dimensión se llamaba así pero ninguno de sus cuatro componentes medía empleo: eran indicadores de producción, de construcción, de pluriempleo y un índice líder." },
    ],
  },

  cobertura_judicial: {
    tipo: "indicador",
    id: "cobertura_judicial",
    cinturon: "politica",
    rezago: "El padrón de magistrados se publica con actualizaciones irregulares, en general de uno a dos meses. Los registros de designaciones y renuncias se actualizan con más frecuencia, de modo que la serie incorpora los movimientos posteriores a la última foto del padrón.",
    fuente: {
      organismo: "Ministerio de Justicia",
      operacion: "Padrón de magistrados de la Justicia Federal y Nacional (con marca de cargo vacante), más los registros de designaciones y de renuncias de magistrados",
      serie: "Tres datasets en CSV del portal datos.jus.gob.ar",
      url: "https://datos.jus.gob.ar/dataset/magistrados-justicia-federal-y-de-la-justicia-nacional",
      acceso: "Automático: los tres archivos se resuelven por la interfaz del portal de datos abiertos. El nombre de cada archivo incluye su fecha de publicación y cambia en cada actualización, de modo que se busca el recurso vigente en lugar de construir la dirección a mano.",
    },
    transformaciones: [
      "Se consideran únicamente los cargos de juez en órganos habilitados: los tribunales creados por ley pero todavía no puestos en funcionamiento no forman parte del denominador, porque no hay nada que cubrir.",
      "Un cargo marcado como vacante cuenta como no cubierto aunque tenga subrogante a cargo. La subrogancia se publica aparte, en el detalle de la card.",
      "Hay una excepción, y la fuente la distingue bien: un puñado de cargos tiene juez designado que está de licencia, con un subrogante a cargo mientras tanto. Ese cargo no figura como vacante, porque el juez existe y el cargo es suyo, aunque quien firme sea el subrogante. Al cinco de junio de 2026 son seis casos.",
      "La serie mensual se reconstruye desde el padrón: hacia atrás, cada designación posterior indica un cargo que antes estaba vacante y cada renuncia posterior uno que antes estaba cubierto; hacia adelante, la operación se invierte. Los registros de designaciones y renuncias incluyen fiscales y defensores, que se descartan porque el padrón que fija el nivel es sólo de jueces.",
    ],
    anclas: {
      bandas: [
        { banda: "> 90", puntaje: 100 },
        { banda: "80 – 90", puntaje: 85 },
        { banda: "70 – 80", puntaje: 65 },
        { banda: "60 – 70", puntaje: 40 },
        { banda: "≤ 60", puntaje: 10 },
      ],
      puntos: [[60, 10], [65, 40], [75, 65], [85, 85], [90, 100]],
      unidadCorta: "% cubierto",
    },
    limitaciones: [
      "Mide la capacidad de integrar el Poder Judicial, no su comportamiento. No dice nada sobre cómo falla la Justicia, con qué velocidad resuelve ni en qué sentido lo hace.",
      "El total de cargos se mantiene constante a lo largo de la serie reconstruida. La creación o habilitación de tribunales nuevos en el período movería el denominador y no está incorporada, de modo que la reconstrucción es más confiable cerca de la fecha del padrón que en su extremo inicial.",
      "Las subrogancias se descuentan por completo, lo que es una decisión metodológica discutible: un juzgado con subrogante funciona, aunque de forma precaria. La composición se publica para que el lector pueda hacer la lectura contraria.",
      "En el período reconstruido la cobertura se movió entre el sesenta y cuatro y el setenta y tres por ciento, de modo que sólo dos de las cinco bandas están pobladas. Las bandas superiores describen situaciones que la justicia argentina no alcanzó en estos años; no se bajaron los umbrales para poblarlas, porque eso convertiría un desempeño bajo en un puntaje alto.",
      "Los traslados de jueces entre tribunales no se procesan como eventos propios: un traslado deja una vacante y cubre otra, y en el agregado se compensan, pero puede introducir diferencias de un cargo en meses puntuales.",
    ],
    faltantes: "Si los archivos no se pueden leer, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, la dimensión del Poder Judicial queda vacía y su peso se redistribuye entre las demás.",
    revisiones: "Cada actualización del padrón vuelve a anclar la serie completa, de modo que los valores pasados pueden ajustarse levemente cuando el Ministerio publica una foto nueva. El salto de junio de 2026 fue contrastado contra una fuente independiente: el archivo de concursos del propio Consejo de la Magistratura, que no registra ninguna entrevista entre octubre de 2024 y mayo de 2026 y concentra siete concursos con entrevistas personales entre junio y julio de 2026. Las dos fuentes marcan el mismo quiebre en el mismo mes, sin compartir método: además de aprobarse pliegos en el Senado, la maquinaria de selección volvió a moverse.",
    cambios: [
      { fecha: "2026-07-25", cambio: "Entra al índice como único indicador de la dimensión nueva del Poder Judicial, con el quince por ciento del cinturón. La serie se reconstruyó completa desde diciembre de 2023." },
    ],
  },

  produccion_legislativa: {
    tipo: "indicador",
    id: "produccion_legislativa",
    cinturon: "politica",
    rezago: "El dataset se actualiza con la sanción de cada ley, de modo que el rezago es el de la carga en el portal de datos abiertos: en general unas semanas.",
    fuente: {
      organismo: "Cámara de Diputados de la Nación",
      operacion: "Dataset de leyes sancionadas, con el expediente inicial y la fecha de sanción definitiva de cada una",
      serie: "Recurso del portal de datos abiertos, consultado por su interfaz de datos",
      url: "https://datos.hcdn.gob.ar/dataset/leyes-sancionadas",
      acceso: "Automático: el mismo portal que el proyecto ya consulta para la eficacia parlamentaria.",
    },
    transformaciones: [
      "Se cuentan las leyes con sanción definitiva dentro de la ventana de doce meses que termina en el mes informado. La ventana es móvil y no calendaria, para que cada mes sea comparable con el anterior sin el salto de enero.",
      "No se distingue de dónde nació cada proyecto. La composición por origen se publica aparte, en el detalle de la card, porque es una lectura y no el puntaje.",
    ],
    anclas: {
      bandas: [
        { banda: "> 74", puntaje: 100 },
        { banda: "50 – 74", puntaje: 85 },
        { banda: "35 – 50", puntaje: 65 },
        { banda: "20 – 35", puntaje: 40 },
        { banda: "≤ 20", puntaje: 10 },
      ],
      puntos: [[20, 10], [30, 40], [42, 65], [60, 85], [74, 100]],
      unidadCorta: "leyes (12m)",
    },
    limitaciones: [
      "Cuenta leyes, no su importancia. Una ley de presupuesto y una que declara una fecha conmemorativa pesan igual.",
      "El promedio histórico con el que se compara incluye años de mayorías muy distintas. No es un óptimo normativo: es la referencia disponible más ancha, de dieciocho años y cuatro presidencias.",
      "La ventana móvil de doce meses suaviza pero también demora: un cambio de ritmo tarda meses en verse completo.",
    ],
    faltantes: "Si el portal no responde, se mantiene el último valor disponible, señalado como desactualizado.",
    revisiones: "El dataset puede incorporar leyes con retraso, de modo que los últimos meses de la serie pueden ajustarse levemente hacia arriba.",
    cambios: [
      { fecha: "2026-07-31", cambio: "Entra al índice. Se decidió medir el total de leyes sancionadas y no la proporción de origen del Ejecutivo, porque esa proporción se mueve por el denominador: el numerador es estable entre cinco y diez leyes en todo el período." },
    ],
  },

  judicializacion: {
    tipo: "indicador",
    id: "judicializacion",
    cinturon: "politica",
    rezago: "La base indexa los fallos con demora variable y el punto es anual, de modo que el dato describe un año que ya cerró.",
    fuente: {
      organismo: "Sistema Argentino de Información Jurídica (SAIJ)",
      operacion: "Buscador de jurisprudencia, restringido por jurisdicción",
      serie: "Conteo de sumarios por año, con y sin el término de búsqueda",
      url: "https://www.saij.gob.ar/busqueda",
      acceso: "Automático: la consulta y el modo de leer los totales quedaron verificados y documentados.",
    },
    transformaciones: [
      "El numerador y el denominador se restringen ambos a jurisdicción federal y nacional. Sin ese filtro, los fallos provinciales contaminan el conteo.",
      "Se publica la proporción y no el conteo. El conteo crudo depende de cuánto publica la base cada año, que varía por razones editoriales y no jurídicas.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 0,8", puntaje: 100 },
        { banda: "0,8 – 1,2", puntaje: 85 },
        { banda: "1,2 – 1,6", puntaje: 65 },
        { banda: "1,6 – 2,0", puntaje: 40 },
        { banda: "> 2,0", puntaje: 10 },
      ],
      puntos: [[0.8, 100], [1.0, 85], [1.4, 65], [1.8, 40], [2.0, 10]],
      unidadCorta: "% de sumarios",
    },
    limitaciones: [
      "La proporción corrige el volumen de publicación de la base, pero no un eventual cambio en su mezcla: si la base empezara a publicar sistemáticamente más fallos de un fuero que de otro, el indicador lo leería como un cambio en la judicialización.",
      "Mide cautelares en general, no cautelares contra el Estado nacional. Distinguir el demandado exige leer cada fallo, y el buscador no permite filtrar por eso.",
      "Es anual. No sirve para leer el pulso de un mes.",
    ],
    faltantes: "Si la base no responde, se mantiene el último valor disponible, señalado como desactualizado.",
    revisiones: "El punto del año en curso se recalcula en cada corrida, porque la base sigue indexando fallos de ese año. Al ser un cociente, el numerador y el denominador se recortan juntos y el punto sigue siendo comparable.",
    cambios: [
      { fecha: "2026-07-31", cambio: "Entra al índice como uno de los tres indicadores de comportamiento del Poder Judicial." },
    ],
  },

  velocidad_resolucion: {
    tipo: "indicador",
    id: "velocidad_resolucion",
    cinturon: "politica",
    rezago: "El anuario se publica con el año cerrado, de modo que el dato describe el año anterior.",
    fuente: {
      organismo: "Corte Suprema de Justicia de la Nación",
      operacion: "Anuario estadístico, sobre su sistema de gestión judicial",
      serie: "Expedientes ingresados y resueltos por año",
      url: "https://www.csjn.gov.ar/estadisticas",
      acceso: "Los tableros interactivos no admiten consulta automática, pero la Corte publica una versión estática de cada hoja con las etiquetas de datos visibles, y el anuario en documento.",
    },
    transformaciones: [
      "Se divide lo resuelto sobre lo ingresado en cada año. Cien por ciento es el punto donde la Corte resuelve exactamente lo que le entra.",
      "Los doce años de la serie se validaron aritméticamente: el saldo que la fuente informa por separado coincide de forma exacta con ingresos menos resueltos en todos los años, sin una sola discrepancia.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 40", puntaje: 100 },
        { banda: "40 – 70", puntaje: 85 },
        { banda: "70 – 100", puntaje: 65 },
        { banda: "100 – 130", puntaje: 40 },
        { banda: "> 130", puntaje: 10 },
      ],
      puntos: [[40, 100], [55, 85], [85, 65], [115, 40], [130, 10]],
      unidadCorta: "% resuelto",
    },
    limitaciones: [
      "El signo de este indicador es deliberado y conviene decirlo: una Corte más lenta le da más puntaje al Gobierno. El cinturón mide capacidad de gobernar sin fricción, no salud institucional, y una causa que tarda años deja en pie mientras tanto lo que se discute.",
      "Cuenta expedientes, no su peso. Una causa que define una política y una queja de trámite cuentan igual.",
      "Los años por encima de cien por ciento son años de descarga de atraso acumulado, no de mayor productividad instantánea.",
      "Es anual. No sirve para leer el pulso de un mes.",
    ],
    faltantes: "Si el anuario no está disponible, se mantiene el último valor publicado, señalado como desactualizado.",
    revisiones: "La fuente puede corregir cifras de años anteriores al publicar el anuario siguiente.",
    cambios: [
      { fecha: "2026-07-31", cambio: "Entra al índice. El veredicto anterior lo daba por imposible por falta de fecha de inicio de causa; la corrección encontró que el anuario publica ingresos y resueltos por año, que es lo que el indicador necesita." },
    ],
  },

  paralisis_denuncias: {
    tipo: "indicador",
    id: "paralisis_denuncias",
    cinturon: "politica",
    rezago: "Depende de cuándo el Consejo publica la nota de cada sesión, en general dentro de las semanas siguientes.",
    fuente: {
      organismo: "Consejo de la Magistratura de la Nación",
      operacion: "Archivo de notas de prensa de las comisiones de Acusación y de Disciplina",
      serie: "Sesiones numeradas de cada comisión desde su separación, en 2022",
      url: "https://www.consejomagistratura.gov.ar",
      acceso: "Automático sobre el archivo público de notas.",
    },
    transformaciones: [
      "Se cuentan las sesiones numeradas de ambas comisiones en la ventana móvil de doce meses. Las notas sin número —sesiones conjuntas, extraordinarias y audiencias testimoniales— se relevan aparte y no entran en el conteo.",
      "Se suman las dos comisiones. Cada una por separado sesiona pocas veces al año, y una serie construida sobre una sola quedaría dominada por el ruido de un evento aislado.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 2", puntaje: 100 },
        { banda: "2 – 4", puntaje: 85 },
        { banda: "4 – 6", puntaje: 65 },
        { banda: "6 – 9", puntaje: 40 },
        { banda: "> 9", puntaje: 10 },
      ],
      puntos: [[2, 100], [3, 85], [5, 65], [7, 40], [9, 10]],
      unidadCorta: "sesiones (12m)",
    },
    limitaciones: [
      "Cuenta que la comisión se reúna, no que resuelva. Las decisiones concretas contra un magistrado son un fenómeno distinto y mucho más raro —cuatro en veinte meses— y no entran en este conteo.",
      "Las dos comisiones se comportan distinto: una sesiona con más frecuencia y produce acciones, la otra sesiona menos y no publicó ninguna. El indicador las suma, de modo que no distingue cuál de las dos se movió.",
      "Depende de que el Consejo publique la nota de cada sesión. Una sesión sin nota es invisible para el indicador.",
    ],
    faltantes: "Si el archivo no se puede leer, se mantiene el último valor disponible, señalado como desactualizado.",
    revisiones: "Una nota publicada con retraso puede sumar una sesión a meses ya informados.",
    cambios: [
      { fecha: "2026-07-31", cambio: "Entra al índice midiendo las sesiones de ambas comisiones. Se descartó medir sólo la comisión de Disciplina: tiene ocho sesiones en cuatro años, lo que la convierte en un indicador de eventos aislados y no en una serie." },
    ],
  },

  emae_difusion: {
    tipo: "indicador",
    id: "emae_difusion",
    cinturon: "macro",
    rezago: "Se publica junto con el EMAE agregado, hacia fines del segundo mes siguiente al de referencia (~2 meses). La apertura sectorial sale el mismo día que el nivel general, de modo que este indicador no agrega rezago sobre el que ya tiene la dimensión.",
    fuente: {
      organismo: "INDEC",
      operacion: "EMAE — Estimador Mensual de Actividad Económica, apertura sectorial (índices por sector, base 2004)",
      serie: "15 series del dataset 11.3 · API de Series de Tiempo (datos.gob.ar)",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-48",
      acceso: "Automático: API pública de series de tiempo de datos.gob.ar, en una única consulta con las quince series.",
    },
    transformaciones: [
      "Para cada uno de los quince sectores se calcula la variación contra el mismo mes del año anterior, sobre el índice original.",
      "Se cuenta cuántos sectores tienen variación positiva y se expresa como porcentaje del total.",
      "Un mes sólo se publica si los quince sectores tienen dato: una difusión calculada sobre doce sectores no sería comparable con una calculada sobre quince.",
    ],
    anclas: {
      bandas: [
        { banda: "> 90 (14-15 sectores)", puntaje: 100 },
        { banda: "70 – 90 (11-13 sectores)", puntaje: 80 },
        { banda: "50 – 70 (8-10 sectores)", puntaje: 60 },
        { banda: "30 – 50 (5-7 sectores)", puntaje: 35 },
        { banda: "≤ 30 (0-4 sectores)", puntaje: 10 },
      ],
      puntos: [[30, 10], [40, 35], [60, 60], [80, 80], [90, 100]],
      unidadCorta: "% sectores",
    },
    limitaciones: [
      "Todos los sectores pesan igual: un mes en que crece la pesca cuenta lo mismo que uno en que crece la industria manufacturera, que es varias veces mayor. Ponderar por participación daría una lectura distinta y exigiría una fuente adicional de estructura sectorial.",
      "Sólo mira el signo de la variación, no su magnitud: un sector que crece 0,1% y otro que crece 15% cuentan igual. Es lo que hace al indicador robusto —no lo mueve un valor extremo— y a la vez lo que le impide distinguir un crecimiento débil de uno fuerte, que es lo que mide el EMAE agregado.",
      "Comparte fuente con el EMAE agregado, con el que correlaciona 0,84 en niveles a lo largo de 257 meses. Aporta señal propia sobre todo cuando el agregado está cerca de cero: en mayo de 2026 la actividad varió 0,2% y la difusión mostró que sólo ocho de quince sectores crecían.",
      "Los sectores del EMAE son quince categorías amplias; una de ellas, la industria manufacturera, agrupa por sí sola actividades muy distintas entre sí.",
    ],
    faltantes: "Si el dato falta, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el peso se redistribuye entre los otros dos indicadores de la dimensión.",
    revisiones: "El INDEC revisa las series sectoriales hacia atrás junto con el EMAE agregado; el informe regenera la serie completa en cada actualización, de modo que una revisión puede cambiar retroactivamente el conteo de un mes ya publicado.",
    cambios: [
      { fecha: "2026-07-25", cambio: "Entra al índice con 20% de la dimensión de actividad, tomado del peso del EMAE agregado. La serie se reconstruyó completa desde 2005." },
    ],
  },

  ipi_manufacturero: {
    tipo: "indicador",
    id: "ipi_manufacturero",
    cinturon: "macro",
    rezago: "El INDEC publica el IPI hacia mediados del mes siguiente al de referencia, aproximadamente un mes antes que el EMAE. La ganancia de frescura es real pero acotada: como el indicador promedia tres meses, su centro de masa queda un mes atrás del último dato, de modo que incorpora el mes más reciente con un tercio del peso en lugar de reflejarlo por completo.",
    fuente: {
      organismo: "INDEC",
      operacion: "IPI manufacturero — Índice de Producción Industrial, nivel general, serie original (base 2004 = 100)",
      serie: "453.1_SERIE_ORIGNAL_0_0_14_46 · API de Series de Tiempo (datos.gob.ar)",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-6-16",
      acceso: "Automático: API pública de series de tiempo de datos.gob.ar.",
    },
    transformaciones: [
      "Se calcula la variación interanual del nivel general contra el mismo mes del año anterior.",
      "Se promedian los últimos tres meses de esa variación. El suavizado no es cosmético: la variación interanual del IPI original salta hasta nueve puntos porcentuales de un mes al siguiente por feriados móviles, cantidad de días hábiles y paradas de planta. El promedio de tres meses reduce el desvío de los cambios mensuales de 6,2 a 2,5 puntos sin agregar rezago apreciable.",
    ],
    anclas: {
      bandas: [
        { banda: "> 5", puntaje: 100 },
        { banda: "3 – 5", puntaje: 80 },
        { banda: "0 – 3", puntaje: 60 },
        { banda: "−2 – 0", puntaje: 40 },
        { banda: "−5 – −2", puntaje: 20 },
        { banda: "≤ −5", puntaje: 5 },
      ],
      puntos: [[-5, 5], [-3.5, 20], [-1, 40], [1.5, 60], [4, 80], [5, 100]],
      unidadCorta: "% i.a.",
    },
    dobleUso: "Usa las mismas bandas que el EMAE, deliberadamente y con una consecuencia que conviene declarar: sobre la historia disponible, un mes mediano del índice industrial puntúa 39 y uno del estimador de actividad agregada puntúa 71. La brecha no es un defecto de calibración sino desempeño real —la industria argentina creció menos que el conjunto de la economía durante el período—, y ensanchar las bandas para cerrarla borraría esa señal. El arrastre que produce se compensa limitando su peso dentro de la dimensión, no retocando las anclas.",
    limitaciones: [
      "Mide sólo la industria manufacturera, alrededor de un sexto del producto: no es una medida de actividad agregada y no reemplaza al EMAE, lo acompaña.",
      "El EMAE ya incluye a la industria manufacturera, así que este indicador no aporta un sector nuevo sino una segunda medición del mismo: su función es que la dimensión no dependa de un único dato, no ampliar la cobertura.",
      "Ambos indicadores de la dimensión los publica el INDEC. La redundancia cubre el riesgo de que falte o se revise una serie, no el de que el organismo cambie de metodología: en ese caso se moverían los dos juntos.",
      "El promedio de tres meses amortigua los cambios de nivel: un quiebre brusco tarda dos o tres meses en verse completo.",
      "La serie es original, no desestacionalizada; la comparación interanual absorbe la estacionalidad pero no los efectos de calendario, que el suavizado atenúa sin eliminar.",
      "El INDEC revisa el índice hacia atrás con cada publicación.",
    ],
    faltantes: "Si el dato falta, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, la dimensión queda sólo con el EMAE y su peso se renormaliza.",
    revisiones: "La fuente revisa la serie; el informe la regenera completa en cada actualización y puntúa siempre el último dato publicado, sin proyecciones propias.",
    cambios: [
      { fecha: "2026-07-18", cambio: "Alta del indicador como segunda señal de actividad junto al EMAE, tras una auditoría de consistencia que señaló que el 11% del índice colgaba de un único dato." },
      { fecha: "2026-07-18", cambio: "Su peso baja de 35% a 20% de la dimensión: al ser la industria parte del propio estimador agregado, el reparto anterior dejaba a la dimensión con casi la mitad de su exposición en un solo sector." },
    ],
  },

  saldo_comercial_12m: {
    tipo: "indicador",
    id: "saldo_comercial_12m",
    cinturon: "macro",
    rezago: "Las series del intercambio comercial (ICA) se publican con un mes y medio a dos meses de rezago.",
    fuente: {
      organismo: "INDEC",
      operacion: "ICA — Intercambio Comercial Argentino: exportaciones e importaciones totales mensuales, en millones de dólares",
      serie: "74.3_IET_0_M_16 (exportaciones) y 74.3_IIT_0_M_25 (importaciones) · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-2-40",
      acceso: "Automático: API pública de series de tiempo; el saldo se calcula en el propio informe.",
    },
    transformaciones: [
      "Saldo acumulado de 12 meses: suma de exportaciones menos suma de importaciones de los últimos 12 meses comunes de ambas series.",
      "El acumulado anual elimina la estacionalidad energética y sojera.",
      "Regla automática declarada: si hay superávit pero se explica más por una caída de importaciones que por un aumento de exportaciones (contracción de la demanda interna, no éxito exportador), el puntaje se interpola hacia un piso de 60 en proporción a cuánto domina esa caída, sin un corte brusco apenas se cruza el umbral. La justificación se genera a partir de los números de cada actualización.",
    ],
    anclas: {
      bandas: [
        { banda: "> 15.000", puntaje: 85 },
        { banda: "10.000 – 15.000", puntaje: 75 },
        { banda: "5.000 – 10.000", puntaje: 60 },
        { banda: "−5.000 – 5.000", puntaje: 50 },
        { banda: "−15.000 – −5.000", puntaje: 30 },
        { banda: "≤ −15.000", puntaje: 10 },
      ],
      puntos: [[-15000, 10], [-10000, 30], [0, 50], [7500, 60], [12500, 75], [15000, 85]],
      unidadCorta: "M USD (12 meses)",
    },
    dobleUso: "Las mismas series del ICA son insumo de la alícuota de apertura comercial (cinturón gestión), y la subserie de bienes de capital importados alimenta el IAI.",
    limitaciones: [
      "Mide sólo el intercambio de BIENES. Quedan afuera los servicios, los intereses de la deuda y las utilidades giradas al exterior, que en el período reciente drenan alrededor de diecisiete mil millones de dólares por año: mientras el saldo comercial marcaba un superávit de trece mil millones, la cuenta corriente —que sí los incluye— estaba en déficit de cuatro mil millones. Un superávit comercial no equivale, por sí solo, a que el sector externo genere los dólares que el programa necesita. La cuenta corriente se publica junto a este indicador en el gráfico, como contexto.",
      "El acumulado de 12 meses suaviza a costa de reactividad: un vuelco del frente comercial tarda meses en reflejarse por completo.",
      "El máximo alcanzable de la escala es 85, no 100: diseño del documento institucional.",
      "Los datos del ICA son provisorios y se revisan; la serie regenerada por actualización los absorbe.",
    ],
    faltantes: "Con las series del ICA caídas, el cálculo cae a la serie de saldo directa (más rezagada y sin composición); agotado eso, se mantiene el último valor disponible señalado como desactualizado y los pesos se renormalizan.",
    revisiones: "La fuente revisa provisorios; el informe re-descarga la serie completa en cada actualización.",
    cambios: [
      { fecha: "2026-07-18", cambio: "Se declara la limitación de cobertura y se publica la cuenta corriente junto a este indicador: el saldo de bienes puede marcar superávit mientras el sector externo en conjunto drena dólares." },
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original, calculado por las series de exportaciones e importaciones del ICA (frescas a ~2 meses) en lugar de la serie de saldo directa (~14 meses de rezago), con la regla de superávit por contracción automatizada." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "La serie del gráfico pasó del saldo mensual al acumulado móvil de 12 meses — la métrica del titular." },
      { fecha: "2026-07-15", cambio: "La regla automática de superávit por contracción dejó de rebajar de golpe a 60 puntos: ahora interpola hacia ese mismo piso según cuánto de la mejora del saldo se explica por la caída de importaciones." },
    ],
  },

  recaudacion: {
    tipo: "indicador",
    id: "recaudacion",
    cinturon: "macro",
    rezago: "Las dos fuentes publican en los primeros días del mes siguiente, y el indicador espera el índice de precios que lleva las cifras a pesos constantes: el último punto es el del último mes con inflación publicada.",
    fuente: {
      organismo: "Secretaría de Hacienda (dato primario de ARCA) y Comisión Arbitral del Convenio Multilateral; deflactor: INDEC",
      operacion: "Recaudación mensual de la Dirección General Impositiva (impuestos internos) más la de los sistemas de la Comisión Arbitral —Ingresos Brutos de los contribuyentes de Convenio Multilateral y sus regímenes de retención—, en pesos corrientes, llevadas a pesos constantes con el índice de precios",
      serie: "172.3_SOTAL_DDGI_M_0_0_12 + IPC 148.3_INIVELNAL_DICI_M_26 (API de datos.gob.ar) + gacetilla mensual de recaudación de la Comisión Arbitral",
      url: "https://www.afip.gob.ar/institucional/estudios/",
      acceso: "Automático. La parte nacional sale de la interfaz pública de series de tiempo. La provincial se lee de la gacetilla mensual en PDF: los nombres de archivo no siguen un patrón fijo, así que se recorre el listado publicado en lugar de construir la dirección, y cada informe se procesa una sola vez y queda guardado.",
    },
    transformaciones: [
      "Se mide la recaudación de la Dirección General Impositiva —el IVA doméstico, Ganancias, créditos y débitos, internos— y no la total. Quedan afuera la recaudación aduanera y los aportes a la seguridad social. La apertura oficial es exacta: las tres partes suman el total.",
      "Se le suma, en nivel, la recaudación de los seis sistemas de la Comisión Arbitral. Sobre el total medido, la parte provincial aporta alrededor de un sexto.",
      "El resultado se lleva a pesos constantes con el índice de precios y se divide por el promedio del cuarto trimestre de 2023, que vale 100: la lectura es cuánta base imponible real queda respecto del punto de partida.",
      "Se corrige la estacionalidad, que es grande: sin corregir, la diferencia entre el mes calendario más alto y el más bajo llega a treinta puntos del índice. El factor de cada mes es el cociente entre ese mes y la tendencia de doce meses centrada, promediado por mes calendario y normalizado para no alterar el nivel. Mayo y junio concentran recaudación —vencimientos y aguinaldo— y marzo es el piso. Corregida, la estacionalidad remanente baja a tres puntos.",
      "La parte provincial de 2022 no se publica como informe mensual y se reconstruye desde la variación interanual que informa cada gacetilla de 2023. La reconstrucción se controla contra el acumulado anual, deducido por separado: los dos caminos coinciden salvo redondeo.",
    ],
    anclas: {
      bandas: [
        { banda: "> 110", puntaje: 100 },
        { banda: "100 – 110", puntaje: 85 },
        { banda: "90 – 100", puntaje: 60 },
        { banda: "80 – 90", puntaje: 35 },
        { banda: "≤ 80", puntaje: 10 },
      ],
      puntos: [[80, 10], [85, 35], [95, 60], [105, 85], [110, 100]],
      unidadCorta: "base 100 = 4T-2023",
    },
    limitaciones: [
      "La parte provincial NO es la recaudación provincial total: son los Ingresos Brutos de los contribuyentes que operan en varias provincias, más los regímenes de retención y percepción. Cada provincia recauda además de sus contribuyentes puramente locales, y eso no pasa por este circuito. Es una porción grande y homogénea de la base imponible provincial, no su universo.",
      "Al medir el nivel mes a mes en lugar de la variación contra el año anterior, el indicador es más nervioso: un mes puede moverlo varios puntos. Es el precio de no diluir la señal en una ventana de doce meses, y se acepta a cambio de que un giro se vea cuando ocurre y no a lo largo del año siguiente.",
      "Los factores que corrigen la estacionalidad se estiman con la propia serie, que todavía tiene tres o cuatro observaciones por mes calendario. Al acumularse meses los factores se recalculan, de modo que los puntos ya publicados pueden moverse algo.",
      "Mide INGRESOS, no resultado fiscal: ni siquiera midiendo sólo los impuestos internos la recaudación dice por sí sola si las cuentas del Estado cierran. Por eso la dimensión incorporó el resultado primario, y este indicador se lee como lo que es: una señal de actividad y formalidad de la base imponible.",
      "Excluir la aduana resuelve el caso más grande de política tributaria contaminando la lectura, pero no todos: la propia DGI contiene impuestos cuyas alícuotas y mínimos cambiaron en el período, y las provincias también movieron alícuotas de Ingresos Brutos. El indicador no es neutral respecto de las decisiones de gobierno; una medición a legislación constante exigiría modelar cada cambio impositivo y no es reproducible de forma automática.",
      "Los aportes a la seguridad social también son base imponible doméstica y quedan afuera. Siguen su propia dinámica —cayeron en términos reales desde fines de 2025— y mezclarlos habría sumado el mercado laboral a un indicador que quiere medir actividad y formalidad.",
      "Deflactor único (índice de precios nacional), sin deflactor específico de la base imponible ni deflactores provinciales.",
      "Las bandas se fijaron sobre una grilla conceptual —pasos de diez puntos de la base imponible real de la transición— y no sobre la distribución observada. La serie disponible recorre de 88 a 115, así que la banda más baja describe una situación posible y no una observada.",
    ],
    faltantes: "Si falta la gacetilla provincial de un mes, ese mes no entra y el indicador mantiene el último punto disponible, señalado como desactualizado. Sin ventana suficiente para corregir estacionalidad, el indicador no publica y el saldo comercial junto con el resultado primario explican la dimensión.",
    revisiones: "La recaudación publicada por las dos fuentes no se revisa hacia atrás, pero este indicador sí puede moverse en puntos ya publicados, porque los factores estacionales se recalculan al acumular meses. La reconstrucción de la parte provincial de 2022 está controlada contra el acumulado anual deducido por separado.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original, entonces como variación mensual nominal." },
      { fecha: "2026-06-26", cambio: "Pasa a variación interanual real deflactada por IPC: la variación nominal confundía inflación con recaudación." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "Pasa a promedio móvil de tres meses sobre meses con IPC cerrado; el mes fresco queda como provisorio sin puntuar." },
      { fecha: "2026-07-18", cambio: "Baja del 60% al 30% de la dimensión y se reinterpreta como indicador de actividad y formalidad de la base imponible: la viabilidad fiscal pasa a medirse con el resultado primario, que entra como componente principal." },
      { fecha: "2026-07-25", cambio: "Pasa a medir la recaudación de impuestos internos en lugar de la total, a pedido del editor. Con el total, el indicador venía castigando el recorte de retenciones: durante 2026 la recaudación aduanera cayó entre quince y treinta y siete por ciento real mientras la base imponible doméstica se mantenía estable, de modo que el índice leía como deterioro económico lo que era una decisión de política tributaria. Las bandas no se tocaron: la unidad sigue siendo la variación real y el cero sigue siendo el punto de referencia." },
      { fecha: "2026-07-29", cambio: "Suma los impuestos provinciales del Convenio Multilateral y cambia de métrica: deja la variación contra el mismo mes del año anterior y pasa al nivel de base imponible real desestacionalizada, con el cuarto trimestre de 2023 igual a 100. El motivo es que el dato es mensual y la variación interanual desperdiciaba esa resolución arrastrando la base de hace un año: en junio de 2026 informaba una mejora de tres por ciento contra un 2025 deprimido, mientras el nivel real estaba casi doce por ciento por debajo del punto de partida. Las dos lecturas eran ciertas y la del nivel es la que corresponde a un índice de tensión. La parte provincial agrega información propia y no repite a la nacional: las dos series se mueven en direcciones distintas en dieciocho de veintiocho meses, y eso se verifica también en el sistema de liquidación central, el más estable, de modo que no es un efecto de sistemas que se van incorporando. Las bandas se rehicieron porque no eran traducibles: estaban ancladas al cero de una variación y el punto con significado de un nivel es el 100." },
    ],
  },

  tcrm: {
    tipo: "indicador",
    id: "tcrm",
    cinturon: "macro",
    rezago: "La planilla oficial se actualiza a diario; el promedio mensual del mes cerrado está disponible en los primeros días del mes siguiente.",
    fuente: {
      organismo: "BCRA",
      operacion: "ITCRM — Índice de Tipo de Cambio Real Multilateral (base 17-dic-2015 = 100), promedios mensuales",
      serie: "Planilla oficial ITCRMSerie.xlsx, hoja de promedios mensuales",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Indices_tipo_cambio_multilateral.asp",
      acceso: "Automático: descarga y lectura de la planilla oficial; una sola descarga por actualización sirve al índice y a los bilaterales de contexto.",
    },
    transformaciones: [
      "Ninguna sobre el valor: se publica el promedio mensual oficial tal cual.",
      "La lectura del puntaje es invertida: un índice más bajo (peso más caro en términos reales) significa menos competitividad y más tensión.",
    ],
    anclas: {
      bandas: [
        { banda: "> 110", puntaje: 100 },
        { banda: "95 – 110", puntaje: 80 },
        { banda: "85 – 95", puntaje: 60 },
        { banda: "75 – 85", puntaje: 35 },
        { banda: "≤ 75", puntaje: 10 },
      ],
      puntos: [[75, 10], [80, 35], [90, 60], [102.5, 80], [110, 100]],
      unidadCorta: "índice",
    },
    dobleUso: "Los tipos de cambio bilaterales con Brasil y Estados Unidos, de la misma planilla, se publican como series de contexto en el gráfico del indicador.",
    limitaciones: [
      "Depende de una planilla con dirección y formato fijos: si el BCRA los cambia, el indicador cae a una serie alternativa discontinuada, marcada como desactualizada.",
      "Las bandas y el peso de la dimensión (11%) son operacionalización propia calibrada con la historia 1997-2026 — el documento institucional no los define.",
    ],
    faltantes: "Con la planilla caída, cae a la serie histórica alternativa (discontinuada a fines de 2024, marcada desactualizada); agotado eso, se mantiene el último valor disponible y los pesos se renormalizan.",
    revisiones: "El índice oficial no se revisa hacia atrás de forma habitual; la serie del informe se reconstruye completa de la planilla en cada actualización.",
    cambios: [
      { fecha: "2026-06-27", cambio: "La fuente pasa de la serie del INDEC (discontinuada en diciembre de 2024, con 18 meses de rezago acumulado) al ITCRM oficial del BCRA. Era un indicador de contexto." },
      { fecha: "2026-06-28", cambio: "Deja de ser contexto y entra al índice como quinta dimensión (competitividad externa)." },
      { fecha: "2026-06-30", cambio: "Peso de la dimensión recortado de 12% a 11% al entrar la dimensión de inversión." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  rem_ipc_12m: {
    tipo: "indicador",
    id: "rem_ipc_12m",
    cinturon: "macro",
    rezago: "El BCRA releva el REM los últimos días de cada mes y publica los resultados en los primeros días hábiles del mes siguiente.",
    fuente: {
      organismo: "BCRA",
      operacion: "REM — Relevamiento de Expectativas de Mercado: mediana de la inflación esperada para los próximos 12 meses",
      serie: "API de Estadísticas Monetarias del BCRA (variable 29)",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Relevamiento_Expectativas_de_Mercado.asp",
      acceso: "Automático: API pública del BCRA.",
    },
    transformaciones: [
      "El valor publicado en la card es el nivel anual esperado, tal cual lo releva el BCRA.",
      "Para puntuar se convierte a su equivalente mensual (raíz doceava) y se lee con la misma escala mensual que el IPC: expectativas y dato realizado quedan en la misma vara.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 1", puntaje: 100 },
        { banda: "1 – 2", puntaje: 85 },
        { banda: "2 – 3", puntaje: 65 },
        { banda: "3 – 5", puntaje: 40 },
        { banda: "> 5", puntaje: 10 },
      ],
      puntos: [[1, 100], [1.5, 85], [2.5, 65], [4, 40], [5, 10]],
      unidadCorta: "% mensual equivalente",
      sinEjemplo: true,
    },
    limitaciones: [
      "Es una expectativa (mediana de pronósticos de consultoras y bancos), no un dato realizado: mide credibilidad, no inflación.",
      "La conversión a equivalente mensual supone un ritmo constante a lo largo del año esperado.",
      "La escala vigente es una decisión propia: las bandas absolutas del documento original quedaron miscalibradas para un régimen de desinflación y se reemplazaron, con el cambio documentado.",
    ],
    faltantes: "Si el dato falta, se mantiene el último valor disponible, señalado como desactualizado; sin dato, el IPC, el IDM y la presión de dolarización renormalizan dentro de la dimensión de estabilidad monetaria.",
    revisiones: "El REM publicado no se revisa: cada mes es un relevamiento nuevo.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original, con bandas absolutas sobre el nivel anual." },
      { fecha: "2026-06-26", cambio: "Pasa a puntuarse por el equivalente mensual con las bandas del IPC, tras descartarse una versión intermedia por brecha contra el ritmo corriente." },
      { fecha: "2026-06-28", cambio: "Su peso interno baja de 50% a 30% de la dimensión al entrar el IDM." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-13", cambio: "Su peso interno pasa de 30% a 25% al incorporarse una cuarta señal de estabilidad monetaria, hoy medida por la presión de dolarización de carteras." },
    ],
  },

  idm: {
    tipo: "indicador",
    id: "idm",
    cinturon: "macro",
    rezago: "Necesita el IPC cerrado para deflactar: se publica para el último mes con IPC disponible, unas dos semanas después de mediados del mes siguiente.",
    fuente: {
      organismo: "BCRA (agregados monetarios) + INDEC (IPC como deflactor)",
      operacion: "Agregados monetarios privados: circulante en poder del público, depósitos privados, cuentas corrientes privadas en pesos, cajas de ahorro privadas en pesos y M2 transaccional privado; índice de elaboración propia",
      serie: "API de Estadísticas Monetarias del BCRA (variables 17, 100 y 197) + IPC 148.3_INIVELNAL_DICI_M_26",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp",
      acceso: "Automático: API pública del BCRA y API de series de datos.gob.ar; la brecha se calcula en el propio informe.",
    },
    transformaciones: [
      "M3 privado construido = circulante en poder del público + depósitos privados, a fin de mes (no existe como serie directa del BCRA).",
      "M2 privado transaccional = circulante en poder del público + cuentas corrientes privadas en pesos + cajas de ahorro privadas en pesos. Excluye los depósitos a la vista remunerados de personas jurídicas.",
      "IDM = crecimiento interanual real del M3 privado − crecimiento interanual real del M2 privado, ambos deflactados por IPC, en puntos porcentuales.",
      "Positivo = sobran pesos respecto de lo que la economía quiere retener (presión latente sobre precios y brecha); negativo = remonetización genuina.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −2", puntaje: 100 },
        { banda: "−2 – 2", puntaje: 85 },
        { banda: "2 – 5", puntaje: 60 },
        { banda: "5 – 8", puntaje: 35 },
        { banda: "> 8", puntaje: 10 },
      ],
      puntos: [[-2, 100], [0, 85], [3.5, 60], [6.5, 35], [8, 10]],
      unidadCorta: "pp",
    },
    dobleUso: "Comparte insumos con el IdC (depósitos privados y el IPC como deflactor).",
    limitaciones: [
      "Las bandas están calibradas con una historia corta (fines de 2024 en adelante): desde −11 puntos en la remonetización hasta +7 en el pico de excedente.",
      "La fórmula es una reinterpretación documentada de la propuesta institucional: la versión literal (nominal contra real, mensual) tenía sesgo inflacionario y estacionalidad de aguinaldo, y se reemplazó por la versión interanual real-real.",
    ],
    faltantes: "Si falta un insumo, se mantiene el último valor disponible, señalado como desactualizado; sin dato, IPC, REM y presión de dolarización renormalizan dentro de la dimensión.",
    revisiones: "Los stocks del BCRA no se revisan de forma habitual; la serie se regenera completa en cada actualización.",
    cambios: [
      { fecha: "2026-06-28", cambio: "Nace y entra al índice: la dimensión de estabilidad monetaria pasa de IPC 50% / REM 50% a IPC 40% / REM 30% / IDM 30%, en versión interanual real-real." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-13", cambio: "Aclaración de transparencia, sin cambio metodológico: la ficha explicita la composición del M2 transaccional y publica la cadena completa de ponderación y el aporte vigente del IDM al ITCM." },
      { fecha: "2026-07-13", cambio: "Su peso interno pasa de 30% a 25% al incorporarse una señal de presión de dolarización; su peso nominal efectivo en el ITCM pasa de 7,8% a 6,5%." },
    ],
  },

  desequilibrio_monetario: {
    tipo: "indicador",
    id: "desequilibrio_monetario",
    cinturon: "macro",
    rezago: "Se publica para el último mes con los cinco insumos completos. El cierre lo marca la planilla mensual del mercado de cambios, que sale con hasta dos meses de rezago; los agregados monetarios del BCRA son diarios.",
    fuente: {
      organismo: "BCRA",
      operacion: "M2 transaccional del sector privado (var. 197), billetes y monedas en poder del público (17), depósitos del sector privado no financiero en pesos (100) y en moneda extranjera expresados en pesos (104), y el concepto 03 del Mercado de Cambios",
      url: "https://www.bcra.gob.ar/estadisticas-estandarizadas-sobre-la-evolucion-del-mercado-de-cambios/",
      acceso: "Automático: API monetaria del BCRA y planilla acumulativa del anexo estadístico del mercado de cambios y balance cambiario.",
    },
    transformaciones: [
      "Componente A (stock, dentro del sistema): el M2 transaccional del sector privado se divide por el M3 ampliado —circulante en poder del público más depósitos privados en pesos más depósitos privados en dólares expresados en pesos— y se expresa en porcentaje. Mide qué proporción de la liquidez privada total sigue en pesos de uso transaccional.",
      "El numerador es la variable 197 del BCRA y no una reconstrucción propia, porque la definición del indicador excluye la vista remunerada de personas jurídicas y esa exclusión no se puede replicar sumando circulante, cuentas corrientes y cajas de ahorro: medido sobre la historia disponible, esa suma corre 22,8% por encima de la 197 en promedio y hasta 57% en un mes.",
      "Componente B (flujo, fuera del sistema): compra neta de billetes y divisas sin fines específicos del sector privado no financiero, en millones de dólares, con el sector público excluido. Positivo significa salida.",
      "Cada componente se convierte en una posición de 0 a 1 interpolando entre los percentiles de su ventana de calibración, con saturación fuera de los extremos. Componente A: 31,62 → 0; 34,48 → 0,25; 38,27 → 0,50; 44,34 → 0,75; 49,96 → 1. Componente B: 1.122 → 0; 1.954 → 0,25; 2.363 → 0,50; 3.644 → 0,75; 6.545 → 1.",
      "Las dos posiciones se cruzan por interpolación bilineal entre las cuatro esquinas de la matriz, expresadas en tensión de 0 a 100: A alto con B bajo (confianza real) da 0; A bajo con B bajo (dolarización contenida en el sistema) da 40; A alto con B alto (fuga oculta fuera del sistema) da 77,5; A bajo con B alto (deterioro dentro y fuera) da 90.",
      "La celda que la ficha original dejó escrita como «naranja/rojo» se resuelve como el punto medio entre naranja (65) y rojo (90), que es 77,5.",
      "La tensión se traduce al ITCM con anclas explícitas que son su inversión exacta: 0 da 100 y 100 da 0. Las cuatro esquinas caen sobre esa recta, de modo que no hay una segunda escala que se pueda desincronizar de la del cálculo.",
      "Pesa 20% dentro de estabilidad monetaria, dimensión que representa 26% del ITCM: su peso nominal efectivo es 5,2% del índice. La ficha original pide un peso similar al de los indicadores cambiarios y de reservas: 5,2% queda al lado del 5,4% de las reservas del BCRA, que es el comparable. No se tomó el tipo de cambio real como referencia, porque su 11% viene de ser el único indicador de su dimensión y no de un juicio sobre su importancia relativa.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 20", puntaje: 100 },
        { banda: "20 – 50", puntaje: 60 },
        { banda: "50 – 80", puntaje: 35 },
        { banda: "> 80", puntaje: 10 },
      ],
      puntos: [[0, 100], [40, 60], [77.5, 22.5], [90, 10], [100, 0]],
      unidadCorta: "pts de tensión (0–100)",
    },
    dobleUso: "Comparte fuente con el IDM (los agregados monetarios del BCRA) y con el saldo del mercado de cambios, pero no mide lo mismo que ninguno: el IDM compara el crecimiento real de la oferta amplia de pesos contra el de la demanda transaccional, y este indicador mira el nivel de dolarización de la liquidez y la salida efectiva de divisas. Reemplaza a la presión de dolarización de carteras, que medía la misma fuga desde la misma planilla y quedaba contándola dos veces dentro de la dimensión.",
    limitaciones: [
      "La serie arranca en abril de 2025 y no antes. El componente de flujo se puede calcular desde 2003, pero bajo cepo daba prácticamente cero por falta de acceso al dólar, no por confianza: publicarlo hacia atrás haría leer «poca fuga» —es decir, verde— justo en los meses de control de cambios.",
      "La ventana de calibración del componente A empieza en enero de 2021, no en 2016 como pedía la ficha original, porque el M2 transaccional del sector privado no se publica antes de esa fecha y reconstruirlo con las series sueltas desplazaría el ratio casi nueve puntos porcentuales.",
      "El componente B tiene sólo quince meses de historia bajo el régimen abierto. Los cortes por percentiles deberán revisarse cuando haya más evidencia posterior a la apertura del cepo.",
      "Los cortes por percentiles hacen que verde signifique el mejor cuarto de la ventana de calibración, que es un período de dolarización alta, y no un nivel deseable en abstracto. Cuando un componente se mueve cerca del extremo de su ventana, su posición se satura y el indicador deja de distinguir entre meses: la tabla de anclas y la serie muestran dónde está cayendo.",
      "El denominador del componente A incluye depósitos en dólares valuados en pesos, así que una devaluación baja el ratio aunque nadie cambie de cartera. El efecto es visible en diciembre de 2023 y en julio de 2025. La tensión cambiaria que eso refleja ya puntúa además por su cuenta en el TCRM.",
      "El componente A tiene estacionalidad de aguinaldo: junio promedia 1,7 puntos porcentuales por encima de la media y diciembre 1,2. Es chico frente al rango del indicador y no se corrige.",
      "La ficha original nombra el componente B como formación de activos externos del sector privado no financiero. El BCRA ya no publica ese rubro con ese nombre —reserva esa etiqueta para el sector financiero y el público— y lo del privado no financiero sale bajo el concepto 03, que es el que se usa.",
      "El componente B no distingue los dólares que quedan depositados en el sistema local de los que van al colchón. La ficha original describía esa distinción, pero ninguna serie publicada del balance cambiario la hace.",
    ],
    faltantes: "Un mes entra sólo si tiene los cinco insumos. Si falta cualquiera, ese punto no se calcula: nunca se imputa cero. La card conserva el último valor válido, señalado como desactualizado; sin dato utilizable, el ITCM renormaliza los componentes disponibles.",
    revisiones: "Las revisiones de la planilla del mercado de cambios se incorporan en la siguiente actualización. Los cortes por percentiles quedan congelados: no se recalculan con cada corrida, porque si se movieran con el último dato el puntaje de un mes dejaría de ser reproducible y la serie cambiaría hacia atrás sin que nadie tocara nada.",
    cambios: [
      { fecha: "2026-08-11", cambio: "El peso dentro de estabilidad monetaria pasa de 10% a 20%, para que su peso nominal en el índice quede a la altura del de las reservas, como pedía la ficha original. Ceden el REM y el IDM; la inflación realizada conserva su 40%." },
      { fecha: "2026-08-11", cambio: "Alta del indicador, a partir de la ficha Desequilibrio Monetario. Reemplaza a la presión de dolarización de carteras dentro de estabilidad monetaria. Los cortes de banda preliminares de la ficha se sustituyeron por percentiles reales de cada serie, como la propia ficha preveía: con los preliminares ninguno de los quince meses de la ventana daba verde, y su referencia de que más de 3.000 millones era comparable a julio de 2025 erraba por unos 80%, porque ese mes fueron 5.436 millones." },
    ],
  },

  iai: {
    tipo: "indicador",
    id: "iai",
    cinturon: "macro",
    rezago: "El titular se calcula al último mes común de la construcción (ISAC) y los bienes de capital importados (~2 meses y medio); el componente más fresco se muestra como provisorio sin puntuar.",
    fuente: {
      organismo: "INDEC (construcción y bienes de capital) + DNRPA (patentamientos comerciales, en acumulación)",
      operacion: "ISAC nivel general (serie original) + importaciones de bienes de capital del ICA + inscripciones iniciales de vehículos comerciales",
      serie: "33.2_ISAC_NIVELRAL_0_M_18_63 · 74.3_IIBCA_0_M_32 (datos.gob.ar) · dataset de inscripciones iniciales de la DNRPA (datos.jus.gob.ar)",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42",
      acceso: "Automático: API de series de datos.gob.ar; los patentamientos comerciales se acumulan mes a mes desde el portal de datos de justicia (la fuente solo publica el mes corriente).",
    },
    transformaciones: [
      "Variación interanual de cada componente al mes común.",
      "Promedio ponderado de construcción y bienes de capital. La composición está prevista para cambiar sola: cuando los patentamientos de vehículos comerciales acumulen trece meses de historia propia entran como tercer componente y los dos actuales ceden peso. Los porcentajes vigentes se leen en la tabla de composición, que se recalcula con cada actualización.",
    ],
    anclas: {
      bandas: [
        { banda: "> 10", puntaje: 100 },
        { banda: "2 – 10", puntaje: 80 },
        { banda: "−2 – 2", puntaje: 60 },
        { banda: "−10 – −2", puntaje: 35 },
        { banda: "≤ −10", puntaje: 10 },
      ],
      puntos: [[-10, 10], [-6, 35], [0, 60], [6, 80], [10, 100]],
      unidadCorta: "% i.a.",
    },
    dobleUso: "La operación ISAC también alimenta (en su variante desestacionalizada) un componente del ITCIS; los bienes de capital son una subserie del ICA que alimenta el saldo comercial.",
    limitaciones: [
      "Los bienes de capital se miden en dólares corrientes e incluyen el efecto de los precios internacionales: el índice de cantidades oficial es solo trimestral.",
      "El tercer componente (patentamientos comerciales) no tiene serie histórica pública: se acumula desde mediados de 2026 y recién tendrá comparación interanual a mediados de 2027.",
      "Las bandas anchas son calibración propia declarada: el umbral fino del documento no sobrevivía a la volatilidad del dato argentino reciente.",
    ],
    faltantes: "Sin patentamientos, la composición renormaliza a 65/35 (situación actual); sin mes común de las otras dos fuentes, se mantiene el último valor disponible señalado como desactualizado y la dimensión se renormaliza.",
    revisiones: "El titular se calcula sobre un panel alineado por mes común y no se revisa; las revisiones de las fuentes se absorben al regenerar las series.",
    cambios: [
      { fecha: "2026-06-30", cambio: "Nace y entra al índice como parte de la sexta dimensión (inversión, 12%), sin el componente de patentamientos por falta de historia." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "El titular pasa al último mes común de las fuentes (antes podía mezclar meses distintos bajo una sola etiqueta); el componente fresco queda como provisorio." },
    ],
  },

  icip: {
    tipo: "indicador",
    id: "icip",
    cinturon: "macro",
    rezago: "El titular se calcula al último mes común de los tres insumos (~2 meses y medio a 3); el insumo más fresco se muestra como provisorio.",
    fuente: {
      organismo: "INDEC (los tres insumos)",
      operacion: "Balanza de servicios (pagos al exterior de servicios de informática) + IPI manufacturero + índice de empleo de la Encuesta de Indicadores Laborales",
      serie: "185.1_PAGO_SERVIICA_0_M_38 · 453.1_SERIE_ORIGNAL_0_0_14_46 · 50.3_ICS_0_M_12 · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-35-45",
      acceso: "Automático: API pública de series de tiempo; la composición se calcula en el propio informe.",
    },
    transformaciones: [
      "Servicios tecnológicos: variación interanual de los pagos al exterior por software, nube e inteligencia artificial.",
      "Productividad: variación interanual del cociente producción industrial / empleo.",
      "Promedio ponderado 57% servicios + 43% productividad.",
    ],
    anclas: {
      bandas: [
        { banda: "> 20", puntaje: 100 },
        { banda: "5 – 20", puntaje: 80 },
        { banda: "−5 – 5", puntaje: 60 },
        { banda: "−20 – −5", puntaje: 35 },
        { banda: "≤ −20", puntaje: 10 },
      ],
      puntos: [[-20, 10], [-12.5, 35], [0, 60], [12.5, 80], [20, 100]],
      unidadCorta: "% i.a.",
    },
    dobleUso: "La operación IPI también alimenta (en su variante desestacionalizada) un componente del ITCIS.",
    limitaciones: [
      "El diseño institucional incluía la importación de hardware de alta tecnología, que no es automatizable con las fuentes públicas actuales: el índice quedó con dos de tres componentes, renormalizados y declarados.",
      "AMBIGÜEDAD DE INTERPRETACIÓN, declarada. Un aumento de los pagos al exterior por servicios de informática admite dos lecturas opuestas y el índice adopta una: puede significar que la economía se está digitalizando —incorpora software, nube e inteligencia artificial para producir mejor— o que depende de tecnología que no produce y gira divisas para conseguirla. El indicador puntúa la primera lectura: más pagos, mejor puntaje. La evidencia disponible la respalda sólo en parte. Sobre ciento siete meses, los pagos anticipan a la productividad con una correlación de 0,28 cuando se los adelanta un trimestre: una asociación real pero modesta, compatible también con que ambas variables suban juntas cuando la economía crece, sin que una cause a la otra. Quien lea el indicador debe saber que un valor alto no distingue por sí solo entre capitalización tecnológica y dependencia tecnológica.",
      "El componente de pagos al exterior es mucho más volátil que el de productividad (desvío de 71 puntos contra 11) y pesa el 57% del índice: los movimientos del indicador los explica casi siempre esa serie, no la de productividad.",
      "Los pagos al exterior por servicios de informática son una aproximación a la digitalización, no una medición directa de inversión en capital digital.",
      "El empleo de la encuesta laboral se usa como aproximación de las horas trabajadas.",
    ],
    faltantes: "Sin mes común de los tres insumos, se mantiene el último valor disponible, señalado como desactualizado; sin dato, el IAI pasa a explicar toda la dimensión de inversión.",
    revisiones: "Titular por panel alineado, no se revisa; las revisiones de las fuentes se absorben al regenerar las series.",
    cambios: [
      { fecha: "2026-07-18", cambio: "Se declara en la ficha la ambigüedad de interpretación del componente de pagos al exterior, que admite leerse como capitalización tecnológica o como dependencia tecnológica, junto con la evidencia que la respalda parcialmente." },
      { fecha: "2026-06-30", cambio: "Nace y entra al índice (dimensión inversión, 40% interno), sin el componente de hardware y con bandas anchas propias." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "El titular pasa al último mes común de los tres insumos." },
    ],
  },

  credito_privado: {
    tipo: "indicador",
    id: "credito_privado",
    cinturon: "macro",
    rezago: "El stock del BCRA es diario, pero el titular espera el IPC que lo deflacta: el dato fresco se muestra como provisorio sin puntuar.",
    fuente: {
      organismo: "BCRA (stock de préstamos) + INDEC (IPC como deflactor)",
      operacion: "Préstamos al sector privado (saldos a fin de mes), variación interanual real",
      serie: "API de Estadísticas Monetarias del BCRA (variable 26) + IPC 148.3_INIVELNAL_DICI_M_26",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp",
      acceso: "Automático: API pública del BCRA y API de series de datos.gob.ar.",
    },
    transformaciones: [
      "Variación interanual del stock a fin de mes, deflactada por el IPC del mismo período: el crédito que efectivamente llegó, no el que infló la nominalidad.",
      "Mide crédito realizado — complementario del IdC, que mide la capacidad de prestar.",
    ],
    anclas: {
      bandas: [
        { banda: "> 40", puntaje: 100 },
        { banda: "20 – 40", puntaje: 85 },
        { banda: "8 – 20", puntaje: 65 },
        { banda: "0 – 8", puntaje: 45 },
        { banda: "−10 – 0", puntaje: 25 },
        { banda: "≤ −10", puntaje: 10 },
      ],
      puntos: [[-10, 10], [-5, 25], [4, 45], [14, 65], [30, 85], [40, 100]],
      unidadCorta: "% i.a. real",
    },
    dobleUso: "La misma serie se sigue extrayendo como contexto no publicado. El cinturón de impacto social usó las líneas a familias (tarjetas y personales) para un componente de endeudamiento que dejó de integrar el ITCIS en julio de 2026: leía el crecimiento de la deuda real como mayor acceso al crédito. Esa dimensión la mide la mora desde entonces.",
    limitaciones: [
      "Bandas calibradas a la remonetización 2024-2026 (el crédito real llegó a crecer 90% interanual desde una base ínfima): calibración propia sobre historia corta, declarada.",
      "Agregado total: no distingue empresas de familias ni líneas de crédito.",
    ],
    faltantes: "Sin mes común entre stock e IPC, se mantiene el último valor disponible, señalado como desactualizado; sin dato, reservas e IdC renormalizan dentro de la dimensión de financiamiento.",
    revisiones: "Los saldos del BCRA no se revisan de forma habitual; la serie se regenera completa (desde diciembre de 2023) en cada actualización.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Nace y entra al índice: rescata la única señal no redundante de los cuatro contextos nominales (que dejan de publicarse); la dimensión de financiamiento queda 45% reservas + 40% IdC + 15% crédito." },
      { fecha: "2026-07-04", cambio: "El titular pasa al último mes con IPC cerrado; el dato diario fresco queda como provisorio (antes se deflactaba el préstamo del día con un IPC de dos meses atrás)." },
    ],
  },

  resultado_primario: {
    tipo: "indicador",
    id: "resultado_primario",
    cinturon: "macro",
    rezago: "Un mes: el informe de ingresos y gastos se publica en la segunda quincena del mes siguiente.",
    fuente: {
      organismo: "Secretaría de Hacienda (resultado primario) + recaudación nacional",
      operacion: "Informe mensual de ingresos y gastos del Sector Público Nacional, y recaudación tributaria total",
      serie: "Resultado primario mensual y recaudación total mensual, ambos en millones de pesos",
      url: "https://www.argentina.gob.ar/economia/sechacienda",
      acceso: "Automático: API de series de tiempo del Estado nacional.",
    },
    transformaciones: [
      "Ambas series se acumulan en ventanas de doce meses. El resultado primario mensual es fuertemente estacional —diciembre da déficit todos los años por el aguinaldo y el cierre del ejercicio, enero da superávit alto—, así que puntuar el mes suelto marcaría un colapso fiscal cada diciembre.",
      "El resultado acumulado se divide por la recaudación acumulada del mismo período: de cada peso que recauda el Estado, cuánto le sobra después de gastar, antes de pagar intereses.",
      "Se normaliza contra la recaudación y no contra el producto ni contra los precios: no hay producto nominal mensual publicado, y usar el índice de precios sumaría una dependencia más a un deflactor que ya interviene en otros cuatro indicadores del índice.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −5", puntaje: 10 },
        { banda: "−5 – 0", puntaje: 30 },
        { banda: "0 – 4", puntaje: 60 },
        { banda: "4 – 8", puntaje: 85 },
        { banda: "> 8", puntaje: 100 },
      ],
      puntos: [[-5, 10], [-2.5, 30], [2, 60], [6, 85], [8, 100]],
      unidadCorta: "% de la recaudación",
    },
    limitaciones: [
      "El denominador es la recaudación tributaria, no el total de ingresos del Sector Público Nacional: sirve como escala estable y comparable en el tiempo, pero no es un cociente entre magnitudes del mismo universo contable.",
      "Es resultado primario: excluye los intereses de la deuda. Un superávit primario alto convive con déficit financiero si la carga de intereses es grande.",
      "La ventana de doce meses suaviza la estacionalidad pero también demora en reflejar un cambio de régimen fiscal: un giro brusco tarda meses en verse completo.",
      "No mide la calidad del ajuste: el mismo resultado puede alcanzarse recortando gasto de capital o licuando jubilaciones, y el indicador no los distingue.",
    ],
    faltantes: "Sin una ventana completa de doce meses se conserva el último valor disponible, señalado como desactualizado; la recaudación y el saldo comercial renormalizan dentro de la dimensión.",
    revisiones: "Las cifras fiscales pueden revisarse en publicaciones posteriores; la serie se regenera completa desde diciembre de 2023 en cada actualización.",
    cambios: [
      { fecha: "2026-07-18", cambio: "Nace y entra como componente principal de la dimensión fiscal-comercial (50%), que hasta entonces medía la viabilidad fiscal por los ingresos: la recaudación baja al 30% y el saldo comercial al 20%." },
    ],
  },

  costo_financiamiento_tesoro: {
    tipo: "indicador",
    id: "costo_financiamiento_tesoro",
    cinturon: "macro",
    rezago: "Se actualiza con cada licitación (dos por mes); el mes cierra cuando la Secretaría de Finanzas publica su planilla de colocaciones.",
    fuente: {
      organismo: "Secretaría de Finanzas (colocaciones de deuda) + BCRA (expectativas de inflación)",
      operacion: "Colocaciones de letras y bonos del Tesoro en el mercado local, y expectativa de inflación a doce meses",
      serie: "Planillas anuales de colocaciones (hojas de letras y bonos) + relevamiento de expectativas de mercado",
      url: "https://www.argentina.gob.ar/economia/finanzas/deudapublica/colocacionesdedeuda",
      acceso: "Automático: planilla oficial de cada año y serie de expectativas del BCRA.",
    },
    transformaciones: [
      "De cada colocación se obtiene la tasa efectiva anual implícita a partir del precio de corte, la fecha de vencimiento y la forma de pago del instrumento.",
      "Las colocaciones del mes se promedian ponderando por el monto adjudicado: una licitación chica no mueve el promedio como una grande.",
      "Solo entran los instrumentos a tasa fija en pesos. Los ajustados por inflación, los atados al dólar y los de tasa variable quedan afuera porque su rendimiento no es comparable con el de una tasa fija.",
      "Al promedio se le descuenta la inflación esperada a doce meses, para leer la tasa en términos reales.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −5", puntaje: 20 },
        { banda: "−5 – 0", puntaje: 55 },
        { banda: "0 – 6", puntaje: 100 },
        { banda: "6 – 12", puntaje: 75 },
        { banda: "12 – 20", puntaje: 45 },
        { banda: "> 20", puntaje: 15 },
      ],
      puntos: [[-5, 20], [-2.5, 55], [3, 100], [9, 75], [16, 45], [20, 15]],
      unidadCorta: "% real",
    },
    limitaciones: [
      "Es el único indicador del tablero cuya escala premia el punto medio y castiga los dos extremos: una tasa real muy negativa significa que el Estado se financia licuando al ahorrista, y una muy alta que la deuda crece más rápido que la economía.",
      "Se expresa en tasa efectiva anual, no en tasa nominal anual. A tasas altas la diferencia es enorme: la letra colocada en diciembre de 2023 equivalía a 105% nominal y a 169% efectiva.",
      "Los meses sin colocaciones a tasa fija en pesos no tienen dato: enero y febrero de 2024 quedan fuera de la serie porque todo lo emitido en esos meses se ajustaba por inflación.",
      "El promedio mezcla plazos: un mes con colocaciones largas y otro con cortas no son estrictamente comparables cuando la curva de tasas tiene pendiente.",
      "El deflactor es una expectativa relevada por encuesta, la misma que usa el indicador de expectativas de inflación.",
    ],
    faltantes: "Sin colocaciones a tasa fija en el mes se conserva el último valor disponible, señalado como desactualizado; reservas, capacidad prestable y crédito renormalizan dentro de la dimensión.",
    revisiones: "Las planillas del año en curso se actualizan a lo largo del año; la serie se regenera completa desde diciembre de 2023 en cada actualización.",
    cambios: [
      { fecha: "2026-07-18", cambio: "Nace y entra al índice con el 25% de la dimensión de financiamiento, que pasa a llamarse capacidad y costo del financiamiento; los otros tres componentes se recortan en proporción. Cubre el precio del financiamiento del Estado, que la dimensión no medía." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // Política — puntúa en el ITCP (paramétrica de 5 dimensiones ponderadas,
  // jul-2026); la tensión del cinturón es (100 − ITCP) / 10
  // ═══════════════════════════════════════════════════════════════════════
  votometro_ventaja_lla: {
    tipo: "indicador",
    id: "votometro_ventaja_lla",
    cinturon: "politica",
    rezago: "El Votómetro se actualiza cuando las consultoras publican encuestas nuevas (cadencia irregular, típicamente semanas); el informe recalcula la ventaja todos los días con lo cargado.",
    fuente: {
      organismo: "Fundación CIGOB — Votómetro",
      operacion: "Agregador de encuestas de intención de voto: todos los sondeos publicados desde diciembre de 2023, con calificación de calidad por consultora",
      url: "https://cigob.github.io/Votometro/",
      acceso: "Automático: lee el listado de encuestas que publica el Votómetro; si el sitio no responde, usa la última copia local.",
    },
    transformaciones: [
      "Solo cuentan las encuestas de los últimos 60 días desde el sondeo más reciente.",
      "Cada encuesta pondera por recencia (el peso decae con los días) y por la calificación de calidad de la consultora (A pesa 3, B pesa 2, C pesa 1).",
      "El indicador es la diferencia LLA − PJ de esas intenciones ponderadas, en puntos porcentuales.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas de la ventaja, interpolado entre anclas: más de +15 puntos → el más alto; entre +5 y +15 → alto; entre −5 y +5 → moderado; entre −15 y −5 → bajo; −15 o menos → el más bajo.",
      "Es el único indicador de la dimensión de imagen y voto del índice del cinturón (8% del total) — la dimensión que pesa deliberadamente menos que las otras cuatro, porque el proyecto distingue capital político de popularidad electoral.",
    ],
    dobleUso: "El mismo dato alimentó el indicador de clima electoral del cinturón espíritu de época entre junio y julio de 2026, hasta que ese cinturón quedó acotado a la intención migratoria como único indicador; la lectura duplicada se sigue registrando como seguimiento interno, sin publicarse ni puntuar.",
    limitaciones: [
      "La fuente es una curaduría propia de encuestas de terceros, no un registro oficial.",
      "El peso por recencia se calcula contra el día de la actualización: sin encuestas nuevas, el valor deriva lentamente día a día.",
      "Si pasan más de 60 días sin sondeos, el indicador se marca como desactualizado.",
    ],
    faltantes: "Si la lectura falla, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "La serie mensual completa se rederiva de las encuestas en cada actualización: un sondeo cargado con retraso corrige los meses que toca. La serie evalúa la ponderación al cierre de cada mes, así que su último punto puede diferir levemente del titular, que se recalcula todos los días.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida del capital electoral del oficialismo." },
      { fecha: "2026-06-30", cambio: "Serie mensual reconstruida hacia atrás hasta diciembre de 2023, evaluando la misma ponderación al cierre de cada mes." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), como único indicador de la dimensión de imagen y voto — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
    ],
  },

  desafios_legislativos: {
    tipo: "indicador",
    id: "desafios_legislativos",
    cinturon: "politica",
    rezago: "Las actas de votación se publican con algunos días de demora respecto de la sesión; InfoLeg carga los vetos al ritmo del Boletín Oficial.",
    fuente: {
      organismo: "Cámara de Diputados · Senado de la Nación · InfoLeg",
      operacion: "Actas de votación nominal de ambas cámaras y base de legislación nacional — normas del Poder Ejecutivo sometidas a votación en el recinto",
      url: "https://votaciones.hcdn.gob.ar",
      acceso: "Automático: clasifica las actas de votación de ambas cámaras y las cruza con los vetos registrados en InfoLeg. Elaboración propia sobre fuentes oficiales.",
    },
    transformaciones: [
      "Una norma cuenta como desafiada cuando el Congreso la somete a votación en el recinto: un veto presidencial sobre el que se vota una insistencia, o un decreto puesto a consideración bajo el procedimiento de la ley 26.122.",
      "Cada norma se cuenta una sola vez, en el mes de su primer desafío, aunque después vuelva al recinto.",
      "Se suman las de los últimos doce meses calendario. No importa el resultado: entran tanto las que el Gobierno terminó perdiendo como las que logró sostener.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del conteo, interpolado entre anclas: 2 desafíos o menos en doce meses → el más alto; entre 2 y 5 → alto; entre 5 y 9 → moderado; entre 9 y 12 → bajo; más de 12 → el más bajo. Las anclas parten de que desafiar una norma del Ejecutivo en el recinto es un acto excepcional, que exige mayorías especiales o un procedimiento específico: un puñado al año ya es confrontación abierta.",
      "Integra la dimensión de poder legislativo del índice del cinturón (25% del total), donde pesa 15% junto a la eficacia parlamentaria, el ratio DNU, las sesiones caídas por quórum y el bloqueo sostenido.",
      "Se lee en par con el bloqueo sostenido: éste cuenta cuántas veces el Congreso da la pelea; aquél, qué proporción de esas peleas gana el Gobierno.",
    ],
    limitaciones: [
      "La ventana contiene pocos eventos —entre cuatro y trece en el período disponible—, así que un solo desafío que entra o sale mueve el indicador de manera perceptible.",
      "Cuenta el acto de desafiar, no su importancia: una norma central y una menor pesan igual.",
      "Sigue acoplado al bloqueo sostenido, con el que comparte el registro de eventos. Son las dos caras del mismo pulso —cuánto confronta el Congreso y cuánto resiste el Gobierno— y no deben leerse como dos confirmaciones independientes.",
    ],
    faltantes: "Si el registro de eventos no está disponible, se mantiene el último valor, señalado como desactualizado. Un mes sin desafíos no es un dato faltante: es un cero, e indica que el Congreso no confrontó.",
    revisiones: "El registro se reconstruye completo en cada actualización: si una fuente carga un acta con retraso, el conteo se corrige solo hacia atrás.",
    cambios: [
      { fecha: "2026-07-19", cambio: "Entra al índice en reemplazo de las derrotas legislativas, que medían casi exactamente lo mismo que el bloqueo sostenido: desde marzo de 2025 ambos indicadores arrojaban mes a mes el mismo número, y entre los dos se llevaban el 40% de la dimensión para responder una sola pregunta. Las derrotas se siguen relevando y quedan a la vista como dato dentro de la ficha del bloqueo." },
    ],
  },

  brecha_obra_publica: {
    tipo: "indicador",
    id: "brecha_obra_publica",
    cinturon: "politica",
    rezago: "El INDEC publica la encuesta junto con el informe mensual de la construcción, unas semanas después del cierre del período relevado.",
    fuente: {
      organismo: "INDEC",
      operacion: "Encuesta Cualitativa de la Construcción — expectativas de las empresas sobre el nivel de actividad de los próximos tres meses, con respuestas separadas para obra pública y obra privada (Cuadro 7.1)",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-46",
      acceso: "Automático: descarga la planilla oficial del indicador sintético de la actividad de la construcción y lee el cuadro de expectativas.",
    },
    transformaciones: [
      "Para cada grupo de empresas se calcula un saldo de respuesta: el porcentaje que espera que su actividad aumente menos el porcentaje que espera que disminuya. Quienes esperan que no varíe no suman ni restan.",
      "La brecha es el saldo de las empresas de obra pública menos el de las de obra privada. Cero significa que ambos grupos esperan lo mismo; un valor negativo, que las que dependen del Estado esperan peor que sus pares privadas.",
      "Se promedian los últimos doce meses. La lectura mensual es volátil —salta unos seis puntos de un mes al siguiente— y el promedio móvil deja ver el movimiento de fondo sin perder capacidad de reacción.",
      "La serie se reconstruye con el mismo cálculo desde noviembre de 2017, de modo que hay línea de base de tres gobiernos anteriores contra la cual comparar.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas de la brecha, interpolado entre anclas: +10 puntos porcentuales o más → el más alto; entre 0 y +10 → alto; entre −10 y 0 → moderado; entre −20 y −10 → bajo; menos de −20 → el más bajo. Las anclas se fijaron en números redondos alrededor del cero, que es el valor con significado propio: brecha nula quiere decir que el Estado no es una fuente diferencial de incertidumbre para quienes trabajan para él.",
      "Pesa la mitad de la dimensión de sector privado del índice del cinturón (13% del total), incorporada en julio de 2026. La otra mitad es la postura pública de las cámaras empresarias.",
    ],
    limitaciones: [
      "El comportamiento del indicador depende del gobierno que se mida, y conviene saberlo antes de leerlo. Contrastado contra el índice de incertidumbre de política económica, acompaña esa incertidumbre durante las dos administraciones anteriores —correlación de −0,56 con Macri y de −0,64 con Alberto Fernández, el signo esperado— y se invierte con la actual, donde da +0,33. La razón es sustantiva y no estadística: para gobiernos anteriores la tensión con las empresas que dependen del Estado era un síntoma de dificultades, mientras que para el actual el recorte de la obra pública es el programa de gobierno. Ejecutarlo reduce la incertidumbre sobre la política económica al mismo tiempo que tensa la relación con ese sector. El caso más claro es 2024: el indicador marcó el peor valor de sus diez años de serie durante el año en que se sancionó la Ley Bases y la incertidumbre de política tocó su nivel más bajo del período.",
      "De lo anterior se sigue el límite de fondo: el indicador mide bien la tensión, pero no distingue cuándo esa tensión es un costo que el Gobierno sufre y cuándo es un precio que decide pagar. El índice lo puntúa como costo. Un lector que quiera evaluar capacidad de gobierno debería leerlo junto con lo que el Gobierno logró en el mismo período, no de forma aislada.",
      "Mide un solo canal de conflicto: el gasto en infraestructura. Sería ciego a una tensión con el agro, la energía o los bancos, y por eso conviene leerlo como lo que es —la relación del Gobierno con el sector que depende de la obra pública— y no como un termómetro del humor empresario en general.",
      "Son expectativas declaradas, no decisiones tomadas. Conviene contrastarlo con el volumen de insumos de construcción efectivamente vendidos: si las expectativas se hunden y las ventas no caen, la tensión es sobre todo discursiva.",
      "La pregunta indaga por el cambio esperado, no por el nivel. Un recorte sostenido termina normalizándose: cuando las empresas se acostumbran al presupuesto nuevo dejan de esperar caídas adicionales y la brecha vuelve a cero aunque la obra pública siga en un piso históricamente bajo.",
      "La encuesta releva grandes empresas constructoras; las pequeñas y las regionales están subrepresentadas.",
    ],
    faltantes: "Si la planilla no está disponible, se mantiene el último valor, señalado como desactualizado; sin ningún valor previo, el indicador queda fuera y su dimensión no puntúa.",
    revisiones: "El INDEC puede revisar los porcentajes de meses anteriores al ampliarse la muestra respondente. Cada actualización recalcula la serie completa desde el origen, de modo que las revisiones se incorporan solas.",
    cambios: [
      { fecha: "2026-07-19", cambio: "Entra al cinturón como primer indicador de la nueva dimensión de sector privado. Una revisión externa del cinturón señaló que de los tres actores que el índice se propone medir —legisladores, gobernadores y empresarios— el tercero no tenía ningún indicador propio." },
      { fecha: "2026-07-20", cambio: "Al revisar el efecto de la incorporación sobre la validación externa del índice apareció que este indicador se comporta de manera distinta según el gobierno: acompaña a la incertidumbre de política económica con las dos administraciones anteriores y se invierte con la actual. Se decidió mantenerlo puntuando y publicar el hallazgo, en lugar de retirarlo o de reducir su peso para que el número diera mejor. La explicación completa quedó en las limitaciones de esta ficha." },
    ],
  },

  apoyo_empresario: {
    tipo: "indicador",
    id: "apoyo_empresario",
    cinturon: "politica",
    rezago: "Ninguno en la fuente: los comunicados se publican el día en que la cámara los emite. El retraso es el de la clasificación, que hace una persona.",
    fuente: {
      organismo: "Asociación Empresaria Argentina (AEA) y Unión Industrial Argentina (UIA)",
      operacion: "Comunicados institucionales fechados de las secciones de prensa de ambas entidades",
      url: "https://www.uia.org.ar/uia/novedades",
      acceso: "Semiautomático: un proceso diario detecta los comunicados nuevos y los deja pendientes; la clasificación de cada uno la hace una persona.",
    },
    transformaciones: [
      "Cada comunicado se clasifica en dos ejes, con reglas escritas antes de mirar el material: qué dice sobre lo que comenta —respalda, critica o no toma posición— y a quién le habla, que puede ser el Gobierno nacional, el Congreso, una provincia o municipio, la Justicia, o un asunto externo o de la propia entidad.",
      "Sólo entran al cálculo los comunicados dirigidos al Gobierno nacional que respaldan o critican. Los que informan una reunión, un acto institucional, un cambio de autoridades o una condolencia no toman posición y quedan afuera aunque hablen del Gobierno, y también quedan afuera los dirigidos a los otros poderes.",
      "El indicador es el saldo de los últimos doce meses: apoyos menos críticas, dividido por el total. Va de −1, si todo fue crítica, a +1 si todo fue apoyo.",
      "Un mes sin ningún comunicado que se pronuncie sobre el Gobierno nacional queda sin valor y no se rellena con cero: cero significa que las cámaras apoyaron tanto como criticaron, que es una afirmación distinta de que no se pronunciaron. En los treinta y dos meses de serie no ocurrió: el mínimo es de tres pronunciamientos por ventana y el promedio, de casi seis.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del saldo, interpolado entre anclas: +0,6 o más → el más alto; entre +0,2 y +0,6 → alto; entre −0,2 y +0,2 → moderado; entre −0,6 y −0,2 → bajo; menos de −0,6 → el más bajo. Las anclas parten en cinco tramos iguales el rango teórico del indicador y se centran en el cero, que es el valor con significado propio: saldo nulo quiere decir que el Gobierno no tiene ni respaldo ni enfrentamiento netos del empresariado organizado.",
      "Pesa la mitad de la dimensión de sector privado del índice del cinturón (13% del total). La otra mitad es la brecha de expectativas entre obra pública y obra privada. El reparto es parejo porque miden cosas distintas y ninguna domina a la otra: la brecha es una medida revelada —lo que las empresas esperan, con dato duro del INDEC— pero de un solo sector; ésta es una medida declarada —lo que las cámaras dicen y firman— directa sobre la relación con el Gobierno y sobre cualquier tema, pero de sólo dos entidades.",
    ],
    limitaciones: [
      "Mide lo que una asociación decidió declarar en público, no el humor del empresariado ni la opinión de sus asociados. Una cámara puede callar por conveniencia, y ese silencio no aparece en ninguna parte del indicador.",
      "Son dos entidades. Se revisaron ocho cámaras y sólo estas dos publican comunicados de postura de manera sostenida: el resto publica agenda institucional, servicios al socio o boletines regulatorios, y dos no tienen contenido accesible. Eso deja fuera al agro y a la banca, que en el país tienen conflictos propios con el Estado.",
      "La clasificación la hace una persona, y por eso el indicador no puede actualizarse solo. Un proceso diario avisa cuando hay comunicados nuevos, pero si nadie los clasifica la serie se congela sin que nada falle: por eso la cantidad de pendientes se muestra en la ficha del indicador.",
      "Para verificar que las reglas de clasificación no dejan lugar a la interpretación, dos codificadores independientes clasificaron por separado los ciento tres comunicados sin ver el trabajo del otro: coincidieron en el cien por ciento de las posturas y en el noventa y siete por ciento de los destinatarios, y el conjunto de comunicados que entran al cálculo resultó idéntico. Cabe una advertencia sobre esa prueba: ambos codificadores son sistemas de inteligencia artificial del mismo tipo, que comparten criterios previos y por lo tanto coinciden más de lo que coincidirían dos personas de formación distinta. La prueba acredita que el manual es unívoco, no que cualquier par de lectores llegaría al mismo número.",
      "La ventana de doce meses hace que el indicador describa, en promedio, la situación de seis meses atrás. Un giro brusco en la relación —como el de marzo de 2026— tarda en verse completo.",
      "Los comunicados de AEA se leen de archivos PDF cuyo texto se extrae con un corte en los primeros párrafos. En los comunicados que abren con un rodeo y recién después fijan posición, esa extracción puede dejar afuera el pasaje decisivo.",
    ],
    faltantes: "Si los sitios de las cámaras no responden, el indicador no cambia: se calcula sobre el registro ya clasificado, que está guardado. Lo que se pierde es el aviso de comunicados nuevos.",
    revisiones: "El registro de clasificación está versionado caso por caso: cualquier corrección queda a la vista con su fecha y recalcula la serie completa desde el origen.",
    cambios: [
      { fecha: "2026-07-27", cambio: "Entra al cinturón como segundo indicador de la dimensión de sector privado, que hasta ahora tenía uno solo. Una revisión externa había señalado que los empresarios eran el actor peor medido del cinturón." },
      { fecha: "2026-07-27", cambio: "Al verificar la clasificación con dos codificadores independientes se descubrió que los cincuenta y siete comunicados de la Unión Industrial se habían leído sin su texto: el proceso de descarga se quedaba con el menú de navegación del sitio y esos casos se habían clasificado sólo por el título. Se corrigió la descarga y se rehízo la clasificación completa sobre el texto real, descartando la primera. El hallazgo no vino de ninguna verificación automática sino de que los dos codificadores, por separado, avisaron que los textos venían todos iguales." },
    ],
  },

  ratio_dnu: {
    tipo: "indicador",
    id: "ratio_dnu",
    cinturon: "politica",
    rezago: "InfoLeg carga las normas al ritmo del Boletín Oficial: días entre la publicación y su aparición en el buscador.",
    fuente: {
      organismo: "InfoLeg (Ministerio de Justicia)",
      operacion: "Buscador oficial de normas — conteo de decretos de necesidad y urgencia y de leyes sancionadas en los últimos 365 días",
      url: "https://servicios.infoleg.gob.ar/infolegInternet/",
      acceso: "Automático: consulta el buscador oficial con dos búsquedas (leyes y decretos con el texto «necesidad y urgencia», ambas acotadas a los últimos 365 días) y toma los conteos de resultados.",
    },
    transformaciones: [
      "Ratio = DNU dictados en los últimos 365 días / leyes sancionadas en los últimos 365 días — ventana móvil, no acumulado del año calendario.",
      "Los DNU se identifican buscando la frase «necesidad y urgencia» dentro de los decretos.",
      "La serie histórica recalcula esta misma ventana móvil al cierre de cada mes desde diciembre de 2023: cada punto es homogéneo y comparable con el anterior, sin el reseteo de un acumulado que arranca de cero cada enero.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del ratio, interpolado entre anclas: 0,3 o menos → el más alto; entre 0,3 y 0,7 → alto; entre 0,7 y 1,2 → moderado; entre 1,2 y 2 → bajo; más de 2 → el más bajo. Estas anclas están ancladas a la práctica histórica 2011-2024 (cuatro presidencias distintas): en promedio, una de cada tres leyes sancionadas tuvo un DNU — ratio ≈0,3.",
      "Integra la dimensión de poder legislativo del índice del cinturón (25% del total), donde pesa 20% junto a la eficacia legislativa, las sesiones caídas por quórum, las derrotas legislativas y el bloqueo sostenido.",
    ],
    limitaciones: [
      "Responde a la pregunta «¿cuánto depende el Gobierno del decreto?», no a «¿le funciona gobernar por decreto?». Cabe la lectura inversa —un Ejecutivo que decreta con éxito está avanzando su plan pese a no tener acompañamiento legislativo—, y el indicador no la mide: un ratio alto baja el puntaje aunque los decretos sigan vigentes. Se eligió la primera lectura porque el cinturón mide capital político en el sentido de capacidad sostenible de gobernar, y la norma dictada por decreto es reversible por el Congreso y por los tribunales de un modo en que la ley no lo es.",
      "Los datos respaldan que la dependencia sea una vulnerabilidad real y no una objeción teórica, pero también que sea latente: de los 162 decretos de necesidad y urgencia dictados desde diciembre de 2023, el 95% nunca se votó en el recinto y por lo tanto sigue vigente; de los ocho que sí se votaron, seis cayeron. El 7 de agosto de 2025 cayeron cinco en un solo día.",
      "Identificar DNU por la frase «necesidad y urgencia» es una aproximación: puede contar de más o de menos.",
      "Depende del formulario del buscador oficial: un rediseño del sitio lo interrumpe hasta adaptarlo.",
      "El buscador no expone un listado con fecha por norma: reconstruir la serie mensual exige una consulta separada por mes, no una descarga única.",
    ],
    faltantes: "Si la consulta falla, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "Los conteos se reconsultan completos en cada actualización: si la fuente carga normas con retraso, el número se corrige solo.",
    cambios: [
      { fecha: "2026-05", cambio: "Entra al cinturón en reemplazo del índice de confianza en el gobierno (UTDT): el cinturón mide capacidad de gobernar, no popularidad." },
      { fecha: "2026-06-30", cambio: "Serie anual desde 2020 para dar contexto histórico al ratio del año en curso." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
      { fecha: "2026-07-19", cambio: "Se explicita en la ficha qué pregunta responde el indicador y cuál es la lectura contraria, a pedido de una revisión externa del cinturón. El cálculo y las anclas no cambian. Se evaluó además incorporar un indicador separado de éxito de ejecución por decreto y se descartó con datos: como el 95% de los decretos nunca se vota, esa medida quedaría permanentemente cerca del 100% y no distinguiría nada." },
      { fecha: "2026-07-15", cambio: "El cociente pasó de acumulado del año calendario (un punto por año, reseteaba en enero) a ventana móvil de 365 días (un punto por mes, comparable mes a mes). Las anclas del puntaje NO cambiaron: siguen ancladas a la práctica histórica 2011-2024, no al rango observado bajo esta gestión." },
    ],
  },

  conflictividad_nacional: {
    tipo: "indicador",
    id: "conflictividad_nacional",
    cinturon: "politica",
    rezago: "El agregado de ACLED se publica semanalmente y los eventos más recientes se cargan con algunos días de rezago; por eso el mes en curso se excluye del cálculo hasta que cierra.",
    fuente: {
      organismo: "ACLED — Armed Conflict Location & Event Data",
      operacion: "Agregado semanal de eventos por provincia para América Latina — eventos de protesta y disturbios (Protests y Riots) en la Argentina",
      url: "https://acleddata.com",
      acceso: "Automático: descarga el archivo agregado semanal con la cuenta académica del proyecto y suma los eventos de las 24 jurisdicciones. Atribución: datos de ACLED.",
    },
    transformaciones: [
      "Suma los eventos de protesta y disturbios de todo el país, mes a mes.",
      "Acumula los últimos 12 meses completos (el mes en curso se excluye hasta que cierra, porque el registro se carga con rezago).",
      "El indicador es la variación porcentual de ese acumulado contra el total del año 2023, la línea de base del mandato: negativo = menos conflicto en la calle que en 2023.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas de la variación, interpolado entre anclas: −32% o menos → el más alto; entre −32% y −29% → alto; entre −29% y −26% → moderado; entre −26% y −15% → bajo; más de −15% → el más bajo. Los umbrales se calibraron con la serie mensual real del indicador (30 meses, dic-2023 en adelante, rango observado −34% a +3%): las cinco bandas tienen meses reales observados.",
      "Es el único indicador de la dimensión de conflicto social del índice del cinturón (12% del total).",
    ],
    limitaciones: [
      "Cuenta eventos, no personas: una marcha multitudinaria y una concentración chica pesan igual — es una medida de frecuencia del conflicto, no de su masividad.",
      "La base de comparación es fija (el total de 2023): a medida que pasa el tiempo, la referencia envejece — el mismo criterio declarado que usa el índice de impacto social con su base de fin de 2023.",
      "La cobertura de ACLED para la Argentina es confiable desde 2020; los años anteriores registran menos eventos por expansión de la propia cobertura, no por menor conflictividad — por eso ni las bandas ni el gráfico usan datos previos a la base.",
      "Depende de la cobertura de prensa que releva ACLED: eventos sin cobertura periodística no entran al registro.",
    ],
    faltantes: "Si la descarga semanal falla, se usa el último archivo ya guardado (el indicador se marca desactualizado si el registro queda más de 30 días atrás); sin archivo, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "ACLED revisa y completa semanas recientes en cada publicación; el acumulado de 12 meses se recalcula completo desde el archivo en cada actualización y absorbe esas revisiones automáticamente.",
    cambios: [
      { fecha: "2026-07-11", cambio: "Incorporado como la medida de la dimensión de conflicto social: eventos de protesta y disturbios de todo el país. Reemplaza a la medición anterior basada en los informes de CEPA, que no permitía una serie mensual comparable." },
    ],
  },

  iaf_transferencias: {
    tipo: "indicador",
    id: "iaf_transferencias",
    cinturon: "politica",
    rezago: "Por diseño compara el último año cerrado contra el anterior: durante 2026 se lee «2025 contra 2024» — el dato puede tener hasta un año de rezago.",
    fuente: {
      organismo: "Ministerio de Economía (Secretaría de Hacienda); deflactor: INDEC",
      operacion: "Serie RON — recursos de origen nacional transferidos a las provincias (archivo anual oficial), deflactada con el IPC nacional",
      serie: "serie_ron_2003_2025.csv · deflactor IPC vía API de Series de Tiempo (datos.gob.ar)",
      url: "https://www.argentina.gob.ar/sites/default/files/serie_ron_2003_2025.csv",
      acceso: "Automático: descarga el archivo oficial y deflacta con el IPC del INDEC obtenido por API.",
    },
    transformaciones: [
      "Suma las transferencias efectivamente giradas a las 24 jurisdicciones durante el año de referencia y durante el año anterior — es ejecución, no presupuesto: la fila de un año es lo que la Nación transfirió ese año calendario. El archivo oficial también distribuye recursos al Tesoro Nacional, a la Seguridad Social y al Fondo ATN; esas porciones no son transferencias a provincias y quedan excluidas (con la exclusión, el nivel anual coincide con los informes fiscales de referencia).",
      "La variación nominal se deflacta por la inflación promedio anual (promedio del índice IPC del año contra el promedio del año anterior): el resultado es la variación real interanual. El promedio —y no la punta diciembre contra diciembre— es el deflactor correcto para sumas anuales de flujos, porque las transferencias se devengan mes a mes a los precios de cada mes; es el mismo criterio que usan los análisis fiscales de referencia.",
      "En el gráfico, cada punto anual se ubica en diciembre del año que cierra: el valor fechado en diciembre de 2025 es la variación del año 2025 completo contra 2024.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas de la variación real, interpolado entre anclas: más de +10% → el más alto; entre 0% y +10% → alto; entre −10% y 0% → moderado; entre −20% y −10% → bajo; −20% o menos → el más bajo.",
      "Integra la dimensión de alianzas territoriales del índice del cinturón (22% del total), donde pesa 40% junto al 30% del alineamiento de senadores por provincia y el 30% de la adhesión provincial al RIGI.",
    ],
    limitaciones: [
      "Granularidad anual: no capta la tensión federal dentro del año.",
      "El nombre del archivo oficial cambia cada año: hay que apuntar la descarga de nuevo cada enero.",
      "Mide el flujo fiscal hacia las provincias — una aproximación parcial a la relación política con los gobernadores.",
      "La serie cubre las transferencias automáticas (coparticipación neta, financiamiento educativo, leyes especiales y compensaciones del Consenso Fiscal); no incluye los giros discrecionales —las transferencias no automáticas—, que otros informes agregan por separado.",
    ],
    faltantes: "Si la descarga falla, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "Se recalcula completo desde la fuente en cada actualización: revisiones del archivo oficial o del IPC se absorben automáticamente.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida de la armonía fiscal entre la Nación y las provincias." },
      { fecha: "2026-06-30", cambio: "El deflactor pasó de una proyección fija al índice IPC oficial del INDEC: la variación real publicada se corrigió de +1,8% a +7,0%." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de alianzas territoriales — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
      { fecha: "2026-07-15", cambio: "El deflactor pasó de la variación diciembre contra diciembre a la inflación promedio anual, el criterio correcto para sumas anuales de flujos y el que usan los análisis fiscales de referencia — con inflación en baja, la punta de diciembre subdeflactaba: la variación real de 2025 se corrigió de +7,0% a un valor en línea con los informes externos (~0/+2% real)." },
      { fecha: "2026-07-15", cambio: "Se excluyeron del cálculo las porciones del archivo oficial que no son transferencias a provincias (Tesoro Nacional, Seguridad Social, Fondo ATN): el nivel anual pasó a coincidir con los informes fiscales de referencia (~$60 billones en 2025) y la variación quedó medida solo sobre lo que efectivamente reciben las jurisdicciones." },
    ],
  },

  eficacia_legislativa: {
    tipo: "indicador",
    id: "eficacia_legislativa",
    cinturon: "politica",
    rezago: "El portal de datos abiertos de Diputados carga proyectos y movimientos con días o semanas de demora respecto del hecho parlamentario.",
    fuente: {
      organismo: "HCDN — Cámara de Diputados de la Nación",
      operacion: "Datasets «proyectos parlamentarios» y «leyes sancionadas» del portal oficial de datos abiertos",
      serie: "API portal de datos abiertos de datos.hcdn.gob.ar",
      url: "https://datos.hcdn.gob.ar",
      acceso: "Automático: API pública del portal, cruzando los proyectos de ley enviados por el Ejecutivo con el registro oficial de leyes sancionadas (que cubre las sanciones de ambas cámaras).",
    },
    transformaciones: [
      "Identifica los proyectos de ley enviados por el Poder Ejecutivo por su número de expediente — tanto los de la Presidencia como los de la Jefatura de Gabinete, la vía por la que entra siempre el Presupuesto anual — y por su tipo de trámite: las comunicaciones administrativas (avisos de vetos, resoluciones, decisiones administrativas), que llevan numeración similar pero no son proyectos, quedan fuera del denominador.",
      "Toma una cohorte MADURA: proyectos enviados entre hace 12 y 24 meses — ya tuvieron al menos un año de margen para tramitarse antes de evaluarlos.",
      "Un proyecto de esa cohorte cuenta como aprobado si figura en el registro oficial de leyes sancionadas, sin importar en qué cámara ocurrió la sanción definitiva ni cuándo.",
      "El indicador es aprobados sobre el total de esa cohorte — ya no exige que envío y sanción caigan en la misma ventana.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del porcentaje aprobado, interpolado entre anclas: más de 50% → el más alto; entre 30% y 50% → alto; entre 15% y 30% → moderado; entre 5% y 15% → bajo; 5% o menos → el más bajo. Los umbrales se calibraron contra series históricas de otras gestiones (proporción de proyectos del Ejecutivo que se convirtieron en ley), no contra el rango de esta gestión.",
      "Integra la dimensión de poder legislativo del índice del cinturón (25% del total), donde pesa 25% junto al ratio DNU, las sesiones caídas por quórum, las derrotas legislativas y el bloqueo sostenido.",
    ],
    limitaciones: [
      "Al exigir un año de margen antes de contar un proyecto, el indicador reporta sobre una cohorte de hace 12 a 24 meses, no sobre el año corriente — es menos inmediato a cambio de no castigar a los proyectos recién enviados.",
      "Un trámite que supera los 24 meses nunca llega a contarse dentro de su cohorte: la ventana captura la mediana y el tramo alto de las duraciones observadas, pero los trámites excepcionalmente largos quedan fuera por construcción.",
      "Denominador chico: con unos quince a veinte proyectos por cohorte, uno solo mueve varios puntos porcentuales.",
      "Cuenta proyectos por igual, sin ponderar su peso político.",
      "La serie histórica es reproducible: si un proyecto se sanciona después de publicado un punto de la serie, ese punto no se corrige retroactivamente (aunque el indicador vigente sí lo refleje al recorrer la fuente completa).",
    ],
    faltantes: "Si la consulta falla, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "La serie completa se regenera desde la fuente en cada actualización.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida de la capacidad de convertir la agenda de gobierno en ley." },
      { fecha: "2026-06-30", cambio: "Serie mensual de ventanas móviles de 12 meses desde diciembre de 2023." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
      { fecha: "2026-07-11", cambio: "Umbrales de puntaje recalibrados contra la serie mensual real del indicador (32 meses): los anteriores describían la tasa de aprobación de un congreso teórico y dejaban el puntaje en el mínimo casi todos los meses, sin discriminar. Se documenta además que, por construcción de la ventana única de 12 meses, el techo alcanzable del porcentaje es más bajo que una tasa de aprobación de manual." },
      { fecha: "2026-07-15", cambio: "Se reemplazó la ventana compartida entre envío y sanción por una cohorte madura (proyectos con 12-24 meses de margen) — elimina el sesgo hacia abajo que la ventana compartida introducía. Los umbrales de puntaje se recalibraron contra series históricas de otras gestiones en vez de contra el rango de esta." },
      { fecha: "2026-07-15", cambio: "Corrección de fuentes: la aprobación pasa a verificarse contra el registro oficial de leyes sancionadas (que cubre las sanciones definitivas del Senado, antes invisibles), y las comunicaciones administrativas del Ejecutivo dejan de contar como proyectos enviados." },
      { fecha: "2026-07-15", cambio: "Se incorporaron los proyectos enviados por la Jefatura de Gabinete — la vía constitucional del Presupuesto anual, que hasta ahora quedaba fuera del conteo en ambas direcciones (ni el Presupuesto 2025 sin aprobar contaba como fracaso, ni el 2026 aprobado contaría como éxito al madurar su camada)." },
    ],
  },

  cohesion_bloque: {
    tipo: "indicador",
    id: "cohesion_bloque",
    cinturon: "politica",
    rezago: "Los portales de votaciones nominales de las dos cámaras registran cada sesión a los pocos días de ocurrida; el informe recalcula el promedio de los últimos 90 días en cada actualización.",
    fuente: {
      organismo: "Cámara de Diputados y Senado de la Nación",
      operacion: "Votaciones nominales de ambas cámaras — bloque propio de La Libertad Avanza, actas divididas de los últimos 90 días",
      url: "https://votaciones.hcdn.gob.ar",
      acceso: "Automático: lectura directa de los portales públicos de votaciones nominales de Diputados y del Senado; sin carga manual del analista.",
    },
    transformaciones: [
      "Para cada acta con al menos un voto a favor o en contra del bloque propio de La Libertad Avanza (se excluyen deliberadamente los bloques aliados de nombre ambiguo, para no inflar la cohesión medida con votos que no son del oficialismo propiamente dicho), calcula qué tan pareja o dispareja fue esa votación puertas adentro: resta los votos a favor menos los votos en contra, toma el valor absoluto y lo divide por el total de votos que emitió el bloque en esa acta.",
      "Por cámara, el cálculo es el promedio de esa cuenta en las actas divididas de los últimos 90 días. Abstenciones y ausencias no entran.",
      "El indicador publicado es el compuesto bicameral: Diputados pesa 65% y el Senado 35% — el mismo reparto que las dos cámaras tenían cuando eran indicadores separados. Si una cámara no tiene dato (por ejemplo, receso sin actas divididas), el peso se reparte sobre la que sí lo tiene; la composición por cámara se publica en el detalle de la card.",
    ],
    incidenciaTexto: [
      "Mide qué tan unido vota el bloque oficialista puertas adentro de las dos cámaras — no si acompaña una «posición oficial», algo que no puede observarse de forma independiente. Si en una votación casi todo el bloque va junto en el mismo sentido (a favor o en contra), la cohesión es alta; si el bloque se parte en partes similares, la cohesión es baja.",
      "El puntaje del índice se asigna por bandas del compuesto, interpolado entre anclas: más de 99,9% → el más alto; entre 99% y 99,9% → alto; entre 97% y 99% → moderado; entre 95% y 97% → bajo; 95% o menos → el más bajo. Los umbrales se calibraron contra la serie mensual del propio compuesto (dic-2023 en adelante, rango observado 90,3–100): las cinco bandas tienen meses reales observados.",
      "Es el único indicador de la dimensión de cohesión interna del oficialismo del índice del cinturón (18% del total).",
    ],
    limitaciones: [
      "Solo cuenta al bloque propio de LLA: deja afuera a los aliados de bloques separados, una decisión declarada para no inflar la cohesión medida con votos ajenos al oficialismo propiamente dicho.",
      "Las dos cámaras tienen sensibilidad distinta: el bloque de Diputados es grande (un disidente mueve poco el promedio) y el del Senado es chico (un solo voto disidente lo mueve con fuerza). El compuesto pondera esa asimetría (65/35) pero no la elimina — la composición por cámara se publica para poder leerla.",
      "No distingue ausencias de abstenciones: ambas quedan fuera del cálculo igual que si el legislador no hubiera votado.",
      "Depende de que los portales públicos mantengan su estructura actual: un cambio de diseño puede interrumpir la lectura automática hasta que se ajuste.",
      "Con pocas actas divididas en la ventana de 90 días, un solo voto conflictivo mueve el promedio con fuerza.",
    ],
    faltantes: "Si la lectura de uno de los portales falla, se conserva el último promedio calculado de esa cámara y el compuesto se arma igual; recién se marca desactualizado si ninguna cámara tuvo una actualización que llegara a su portal en más de 10 días — un receso legislativo sin actas nuevas no cuenta como desactualización.",
    revisiones: "El promedio de los últimos 90 días se recalcula completo desde las fuentes en cada actualización; no se arrastran promedios previos.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón como estimación manual, a la espera de una fuente estructurada de votaciones vigente." },
      { fecha: "2026-07-07", cambio: "Deja de ser una estimación manual: pasa a calcularse en forma automática desde las votaciones nominales de Diputados, con una definición observable — qué tan pareja o dispareja es la votación interna del bloque propio, acta por acta." },
      { fecha: "2026-07-09", cambio: "Serie histórica mensual del gráfico y umbrales de puntaje recalibrados contra las series reconstruidas de cada cámara (29 a 31 meses reales)." },
      { fecha: "2026-07-10", cambio: "Revisión editorial del cinturón: las dos cámaras se fusionan en este único indicador bicameral (Diputados 65%, Senado 35% — el reparto que ya tenían como indicadores separados), con umbrales recalibrados contra la serie mensual del compuesto (99,9/99,0/97,0/95,0). La serie del gráfico pasa a ser la del compuesto." },
    ],
  },

  alineamiento_senadores_prov: {
    tipo: "indicador",
    id: "alineamiento_senadores_prov",
    cinturon: "politica",
    rezago: "El portal de votaciones nominales del Senado registra cada sesión a los pocos días de ocurrida; el informe recalcula el promedio de los últimos 90 días en cada actualización.",
    fuente: {
      organismo: "Senado de la Nación",
      operacion: "Votaciones nominales del Senado — coincidencia de senadores no alineados con la posición del bloque de La Libertad Avanza, por provincia, actas de los últimos 90 días",
      url: "https://www.senado.gob.ar/votaciones/actas",
      acceso: "Automático: lectura directa del portal público de votaciones nominales del Senado; sin carga manual.",
    },
    transformaciones: [
      "Para cada acta, determina la posición del bloque de La Libertad Avanza (el sentido en el que votó la mayoría de sus senadores). Si el bloque queda empatado, esa acta no aporta señal.",
      "Para cada provincia, mide qué proporción de los votos de sus senadores QUE NO son del bloque LLA coincidió con esa posición. Las provincias donde los 3 senadores son de LLA quedan fuera del cálculo: su coincidencia sería automática por definición, no aporta información.",
      "El indicador es el promedio simple de esa proporción entre todas las provincias con al menos un senador no-LLA, sobre las actas de los últimos 90 días.",
    ],
    incidenciaTexto: [
      "Reemplaza, desde julio de 2026, a un indicador de carga manual (\"alineamiento de gobernadores\") que quedó congelado por meses sin una fuente pública estructurada para actualizarlo — dos rondas de búsqueda de fuentes automatizables no encontraron ninguna que midiera directamente la postura del Poder Ejecutivo provincial.",
      "Caveat importante: este indicador mide comportamiento de voto de SENADORES, no la postura pública del gobernador de la provincia — un senador no depende del gobernador de turno, puede responder a la estrategia nacional de su propio partido. Es la mejor señal automatizable disponible hoy, no una medición directa del Poder Ejecutivo provincial.",
      "El puntaje del índice se asigna por bandas de ese porcentaje, interpolado entre anclas: más de 70% de coincidencia → el más alto; entre 60% y 70% → alto; entre 50% y 60% → moderado; entre 40% y 50% → bajo; 40% o menos → el más bajo. Los umbrales se calibraron con la serie mensual reconstruida del propio indicador (feb-2024 en adelante).",
      "Integra la dimensión de alianzas territoriales del índice del cinturón (22% del total), donde pesa 30% junto al 40% de las transferencias federales y el 30% de adhesión al RIGI.",
    ],
    limitaciones: [
      "Proxy de comportamiento legislativo, no medición directa de la postura del gobernador (Poder Ejecutivo provincial) — ver caveat arriba.",
      "Incluye votaciones consensuadas (donde todo el Senado vota en el mismo sentido), no solo las genuinamente disputadas — solo se excluyen las actas donde el propio bloque LLA queda internamente empatado.",
      "Bloque LLA chico en el Senado: pocos senadores propios hacen que su 'posición' en un acta dependa de muy pocos votos.",
      "Depende de que el portal público del Senado mantenga su estructura actual: un cambio de diseño del sitio puede interrumpir la lectura automática hasta que se ajuste.",
    ],
    faltantes: "Si la lectura del sitio falla, se conserva el último promedio calculado; recién se marca desactualizado si pasan más de 10 días sin una actualización que haya llegado al portal — un receso legislativo sin actas nuevas no cuenta como desactualización.",
    revisiones: "El promedio de los últimos 90 días se recalcula completo desde la fuente en cada actualización; no se arrastran promedios previos.",
    cambios: [
      { fecha: "2026-07-08", cambio: "Alta como reemplazo de \"alineamiento de gobernadores\" (indicador de carga manual, sin fuente automatizable encontrada): mide coincidencia de voto de senadores no oficialistas con la posición del bloque de gobierno, por provincia." },
      { fecha: "2026-07-09", cambio: "Umbrales de puntaje recalibrados (antes 65/45/25/10, heredados de \"alineamiento de gobernadores\" sin validar) a partir de una serie mensual propia reconstruida (29 meses reales, feb-2024 a jun-2026): nuevos cortes en 70/60/50/40." },
    ],
  },

  adhesion_reformas_provincial: {
    tipo: "indicador",
    id: "adhesion_reformas_provincial",
    cinturon: "politica",
    rezago: "La tabla de provincias adheridas se actualiza en el sitio oficial apenas una provincia formaliza su adhesión; el informe la relee completa en cada actualización.",
    fuente: {
      organismo: "Ministerio de Agricultura, Ganadería y Pesca (MAGyP)",
      operacion: "Tabla de provincias adheridas al Régimen de Incentivo para Grandes Inversiones (RIGI, Título VII de la Ley 27.742)",
      url: "https://www.magyp.gob.ar/desarrollo-foresto-industrial/provincias-adheridas.php",
      acceso: "Automático: lectura directa de la tabla publicada en el sitio del MAGyP.",
    },
    transformaciones: [
      "Cuenta cuántas de las 24 jurisdicciones del país (23 provincias y la Ciudad de Buenos Aires) figuran en la tabla oficial como adheridas al RIGI.",
      "El indicador es ese conteo sobre 24, expresado en porcentaje.",
    ],
    incidenciaTexto: [
      "Mide adhesión a un régimen fiscal y de promoción de inversiones puntual, no el alineamiento político general de una provincia con la Nación — eso lo mide, con otro método, el indicador de alineamiento de senadores por provincia. Una provincia puede adherir al RIGI por conveniencia fiscal aun con un gobernador crítico del gobierno nacional, y a la inversa.",
      "El puntaje del índice se asigna por bandas del porcentaje adherido, interpolado entre anclas: más de 80% de jurisdicciones adheridas → el más alto; entre 60% y 80% → alto; entre 40% y 60% → moderado; entre 20% y 40% → bajo; menos de 20% → el más bajo. Los umbrales se chequearon contra la serie histórica real del indicador (24 meses, jul-2024 a jun-2026): a diferencia de otros indicadores del cinturón, no se recalibraron — la adhesión es un evento irreversible por jurisdicción, así que el rango observado hoy es el arranque de un proceso todavía en curso, no una muestra representativa contra la cual fijar anclas permanentes.",
      "Integra la dimensión de alianzas territoriales del índice del cinturón (22% del total), donde pesa 30% junto al 40% de las transferencias federales y el 30% del alineamiento de senadores por provincia.",
    ],
    limitaciones: [
      "Cuenta la adhesión formal, no la inversión efectiva que esa adhesión termina generando en cada provincia.",
      "Es una tabla acumulativa: una vez que una provincia adhiere no se espera que salga de la lista, así que el indicador solo sube o queda estable — no capta marchas atrás.",
      "El sitio fuente tiene una fila vacía mal formada que puede duplicar el nombre de una provincia al leer la tabla; no altera el conteo final porque cada provincia se cuenta una sola vez.",
    ],
    faltantes: "Si la consulta al sitio falla, el indicador queda fuera de esa actualización y el puntaje del cinturón se calcula con los indicadores disponibles.",
    revisiones: "La tabla completa se relee de la fuente en cada actualización; no se acumulan lecturas parciales.",
    cambios: [
      { fecha: "2026-07-07", cambio: "Alta como indicador de la dimensión de alianzas territoriales: mide adhesión fiscal al RIGI, distinta del alineamiento político general que ya capta el indicador de gobernadores." },
      { fecha: "2026-07-09", cambio: "Serie histórica mensual del gráfico: la fecha de adhesión de cada provincia se documentó una por una contra el Boletín Oficial provincial (u otra fuente oficial equivalente)." },
    ],
  },

  gobernadores_alineamiento: {
    tipo: "indicador",
    id: "gobernadores_alineamiento",
    cinturon: "politica",
    rezago: "Se actualiza cuando el analista carga una estimación nueva; a los 45 días el dato se marca como desactualizado.",
    fuente: {
      organismo: "Elaboración CIGOB",
      operacion: "Estimación cualitativa del analista — carga manual declarada",
      acceso: "Carga manual: no existe una fuente pública estructurada del alineamiento político de los 24 gobernadores.",
    },
    transformaciones: [
      "Porcentaje de gobernadores con posición pública de acompañamiento al programa nacional (acuerdos fiscales, apoyo a reformas), evaluado por el analista.",
    ],
    anclas: {
      bandas: [
        { banda: "> 65", puntaje: 100 },
        { banda: "45 – 65", puntaje: 85 },
        { banda: "25 – 45", puntaje: 65 },
        { banda: "10 – 25", puntaje: 40 },
        { banda: "≤ 10", puntaje: 10 },
      ],
      puntos: [[0, 10], [10, 40], [25, 65], [45, 85], [65, 100]],
      unidadCorta: "% alineados",
    },
    incidenciaTexto: [
      "La tensión crece cuando el apoyo se retira, por las bandas de la tabla y no de forma lineal: con 80% de gobernadores alineados la tensión es 0, con 40% es 3,0 y con 0% llega a 9,0 — el tramo más bajo puntúa 10 sobre 100, no cero, porque perder a todos los gobernadores no agota la capacidad de gobierno.",
      "El score del cinturón es el promedio simple de las tensiones de los indicadores disponibles.",
    ],
    limitaciones: [
      "Estimación cualitativa no replicable por un lector externo: se publica identificada como tal.",
      "Podría construirse con análisis sistemático de declaraciones en prensa, pero es un proyecto aparte.",
      "El valor entra al promedio del cinturón aunque esté vencido, marcado como desactualizado.",
    ],
    faltantes: "Si no hay valor cargado, el indicador queda fuera y el score del cinturón promedia los presentes.",
    revisiones: "Solo cambia con una nueva carga del analista.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón como estimación manual: la relación con los gobernadores es una dimensión del capital político sin fuente estructurada." },
      { fecha: "2026-07-08", cambio: "Retirado del peso del índice: reemplazado por alineamiento_senadores_prov, un proxy automatizable de comportamiento de voto legislativo por provincia. Esta ficha queda como referencia histórica." },
    ],
  },

  veto_quorum: {
    tipo: "indicador",
    id: "veto_quorum",
    cinturon: "politica",
    rezago: "El portal de datos abiertos de Diputados registra las sesiones a los días de ocurridas.",
    fuente: {
      organismo: "HCDN — Cámara de Diputados de la Nación",
      operacion: "Dataset «sesiones» (sesiones plenarias) del portal oficial de datos abiertos",
      serie: "API portal de datos abiertos de datos.hcdn.gob.ar",
      url: "https://datos.hcdn.gob.ar",
      acceso: "Automático: API pública del portal, filtrando las sesiones de Diputados del período legislativo en curso.",
    },
    transformaciones: [
      "Una sesión cuenta como caída cuando el registro oficial la clasifica «en minoría»: fue convocada, esperó —unas dos horas en promedio— y nunca llegó a constituirse, por lo que no recibió número de sesión. Las que sí se constituyen duran alrededor de doce horas y llevan número.",
      "El denominador son las sesiones convocadas para tratar temas: las especiales, sus continuaciones y las que quedaron en minoría. Quedan afuera las informativas, la sesión preparatoria y la presentación del presupuesto, instancias donde el oficialismo no necesita reunir quórum para avanzar su agenda.",
      "Se calcula sobre los últimos doce meses calendario, no por período legislativo. El período reiniciaba el conteo cada marzo, de modo que durante buena parte del año el indicador se apoyaba en dos o tres sesiones.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del porcentaje de sesiones caídas, interpolado entre anclas: 5% o menos → el más alto; entre 5% y 10% → alto; entre 10% y 20% → moderado; entre 20% y 30% → bajo; más de 30% → el más bajo.",
      "Integra la dimensión de poder legislativo del índice del cinturón (25% del total), donde pesa 15% junto al ratio DNU, la eficacia legislativa, los desafíos legislativos y el bloqueo sostenido.",
    ],
    limitaciones: [
      "Las sesiones desactivadas antes de la convocatoria formal no aparecen en el registro oficial: el indicador subestima el bloqueo.",
      "El denominador sigue siendo modesto —entre doce y dieciséis sesiones en la ventana—, así que cada sesión caída mueve varios puntos porcentuales. Es una mejora sobre el conteo por período legislativo, que llegó a apoyarse en cinco sesiones, pero conviene leer el indicador por su tendencia y no por su valor exacto de un mes.",
      "No distingue el quórum frustrado por la oposición de la inasistencia propia — decisión metodológica declarada.",
    ],
    faltantes: "Si la consulta falla, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "El dataset se reconsulta completo en cada actualización.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida del bloqueo parlamentario." },
      { fecha: "2026-06-30", cambio: "Serie por período legislativo desde 2024." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
      { fecha: "2026-07-20", cambio: "Corrección de fondo del criterio de conteo, a partir de una revisión de los registros crudos del dataset oficial. La versión anterior identificaba las sesiones caídas buscando la palabra «fracasada» en el tipo de reunión, lo que dejaba fuera las once sesiones clasificadas «en minoría» —que son el fracaso de quórum propiamente dicho— y en cambio contaba dos sesiones informativas del artículo 71 de la Constitución que no se realizaron, un fenómeno distinto. La ventana pasó además de período legislativo a doce meses móviles, y la serie de anual a mensual." },
    ],
  },

  derrotas_legislativas: {
    tipo: "indicador",
    id: "derrotas_legislativas",
    cinturon: "politica",
    rezago: "InfoLeg incorpora decretos y leyes el día de su publicación en el Boletín Oficial; el Senado publica sus actas de votación a los días de cada sesión. Una insistencia se registra con la publicación de la ley en el Boletín Oficial, que llega dos a tres semanas después del voto de la segunda cámara.",
    fuente: {
      organismo: "InfoLeg (Ministerio de Justicia) + Senado de la Nación",
      operacion: "Base de legislación nacional (decretos de observación total o parcial y leyes promulgadas por insistencia) + actas de votación nominal del Senado (tratamientos de decretos bajo la ley 26.122)",
      url: "https://servicios.infoleg.gob.ar/infolegInternet/",
      acceso: "Automático: se buscan los vetos en el buscador oficial de InfoLeg y se filtran las actas del Senado por la fórmula «en los términos de la ley 26.122», contando los votos para clasificar rechazo o aprobación. Cada derrota queda documentada con su fecha, acta y fuente.",
    },
    transformaciones: [
      "Un veto cuenta como derrota cuando ambas cámaras insisten la ley con dos tercios de los votos y la ley se promulga pese al veto (art. 83 de la Constitución); se fecha en el mes en que la insistencia se completa.",
      "Un decreto —de necesidad y urgencia, delegado o de promulgación parcial— cuenta como derrota cuando al menos una cámara lo rechaza en el recinto bajo la ley 26.122; se fecha en el mes del primer rechazo. El rechazo de una sola cámara no deroga el decreto (hace falta el de ambas), pero es una derrota política consumada y así se cuenta.",
      "Cada norma cuenta una sola vez: el segundo rechazo de un decreto (el que consuma la derogación) no suma un evento nuevo.",
      "El indicador es la suma de derrotas de los últimos 12 meses calendario (ventana móvil).",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 1", puntaje: 100 },
        { banda: "1 – 3", puntaje: 85 },
        { banda: "3 – 8", puntaje: 65 },
        { banda: "8 – 14", puntaje: 40 },
        { banda: "> 14", puntaje: 10 },
      ],
      puntos: [[1, 100], [2, 85], [5.5, 65], [11, 40], [14, 10]],
      unidadCorta: "derrotas 12m",
    },
    incidenciaTexto: [
      "Los umbrales se calibraron contra la serie mensual del indicador desde diciembre de 2023: el período va de meses sin ninguna derrota hasta el pico de ocho en doce meses, tras la ola de rechazos e insistencias de agosto-octubre de 2025. Las dos bandas más bajas quedan por encima de todo lo observado: son el margen para escenarios de confrontación más intensos que los ya vistos.",
      "Integra la dimensión de poder legislativo del índice del cinturón (25% del total), donde pesa 20% junto al ratio DNU, la eficacia legislativa, las sesiones caídas por quórum y el bloqueo sostenido — su contracara: éste cuenta las normas caídas, aquél acredita las sostenidas. Menos derrotas = puntaje más alto.",
    ],
    limitaciones: [
      "Es un indicador de eventos raros con ventana móvil: el valor puede saltar varios enteros de un mes al siguiente, tanto cuando ocurre una tanda de derrotas como —en espejo— doce meses después, cuando esa tanda sale de la ventana. El movimiento de salida es mecánico (aritmética de la ventana), no una mejora política nueva; el detalle de la card publica la composición del conteo para leerlo con contexto.",
      "Un conteo de cero informa ausencia de derrotas, no necesariamente dominio del Ejecutivo: también puede reflejar que no hubo vetos ni tratamientos de decretos en juego en el período (menos confrontación, no más control).",
      "La detección automática de rechazos de decretos mira las actas del Senado: un rechazo que ocurra primero en Diputados se registra recién cuando el Senado también lo vota (o con una corrección manual del registro). En el período histórico eso habría corrido la fecha de cinco decretos apenas dos semanas, sin alterar el conteo anual.",
      "Las insistencias se fechan por la publicación de la ley en el Boletín Oficial, no por el voto de la segunda cámara: una insistencia votada sobre el fin de mes puede registrarse al mes siguiente. En los tres casos reales del período ambos hechos cayeron en el mismo mes.",
      "Mide derrotas consumadas en el recinto; los amagues que no llegan a votarse (sesiones sin quórum para rechazar un decreto, insistencias que no reúnen los dos tercios) no cuentan — las sesiones fracasadas las captura, con otro método, el indicador de sesiones caídas por quórum.",
    ],
    faltantes: "Si las fuentes fallan, se mantiene el último valor disponible, señalado como desactualizado; el registro de eventos preserva todo el pasado, así que una caída de fuente solo retrasa la detección de eventos nuevos.",
    revisiones: "Los eventos consumados son inmutables (una insistencia no se des-insiste; un rechazo no se des-vota). Los vetos con insistencia incompleta se re-verifican en cada actualización: media insistencia pendiente no caduca y puede completarse en cualquier momento — si eso ocurre, el evento nuevo se fecha en el mes en que se complete, sin reescribir el histórico.",
    cambios: [
      { fecha: "2026-07-09", cambio: "Incorporado al cinturón político: ningún otro indicador capturaba las insistencias de vetos ni los rechazos de decretos en el recinto. Serie mensual completa desde diciembre de 2023." },
    ],
  },

  bloqueo_sostenido: {
    tipo: "indicador",
    id: "bloqueo_sostenido",
    cinturon: "politica",
    rezago: "Las cámaras publican sus actas de votación a los días de cada sesión; el clasificador incorpora las actas nuevas en la actualización nocturna siguiente. La caída de un veto se registra con la publicación de la ley insistida en el Boletín Oficial, dos a tres semanas después del voto de la segunda cámara.",
    fuente: {
      organismo: "Cámara de Diputados + Senado de la Nación + InfoLeg (Ministerio de Justicia)",
      operacion: "Actas de votación nominal de ambas cámaras (insistencias de leyes vetadas y tratamientos de decretos bajo la ley 26.122) + base de legislación nacional (decretos de veto, leyes promulgadas por insistencia)",
      url: "https://votaciones.hcdn.gob.ar",
      acceso: "Automático: se leen las actas de votación de ambas cámaras y se identifica, en cada una, si se trató la insistencia de un veto o el control de un decreto, y cómo salió la votación. Los casos ambiguos quedan en una cola de revisión manual; nunca se infiere el sentido de una votación. El registro de eventos se comparte con el indicador de derrotas legislativas.",
    },
    transformaciones: [
      "Una norma queda DESAFIADA desde su primera votación en el recinto, gane quien gane: la insistencia de una ley vetada (art. 83 de la Constitución) o el control de un decreto bajo la ley 26.122.",
      "Sigue EN PIE mientras la insistencia no se complete en ambas cámaras (el veto se sostiene con un tercio de una sola) y mientras el decreto no sea rechazado por las dos (el rechazo de una sola cámara no lo deroga, como al DNU 70/2023).",
      "El indicador es el porcentaje de normas desafiadas en los últimos 12 meses calendario que seguían en pie al cierre del mes: cada punto histórico evalúa el estado a esa fecha, así que una caída posterior no reescribe los meses ya publicados.",
      "Los vetos sin insistencia votada y los decretos que ninguna cámara trató no entran al denominador: sin desafío no hay prueba del bloqueo.",
    ],
    anclas: {
      bandas: [
        { banda: "≥ 90", puntaje: 100 },
        { banda: "75 – 90", puntaje: 85 },
        { banda: "50 – 75", puntaje: 60 },
        { banda: "25 – 50", puntaje: 35 },
        { banda: "< 25", puntaje: 10 },
      ],
      puntos: [[95, 100], [82.5, 85], [62.5, 60], [37.5, 35], [20, 10]],
      unidadCorta: "% en pie",
    },
    incidenciaTexto: [
      "Los umbrales usan una referencia externa, no el rango propio del período: entre 2003 y 2025 el Congreso no logró revertir ningún veto presidencial —ni siquiera frente a los gobiernos en minoría—, así que sostener el 90% o más de lo desafiado es el dominio histórico normal del bloqueo; por debajo del 25%, el Ejecutivo perdió la llave del tercio. El período cubierto recorre casi todo el rango: 100% en el primer semestre de 2024, 75% tras la caída del decreto de fondos reservados, 33% tras la ola de insistencias y derogaciones de agosto-octubre de 2025, y el mínimo en 2026, cuando la ventana móvil todavía carga esa ola pero los desafíos sostenidos más viejos ya salieron de ella.",
      "Integra la dimensión de poder legislativo del índice del cinturón (25% del total), donde pesa 20% junto a la eficacia parlamentaria, el ratio DNU, las derrotas legislativas y las sesiones caídas por quórum. Es la contracara de las derrotas: aquéllas cuentan las normas caídas en términos absolutos; éste acredita también las sostenidas. Más es mejor.",
    ],
    limitaciones: [
      "La ventana de 12 meses retiene las caídas durante un año: la recuperación del bloqueo después de una crisis aparece con rezago mecánico, incluso si el Congreso nuevo dejó de desafiar normas (los desafíos viejos salen de la ventana doce meses después, no antes).",
      "Un período sin desafíos votados no genera dato (sin denominador no hay tasa): el indicador queda fuera ese mes y los pesos de su dimensión se renormalizan — ausencia de desafíos puede ser dominio de agenda o simple falta de confrontación, y el indicador no distingue entre ambas.",
      "Con pocos desafíos en ventana la tasa se mueve a saltos grandes (un desafío sobre cuatro son 25 puntos): es un indicador de eventos raros, como las derrotas legislativas.",
      "La moción estándar de la comisión bicameral sobre un decreto es su rechazo; el caso raro de un dictamen de aprobación (una vez en el período: el acuerdo con el FMI) se detecta por el texto del motivo y queda para clasificación manual — la dirección de una moción ambigua nunca se adivina.",
      "Las actas de Diputados se incorporan con la actualización nocturna: un acta publicada hoy se clasifica al día siguiente.",
    ],
    faltantes: "Si las actas o InfoLeg fallan, se mantiene el último valor disponible, señalado como desactualizado; el histórico ya clasificado se preserva, así que una caída de fuente solo retrasa la detección de votaciones nuevas.",
    revisiones: "Las votaciones consumadas son inmutables. Los vetos con media insistencia pendiente se re-verifican en cada actualización (no caducan): si la segunda cámara completa la insistencia, la norma pasa a caída desde ese mes en adelante — los puntos históricos ya publicados no se reescriben, porque cada uno evalúa el estado al cierre de su propio mes.",
    cambios: [
      { fecha: "2026-07-16", cambio: "Incorporado como la cara ganada del pulso legislativo: los vetos sostenidos y la supervivencia de decretos no puntuaban en ningún indicador (el conteo de derrotas solo registra las normas caídas). Serie mensual desde marzo de 2024." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // Espíritu de época — un único indicador puntuable (intención migratoria,
  // jul-2026); los tres proxies iniciales (clima electoral, y los icc_utdt/
  // sentimiento_digital compartidos con vida) quedaron como seguimiento
  // interno, fuera del tablero y del score
  // ═══════════════════════════════════════════════════════════════════════

  // ═══════════════════════════════════════════════════════════════════════
  // Gestión — indicadores del ITCG
  // ═══════════════════════════════════════════════════════════════════════
  cepo_mulc: {
    tipo: "indicador",
    id: "cepo_mulc",
    cinturon: "gestion",
    rezago: "Sin rezago: cotizaciones del día; la serie mensual usa promedios.",
    fuente: {
      organismo: "dolarapi.com (agregador de cotizaciones; el mayorista replica la referencia oficial A3500 del BCRA)",
      operacion: "Cotizaciones del dólar contado con liquidación (CCL) y del mayorista; brecha porcentual entre ambos",
      url: "https://dolarapi.com/v1/dolares",
      acceso: "Automático: API pública de cotizaciones; la serie histórica se reconstruye con el CCL promedio del mes sobre el mayorista promedio.",
    },
    transformaciones: [
      "Brecha = (CCL − mayorista) / mayorista × 100.",
      "Se usa el mayorista y no el minorista de pizarra: el minorista incluye el margen bancario y subestima la brecha.",
      "Cerca de 0% = mercado cambiario unificado de hecho: el cepo dejó de morder.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 5", puntaje: 100 },
        { banda: "5 – 10", puntaje: 85 },
        { banda: "10 – 15", puntaje: 65 },
        { banda: "15 – 25", puntaje: 40 },
        { banda: "> 25", puntaje: 10 },
      ],
      puntos: [[5, 100], [7.5, 85], [12.5, 65], [20, 40], [25, 10]],
      unidadCorta: "%",
    },
    limitaciones: [
      "La fuente es un agregador privado, no un organismo oficial (el mayorista replica la referencia oficial).",
      "Mide el cepo por su precio (la brecha que paga quien no accede al mercado oficial), no el stock regulatorio de restricciones.",
      "El valor de la card es el spot del día; la serie usa promedios mensuales — difieren de forma inmaterial, declarado.",
    ],
    faltantes: "Si la API falla, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Cotizaciones cerradas, sin revisión; el punto del mes corriente se recalcula a diario.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial del indicador sobre la brecha CCL/oficial minorista, en la escala de avance del cinturón anterior." },
      { fecha: "2026-07-02", cambio: "Entra al ITCG con umbrales institucionales sobre la brecha CCL/mayorista." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas. Además, la brecha deja de puntuar una segunda vez dentro del compuesto de apertura comercial: puntúa una sola vez, acá." },
    ],
  },

  apertura_comercial: {
    tipo: "indicador",
    id: "apertura_comercial",
    cinturon: "gestion",
    rezago: "El titular usa el último mes común entre cinco series oficiales con rezagos distintos: ~2 meses.",
    fuente: {
      organismo: "ARCA (recaudación de derechos) + INDEC (intercambio comercial) + BCRA (tipo de cambio)",
      operacion: "Alícuota efectiva del comercio exterior: derechos de exportación e importación recaudados sobre el intercambio total",
      serie: "142.3_DEREC_2001_M_20 y _26 (derechos) · 74.3_IET_0_M_16 y 74.3_IIT_0_M_25 (ICA) · API BCRA (A3500 promedio)",
      url: "https://www.afip.gob.ar/institucional/estudios/",
      acceso: "Automático: APIs públicas de series de tiempo y del BCRA.",
    },
    transformaciones: [
      "Alícuota = derechos de exportación + importación (convertidos a dólares por el tipo de cambio oficial promedio del mes) sobre el intercambio total (exportaciones + importaciones).",
      "Lectura llana: cuántos centavos de impuesto paga cada dólar comerciado. 0% = libre comercio; 15% del intercambio ≈ cierre comercial de hecho.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ 1", puntaje: 100 },
        { banda: "1 – 3,5", puntaje: 85 },
        { banda: "3,5 – 7", puntaje: 65 },
        { banda: "7 – 11", puntaje: 40 },
        { banda: "> 11", puntaje: 10 },
      ],
      puntos: [[1, 100], [2.25, 85], [5.25, 65], [9, 40], [11, 10]],
      unidadCorta: "%",
    },
    limitaciones: [
      "Mide la fricción arancelaria efectiva, no las barreras no arancelarias.",
      "El «canal verde» aduanero (parte del diseño institucional original) sigue sin fuente pública estructurada y no se mide.",
      "Depende del mes común entre cinco series con rezagos distintos.",
    ],
    faltantes: "Si falta un insumo, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Las series oficiales pueden revisarse; la serie propia se recalcula completa en cada actualización.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como variación interanual de importaciones (aproximación de apertura)." },
      { fecha: "2026-07-02", cambio: "Pasa a un compuesto de liberalización (brecha cambiaria + alícuota) con el ITCG." },
      { fecha: "2026-07-03", cambio: "Queda la alícuota efectiva sola: la brecha cambiaria ya puntuaba como indicador propio y el compuesto la hacía pesar dos veces en la dimensión. Las anclas se eligieron sobre la recta del documento (0% → 100 · 15% → 0)." },
    ],
  },

  desregulacion_normativa: {
    tipo: "indicador",
    id: "desregulacion_normativa",
    cinturon: "gestion",
    rezago: "El ministerio publica el informe de cada mes durante las primeras semanas del siguiente (~1 mes).",
    fuente: {
      organismo: "Ministerio de Desregulación y Transformación del Estado — Unidad de Evaluación de Impacto",
      operacion: "Análisis de la desregulación implementada, informe mensual — artículos de normas modificados o eliminados, acumulados desde el 10 de diciembre de 2023",
      url: "https://www.argentina.gob.ar/desregulacion/desregulacion-en-numeros",
      acceso: "Automático: se leen los enlaces de la página oficial y se extrae la cifra de portada de cada informe en PDF. Los nombres de archivo son irregulares, de modo que los enlaces se resuelven leyendo la página y nunca se arman a mano. Cada informe publicado se conserva, porque su contenido no cambia.",
    },
    transformaciones: [
      "El informe publica tres cifras: cuántas normas de desregulación se dictaron, cuántas normas anteriores alcanzaron y cuántos artículos quedaron modificados o eliminados. El indicador usa la tercera; las otras dos se muestran en la card como contexto.",
      "Se eligió el recuento de artículos porque las normas no son equivalentes entre sí: un decreto que reescribe quinientos artículos y una resolución que toca uno cuentan igual si se cuentan normas, y muy distinto si se cuentan artículos. Es la misma objeción que señaló la revisión externa del cinturón.",
      "El valor del mes es la cifra que el propio informe publica; no hay recálculo del proyecto.",
      "El período se toma de la fecha de corte del informe («al 31 de octubre de 2025»), no del mes de su tapa: hay informes cuya portada dice un mes y cuyo corte cae en el siguiente.",
      "La serie histórica hasta abril de 2026 se reconstruyó midiendo las barras del gráfico de artículos acumulados que publica el informe, porque ese gráfico es la única fuente oficial con detalle mes a mes desde diciembre de 2023. La medición se calibró con la cifra del mismo informe y se contrastó contra los otros nueve informes, que son independientes de ese gráfico.",
    ],
    anclas: {
      bandas: [
        { banda: "> 30.000", puntaje: 100 },
        { banda: "15.000 – 30.000", puntaje: 85 },
        { banda: "7.000 – 15.000", puntaje: 60 },
        { banda: "2.500 – 7.000", puntaje: 35 },
        { banda: "≤ 2.500", puntaje: 10 },
      ],
      puntos: [[2500, 10], [4750, 35], [11000, 60], [22500, 85], [30000, 100]],
      unidadCorta: "artículos",
    },
    limitaciones: [
      "Es el Gobierno midiendo su propio programa. El criterio de qué norma cuenta como «de desregulación», y por lo tanto qué artículos se computan, lo fija el ministerio responsable, y no hay un tercero que lo audite. Es la contrapartida de usar la cifra oficial en lugar de una reconstrucción propia.",
      "La escala de referencia es una convención del proyecto. El ministerio publica el recuento pero no declara ninguna meta, así que el punto en que la desregulación se considera completa lo fijamos nosotros. Conviene leer el indicador por su evolución más que por su nivel absoluto. Se evaluó reemplazar esa convención por una división contra el stock de normas vigentes, y se descartó: el recuento del ministerio incluye resoluciones, mientras que el stock disponible de normas nacionales vigentes de alcance general está compuesto sólo por leyes y decretos, de modo que los dos universos no son comparables.",
      "Contar artículos corrige la equivalencia entre normas de peso muy distinto, pero no la resuelve del todo: un artículo que libera un mercado entero sigue contando igual que uno que ajusta una definición.",
      "El ministerio revisa su serie hacia atrás, y lo ha hecho de forma sustantiva. El informe publica la versión corregida y es la que se usa, del mismo modo que se usa la última revisión de una serie estadística.",
      "La serie anterior a abril de 2026 proviene de la medición de un gráfico y no de cifras publicadas como texto. El contraste contra los nueve informes que publican su total arroja coincidencia exacta en cinco casos y una diferencia máxima de cuarenta y cinco artículos sobre una serie que supera los dieciséis mil, es decir alrededor de tres décimas de punto porcentual.",
      "Es un recuento normativo, no una auditoría del efecto económico de lo desregulado.",
    ],
    faltantes: "Si el informe del mes todavía no salió o el PDF no se puede leer, se mantiene el último valor disponible, señalado como desactualizado; sin ningún valor previo, el peso se redistribuye entre los otros indicadores de la dimensión.",
    revisiones: "El ministerio revisa su serie hacia atrás. El informe conserva cada publicación y toma siempre la última cifra oficial de cada mes.",
    cambios: [
      { fecha: "2026-05", cambio: "Automatizado desde el inicio del cinturón con la misma búsqueda, en escala lineal." },
      { fecha: "2026-07-02", cambio: "Umbrales institucionales del ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-20", cambio: "Cambio de unidad, a partir de una revisión externa del cinturón. El indicador contaba las normas cuyo texto mencionaba una derogación en cualquier parte del documento, y cerca de la mitad de lo contado no derogaba nada: eran normas que en sus considerandos referían la derogación hecha por otra. Ahora se lee la parte dispositiva y se cuentan las normas efectivamente derogadas. Se corrigió además una afirmación equivocada de esta misma ficha, que sostenía que el decreto de necesidad y urgencia de diciembre de 2023 no figuraba en la fuente: sí figura, y siempre estuvo contado, aunque pesaba como una sola norma pese a derogar treinta y ocho." },
      { fecha: "2026-07-25", cambio: "Cambio de fuente, a propuesta de la revisión externa del cinturón. El indicador dejó de construirse con un conteo propio sobre la base de legislación y pasó a publicar la cifra oficial del Ministerio de Desregulación y Transformación del Estado, que es el organismo que conduce el programa. La serie histórica se reconstruyó completa desde diciembre de 2023. El puntaje se movió de setenta y dos a setenta y tres: cambió de dónde sale el número, no el resultado." },
    ],
  },

  reduccion_estado: {
    tipo: "indicador",
    id: "reduccion_estado",
    cinturon: "gestion",
    rezago: "La serie de dotación se publica con ~2 meses de rezago; los últimos meses aparecen imputados y se revisan.",
    fuente: {
      organismo: "INDEC + Secretaría de Transformación del Estado",
      operacion: "Dotación de personal del Estado nacional (serie mensual). La planilla abre el total en dos universos: la Administración Pública Nacional y las empresas y sociedades del Estado; este indicador usa el primero",
      serie: "Planilla oficial serie_dotacion_apn.xlsx, cuadro 1, fila «Administración pública nacional» — que agrupa la administración centralizada, la descentralizada, la desconcentrada y otros entes, y NO incluye las empresas del Estado",
      url: "https://www.indec.gob.ar/indec/web/Institucional-Indec-empleoAPN",
      acceso: "Automático: lectura de la planilla oficial.",
    },
    transformaciones: [
      "Variación porcentual de la dotación contra la línea de base de diciembre de 2023 (231.305 agentes).",
      "A diferencia de las series previsionales, excluye provincias y municipios: es la métrica insignia de la reforma del Estado nacional.",
      "También excluye a las empresas y sociedades del Estado, que la planilla informa por separado. Se eligió la Administración Pública Nacional porque es el universo sobre el que el Poder Ejecutivo decide directamente su planta. La elección no cambia la lectura: al mes de mayo de 2026 la Administración Pública Nacional cae 19,8%, las empresas del Estado 20,2% y el universo completo 19,9%.",
      "Sí incluye a las fuerzas armadas y de seguridad. Siete entidades informan su dotación dentro de la Administración Pública Nacional: los estados mayores del Ejército, la Armada, la Fuerza Aérea y el Estado Mayor Conjunto, más Gendarmería, Prefectura y la Policía de Seguridad Aeroportuaria. Representan alrededor del diez por ciento del total y se redujeron menos que el resto, de modo que su presencia atenúa levemente el ajuste medido: a febrero de 2026 el conjunto cae 18,6% y la planta civil sola 19,0%. No se las descuenta —son parte del Estado y sostener sus dotaciones también es una decisión de gobierno—, pero el desglose se publica en la card para que cada lector pueda hacer la cuenta que prefiera.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −12", puntaje: 100 },
        { banda: "−12 – −8", puntaje: 85 },
        { banda: "−8 – −4", puntaje: 65 },
        { banda: "−4 – 0", puntaje: 40 },
        { banda: "> 0", puntaje: 10 },
      ],
      puntos: [[-12, 100], [-10, 85], [-6, 65], [-2, 40], [0, 10]],
      unidadCorta: "% vs dic-2023",
    },
    dobleUso: "Mide personas; el costo de la nómina lo miden por separado el gasto de funcionamiento y la masa salarial — tres patas complementarias declaradas de la misma dimensión.",
    limitaciones: [
      "Los meses recientes vienen imputados y el INDEC los revisa hacia atrás.",
      "Las bandas se calibraron a mano contra el recorte observado (~10-12% → banda alta): es una convención propia del proyecto y no una meta oficial.",
      "Mide personas, no costo. La reducción de la planta puede convivir con un gasto salarial que no baje en la misma proporción, y por eso el cinturón sigue ambas cosas por separado.",
    ],
    faltantes: "Con la planilla caída, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "La fuente revisa los meses imputados en cada publicación; la serie propia se relee completa en cada actualización.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial sobre la serie previsional trimestral, con meta de largo plazo." },
      { fecha: "2026-07-02", cambio: "Pasa a la planilla mensual de dotación APN contra diciembre de 2023, con umbrales del ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  gasto_funcionamiento: {
    tipo: "indicador",
    id: "gasto_funcionamiento",
    cinturon: "gestion",
    rezago: "Las series de gasto se publican con ~2 meses de rezago.",
    fuente: {
      organismo: "Secretaría de Hacienda; deflactor: INDEC",
      operacion: "Gastos de funcionamiento del Estado nacional (salarios + otros gastos), variación real contra el mismo mes de 2023",
      serie: "452.2_SALARIOSIOS_0_T_8_22 + 452.2_OTROS_GASTNTO_0_T_27_55 + IPC 148.3_INIVELNAL_DICI_M_26 · API de datos.gob.ar",
      url: "https://www.presupuestoabierto.gob.ar/",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Total = salarios + otros gastos de funcionamiento.",
      "Variación real del último mes contra el mismo mes de 2023, deflactada por IPC: comparar el mismo mes aísla a la vez la inflación y la estacionalidad de los aguinaldos.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −25", puntaje: 100 },
        { banda: "−25 – −15", puntaje: 85 },
        { banda: "−15 – −5", puntaje: 65 },
        { banda: "−5 – 0", puntaje: 40 },
        { banda: "> 0", puntaje: 10 },
      ],
      puntos: [[-25, 100], [-20, 85], [-10, 65], [-2.5, 40], [0, 10]],
      unidadCorta: "% real vs 2023",
    },
    dobleUso: "Su componente de salarios se solapa conceptualmente con la masa salarial (fuente distinta): el marco las trata como patas complementarias — ninguna sola alcanza.",
    limitaciones: [
      "Bandas calibradas a mano contra el ajuste 2024, un episodio históricamente atípico.",
      "La base caja/devengado de Hacienda está sujeta a reclasificaciones presupuestarias.",
    ],
    faltantes: "Si falta un insumo, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Series revisables por el publicador; la serie propia se recalcula entera en cada actualización.",
    cambios: [
      { fecha: "2026-07-02", cambio: "Indicador nuevo, creado con el ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  masa_salarial: {
    tipo: "indicador",
    id: "masa_salarial",
    cinturon: "gestion",
    rezago: "Las series de gasto se publican con ~2 meses de rezago.",
    fuente: {
      organismo: "Secretaría de Hacienda (base caja); deflactor: INDEC",
      operacion: "Remuneraciones del Sector Público Nacional, variación real contra el mismo mes de 2023",
      serie: "379.9_GTOS_CORR_017__49_26 + IPC 148.3_INIVELNAL_DICI_M_26 · API de datos.gob.ar",
      url: "https://www.presupuestoabierto.gob.ar/",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Variación real contra el mismo mes de 2023, deflactada por IPC — la misma mecánica que el gasto de funcionamiento.",
      "Complementa a la dotación con el costo real: distingue el achicamiento genuino de la licuación nominal por inflación.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −20", puntaje: 100 },
        { banda: "−20 – −12", puntaje: 85 },
        { banda: "−12 – −5", puntaje: 65 },
        { banda: "−5 – 0", puntaje: 40 },
        { banda: "> 0", puntaje: 10 },
      ],
      puntos: [[-20, 100], [-16, 85], [-8.5, 65], [-2.5, 40], [0, 10]],
      unidadCorta: "% real vs 2023",
    },
    dobleUso: "Solapamiento conceptual declarado con el componente de salarios del gasto de funcionamiento (fuentes distintas, misma dimensión).",
    limitaciones: [
      "Base caja: el calendario de pagos puede desalinear meses.",
      "Comparte el deflactor con el gasto de funcionamiento: un error del IPC mueve a los dos a la vez.",
      "Desde agosto de 2026 no integra el ITCG: CIGOB pidió sacarlo del cálculo por dudas sobre la forma de exponer estos datos, hasta tener certeza de las afirmaciones que permiten sostener. La card se sigue publicando con su valor mensual — ver ADR-0186.",
    ],
    faltantes: "Si falta un insumo, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Series revisables por el publicador; recalculada entera en cada actualización.",
    cambios: [
      { fecha: "2026-07-02", cambio: "Indicador nuevo, creado con el ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-08-09", cambio: "Sale del cálculo del ITCG a pedido de CIGOB (dudas sobre la exposición de la fuente); la dimensión reforma_estado renormaliza sus pesos 35/25/20 → 43,75/31,25/25 entre los tres indicadores que quedan. La card se mantiene. Ver ADR-0186." },
    ],
  },

  reestructuracion_organismos: {
    tipo: "indicador",
    id: "reestructuracion_organismos",
    cinturon: "gestion",
    rezago: "Sin rezago: conteo al día de la actualización.",
    fuente: {
      organismo: "InfoLeg (Ministerio de Justicia)",
      operacion: "Conteo de normas nacionales publicadas desde diciembre de 2023 cuyo texto contiene «disolución», filtrado caso por caso contra un registro curado",
      url: "https://servicios.infoleg.gob.ar/infolegInternet/",
      acceso: "InfoLeg como descubrimiento (mismo mecanismo que la desregulación) + un registro curado que clasifica cada hallazgo: cuenta, no cuenta por ser ajeno a un organismo público, o no cuenta por haber sido revertido.",
    },
    transformaciones: [
      "Avance = actos de disolución o cierre VIGENTES de organismos públicos, sobre un plan de 45 (calibración declarada). No cuenta fusiones, transformaciones ni centralizaciones —difíciles de verificar caso por caso, CIGOB pidió (ago-2026) hablar solo de disolución o cierre— y desde agosto de 2026 tampoco cuenta un hallazgo de texto que no sea, caso por caso, el cierre vigente de un organismo público (ADR-0188): de los 18 documentos que la búsqueda encontraba, 11 pasan el filtro (24,4% de avance); los otros 7 quedan excluidos con su motivo documentado.",
    ],
    anclas: {
      bandas: [
        { banda: "> 80", puntaje: 100 },
        { banda: "60 – 80", puntaje: 85 },
        { banda: "40 – 60", puntaje: 65 },
        { banda: "20 – 40", puntaje: 40 },
        { banda: "≤ 20", puntaje: 10 },
      ],
      puntos: [[20, 10], [30, 40], [50, 65], [70, 85], [80, 100]],
      unidadCorta: "% de avance",
    },
    limitaciones: [
      "El megadecreto 70/2023 no aparece en la búsqueda de texto: solo captura los actos posteriores.",
      "La calibración (originalmente 18 = 40%, 45 = plan completo) es una decisión propia validada a mano y declarada; el 45 no cambió, el numerador sí (ver el cambio de agosto de 2026 abajo).",
      "El 45 (plan completo) se fijó en mayo de 2026 contra una estimación manual descripta en ese momento como \"decretos de disolución/fusión de organismos\" — un universo más amplio que el que la etiqueta de este indicador afirma medir desde agosto de 2026. Se revisó (agosto de 2026) si había una cifra mejor: ni la Ley Bases, ni el Ministerio de Desregulación, ni la prensa publican un objetivo de organismos a cerrar en la misma unidad que este indicador mide (normas, no organismos), así que el 45 se mantiene como convención declarada, no corregida — el detalle de la búsqueda está en ADR-0185.",
      "Una búsqueda de texto por sí sola no distingue de qué habla la norma: de los 18 documentos que \"disolución\" encontraba, 3 eran ajenos a un organismo público (el procedimiento de disolución de sociedades y asociaciones civiles privadas, la disolución de una obra social sindical privada, y un producto de limpieza llamado \"Cloro Granulado Disolución Rápida\") y 4 eran actos de un paquete de decretos (461/2025 y 462/2025) que el Congreso rechazó en agosto de 2025 y quedaron abrogados — esos organismos siguen existiendo. Los 7 se excluyen, cada uno con su motivo y su norma (ADR-0188).",
      "Si InfoLeg indexa una norma nueva con \"disolución\" que todavía nadie clasificó caso por caso, esa norma NO se suma al avance: la corrida la deja afuera y lo avisa, en vez de contarla sin revisar (que es exactamente el defecto que corrigió agosto de 2026) o descartarla en silencio.",
    ],
    faltantes: "Con el buscador caído, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "El acumulado se reevalúa completo en cada actualización.",
    cambios: [
      { fecha: "2026-05", cambio: "Automatizado desde el inicio del cinturón con la misma búsqueda." },
      { fecha: "2026-07-02", cambio: "Umbrales institucionales del ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-08-09", cambio: "Etiqueta y descripción precisadas a pedido de CIGOB: se habla solo de disolución o cierre, no de fusión/transformación/centralización. El cálculo no cambió — la búsqueda en InfoLeg siempre fue solo «disolución». Ver ADR-0185." },
      { fecha: "2026-08-09", cambio: "Se buscó una cifra mejor que 45 para el denominador (Ley Bases, Ministerio de Desregulación, prensa) y ninguna resultó viable; el 45 se mantiene, ahora documentado en detalle. Ver ADR-0185." },
      { fecha: "2026-08-09", cambio: "El conteo pasa de 18 a 11 (avance de 40,0% a 24,4%; ITCG de 78,7 a 76,8): la lectura caso por caso que pidió CIGOB encontró que 3 de los 18 documentos no hablaban de un organismo público y 4 eran actos de un paquete de decretos que el Congreso rechazó y quedaron sin efecto. InfoLeg sigue siendo la fuente de descubrimiento, pero cada hallazgo se contrasta ahora contra un registro curado con motivo y norma; lo que todavía nadie clasificó no cuenta y la corrida lo avisa. Ver ADR-0188." },
    ],
  },

  fal_modernizacion_laboral: {
    tipo: "indicador",
    id: "fal_modernizacion_laboral",
    cinturon: "gestion",
    rezago: "Sin rezago: las dos normas están publicadas y fechadas.",
    fuente: {
      organismo: "InfoLeg — Ley 27.802 y Decreto 408/2026",
      operacion: "Actos fundamentales del Fondo de Asistencia Laboral: sanción de la ley (50%) + reglamentación del Poder Ejecutivo (50%)",
      url: "https://www.infoleg.gob.ar/",
      acceso: "Registro versionado de hitos normativos, cada uno fechado y respaldado por una norma publicada, verificable por número en InfoLeg. Los fondos registrados en la Comisión Nacional de Valores y las menciones del instrumento en el Boletín Oficial se siguen relevando automáticamente y se muestran como contexto de la ficha, pero no inciden en el puntaje.",
    },
    transformaciones: [
      "El indicador mide los dos actos que ponen en pie al Fondo, cincuenta puntos cada uno: la Ley 27.802 de Modernización Laboral, con la que el Congreso instauró el Fondo (publicada el 6 de marzo de 2026), y el Decreto 408/2026, con el que el Poder Ejecutivo reglamentó el Título II (publicado el 1 de junio de 2026). Los dos están cumplidos.",
      "El criterio es que, con la ley sancionada y reglamentada, el Gobierno agotó lo que podía cumplir de la promesa hasta que el régimen entre en vigencia el 1 de noviembre de 2026, fecha fijada por el artículo 27 del decreto reglamentario.",
      "La serie mensual se reconstruye con la misma regla desde diciembre de 2023: cero hasta febrero de 2026, cincuenta desde marzo cuando se sanciona la ley, cien desde junio cuando se publica la reglamentación.",
    ],
    anclas: {
      bandas: [
        { banda: "> 75", puntaje: 100 },
        { banda: "25 – 75", puntaje: 50 },
        { banda: "≤ 25", puntaje: 10 },
      ],
      puntos: [[25, 10], [50, 50], [75, 100]],
      unidadCorta: "actos cumplidos (0-100)",
    },
    dobleUso: "La litigiosidad laboral puntúa como indicador aparte de la misma dimensión: par instrumento (este) / resultado (aquella), sin doble conteo.",
    limitaciones: [
      "El indicador dice que las bases quedaron puestas, no que el Fondo funcione. Son cosas distintas y conviene no leerlas como si fueran la misma: un Gobierno puede sancionar y reglamentar una ley que después nadie use. Por eso la dimensión de reforma laboral mide además el resultado —la litigiosidad— con un indicador aparte y del mismo peso.",
      "Los dos actos ya ocurrieron y no pueden deshacerse, de modo que el valor queda fijo en cien y ningún hecho futuro lo mueve: ni la entrada en vigencia del régimen ni que el instrumento se use o no. Es una limitación seria y asumida —el indicador dejó de discriminar— y obliga a rediseñarlo cuando el régimen empiece a regir.",
      "Es una medida de cumplimiento formal de la promesa, no de su efecto. La versión anterior componía construcción, vigencia y adopción para mantener recorrido; se reemplazó por decisión editorial, a propuesta de la revisión externa del cinturón, y el cambio mejoró el puntaje del indicador. Queda dicho para que se pueda discutir.",
    ],
    faltantes: "No aplica: las dos normas están publicadas y el registro es local. El contexto que viene de la Comisión Nacional de Valores y del Boletín Oficial puede faltar sin afectar el puntaje.",
    revisiones: "El registro de hitos se reverifica contra InfoLeg por número de norma; la serie se reconstruye entera en cada corrida.",
    cambios: [
      { fecha: "2026-07-20", cambio: "Pasa a medirse en tres etapas —construcción normativa, vigencia y adopción— a partir de una revisión externa del cinturón, que observó que el indicador informaba un valor cercano a cero por una razón de cronograma legal y no de gestión: medía la adopción de un instrumento que todavía no podía adoptarse. Con la escala anterior el valor era 0,4 sobre 100; con la nueva es 40,2, que corresponde a un instrumento íntegramente construido y en espera de entrar en vigencia. Las bandas se recalibraron porque cambió lo que la escala mide, no para mover el puntaje: sobre la escala nueva, las anclas viejas habrían dado 75 a un instrumento que nadie usa." },
      { fecha: "2026-05", cambio: "Versión inicial como carga manual de etapas implementadas." },
      { fecha: "2026-07-02", cambio: "Compuesto del documento institucional renormalizado a lo medible, con el registro CNV automático." },
      { fecha: "2026-07-03", cambio: "La litigiosidad se separa como indicador propio de la dimensión. Después, la cobertura se automatizó vía menciones del Boletín Oficial con calibración anclada." },
      { fecha: "2026-07-15", cambio: "La cobertura pasa a contar las menciones del Fondo de Asistencia Laboral (Ley 27.802) desde marzo de 2026, distinguiéndolo del régimen homónimo de la construcción. La serie histórica arranca en cero con la creación del régimen." },
      { fecha: "2026-07-25", cambio: "Su peso dentro de la dimensión baja del setenta al cincuenta por ciento, a propuesta de una revisión externa: la dimensión mide un instrumento y su resultado, y no había razón para que el instrumento pesara más del doble que el resultado. El cambio mejora el puntaje de la dimensión, porque la litigiosidad venía puntuando más alto que el fondo; se deja dicho para que la decisión pueda discutirse por su argumento y no por su efecto." },
    ],
  },

  litigiosidad_laboral: {
    tipo: "indicador",
    id: "litigiosidad_laboral",
    cinturon: "gestion",
    rezago: "La serie oficial de juicios se publica con 3-4 meses de rezago.",
    fuente: {
      organismo: "SRT — Superintendencia de Riesgos del Trabajo",
      operacion: "Serie histórica de litigiosidad: ingresos de juicios del sistema de riesgos del trabajo, total sistema",
      serie: "Planilla oficial «Juicios - Total Sistema» (serie mensual desde 2010)",
      url: "https://www.srt.gob.ar/estadisticas/",
      acceso: "Automático: lectura de la planilla oficial.",
    },
    transformaciones: [
      "Variación porcentual del acumulado de 12 meses contra los 12 meses previos: si la industria del juicio se enfría, la variación se hace negativa.",
    ],
    anclas: {
      bandas: [
        { banda: "≤ −15", puntaje: 100 },
        { banda: "−15 – −5", puntaje: 85 },
        { banda: "−5 – 5", puntaje: 65 },
        { banda: "5 – 20", puntaje: 40 },
        { banda: "> 20", puntaje: 10 },
      ],
      puntos: [[-15, 100], [-10, 85], [0, 65], [12.5, 40], [20, 10]],
      unidadCorta: "% (12m vs 12m)",
    },
    dobleUso: "Es el «resultado» que complementa al «instrumento» (Fondo de Asistencia Laboral) dentro de la dimensión de reforma laboral.",
    limitaciones: [
      "Aproximación declarada: son juicios del sistema de riesgos del trabajo, no el canal indemnizatorio que el Fondo de Asistencia Laboral reemplaza — pero es la única serie nacional mensual pública.",
      "La ventana de 12 contra 12 meses reacciona lento a los quiebres.",
    ],
    faltantes: "Con la planilla caída, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "La fuente puede revisar meses; la planilla completa se relee en cada actualización.",
    cambios: [
      { fecha: "2026-07-02", cambio: "Alta como indicador de contexto, fuera del índice." },
      { fecha: "2026-07-03", cambio: "Entra al ITCG (reforma laboral, 30% interno): es el resultado que la reforma persigue y complementa al instrumento." },
    ],
  },

  privatizaciones: {
    tipo: "indicador",
    id: "privatizaciones",
    cinturon: "gestion",
    rezago: "Al día del último hito curado; el registro se actualiza con seguimiento quincenal del Boletín Oficial.",
    fuente: {
      organismo: "Boletín Oficial (hechos) + Fundación CIGOB (curaduría del registro)",
      operacion: "Avance de la cartera de privatizaciones de la Ley Bases por etapas 0-4 (sin definir → preparatoria → pliegos → licitación/adjudicación → cerrada), nueve empresas",
      url: "https://www.boletinoficial.gob.ar/",
      acceso: "Registro curado a mano con seguimiento quincenal del Boletín Oficial: no existe una fuente única automatizable (ni la agencia responsable ni la comisión bicameral publican un tablero).",
    },
    transformaciones: [
      "Cada empresa recibe una etapa 0-4 con la norma que la respalda; el avance es el promedio de etapas sobre 4, en porcentaje.",
      "La serie histórica se reconstruye con las transiciones de etapa fechadas por su norma del Boletín Oficial.",
    ],
    anclas: {
      bandas: [
        { banda: "> 75", puntaje: 100 },
        { banda: "55 – 75", puntaje: 85 },
        { banda: "35 – 55", puntaje: 65 },
        { banda: "15 – 35", puntaje: 40 },
        { banda: "≤ 15", puntaje: 10 },
      ],
      puntos: [[15, 10], [25, 40], [45, 65], [65, 85], [75, 100]],
      unidadCorta: "% de avance",
    },
    limitaciones: [
      "Es el único indicador del índice sin una fuente de datos en vivo: la asignación de etapas es juicio del analista, con las normas citadas en el registro.",
      "La escala 0-4 discretiza procesos continuos.",
    ],
    faltantes: "Sin registro disponible, se mantiene el último valor disponible, señalado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Seguimiento quincenal declarado; la serie avisa si el estado vivo no reconcilia con las transiciones fechadas.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual (porcentaje de empresas privatizadas)." },
      { fecha: "2026-07-02", cambio: "Pasa al esquema de etapas 0-4 del documento institucional, con registro curado por empresa." },
      { fecha: "2026-07-03", cambio: "Serie histórica reconstruida por hitos fechados del Boletín Oficial. Puntaje interpolado entre anclas." },
    ],
  },

  rigi_inversiones: {
    tipo: "indicador",
    id: "rigi_inversiones",
    cinturon: "gestion",
    rezago: "Sin rezago: foto de la plataforma oficial al día de la actualización.",
    fuente: {
      organismo: "Ministerio de Economía — plataforma oficial del RIGI",
      operacion: "Cartera del Régimen de Incentivo a Grandes Inversiones: inversión aprobada sobre el total de la cartera (aprobada + en evaluación)",
      serie: "Planilla pública que alimenta el mapa oficial del RIGI (pestañas de proyectos aprobados y en evaluación)",
      url: "https://www.argentina.gob.ar/economia/rigi",
      acceso: "Automático: lectura de la planilla pública de la plataforma oficial; las fechas de aprobación se toman del Boletín Oficial solo para proyectos nuevos.",
    },
    transformaciones: [
      "Avance = inversión aprobada / (aprobada + en evaluación), en porcentaje.",
      "Los proyectos multi-provincia cuentan una sola vez (mismo criterio que el sitio oficial).",
      "La serie histórica es la inversión aprobada acumulada, fechada por la norma de aprobación de cada proyecto.",
    ],
    anclas: {
      bandas: [
        { banda: "> 60", puntaje: 100 },
        { banda: "40 – 60", puntaje: 85 },
        { banda: "25 – 40", puntaje: 65 },
        { banda: "10 – 25", puntaje: 40 },
        { banda: "≤ 10", puntaje: 10 },
      ],
      puntos: [[10, 10], [17.5, 40], [32.5, 65], [50, 85], [60, 100]],
      unidadCorta: "% de la cartera",
    },
    limitaciones: [
      "No existe fuente estructurada de inversión efectivamente desembolsada: la inversión aprobada es lo más cercano al hecho, y se declara como tal.",
      "El denominador salta con cada anuncio grande en evaluación: el avance puede bajar sin que nada empeore.",
      "Depende de que la planilla oficial siga pública y con el mismo esquema (ya cambió una vez y la lectura se adaptó).",
    ],
    faltantes: "Con la plataforma caída, cae a una aproximación por conteo de resoluciones oficiales (marcada como desactualizada); agotado eso, se mantiene el último valor disponible y los pesos se renormalizan.",
    revisiones: "La plataforma se actualiza sin registro de cambios; las fechas de aprobación quedan fijadas con su norma.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial por conteo de resoluciones (aproximación)." },
      { fecha: "2026-06-30", cambio: "Pasa a la plataforma oficial del Ministerio de Economía: inversión aprobada sobre la cartera total, con montos reales." },
      { fecha: "2026-07-02", cambio: "Umbrales institucionales del ITCG; después, puntaje interpolado entre anclas." },
    ],
  },

  concesiones_infraestructura: {
    tipo: "indicador",
    id: "concesiones_infraestructura",
    cinturon: "gestion",
    rezago: "Sin rezago: estado del portal de contrataciones al día de la actualización.",
    fuente: {
      organismo: "CONTRAT.AR (portal oficial de contrataciones) + Vialidad Nacional (página de la Red Federal de Concesiones)",
      operacion: "Tasa de adjudicación de la Red Federal de Concesiones, en kilómetros: km bajo concesión adjudicada sobre km totales del plan",
      url: "https://www.argentina.gob.ar/transporte/vialidad-nacional/red-federal-de-concesiones",
      acceso: "Automático: el estado de cada proceso licitatorio se lee de CONTRAT.AR (búsqueda pública, sin usuario) y el kilometraje por etapa de la página oficial de la Red.",
    },
    transformaciones: [
      "Una etapa cuenta con el 100% de sus kilómetros cuando su proceso figura adjudicado.",
      "La serie histórica es escalonada, por hitos de adjudicación fechados con su norma.",
    ],
    anclas: {
      bandas: [
        { banda: "> 75", puntaje: 100 },
        { banda: "55 – 75", puntaje: 85 },
        { banda: "35 – 55", puntaje: 65 },
        { banda: "15 – 35", puntaje: 40 },
        { banda: "≤ 15", puntaje: 10 },
      ],
      puntos: [[15, 10], [25, 40], [45, 65], [65, 85], [75, 100]],
      unidadCorta: "% de km",
    },
    limitaciones: [
      "Las etapas que adjudican por renglones cuentan hoy solo al cierre total: refinamiento pendiente declarado.",
      "Binario por etapa: 0 o 100% de sus kilómetros.",
      "Depende de dos lecturas de páginas oficiales: un rediseño de cualquiera de las dos interrumpe el dato hasta adaptarlo.",
    ],
    faltantes: "Con los portales caídos, cae al valor de respaldo documentado con fecha; agotado eso, se mantiene el último valor disponible y los pesos se renormalizan.",
    revisiones: "Los kilómetros por etapa se refrescan de la página oficial en cada actualización; para las adjudicaciones manda la fecha del Boletín Oficial.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual." },
      { fecha: "2026-07-02", cambio: "Automatizado: estado por CONTRAT.AR y kilometraje por la página oficial de la Red, en km." },
      { fecha: "2026-07-03", cambio: "Serie escalonada por hitos fechados. Puntaje interpolado entre anclas." },
    ],
  },

  asistencia_directa: {
    tipo: "indicador",
    id: "asistencia_directa",
    cinturon: "gestion",
    rezago: "Semanas: el devengado del ejercicio corriente se carga de forma continua.",
    fuente: {
      organismo: "Secretaría de Hacienda — Presupuesto Abierto",
      operacion: "TDPS — tasa de desintermediación de los planes sociales: porcentaje del gasto de los programas de empleo y acompañamiento pagado directo a personas, sin organizaciones intermediarias",
      serie: "API de Presupuesto Abierto (devengado por partida); línea de base 2023: Potenciar Trabajo",
      url: "https://www.presupuestoabierto.gob.ar/",
      acceso: "Automático: API oficial con credencial de acceso; la línea de base 2023 (ejercicio cerrado) se calculó una vez y quedó fijada.",
    },
    transformaciones: [
      "TDPS = 100 × devengado en «ayudas sociales a personas» / total de transferencias de los programas; el resto del inciso son fondos que llegan vía terceros (las «unidades de gestión» eliminadas por decreto en 2024).",
      "Línea de base 2023 (Potenciar Trabajo): 98,3% directo.",
    ],
    anclas: {
      bandas: [
        { banda: "> 95", puntaje: 100 },
        { banda: "85 – 95", puntaje: 85 },
        { banda: "60 – 85", puntaje: 65 },
        { banda: "30 – 60", puntaje: 40 },
        { banda: "≤ 30", puntaje: 10 },
      ],
      puntos: [[30, 10], [45, 40], [72.5, 65], [90, 85], [95, 100]],
      unidadCorta: "%",
    },
    limitaciones: [
      "Advertencia metodológica declarada: desintermediar y recortar son promesas distintas — esto mide solo la primera.",
      "La base 2023 ya era 98,3%: el salto normativo fue puntual y el indicador está saturado cerca del máximo desde 2024 (decisión de rediseño abierta con CIGOB).",
      "Depende de que los nombres de los programas no cambien en el presupuesto.",
    ],
    faltantes: "Sin acceso a la API, cae al valor de respaldo documentado (el decreto de 2024); agotado eso, se mantiene el último valor disponible y los pesos se renormalizan.",
    revisiones: "El devengado del ejercicio corriente es acumulado en curso, revisable por definición; la base 2023 está congelada.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual (porcentaje de beneficiarios que cobra directo)." },
      { fecha: "2026-07-02", cambio: "Pasa a la tasa real contra la ejecución presupuestaria, con línea de base 2023 verificada." },
    ],
  },

  protocolo_antipiquetes: {
    tipo: "indicador",
    id: "protocolo_antipiquetes",
    cinturon: "gestion",
    rezago: "Hasta un año: los anclajes públicos de la fuente son por año cerrado.",
    fuente: {
      organismo: "Diagnóstico Político (consultora; relevamiento diario de cortes sobre más de cien medios desde 2009)",
      operacion: "Reducción porcentual de los cortes por manifestación en CABA contra 2023, con los anclajes anuales públicos de la fuente (2023: 931 · 2024: 440 · 2025: 240)",
      url: "https://diagnosticopolitico.com.ar/monitoreos-politicos",
      acceso: "Automático sobre un registro curado: los anclajes anuales se cargan con su fuente pública; un detector revisa la página de la consultora y avisa cuando aparece un año nuevo.",
    },
    transformaciones: [
      "Reducción = (1 − cortes del último año cerrado / cortes de 2023) × 100.",
      "La definición de piquete de la fuente coincide con la del protocolo oficial (Resolución 943/23).",
    ],
    anclas: {
      bandas: [
        { banda: "> 75", puntaje: 100 },
        { banda: "50 – 75", puntaje: 85 },
        { banda: "25 – 50", puntaje: 65 },
        { banda: "0 – 25", puntaje: 40 },
        { banda: "≤ 0", puntaje: 10 },
      ],
      puntos: [[0, 10], [12.5, 40], [37.5, 65], [62.5, 85], [75, 100]],
      unidadCorta: "% de reducción",
    },
    dobleUso: "El seguimiento interno de eventos de protesta (ACLED) que mantiene el proyecto muestra que la protesta no desapareció — se reconvirtió a marchas sin corte; ese contraste informa la lectura de este indicador aunque ya no se publique como card propia.",
    limitaciones: [
      "Fuente privada sin microdatos abiertos: los anclajes se reconstruyen de cifras publicadas.",
      "Granularidad anual: el valor se arrastra todo el año hasta el anclaje siguiente.",
      "Estado judicial verificado: la nulidad de primera instancia fue revocada por la Cámara en lo Contencioso Administrativo Federal (marzo de 2026) — el protocolo es un acto válido y vigente.",
      "El registro histórico oficial de cortes del GCBA está fuera de servicio; el monitoreo propio de alertas de transporte acumula la serie que permitirá automatizar el dato.",
    ],
    faltantes: "Cae al valor de respaldo documentado; agotado eso, se mantiene el último valor disponible y los pesos se renormalizan.",
    revisiones: "El registro se actualiza cuando la fuente publica el año nuevo (con aviso automático del detector).",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual (55%, la foto 2024)." },
      { fecha: "2026-07-02", cambio: "Se crea el monitoreo propio de alertas de transporte como futura fuente automática." },
      { fecha: "2026-07-03", cambio: "Automatizado con los anclajes anuales públicos de Diagnóstico Político; la corrección del año cerrado 2025 llevó el valor de 55% a 74,2%." },
    ],
  },

  libertad_opcion_salud: {
    tipo: "indicador",
    id: "libertad_opcion_salud",
    cinturon: "gestion",
    rezago: "3-4 meses en el padrón principal; el denominador (usuarios de prepagas) corre con más rezago y se arrastra al último disponible.",
    fuente: {
      organismo: "Superintendencia de Servicios de Salud",
      operacion: "Padrones oficiales: beneficiarios por Agente del Seguro de Salud (RNAS) y usuarios de entidades de medicina prepaga (RNEMP)",
      serie: "Planillas anuales oficiales de evolución de beneficiarios y usuarios (columnas mensuales)",
      url: "https://www.argentina.gob.ar/sssalud/estadisticas",
      acceso: "Automático: lectura de las planillas oficiales; las prepagas inscriptas como Agentes del Seguro se identifican por su rango de código de registro (canal creado por el DNU 70/2023).",
    },
    transformaciones: [
      "Porcentaje = beneficiarios con aportes derivados directo a prepagas inscriptas / usuarios totales de prepagas.",
    ],
    anclas: {
      bandas: [
        { banda: "> 70", puntaje: 100 },
        { banda: "50 – 70", puntaje: 85 },
        { banda: "30 – 50", puntaje: 65 },
        { banda: "10 – 30", puntaje: 40 },
        { banda: "≤ 10", puntaje: 10 },
      ],
      puntos: [[10, 10], [20, 40], [40, 65], [60, 85], [70, 100]],
      unidadCorta: "%",
    },
    limitaciones: [
      "Numerador y denominador salen de registros distintos con rezagos distintos, declarado en el dato.",
      "Mide la derivación directa de aportes, una parte de la «libertad de opción» — no toda la reforma del sistema.",
      "El contador histórico de traspasos del sitio oficial sigue fuera de servicio; este indicador lo reemplaza con otra semántica.",
    ],
    faltantes: "Cae al valor de respaldo documentado con fecha; agotado eso, se mantiene el último valor disponible y los pesos se renormalizan.",
    revisiones: "Las planillas anuales se releen completas en cada actualización (la fuente puede revisar meses hacia atrás).",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual: la fuente en línea estaba bloqueada." },
      { fecha: "2026-07-02", cambio: "Automatizado con los padrones oficiales de beneficiarios y usuarios." },
    ],
  },

  // (alertas_manifestacion y protestas_caba no tienen ficha: quedaron fuera
  // del tablero de gestión en jul-2026 — el tablero solo muestra lo que
  // integra las dimensiones del índice; ambos se siguen relevando como
  // seguimiento interno, igual que los ocultos de macro/política/espíritu.)

  // ═══════════════════════════════════════════════════════════════════════
  // Impacto social — componentes base-100 del ITCIS (100 = promedio 4T-2023)
  // ═══════════════════════════════════════════════════════════════════════
  brecha_salario_cbt: {
    tipo: "indicador",
    id: "brecha_salario_cbt",
    cinturon: "vida_cotidiana",
    rezago: "El salario formal (RIPTE) corre un mes detrás de la canasta: el par común queda ~2 meses atrás del calendario.",
    fuente: {
      organismo: "Secretaría de Trabajo (RIPTE) + INDEC (Canasta Básica Total)",
      operacion: "RIPTE — remuneración imponible promedio de los trabajadores estables ÷ Canasta Básica Total por adulto equivalente",
      serie: "RIPTE (planilla oficial mensual) + CBT 150.1_CSTA_BATAL_0_D_20 (datos.gob.ar)",
      url: "https://www.argentina.gob.ar/trabajo/seguridadsocial/ripte",
      acceso: "Automático: descarga de la planilla oficial del RIPTE y API de series para la canasta; el cociente se calcula alineando por mes común.",
    },
    transformaciones: [
      "Canastas cubiertas = salario formal promedio ÷ canasta básica total del mismo mes.",
      "Componente del índice: el cociente rebaseado a 100 = promedio del 4º trimestre de 2023 (más canastas = mejora).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de ingresos y consumo (47,67% interno · 13,38% del ITCIS) y sigue siendo el componente más pesado.",
      "El ITCIS promedia sus componentes base-100 por dimensión: por encima de 100, la brecha acumula mejora contra el arranque del mandato.",
    ],
    limitaciones: [
      "El RIPTE cubre solo asalariados formales estables: deja afuera a informales y cuentapropistas; la canasta es por adulto equivalente.",
      "El peso del componente (13,38% del índice) es una discusión abierta declarada del diseño.",
      "Efecto base auditado: parte de la mejora contra el 4º trimestre de 2023 es rebote de la devaluación de diciembre.",
    ],
    faltantes: "Si una fuente falla, se mantiene el último valor publicado (marcado como desactualizado); si el componente no calcula, los pesos del índice se renormalizan.",
    revisiones: "Cada actualización re-descarga las series completas y adopta las revisiones de las fuentes; con canasta fresca sin salario, el par se declara provisorio.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS base-100 como rebase directo del cociente, con 22,75% de peso efectivo." },
      { fecha: "2026-07-04", cambio: "Alineación estricta por mes común: antes podía mezclar el salario de un mes con la canasta de otro. Además queda como única medición del ratio ingresos/comida del índice." },
    ],
  },

  ipc_alimentos: {
    tipo: "indicador",
    id: "ipc_alimentos",
    cinturon: "vida_cotidiana",
    rezago: "El IPC se publica a mediados del mes siguiente.",
    fuente: {
      organismo: "INDEC",
      operacion: "IPC — Alimentos y bebidas no alcohólicas, nivel nacional; el componente lo compara contra el IPC general",
      serie: "146.3_IALIMENNAL_DICI_M_45 + IPC general 148.3_INIVELNAL_DICI_M_26 · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "La card muestra la variación mensual de los alimentos.",
      "El componente del índice mide el encarecimiento RELATIVO de la comida: el nivel de alimentos contra el nivel general de precios, rebaseado a 100 = 4º trimestre de 2023. Por encima de 100, la comida sube menos que el resto de los precios.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de presión de precios (35% interno · 8,75% del ITCIS).",
      "La comparación contra el IPC general evita contar dos veces el ratio salario/comida, que ya mide la brecha con la canasta.",
    ],
    limitaciones: [
      "La métrica anterior (alimentos contra salario) correlacionaba casi uno a uno con la brecha de la canasta: un tercio del índice contaba dos veces lo mismo. Se corrigió con el rediseño relativo al IPC general.",
      "Leve estacionalidad de la canasta alimentaria aceptada sin corrección, auditada y declarada.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, los pesos del índice se renormalizan.",
    revisiones: "La API sirve la serie revisada; la base del 4º trimestre de 2023 se recalcula dinámicamente de la propia serie.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS base-100 (entonces como nivel contra el salario)." },
      { fecha: "2026-07-04", cambio: "Rediseño: nivel contra el IPC general, eliminando el doble conteo con la brecha salario/canasta." },
    ],
  },

  mora_familias: {
    tipo: "indicador",
    id: "mora_familias",
    cinturon: "vida_cotidiana",
    rezago: "El anexo del Informe sobre Bancos se publica con ~2 meses de rezago.",
    fuente: {
      organismo: "BCRA",
      operacion: "Anexo del Informe sobre Bancos — planilla de calidad de cartera, sección Familias: ratio de irregularidad y saldos de préstamos personales y tarjetas",
      serie: "InfBanc_Anexo.xlsx, hoja de calidad de cartera por líneas",
      url: "https://www.bcra.gob.ar/publicaciones-e-investigaciones/informe-sobre-bancos/",
      acceso: "Automático: lectura de la planilla oficial; el titular es el último punto de la serie mensual.",
    },
    transformaciones: [
      "Mora ponderada: el ratio de irregularidad de préstamos personales y el de tarjetas de crédito se combinan según el saldo de cada línea.",
      "En el ITCIS puntúa por el nivel relativo al 4º trimestre de 2023 (índice base 100), invertido: más mora que en la base, peor puntaje.",
      "Sin piso de recorte, igual que el resto de los componentes: el deterioro no se maquilla.",
    ],
    incidenciaTexto: [
      "Es el único componente de la dimensión de vulnerabilidad financiera, así que aporta el 10% del ITCIS por sí solo.",
      "Acompañaba al endeudamiento de consumo al 50% cada uno. El endeudamiento dejó de integrar el índice porque leía el crecimiento de la deuda real como mayor acceso al crédito, y con la morosidad multiplicada por más de cinco en el mismo período esa lectura compensaba justo la señal que la dimensión existe para dar.",
    ],
    limitaciones: [
      "La mora de las familias se multiplicó por varias veces desde la base 4T-2023: el componente concentra buena parte del arrastre del índice, y así se publica.",
      "Cubre el crédito bancario regulado: no ve el endeudamiento no bancario (fintech, cadenas de consumo, prestamistas informales), donde el estrés suele ser mayor.",
      "El corte es la cartera consolidada del sistema, con el rezago de la planilla oficial.",
    ],
    faltantes: "Si la planilla no está disponible, la serie conserva sus puntos previos y el titular queda en el último mes publicado. Es el único componente de su dimensión, así que no hay con qué renormalizar dentro de ella: si se quedara sin dato, la dimensión entera no se calcula y su diez por ciento se reparte entre las otras cinco. Ese es el costo de haber dejado la dimensión con un solo indicador, y queda declarado.",
    revisiones: "La planilla oficial se relee completa en cada actualización y adopta las revisiones del BCRA.",
    cambios: [
      { fecha: "2026-07-15", cambio: "Entra al ITCIS como indicador propio: hasta ahora la mora vivía adentro del componente de endeudamiento (deuda real × mora); separarla hace legible cada señal — acceso al crédito por un lado, estrés de pago por el otro — sin cambiar la información que el índice procesa." },
    ],
  },

  alquiler_real: {
    tipo: "indicador",
    id: "alquiler_real",
    cinturon: "vida_cotidiana",
    rezago: "El IPC-GBA se publica a mediados del mes siguiente (~1 mes).",
    fuente: {
      organismo: "INDEC",
      operacion: "Índice de Precios al Consumidor del Gran Buenos Aires — alquiler de la vivienda",
      serie: "104.1_I2RE_2016_M_25 (alquiler) + 103.1_I2N_2016_M_19 (nivel general GBA) · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31",
      acceso: "Automático: API pública de series.",
    },
    transformaciones: [
      "La card muestra la variación mensual del alquiler.",
      "El componente mide el encarecimiento RELATIVO del alquiler: nivel del alquiler contra el nivel general de precios del mismo aglomerado, rebaseado a 100 = 4º trimestre de 2023. Por debajo de 100, el alquiler subió más que el resto de los precios desde el arranque.",
      "Se compara contra el índice general del Gran Buenos Aires y no contra el nacional: dividir un precio de una plaza por el índice de otra mezclaría dos mercados en el mismo cociente.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de presión de precios (20% interno · 5% del ITCIS).",
      "Entra por debajo de tarifas y alimentos porque el alquiler golpea a los hogares inquilinos —alrededor de un tercio de los urbanos— mientras los otros dos pesan sobre todos.",
      "Es el único componente del cinturón que mide el costo de la vivienda, un gasto fijo que ningún otro captura.",
    ],
    limitaciones: [
      "Sólo mide el Gran Buenos Aires: es la única apertura de alquiler que publica el INDEC, y el mercado del interior puede comportarse distinto.",
      "Mide el alquiler que releva el IPC, que sigue contratos vigentes; los valores de los contratos nuevos pueden moverse antes.",
      "No distingue entre hogares propietarios e inquilinos: el índice describe el precio, no cuántos lo pagan.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización.",
    revisiones: "Re-descarga completa por actualización; base fija en el 4º trimestre de 2023.",
    cambios: [
      { fecha: "2026-07-20", cambio: "Alta del indicador: la dimensión de precios no medía el costo de la vivienda." },
    ],
  },
  peso_tarifas: {
    tipo: "indicador",
    id: "peso_tarifas",
    cinturon: "vida_cotidiana",
    rezago: "El IPC sale a mediados del mes siguiente; el componente espera además el salario formal (~2 meses).",
    fuente: {
      organismo: "INDEC (precios regulados) + Secretaría de Trabajo (RIPTE)",
      operacion: "IPC — precios regulados, comparados contra el salario formal",
      serie: "148.3_IREGULANAL_DICI_M_22 + RIPTE · API de datos.gob.ar y planilla oficial",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31",
      acceso: "Automático: API pública de series y planilla del RIPTE.",
    },
    transformaciones: [
      "La card muestra la variación mensual de los regulados.",
      "El componente mide el peso de los servicios regulados en el salario: nivel de regulados contra nivel del RIPTE, rebaseado a 100 = 4º trimestre de 2023. Por debajo de 100, las tarifas subieron más que los salarios desde el arranque.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de presión de precios (45% interno · 11,25% del ITCIS).",
      "Captura el efecto de la quita de subsidios que el IPC general diluye.",
    ],
    limitaciones: [
      "La tensión equivalente del componente excede la escala del cinturón y se corta en el máximo: el deterioro es mayor que lo que la escala muestra.",
      "Depende del RIPTE, que cubre solo asalariados formales.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización.",
    revisiones: "Re-descarga completa por actualización; base dinámica de la propia serie.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS base-100 como nivel de regulados contra el salario (antes puntuaba por variación mensual anclada)." },
    ],
  },

  consumo_carnes_total: {
    tipo: "indicador",
    id: "consumo_carnes_total",
    cinturon: "vida_cotidiana",
    rezago: "El tablero oficial publica el mes con unas semanas de demora; la faena del INDEC, con dos meses. El titular avanza con el tablero y el índice con la faena.",
    fuente: {
      organismo: "SAGYP (nivel) e INDEC (evolución)",
      operacion: "Nivel: SAGYP — Dirección Nacional de Producción Ganadera, tablero de consumo per cápita de carnes, promedio móvil de 12 meses. Evolución: faena mensual en toneladas de vacunos, porcinos y aves (INDEC, series 40.3_VT_0_M_17 · 40.3_PT_0_M_18 · 40.3_AT_0_M_14), per cápita con la población proyectada del INDEC.",
      url: "https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_sectorial",
      acceso: "Automático: lectura mensual del PDF del tablero y de la API de series de tiempo del INDEC.",
    },
    transformaciones: [
      "Suma de las tres carnes —vacuna, aviar y porcina— en toneladas, promedio móvil de 12 meses: la misma ventana con la que la fuente oficial publica su per cápita, y la que saca la estacionalidad fuerte de la faena.",
      "Pasaje a per cápita con la población total proyectada del INDEC, interpolada a meses desde su serie trimestral.",
      "Componente del índice: el resultado rebaseado a 100 = promedio del 4º trimestre de 2023 (menos proteína por habitante = deterioro).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de ingresos y consumo (3,14% interno · 0,88% del ITCIS).",
      "Mide el acceso TOTAL a proteína cárnica, no el consumo de una carne. La distinción no es de matiz: la carne vacuna cae 10,7% contra el arranque del mandato y el total cae 5,0%, porque parte de esa caída es sustitución hacia pollo y cerdo. Leer la vacuna sola como pérdida de poder adquisitivo es el falso positivo que este indicador desarma.",
      "La composición se publica junto al color: qué parte del consumo sigue siendo vacuna, y si el total se sostiene o cae con ella.",
    ],
    limitaciones: [
      "El nivel es consumo «aparente», no medición de hogares: no observa lo que come una familia, sino lo que queda en el mercado interno.",
      "La evolución se reconstruye desde la FAENA, que es producción y no netea exportaciones. No afecta al puntaje —el índice se lee contra su propia base, así que pesa la evolución y no el nivel— pero sí explica que la variación reconstruida no dé idéntica a la que publica el tablero. La distancia entre ambas se vigila: si supera los 3 puntos porcentuales, la faena dejó de aproximar el consumo.",
      "Sólo cubre las tres carnes. Huevo, lácteos, pescado y legumbres también son proteína y también muestran sustitución; sus fuentes no tienen la frecuencia necesaria para un seguimiento mensual.",
      "El pasaje a per cápita usa una proyección de población, no un censo del mes.",
    ],
    faltantes: "Un mes sin tablero legible deja el titular en el último valor publicado; la serie del índice sigue avanzando con la faena, que es independiente.",
    revisiones: "La faena del INDEC se revisa hacia atrás y la serie se reconstruye entera en cada corrida, así que las revisiones entran solas.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS el consumo de carne VACUNA (CICCRA), con línea de base documentada." },
      { fecha: "2026-08-12", cambio: "Se suma el consumo total de las tres carnes y la matriz que distingue sustitución de pérdida de acceso; el nivel pasa al tablero de SAGYP." },
      { fecha: "2026-08-20", cambio: "Pasa a puntuar el TOTAL y no la vacuna, con la serie reconstruida desde la faena del INDEC hasta el 4º trimestre de 2023 (ADR-0217). La vacuna queda como diagnóstico dentro de la matriz. El componente pasa de 89,3 a 95,0 sin mover el índice del cinturón." },
    ],
  },
  pobreza_nowcast: {
    tipo: "indicador",
    id: "pobreza_nowcast",
    cinturon: "vida_cotidiana",
    rezago: "El informe mensual sale a mediados del mes siguiente al que describe. La referencia oficial del INDEC llega dos veces al año y con más demora.",
    fuente: {
      organismo: "Universidad Torcuato Di Tella (estimación mensual) e INDEC (base y referencia oficial)",
      operacion: "Nowcast de pobreza: porcentaje de personas en hogares con ingresos por debajo de la línea, estimado mes a mes; y Encuesta Permanente de Hogares del INDEC para la base y el contraste",
      serie: "Informes mensuales del nowcast desde enero de 2025 + serie semestral oficial del INDEC desde 2003",
      url: "https://www.utdt.edu/profesores/mrozada/pobreza",
      acceso: "Automático: los informes mensuales se descubren desde el listado de la universidad y cada uno se procesa una sola vez; la serie oficial sale de la interfaz pública de series de tiempo.",
    },
    transformaciones: [
      "Se rebasea a 100 = la pobreza del segundo semestre de 2023, que es el semestre que contiene al cuarto trimestre, igual que el resto de los componentes del cinturón.",
      "Se invierte, como los otros componentes que se leen al revés: más pobreza es peor, así que la base va arriba en el cociente y por encima de 100 significa MENOS pobreza que en la transición.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de ingresos y consumo (26,02% interno · 7,3% del ITCIS).",
      "Cubre lo que el indicador de salario no puede ver: la brecha entre salario y canasta compara salario REGISTRADO, así que sólo alcanza al empleo formal, mientras la pobreza cuenta personas, incluidos los hogares informales y los que no viven de un sueldo.",
    ],
    limitaciones: [
      "La base y el nivel salen de DOS fuentes distintas, y no coinciden. El nivel es la estimación mensual de la universidad, que empieza en enero de 2025 y por eso no llega al período que sirve de base; la base es la medición oficial. En los tres semestres en que las dos se superponen, la estimación mensual queda 2,3 puntos por debajo de la oficial, luego medio punto por debajo, y después 2 puntos por ENCIMA: no es una diferencia con signo constante que se pueda corregir. Sobre una base de 40,1 puntos eso implica hasta un 5,7% de error, que se traslada a todos los valores del componente. Se acepta porque la alternativa —usar sólo la medición semestral— renuncia al dato mensual.",
      "El indicador se lee contra la transición, no contra un óptimo: la pobreza del segundo semestre de 2023 fue muy alta, así que superar 100 no significa una situación buena sino mejor que ese punto de partida.",
      "Es una estimación, no una medición: proyecta la pobreza a partir de ingresos y precios entre encuesta y encuesta. La referencia autorizada sigue siendo la del INDEC.",
      "No distingue intensidad: dos hogares apenas por debajo de la línea y dos muy por debajo cuentan igual.",
    ],
    faltantes: "Si un mes no publica informe, el componente mantiene el último valor disponible y el cinturón renormaliza los pesos de su dimensión.",
    revisiones: "La universidad puede revisar meses previos al recalcular su modelo, y el INDEC actualiza la línea de pobreza; se re-descarga la serie completa en cada corrida. Cada informe declara dos veces a qué semestre corresponde —en el título y en el texto— y las dos leyendas se escriben a mano, así que a veces una de ellas quedó del mes anterior; se toma la más reciente de las dos y se verifica que la serie no quede con meses faltantes, porque la publicación es mensual y un mes ausente indicaría una leyenda mal puesta antes que un informe no publicado.",
    cambios: [
      { fecha: "2026-07-16", cambio: "Alta como estimación mensual publicada junto a la medición oficial, sin integrar el índice." },
      { fecha: "2026-07-30", cambio: "Entra al índice con 25% de la dimensión de ingresos y consumo. Hasta entonces era una card visible que no puntuaba, una categoría que el equipo dio de baja: un indicador integra las dimensiones de su índice o no se publica. Se decidió que corresponde a este cinturón y no al macroeconómico, porque las dimensiones de aquel son condiciones de la economía y la pobreza es el resultado social que este cinturón ya mide. Los cuatro componentes previos de la dimensión cedieron peso proporcionalmente y conservan su orden relativo." },
    ],
  },

  informalidad: {
    tipo: "indicador",
    id: "informalidad",
    cinturon: "vida_cotidiana",
    rezago: "Encuesta trimestral publicada con uno a dos trimestres de rezago.",
    fuente: {
      organismo: "INDEC (EPH)",
      operacion: "EPH — asalariados sin descuento jubilatorio, tasa trimestral",
      serie: "52.2_ASDJ_0_0_37 · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Componente del índice: la tasa rebaseada de forma invertida (menos informalidad = mejora) contra el trimestre del arranque del mandato (4º trimestre de 2023).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de prospectivas de empleo (34,19% interno · 8,27% del ITCIS): es su componente más pesado.",
    ],
    limitaciones: [
      "Solo asalariados: no captura la informalidad cuentapropista.",
      "Serie trimestral contra una base de un solo trimestre: sesgo estacional chico, aceptado y declarado.",
      "La serie trimestral pública original se discontinuó en 2020; la vigente la reemplaza desde el rediseño del componente.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, la brecha salarial absorbe el peso de la dimensión.",
    revisiones: "La encuesta se revisa; la re-descarga completa por actualización adopta las revisiones.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS vía la serie anual disponible, invertida, con base en el año 2023." },
      { fecha: "2026-07-04", cambio: "Pasa a la serie trimestral con base exacta en el 4º trimestre de 2023 (la anual solo se actualizaba una vez al año y planchaba el componente)." },
    ],
  },

  mortalidad_pymes: {
    tipo: "indicador",
    id: "mortalidad_pymes",
    cinturon: "vida_cotidiana",
    rezago: "~3 meses. La SRT publica su serie histórica todos los meses, con el rezago del cierre administrativo de las declaraciones.",
    fuente: {
      organismo: "SRT — Superintendencia de Riesgos del Trabajo",
      operacion: "Serie histórica de partes empleadoras según tamaño de la nómina, cuadro 4.2: cantidad de empleadores con al menos una persona declarada con cobertura de ART, abierta por tramo de nómina, desde julio de 1996.",
      url: "https://www.srt.gob.ar/estadisticas/",
      acceso: "Automático: lectura mensual del XLSX publicado por la SRT.",
    },
    transformaciones: [
      "Recorte PyME: se SUMAN los tramos de 1 · 2 · 3 a 5 · 6 a 10 · 11 a 25 · 26 a 40 · 41 a 50 trabajadores. No se toma el total del sistema aunque el tramo PyME sea la enorme mayoría de los empleadores: el total incluye a las grandes, y el indicador dejaría de decir PyME apenas cambie esa proporción.",
      "Componente del índice: el NIVEL de empleadores activos rebaseado a 100 = promedio del 4º trimestre de 2023. No la variación neta del mes: el nivel acumulado dice cuántas empresas quedan respecto del arranque, que es la pregunta del informe, y no depende de la estacionalidad de un mes suelto.",
      "Una sola serie, en unidades, para el titular y para el índice — el rebase lo hace el motor. Antes se publicaban dos series distintas para el mismo indicador y nunca podían reconciliarse.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de prospectivas de empleo (14,76% interno · 3,57% del ITCIS).",
      "Mide el cierre neto de empresas de forma directa: 491.484 empleadores PyME en el 4º trimestre de 2023 contra 460.777 en mayo de 2026, o sea 30.707 menos, un 6,2% de caída.",
      "Contraste que la misma fuente permite: las empresas de más de 500 trabajadores cayeron 3,8% en el mismo período. El fenómeno es del tramo chico, no de toda la economía.",
    ],
    limitaciones: [
      "Sólo ve empleadores con al menos una persona declarada: una empresa que despide a toda su nómina y sigue existiendo cuenta como baja, y una que nunca tuvo empleados no cuenta nunca.",
      "Es cobertura de riesgos del trabajo, no padrón tributario: el universo es el de las relaciones laborales registradas con ART.",
      "Mide el saldo neto, no las altas y bajas por separado: un mes con mucha rotación y saldo cero se lee igual que un mes quieto.",
      "El equivalente por el lado de AFIP —la base de empleadores de OEDE— dejaría ver el universo tributario completo, pero está congelada en octubre de 2023, justo antes del período que el informe evalúa.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión. Si el cuadro 4.2 deja de traer alguno de los siete tramos, el colector falla en voz alta en vez de publicar una suma incompleta.",
    revisiones: "La SRT reemite el archivo entero cada mes y la serie se relee completa en cada corrida, así que las revisiones hacia atrás entran solas.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS como nivel desestacionalizado base-100 (antes puntuaba por variación mensual de la serie original, dominada por estacionalidad)." },
      { fecha: "2026-08-21", cambio: "Pasa a medir lo que su nombre promete (ADR-0218): empleadores PyME activos de la SRT, en lugar del IPI manufacturero del INDEC, que era una aproximación declarada por producción industrial. El componente pasa de 97,4 a 93,8 — la producción había recuperado más que el número de empresas. El rótulo público pasa de «Actividad industrial (IPI)» a «Empleadores PyME activos» y el tope de frescura sube de 140 a 165 días." },
    ],
  },

  trabajo_independiente: {
    tipo: "indicador",
    id: "trabajo_independiente",
    cinturon: "vida_cotidiana",
    rezago: "~3 meses, el mismo del cierre administrativo con que el SIPA publica sus series de trabajo registrado.",
    fuente: {
      organismo: "SIPA — Sistema Integrado Previsional Argentino (Secretaría de Trabajo)",
      operacion: "Series mensuales sin estacionalidad de trabajadores registrados: autónomos y monotributistas por un lado; asalariados del sector privado, del sector público y de casas particulares por el otro.",
      serie: "151.1_IPENDIETAC_2012_M_34 y _M_36 (independientes) · 151.1_AARIADOTAC_2012_M_26, _M_25 y _M_40 (asalariados) · API de datos.gob.ar",
      url: "https://www.argentina.gob.ar/trabajo/estadisticas",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Participación: autónomos más monotributistas sobre el TOTAL del empleo registrado, no sólo sobre el privado — un asalariado que pasa a monotributo puede venir de cualquiera de los tres sectores.",
      "El monotributo social queda EXCLUIDO, y es la decisión que más pesa acá: su serie cae 394 mil personas en un solo mes, diciembre de 2024. Eso no es mercado de trabajo, es una decisión regulatoria sobre el propio régimen.",
      "Componente del índice: la participación rebaseada de forma INVERTIDA contra el promedio del 4º trimestre de 2023 (más peso independiente = deterioro).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de prospectivas de empleo (10% interno · 2,42% del ITCIS).",
      "Es la contracara del cierre de empresas: una economía donde cierran PyMEs y aparecen personas facturando por su cuenta no es lo mismo que una donde cierran y no aparece nada. Entre el 4º trimestre de 2023 y mayo de 2026 los independientes registrados crecen 6,2% mientras los asalariados caen 3,3%.",
      "Lo que costaba no excluir el monotributo social: con ese régimen adentro la participación BAJA de 22,91% a 22,05% y el indicador habría leído una reforma administrativa como una mejora del empleo. Sin él, SUBE de 19,12% a 20,60%. Las dos lecturas son opuestas y sólo una describe la economía.",
    ],
    limitaciones: [
      "El signo es una decisión de criterio, no un hecho de la fuente. Se puntúa invertido porque un empleo que se corre del salario al trabajo por cuenta propia pierde aportes patronales, indemnización y estabilidad, aunque siga siendo registrado. La lectura contraria —emprendedorismo registrado como mejora— existe y está declarada; cambiarla es cambiar un signo y recalcular.",
      "La participación puede subir porque caen los asalariados y no porque crezcan los independientes. Por eso el informe publica las dos variaciones por separado y no sólo el cociente.",
      "Sólo ve trabajo REGISTRADO: la informalidad, que es el otro modo de salir de la relación salarial, la mide su propio componente.",
      "La exclusión del monotributo social deja fuera un régimen que sí es empleo para quien lo tiene; lo que queda afuera es su serie, por el quiebre regulatorio, no la existencia del fenómeno.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión. Si alguna de las cinco series de SIPA no responde, el colector falla en voz alta: una participación calculada sobre un denominador incompleto sería un número plausible y equivocado.",
    revisiones: "El SIPA revisa hacia atrás con cada edición y las cinco series se releen completas en cada corrida, así que las revisiones entran solas.",
    cambios: [
      { fecha: "2026-08-21", cambio: "Entra al ITCIS (ADR-0219) como la contracara del cierre de PyMEs, con 10% de la dimensión; los cinco componentes previos ceden proporcionalmente y conservan su orden relativo. El componente entra en 92,8 y el peso nominal de la dimensión no se toca." },
    ],
  },

  despacho_cemento: {
    tipo: "indicador",
    id: "despacho_cemento",
    cinturon: "vida_cotidiana",
    rezago: "~2 meses (calendario de difusión de la construcción del INDEC).",
    fuente: {
      organismo: "INDEC",
      operacion: "ISAC — Indicador Sintético de la Actividad de la Construcción, serie desestacionalizada (el nombre histórico del indicador quedó; la métrica real es el ISAC)",
      serie: "33.2_ISAC_SIN_EDAD_0_M_23_56 · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Componente del índice: el nivel desestacionalizado rebaseado a 100 = promedio del 4º trimestre de 2023.",
      "La serie original tiene un desplome estacional en diciembre que contaminaría la base: por eso la desestacionalizada.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de prospectivas de empleo (13,47% interno · 3,26% del ITCIS).",
    ],
    limitaciones: [
      "Aproximación al empleo vía actividad de la construcción, no despachos de cemento reales (la serie de insumos existe aparte, como contraste).",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "Serie desestacionalizada revisable por la fuente; re-descarga completa por actualización.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS como nivel desestacionalizado base-100; el mismo día el gráfico pasó a la misma métrica del titular (antes mostraba otra serie de insumos por un alias)." },
    ],
  },

  pluriempleo: {
    tipo: "indicador",
    id: "pluriempleo",
    cinturon: "vida_cotidiana",
    rezago: "Encuesta trimestral publicada con uno a dos trimestres de rezago.",
    fuente: {
      organismo: "INDEC (EPH)",
      operacion: "EPH — tasa de subocupación demandante (aproximación declarada del pluriempleo)",
      serie: "47.2_ECTSDT_0_T_47 · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-31-58",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Componente del índice: la tasa rebaseada de forma invertida (menos subocupación demandante = mejora) contra el 4º trimestre de 2023.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de prospectivas de empleo (5,12% interno · 1,24% del ITCIS).",
    ],
    limitaciones: [
      "Aproximación declarada: mide gente que trabaja poco y busca más, no la tenencia de múltiples empleos.",
      "Trimestral contra base de un trimestre: sesgo estacional chico aceptado.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "La encuesta se revisa; re-descarga completa por actualización.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS con rebase invertido base-100." },
    ],
  },

  inseguridad: {
    tipo: "indicador",
    id: "inseguridad",
    cinturon: "vida_cotidiana",
    rezago: "La encuesta de victimización se publica con uno a dos meses de rezago.",
    fuente: {
      organismo: "Universidad Torcuato Di Tella — LICIP (métrica) + Ministerio de Seguridad — SNIC (contraste)",
      operacion: "IVI — Índice de Victimización: porcentaje de hogares de 40 centros urbanos que sufrieron al menos un delito en los últimos 12 meses, denunciado o no",
      serie: "Informes mensuales del IVI (LICIP-UTDT) + serie anual del SNIC como contraste",
      url: "https://www.utdt.edu/ver_contenido.php?id_contenido=912&id_item_menu=1967",
      acceso: "Automático: los informes mensuales se descubren desde el listado de la universidad y cada uno se procesa una sola vez; el registro oficial de delitos (SNIC) se publica como serie de contraste.",
    },
    transformaciones: [
      "Componente del índice: el porcentaje de hogares víctimas, rebaseado de forma invertida (menos victimización = mejora) con base declarada en enero de 2024 — no existe medición del 4º trimestre de 2023.",
      "La ventana de 12 meses de la pregunta desestacionaliza por construcción.",
    ],
    incidenciaTexto: [
      "Es el único indicador de la dimensión de seguridad, así que se lleva su peso entero: 4,5% del ITCIS.",
    ],
    limitaciones: [
      "La encuesta estuvo suspendida entre 2020 y 2023: la base de enero de 2024 es una aproximación declarada del arranque (su ventana de 12 meses cubre mayormente el año previo).",
      "Error muestral de ±3 puntos por mes (~1.000 hogares) y cobertura solo urbana.",
      "La divergencia con el registro de denuncias se publica como información: denuncias bajando con victimización subiendo indica que crece el delito no denunciado.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "Los informes procesados no se releen; el registro oficial de contraste se revisa hacia atrás y su serie se refresca completa.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS vía el registro anual de delitos, invertido, con base 2023." },
      { fecha: "2026-07-04", cambio: "La métrica pasa a la encuesta mensual de victimización (con la base declarada en enero de 2024); el registro de denuncias queda como serie de contraste." },
    ],
  },

  icc_utdt: {
    tipo: "indicador",
    id: "icc_utdt",
    cinturon: "vida_cotidiana",
    rezago: "Semanas: la universidad publica el índice del mes durante el mes siguiente.",
    fuente: {
      organismo: "Universidad Torcuato Di Tella — Centro de Investigación en Finanzas",
      operacion: "ICC — Índice de Confianza del Consumidor, serie histórica nacional",
      url: "https://www.utdt.edu/ver_contenido.php?id_contenido=8513&id_item_menu=16458",
      acceso: "Automático: se descubre la planilla más reciente desde el listado de la universidad y se lee la serie completa.",
    },
    transformaciones: [
      "Componente del índice: el ICC rebaseado a 100 = promedio del 4º trimestre de 2023 (más confianza = mejora).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y percepción (81,8% interno · 6,75% del ITCIS).",
    ],
    dobleUso: "Doble función declarada: (1) componente del ITCIS; (2) ancla de la validación externa del ITCIS — para no ser circular, en ese estudio el índice se recalcula sin este componente. Hasta julio de 2026 puntuó además en el cinturón espíritu de época, que desde entonces quedó acotado a la intención migratoria; esa lectura se sigue registrando como seguimiento interno.",
    limitaciones: [
      "Mide percepción y ánimo, no condiciones materiales: por diseño convive con medidas de conducta (consumo, patentamientos) en la misma dimensión.",
      "Depende del formato de publicación de la universidad: un cambio en el listado o la planilla interrumpe la lectura hasta adaptarla.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "La planilla oficial trae la serie completa en cada descarga y adopta las revisiones de la fuente.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS base-100 con 50% interno de su dimensión." },
      { fecha: "2026-07-04", cambio: "Cede cinco puntos de peso interno al sentimiento digital, que mide lo mismo por conducta de búsqueda." },
    ],
  },

  sentimiento_digital: {
    tipo: "indicador",
    id: "sentimiento_digital",
    cinturon: "vida_cotidiana",
    rezago: "Hasta un mes: el mes en curso se descarta por incompleto y se publica el último mes cerrado.",
    fuente: {
      organismo: "Google Trends (fuente no oficial)",
      operacion: "Interés de búsqueda en Argentina de una canasta de seis términos: inflación, precios, dólar, empleo, inseguridad y corrupción",
      url: "https://trends.google.com/",
      acceso: "Automático: una consulta por término sobre la misma ventana fija (2021 en adelante). Cada término se reemplaza entero cuando su propia descarga es sana; el que falla conserva su serie anterior.",
    },
    transformaciones: [
      "Cada término se compara contra su propio 4º trimestre de 2023 dentro de su propia consulta: la fuente normaliza cada consulta por un factor único, que se cancela en ese cociente. Por eso seis consultas distintas se promedian sin necesidad de un término de anclaje.",
      "La canasta es el promedio simple de los seis: peso igual y declarado. El promedio de los valores crudos que se usaba antes pesaba por volumen de búsqueda, y ese reparto no lo eligió nadie.",
      "Componente del índice: la canasta rebaseada de forma invertida (más búsquedas de urgencia = peor) contra el promedio del 4º trimestre de 2023.",
      "Sólo se publican los meses en los que están los seis términos: una canasta que cambia de composición mes a mes mueve el número por composición y no por búsquedas.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y percepción (18,2% interno · 1,5% del ITCIS): peso chico acorde a un constructo blando.",
      "La card y el gráfico publican el mismo número: el último mes cerrado de la canasta.",
    ],
    dobleUso: "Hasta julio de 2026 integró además el cinturón espíritu de época con fórmula de tensión propia; ese cinturón quedó acotado a la intención migratoria y la lectura duplicada se sigue registrando como seguimiento interno, sin publicarse ni puntuar.",
    limitaciones: [
      "Mide atención, no sentimiento: una noticia dispara búsquedas sin que cambie el bolsillo.",
      "«Corrupción» es un proxy de saliencia de escándalo, no de urgencia del hogar: un pico suyo se lee como que se habla de un caso, no como que empeoró el bolsillo.",
      "Un término de mucho volumen aplasta a uno de poco cuando comparten consulta —la fuente redondea a entero—, y por eso se consulta uno por vez. Con la canasta de cuatro términos anterior, «inseguridad» quedaba reducida a ceros y unos.",
      "La canasta entera está por debajo de su base: el componente queda recortado en el techo de 140 en buena parte de los meses recientes, así que su movimiento no se refleja completo en el índice.",
      "Fuente no oficial con límites de consulta: si el servicio restringe el acceso, cada término continúa desde el archivo propio.",
    ],
    faltantes: "Con la fuente caída, cada término conserva su última serie buena y la canasta llega hasta el último mes en que están los seis; la card mantiene el último valor como desactualizado.",
    revisiones: "Reemplazo total de la serie de cada término en cada descarga sana; la fuente no revisa datos propiamente.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Declarado indicador de contexto: la ventana de tres meses no permitía línea de base 2023." },
      { fecha: "2026-07-04", cambio: "Pasa a componente puntuable tras un banco de pruebas empírico: la canasta de ventana fija con cociente interno resultó estable entre actualizaciones y consistente con la inflación." },
      { fecha: "2026-08-21", cambio: "ADR-0222: la canasta pasa a seis términos con peso igual —entran dólar, empleo y corrupción, y sale trabajo, cuyas búsquedas asociadas son derecho laboral, un plan social, el feriado y la tarea escolar—. Cada término se consulta por separado y se compara contra su propia base, lo que reemplaza al promedio crudo, que pesaba por volumen de búsqueda. La card deja de ser un pulso aparte y publica el mismo último mes cerrado que el gráfico." },
    ],
  },

  motorizacion_total: {
    tipo: "indicador",
    id: "motorizacion_total",
    cinturon: "vida_cotidiana",
    rezago: "Menos de un mes: el registro publica cada mes en los primeros días del siguiente. Se toma el último mes calendario completo.",
    fuente: {
      organismo: "DNRPA — Dirección Nacional de los Registros Nacionales de la Propiedad del Automotor y de Créditos Prendarios (unidades) e INDEC (población)",
      operacion: "Inscripciones iniciales de automotores y de motovehículos (0 kilómetro), por mes y jurisdicción del registro seccional, sumadas y divididas por la población urbana total proyectada del INDEC.",
      serie: "Estadística de trámites de automotores (desde enero de 2000) y de motovehículos (desde enero de 2007)",
      url: "https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores",
      acceso: "Automático: CSV abierto sin credenciales. La dirección de descarga lleva el período adentro y cambia todos los meses, así que se descubre por catálogo en cada corrida en lugar de fijarse.",
    },
    transformaciones: [
      "Se suman las unidades de los dos registros —autos y motos— y se toma el acumulado móvil de 12 meses. La estacionalidad del flujo crudo es fuerte en los dos (enero pesa 1,36 veces el mes promedio en autos, y en motos duplica a junio), de modo que contra una base fija mediría calendario además de poder de compra.",
      "Pasaje a per cápita con la población urbana total proyectada del INDEC, interpolada a meses desde su serie trimestral.",
      "Componente del índice: el resultado rebaseado a 100 = promedio del 4º trimestre de 2023 (menos vehículos por habitante = deterioro).",
      "Se excluye Tierra del Fuego de las dos series. La provincia inscribió unas 29.000 motos en un solo año contra menos de 900 en cada uno de los dos anteriores, concentradas en ocho meses: es un movimiento registral de su régimen de promoción industrial, no compras de hogares fueguinos. La exclusión se aplica a la provincia entera y a toda la serie, porque recortar sólo los meses anómalos exigiría un umbral, y cualquier umbral que atrape una carga fiscal también atrapa un mes de cuarentena.",
      "Es el único componente EXENTO del techo de recorte de 140 que rige para el resto del índice. Con un peso de 1,11%, lo máximo que puede aportar por encima de ese techo son 0,33 puntos del índice, así que el techo acota una compensación que el peso ya acota. Y contra una base tomada en el 4º trimestre de 2023 —el fondo del congelamiento previo a la devaluación— el nivel 140 no marca un valor extremo: dos tercios de los meses de la década anterior lo habrían superado.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de ingresos y consumo (3,17% interno · 0,89% del ITCIS).",
      "Mide el acceso TOTAL a un vehículo 0 kilómetro, no la compra de un tipo de vehículo. La distinción decide el signo: cuando el patentamiento de motos sube, puede ser que hogares sin vehículo accedan al primero o que hogares con auto bajen de categoría, y las dos cosas mueven la serie de motos hacia arriba. El total las separa, porque un descenso de categoría deja el total plano: cada moto que entra tendría un auto que sale.",
      "La composición se publica junto al color: cuántos autos y cuántas motos hay detrás del total, y qué proporción de lo que se patenta son motos contra la proporción del arranque del mandato.",
    ],
    limitaciones: [
      "Es un FLUJO de altas, no el parque circulante: cuenta los vehículos que se incorporan, no los que hay. Un hogar que conserva el auto que ya tenía no aparece.",
      "Cuenta unidades, no gama ni precio: un auto de entrada de gama y uno caro se registran igual, y una moto pesa lo mismo que un auto en la suma. El registro no publica cilindrada ni valor, así que separar gamas exigiría otra fuente.",
      "Es una compra financiada: responde tanto al crédito prendario y a las condiciones de importación como al ingreso de los hogares. No distingue un hogar que puede más de un hogar que consigue cuota.",
      "La composición no es neutral, y el indicador no la puntúa. Los índices de pobreza multidimensional de referencia tratan al automóvil como un activo cuya sola tenencia saca al hogar de la privación, y a la motocicleta como un activo menor; los índices de riqueza que estiman el peso de cada bien en vez de suponerlo le asignan a la moto alrededor de un quinto del peso del auto. La escalera de activos existe y tiene peldaños. Que el total suba mientras la mezcla se corre a la moto es acceso y descenso de peldaño a la vez, y el color sólo refleja lo primero.",
      "Una suba del total puede venir de precios relativos y no de ingreso. El precio de adquirir un vehículo cayó en términos reales mientras el del transporte público más que se duplicó, así que parte de la motorización es un desplazamiento forzado desde el colectivo y no una mejora del bolsillo. El componente no separa esos dos motores.",
      "La inscripción es del registro seccional donde se hace el trámite, que no siempre coincide con dónde vive el comprador — la apertura por jurisdicción sirve para composición, no para geografía del consumo.",
      "Es un proxy de consumo durable, no de bienestar general.",
    ],
    faltantes: "El colector levanta excepción ante cualquier cambio de forma de la fuente —una columna que falta, un mes a medio cargar, una jurisdicción que cambia de nombre— en vez de publicar una serie recortada. Con la fuente caída, la card mantiene el último valor como desactualizado y la serie conserva sus puntos anteriores.",
    revisiones: "Los dos archivos publican su histórico completo y se rebajan enteros en cada corrida, así que una corrección de la fuente se incorpora sola.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITCIS el patentamiento de motos con rebase simple del flujo mensual; el mismo día pasa al acumulado móvil de 12 meses por la estacionalidad." },
      { fecha: "2026-07-04", cambio: "Se aplica al componente de motos el techo de recorte 140 y su peso interno baja de 10% a 5%." },
      { fecha: "2026-08-21", cambio: "Entra el patentamiento de autos como componente espejo, con el mismo peso y la misma transformación que motos (ADR-0223)." },
      { fecha: "2026-08-21", cambio: "Los dos vehículos se funden en la motorización total per cápita, que toma el peso combinado de ambos; autos y motos dejan de ser tarjetas y pasan a explicar el color desde adentro (ADR-0224). El motivo es que ninguna de las dos series por separado distingue acceso de descenso de categoría, y el total sí. Con el cambio, el componente deja de estar apoyado contra el techo de recorte —del que queda exento— y vuelve a moverse con la fuente. La fuente de motos pasa de la cámara al registro, que es lo único que permite excluir el movimiento registral de Tierra del Fuego." },
    ],
  },

  consumo_supermercados: {
    tipo: "indicador",
    id: "consumo_supermercados",
    cinturon: "vida_cotidiana",
    rezago: "Encadena dos demoras y por eso es de las cards más lentas del cinturón: el INDEC publica el mes de referencia unos 52 días después de terminado, y la API de series tarda unas dos semanas más en espejarlo. El último punto disponible tiene entre tres y cuatro meses según en qué parte de ese ciclo caiga la corrida.",
    fuente: {
      organismo: "INDEC",
      operacion: "Encuesta de supermercados — ventas a precios constantes, serie desestacionalizada",
      serie: "455.1_VENTAS_PREADA_0_M_44_44 · API de series de tiempo de datos.gob.ar, enero de 2017 en adelante",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-12-37",
      acceso: "Automático: API pública sin credenciales.",
    },
    transformaciones: [
      "Componente del índice: el índice de la fuente rebaseado a 100 = promedio del 4º trimestre de 2023 (más volumen comprado = mejora).",
      "Se usa la serie DESESTACIONALIZADA que publica el propio INDEC y no se la vuelve a suavizar. No es un detalle de implementación: aplanar la serie original con una media móvil de 12 meses la atrasa medio año, y ese atraso llega a invertir el signo de la relación — está medido, y es la razón por la que la regla del proyecto es tomar el ajuste estacional de la fuente antes que fabricarlo.",
      "Tampoco lleva promedio móvil de 12 meses, a diferencia de los patentamientos: esa transformación existe para sacarle el calendario a un flujo crudo, y acá el calendario ya está sacado.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de ingresos y consumo (20% interno · 5,61% del ITCIS).",
      "Es el único componente del índice que mide VOLUMEN EFECTIVAMENTE COMPRADO. Los otros diecisiete miden lo que entra al hogar (ingresos), lo que cuesta (precios), de dónde sale ese ingreso (empleo), lo que no se llega a pagar (mora), lo que se opina (percepción) o el delito sufrido. Ninguno mira lo que el hogar se llevó de la góndola.",
      "El peso surge de esa jerarquía: por encima de los dos proxies de compra realizada que ya había —una proteína y la motorización, que juntos no llegan al 8% de la dimensión— y por debajo de las dos medidas estructurales, la brecha entre salario y canasta y el conteo de pobreza.",
    ],
    limitaciones: [
      "Cubre comercio registrado de cadenas de supermercados: no ve el almacén de barrio, la feria ni el comercio informal, que es justamente donde se refugia parte del gasto cuando el ingreso se estrecha.",
      "Tampoco ve el traslado de compras al canal mayorista y de descuento. Ese canal se mueve en sentido contrario —comprar ahí es señal de ajuste, no de holgura— y por eso no se suma a este componente; se sigue publicando aparte, en el panel de contraste externo del cinturón.",
      "«A precios constantes» significa deflactado con índices de precios del propio INDEC, así que comparte insumo con el componente de precios de los alimentos. El solapamiento está declarado y medido: entre los dos la correlación es +0,558 en niveles y +0,058 al mirar los cambios mes a mes.",
      "Mide cantidad vendida, no calidad de lo comprado: un carrito que cambia primera marca por segunda a igual volumen se registra igual.",
    ],
    faltantes: "El colector levanta excepción si la serie no trae los tres meses de la base del 4º trimestre de 2023, en lugar de rebasear contra lo que haya: sin base, el componente mediría contra otra cosa sin que nada avisara. Con la fuente caída, la card mantiene el último valor como desactualizado.",
    revisiones: "La API devuelve el histórico completo en cada corrida, así que una revisión del INDEC —habituales en las series desestacionalizadas, que se recalculan al agregar meses— se incorpora sola y sin dejar huella de la versión anterior.",
    cambios: [
      { fecha: "2026-08-21", cambio: "Entra al ITCIS con 20% de la dimensión de ingresos y consumo, y los cinco componentes previos ceden proporcionalmente conservando su orden relativo (ADR-0225). Venía de ser el ancla de validación externa del cinturón: mide condiciones materiales del hogar, así que integra el índice en vez de juzgarlo — la misma regla que había sacado a la confianza del consumidor de ese papel." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // ITCG — índice compuesto del cinturón gestión (checklist OCDE/JRC)
  // ═══════════════════════════════════════════════════════════════════════
  itcg: {
    tipo: "indice",
    id: "itcg",
    sigla: "ITCG",
    nombreLargo: "Índice de Tensión del Cinturón de Gestión",
    cinturon: "gestion",
    resumen: "Mide si la agenda de reformas del gobierno se ejecuta, en una escala 0–100: 0 = el gobierno promete reformas pero no las ejecuta; 100 = agenda ejecutándose. Cinco dimensiones con umbrales y pesos de la paramétrica institucional CIGOB.",
    marcoConceptual: [
      "El cinturón de gestión mide la capacidad de ejecutar: el cumplimiento efectivo de la agenda de reformas (económicas, del Estado, laboral, privatizaciones, social y de orden público), no la popularidad del gobierno ni el resultado macroeconómico.",
      "El marco proviene de la «Fórmula Paramétrica para la Evaluación del Estado de Tensión — Cinturón de la Gestión» (Fundación CIGOB, julio de 2026). Los pesos de las cinco dimensiones y la estructura de la primera vienen del documento; los pesos internos de las restantes son operacionalización propia documentada.",
    ],
    seleccion: [
      "Quince indicadores puntúan en cinco dimensiones (la tabla de composición muestra la estructura vigente con los puntajes de hoy). El tablero solo muestra lo que integra el índice: dos series complementarias de conflictividad (alertas de manifestación y eventos de protesta) se siguen relevando como seguimiento interno, sin publicarse ni puntuar.",
      "Criterio de selección: fuentes públicas verificables y automatizables. El cinturón es íntegramente automático: el único registro curado a mano (privatizaciones) cita la norma del Boletín Oficial detrás de cada estado.",
    ],
    tratamiento: [
      "Indicadores faltantes: los pesos se renormalizan entre los presentes, primero dentro de la dimensión y luego entre dimensiones si una queda vacía.",
      "Juicio experto: la paramétrica admite ajustes manuales por indicador con justificación escrita y fecha de vencimiento (un ajuste vencido se ignora solo); todo ajuste activo se publica junto al índice.",
      "Varios indicadores llevan calibraciones declaradas (por ejemplo, «100 normas derogatorias = plan completo»): cada ficha las documenta.",
    ],
    normalizacion: [
      "Cada indicador, en su unidad original, se convierte a un puntaje 0–100 mediante los umbrales institucionales leídos como anclas de interpolación: cada banda finita ancla su puntaje en su punto medio, las abiertas en su borde; entre anclas el puntaje es lineal, en los extremos queda plano.",
      "Hasta julio de 2026 el puntaje era escalonado por banda; la interpolación eliminó los saltos entre valores casi iguales sin tocar los umbrales institucionales.",
    ],
    agregacion: {
      latex: String.raw`\text{ITCG}=\sum_{\text{5 dimensiones}}\text{peso}_{\text{dim}}\times\Big(\sum_{\text{indicadores}}\text{peso}_{\text{interno}}\times\text{puntaje}_{0\text{–}100}\Big)`,
      leyenda: "Promedio ponderado en dos niveles: dentro de cada dimensión y entre dimensiones (35% reformas económicas · 25% reforma del Estado · 15% laboral · 15% privatizaciones e inversión · 10% social y orden).",
      parrafos: [
        "La agregación es compensatoria: por eso el índice incluye el flag de dimensión crítica — si una dimensión cae por debajo de su umbral, se declara junto al valor publicado en lugar de dejar que el promedio la esconda.",
      ],
    },
    robustez: [
      "Análisis de sensibilidad Monte Carlo: el índice se recalcula en 1.000 escenarios perturbando los pesos ±20% y los insumos ±5% del rango entre anclas, re-puntuados por la escala interpolada. La banda del 90% de los escenarios se publica en cada edición.",
      "Se acompaña con el ejercicio de quitar cada componente por vez, para identificar cuál domina la lectura del mes.",
    ],
    validacion: [
      "El índice se reconstruye mes a mes desde diciembre de 2023 y se contrasta contra un ancla de mercado: el Merval medido en dólares. Se espera correlación positiva — el mercado de acciones pone precio a la ejecución de las reformas.",
      "El contraste discriminante se publica también: el ITCG correlaciona negativo con el índice de confianza en el gobierno (UTDT) en niveles — el índice mide gestión acumulada, no popularidad, y la diferencia es visible en los datos.",
    ],
    comunicacion: [
      "El resto del informe consume el índice como tensión 0–10: tensión = (100 − ITCG) / 10, con los umbrales globales de siempre (0–3 estable · 4–6 en tensión · 7–10 tensionado).",
      "Cada indicador publica su ficha, su fórmula, su tensión equivalente y los ajustes de analista activos, si los hay.",
    ],
    interpretacion: [
      { rango: "0 – 20", lectura: "Severamente apretado" },
      { rango: "21 – 40", lectura: "Apretado" },
      { rango: "41 – 60", lectura: "Moderadamente apretado" },
      { rango: "61 – 80", lectura: "Moderadamente aflojado" },
      { rango: "81 – 100", lectura: "Aflojado" },
    ],
    limitaciones: [
      "Mide ejecución de la agenda declarada, no la calidad ni el resultado de las reformas: un índice alto significa «se está haciendo lo prometido», no «lo prometido funciona».",
      "Varios indicadores usan calibraciones propias declaradas (planes completos, umbrales de avance) donde no existe una vara oficial.",
      "El análisis multivariado previo del estándar OCDE/JRC (contrastar la estructura teórica con la correlación real entre indicadores) está pendiente; la validación cruzada lo aproxima por las anclas externas.",
      "La ventana de validación es corta (los meses del mandato): las correlaciones se leen como consistencia, no como prueba.",
    ],
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial del cinturón: doce indicadores de cumplimiento de reformas con promedio simple de avances." },
      { fecha: "2026-07-02", cambio: "Nace el ITCG: la paramétrica institucional de cinco dimensiones reemplaza el promedio simple. Se automatizan en la misma tanda las concesiones, la desintermediación social y la opción en salud." },
      { fecha: "2026-07-03", cambio: "Revisión metodológica: puntaje interpolado entre anclas, flag de dimensión crítica, la brecha cambiaria deja de contar dos veces (sale del compuesto de apertura), y la litigiosidad entra al índice como resultado de la reforma laboral. El protocolo de orden público se automatiza con anclajes públicos." },
      { fecha: "2026-07-04", cambio: "Matriz de validación cruzada como tercer pilar de robustez, con el Merval en dólares como ancla propia del índice." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // ITCIS — índice base-100 del cinturón de impacto social (checklist OCDE/JRC)
  // ═══════════════════════════════════════════════════════════════════════
  itvc: {
    tipo: "indice",
    id: "itvc",
    sigla: "ITCIS",
    nombreLargo: "Índice de Tensión del Cinturón de Impacto Social",
    base100: true,
    cinturon: "vida_cotidiana",
    resumen: "Índice de seguimiento base 100: cada componente se compara contra el promedio del 4º trimestre de 2023 (el arranque del mandato). Más de 100 = mejora acumulada en las condiciones de vida; menos de 100 = deterioro. Diecinueve componentes en seis dimensiones.",
    marcoConceptual: [
      "El cinturón de impacto social mide el bolsillo y la calle: ingresos contra canasta, precios sensibles, la mora de las familias con el crédito, el empleo y sus prospectivas, y el clima de confianza y seguridad.",
      "El marco proviene del documento institucional del índice en versión base 100 (Fundación CIGOB, julio de 2026), heredero del Monitor de la Vida Cotidiana de mayo de 2026. A diferencia del ITCM y el ITCG, no usa tablas de umbrales: mide la evolución acumulada contra una línea de base común — el arranque del mandato.",
    ],
    seleccion: [
      "Diecinueve componentes en seis dimensiones (la tabla muestra la composición vigente con los niveles de hoy). Todos puntúan: el cinturón no tiene indicadores de contexto — lo que no integra el índice no se publica como tarjeta.",
      "Criterio: fuentes públicas con serie reconstruible al 4º trimestre de 2023 — o con línea de base declarada donde no existe medición de entonces (la encuesta de victimización arranca su base en enero de 2024, documentado).",
    ],
    tratamiento: [
      "Componentes faltantes: los pesos se renormalizan dentro de la dimensión y entre dimensiones; ante una fuente caída, el indicador mantiene su último valor publicado marcado como desactualizado.",
      "Polaridad: los componentes donde «más es peor» —informalidad, mora de las familias, pluriempleo, peso del trabajo independiente, victimización y búsquedas de urgencia— se invierten para que en todos valga la misma lectura: por encima de 100, mejora.",
      "Recorte asimétrico declarado: los componentes se acotan a un techo de 140 (un boom puntual no compra compensación ilimitada) y deliberadamente NO tienen piso — el deterioro no se recorta, se señaliza con el flag de dimensión crítica.",
    ],
    normalizacion: [
      "Cada componente es un índice continuo rebaseado a 100 = promedio del 4º trimestre de 2023 (o su base declarada). No hay bandas ni anclas: la normalización es el rebase, y las transformaciones por componente (acumulados móviles, deflactación, relativos al IPC general) están documentadas en cada ficha.",
    ],
    agregacion: {
      latex: String.raw`\text{ITCIS}=\sum_{\text{6 dimensiones}}\text{peso}_{\text{dim}}\times\Big(\sum_{\text{componentes}}\text{peso}_{\text{interno}}\times\min(\text{componente},140)\Big)`,
      leyenda: "Promedio ponderado en dos niveles (28,06% ingresos y consumo · 25% presión de precios · 24,19% prospectivas de empleo · 10% vulnerabilidad financiera · 8,25% confianza y percepción · 4,5% seguridad), con el techo de recorte declarado.",
      parrafos: [
        "La agregación es compensatoria y el flag de dimensión crítica lo declara cuando una dimensión cae por debajo del umbral. Cuáles están marcadas se lee en la tabla de composición, que se recalcula con cada actualización: nombrarlas acá dejaría el texto viejo al mes siguiente.",
        "El índice y la tensión son DOS ESCALAS DISTINTAS y conviene no confundirlas. El índice suma niveles: cada componente vale lo que vale contra su base de 2023, y esos números se promedian. La tensión es una lectura del resultado —5 − (índice − 100) × 0,2, recortada al rango 0-10— pensada para ponerlo en la misma vara que los otros cinturones. La tensión que aparece en la ficha de cada componente aplica esa misma fórmula a ese componente solo, y sirve para leerlo, no para calcular: al índice entra el nivel, nunca la tensión.",
        "Eso explica algo que sorprende: varios componentes muestran una tensión de 0 o de 10 a la vez. No es que midan lo mismo — es que la escala 0-10 se corta ahí, y su tensión sin recortar seguiría subiendo o bajando. Cada ficha publica ese valor sin recortar junto al recortado, para que el techo no esconda la diferencia.",
        "Hay además un segundo recorte, éste sí sobre el número que entra al índice: ningún componente puede superar 140 (un salto puntual de uno solo no compra compensación ilimitada en el promedio). El recorte es sólo hacia arriba: las caídas no se recortan, se señalizan con el flag de dimensión crítica. Qué componentes están recortados y cuánto resta el recorte se publica en la ficha de cada uno y en la tabla de composición, porque cambia mes a mes",
      ],
    },
    robustez: [
      "Análisis de sensibilidad Monte Carlo: el índice se recalcula en 1.000 escenarios perturbando los pesos ±20% (al ser componentes continuos, el ruido de insumos llega vía el propio rebase). La banda del 90% de los escenarios se publica en cada edición.",
      "Se acompaña con el ejercicio de quitar cada componente por vez.",
    ],
    validacion: [
      "El índice se reconstruye mes a mes desde diciembre de 2023 y se contrasta contra un PANEL de estadísticas externas, no contra una sola. No es una preferencia de método: no hay una serie única en condiciones de hacer de referencia, y el motivo forma parte del resultado.",
      "El ancla era el consumo medido —las ventas en supermercados a precios constantes del INDEC— y dejó de serlo porque pasó a ser COMPONENTE del índice. Mide condiciones materiales del hogar, así que le corresponde integrar el ITCIS y no juzgarlo: es la misma regla que antes había desplazado a la confianza del consumidor, que también componía el índice.",
      "El reemplazo conceptualmente correcto está identificado y declarado: el consumo privado que el INDEC publica en las Cuentas Nacionales a precios constantes. No es un canal del consumo del hogar sino su agregado, que es exactamente lo que el cinturón dice medir. Todavía no puede usarse: es trimestral y arranca junto con la base del índice, así que la muestra son nueve trimestres y la correlación en primeras diferencias se mueve entre 0,17 y 0,73 según qué trimestre se quite. Un número que depende de cuál dato se saque no es un número publicable.",
      "El umbral de promoción queda fijado por adelantado, antes de volver a mirar la correlación: pasa a ser la serie de referencia del cinturón cuando acumule 20 trimestres, hacia fines de 2028. Fijarlo ahora es lo que impide que la decisión termine dependiendo del número que dé ese día.",
      "Su solapamiento con el índice también queda declarado y medido, porque el consumo privado contiene a las ventas en supermercados, que ahora son componente: la encuesta de supermercados representa el 4,49% del consumo privado en promedio del período (5,68% al inicio, 3,68% en el último trimestre disponible). El acoplamiento existe, es de segundo orden y se publica en vez de omitirse.",
      "Mientras tanto el contraste es el panel completo, y el gráfico compara el índice contra el FACTOR COMÚN de las estadísticas de su terreno que miden volúmenes físicos consumidos por el hogar —electricidad, gas, transporte, combustible—: lo que todas ellas comparten, en lugar de cualquiera de ellas suelta. Las cargas de cada una y la varianza que el factor explica se publican acá abajo.",
      "Del panel se reportan dos promedios —contra las estadísticas del propio terreno y contra las ajenas— y la brecha entre ambos, en niveles y en primeras diferencias. La segunda es la que manda: en una muestra de unos treinta meses casi todas las series argentinas comparten la tendencia del período, así que un valor alto en niveles puede ser sólo eso.",
      "La confianza del consumidor se sigue publicando como contraste que DISTINGUE en vez de confirmar: sirve para mostrar que la percepción y las condiciones materiales no son lo mismo. Que ese número sea más bajo no es una falla del índice, es el resultado.",
      "La matriz de validación cruzada compara además cada índice del informe contra todos los contrastes a la vez, para ver si correlaciona más con el propio que con los ajenos. No se cumple en todos los casos y la matriz lo declara.",
    ],
    comunicacion: [
      "El resto del informe consume el índice como tensión 0–10 con su propia fórmula: tensión = 5 − (ITCIS − 100) × 0,2. Un índice en 100 (sin cambios contra el arranque) equivale a tensión 5; cada 5 puntos de índice mueven un punto de tensión.",
      "Cada componente publica su ficha con la transformación exacta, su nivel actual y su peso.",
    ],
    interpretacion: [
      { rango: "> 110", lectura: "Mejora sustancial vs. 4T-2023" },
      { rango: "105 – 110", lectura: "Mejora moderada" },
      { rango: "95 – 105", lectura: "Sin cambios apreciables" },
      { rango: "85 – 95", lectura: "Deterioro moderado" },
      { rango: "< 85", lectura: "Deterioro sustancial" },
    ],
    limitaciones: [
      "Mide evolución contra un punto de partida, no niveles absolutos: un país que arranca mal y mejora poco puntúa mejor que uno que arranca bien y empeora poco.",
      "El punto de partida (4º trimestre de 2023) contiene la devaluación de diciembre: parte de las mejoras medidas es rebote del pozo — auditado y declarado, con la base mantenida por diseño del documento institucional.",
      "Dos discusiones de diseño están abiertas y declaradas: el peso de la brecha salarial (17,06%, el mayor del índice) y el signo con el que puntúa el trabajo independiente, que admite leerse como precarización o como emprendedorismo.",
      "El análisis multivariado previo del estándar OCDE/JRC está pendiente; la eliminación del doble conteo salario/comida (detectado por correlación casi perfecta entre dos componentes) fue un paso en esa dirección.",
    ],
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial del cinturón: fórmulas de tensión ancladas por indicador, promediadas." },
      { fecha: "2026-07-03", cambio: "Nace el ITCIS base 100: reemplaza el promedio de fórmulas ancladas por la evolución acumulada contra el 4º trimestre de 2023, con robustez Monte Carlo y flag de dimensión crítica publicados. Los patentamientos pasan al acumulado móvil de 12 meses por estacionalidad." },
      { fecha: "2026-07-04", cambio: "Barrido componente por componente: la victimización pasa de la serie anual de denuncias a la encuesta mensual; se elimina el doble conteo salario/comida (dos componentes correlacionaban 0,985); se aplica el techo de recorte 140 sin piso; el sentimiento digital pasa a puntuar tras un banco de pruebas empírico; y la matriz de validación cruzada queda como tercer pilar de robustez." },
      { fecha: "2026-07-15", cambio: "La mora de las familias se separa como indicador propio de la dimensión de vulnerabilidad financiera (antes iba multiplicada dentro del endeudamiento): la deuda mide el acceso al crédito y la mora, si esa deuda se puede pagar. El índice pasa a catorce indicadores puntuables y la dimensión reparte 50/50." },
      { fecha: "2026-08-19", cambio: "El cinturón pasa a llamarse Impacto Social y el índice, ITCIS (ADR-0212). Cambia la etiqueta, no la composición: ninguna clave de datos, ninguna serie y ningún peso se tocan." },
      { fecha: "2026-08-20", cambio: "La informalidad se muda de la dimensión de ingresos y consumo a la de prospectivas de empleo, que es donde mide (ADR-0214). Los pesos de las dos dimensiones se ajustan para que el peso efectivo de cada componente quede intacto: se mueve de casa, no de importancia. Ingresos pasa de 37% a 28,06% y empleo de 15% a 24,19%." },
      { fecha: "2026-08-20", cambio: "El componente de proteína animal pasa a puntuar el consumo TOTAL de carnes y no la carne vacuna sola (ADR-0217): buena parte de la caída de la vacuna es sustitución hacia pollo y cerdo, y leerla como pérdida de poder adquisitivo era un falso positivo. La vacuna sigue relevándose como diagnóstico, sin tarjeta propia." },
      { fecha: "2026-08-21", cambio: "Dos cambios en la dimensión de empleo. El cierre de PyMEs pasa a medirse con los empleadores activos de la SRT en lugar del IPI manufacturero, que era una aproximación por producción industrial (ADR-0218). Y entra el peso del trabajo independiente como su contracara (ADR-0219). El índice queda con diecisiete componentes y cuatro de los seis de la dimensión miden empleo directamente." },
      { fecha: "2026-08-21", cambio: "Entra el patentamiento de autos a la dimensión de ingresos y consumo, con el mismo peso y la misma transformación que el de motos (ADR-0223). El índice queda con dieciocho componentes. La razón no es sumar un dato más de consumo: con motos solas, un aumento del patentamiento se lee siempre como mejora, y la moto es además el sustituto barato del auto. Las dos series juntas distinguen más consumo de bajar de categoría." },
      { fecha: "2026-08-21", cambio: "Las ventas en supermercados a precios constantes dejan de ser el ancla de validación externa y entran como componente de la dimensión de ingresos y consumo, con 20% interno (ADR-0225). El índice queda con dieciocho componentes y es la primera vez que uno mide volumen efectivamente comprado. En el mismo movimiento el cinturón deja de tener ancla única y su contraste pasa a ser el panel: el reemplazo natural —el consumo privado de las Cuentas Nacionales— existe pero todavía tiene nueve trimestres, y queda declarado como referencia en formación con su umbral de promoción fijado de antemano." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // ITCP — índice compuesto del cinturón político (checklist OCDE/JRC)
  // ═══════════════════════════════════════════════════════════════════════
  itcp: {
    tipo: "indice",
    id: "itcp",
    sigla: "ITCP",
    nombreLargo: "Índice de Tensión del Cinturón Político",
    cinturon: "politica",
    resumen: "Mide el capital político del gobierno —la capacidad de gobernar con otros actores, no la popularidad— en una escala 0–100: 0 = mínimo capital político, 100 = máximo. Cinco dimensiones con pesos editoriales explícitos, sin documento institucional previo que los fije.",
    marcoConceptual: [
      "El cinturón político mide el capital político del gobierno según el marco de Carlos Matus (Política, Planificación y Gobierno): la capacidad de gobernar con otros actores —el Congreso, los gobernadores, el propio bloque legislativo, la calle—, no la popularidad medida en encuestas. Se organiza en cinco dimensiones: poder legislativo, alianzas territoriales, cohesión interna del oficialismo, conflicto social e imagen y voto.",
      "A diferencia del ITCM, el ITCG y el ITCIS, no existe un documento institucional que fije los pesos de estas cinco dimensiones: el marco ya las describía, pero nunca se habían ponderado. Los pesos son una decisión editorial explícita, apoyada en esa misma distinción del marco: la dimensión de imagen y voto pesa deliberadamente menos que las otras cuatro, porque el proyecto distingue capital político de popularidad electoral.",
    ],
    seleccion: [
      "Once indicadores puntúan en cinco dimensiones (la tabla de composición de abajo muestra la estructura vigente con los puntajes de hoy). El tablero publica solo lo que integra el índice: dos mediciones que quedaron fuera del puntaje (la rotación del gabinete y las protestas en la Ciudad de Buenos Aires) se siguen relevando como seguimiento interno, sin tile propio. Reemplaza a un promedio simple de nueve indicadores que pesaba todo por igual, sin distinguir la capacidad de gobernar de la popularidad.",
      "Criterio de selección: fuentes públicas verificables y automatizables. El alineamiento de los gobernadores —una estimación manual sin fuente pública estructurada— se retiró del índice en julio de 2026 y lo reemplazó el alineamiento de voto de los senadores por provincia, una conducta observable.",
      "La revisión editorial de julio de 2026 acotó el alcance del índice a la capacidad del gobierno de gestionar y avanzar su agenda —el Parlamento, las alianzas territoriales y la cohesión del oficialismo—: la rotación del gabinete y el volumen de protesta quedaron fuera del puntaje y del tablero, aunque su recolección continúa (mismo criterio que los insumos monetarios del índice macroeconómico).",
    ],
    tratamiento: [
      "Indicadores faltantes: los pesos se renormalizan entre los presentes, primero dentro de la dimensión y, si una dimensión queda vacía, entre dimensiones.",
      "Juicio experto: la paramétrica admite ajustes manuales por indicador con justificación escrita y fecha de vencimiento (un ajuste vencido se ignora solo); todo ajuste activo se publica junto al índice.",
      "Varios indicadores del cinturón son incorporaciones o redefiniciones de julio de 2026: sus series mensuales se reconstruyeron hacia atrás desde las fuentes y sus umbrales se calibraron contra esa historia. La excepción es la adhesión provincial, cuyos umbrales no se recalibraron porque la adhesión es un proceso acumulativo todavía en curso.",
    ],
    normalizacion: [
      "Cada indicador, en su unidad original, se convierte a un puntaje 0–100 mediante umbrales por banda, leídos como anclas de interpolación: cada banda finita ancla su puntaje en su punto medio, las abiertas en su borde; entre anclas el puntaje es lineal, en los extremos queda plano.",
      "A diferencia de ITCM/ITCG, cuyos umbrales provienen de un documento institucional, acá los umbrales de los indicadores originales heredan el criterio de la fórmula que reemplazan, y los de los indicadores incorporados en julio de 2026 se calibraron contra la serie mensual reconstruida de cada uno (la ficha de cada indicador documenta sus cortes y su calibración).",
    ],
    agregacion: {
      latex: String.raw`\text{ITCP}=\sum_{\text{5 dimensiones}}\text{peso}_{\text{dim}}\times\Big(\sum_{\text{indicadores}}\text{peso}_{\text{interno}}\times\text{puntaje}_{0\text{–}100}\Big)`,
      leyenda: "Promedio ponderado en dos niveles: dentro de cada dimensión y entre dimensiones (30% poder legislativo · 25% alianzas territoriales · 20% cohesión interna del oficialismo · 15% conflicto social · 10% imagen y voto).",
      parrafos: [
        "La agregación es compensatoria: una dimensión alta puede tapar una baja. Por eso el índice incluye el flag de dimensión crítica: si una dimensión cae por debajo de su umbral, se declara junto al valor publicado en lugar de dejar que el promedio la esconda.",
      ],
    },
    robustez: [
      "Análisis de sensibilidad Monte Carlo: el índice se recalcula en 1.000 escenarios perturbando los pesos ±20% y los insumos ±5% del rango entre anclas, re-puntuados por la escala interpolada. La banda donde cae el 90% de los escenarios se publica junto al valor en cada edición.",
      "Se acompaña con el ejercicio de quitar cada componente por vez, para identificar cuál domina la lectura del mes.",
    ],
    validacion: [
      "El ITCP se contrasta contra el EPU de Argentina (Economic Policy Uncertainty: minería de texto sobre diarios locales, la misma familia metodológica que el índice de Baker/Bloom/Davis): el índice reconstruido mes a mes se correlaciona contra el EPU, con correlación esperada negativa (más capital político, menos incertidumbre de política en la prensa). El resultado se publica en la sección de validación del cinturón.",
      "Participa además de la matriz de validación cruzada que compara los cuatro índices del informe contra sus cuatro anclas externas a la vez, publicada en la página del cinturón.",
    ],
    comunicacion: [
      "El resto del informe consume el índice como tensión 0–10: tensión = (100 − ITCP) / 10, con los mismos umbrales globales de siempre (0–3 estable · 4–6 en tensión · 7–10 tensionado).",
      "Cada indicador del cinturón publica su ficha, su fórmula y su tensión equivalente, junto con los ajustes de analista activos, si los hay.",
    ],
    interpretacion: [
      { rango: "0 – 20", lectura: "Severamente apretado" },
      { rango: "21 – 40", lectura: "Apretado" },
      { rango: "41 – 60", lectura: "Moderadamente apretado" },
      { rango: "61 – 80", lectura: "Moderadamente aflojado" },
      { rango: "81 – 100", lectura: "Aflojado" },
    ],
    limitaciones: [
      "Los pesos de las cinco dimensiones no provienen de un documento institucional previo, a diferencia de los otros tres índices del informe: son una decisión editorial explícita, declarada como tal.",
      "Varios de los indicadores son incorporaciones de julio de 2026: sus umbrales se calibraron contra series mensuales reconstruidas de unos dos años — una historia real pero corta, que cubre un solo gobierno.",
      "Su validación externa es la más reciente del sistema: varios componentes tienen historia corta y la reconstrucción de los meses más antiguos se apoya en los indicadores de serie más larga (con un piso de cobertura declarado) — las correlaciones se leen como consistencia, no como prueba.",
      "El alineamiento territorial se mide por el comportamiento de voto de los senadores, no por la postura del Poder Ejecutivo provincial: no existe todavía una fuente pública estructurada que mida directamente el alineamiento de los gobernadores.",
      "El análisis multivariado previo del estándar OCDE/JRC (contrastar la estructura teórica con la correlación real entre los indicadores) está pendiente, igual que en el resto de los índices del informe.",
    ],
    cambios: [
      { fecha: "2026-07-07", cambio: "Nace el ITCP: reemplaza al promedio simple de nueve indicadores por la paramétrica de cinco dimensiones ponderadas, con flag de dimensión crítica y ajustes de analista con vencimiento. Se incorporan tres indicadores —cohesión de bloque en el Senado, adhesión provincial a un régimen de inversión y variación de protestas en la Ciudad de Buenos Aires— y se redefine la cohesión de bloque en Diputados, de una estimación manual a un cálculo automático sobre las votaciones nominales." },
      { fecha: "2026-07-08", cambio: "El alineamiento de gobernadores (estimación manual, congelada por falta de fuente) se retira del índice; lo reemplaza el alineamiento de voto de los senadores por provincia, calculado en forma automática de las votaciones nominales del Senado." },
      { fecha: "2026-07-09", cambio: "Recalibración contra historia real: los umbrales de la cohesión de bloque (ambas cámaras), el alineamiento de senadores y las protestas se recalibran con series mensuales reconstruidas desde las fuentes (24 a 31 meses). Se publica la validación externa del índice contra el EPU de Argentina." },
      { fecha: "2026-07-09", cambio: "Se incorporan dos indicadores: las derrotas legislativas del Ejecutivo (vetos insistidos y decretos rechazados, acumulados en 12 meses) en la dimensión de poder legislativo, y la rotación del gabinete en la de cohesión interna." },
      { fecha: "2026-07-10", cambio: "Revisión editorial del cinturón: el índice se acota a la capacidad de gestionar y avanzar la agenda de gobierno. La rotación del gabinete y las protestas en la Ciudad de Buenos Aires salen del puntaje y del tablero (su recolección continúa como seguimiento interno), y la cohesión del bloque en Diputados y en el Senado se fusiona en un único indicador bicameral (Diputados 65%, Senado 35%), con umbrales recalibrados contra la serie compuesta." },
      { fecha: "2026-07-11", cambio: "En la dimensión de conflicto social, la conflictividad nacional (eventos de protesta y disturbios de todo el país, serie mensual completa) reemplaza a la medición anterior basada en informes de conflictividad, que no permitía una serie comparable." },
      { fecha: "2026-07-15", cambio: "Las comisiones sin sanción salen del puntaje: su fuente es ciega a las sanciones del Senado y se solapa con la eficacia legislativa corregida. Poder legislativo queda con cuatro indicadores." },
      { fecha: "2026-07-16", cambio: "Se incorpora el bloqueo legislativo sostenido a la dimensión de poder legislativo: la contracara de las derrotas (qué porción de las normas propias desafiadas en el recinto sigue en pie). El índice pasa a once indicadores puntuables y los pesos internos de la dimensión se redistribuyen." },
    ],
  },
};
