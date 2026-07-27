// Fórmula de composición de cada indicador (LaTeX, renderizada con KaTeX en
// el modal). Estilo: PALABRAS dentro de la fórmula (no símbolos de paper) —
// cualquier lector debe poder leer qué compone el indicador sin diccionario.
// Pesos y transformaciones verificados contra los colectores (scripts/*.py).
// Los indicadores sin entrada simplemente no muestran la sección.

export interface Formula {
  latex: string;
  leyenda?: string;
}

export const FORMULAS: Record<string, Formula> = {
  // ── Macro (ITCM) ─────────────────────────────────────────────────────────
  ipc_total: {
    latex: String.raw`\left(\frac{\text{IPC}_{\text{este mes}}}{\text{IPC}_{\text{mes anterior}}}-1\right)\times 100`,
    leyenda: "Variación mensual del nivel general de precios (INDEC).",
  },
  rem_ipc_12m: {
    latex: String.raw`\left(\sqrt[12]{\,1+\tfrac{\text{expectativa anual}}{100}\,}-1\right)\times 100`,
    leyenda: "La inflación esperada a 12 meses (mediana del REM, BCRA) convertida a su equivalente mensual, para compararla con el IPC en la misma escala.",
  },
  idm: {
    latex: String.raw`\underbrace{\text{crecim. real de }M3}_{\text{pesos que HAY}}\;-\;\underbrace{\text{crecim. real de }M2}_{\text{pesos que la gente QUIERE}}`,
    leyenda: "Crecimientos interanuales reales (descontada la inflación) de los agregados privados. Positivo = sobran pesos → presión sobre precios y brecha; negativo = remonetización genuina.",
  },
  presion_dolarizacion: {
    latex: String.raw`\begin{cases}P_t=f_{precio}\!\left(\overline{100\left(\frac{CCL}{TC_{may}}-1\right)}_{\,3m}\right),&\text{régimen restringido}\\[8pt]P_t=\max\!\left\{f_{flujo}\!\left(100\,\frac{\sum \text{compras netas USD de personas humanas}}{\sum \left(M2_{privado,ARS}/TC_{may}\right)}\right),\; f_{flujo}\!\left(100\left(\frac{cripto}{TC_{may}}-1\right)\right)\right\},&\text{régimen abierto}\end{cases}\qquad \text{puntaje ITCM}=g(P_t),\;P_t\in[0,100]`,
    leyenda: "La señal cambia con el régimen. Hasta marzo de 2025 usa el promedio móvil de tres meses de la brecha CCL/mayorista. Desde abril mira dos canales sobre la misma ventana (1 mes en abril, 2 en mayo, 3 desde junio) y se queda con el MAYOR de los dos: las compras netas de dólares de personas humanas como porcentaje del M2 privado expresado en USD (canal bancarizado), y la brecha entre el dólar cripto y el mayorista (canal no bancarizado). Se toma el mayor y no un promedio porque los dos canales son sustitutos: cuando el mercado está abierto la demanda se vuelca al canal bancarizado y la brecha del cripto se desploma, de modo que promediarlos apagaría la señal del canal que efectivamente está activo. Si falta el dato de dólar cripto, la presión queda 100% del primer canal. Todas las métricas se convierten a presión 0–100; mayor presión implica menor puntaje ITCM.",
  },
  recaudacion: {
    latex: String.raw`\frac{1}{3}\sum_{\text{\'ultimos 3 meses}}\left(\frac{\text{DGI}_{m}}{\text{DGI}_{m-12}}\cdot\frac{\text{IPC}_{m-12}}{\text{IPC}_{m}}-1\right)\times 100`,
    leyenda: "Variación interanual de la recaudación de impuestos internos (DGI) descontada la inflación, promediada sobre los últimos tres meses con IPC publicado. Se mide la DGI y no el total porque el indicador sigue la base imponible y la actividad, y el total incluye la aduana, cuya caída en estos años responde a la decisión de bajar retenciones y no a un deterioro de la economía. El dato de un solo mes hereda el calendario tributario (vencimientos, anticipos); el promedio trimestral —la lectura habitual de los analistas fiscales— muestra la tendencia. El mes más reciente aparece como provisorio en el detalle hasta que su IPC cierre, y la card publica además el total y la aduana en la misma métrica.",
  },
  saldo_comercial_12m: {
    latex: String.raw`\sum_{\text{\'ultimos 12 meses}}\left(\text{exportaciones}-\text{importaciones}\right)`,
    leyenda: "Acumulado de 12 meses del intercambio de bienes (ICA, INDEC), en millones de USD.",
  },
  reservas_bcra: {
    latex: String.raw`\text{netas}=\text{brutas}-\underbrace{\text{swap} + \text{encajes USD} + \text{otros}}_{\text{fondos comprometidos, no disponibles}}+\text{dep. del Tesoro}`,
    leyenda: "Planilla SDDS del BCRA (drenajes de la Sección II) + depósitos del Tesoro en USD del balance: las divisas de libre disponibilidad, descontando las que figuran en el activo pero están comprometidas.",
  },
  idc: {
    latex: String.raw`\begin{gathered}0{,}30\cdot\underbrace{z_{\text{tasa real}}}_{\text{precio}}\;+\;0{,}40\cdot\underbrace{z_{\text{dep\'ositos}}}_{\text{volumen}}\;+\;0{,}30\cdot\underbrace{z_{\text{holgura}}}_{\text{asignaci\'on}}\\[4pt] z=\frac{\text{nivel de hoy}-\text{promedio hist\'orico}}{\text{desv\'io hist\'orico}}\end{gathered}`,
    leyenda: "Cada componente se compara con su propia historia (2018 a hoy) y se expresa en desvíos estándar: la tasa real que reciben los depositantes, el crecimiento interanual real de los depósitos privados (la comparación interanual absorbe la estacionalidad) y la holgura que queda para prestar (1 − préstamos/depósitos). Cero es el mes histórico típico; por encima de +0,5 la capacidad de fondeo es mayor a la habitual, por debajo de −0,5, menor.",
  },
  credito_privado: {
    latex: String.raw`\left(\frac{1+\text{crecim. nominal del cr\'edito}}{1+\text{inflaci\'on}}-1\right)\times 100`,
    leyenda: "Préstamos al sector privado (BCRA), variación interanual descontada la inflación: el crédito que efectivamente llegó, no el que infló la nominalidad.",
  },
  resultado_primario: {
    latex: String.raw`\frac{\sum_{12m}\text{resultado primario}}{\sum_{12m}\text{recaudaci\'on}}\times 100`,
    leyenda: "Resultado primario del Estado nacional acumulado en doce meses, dividido por la recaudación del mismo período: de cada peso recaudado, cuánto sobra antes de pagar intereses.",
  },
  costo_financiamiento_tesoro: {
    latex: String.raw`\left(\frac{1+\text{tasa efectiva de colocaci\'on}}{1+\text{inflaci\'on esperada}}-1\right)\times 100`,
    leyenda: "Tasa efectiva anual promedio de las licitaciones del mes, ponderada por el monto colocado, descontada la inflación esperada a doce meses.",
  },
  emae_ia: {
    latex: String.raw`\left(\frac{\text{actividad}_{\text{hoy}}}{\text{actividad}_{\text{hace 12 m}}}-1\right)\times 100`,
    leyenda: "EMAE (INDEC): el PIB mensual, comparado contra el mismo mes del año pasado.",
  },
  empleo_registrado: {
    latex: String.raw`\frac{\text{asalariados privados registrados}_{\text{hoy}}}{\text{promedio 4T-2023}}\times 100`,
    leyenda: "Asalariados del sector privado declarados al Sistema Integrado Previsional Argentino, en miles de personas. La card muestra el nivel; el índice del cinturón lo expresa contra el promedio del último trimestre de 2023, como el resto de los componentes. Por encima de 100 hay más empleo registrado que en la línea de base; por debajo, menos. Se usa la serie con estacionalidad porque la comparación es contra una base fija de tres meses y no contra el mes anterior.",
  },
  cobertura_judicial: {
    latex: String.raw`\frac{\text{cargos con juez designado}}{\text{cargos de juez habilitados}}\times 100`,
    leyenda: "Padrón de magistrados del Ministerio de Justicia: de los cargos de juez de la justicia federal y nacional que están habilitados, qué porcentaje tiene juez designado. Los cargos vacantes se cuentan como no cubiertos aunque haya un subrogante a cargo, porque un subrogante es una solución transitoria y no un juez designado para ese tribunal. La serie mensual se reconstruye moviendo el padrón hacia atrás y hacia adelante con los registros oficiales de designaciones y renuncias.",
  },
  emae_difusion: {
    latex: String.raw`\frac{\text{sectores que crecen i.a.}}{15\ \text{sectores}}\times 100`,
    leyenda: "EMAE por sector (INDEC): se compara cada uno de los quince sectores contra el mismo mes del año anterior y se cuenta cuántos crecen. 15 de 15 = todos los sectores en alza; 8 de 15 = poco más de la mitad. Se compara contra el año anterior y no contra el mes previo porque las series son originales, sin desestacionalizar. Limitación declarada: todos los sectores cuentan igual, sin ponderar por su tamaño en la economía — un mes en que crece la pesca cuenta lo mismo que uno en que crece la industria.",
  },
  tcrm: {
    latex: String.raw`\text{ITCRM}_{\text{hoy}}\qquad(\text{base dic-2015}=100)`,
    leyenda: "Tipo de cambio real multilateral oficial del BCRA: cuánto vale el peso contra las monedas de los socios comerciales, descontadas las inflaciones. Bajo = peso caro = exportar cuesta más.",
  },
  iai: {
    latex: String.raw`\begin{gathered}0{,}55\cdot\text{construcci\'on}\;+\;0{,}30\cdot\text{bienes de capital}\\[2pt]+\;0{,}15\cdot\text{patentamientos}\end{gathered}`,
    leyenda: "Variaciones interanuales de la inversión física, calculadas al último mes que ambas fuentes tienen publicado: ISAC (construcción), importación de bienes de capital y patentamientos comerciales. Sin patentamientos, renormaliza a 0,65/0,35. Limitación declarada: los bienes de capital se miden en dólares corrientes e incluyen el efecto de los precios internacionales — el INDEC solo publica el índice de cantidades con frecuencia trimestral.",
  },
  icip: {
    latex: String.raw`0{,}57\cdot\text{servicios tech}\;+\;0{,}43\cdot\text{productividad}`,
    leyenda: "Variaciones interanuales de la inversión intangible: pagos al exterior por software/cloud/IA + productividad laboral (producción industrial por empleado).",
  },

  // ── Gestión (ITCG) ───────────────────────────────────────────────────────
  cepo_mulc: {
    latex: String.raw`\left(\frac{\text{d\'olar CCL}}{\text{d\'olar mayorista}}-1\right)\times 100`,
    leyenda: "Cuánto más caro es el dólar financiero libre que el oficial. Cerca de 0 = mercado unificado, el cepo dejó de morder.",
  },
  apertura_comercial: {
    latex: String.raw`\frac{\text{impuestos al comercio exterior}}{\text{exportaciones}+\text{importaciones}}\times 100`,
    leyenda: "Recaudación por derechos de exportación + importación (ARCA, en USD) sobre el intercambio total (ICA): cuántos centavos de impuesto paga cada dólar comerciado. 0% = libre comercio.",
  },
  desregulacion_normativa: {
    latex: String.raw`\text{normas de desregulaci\'on acumuladas desde el 10-dic-2023}`,
    leyenda: "Es el conteo que publica el propio Ministerio de Desregulación y Transformación del Estado en su informe mensual: cuántas normas dictadas desde el 10 de diciembre de 2023 eliminan o modifican regulaciones anteriores. No es una elaboración del proyecto sino la cifra oficial del organismo responsable del programa, verificable en el informe. La escala de referencia sí es una convención propia: el ministerio publica el conteo pero no declara ninguna meta, de modo que el punto en que la desregulación se considera un plan completo lo fija el proyecto.",
  },
  reduccion_estado: {
    latex: String.raw`\left(\frac{\text{empleados del Estado}_{\text{hoy}}}{\text{empleados del Estado}_{\text{dic-23}}}-1\right)\times 100`,
    leyenda: "Dotación de personal de la Administración Pública Nacional (base de empleo público).",
  },
  gasto_funcionamiento: {
    latex: String.raw`\left(\frac{\text{gasto}_{\text{hoy}}}{\text{gasto}_{2023}}\cdot\frac{\text{IPC}_{2023}}{\text{IPC}_{\text{hoy}}}-1\right)\times 100`,
    leyenda: "Gasto de funcionamiento devengado (Presupuesto Abierto) comparado contra 2023 en términos reales.",
  },
  masa_salarial: {
    latex: String.raw`\left(\frac{\text{masa salarial}_{\text{hoy}}}{\text{masa salarial}_{2023}}\cdot\frac{\text{IPC}_{2023}}{\text{IPC}_{\text{hoy}}}-1\right)\times 100`,
    leyenda: "Masa salarial devengada del personal público (Presupuesto Abierto) contra 2023, descontada la inflación — filtra tanto despidos como licuación.",
  },
  reestructuracion_organismos: {
    latex: String.raw`\frac{\text{actos de disoluci\'on/reestructuraci\'on}}{45\;(\text{plan completo})}\times 100`,
    leyenda: "Normas con disolución de organismos desde dic-2023 (InfoLeg). Calibración validada a mano: 18 actos = 40%.",
  },
  fal_modernizacion_laboral: {
    latex: String.raw`\frac{\text{actos fundamentales cumplidos}}{2}\times 100`,
    leyenda: "Los dos actos que ponen en pie al Fondo de Asistencia Laboral, cincuenta puntos cada uno: la Ley 27.802, con la que el Congreso instauró el Fondo (marzo de 2026), y el Decreto 408/2026, con el que el Poder Ejecutivo lo reglamentó (junio de 2026). Ambos están cumplidos y son verificables por número de norma. El criterio es que, con la ley sancionada y reglamentada, el Gobierno agotó lo que podía cumplir de la promesa hasta que el régimen entre en vigencia el 1 de noviembre de 2026. Los fondos registrados en la Comisión Nacional de Valores y las menciones del instrumento en el Boletín Oficial se siguen relevando y se muestran como contexto, pero no inciden en el puntaje.",
  },
  litigiosidad_laboral: {
    latex: String.raw`\left(\frac{\text{juicios \'ultimos 12 meses}}{\text{juicios 12 meses anteriores}}-1\right)\times 100`,
    leyenda: "Juicios del sistema de riesgos del trabajo (SRT): si la industria del juicio se enfría, la variación se hace negativa.",
  },
  privatizaciones: {
    latex: String.raw`\frac{\text{etapa promedio de la cartera}}{4}\times 100`,
    leyenda: "Cada empresa de la Ley Bases se puntúa por etapa verificable en el Boletín Oficial: 0 sin definir · 1 preparatoria · 2 pliegos · 3 licitación · 4 cerrada. Separa el anuncio del hecho.",
  },
  rigi_inversiones: {
    latex: String.raw`\frac{\text{inversi\'on aprobada}}{\text{inversi\'on aprobada}+\text{inversi\'on en evaluaci\'on}}\times 100`,
    leyenda: "Montos en USD de la plataforma oficial del RIGI: cuánto de la cartera ya tiene luz verde.",
  },
  concesiones_infraestructura: {
    latex: String.raw`\frac{\text{km de rutas adjudicados}}{\text{km del plan}}\times 100`,
    leyenda: "Red Federal de Concesiones, por etapas con fecha del Boletín Oficial (CONTRAT.AR).",
  },
  asistencia_directa: {
    latex: String.raw`\frac{\text{pagado directo a las personas}}{\text{total de transferencias del programa}}\times 100`,
    leyenda: "Ejecución presupuestaria real (partida 5.1.4 sobre el total) de los programas sucesores del Potenciar: qué proporción de la asistencia llega sin intermediarios.",
  },
  protocolo_antipiquetes: {
    latex: String.raw`\left(1-\frac{\text{cortes en CABA, \'ultimo a\~no}}{\text{cortes en CABA en 2023}}\right)\times 100`,
    leyenda: "Reducción porcentual de cortes contra 2023, con los anclajes anuales públicos de Diagnóstico Político (2023: 931 · 2025: 240). 100 = cero cortes; 0 = igual que 2023.",
  },
  libertad_opcion_salud: {
    latex: String.raw`\frac{\text{usuarios con aporte directo a su prepaga}}{\text{usuarios de prepagas}}\times 100`,
    leyenda: "Padrones oficiales de la SSS: cuántos usuarios ya derivan sus aportes directo (canal creado por el DNU 70/2023), sin triangular por una obra social.",
  },

  // ── Vida cotidiana (ITVC-B100: índices 100 = promedio 4T-2023) ──────────
  brecha_salario_cbt: {
    latex: String.raw`\frac{\text{salario registrado promedio (RIPTE)}}{\text{canasta b\'asica total del hogar}}`,
    leyenda: "Cuántas canastas de pobreza compra un sueldo. Al ITVC entra rebaseado: 100 = arranque del mandato (4T-2023).",
  },
  ipc_alimentos: {
    latex: String.raw`100\cdot\frac{\left(\text{precios generales}\,/\,\text{precio de alimentos}\right)_{\text{hoy}}}{\left(\text{precios generales}\,/\,\text{precio de alimentos}\right)_{\text{4T-23}}}`,
    leyenda: "Encarecimiento relativo de la comida: si los alimentos suben más que el resto de los precios, la canasta de los hogares de menores ingresos se castiga aunque la inflación general baje. Más de 100 = la comida sube menos que el promedio (alivio); menos de 100 = la comida encarece por encima del resto. Independiente del salario — el poder de compra ya lo mide la brecha salario/canasta, en Ingresos. (La card muestra la variación mensual del rubro.)",
  },
  peso_tarifas: {
    latex: String.raw`100\cdot\frac{\left(\text{salario}\,/\,\text{tarifas}\right)_{\text{hoy}}}{\left(\text{salario}\,/\,\text{tarifas}\right)_{\text{4T-23}}}`,
    leyenda: "Cuántas facturas de servicios regulados paga el sueldo, contra el arranque del mandato. Debajo de 100 = las tarifas pesan más en el bolsillo que en 2023 (fin de subsidios).",
  },
  indice_lider: {
    latex: String.raw`100\cdotrac{	ext{'Indice L'ider}_{	ext{hoy}}}{	ext{'Indice L'ider}_{	ext{4T-23}}}`,
    leyenda: "Nivel del Índice Líder de la Universidad Torcuato Di Tella contra el arranque del mandato. Por encima de 100, las señales tempranas de la economía están mejor que en 2023.",
  },
  alquiler_real: {
    latex: String.raw`100\cdotrac{\left(	ext{IPC general}\,/\,	ext{alquiler}
ight)_{	ext{hoy}}}{\left(	ext{IPC general}\,/\,	ext{alquiler}
ight)_{	ext{4T-23}}}`,
    leyenda: "Cuánto sube el alquiler comparado con el resto de los precios, contra el arranque del mandato. Debajo de 100 = el alquiler se encareció más que todo lo demás.",
  },
  mortalidad_pymes: {
    latex: String.raw`100\cdot\frac{\text{producci\'on industrial}_{\text{hoy}}}{\text{producci\'on industrial}_{\text{4T-23}}}`,
    leyenda: "Nivel del IPI manufacturero desestacionalizado como proxy de la salud de las pymes industriales (empleadoras), 100 = 4T-2023.",
  },
  despacho_cemento: {
    latex: String.raw`100\cdot\frac{\text{actividad de la construcci\'on}_{\text{hoy}}}{\text{actividad de la construcci\'on}_{\text{4T-23}}}`,
    leyenda: "Nivel del ISAC desestacionalizado — la construcción es el sector más intensivo en mano de obra, 100 = 4T-2023.",
  },
  endeudamiento_familiar: {
    latex: String.raw`100\cdot\frac{\text{deuda real de las familias}_{\text{hoy}}}{\text{deuda real}_{\text{4T-23}}}`,
    leyenda: "Crédito de consumo (tarjetas + personales, BCRA) descontado la inflación, como stock puro: mide el acceso de los hogares al financiamiento. El estrés de pago lo mide por separado la mora de las familias, en la misma dimensión.",
  },
  mora_familias: {
    latex: String.raw`\frac{\text{mora}_{\text{pers}}\cdot\text{saldo}_{\text{pers}}+\text{mora}_{\text{tarj}}\cdot\text{saldo}_{\text{tarj}}}{\text{saldo}_{\text{pers}}+\text{saldo}_{\text{tarj}}}`,
    leyenda: "Porcentaje de la cartera de consumo de las familias en situación irregular (Informe sobre Bancos, BCRA), ponderando la mora de personales y tarjetas por el saldo de cada línea. En el ITVC puntúa por el nivel relativo al 4T-2023. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100.",
  },
  pluriempleo: {
    latex: String.raw`100\cdot\frac{\text{subocupaci\'on}_{\text{4T-23}}}{\text{subocupaci\'on}_{\text{hoy}}}`,
    leyenda: "Subocupación demandante (EPH): gente que necesita trabajar más horas. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100.",
  },
  informalidad: {
    latex: String.raw`100\cdot\frac{\text{informalidad}_{\text{4T-23}}}{\text{informalidad}_{\text{hoy}}}`,
    leyenda: "Asalariados sin descuento jubilatorio (EPH, trimestral). En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100. La card muestra la tasa del trimestre.",
  },
  consumo_carne: {
    latex: String.raw`100\cdot\frac{\text{kg de carne por habitante}_{\text{hoy}}}{\text{kg por habitante}_{\text{4T-23}}}`,
    leyenda: "Consumo per cápita anualizado (promedio móvil 12 meses, CICCRA): el termómetro de bolsillo más argentino, 100 = 4T-2023.",
  },
  patentamiento_motos: {
    latex: String.raw`100\cdot\frac{\text{patentamientos, promedio 12 meses}_{\text{hoy}}}{\text{promedio 12 meses}_{\text{4T-23}}}`,
    leyenda: "Motos patentadas (CAFAM) en promedio móvil anual — desestacionalizado: enero patenta ≈ el doble que junio. La card muestra el mes crudo.",
  },
  inseguridad: {
    latex: String.raw`100\cdot\frac{\text{hogares v\'ictimas}_{\text{ene-24}}}{\text{hogares v\'ictimas}_{\text{hoy}}}`,
    leyenda: "Índice de Victimización del LICIP (Universidad Di Tella): porcentaje de hogares de 40 centros urbanos que sufrió al menos un delito en los últimos 12 meses, lo haya denunciado o no — capta la cifra negra que las estadísticas de denuncias no ven. Encuesta mensual; la ventana de 12 meses absorbe la estacionalidad. Base declarada: enero 2024, la primera medición tras la reanudación de la encuesta (suspendida 2020-2023) — su ventana de 12 meses cubre mayormente el año previo al mandato. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100. Contraste: los hechos denunciados del SNIC, en la ficha.",
  },
  icc_utdt: {
    latex: String.raw`100\cdot\frac{\text{confianza del consumidor}_{\text{hoy}}}{\text{confianza}_{\text{4T-23}}}`,
    leyenda: "ICC de la Universidad Torcuato Di Tella, rebaseado al arranque del mandato.",
  },
  sentimiento_digital: {
    latex: String.raw`100\cdot\frac{\text{inter\'es de b\'usqueda}_{\text{4T-23}}}{\text{inter\'es de b\'usqueda}_{\text{hoy}}}`,
    leyenda: "Canasta de búsquedas en Google sobre inflación, precios, inseguridad y trabajo (promedio mensual, ventana fija desde 2021). La escala de Google Trends es relativa a la ventana consultada, pero el cociente entre dos meses de la misma consulta no depende de esa escala — eso permite compararlo contra el 4T-2023. Más búsquedas de urgencia económica = peor. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100. Validación: correlación +0,76 con la inflación mensual. El titular de la card es el pulso de los últimos 3 meses, en tiempo real.",
  },

  // ── Política ─────────────────────────────────────────────────────────────
  eficacia_legislativa: {
    latex: String.raw`\frac{\text{proyectos del Ejecutivo convertidos en ley}}{\text{proyectos de ley enviados hace 12-24 meses}}\times 100`,
    leyenda: "Cohorte madura: solo cuenta proyectos de ley con al menos 12 meses de margen desde que se enviaron, sobre los datos abiertos de la Cámara de Diputados. La aprobación se verifica contra el registro oficial de leyes sancionadas — cubre las sanciones de ambas cámaras — y se mira sin tope de tiempo.",
  },
  desafios_legislativos: {
    latex: String.raw`\sum_{\text{\'ultimos 12 meses}}\left(\text{vetos con insistencia votada}+\text{decretos votados bajo la ley 26.122}\right)`,
    leyenda: "Conteo de normas del Ejecutivo llevadas a votación en el recinto, cada una contada una sola vez en el mes de su primer desafío. No importa el resultado: entran tanto las que el Gobierno terminó perdiendo como las que logró sostener. Fuentes: actas de votación de Diputados y del Senado, y la base InfoLeg de legislación nacional. Menos desafíos = puntaje más alto.",
  },
  brecha_obra_publica: {
    latex: String.raw`\frac{1}{12}\sum_{\text{\'ultimos 12 meses}}\Big[\underbrace{(\%\text{sube}-\%\text{baja})_{\text{obra p\'ublica}}}_{\text{saldo p\'ublico}}-\underbrace{(\%\text{sube}-\%\text{baja})_{\text{obra privada}}}_{\text{saldo privado}}\Big]`,
    leyenda: "Encuesta Cualitativa de la Construcción del INDEC (Cuadro 7.1): cada mes se consulta a las grandes empresas constructoras si esperan que su actividad aumente, no varíe o disminuya en los próximos tres meses, con respuestas separadas para obra pública y obra privada. El saldo de cada grupo es el porcentaje que espera subas menos el que espera bajas. La brecha es la diferencia entre ambos saldos, promediada en doce meses para quitarle ruido. Cero significa que ambos grupos esperan lo mismo; negativo, que las empresas que dependen del Estado esperan peor que sus pares privadas.",
  },
  ratio_dnu: {
    latex: String.raw`\frac{\text{DNU dictados, \'ultimos 365 d\'ias}}{\text{leyes sancionadas, \'ultimos 365 d\'ias}}`,
    leyenda: "Conteos del buscador oficial de InfoLeg sobre una ventana móvil de 365 días (no el año calendario). Más de 1 = el Ejecutivo dicta más decretos de necesidad y urgencia que leyes logra sancionar el Congreso.",
  },
  veto_quorum: {
    latex: String.raw`\frac{\text{sesiones en minor\'ia}_{\text{12 m}}}{\text{sesiones convocadas}_{\text{12 m}}}\times 100`,
    leyenda: "Sesiones plenarias de Diputados de los últimos doce meses (datos abiertos HCDN). Una sesión cuenta como caída cuando el registro oficial la clasifica «en minoría»: fue convocada, esperó y nunca llegó a constituirse, de modo que no recibió número de sesión. El denominador son las sesiones convocadas para tratar temas —las especiales y las que quedaron en minoría—; quedan afuera las informativas, la preparatoria y la presentación del presupuesto, donde el oficialismo no necesita juntar quórum para avanzar su agenda.",
  },
  comisiones_caidas: {
    latex: String.raw`\frac{\text{proyectos con dictamen sin sanci\'on}_{\text{12 m}}}{\text{proyectos con dictamen}_{\text{12 m}}}\times 100`,
    leyenda: "Dictámenes de comisión con Orden del Día de los últimos 12 meses que nunca llegaron a sancionarse en el recinto (datos abiertos HCDN).",
  },
  derrotas_legislativas: {
    latex: String.raw`\sum_{\text{\'ultimos 12 meses}}\left(\text{vetos insistidos por ambas c\'amaras}+\text{decretos rechazados en el recinto}\right)`,
    leyenda: "Conteo de derrotas consumadas del Ejecutivo: una ley vetada cuenta cuando la segunda cámara completa la insistencia con dos tercios (la ley se promulga pese al veto); un decreto cuenta cuando una cámara lo rechaza bajo el procedimiento de la ley 26.122. Cada norma cuenta una sola vez, en el mes de la derrota. Fuentes: base InfoLeg de legislación nacional y actas de votación del Senado. Menos es mejor para el Ejecutivo.",
  },
  bloqueo_sostenido: {
    latex: String.raw`\frac{\text{normas desafiadas que siguen en pie}_{\text{12 m}}}{\text{normas desafiadas en el recinto}_{\text{12 m}}}\times 100`,
    leyenda: "Una norma queda desafiada desde su primera votación en el recinto: la insistencia de una ley vetada (gane o pierda) o el control de un decreto bajo la ley 26.122. Sigue en pie mientras la insistencia no se complete en ambas cámaras o el decreto no sea rechazado por las dos. Fuentes: actas de votación nominales de Diputados y del Senado, y base InfoLeg para vetos e insistencias. Más es mejor para el Ejecutivo: es la contracara del conteo de derrotas, la capacidad de sostener la norma propia con un tercio de una cámara.",
  },
  movilizacion_cepa: {
    latex: String.raw`\frac{\text{conflictos laborales acumulados del a\~no}}{200\;(\text{m\'aximo de referencia})}\times 100`,
    leyenda: "La cifra del informe de conflictividad de CEPA, normalizada a un índice 0–100. El máximo de referencia (200 conflictos acumulados) es una calibración propia del informe, declarada en la ficha.",
  },
  conflictividad_nacional: {
    latex: String.raw`\left(\frac{\text{eventos de protesta y disturbios en el pa\'is}_{\text{\'ultimos 12 meses}}}{\text{eventos}_{\text{2023}}}-1\right)\times 100`,
    leyenda: "Eventos de protesta y disturbios en todo el país (marchas, concentraciones y disturbios registrados por ACLED, el relevamiento académico internacional estándar), acumulados en los últimos 12 meses completos y comparados contra el total de 2023, la línea de base del mandato. Negativo = menos conflicto en la calle que en 2023. El mes en curso se excluye hasta que cierra, porque el registro se carga con rezago.",
  },
  iaf_transferencias: {
    latex: String.raw`\left(\frac{\text{transferencias a provincias}_{\text{a\~no}}}{\text{transferencias}_{\text{a\~no anterior}}}\cdot\frac{\overline{\text{IPC}}_{\text{a\~no anterior}}}{\overline{\text{IPC}}_{\text{a\~no}}}-1\right)\times 100`,
    leyenda: "Serie oficial de recursos de origen nacional efectivamente girados (Hacienda), deflactada con la inflación promedio anual del IPC de INDEC — el criterio correcto para sumas anuales de flujos: la variación real interanual de lo que la Nación transfirió a las provincias.",
  },
  adhesion_reformas_provincial: {
    latex: String.raw`\frac{\text{jurisdicciones adheridas al RIGI}}{24}\times 100`,
    leyenda: "Conteo sobre la tabla oficial de adhesiones (MAGyP): 24 jurisdicciones = 23 provincias más la Ciudad de Buenos Aires.",
  },
  protestas_caba: {
    latex: String.raw`\sum_{\text{\'ultimos 12 meses}}\text{eventos de protesta en CABA}`,
    leyenda: "Conteo de ACLED (marchas, concentraciones, disturbios con cobertura de prensa). El índice político no puntúa el conteo sino su variación contra el total de 2023, la línea de base del mandato.",
  },
  rotacion_gabinete: {
    latex: String.raw`\sum_{\text{\'ultimos 12 meses}}\text{salidas de jefes de Gabinete y ministros}`,
    leyenda: "Salidas de cargos de rango ministerial pleno (jefe de Gabinete y ministros), contadas por el mes del cese efectivo sobre un registro curado de decretos del Boletín Oficial. No cuentan los pases a otro cargo del mismo gabinete ni los ministerios cerrados o fusionados por reorganización. Menos salidas = puntaje más alto.",
  },
  cohesion_bloque: {
    latex: String.raw`0{,}65\times\text{cohesi\'on Diputados}+0{,}35\times\text{cohesi\'on Senado}`,
    leyenda: "Compuesto bicameral. La cohesión de cada cámara es el promedio, sobre las actas divididas de los últimos 90 días, de |votos a favor − votos en contra| dividido por el total de votos que emitió el bloque propio de LLA en cada acta (índice de Rice); abstenciones y ausencias no entran. Si una cámara no tiene actas divididas en la ventana, el peso se reparte sobre la otra.",
  },
  alineamiento_senadores_prov: {
    latex: String.raw`\frac{1}{N_{\text{provincias}}}\sum_{\text{provincias}}\frac{\text{votos no-LLA que coinciden con la posici\'on LLA}}{\text{votos no-LLA}}\times 100`,
    leyenda: "Actas del Senado de los últimos 90 días: por provincia, qué proporción de los votos de senadores que no son del bloque LLA coincidió con el sentido en que votó ese bloque; el indicador promedia entre provincias con al menos un senador no oficialista.",
  },
  votometro_ventaja_lla: {
    latex: String.raw`\text{intenci\'on de voto LLA}-\text{intenci\'on de voto PJ}`,
    leyenda: "Gap en puntos porcentuales del agregador Votómetro (encuestas ponderadas por calidad y recencia).",
  },
  clima_electoral: {
    latex: String.raw`\text{intenci\'on de voto LLA}-\text{intenci\'on de voto PJ}`,
    leyenda: "Gap en puntos porcentuales (Votómetro).",
  },
  indice_intencion_migratoria: {
    latex: String.raw`\text{inter\'es de b\'usqueda mensual}\;(0\text{-}100)`,
    leyenda: "Canasta de búsquedas en Google sobre intención de emigrar (por ejemplo \"emigrar de argentina\", \"vivir en el exterior\"), promedio mensual en ventana fija desde 2021 — misma técnica que sentimiento digital. Más búsqueda = más tensión: a diferencia de sentimiento digital (urgencia económica del momento), esta es una señal de salida más estructural. Nunca debería leerse sola: por eso la card la acompaña con un contraste de migración efectiva (visas, residencias y ciudadanías otorgadas a argentinos en los destinos principales) que se muestra sin puntuar.",
  },
};
