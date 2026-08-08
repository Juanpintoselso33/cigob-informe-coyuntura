"""Los cuatro colores del semáforo existen en el CSS y no hay cortes duplicados en TS."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSS = RAIZ / "web" / "public" / "dashboard.css"
LIB = RAIZ / "web" / "src" / "lib"

COLORES = ("verde", "amarillo", "naranja", "rojo")


class TestTokensCss:
    def test_los_cuatro_colores_tienen_token_y_variante_soft(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert re.search(rf"--{color}:\s*#", css), f"falta el token --{color}"
            assert re.search(rf"--{color}-soft:\s*#", css), f"falta --{color}-soft"

    def test_los_cuatro_colores_pintan_genoma_y_verdict(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert f".cg-genoma-seg.sem-{color}" in css, f"falta .sem-{color}"
            assert f".cg-verdict.{color}" in css, f"falta .cg-verdict.{color}"

    def test_los_cuatro_colores_pintan_el_punto_del_verdict(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert re.search(rf"\.cg-verdict\.{color}\s+\.cg-verdict-dot", css), f"falta punto de {color} en verdict"


class TestSinCortesDuplicadosEnTs:
    def test_datos_ts_no_recalcula_el_semaforo(self):
        """Los cortes viven solo en parametrica.py. Si el cliente los repite,
        se desincronizan sin que falle nada."""
        ts = (LIB / "datos.ts").read_text(encoding="utf-8")
        assert "semaforoDimension" not in ts, (
            "semaforoDimension calculaba el color en el cliente; "
            "tiene que leer el color publicado")
        assert "semaforoDe" in ts, "falta el lector semaforoDe"

    def test_ningun_ts_deriva_el_color_de_un_numero(self):
        """El invariante real, no una lista de cortes conocidos.

        La versión anterior de este test prohibía literales puntuales
        (">= 95", ">= 90", ">= 105", ">= 85") — los cortes del ITVC
        base-100. Eso dejaba totalmente afuera los cortes 60/40/20 del
        0-100 que usan ITCM, ITCG e ITCP (el "puntaje >= 60 ? verde : ..."
        original de semaforoDimension no llevaba ningún ">= 9x", así que la
        lista nunca lo habría atrapado). El invariante que de verdad importa
        no es "no aparezcan estos números": es que ninguna línea que nombre
        un color del semáforo lo derive de comparar un número — cualquiera
        sea el corte, hoy o el que se agregue mañana.
        """
        color = re.compile("|".join(COLORES))
        comparacion_numerica = re.compile(r"[<>]=?\s*\d|\d\s*[<>]=?")
        for archivo in LIB.glob("*.ts"):
            for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
                if color.search(linea) and comparacion_numerica.search(linea):
                    raise AssertionError(
                        f"{archivo.name}:{n}: el color se deriva de una "
                        f"comparación numérica en el cliente — {linea.strip()!r}")
