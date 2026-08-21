"""`mortalidad_pymes` mide cierre de PyMEs. Recién desde ADR-0218.

Durante trece meses el indicador se llamó así y midió otra cosa: el IPI
manufacturero desestacionalizado del INDEC, o sea producción industrial. El
informe decía "mortalidad de PyMEs" y publicaba actividad fabril. ADR-0119 lo
había detectado y decidido no tocarlo hasta tener la fuente real.

La fuente real es la base de partes empleadoras de la SRT: cuando una PyME
cierra, quiebra o despide a toda su nómina, el contrato con la ART se rescinde
casi en el acto. Se suman los tramos de hasta 50 trabajadores.

Estos tests cuidan que no vuelva a divergir el nombre del contenido.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# El colector se carga POR RUTA y no por sys.path: `scripts/vida_cotidiana/`
# tiene su propio `config.py`, y ponerlo al frente del path tapa al del
# proyecto y rompe la colección de los otros diecisiete módulos de test.
_spec = importlib.util.spec_from_file_location(
    "srt_empleadores",
    ROOT / "scripts" / "vida_cotidiana" / "collectors" / "srt_empleadores.py")
_srt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_srt)
TRAMOS_PYME, TRAMOS_GRANDES = _srt.TRAMOS_PYME, _srt.TRAMOS_GRANDES

SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
DATOS_TS = (ROOT / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
IND = SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"]["mortalidad_pymes"]


def test_la_fuente_es_la_srt_y_no_el_ipi():
    fuente = IND.get("fuente", "")
    assert "SRT" in fuente, f"la fuente volvió a ser otra: {fuente!r}"
    assert "IPI" not in fuente, "volvió a medir producción industrial"


def test_la_card_cuenta_empleadores():
    """Un índice o un porcentaje no serviría: el número que importa es cuántas
    empresas quedan, y su caída en unidades es la noticia."""
    assert IND.get("unidad") == "empleadores", IND.get("unidad")
    assert IND.get("valor", 0) > 100_000, "la magnitud no es de un padrón de empleadores"
    assert 'mortalidad_pymes: "Empleadores PyME activos"' in DATOS_TS, (
        "la etiqueta pública volvió a prometer otra cosa")


def test_card_y_serie_son_el_mismo_numero():
    """La versión anterior tenía DOS series para este indicador —la card en %
    m/m del IPI y el índice en base 100— y por eso G3 no podía reconciliarlas.
    Ahora hay una sola, en unidades, y el rebase lo hace el motor."""
    serie = SERIES.get("mortalidad_pymes") or []
    assert serie, "sin serie publicada"
    assert abs(serie[-1]["valor"] - IND["valor"]) < 1, (
        f"card {IND['valor']} ≠ serie {serie[-1]['valor']}")
    assert "itvc_ipi" not in SERIES, "la serie del IPI quedó publicada de más"


def test_el_recorte_pyme_se_declara_por_tramo():
    """No se toma el total del sistema: se SUMAN los tramos de hasta 50. El
    total incluiría las grandes, y el indicador dejaría de decir PyME apenas
    cambie la proporción."""
    assert TRAMOS_PYME[-1] == "41 a 50", TRAMOS_PYME
    assert "51 a 100" not in TRAMOS_PYME, "se coló un tramo que no es PyME"
    assert "501 a 1500" in TRAMOS_GRANDES, "se perdió el contraste con las grandes"


def test_la_serie_llega_al_4t_2023():
    serie = SERIES["mortalidad_pymes"]
    assert serie[0]["fecha"][:7] <= "2023-10", (
        "la serie no cubre la base del índice")
    assert len(serie) >= 60, f"sólo {len(serie)} puntos"
