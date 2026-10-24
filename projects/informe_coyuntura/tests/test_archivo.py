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
    con_pagina = {m["mes"] for m in INDICE["meses"] if m.get("pagina")}
    for mes in meses:
        assert re.fullmatch(r"\d{4}-\d{2}", mes), mes
    # Sólo los meses verificados (sin datos posteriores al mes) se enlazan y
    # tienen foto; una foto sin verificar no se publica ni por link directo.
    for mes in con_pagina:
        foto = FOTOS / mes / "index.html"
        assert foto.exists() and foto.stat().st_size > 100_000, f"{mes}: falta la foto o está vacía"
    publicadas = {p.name for p in FOTOS.iterdir() if p.is_dir()} if FOTOS.exists() else set()
    assert publicadas == con_pagina, f"fotos publicadas {sorted(publicadas)} ≠ meses verificados {sorted(con_pagina)}"


def test_la_foto_es_autocontenida_y_sin_muro():
    """El emisor ya aborta si queda una llamada a un tercero; acá se cuida que el
    archivo no herede el muro (la foto se arma con PUBLIC_MURO=0)."""
    for m in (x for x in INDICE["meses"] if x.get("pagina")):
        html = (FOTOS / m["mes"] / "index.html").read_text(encoding="utf-8", errors="ignore")
        assert 'id="cg-muro"' not in html, f"{m['mes']}: la foto quedó con el muro"
        assert "googletagmanager" not in html, f"{m['mes']}: la foto quedó con GA"


def test_las_cards_exentas_de_g3_no_salen_del_ultimo_punto_de_su_serie():
    """RIGI publica el % de la cartera y su serie guarda el monto en M USD: el
    septiembre-2026 rehecho salió con «49.766 %» (los US$ M aprobados), puntuado
    100, porque cada card tomaba el último punto de su serie. Las exentas de G3
    toman la card de la foto del mes, y sin foto no se inventan."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    import archivo
    from gate_calidad import G3_EXCEPCIONES

    ultimo = {"rigi_inversiones": ("2026-09-01", 49766.0), "privatizaciones": ("2026-09-01", 55.6)}
    foto = {"rigi_inversiones": ("2026-09-30", 23.8)}
    cards = {"rigi_inversiones": {"valor": 33.3, "unidad": "%", "fecha_dato": "2026-10-20"},
             "privatizaciones": {"valor": 60.0, "unidad": "%", "fecha_dato": "2026-10-20"}}

    con_foto = archivo.cortar_indicadores(cards, archivo.con_cards_exentas(ultimo, set(G3_EXCEPCIONES), foto), "2026-09")
    assert con_foto["rigi_inversiones"]["valor"] == 23.8
    assert con_foto["privatizaciones"]["valor"] == 55.6

    sin_foto = archivo.cortar_indicadores(cards, archivo.con_cards_exentas(ultimo, set(G3_EXCEPCIONES), {}), "2026-09")
    assert "rigi_inversiones" not in sin_foto, "sin foto, una card de octubre no puede entrar a septiembre"
