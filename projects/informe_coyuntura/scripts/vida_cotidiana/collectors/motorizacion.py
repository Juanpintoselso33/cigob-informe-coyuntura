"""Motorización total — autos + motos 0km per cápita (DNRPA + INDEC).

El componente que PUNTÚA en el ITCIS desde ADR-0224. Reemplaza a
`patentamiento_motos` y `patentamiento_autos`, que pasan a vivir dentro de la
explicación como Componentes A y B de la matriz A×B.

## Por qué el total y no cada vehículo por su lado

La discusión editorial era si el pasaje del auto a la moto es empobrecimiento
(un hogar que no sostiene el auto baja de categoría) o acceso (un hogar que no
tenía nada compra su primera moto). Las dos lecturas mueven el patentamiento de
motos hacia arriba, así que ninguna de las dos series por separado las
distingue.

Lo que sí las distingue es el TOTAL. Si los hogares bajaran de categoría, el
total estaría plano o cayendo: cada moto que entra tendría un auto que sale.
Medido sobre la ventana dic-2025 → jul-2026, en la que las dos series se
separan, el total per cápita sube 7,5% — entraron 3,17 motos por cada auto que
se dejó de patentar. La sustitución descendente no aparece.

Es la misma salida que ADR-0217 le dio a la carne: puntuar el ACCESO TOTAL y
usar la composición para explicar el color, en vez de elegirle un signo a un
movimiento que tiene dos lecturas.

## Los tres supuestos, declarados

- **Es un FLUJO de altas, no el parque.** Mide cuántos vehículos 0km se
  incorporan por año cada mil habitantes, no cuántos hay circulando. Un hogar
  que conserva el auto que ya tenía no aparece acá.
- **El denominador es la población urbana nacional del INDEC**, que incluye a
  Tierra del Fuego aunque la provincia se excluya del numerador (ver abajo).
  Como el índice se lee contra su propia base y TDF aporta un 0,6% estable de
  los vehículos fuera del período del artefacto, el desajuste de nivel se
  cancela en el rebase.
- **Autos y motos se suman por unidad, sin ponderar por precio ni por gama.**
  Un mes de autos de entrada y uno de vehículos caros se registran igual. La
  DNRPA no publica ni cilindrada ni precio, así que separar gamas exigiría otra
  fuente.
"""
import csv
import io
import logging
import re
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)

# Constantes propias y no importadas de `config`, por el mismo motivo que en
# `dnrpa_autos`: este módulo se carga POR RUTA desde los tests y desde
# `descargar_series.py`, y ahí `import config` resuelve al `config.py` de la
# raíz del proyecto, que es otro archivo.
HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"),
}
HTTP_TIMEOUT = 30

CKAN_PACKAGE_SHOW = "https://datos.jus.gob.ar/api/3/action/package_show"

# Los dos registros. Misma forma de CSV —una fila por (mes, jurisdicción)— y el
# mismo organismo, así que el total no mezcla fuentes ni metodologías.
# Motovehículos arranca en 2007 y automotores en 2000; los dos cubren el
# 4T-2023 con años de sobra.
DATASETS = {
    "autos": ("estadistica-de-tramites-de-automotores", "Automotores",
              re.compile(r"inscripciones\s+iniciales\s+de\s+automotores"
                         r"\s*-\s*(\d{6})\s*-\s*(\d{6})", re.I)),
    "motos": ("estadistica-de-tramites-de-motovehiculos", "Motovehículos",
              re.compile(r"inscripciones\s+iniciales\s+de\s+motoveh[íi]culos"
                         r"\s*-\s*(\d{6})\s*-\s*(\d{6})", re.I)),
}

COLUMNAS = {
    "tipo_vehiculo",
    "anio_inscripcion_inicial",
    "mes_inscripcion_inicial",
    "provincia_inscripcion_inicial",
    "cantidad_inscripciones_iniciales",
}

# 24 jurisdicciones (23 provincias + CABA) en TODOS los meses de los dos
# archivos. Un mes con menos es un mes que se subió incompleto.
JURISDICCIONES = 24

# ── Tierra del Fuego: la exclusión, con su motivo y su período ───────────────
#
# TDF patentó 29.005 motos en 2025 contra 816 en 2023, 762 en 2024 y 294 en los
# siete meses de 2026. Todo el exceso se concentra entre abril y noviembre de
# 2025, con un pico de 7.428 en octubre sobre una línea de base de ~60 por mes:
# 35 veces lo normal, en la provincia menos poblada del país.
#
# No es demanda de hogares fueguinos, es un evento registral —la provincia tiene
# régimen de promoción industrial y las unidades se inscriben ahí—, así que
# entra al índice como si 29.000 familias hubieran comprado una moto.
#
# Se excluye la provincia ENTERA y en TODA la serie, no sólo los meses del pico:
# recortar los meses anómalos exigiría un umbral, y un umbral que atrape una
# carga fiscal también atrapa un mes real —abril de 2020 fue el 12% de la
# mediana de los doce meses previos, y era una cuarentena—. Excluir la
# jurisdicción completa cuesta 0,6% del total y es una regla que no depende de
# calibrar nada.
JURISDICCION_EXCLUIDA = "Tierra del Fuego"
ARTEFACTO_TDF = ("2025-04", "2025-11")

# La base del ITCIS (ADR-0018) y 11 meses antes, para que las ventanas móviles
# de 12 meses que terminan en oct/nov/dic-2023 estén completas (ADR-0024).
BASE_4T_2023 = ("2023-10", "2023-11", "2023-12")
DESDE = "2022-11"

# Población urbana total (INDEC/SSPM, vía datos.gob.ar). Trimestral y proyectada
# en línea recta, así que interpolarla a meses no inventa nada que la fuente no
# diga. Es la MISMA serie con la que ADR-0217 pasó la faena a per cápita.
DATOS_GOB_BASE = "https://apis.datos.gob.ar/series/api/series/"
POBLACION_ID = "461.3_POBLACION_ANO_AEA_T_28_3"


def _url_del_recurso(dataset: str, patron) -> tuple[str, str, str]:
    """(url, período_inicial, período_final) del CSV agregado, vía catálogo.

    La URL de descarga lleva el rango de fechas adentro y cambia cada mes, así
    que fijarla a mano garantiza que el colector se congele en un archivo viejo
    sin que nada avise.
    """
    r = requests.get(CKAN_PACKAGE_SHOW, params={"id": dataset},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    cuerpo = r.json()
    if not cuerpo.get("success"):
        raise ValueError(f"el catálogo rechazó la consulta por «{dataset}»")

    candidatos = []
    for recurso in cuerpo["result"].get("resources", []):
        m = patron.search(recurso.get("name") or "")
        if m and (recurso.get("format") or "").upper() == "CSV":
            candidatos.append((recurso["url"], m.group(1), m.group(2)))
    if len(candidatos) != 1:
        nombres = [x.get("name") for x in cuerpo["result"].get("resources", [])]
        raise ValueError(
            f"se esperaba 1 recurso de inscripciones iniciales en «{dataset}» "
            f"y hay {len(candidatos)}; el dataset publica: {nombres}")
    return candidatos[0]


def _mensual(texto: str, tipo: str) -> tuple[dict, dict]:
    """({YYYY-MM: unidades}, {YYYY-MM: {jurisdicción: unidades}})."""
    lector = csv.DictReader(io.StringIO(texto))
    faltan = COLUMNAS - set(lector.fieldnames or [])
    if faltan:
        raise ValueError(f"el CSV de la DNRPA ya no trae las columnas {sorted(faltan)} "
                         f"(trae {lector.fieldnames})")

    total: dict = defaultdict(int)
    por_provincia: dict = defaultdict(dict)
    for fila in lector:
        if fila["tipo_vehiculo"] != tipo:
            continue
        ym = (f"{int(fila['anio_inscripcion_inicial'])}-"
              f"{int(fila['mes_inscripcion_inicial']):02d}")
        cantidad = int(fila["cantidad_inscripciones_iniciales"])
        total[ym] += cantidad
        por_provincia[ym][fila["provincia_inscripcion_inicial"]] = cantidad
    if not total:
        raise ValueError(f"ninguna fila del CSV es de tipo «{tipo}»: la fuente "
                         f"cambió el rótulo del universo que se suma")
    return dict(sorted(total.items())), dict(por_provincia)


def _sin_huecos(meses: list, que: str) -> None:
    a0, m0 = int(meses[0][:4]), int(meses[0][5:7])
    af, mf = int(meses[-1][:4]), int(meses[-1][5:7])
    esperados = (af * 12 + mf) - (a0 * 12 + m0) + 1
    if esperados != len(meses):
        raise ValueError(f"la serie de {que} tiene huecos: {len(meses)} meses "
                         f"entre {meses[0]} y {meses[-1]}, se esperaban {esperados}")


def _bajar(clave: str) -> tuple[dict, dict]:
    """Serie mensual país y por jurisdicción de uno de los dos registros,
    con todas las guardas de forma aplicadas."""
    dataset, tipo, patron = DATASETS[clave]
    url, declarado_ini, declarado_fin = _url_del_recurso(dataset, patron)
    r = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT * 3)
    r.raise_for_status()
    total, por_provincia = _mensual(r.content.decode("utf-8-sig", errors="strict"), tipo)

    meses = list(total)
    _sin_huecos(meses, clave)

    # El anclaje que importa: el archivo declara su período en el nombre del
    # recurso y tiene que traer exactamente eso. Un umbral por magnitud no
    # sirve — abril de 2020 fue el 12% de la mediana previa y era real.
    for etiqueta, declarado, real in (("primer", declarado_ini, meses[0]),
                                      ("último", declarado_fin, meses[-1])):
        if declarado != real.replace("-", ""):
            raise ValueError(
                f"el catálogo de {clave} declara {etiqueta} período {declarado} "
                f"y el CSV trae {real}: el archivo está a medio cargar o cambió "
                f"de forma")

    faltan_base = [m for m in BASE_4T_2023 if m not in total]
    if faltan_base:
        raise ValueError(f"la serie de {clave} no cubre la base del índice: "
                         f"falta {faltan_base}")

    flacos = [m for m in meses[-12:] if len(por_provincia[m]) < JURISDICCIONES]
    if flacos:
        raise ValueError(f"meses de {clave} con menos de {JURISDICCIONES} "
                         f"jurisdicciones informadas: {flacos}")

    if JURISDICCION_EXCLUIDA not in por_provincia[meses[-1]]:
        raise ValueError(
            f"«{JURISDICCION_EXCLUIDA}» no aparece entre las jurisdicciones de "
            f"{clave}: la fuente le cambió el rótulo y la exclusión del "
            f"artefacto dejaría de aplicarse en silencio")

    return total, por_provincia


def _sin_la_excluida(total: dict, por_provincia: dict) -> dict:
    """El total país menos la jurisdicción excluida, mes a mes."""
    return {m: v - por_provincia[m].get(JURISDICCION_EXCLUIDA, 0)
            for m, v in total.items()}


def _poblacion_mensual(puntos: list):
    """Interpola la serie trimestral del INDEC a meses y la extiende con su
    propia pendiente. Copia deliberada de `descargar_series._poblacion_mensual`:
    este módulo se carga por ruta y no puede importar del script de series."""
    puntos = sorted((f[:7], v) for f, v in puntos)
    if len(puntos) < 2:
        raise ValueError("la serie de población del INDEC vino con menos de dos puntos")
    ym = lambda x: int(x[:4]) * 12 + int(x[5:7])

    def en(mes: str) -> float:
        t = ym(mes)
        if t <= ym(puntos[0][0]):
            return puntos[0][1]
        for (f0, v0), (f1, v1) in zip(puntos, puntos[1:]):
            if ym(f0) <= t <= ym(f1):
                return v0 + (v1 - v0) * (t - ym(f0)) / (ym(f1) - ym(f0))
        (f0, v0), (f1, v1) = puntos[-2], puntos[-1]
        return v1 + (v1 - v0) / (ym(f1) - ym(f0)) * (t - ym(f1))

    return en


def _fetch_poblacion() -> list:
    r = requests.get(DATOS_GOB_BASE,
                     params={"ids": POBLACION_ID, "format": "json", "limit": 80},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    datos = r.json().get("data") or []
    if not datos:
        raise ValueError(f"la serie de población {POBLACION_ID} vino vacía")
    # La serie viene en MILES de personas.
    return [(f, v * 1000.0) for f, v in datos if v]


def _movil12(serie: dict) -> dict:
    """Acumulado de 12 meses CONSECUTIVOS (ADR-0024). Los huecos ya los
    descartó `_sin_huecos`, pero la ventana los vuelve a exigir: es la misma
    regla que aplica `itvc.rebase_movil12` y tienen que coincidir."""
    meses = sorted(serie)
    out = {}
    for i in range(11, len(meses)):
        win = meses[i - 11:i + 1]
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        if (af * 12 + mf) - (a0 * 12 + m0) != 11:
            continue
        out[meses[i]] = sum(serie[k] for k in win)
    return out


def fetch_motorizacion() -> dict:
    """Card, composición y serie base-100 de la motorización total.

    Todo lo que puede salir mal levanta excepción: el colector es de falla
    ruidosa a propósito. Una serie a la que le falta el último mes, o que suma
    un universo distinto, no se distingue a ojo de una serie sana — y ésta
    alimenta un componente que se publica en una web.
    """
    autos, autos_prov = _bajar("autos")
    motos, motos_prov = _bajar("motos")

    if max(autos) != max(motos):
        raise ValueError(
            f"los dos registros no llegan al mismo mes (autos {max(autos)}, "
            f"motos {max(motos)}): sumarlos daría un total con una pata corta")

    limpios_a = _sin_la_excluida(autos, autos_prov)
    limpios_m = _sin_la_excluida(motos, motos_prov)
    meses = sorted(set(limpios_a) & set(limpios_m))
    total = {m: limpios_a[m] + limpios_m[m] for m in meses}

    mov_total = _movil12(total)
    mov_autos = _movil12({m: limpios_a[m] for m in meses})
    mov_motos = _movil12({m: limpios_m[m] for m in meses})

    pob = _poblacion_mensual(_fetch_poblacion())
    per_capita = {m: mov_total[m] / pob(m) * 1000.0 for m in mov_total}

    faltan = [m for m in BASE_4T_2023 if m not in per_capita]
    if faltan:
        raise ValueError(f"la serie no llega al 4T-2023 con ventanas móviles "
                         f"completas: falta {faltan}")
    base = sum(per_capita[m] for m in BASE_4T_2023) / len(BASE_4T_2023)

    ultimo = max(per_capita)
    ultimo_mes = max(meses)
    if ultimo != ultimo_mes:
        raise ValueError(
            f"la ventana móvil termina en {ultimo} y la serie mensual en "
            f"{ultimo_mes}: el último mes no tiene doce meses detrás")
    prev = f"{int(ultimo[:4]) - 1}-{ultimo[5:7]}"

    def _var(mov):
        return ((mov[ultimo] / mov[prev] - 1) * 100.0) if mov.get(prev) else None

    composicion = {
        "autos_12m": mov_autos[ultimo],
        "motos_12m": mov_motos[ultimo],
        "total_12m": mov_total[ultimo],
        # El Componente C de la ficha: qué proporción de los vehículos que se
        # incorporan son motos. Es el número que discute el editorial.
        "ratio_motos": round(mov_motos[ultimo] / mov_total[ultimo] * 100.0, 1),
        "ratio_motos_base": round(
            sum(mov_motos[m] for m in BASE_4T_2023)
            / sum(mov_total[m] for m in BASE_4T_2023) * 100.0, 1),
        "autos_var": _var(mov_autos),
        "motos_var": _var(mov_motos),
        "total_var": _var(mov_total),
    }

    logger.info("MOTORIZACIÓN OK: %.2f por mil hab en %s (índice %.1f), "
                "%.1f%% motos", per_capita[ultimo], ultimo,
                per_capita[ultimo] / base * 100.0, composicion["ratio_motos"])

    return {
        "motorizacion_total": {
            # La card publica el NIVEL, que es el número con significado para
            # el lector: "31,6 vehículos 0km por cada mil habitantes" dice
            # algo, "144,7 de índice" no. Mismo criterio que ADR-0217 con los
            # kg de carne por habitante.
            "valor": round(per_capita[ultimo], 2),
            "fecha": ultimo,
            "unidad": "vehículos 0km por cada 1.000 habitantes (12 meses)",
            "fuente": ("DNRPA — inscripciones iniciales de automotores y "
                       "motovehículos, per cápita (INDEC)"),
            "composicion": composicion,
        },
        # Serie YA rebaseada a 100 = promedio del 4T-2023: entra al índice por
        # `SERIES_REBASEADAS`, sin volver a rebasearse (igual que la carne).
        "serie": {m: round(v / base * 100.0, 1)
                  for m, v in per_capita.items() if m >= "2023-01"},
        # Las dos patas, Componentes A y B de la matriz. Van con la MISMA
        # exclusión que el total y no con el país entero, aunque el país entero
        # sea lo que publica la DNRPA: si el gráfico trajera Tierra del Fuego y
        # el índice no, sumar las dos series del propio informe daría un ratio
        # distinto del que dice el texto que lo explica (59,1% contra 58,4%).
        # La exclusión viaja escrita en la línea de fuente de las tres series,
        # que es donde el lector la puede ver.
        "serie_autos": {m: v for m, v in limpios_a.items() if m >= DESDE},
        "serie_motos": {m: v for m, v in limpios_m.items() if m >= DESDE},
        "patentamiento_autos": {"valor": limpios_a[ultimo_mes], "fecha": ultimo_mes,
                                "provincias": {p: n for p, n in autos_prov[ultimo_mes].items()
                                               if p != JURISDICCION_EXCLUIDA}},
        "patentamiento_motos": {"valor": limpios_m[ultimo_mes], "fecha": ultimo_mes,
                                "provincias": {p: n for p, n in motos_prov[ultimo_mes].items()
                                               if p != JURISDICCION_EXCLUIDA}},
    }
