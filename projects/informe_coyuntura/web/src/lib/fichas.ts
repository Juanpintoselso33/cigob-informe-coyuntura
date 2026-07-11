// ── Fichas metodológicas (/metodologia) ─────────────────────────────────────
// El estándar de documentación por indicador del informe. La estructura adapta
// tres referencias de la industria estadística:
//   · el template de metadatos de indicadores ODS (IAEG-SDGs, Naciones Unidas):
//     definición, fuentes, método de cómputo (4.c), limitaciones (4.b),
//     tratamiento de faltantes (4.g);
//   · la ficha metodológica de los institutos de estadística (DANE/INE);
//   · las "data pages" de Our World in Data (última actualización, linaje del
//     dato, "lo que hay que saber para leerlo").
// Para los índices compuestos (ITCM/ITCG/ITVC) las secciones siguen el
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
  cinturon: "macro" | "politica" | "vida_cotidiana" | "gestion" | "espiritu_epoca";
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
  base100?: boolean;                // índice de seguimiento base 100 (ITVC): sin techo,
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
    ],
    faltantes: "Si al calcular el índice el dato del mes no está publicado, el indicador queda fuera de esa corrida y los pesos de su dimensión se renormalizan entre los presentes: la ausencia no puntúa ni a favor ni en contra.",
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
    resumen: "Mide la tensión del cinturón macroeconómico en una escala 0–100: 0 = cinturón severamente apretado (máxima tensión), 100 = aflojado. Doce indicadores en seis dimensiones, con umbrales y pesos de la paramétrica institucional CIGOB.",
    marcoConceptual: [
      "El informe lee la realidad como un sistema de cinco cinturones que rodean al gobierno (Planificación Estratégica Situacional de Carlos Matus). El cinturón macroeconómico agrupa los indicadores del motor económico: precios, cuentas fiscales y externas, financiamiento, actividad, competitividad e inversión.",
      "El marco, las dimensiones, los umbrales y los pesos provienen de un documento institucional: «Fórmula Paramétrica para la Evaluación del Estado de Tensión — Cinturón de la Macroeconomía» (Fundación CIGOB, mayo de 2026). El índice no estima esos parámetros a partir de los datos: los toma del marco y luego mide — con las herramientas de robustez de abajo — cuánto dependen las conclusiones de esa elección.",
    ],
    seleccion: [
      "Doce indicadores agrupados en seis dimensiones (la tabla de composición de abajo muestra la estructura vigente con los puntajes de hoy). Criterio de selección: fuentes públicas oficiales (INDEC, BCRA, ARCA), extracción automatizable y serie histórica reconstruible al inicio del mandato (diciembre de 2023).",
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
      "El índice se reconstruye mes a mes desde diciembre de 2023 y se contrasta contra un ancla externa que nadie del proyecto controla: el riesgo país (EMBI). Se espera correlación negativa — a menor tensión macroeconómica, menor riesgo percibido por el mercado.",
      "La asociación es de tendencia y de media frecuencia, no de mes a mes: reaparece con fuerza en ventanas semestrales pero es nula en los saltos de un mes, porque el mercado reacciona en el día mientras el índice publica con el rezago y el suavizado de sus fuentes — el ITCM describe la macro, no anticipa al mercado. Los sobresaltos mensuales del riesgo país suelen ser políticos antes que macroeconómicos. Ambas correlaciones (niveles y cambios mes a mes) se publican en la página del cinturón.",
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
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Planilla_reservas.asp",
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
    faltantes: "Si la planilla no está disponible, el cálculo cae a las reservas brutas de la API menos los últimos drenajes conocidos; si todo falla, se usa el último valor en caché marcado como desactualizado y los pesos del índice se renormalizan.",
    revisiones: "La planilla publicada no se revisa; el informe reconstruye la serie completa releyendo todas las planillas disponibles en cada corrida.",
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
      acceso: "Automático: API pública del BCRA y API de series de datos.gob.ar; el índice se calcula en el pipeline.",
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
      "Los desvíos se recalculan contra la historia completa en cada corrida: los puntos históricos pueden moverse levemente entre ediciones.",
    ],
    faltantes: "Si la historia disponible baja de 60 meses o falla algún insumo, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión de financiamiento se renormalizan.",
    revisiones: "Al redefinirse la métrica, el histórico de la versión anterior se purgó: la serie publicada es homogénea. Se regenera completa en cada corrida.",
    cambios: [
      { fecha: "2026-06-26", cambio: "Nace el IdC en reemplazo de la tasa BADLAR dentro de la dimensión de financiamiento, como índice de ratios mensuales." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "Rediseño completo tras una auditoría interna: de ratios mes a mes (que medían la variación, no el estado, y contaban dos veces los depósitos) a niveles estandarizados contra la propia historia, publicados en desvíos estándar." },
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
    dobleUso: "La misma serie se extrae también como insumo de contexto en el cinturón de vida cotidiana.",
    limitaciones: [
      "El EMAE es provisorio y el INDEC lo revisa hacia atrás con cada publicación; la serie del informe absorbe esas revisiones al regenerarse.",
      "Es la única variable de su dimensión: el 11% del índice cuelga de un solo dato.",
    ],
    faltantes: "Si el dato falta, se usa el último valor en caché marcado como desactualizado; sin dato ni caché, la dimensión de actividad queda vacía y su peso se redistribuye entre las demás.",
    revisiones: "La fuente revisa (serie provisoria); el informe regenera la serie completa en cada corrida y puntúa siempre el último dato publicado, sin proyecciones propias.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original como única variable de actividad; su peso de dimensión bajó de 15% a 13% y luego a 11% al incorporarse las dimensiones de competitividad e inversión." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
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
      acceso: "Automático: API pública de series de tiempo; el saldo se calcula en el pipeline.",
    },
    transformaciones: [
      "Saldo acumulado de 12 meses: suma de exportaciones menos suma de importaciones de los últimos 12 meses comunes de ambas series.",
      "El acumulado anual elimina la estacionalidad energética y sojera.",
      "Regla automática declarada: si hay superávit pero se explica por una caída de importaciones mayor que el aumento de exportaciones (contracción de la demanda interna, no éxito exportador), el puntaje se rebaja a 60 con la justificación generada a partir de los números.",
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
      "El acumulado de 12 meses suaviza a costa de reactividad: un vuelco del frente comercial tarda meses en reflejarse por completo.",
      "El máximo alcanzable de la escala es 85, no 100: diseño del documento institucional.",
      "Los datos del ICA son provisorios y se revisan; la serie regenerada por corrida los absorbe.",
    ],
    faltantes: "Con las series del ICA caídas, el cálculo cae a la serie de saldo directa (más rezagada y sin composición, con la regla automática muda); después, caché marcado como desactualizado y renormalización.",
    revisiones: "La fuente revisa provisorios; el informe re-descarga la serie completa en cada corrida.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original, calculado por las series de exportaciones e importaciones del ICA (frescas a ~2 meses) en lugar de la serie de saldo directa (~14 meses de rezago), con la regla de superávit por contracción automatizada." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "La serie del gráfico pasó del saldo mensual al acumulado móvil de 12 meses — la métrica del titular." },
    ],
  },

  recaudacion: {
    tipo: "indicador",
    id: "recaudacion",
    cinturon: "macro",
    rezago: "La recaudación del mes se publica en los primeros días del mes siguiente, pero el indicador espera el IPC que la deflacta: el mes más fresco se muestra como provisorio y no puntúa.",
    fuente: {
      organismo: "Secretaría de Hacienda (dato primario de ARCA); deflactor: INDEC",
      operacion: "Recaudación tributaria total mensual, en pesos corrientes, deflactada por el IPC nacional",
      serie: "172.3_TL_RECAION_M_0_0_17 + IPC 148.3_INIVELNAL_DICI_M_26 · API de datos.gob.ar",
      url: "https://www.argentina.gob.ar/economia/ingresos-publicos",
      acceso: "Automático: API pública de series de tiempo; deflactación y promedio en el pipeline.",
    },
    transformaciones: [
      "Variación interanual real por mes: la recaudación contra el mismo mes del año anterior, descontada la inflación.",
      "Promedio móvil de los últimos tres meses con IPC cerrado, para filtrar el calendario tributario (vencimientos, anticipos).",
      "El mes más fresco se publica solo como contexto, con deflactor provisorio, sin puntuar.",
    ],
    anclas: {
      bandas: [
        { banda: "> 10", puntaje: 100 },
        { banda: "5 – 10", puntaje: 80 },
        { banda: "0 – 5", puntaje: 60 },
        { banda: "−5 – 0", puntaje: 40 },
        { banda: "≤ −5", puntaje: 10 },
      ],
      puntos: [[-5, 10], [-2.5, 40], [2.5, 60], [7.5, 80], [10, 100]],
      unidadCorta: "% i.a. real (3m)",
    },
    limitaciones: [
      "El promedio trimestral mitiga pero no elimina el calendario tributario; antes del suavizado, el índice oscilaba varios puntos por puro ruido de vencimientos.",
      "Es el componente más pesado del índice (14,4%): cualquier defecto acá es el que más mueve el titular.",
      "Deflactor único (IPC nacional), sin deflactor específico de la base imponible.",
    ],
    faltantes: "Con menos de tres meses reales disponibles, se usa el último valor en caché marcado como desactualizado; sin dato, el saldo comercial pasa a explicar toda la dimensión fiscal-comercial.",
    revisiones: "La serie de recaudación no se revisa hacia atrás. Validación externa documentada: la estimación propia del mes provisorio quedó a 0,3 puntos de la de un instituto fiscal independiente.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original, entonces como variación mensual nominal." },
      { fecha: "2026-06-26", cambio: "Pasa a variación interanual real deflactada por IPC: la variación nominal confundía inflación con recaudación." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
      { fecha: "2026-07-04", cambio: "Pasa a promedio móvil de tres meses sobre meses con IPC cerrado; el mes fresco queda como provisorio sin puntuar." },
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
      acceso: "Automático: descarga y lectura de la planilla oficial; una sola descarga por corrida sirve al índice y a los bilaterales de contexto.",
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
    faltantes: "Con la planilla caída, cae a la serie histórica alternativa (discontinuada a fines de 2024, marcada desactualizada); después, caché y renormalización.",
    revisiones: "El índice oficial no se revisa hacia atrás de forma habitual; la serie del informe se reconstruye completa de la planilla en cada corrida.",
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
    faltantes: "Si el dato falta, se usa el último valor en caché marcado como desactualizado; sin dato, el IPC y el IDM renormalizan dentro de la dimensión de estabilidad monetaria.",
    revisiones: "El REM publicado no se revisa: cada mes es un relevamiento nuevo.",
    cambios: [
      { fecha: "2026-06", cambio: "En el índice desde la paramétrica original, con bandas absolutas sobre el nivel anual." },
      { fecha: "2026-06-26", cambio: "Pasa a puntuarse por el equivalente mensual con las bandas del IPC, tras descartarse una versión intermedia por brecha contra el ritmo corriente." },
      { fecha: "2026-06-28", cambio: "Su peso interno baja de 50% a 30% de la dimensión al entrar el IDM." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  idm: {
    tipo: "indicador",
    id: "idm",
    cinturon: "macro",
    rezago: "Necesita el IPC cerrado para deflactar: se publica para el último mes con IPC disponible, unas dos semanas después de mediados del mes siguiente.",
    fuente: {
      organismo: "BCRA (agregados monetarios) + INDEC (IPC como deflactor)",
      operacion: "Agregados monetarios privados: circulante en poder del público, depósitos privados y M2 privado; índice de elaboración propia",
      serie: "API de Estadísticas Monetarias del BCRA (variables 17, 100 y 197) + IPC 148.3_INIVELNAL_DICI_M_26",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp",
      acceso: "Automático: API pública del BCRA y API de series de datos.gob.ar; la brecha se calcula en el pipeline.",
    },
    transformaciones: [
      "M3 privado construido = circulante en poder del público + depósitos privados, a fin de mes (no existe como serie directa del BCRA).",
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
    faltantes: "Si falta un insumo, se usa el último valor en caché marcado como desactualizado; sin dato, IPC y REM renormalizan dentro de la dimensión.",
    revisiones: "Los stocks del BCRA no se revisan de forma habitual; la serie se regenera completa en cada corrida.",
    cambios: [
      { fecha: "2026-06-28", cambio: "Nace y entra al índice: la dimensión de estabilidad monetaria pasa de IPC 50% / REM 50% a IPC 40% / REM 30% / IDM 30%, en versión interanual real-real." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
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
      "Promedio ponderado: hoy construcción 65% + bienes de capital 35%; cuando los patentamientos comerciales acumulen 13 meses de historia propia, la composición pasa sola a 55/30/15.",
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
    dobleUso: "La operación ISAC también alimenta (en su variante desestacionalizada) un componente del ITVC de vida cotidiana; los bienes de capital son una subserie del ICA que alimenta el saldo comercial.",
    limitaciones: [
      "Los bienes de capital se miden en dólares corrientes e incluyen el efecto de los precios internacionales: el índice de cantidades oficial es solo trimestral.",
      "El tercer componente (patentamientos comerciales) no tiene serie histórica pública: se acumula desde mediados de 2026 y recién tendrá comparación interanual a mediados de 2027.",
      "Las bandas anchas son calibración propia declarada: el umbral fino del documento no sobrevivía a la volatilidad del dato argentino reciente.",
    ],
    faltantes: "Sin patentamientos, la composición renormaliza a 65/35 (situación actual); sin mes común de las otras dos fuentes, caché desactualizado y renormalización de la dimensión.",
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
      acceso: "Automático: API pública de series de tiempo; la composición se calcula en el pipeline.",
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
    dobleUso: "La operación IPI también alimenta (en su variante desestacionalizada) un componente del ITVC de vida cotidiana.",
    limitaciones: [
      "El diseño institucional incluía la importación de hardware de alta tecnología, que no es automatizable con las fuentes públicas actuales: el índice quedó con dos de tres componentes, renormalizados y declarados.",
      "Los pagos al exterior por servicios de informática son una aproximación a la digitalización, no una medición directa de inversión en capital digital.",
      "El empleo de la encuesta laboral se usa como aproximación de las horas trabajadas.",
    ],
    faltantes: "Sin mes común de los tres insumos, se usa el último valor en caché marcado como desactualizado; sin dato, el IAI pasa a explicar toda la dimensión de inversión.",
    revisiones: "Titular por panel alineado, no se revisa; las revisiones de las fuentes se absorben al regenerar las series.",
    cambios: [
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
    dobleUso: "La misma serie se sigue extrayendo como contexto no publicado, y el cinturón de vida cotidiana usa las líneas a familias (tarjetas y personales) para su componente de endeudamiento.",
    limitaciones: [
      "Bandas calibradas a la remonetización 2024-2026 (el crédito real llegó a crecer 90% interanual desde una base ínfima): calibración propia sobre historia corta, declarada.",
      "Agregado total: no distingue empresas de familias ni líneas de crédito.",
    ],
    faltantes: "Sin mes común entre stock e IPC, se usa el último valor en caché marcado como desactualizado; sin dato, reservas e IdC renormalizan dentro de la dimensión de financiamiento.",
    revisiones: "Los saldos del BCRA no se revisan de forma habitual; la serie se regenera completa (desde diciembre de 2023) en cada corrida.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Nace y entra al índice: rescata la única señal no redundante de los cuatro contextos nominales (que dejan de publicarse); la dimensión de financiamiento queda 45% reservas + 40% IdC + 15% crédito." },
      { fecha: "2026-07-04", cambio: "El titular pasa al último mes con IPC cerrado; el dato diario fresco queda como provisorio (antes se deflactaba el préstamo del día con un IPC de dos meses atrás)." },
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
      "Es el único indicador de la dimensión de imagen y voto del índice del cinturón (10% del total) — la dimensión que pesa deliberadamente menos que las otras cuatro, porque el proyecto distingue capital político de popularidad electoral.",
    ],
    dobleUso: "El mismo dato alimenta el indicador de clima electoral del cinturón espíritu de época: la ventaja del Votómetro puntúa en los dos cinturones, decisión declarada de la versión inicial de ese cinturón.",
    limitaciones: [
      "La fuente es una curaduría propia de encuestas de terceros, no un registro oficial.",
      "El peso por recencia se calcula contra el día de la corrida: sin encuestas nuevas, el valor deriva lentamente día a día.",
      "Si pasan más de 60 días sin sondeos, el indicador se marca como desactualizado.",
    ],
    faltantes: "Si la lectura falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "La serie mensual completa se rederiva de las encuestas en cada corrida: un sondeo cargado con retraso corrige los meses que toca. La serie evalúa la ponderación al cierre de cada mes, así que su último punto puede diferir levemente del titular, que se recalcula todos los días.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida del capital electoral del oficialismo." },
      { fecha: "2026-06-30", cambio: "Serie mensual reconstruida hacia atrás hasta diciembre de 2023, evaluando la misma ponderación al cierre de cada mes." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), como único indicador de la dimensión de imagen y voto — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
    ],
  },

  ratio_dnu: {
    tipo: "indicador",
    id: "ratio_dnu",
    cinturon: "politica",
    rezago: "InfoLeg carga las normas al ritmo del Boletín Oficial: días entre la publicación y su aparición en el buscador.",
    fuente: {
      organismo: "InfoLeg (Ministerio de Justicia)",
      operacion: "Buscador oficial de normas — conteo de decretos de necesidad y urgencia y de leyes sancionadas del año corriente",
      url: "https://servicios.infoleg.gob.ar/infolegInternet/",
      acceso: "Automático: consulta el buscador oficial con dos búsquedas (leyes del año y decretos con el texto «necesidad y urgencia») y toma los conteos de resultados.",
    },
    transformaciones: [
      "Ratio = DNU dictados en el año corriente / leyes sancionadas en el año corriente.",
      "Los DNU se identifican buscando la frase «necesidad y urgencia» dentro de los decretos.",
      "La serie histórica repite el mismo cociente por año calendario, desde 2020. Los años cerrados son completos; el punto del año en curso es parcial (de enero a la fecha de la corrida) y se actualiza hasta cerrar el año — al comparar en el gráfico, ese último punto no es estrictamente homogéneo con los anteriores.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del ratio, interpolado entre anclas: 0,3 o menos → el más alto; entre 0,3 y 0,7 → alto; entre 0,7 y 1,2 → moderado; entre 1,2 y 2 → bajo; más de 2 → el más bajo.",
      "Integra la dimensión de poder legislativo del índice del cinturón (30% del total), donde pesa 25% junto a la eficacia legislativa, las sesiones caídas por quórum y los proyectos varados en comisión.",
    ],
    limitaciones: [
      "Identificar DNU por la frase «necesidad y urgencia» es una aproximación: puede contar de más o de menos.",
      "El ratio del año corriente es inestable en los primeros meses (pocas leyes en el denominador).",
      "Depende del formulario del buscador oficial: un rediseño del sitio lo interrumpe hasta adaptarlo.",
    ],
    faltantes: "Si la consulta falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "Los conteos se reconsultan completos en cada corrida: si la fuente carga normas con retraso, el número se corrige solo.",
    cambios: [
      { fecha: "2026-05", cambio: "Entra al cinturón en reemplazo del índice de confianza en el gobierno (UTDT): el cinturón mide capacidad de gobernar, no popularidad." },
      { fecha: "2026-06-30", cambio: "Serie anual desde 2020 para dar contexto histórico al ratio del año en curso." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
    ],
  },

  movilizacion_cepa: {
    tipo: "indicador",
    id: "movilizacion_cepa",
    cinturon: "politica",
    rezago: "CEPA publica sus informes de conflictividad con cadencia irregular (aproximadamente mensual o bimestral); el informe reintenta la lectura todos los días.",
    fuente: {
      organismo: "CEPA — Centro de Economía Política Argentina",
      operacion: "Informes de conflictividad laboral (sección Documentos → Informes)",
      url: "https://centrocepa.com.ar/documentos/informes",
      acceso: "Automático: recorre el listado de informes, identifica el más reciente sobre conflictividad y extrae la cifra del texto.",
    },
    transformaciones: [
      "La cifra del informe se normaliza a un índice 0–100.",
      "Según cómo reporte la fuente, se usan dos escalas de referencia distintas: casos por mes (sobre un máximo de 80) o conflictos acumulados (sobre 200).",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del nivel de conflictividad, interpolado entre anclas: 20 o menos → el más alto; entre 20 y 40 → alto; entre 40 y 60 → moderado; entre 60 y 80 → bajo; más de 80 → el más bajo.",
      "Integra la dimensión de conflicto social del índice del cinturón (15% del total), donde pesa 60% junto al 40% de la variación de eventos de protesta en la Ciudad de Buenos Aires.",
    ],
    limitaciones: [
      "La fuente es un centro de estudios con línea editorial propia, no un organismo oficial.",
      "Los informes no reportan siempre la misma métrica: valores de informes distintos no son estrictamente comparables, y el indicador puede moverse por un cambio de métrica y no de realidad.",
      "Los máximos de las escalas (80 casos por mes, 200 conflictos) son calibraciones propias del informe, no de la fuente.",
      "No hay serie histórica reconstruible: la fuente no publica una serie comparable hacia atrás, así que las mediciones se acumulan hacia adelante.",
    ],
    faltantes: "Si la lectura falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "Cada informe nuevo reemplaza al anterior; la fuente no revisa hacia atrás.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como aproximación a la conflictividad social y laboral en la calle." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de conflicto social — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
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
      "Suma todas las transferencias del año de referencia y del año anterior.",
      "La variación nominal se deflacta por el IPC diciembre contra diciembre: el resultado es la variación real interanual.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas de la variación real, interpolado entre anclas: más de +10% → el más alto; entre 0% y +10% → alto; entre −10% y 0% → moderado; entre −20% y −10% → bajo; −20% o menos → el más bajo.",
      "Integra la dimensión de alianzas territoriales del índice del cinturón (25% del total), donde pesa 40% junto al 30% del alineamiento de senadores por provincia y el 30% de la adhesión provincial al RIGI.",
    ],
    limitaciones: [
      "Granularidad anual: no capta la tensión federal dentro del año.",
      "El nombre del archivo oficial cambia cada año: hay que apuntar la descarga de nuevo cada enero.",
      "Mide el flujo fiscal hacia las provincias — una aproximación parcial a la relación política con los gobernadores.",
    ],
    faltantes: "Si la descarga falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "Se recalcula completo desde la fuente en cada corrida: revisiones del archivo oficial o del IPC se absorben automáticamente.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida de la armonía fiscal entre la Nación y las provincias." },
      { fecha: "2026-06-30", cambio: "El deflactor pasó de una proyección fija al índice IPC oficial del INDEC: la variación real publicada se corrigió de +1,8% a +7,0%." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de alianzas territoriales — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
    ],
  },

  eficacia_legislativa: {
    tipo: "indicador",
    id: "eficacia_legislativa",
    cinturon: "politica",
    rezago: "El portal de datos abiertos de Diputados carga proyectos y movimientos con días o semanas de demora respecto del hecho parlamentario.",
    fuente: {
      organismo: "HCDN — Cámara de Diputados de la Nación",
      operacion: "Datasets «proyectos parlamentarios» y «movimientos de proyectos» del portal oficial de datos abiertos",
      serie: "API CKAN de datos.hcdn.gob.ar",
      url: "https://datos.hcdn.gob.ar",
      acceso: "Automático: API pública del portal, cruzando los proyectos enviados por el Ejecutivo con los movimientos de sanción.",
    },
    transformaciones: [
      "Identifica los proyectos enviados por el Poder Ejecutivo por su número de expediente.",
      "Un proyecto cuenta como aprobado si registra una sanción.",
      "Ambos hechos dentro de una ventana móvil de 12 meses: el indicador es aprobados sobre enviados.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del porcentaje aprobado, interpolado entre anclas: más de 55% → el más alto; entre 35% y 55% → alto; entre 15% y 35% → moderado; entre 5% y 15% → bajo; 5% o menos → el más bajo.",
      "Integra la dimensión de poder legislativo del índice del cinturón (30% del total), donde pesa 30% junto al ratio DNU, las sesiones caídas por quórum y los proyectos varados en comisión.",
    ],
    limitaciones: [
      "Denominador chico: con unos veinte proyectos en la ventana, uno solo mueve más de cuatro puntos porcentuales.",
      "La sanción se detecta por el texto del movimiento: no distingue medias sanciones de otras variantes de registro.",
      "Cuenta proyectos por igual, sin ponderar su peso político.",
    ],
    faltantes: "Si la consulta falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "La serie completa de ventanas móviles se regenera desde la fuente en cada corrida.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida de la capacidad de convertir la agenda de gobierno en ley." },
      { fecha: "2026-06-30", cambio: "Serie mensual de ventanas móviles de 12 meses desde diciembre de 2023." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
    ],
  },

  cohesion_bloque: {
    tipo: "indicador",
    id: "cohesion_bloque",
    cinturon: "politica",
    rezago: "Los portales de votaciones nominales de las dos cámaras registran cada sesión a los pocos días de ocurrida; el informe recalcula el promedio de los últimos 90 días en cada corrida.",
    fuente: {
      organismo: "Cámara de Diputados y Senado de la Nación",
      operacion: "Votaciones nominales de ambas cámaras — bloque propio de La Libertad Avanza, actas divididas de los últimos 90 días",
      url: "https://votaciones.hcdn.gob.ar",
      acceso: "Automático: scraping directo de los portales públicos de votaciones nominales de Diputados y del Senado; sin carga manual del analista.",
    },
    transformaciones: [
      "Para cada acta con al menos un voto a favor o en contra del bloque propio de La Libertad Avanza (se excluyen deliberadamente los bloques aliados de nombre ambiguo, para no inflar la cohesión medida con votos que no son del oficialismo propiamente dicho), calcula qué tan pareja o dispareja fue esa votación puertas adentro: resta los votos a favor menos los votos en contra, toma el valor absoluto y lo divide por el total de votos que emitió el bloque en esa acta.",
      "Por cámara, el cálculo es el promedio de esa cuenta en las actas divididas de los últimos 90 días. Abstenciones y ausencias no entran.",
      "El indicador publicado es el compuesto bicameral: Diputados pesa 65% y el Senado 35% — el mismo reparto que las dos cámaras tenían cuando eran indicadores separados. Si una cámara no tiene dato (por ejemplo, receso sin actas divididas), el peso se reparte sobre la que sí lo tiene; la composición por cámara se publica en el detalle de la card.",
    ],
    incidenciaTexto: [
      "Mide qué tan unido vota el bloque oficialista puertas adentro de las dos cámaras — no si acompaña una «posición oficial», algo que no puede observarse de forma independiente. Si en una votación casi todo el bloque va junto en el mismo sentido (a favor o en contra), la cohesión es alta; si el bloque se parte en partes similares, la cohesión es baja.",
      "El puntaje del índice se asigna por bandas del compuesto, interpolado entre anclas: más de 99,9% → el más alto; entre 99% y 99,9% → alto; entre 97% y 99% → moderado; entre 95% y 97% → bajo; 95% o menos → el más bajo. Los umbrales se calibraron contra la serie mensual del propio compuesto (dic-2023 en adelante, rango observado 90,3–100): las cinco bandas tienen meses reales observados.",
      "Es el único indicador de la dimensión de cohesión interna del oficialismo del índice del cinturón (20% del total).",
    ],
    limitaciones: [
      "Solo cuenta al bloque propio de LLA: deja afuera a los aliados de bloques separados, una decisión declarada para no inflar la cohesión medida con votos ajenos al oficialismo propiamente dicho.",
      "Las dos cámaras tienen sensibilidad distinta: el bloque de Diputados es grande (un disidente mueve poco el promedio) y el del Senado es chico (un solo voto disidente lo mueve con fuerza). El compuesto pondera esa asimetría (65/35) pero no la elimina — la composición por cámara se publica para poder leerla.",
      "No distingue ausencias de abstenciones: ambas quedan fuera del cálculo igual que si el legislador no hubiera votado.",
      "Depende de que los portales públicos mantengan su estructura actual: un cambio de diseño puede interrumpir la lectura automática hasta que se ajuste.",
      "Con pocas actas divididas en la ventana de 90 días, un solo voto conflictivo mueve el promedio con fuerza.",
    ],
    faltantes: "Si el scraping no logra llegar a uno de los portales, se conserva el último promedio calculado de esa cámara y el compuesto se arma igual; recién se marca desactualizado si ninguna cámara tuvo una corrida que llegara a su portal en más de 10 días — un receso legislativo sin actas nuevas no cuenta como desactualización.",
    revisiones: "El promedio de los últimos 90 días se recalcula completo desde las fuentes en cada corrida; no se arrastran promedios previos.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón como estimación manual, a la espera de una fuente estructurada de votaciones vigente." },
      { fecha: "2026-07-07", cambio: "Deja de ser una estimación manual: pasa a calcularse en forma automática con el scraping de las votaciones nominales de Diputados. Cambia también la definición — de «porcentaje alineado con la posición oficial» (no observable de forma independiente) a «qué tan pareja o dispareja es la votación interna del bloque propio», calculada acta por acta. El mismo día nace la lectura complementaria sobre el Senado, como indicador separado." },
      { fecha: "2026-07-09", cambio: "El scraping automático de Diputados quedó bloqueado en producción entre el 07 y el 09 de julio (protección del portal contra acceso automatizado) — el indicador se sostuvo con el último dato calculado. Restablecido usando una vía de acceso directa del mismo portal, sin depender de la parte bloqueada." },
      { fecha: "2026-07-09", cambio: "Suma una caché permanente por acta: una corrida ya no vuelve a descargar actas ya vistas, solo las nuevas desde la corrida anterior (antes de esto, reconstruir el historial completo agregaba ~53 minutos al pipeline). Habilita también la serie histórica MENSUAL del gráfico (antes: 3 puntos anuales)." },
      { fecha: "2026-07-09", cambio: "Umbrales de puntaje de cada cámara recalibrados (antes 90/75/60/40, fórmula ad hoc nunca validada) a partir de las series mensuales reconstruidas (29 a 31 meses reales por cámara)." },
      { fecha: "2026-07-10", cambio: "Revisión editorial del cinturón: las dos cámaras se fusionan en este único indicador bicameral (Diputados 65%, Senado 35% — el reparto que ya tenían como indicadores separados), con umbrales recalibrados contra la serie mensual del compuesto (99,9/99,0/97,0/95,0). La serie del gráfico pasa a ser la del compuesto." },
    ],
  },

  alineamiento_senadores_prov: {
    tipo: "indicador",
    id: "alineamiento_senadores_prov",
    cinturon: "politica",
    rezago: "El portal de votaciones nominales del Senado registra cada sesión a los pocos días de ocurrida; el informe recalcula el promedio de los últimos 90 días en cada corrida.",
    fuente: {
      organismo: "Senado de la Nación",
      operacion: "Votaciones nominales del Senado — coincidencia de senadores no alineados con la posición del bloque de La Libertad Avanza, por provincia, actas de los últimos 90 días",
      url: "https://www.senado.gob.ar/votaciones/actas",
      acceso: "Automático: scraping directo del portal público de votaciones nominales del Senado; sin carga manual.",
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
      "Integra la dimensión de alianzas territoriales del índice del cinturón (25% del total), donde pesa 30% junto al 40% de las transferencias federales y el 30% de adhesión al RIGI.",
    ],
    limitaciones: [
      "Proxy de comportamiento legislativo, no medición directa de la postura del gobernador (Poder Ejecutivo provincial) — ver caveat arriba.",
      "Incluye votaciones consensuadas (donde todo el Senado vota en el mismo sentido), no solo las genuinamente disputadas — solo se excluyen las actas donde el propio bloque LLA queda internamente empatado.",
      "Bloque LLA chico en el Senado: pocos senadores propios hacen que su 'posición' en un acta dependa de muy pocos votos.",
      "Depende de que el portal público del Senado mantenga su estructura actual: un cambio de diseño del sitio puede interrumpir la lectura automática hasta que se ajuste.",
    ],
    faltantes: "Si el scraping no logra llegar al sitio, se conserva el último promedio calculado en caché; recién se marca desactualizado si pasan más de 10 días sin una corrida que haya llegado al portal — un receso legislativo sin actas nuevas no cuenta como desactualización.",
    revisiones: "El promedio de los últimos 90 días se recalcula completo desde la fuente en cada corrida; no se arrastran promedios previos.",
    cambios: [
      { fecha: "2026-07-08", cambio: "Alta como reemplazo de \"alineamiento de gobernadores\" (indicador de carga manual, sin fuente automatizable encontrada): mide coincidencia de voto de senadores no oficialistas con la posición del bloque de gobierno, por provincia." },
      { fecha: "2026-07-09", cambio: "Umbrales de puntaje recalibrados (antes 65/45/25/10, heredados de \"alineamiento de gobernadores\" sin validar) a partir de una serie mensual propia reconstruida (29 meses reales, feb-2024 a jun-2026): nuevos cortes en 70/60/50/40." },
    ],
  },

  adhesion_reformas_provincial: {
    tipo: "indicador",
    id: "adhesion_reformas_provincial",
    cinturon: "politica",
    rezago: "La tabla de provincias adheridas se actualiza en el sitio oficial apenas una provincia formaliza su adhesión; el informe la relee completa en cada corrida.",
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
      "Integra la dimensión de alianzas territoriales del índice del cinturón (25% del total), donde pesa 30% junto al 40% de las transferencias federales y el 30% del alineamiento de senadores por provincia.",
    ],
    limitaciones: [
      "Cuenta la adhesión formal, no la inversión efectiva que esa adhesión termina generando en cada provincia.",
      "Es una tabla acumulativa: una vez que una provincia adhiere no se espera que salga de la lista, así que el indicador solo sube o queda estable — no capta marchas atrás.",
      "El sitio fuente tiene una fila vacía mal formada que puede duplicar el nombre de una provincia al leer la tabla; no altera el conteo final porque cada provincia se cuenta una sola vez.",
    ],
    faltantes: "Si la consulta al sitio falla, el indicador queda fuera de esa corrida y el puntaje del cinturón se calcula con los indicadores disponibles.",
    revisiones: "La tabla completa se relee de la fuente en cada corrida; no se acumulan lecturas parciales.",
    cambios: [
      { fecha: "2026-07-07", cambio: "Alta como indicador de la dimensión de alianzas territoriales: mide adhesión fiscal al RIGI, distinta del alineamiento político general que ya capta el indicador de gobernadores." },
      { fecha: "2026-07-09", cambio: "Serie histórica MENSUAL del gráfico (antes: 1 solo punto, el valor actual). La tabla fuente no trae fecha de adhesión por provincia, así que se investigó a mano la fecha de la ley de adhesión de cada una de las 16 provincias (Boletín Oficial provincial u otra fuente oficial equivalente) — no es un scraper automático, es un dataset investigado una vez y versionado (data/politica/adhesion_reformas_provincial_fechas.json)." },
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
    incidenciaTexto: [
      "La tensión crece cuando el apoyo se retira: 80% alineado → tensión 0 · 40% → 5 · 0% → 10.",
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
      serie: "API CKAN de datos.hcdn.gob.ar",
      url: "https://datos.hcdn.gob.ar",
      acceso: "Automático: API pública del portal, filtrando las sesiones de Diputados del período legislativo en curso.",
    },
    transformaciones: [
      "Cuenta las sesiones del período legislativo en curso y cuántas figuran como fracasadas.",
      "El indicador es sesiones fracasadas sobre sesiones convocadas.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del porcentaje de sesiones caídas, interpolado entre anclas: 5% o menos → el más alto; entre 5% y 10% → alto; entre 10% y 20% → moderado; entre 20% y 30% → bajo; más de 30% → el más bajo.",
      "Integra la dimensión de poder legislativo del índice del cinturón (30% del total), donde pesa 20% junto al ratio DNU, la eficacia legislativa y los proyectos varados en comisión.",
    ],
    limitaciones: [
      "Las sesiones desactivadas antes de la apertura formal no aparecen en el registro oficial: el indicador subestima el bloqueo.",
      "Muestra chica: con pocas sesiones en el período, cada una mueve decenas de puntos porcentuales.",
      "No distingue el quórum frustrado por la oposición de la inasistencia propia — decisión metodológica declarada.",
    ],
    faltantes: "Si la consulta falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "El dataset se reconsulta completo en cada corrida.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida del bloqueo parlamentario." },
      { fecha: "2026-06-30", cambio: "Serie por período legislativo desde 2024." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
    ],
  },

  comisiones_caidas: {
    tipo: "indicador",
    id: "comisiones_caidas",
    cinturon: "politica",
    rezago: "El portal de datos abiertos de Diputados carga dictámenes y movimientos con días o semanas de demora.",
    fuente: {
      organismo: "HCDN — Cámara de Diputados de la Nación",
      operacion: "Datasets «dictámenes de comisión» y «movimientos de proyectos» del portal oficial de datos abiertos",
      serie: "API CKAN de datos.hcdn.gob.ar",
      url: "https://datos.hcdn.gob.ar",
      acceso: "Automático: API pública del portal, cruzando dictámenes con Orden del Día contra sanciones registradas.",
    },
    transformaciones: [
      "Toma los dictámenes de comisión con Orden del Día de los últimos 12 meses.",
      "Un proyecto cuenta como caído si obtuvo dictamen pero no registra sanción en la ventana.",
      "El indicador es proyectos caídos sobre el total con dictamen.",
    ],
    incidenciaTexto: [
      "El puntaje del índice se asigna por bandas del porcentaje de proyectos caídos, interpolado entre anclas: 96% o menos → el más alto; entre 96% y 97% → alto; entre 97% y 98% → moderado; entre 98% y 99% → bajo; más de 99% → el más bajo. Los umbrales se calibraron con la serie mensual real del indicador (32 meses, dic-2023 en adelante) — los anteriores (30/50/70/85) describían un congreso teórico y dejaban el puntaje clavado en el mínimo todos los meses, sin discriminar nada.",
      "Integra la dimensión de poder legislativo del índice del cinturón (30% del total), donde pesa 25% junto al ratio DNU, la eficacia legislativa y las sesiones caídas por quórum.",
    ],
    limitaciones: [
      "El valor vive cerca del máximo por una razón estructural: la gran mayoría de los dictámenes no llega al recinto bajo ningún gobierno, y con una ventana móvil de 12 meses un dictamen reciente casi nunca alcanza a sancionarse dentro de su propia ventana. Por eso los umbrales de puntaje se calibraron sobre el rango realmente observado (94,7%–99,8%) y no sobre porcentajes teóricos.",
      "Depende del etiquetado de la fuente («Orden del Día», «sanción»): variantes de registro pueden contar mal.",
    ],
    faltantes: "Si la consulta falla, se usa el último valor en caché marcado como desactualizado; sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "La serie completa se regenera desde la fuente en cada corrida.",
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón político como medida del embudo entre comisiones y recinto." },
      { fecha: "2026-06-30", cambio: "Serie mensual de ventanas móviles de 12 meses desde diciembre de 2023." },
      { fecha: "2026-07-07", cambio: "Pasa a puntuar dentro del ITCP (índice paramétrico de cinco dimensiones ponderadas), en la dimensión de poder legislativo — antes el cinturón promediaba en partes iguales las tensiones de sus indicadores." },
      { fecha: "2026-07-09", cambio: "Umbrales de puntaje recalibrados (antes 30/50/70/85, tomados del diseño conceptual y nunca validados) con la serie mensual real de 32 meses: nuevos cortes en 96/97/98/99. Con los anteriores, el rango realmente observado (94,7%–99,8%) caía completo en el escalón más bajo — tensión máxima permanente, sin capacidad de distinguir un mes de otro; la propia ficha ya declaraba esa saturación como limitación." },
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
      url: "https://servicios.infoleg.gob.ar",
      acceso: "Automático: búsqueda de frase exacta en el buscador oficial de InfoLeg (tres variantes de sumario que cubren todos los vetos del período, verificadas una por una) y filtrado de las actas del Senado por la fórmula «en los términos de la ley 26.122», con recuento de votos del acta para clasificar rechazo o aprobación. El registro de eventos es versionado: cada derrota queda documentada con su fecha, acta y fuente.",
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
      "Los umbrales se calibraron contra la serie mensual reconstruida completa del indicador (32 meses, diciembre de 2023 en adelante, con cada evento verificado contra la fuente primaria): el período cubre desde meses sin ninguna derrota hasta el pico de ocho derrotas en doce meses tras la ola de rechazos e insistencias de agosto-octubre de 2025. Las dos bandas más bajas quedan deliberadamente por encima de todo lo observado: son el margen para escenarios de confrontación más intensos que los ya vistos.",
      "Integra la dimensión de poder legislativo del índice del cinturón (30% del total), donde pesa 20% junto al ratio DNU, la eficacia legislativa, las sesiones caídas por quórum y los proyectos varados en comisión. Menos derrotas = puntaje más alto.",
    ],
    limitaciones: [
      "Es un indicador de eventos raros con ventana móvil: el valor puede saltar varios enteros de un mes al siguiente, tanto cuando ocurre una tanda de derrotas como —en espejo— doce meses después, cuando esa tanda sale de la ventana. El movimiento de salida es mecánico (aritmética de la ventana), no una mejora política nueva; el detalle de la card publica la composición del conteo para leerlo con contexto.",
      "Un conteo de cero informa ausencia de derrotas, no necesariamente dominio del Ejecutivo: también puede reflejar que no hubo vetos ni tratamientos de decretos en juego en el período (menos confrontación, no más control).",
      "La detección automática de rechazos de decretos mira las actas del Senado: un rechazo que ocurra primero en Diputados se registra recién cuando el Senado también lo vota (o con una corrección manual del registro). En el período histórico eso habría corrido la fecha de cinco decretos apenas dos semanas, sin alterar el conteo anual.",
      "Las insistencias se fechan por la publicación de la ley en el Boletín Oficial, no por el voto de la segunda cámara: una insistencia votada sobre el fin de mes puede registrarse al mes siguiente. En los tres casos reales del período ambos hechos cayeron en el mismo mes.",
      "Mide derrotas consumadas en el recinto; los amagues que no llegan a votarse (sesiones sin quórum para rechazar un decreto, insistencias que no reúnen los dos tercios) no cuentan — las sesiones fracasadas las captura, con otro método, el indicador de sesiones caídas por quórum.",
    ],
    faltantes: "Si InfoLeg o el Senado fallan, se usa el último valor en caché marcado como desactualizado; el registro versionado de eventos preserva todo el pasado, así que una caída de fuente solo retrasa la detección de eventos nuevos. Sin caché, el indicador queda fuera y los pesos de su dimensión se renormalizan entre los presentes.",
    revisiones: "Los eventos consumados son inmutables (una insistencia no se des-insiste; un rechazo no se des-vota). Los vetos con insistencia incompleta se re-verifican en cada corrida: media insistencia pendiente no caduca y puede completarse en cualquier momento — si eso ocurre, el evento nuevo se fecha en el mes en que se complete, sin reescribir el histórico.",
    cambios: [
      { fecha: "2026-07-09", cambio: "Incorporado al cinturón político: las insistencias de 2025 fueron las primeras que revirtieron vetos presidenciales desde 2003, y ningún otro indicador del cinturón capturaba ese pulso ni los rechazos de decretos en el recinto. Serie mensual completa desde diciembre de 2023, reconstruida evento por evento contra fuente primaria." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // Espíritu de época — promedio simple de cuatro indicadores, dos de ellos
  // compartidos con vida cotidiana (icc_utdt, sentimiento_digital)
  // ═══════════════════════════════════════════════════════════════════════
  clima_electoral: {
    tipo: "indicador",
    id: "clima_electoral",
    cinturon: "espiritu_epoca",
    rezago: "Hereda la cadencia del Votómetro: se actualiza cuando hay encuestas nuevas, típicamente semanas.",
    fuente: {
      organismo: "Fundación CIGOB — Votómetro",
      operacion: "Lectura del indicador de ventaja electoral del cinturón político (el mismo dato, sin re-extracción)",
      url: "https://cigob.github.io/Votometro/",
      acceso: "Automático: se copia del cálculo del cinturón político dentro de la misma corrida diaria.",
    },
    transformaciones: [
      "Sin transformación adicional: es la misma ventaja LLA − PJ ponderada por recencia y calidad de encuesta.",
    ],
    incidenciaTexto: [
      "La tensión es lineal en la ventaja: +15 puntos → tensión 0 · empate → 5 · −15 puntos → 10.",
      "El cinturón espíritu de época no usa un índice compuesto: promedia las tensiones de sus cuatro indicadores (confianza del consumidor, sentimiento digital, clima electoral e intención migratoria).",
    ],
    dobleUso: "Es la segunda lectura del mismo dato del Votómetro: puntúa en política como ventaja electoral y acá como clima. La duplicación es una decisión declarada de la versión inicial del cinturón, hasta que exista una paramétrica propia.",
    limitaciones: [
      "No es una medición independiente del humor social: correlaciona uno a uno con el indicador del cinturón político.",
      "Aproximación provisional: el marco conceptual todavía no define indicadores propios para este cinturón.",
      "Queda pendiente medir la apatía electoral (voto en blanco y ausentismo): las encuestas agregadas no publican ese dato por sondeo.",
    ],
    faltantes: "Si la lectura del cinturón político no está disponible, usa el último caché marcado como desactualizado; sin nada, el score del cinturón promedia los presentes.",
    revisiones: "Hereda las del Votómetro: la serie se rederiva completa en cada corrida.",
    cambios: [
      { fecha: "2026-06-10", cambio: "Nace el cinturón espíritu de época (quinto cinturón del marco conceptual) con tres indicadores tomados de vida cotidiana y política." },
      { fecha: "2026-06-30", cambio: "Serie histórica publicada como alias de la serie del Votómetro." },
    ],
  },

  indice_intencion_migratoria: {
    tipo: "indicador",
    id: "indice_intencion_migratoria",
    cinturon: "espiritu_epoca",
    rezago: "Hasta un mes: el mes en curso se descarta por incompleto; el dato se actualiza como máximo una vez por mes calendario.",
    fuente: {
      organismo: "Google Trends (fuente no oficial)",
      operacion: "Interés de búsqueda en Argentina de una canasta de términos de intención de emigrar (por ejemplo \"emigrar de argentina\", \"vivir en el exterior\")",
      url: "https://trends.google.com/",
      acceso: "Automático: consulta mensual de la canasta en ventana fija (2021 en adelante); cada descarga sana reemplaza el archivo completo — corridas con escalas distintas nunca se mezclan.",
    },
    transformaciones: [
      "La tensión es lineal en el interés de búsqueda: 0 → tensión 0 · 50 → tensión 5 · 100 → tensión 10.",
      "El cociente entre valores de una misma consulta cancela la renormalización de escala de la fuente, igual que en sentimiento digital.",
      "Se recolectan además canastas de contexto (ciudadanías, trabajo/visas, destinos y un diagnóstico de causa económica vs. estructural) y un desglose por provincia — ninguna de estas entra al puntaje: son insumo de lectura para el analista, no números publicados en la card.",
    ],
    incidenciaTexto: [
      "El cinturón espíritu de época no usa un índice compuesto: promedia las tensiones de sus cuatro indicadores (confianza del consumidor, sentimiento digital, clima electoral e intención migratoria).",
    ],
    limitaciones: [
      "Mide intención expresada en la búsqueda, no un trámite ni una salida real del país: alguien puede buscar por curiosidad sin intención de emigrar.",
      "Por eso este indicador nunca se publica solo: su card en el tablero lo acompaña con un contraste de migración efectiva — seis registros administrativos de cinco destinos (visas de EE.UU., residencias permanentes de Canadá, nacionalizaciones de España, ciudadanías de Italia y residencias definitivas de Chile). El contraste no puntúa: mezcla flujos de naturaleza distinta y cada fuente publica con su propio calendario (las europeas y Chile son anuales; las series de EE.UU. llegan con rezago).",
      "Fuente no oficial con límites de consulta: si el servicio restringe el acceso, se mantiene el último valor del archivo propio.",
    ],
    faltantes: "Con la fuente caída o sin el mes calendario todavía consultado, se mantiene el último valor del archivo propio, marcado como desactualizado.",
    revisiones: "Reemplazo total del archivo en cada descarga sana; la fuente no revisa datos propiamente.",
    cambios: [
      { fecha: "2026-07-10", cambio: "Cuarto indicador del cinturón espíritu de época: intención de emigrar vía Google Trends, distinta de la ansiedad económica inmediata que ya mide sentimiento digital." },
      { fecha: "2026-07-10", cambio: "La card del indicador incorpora el contraste de migración real: seis registros administrativos de EE.UU., Canadá, España, Italia y Chile, que acompañan la lectura sin puntuar." },
    ],
  },

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
    faltantes: "Si la API falla, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
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
      url: "https://www.argentina.gob.ar/economia/ingresos-publicos",
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
    faltantes: "Si falta un insumo, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Las series oficiales pueden revisarse; la serie propia se recalcula completa en cada corrida.",
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
    rezago: "Sin rezago: el conteo se evalúa al día de la corrida (InfoLeg carga al ritmo del Boletín Oficial).",
    fuente: {
      organismo: "InfoLeg (Ministerio de Justicia)",
      operacion: "Conteo de normas nacionales publicadas desde diciembre de 2023 cuyo texto contiene «deroga»",
      url: "https://servicios.infoleg.gob.ar/infolegInternet/",
      acceso: "Automático: consulta al buscador oficial de normas con rango de fechas y texto, con reintento.",
    },
    transformaciones: [
      "Avance = cantidad de normas derogatorias, con calibración declarada: 100 normas = plan desregulador completo.",
      "Cada norma cuenta una vez, sin importar cuántos artículos deroga.",
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
      unidadCorta: "% de avance",
    },
    limitaciones: [
      "Es un conteo de menciones, no una auditoría del contenido derogado.",
      "La calibración «100 normas = plan completo» es una decisión propia declarada.",
      "El megadecreto 70/23 no está indexado como texto completo en la fuente y no aparece en el conteo: el indicador captura lo posterior.",
    ],
    faltantes: "Con el buscador caído, cae al valor de respaldo documentado (lectura del documento institucional); después, caché y renormalización.",
    revisiones: "El acumulado se reevalúa completo en cada corrida y puede moverse si la fuente reindexa.",
    cambios: [
      { fecha: "2026-05", cambio: "Automatizado desde el inicio del cinturón con la misma búsqueda, en escala lineal." },
      { fecha: "2026-07-02", cambio: "Umbrales institucionales del ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  reduccion_estado: {
    tipo: "indicador",
    id: "reduccion_estado",
    cinturon: "gestion",
    rezago: "La serie de dotación se publica con ~2 meses de rezago; los últimos meses aparecen imputados y se revisan.",
    fuente: {
      organismo: "INDEC + Secretaría de Transformación del Estado",
      operacion: "Dotación de personal de la Administración Pública Nacional, empresas y sociedades (serie mensual)",
      serie: "Planilla oficial serie_dotacion_apn.xlsx (cuadro 1, Administración pública nacional)",
      url: "https://www.indec.gob.ar/indec/web/Institucional-Indec-empleoAPN",
      acceso: "Automático: lectura de la planilla oficial.",
    },
    transformaciones: [
      "Variación porcentual de la dotación contra la línea de base de diciembre de 2023 (231.305 agentes).",
      "A diferencia de las series previsionales, excluye provincias y municipios: es la métrica insignia de la reforma del Estado nacional.",
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
      "Las bandas se calibraron a mano contra el recorte observado (~10-12% → banda alta).",
    ],
    faltantes: "Con la planilla caída, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "La fuente revisa los meses imputados en cada publicación; la serie propia se relee completa en cada corrida.",
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
    faltantes: "Si falta un insumo, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Series revisables por el publicador; la serie propia se recalcula entera en cada corrida.",
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
    ],
    faltantes: "Si falta un insumo, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "Series revisables por el publicador; recalculada entera en cada corrida.",
    cambios: [
      { fecha: "2026-07-02", cambio: "Indicador nuevo, creado con el ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  reestructuracion_organismos: {
    tipo: "indicador",
    id: "reestructuracion_organismos",
    cinturon: "gestion",
    rezago: "Sin rezago: conteo al día de la corrida.",
    fuente: {
      organismo: "InfoLeg (Ministerio de Justicia)",
      operacion: "Conteo de normas nacionales publicadas desde diciembre de 2023 cuyo texto contiene «disolución»",
      url: "https://servicios.infoleg.gob.ar/infolegInternet/",
      acceso: "Automático: consulta al buscador oficial de normas (mismo mecanismo que la desregulación).",
    },
    transformaciones: [
      "Avance = actos de disolución o reestructuración, con calibración declarada y validada a mano: 18 actos = 40% de avance; 45 actos = plan completo.",
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
      "El megadecreto 70/23 no aparece en la búsqueda de texto: solo captura los actos posteriores.",
      "La calibración (18 = 40%, 45 = plan completo) es una decisión propia validada a mano y declarada.",
    ],
    faltantes: "Con el buscador caído, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "El acumulado se reevalúa completo en cada corrida.",
    cambios: [
      { fecha: "2026-05", cambio: "Automatizado desde el inicio del cinturón con la misma búsqueda." },
      { fecha: "2026-07-02", cambio: "Umbrales institucionales del ITCG." },
      { fecha: "2026-07-03", cambio: "Puntaje interpolado entre anclas." },
    ],
  },

  fal_modernizacion_laboral: {
    tipo: "indicador",
    id: "fal_modernizacion_laboral",
    cinturon: "gestion",
    rezago: "Sin rezago: registro de fondos y Boletín Oficial al día.",
    fuente: {
      organismo: "CNV (registro de fondos comunes) + Boletín Oficial",
      operacion: "Índice de avance del Fondo de Cese Laboral: cobertura en convenios (40%) + adopción financiera (30%), renormalizados sobre lo medible",
      url: "https://www.boletinoficial.gob.ar/",
      acceso: "Automático: registro público de la CNV (los fondos de cese llevan la denominación obligatoria «Cese Laboral») + buscador del Boletín Oficial (menciones del instrumento en la Primera Sección desde la Ley Bases).",
    },
    transformaciones: [
      "Adopción financiera = fondos de cese registrados en la CNV sobre 10 (adopción plena, calibración provisoria). Hoy: cero fondos — dato duro, no faltante.",
      "Cobertura = menciones en el Boletín Oficial sobre 420 (plena), calibración anclada a la estimación manual vigente al cambiar de fuente, para que el índice no saltara por el cambio de método.",
      "El tercer componente del diseño institucional (litigiosidad diferencial por sector) no tiene fuente pública: los pesos se renormalizan sobre lo disponible.",
    ],
    anclas: {
      bandas: [
        { banda: "> 60", puntaje: 100 },
        { banda: "40 – 60", puntaje: 85 },
        { banda: "20 – 40", puntaje: 65 },
        { banda: "5 – 20", puntaje: 40 },
        { banda: "≤ 5", puntaje: 10 },
      ],
      puntos: [[5, 10], [12.5, 40], [30, 65], [50, 85], [60, 100]],
      unidadCorta: "índice 0-100",
    },
    dobleUso: "La litigiosidad laboral puntúa como indicador aparte de la misma dimensión: par instrumento (este) / resultado (aquella), sin doble conteo.",
    limitaciones: [
      "La cobertura por menciones en el Boletín Oficial es una aproximación con pleno calibrado a mano; el buscador oficial de convenios no tiene interfaz consultable.",
      "La reglamentación operativa plena del instrumento está postergada al segundo semestre de 2026: el valor bajo refleja eso.",
    ],
    faltantes: "Si el Boletín falla, la cobertura cae a la estimación manual declarada; si el registro CNV falla, entra el valor de respaldo completo; después, caché y renormalización.",
    revisiones: "El registro CNV se reverifica en cada corrida; la serie de menciones se reconstruye por consulta mensual.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual de etapas implementadas." },
      { fecha: "2026-07-02", cambio: "Compuesto del documento institucional renormalizado a lo medible, con el registro CNV automático." },
      { fecha: "2026-07-03", cambio: "La litigiosidad se separa como indicador propio de la dimensión. Después, la cobertura se automatizó vía menciones del Boletín Oficial con calibración anclada." },
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
    dobleUso: "Es el «resultado» que complementa al «instrumento» (Fondo de Cese) dentro de la dimensión de reforma laboral.",
    limitaciones: [
      "Aproximación declarada: son juicios del sistema de riesgos del trabajo, no el canal indemnizatorio que el Fondo de Cese reemplaza — pero es la única serie nacional mensual pública.",
      "La ventana de 12 contra 12 meses reacciona lento a los quiebres.",
    ],
    faltantes: "Con la planilla caída, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
    revisiones: "La fuente puede revisar meses; la planilla completa se relee en cada corrida.",
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
      "Es el único indicador del índice sin colector de fuente viva: la asignación de etapas es juicio del analista, con las normas citadas en el registro.",
      "La escala 0-4 discretiza procesos continuos.",
    ],
    faltantes: "Sin registro disponible, se usa el último valor en caché marcado como desactualizado; sin dato, los pesos de la dimensión se renormalizan.",
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
    rezago: "Sin rezago: foto de la plataforma oficial al día de la corrida.",
    fuente: {
      organismo: "Ministerio de Economía — plataforma oficial del RIGI",
      operacion: "Pipeline del Régimen de Incentivo a Grandes Inversiones: inversión aprobada sobre el total del pipeline (aprobada + en evaluación)",
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
      unidadCorta: "% del pipeline",
    },
    limitaciones: [
      "No existe fuente estructurada de inversión efectivamente desembolsada: el pipeline aprobado es lo más cercano al hecho, y se declara como tal.",
      "El denominador salta con cada anuncio grande en evaluación: el avance puede bajar sin que nada empeore.",
      "Depende de que la planilla oficial siga pública y con el mismo esquema (ya cambió una vez y el lector se adaptó).",
    ],
    faltantes: "Con la plataforma caída, cae a una aproximación por conteo de resoluciones oficiales (marcada como desactualizada); después, caché y renormalización.",
    revisiones: "La plataforma se actualiza sin registro de cambios; las fechas de aprobación quedan fijadas con su norma.",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial por conteo de resoluciones (aproximación)." },
      { fecha: "2026-06-30", cambio: "Pasa a la plataforma oficial del Ministerio de Economía: inversión aprobada sobre pipeline, con montos reales." },
      { fecha: "2026-07-02", cambio: "Umbrales institucionales del ITCG; después, puntaje interpolado entre anclas." },
    ],
  },

  concesiones_infraestructura: {
    tipo: "indicador",
    id: "concesiones_infraestructura",
    cinturon: "gestion",
    rezago: "Sin rezago: estado del portal de contrataciones al día de la corrida.",
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
    faltantes: "Con los portales caídos, cae al valor de respaldo documentado con fecha; después, caché y renormalización.",
    revisiones: "Los kilómetros por etapa se refrescan de la página oficial en cada corrida; para las adjudicaciones manda la fecha del Boletín Oficial.",
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
      "TDPS = 100 × devengado en «ayudas sociales a personas» / total de transferencias de los programas; el resto del inciso es plata que llega vía terceros (las «unidades de gestión» eliminadas por decreto en 2024).",
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
    faltantes: "Sin acceso a la API, cae al valor de respaldo documentado (el decreto de 2024); después, caché y renormalización.",
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
    dobleUso: "Se lee junto a la serie de contexto de protestas (ACLED): la protesta no desapareció — se reconvirtió a marchas sin corte.",
    limitaciones: [
      "Fuente privada sin microdatos abiertos: los anclajes se reconstruyen de cifras publicadas.",
      "Granularidad anual: el valor se arrastra todo el año hasta el anclaje siguiente.",
      "Estado judicial verificado: la nulidad de primera instancia fue revocada por la Cámara en lo Contencioso Administrativo Federal (marzo de 2026) — el protocolo es un acto válido y vigente.",
      "El registro histórico oficial de cortes del GCBA está fuera de servicio; el monitoreo propio de alertas de transporte acumula la serie que permitirá automatizar el dato.",
    ],
    faltantes: "Cae al valor de respaldo documentado; después, caché y renormalización.",
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
      acceso: "Automático: lectura de las planillas oficiales; las prepagas inscriptas como Agentes del Seguro se identifican por su rango de código de registro (canal creado por el DNU 70/23).",
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
    faltantes: "Cae al valor de respaldo documentado con fecha; después, caché y renormalización.",
    revisiones: "Las planillas anuales se releen completas en cada corrida (la fuente puede revisar meses hacia atrás).",
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial como carga manual: la fuente en línea estaba bloqueada." },
      { fecha: "2026-07-02", cambio: "Automatizado con los padrones oficiales de beneficiarios y usuarios." },
    ],
  },

  alertas_manifestacion: {
    tipo: "indicador",
    id: "alertas_manifestacion",
    cinturon: "gestion",
    rezago: "Sin rezago: alertas activas del momento, muestreadas varias veces por día.",
    fuente: {
      organismo: "GCBA — API Transporte (alertas de servicio de colectivos y subtes)",
      operacion: "Alertas de servicio clasificadas como manifestación (por causa declarada o vocabulario del texto), acumuladas día a día",
      url: "https://apitransporte.buenosaires.gob.ar/",
      acceso: "Automático con credenciales: la fuente es de tiempo real puro, sin histórico — el informe acumula su propia serie con muestreos diarios en la franja típica de cortes.",
    },
    transformaciones: [
      "Valor = alertas únicas del mes corriente (la misma protesta vista en dos muestreos cuenta una vez).",
    ],
    incidenciaTexto: [
      "Indicador de contexto: no integra el ITCG. Es una serie recién nacida, sin línea de base 2023 — cuando acumule unos 12 meses de historia, está llamada a automatizar el indicador de orden público.",
    ],
    limitaciones: [
      "Serie sin historia previa: imposible compararla contra el arranque del mandato todavía.",
      "Mide alertas de transporte, no cortes verificados; la cobertura depende de la franja horaria muestreada.",
    ],
    faltantes: "Si la API no responde, la corrida se saltea y el acumulado propio persiste.",
    revisiones: "Acumulación con deduplicación, sin revisión hacia atrás.",
    cambios: [
      { fecha: "2026-07-02", cambio: "Se crea el monitoreo acumulativo: el registro histórico oficial de cortes del GCBA está fuera de servicio y no hay alternativa pública con historia." },
    ],
  },

  protestas_caba: {
    tipo: "indicador",
    id: "protestas_caba",
    cinturon: "gestion",
    rezago: "1-2 meses efectivos: el archivo se actualiza semanalmente y el mes parcial se excluye.",
    fuente: {
      organismo: "ACLED — Armed Conflict Location & Event Data",
      operacion: "Agregado semanal de eventos de protesta por provincia (América Latina y el Caribe), filtrado CABA y agregado a meses",
      url: "https://acleddata.com/",
      acceso: "Automático con cuenta de miembro: descarga del archivo agregado semanal (el nivel de acceso disponible no habilita el detalle por evento).",
    },
    transformaciones: [
      "Valor = eventos de protesta acumulados en 12 meses, comparados contra el total de 2023 (la línea de base del mandato).",
    ],
    incidenciaTexto: [
      "Indicador de contexto: no integra el ITCG, por una razón declarada — puntuar el volumen de protesta premiaría «menos marchas», que es un derecho ejercido y no un resultado de gestión. Leído junto al indicador de orden público, muestra que la protesta se reconvirtió: menos cortes, no menos marchas.",
    ],
    dobleUso: "El mismo dato (variación de eventos contra la base 2023) integró el puntaje del índice del cinturón político entre el 07 y el 10 de julio de 2026, hasta que la revisión editorial acotó ese índice a la capacidad de gestionar y avanzar la agenda de gobierno. Desde entonces el cinturón político no lo publica: la serie se sigue relevando como seguimiento interno de la conflictividad, y esta card de gestión queda como su única lectura pública.",
    limitaciones: [
      "Fuente de membresía con criterios de codificación propios (en inglés), no la definición local de piquete.",
      "Cuenta eventos de protesta (marchas, concentraciones), no cortes de calle: complementa, no sustituye, al indicador de orden público.",
    ],
    faltantes: "Si la descarga falla, se usa el archivo local versionado de la última descarga exitosa; el dato sigue publicándose como contexto.",
    revisiones: "La fuente revisa y agrega semanas hacia atrás; el archivo local se regenera completo en cada descarga exitosa.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Alta como indicador de contexto, con cobertura desde 2018 (línea de base 2023 real). En la revisión posterior se confirmó que siga fuera del índice." },
      { fecha: "2026-07-07", cambio: "El mismo dato pasa a integrar también, como indicador de condición de gobernabilidad, la dimensión de conflicto social del índice del cinturón político." },
      { fecha: "2026-07-09", cambio: "Umbrales de puntaje del índice político recalibrados (antes ±30/±10, simétricos y nunca validados) reconstruyendo la métrica de puntaje mes a mes sobre la serie ya existente (30 meses reales, dic-2023 a may-2026): nuevos cortes en -6,0/-3,0/0,0/10,0. Con las anclas viejas, el 73% de los meses caía en el mismo escalón intermedio." },
      { fecha: "2026-07-10", cambio: "Deja de puntuar también en el índice político: la revisión editorial acotó ese índice a la capacidad de gestionar y avanzar la agenda de gobierno. Queda como indicador de contexto en los dos cinturones, con la misma card y el mismo gráfico." },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════
  // Vida cotidiana — componentes base-100 del ITVC (100 = promedio 4T-2023)
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
      "Pertenece a la dimensión de sostenibilidad de ingresos y es el componente más pesado del ITVC (22,75% efectivo).",
      "El ITVC promedia sus componentes base-100 por dimensión: por encima de 100, la brecha acumula mejora contra el arranque del mandato.",
    ],
    limitaciones: [
      "El RIPTE cubre solo asalariados formales estables: deja afuera a informales y cuentapropistas; la canasta es por adulto equivalente.",
      "El peso del componente (22,75% del índice) es una discusión abierta declarada del diseño.",
      "Efecto base auditado: parte de la mejora contra el 4º trimestre de 2023 es rebote de la devaluación de diciembre.",
    ],
    faltantes: "Si una fuente falla, se mantiene el último valor publicado (marcado como desactualizado); si el componente no calcula, los pesos del índice se renormalizan.",
    revisiones: "Cada corrida re-descarga las series completas y adopta las revisiones de las fuentes; con canasta fresca sin salario, el par se declara provisorio.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC base-100 como rebase directo del cociente, con 22,75% de peso efectivo." },
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
      "Pertenece a la dimensión de presión de precios (40% interno · 10% del ITVC).",
      "La comparación contra el IPC general evita contar dos veces el ratio salario/comida, que ya mide la brecha con la canasta.",
    ],
    limitaciones: [
      "La métrica anterior (alimentos contra salario) correlacionaba casi uno a uno con la brecha de la canasta: un tercio del índice contaba dos veces lo mismo. Se corrigió con el rediseño relativo al IPC general.",
      "Leve estacionalidad de la canasta alimentaria aceptada sin corrección, auditada y declarada.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, los pesos del índice se renormalizan.",
    revisiones: "La API sirve la serie revisada; la base del 4º trimestre de 2023 se recalcula dinámicamente de la propia serie.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC base-100 (entonces como nivel contra el salario)." },
      { fecha: "2026-07-04", cambio: "Rediseño: nivel contra el IPC general, eliminando el doble conteo con la brecha salario/canasta." },
    ],
  },

  endeudamiento_familiar: {
    tipo: "indicador",
    id: "endeudamiento_familiar",
    cinturon: "vida_cotidiana",
    rezago: "La card (stock de crédito) casi no tiene rezago; el componente del índice usa el anexo del Informe sobre Bancos, ~2 meses atrás.",
    fuente: {
      organismo: "BCRA",
      operacion: "Card: préstamos personales + tarjetas de crédito (estadísticas monetarias). Componente: saldos y mora de las familias del anexo del Informe sobre Bancos",
      serie: "API de Estadísticas Monetarias (variables 114 y 115) + anexo del Informe sobre Bancos (planilla de calidad de cartera, sección Familias)",
      url: "https://www.bcra.gob.ar/PublicacionesEstadisticas/Informe_mensual_sobre_bancos.asp",
      acceso: "Automático: API pública para el stock y lectura de la planilla oficial para deuda real y mora.",
    },
    transformaciones: [
      "El componente combina dos cosas: la deuda de las familias deflactada por IPC y la mora de esa cartera contra su nivel del 4º trimestre de 2023.",
      "Polaridad empírica declarada: más deuda con mora estable es acceso al crédito (mejora); más deuda con mora disparada es sobreendeudamiento (deterioro).",
      "Sin piso de recorte deliberadamente: la crisis no se maquilla — se señaliza.",
    ],
    incidenciaTexto: [
      "Es el único componente de la dimensión de vulnerabilidad financiera (10% del ITVC) — hoy la dimensión está marcada como crítica y es el componente que domina la lectura del índice.",
    ],
    limitaciones: [
      "La mora de las familias se multiplicó por más de cinco desde la base: el componente concentra el arrastre del índice, y así se publica.",
      "Card y componente miden cortes distintos de la misma realidad (stock vivo contra cartera bancaria consolidada).",
      "Si el BCRA discontinuara la mora por línea, el plan declarado es volver a deuda real sin corrección.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin el componente, la dimensión de vulnerabilidad desaparece y su peso se redistribuye.",
    revisiones: "La planilla oficial se relee completa en cada corrida y adopta las revisiones del BCRA.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC como deuda real castigada por mora, con la polaridad empírica documentada (corrección sobre el diseño original)." },
      { fecha: "2026-07-04", cambio: "Se decide no aplicarle piso de recorte: la primera prueba con piso maquillaba el deterioro y se revirtió." },
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
      "Pertenece a la dimensión de presión de precios (60% interno · 15% del ITVC).",
      "Captura el efecto de la quita de subsidios que el IPC general diluye.",
    ],
    limitaciones: [
      "La tensión equivalente del componente excede la escala del cinturón y se corta en el máximo: el deterioro es mayor que lo que la escala muestra.",
      "Depende del RIPTE, que cubre solo asalariados formales.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización.",
    revisiones: "Re-descarga completa por corrida; base dinámica de la propia serie.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC base-100 como nivel de regulados contra el salario (antes puntuaba por variación mensual anclada)." },
    ],
  },

  consumo_carne: {
    tipo: "indicador",
    id: "consumo_carne",
    cinturon: "vida_cotidiana",
    rezago: "La cámara publica el informe de cada mes con un mes de demora; el titular y la serie avanzan juntos apenas aparece el informe nuevo.",
    fuente: {
      organismo: "CICCRA — Cámara de la Industria y Comercio de Carnes",
      operacion: "Informe económico mensual: consumo aparente de carne vacuna por habitante, promedio móvil de 12 meses anualizado",
      url: "https://ciccra.com.ar/",
      acceso: "Automático: lectura del informe mensual (PDF); cada informe se procesa una sola vez y queda en el archivo propio de la serie.",
    },
    transformaciones: [
      "La fuente ya publica el promedio móvil de 12 meses: desestacionaliza por construcción.",
      "Componente del índice: el consumo rebaseado a 100 = promedio del 4º trimestre de 2023 (menos carne = deterioro).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y seguridad (10% interno · 1,5% del ITVC).",
    ],
    limitaciones: [
      "Consumo «aparente» (producción menos exportaciones), no medición de hogares; la sustitución por pollo o cerdo no se captura.",
      "Fuente sectorial privada, publicada en PDF sin interfaz de datos: la lectura depende del formato del informe.",
      "La línea de base del 4º trimestre de 2023 usa la foto contemporánea de entonces, declarada; el dato revisado de la fuente difiere levemente.",
    ],
    faltantes: "Un mes sin informe legible queda vacío en la serie y se reintenta el mes más reciente en cada corrida; el titular nunca retrocede respecto de la serie publicada.",
    revisiones: "Los informes procesados no se releen; si la fuente revisa, el dato nuevo entra por el informe siguiente.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC con línea de base documentada; el mismo día se reconstruyó la serie mensual real desde octubre de 2023 y pasó a rebase dinámico." },
      { fecha: "2026-07-06", cambio: "El titular queda protegido contra retrocesos: si la lectura en vivo devuelve un informe más viejo que el ya publicado en la serie (falla transitoria de la fuente), se mantiene el último punto de la serie." },
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
      "Pertenece a la dimensión de sostenibilidad de ingresos (35% interno · 12,25% del ITVC).",
    ],
    limitaciones: [
      "Solo asalariados: no captura la informalidad cuentapropista.",
      "Serie trimestral contra una base de un solo trimestre: sesgo estacional chico, aceptado y declarado.",
      "La serie trimestral pública original se discontinuó en 2020; la vigente la reemplaza desde el rediseño del componente.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, la brecha salarial absorbe el peso de la dimensión.",
    revisiones: "La encuesta se revisa; la re-descarga completa por corrida adopta las revisiones.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC vía la serie anual disponible, invertida, con base en el año 2023." },
      { fecha: "2026-07-04", cambio: "Pasa a la serie trimestral con base exacta en el 4º trimestre de 2023 (la anual solo se actualizaba una vez al año y planchaba el componente)." },
    ],
  },

  mortalidad_pymes: {
    tipo: "indicador",
    id: "mortalidad_pymes",
    cinturon: "vida_cotidiana",
    rezago: "~2 meses (calendario de difusión industrial del INDEC).",
    fuente: {
      organismo: "INDEC",
      operacion: "IPI manufacturero — índice de producción industrial, serie desestacionalizada (aproximación declarada de la mortandad de empresas)",
      serie: "453.1_SERIE_DESEADA_0_0_24_58 · API de datos.gob.ar",
      url: "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-6-15",
      acceso: "Automático: API pública de series de tiempo.",
    },
    transformaciones: [
      "Componente del índice: el nivel desestacionalizado rebaseado a 100 = promedio del 4º trimestre de 2023.",
      "Se usa la serie desestacionalizada porque la original mostraba variaciones de hasta ±20% mensual de puro calendario.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de prospectivas de empleo (45% interno · 6,75% del ITVC).",
    ],
    limitaciones: [
      "Es una aproximación declarada: mide producción industrial agregada, no mortandad de empresas — el nombre del indicador promete más de lo que la fuente da.",
      "La taxonomía de la dimensión (empleo sin medidas directas de empleo) es una discusión abierta declarada del diseño.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "Los factores de desestacionalización se recalculan y revisan la serie; la re-descarga completa los absorbe.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC como nivel desestacionalizado base-100 (antes puntuaba por variación mensual de la serie original, dominada por estacionalidad)." },
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
      "Pertenece a la dimensión de prospectivas de empleo (40% interno · 6% del ITVC).",
    ],
    limitaciones: [
      "Aproximación al empleo vía actividad de la construcción, no despachos de cemento reales (la serie de insumos existe aparte, como contraste).",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "Serie desestacionalizada revisable por la fuente; re-descarga completa por corrida.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC como nivel desestacionalizado base-100; el mismo día el gráfico pasó a la misma métrica del titular (antes mostraba otra serie de insumos por un alias)." },
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
      "Pertenece a la dimensión de prospectivas de empleo (15% interno · 2,25% del ITVC).",
    ],
    limitaciones: [
      "Aproximación declarada: mide gente que trabaja poco y busca más, no la tenencia de múltiples empleos.",
      "Trimestral contra base de un trimestre: sesgo estacional chico aceptado.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "La encuesta se revisa; re-descarga completa por corrida.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC con rebase invertido base-100." },
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
      url: "https://www.utdt.edu/ver_contenido.php?id_contenido=1626&id_item_menu=2964",
      acceso: "Automático: los informes mensuales se descubren desde el listado de la universidad y cada uno se procesa una sola vez; el registro oficial de delitos (SNIC) se publica como serie de contraste.",
    },
    transformaciones: [
      "Componente del índice: el porcentaje de hogares víctimas, rebaseado de forma invertida (menos victimización = mejora) con base declarada en enero de 2024 — no existe medición del 4º trimestre de 2023.",
      "La ventana de 12 meses de la pregunta desestacionaliza por construcción.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y seguridad (30% interno · 4,5% del ITVC).",
    ],
    limitaciones: [
      "La encuesta estuvo suspendida entre 2020 y 2023: la base de enero de 2024 es una aproximación declarada del arranque (su ventana de 12 meses cubre mayormente el año previo).",
      "Error muestral de ±3 puntos por mes (~1.000 hogares) y cobertura solo urbana.",
      "La divergencia con el registro de denuncias se publica como información: denuncias bajando con victimización subiendo indica que crece el delito no denunciado.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "Los informes procesados no se releen; el registro oficial de contraste se revisa hacia atrás y su serie se refresca completa.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC vía el registro anual de delitos, invertido, con base 2023." },
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
      url: "https://www.utdt.edu/ver_contenido.php?id_contenido=2575&id_item_menu=4972",
      acceso: "Automático: se descubre la planilla más reciente desde el listado de la universidad y se lee la serie completa.",
    },
    transformaciones: [
      "Componente del índice: el ICC rebaseado a 100 = promedio del 4º trimestre de 2023 (más confianza = mejora).",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y seguridad (45% interno · 6,75% del ITVC).",
    ],
    dobleUso: "Triple función declarada: (1) componente del ITVC; (2) indicador del cinturón espíritu de época, con fórmula de tensión propia; (3) ancla de la validación externa del ITVC — para no ser circular, en ese estudio el índice se recalcula sin este componente.",
    limitaciones: [
      "Mide percepción y ánimo, no condiciones materiales: por diseño convive con medidas de conducta (consumo, patentamientos) en la misma dimensión.",
      "Depende del formato de publicación de la universidad: un cambio en el listado o la planilla interrumpe la lectura hasta adaptarla.",
    ],
    faltantes: "Se mantiene el último valor publicado como desactualizado; sin componente, renormalización dentro de la dimensión.",
    revisiones: "La planilla oficial trae la serie completa en cada descarga y adopta las revisiones de la fuente.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC base-100 con 50% interno de su dimensión." },
      { fecha: "2026-07-04", cambio: "Cede cinco puntos de peso interno al sentimiento digital, que mide lo mismo por conducta de búsqueda." },
    ],
  },

  sentimiento_digital: {
    tipo: "indicador",
    id: "sentimiento_digital",
    cinturon: "vida_cotidiana",
    rezago: "Hasta un mes: el mes en curso se descarta por incompleto; la card muestra además un pulso de los últimos tres meses casi en tiempo real.",
    fuente: {
      organismo: "Google Trends (fuente no oficial)",
      operacion: "Interés de búsqueda en Argentina de una canasta de cuatro términos de urgencia económica: inflación, precios, inseguridad y trabajo",
      url: "https://trends.google.com/",
      acceso: "Automático: consulta mensual de la canasta en ventana fija (2021 en adelante); cada descarga sana reemplaza el archivo completo — corridas con escalas distintas nunca se mezclan.",
    },
    transformaciones: [
      "Componente del índice: la canasta mensual rebaseada de forma invertida (más búsquedas de urgencia = peor) contra el promedio del 4º trimestre de 2023.",
      "El cociente entre valores de una misma consulta cancela la renormalización de escala de la fuente — verificado con corridas repetidas idénticas.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y seguridad (10% interno · 1,5% del ITVC): peso chico acorde a un constructo blando.",
      "La card muestra el pulso de tres meses; el puntaje usa la canasta mensual de ventana fija — doble registro declarado.",
    ],
    dobleUso: "Integra también el cinturón espíritu de época con fórmula de tensión propia.",
    limitaciones: [
      "Mide atención, no sentimiento: una noticia dispara búsquedas sin que cambie el bolsillo.",
      "Fuente no oficial con límites de consulta: si el servicio restringe el acceso, la serie continúa desde el archivo propio.",
      "Validación de constructo documentada: es la serie del cinturón que más co-mueve con la inflación mensual.",
    ],
    faltantes: "Con la fuente caída, la serie sale del archivo propio (con su fecha declarada); la card mantiene el último valor como desactualizado.",
    revisiones: "Reemplazo total del archivo en cada descarga sana; la fuente no revisa datos propiamente.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Declarado indicador de contexto: la ventana de tres meses no permitía línea de base 2023." },
      { fecha: "2026-07-04", cambio: "Pasa a componente puntuable tras un banco de pruebas empírico: la canasta de ventana fija con cociente interno resultó estable entre corridas y consistente con la inflación." },
    ],
  },

  patentamiento_motos: {
    tipo: "indicador",
    id: "patentamiento_motos",
    cinturon: "vida_cotidiana",
    rezago: "Menos de un mes: se toma el último mes calendario completo (el mes en curso sería un acumulado parcial).",
    fuente: {
      organismo: "CAFAM — Cámara Argentina de Fabricantes de Motovehículos",
      operacion: "Patentamientos mensuales de motovehículos, total país",
      serie: "API pública de patentamientos de CAFAM (histórico mensual por provincia)",
      url: "https://www.cafam.org.ar/",
      acceso: "Automático: API pública sin credenciales; la serie histórica se consulta mes a mes desde fines de 2022.",
    },
    transformaciones: [
      "Componente del índice: el promedio móvil de 12 meses contra las ventanas móviles equivalentes del 4º trimestre de 2023 — la estacionalidad del flujo crudo es fuerte (enero duplica a junio).",
      "Recorte declarado: el componente se acota al techo de 140 — un boom puntual no compra compensación ilimitada dentro del índice; el valor crudo queda declarado en el detalle.",
    ],
    incidenciaTexto: [
      "Pertenece a la dimensión de confianza y seguridad (5% interno · 0,75% del ITVC): el peso más chico del índice.",
    ],
    limitaciones: [
      "Es el componente más eufórico del cinturón (muy por encima de su base): motivo del techo de recorte y de la baja de peso.",
      "Aproximación al consumo discrecional financiado, no al bienestar general.",
    ],
    faltantes: "Un mes que falla en la API se saltea; la card mantiene el último valor como desactualizado; sin componente, renormalización.",
    revisiones: "La API expone el histórico completo y se reconsulta entero en cada corrida.",
    cambios: [
      { fecha: "2026-07-03", cambio: "Entra al ITVC con rebase simple del flujo mensual; el mismo día pasa al acumulado móvil de 12 meses por la estacionalidad." },
      { fecha: "2026-07-04", cambio: "Se aplica el techo de recorte 140 y el peso interno baja de 10% a 5%." },
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
      "Quince indicadores puntúan en cinco dimensiones (la tabla de composición muestra la estructura vigente con los puntajes de hoy), más dos series de contexto declaradas que no integran el índice.",
      "Criterio de selección: fuentes públicas verificables y automatizables. Hoy el cinturón es 100% automático: el único registro curado a mano (privatizaciones) cita la norma del Boletín Oficial detrás de cada estado.",
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
  // ITVC — índice base-100 del cinturón vida cotidiana (checklist OCDE/JRC)
  // ═══════════════════════════════════════════════════════════════════════
  itvc: {
    tipo: "indice",
    id: "itvc",
    sigla: "ITVC",
    nombreLargo: "Índice de Tensión del Cinturón de Vida Cotidiana",
    base100: true,
    cinturon: "vida_cotidiana",
    resumen: "Índice de seguimiento base 100: cada componente se compara contra el promedio del 4º trimestre de 2023 (el arranque del mandato). Más de 100 = mejora acumulada de la vida cotidiana; menos de 100 = deterioro. Trece componentes en cinco dimensiones.",
    marcoConceptual: [
      "El cinturón de vida cotidiana mide el bolsillo y la calle: ingresos contra canasta, precios sensibles, endeudamiento de las familias, empleo y el clima de confianza y seguridad.",
      "El marco proviene del documento institucional del ITVC en versión base 100 (Fundación CIGOB, julio de 2026), heredero del Monitor de la Vida Cotidiana de mayo de 2026. A diferencia del ITCM y el ITCG, no usa tablas de umbrales: mide la evolución acumulada contra una línea de base común — el arranque del mandato.",
    ],
    seleccion: [
      "Trece componentes en cinco dimensiones (la tabla muestra la composición vigente con los niveles de hoy). Todos puntúan: el cinturón no tiene indicadores de contexto.",
      "Criterio: fuentes públicas con serie reconstruible al 4º trimestre de 2023 — o con línea de base declarada donde no existe medición de entonces (la encuesta de victimización arranca su base en enero de 2024, documentado).",
    ],
    tratamiento: [
      "Componentes faltantes: los pesos se renormalizan dentro de la dimensión y entre dimensiones; ante una fuente caída, el indicador mantiene su último valor publicado marcado como desactualizado.",
      "Polaridad: los componentes donde «más es peor» (informalidad, victimización, subocupación, búsquedas de urgencia) se invierten para que en todos valga la misma lectura: por encima de 100, mejora.",
      "Recorte asimétrico declarado: los componentes se acotan a un techo de 140 (un boom puntual no compra compensación ilimitada) y deliberadamente NO tienen piso — el deterioro no se recorta, se señaliza con el flag de dimensión crítica.",
    ],
    normalizacion: [
      "Cada componente es un índice continuo rebaseado a 100 = promedio del 4º trimestre de 2023 (o su base declarada). No hay bandas ni anclas: la normalización es el rebase, y las transformaciones por componente (acumulados móviles, deflactación, relativos al IPC general) están documentadas en cada ficha.",
    ],
    agregacion: {
      latex: String.raw`\text{ITVC}=\sum_{\text{5 dimensiones}}\text{peso}_{\text{dim}}\times\Big(\sum_{\text{componentes}}\text{peso}_{\text{interno}}\times\min(\text{componente},140)\Big)`,
      leyenda: "Promedio ponderado en dos niveles (35% ingresos · 25% precios · 10% vulnerabilidad financiera · 15% empleo · 15% confianza y seguridad), con el techo de recorte declarado.",
      parrafos: [
        "La agregación es compensatoria y el flag de dimensión crítica lo declara cuando una dimensión cae por debajo del umbral: hoy la vulnerabilidad financiera (endeudamiento con mora) está marcada crítica y domina la lectura del índice.",
      ],
    },
    robustez: [
      "Análisis de sensibilidad Monte Carlo: el índice se recalcula en 1.000 escenarios perturbando los pesos ±20% (al ser componentes continuos, el ruido de insumos llega vía el propio rebase). La banda del 90% de los escenarios se publica en cada edición.",
      "Se acompaña con el ejercicio de quitar cada componente por vez.",
    ],
    validacion: [
      "El índice se reconstruye mes a mes desde diciembre de 2023 y se contrasta contra el Índice de Confianza del Consumidor (UTDT). Para no ser circular — el ICC es también un componente —, en el estudio el ITVC se recalcula sin ese componente.",
      "La matriz de validación cruzada verifica además que cada índice del informe correlacione más con su ancla propia que con las ajenas; la matriz completa se publica en la página del cinturón.",
    ],
    comunicacion: [
      "El resto del informe consume el índice como tensión 0–10 con su propia fórmula: tensión = 5 − (ITVC − 100) × 0,2. Un índice en 100 (sin cambios contra el arranque) equivale a tensión 5; cada 5 puntos de índice mueven un punto de tensión.",
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
      "Dos discusiones de diseño están abiertas y declaradas: el peso de la brecha salarial (22,75%, el mayor del índice) y la taxonomía de las dimensiones de empleo y confianza.",
      "El análisis multivariado previo del estándar OCDE/JRC está pendiente; la eliminación del doble conteo salario/comida (detectado por correlación casi perfecta entre dos componentes) fue un paso en esa dirección.",
    ],
    cambios: [
      { fecha: "2026-05", cambio: "Versión inicial del cinturón: fórmulas de tensión ancladas por indicador, promediadas." },
      { fecha: "2026-07-03", cambio: "Nace el ITVC base 100: reemplaza el promedio de fórmulas ancladas por la evolución acumulada contra el 4º trimestre de 2023, con robustez Monte Carlo y flag de dimensión crítica publicados. Los patentamientos pasan al acumulado móvil de 12 meses por estacionalidad." },
      { fecha: "2026-07-04", cambio: "Barrido componente por componente: la victimización pasa de la serie anual de denuncias a la encuesta mensual; se elimina el doble conteo salario/comida (dos componentes correlacionaban 0,985); se aplica el techo de recorte 140 sin piso; el sentimiento digital pasa a puntuar tras un banco de pruebas empírico; y la matriz de validación cruzada queda como tercer pilar de robustez." },
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
      "A diferencia del ITCM, el ITCG y el ITVC, no existe un documento institucional que fije los pesos de estas cinco dimensiones: el marco ya las describía, pero nunca se habían ponderado. Los pesos son una decisión editorial explícita, apoyada en esa misma distinción del marco: la dimensión de imagen y voto pesa deliberadamente menos que las otras cuatro, porque el proyecto distingue capital político de popularidad electoral.",
    ],
    seleccion: [
      "Once indicadores puntúan en cinco dimensiones (la tabla de composición de abajo muestra la estructura vigente con los puntajes de hoy). El tablero publica solo lo que integra el índice: dos mediciones que quedaron fuera del puntaje (la rotación del gabinete y las protestas en la Ciudad de Buenos Aires) se siguen relevando como seguimiento interno, sin tile propio. Reemplaza a un promedio simple de nueve indicadores que pesaba todo por igual, sin distinguir la capacidad de gobernar de la popularidad.",
      "Criterio de selección: fuentes públicas verificables y automatizables. Los indicadores vigentes se calculan en forma automática (la rotación del gabinete, desde un registro curado con respaldo documental en el Boletín Oficial). El alineamiento de los gobernadores —una estimación manual del analista, sin fuente pública estructurada que lo mida de forma objetiva— se retiró del índice en julio de 2026 y lo reemplazó el alineamiento de voto de los senadores por provincia; los caminos alternativos evaluados (composición legislativa por provincia, transferencias discrecionales) resultaron no ser proxies válidos de la conducta del Poder Ejecutivo provincial.",
      "La revisión editorial de julio de 2026 acotó el alcance del índice a la capacidad del gobierno de gestionar y avanzar su agenda —el Parlamento, las alianzas territoriales y la cohesión del oficialismo—: la rotación del gabinete y el volumen de protesta quedaron fuera del puntaje y del tablero, aunque su recolección continúa (mismo criterio que los insumos monetarios del índice macroeconómico).",
    ],
    tratamiento: [
      "Indicadores faltantes: los pesos se renormalizan entre los presentes, primero dentro de la dimensión y, si una dimensión queda vacía, entre dimensiones.",
      "Juicio experto: la paramétrica admite ajustes manuales por indicador con justificación escrita y fecha de vencimiento (un ajuste vencido se ignora solo); todo ajuste activo se publica junto al índice.",
      "Varios indicadores —la cohesión del bloque propio (hoy un único indicador bicameral: Diputados 65% y Senado 35% dentro de la misma fórmula), el alineamiento de senadores por provincia, la adhesión provincial a un régimen de inversión y las derrotas legislativas— son incorporaciones o redefiniciones de julio de 2026: sus series mensuales se reconstruyeron hacia atrás desde las fuentes (24 a 31 meses según el indicador) y sus umbrales se calibraron contra esa historia real. La excepción declarada es la adhesión provincial, cuyos umbrales no se recalibraron: la adhesión es un proceso acumulativo todavía en curso y su rango observado no es una muestra representativa.",
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
      "El ITCP se contrasta contra el EPU de Argentina (Economic Policy Uncertainty: minería de texto sobre diarios locales, la misma familia metodológica que el índice de Baker/Bloom/Davis): el índice se reconstruye mes a mes desde las series de sus componentes y se correlaciona contra el EPU — la correlación esperada es negativa (más capital político, menos incertidumbre de política en la prensa) y el resultado se publica en la sección de validación del cinturón, actualizado en cada corrida.",
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
    ],
  },
};
