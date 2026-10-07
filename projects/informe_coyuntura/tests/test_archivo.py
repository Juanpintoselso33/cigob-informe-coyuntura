"""El archivo de informes mensuales (ADR-0348) no puede prometer un mes que no
tiene: cada tarjeta de web/src/contenido/archivo.json necesita su foto en
web/public/archivo/AAAA-MM/index.html, y una foto sin tarjeta no se ve desde
/archivo/."""
import json
import re
from pathlib import Path

WEB = Path(__file__).parent.parent / "web"
INDICE = json.loads((WEB / "src" / "contenido" / "archivo.json").read_text(encoding="utf-8"))
FOTOS = WEB / "public" / "archivo"


def test_cada_tarjeta_tiene_su_foto_y_viceversa():
    meses = [m["mes"] for m in INDICE["meses"]]
    assert len(meses) == len(set(meses)), "un mes repetido en el índice del archivo"
    assert meses == sorted(meses, reverse=True), "el archivo va del mes más nuevo al más viejo"
    for mes in meses:
        assert re.fullmatch(r"\d{4}-\d{2}", mes), mes
        foto = FOTOS / mes / "index.html"
        assert foto.exists() and foto.stat().st_size > 100_000, f"{mes}: falta la foto o está vacía"
    sueltas = {p.name for p in FOTOS.iterdir() if p.is_dir()} - set(meses) if FOTOS.exists() else set()
    assert not sueltas, f"fotos sin tarjeta en /archivo/: {sorted(sueltas)}"


def test_la_foto_es_autocontenida_y_sin_muro():
    """El emisor ya aborta si queda una llamada a un tercero; acá se cuida que el
    archivo no herede el muro (la foto se arma con PUBLIC_MURO=0)."""
    for m in INDICE["meses"]:
        html = (FOTOS / m["mes"] / "index.html").read_text(encoding="utf-8", errors="ignore")
        assert 'id="cg-muro"' not in html, f"{m['mes']}: la foto quedó con el muro"
        assert "googletagmanager" not in html, f"{m['mes']}: la foto quedó con GA"
