// Descripción por indicador: qué es, qué aporta a la lectura del cinturón,
// con qué frecuencia se publica y qué tipo de dato es. Se usa en el modal.
export interface Descripcion {
  que: string;
  aporta: string;
  frecuencia: string;
  tipo: string;
}

export const DESCRIPCIONES: Record<string, Descripcion> = {
  // ── Macroeconomía (el motor económico) ──────────────────────────
  ipc_total: {
    que: "Variación mensual del nivel general de precios al consumidor (INDEC).",
    aporta: "Es el termómetro central de la estabilización: marca si el programa antiinflacionario avanza o se estanca.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  reservas_bcra: {
    que: "Reservas NETAS del Banco Central (metodología Machado/OPEN): brutas menos los pasivos en dólares (encajes, swap China, préstamos a organismos y repos a 12m), calculadas con datos oficiales del BCRA.",
    aporta: "Miden los dólares de libre disponibilidad reales: a diferencia de las brutas, descuentan la deuda en moneda extranjera. Son el verdadero colchón para defender el peso y pagar deuda.",
    frecuencia: "Diaria (brutas) + pasivos mensuales", tipo: "Nivel neto (stock)",
  },
  idc: {
    que: "Índice de Capacidad Prestable: combina tasa real de la BADLAR (precio), depósitos privados reales (volumen) y holgura préstamos/depósitos (asignación).",
    aporta: "Resume si el sistema financiero tiene fondos y disposición para prestar. >1,02 expansión (verde), 0,98-1,02 neutro (amarillo), <0,98 contracción (rojo).",
    frecuencia: "Mensual", tipo: "Índice (~1,0)",
  },
  badlar: {
    que: "Tasa que pagan los bancos por depósitos mayoristas a 30 días o más (referencia de contexto; insumo del IdC).",
    aporta: "Refleja el costo del dinero y el sesgo de la política monetaria (más o menos restrictiva).",
    frecuencia: "Diaria", tipo: "Tasa",
  },
  emae_ia: {
    que: "Variación interanual del Estimador Mensual de Actividad Económica.",
    aporta: "Adelanta el pulso del PBI: si la economía crece o se contrae mes a mes.",
    frecuencia: "Mensual", tipo: "Variación i.a.",
  },
  saldo_comercial_12m: {
    que: "Balance acumulado de exportaciones menos importaciones de los últimos 12 meses.",
    aporta: "Indica si el sector externo genera o drena los dólares que necesita el programa.",
    frecuencia: "Mensual", tipo: "Nivel (acum. 12m)",
  },
  recaudacion: {
    que: "Variación INTERANUAL REAL de la recaudación tributaria nacional (deflactada por el IPC del mismo período).",
    aporta: "Aísla la recuperación genuina de los ingresos del efecto inflacionario: mide la salud fiscal en términos reales.",
    frecuencia: "Mensual", tipo: "Variación i.a. real",
  },
  tcrm: {
    que: "Tipo de cambio real multilateral: competitividad cambiaria frente a los socios comerciales (base 2010=100).",
    aporta: "Señala si el peso está caro o barato, clave para exportar y acumular reservas.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  rem_ipc_12m: {
    que: "Inflación esperada a 12 meses según el Relevamiento de Expectativas de Mercado del BCRA.",
    aporta: "Captura la credibilidad del programa. Se puntúa por su equivalente mensual (raíz 12), en la misma escala que la inflación realizada: cuanto menor la inflación mensual esperada, mayor la credibilidad.",
    frecuencia: "Mensual", tipo: "Expectativa",
  },
  prestamos_privados: {
    que: "Variación del crédito bancario otorgado al sector privado.",
    aporta: "Mide si el sistema financiero acompaña la actividad con financiamiento.",
    frecuencia: "Diaria", tipo: "Variación",
  },
  base_monetaria: {
    que: "Variación de la base monetaria (billetes en circulación más reservas bancarias).",
    aporta: "Refleja la emisión y el ancla monetaria sobre la que descansa el plan.",
    frecuencia: "Diaria", tipo: "Variación",
  },
  tc_mayorista: {
    que: "Variación del tipo de cambio oficial mayorista de referencia.",
    aporta: "Marca el ritmo de devaluación del ancla cambiaria del programa.",
    frecuencia: "Diaria", tipo: "Variación",
  },

  // ── Política (el tablero de poder) ──────────────────────────────
  votometro_ventaja_lla: {
    que: "Diferencia de intención de voto ponderada entre LLA y el PJ (Votómetro CIGOB).",
    aporta: "Mide el capital electoral del oficialismo, base de su poder de negociación.",
    frecuencia: "Continua", tipo: "Brecha (pp)",
  },
  ratio_dnu: {
    que: "Cantidad de Decretos de Necesidad y Urgencia sobre leyes sancionadas en el año.",
    aporta: "Un ratio alto indica un Ejecutivo que legisla por decreto ante un Congreso que no acompaña.",
    frecuencia: "Continua (año)", tipo: "Ratio",
  },
  movilizacion_cepa: {
    que: "Índice de conflictividad social y laboral relevado por el CEPA.",
    aporta: "Aproxima la tensión en la calle, un límite real al margen de maniobra del Gobierno.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
  },
  iaf_transferencias: {
    que: "Variación real interanual de las transferencias federales a las provincias.",
    aporta: "Mide la armonía —o el conflicto— fiscal con los gobernadores.",
    frecuencia: "Anual", tipo: "Variación real",
  },
  eficacia_legislativa: {
    que: "Porcentaje de proyectos enviados por el Ejecutivo que el Congreso aprobó (ventana de 12 meses).",
    aporta: "Mide la capacidad real de convertir la agenda de gobierno en ley.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },
  cohesion_bloque: {
    que: "Porcentaje de diputados de LLA que votan alineados con la posición oficial del bloque.",
    aporta: "Indica la disciplina de la tropa propia, clave para sostener vetos y aprobar leyes.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  gobernadores_alineamiento: {
    que: "Porcentaje de gobernadores cuya posición pública es de alineamiento con la política nacional.",
    aporta: "Mide el apoyo territorial, decisivo en el Senado y en la gobernabilidad.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  veto_quorum: {
    que: "Porcentaje de sesiones de Diputados frustradas por falta de quórum.",
    aporta: "Señala la capacidad de la oposición de bloquear o forzar la agenda parlamentaria.",
    frecuencia: "Continua", tipo: "Nivel (%)",
  },
  comisiones_caidas: {
    que: "Porcentaje de proyectos con dictamen de comisión que nunca llegaron al recinto.",
    aporta: "Mide el embudo legislativo: cuánto queda trabado antes de poder votarse.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },

  // ── Vida cotidiana (el bolsillo y la calle) ─────────────────────
  brecha_salario_cbt: {
    que: "Cantidad de canastas básicas totales que cubre el salario formal promedio (RIPTE/CBT).",
    aporta: "Mide el poder adquisitivo real del ingreso, lo que la gente siente en el bolsillo.",
    frecuencia: "Mensual", tipo: "Ratio (canastas)",
  },
  ipc_alimentos: {
    que: "Variación mensual de los precios de alimentos y bebidas (INDEC).",
    aporta: "Es la inflación más sensible socialmente: pega directo en la mesa de cada hogar.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  endeudamiento_familiar: {
    que: "Saldo del crédito de consumo de las familias (tarjeta más préstamos personales), en billones de pesos.",
    aporta: "Refleja si los hogares llegan a fin de mes apoyándose en deuda.",
    frecuencia: "Diaria", tipo: "Nivel (stock)",
  },
  peso_tarifas: {
    que: "Variación mensual de los precios regulados (luz, gas, agua, transporte).",
    aporta: "Mide el impacto de la quita de subsidios sobre el gasto fijo del hogar.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  consumo_carne: {
    que: "Consumo aparente de carne vacuna por habitante al año (CICCRA).",
    aporta: "Proxy histórico del bienestar alimentario y del poder de compra popular.",
    frecuencia: "Mensual", tipo: "Nivel per cápita",
  },
  informalidad: {
    que: "Porcentaje de asalariados sin descuento jubilatorio (empleo informal, INDEC EPH).",
    aporta: "Mide la precariedad laboral y la exclusión de la red de protección social.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  mortalidad_pymes: {
    que: "Variación de la actividad industrial manufacturera (IPI), usada como proxy.",
    aporta: "Aproxima la salud del entramado productivo y del empleo PyME.",
    frecuencia: "Mensual", tipo: "Variación (IPI)",
  },
  despacho_cemento: {
    que: "Índice de actividad de la construcción (ISAC, INDEC).",
    aporta: "Termómetro de la obra pública y privada, gran motor de empleo de baja calificación.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  pluriempleo: {
    que: "Porcentaje de subocupados que buscan trabajar más horas (INDEC EPH).",
    aporta: "Señala empleo insuficiente: gente ocupada a la que no le alcanza.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  inseguridad: {
    que: "Cantidad de hechos delictivos registrados por año (SNIC, Ministerio de Seguridad).",
    aporta: "Mide una de las principales preocupaciones cotidianas de la población.",
    frecuencia: "Anual", tipo: "Conteo",
  },
  icc_utdt: {
    que: "Índice de Confianza del Consumidor (Universidad Torcuato Di Tella).",
    aporta: "Captura el humor económico de la gente, que anticipa consumo y voto.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  sentimiento_digital: {
    que: "Interés de búsqueda en Google sobre inflación, precios y términos afines.",
    aporta: "Proxy en tiempo real de la urgencia económica percibida por la sociedad.",
    frecuencia: "Tiempo real", tipo: "Índice (0–100)",
  },
  patentamiento_motos: {
    que: "Unidades de motos patentadas en el mes (CAFAM).",
    aporta: "Proxy de consumo durable de los sectores medios y bajos.",
    frecuencia: "Mensual", tipo: "Conteo",
  },

  // ── Espíritu de época (el humor social) ─────────────────────────
  clima_electoral: {
    que: "Ventaja del oficialismo sobre el principal opositor (LLA − PJ) según el promedio ponderado de encuestas del Votómetro CIGOB.",
    aporta: "Proxy de la adhesión política al proyecto de gobierno: cuando el humor social acompaña, la ventaja se sostiene.",
    frecuencia: "Continua", tipo: "Brecha (pp)",
  },

  // ── Gestión (la capacidad de ejecutar) ──────────────────────────
  cepo_mulc: {
    que: "Brecha entre el dólar financiero (CCL) y el mayorista (referencia A3500 del BCRA).",
    aporta: "Mide el grado de normalización cambiaria, uno de los ejes del programa económico.",
    frecuencia: "Diaria", tipo: "Brecha (%)",
  },
  privatizaciones: {
    que: "Avance de la transferencia efectiva de empresas públicas al sector privado.",
    aporta: "Mide la ejecución de una reforma estructural emblema del Gobierno.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  concesiones_infraestructura: {
    que: "Avance de la concesión de corredores viales y obras de infraestructura.",
    aporta: "Indica si el Estado logra traspasar infraestructura al sector privado.",
    frecuencia: "Trimestral", tipo: "Avance de reforma",
  },
  reduccion_estado: {
    que: "Variación de la dotación de empleo del sector público.",
    aporta: "Mide el ajuste del tamaño del Estado, prioridad declarada del oficialismo.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  reestructuracion_organismos: {
    que: "Organismos públicos disueltos, fusionados o centralizados desde diciembre de 2023.",
    aporta: "Mide el avance concreto de la reforma del aparato estatal.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  rigi_inversiones: {
    que: "Avance de las inversiones aprobadas bajo el Régimen de Incentivo a Grandes Inversiones (RIGI).",
    aporta: "Señala la llegada de grandes inversiones, apuesta de crecimiento del plan.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  desregulacion_normativa: {
    que: "Normas derogadas o modificadas desde diciembre de 2023 (InfoLeg).",
    aporta: "Mide el ritmo de la desregulación económica impulsada por el Gobierno.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  apertura_comercial: {
    que: "Variación interanual de las importaciones totales, usada como proxy.",
    aporta: "Aproxima el grado de apertura de la economía al comercio exterior.",
    frecuencia: "Mensual", tipo: "Variación i.a.",
  },
  asistencia_directa: {
    que: "Porcentaje de beneficios sociales pagados sin intermediación de organizaciones.",
    aporta: "Mide la reforma del esquema de asistencia social y el corte de intermediarios.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  fal_modernizacion_laboral: {
    que: "Avance de implementación de la modernización laboral (Fondo de Asistencia Laboral).",
    aporta: "Indica el progreso de la reforma del régimen de trabajo.",
    frecuencia: "Por hito", tipo: "Avance de reforma",
  },
  libertad_opcion_salud: {
    que: "Opciones de cambio de obra social captadas por la Superintendencia de Servicios de Salud.",
    aporta: "Mide la desregulación del sistema de salud y la libre elección.",
    frecuencia: "Trimestral", tipo: "Avance de reforma",
  },
  protocolo_antipiquetes: {
    que: "Porcentaje de cortes de calle con carril libre garantizado.",
    aporta: "Mide la aplicación del protocolo de orden público en la vía pública.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
};
