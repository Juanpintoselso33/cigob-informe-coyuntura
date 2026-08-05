# -*- coding: utf-8 -*-
"""Ningún test puede modificar un archivo versionado (ADR-0179).

ADR-0178 arregló el único test que escribía en el árbol —`publicar.py` corrido
de verdad contra el repo— pero dejó anotado que el aislamiento era puntual y no
estructural: nada impedía que el próximo hiciera lo mismo. Esto es la versión
general.

Por qué importa más de lo que parece: un test que escribe en
`web/src/data/informe.json` no rompe ese test, rompe los que corren DESPUÉS. El
5-ago-2026 eso produjo diez fallas G3 fantasma en el gate y dos tests que pasan
solos y fallan en conjunto, y esas fallas se confundieron dos veces con
problemas de datos reales. El síntoma aparece lejos de la causa, que es la peor
forma de un bug.

El guardián hace dos cosas:
  1. **nombra al culpable** — falla el test que escribió, no el que lo sufre;
  2. **corta la cascada** — restaura el contenido original, así el resto de la
     suite sigue viendo el árbol que corresponde y sus resultados valen.

Un test que necesite escribir de verdad puede declararlo:

    @pytest.mark.escribe_en_el_arbol("motivo por el que es inevitable")
"""
import os
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]          # projects/informe_coyuntura
REPO = RAIZ.parents[1]                              # raíz del repo
VIGILADOS = ["data", "web/src/data", "output"]      # salidas versionadas
MARCA = "escribe_en_el_arbol"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        f"{MARCA}(motivo): el test escribe en archivos versionados a propósito")


def _archivos_versionados():
    """Rutas absolutas de los archivos que git tiene bajo control en las
    carpetas de salida. Sin git no hay guardián: se avisa y se sigue, porque un
    tarball sin `.git` tiene que poder correr los tests igual."""
    rel = [f"projects/informe_coyuntura/{d}" for d in VIGILADOS]
    try:
        r = subprocess.run(["git", "ls-files", "-z", *rel],
                           cwd=REPO, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [REPO / p for p in r.stdout.decode("utf-8").split("\0") if p]


@pytest.fixture(scope="session")
def _linea_base():
    """{ruta: bytes} al arrancar la sesión. Son ~3 MB en 78 archivos: alcanza
    para restaurar sin depender de `git checkout`, que pisaría las
    modificaciones locales legítimas de quien esté trabajando."""
    archivos = _archivos_versionados()
    if archivos is None:
        return None
    return {p: p.read_bytes() for p in archivos if p.exists()}


def _huella(rutas):
    """(tamaño, mtime) por archivo. Es el filtro barato: se corre 1900 veces y
    statear 78 archivos cuesta ~1 ms, mientras que hashearlos costaría minutos.
    El contenido sólo se compara sobre los que se movieron."""
    huella = {}
    for p in rutas:
        try:
            st = os.stat(p)
            huella[p] = (st.st_size, st.st_mtime_ns)
        except FileNotFoundError:
            huella[p] = None
    return huella


@pytest.fixture(autouse=True)
def _ningun_test_escribe_en_el_arbol(request, _linea_base):
    if _linea_base is None:
        yield
        return

    rutas = list(_linea_base)
    antes = _huella(rutas)
    yield
    despues = _huella(rutas)

    # Sólo los que cambiaron de tamaño o mtime pagan la lectura. Un archivo
    # reescrito con contenido idéntico mueve el mtime y no ensucia nada: no se
    # reporta, porque una falla que no corresponde a un daño real entrena a
    # ignorar el guardián.
    sospechosos = [p for p in rutas if antes[p] != despues[p]]
    tocados = []
    for p in sospechosos:
        actual = p.read_bytes() if p.exists() else None
        if actual != _linea_base[p]:
            tocados.append(p)

    if not tocados:
        return

    permitido = request.node.get_closest_marker(MARCA)
    if permitido:
        # Se acepta y la línea base se actualiza, para que los tests siguientes
        # no arrastren la culpa de este.
        for p in tocados:
            _linea_base[p] = p.read_bytes() if p.exists() else b""
        return

    for p in tocados:                       # cortar la cascada ANTES de fallar
        p.write_bytes(_linea_base[p])

    nombres = ", ".join(sorted(str(p.relative_to(REPO)) for p in tocados))
    pytest.fail(
        f"{request.node.nodeid} modificó archivos versionados: {nombres}\n"
        f"Se restauró el contenido original, así que el resto de la suite sigue "
        f"siendo confiable — pero el test tiene que escribir en tmp_path o "
        f"redirigir su salida (ADR-0178 lo hizo con CIGOB_SALIDA_WEB en "
        f"publicar.py). Si escribir ahí es realmente inevitable, declararlo con "
        f"@pytest.mark.{MARCA}('motivo').",
        pytrace=False)
