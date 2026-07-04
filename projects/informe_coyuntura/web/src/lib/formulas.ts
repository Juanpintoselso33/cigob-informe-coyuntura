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
  recaudacion: {
    latex: String.raw`\left(\frac{\text{recaudaci\'on}_{\text{hoy}}}{\text{recaudaci\'on}_{\text{hace 12 m}}}\cdot\frac{\text{IPC}_{\text{hace 12 m}}}{\text{IPC}_{\text{hoy}}}-1\right)\times 100`,
    leyenda: "Variación interanual de la recaudación total, descontada la inflación: cuánto crece en serio, no por suba de precios.",
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
    latex: String.raw`0{,}30\cdot\underbrace{z_{\text{tasa real}}}_{\text{precio}}\;+\;0{,}40\cdot\underbrace{z_{\text{dep\'ositos}}}_{\text{volumen}}\;+\;0{,}30\cdot\underbrace{z_{\text{holgura}}}_{\text{asignaci\'on}}\qquad z=\frac{\text{nivel de hoy}-\text{promedio hist\'orico}}{\text{desv\'io hist\'orico}}`,
    leyenda: "Cada componente se compara con su propia historia (2018 a hoy) y se expresa en desvíos estándar: la tasa real que reciben los depositantes, el crecimiento interanual real de los depósitos privados (la comparación interanual absorbe la estacionalidad) y la holgura que queda para prestar (1 − préstamos/depósitos). Cero es el mes histórico típico; por encima de +0,5 la capacidad de fondeo es mayor a la habitual, por debajo de −0,5, menor.",
  },
  credito_privado: {
    latex: String.raw`\left(\frac{1+\text{crecim. nominal del cr\'edito}}{1+\text{inflaci\'on}}-1\right)\times 100`,
    leyenda: "Préstamos al sector privado (BCRA), variación interanual descontada la inflación: el crédito que efectivamente llegó, no el que infló la nominalidad.",
  },
  emae_ia: {
    latex: String.raw`\left(\frac{\text{actividad}_{\text{hoy}}}{\text{actividad}_{\text{hace 12 m}}}-1\right)\times 100`,
    leyenda: "EMAE (INDEC): el PIB mensual, comparado contra el mismo mes del año pasado.",
  },
  tcrm: {
    latex: String.raw`\text{ITCRM}_{\text{hoy}}\qquad(\text{base dic-2015}=100)`,
    leyenda: "Tipo de cambio real multilateral oficial del BCRA: cuánto vale el peso contra las monedas de los socios comerciales, descontadas las inflaciones. Bajo = peso caro = exportar cuesta más.",
  },
  iai: {
    latex: String.raw`0{,}55\cdot\text{construcci\'on}\;+\;0{,}30\cdot\text{bienes de capital}\;+\;0{,}15\cdot\text{patentamientos}`,
    leyenda: "Variaciones interanuales de la inversión física: ISAC, importación de bienes de capital y patentamientos comerciales. Sin patentamientos, renormaliza a 0,65/0,35.",
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
    latex: String.raw`\min\left(100,\;\text{normas derogatorias desde dic-2023}\right)`,
    leyenda: "Conteo de normas publicadas con texto derogatorio (InfoLeg). Calibración: 100 normas = plan desregulador completo.",
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
    latex: String.raw`\frac{0{,}40\cdot\text{cobertura (menciones BO)}+0{,}30\cdot\text{fondos de cese en CNV}}{0{,}40+0{,}30}`,
    leyenda: "Adopción del Fondo de Cese: cobertura medida por menciones del instrumento en el Boletín Oficial desde la Ley Bases (420 = plena) + fondos registrados en la CNV (10 = plena). El tercer componente del doc (litigiosidad diferencial) no tiene fuente pública y los pesos se renormalizan.",
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
    leyenda: "Montos en USD de la plataforma oficial del RIGI: cuánto del pipeline ya tiene luz verde.",
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
    leyenda: "Padrones oficiales de la SSS: cuántos usuarios ya derivan sus aportes directo (canal creado por el DNU 70/23), sin triangular por una obra social.",
  },

  // ── Vida cotidiana (ITVC-B100: índices 100 = promedio 4T-2023) ──────────
  brecha_salario_cbt: {
    latex: String.raw`\frac{\text{salario registrado promedio (RIPTE)}}{\text{canasta b\'asica total del hogar}}`,
    leyenda: "Cuántas canastas de pobreza compra un sueldo. Al ITVC entra rebaseado: 100 = arranque del mandato (4T-2023).",
  },
  ipc_alimentos: {
    latex: String.raw`100\cdot\frac{\left(\text{salario}\,/\,\text{precio de alimentos}\right)_{\text{hoy}}}{\left(\text{salario}\,/\,\text{precio de alimentos}\right)_{\text{4T-23}}}`,
    leyenda: "Poder de compra de alimentos del salario: cuántos alimentos compra el salario registrado hoy contra el arranque del mandato. Más de 100 = el salario rinde más en la góndola. (La card muestra la variación mensual del rubro.)",
  },
  peso_tarifas: {
    latex: String.raw`100\cdot\frac{\left(\text{salario}\,/\,\text{tarifas}\right)_{\text{hoy}}}{\left(\text{salario}\,/\,\text{tarifas}\right)_{\text{4T-23}}}`,
    leyenda: "Cuántas facturas de servicios regulados paga el sueldo, contra el arranque del mandato. Debajo de 100 = las tarifas pesan más en el bolsillo que en 2023 (fin de subsidios).",
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
    latex: String.raw`100\cdot\frac{\text{deuda real de las familias}_{\text{hoy}}}{\text{deuda real}_{\text{4T-23}}}\cdot\frac{\text{mora}_{\text{4T-23}}}{\text{mora}_{\text{hoy}}}`,
    leyenda: "Crédito de consumo (tarjetas + personales, BCRA) descontada la inflación, corregido por la mora: deuda que sube con mora estable = acceso al crédito (bueno); deuda que sube con mora disparada = endeudarse para llegar a fin de mes (malo).",
  },
  pluriempleo: {
    latex: String.raw`100\cdot\frac{\text{subocupaci\'on}_{\text{4T-23}}}{\text{subocupaci\'on}_{\text{hoy}}}`,
    leyenda: "Subocupación demandante (EPH): gente que necesita trabajar más horas. Invertido: si sube, el índice baja.",
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
    latex: String.raw`100\cdot\frac{\text{delitos}_{2023}}{\text{delitos}_{\text{hoy}}}`,
    leyenda: "Hechos delictivos anuales (SNIC). Invertido: más delitos = índice más bajo. Frecuencia anual (excepción declarada del doc).",
  },
  icc_utdt: {
    latex: String.raw`100\cdot\frac{\text{confianza del consumidor}_{\text{hoy}}}{\text{confianza}_{\text{4T-23}}}`,
    leyenda: "ICC de la Universidad Torcuato Di Tella, rebaseado al arranque del mandato.",
  },
  sentimiento_digital: {
    latex: String.raw`\frac{\text{suma del inter\'es de b\'usqueda por palabra clave}}{\text{cantidad de palabras clave}}`,
    leyenda: "Google Trends (0–100, relativo a la ventana de 3 meses): cuánto busca la gente sobre inflación, precios y trabajo — urgencia económica percibida en tiempo real.",
  },

  // ── Política ─────────────────────────────────────────────────────────────
  eficacia_legislativa: {
    latex: String.raw`\frac{\text{proyectos del Ejecutivo aprobados}_{\text{12 m}}}{\text{proyectos enviados}_{\text{12 m}}}\times 100`,
    leyenda: "Ventana móvil de 12 meses sobre los datos abiertos de la Cámara de Diputados.",
  },
  votometro_ventaja_lla: {
    latex: String.raw`\text{intenci\'on de voto LLA}-\text{intenci\'on de voto PJ}`,
    leyenda: "Gap en puntos porcentuales del agregador Votómetro (encuestas ponderadas por calidad y recencia).",
  },
  clima_electoral: {
    latex: String.raw`\text{intenci\'on de voto LLA}-\text{intenci\'on de voto PJ}`,
    leyenda: "Gap en puntos porcentuales (Votómetro).",
  },
};
