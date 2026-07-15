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
    que: "Índice de Capacidad Prestable: mide si el sistema financiero tiene fondos y margen para prestar, comparando tres niveles contra su propia historia — la tasa real que reciben los depositantes (precio), el crecimiento interanual real de los depósitos privados (volumen) y la holgura entre depósitos y préstamos (asignación).",
    aporta: "Un sistema con capacidad de fondeo por encima de lo habitual puede acompañar la inversión y la actividad; uno sin margen, no. Se publica en desvíos estándar respecto de la historia 2018→hoy: 0 es el mes típico · por encima de +0,5 expansión (verde) · por debajo de −0,5 contracción (rojo). Datos del BCRA (BADLAR, depósitos y préstamos privados) e IPC del INDEC.",
    frecuencia: "Mensual", tipo: "Índice (σ)",
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
    que: "Cuánto recauda el Estado en impuestos medido en términos reales: la variación contra el mismo mes del año anterior, descontada la inflación y promediada sobre los últimos tres meses para filtrar el calendario tributario.",
    aporta: "Aísla la recuperación genuina de los ingresos del efecto inflacionario y del ruido de los vencimientos impositivos: mide la tendencia fiscal de verdad, no el mes suelto.",
    frecuencia: "Mensual", tipo: "Variación i.a. real (prom. 3 meses)",
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
    que: "Índice de Desequilibrio Monetario: compara cuánto crece la oferta amplia de pesos del sector privado (M3 privado) con cuánto crece su demanda transaccional (M2 privado), ambos en términos reales e interanuales. El M2 transaccional incluye el circulante en poder del público, las cuentas corrientes privadas en pesos y las cajas de ahorro privadas en pesos; excluye los depósitos a la vista remunerados de personas jurídicas.",
    aporta: "Detecta si sobran pesos respecto de lo que la economía quiere retener: una brecha positiva señala un excedente monetario que puede presionar sobre los precios y la brecha cambiaria; una negativa indica una remonetización traccionada por la demanda real de dinero.",
    frecuencia: "Mensual", tipo: "Brecha i.a. real",
  },
  presion_dolarizacion: {
    que: "Una medida de 0 a 100 de la presión por salir del peso. Bajo restricciones cambiarias observa la brecha entre el dólar CCL y el mayorista; desde abril de 2025 combina las compras netas de dólares de personas humanas en relación con el M2 privado (canal bancarizado) con la brecha del dólar cripto frente al mayorista (canal no bancarizado).",
    aporta: "Distingue la presión de cartera que se expresa en precios paralelos de la que, con acceso abierto, se expresa en compras efectivas de divisas — y ya no se queda ciega a la demanda que elige un canal no bancarizado. Mayor presión reduce el puntaje de estabilidad monetaria.",
    frecuencia: "Mensual", tipo: "Presión 0–100",
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
    que: "Cuántos Decretos de Necesidad y Urgencia se dictan por cada ley sancionada, en los últimos 12 meses.",
    aporta: "Un ratio alto indica un Ejecutivo que legisla por decreto ante un Congreso que no acompaña.",
    frecuencia: "Continua (12m)", tipo: "Ratio",
  },
  conflictividad_nacional: {
    que: "Cuántos eventos de protesta y disturbios hubo en todo el país en los últimos 12 meses completos, comparados contra el total de 2023 (el año base del mandato). Cuenta marchas, concentraciones y disturbios registrados por ACLED, el relevamiento académico internacional estándar de conflicto social, en las 24 jurisdicciones.",
    aporta: "Aproxima la tensión en la calle a escala nacional, un límite real al margen de maniobra del Gobierno. Menos conflicto que en 2023 significa menos tensión; la comparación de 12 meses contra el año completo absorbe la estacionalidad del calendario de protestas.",
    frecuencia: "Semanal (ACLED)", tipo: "Variación (%)",
  },
  movilizacion_cepa: {
    que: "El nivel de conflictividad social y laboral: paros, protestas y cortes, según los informes del centro CEPA.",
    aporta: "Aproxima la tensión en la calle. Desde julio de 2026 no integra el índice del cinturón ni se publica en el tablero: su fuente publica informes recién desde fines de 2025 (sin serie histórica posible) y su cifra acumula conflictos desde el inicio de cada año, lo que impide comparar meses entre sí — la medición continúa como contraste interno del indicador nacional de conflictividad.",
    frecuencia: "Por informe", tipo: "Índice (0–100)",
  },
  iaf_transferencias: {
    que: "Cuánto varían, en términos reales, las transferencias del Estado nacional a las provincias.",
    aporta: "Mide la armonía —o el conflicto— fiscal con los gobernadores.",
    frecuencia: "Anual", tipo: "Variación real",
  },
  eficacia_legislativa: {
    que: "Qué porcentaje de los proyectos que envía el Ejecutivo el Congreso termina aprobando, contados recién a partir de que tuvieron un año de margen para tramitarse.",
    aporta: "Mide la capacidad real de convertir la agenda de gobierno en ley, sin castigar a los proyectos recién enviados que todavía no tuvieron tiempo de tratarse.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },
  cohesion_bloque: {
    que: "Qué tan pareja o dispareja vota puertas adentro el bloque propio de LLA, en las votaciones nominales divididas de los últimos 90 días de las dos cámaras: por acta, resta los votos a favor menos los votos en contra, en valor absoluto, sobre el total de votos que emitió el bloque. El indicador pondera Diputados 65% y Senado 35%; si una cámara no tiene actas divididas en la ventana, el peso se reparte sobre la otra.",
    aporta: "Mide la cohesión interna del oficialismo en el Congreso — no si acompaña una «posición oficial», algo que no puede observarse de forma independiente —, clave para sostener vetos y aprobar leyes. La composición por cámara se publica en el detalle.",
    frecuencia: "Continua (90d)", tipo: "Nivel (%)",
  },
  rotacion_gabinete: {
    que: "Cuántos funcionarios de rango ministerial pleno (el jefe de Gabinete y los ministros) dejaron su cargo en los últimos 12 meses, con la fecha del cese efectivo. No cuenta los pases de un ministro a otro cargo del mismo gabinete ni los cierres o fusiones de ministerios: una reorganización no es una salida.",
    aporta: "Un gabinete estable indica que el Presidente conserva la capacidad de sostener a su equipo; las salidas encadenadas son señal de tensión interna. Desde julio de 2026 no integra el índice del cinturón ni se publica en el tablero: la medición continúa como seguimiento interno.",
    frecuencia: "Continua (registro curado, chequeo diario)", tipo: "Conteo (12 meses)",
  },
  adhesion_reformas_provincial: {
    que: "Cuántas de las 24 jurisdicciones del país (23 provincias y la Ciudad de Buenos Aires) figuran adheridas al Régimen de Incentivo para Grandes Inversiones (RIGI), sobre el total.",
    aporta: "Mide adhesión fiscal a un régimen de promoción de inversiones puntual, no el alineamiento político general de una provincia con la Nación — eso lo mide, con otro método, el indicador de alineamiento de senadores por provincia.",
    frecuencia: "Continua", tipo: "Nivel (%)",
  },
  alineamiento_senadores_prov: {
    que: "Qué porcentaje de los votos de senadores no alineados con el oficialismo (La Libertad Avanza) coincide con la posición que tomó el bloque oficialista en esa misma votación, promediado entre provincias.",
    aporta: "Mide alianzas territoriales por el comportamiento real de voto en el Senado, no por declaraciones o el alineamiento partidario formal de cada gobernador con la Nación.",
    frecuencia: "Continua (90d)", tipo: "Nivel (%)",
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
  derrotas_legislativas: {
    que: "Cuántas veces en los últimos 12 meses el Congreso le volteó una norma al Poder Ejecutivo en el recinto. Cuenta dos tipos de derrota consumada: leyes vetadas por el Presidente que ambas cámaras insistieron con dos tercios de los votos (la ley se promulga pese al veto, como fija la Constitución) y decretos —de necesidad y urgencia o delegados— rechazados por al menos una cámara bajo el procedimiento de control de la ley 26.122. Cada norma cuenta una sola vez, en el mes en que la derrota se consuma.",
    aporta: "Es la medida más directa del balance de fuerzas entre el Ejecutivo y el Congreso: cada insistencia o rechazo en el recinto es una derrota política difícil de revertir. Cero derrotas indican control de la agenda (o ausencia de confrontación); un conteo alto marca un Congreso capaz de imponerse.",
    frecuencia: "Continua (12m)", tipo: "Conteo (12m)",
  },

  // ── Vida cotidiana (el bolsillo y la calle) ─────────────────────
  brecha_salario_cbt: {
    que: "Cuántas canastas básicas totales alcanza a cubrir el salario formal promedio.",
    aporta: "Mide el poder adquisitivo real del ingreso, lo que la gente siente en el bolsillo.",
    frecuencia: "Mensual", tipo: "Ratio (canastas)",
  },
  // ADR-0033: en el ITVC puntúa el encarecimiento RELATIVO (alimentos vs IPC
  // general) — la versión salario/alimentos duplicaba la brecha (r = 0,985)
  ipc_alimentos: {
    que: "Cuánto suben en el mes los precios de alimentos y bebidas. En el ITVC puntúa por el NIVEL acumulado del índice de alimentos relativo al IPC general, rebaseado a 100 = 4T-2023: si supera 100, la comida subió menos que el resto de los precios desde el arranque del mandato (alivio relativo); si queda debajo, encarece por encima del promedio.",
    aporta: "Es la inflación más sensible socialmente: pega directo en la mesa de cada hogar, y castiga la canasta de los hogares de menores ingresos aunque la inflación general baje. Es una pregunta de precios pura, independiente del salario — el poder de compra lo mide la brecha salario/canasta, en Ingresos.",
    frecuencia: "Mensual", tipo: "Variación (card) · nivel vs IPC general (índice)",
  },
  endeudamiento_familiar: {
    que: "Cuánto deben las familias por consumo (tarjetas + personales). En el ITVC puntúa la deuda REAL corregida por la tasa de mora de esa cartera (Informe sobre Bancos, BCRA): más crédito con mora estable es acceso; más crédito con mora disparada es sobreendeudamiento por necesidad.",
    aporta: "La corrección por mora resuelve la ambigüedad de polaridad: la deuda real creció ~66% desde el 4T-2023 pero la irregularidad de las familias se multiplicó por 5,5 — el índice del componente lo castiga con fuerza.",
    frecuencia: "Mensual (mora con ~2 meses de rezago)", tipo: "Índice deuda real × calidad de cartera",
  },
  peso_tarifas: {
    que: "Cuánto suben en el mes los precios regulados: luz, gas, agua y transporte. En el ITVC puntúa por el NIVEL acumulado de regulados relativo a los salarios, rebaseado a 100 = 4T-2023.",
    aporta: "Mide el impacto acumulado de la quita de subsidios sobre el gasto fijo del hogar en términos de ingresos — la decisión de política más atribuible a la gestión dentro de la dimensión de precios.",
    frecuencia: "Mensual", tipo: "Variación (card) · nivel vs salarios (índice)",
  },
  consumo_carne: {
    que: "Cuántos kilos de carne vacuna consume por año cada habitante.",
    aporta: "Proxy histórico del bienestar alimentario y del poder de compra popular.",
    frecuencia: "Mensual", tipo: "Nivel per cápita",
  },
  informalidad: {
    que: "Qué porcentaje de los asalariados trabaja sin aportes jubilatorios (empleo en negro), según la EPH trimestral del INDEC.",
    aporta: "Mide la precariedad laboral y la exclusión de la red de protección social. En el ITVC su base es el 4T-2023 exacto (el trimestre de arranque del mandato).",
    frecuencia: "Trimestral (EPH)", tipo: "Nivel (%)",
  },
  mortalidad_pymes: {
    que: "La salud del entramado productivo y del empleo PyME, aproximada por la actividad industrial manufacturera. En el ITVC puntúa por el NIVEL del IPI desestacionalizado rebaseado a 100 = 4T-2023 (ya no la variación de un mes, que premiaba o castigaba por estacionalidad).",
    aporta: "Cuando la industria se contrae, las PyMEs y su empleo son las primeras en sufrirlo; el nivel acumulado dice si la actividad recuperó o no el punto de partida del mandato.",
    frecuencia: "Mensual", tipo: "Variación (card) · nivel desest. (índice)",
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
    que: "Qué porcentaje de los hogares sufrió al menos un delito en los últimos 12 meses, según la encuesta mensual de victimización del LICIP (Universidad Di Tella) en 40 centros urbanos.",
    aporta: "Mide una de las principales preocupaciones cotidianas midiendo lo que la gente efectivamente sufre — incluidos los delitos que nunca se denuncian. Las denuncias registradas (SNIC, anual) quedan como contraste en el detalle: cuando ambas fuentes divergen, la divergencia es información.",
    frecuencia: "Mensual (encuesta)", tipo: "Nivel (%)",
  },
  icc_utdt: {
    que: "El optimismo de la gente sobre la economía y sus finanzas personales (Índice de Confianza del Consumidor).",
    aporta: "Captura el humor económico de la gente, que anticipa consumo y voto.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  sentimiento_digital: {
    que: "La urgencia económica que percibe la sociedad, medida por cuánto se busca en internet sobre inflación, precios, inseguridad y trabajo.",
    aporta: "Mide la preocupación económica por la conducta (qué busca la gente cuando le duele el bolsillo), complementando al ICC que la mide por encuesta. Puntúa en el índice con la canasta mensual comparada contra el arranque del mandato; el titular es el pulso en tiempo real.",
    frecuencia: "Mensual (puntaje) · tiempo real (pulso)", tipo: "Índice (0–100)",
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
  indice_intencion_migratoria: {
    que: "Cuánto se busca en internet sobre emigrar de Argentina (por ejemplo \"emigrar de argentina\", \"vivir en el exterior\").",
    aporta: "Es una señal más estructural que sentimiento digital: no mide urgencia económica del momento, sino gente que dejó de creer en un cambio dentro del país. Nunca debería leerse sola — es un proxy de atención, no de flujo migratorio real; por eso su card la acompaña con la migración efectiva hacia los destinos principales, como contraste.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
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
    que: "Qué porcentaje de los kilómetros del plan de la Red Federal de Concesiones ya está adjudicado: el estado de cada proceso sale de CONTRAT.AR y el kilometraje por tramo de la página oficial de la RFC (16 tramos, ~9.100 km en 4 etapas).",
    aporta: "Mide con actos administrativos —no anuncios— si el traspaso de la red vial al sector privado avanza: una etapa cuenta recién cuando su licitación figura Adjudicada en el sistema de contrataciones.",
    frecuencia: "Continua (CONTRAT.AR)", tipo: "Avance de reforma",
  },
  reduccion_estado: {
    que: "Cuánto varía la dotación de personal de la Administración Pública Nacional respecto de diciembre de 2023 (inicio del mandato), según la serie mensual oficial del INDEC.",
    aporta: "La métrica insignia de la reforma del Estado: personas, no pesos. A diferencia de las series de sector público total, excluye provincias y municipios — mide solo lo que depende del Gobierno nacional.",
    frecuencia: "Mensual", tipo: "Variación vs. dic-2023",
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
    que: "La alícuota efectiva del comercio exterior: cuántos impuestos (derechos de importación + exportación, ARCA) paga en promedio cada dólar de intercambio (expo+impo del ICA). 0% = comercio libre de fricción arancelaria; 15% o más = cierre de hecho.",
    aporta: "No mide cuántos dólares entran o salen (eso puede ser una buena cosecha): mide si el Estado desmantela la fricción impositiva que encarece el comercio. La brecha cambiaria puntúa aparte (en su propio indicador) — hasta jul-2026 este índice la incluía y la contaba dos veces (corregido).",
    frecuencia: "Mensual", tipo: "Nivel (%)",
  },
  credito_privado: {
    que: "Cuánto crece el crédito al sector privado en términos reales (variación interanual de los préstamos, deflactada por el IPC).",
    aporta: "Es el crédito REALIZADO — complementa al IdC, que mide la capacidad prestable: si la capacidad existe pero el crédito real no crece, el financiamiento no está llegando a la economía. Es la única señal no redundante de los viejos indicadores monetarios de contexto.",
    frecuencia: "Diaria (BCRA)", tipo: "Variación real",
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
    aporta: "Es el indicador bisagra de la reforma laboral: el propio Gobierno lo presenta como la herramienta central contra la litigiosidad. No se impone por ley — se pacta por convenio —, así que su adopción mide si la reforma prende de verdad. La cobertura se mide con las menciones del instrumento en el Boletín Oficial desde la Ley Bases (calibración: 420 menciones = adopción plena); la adopción financiera, con los fondos registrados en la CNV.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
  },
  libertad_opcion_salud: {
    que: "Qué porcentaje de los usuarios de medicina prepaga tiene sus aportes derivados directo a la prepaga, inscripta como Agente del Seguro de Salud — el canal que creó el DNU 70/23 al eliminar la triangulación obligatoria por una obra social.",
    aporta: "Mide la adopción real de la libre elección con los padrones oficiales de la SSS (RNAS y RNEMP): antes de la reforma este canal no existía; a marzo de 2026 lo usan 2,66 millones de personas en 59 prepagas inscriptas.",
    frecuencia: "Mensual (~2 meses de rezago)", tipo: "Avance de reforma",
  },
  protocolo_antipiquetes: {
    que: "En qué porcentaje se redujeron los cortes de calle por manifestación en CABA respecto de 2023 (el distrito donde actúan las fuerzas federales y aplica el protocolo).",
    aporta: "Mide el restablecimiento del orden público que prometió el Gobierno, donde le es atribuible. Fuente: los monitoreos públicos de Diagnóstico Político (relevamiento diario sobre más de 100 medios desde 2009), cuya definición de piquete coincide con la de la Res. 943/23. La validez del instrumento fue confirmada judicialmente: la Cámara revocó en marzo de 2026 la nulidad de primera instancia.",
    frecuencia: "Anual (informes públicos de DP)", tipo: "Variación vs. base 2023",
  },
  litigiosidad_laboral: {
    que: "Cuánto varían los juicios laborales del sistema de riesgos del trabajo (SRT): acumulado de los últimos 12 meses contra los 12 previos.",
    aporta: "Es el RESULTADO que la reforma laboral persigue: enfriar la industria del juicio. Complementa al Fondo de Cese (que mide la adopción del instrumento): si el instrumento no avanza pero la litigiosidad se enfría igual, la dimensión lo refleja. Proxy por juicios ART — la única serie nacional mensual pública.",
    frecuencia: "Mensual (~3 meses de rezago)", tipo: "Variación 12m",
  },
  alertas_manifestacion: {
    que: "Cuántas alertas de manifestación únicas reportaron los feeds en tiempo real del transporte porteño (colectivos y subtes) durante el mes.",
    aporta: "Serie propia en construcción (acumula desde jul-2026, muestreada varias veces por día): cuando tenga historia suficiente será la base automatizable del indicador de orden público. Sin línea base 2023 — el registro histórico oficial de cortes fue dado de baja.",
    frecuencia: "Continua (muestreo 3×/día)", tipo: "Conteo mensual",
  },
  protestas_caba: {
    que: "Cuántos eventos de protesta (marchas, concentraciones, disturbios) registró ACLED en la Ciudad de Buenos Aires en los últimos 12 meses, con serie semanal desde 2018.",
    aporta: "El contraste clave del orden público: los cortes de calle se desplomaron (74% vs 2023, según Diagnóstico Político) pero los eventos de protesta NO — subieron 25%: la protesta se reconvirtió a marchas sin corte, que es exactamente lo que el protocolo buscaba. ACLED cuenta eventos con cobertura de prensa; no capta piquetes barriales chicos. Datos de ACLED (acleddata.com).",
    frecuencia: "Semanal (ACLED)", tipo: "Conteo (12 meses)",
  },
};

// Qué mide cada DIMENSIÓN de los índices paramétricos (modal de dimensión).
// Claves únicas entre ITCM/ITCG/ITVC.
export const DIM_DESCRIPCIONES: Record<string, string> = {
  // ITCM
  estabilidad_monetaria: "La estabilidad de la moneda desde cuatro señales complementarias: la inflación actual (IPC), la esperada por el mercado (REM), el desequilibrio entre oferta y demanda transaccional de pesos (IDM) y la presión por salir del peso, observada según el régimen cambiario vigente.",
  viabilidad_fiscal_comercial: "Si las cuentas cierran: la recaudación real (el sostén del ancla fiscal) y el saldo comercial (los dólares genuinos del intercambio).",
  financiamiento: "Si hay combustible para la economía: reservas netas (el respaldo externo), capacidad prestable del sistema financiero (IdC) y crédito real efectivamente otorgado.",
  actividad: "Si la economía crece o se contrae: el EMAE interanual como pulso general de la actividad.",
  competitividad_externa: "Si el tipo de cambio real alcanza para competir: el ITCRM oficial del BCRA contra su propia historia.",
  inversion: "Si alguien está apostando al futuro: inversión física (construcción, bienes de capital) y capitalización digital e intangible.",
  // ITCG
  reformas_economicas: "El corazón de la promesa económica: cepo desarmado (brecha cambiaria), comercio exterior abierto (alícuota efectiva) y desregulación normativa.",
  reforma_estado: "El achicamiento del Estado en cuatro medidas que se controlan entre sí: dotación de personal, gasto de funcionamiento real, masa salarial real y reestructuración de organismos.",
  reforma_laboral: "Instrumento y resultado: la adopción del Fondo de Cese (el reemplazo del canal indemnizatorio) y la litigiosidad laboral (la industria del juicio que la reforma promete enfriar).",
  privatizaciones_inversion: "Los activos del Estado y la inversión privada grande: cartera de privatizaciones, pipeline del RIGI y concesiones viales.",
  social_orden: "La reforma social y el orden público: asistencia sin intermediarios (TDPS), protocolo antipiquetes y libertad de opción en salud.",
  // ITVC
  ingresos: "Si el sueldo alcanza: la brecha entre el salario y la canasta de pobreza, y cuánta gente trabaja en la informalidad.",
  precios: "Lo que más duele en la compra de todos los días: alimentos y tarifas, medidos contra los salarios (no contra la inflación general).",
  vulnerabilidad: "Cuánto están endeudadas las familias: crédito real por hogar, corregido por la mora — deuda que crece con mora estable es acceso; con mora subiendo es fragilidad.",
  empleo: "Las perspectivas de trabajo: mortalidad de pymes (empleadores), construcción (cemento, el sector más intensivo en mano de obra) y pluriempleo.",
  confianza: "El ánimo y la seguridad de la vida diaria: confianza del consumidor (UTDT), inseguridad, consumo de carne y patentamiento de motos como termómetros de bolsillo.",
  // ITCP
  imagen_voto: "La ventaja electoral medida en las encuestas: la brecha de intención de voto entre La Libertad Avanza y el peronismo.",
  poder_legislativo: "La capacidad de gobernar por ley en el Congreso: cuánto legisla por decreto en vez de ley (ratio DNU), qué porción de la agenda del Ejecutivo se aprueba, cuántas sesiones de Diputados fracasan por falta de quórum, cuántos proyectos quedan varados en comisión y cuántas derrotas consumadas sufre el Ejecutivo en el recinto (vetos insistidos y decretos rechazados).",
  alianzas_territoriales: "El sostén federal del gobierno: las transferencias a las provincias (armonía fiscal), el alineamiento de los senadores no oficialistas con la posición del bloque de gobierno, y la adhesión provincial al RIGI.",
  cohesion_interna: "Qué tan unido está el oficialismo puertas adentro: la disciplina de voto del bloque propio de La Libertad Avanza, medida en un único indicador bicameral (Diputados 65%, Senado 35%).",
  conflicto_social: "La conflictividad social que el gobierno tiene que administrar: los eventos de protesta y disturbios de todo el país registrados por ACLED, acumulados en 12 meses y comparados contra 2023, la línea de base del mandato.",
};
