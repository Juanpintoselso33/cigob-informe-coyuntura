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


def test_un_dato_anual_conserva_su_fecha_en_el_mes_rehecho():
    """La serie de piquetes repite el dato de 2025 mes a mes: el último punto
    hasta septiembre es 2026-09-01 y la edición de septiembre lo fechaba en
    2026. Si la card trae el mismo valor con una fecha que no pasa del mes, se
    queda con la suya; un valor distinto, o una fecha posterior, no."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    import archivo

    ultimo = {"protocolo_antipiquetes": ("2026-09-01", 74.2), "cepo_mulc": ("2026-09-01", 6.27)}
    cards = {"protocolo_antipiquetes": {"valor": 74.2, "fecha_dato": "2025-12-31"},
             "cepo_mulc": {"valor": 8.14, "fecha_dato": "2026-10-24", "usuarios_prepagas": 1}}
    cortadas = archivo.cortar_indicadores(cards, ultimo, "2026-09")
    assert cortadas["protocolo_antipiquetes"]["fecha_dato"] == "2025-12-31"
    # El total de salud acompaña a su dato; con otro dato no se arrastra.
    salud = {"libertad_opcion_salud": {"valor": 33.1, "fecha_dato": "2026-06-01", "derivados": 2754461, "usuarios_prepagas": 8332458}}
    s = archivo.cortar_indicadores(salud, {"libertad_opcion_salud": ("2026-09-01", 33.1)}, "2026-09")["libertad_opcion_salud"]
    assert (s["derivados"], s["usuarios_prepagas"], s["fecha_dato"]) == (2754461, 8332458, "2026-06-01")
    # Si el padrón de prepagas ya es de octubre, ese total no es el de septiembre.
    salud["libertad_opcion_salud"]["fecha_denominador"] = "2026-10-01"
    s = archivo.cortar_indicadores(salud, {"libertad_opcion_salud": ("2026-09-01", 33.1)}, "2026-09")["libertad_opcion_salud"]
    assert "usuarios_prepagas" not in s and s["valor"] == 33.1
    # El desglose por sector de desregulación acompaña a su informe (ADR-0363).
    des = {"desregulacion_normativa": {"valor": 17606.0, "fecha_dato": "2026-09-01", "normas_por_sector": {"Agroindustria": 129}}}
    d = archivo.cortar_indicadores(des, {"desregulacion_normativa": ("2026-09-01", 17606.0)}, "2026-09")["desregulacion_normativa"]
    assert d["normas_por_sector"] == {"Agroindustria": 129}
    d = archivo.cortar_indicadores(des, {"desregulacion_normativa": ("2026-08-01", 17115.0)}, "2026-08")["desregulacion_normativa"]
    assert "normas_por_sector" not in d and d["valor"] == 17115.0
    # La poda de la validación externa saca los meses posteriores, en cualquier nivel.
    v = {"merval_usd_mensual": {"2026-09": 1, "2026-10": 2}, "a": {"serie": {"2026-10-03": 3, "2026-08": 4}}, "giros": [{"mes": "2026-10"}]}
    assert archivo.podar_meses(v, "2026-09") == {"merval_usd_mensual": {"2026-09": 1}, "a": {"serie": {"2026-08": 4}}, "giros": [{"mes": "2026-10"}]}
    assert cortadas["cepo_mulc"] == {"valor": 6.27, "fecha_dato": "2026-09-01", "desactualizado": False}


def _arbol_del_corte(raiz: Path, mes: str = "2026-09") -> Path:
    """Un proyecto mínimo con los archivos de archivo.CORTE_RAMA, todos del
    corte del 30-sep-2026."""
    gen = "2026-09-30T23:00:00+00:00"
    escribir = lambda rel, txt: ((raiz / rel).parent.mkdir(parents=True, exist_ok=True), (raiz / rel).write_text(txt, encoding="utf-8"))
    sitio = {"generated_at": gen, "period": mes,
             "cinturones": {"gestion": {"itcg": {"valor": 79.1},
                                        "indicadores": {"cepo_mulc": {"valor": 6.27, "fecha_dato": "2026-09-29"}}}}}
    escribir("web/src/data/informe.json", json.dumps(sitio))
    escribir("web/src/data/series.json", json.dumps({"cepo_mulc": [{"fecha": "2026-09-01", "valor": 6.27}]}))
    escribir("output/informe.json", json.dumps({"generated_at": gen}))
    escribir("output/validacion_externa.json", json.dumps({"_meta": {"generated_at": gen}, "merval_usd_mensual": {"2026-09": 1.0}}))
    escribir("output/sensibilidad.json", json.dumps({"_meta": {"snapshot": gen}, "itcg": {"valor_publicado": 79.1}}))
    escribir("output/series/gestion.csv", "fecha,indicador,valor\n2026-09-01,cepo_mulc,6.27\n")
    escribir("output/fichas/fichas-gestion.md", "*Datos al 2026-09-30.*\n")
    escribir("data/historico/indicadores.json", json.dumps({"cepo_mulc": {"2026-09": 6.27}}))
    return raiz


def test_el_control_del_corte_unico_atrapa_cada_archivo_de_otro_mes(tmp_path):
    """Lo pidió la auditoría externa del cinturón de Gestión (23-oct-2026): la
    página decía septiembre y las fichas, la robustez y los CSV de la rama
    decían octubre. Se rompe un archivo por vez y el control tiene que verlo."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    import archivo

    assert archivo.verificar_corte(_arbol_del_corte(tmp_path / "ok"), "2026-09") == []

    roturas = {
        "una card de octubre": ("web/src/data/informe.json", lambda d: d["cinturones"]["gestion"]["indicadores"]["cepo_mulc"].update(fecha_dato="2026-10-24")),
        "una serie con octubre": ("web/src/data/series.json", lambda d: d["cepo_mulc"].append({"fecha": "2026-10-01", "valor": 8.1})),
        "output/informe.json de otra corrida": ("output/informe.json", lambda d: d.update(generated_at="2026-10-24T03:31:06")),
        "la robustez de otra corrida": ("output/sensibilidad.json", lambda d: d["_meta"].update(snapshot="2026-10-24T03:31:06")),
        "la robustez con otro índice": ("output/sensibilidad.json", lambda d: d["itcg"].update(valor_publicado=78.6)),
        "la validación externa con octubre": ("output/validacion_externa.json", lambda d: d["merval_usd_mensual"].update({"2026-10": 1.1})),
        "el histórico con octubre": ("data/historico/indicadores.json", lambda d: d["cepo_mulc"].update({"2026-10": 8.1})),
    }
    for nombre, (rel, romper) in roturas.items():
        raiz = _arbol_del_corte(tmp_path / nombre.replace(" ", "_"))
        datos = json.loads((raiz / rel).read_text(encoding="utf-8"))
        romper(datos)
        (raiz / rel).write_text(json.dumps(datos), encoding="utf-8")
        assert archivo.verificar_corte(raiz, "2026-09"), f"no vio {nombre}"

    raiz = _arbol_del_corte(tmp_path / "csv")
    with open(raiz / "output/series/gestion.csv", "a", encoding="utf-8") as f:
        f.write("2026-10-01,cepo_mulc,8.1\n")
    assert archivo.verificar_corte(raiz, "2026-09"), "no vio un CSV con octubre"

    raiz = _arbol_del_corte(tmp_path / "ficha")
    (raiz / "output/fichas/fichas-gestion.md").write_text("*Datos al 2026-10-24.*\n", encoding="utf-8")
    assert archivo.verificar_corte(raiz, "2026-09"), "no vio una ficha de octubre"
