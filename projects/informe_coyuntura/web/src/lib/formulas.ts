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
  desequilibrio_monetario: {
    latex: String.raw`A_t=100\,\frac{M2^{transaccional}_{privado}}{\text{circulante}+\text{dep}^{\$}_{priv}+\text{dep}^{U\!S\!D}_{priv}}\qquad B_t=\text{compra neta de divisas del SPNF (U\!S\!D M)}\\[6pt]a=\pi_A(A_t),\;b=\pi_B(B_t)\in[0,1]\qquad T_t=(1-a)(1-b)\,40+a(1-b)\,0+(1-a)b\,90+ab\,77{,}5\\[6pt]\text{puntaje ITCM}=100-T_t`,
    leyenda: "El indicador cruza dos componentes en vez de promediarlos. A mide, sobre el total de la liquidez privada (pesos más los dólares depositados, valuados en pesos), qué proporción sigue en pesos de uso transaccional: es la dolarización que se ve, porque no sale del sistema. B mide la compra neta de divisas del sector privado no financiero en el mercado de cambios: es la que se va, y aparece aunque no toque ningún depósito. Cada uno se lleva a una posición de 0 a 1 interpolando entre los percentiles de su ventana de calibración (A desde enero de 2021, que es cuando el BCRA empieza a publicar el M2 transaccional privado; B desde abril de 2025, la apertura del cepo a personas humanas, para no mezclar regímenes cambiarios). La tensión sale de interpolar bilinealmente entre las cuatro esquinas de la matriz: confianza real 0, dolarización contenida en el sistema 40, fuga oculta fuera del sistema 77,5 y deterioro dentro y fuera 90. La matriz no es simétrica a propósito: que se degrade la fuga cuesta casi el doble que se degrade el stock, porque la fuga fuera del sistema es la señal grave. El puntaje del ITCM es el complemento de la tensión.",
  },
  recaudacion: {
    latex: String.raw`\frac{\left(\text{DGI}_{m}+\text{IIBB}_{m}\right)/\text{IPC}_{m}}{\text{factor estacional}_{\text{mes}}}\div\overline{\left(\text{4T-2023}\right)}\times 100`,
    leyenda: "Recaudación de impuestos internos de la Nación (DGI) más la de los sistemas de la Comisión Arbitral —Ingresos Brutos de los contribuyentes de Convenio Multilateral y sus regímenes de retención—, sumadas en nivel, llevadas a pesos constantes con el IPC y divididas por el promedio del cuarto trimestre de 2023, que vale 100. Se mide la DGI y no el total porque el indicador sigue la base imponible y la actividad, y el total incluye la aduana, cuya caída en estos años responde a la decisión de bajar retenciones y no a un deterioro de la economía. El factor estacional corrige el calendario tributario, que concentra la recaudación en mayo y junio y la deprime en marzo: se calcula como el cociente entre cada mes y la tendencia de doce meses centrada, promediado por mes calendario. Antes se publicaba la variación contra el mismo mes del año anterior; se cambió porque teniendo el dato mensual esa comparación arrastra la base de hace un año y puede informar crecimiento mientras el nivel sigue por debajo del punto de partida.",
  },
  pobreza_nowcast: {
    latex: String.raw`\frac{\text{pobreza}_{\text{2do sem. 2023}}}{\text{pobreza}_{\text{este mes}}}\times 100`,
    leyenda: "Pobreza rebaseada al segundo semestre de 2023, que vale 100, e invertida: la base va arriba porque más pobreza es peor, así que por encima de 100 hay menos pobreza que en la transición. El nivel de cada mes es la estimación mensual de la Universidad Torcuato Di Tella; la base es la medición oficial del INDEC, porque la estimación mensual empieza en enero de 2025 y no alcanza el período base. Las dos fuentes no coinciden exactamente y el desvío está declarado en las limitaciones de la ficha.",
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
  produccion_legislativa: {
    latex: String.raw`\text{leyes sancionadas en los \'ultimos 12 meses}`,
    leyenda: "Dataset oficial de leyes sancionadas de la Cámara de Diputados: se cuentan las leyes con sanción definitiva en la ventana de doce meses que termina en el mes informado. El promedio histórico de los dieciocho años completos que trae el dataset —desde 2008, con cuatro presidencias— es de setenta y cuatro leyes por año, y ése es el valor con el que se compara, no el rango de estos años.",
  },
  judicializacion: {
    latex: String.raw`\frac{\text{sumarios con medida cautelar}}{\text{total de sumarios}}\times 100`,
    leyenda: "Base de jurisprudencia SAIJ, restringida a jurisdicción federal y nacional en el numerador y en el denominador. La proporción es lo que vuelve comparables años distintos: el conteo sin normalizar pasa de sesenta y nueve fallos en 2016 a trescientos cincuenta en 2021, y eso mide cuánto publica la base, no cuántas cautelares hubo.",
  },
  velocidad_resolucion: {
    latex: String.raw`\frac{\text{expedientes resueltos en el a\~no}}{\text{expedientes ingresados en el a\~no}}\times 100`,
    leyenda: "Anuario estadístico de la Corte Suprema, sobre su sistema de gestión judicial. Cien por ciento significa que la Corte resuelve exactamente lo que le entra: por encima descarga atraso acumulado, por debajo lo acumula. Los doce años de la serie cierran de forma exacta contra el saldo que la propia fuente informa por separado.",
  },
  paralisis_denuncias: {
    latex: String.raw`\text{sesiones de Acusaci\'on y Disciplina en 12 meses}`,
    leyenda: "Archivo de notas del Consejo de la Magistratura: se cuentan las sesiones numeradas de las comisiones de Acusación y de Disciplina en la ventana de doce meses. Las notas sin número —sesiones conjuntas, extraordinarias y audiencias testimoniales— se relevan aparte y no entran en el conteo.",
  },
  emae_difusion: {
    latex: String.raw`\frac{\text{sectores que crecen i.a.}}{15\ \text{sectores}}\times 100`,
    leyenda: "EMAE por sector (INDEC): se compara cada uno de los quince sectores contra el mismo mes del año anterior y se cuenta cuántos crecen. 15 de 15 = todos los sectores en alza; 8 de 15 = poco más de la mitad. Se compara contra el año anterior y no contra el mes previo porque las series son originales, sin desestacionalizar. Limitación declarada: todos los sectores cuentan igual, sin ponderar por su tamaño en la economía — un mes en que crece la pesca cuenta lo mismo que uno en que crece la industria.",
  },
  ipi_manufacturero: {
    latex: String.raw`\frac{1}{3}\sum_{m=0}^{2}\left(\frac{\text{IPI manufacturero}_{t-m}}{\text{IPI manufacturero}_{t-m-12}}-1\right)\times 100`,
    leyenda: "Promedio simple de las tres variaciones interanuales más recientes del Índice de Producción Industrial manufacturero del INDEC. El promedio móvil reduce el ruido mensual sin mezclar meses de distinta estacionalidad.",
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
    latex: String.raw`\text{art\'iculos modificados o eliminados, acumulados desde el 10-dic-2023}`,
    leyenda: "Es una de las tres cifras que publica el Ministerio de Desregulación y Transformación del Estado en su informe mensual: cuántos artículos de normas anteriores quedaron modificados o eliminados por el programa desde el 10 de diciembre de 2023. Se eligió el recuento de artículos y no el de normas porque las normas no son equivalentes entre sí: un decreto que reescribe quinientos artículos y una resolución que toca uno cuentan igual si se cuentan normas, y muy distinto si se cuentan artículos. La cifra es oficial y verificable en el informe; la escala de referencia, en cambio, es una convención propia, porque el ministerio publica el recuento pero no declara ninguna meta. Dos cosas que el número no dice y la ficha desarrolla: el recuento cuenta actos y no efectos —un artículo derogado que después queda suspendido suma igual que uno que rige— y lo publica el mismo ministerio que conduce el programa que se está midiendo.",
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
    latex: String.raw`\frac{\text{actos de disoluci\'on o cierre}}{45\;(\text{plan completo})}\times 100`,
    leyenda: "Normas con disolución de organismos desde dic-2023 (InfoLeg), filtradas caso por caso contra un registro curado: no cuentan ni fusiones/transformaciones ni hallazgos de texto que no sean, revisados uno por uno, el cierre vigente de un organismo público (por ejemplo, un acto rechazado después por el Congreso). Calibración validada a mano: 45 = plan completo.",
  },
  fal_modernizacion_laboral: {
    latex: String.raw`100\times\left(0{,}50\cdot\frac{\text{actos fundamentales vigentes}}{2}+0{,}20\cdot\text{vigencia}+0{,}30\cdot\text{adopci\'on}\right)`,
    leyenda: "Mide lo que rige, no lo que se dictó. Los dos actos que ponen en pie al Fondo de Asistencia Laboral valen la mitad del indicador —la Ley 27.802, con la que el Congreso lo instauró en marzo de 2026, y el Decreto 408/2026, con el que el Poder Ejecutivo lo reglamentó en junio—, y cada uno cuenta sólo mientras esté dictado y no suspendido judicialmente con alcance general. La vigencia del régimen vale un veinte por ciento y se cumple el 1 de noviembre de 2026, fecha que fijó el artículo 27 del propio decreto. La adopción vale un treinta por ciento y se cumple con el primer fondo inscripto en la Comisión Nacional de Valores bajo la denominación de la Ley 27.802. Las menciones del instrumento en el Boletín Oficial y los fondos del régimen homónimo de la construcción se siguen relevando como contexto y no inciden en el puntaje.",
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

  // ── Impacto social (ITCIS: 17 bases temporales + tarifas por asequibilidad) ─
  brecha_salario_cbt: {
    latex: String.raw`\frac{\text{salario registrado promedio (RIPTE)}}{\text{canasta b\'asica total del hogar}}`,
    leyenda: "Cuántas canastas de pobreza compra un sueldo. Al ITCIS entra rebaseado: 100 = arranque del mandato (4T-2023).",
  },
  ipc_alimentos: {
    latex: String.raw`100\cdot\frac{\left(\text{precios generales}\,/\,\text{precio de alimentos}\right)_{\text{hoy}}}{\left(\text{precios generales}\,/\,\text{precio de alimentos}\right)_{\text{4T-23}}}`,
    leyenda: "Encarecimiento relativo de la comida: si los alimentos suben más que el resto de los precios, la canasta de los hogares de menores ingresos se castiga aunque la inflación general baje. Más de 100 = la comida sube menos que el promedio (alivio); menos de 100 = la comida encarece por encima del resto. Independiente del salario — el poder de compra ya lo mide la brecha salario/canasta, en Ingresos. (La card muestra la variación mensual del rubro.)",
  },
  peso_tarifas: {
    latex: String.raw`T=\max\left\{\operatorname{clip}_{0}^{10}\!\left[2(E-10)\right],\operatorname{clip}_{0}^{10}\!\left[2(P-5)\right]\right\},\quad I=125-5T`,
    leyenda: "E es agua+energía y P es transporte, cada uno como % del RIPTE. Agua+energía: 10% = tensión 0, 12,5% = 5 y 15% = 10. Transporte: 5% = tensión 0, 7,5% = 5 y 10% = 10. Se usa el peor de los dos grupos para impedir compensaciones; la card muestra además el total.",
  },
  indice_lider: {
    latex: String.raw`100\cdot\frac{\text{Índice Líder}_{\text{hoy}}}{\text{Índice Líder}_{\text{4T-23}}}`,
    leyenda: "Nivel del Índice Líder de la Universidad Torcuato Di Tella contra el arranque del mandato. Por encima de 100, las señales tempranas de la economía están mejor que en 2023.",
  },
  alquiler_real: {
    latex: String.raw`100\cdot\frac{\left(\text{IPC general}\,/\,\text{alquiler}\right)_{\text{hoy}}}{\left(\text{IPC general}\,/\,\text{alquiler}\right)_{\text{4T-23}}}`,
    leyenda: "Cuánto sube el alquiler comparado con el resto de los precios, contra el arranque del mandato. Debajo de 100 = el alquiler se encareció más que todo lo demás.",
  },
  trabajo_independiente: {
    latex: String.raw`100\cdot\frac{\text{participaci\'on}_{\text{4T-23}}}{\text{participaci\'on}_{\text{hoy}}}\quad\text{con}\quad\text{participaci\'on}=\frac{\text{aut\'onomos}+\text{monotributo}}{\text{empleo registrado total}}`,
    leyenda: "Peso de autónomos y monotributistas en el empleo registrado, invertido: más participación independiente es peor, 100 = 4T-2023.",
  },
  mortalidad_pymes: {
    latex: String.raw`100\cdot\frac{\text{empleadores hasta 50}_{\text{hoy}}}{\text{empleadores hasta 50}_{\text{4T-23}}}`,
    leyenda: "Cantidad de empleadores de hasta 50 trabajadores con cobertura de ART (SRT), 100 = 4T-2023. Menos empleadores es peor.",
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
    leyenda: "Porcentaje de la cartera de consumo de las familias en situación irregular (Informe sobre Bancos, BCRA), ponderando la mora de personales y tarjetas por el saldo de cada línea. En el ITCIS puntúa por el nivel relativo al 4T-2023. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100.",
  },
  carga_servicio_deuda_hogares: {
    latex: String.raw`100\cdot\frac{\left(\frac{\text{servicio de deuda}}{\text{masa salarial registrada}}\right)_{\text{4T-23}}}{\left(\frac{\text{servicio de deuda}}{\text{masa salarial registrada}}\right)_{\text{hoy}}}`,
    leyenda: "Carga mensual de capital e intereses de las familias sobre la masa salarial registrada (CDF/MS, BCRA), con promedio móvil de tres meses en numerador y denominador. Se invierte al rebasear: más ingreso comprometido en deuda significa menor capacidad de pago y peor puntaje.",
  },
  subocupacion_demandante: {
    latex: String.raw`100\cdot\frac{\text{subocupaci\'on}_{\text{4T-23}}}{\text{subocupaci\'on}_{\text{hoy}}}`,
    leyenda: "Subocupación demandante (EPH): gente que necesita trabajar más horas. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100.",
  },
  informalidad: {
    latex: String.raw`100\cdot\frac{\text{informalidad}_{\text{4T-23}}}{\text{informalidad}_{\text{hoy}}}`,
    leyenda: "Asalariados sin descuento jubilatorio (EPH, trimestral). En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el de hoy abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora: si hoy hay menos que en 2023, el cociente supera 100. La card muestra la tasa del trimestre.",
  },
  consumo_carnes_total: {
    latex: String.raw`100\cdot\frac{\left(\text{vacuna}+\text{aviar}+\text{porcina}\right)\text{ por habitante}_{\text{hoy}}}{\left(\text{vacuna}+\text{aviar}+\text{porcina}\right)\text{ por habitante}_{\text{4T-23}}}`,
    leyenda: "Acceso total a proteína cárnica por habitante, promedio móvil de 12 meses, 100 = 4T-2023. La evolución se reconstruye desde la faena del INDEC; el nivel en kilos lo publica SAGYP.",
  },
  motorizacion_total: {
    latex: String.raw`100\cdot\frac{\left[\left(\sum_{12m}\text{autos}+\sum_{12m}\text{motos}\right)\,/\,\text{población}\right]_{\text{hoy}}}{\left[\left(\sum_{12m}\text{autos}+\sum_{12m}\text{motos}\right)\,/\,\text{población}\right]_{\text{4T-23}}}`,
    leyenda: "Inscripciones iniciales de autos y motos sumadas en una ventana móvil de doce meses, por habitante y rebaseadas a 100 = promedio del 4º trimestre de 2023. Tierra del Fuego se excluye de ambas patas por el movimiento registral documentado en la ficha.",
  },
  patentamiento_motos: {
    latex: String.raw`100\cdot\frac{\text{patentamientos, promedio 12 meses}_{\text{hoy}}}{\text{promedio 12 meses}_{\text{4T-23}}}`,
    leyenda: "Motos patentadas (CAFAM) en promedio móvil anual — desestacionalizado: enero patenta ≈ el doble que junio. La card muestra el mes crudo.",
  },
  patentamiento_autos: {
    latex: String.raw`100\cdot\frac{\text{inscripciones iniciales, promedio 12 meses}_{\text{hoy}}}{\text{promedio 12 meses}_{\text{4T-23}}}`,
    leyenda: "Autos 0km inscriptos en los registros de la propiedad del automotor (DNRPA) en promedio móvil anual — misma transformación que motos, y por el mismo motivo medido: enero pesa 1,36 veces el mes promedio y diciembre 0,57. La card muestra el mes crudo.",
  },
  consumo_supermercados: {
    latex: String.raw`100\cdot\frac{\text{ventas a precios constantes}_{\text{hoy}}}{\text{ventas a precios constantes}_{\text{4T-23}}}`,
    leyenda: "Índice de ventas en supermercados a precios constantes del INDEC, en la serie DESESTACIONALIZADA que publica el propio organismo. No se le aplica promedio móvil, a diferencia de motos y autos: la fuente ya le sacó el calendario, y volver a suavizarla con una media móvil de 12 meses la atrasaría medio año — probado, y ese atraso llega a invertir el signo de la correlación. Mide comercio registrado de cadenas: no ve el almacén de barrio ni el comercio informal.",
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
    latex: String.raw`100\cdot\frac{100}{\dfrac{1}{6}\sum_{i=1}^{6}100\cdot\dfrac{\text{b\'usquedas del t\'ermino }i_{\text{ mes}}}{\text{b\'usquedas del t\'ermino }i_{\text{ 4T-23}}}}`,
    leyenda: "Canasta de seis búsquedas en Google —inflación, precios, dólar, empleo, inseguridad y corrupción— sobre una ventana fija desde 2021. Cada término se consulta por separado y se compara contra su propio 4º trimestre de 2023: la escala de Google Trends es relativa a cada consulta, pero ese factor se cancela en el cociente, y por eso seis consultas distintas se pueden promediar sin necesidad de un término de anclaje. Los seis pesan lo mismo, un sexto cada uno; el promedio de valores crudos que se usaba antes repartía el peso por volumen de búsqueda, y ahí un solo término se llevaba la mitad del índice. Más búsquedas de urgencia = peor. En estos indicadores «al revés» la fórmula se invierte a propósito —el valor de 2023 va arriba y el del mes abajo— para que, igual que en todos los demás, un resultado por encima de 100 signifique mejora. Validación: correlación +0,61 con la inflación mensual.",
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
  apoyo_empresario: {
    latex: String.raw`\frac{\text{apoyos}_{\text{12 m}}-\text{cr\'iticas}_{\text{12 m}}}{\text{apoyos}_{\text{12 m}}+\text{cr\'iticas}_{\text{12 m}}}`,
    leyenda: "Comunicados institucionales fechados de la Asociación Empresaria Argentina (AEA) y la Unión Industrial Argentina (UIA). Cada comunicado se clasifica a mano en dos ejes: si respalda o critica lo que comenta, y a quién le habla. Sólo entran al cálculo los que se pronuncian sobre una medida del Gobierno nacional: los que informan una reunión, un acto o un cambio de autoridades no toman posición y quedan afuera, igual que los dirigidos al Congreso, a una provincia o a la Justicia. El resultado va de −1, si en doce meses todo fue crítica, a +1 si todo fue apoyo; cero significa que las cámaras apoyaron tanto como criticaron.",
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
  jornadas_individuales_no_trabajadas_12m: {
    latex: String.raw`\sum_{m=t-11}^{t}\sum_{p\in m}\left(\text{huelguistas}_{p}\times\text{duraci\'on}_{p}\right)`,
    leyenda: "Jornadas individuales no trabajadas por paros, acumuladas en doce meses. La metodología oficial permite sumar esta magnitud entre meses porque ya combina el tamaño y la duración del paro; no se suman conflictos ni huelguistas, que podrían repetirse.",
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
