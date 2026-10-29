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
    que: "Los dólares del Banco Central una vez descontadas sus deudas de corto plazo, según una cuenta propia de CiGob sobre la planilla oficial de reservas. Suma además los depósitos del Tesoro y deja afuera un tramo de vencimientos, por eso da más que otras estimaciones del mercado. No es una cifra oficial de reservas netas ni de dólares de libre disponibilidad.",
    aporta: "Aproxima el margen externo con una definición explícita. Su lectura depende de los pasivos excluidos y debe contrastarse con otras medidas de reservas y liquidez.",
    frecuencia: "Mensual", tipo: "Nivel neto (stock)",
  },
  idc: {
    que: "Mide si los bancos tienen plata y margen para prestar, comparado con lo habitual desde 2018. Cero es un mes normal; positivo, más margen; negativo, menos. Combina tres cosas: lo que cobran en términos reales los que depositan, cuánto crecen los depósitos privados y cuánto de esos depósitos queda sin prestar.",
    aporta: "Un sistema con capacidad de fondeo por encima de lo habitual puede acompañar la inversión y la actividad; uno sin margen, no. Se publica en desvíos estándar respecto de la historia 2018→hoy: 0 es el mes típico; por encima, más capacidad que la habitual, y por debajo, menos. En el semáforo de la tarjeta, desde 0 es verde, de −0,6 a 0 amarillo, de −0,9 a −0,6 naranja y por debajo de −0,9 rojo. Datos del Banco Central de la República Argentina (BCRA) —tasa de plazos fijos mayoristas (BADLAR), depósitos y préstamos privados— e índice de precios al consumidor (IPC) del Instituto Nacional de Estadística y Censos (INDEC).",
    frecuencia: "Mensual", tipo: "Índice (σ)",
  },
  badlar: {
    que: "Tasa de referencia que pagan los bancos por captar depósitos mayoristas a 30 días o más.",
    aporta: "Refleja el costo del dinero y el sesgo de la política monetaria; hoy es insumo del Índice de Capacidad Prestable.",
    frecuencia: "Diaria", tipo: "Tasa",
  },
  emae_ia: {
    que: "El pulso mensual de la actividad económica: cuánto creció o cayó respecto de un año atrás.",
    aporta: "Adelanta el ritmo del producto interno bruto: si la economía se expande o se contrae.",
    frecuencia: "Mensual", tipo: "Variación interanual",
  },
  empleo_registrado: {
    que: "Cuántos asalariados del sector privado están registrados ante la seguridad social. Es el dato que las empresas declaran mes a mes, no una estimación de encuesta.",
    aporta: "Cuenta puestos asalariados privados registrados. Complementa las medidas de actividad e informalidad; no cubre empleo público, independiente o no registrado ni describe por sí solo la calidad de esos puestos. La serie permite seguir el nivel y sus variaciones con la fecha de cada observación. NO puntúa: salió del índice de impacto social en octubre de 2026 y se sigue relevando como archivo.",
    frecuencia: "Mensual", tipo: "Nivel (miles de puestos)",
  },
  cobertura_judicial: {
    que: "Qué porcentaje estimado de los cargos de juez de la justicia federal y nacional tiene juez designado. Se reconstruye desde un padrón y movimientos netos documentados; no certifica juras ni todos los cargos efectivamente en ejercicio. Una vacante sigue contando como vacante aunque tenga subrogante. Un titular de licencia con reemplazo transitorio conserva su cargo cubierto.",
    aporta: "Describe la capacidad de integrar el Poder Judicial mediante un proceso que requiere designación del Ejecutivo y acuerdo del Senado. El acuerdo sobre un pliego no equivale a una toma de posesión. La reconstrucción conserva un universo fijo de órganos habilitados y requiere conciliar altas, promociones, traslados y bajas; sus revisiones no deben interpretarse como cambios ocurridos en el mes.",
    frecuencia: "Irregular (registro revisado)", tipo: "% estimado de cobertura",
  },
  produccion_legislativa: {
    que: "Cuántas leyes sancionó el Congreso en los últimos doce meses que el Gobierno aceptó: no cuentan las que el Poder Ejecutivo vetó en su totalidad, aunque el Congreso después haya insistido; las vetadas en parte sí, porque se promulgaron. No distingue de quién nació cada proyecto. Cuenta leyes sancionadas, no publicadas. Por eso no es el mismo denominador que «Decretos de necesidad y urgencia por ley», que cuenta leyes publicadas en el Boletín Oficial, otro momento del trámite: los dos números de leyes no coinciden.",
    aporta: "Responde si el Congreso sanciona leyes que el Gobierno acepta: más leyes, menos tensión entre los poderes. Una ley vetada entera no es producción compartida sino un desacuerdo, y ese desacuerdo ya lo registran los vetos insistidos. No equipara el total a victorias del Ejecutivo: ni el origen ni el contenido de cada ley se deducen del conteo.",
    frecuencia: "Mensual", tipo: "Conteo en ventana móvil",
  },
  judicializacion: {
    que: "Qué porcentaje de los sumarios publicados por el Sistema Argentino de Información Jurídica (SAIJ) en jurisdicción federal y nacional menciona una medida cautelar. Ya no puntúa en el índice político: salió del índice porque ese corpus no identifica causas contra el Poder Ejecutivo ni contra políticas de su agenda —una cautelar entre privados cuenta igual—, así que la proporción no mide judicialización de la agenda de gobierno. Se sigue relevando.",
    aporta: "Da la densidad de menciones cautelares en la jurisprudencia publicada, que es un dato sobre el corpus del Sistema Argentino de Información Jurídica (SAIJ) y no sobre el Ejecutivo. Se publica como proporción y no como conteo porque el número de fallos publicados depende del volumen editorial de la base de jurisprudencia: el conteo crudo se quintuplica entre 2016 y 2021 sin que las cautelares se hayan quintuplicado.",
    frecuencia: "Anual", tipo: "% de fallos",
  },
  velocidad_resolucion: {
    que: "Cuántos expedientes resuelve la Corte Suprema en un año, en proporción a los que le ingresan.",
    aporta: "Compara las salidas y entradas anuales de casos: por encima de cien se resuelven más casos de los que ingresan; por debajo, menos. No mide el tiempo que tarda una causa ni si las decisiones favorecen al Gobierno. Desde octubre de 2026 no integra el índice político: mide la eficiencia de la Justicia, no al Poder Ejecutivo. Se sigue calculando.",
    frecuencia: "Anual", tipo: "% resuelto sobre ingresado",
  },
  paralisis_denuncias: {
    que: "Cuántas veces sesionaron en los últimos doce meses las dos comisiones del Consejo de la Magistratura que tramitan las denuncias contra jueces: Acusación y Disciplina.",
    aporta: "Describe la frecuencia de reuniones de Acusación y Disciplina. No informa cuántas denuncias se resolvieron, el sentido de las decisiones ni si hubo sanciones. La ausencia de una nota publicada tampoco certifica que una comisión no se haya reunido. Desde octubre de 2026 no integra el índice político: el control sobre los jueces lo ejerce el Consejo, no el Poder Ejecutivo. Se sigue calculando.",
    frecuencia: "Mensual", tipo: "Conteo en ventana móvil",
  },
  emae_difusion: {
    que: "De los quince sectores en que el Instituto Nacional de Estadística y Censos (INDEC) divide la actividad económica, cuántos crecen respecto de un año atrás.",
    aporta: "Distingue un crecimiento generalizado de uno concentrado en pocos sectores. El estimador mensual de actividad económica (EMAE) informa cuánto crece la economía; este indicador, en cuántas partes de ella crece: dos meses con la misma variación agregada pueden significar cosas muy distintas según cuántos sectores la sostengan.",
    frecuencia: "Mensual", tipo: "Índice de difusión",
  },
  ipi_manufacturero: {
    que: "Cuánto produce la industria manufacturera respecto de un año atrás, promediado en tres meses.",
    aporta: "Segunda lectura de la actividad, junto al estimador mensual de actividad económica (EMAE): mide sólo la industria y se publica algo antes, de modo que la dimensión no depende de un único dato.",
    frecuencia: "Mensual", tipo: "Variación interanual (promedio de 3 meses)",
  },
  actividad_tributaria: {
    que: "Cuánto crecieron, en términos reales y respecto de un año atrás, el impuesto al valor agregado (IVA) que cobra la Dirección General Impositiva y el impuesto a los créditos y débitos bancarios (impuesto al cheque), promediados con más peso para el IVA.",
    aporta: "La lectura más fresca de la dimensión: Hacienda informa estos dos tributos antes de que el Instituto Nacional de Estadística y Censos (INDEC) cierre el estimador mensual de actividad económica (EMAE) del mismo mes. El impuesto al valor agregado (IVA) sigue de cerca el consumo interno; el cheque sigue toda transacción bancaria, así que además de actividad capta bancarización.",
    frecuencia: "Mensual", tipo: "Variación interanual real (compuesto)",
  },
  saldo_comercial_12m: {
    que: "El balance entre lo que el país exporta y lo que importa, acumulado en los últimos 12 meses, como porcentaje de todo el comercio de esos meses (exportaciones más importaciones). El monto en dólares se ve en el detalle.",
    aporta: "Muestra si el intercambio de bienes aporta o resta dólares, en proporción a su tamaño, para que un mismo resultado se compare entre años con comercios muy distintos. No alcanza para saber si el sector externo en conjunto los genera: faltan los servicios, los intereses y las utilidades giradas, que se ven en la cuenta corriente del gráfico.",
    frecuencia: "Mensual", tipo: "Proporción del comercio (acumulado de 12 meses)",
  },
  recaudacion: {
    que: "Índice de recaudación interna en términos reales, ajustado por estacionalidad y comparado con el cuarto trimestre de 2023, que vale 100. Combina tributos internos nacionales e Ingresos Brutos recaudado por los regímenes de la Comisión Arbitral del Convenio Multilateral; excluye los tributos aduaneros.",
    aporta: "Aproxima la evolución de la base imponible mediante ingresos cobrados. También responde a cambios de alícuotas, vencimientos, pagos atrasados y reasignaciones tributarias. Un nivel menor que 100 indica menor recaudación real ajustada respecto de la base; no prueba por sí solo que haya menos actividad formal.",
    frecuencia: "Mensual", tipo: "Índice de base imponible real (100 = 4º trimestre de 2023)",
  },
  tcrm: {
    que: "Si el peso está caro o barato frente a los socios comerciales, en términos reales (competitividad cambiaria), según el tipo de cambio real multilateral del Banco Central.",
    aporta: "Una apreciación real (peso caro) frena exportaciones y la acumulación de reservas, y suele anticipar presión cambiaria: cuanto más apreciado, más tensión. El sector externo no lo promedia con los términos del intercambio: los cruza, porque un peso apreciado con buenos precios de exportación no es lo mismo que el mismo peso con precios en caída.",
    frecuencia: "Mensual", tipo: "Índice (base diciembre de 2015 = 100)",
  },
  tcr_terminos_intercambio: {
    que: "El cruce del tipo de cambio real con los términos del intercambio en una medida de 0 a 100. Desde octubre de 2026 no es tarjeta: ese cruce lo hace el sector externo con las dos tarjetas por separado, y este número es el mismo que el del cruce.",
    aporta: "Se sigue calculando para conservar su serie.",
    frecuencia: "Mensual", tipo: "Puntaje 0–100",
  },
  terminos_intercambio: {
    que: "Cuánto valen las exportaciones argentinas frente a lo que se importa: los precios de exportación sobre los de importación, según el Instituto Nacional de Estadística y Censos.",
    aporta: "Dice si el nivel del tipo de cambio real se sostiene: con buenos precios de exportación, un peso caro aguanta más. El sector externo lo cruza con el tipo de cambio real en vez de promediarlos: con el peso competitivo el ajuste ya ocurrió; un peso apreciado que se sostiene por buenos precios depende de una variable externa y volátil. Se publica por trimestre, con unos dos meses y medio de demora.",
    frecuencia: "Trimestral", tipo: "Índice (base 2004 = 100)",
  },
  rem_ipc_12m: {
    que: "La inflación que el mercado espera para los próximos 12 meses, en tasa anual, según el relevamiento de expectativas del Banco Central. Para compararla con la inflación del mes, 12,7 % anual equivale a 1 % por mes y 26,8 % anual, a 2 % por mes.",
    aporta: "Captura la credibilidad del programa: si el mercado espera que la inflación siga bajando, el ancla de expectativas funciona; si la ve acelerarse, hay desconfianza.",
    frecuencia: "Mensual", tipo: "Expectativa",
  },
  idm: {
    que: "Brecha de crecimiento real entre dos agregados monetarios: compara cuánto crece el agregado amplio de pesos del sector privado (el que se conoce como M3 privado) con cuánto crece el transaccional (M2 privado), ambos en términos reales e interanuales. Los dos son agregados monetarios, así que la brecha no es oferta menos demanda de dinero: estimar una demanda pide variables, forma funcional y validación, y nada de eso hay acá. El agregado transaccional incluye el circulante en poder del público, las cuentas corrientes privadas en pesos y las cajas de ahorro privadas en pesos; excluye los depósitos a la vista remunerados de personas jurídicas. Ya no puntúa en el índice macroeconómico: salió del índice en agosto de 2026 porque su banda castigaba la brecha positiva apoyada en esa lectura de oferta contra demanda, que el proyecto descartó, y ninguna referencia externa del proyecto pudo firmar esa dirección. Se sigue calculando y su serie histórica se conserva, pero ya no se publica como tarjeta del tablero.",
    aporta: "Muestra hacia dónde se mueven los pesos dentro del sistema: una brecha positiva dice que el agregado amplio corre más rápido que el transaccional —los pesos se van a plazo y a instrumentos remunerados en vez de quedarse en transacciones—; una negativa, lo contrario. Es un dato sobre la velocidad relativa de dos agregados, no un diagnóstico de exceso monetario — y por eso se publica como dato y no como puntaje.",
    frecuencia: "Mensual", tipo: "Brecha interanual real",
  },
  desequilibrio_monetario: {
    que: "Mira dos cosas a la vez: si la gente sigue usando pesos y cuántos dólares compra; si las dos empeoran juntas, la presión sobre el peso es mayor. Es una medida de tensión de 0 a 100 (más alto es peor) que cruza dos cosas observables: cuánta de la liquidez privada total —pesos más dólares depositados— sigue estando en pesos de uso transaccional, y cuántos dólares netos compra el sector privado no financiero en el mercado de cambios. Hasta agosto de 2026 el segundo componente se llamaba «fuga fuera del sistema»; no mide eso: el Banco Central estimó que cerca del 80% de esas compras quedó depositado localmente. Comprar divisas y sacarlas del sistema financiero son dos actos distintos, y acá sólo se observa el primero.",
    aporta: "Los dos componentes se leen juntos porque uno solo alcanza para engañar: la composición de la liquidez puede verse estable mientras crece la compra de divisas, y a la inversa. El resultado sale de cruzarlos en una matriz, no de promediarlos. Mayor tensión reduce el puntaje de estabilidad monetaria.",
    frecuencia: "Mensual", tipo: "Tensión 0–100",
  },
  iai: {
    que: "Índice Anticipador de Inversión: mide la inversión física/tradicional combinando el indicador sintético de la actividad de la construcción (ISAC) que releva el Instituto Nacional de Estadística y Censos (INDEC) y la importación de bienes de capital, en variación interanual.",
    aporta: "Resume señales de construcción e importación de bienes de capital frente al mismo mes del año anterior. Los cortes de su escala se corren 0,17 puntos, lo que crece la población por año: invertir menos que eso es invertir menos por habitante. No mide depreciación ni inversión neta: una caída interanual no demuestra que se consuma más capital del que se repone. Los bienes importados se miden en dólares corrientes, por lo que también influyen sus precios.",
    frecuencia: "Mensual", tipo: "Variación interanual ponderada",
  },
  icip: {
    que: "Pagos de servicios digitales y productividad: combina los pagos al exterior por servicios de informática (software, nube, inteligencia artificial) con la productividad laboral (producción industrial por ocupado), en variación interanual. No es inversión digital ni capitalización: en cuentas nacionales esos pagos transfronterizos son consumo intermedio, no formación bruta de capital — pagar la licencia de la nube todos los meses no capitaliza a nadie. Ya no puntúa en el índice macroeconómico: salió del índice en agosto de 2026 porque suma con el mismo signo dos insumos que necesitarían signos opuestos —más pagos al exterior por informática suben el puntaje, y son gasto corriente en divisas—, así que ninguna dimensión lo arreglaba. Se sigue calculando y su serie histórica se conserva, pero ya no se publica como tarjeta del tablero.",
    aporta: "Sigue el gasto en tecnología que no pasa por aduana como bien de capital. Leído junto al índice anticipador de inversión apunta a la 'trampa de la madurez': un país puede invertir en ladrillos y camiones pero estancarse si no se digitaliza. Con una advertencia declarada en la ficha: un aumento de los pagos al exterior por software admite leerse como digitalización o como dependencia tecnológica, y el indicador puntúa la primera. Medir inversión digital de verdad pediría software, bases de datos y equipos de informática y comunicaciones según cuentas nacionales: eso es un indicador nuevo, no otro rótulo sobre éste. Se construye con datos del Instituto Nacional de Estadística y Censos (INDEC): balanza de servicios y producción industrial por ocupado.",
    frecuencia: "Mensual", tipo: "Variación interanual ponderada",
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
    que: "La diferencia de intención de voto entre La Libertad Avanza y el Partido Justicialista, ponderando las encuestas disponibles.",
    aporta: "Mide el capital electoral del oficialismo, base de su poder de negociación.",
    frecuencia: "Continua", tipo: "Brecha (puntos porcentuales)",
  },
  desafios_legislativos: {
    que: "Cuántas normas propias del Gobierno fueron puestas en discusión en el recinto durante los últimos doce meses: vetos presidenciales sobre los que el Congreso votó una insistencia, y decretos sometidos a votación bajo la ley 26.122.",
    aporta: "Mide con qué frecuencia el Congreso decide dar la pelea, sin importar cómo termine. Desafiar una norma del Ejecutivo es un acto excepcional —exige mayorías especiales o un procedimiento específico—, así que un puñado al año ya indica confrontación abierta. Desde octubre de 2026 no integra el índice: lo reemplazan los vetos que el Congreso dio vuelta y los decretos que derogó con las dos cámaras, que cuentan sólo lo consumado. Se sigue calculando.",
    frecuencia: "Continua (12 meses)", tipo: "Conteo",
  },
  insistencias_vetos: {
    que: "Cuántos vetos del Presidente dio vuelta el Congreso en los últimos doce meses: leyes vetadas a las que las dos cámaras les insistieron con dos tercios de los votos, y que quedaron promulgadas igual.",
    aporta: "Es la derrota legislativa más dura que puede sufrir el Ejecutivo: exige dos tercios en las dos cámaras. Cuenta sólo lo consumado; una insistencia que se vota y no alcanza los dos tercios, o que aprueba una sola cámara, no suma. Cero es la lectura más favorable para el Gobierno.",
    frecuencia: "Continua (12 meses)", tipo: "Conteo",
  },
  rechazos_decretos: {
    que: "Cuántos decretos de necesidad y urgencia o delegados derogó el Congreso en los últimos doce meses: los que rechazaron las dos cámaras, como exige la ley 26.122.",
    aporta: "El rechazo de una sola cámara no deroga el decreto; el de las dos, sí. Cuenta sólo los derogados, fechados en el rechazo de la segunda cámara. Cero es la lectura más favorable para el Gobierno.",
    frecuencia: "Continua (12 meses)", tipo: "Conteo",
  },
  brecha_obra_publica: {
    que: "La diferencia entre lo que esperan las empresas constructoras que trabajan para el Estado y lo que esperan las que trabajan para clientes privados. El Instituto Nacional de Estadística y Censos (INDEC) les pregunta todos los meses si creen que su actividad va a subir o bajar en el trimestre siguiente, y publica las dos respuestas por separado. El indicador resta una de la otra y promedia los últimos doce meses.",
    aporta: "Compara las expectativas de constructoras orientadas a obra pública y privada. Una brecha negativa indica un saldo de expectativas menor en el primer grupo. Compartir sector no garantiza iguales costos, acceso al crédito ni composición de proyectos: la diferencia no aísla el efecto causal de la política pública ni elimina el ciclo económico. Su interpretación como tensión política debe contrastarse con la agenda y las condiciones del período.",
    frecuencia: "Mensual (12 meses)", tipo: "Brecha (puntos porcentuales)",
  },
  apoyo_empresario: {
    que: "Qué dicen en público, por escrito y con firma institucional, las cámaras de la industria sobre las medidas del Gobierno nacional: la Unión Industrial Argentina (UIA) y, desde el 27 de octubre de 2026, la Asociación de Fábricas Argentinas de Componentes (AFAC), que reúne a los autopartistas. Cada comunicado se lee y se clasifica: si respalda o critica, y a quién le habla. Se cuentan sólo los que se pronuncian sobre una medida del Ejecutivo nacional. Cada cámara tiene su saldo entre apoyos y críticas de los últimos doce meses, y el indicador es el promedio simple de los dos: cada cámara pesa lo mismo, publique mucho o poco, y si una no llega a tres pronunciamientos en la ventana cuenta la otra. Los informes estadísticos periódicos de AFAC —actividad y comercio exterior del sector— no son tomas de posición y quedan afuera. Es el componente de la industria de la dimensión de sector privado del índice político, que reparte en partes iguales entre la industria, el comercio, el campo y la construcción. Estuvo fuera del índice entre agosto y septiembre de 2026 porque el saldo se calculaba con comunicados sin clasificar; volvió con una regla que lo impide: la serie sólo llega hasta el último mes con todos los comunicados clasificados. Hasta septiembre de 2026 el indicador promediaba dos cámaras, con la Asociación Empresaria Argentina; salió del cálculo porque dejó de publicar comunicados el 31 de marzo de 2026 y un rótulo no puede prometer dos cámaras midiendo una. Sus comunicados quedan guardados y clasificados: si vuelve a publicar, vuelve a entrar. Desde el recorte, un mes se publica sólo si tiene al menos tres comunicados computables en la ventana — con una sola cámara, dos comunicados alcanzaban para dar un saldo extremo que no describe nada.",
    aporta: "Es la única medida directa de la relación entre el Gobierno y el empresariado organizado: las demás miran el clima de negocios o los datos de un sector, y de ahí infieren el vínculo. Acá el vínculo está dicho. Conviene saber qué no dice: no mide el humor del empresariado en general ni la opinión de sus asociados, sino lo que una asociación decidió declarar públicamente — una cámara puede callar por conveniencia y ese silencio no aparece. Desde septiembre de 2026 el silencio sí aparece: hay un aviso automático cuando una cámara deja de publicar por más tiempo que el que se tomó nunca. La clasificación la hace una persona siguiendo reglas escritas de antemano, y dos personas distintas la hicieron por separado para verificar que las reglas no dejan lugar a la interpretación.",
    frecuencia: "Continua (12 meses)", tipo: "Saldo (−1 a +1)",
  },
  apoyo_campo: {
    que: "Qué dicen en público, por escrito y con firma institucional, Coninagro, la Sociedad Rural Argentina (SRA) y las Confederaciones Rurales Argentinas (CRA) sobre las medidas del Gobierno nacional. Cada nota se lee y se clasifica con las mismas reglas que las de la industria y el comercio: si respalda o critica, y a quién le habla. Se cuentan sólo las que se pronuncian sobre una medida del Ejecutivo nacional. Cada cámara tiene su saldo entre apoyos y críticas de los últimos doce meses, y el indicador es el promedio simple de esos saldos: cada entidad pesa lo mismo, publique mucho o poco. Los informes estadísticos periódicos de Coninagro no son tomas de posición y quedan afuera. La Federación Agraria no tiene sección de prensa y no se mide.",
    aporta: "Suma al campo, el sector que más pelea con el Estado por impuestos y retenciones, a la lectura del vínculo entre el Gobierno y el empresariado organizado. Conviene saber qué dice y qué no: las tres cámaras publican en sitios con archivos distintos — el de la SRA arranca en enero de 2025, y por eso la serie empieza en enero de 2026 —, y sus posturas son muy distintas entre sí: la CRA critica mucho más de lo que apoya y la SRA apoya más de lo que critica; el promedio las pone en pie de igualdad aunque la CRA publique varias veces más. No mide la opinión de los productores: mide lo que tres entidades decidieron declarar públicamente.",
    frecuencia: "Continua (12 meses)", tipo: "Saldo (−1 a +1)",
  },
  apoyo_construccion: {
    que: "Qué dice en público, por escrito y con firma institucional, la Cámara Argentina de la Construcción (CAMARCO) sobre las medidas del Gobierno nacional. Cada nota se lee y se clasifica con las mismas reglas que las de la industria, el comercio y el campo: si respalda o critica, y a quién le habla. Se cuentan sólo las que se pronuncian sobre una medida del Ejecutivo nacional, y el indicador es el saldo entre apoyos y críticas de los últimos doce meses. La cámara publica todo en un mismo lugar —agenda, cursos, delegaciones, su indicador mensual y los acuerdos salariales—; lo que no es un comunicado queda afuera, y la crónica de un acto cuya declaración ya se contó no se cuenta de nuevo.",
    aporta: "Suma a la construcción, el sector que más depende de la obra pública, a la lectura del vínculo entre el Gobierno y el empresariado organizado. Conviene saber qué dice y qué no: la cámara se pronuncia poco sobre el Ejecutivo —dieciséis veces en casi tres años, cuatro en el último—, así que cada comunicado mueve mucho el saldo. No mide la opinión de las constructoras: mide lo que una cámara decidió declarar públicamente. Las notas las clasificaron por separado dos lectores, y una persona resolvió los desacuerdos que importaban.",
    frecuencia: "Continua (12 meses)", tipo: "Saldo (−1 a +1)",
  },
  apoyo_comercio: {
    que: "Qué dice en público, por escrito y con firma institucional, la Cámara Argentina de Comercio y Servicios (CAC) sobre las medidas del Gobierno nacional. Cada comunicado se lee y se clasifica con las mismas reglas que los de la Unión Industrial: si respalda o critica, y a quién le habla. Se cuentan sólo los que se pronuncian sobre una medida del Ejecutivo nacional, y el indicador es el saldo entre apoyos y críticas de los últimos doce meses. Los informes estadísticos periódicos de la cámara (consumo, venta ilegal, comercio con Brasil) no son tomas de posición y quedan afuera. La Confederación Argentina de la Mediana Empresa (CAME) está clasificada pero no entra al cálculo: en los últimos doce meses sólo dos de sus comunicados se pronunciaron sobre el Gobierno nacional y el mínimo para entrar es de cuatro.",
    aporta: "Suma al comercio a la lectura del vínculo entre el Gobierno y el empresariado organizado, que antes miraba sólo a la industria. Conviene saber qué dice y qué no: la CAC apoyó al Gobierno en cada comunicado que le dedicó, y sus críticas van dirigidas a las provincias, los municipios y el Congreso — no al Ejecutivo nacional —, de modo que el saldo está en el máximo en toda la serie y es difícil que se mueva hacia abajo aunque cambie el humor del sector. Con tan pocos pronunciamientos por año, una sola crítica lo movería mucho. No mide la opinión de los comerciantes ni de las pymes: mide lo que una cámara decidió declarar públicamente. La clasificación la hace una persona siguiendo reglas escritas de antemano; esta vez la hicieron por separado dos lectores de distinto tipo para verificar que las reglas no dejan lugar a la interpretación.",
    frecuencia: "Continua (12 meses)", tipo: "Saldo (−1 a +1)",
  },
  ratio_dnu: {
    que: "Cuántos decretos de necesidad y urgencia se publican en el Boletín Oficial por cada ley publicada en él, dentro de una ventana móvil de 365 días. Las leyes del denominador son las publicadas, no las sancionadas, así que no coincide con la «Producción legislativa», que cuenta las que sanciona el Congreso. Los dos lados del cociente usan la misma convención jurídica —la publicación, no el dictado ni la sanción—: son momentos distintos del trámite y mezclarlos mueve el ratio sin que nada falle.",
    aporta: "Mide con cuánta frecuencia el Gobierno recurre al decreto en lugar de la ley, no si esos decretos le funcionan. Son dos preguntas distintas y conviene no confundirlas. La gran mayoría de los decretos de necesidad y urgencia nunca llega a votarse en el recinto y sigue vigente, pero el Congreso puede derogarlos con el rechazo de las dos cámaras, como hizo con el de los fondos reservados de inteligencia en 2024 y el de la marina mercante en 2025. La dependencia del decreto es una vulnerabilidad latente: no se cobra mientras el Congreso no active el procedimiento, y se cobra de golpe cuando lo activa.",
    frecuencia: "Continua (12 meses)", tipo: "Ratio",
  },
  conflictividad_nacional: {
    que: "Cuántos eventos de protesta y disturbios hubo en todo el país en los últimos 12 meses completos, comparados contra el total de 2023 (el año base del mandato). Cuenta marchas, concentraciones y disturbios registrados por Armed Conflict Location & Event Data (ACLED), el relevamiento académico internacional estándar de conflicto social, en las 24 jurisdicciones.",
    aporta: "Aproxima la tensión en la calle a escala nacional, un límite real al margen de maniobra del Gobierno. Menos conflicto que en 2023 significa menos tensión; la comparación de 12 meses contra el año completo absorbe la estacionalidad del calendario de protestas.",
    frecuencia: "Semanal", tipo: "Variación (%)",
  },
  jornadas_individuales_no_trabajadas_12m: {
    que: "Cuántas jornadas individuales de trabajo se perdieron por paros en todo el país durante los últimos doce meses. La Secretaría de Trabajo las estima multiplicando la cantidad de huelguistas por la duración de cada paro.",
    aporta: "Agrega intensidad a la frecuencia de eventos que mide el relevamiento internacional Armed Conflict Location & Event Data (ACLED): distingue un conflicto breve y pequeño de uno largo o masivo. Es una estadística laboral oficial y sus valores mensuales pueden sumarse sin duplicar conflictos ni personas.",
    frecuencia: "Mensual (12 meses)", tipo: "Conteo de jornadas",
  },
  movilizacion_cepa: {
    que: "El nivel de conflictividad social y laboral: paros, protestas y cortes, según los informes del Centro de Economía Política Argentina.",
    aporta: "Aproxima la tensión en la calle. Desde julio de 2026 no integra el índice del cinturón ni se publica en el tablero: su fuente publica informes recién desde fines de 2025 (sin serie histórica posible) y su cifra acumula conflictos desde el inicio de cada año, lo que impide comparar meses entre sí — la medición continúa como contraste interno del indicador nacional de conflictividad.",
    frecuencia: "Por informe", tipo: "Índice (0–100)",
  },
  iaf_transferencias: {
    que: "Cuánto varían, en términos reales, los recursos de origen nacional que la Nación giró a las jurisdicciones durante los últimos 12 meses, comparado con los 12 meses anteriores (la ventana termina en el último mes con índice de precios al consumidor publicado). Entra lo transferido a las provincias, a la Ciudad de Buenos Aires y al Fondo Compensador, incluida la compensación del Consenso Fiscal; quedan afuera las porciones que se quedan en la Nación —Tesoro Nacional, Seguridad Social y Fondo de Aportes del Tesoro Nacional—. Son las transferencias automáticas (coparticipación neta, financiamiento educativo, leyes especiales y compensaciones), no los giros discrecionales.",
    aporta: "Mide el gesto fiscal de la Nación hacia las provincias: cuánto gira por encima o por debajo de lo que giraba antes, en términos reales. Es un insumo de la relación federal, no la respuesta de los gobernadores: informa lo que hace el Gobierno nacional, no cómo reaccionan las provincias.",
    frecuencia: "Mensual (12 meses móviles)", tipo: "Variación real",
  },
  transferencias_no_automaticas: {
    que: "Cuánto devengó la Nación, en términos reales, como transferencias a provincias y municipios por decisión —Aportes del Tesoro Nacional (ATN) y transferencias corrientes y de capital por programa— durante los últimos 12 meses, comparado con el total de 2023, el año anterior al mandato (la ventana termina en el último mes cerrado con índice de precios al consumidor publicado). Quedan afuera la coparticipación y el resto del reparto automático, que no pasa por el presupuesto como gasto, y las partidas que son por ley o fallo: la coparticipación de la Ciudad de Buenos Aires, el Fondo de Incentivo Docente, las cajas previsionales provinciales y los hospitales nacionales. No incluye los adelantos financieros del Tesoro, que no tienen serie mensual.",
    aporta: "Mide cuánto recurso discrecional pone la Nación en juego con las provincias frente al nivel de 2023, en términos reales. Compara contra una base fija y no contra el año anterior: así una recuperación parcial después de una caída no se lee como un aumento. Es un insumo de la relación federal, no la respuesta de los gobernadores: informa lo que hace el Gobierno nacional, no a qué provincias va ni cómo reaccionan.",
    frecuencia: "Mensual (12 meses móviles)", tipo: "Variación real (%)",
  },
  eficacia_legislativa: {
    que: "Porcentaje sancionado de los proyectos de ley del Ejecutivo publicados entre 365 y 730 días antes del corte. Cada proyecto tuvo al menos un año para tramitarse.",
    aporta: "Mide la aprobación de una cohorte de proyectos maduros. Las iniciativas publicadas hace menos de un año quedan fuera: no resume la aprobación de la agenda actual ni pondera la importancia política de cada proyecto.",
    frecuencia: "Continua (cohorte de 365–730 días)", tipo: "Nivel (%)",
  },
  cohesion_bloque: {
    que: "Qué tan parejo vota puertas adentro el bloque propio de La Libertad Avanza en las votaciones divididas (la minoría tuvo al menos 10 % de los votos) de los últimos 90 días de ambas cámaras. Diputados pesa más que el Senado (el reparto está en el detalle de la tarjeta); si una cámara no tiene votaciones divididas en la ventana, el peso pasa a la otra.",
    aporta: "Mide la cohesión interna del oficialismo en el Congreso, clave para sostener vetos y aprobar leyes. Se compara con la cohesión del bloque de Propuesta Republicana (PRO) en el gobierno de Macri, medida igual. La composición por cámara se publica en el detalle.",
    frecuencia: "Continua (90 días)", tipo: "Nivel (%)",
  },
  votos_sobre_bancas: {
    que: "Cuántos votos de legisladores que no son del bloque La Libertad Avanza hicieron falta para aprobar las leyes que mandó el Gobierno, medidos como porcentaje de las bancas de la cámara. En cada ley del Poder Ejecutivo aprobada en la votación en general (sin contar los tratados y convenios internacionales, que se votan casi por unanimidad), con el bloque oficialista votando a favor, se restan las bancas propias de La Libertad Avanza a los votos afirmativos totales. Es el promedio de los últimos 12 meses; Diputados pesa más que el Senado, y si una cámara no tuvo votaciones en la ventana, queda sólo la otra.",
    aporta: "Mide la capacidad del Ejecutivo de sumar votos ajenos en el Congreso: con un bloque propio grande hacen falta pocos votos de otros bloques, con uno chico hacen falta muchos. Complementa a la cohesión del bloque: un oficialismo unido puede igual necesitar más votos de los que tiene. Una ley aprobada con los votos de un bloque grande aliado cuenta igual que una aprobada con muchos bloques chicos, y cuando el bloque oficialista crece (como en diciembre de 2025) el excedente baja aunque el Gobierno apruebe lo mismo.",
    frecuencia: "Mensual (12 meses móviles)", tipo: "Nivel (% de la cámara)",
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
    que: "Qué porcentaje de los votos de senadores no alineados con el oficialismo (La Libertad Avanza) coincide con la posición que tomó el bloque oficialista en esa misma votación, promediado entre provincias. Se compara con lo que acompañaban a su oficialismo los senadores de otros bloques en los tres gobiernos anteriores.",
    aporta: "Es la mejor señal automatizable disponible del respaldo territorial, y conviene leerla por lo que es: mide el voto de los senadores, no la postura del gobernador de cada provincia. Un senador no depende del gobernador de turno y puede responder a la estrategia nacional de su propio partido. Reemplaza a un indicador de alineamiento de gobernadores que quedó congelado por falta de una fuente pública que midiera directamente la posición de los ejecutivos provinciales.",
    frecuencia: "Continua (90 días)", tipo: "Nivel (%)",
  },
  veto_quorum: {
    que: "Qué porcentaje de las sesiones convocadas en Diputados para tratar temas queda en minoría, es decir, no reúne el quórum necesario para sesionar. Se miden los últimos doce meses. No cuentan las sesiones que pidió la oposición y no juntaron quórum, porque ahí el que gana es el oficialismo.",
    aporta: "El quórum es el primer filtro de cualquier agenda legislativa: sin él no se debate ni se vota nada. Una tasa alta indica que el oficialismo no logra reunir a la cámara, sea porque la oposición se ausenta deliberadamente o porque sus propios aliados no acompañan.",
    frecuencia: "Mensual (12 meses)", tipo: "Nivel (%)",
  },
  comisiones_caidas: {
    que: "Qué porcentaje de los proyectos con dictamen de comisión nunca llega al recinto.",
    aporta: "Mide el embudo legislativo: cuánto queda trabado antes de poder votarse.",
    frecuencia: "Continua (12 meses)", tipo: "Nivel (%)",
  },
  derrotas_legislativas: {
    que: "Cuántas veces en los últimos 12 meses el Congreso le volteó una norma al Ejecutivo en el recinto: leyes vetadas que ambas cámaras insistieron con dos tercios, y decretos rechazados por al menos una cámara bajo la ley 26.122. Cada norma cuenta una vez.",
    aporta: "Es la medida más directa del balance de fuerzas entre el Ejecutivo y el Congreso. Cero derrotas indican control de la agenda (o falta de confrontación); un conteo alto, un Congreso capaz de imponerse.",
    frecuencia: "Continua (12 meses)", tipo: "Conteo (12 meses)",
  },
  bloqueo_sostenido: {
    que: "De las normas del Ejecutivo que el Congreso desafió en el recinto en los últimos 12 meses (vetos cuya insistencia se votó y decretos sometidos a la ley 26.122), qué porcentaje sigue en pie.",
    aporta: "Es la cara ganada del pulso legislativo que el conteo de derrotas no registra: un gobierno sin mayoría gobierna sosteniendo sus vetos con un tercio de una cámara. Una tasa alta indica bloqueo firme; una baja, un Congreso capaz de voltear sus normas. Al mirar 12 meses atrás, una crisis reciente pesa durante un año.",
    frecuencia: "Continua (12 meses)", tipo: "Nivel (%)",
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
    que: "Cuánto suben en el mes los precios de alimentos y bebidas. En el índice de impacto social puntúa por el nivel acumulado del índice de alimentos relativo al índice de precios al consumidor (IPC) general, rebaseado a 100 = 4º trimestre de 2023: si supera 100, la comida subió menos que el resto de los precios desde el arranque del mandato (alivio relativo); si queda debajo, encarece por encima del promedio.",
    aporta: "Es la inflación más sensible socialmente: pega directo en la mesa de cada hogar, y castiga la canasta de los hogares de menores ingresos aunque la inflación general baje. Es una pregunta de precios pura, independiente del salario — el poder de compra lo mide la brecha salario/canasta, en Ingresos.",
    frecuencia: "Mensual", tipo: "Variación (tarjeta) · nivel frente al índice general de precios (índice)",
  },
  endeudamiento_familiar: {
    que: "Cuánto deben las familias por consumo (tarjetas + personales), en nivel de deuda real (descontada la inflación). Ya no puntúa en el índice de impacto social: salió del índice porque el stock de deuda por sí solo no distingue acceso al crédito de fragilidad. Se sigue relevando y su serie se publica.",
    aporta: "Mide el acceso al crédito de los hogares como stock puro, y esa es justamente su limitación: sin saber si esa deuda se puede pagar, más crédito no dice si es acceso o necesidad. Lo que quedó midiendo la dimensión de vulnerabilidad es la mora de esa cartera, que sí lo distingue.",
    frecuencia: "Mensual (unos 2 meses de rezago)", tipo: "Índice de deuda real (base 100)",
  },
  mora_familias: {
    que: "Qué porcentaje del crédito de consumo de las familias (préstamos personales y tarjetas) está en situación irregular — con atrasos de pago —, ponderado por el saldo de cada línea.",
    aporta: "Es la señal directa de estrés financiero de los hogares: la deuda puede crecer por acceso sano o por necesidad, pero la mora que se dispara solo tiene una lectura. Puntúa invertida: más mora, peor.",
    frecuencia: "Mensual (unos 2 meses de rezago)", tipo: "Nivel (%)",
  },
  icg_utdt: {
    que: "Cuánta confianza tiene la población en el Gobierno nacional, según la encuesta mensual de la Universidad Torcuato Di Tella. Promedia cinco atributos —imagen general, eficiencia en el gasto, honestidad, capacidad para resolver los problemas del país y si gobierna pensando en el interés general— en una escala de 0 a 5.",
    aporta: "Es la percepción política de los hogares: cuánto apoyo tiene disponible el Gobierno para sostener el rumbo mientras las condiciones materiales se acomodan. Completa con una opinión lo que el resto del índice mide con hechos.",
    frecuencia: "Mensual", tipo: "Índice (0-5)",
  },
  carga_servicio_deuda_hogares: {
    que: "Qué porcentaje de la masa salarial registrada destinan las familias al pago mensual de capital e intereses de sus deudas. El Banco Central calcula promedios de tres meses para el servicio de deuda y para la masa salarial.",
    aporta: "Mide capacidad comprometida antes de que aparezca el incumplimiento. Complementa a la mora: una observa la presión de pagos y la otra los atrasos ya materializados.",
    frecuencia: "Mensual (publicación semestral)", tipo: "Nivel (%)",
  },
  peso_tarifas: {
    que: "Qué porcentaje del salario registrado promedio (la remuneración imponible promedio de los trabajadores estables, RIPTE) cuesta la canasta mensual de electricidad, gas, agua y transporte de un hogar representativo del Área Metropolitana de Buenos Aires (AMBA).",
    aporta: "Mide directamente la asequibilidad de los servicios públicos y puntúa dentro de la dimensión de precios. Agua+energía y transporte se comparan por separado con referencias internacionales de 10% y 5% del ingreso; entra la mayor tensión para que un rubro caro no quede oculto por otro barato.",
    frecuencia: "Mensual", tipo: "Canasta de servicios / salario · ancla internacional",
  },
  pobreza_nowcast: {
    que: "El porcentaje de personas que viven en hogares urbanos pobres, estimado para el semestre móvil que termina en el mes del dato. No es la cifra oficial del Instituto Nacional de Estadística y Censos (INDEC), que se publica dos veces al año: es una proyección que se actualiza todos los meses.",
    aporta: "Permite seguir una estimación de pobreza entre publicaciones oficiales. Integra la dimensión de ingresos con signo invertido: más pobreza reduce el componente. Su peso efectivo se muestra en la composición del índice y no convierte la estimación en una medición oficial mensual.",
    frecuencia: "Mensual (semestre móvil)", tipo: "Estimación de terceros",
  },
  indice_lider: {
    que: "Un índice que combina señales tempranas de la economía —financieras, de expectativas y de actividad— para anticipar los cambios de rumbo antes de que aparezcan en los datos corrientes. Ya no puntúa en el índice de impacto social: salió del índice y pasó a ser el ancla externa contra la que se valida el índice macroeconómico.",
    aporta: "Mira hacia adelante, que es lo que ningún componente del cinturón hace: los demás describen lo que ya ocurrió. Por eso su lugar pasó a ser el de contraste externo — un índice líder que se da vuelta anticipa el punto de giro que la marcha de la actividad va a registrar meses después.",
    frecuencia: "Mensual", tipo: "Nivel (índice base 100)",
  },
  alquiler_real: {
    que: "Cuánto cuesta el alquiler de la vivienda en los contratos vigentes, descontado el aumento del resto de los precios y comparado con fines de 2023. La tarjeta es un índice donde 100 es el cuarto trimestre de 2023: por encima de 100, el alquiler se encareció en términos reales desde entonces; por debajo, se abarató. En el índice de impacto social puntúa con la misma cuenta al revés, de modo que más de 100 es alivio.",
    aporta: "La desregulación del mercado de alquileres fue uno de los cambios de política más visibles del período, y el costo de la vivienda golpea sobre todo a los hogares inquilinos urbanos — un gasto fijo que ningún otro componente del cinturón captura.",
    frecuencia: "Mensual", tipo: "Nivel real (índice, fines de 2023 = 100)",
  },
  alquiler_udesa_real: {
    que: "Cuánto cuesta alquilar un departamento en el Área Metropolitana de Buenos Aires según los avisos de Mercado Libre, descontado el aumento de los precios y comparado con fines de 2023. La tarjeta es un índice donde 100 es el cuarto trimestre de 2023: por debajo de 100, el alquiler pedido es más barato en términos reales que entonces. La fuente no publica niveles: es una reconstrucción de CIGOB a partir de las variaciones que informa. En el índice de impacto social puntúa al revés, de modo que más de 100 es alivio.",
    aporta: "El índice de precios al consumidor mide el alquiler de los contratos vigentes, que se ajustan con rezago; los avisos muestran lo que piden quienes ofrecen un departamento para alquilar. Es el costo al que se enfrenta quien se muda, el que más pesa en una decisión de vivienda.",
    frecuencia: "Mensual (carga manual)", tipo: "Nivel real reconstruido (índice, fines de 2023 = 100)",
  },
  consumo_carne_vacuna: {
    que: "Consumo aparente de carne vacuna por habitante, en promedio móvil de doce meses, según la Secretaría de Agricultura, Ganadería y Pesca. Son kilos de carne, no gramos de proteína ni una encuesta de ingesta de los hogares. Puntúa por separado, como corte aspiracional del consumo argentino.",
    aporta: "Mide específicamente la carne vacuna, que es la que el consumo aparente argentino trata como aspiracional y la que más cae. El titular, el gráfico y el puntaje usan el mismo dato: el titular en kilos y el gráfico y el puntaje comparados con fines de 2023.",
    frecuencia: "Mensual (unos 2 meses de rezago)", tipo: "Nivel (kg por habitante) · índice base-100 en el gráfico",
  },
  consumo_carnes_total: {
    que: "Consumo aparente por habitante de carne vacuna, aviar y porcina, en promedio móvil de doce meses, según la Secretaría de Agricultura, Ganadería y Pesca. Son kilos de carne, no gramos de proteína ni una encuesta de ingesta de los hogares.",
    aporta: "La suma y el desglose muestran la evolución agregada de las tres carnes, sin identificar sustituciones dentro de los mismos hogares. El titular, el gráfico y el puntaje usan el mismo dato: el titular en kilos y el gráfico y el puntaje comparados con fines de 2023.",
    frecuencia: "Mensual (unos 2 meses de rezago)", tipo: "Nivel (kg por habitante) · índice base-100 en el gráfico",
  },
  consumo_carnes_otras: {
    que: "Consumo aparente por habitante de carne aviar y porcina combinadas, en promedio móvil de doce meses, según la Secretaría de Agricultura, Ganadería y Pesca. Puntúa junto con el consumo de carne vacuna, en reemplazo del compuesto único de las tres carnes: separadas, una cae mientras la otra puede sostenerse o subir por sustitución.",
    aporta: "Complementa a la vacuna: si sube mientras la vacuna cae, describe sustitución hacia pollo y cerdo, no necesariamente menos proteína en total. El titular, el gráfico y el puntaje usan el mismo dato: el titular en kilos y el gráfico y el puntaje comparados con fines de 2023.",
    frecuencia: "Mensual (unos 2 meses de rezago)", tipo: "Nivel (kg por habitante) · índice base-100 en el gráfico",
  },
  ocupacion_eph: {
    que: "Cuánto más alto o más bajo está el porcentaje de la población que tiene empleo (tasa de empleo) que en el mismo trimestre de 2023, antes del mandato, según la Encuesta Permanente de Hogares continua del Instituto Nacional de Estadística y Censos (INDEC) en los 31 aglomerados urbanos. Se muestra en puntos porcentuales.",
    aporta: "Es el principal componente de la dimensión de empleo del índice de impacto social: dice si en el último trimestre publicado trabaja más o menos gente que cuando empezó el Gobierno, sea o no en empleo registrado. Se compara el mismo trimestre porque la encuesta no está desestacionalizada. La tasa se mueve poco, así que cada décima de punto cuenta. No distingue la calidad del empleo.",
    frecuencia: "Trimestral (unos 80 días de rezago)", tipo: "Diferencia contra 2023 (puntos porcentuales)",
  },
  informalidad: {
    que: "Qué porcentaje de los asalariados trabaja sin descuento jubilatorio y sin pagarse los aportes por su cuenta (empleo en negro), según la Encuesta Permanente de Hogares, trimestral, del Instituto Nacional de Estadística y Censos (INDEC). El asalariado que no tiene descuento pero se paga sus aportes, por ejemplo con monotributo, no cuenta como informal.",
    aporta: "Mide la precariedad laboral y la exclusión de la red de protección social. Es la definición que el INDEC publica desde el cuarto trimestre de 2023, cuando cambió el cuestionario. En el índice de impacto social su base es el 4º trimestre de 2023 exacto (el trimestre de arranque del mandato).",
    frecuencia: "Trimestral (encuesta de hogares)", tipo: "Nivel (%)",
  },
  trabajo_independiente: {
    que: "Qué proporción del empleo registrado son trabajadores independientes —autónomos y monotributistas— frente a los asalariados. En el índice de impacto social puntúa invertida: más peso independiente es peor.",
    aporta: "Describe la composición del empleo registrado, excluido el monotributo social. Puede aumentar porque crecen los independientes o porque caen los asalariados. Complementa el número de empleadores, pero no permite identificar si quienes perdieron un empleo pasaron a facturar por su cuenta. El signo invertido expresa el criterio del monitor sobre protección laboral; no mide la calidad de cada trabajo independiente. NO puntúa: salió del índice de impacto social en octubre de 2026 y se sigue relevando como archivo.",
    frecuencia: "Mensual (unos 3 meses de rezago)", tipo: "Participación (%)",
  },
  mortalidad_pymes: {
    que: "Cuántos empleadores con nóminas de 1 a 50 trabajadores tienen cobertura de una aseguradora de riesgos del trabajo. En el índice de impacto social puntúa por el nivel rebaseado a 100 = 4º trimestre de 2023: menos empleadores es peor.",
    aporta: "Observa la cantidad de empleadores dentro de ese universo. Una baja puede corresponder a un cierre, a dejar de tener personal declarado o a superar los 50 trabajadores; una entrada puede provenir de una empresa que reduce su nómina. La serie agregada no separa esos movimientos ni acredita quiebras. NO puntúa: salió del índice de impacto social en octubre de 2026 y se sigue relevando como archivo.",
    frecuencia: "Mensual (unos 3 meses de rezago)", tipo: "Cantidad de empleadores",
  },
  despacho_cemento: {
    que: "Nivel de actividad de la construcción medido por el indicador sintético de la actividad de la construcción (ISAC), desestacionalizado, del Instituto Nacional de Estadística y Censos (INDEC). La clave interna conserva un nombre histórico, pero la observación no es el despacho de cemento.",
    aporta: "Termómetro de la obra pública y privada, sensible al ciclo económico. NO puntúa: salió del índice de impacto social en octubre de 2026 y se sigue relevando como archivo.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  subocupacion_demandante: {
    que: "Qué porcentaje de la población económicamente activa (PEA) trabaja menos horas de las que quisiera y además está buscando otro empleo. Es la tasa de subocupación demandante de la Encuesta Permanente de Hogares (EPH), y el Instituto Nacional de Estadística y Censos (INDEC) la calcula sobre la PEA —no sobre los ocupados—, que es lo que la vuelve comparable con la tasa de desocupación.",
    aporta: "Señala empleo insuficiente: gente que ya tiene trabajo y sale igual a buscar más horas. Es la presión sobre el mercado laboral que la desocupación no ve, porque a estas personas las cuenta como ocupadas. NO puntúa: salió del índice de impacto social en octubre de 2026 y se sigue relevando como archivo.",
    frecuencia: "Trimestral", tipo: "Nivel (%)",
  },
  inseguridad: {
    que: "Qué porcentaje de los hogares sufrió al menos un delito en los últimos 12 meses, según la encuesta mensual de victimización del Laboratorio de Investigaciones sobre Crimen, Instituciones y Políticas de la Universidad Torcuato Di Tella, en 40 centros urbanos.",
    aporta: "Recoge hechos de victimización declarados por los hogares, incluidos casos no denunciados. Sigue sujeto a cobertura, recuerdo y error muestral de la encuesta. Comparte dimensión con las tasas de homicidios y de robos del Sistema Nacional de Información Criminal: son complementarios, no redundantes — este capta la cifra negra pero no distingue tipo de delito.",
    frecuencia: "Mensual (encuesta)", tipo: "Nivel (%)",
  },
  tasa_homicidios: {
    que: "Homicidios dolosos cada 100.000 habitantes, tasa ya calculada por el Sistema Nacional de Información Criminal (SNIC) del Ministerio de Seguridad sobre su registro anual de denuncias, serie oficial 2000-2025.",
    aporta: "Es el tipo de delito con menos subregistro del desglose —hay un cuerpo, así que casi no depende de que alguien denuncie— y complementa al índice de victimización de la Universidad Torcuato Di Tella, que es mensual pero no distingue tipo de delito. Es anual, con unos 8,5 meses de rezago desde el cierre del año.",
    frecuencia: "Anual (unos 8,5 meses de rezago)", tipo: "Tasa cada 100.000 habitantes · índice base-100 en el gráfico",
  },
  tasa_robos: {
    que: "Robos que excluyen los agravados por lesiones o muertes, cada 100.000 habitantes, tasa ya calculada por el Sistema Nacional de Información Criminal (SNIC). Es el equivalente del SNIC a lo que suele llamarse «rapiña».",
    aporta: "A diferencia de los homicidios, depende de que la víctima denuncie. La tasa 2025 (778,1) cae 22,4% contra 2024 sin un evento conocido que lo explique, y el patrón —Hurtos cae parecido mientras Robos agravados sube el mismo año— no se pudo confirmar ni descartar contra un informe metodológico público del Sistema Nacional de Información Criminal: se publica el dato oficial con esta limitación declarada.",
    frecuencia: "Anual (unos 8,5 meses de rezago)", tipo: "Tasa cada 100.000 habitantes · índice base-100 en el gráfico",
  },
  icc_utdt: {
    que: "El optimismo de la gente sobre la economía y sus finanzas personales (Índice de Confianza del Consumidor de la Universidad Torcuato Di Tella). Ya no puntúa en el índice de impacto social: salió del índice porque un indicador no puede ser componente y juez del mismo índice a la vez. Pasó a ser el ancla de validación externa del índice de impacto social —el mismo rol que cumple el Índice Líder para el índice macroeconómico—, así que ahora se lo contrasta contra el índice en vez de promediarse adentro.",
    aporta: "Describe percepciones y expectativas económicas de los encuestados, y sirve para leer si la percepción sigue a las condiciones materiales que mide el índice de impacto social. No mide intención de voto ni demuestra por sí solo capacidad de anticipar consumo o resultados electorales.",
    frecuencia: "Mensual", tipo: "Índice",
  },
  sentimiento_digital: {
    que: "Cuánta atención pública se llevan seis problemas, medida por lo que se busca en internet: inflación, precios, dólar, empleo, inseguridad y corrupción. Ya no puntúa en el índice de impacto social: salió del índice porque el volumen de búsquedas no distingue si un tema preocupa o alegra, y la validación externa dio el signo contrario al esperado. Se sigue relevando y su serie se publica.",
    aporta: "Describe atención relativa a seis términos de búsqueda. El volumen no revela si la búsqueda expresa preocupación, interés o una valoración positiva; por eso permanece fuera del índice. Un aumento de búsquedas sobre corrupción tampoco mide directamente su incidencia.",
    frecuencia: "Mensual", tipo: "Índice (100 = 4º trimestre de 2023)",
  },
  motorizacion_total: {
    que: "Cuántos vehículos 0 kilómetro —autos y motos sumados— se incorporan por cada mil habitantes en una ventana móvil de doce meses. En el índice de impacto social se compara contra el promedio del 4º trimestre de 2023.",
    aporta: "Mide patentamientos totales por habitante y muestra la composición entre autos y motos. Es un proxy de consumo durable: el registro no distingue primeras compras, reposición, flotas ni sustitución entre vehículos de un mismo hogar.",
    frecuencia: "Mensual (primeros días del mes siguiente)", tipo: "Nivel per cápita · índice base-100 en el gráfico",
  },
  ratio_motos_autos: {
    que: "Cuántas motos se patentan por cada auto patentado, en la misma ventana móvil de doce meses que la motorización total. Puntúa invertido: más motos por auto es deterioro.",
    aporta: "Aísla la composición del flujo de patentamientos que la motorización total mide en nivel: un total que crece mientras este ratio también sube dice que el crecimiento viene de la moto —el vehículo más barato— y no de una mejora pareja. La polaridad es una decisión de contenido, no un hecho aritmético.",
    frecuencia: "Mensual (primeros días del mes siguiente)", tipo: "Cociente (motos/auto) · índice base-100 en el gráfico",
  },
  patentamiento_motos: {
    que: "Cuántas motos se patentan en el mes.",
    aporta: "Proxy de consumo durable de los sectores medios y bajos.",
    frecuencia: "Mensual", tipo: "Conteo",
  },
  patentamiento_autos: {
    que: "Inscripciones iniciales de autos 0 kilómetro. Se conserva como desglose: el componente que puntúa es la motorización total por habitante, que suma autos y motos.",
    aporta: "Permite observar el volumen y la composición de los patentamientos. No identifica primeras compras, reposición, flotas ni sustitución entre vehículos de un mismo hogar.",
    frecuencia: "Mensual (el mes se publica en los primeros días del siguiente)", tipo: "Conteo",
  },
  consumo_supermercados: {
    que: "Cuánto compra la gente en los supermercados una vez descontada la inflación: el índice de ventas a precios constantes que publica el Instituto Nacional de Estadística y Censos (INDEC) en su serie desestacionalizada. En el índice de impacto social puntúa rebaseado a 100 = 4º trimestre de 2023.",
    aporta: "Mide ventas reales de los supermercados relevados. Complementa ingresos, precios y otros consumos; no cubre toda la compra de alimentos ni el comercio minorista. Los cambios de canal de compra también pueden mover la serie.",
    frecuencia: "Mensual (el Instituto Nacional de Estadística y Censos lo publica unos dos meses después del mes de referencia)", tipo: "Índice",
  },

  // ── Espíritu de época (el humor social) ─────────────────────────
  clima_electoral: {
    que: "La ventaja del oficialismo sobre el principal opositor (La Libertad Avanza menos el Partido Justicialista) en el promedio ponderado de encuestas.",
    aporta: "Proxy de la adhesión política al proyecto de gobierno: cuando el humor social acompaña, la ventaja se sostiene.",
    frecuencia: "Continua", tipo: "Brecha (puntos porcentuales)",
  },
  indice_intencion_migratoria: {
    que: "Cuánto se busca en internet sobre emigrar de Argentina (por ejemplo \"emigrar de argentina\", \"vivir en el exterior\").",
    aporta: "Es una señal más estructural que el sentimiento digital: no mide urgencia del momento, sino gente que dejó de creer en un cambio dentro del país. Es un proxy de atención, no de flujo migratorio real; por eso su tarjeta lo acompaña con la migración efectiva hacia los destinos principales, como contraste.",
    frecuencia: "Mensual", tipo: "Índice (0–100)",
  },

  // ── Gestión (la capacidad de ejecutar) ──────────────────────────
  cepo_mulc: {
    que: "Cuánto se separa el dólar financiero (contado con liquidación) del dólar mayorista de referencia: la brecha cambiaria.",
    aporta: "Es una señal del resultado de la normalización cambiaria, no del desarme del cepo en sí: la brecha puede ser baja con restricciones vigentes y moverse por tasas o elecciones sin que cambie ninguna norma. Las cotizaciones del día salen de dolarapi.com, un servicio privado que replica las del mercado; el mayorista es el de referencia del Banco Central. La historia mensual usa el promedio del contado con liquidación de ArgentinaDatos, del mismo proyecto, sobre el promedio del mayorista que publica el Banco Central.",
    frecuencia: "Diaria", tipo: "Brecha (%)",
  },
  privatizaciones: {
    que: "Cuánto avanza la privatización de la cartera de empresas públicas habilitada por la Ley Bases, medida por etapas verificables: 0 sin definir · 1 preparatoria · 2 pliegos · 3 licitación/adjudicación · 4 operación cerrada.",
    aporta: "Describe el avance documentado de cada proceso: una operación cerrada recibe etapa 4 y los pliegos etapa 2. Las empresas pesan igual; el promedio no mide valor de activos vendido ni dinero cobrado. Corredores Viales no integra la cartera: la concesión de la red vial la mide el indicador de concesiones de infraestructura. Se mantiene mediante curaduría de normas y comunicaciones primarias; una revisión parcial o una búsqueda sin novedades no certifica exhaustividad.",
    frecuencia: "Quincenal prevista (curaduría)", tipo: "Avance por etapas",
  },
  concesiones_infraestructura: {
    que: "Qué porcentaje de los kilómetros del plan de la Red Federal de Concesiones ya está adjudicado: el estado de cada etapa sale de las resoluciones de adjudicación del Boletín Oficial (el sistema de contrataciones del Estado, CONTRAT.AR, se usa para detectar procesos nuevos) y el kilometraje por tramo de la página oficial de la Red Federal de Concesiones (16 tramos, unos 9.100 km en 4 etapas).",
    aporta: "Mide con actos administrativos —no anuncios— si el traspaso de la red vial al sector privado avanza: una etapa cuenta recién cuando su resolución de adjudicación está publicada en el Boletín Oficial; que el sistema de contrataciones la muestre adjudicada no alcanza (sólo avisa). El 100% quiere decir que todo lo licitado está adjudicado, no que la red esté concesionada ni operando: las cuatro etapas suman cerca del 23% de la red vial nacional, y a octubre de 2026 la toma de posesión consta en 7.843 de sus 9.091 km (la de dos tramos de la Etapa II-B, Puntano y Portuario Norte, no pudo confirmarse en fuente oficial).",
    frecuencia: "Diaria (Boletín Oficial)", tipo: "Avance de reforma",
  },
  reduccion_estado: {
    que: "Cuánto varía la dotación de personal de la Administración Pública Nacional respecto de diciembre de 2023 (inicio del mandato), según la serie mensual oficial del Instituto Nacional de Estadística y Censos (INDEC).",
    aporta: "La métrica insignia de la reforma del Estado: personas, no pesos. Universo: Administración Pública Nacional — incluye fuerzas armadas y de seguridad (alrededor del 10% de la dotación) y no incluye empresas del Estado ni provincias/municipios.",
    frecuencia: "Mensual", tipo: "Variación frente a diciembre de 2023",
  },
  reestructuracion_organismos: {
    que: "Cuántos organismos públicos se disolvieron o cerraron desde diciembre de 2023, con ese cierre todavía vigente. Ya no puntúa en el índice de gestión: salió del índice porque el porcentaje dividía normas por una meta documental —dos unidades distintas— y el buscador se salteaba cierres conocidos. Se sigue relevando como inventario.",
    aporta: "Mide el avance concreto de la reforma del aparato estatal por la vía más dura y verificable: el cierre. No cuenta fusiones, transformaciones ni reorganizaciones que no impliquen disolver un organismo — esas son difíciles de verificar caso por caso y quedan fuera de lo que este indicador afirma medir. Tampoco cuenta un hallazgo de la búsqueda que, revisado caso por caso, resultó ajeno a un organismo público o fue revertido después: cada norma se contrasta contra un registro curado antes de sumar.",
    frecuencia: "Mensual", tipo: "Avance de reforma",
  },
  rigi_inversiones: {
    que: "Cuánto de la inversión del Régimen de Incentivo a Grandes Inversiones (RIGI) ya está aprobada: el monto aprobado por resolución sobre el total de la cartera (aprobados + en evaluación).",
    aporta: "Mide decisiones administrativas de aprobación, con la plataforma oficial del Ministerio de Economía: no cuánto se invirtió efectivamente ni cuánto avanzaron los proyectos, porque no hay una serie pública de inversión ejecutada. Como el total incluye lo que está en evaluación, el porcentaje baja cuando entran proyectos nuevos aunque no se haya rechazado ninguno; y como casi todo lo presentado termina aprobado, mide sobre todo la demora en aprobar. La evolución histórica grafica la inversión aprobada acumulada en dólares.",
    frecuencia: "Continua (plataforma oficial)", tipo: "Avance de reforma",
  },
  desregulacion_normativa: {
    que: "Cuántos artículos de normas quedaron modificados o eliminados por el programa desregulador desde el 10 de diciembre de 2023, según el conteo oficial del Ministerio de Desregulación y Transformación del Estado, que es el mismo que ejecuta el programa.",
    aporta: "Mide el volumen de intervención normativa, no la importancia ni la efectividad de cada cambio: un artículo menor cuenta igual que uno que transforma un régimen completo. Tampoco cuenta actos administrativos firmados. La diferencia importa: un decreto que reescribe quinientos artículos y una resolución que toca uno pesan igual si se cuentan normas, y muy distinto si se cuentan artículos. Lo que el recuento no distingue es si lo derogado dejó de regir: un artículo que la Justicia repuso suma igual que uno vigente, de modo que el indicador mide el acto de desregular y no su efecto. Muestra además la forma del programa en el tiempo, que es muy desigual: un arranque acotado, un salto marcado a partir de la Ley Bases y la creación del ministerio, y una aceleración durante 2026. La tarjeta publica también las otras dos cifras del mismo informe: cuántas normas de desregulación se dictaron y cuántas normas anteriores alcanzaron.",
    frecuencia: "Mensual", tipo: "Conteo acumulado oficial",
  },
  apertura_comercial: {
    que: "La recaudación de derechos de importación, exportación y tasa de estadística que cobra la Agencia de Recaudación y Control Aduanero, por cada dólar de intercambio (exportaciones más importaciones, según el Intercambio Comercial Argentino que publica el Instituto Nacional de Estadística y Censos). Es una aproximación a la carga tributaria efectiva; también depende de la composición del comercio y de los momentos de pago.",
    aporta: "Aproxima la carga tributaria sobre el intercambio. Una baja del cociente puede acompañar una reducción de impuestos, pero también responder a cambios en la composición o valoración del comercio y en los pagos. No identifica por sí sola el desmantelamiento de barreras comerciales. La brecha cambiaria se mide aparte.",
    frecuencia: "Mensual", tipo: "Nivel (%)",
  },
  credito_privado: {
    que: "Cuánto crecen los préstamos en pesos al sector privado en términos reales (contra un año atrás, descontada la inflación).",
    aporta: "Es el crédito que efectivamente se dio y complementa a la capacidad prestable: si los bancos tienen margen pero el crédito real no crece, el financiamiento no está llegando a la economía.",
    frecuencia: "Mensual", tipo: "Variación real",
  },
  resultado_primario: {
    que: "Cuánto le sobra (o le falta) al Estado nacional después de pagar todo su gasto, antes de los intereses de la deuda, acumulado en doce meses y medido como porcentaje de lo que recauda.",
    aporta: "Es el resultado fiscal, no los ingresos. La recaudación puede caer porque la actividad afloja o porque se bajaron impuestos a propósito, y en ninguno de los dos casos eso dice si las cuentas cierran. Este indicador responde esa pregunta directamente: de cada cien pesos recaudados, cuántos quedan (la recaudación es la total de la Nación: incluye los aportes a la seguridad social y la parte que se coparticipa a las provincias). Se mide sobre la recaudación y no sobre el producto porque es un dato mensual que no espera al producto bruto interno (PBI); como referencia, un 6 % de la recaudación equivale aproximadamente a 1,5 % del PBI. No incluye los intereses: el resultado con intereses (financiero) puede ser menor.",
    frecuencia: "Mensual", tipo: "Resultado fiscal",
  },
  costo_financiamiento_tesoro: {
    que: "Qué tasa de interés real paga el Tesoro para renovar su deuda en pesos: la tasa efectiva anual de las licitaciones del mes, descontada la inflación esperada.",
    aporta: "Es el precio del financiamiento del Estado. Capacidad prestable y crédito miden cuánta financiación hay; esta mide cuánto cuesta conseguirla. Los dos extremos son malos: una tasa real muy negativa indica que el Tesoro coloca licuando al ahorrista, y una muy alta que la deuda crece más rápido que la economía.",
    frecuencia: "Mensual (licitaciones)", tipo: "Tasa real",
  },
  gasto_funcionamiento: {
    que: "Cuánto varía en términos reales el gasto de funcionamiento del Estado nacional —salarios y otros gastos de funcionamiento—: el promedio de los últimos doce meses contra el promedio mensual de 2023, el año anterior al mandato.",
    aporta: "La magnitud fiscal del aparato administrativo, aislada de la inflación: distingue el achicamiento del Estado de la mera licuación nominal. Incluye las remuneraciones. Un puntaje de 100 quiere decir que alcanzó la referencia fijada, no que la reforma del Estado esté terminada.",
    frecuencia: "Mensual", tipo: "Variación real",
  },
  masa_salarial: {
    que: "Cuánto varía en términos reales la masa salarial del personal del Estado nacional respecto de 2023.",
    aporta: "Filtra el efecto de la inflación sobre plantas nominales: complementa a la dotación (personas) con el costo salarial real.",
    frecuencia: "Mensual", tipo: "Variación real",
  },
  asistencia_directa: {
    que: "Si los planes sociales siguen pasando por intermediarios: vale 100 desde que la Resolución 84/2024 del Ministerio de Capital Humano dispuso el cese de las unidades de gestión y de certificación del Potenciar Trabajo (10 de abril de 2024), y 0 antes.",
    aporta: "Mide lo que el compromiso prometía cambiar. La intermediación no estaba en la clasificación del gasto —en 2023 el 98,3% del devengado ya figuraba como ayudas a personas—, sino en las unidades de gestión: municipios, cooperativas y organizaciones que certificaban la contraprestación y manejaban la lista. Es un acto, no un resultado: no acredita cómo se paga cada prestación ni que no quede intermediación informal.",
    frecuencia: "Por acto (Boletín Oficial)", tipo: "Hito de reforma",
  },
  fal_modernizacion_laboral: {
    que: "Cuánto avanzó la puesta en marcha del Fondo de Asistencia Laboral —el mecanismo con el que la Ley de Modernización Laboral financia las indemnizaciones por despido—. Cinco hitos de construcción valen 18 puntos cada uno: la Ley 27.802, el Decreto 408/2026 que la reglamenta, la resolución de la Comisión Nacional de Valores que reglamenta sus fondos de inversión, la de la Agencia de Recaudación y Control Aduanero que regula los aportes, y la oferta del producto por los bancos. El 10 % restante llega con el primer fondo inscripto en la Comisión Nacional de Valores.",
    aporta: "Sigue la construcción del régimen paso a paso con normas y hechos fechados, que se muestran en el detalle. La ley y el decreto cuentan sólo si no están suspendidos por la Justicia. Que el régimen esté armado no dice cuántas empresas lo usan: eso recién se puede ver desde el 1 de diciembre de 2026, cuando entra en vigencia (Decreto 1228/2026). El avance (0–100) y el puntaje para el índice son dos números distintos: el puntaje sale de pasar el avance por las anclas de la ficha.",
    frecuencia: "Mensual", tipo: "Avance de puesta en marcha (0–100)",
  },
  libertad_opcion_salud: {
    que: "Cuánto avanzó la implementación de la libre elección de cobertura de salud: que los trabajadores puedan elegir entre obras sociales y prepagas, sin permanencias ni intermediarios obligatorios. Se mide por cinco hitos: el marco normativo que habilita la elección (decreto de necesidad y urgencia 70/2023, 25 puntos), el fin de la permanencia obligatoria inicial (Decreto 170/2024, 20), la derivación directa de aportes a las prepagas (Resolución 3284/2024 de la Superintendencia de Servicios de Salud, 20), el trámite de cambio en línea (diciembre de 2024, 20) y el funcionamiento verificado en el padrón de la Superintendencia (15).",
    aporta: "Evalúa lo que depende del Gobierno: que la elección esté habilitada y funcione. No cuenta cuántas personas se cambian, porque quedarse en la cobertura actual también es elegir. Como dato de contexto, la tarjeta muestra qué parte de los usuarios de prepagas tiene sus aportes derivados directo. Con los hitos cumplidos el puntaje queda alto y estable: es una promesa cumplida, no un indicador de variación.",
    frecuencia: "Mensual (padrón) · por acto (normas)", tipo: "Avance de reforma (hitos)",
  },
  protocolo_antipiquetes: {
    que: "En qué porcentaje se redujo el número de cortes por manifestación relevados en la Ciudad de Buenos Aires respecto de una base estimada para 2023.",
    aporta: "Describe la evolución de los cortes registrados por Diagnóstico Político, una consultora privada que no publica sus microdatos; el último dato es el del año 2025. El protocolo está vigente: un juez lo anuló en diciembre de 2025, la Cámara en lo Contencioso Administrativo Federal revocó esa nulidad en marzo de 2026 y el caso espera a la Corte Suprema (verificado en octubre de 2026). Mide resultados observados, no la aplicación del protocolo: no hay una serie pública de cuántas veces se aplicó. La reducción no identifica por sí sola el efecto del protocolo ni permite atribuirla exclusivamente al Gobierno nacional. Tampoco mide toda la protesta social; el detalle y la ficha informan las limitaciones de actualización de la fuente.",
    frecuencia: "Anual", tipo: "Variación frente a la base 2023",
  },
  litigiosidad_laboral: {
    que: "Cuánto varían los juicios laborales del sistema de riesgos del trabajo, según la Superintendencia de Riesgos del Trabajo (SRT): acumulado de los últimos 12 meses contra los 12 previos.",
    aporta: "Aporta la evolución de litigios por riesgos del trabajo. Desde octubre de 2026 no integra el índice: lo reemplaza la siniestralidad laboral registrada. Se sigue calculando.",
    frecuencia: "Mensual (unos 3 meses de rezago; julio cae todos los años por la feria judicial)", tipo: "Variación en 12 meses",
  },
  siniestralidad_laboral: {
    que: "Cuánto varía la siniestralidad registrada en el sistema de riesgos del trabajo: los accidentes de trabajo y enfermedades profesionales con días de baja o secuelas incapacitantes, por cada mil personas trabajadoras cubiertas, en todo el país. Compara lo que va del año con el mismo período del año anterior, según los informes de la Superintendencia de Riesgos del Trabajo (SRT).",
    aporta: "Es la lectura de cuántos accidentes y enfermedades registra el sistema de riesgos del trabajo: si bajan los siniestros por trabajador cubierto, el sistema registra menos. Dice cuánto cambió, no por qué: no se atribuye a ninguna reforma sus subas o bajas, que dependen también del empleo, de la actividad y de cuánto se denuncia. Los informes provisorios pueden revisarse al consolidarse.",
    frecuencia: "Trimestral (el informe sale unos tres meses después del cierre del período)", tipo: "Variación interanual del período acumulado",
  },
  juicios_trabajo_capital: {
    que: "Cuánto varían los juicios laborales que se inician en la Justicia Nacional del Trabajo, que atiende la Capital: los entrados en primera instancia en los últimos 12 meses contra los 12 previos, según la Oficina de Estadísticas del Consejo de la Magistratura.",
    aporta: "Cuenta todos los juicios laborales —despidos, diferencias salariales, accidentes—, pero sólo los de la Capital. Lo pidió la auditoría de CiGob. Describe la evolución de los juicios y no atribuye a la reforma sus subas o bajas.",
    frecuencia: "Semestral (el 2º semestre sale hacia mayo del año siguiente)", tipo: "Variación en 12 meses",
  },
  alertas_manifestacion: {
    que: "Cuántas alertas de manifestación únicas reportaron los feeds en tiempo real del transporte porteño (colectivos y subtes) durante el mes.",
    aporta: "Serie propia en construcción (acumula desde julio de 2026, muestreada varias veces por día): cuando tenga historia suficiente será la base automatizable del indicador de orden público. Sin línea base 2023 — el registro histórico oficial de cortes fue dado de baja.",
    frecuencia: "Continua (muestreo 3 veces por día)", tipo: "Conteo mensual",
  },
  protestas_caba: {
    que: "Cuántos eventos de protesta (marchas, concentraciones, disturbios) registró Armed Conflict Location & Event Data (ACLED) en la Ciudad de Buenos Aires en los últimos 12 meses, con serie semanal desde 2018.",
    aporta: "Complementa el conteo de cortes con eventos de protesta registrados por el relevamiento internacional Armed Conflict Location & Event Data (ACLED) a partir de fuentes públicas. Son universos y métodos distintos: una divergencia entre las series no demuestra que las mismas protestas se hayan transformado en marchas sin corte ni identifica el efecto del protocolo. La cobertura informativa condiciona qué eventos se registran.",
    frecuencia: "Semanal", tipo: "Conteo (12 meses)",
  },
};

// Qué mide cada DIMENSIÓN de los índices paramétricos (modal de dimensión).
// Claves únicas entre ITCM/ITCG/ITCIS.
export const DIM_DESCRIPCIONES: Record<string, string> = {
  // ITCM
  estabilidad_monetaria: "La estabilidad de la moneda desde cuatro señales complementarias: la inflación actual, según el índice de precios al consumidor; la esperada por el mercado, según el Relevamiento de Expectativas de Mercado del Banco Central; la presión por salir del peso, observada según el régimen cambiario vigente, y las reservas netas del Banco Central, los dólares propios con que respalda la moneda. Las reservas estaban en el sector externo hasta octubre de 2026 y pasaron acá con el mismo peso en el índice. La brecha de crecimiento real entre el agregado amplio y el transaccional acompañaba como otra señal hasta agosto de 2026: se sigue calculando fuera del índice, porque su banda afirmaba una dirección que ninguna referencia externa pudo firmar.",
  cuentas_fiscales: "Si las cuentas del Estado cierran: el resultado primario sobre lo recaudado y la recaudación real. El resultado primario responde la pregunta de frente —de cada cien pesos recaudados por la Nación (total, incluida la seguridad social y lo coparticipado), cuántos quedan después de pagar el gasto y antes de los intereses—; la recaudación real mide la base imponible, es decir, cuánta actividad formal sostiene los ingresos. Hasta octubre de 2026 esta dimensión incluía también el saldo comercial, que ahora está en el sector externo.",
  financiamiento: "Si hay combustible para la economía y a qué precio: capacidad prestable del sistema financiero, crédito real otorgado y el costo del Tesoro. Las dos primeras miden cuánta financiación hay —lo que el sistema puede prestar y lo que efectivamente prestó—; la tasa real que el Tesoro paga para renovar su deuda en pesos mide cuánto cuesta conseguirla. Hasta octubre de 2026 incluía también las reservas netas, que ahora están en el sector externo.",
  actividad: "Si la economía crece y si alguien apuesta al futuro: el estimador mensual de actividad económica (EMAE) interanual, cuántos de sus quince sectores crecen, la producción industrial manufacturera y la inversión física —construcción y bienes de capital—. El EMAE da el pulso general y su apertura sectorial distingue un crecimiento generalizado de uno concentrado en pocos sectores; la industria aporta una fuente distinta, para que la dimensión no cuelgue de un solo dato. La recaudación del impuesto al valor agregado y del impuesto al cheque salió en octubre de 2026: repetía la lectura del estimador mensual de actividad económica. La inversión física mira lo que viene: actividad que crece sin inversión es recuperación con techo cercano. Hasta octubre de 2026 la inversión era una dimensión aparte.",
  sector_externo: "Qué tan holgada está la economía frente al resto del mundo: el saldo comercial de los últimos doce meses y la competitividad del tipo de cambio (las reservas netas del Banco Central se leen, desde octubre de 2026, en la estabilidad monetaria). La competitividad no es un promedio de dos datos sino su cruce: el tipo de cambio real multilateral oficial del Banco Central con los términos del intercambio del Instituto Nacional de Estadística y Censos (precios de exportación sobre precios de importación) dicen si el peso alcanza para competir y si ese nivel se sostiene. Cada combinación tiene su puntaje (peso competitivo con términos altos 85 · competitivo con términos bajos 50 · apreciado con términos altos 30 · apreciado con términos bajos 10), y entre esas esquinas se interpola.",
  // ITCG
  reformas_economicas: "El corazón de la promesa económica: la normalización cambiaria, vista en la brecha entre el dólar financiero y el oficial; la carga de impuestos sobre el comercio exterior, y la desregulación normativa.",
  reforma_estado: "El achicamiento del Estado en dos medidas que se controlan entre sí: la dotación de personal, que cuenta gente, y el gasto de funcionamiento real, que cuenta pesos a precios constantes. El avance de reestructuración de organismos salió del índice en agosto de 2026 —dividía normas por una meta documental, dos unidades distintas— y se sigue relevando como inventario. El puntaje máximo refleja el cumplimiento de las referencias fijadas para esas dos variables; no implica que se haya completado la reforma y transformación del Estado. La de dotación es la meta de recortar otro 10% de la planta en 2026, que informó la prensa citando fuentes oficiales (el Gobierno no publicó un número); la de gasto de funcionamiento es una referencia propia, porque no hay meta oficial con la que compararlo.",
  reforma_laboral: "Combina las etapas del Fondo de Asistencia Laboral (la mitad de la dimensión) con la siniestralidad laboral registrada en el sistema de riesgos del trabajo (un cuarto: accidentes y enfermedades con días de baja, en todo el país) y con los juicios que se inician en la Justicia Nacional del Trabajo de la Capital (otro cuarto, despidos incluidos). Ni la siniestralidad ni los juicios permiten atribuir sus variaciones a la reforma.",
  privatizaciones_inversion: "Los activos del Estado y la inversión privada grande: privatizaciones, cartera del Régimen de Incentivo para Grandes Inversiones (RIGI) y concesiones viales.",
  social_orden: "Reúne el cese de los intermediarios en los planes sociales, la evolución de los cortes por protesta en la Ciudad de Buenos Aires y la implementación de la libre elección de cobertura de salud, que se mide por hitos. La caída de cortes no identifica por sí sola el efecto del protocolo.",
  // ITCIS
  ingresos: "Si el ingreso alcanza: la brecha entre el salario registrado y la canasta de pobreza, y la pobreza estimada mes a mes, que alcanza también a los hogares informales y a los que no viven de un salario.",
  consumo: "Lo que efectivamente se compra: las ventas de supermercados a precios constantes, la motorización total —autos y motos 0 km por habitante— y cuántas motos se patentan por cada auto, y el consumo de carnes. Se mueven con el poder de compra, pero también con el crédito y los precios relativos.",
  precios: "Tres gastos sensibles: alimentos contra el índice general de precios al consumidor, el alquiler —medido de dos formas: el que releva el índice de precios, contra el resto de los precios, y el que se pide en los avisos de Mercado Libre, descontada la inflación— y la canasta efectiva de electricidad, gas, agua y transporte como proporción del salario. Agua+energía y transporte se evalúan por separado contra referencias internacionales de asequibilidad, no contra las tarifas subsidiadas de 2023.",
  vulnerabilidad: "Cuán expuestas están las familias por su deuda de consumo. Combina la mora de la cartera —incumplimiento ya materializado— con la carga del servicio de deuda sobre la masa salarial —capacidad de pago comprometida antes del atraso—.",
  empleo: "Cuánta gente trabaja y en qué condiciones: la tasa de empleo de la Encuesta Permanente de Hogares (EPH) del Instituto Nacional de Estadística y Censos (INDEC) contra el mismo trimestre de 2023, que es el principal, y el porcentaje de asalariados sin aportes jubilatorios, el complemento. Dejaron de integrarla en octubre de 2026 el empleo registrado, los empleadores de pequeñas y medianas empresas, la subocupación demandante, el trabajo independiente y la construcción. La tasa de empleo se mueve despacio y no distingue la calidad del puesto.",
  percepcion: "La confianza de la población en el Gobierno nacional, medida preguntando: el Índice de Confianza en el Gobierno de la Universidad Torcuato Di Tella, único componente de la dimensión desde octubre de 2026. La otra vía —observar qué busca la gente en internet— está fuera del índice porque el volumen de búsquedas no distingue si un tema preocupa o alegra; se sigue relevando y su serie se publica.",
  seguridad: "Proporción de hogares que declaran haber sufrido al menos un delito, relevada por encuesta. Describe victimización reportada, con sus límites muestrales y de recuerdo; no es un censo de delitos ni una medida de sensación de inseguridad.",
  // ITCP
  sector_privado: "Lo que dicen en público, por escrito y con firma institucional, las cámaras empresarias sobre las medidas del Gobierno nacional, en cuatro sectores que pesan lo mismo: la industria (la Unión Industrial Argentina y la Asociación de Fábricas Argentinas de Componentes, la cámara de los autopartistas), el comercio (la Cámara Argentina de Comercio y Servicios), el campo (Coninagro, la Sociedad Rural y Confederaciones Rurales) y la construcción (la Cámara Argentina de la Construcción). Donde un sector tiene más de una cámara, se promedia el saldo de cada una. Es lo que dicen las cámaras de cada sector, no el humor de todo el empresariado: los bancos (la Asociación de Bancos Argentinos, la Asociación de Bancos de la Argentina y la Asociación de Bancos Públicos y Privados de la República Argentina) están clasificados pero no entran, porque en el último año se pronunciaron sobre el Gobierno nacional sólo tres veces y el mínimo es de cuatro; la tecnología no está porque ninguna de sus cámaras tiene comunicados de postura. Hasta septiembre de 2026 la completaba la brecha de expectativas de las constructoras de obra pública y privada, que salió en octubre por medir un solo sector.",
  poder_judicial: "Mide la cobertura estimada de cargos de juez, que depende de los pliegos que eleva el Poder Ejecutivo y del acuerdo del Senado. Desde octubre de 2026 la tasa de resolución de la Corte y la actividad de las comisiones de control del Consejo quedan fuera: miden a la Justicia, no al Ejecutivo. No mide juras certificadas, duración de causas ni resultados favorables al Gobierno. Las menciones cautelares del Sistema Argentino de Información Jurídica permanecen fuera del índice porque ese corpus no identifica litigios contra la agenda del Ejecutivo.",
  poder_legislativo: "La capacidad de gobernar por ley en el Congreso, en cinco señales: cuánto legisla por decreto de necesidad y urgencia en vez de ley, qué porción de la agenda del Ejecutivo se aprueba, cuántos vetos le dio vuelta el Congreso con dos tercios en las dos cámaras, cuántos decretos le derogó con el rechazo de las dos cámaras, y cuántas leyes sanciona el Congreso en total — el volumen contra el que se lee todo lo demás.",
  alianzas_territoriales: "El sostén federal del gobierno, visto desde tres señales: las transferencias no automáticas a las provincias —lo que la Nación les gira por decisión y no por ley—, el alineamiento de los senadores no oficialistas con la posición del bloque de gobierno, y la adhesión provincial al Régimen de Incentivo para Grandes Inversiones (RIGI). Conviene una precisión sobre qué mide y qué no: ninguna de las tres observa directamente la conducta de los gobernadores. La primera describe lo que hace el Gobierno nacional; la segunda, cómo votan los senadores de cada provincia; la tercera, una decisión legislativa provincial ya tomada. No se encontró una fuente pública que midiera de forma automatizable la postura de los ejecutivos provinciales, así que la dimensión se lee como respaldo territorial observado por sus efectos, no como una medición de la relación con cada gobernador.",
  cohesion_interna: "Qué tan unido está el oficialismo puertas adentro y cuánto necesita de los demás: la disciplina de voto del bloque propio de La Libertad Avanza, medida con dos indicadores bicamerales (Diputados 65%, Senado 35%) que pesan lo mismo: qué tan parejo vota el bloque propio de La Libertad Avanza, y cuántos votos de otros bloques hacen falta para aprobar una ley una vez descontadas sus propias bancas.",
  conflicto_social: "La conflictividad social que el gobierno tiene que administrar, medida en la calle y en el trabajo. Los eventos de protesta y disturbios de todo el país registrados por Armed Conflict Location & Event Data (ACLED), acumulados en 12 meses y comparados contra 2023 —la línea de base del mandato—, se completan con las jornadas individuales no trabajadas por conflicto laboral que publica la Secretaría de Trabajo, también acumuladas en 12 meses: huelguistas por duración del paro, que agrega el tamaño y la persistencia que el conteo de eventos no distingue.",
};
