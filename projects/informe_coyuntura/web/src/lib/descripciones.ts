// Descripción por indicador: qué es, qué aporta a la lectura del cinturón,
// con qué frecuencia se publica y qué tipo de dato es. Se usa en el modal.
// Criterio del "que": explica QUÉ MIDE el indicador en términos conceptuales,
// NO de dónde sale el dato (eso está en el campo "Fuente") ni cómo se computa
// (eso está en "Cómo se calcula / Valor usado").
export interface Descripcion {
  que: string;
  aporta: string;
  frecuencia: string;
  tipo: string;
}

export const DESCRIPCIONES: Record<string, Descripcion> = {
  // ── Macroeconomía (el motor económico) ──────────────────────────
  ipc_total: {
    que: "Cuánto suben en el mes los precios al consumidor en general.",
    aporta: "Es el termómetro central de la estabilización: marca si el programa antiinflacionario avanza o se estanca.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  reservas_bcra: {
    que: "Los dólares de libre disponibilidad del Banco Central: lo que realmente posee, descontada la deuda en moneda extranjera de corto plazo. Más exigente que las brutas.",
    aporta: "Es el termómetro real de la solvencia externa: con netas bajas o negativas, cualquier shock obliga a devaluar o a frenar importaciones. Las brutas pueden lucir altas y ocultar esa fragilidad.",
    frecuencia: "Mensual", tipo: "Nivel neto (stock)",
  },
  idc: {
    que: "Índice de Capacidad Prestable: combina precio (BADLAR real), volumen (depósitos privados reales) y asignación (holgura préstamos/depósitos) para medir si el sistema financiero tiene fondos y disposición para prestar al sector privado.",
    aporta: "Un crédito que se expande acompaña la inversión y la actividad; uno que se contrae las ahoga. Semáforo: >1,02 expansión (verde) · 0,98–1,02 neutro (amarillo) · <0,98 contracción (rojo). Se arma con datos del BCRA (BADLAR, depósitos y préstamos privados) y el IPC del INDEC.",
    frecuencia: "Mensual", tipo: "Índice (~1,0)",
  },
  badlar: {
    que: "Tasa de referencia que pagan los bancos por captar depósitos mayoristas a 30 días o más.",
    aporta: "Refleja el costo del dinero y el sesgo de la política monetaria; hoy es insumo del Índice de Capacidad Prestable.",
    frecuencia: "Diaria", tipo: "Tasa",
  },
  emae_ia: {
    que: "El pulso mensual de la actividad económica: cuánto creció o cayó respecto de un año atrás.",
    aporta: "Adelanta el ritmo del PBI: si la economía se expande o se contrae.",
    frecuencia: "Mensual", tipo: "Variación i.a.",
  },
  saldo_comercial_12m: {
    que: "El balance entre lo que el país exporta y lo que importa, acumulado en los últimos 12 meses.",
    aporta: "Indica si el sector externo genera o drena los dólares que necesita el programa.",
    frecuencia: "Mensual", tipo: "Nivel (acum. 12m)",
  },
  recaudacion: {
    que: "Cuánto recauda el Estado en impuestos medido en términos reales: la variación respecto del mismo mes del año anterior, una vez descontada la inflación.",
    aporta: "Aísla la recuperación genuina de los ingresos del efecto inflacionario: mide la salud fiscal de verdad.",
    frecuencia: "Mensual", tipo: "Variación i.a. real",
  },
  tcrm: {
    que: "Si el peso está caro o barato frente a los socios comerciales, en términos reales (competitividad cambiaria). Mide la dimensión de competitividad externa del índice.",
    aporta: "Una apreciación real (peso caro) frena exportaciones y la acumulación de reservas, y suele anticipar presión cambiaria: cuanto más apreciado, más tensión. Un peso más competitivo afloja esa restricción.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  rem_ipc_12m: {
    que: "La inflación que el mercado espera para los próximos 12 meses.",
    aporta: "Captura la credibilidad del programa: si el mercado espera que la inflación siga bajando, el ancla de expectativas funciona; si la ve acelerarse, hay desconfianza.",
    frecuencia: "Mensual", tipo: "Expectativa",
  },
  idm: {
    que: "Índice de Desequilibrio Monetario: la brecha entre cuánto crece la oferta amplia de pesos del sector privado (M3 privado) y cuánto crece la demanda transaccional de dinero (M2 privado), ambos en términos reales e interanuales.",
    aporta: "Detecta si sobran pesos respecto de lo que la economía quiere retener: una brecha positiva señala excedente monetario que tiende a presionar la brecha cambiaria; una negativa indica remonetización genuina traccionada por la demanda real. Se construye con agregados del BCRA (circulante, depósitos y M2 privado) deflactados por el IPC.",
    frecuencia: "Mensual", tipo: "Brecha i.a. real",
  },
  iai: {
    que: "Índice Anticipador de Inversión: mide la inversión física/tradicional combinando la actividad de la construcción (ISAC) y la importación de bienes de capital, en variación interanual.",
    aporta: "Anticipa si el país amplía su capacidad productiva (máquinas, obra, equipo) o se descapitaliza. Mayor = la inversión se expande por encima de la reposición; negativo = se consume más stock de capital del que se genera. Se construye con datos del INDEC (ISAC + ICA bienes de capital).",
    frecuencia: "Mensual", tipo: "Variación i.a. ponderada",
  },
  icip: {
    que: "Índice de Capitalización Inteligente y Productividad: mide la inversión digital/intangible —pagos al exterior por servicios de informática (software, nube, IA) y productividad laboral (IPI/empleo)— en variación interanual.",
    aporta: "Capta el salto a la frontera tecnológica que no pasa por aduana como bien de capital. Leído junto al IAI revela la 'trampa de la madurez': un país puede invertir en ladrillos y camiones pero estancarse si no se digitaliza. Se construye con datos del INDEC (balanza de servicios + IPI/empleo).",
    frecuencia: "Mensual", tipo: "Variación i.a. ponderada",
  },
  prestamos_privados: {
    que: "Cuánto varía el crédito bancario otorgado al sector privado.",
    aporta: "Mide si el sistema financiero acompaña la actividad con financiamiento.",
    frecuencia: "Diaria", tipo: "Variación",
  },
  base_monetaria: {
    que: "Cuánto varía el dinero primario de la economía (billetes en circulación más encajes bancarios).",
    aporta: "Refleja la emisión y el ancla monetaria sobre la que descansa el plan.",
    frecuencia: "Diaria", tipo: "Variación",
  },
  tc_mayorista: {
    que: "Cuánto se mueve el dólar oficial mayorista, el ancla cambiaria del programa.",
    aporta: "Marca el ritmo de devaluación de la referencia cambiaria.",
    frecuencia: "Diaria", tipo: "Variación",
  },

  // ── Política (el tablero de poder) ──────────────────────────────
  votometro_ventaja_lla: {
    que: "La diferencia de intención de voto entre LLA y el PJ, ponderando las encuestas disponibles.",
    aporta: "Mide el capital electoral del oficialismo, base de su poder de negociación.",
    frecuencia: "Continua", tipo: "Brecha (pp)",
  },
  ratio_dnu: {
    que: "Cuántos Decretos de Necesidad y Urgencia se dictan por cada ley sancionada en el año.",
    aporta: "Un ratio alto indica un Ejecutivo que legisla por decreto ante un Congreso que no acompaña.",
    frecuencia: "Continua (año)", tipo: "Ratio",
  },
  movilizacion_cepa: {
    que: "El nivel de conflictividad social y laboral: paros, protestas y cortes.",
    aporta: "Aproxima la tensión en la calle, un límite real al margen de maniobra del Gobierno.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
  },
  iaf_transferencias: {
    que: "Cuánto varían, en términos reales, las transferencias del Estado nacional a las provincias.",
    aporta: "Mide la armonía —o el conflicto— fiscal con los gobernadores.",
    frecuencia: "Anual", tipo: "Variación real",
  },
  eficacia_legislativa: {
    que: "Qué porcentaje de los proyectos que envía el Ejecutivo el Congreso termina aprobando (últimos 12 meses).",
    aporta: "Mide la capacidad real de convertir la agenda de gobierno en ley.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },
  cohesion_bloque: {
    que: "Qué porcentaje de los diputados de LLA vota alineado con la posición oficial del bloque.",
    aporta: "Indica la disciplina de la tropa propia, clave para sostener vetos y aprobar leyes.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  gobernadores_alineamiento: {
    que: "Qué porcentaje de los gobernadores se posiciona públicamente alineado con la política nacional.",
    aporta: "Mide el apoyo territorial, decisivo en el Senado y en la gobernabilidad.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  veto_quorum: {
    que: "Qué porcentaje de las sesiones de Diputados se cae por falta de quórum.",
    aporta: "Señala la capacidad de la oposición de bloquear o forzar la agenda parlamentaria.",
    frecuencia: "Continua", tipo: "Nivel (%)",
  },
  comisiones_caidas: {
    que: "Qué porcentaje de los proyectos con dictamen de comisión nunca llega al recinto.",
    aporta: "Mide el embudo legislativo: cuánto queda trabado antes de poder votarse.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },

  // ── Vida cotidiana (el bolsillo y la calle) ─────────────────────
  brecha_salario_cbt: {
    que: "Cuántas canastas básicas totales alcanza a cubrir el salario formal promedio.",
    aporta: "Mide el poder adquisitivo real del ingreso, lo que la gente siente en el bolsillo.",
    frecuencia: "Mensual", tipo: "Ratio (canastas)",
  },
  ipc_alimentos: {
    que: "Cuánto suben en el mes los precios de alimentos y bebidas.",
    aporta: "Es la inflación más sensible socialmente: pega directo en la mesa de cada hogar.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  endeudamiento_familiar: {
    que: "Cuánto deben las familias por consumo: el saldo de tarjetas más préstamos personales.",
    aporta: "Refleja si los hogares llegan a fin de mes apoyándose en deuda.",
    frecuencia: "Diaria", tipo: "Nivel (stock)",
  },
  peso_tarifas: {
    que: "Cuánto suben en el mes los precios regulados: luz, gas, agua y transporte.",
    aporta: "Mide el impacto de la quita de subsidios sobre el gasto fijo del hogar.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  consumo_carne: {
    que: "Cuántos kilos de carne vacuna consume por año cada habitante.",
    aporta: "Proxy histórico del bienestar alimentario y del poder de compra popular.",
    frecuencia: "Mensual", tipo: "Nivel per cápita",
  },
  informalidad: {
    que: "Qué porcentaje de los asalariados trabaja sin aportes jubilatorios (empleo en negro).",
    aporta: "Mide la precariedad laboral y la exclusión de la red de protección social.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  mortalidad_pymes: {
    que: "La salud del entramado productivo y del empleo PyME, aproximada por la actividad industrial manufacturera (proxy).",
    aporta: "Cuando la industria se contrae, las PyMEs y su empleo son las primeras en sufrirlo.",
    frecuencia: "Mensual", tipo: "Variación (IPI)",
  },
  despacho_cemento: {
    que: "El nivel de actividad de la construcción, gran motor de empleo de baja calificación.",
    aporta: "Termómetro de la obra pública y privada, sensible al ciclo económico.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  pluriempleo: {
    que: "Qué porcentaje de los ocupados busca trabajar más horas porque su empleo no le alcanza.",
    aporta: "Señala empleo insuficiente: gente ocupada a la que no le alcanza.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  inseguridad: {
    que: "Cuántos hechos delictivos se registran por año.",
    aporta: "Mide una de las principales preocupaciones cotidianas de la población.",
    frecuencia: "Anual", tipo: "Conteo",
  },
  icc_utdt: {
    que: "El optimismo de la gente sobre la economía y sus finanzas personales (Índice de Confianza del Consumidor).",
    aporta: "Captura el humor económico de la gente, que anticipa consumo y voto.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  sentimiento_digital: {
    que: "La urgencia económica que percibe la sociedad, medida por cuánto se busca en internet sobre inflación y precios.",
    aporta: "Proxy en tiempo real de la preocupación económica de la gente.",
    frecuencia: "Tiempo real", tipo: "Índice (0–100)",
  },
  patentamiento_motos: {
    que: "Cuántas motos se patentan en el mes.",
    aporta: "Proxy de consumo durable de los sectores medios y bajos.",
    frecuencia: "Mensual", tipo: "Conteo",
  },

  // ── Espíritu de época (el humor social) ─────────────────────────
  clima_electoral: {
    que: "La ventaja del oficialismo sobre el principal opositor (LLA − PJ) en el promedio ponderado de encuestas.",
    aporta: "Proxy de la adhesión política al proyecto de gobierno: cuando el humor social acompaña, la ventaja se sostiene.",
    frecuencia: "Continua", tipo: "Brecha (pp)",
  },

  // ── Gestión (la capacidad de ejecutar) ──────────────────────────
  cepo_mulc: {
    que: "Cuánto se separa el dólar financiero (CCL) del dólar mayorista de referencia: la brecha cambiaria.",
    aporta: "Mide el grado de normalización cambiaria, uno de los ejes del programa económico.",
    frecuencia: "Diaria", tipo: "Brecha (%)",
  },
  privatizaciones: {
    que: "Cuánto avanza la privatización de la cartera de empresas públicas habilitada por la Ley Bases, medida por etapas verificables: 0 sin definir · 1 preparatoria · 2 pliegos · 3 licitación/adjudicación · 4 operación cerrada.",
    aporta: "Mide la ejecución real de una reforma emblema — el promedio de etapas separa el anuncio del hecho consumado (una venta cerrada vale más que diez pliegos). Se mantiene con seguimiento del Boletín Oficial: no existe fuente única automatizable.",
    frecuencia: "Quincenal (BO)", tipo: "Avance por etapas",
  },
  concesiones_infraestructura: {
    que: "Qué porcentaje de los kilómetros licitados en la Red Federal de Concesiones ya está adjudicado: el estado de cada proceso sale de CONTRAT.AR y el kilometraje por tramo de la página oficial de la RFC (16 tramos, ~9.100 km en 4 etapas).",
    aporta: "Mide con actos administrativos —no anuncios— si el traspaso de la red vial al sector privado avanza: una etapa cuenta recién cuando su licitación figura Adjudicada en el sistema de contrataciones.",
    frecuencia: "Continua (CONTRAT.AR)", tipo: "Avance de reforma",
  },
  reduccion_estado: {
    que: "Cuánto varía la dotación de empleo del sector público.",
    aporta: "Mide el ajuste del tamaño del Estado, prioridad declarada del oficialismo.",
    frecuencia: "Mensual", tipo: "Variación",
  },
  reestructuracion_organismos: {
    que: "Cuántos organismos públicos se disolvieron, fusionaron o centralizaron desde diciembre de 2023.",
    aporta: "Mide el avance concreto de la reforma del aparato estatal.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  rigi_inversiones: {
    que: "Cuánto de la inversión del Régimen de Incentivo a Grandes Inversiones (RIGI) ya está aprobada: el monto aprobado por resolución sobre el total del pipeline (aprobados + en evaluación).",
    aporta: "Mide si el régimen convierte las promesas en inversión ratificada. Se toma de la plataforma oficial del Ministerio de Economía (proyectos aprobados y en evaluación, con monto y empleos); la ficha muestra el conteo de proyectos y los montos en USD. La evolución histórica grafica la inversión aprobada acumulada (US$ M), reconstruida con la fecha de sanción de cada resolución en el Boletín Oficial.",
    frecuencia: "Continua (plataforma oficial)", tipo: "Avance de reforma",
  },
  desregulacion_normativa: {
    que: "Cuántas normas económicas se derogaron o modificaron desde diciembre de 2023.",
    aporta: "Mide el ritmo de la desregulación económica impulsada por el Gobierno.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  apertura_comercial: {
    que: "El Índice de Libertad Comercial Efectiva (ILCE, 0–100): cuán libre, barato y predecible es operar el comercio exterior. Combina la brecha cambiaria inversa (la madre de todas las restricciones) y la alícuota efectiva (recaudación de derechos de importación y exportación sobre el intercambio total del ICA).",
    aporta: "No mide cuántos dólares entran o salen (eso puede ser una buena cosecha): mide si el Estado desmantela los parches regulatorios y cambiarios que encarecen el comercio. Lectura: >90 economía integrada · 70–90 apertura condicionada · <70 economía reprimida.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
  },
  gasto_funcionamiento: {
    que: "Cuánto varía en términos reales el gasto de funcionamiento del Estado nacional respecto de 2023.",
    aporta: "La magnitud fiscal del aparato administrativo, aislada de la inflación: distingue el achicamiento del Estado de la mera licuación nominal.",
    frecuencia: "Mensual", tipo: "Variación real",
  },
  masa_salarial: {
    que: "Cuánto varía en términos reales la masa salarial del personal del Estado nacional respecto de 2023.",
    aporta: "Filtra el efecto de la inflación sobre plantas nominales: complementa a la dotación (personas) con el costo salarial real.",
    frecuencia: "Mensual", tipo: "Variación real",
  },
  asistencia_directa: {
    que: "La Tasa de Desintermediación de Planes Sociales (TDPS): qué porcentaje del devengado de Volver al Trabajo y Acompañamiento Social se paga directo al beneficiario (partida 5.1.4, ayudas sociales a personas) sobre el total transferido, según la ejecución presupuestaria real.",
    aporta: "Verifica contra el presupuesto — no contra el anuncio — que el Decreto 198/2024 eliminó la intermediación de las Unidades de Gestión: en 2023 el Potenciar Trabajo transfería ~$17.000M vía organizaciones y cooperativas; hoy el 100% va directo a personas. Ojo: desintermediar y recortar son dos cosas distintas — esto mide solo la primera.",
    frecuencia: "Mensual (devengado SIDIF)", tipo: "Avance de reforma",
  },
  fal_modernizacion_laboral: {
    que: "El avance del Sistema de Cese Laboral (Ley Bases · Dto. 847/2024 · RG CNV 1071/2025): adopción en convenios colectivos, cobertura de trabajadores y dinero efectivamente puesto en fondos de cese.",
    aporta: "Es el indicador bisagra de la reforma laboral: el propio Gobierno lo presenta como la herramienta central contra la litigiosidad. No se impone por ley — se pacta por convenio —, así que su adopción mide si la reforma prende de verdad.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
  },
  libertad_opcion_salud: {
    que: "Qué porcentaje de los usuarios de medicina prepaga tiene sus aportes derivados directo a la prepaga, inscripta como Agente del Seguro de Salud — el canal que creó el DNU 70/23 al eliminar la triangulación obligatoria por una obra social.",
    aporta: "Mide la adopción real de la libre elección con los padrones oficiales de la SSS (RNAS y RNEMP): antes de la reforma este canal no existía; a marzo de 2026 lo usan 2,66 millones de personas en 59 prepagas inscriptas.",
    frecuencia: "Mensual (~2 meses de rezago)", tipo: "Avance de reforma",
  },
  protocolo_antipiquetes: {
    que: "En qué porcentaje se redujeron los cortes de calle por manifestación en CABA respecto del promedio 2023 (el distrito donde actúan las fuerzas federales y aplica el protocolo).",
    aporta: "Mide el restablecimiento del orden público que prometió el Gobierno, donde le es atribuible. Advertencia de primer orden: el protocolo fue anulado judicialmente (29-dic-2025, en apelación) — una caída de cortes posterior ya no es atribuible al instrumento.",
    frecuencia: "Mensual", tipo: "Variación vs. base 2023",
  },
  litigiosidad_laboral: {
    que: "Cuánto varían los juicios laborales del sistema de riesgos del trabajo (SRT): acumulado de los últimos 12 meses contra los 12 previos.",
    aporta: "Contexto de la reforma laboral: el clima de litigiosidad que el Fondo de Cese promete bajar. Mide juicios por ART, no despidos — por eso acompaña la lectura pero no puntúa en el índice.",
    frecuencia: "Mensual (~3 meses de rezago)", tipo: "Variación 12m",
  },
  alertas_manifestacion: {
    que: "Cuántas alertas de manifestación únicas reportaron los feeds en tiempo real del transporte porteño (colectivos y subtes) durante el mes.",
    aporta: "Serie propia en construcción (acumula desde jul-2026, muestreada varias veces por día): cuando tenga historia suficiente será la base automatizable del indicador de orden público. Sin línea base 2023 — el registro histórico oficial de cortes fue dado de baja.",
    frecuencia: "Continua (muestreo 3×/día)", tipo: "Conteo mensual",
  },
};
