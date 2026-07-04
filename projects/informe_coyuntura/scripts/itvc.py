"""ITVC-B100 — Índice de Tensión del Cinturón de Vida Cotidiana (base 100).

Implementa el "ITVC — versión base 100" (Fundación CIGOB, doc 260702 vida
cotidiana, jul-2026): un índice de SEGUIMIENTO DE GESTIÓN, no de nivel
absoluto. Cada componente se rebasea a 100 = promedio del 4º trimestre de
2023 (oct-nov-dic, para amortiguar la distorsión de la devaluación de fines
de diciembre); el ITVC es el promedio ponderado directo de esos índices.

    ITVC > 100 = mejora acumulada vs el arranque del mandato
    ITVC < 100 = deterioro acumulado

A diferencia del ITCM/ITCG no hay tablas de bandas: los componentes entran
como índices continuos (la banda solo interpreta el resultado agregado).

Los cinco pesos de dimensión (35/25/10/15/15) y los internos vienen TODOS
del documento (no hay operacionalización propia de pesos). Polaridades:
las fórmulas de rebase viven en descargar_series (series itvc por
componente) y en publicar (componentes sin serie histórica); acá solo se
agrega, renormaliza e interpreta.

La tensión 0-10 del informe se deriva LINEAL de la escala del doc (decisión
del usuario, jul-2026): tensión = 5 − (ITVC − 100) × 0,2, con tope [0, 10].
Calza exacto: ITVC 110 → 3 · 105 → 4 · 100 → 5 · 95 → 6 · 85 → 8.

Overrides del analista: data/vida/ajustes_itvc.json ({indicador: {puntaje,
justificacion, vigente_hasta}}, mismo mecanismo que ITCM/ITCG — acá el
"puntaje" pisa el índice base-100 del componente).
"""
import parametrica

INF = float("inf")

# Dimensiones y pesos del doc 260702 (sección III). Las claves de indicador
# son las HISTÓRICAS del cinturón vida (mapeo componente→clave en el ADR-0018):
# I_SRC→brecha_salario_cbt · I_IFL→informalidad · I_IA→ipc_alimentos ·
# I_PT→peso_tarifas · I_EC→endeudamiento_familiar · I_IPI→mortalidad_pymes ·
# I_ISC→despacho_cemento · I_SD→pluriempleo · I_ICC→icc_utdt ·
# I_HD→inseguridad · I_CC→consumo_carne · I_PM→patentamiento_motos.
DIMENSIONES_ITVC = {
    "ingresos": {
        "nombre": "Sostenibilidad de ingresos",
        "peso": 0.35,
        "indicadores": {"brecha_salario_cbt": 0.65, "informalidad": 0.35},
    },
    "precios": {
        "nombre": "Presión de precios",
        "peso": 0.25,
        "indicadores": {"ipc_alimentos": 0.40, "peso_tarifas": 0.60},
    },
    "vulnerabilidad": {
        "nombre": "Vulnerabilidad financiera",
        "peso": 0.10,
        "indicadores": {"endeudamiento_familiar": 1.0},
    },
    "empleo": {
        "nombre": "Prospectivas de empleo",
        "peso": 0.15,
        "indicadores": {"mortalidad_pymes": 0.45, "despacho_cemento": 0.40,
                        "pluriempleo": 0.15},
    },
    "confianza": {
        "nombre": "Confianza y seguridad",
        "peso": 0.15,
        # ADR-0034: entra sentimiento_digital (10%) — le cede el ICC (mide ánimo
        # con encuesta, el Trends lo mide con conducta de búsqueda) y motos (el
        # componente más eufórico del cinturón).
        "indicadores": {"icc_utdt": 0.45, "inseguridad": 0.30,
                        "sentimiento_digital": 0.10,
                        "consumo_carne": 0.10, "patentamiento_motos": 0.05},
    },
}

# Escala de interpretación del doc (sección III). (low, high, etiqueta).
BANDAS_INTERPRETACION = [
    (-INF, 85.0, "deterioro_sustancial"),
    (85.0, 95.0, "deterioro_moderado"),
    (95.0, 105.0, "sin_cambios"),
    (105.0, 110.0, "mejora_moderada"),
    (110.0, INF, "mejora_sustancial"),
]

INTERPRETACION_LEGIBLE = {
    "deterioro_sustancial": "Deterioro sustancial vs 4T-2023",
    "deterioro_moderado":   "Deterioro moderado vs 4T-2023",
    "sin_cambios":          "Sin cambios significativos vs 4T-2023",
    "mejora_moderada":      "Mejora moderada vs 4T-2023",
    "mejora_sustancial":    "Mejora sustancial vs 4T-2023",
}

# Indicadores del cinturón que se publican pero no integran el índice.
# ADR-0034: sentimiento_digital dejó de ser contexto — la serie mensual de
# ventana fija (2021→) permite el B100 vs 4T-2023 con cociente intra-consulta,
# inmune a la renormalización de Trends.
INDICADORES_CONTEXTO = []


def banda_interpretacion(itvc: float) -> str:
    return parametrica.banda_interpretacion(itvc, BANDAS_INTERPRETACION)


def tension_de_itvc(itvc: float) -> float:
    """Tensión 0-10 del cinturón, lineal sobre la escala del doc:
    5 − (ITVC − 100) × 0,2, acotada a [0, 10]."""
    return round(min(10.0, max(0.0, 5.0 - (itvc - 100.0) * 0.2)), 1)


def cargar_ajustes(path, periodo: str) -> dict:
    """Overrides del analista vigentes para `periodo` (ver parametrica)."""
    return parametrica.cargar_ajustes(path, periodo)


def calcular_itvc(indices: dict, ajustes: dict | None = None) -> dict | None:
    """Agrega los índices base-100 por componente ({clave: índice} — None se
    ignora) en el ITVC-B100, renormalizando pesos ante faltantes (dentro de
    cada dimensión y entre dimensiones), con overrides del analista.

    Devuelve la misma forma que calcular_itcm/itcg ({valor, banda,
    banda_legible, dimensiones, ajustes_aplicados}; `puntaje_banda` guarda el
    índice sin override y `puntaje_aplicado` el vigente) para que el resto
    del pipeline y la web lo consuman genérico. None sin ningún componente.
    """
    ajustes = ajustes or {}
    resultado_dims = {}
    ajustes_aplicados = []

    for dkey, dim in DIMENSIONES_ITVC.items():
        presentes = {}
        for ikey, peso in dim["indicadores"].items():
            valor = indices.get(ikey)
            if valor is None:
                continue
            indice = round(float(valor), 1)
            aplicado = indice
            if ikey in ajustes:
                aplicado = ajustes[ikey]["puntaje"]
                ajustes_aplicados.append({
                    "indicador": ikey,
                    "de": indice,
                    "a": aplicado,
                    "justificacion": ajustes[ikey].get("justificacion", ""),
                    "origen": ajustes[ikey].get("origen", "manual"),
                })
            presentes[ikey] = {"peso": peso, "puntaje_banda": indice,
                               "puntaje_aplicado": aplicado}
        if not presentes:
            continue
        suma_pesos = sum(i["peso"] for i in presentes.values())
        for info in presentes.values():
            info["peso_renorm"] = info["peso"] / suma_pesos
        puntaje_dim = sum(i["puntaje_aplicado"] * i["peso_renorm"] for i in presentes.values())
        resultado_dims[dkey] = {
            "nombre": dim["nombre"],
            "peso": dim["peso"],
            "puntaje": round(puntaje_dim, 1),
            "indicadores": presentes,
        }

    if not resultado_dims:
        return None

    suma_dim = sum(d["peso"] for d in resultado_dims.values())
    itvc = 0.0
    for d in resultado_dims.values():
        d["peso_efectivo"] = round(d["peso"] / suma_dim, 4)
        itvc += d["puntaje"] * d["peso"] / suma_dim
        for info in d["indicadores"].values():
            info["peso_efectivo"] = round(info["peso_renorm"] * d["peso"] / suma_dim, 4)
            del info["peso_renorm"]
    itvc = round(itvc, 1)

    etiqueta = banda_interpretacion(itvc)
    return {
        "valor": itvc,
        "banda": etiqueta,
        "banda_legible": INTERPRETACION_LEGIBLE[etiqueta],
        "dimensiones": resultado_dims,
        "ajustes_aplicados": ajustes_aplicados,
    }
