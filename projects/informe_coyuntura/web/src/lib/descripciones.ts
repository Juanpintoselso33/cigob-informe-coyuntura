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
  empleo_registrado: {
    que: "Cuántos asalariados del sector privado están registrados ante la seguridad social. Es el dato que las empresas declaran mes a mes, no una estimación de encuesta.",
    aporta: "Es la única medida directa de empleo del cinturón. Los otros componentes de la dimensión describen actividad —producción industrial, construcción— o anticipan giros, pero ninguno cuenta puestos de trabajo. Desde diciembre de 2023 el sector privado registrado perdió alrededor de doscientos cincuenta mil puestos, y la caída interanual no se interrumpió en ningún mes desde agosto de 2025.",
    frecuencia: "Mensual", tipo: "Nivel (miles de puestos)",
  },
  cobertura_judicial: {
    que: "Qué porcentaje de los cargos de juez de la justicia federal y nacional tiene juez designado. Un cargo cubierto por un subrogante cuenta como vacante, porque la subrogancia es transitoria y no reemplaza a un juez nombrado para ese tribunal.",
    aporta: "Mide una capacidad que el Gobierno no ejerce solo: designar jueces requiere acuerdo del Senado, de modo que la cobertura del Poder Judicial es un termómetro de la negociación política, no de la gestión administrativa. La serie muestra un desgaste sostenido durante más de dos años —las renuncias siguieron y las designaciones se detuvieron— seguido de una recuperación abrupta cuando el Senado aprobó un conjunto de pliegos en junio de 2026.",
    frecuencia: "Mensual", tipo: "% de cobertura",
  },
  produccion_legislativa: {
    que: "Cuántas leyes sancionó el Congreso en los últimos doce meses, sin distinguir de quién nació cada proyecto.",
    aporta: "Mide la actividad legislativa por su volumen, que es el número que efectivamente se mueve. La participación del Ejecutivo en esa producción es notablemente estable —entre cinco y diez leyes por ventana en todo el período—, de modo que cuando su porcentaje sube, lo que cambió no fue el Ejecutivo sino el Congreso, que sancionó menos. Medir el total evita leer una parálisis legislativa como un avance del Gobierno.",
    frecuencia: "Mensual", tipo: "Conteo en ventana móvil",
  },
  judicializacion: {
    que: "Qué porcentaje de los fallos publicados en jurisdicción federal y nacional involucra una medida cautelar.",
    aporta: "Mide cuánto de la agenda se dirime en tribunales por la vía de la suspensión, que es el instrumento con el que una decisión del Ejecutivo se frena antes de discutirse en el fondo. Se publica como proporción y no como conteo porque el número de fallos publicados depende del volumen editorial de la base de jurisprudencia: el conteo crudo se quintuplica entre 2016 y 2021 sin que las cautelares se hayan quintuplicado.",
    frecuencia: "Anual", tipo: "% de fallos",
  },
  velocidad_resolucion: {
    que: "Cuántos expedientes resuelve la Corte Suprema en un año, en proporción a los que le ingresan.",
    aporta: "Distingue una Corte que se pone al día de una que acumula. Por encima de cien resuelve más de lo que recibe y descarga atraso; por debajo, el atraso crece. Importa para este cinturón porque una causa que tarda años en resolverse deja en pie, mientras tanto, lo que se discute.",
    frecuencia: "Anual", tipo: "% resuelto sobre ingresado",
  },
  paralisis_denuncias: {
    que: "Cuántas veces sesionaron en los últimos doce meses las dos comisiones del Consejo de la Magistratura que tramitan las denuncias contra jueces: Acusación y Disciplina.",
    aporta: "Mide si el mecanismo de control disciplinario de los jueces está funcionando o está detenido. Se cuentan las sesiones de ambas comisiones y no las de una sola porque el conjunto da una serie estable y comparable mes a mes, mientras que cada comisión por separado sesiona pocas veces al año.",
    frecuencia: "Mensual", tipo: "Conteo en ventana móvil",
  },
  emae_difusion: {
    que: "De los quince sectores en que el INDEC divide la actividad económica, cuántos crecen respecto de un año atrás.",
    aporta: "Distingue un crecimiento generalizado de uno concentrado en pocos sectores. El EMAE informa cuánto crece la economía; este indicador, en cuántas partes de ella crece: dos meses con la misma variación agregada pueden significar cosas muy distintas según cuántos sectores la sostengan.",
    frecuencia: "Mensual", tipo: "Índice de difusión",
  },
  ipi_manufacturero: {
    que: "Cuánto produce la industria manufacturera respecto de un año atrás, promediado en tres meses.",
    aporta: "Segunda lectura de la actividad, junto al EMAE: mide sólo la industria y se publica algo antes, de modo que la dimensión no depende de un único dato.",
    frecuencia: "Mensual", tipo: "Variación i.a. (promedio 3 meses)",
  },
  saldo_comercial_12m: {
    que: "El balance entre lo que el país exporta y lo que importa, acumulado en los últimos 12 meses.",
    aporta: "Muestra si el intercambio de bienes aporta o resta dólares. No alcanza para saber si el sector externo en conjunto los genera: faltan los servicios, los intereses y las utilidades giradas, que se ven en la cuenta corriente del gráfico.",
    frecuencia: "Mensual", tipo: "Nivel (acum. 12m)",
  },
  recaudacion: {
    que: "Cuánta economía formal hay para gravar, medida en pesos constantes y comparada contra el cuarto trimestre de 2023, que vale 100. Suma los impuestos internos de la Nación —IVA doméstico, Ganancias, créditos y débitos— y el Impuesto sobre los Ingresos Brutos de las empresas que operan en varias provincias, con sus regímenes de retención. Se corrige la estacionalidad del calendario tributario, que concentra la recaudación en mayo y junio.",
    aporta: "Mide el tamaño de la base imponible y el nivel de actividad, no la caja del Estado. Por eso excluye la aduana: cuando el Gobierno baja retenciones, la recaudación total cae porque así se decidió, y contar esa caída como deterioro sería puntuar como fracaso el cumplimiento de una promesa. Un nivel por debajo de 100 dice que hay menos economía formal para gravar que en la transición, con independencia de cómo venga la comparación contra el año anterior.",
    frecuencia: "Mensual", tipo: "Índice de base imponible real (100 = 4T-2023)",
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
    aporta: "Detecta si sobran pesos respecto de lo que la economía quiere retener: una brecha positiva señala excedente monetario que puede presionar precios y brecha cambiaria; una negativa, remonetización traccionada por demanda real de dinero.",
    frecuencia: "Mensual", tipo: "Brecha i.a. real",
  },
  desequilibrio_monetario: {
    que: "Una medida de 0 a 100 de la tensión monetaria vista desde la confianza en el peso. Cruza dos cosas que por separado engañan: cuánta de la liquidez privada total —pesos más dólares depositados— sigue estando en pesos de uso transaccional (lo que se ve, porque queda dentro del sistema financiero), y cuántos dólares netos compra el sector privado no financiero en el mercado de cambios (lo que se va, aunque nunca pase por un depósito).",
    aporta: "Los dos componentes se leen juntos porque uno solo miente: si la salida hacia el colchón es fuerte, la foto de adentro puede verse estable o hasta mejorando —esos dólares nunca entraron al denominador— mientras el fondo es lo peor posible. El resultado sale de cruzarlos en una matriz, no de promediarlos. Mayor tensión reduce el puntaje de estabilidad monetaria.",
    frecuencia: "Mensual", tipo: "Tensión 0–100",
  },
  iai: {
    que: "Índice Anticipador de Inversión: mide la inversión física/tradicional combinando la actividad de la construcción (ISAC) y la importación de bienes de capital, en variación interanual.",
    aporta: "Anticipa si el país amplía su capacidad productiva (máquinas, obra, equipo) o se descapitaliza. Mayor = la inversión se expande por encima de la reposición; negativo = se consume más stock de capital del que se genera. Se construye con datos del INDEC (ISAC + ICA bienes de capital).",
    frecuencia: "Mensual", tipo: "Variación i.a. ponderada",
  },
  icip: {
    que: "Índice de Capitalización Inteligente y Productividad: mide la inversión digital/intangible —pagos al exterior por servicios de informática (software, nube, IA) y productividad laboral (IPI/empleo)— en variación interanual.",
    aporta: "Sigue la incorporación de tecnología que no pasa por aduana como bien de capital. Leído junto al IAI apunta a la 'trampa de la madurez': un país puede invertir en ladrillos y camiones pero estancarse si no se digitaliza. Con una advertencia declarada en la ficha: un aumento de los pagos al exterior por software admite leerse como digitalización o como dependencia tecnológica, y el indicador puntúa la primera. Se construye con datos del INDEC (balanza de servicios + IPI/empleo).",
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
  desafios_legislativos: {
    que: "Cuántas normas propias del Gobierno fueron puestas en discusión en el recinto durante los últimos doce meses: vetos presidenciales sobre los que el Congreso votó una insistencia, y decretos sometidos a votación bajo la ley 26.122.",
    aporta: "Mide con qué frecuencia el Congreso decide dar la pelea, sin importar cómo termine. Desafiar una norma del Ejecutivo es un acto excepcional —exige mayorías especiales o un procedimiento específico—, así que un puñado al año ya indica confrontación abierta. Junto con la proporción de normas que el Gobierno logra sostener, responde las dos preguntas del pulso legislativo: cuánto lo confrontan y cuánto aguanta.",
    frecuencia: "Continua (12m)", tipo: "Conteo",
  },
  brecha_obra_publica: {
    que: "La diferencia entre lo que esperan las empresas constructoras que trabajan para el Estado y lo que esperan las que trabajan para clientes privados. El INDEC les pregunta todos los meses si creen que su actividad va a subir o bajar en el trimestre siguiente, y publica las dos respuestas por separado. El indicador resta una de la otra y promedia los últimos doce meses.",
    aporta: "Conviene una advertencia antes del dato: este indicador se comporta distinto según el gobierno, porque para el actual el recorte de la obra pública es el programa y no un síntoma de dificultades, de modo que la tensión con el sector puede subir mientras el Gobierno gobierna con comodidad. Dicho eso, lo que mide es sólido. Las dos submuestras son el mismo sector: mismos costos, mismo crédito, misma economía. Lo único que las distingue es quién les paga. Por eso la diferencia entre ambas aísla lo que aporta el Estado y descarta el ciclo económico general. Cuando las que dependen de la obra pública esperan mucho peor que sus pares privadas, la fuente del problema es la política pública y no el mercado.",
    frecuencia: "Mensual (12m)", tipo: "Brecha (pp)",
  },
  apoyo_empresario: {
    que: "Qué dicen en público, por escrito y con firma institucional, las dos cámaras empresarias de referencia —la Asociación Empresaria Argentina y la Unión Industrial Argentina— sobre las medidas del Gobierno nacional. Cada comunicado se lee y se clasifica: si respalda o critica, y a quién le habla. Se cuentan sólo los que se pronuncian sobre una medida del Ejecutivo nacional, y el indicador es el saldo entre apoyos y críticas de los últimos doce meses.",
    aporta: "Es la única medida directa de la relación entre el Gobierno y el empresariado organizado: las demás miran el clima de negocios o los datos de un sector, y de ahí infieren el vínculo. Acá el vínculo está dicho. Conviene saber qué no dice: no mide el humor del empresariado en general ni la opinión de sus asociados, sino lo que una asociación decidió declarar públicamente — una cámara puede callar por conveniencia y ese silencio no aparece. La clasificación la hace una persona siguiendo reglas escritas de antemano, y dos personas distintas la hicieron por separado para verificar que las reglas no dejan lugar a la interpretación.",
    frecuencia: "Continua (12m)", tipo: "Saldo (−1 a +1)",
  },
  ratio_dnu: {
    que: "Cuántos Decretos de Necesidad y Urgencia se dictan por cada ley sancionada, en los últimos 12 meses.",
    aporta: "Mide con cuánta frecuencia el Gobierno recurre al decreto en lugar de la ley, no si esos decretos le funcionan. Son dos preguntas distintas y conviene no confundirlas. En el relevamiento cerrado el 19 de julio de 2026, el 95% de los decretos de necesidad y urgencia de esta gestión nunca había llegado a votarse en el recinto; de los ocho que sí habían llegado, seis habían caído. La dependencia del decreto es una vulnerabilidad latente: no se cobra mientras el Congreso no active el procedimiento, y se cobra de golpe cuando lo activa.",
    frecuencia: "Continua (12m)", tipo: "Ratio",
  },
  conflictividad_nacional: {
    que: "Cuántos eventos de protesta y disturbios hubo en todo el país en los últimos 12 meses completos, comparados contra el total de 2023 (el año base del mandato). Cuenta marchas, concentraciones y disturbios registrados por ACLED, el relevamiento académico internacional estándar de conflicto social, en las 24 jurisdicciones.",
    aporta: "Aproxima la tensión en la calle a escala nacional, un límite real al margen de maniobra del Gobierno. Menos conflicto que en 2023 significa menos tensión; la comparación de 12 meses contra el año completo absorbe la estacionalidad del calendario de protestas.",
    frecuencia: "Semanal (ACLED)", tipo: "Variación (%)",
  },
  jornadas_individuales_no_trabajadas_12m: {
    que: "Cuántas jornadas individuales de trabajo se perdieron por paros en todo el país durante los últimos doce meses. La Secretaría de Trabajo las estima multiplicando la cantidad de huelguistas por la duración de cada paro.",
    aporta: "Agrega intensidad a la frecuencia de eventos que mide ACLED: distingue un conflicto breve y pequeño de uno largo o masivo. Es una estadística laboral oficial y sus valores mensuales pueden sumarse sin duplicar conflictos ni personas.",
    frecuencia: "Mensual (12m)", tipo: "Conteo de jornadas",
  },
  movilizacion_cepa: {
    que: "El nivel de conflictividad social y laboral: paros, protestas y cortes, según los informes del centro CEPA.",
    aporta: "Aproxima la tensión en la calle. Desde julio de 2026 no integra el índice del cinturón ni se publica en el tablero: su fuente publica informes recién desde fines de 2025 (sin serie histórica posible) y su cifra acumula conflictos desde el inicio de cada año, lo que impide comparar meses entre sí — la medición continúa como contraste interno del indicador nacional de conflictividad.",
    frecuencia: "Por informe", tipo: "Índice (0–100)",
  },
  iaf_transferencias: {
    que: "Cuánto varían, en términos reales, las transferencias del Estado nacional a las provincias.",
    aporta: "Mide el gesto fiscal de la Nación hacia las provincias: cuánto gira por encima o por debajo de lo que giraba antes, en términos reales. Es un insumo de la relación federal, no la respuesta de los gobernadores: informa lo que hace el Gobierno nacional, no cómo reaccionan las provincias.",
    frecuencia: "Anual", tipo: "Variación real",
  },
  eficacia_legislativa: {
    que: "Qué porcentaje de los proyectos que envía el Ejecutivo el Congreso termina aprobando, contados recién a partir de que tuvieron un año de margen para tramitarse.",
    aporta: "Mide la capacidad real de convertir la agenda de gobierno en ley, sin castigar a los proyectos recién enviados que todavía no tuvieron tiempo de tratarse.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },
  cohesion_bloque: {
    que: "Qué tan parejo vota puertas adentro el bloque propio de LLA en las votaciones divididas de los últimos 90 días de ambas cámaras. Pondera Diputados 65% y Senado 35%; si una cámara no tiene actas divididas en la ventana, el peso pasa a la otra.",
    aporta: "Mide la cohesión interna del oficialismo en el Congreso, clave para sostener vetos y aprobar leyes. La composición por cámara se publica en el detalle.",
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
    aporta: "Es la mejor señal automatizable disponible del respaldo territorial, y conviene leerla por lo que es: mide el voto de los senadores, no la postura del gobernador de cada provincia. Un senador no depende del gobernador de turno y puede responder a la estrategia nacional de su propio partido. Reemplaza a un indicador de alineamiento de gobernadores que quedó congelado por falta de una fuente pública que midiera directamente la posición de los ejecutivos provinciales.",
    frecuencia: "Continua (90d)", tipo: "Nivel (%)",
  },
  veto_quorum: {
    que: "Qué porcentaje de las sesiones convocadas en Diputados para tratar temas queda en minoría, es decir, no reúne el quórum necesario para sesionar. Se miden los últimos doce meses.",
    aporta: "El quórum es el primer filtro de cualquier agenda legislativa: sin él no se debate ni se vota nada. Una tasa alta indica que el oficialismo no logra reunir a la cámara, sea porque la oposición se ausenta deliberadamente o porque sus propios aliados no acompañan.",
    frecuencia: "Mensual (12m)", tipo: "Nivel (%)",
  },
  comisiones_caidas: {
    que: "Qué porcentaje de los proyectos con dictamen de comisión nunca llega al recinto.",
    aporta: "Mide el embudo legislativo: cuánto queda trabado antes de poder votarse.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },
  derrotas_legislativas: {
    que: "Cuántas veces en los últimos 12 meses el Congreso le volteó una norma al Ejecutivo en el recinto: leyes vetadas que ambas cámaras insistieron con dos tercios, y decretos rechazados por al menos una cámara bajo la ley 26.122. Cada norma cuenta una vez.",
    aporta: "Es la medida más directa del balance de fuerzas entre el Ejecutivo y el Congreso. Cero derrotas indican control de la agenda (o falta de confrontación); un conteo alto, un Congreso capaz de imponerse.",
    frecuencia: "Continua (12m)", tipo: "Conteo (12m)",
  },
  bloqueo_sostenido: {
    que: "De las normas del Ejecutivo que el Congreso desafió en el recinto en los últimos 12 meses (vetos cuya insistencia se votó y decretos sometidos a la ley 26.122), qué porcentaje sigue en pie.",
    aporta: "Es la cara ganada del pulso legislativo que el conteo de derrotas no registra: un gobierno sin mayoría gobierna sosteniendo sus vetos con un tercio de una cámara. Una tasa alta indica bloqueo firme; una baja, un Congreso capaz de voltear sus normas. Al mirar 12 meses atrás, una crisis reciente pesa durante un año.",
    frecuencia: "Continua (12m)", tipo: "Nivel (%)",
  },

  // ── Impacto social (el bolsillo y la calle) ─────────────────────
  brecha_salario_cbt: {
    que: "Cuántas canastas básicas totales alcanza a cubrir el salario formal promedio.",
    aporta: "Mide el poder adquisitivo real del ingreso, lo que la gente siente en el bolsillo.",
    frecuencia: "Mensual", tipo: "Ratio (canastas)",
  },
  // ADR-0033: en el ITCIS puntúa el encarecimiento RELATIVO (alimentos vs IPC
  // general) — la versión salario/alimentos duplicaba la brecha (r = 0,985)
  ipc_alimentos: {
    que: "Cuánto suben en el mes los precios de alimentos y bebidas. En el ITCIS puntúa por el NIVEL acumulado del índice de alimentos relativo al IPC general, rebaseado a 100 = 4T-2023: si supera 100, la comida subió menos que el resto de los precios desde el arranque del mandato (alivio relativo); si queda debajo, encarece por encima del promedio.",
    aporta: "Es la inflación más sensible socialmente: pega directo en la mesa de cada hogar, y castiga la canasta de los hogares de menores ingresos aunque la inflación general baje. Es una pregunta de precios pura, independiente del salario — el poder de compra lo mide la brecha salario/canasta, en Ingresos.",
    frecuencia: "Mensual", tipo: "Variación (card) · nivel vs IPC general (índice)",
  },
  endeudamiento_familiar: {
    que: "Cuánto deben las familias por consumo (tarjetas + personales), en nivel de deuda REAL (descontada la inflación). Ya NO puntúa en el ITCIS: salió del índice en ADR-0154 porque el stock de deuda por sí solo no distingue acceso al crédito de fragilidad. Se sigue relevando y su serie se publica.",
    aporta: "Mide el acceso al crédito de los hogares como stock puro, y esa es justamente su limitación: sin saber si esa deuda se puede pagar, más crédito no dice si es acceso o necesidad. Lo que quedó midiendo la dimensión de vulnerabilidad es la mora de esa cartera, que sí lo distingue.",
    frecuencia: "Mensual (~2 meses de rezago)", tipo: "Índice de deuda real (B100)",
  },
  mora_familias: {
    que: "Qué porcentaje del crédito de consumo de las familias (préstamos personales y tarjetas) está en situación irregular — con atrasos de pago —, ponderado por el saldo de cada línea.",
    aporta: "Es la señal directa de estrés financiero de los hogares: la deuda puede crecer por acceso sano o por necesidad, pero la mora que se dispara solo tiene una lectura. Puntúa invertida: más mora, peor.",
    frecuencia: "Mensual (~2 meses de rezago)", tipo: "Nivel (%)",
  },
  carga_servicio_deuda_hogares: {
    que: "Qué porcentaje de la masa salarial registrada destinan las familias al pago mensual de capital e intereses de sus deudas. El BCRA calcula promedios de tres meses para el servicio de deuda y para la masa salarial.",
    aporta: "Mide capacidad comprometida antes de que aparezca el incumplimiento. Complementa a la mora: una observa la presión de pagos y la otra los atrasos ya materializados.",
    frecuencia: "Mensual (publicación semestral)", tipo: "Nivel (%)",
  },
  peso_tarifas: {
    que: "Cuánto suben en el mes los precios regulados: luz, gas, agua y transporte. En el ITCIS puntúa por el NIVEL acumulado de regulados relativo a los salarios, rebaseado a 100 = 4T-2023.",
    aporta: "Mide el impacto acumulado de la quita de subsidios sobre el gasto fijo del hogar en términos de ingresos — la decisión de política más atribuible a la gestión dentro de la dimensión de precios.",
    frecuencia: "Mensual", tipo: "Variación (card) · nivel vs salarios (índice)",
  },
  pobreza_nowcast: {
    que: "El porcentaje de personas que viven en hogares urbanos pobres, estimado para el semestre móvil que termina en el mes del dato. No es la cifra oficial del INDEC, que se publica dos veces al año: es una proyección que se actualiza todos los meses.",
    aporta: "Es la única medición de pobreza con frecuencia mensual que existe en el país, y la variable de mayor carga simbólica del cinturón. Integra el ITCIS con el 25% de la dimensión de ingresos y consumo (9,31% del índice), invertida: más pobreza, peor puntaje.",
    frecuencia: "Mensual (semestre móvil)", tipo: "Estimación de terceros",
  },
  indice_lider: {
    que: "Un índice que combina señales tempranas de la economía —financieras, de expectativas y de actividad— para anticipar los cambios de rumbo antes de que aparezcan en los datos corrientes. Ya NO puntúa en el ITCIS: salió del índice en ADR-0154 y pasó a ser el ancla externa contra la que se valida el ITCM.",
    aporta: "Mira hacia adelante, que es lo que ningún componente del cinturón hace: los demás describen lo que ya ocurrió. Por eso su lugar pasó a ser el de contraste externo — un índice líder que se da vuelta anticipa el punto de giro que la marcha de la actividad va a registrar meses después.",
    frecuencia: "Mensual", tipo: "Nivel (índice base 100)",
  },
  alquiler_real: {
    que: "Cuánto se encareció el alquiler de la vivienda por encima del resto de los precios. En el ITCIS puntúa por el NIVEL del alquiler relativo al índice general del Gran Buenos Aires, rebaseado a 100 = 4T-2023.",
    aporta: "La desregulación del mercado de alquileres fue uno de los cambios de política más visibles del período, y el costo de la vivienda golpea sobre todo a los hogares inquilinos urbanos — un gasto fijo que ningún otro componente del cinturón captura.",
    frecuencia: "Mensual", tipo: "Variación (card) · nivel relativo al IPC (índice)",
  },
  consumo_carne: {
    que: "Cuántos kilos de carne vacuna consume por año cada habitante. Ya NO puntúa por su cuenta: desde ADR-0217 el índice mide el acceso TOTAL a proteína cárnica, y la vacuna quedó como el desglose que explica si una caída es sustitución o pérdida real. Se sigue relevando y su serie se publica.",
    aporta: "Es la carne con más peso simbólico y la que más se mueve, así que su caída sola se lee como empobrecimiento aunque el total se sostenga. Separarla del total es lo que permite decir cuál de las dos cosas está pasando.",
    frecuencia: "Mensual", tipo: "Nivel per cápita (desglose)",
  },
  consumo_carnes_total: {
    que: "Los kilos de carne por habitante y por año sumando vacuna, aviar y porcina, en promedio móvil de doce meses. Es el acceso total a proteína cárnica, sin importar de qué animal viene.",
    aporta: "Distingue dos cosas que se parecen y no son lo mismo: si el consumo de vacuna cae y el total se sostiene, hay sustitución hacia pollo o cerdo; si caen los dos juntos, hay una pérdida real de acceso a proteína animal. Por eso puntúa el total y no la vacuna, que sola no permite separarlas — el desglose por carne se publica acá abajo, junto al color. El titular muestra el nivel oficial en kilos; el gráfico y el puntaje van en índice base 100 = 4T-2023, reconstruido desde la faena, que es lo único con historia para comparar contra el arranque del mandato.",
    frecuencia: "Mensual (unos 2 meses de rezago)", tipo: "Nivel (kg/hab) · índice base-100 en el gráfico",
  },
  informalidad: {
    que: "Qué porcentaje de los asalariados trabaja sin aportes jubilatorios (empleo en negro), según la EPH trimestral del INDEC.",
    aporta: "Mide la precariedad laboral y la exclusión de la red de protección social. En el ITCIS su base es el 4T-2023 exacto (el trimestre de arranque del mandato).",
    frecuencia: "Trimestral (EPH)", tipo: "Nivel (%)",
  },
  trabajo_independiente: {
    que: "Qué proporción del empleo registrado son trabajadores independientes —autónomos y monotributistas— frente a los asalariados. En el ITCIS puntúa INVERTIDA: más peso independiente es peor.",
    aporta: "Es la contracara del cierre de empresas. Cuando caen los empleadores, dice si esas unidades productivas desaparecieron o se reconfiguraron en gente que factura por su cuenta. Un empleo que se corre del salario al trabajo independiente pierde aportes patronales, indemnización y estabilidad, aunque siga siendo registrado.",
    frecuencia: "Mensual (unos 3 meses de rezago)", tipo: "Participación (%)",
  },
  mortalidad_pymes: {
    que: "Cuántas empresas de hasta 50 trabajadores siguen teniendo al menos una persona declarada con cobertura de ART. Cuando una PyME cierra, quiebra o despide a toda su nómina, el contrato con la aseguradora se rescinde casi en el acto, así que la baja aparece en el mes. En el ITCIS puntúa por el NIVEL rebaseado a 100 = 4T-2023: menos empleadores es peor.",
    aporta: "Es el cierre neto de empresas medido de forma directa, no aproximado por la producción industrial: el saldo entre las que abren y las que cierran, que es el dato que dice si el entramado PyME se está achicando.",
    frecuencia: "Mensual (unos 3 meses de rezago)", tipo: "Cantidad de empleadores",
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
    que: "Cuánta atención pública se llevan seis problemas, medida por lo que se busca en internet: inflación, precios, dólar, empleo, inseguridad y corrupción.",
    aporta: "Mide la preocupación por la conducta (qué busca la gente cuando algo le duele), complementando al ICC que la mide por encuesta. Los seis términos pesan lo mismo y cada uno se compara contra el arranque del mandato. La corrupción es la excepción de lectura: se mueve por escándalos, así que un pico suyo dice que se habla de un caso, no que empeoró el bolsillo.",
    frecuencia: "Mensual", tipo: "Índice (100 = 4T-2023)",
  },
  motorizacion_total: {
    que: "Cuántos vehículos 0 kilómetro —autos y motos sumados— se incorporan por cada mil habitantes en una ventana móvil de doce meses. En el ITCIS se compara contra el promedio del 4º trimestre de 2023.",
    aporta: "Mide acceso total a un vehículo sin confundir una suba de motos con una mejora automática: si los hogares sólo reemplazaran autos por motos, la suma quedaría estable. La ficha muestra ambas patas y el cambio de su composición para distinguir acceso de sustitución descendente.",
    frecuencia: "Mensual (primeros días del mes siguiente)", tipo: "Nivel per cápita · índice base-100 en el gráfico",
  },
  patentamiento_motos: {
    que: "Cuántas motos se patentan en el mes.",
    aporta: "Proxy de consumo durable de los sectores medios y bajos.",
    frecuencia: "Mensual", tipo: "Conteo",
  },
  patentamiento_autos: {
    que: "Cuántos autos 0 kilómetro se inscriben en el mes en los Registros Seccionales de la Propiedad del Automotor. En el ITCIS puntúa por el promedio móvil de 12 meses rebaseado a 100 = 4T-2023, igual que las motos.",
    aporta: "Es la compra más cara que hace un hogar después de la vivienda, y la más sensible al crédito: se pospone apenas el ingreso se estrecha. Leído junto al de motos separa dos cosas que un solo indicador confunde — que los hogares compren más, o que bajen de categoría —, porque la moto es a la vez medio de trabajo y sustituto barato del auto.",
    frecuencia: "Mensual (el mes se publica en los primeros días del siguiente)", tipo: "Conteo",
  },
  consumo_supermercados: {
    que: "Cuánto compra la gente en los supermercados una vez descontada la inflación: el índice de ventas a precios constantes que publica el INDEC en su serie desestacionalizada. En el ITCIS puntúa rebaseado a 100 = 4T-2023.",
    aporta: "Es el único componente del cinturón que mide volumen efectivamente comprado. Todos los demás miden lo que entra (ingresos), lo que cuesta (precios), de dónde viene el ingreso (empleo), lo que no se paga (mora) o lo que se opina (percepción): ninguno mira lo que el hogar se llevó de la góndola. Cubre comercio registrado de cadenas, así que no ve el almacén de barrio ni el comercio informal.",
    frecuencia: "Mensual (el INDEC lo publica unos dos meses después del mes de referencia)", tipo: "Índice",
  },

  // ── Espíritu de época (el humor social) ─────────────────────────
  clima_electoral: {
    que: "La ventaja del oficialismo sobre el principal opositor (LLA − PJ) en el promedio ponderado de encuestas.",
    aporta: "Proxy de la adhesión política al proyecto de gobierno: cuando el humor social acompaña, la ventaja se sostiene.",
    frecuencia: "Continua", tipo: "Brecha (pp)",
  },
  indice_intencion_migratoria: {
    que: "Cuánto se busca en internet sobre emigrar de Argentina (por ejemplo \"emigrar de argentina\", \"vivir en el exterior\").",
    aporta: "Es una señal más estructural que el sentimiento digital: no mide urgencia del momento, sino gente que dejó de creer en un cambio dentro del país. Es un proxy de atención, no de flujo migratorio real; por eso su card lo acompaña con la migración efectiva hacia los destinos principales, como contraste.",
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
    aporta: "La métrica insignia de la reforma del Estado: personas, no pesos. Universo: Administración Pública Nacional — incluye fuerzas armadas y de seguridad (~10% de la dotación) y no incluye empresas del Estado ni provincias/municipios.",
    frecuencia: "Mensual", tipo: "Variación vs. dic-2023",
  },
  reestructuracion_organismos: {
    que: "Cuántos organismos públicos se disolvieron o cerraron desde diciembre de 2023, con ese cierre todavía vigente.",
    aporta: "Mide el avance concreto de la reforma del aparato estatal por la vía más dura y verificable: el cierre. No cuenta fusiones, transformaciones ni reorganizaciones que no impliquen disolver un organismo — esas son difíciles de verificar caso por caso y quedan fuera de lo que este indicador afirma medir. Tampoco cuenta un hallazgo de la búsqueda que, revisado caso por caso, resultó ajeno a un organismo público o fue revertido después: cada norma se contrasta contra un registro curado antes de sumar.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  rigi_inversiones: {
    que: "Cuánto de la inversión del Régimen de Incentivo a Grandes Inversiones (RIGI) ya está aprobada: el monto aprobado por resolución sobre el total de la cartera (aprobados + en evaluación).",
    aporta: "Mide si el régimen convierte las promesas en inversión ratificada, con la plataforma oficial del Ministerio de Economía. La evolución histórica grafica la inversión aprobada acumulada en dólares.",
    frecuencia: "Continua (plataforma oficial)", tipo: "Avance de reforma",
  },
  desregulacion_normativa: {
    que: "Cuántos artículos de normas quedaron modificados o eliminados por el programa desregulador desde el 10 de diciembre de 2023, según el conteo oficial del Ministerio de Desregulación y Transformación del Estado.",
    aporta: "Mide el volumen de articulado que el programa alcanzó, no la cantidad de actos administrativos firmados. La diferencia importa: un decreto que reescribe quinientos artículos y una resolución que toca uno pesan igual si se cuentan normas, y muy distinto si se cuentan artículos. Lo que el recuento no distingue es si lo derogado dejó de regir: un artículo que la Justicia repuso suma igual que uno vigente, de modo que el indicador mide el acto de desregular y no su efecto. Muestra además la forma del programa en el tiempo, que es muy desigual: un arranque acotado, un salto marcado a partir de la Ley Bases y la creación del ministerio, y una aceleración durante 2026. La card publica también las otras dos cifras del mismo informe: cuántas normas de desregulación se dictaron y cuántas normas anteriores alcanzaron.",
    frecuencia: "Mensual", tipo: "Conteo acumulado oficial",
  },
  apertura_comercial: {
    que: "La alícuota efectiva del comercio exterior: cuántos impuestos (derechos de importación + exportación, ARCA) paga en promedio cada dólar de intercambio (expo+impo del ICA). 0% = comercio libre de fricción arancelaria; 15% o más = cierre de hecho.",
    aporta: "No mide cuántos dólares entran o salen (eso puede ser una buena cosecha): mide si el Estado desmantela la fricción impositiva que encarece el comercio. La brecha cambiaria puntúa aparte, en su propio indicador.",
    frecuencia: "Mensual", tipo: "Nivel (%)",
  },
  credito_privado: {
    que: "Cuánto crece el crédito al sector privado en términos reales (variación interanual de los préstamos, deflactada por el IPC).",
    aporta: "Es el crédito REALIZADO — complementa al IdC, que mide la capacidad prestable: si la capacidad existe pero el crédito real no crece, el financiamiento no está llegando a la economía. Es la única señal no redundante de los viejos indicadores monetarios de contexto.",
    frecuencia: "Diaria (BCRA)", tipo: "Variación real",
  },
  resultado_primario: {
    que: "Cuánto le sobra (o le falta) al Estado nacional después de pagar todo su gasto, antes de los intereses de la deuda, acumulado en doce meses y medido como porcentaje de lo que recauda.",
    aporta: "Es el resultado fiscal, no los ingresos. La recaudación puede caer porque la actividad afloja o porque se bajaron impuestos a propósito, y en ninguno de los dos casos eso dice si las cuentas cierran. Este indicador responde esa pregunta directamente: de cada cien pesos recaudados, cuántos quedan.",
    frecuencia: "Mensual", tipo: "Resultado fiscal",
  },
  costo_financiamiento_tesoro: {
    que: "Qué tasa de interés real paga el Tesoro para renovar su deuda en pesos: la tasa efectiva anual de las licitaciones del mes, descontada la inflación esperada.",
    aporta: "Es el precio del financiamiento del Estado. Reservas, capacidad prestable y crédito miden cuánta financiación hay; esta mide cuánto cuesta conseguirla. Los dos extremos son malos: una tasa real muy negativa indica que el Tesoro coloca licuando al ahorrista, y una muy alta que la deuda crece más rápido que la economía.",
    frecuencia: "Mensual (licitaciones)", tipo: "Tasa real",
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
    aporta: "Verifica contra el presupuesto —no contra el anuncio— que el Decreto 198/2024 eliminó la intermediación de las Unidades de Gestión: en 2023 buena parte de la ayuda pasaba por organizaciones y cooperativas y el giro fue hacia el pago directo a las personas. Desintermediar y recortar son cosas distintas: esto mide solo lo primero.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  fal_modernizacion_laboral: {
    que: "Cuánto de la reforma laboral RIGE, y no sólo cuánto se dictó, para el Fondo de Asistencia Laboral —el mecanismo con el que la Ley de Modernización Laboral financia las indemnizaciones por despido—. Se compone de tres etapas: que los dos actos que lo ponen en pie estén dictados y no suspendidos, la Ley 27.802 y el Decreto 408/2026 (la mitad del indicador); que el régimen haya entrado en vigencia (un quinto); y que exista al menos un fondo inscripto en la Comisión Nacional de Valores (el resto).",
    aporta: "Es el indicador bisagra de la reforma laboral: el Gobierno lo presenta como su herramienta central contra la litigiosidad. Separa dos cosas que en política laboral argentina no coinciden —una norma dictada y una norma que rige— y que un indicador de actos cumplidos no puede distinguir: la Ley 27.802 estuvo suspendida con alcance general entre el 30 de marzo y el 23 de abril de 2026 por una cautelar que alcanzaba a los artículos del Fondo, y la acción de inconstitucionalidad sigue en trámite. El régimen empieza a regir el 1 de noviembre de 2026, así que hasta esa fecha no puede haber aportes ni fondos operando por más empeño que se ponga: el indicador reserva esas etapas en vez de darlas por cumplidas.",
    frecuencia: "Mensual", tipo: "Reforma vigente (0–100)",
  },
  libertad_opcion_salud: {
    que: "Qué porcentaje de los usuarios de medicina prepaga tiene sus aportes derivados directo a la prepaga, inscripta como Agente del Seguro de Salud — el canal que creó el DNU 70/2023 al eliminar la triangulación obligatoria por una obra social.",
    aporta: "Mide la adopción real de la libre elección con los padrones oficiales de la SSS (RNAS y RNEMP): antes de la reforma este canal no existía; a marzo de 2026 lo usan 2,66 millones de personas en 59 prepagas inscriptas.",
    frecuencia: "Mensual (~2 meses de rezago)", tipo: "Avance de reforma",
  },
  protocolo_antipiquetes: {
    que: "En qué porcentaje se redujeron los cortes de calle por manifestación en CABA respecto de 2023 (el distrito donde actúan las fuerzas federales y aplica el protocolo).",
    aporta: "Mide el restablecimiento del orden público que prometió el Gobierno, donde le es atribuible. Fuente: los monitoreos de Diagnóstico Político, cuya definición de piquete coincide con la de la Resolución 943/23.",
    frecuencia: "Anual", tipo: "Variación vs. base 2023",
  },
  litigiosidad_laboral: {
    que: "Cuánto varían los juicios laborales del sistema de riesgos del trabajo (SRT): acumulado de los últimos 12 meses contra los 12 previos.",
    aporta: "Es el RESULTADO que la reforma laboral persigue: enfriar la industria del juicio. Complementa al Fondo de Asistencia Laboral (que mide la adopción del instrumento): si el instrumento no avanza pero la litigiosidad se enfría igual, la dimensión lo refleja. Proxy por juicios ART — la única serie nacional mensual pública.",
    frecuencia: "Mensual (~3 meses de rezago)", tipo: "Variación 12m",
  },
  alertas_manifestacion: {
    que: "Cuántas alertas de manifestación únicas reportaron los feeds en tiempo real del transporte porteño (colectivos y subtes) durante el mes.",
    aporta: "Serie propia en construcción (acumula desde jul-2026, muestreada varias veces por día): cuando tenga historia suficiente será la base automatizable del indicador de orden público. Sin línea base 2023 — el registro histórico oficial de cortes fue dado de baja.",
    frecuencia: "Continua (muestreo 3×/día)", tipo: "Conteo mensual",
  },
  protestas_caba: {
    que: "Cuántos eventos de protesta (marchas, concentraciones, disturbios) registró ACLED en la Ciudad de Buenos Aires en los últimos 12 meses, con serie semanal desde 2018.",
    aporta: "El contraste clave del orden público: los cortes de calle se desplomaron pero los eventos de protesta no, porque la protesta se reconvirtió a marchas sin corte —exactamente lo que el protocolo buscaba—. ACLED cuenta eventos con cobertura de prensa; no capta piquetes barriales chicos.",
    frecuencia: "Semanal (ACLED)", tipo: "Conteo (12 meses)",
  },
};

// Qué mide cada DIMENSIÓN de los índices paramétricos (modal de dimensión).
// Claves únicas entre ITCM/ITCG/ITCIS.
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
  reforma_laboral: "Instrumento y resultado: la adopción del Fondo de Asistencia Laboral (el reemplazo del canal indemnizatorio) y la litigiosidad laboral (la industria del juicio que la reforma promete enfriar).",
  privatizaciones_inversion: "Los activos del Estado y la inversión privada grande: privatizaciones, cartera del RIGI y concesiones viales.",
  social_orden: "La reforma social y el orden público: asistencia sin intermediarios (TDPS), protocolo antipiquetes y libertad de opción en salud.",
  // ITCIS
  ingresos: "Si el sueldo alcanza y qué compra: la brecha entre el salario y la canasta de pobreza, la pobreza estimada mes a mes, y dos termómetros de bolsillo —el consumo de carne y el patentamiento de motos— que se mueven con el poder de compra.",
  precios: "Lo que más duele en la compra de todos los días: alimentos y tarifas, medidos contra los salarios (no contra la inflación general).",
  vulnerabilidad: "Cuán expuestas están las familias por su deuda de consumo. Combina la mora de la cartera —incumplimiento ya materializado— con la carga del servicio de deuda sobre la masa salarial —capacidad de pago comprometida antes del atraso—.",
  empleo: "El trabajo por sus dos caras: cuánto hay y de qué calidad es. La informalidad y el empleo registrado del sector privado miden lo segundo y lo primero; las completan tres señales del entorno que demanda ese empleo: actividad industrial, construcción (cemento, el sector más intensivo en mano de obra) y pluriempleo.",
  percepcion: "El ánimo con que se vive el momento, medido de dos maneras: preguntando (el Índice de Confianza del Consumidor de la UTDT) y observando qué busca la gente en internet.",
  seguridad: "Qué proporción de los hogares fue víctima de un delito. No es percepción ni sensación: es el hecho, relevado por encuesta.",
  // ITCP
  imagen_voto: "La ventaja electoral medida en las encuestas: la brecha de intención de voto entre La Libertad Avanza y el peronismo.",
  sector_privado: "La relación con los empresarios, medida por la diferencia entre lo que esperan las constructoras que trabajan para el Estado y lo que esperan sus pares que trabajan para clientes privados. Al ser el mismo sector, con los mismos costos y el mismo crédito, lo único que las separa es quién les paga: la diferencia aísla lo que aporta la política pública y descarta el ciclo económico.",
  poder_judicial: "La capacidad de integrar el Poder Judicial, medida por la proporción de cargos de juez que tienen juez designado. No es una decisión que el Gobierno tome solo: designar jueces requiere acuerdo del Senado, de modo que la cobertura de los tribunales es un termómetro de la negociación política. La dimensión mide por ahora la capacidad de nombrar, no el comportamiento de la Justicia.",
  poder_legislativo: "La capacidad de gobernar por ley en el Congreso: cuánto legisla por decreto en vez de ley (ratio DNU), qué porción de la agenda del Ejecutivo se aprueba, cuántas sesiones de Diputados fracasan por falta de quórum, cuántas derrotas sufre el Ejecutivo en el recinto y qué porción de sus normas desafiadas logra sostener en pie.",
  alianzas_territoriales: "El sostén federal del gobierno, visto desde tres señales: las transferencias a las provincias, el alineamiento de los senadores no oficialistas con la posición del bloque de gobierno, y la adhesión provincial al RIGI. Conviene una precisión sobre qué mide y qué no: ninguna de las tres observa directamente la conducta de los gobernadores. La primera describe lo que hace el Gobierno nacional; la segunda, cómo votan los senadores de cada provincia; la tercera, una decisión legislativa provincial ya tomada. No se encontró una fuente pública que midiera de forma automatizable la postura de los ejecutivos provinciales, así que la dimensión se lee como respaldo territorial observado por sus efectos, no como una medición de la relación con cada gobernador.",
  cohesion_interna: "Qué tan unido está el oficialismo puertas adentro: la disciplina de voto del bloque propio de La Libertad Avanza, medida en un único indicador bicameral (Diputados 65%, Senado 35%).",
  conflicto_social: "La conflictividad social que el gobierno tiene que administrar: los eventos de protesta y disturbios de todo el país registrados por ACLED, acumulados en 12 meses y comparados contra 2023, la línea de base del mandato.",
};
