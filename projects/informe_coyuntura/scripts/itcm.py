"""
ITCM — Índice de Tensión del Cinturón Macroeconómico.

Implementa la "Fórmula Paramétrica para Evaluación del Estado de Tensión —
Cinturón de la Macroeconomía" (Fundación CIGOB, mayo 2026). Escala 0-100:
0 = máxima tensión (cinturón apretado), 100 = mínima tensión (aflojado).

ITCM = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor))

La tensión 0-10 del informe se deriva como (100 − ITCM) / 10, así el resto
del pipeline (umbrales, estados, score global) conserva su convención.

Convención de bordes de banda (uniforme, pineada por tests/test_itcm.py):
cada banda es (low, high, puntaje) con low EXCLUSIVO y high INCLUSIVO.
El documento fuente es ambiguo en los límites exactos (ej. "50-60.000" y
"40-50.000" comparten el 50.000); esta convención lo resuelve de forma única.

Los puntajes salen siempre de las tablas. El juicio cualitativo del analista
(ej. "saldo comercial positivo pero por contracción") se expresa como override
en data/macro/ajustes_itcm.json, con justificación y vencimiento.

Revisiones sobre el doc original (observaciones del analista, docs
"260602 Parametrica Macro (2)" y "260626 aportes para el cinturon macro"):
  * REM: se puntúa por el EQUIVALENTE MENSUAL de la expectativa anual
    (raíz 12: (1+REM/100)^(1/12)−1), bandeado con la misma escala mensual del
    IPC. Pone las expectativas y la inflación realizada en la misma vara.
    El equivalente mensual se deriva en macro.py y alimenta la banda "rem_ipc_12m".
  * Recaudación: variación INTERANUAL REAL (deflactada por el IPC del mismo
    período), no la variación mensual nominal.
  * Reservas: NETAS "a secas" (el número del mercado), 100% datos oficiales y sin
    constantes: netas = SDDS estricto (Activos de reserva − drenajes Sección II de la
    Planilla SDDS) + depósitos del Tesoro en USD (balance BCRA) + Bopreal 12m (bucket
    de vencimiento 3m-1año de la Sección II.1 del SDDS). El mercado suma de vuelta
    Tesoro y Bopreal porque no son pasivos del BCRA para defender el TC. Escala propia
    (ver BANDAS_ITCM). BADLAR pasa a contexto.
  * Financiamiento: la tasa se reemplaza por el ÍNDICE DE CAPACIDAD PRESTABLE
    (IdC): Precio (BADLAR real, 30%), Volumen (depósitos privados reales, 40%)
    y Asignación (holgura préstamos/depósitos, 30%). Índice ~1,0 (>1,02 verde /
    0,98-1,02 amarillo / <0,98 rojo). Nota: el doc define A=1−R (un nivel ~0,14
    que rompe el semáforo); se implementa A como el RATIO mensual de holgura
    (1−R_t)/(1−R_{t-1}), que sí deja el índice centrado en 1,0 y reproduce el
    "amarillo" de mayo 2026 del doc. El IdC se computa en macro.py.

Incorporaciones de la 3ª tanda (propuesta "Índice de Desequilibrio Monetario"
+ tipo de cambio multilateral, jun-2026):
  * Estabilidad monetaria suma el IDM (Índice de Desequilibrio Monetario): la
    brecha entre el crecimiento de la oferta amplia de pesos privados (M3 privado)
    y la demanda transaccional (M2 privado). La propuesta original lo define como
    ΔM3 nominal − ΔM2 real mensual; esa fórmula está sesgada por la inflación
    (resta una tasa real de una nominal → da rojo permanente) y por la
    estacionalidad del aguinaldo. Se implementa la versión REAL-REAL INTERANUAL
    (ΔM3 priv. real i.a. − ΔM2 priv. real i.a.), que respeta la intención
    (oferta vs demanda real de pesos) sin esos defectos. El IDM se computa en
    macro.py a partir de circulante (var. 17) + depósitos privados (var. 100) y
    M2 privado transaccional (var. 197) del BCRA, deflactados por el IPC.
  * Nueva dimensión COMPETITIVIDAD EXTERNA (12%): el TCRM (ITCRM oficial del BCRA,
    base 2015=100) deja de ser contexto y puntúa. Apreciación real = atraso
    cambiario = más tensión. Las 4 dimensiones originales se recortan en
    proporción para hacer lugar (ver DIMENSIONES_ITCM).

Capítulo INVERSIÓN (docs "260629 INDICADOR DE INVERSION" + "260630 INVERSIÓN E IA",
jun-2026): nueva 6ª dimensión (12%) con dos indicadores compuestos calculados en
macro.py como promedios ponderados de variaciones interanuales:
  * IAI — Índice Anticipador de Inversión (físico): ISAC construcción + bienes de
    capital importados (+ patentamientos comerciales cuando haya histórico). Mide
    la inversión tradicional/tangible.
  * ICIP — Índice de Capitalización Inteligente: pagos al exterior de servicios de
    informática (software/cloud/IA) + productividad laboral (IPI/empleo). Mide la
    inversión digital/intangible. La lectura conjunta IAI vs ICIP expone la
    "trampa de la madurez" (invertir en ladrillos sin digitalizarse).
  El umbral ±2% de los docs no sobrevive al dato argentino (las series i.a. se
  mueven ±30-180% por la base 2024-2025): se usan BANDAS ANCHAS calibradas a la
  realidad, conservando la lógica contracción/neutro/expansión.
"""
import json
from pathlib import Path

INF = float("inf")

# Tablas de bandas de la sección IV del documento. (low, high, puntaje).
BANDAS_ITCM = {
    "ipc_total": [                      # % mensual
        (-INF, 1.0, 100), (1.0, 2.0, 85), (2.0, 3.0, 65), (3.0, 5.0, 40), (5.0, INF, 10),
    ],
    "rem_ipc_12m": [                    # EQUIVALENTE MENSUAL del REM (% mensual), raíz 12.
        # Valor DERIVADO en macro.py. Misma escala mensual que el IPC: pone la
        # expectativa anual en términos mensuales comparables a la inflación realizada.
        (-INF, 1.0, 100), (1.0, 2.0, 85), (2.0, 3.0, 65), (3.0, 5.0, 40), (5.0, INF, 10),
    ],
    "idm": [                            # Índice de Desequilibrio Monetario (pp, brecha i.a. real)
        # gap = crecimiento i.a. REAL del M3 privado − del M2 privado transaccional.
        # Negativo = la demanda real tracciona (remonetización genuina, baja tensión);
        # positivo = la masa amplia corre por encima de la demanda → excedente de pesos
        # que presiona la brecha cambiaria. Calibrado con la historia 2024-2026 (oct-24 a
        # may-26 va de −11 pp en la remonetización post-estabilización a +7 pp en el pico).
        (-INF, -2.0, 100), (-2.0, 2.0, 85), (2.0, 5.0, 60), (5.0, 8.0, 35), (8.0, INF, 10),
    ],
    "recaudacion": [                    # % var mensual
        (10.0, INF, 100), (5.0, 10.0, 80), (0.0, 5.0, 60), (-5.0, 0.0, 40), (-INF, -5.0, 10),
    ],
    "saldo_comercial_12m": [            # millones USD acumulado 12m
        (15000.0, INF, 85), (10000.0, 15000.0, 75), (5000.0, 10000.0, 60),
        (-5000.0, 5000.0, 50), (-15000.0, -5000.0, 30), (-INF, -15000.0, 10),
    ],
    "reservas_bcra": [                  # millones USD — RESERVAS NETAS (no brutas)
        (20000.0, INF, 100), (15000.0, 20000.0, 85), (10000.0, 15000.0, 70),
        (5000.0, 10000.0, 50), (0.0, 5000.0, 30), (-INF, 0.0, 10),
    ],
    "idc": [                            # Índice de Capacidad Prestable (~1,0). Semáforo del doc:
        # >1,02 verde · 0,98-1,02 amarillo · <0,98 rojo. Subdividido a 5 bandas.
        (1.04, INF, 100), (1.02, 1.04, 85), (0.98, 1.02, 60), (0.95, 0.98, 35), (-INF, 0.95, 10),
    ],
    "emae_ia": [                        # % variación interanual
        (5.0, INF, 100), (3.0, 5.0, 80), (0.0, 3.0, 60),
        (-2.0, 0.0, 40), (-5.0, -2.0, 20), (-INF, -5.0, 5),
    ],
    "tcrm": [                           # ITCRM oficial del BCRA (base 17-dic-2015=100)
        # Apreciación real = pérdida de competitividad y atraso cambiario = más tensión.
        # Bandas calibradas con la historia 1997-2026 (p10≈75, p25≈87, mediana≈106):
        # >110 competitivo · 95-110 cómodo (~nivel 2015) · 85-95 apreciación moderada ·
        # 75-85 apreciación marcada · ≤75 atraso severo.
        (110.0, INF, 100), (95.0, 110.0, 80), (85.0, 95.0, 60), (75.0, 85.0, 35), (-INF, 75.0, 10),
    ],
    "iai": [                            # IAI — Índice Anticipador de Inversión (% i.a. ponderado)
        # Inversión física (ISAC + bienes de capital importados). Más = expansión.
        # El umbral ±2% del doc no sobrevive al dato (las series i.a. de inversión
        # argentina se mueven ±30-180% por la base 2024); bandas ANCHAS calibradas a
        # la realidad 2024-2026 conservando la lógica contracción/neutro/expansión.
        (10.0, INF, 100), (2.0, 10.0, 80), (-2.0, 2.0, 60), (-10.0, -2.0, 35), (-INF, -10.0, 10),
    ],
    "icip": [                           # ICIP — Capitalización Inteligente (% i.a. ponderado)
        # Inversión digital/intangible (servicios tech + productividad). Más rápido y
        # volátil que la física (los pagos de servicios informáticos i.a. oscilan más),
        # de ahí la banda más ancha. Más = la economía se digitaliza más rápido.
        (20.0, INF, 100), (5.0, 20.0, 80), (-5.0, 5.0, 60), (-20.0, -5.0, 35), (-INF, -20.0, 10),
    ],
}

# Dimensiones del índice con su peso y la ponderación interna de indicadores.
# Pesos de dimensión: operacionalización propia. La Paramétrica CIGOB define las 4
# originales (35/30/20/15); las dimensiones 5ª (competitividad externa) y 6ª (inversión)
# y el recorte proporcional de las demás para hacerles lugar son extensión propia.
# Pisables vía data/macro/ajustes_itcm.json.
DIMENSIONES_ITCM = {
    "estabilidad_monetaria": {
        "nombre": "Estabilidad monetaria-inflacionaria",
        "peso": 0.26,
        "indicadores": {"ipc_total": 0.40, "rem_ipc_12m": 0.30, "idm": 0.30},
    },
    "viabilidad_fiscal_comercial": {
        "nombre": "Viabilidad fiscal-comercial",
        "peso": 0.24,
        "indicadores": {"recaudacion": 0.6, "saldo_comercial_12m": 0.4},
    },
    "financiamiento": {
        "nombre": "Capacidad de financiamiento",
        "peso": 0.16,
        "indicadores": {"reservas_bcra": 0.5, "idc": 0.5},
    },
    "actividad": {
        "nombre": "Actividad económica",
        "peso": 0.11,
        "indicadores": {"emae_ia": 1.0},
    },
    "competitividad_externa": {
        "nombre": "Competitividad externa",
        "peso": 0.11,
        "indicadores": {"tcrm": 1.0},
    },
    "inversion": {
        "nombre": "Inversión",
        "peso": 0.12,
        "indicadores": {"iai": 0.6, "icip": 0.4},
    },
}

# Interpretación del ITCM (sección VI del documento). (low, high, etiqueta).
BANDAS_INTERPRETACION = [
    (-INF, 20.0, "severamente_apretado"),
    (20.0, 40.0, "apretado"),
    (40.0, 60.0, "moderadamente_apretado"),
    (60.0, 80.0, "moderadamente_aflojado"),
    (80.0, INF, "aflojado"),
]

INTERPRETACION_LEGIBLE = {
    "severamente_apretado":   "Severamente apretado",
    "apretado":               "Apretado",
    "moderadamente_apretado": "Moderadamente apretado",
    "moderadamente_aflojado": "Moderadamente aflojado",
    "aflojado":               "Aflojado",
}

# Indicadores macro que se publican pero no integran el índice.
# badlar: ya no integra el índice (la dimensión de financiamiento usa el IdC);
# se sigue publicando como contexto e insumo del IdC (tasa pasiva de referencia).
# tcrm SALIÓ de contexto: ahora puntúa en la dimensión competitividad_externa.
INDICADORES_CONTEXTO = ["badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"]


def puntaje_banda(valor: float, bandas: list) -> int:
    """Puntaje de la banda donde cae `valor` (low exclusivo, high inclusivo)."""
    for low, high, puntaje in bandas:
        if low < valor <= high:
            return puntaje
    raise ValueError(f"valor {valor} fuera de toda banda")


def banda_interpretacion(itcm: float) -> str:
    for low, high, etiqueta in BANDAS_INTERPRETACION:
        if low < itcm <= high:
            return etiqueta
    raise ValueError(f"ITCM {itcm} fuera de rango")


def tension_de_itcm(itcm: float) -> float:
    """Tensión 0-10 del cinturón (convención del informe) derivada del ITCM."""
    return round((100.0 - itcm) / 10.0, 1)


def anualizar_mensual(var_m_pct: float) -> float:
    """Tasa anual equivalente (capitalización) de una variación mensual %."""
    return ((1.0 + var_m_pct / 100.0) ** 12 - 1.0) * 100.0


def rem_mensual_equivalente(rem_anual_pct: float) -> float:
    """Equivalente mensual (raíz 12) de la expectativa de inflación anual del
    REM: (1+REM/100)^(1/12)−1, en %. Permite bandear el REM con la misma escala
    mensual del IPC. Ej.: REM 23,3% → 1,76% mensual."""
    return ((1.0 + rem_anual_pct / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0


# Ponderación interna del Índice de Capacidad Prestable (doc "260626 aportes").
IDC_PESOS = {"precio": 0.30, "volumen": 0.40, "asignacion": 0.30}


def indice_capacidad_prestable(precio: float, volumen: float, asignacion: float) -> float:
    """IdC = 0,30·Precio + 0,40·Volumen + 0,30·Asignación (componentes ~1,0).
    Precio = 1 + tasa real mensual de la BADLAR; Volumen = ratio mensual de
    depósitos privados reales; Asignación = ratio mensual de holgura prestable
    (1−R_t)/(1−R_{t-1}), R = préstamos/depósitos. Devuelve un índice centrado
    en 1,0 (mayor = más capacidad prestable / crédito más fluido)."""
    return (IDC_PESOS["precio"] * precio
            + IDC_PESOS["volumen"] * volumen
            + IDC_PESOS["asignacion"] * asignacion)


def texto_bandas(indicador: str) -> str:
    """Texto legible de la tabla de bandas, para transparencia en el frontend."""
    partes = []
    for low, high, puntaje in BANDAS_ITCM[indicador]:
        if low == -INF:
            rango = f"≤{_num(high)}"
        elif high == INF:
            rango = f">{_num(low)}"
        else:
            rango = f"{_num(low)}–{_num(high)}"
        partes.append(f"{rango} → {puntaje}")
    return " · ".join(partes)


def _num(x: float) -> str:
    s = f"{x:g}"
    return s.replace(".", ",")


def ajuste_automatico_saldo(ind_saldo: dict) -> dict | None:
    """Regla automática del "Subcomponente D" de la Paramétrica: un superávit
    comercial que refleja caída de demanda interna (menos importaciones) más
    que aumento de exportaciones es sintomático de apretamiento y se ajusta
    a 60 puntos (el valor que aplica el documento en su ejemplo).

    Condición (sobre acumulados 12m vs los 12m previos): hay superávit con
    banda > 60, las importaciones CAEN, y esa caída explica más de la mejora
    del saldo que el aumento de exportaciones. Requiere la composición
    expo/impo que produce fetch_saldo_comercial_12m; sin esos campos (ej.
    fallback a la serie de saldo directa) no opina y devuelve None.
    """
    valor = ind_saldo.get("valor")
    d_expo = ind_saldo.get("expo_delta_12m")
    d_impo = ind_saldo.get("impo_delta_12m")
    if valor is None or d_expo is None or d_impo is None:
        return None
    if valor <= 5000:                # sin superávit relevante: la banda ya lo castiga
        return None
    if puntaje_banda(float(valor), BANDAS_ITCM["saldo_comercial_12m"]) <= 60:
        return None
    if d_impo >= 0:                  # importaciones creciendo: no hay contracción
        return None
    if -d_impo <= max(0.0, d_expo):  # la caída de impo no domina la mejora del saldo
        return None
    expo_var = ind_saldo.get("expo_var_ia")
    impo_var = ind_saldo.get("impo_var_ia")
    return {
        "puntaje": 60,
        "justificacion": (
            f"Regla automática: superávit explicado por contracción de importaciones "
            f"({impo_var:+.1f}% i.a.) más que por exportaciones ({expo_var:+.1f}% i.a.) "
            f"— sintomático de caída de demanda interna (Paramétrica CIGOB, may-2026)."
        ),
        "origen": "automatico",
    }


def cargar_ajustes(path: Path, periodo: str) -> dict:
    """Lee los overrides del analista vigentes para `periodo` (YYYY-MM).

    Formato del archivo: {indicador: {puntaje, justificacion, vigente_hasta}}.
    Un ajuste con vigente_hasta < periodo está vencido y se ignora (evita
    overrides zombis). Archivo ausente o vacío → sin ajustes.
    """
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        ajustes = json.load(f)
    return {
        nombre: spec for nombre, spec in ajustes.items()
        if spec.get("vigente_hasta", "9999-12") >= periodo
    }


def calcular_itcm(valores: dict, ajustes: dict | None = None) -> dict | None:
    """Calcula el ITCM a partir de {indicador: valor} (valores None se ignoran).

    Renormaliza pesos ante faltantes: dentro de cada dimensión entre los
    indicadores presentes, y entre dimensiones si alguna queda vacía
    (consistente con el "ignorar ausencias" del resto del informe).

    Devuelve {valor, banda, dimensiones, ajustes_aplicados} o None si no hay
    ningún indicador del índice disponible. `peso_efectivo` por indicador es
    el peso final post-renormalización (suman 1.0 entre los presentes).
    """
    ajustes = ajustes or {}
    dimensiones = {}
    ajustes_aplicados = []

    for dkey, dim in DIMENSIONES_ITCM.items():
        presentes = {}
        for ikey, peso in dim["indicadores"].items():
            valor = valores.get(ikey)
            if valor is None:
                continue
            p_banda = puntaje_banda(float(valor), BANDAS_ITCM[ikey])
            p_aplicado = p_banda
            if ikey in ajustes:
                p_aplicado = ajustes[ikey]["puntaje"]
                ajustes_aplicados.append({
                    "indicador": ikey,
                    "de": p_banda,
                    "a": p_aplicado,
                    "justificacion": ajustes[ikey].get("justificacion", ""),
                    "origen": ajustes[ikey].get("origen", "manual"),
                })
            presentes[ikey] = {"peso": peso, "puntaje_banda": p_banda,
                               "puntaje_aplicado": p_aplicado}
        if not presentes:
            continue
        suma_pesos = sum(i["peso"] for i in presentes.values())
        for info in presentes.values():
            info["peso_renorm"] = info["peso"] / suma_pesos
        puntaje_dim = sum(i["puntaje_aplicado"] * i["peso_renorm"] for i in presentes.values())
        dimensiones[dkey] = {
            "nombre": dim["nombre"],
            "peso": dim["peso"],
            "puntaje": round(puntaje_dim, 1),
            "indicadores": presentes,
        }

    if not dimensiones:
        return None

    suma_dim = sum(d["peso"] for d in dimensiones.values())
    itcm = 0.0
    for d in dimensiones.values():
        d["peso_efectivo"] = round(d["peso"] / suma_dim, 4)
        itcm += d["puntaje"] * d["peso"] / suma_dim
        for info in d["indicadores"].values():
            info["peso_efectivo"] = round(info["peso_renorm"] * d["peso"] / suma_dim, 4)
            del info["peso_renorm"]
    itcm = round(itcm, 1)

    return {
        "valor": itcm,
        "banda": banda_interpretacion(itcm),
        "banda_legible": INTERPRETACION_LEGIBLE[banda_interpretacion(itcm)],
        "dimensiones": dimensiones,
        "ajustes_aplicados": ajustes_aplicados,
    }
