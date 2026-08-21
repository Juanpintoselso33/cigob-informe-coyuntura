"""Patentamiento de AUTOS — inscripciones iniciales de automotores (DNRPA).

El espejo de `patentamiento_motos`. La moto es medio de trabajo y sustituto
barato del auto, así que un cinturón que sólo mira motos no puede distinguir
"los hogares compran más" de "los hogares bajan de categoría": las dos cosas
mueven el patentamiento de motos para arriba.

## Por qué DNRPA y no ACARA ni ADEFA

El patentamiento es un ACTO REGISTRAL: un auto 0km existe cuando se inscribe en
un Registro Seccional de la Propiedad del Automotor. La DNRPA es quien lleva ese
registro, así que es la fuente primaria — ACARA publica los mismos números
reelaborados, y ADEFA mide otra cosa (producción y ventas de fábrica a
concesionario, que ocurren antes y pueden quedar en stock).

## Los anclajes, y por qué son de texto y no de magnitud

La trampa de este recurso es que su URL lleva el rango de fechas adentro
(`...-2000-01-2026-07.csv`) y cambia todos los meses: hay que descubrirlo por
catálogo. Y el nombre del recurso DECLARA el período que contiene
(«... - 200001 - 202607»), lo que da algo mucho mejor que un umbral: se compara
lo que el archivo dice traer contra lo que efectivamente trae. Si la fuente
sube un mes a medio cargar, el mes declarado y el mes con datos dejan de
coincidir y esto revienta en vez de publicar un derrumbe falso.

Un chequeo por magnitud —"el último mes no puede ser menos del X% del promedio"—
NO sirve acá, y está medido: abril de 2020 fue el 12% de la mediana de los doce
meses previos. Era real. Cualquier umbral que atrape una carga parcial también
atrapa una cuarentena.
"""
import csv
import io
import logging
import re
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)

# Constantes propias y no importadas de `config`, igual que en el colector de
# trabajo independiente. Este módulo se carga POR RUTA desde los tests y desde
# `descargar_series.py`, y ahí `import config` resuelve al `config.py` de la
# raíz del proyecto, que es otro archivo: la dependencia se rompería sólo fuera
# del colector principal, que es la peor forma de romperse.
HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"),
}
HTTP_TIMEOUT = 30

CKAN_PACKAGE_SHOW = "https://datos.jus.gob.ar/api/3/action/package_show"
DATASET = "estadistica-de-tramites-de-automotores"

# El recurso agregado del dataset: una fila por (mes, jurisdicción). El dataset
# publica también TRANSFERENCIAS con nombre casi igual, así que el patrón exige
# «inscripciones iniciales» y captura el período declarado en el propio nombre.
RECURSO = re.compile(
    r"inscripciones\s+iniciales\s+de\s+automotores\s*-\s*(\d{6})\s*-\s*(\d{6})",
    re.I)

COLUMNAS = {
    "tipo_vehiculo",
    "anio_inscripcion_inicial",
    "mes_inscripcion_inicial",
    "provincia_inscripcion_inicial",
    "cantidad_inscripciones_iniciales",
}
TIPO = "Automotores"

# 24 jurisdicciones (23 provincias + CABA) en TODOS los meses del archivo, desde
# el año 2000. Un mes con menos es un mes que se subió incompleto.
JURISDICCIONES = 24

# La base del ITCIS. Sin estos tres meses el rebase no existe (ADR-0018).
BASE_4T_2023 = ("2023-10", "2023-11", "2023-12")

# 11 meses antes de la base, para que las ventanas móviles de 12 meses que
# terminan en oct/nov/dic-2023 estén completas (ADR-0024).
DESDE = "2022-11"


def _url_del_recurso() -> tuple[str, str, str]:
    """(url, período_inicial, período_final) del CSV agregado, vía catálogo.

    La URL de descarga lleva el rango de fechas adentro y cambia cada mes, así
    que fijarla a mano garantiza que el colector se congele en un archivo viejo
    sin que nada avise.
    """
    r = requests.get(CKAN_PACKAGE_SHOW, params={"id": DATASET},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    cuerpo = r.json()
    if not cuerpo.get("success"):
        raise ValueError(f"el catálogo rechazó la consulta por «{DATASET}»")

    candidatos = []
    for recurso in cuerpo["result"].get("resources", []):
        m = RECURSO.search(recurso.get("name") or "")
        if m and (recurso.get("format") or "").upper() == "CSV":
            candidatos.append((recurso["url"], m.group(1), m.group(2)))
    if len(candidatos) != 1:
        nombres = [x.get("name") for x in cuerpo["result"].get("resources", [])]
        raise ValueError(
            f"se esperaba 1 recurso de inscripciones iniciales y hay "
            f"{len(candidatos)}; el dataset publica: {nombres}")
    return candidatos[0]


def _mensual(texto: str) -> tuple[dict, dict]:
    """({YYYY-MM: unidades}, {YYYY-MM: {jurisdicción: unidades}})."""
    lector = csv.DictReader(io.StringIO(texto))
    faltan = COLUMNAS - set(lector.fieldnames or [])
    if faltan:
        raise ValueError(f"el CSV de la DNRPA ya no trae las columnas {sorted(faltan)} "
                         f"(trae {lector.fieldnames})")

    total: dict = defaultdict(int)
    por_provincia: dict = defaultdict(dict)
    for fila in lector:
        if fila["tipo_vehiculo"] != TIPO:
            continue
        ym = (f"{int(fila['anio_inscripcion_inicial'])}-"
              f"{int(fila['mes_inscripcion_inicial']):02d}")
        cantidad = int(fila["cantidad_inscripciones_iniciales"])
        total[ym] += cantidad
        por_provincia[ym][fila["provincia_inscripcion_inicial"]] = cantidad
    if not total:
        raise ValueError(f"ninguna fila del CSV es de tipo «{TIPO}»: la fuente "
                         f"cambió el rótulo del universo que se suma")
    return dict(sorted(total.items())), dict(por_provincia)


def _sin_huecos(meses: list) -> None:
    a0, m0 = int(meses[0][:4]), int(meses[0][5:7])
    af, mf = int(meses[-1][:4]), int(meses[-1][5:7])
    esperados = (af * 12 + mf) - (a0 * 12 + m0) + 1
    if esperados != len(meses):
        raise ValueError(f"la serie de la DNRPA tiene huecos: {len(meses)} meses "
                         f"entre {meses[0]} y {meses[-1]}, se esperaban {esperados}")


def fetch_patentamiento_autos() -> dict:
    """Card + serie mensual de patentamientos de autos, total país.

    Todo lo que puede salir mal levanta excepción: el colector es de falla
    ruidosa a propósito. Una serie a la que le falta el último mes, o que suma
    un universo distinto, no se distingue a ojo de una serie sana — y esta
    alimenta un componente del índice que se publica en una web.
    """
    url, declarado_ini, declarado_fin = _url_del_recurso()
    r = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT * 3)
    r.raise_for_status()
    total, por_provincia = _mensual(r.content.decode("utf-8-sig", errors="strict"))

    meses = list(total)
    _sin_huecos(meses)

    # El anclaje que importa: el archivo declara su período en el nombre del
    # recurso y tiene que traer exactamente eso.
    for etiqueta, declarado, real in (("primer", declarado_ini, meses[0]),
                                      ("último", declarado_fin, meses[-1])):
        if declarado != real.replace("-", ""):
            raise ValueError(
                f"el catálogo declara {etiqueta} período {declarado} y el CSV "
                f"trae {real}: el archivo está a medio cargar o cambió de forma")

    faltan_base = [m for m in BASE_4T_2023 if m not in total]
    if faltan_base:
        raise ValueError(f"la serie no cubre la base del índice: falta {faltan_base}")

    flacos = [m for m in meses[-12:] if len(por_provincia[m]) < JURISDICCIONES]
    if flacos:
        raise ValueError(f"meses con menos de {JURISDICCIONES} jurisdicciones "
                         f"informadas: {flacos}")

    ultimo = meses[-1]
    logger.info("DNRPA OK: %d autos en %s (%d meses)", total[ultimo], ultimo, len(meses))
    return {
        "patentamiento_autos": {
            "valor": total[ultimo],
            "fecha": ultimo,
            "unidad": "Unidades",
            "provincias": por_provincia[ultimo],
            "fuente": "DNRPA — inscripciones iniciales de automotores",
        },
        "serie": {m: v for m, v in total.items() if m >= DESDE},
    }
