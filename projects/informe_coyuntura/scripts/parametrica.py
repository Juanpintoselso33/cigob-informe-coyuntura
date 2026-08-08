"""Motor genérico de los índices paramétricos 0-100 del informe (ITCM, ITCG).

Cada cinturón con paramétrica define SUS tablas (bandas por indicador,
dimensiones con pesos, bandas de interpretación) en su propio módulo
(itcm.py, itcg.py); acá vive el algoritmo común:

  índice = Σ peso_dimensión × Σ (peso_indicador × puntaje_interpolado(valor))

con renormalización de pesos ante faltantes (dentro de cada dimensión entre
los indicadores presentes, y entre dimensiones si alguna queda vacía) y
overrides del analista con vencimiento.

Convención de bordes de banda (uniforme, pineada por tests): cada banda es
(low, high, puntaje) con low EXCLUSIVO y high INCLUSIVO.

PUNTAJE POR INTERPOLACIÓN (ADR-0021, jul-2026): los umbrales institucionales
del doc son ANCLAS — cada banda finita ancla su puntaje en su punto medio y
las abiertas (±inf) en su borde finito; entre anclas el puntaje es lineal y
en los extremos queda plano. Indicadores con un contrato continuo propio
pueden declarar anclas explícitas, sin cambiar la semántica de las tablas
tradicionales. Reemplaza al puntaje escalonado por banda (puntaje_banda, que
se conserva en el contrato público): misma escala institucional, sin
acantilados de umbral — el estudio sombra del ADR-0019 midió que los escalones
duplicaban la incertidumbre del índice y truncaban hasta ±13 puntos por componente.

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


def _anclas(bandas: list) -> list:
    """[(valor, puntaje)] ordenado: punto medio de las bandas finitas, borde
    finito de las abiertas."""
    out = []
    for low, high, puntaje in bandas:
        if low == -INF and high == INF:
            continue
        if low == -INF:
            out.append((float(high), float(puntaje)))
        elif high == INF:
            out.append((float(low), float(puntaje)))
        else:
            out.append(((float(low) + float(high)) / 2.0, float(puntaje)))
    return sorted(out)


def puntaje_desde_anclas(valor: float, anclas: list | tuple) -> float:
    """Interpola un puntaje 0-100 entre anclas explícitas y satura extremos."""
    a = sorted((float(x), float(puntaje)) for x, puntaje in anclas)
    if not a:
        raise ValueError("se requiere al menos un ancla")
    if valor <= a[0][0]:
        return round(a[0][1], 1)
    if valor >= a[-1][0]:
        return round(a[-1][1], 1)
    for (x0, p0), (x1, p1) in zip(a, a[1:]):
        if x0 <= valor <= x1:
            if x1 == x0:
                return round(p1, 1)
            return round(p0 + (p1 - p0) * (valor - x0) / (x1 - x0), 1)
    return round(a[-1][1], 1)


def puntaje_interpolado(valor: float, bandas: list) -> float:
    """Puntaje continuo 0-100: lineal entre las anclas de la tabla de bandas,
    plano más allá de las anclas extremas (sin extrapolación). Redondeado a 1
    decimal (ADR-0021)."""
    return puntaje_desde_anclas(valor, _anclas(bandas))


def banda_interpretacion(valor: float, bandas_interpretacion: list) -> str:
    for low, high, etiqueta in bandas_interpretacion:
        if low < valor <= high:
            return etiqueta
    raise ValueError(f"índice {valor} fuera de rango")


def tension_de_indice(indice: float) -> float:
    """Tensión 0-10 del cinturón (convención del informe) derivada del índice."""
    return round((100.0 - indice) / 10.0, 1)


# ── Semáforo de 4 colores (ADR-0181) ──────────────────────────────────────────
# El color NO es una escala nueva: es la tensión 0-10 que el informe ya publica,
# partida en cuatro tramos. Para los índices 0-100 eso da los cortes 60/40/20,
# que son los bordes de BANDAS_INTERPRETACION; para el ITVC base-100 sale de
# despejar su propia fórmula (tensión = 5 − (índice−100) × 0,2).
#
# El color se calcula SIEMPRE sobre la tensión sin redondear. `aporte_score` en
# el snapshot está redondeado a un decimal y usarlo acá rompe el borde: puntaje
# 59,9 da tensión 4,01, que redondeada es 4,0 y saldría verde.
CORTES_SEMAFORO = (("verde", 4.0), ("amarillo", 6.0), ("naranja", 8.0), ("rojo", INF))


def color_de_tension(tension: float) -> str:
    """Color del semáforo para una tensión 0-10 (sin redondear)."""
    for color, tope in CORTES_SEMAFORO:
        if tension <= tope:
            return color
    return CORTES_SEMAFORO[-1][0]


def color_de_puntaje(puntaje: float) -> str:
    """Color de un puntaje 0-100 (ITCM/ITCG/ITCP), vía su tensión equivalente."""
    return color_de_tension((100.0 - float(puntaje)) / 10.0)


def color_de_indice_base100(indice: float) -> str:
    """Color de un índice base-100 (ITVC), vía su fórmula de tensión publicada."""
    return color_de_tension(5.0 - (float(indice) - 100.0) * 0.2)


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


class Escala:
    """Todo lo necesario para convertir un valor CRUDO en puntaje, junto.

    Existe porque puntuar exige saber tres cosas —qué bandas, si hay anclas
    explícitas, y si el valor se transforma antes— y mientras se pasaran por
    separado, alguien olvidaba una. Pasó CUATRO veces (ADR-0082), la última
    dentro del arreglo de la tercera: la matriz de redundancia llamaba a la
    función correcta pero sin las transformaciones, y volvió a publicar un
    número equivocado.

    Con la escala armada una sola vez por índice, olvidarse una parte deja de
    ser posible: no hay parámetro que omitir.
    """

    __slots__ = ("bandas", "anclas", "transformaciones")

    def __init__(self, bandas: dict, anclas: dict | None = None,
                 transformaciones: dict | None = None):
        self.bandas = bandas or {}
        self.anclas = anclas or {}
        self.transformaciones = transformaciones or {}

    def puntaje(self, valor, indicador: str) -> float:
        """Puntaje 0-100 del valor crudo del indicador."""
        return puntaje_de(valor, indicador, self.bandas, self.anclas,
                          self.transformaciones)

    def span_crudo(self, indicador: str) -> float | None:
        """Ancho entre anclas finitas, EN LAS UNIDADES DEL VALOR CRUDO.

        Lo usa la simulación de sensibilidad, que perturba el valor crudo: si
        el indicador se transforma antes de puntuar, sus anclas están en
        unidades de la banda y hay que traerlas con la inversa declarada."""
        if indicador in self.anclas:
            ancs = [float(x) for x, _ in self.anclas[indicador]]
        elif indicador in self.bandas:
            inf = float("inf")
            ancs = [a for b in self.bandas[indicador] for a in b[:2] if abs(a) != inf]
        else:
            return None
        t = self.transformaciones.get(indicador)
        if isinstance(t, tuple):
            ancs = [t[1](a) for a in ancs]
        return (max(ancs) - min(ancs)) if ancs else None

    def puntuable(self, indicador: str) -> bool:
        return indicador in self.bandas or indicador in self.anclas


def puntaje_de(valor, indicador: str, bandas_por_indicador: dict,
               anclas_por_indicador: dict | None = None,
               transformaciones_por_indicador: dict | None = None) -> float:
    """Puntaje de banda de UN indicador, a partir de su valor CRUDO.

    Único camino de "valor de la serie" a "puntaje". Resuelve las dos cosas que
    hay que saber para puntuar, y que antes vivían separadas:

      1. QUÉ ESCALA. Algunos indicadores tienen anclas explícitas que NO
         coinciden con los puntos medios de sus bandas: `presion_dolarizacion`
         con valor 75 da 10 puntos por bandas y 35 por anclas.
      2. SI EL VALOR SE TRANSFORMA ANTES. `rem_ipc_12m` se publica como
         expectativa ANUAL (24,2%) y se puntúa por su equivalente MENSUAL
         (1,82%), contra bandas mensuales.

    Las dos cosas se olvidaron en producción, tres veces entre las dos (ADR-0082
    documenta los casos). Mientras la información necesaria para puntuar viva en
    un lado y el acto de puntuar en otro, la próxima es cuestión de tiempo: acá
    están juntas, y el motor pasa por esta función.
    """
    anclas_por_indicador = anclas_por_indicador or {}
    transformaciones_por_indicador = transformaciones_por_indicador or {}
    if indicador in transformaciones_por_indicador:
        t = transformaciones_por_indicador[indicador]
        directa = t[0] if isinstance(t, tuple) else t
        valor = directa(float(valor))
    if indicador in anclas_por_indicador:
        return puntaje_desde_anclas(float(valor), anclas_por_indicador[indicador])
    return puntaje_interpolado(float(valor), bandas_por_indicador[indicador])


def calcular_indice(valores: dict, ajustes: dict | None, bandas_por_indicador: dict,
                    dimensiones: dict, bandas_interpretacion: list,
                    interpretacion_legible: dict,
                    anclas_por_indicador: dict | None = None,
                    transformaciones_por_indicador: dict | None = None) -> dict | None:
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
    anclas_por_indicador = anclas_por_indicador or {}
    resultado_dims = {}
    ajustes_aplicados = []

    for dkey, dim in dimensiones.items():
        presentes = {}
        for ikey, peso in dim["indicadores"].items():
            valor = valores.get(ikey)
            if valor is None:
                continue
            p_banda = puntaje_de(
                valor, ikey, bandas_por_indicador, anclas_por_indicador,
                transformaciones_por_indicador
            )
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
