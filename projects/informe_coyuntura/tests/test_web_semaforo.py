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

    def test_ningun_corte_del_semaforo_hardcodeado_en_ts(self):
        prohibidos = (">= 95", ">= 90", ">= 105", ">= 85")
        for archivo in LIB.glob("*.ts"):
            texto = archivo.read_text(encoding="utf-8")
            for patron in prohibidos:
                assert patron not in texto, f"{archivo.name}: corte hardcodeado {patron}"
