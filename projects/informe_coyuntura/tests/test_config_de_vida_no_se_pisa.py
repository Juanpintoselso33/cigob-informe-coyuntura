"""Dos módulos se llaman `config`: el de la raíz del proyecto y el de
`scripts/vida_cotidiana/`. Python los distingue sólo por el nombre, así que el
primero que se importa en un proceso queda en `sys.modules["config"]` y el
segundo recibe ese mismo módulo.

Pasó el 21-sep-2026: ADR-0333 hizo que `parametrica.py` importara el `config` de
la raíz, `descargar_series.py` lo carga al arrancar, y las ~22 series de vida
cotidiana que después hacen `from config import ...` fallaron con
`cannot import name`. El colector conserva las filas anteriores ante cualquier
error, así que la corrida terminó en verde con las series congeladas.

Corre en un subproceso porque `sys.modules` del proceso de pytest ya viene
contaminado por otros tests: la prueba tiene que ver el orden de importación
real de la corrida nocturna.
"""
import subprocess
import sys
from pathlib import Path

PROYECTO = Path(__file__).resolve().parents[1]


def _correr(codigo: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", codigo], cwd=PROYECTO,
                          capture_output=True, text=True, timeout=120)


def test_descargar_series_no_le_pisa_el_config_a_vida_cotidiana():
    r = _correr(
        "import sys\n"
        "sys.path.insert(0, 'scripts')\n"
        "import descargar_series\n"
        "sys.path.insert(0, 'scripts/vida_cotidiana')\n"
        "from config import DATOS_GOB_BASE, SNIC_CSV, UTDT_IL_LISTADO\n"
        "print('ok')\n"
    )
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-800:]


def test_parametrica_sigue_leyendo_los_umbrales_de_la_raiz():
    r = _correr(
        "import sys\n"
        "sys.path.insert(0, 'scripts')\n"
        "import parametrica, config as raiz\n"
        "assert parametrica.UMBRALES == raiz.UMBRALES\n"
        "print('ok')\n"
    )
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-800:]


def test_con_el_config_de_la_raiz_ya_cargado_vida_sigue_encontrando_el_suyo():
    """El orden que rompe: algo carga el config de la raíz primero (publicar,
    generar_informe, validacion_externa) y después se piden series de vida."""
    r = _correr(
        "import sys\n"
        "sys.path.insert(0, '.'); sys.path.insert(0, 'scripts')\n"
        "import config, publicar, generar_informe\n"
        "import descargar_series as ds\n"
        "@ds._con_config_de_vida\n"
        "def pedir():\n"
        "    ds._entrar_a_vida_cotidiana()\n"
        "    from config import DATOS_GOB_BASE, SNIC_CSV, UTDT_IL_LISTADO, RIPTE_CSV\n"
        "pedir()\n"
        "print('ok')\n"
    )
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-800:]


def test_al_salir_de_vida_vuelve_el_config_de_la_raiz():
    """El choque al revés: pytest corre todo en un proceso, y un test que pide
    series de vida no puede dejarle a los siguientes el config de vida."""
    r = _correr(
        "import sys\n"
        "sys.path.insert(0, '.'); sys.path.insert(0, 'scripts')\n"
        "import config\n"
        "import descargar_series as ds\n"
        "@ds._con_config_de_vida\n"
        "def pedir():\n"
        "    ds._entrar_a_vida_cotidiana()\n"
        "    from config import RIPTE_CSV\n"
        "pedir()\n"
        "from config import PESOS_CINTURONES, SIGLAS_PUBLICAS\n"
        "print('ok')\n"
    )
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-800:]


def test_sin_config_previo_al_salir_se_importa_el_de_la_raiz():
    """Hallado por Codex: el decorador restauraba sys.modules pero no sys.path,
    así que sin un config previo el siguiente `import config` encontraba el de
    vida, que había quedado primero en la ruta."""
    r = _correr(
        "import sys\n"
        "sys.path.insert(0, 'scripts')\n"
        "import descargar_series as ds\n"
        "sys.modules.pop('config', None)\n"
        "@ds._con_config_de_vida\n"
        "def pedir():\n"
        "    ds._entrar_a_vida_cotidiana()\n"
        "    from config import RIPTE_CSV\n"
        "pedir()\n"
        "from config import PESOS_CINTURONES\n"
        "print('ok')\n"
    )
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-800:]
