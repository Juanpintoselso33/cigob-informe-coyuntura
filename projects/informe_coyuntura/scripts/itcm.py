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
"""
import json
from pathlib import Path

INF = float("inf")

# Tablas de bandas de la sección IV del documento. (low, high, puntaje).
BANDAS_ITCM = {
    "ipc_total": [                      # % mensual
        (-INF, 1.0, 100), (1.0, 2.0, 85), (2.0, 3.0, 65), (3.0, 5.0, 40), (5.0, INF, 10),
    ],
    "rem_ipc_12m": [                    # % anual esperado
        (-INF, 10.0, 100), (10.0, 15.0, 85), (15.0, 20.0, 60), (20.0, 30.0, 35), (30.0, INF, 10),
    ],
    "recaudacion": [                    # % var mensual
        (10.0, INF, 100), (5.0, 10.0, 80), (0.0, 5.0, 60), (-5.0, 0.0, 40), (-INF, -5.0, 10),
    ],
    "saldo_comercial_12m": [            # millones USD acumulado 12m
        (15000.0, INF, 85), (10000.0, 15000.0, 75), (5000.0, 10000.0, 60),
        (-5000.0, 5000.0, 50), (-15000.0, -5000.0, 30), (-INF, -15000.0, 10),
    ],
    "reservas_bcra": [                  # millones USD
        (60000.0, INF, 100), (50000.0, 60000.0, 85), (40000.0, 50000.0, 70),
        (30000.0, 40000.0, 50), (20000.0, 30000.0, 30), (-INF, 20000.0, 10),
    ],
    "badlar": [                         # % anual
        (-INF, 5.0, 100), (5.0, 10.0, 80), (10.0, 15.0, 60), (15.0, 25.0, 35), (25.0, INF, 10),
    ],
    "emae_ia": [                        # % variación interanual
        (5.0, INF, 100), (3.0, 5.0, 80), (0.0, 3.0, 60),
        (-2.0, 0.0, 40), (-5.0, -2.0, 20), (-INF, -5.0, 5),
    ],
}

# Dimensiones del índice con su peso y la ponderación interna de indicadores.
DIMENSIONES_ITCM = {
    "estabilidad_monetaria": {
        "nombre": "Estabilidad monetaria-inflacionaria",
        "peso": 0.35,
        "indicadores": {"ipc_total": 0.5, "rem_ipc_12m": 0.5},
    },
    "viabilidad_fiscal_comercial": {
        "nombre": "Viabilidad fiscal-comercial",
        "peso": 0.30,
        "indicadores": {"recaudacion": 0.6, "saldo_comercial_12m": 0.4},
    },
    "financiamiento": {
        "nombre": "Capacidad de financiamiento",
        "peso": 0.20,
        "indicadores": {"reservas_bcra": 0.5, "badlar": 0.5},
    },
    "actividad": {
        "nombre": "Actividad económica",
        "peso": 0.15,
        "indicadores": {"emae_ia": 1.0},
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
INDICADORES_CONTEXTO = ["tcrm", "prestamos_privados", "base_monetaria", "tc_mayorista"]


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
