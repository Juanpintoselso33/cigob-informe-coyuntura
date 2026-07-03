// Fórmula de composición de cada indicador (LaTeX, renderizada con KaTeX en
// el modal). La fórmula muestra CÓMO SE CONSTRUYE el valor publicado — pesos
// y transformaciones verificados contra los colectores (scripts/*.py).
// Los indicadores sin entrada simplemente no muestran la sección.

export interface Formula {
  latex: string;
  leyenda?: string;
}

export const FORMULAS: Record<string, Formula> = {
  // ── Macro (ITCM) ─────────────────────────────────────────────────────────
  ipc_total: {
    latex: String.raw`\mathrm{IPC}_m=\left(\frac{P_t}{P_{t-1}}-1\right)\times 100`,
    leyenda: "P = nivel del IPC nacional (INDEC).",
  },
  rem_ipc_12m: {
    latex: String.raw`\mathrm{REM}_{\mathrm{mens}}=\left[\left(1+\tfrac{\mathrm{REM}_{12m}}{100}\right)^{1/12}-1\right]\times 100`,
    leyenda: "La expectativa anual del REM se convierte a equivalente mensual (raíz 12) para puntuarla en la misma escala que el IPC (ADR-0002).",
  },
  idm: {
    latex: String.raw`\mathrm{IDM}=g^{\mathrm{real}}_{M3^{\mathrm{priv}}}-g^{\mathrm{real}}_{M2^{\mathrm{priv}}}`,
    leyenda: "Crecimientos interanuales REALES (deflactados por IPC). M3 privado = circulante + depósitos privados (oferta amplia); M2 privado = demanda transaccional. Positivo = excedente de pesos.",
  },
  recaudacion: {
    latex: String.raw`g^{\mathrm{real}}=\left(\frac{R_t}{R_{t-12}}\cdot\frac{\mathrm{IPC}_{t-12}}{\mathrm{IPC}_t}-1\right)\times 100`,
    leyenda: "R = recaudación total mensual; variación interanual deflactada (ADR-0003).",
  },
  saldo_comercial_12m: {
    latex: String.raw`S_{12m}=\sum_{i=0}^{11}\left(X_{t-i}-M_{t-i}\right)`,
    leyenda: "X, M = exportaciones e importaciones mensuales del ICA (INDEC), acumulado 12 meses en millones de USD.",
  },
  reservas_bcra: {
    latex: String.raw`R^{\mathrm{netas}}=R^{\mathrm{SDDS\;estricto}}+\mathrm{Dep.\;Tesoro}`,
    leyenda: "Planilla SDDS del BCRA (brutas − drenajes de la Sección II: swap, encajes en USD, BIS/Sedesa) + depósitos del Tesoro en USD del balance (ADR-0005).",
  },
  idc: {
    latex: String.raw`\mathrm{IdC}=0{,}30\,P+0{,}40\,V+0{,}30\,A`,
    leyenda: "P = precio del dinero (BADLAR real) · V = volumen (depósitos privados reales) · A = asignación (préstamos/depósitos). Semáforo alrededor de 1 (ADR-0004).",
  },
  credito_privado: {
    latex: String.raw`g^{\mathrm{real}}_{ia}=\left(\frac{1+g^{\mathrm{nom}}_{ia}}{1+\pi_{ia}}-1\right)\times 100`,
    leyenda: "Préstamos al sector privado (BCRA), variación interanual nominal deflactada por la inflación interanual (ADR-0022).",
  },
  emae_ia: {
    latex: String.raw`g_{ia}=\left(\frac{\mathrm{EMAE}_t}{\mathrm{EMAE}_{t-12}}-1\right)\times 100`,
  },
  tcrm: {
    latex: String.raw`\mathrm{ITCRM}_t\quad(\text{base 17-dic-2015}=100)`,
    leyenda: "Índice de Tipo de Cambio Real Multilateral oficial del BCRA (ADR-0008): nivel bajo = peso apreciado = menos competitividad.",
  },
  iai: {
    latex: String.raw`\mathrm{IAI}=0{,}55\,g_{\mathrm{ISAC}}+0{,}30\,g_{\mathrm{BK}}+0{,}15\,g_{\mathrm{pat}}`,
    leyenda: "Variaciones interanuales: construcción (ISAC), bienes de capital importados y patentamientos comerciales. Sin patentamientos renormaliza a 0,65/0,35 (ADR-0010).",
  },
  icip: {
    latex: String.raw`\mathrm{ICIP}=0{,}57\,g_{\mathrm{svc\,tech}}+0{,}43\,g_{\mathrm{prod}}`,
    leyenda: "Pagos al exterior de servicios de informática (i.a.) + productividad laboral (IPI/empleo, i.a.) — ADR-0010.",
  },

  // ── Gestión (ITCG) ───────────────────────────────────────────────────────
  cepo_mulc: {
    latex: String.raw`\mathrm{brecha}=\left(\frac{\mathrm{CCL}}{\mathrm{TC}_{\mathrm{mayorista}}}-1\right)\times 100`,
    leyenda: "CCL implícito en bonos vs tipo de cambio mayorista A3500 (ADR-0006).",
  },
  apertura_comercial: {
    latex: String.raw`\alpha=\frac{\mathrm{Rec}_{\mathrm{DEX}}+\mathrm{Rec}_{\mathrm{DIM}}}{(X+M)_{\mathrm{ICA}}}\times 100`,
    leyenda: "Derechos de exportación + importación (ARCA, convertidos a USD por el A3500 promedio del mes) sobre el intercambio total del ICA (ADR-0021).",
  },
  desregulacion_normativa: {
    latex: String.raw`D=\min\!\left(100,\;N_{\mathrm{deroga}}\right)`,
    leyenda: "N = normas publicadas desde dic-2023 con texto derogatorio (InfoLeg). Calibración: 100 normas derogantes = plan completo.",
  },
  reduccion_estado: {
    latex: String.raw`\Delta=\left(\frac{\mathrm{Dotaci\acute{o}n}_t}{\mathrm{Dotaci\acute{o}n}_{\mathrm{dic\text{-}23}}}-1\right)\times 100`,
    leyenda: "Dotación de personal de la APN (base de empleo público).",
  },
  gasto_funcionamiento: {
    latex: String.raw`g^{\mathrm{real}}=\left(\frac{G_t}{G_{2023}}\cdot\frac{\mathrm{IPC}_{2023}}{\mathrm{IPC}_t}-1\right)\times 100`,
    leyenda: "G = gasto de funcionamiento devengado (Presupuesto Abierto), comparación real vs 2023.",
  },
  masa_salarial: {
    latex: String.raw`g^{\mathrm{real}}=\left(\frac{W_t}{W_{2023}}\cdot\frac{\mathrm{IPC}_{2023}}{\mathrm{IPC}_t}-1\right)\times 100`,
    leyenda: "W = masa salarial devengada del personal (Presupuesto Abierto), comparación real vs 2023.",
  },
  reestructuracion_organismos: {
    latex: String.raw`R=\min\!\left(100,\;\frac{N_{\mathrm{disol}}}{45}\times 100\right)`,
    leyenda: "N = actos con disolución/reestructuración desde dic-2023 (InfoLeg). Calibración validada: 18 actos = 40%.",
  },
  fal_modernizacion_laboral: {
    latex: String.raw`\mathrm{FAL}=\frac{0{,}40\,C+0{,}30\,F}{0{,}40+0{,}30}\,,\qquad F=\min\!\left(100,\;n_{\mathrm{FCI}}\cdot\tfrac{100}{n_{\mathrm{pleno}}}\right)`,
    leyenda: "C = cobertura de CCT con cláusula de cese (estimada) · F = adopción financiera (FCI de cese registrados en CNV). El tercer componente del doc (litigiosidad diferencial) no tiene fuente y los pesos renormalizan.",
  },
  litigiosidad_laboral: {
    latex: String.raw`\Delta J=\left(\frac{\sum_{12m}J_t}{\sum_{12m}J_{t-12}}-1\right)\times 100`,
    leyenda: "J = juicios mensuales del sistema de riesgos del trabajo (SRT): acumulado móvil de 12 meses contra los 12 previos (ADR-0023).",
  },
  privatizaciones: {
    latex: String.raw`P=\frac{\overline{\mathrm{etapa}}}{4}\times 100`,
    leyenda: "Cada empresa de la cartera Ley Bases se puntúa 0–4 (sin definir → preparatoria → pliegos → licitación → cerrada) con fecha del Boletín Oficial; P = promedio de la cartera.",
  },
  rigi_inversiones: {
    latex: String.raw`\mathrm{RIGI}=\frac{I_{\mathrm{aprobada}}}{I_{\mathrm{aprobada}}+I_{\mathrm{en\;evaluaci\acute{o}n}}}\times 100`,
    leyenda: "Inversión en USD de la plataforma oficial del RIGI (ADR-0011).",
  },
  concesiones_infraestructura: {
    latex: String.raw`C=\frac{\mathrm{km}_{\mathrm{adjudicados}}}{\mathrm{km}_{\mathrm{plan}}}\times 100`,
    leyenda: "Red Federal de Concesiones por etapas (CONTRAT.AR + Boletín Oficial, ADR-0016).",
  },
  asistencia_directa: {
    latex: String.raw`\mathrm{TDPS}=\frac{\mathrm{devengado}_{5.1.4}}{\mathrm{devengado}_{\mathrm{transferencias}}}\times 100`,
    leyenda: "Partida 5.1.4 (transferencias directas a personas) sobre el total de transferencias de los programas sucesores del Potenciar (API Presupuesto Abierto, ADR-0015).",
  },
  protocolo_antipiquetes: {
    latex: String.raw`\mathrm{IRPC}=\left(1-\frac{\mathrm{cortes}_t}{\mathrm{cortes}_{2023}}\right)\times 100`,
    leyenda: "Reducción porcentual de cortes de calle vs el promedio 2023.",
  },
  libertad_opcion_salud: {
    latex: String.raw`L=\frac{\mathrm{usuarios\;con\;derivaci\acute{o}n\;directa}}{\mathrm{usuarios\;de\;prepagas\;(RNEMP)}}\times 100`,
    leyenda: "Padrones oficiales de la SSS: aportes derivados directo a prepagas inscriptas como Agente del Seguro (RNAS, DNU 70/23) — ADR-0016.",
  },

  // ── Vida cotidiana (ITVC-B100: índices 100 = promedio 4T-2023) ──────────
  brecha_salario_cbt: {
    latex: String.raw`B=\frac{\mathrm{RIPTE}}{\mathrm{CBT}_{\mathrm{hogar}}}`,
    leyenda: "Cuántas canastas básicas totales (hogar tipo) compra el salario registrado promedio. Al ITVC entra rebaseado: 100 = promedio 4T-2023.",
  },
  ipc_alimentos: {
    latex: String.raw`I_{IA}=100\cdot\frac{\left(\mathrm{RIPTE}/P^{\mathrm{alim}}\right)_t}{\left(\mathrm{RIPTE}/P^{\mathrm{alim}}\right)_{4T23}}`,
    leyenda: "Poder de compra de alimentos del salario: RIPTE sobre el NIVEL del IPC Alimentos, 100 = 4T-2023 (la card muestra la variación mensual).",
  },
  peso_tarifas: {
    latex: String.raw`I_{PT}=100\cdot\frac{\left(\mathrm{RIPTE}/P^{\mathrm{reg}}\right)_t}{\left(\mathrm{RIPTE}/P^{\mathrm{reg}}\right)_{4T23}}`,
    leyenda: "Peso de los servicios regulados (tarifas) en el salario: RIPTE sobre el NIVEL del IPC Regulados, 100 = 4T-2023. Debajo de 100 = las tarifas pesan más que en la base.",
  },
  mortalidad_pymes: {
    latex: String.raw`I_{IPI}=100\cdot\frac{\mathrm{IPI}^{\mathrm{s.e.}}_t}{\overline{\mathrm{IPI}^{\mathrm{s.e.}}}_{4T23}}`,
    leyenda: "Nivel del IPI manufacturero desestacionalizado como proxy de la salud de las pymes industriales, 100 = 4T-2023.",
  },
  despacho_cemento: {
    latex: String.raw`I_{ISC}=100\cdot\frac{\mathrm{ISAC}^{\mathrm{s.e.}}_t}{\overline{\mathrm{ISAC}^{\mathrm{s.e.}}}_{4T23}}`,
    leyenda: "Nivel del ISAC desestacionalizado (construcción = el sector más intensivo en empleo), 100 = 4T-2023.",
  },
  endeudamiento_familiar: {
    latex: String.raw`I_{EC}=100\cdot\frac{D^{\mathrm{real}}_t}{D^{\mathrm{real}}_{4T23}}\cdot\frac{\mathrm{mora}_{4T23}}{\mathrm{mora}_t}`,
    leyenda: "D = crédito de consumo de familias (personales + tarjetas, Informe sobre Bancos BCRA) en términos reales, corregido por la tasa de irregularidad: deuda subiendo con mora estable = acceso; con mora disparada = fragilidad (ADR-0018).",
  },
  pluriempleo: {
    latex: String.raw`I=100\cdot\frac{p_{4T23}}{p_t}`,
    leyenda: "p = subocupación demandante (EPH). Invertido: más gente necesitando otro empleo = índice más bajo.",
  },
  consumo_carne: {
    latex: String.raw`I=100\cdot\frac{\mathrm{kg}^{\mathrm{PM12m}}_t}{\mathrm{kg}^{\mathrm{PM12m}}_{4T23}}`,
    leyenda: "Consumo per cápita de carne vacuna anualizado (promedio móvil 12 meses, CICCRA), 100 = 4T-2023.",
  },
  patentamiento_motos: {
    latex: String.raw`I=100\cdot\frac{\overline{\mathrm{pat}}_{12m}(t)}{\overline{\mathrm{pat}}_{12m}(4T23)}`,
    leyenda: "Promedio móvil de 12 meses de patentamientos (CAFAM) — desestacionalizado por ventana anual (ADR-0024: enero patenta ≈ 2× junio). La card muestra el flujo mensual crudo.",
  },
  inseguridad: {
    latex: String.raw`I=100\cdot\frac{H_{2023}}{H_t}`,
    leyenda: "H = hechos delictivos anuales (SNIC). Invertido: más hechos = índice más bajo. Frecuencia anual (excepción declarada del doc).",
  },
  icc_utdt: {
    latex: String.raw`I=100\cdot\frac{\mathrm{ICC}_t}{\overline{\mathrm{ICC}}_{4T23}}`,
    leyenda: "Índice de Confianza del Consumidor (UTDT) rebaseado, 100 = promedio 4T-2023.",
  },
  sentimiento_digital: {
    latex: String.raw`S=\frac{1}{k}\sum_{i=1}^{k}\mathrm{inter\acute{e}s}_i`,
    leyenda: "Promedio del interés de búsqueda (Google Trends, 0–100 relativo a la ventana de 3 meses) sobre k palabras clave de urgencia económica.",
  },

  // ── Política ─────────────────────────────────────────────────────────────
  eficacia_legislativa: {
    latex: String.raw`E=\frac{\mathrm{aprobados}_{12m}}{\mathrm{enviados}_{12m}}\times 100`,
    leyenda: "Proyectos del Ejecutivo aprobados sobre enviados, ventana móvil de 12 meses (datos abiertos HCDN).",
  },
  votometro_ventaja_lla: {
    latex: String.raw`\Delta=\mathrm{intenci\acute{o}n}_{\mathrm{LLA}}-\mathrm{intenci\acute{o}n}_{\mathrm{PJ}}`,
    leyenda: "Gap de intención de voto en puntos porcentuales (agregador Votómetro: encuestas ponderadas por calidad y recencia).",
  },
  clima_electoral: {
    latex: String.raw`\Delta=\mathrm{intenci\acute{o}n}_{\mathrm{LLA}}-\mathrm{intenci\acute{o}n}_{\mathrm{PJ}}`,
    leyenda: "Gap de intención de voto en puntos porcentuales (Votómetro).",
  },
};
