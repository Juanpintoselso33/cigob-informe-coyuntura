"""Motor genérico de los índices paramétricos 0-100 del informe (ITCM, ITCG).

Cada cinturón con paramétrica define SUS tablas (bandas por indicador,
dimensiones con pesos, bandas de interpretación) en su propio módulo
(itcm.py, itcg.py); acá vive el algoritmo común:

  índice = Σ peso_dimensión × Σ (peso_indicador × puntaje_banda(valor))

con renormalización de pesos ante faltantes (dentro de cada dimensión entre
los indicadores presentes, y entre dimensiones si alguna queda vacía) y
overrides del analista con vencimiento.

Convención de bordes de banda (uniforme, pineada por tests): cada banda es
(low, high, puntaje) con low EXCLUSIVO y high INCLUSIVO.

La tensión 0-10 del informe se deriva como (100 − índice) / 10, así el resto
del pipeline (umbrales, estados, score global) conserva su convención.
"""
import json
from pathlib import Path

INF = float("inf")


def puntaje_banda(valor: float, bandas: list) -> int:
    """Puntaje de la banda donde cae `valor` (low exclusivo, high inclusivo)."""
    for low, high, puntaje in bandas:
        if low < valor <= high:
            return puntaje
    raise ValueError(f"valor {valor} fuera de toda banda")


def banda_interpretacion(valor: float, bandas_interpretacion: list) -> str:
    for low, high, etiqueta in bandas_interpretacion:
        if low < valor <= high:
            return etiqueta
    raise ValueError(f"índice {valor} fuera de rango")


def tension_de_indice(indice: float) -> float:
    """Tensión 0-10 del cinturón (convención del informe) derivada del índice."""
    return round((100.0 - indice) / 10.0, 1)


def texto_bandas(bandas: list) -> str:
    """Texto legible de una tabla de bandas, para transparencia en el frontend."""
    partes = []
    for low, high, puntaje in bandas:
        if low == -INF:
            rango = f"≤{_num(high)}"
        elif high == INF:
            rango = f">{_num(low)}"
        elif low < 0 or high < 0:
            # con negativos, el guion de rango se vuelve ilegible ("-12–-8")
            rango = f"{_num(low)} a {_num(high)}"
        else:
            rango = f"{_num(low)}–{_num(high)}"
        partes.append(f"{rango} → {puntaje}")
    return " · ".join(partes)


def _num(x: float) -> str:
    s = f"{x:g}"
    return s.replace(".", ",")


def cargar_ajustes(path: Path, periodo: str) -> dict:
    """Lee los overrides del analista vigentes para `periodo` (YYYY-MM).

    Formato del archivo: {indicador: {puntaje, justificacion, vigente_hasta}}.
    Un ajuste con vigente_hasta < periodo está vencido y se ignora (evita
    overrides zombis). Archivo ausente o vacío → sin ajustes.
    """
    path = Path(path)
    if not path.exists():
        return {}
    # utf-8-sig: tolera el BOM que meten los editores/PowerShell de Windows
    with open(path, encoding="utf-8-sig") as f:
        ajustes = json.load(f)
    return {
        nombre: spec for nombre, spec in ajustes.items()
        if spec.get("vigente_hasta", "9999-12") >= periodo
    }


def calcular_indice(valores: dict, ajustes: dict | None, bandas_por_indicador: dict,
                    dimensiones: dict, bandas_interpretacion: list,
                    interpretacion_legible: dict) -> dict | None:
    """Calcula el índice 0-100 a partir de {indicador: valor} (None se ignora).

    Renormaliza pesos ante faltantes: dentro de cada dimensión entre los
    indicadores presentes, y entre dimensiones si alguna queda vacía
    (consistente con el "ignorar ausencias" del resto del informe).

    Devuelve {valor, banda, banda_legible, dimensiones, ajustes_aplicados} o
    None si no hay ningún indicador del índice disponible. `peso_efectivo` por
    indicador es el peso final post-renormalización (suman 1.0 entre los
    presentes).
    """
    ajustes = ajustes or {}
    resultado_dims = {}
    ajustes_aplicados = []

    for dkey, dim in dimensiones.items():
        presentes = {}
        for ikey, peso in dim["indicadores"].items():
            valor = valores.get(ikey)
            if valor is None:
                continue
            p_banda = puntaje_banda(float(valor), bandas_por_indicador[ikey])
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
                               "puntaje_aplicado": p_aplicado,
                               # valor crudo puntuado contra la banda: lo consumen
                               # el estudio de interpolación (ADR-0019, Decisión 3)
                               # y cualquier auditoría del snapshot
                               "valor": round(float(valor), 4)}
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
    indice = 0.0
    for d in resultado_dims.values():
        d["peso_efectivo"] = round(d["peso"] / suma_dim, 4)
        indice += d["puntaje"] * d["peso"] / suma_dim
        for info in d["indicadores"].values():
            info["peso_efectivo"] = round(info["peso_renorm"] * d["peso"] / suma_dim, 4)
            del info["peso_renorm"]
    indice = round(indice, 1)

    etiqueta = banda_interpretacion(indice, bandas_interpretacion)
    return {
        "valor": indice,
        "banda": etiqueta,
        "banda_legible": interpretacion_legible[etiqueta],
        "dimensiones": resultado_dims,
        "ajustes_aplicados": ajustes_aplicados,
    }
