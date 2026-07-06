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
//     faltantes, revisiones, ADRs, changelog) → este archivo.

export interface AdrRef {
  id: string;      // "ADR-0021"
  titulo: string;
}

export interface CambioMetodologico {
  fecha: string;   // "2026-07-03" o "2026-06" si la precisión es mensual
  cambio: string;
  adr?: string;    // referencia(s) al registro de decisiones
}

export interface FuenteFicha {
  organismo: string;    // quién produce el dato original
  operacion: string;    // la operación estadística / serie exacta
  serie?: string;       // identificador técnico de la serie (API)
  url?: string;         // página oficial de la fuente
  acceso: string;       // cómo lo obtiene el informe (automático/manual)
}

// Banda institucional tal como la publica el documento CIGOB, más los puntos
// ancla que usa el motor de interpolación (ADR-0021) para el ejemplo resuelto.
export interface AnclasFicha {
  bandas: { banda: string; puntaje: number }[];   // la tabla del documento
  puntos: [number, number][];                     // anclas [valor, puntaje], x ascendente
  unidadCorta: string;                            // "% m/m"
}

export interface FichaIndicador {
  tipo: "indicador";
  id: string;                       // clave técnica en informe.json / series.json
  cinturon: "macro" | "politica" | "vida_cotidiana" | "gestion" | "espiritu_epoca";
  rezago: string;                   // cuánto tarda la fuente en publicar
  fuente: FuenteFicha;
  transformaciones: string[];       // complemento en llano de la fórmula (ODS 4.c)
  anclas?: AnclasFicha;             // umbrales institucionales → puntaje
  dobleUso?: string;                // dónde más participa el dato dentro del sistema
  limitaciones: string[];           // ODS 4.b — declaradas, no escondidas
  faltantes: string;                // ODS 4.g
  revisiones: string;               // política de revisión (fuente y serie propia)
  adrs: AdrRef[];
  cambios: CambioMetodologico[];
}

export interface FichaIndice {
  tipo: "indice";
  id: string;                       // "itcm" (clave del bloque en informe.json)
  sigla: string;
  nombreLargo: string;
  cinturon: "macro" | "gestion" | "vida_cotidiana";
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
  adrs: AdrRef[];
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
    revisiones: "El INDEC no revisa retroactivamente el IPC publicado: la serie de la fuente es definitiva. Del lado del informe, la serie se reconstruyó hacia atrás hasta julio de 2021 y todo cambio de método propio queda asentado en el registro de decisiones (abajo).",
    adrs: [
      { id: "ADR-0021", titulo: "Puntaje interpolado entre anclas en ITCM e ITCG" },
      { id: "ADR-0019", titulo: "Revisión metodológica de las tres paramétricas (sensibilidad de umbrales y pesos)" },
    ],
    cambios: [
      {
        fecha: "2026-06",
        cambio: "El indicador deja de promediarse directamente como tensión 0–10 y pasa a puntuar dentro del ITCM según los umbrales institucionales de la paramétrica CIGOB (documento de mayo de 2026).",
      },
      {
        fecha: "2026-07-03",
        cambio: "El puntaje escalonado por banda se reemplaza por interpolación lineal entre anclas: se eliminan los saltos de 15–25 puntos entre valores casi iguales a ambos lados de un umbral. Los umbrales institucionales no cambian.",
        adr: "ADR-0021",
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
    adrs: [
      { id: "ADR-0009", titulo: "IDM y TCRM entran al ITCM (5ª dimensión: competitividad externa)" },
      { id: "ADR-0010", titulo: "Capítulo inversión: IAI e ICIP como 6ª dimensión" },
      { id: "ADR-0019", titulo: "Revisión metodológica de las tres paramétricas" },
      { id: "ADR-0020", titulo: "Flag de dimensión crítica: la compensabilidad se señaliza, no se corrige" },
      { id: "ADR-0021", titulo: "Puntaje interpolado entre anclas" },
      { id: "ADR-0022", titulo: "Crédito privado real al índice; las variables nominales quedan fuera de la publicación" },
      { id: "ADR-0028", titulo: "IdC rediseñado: z-scores de nivel contra la propia historia" },
      { id: "ADR-0029", titulo: "Recaudación real: promedio móvil de 3 meses sobre IPC cerrado" },
      { id: "ADR-0031", titulo: "Validación cruzada: matriz discriminante como tercer pilar de robustez" },
    ],
    cambios: [
      {
        fecha: "2026-06",
        cambio: "Entra en producción la paramétrica institucional (documento CIGOB de mayo de 2026): el cinturón deja el promedio simple de tensiones y pasa al ITCM de cuatro dimensiones ponderadas con umbrales por tabla.",
      },
      {
        fecha: "2026-06-28",
        cambio: "Se incorporan el IDM (desequilibrio monetario) a la dimensión de estabilidad y el TCRM como quinta dimensión (competitividad externa).",
        adr: "ADR-0009",
      },
      {
        fecha: "2026-06-30",
        cambio: "Capítulo inversión: IAI (física) e ICIP (digital) como sexta dimensión. La estructura de pesos queda 26 / 24 / 16 / 11 / 11 / 12 %.",
        adr: "ADR-0010",
      },
      {
        fecha: "2026-07-03",
        cambio: "Revisión metodológica: puntaje interpolado entre anclas, flag de dimensión crítica, crédito privado real al índice y variables nominales fuera de la publicación. El valor publicado pasó de 51,7 a 54,7 por el cambio de método, sin cambiar de banda de lectura.",
        adr: "ADR-0019 · 0020 · 0021 · 0022",
      },
      {
        fecha: "2026-07-04",
        cambio: "IdC rediseñado por z-scores contra su propia historia, recaudación como promedio móvil trimestral real y matriz de validación cruzada como tercer pilar de robustez.",
        adr: "ADR-0028 · 0029 · 0031",
      },
    ],
  },
};
