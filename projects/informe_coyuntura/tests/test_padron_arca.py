"""ADR-0389: padrón de empleadores de ARCA. Sin red, con CUIT inventados."""
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts/vida_cotidiana/collectors"))

import padron_arca as pa  # noqa: E402

# 20 registros de 21 caracteres con la forma real y CUIT cambiados:
# CUIT · ganancias · IVA · monotributo · sociedad · empleador · actividad
LINEAS = [
    "20000000011ACACNINS00",   # humana, empleador, no monotributista
    "20000000022ACACNINS00",   # humana, empleador, no monotributista
    "27000000033NINIB NS00",   # humana, empleador, monotributista (B)
    "30000000044ACACNINS00",   # jurídica, empleador
    "33000000055ACACNINS00",   # jurídica, empleador
    "20000000066ACACNINN00",
    "20000000077ACACNINN00",
    "20000000088ACNININN00",
    "23000000099ACNININN00",
    "24000000100ACNININN00",
    "27000000111NINIA NN00",
    "30000000122ACACNINN00",
    "30000000133ACACNINN00",
    "34000000144ACACNINN00",
    "20000000155ACACNIN 00",   # marca en blanco
    "20000000166ACACNIN 00",   # marca en blanco
    "20000000177ACACNINN00",
    "20000000188ACNININN00",
    "20000000199ACNININN00",
    "20000000200ACNININN00",
]


def test_las_lineas_de_prueba_tienen_el_largo_del_formato():
    assert {len(x) for x in LINEAS} == {21}


def test_el_parser_cuenta_cada_grupo():
    c = pa.contar([x + "\n" for x in LINEAS], minimo_registros=1)
    assert c == {"empleadores": 5, "juridicas": 2, "humanas": 3, "monotributistas": 1,
                 "blanco": 2, "cuit_total": 20}
    assert c["juridicas"] + c["humanas"] == c["empleadores"]


def test_acepta_bytes_y_lectura_por_bloques():
    datos = "".join(x + "\n" for x in LINEAS).encode("latin-1")
    por_bloques = list(pa._lineas(io.BytesIO(datos), bloque=7))
    assert pa.contar(por_bloques, minimo_registros=1)["empleadores"] == 5


def test_rechaza_un_largo_distinto():
    with pytest.raises(pa.FormatoInesperado, match="caracteres"):
        pa.contar(LINEAS[:-1] + ["2000000020ACACNINS00"], minimo_registros=1)


def test_rechaza_un_cuit_no_numerico():
    with pytest.raises(pa.FormatoInesperado, match="CUIT"):
        pa.contar(LINEAS[:-1] + ["2000000020XACACNINS00"], minimo_registros=1)


def test_rechaza_una_marca_inesperada():
    with pytest.raises(pa.FormatoInesperado, match="marca"):
        pa.contar(LINEAS[:-1] + ["20000000200ACACNINX00"], minimo_registros=1)


def test_rechaza_una_proporcion_implausible():
    todos = [x[:18] + "S" + x[19:] for x in LINEAS]
    with pytest.raises(pa.FormatoInesperado, match="proporción"):
        pa.contar(todos, minimo_registros=1)


def test_rechaza_un_archivo_demasiado_chico():
    with pytest.raises(pa.FormatoInesperado, match="registros"):
        pa.contar(LINEAS)


def test_el_zip_toma_la_fecha_del_nombre_interno(tmp_path):
    z = tmp_path / "p.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("utlfile/padr/SELE-SAL-CONSTA.p20out2.20261024.tmp",
                   "".join(x + "\n" for x in LINEAS))
    conteo, fecha = pa.contar_zip(z, minimo_registros=1)
    assert fecha == "2026-10-24" and conteo["empleadores"] == 5


def test_layout_con_nombres_lee_la_marca_en_la_posicion_49():
    con_nombre = [x[:11] + "X" * 30 + x[11:] for x in LINEAS]
    c = pa.contar(con_nombre, minimo_registros=1, layout=pa.LAYOUT_CON_NOMBRES)
    assert c["empleadores"] == 5 and c["monotributistas"] == 1


def _conteo(fecha, emp=100, jur=60, hum=40, blanco=5):
    return {"fecha_archivo": fecha, "empleadores": emp, "juridicas": jur, "humanas": hum,
            "monotributistas": 10, "blanco": blanco, "cuit_total": 1000}


def test_el_registro_guarda_un_valor_por_mes_el_mas_nuevo():
    m = pa.anotar({}, _conteo("2026-10-10", emp=100))
    m = pa.anotar(m, _conteo("2026-10-24", emp=120, jur=70, hum=50))
    assert list(m) == ["2026-10"] and m["2026-10"]["empleadores"] == 120
    # un archivo más viejo del mismo mes no pisa al más nuevo
    m = pa.anotar(m, _conteo("2026-10-17", emp=90))
    assert m["2026-10"]["fecha_archivo"] == "2026-10-24"
    m = pa.anotar(m, _conteo("2026-11-07"))
    assert list(m) == ["2026-10", "2026-11"]


def test_el_registro_versionado_es_valido_y_no_guarda_cuit():
    meses = pa.leer_registro()
    assert "2026-10" in meses and meses["2026-10"]["empleadores"] == 511847
    assert meses["2024-08"]["empleadores"] - meses["2026-10"]["empleadores"] == 41210
    crudo = (RAIZ / "data/vida/arca_empleadores.json").read_text(encoding="utf-8")
    assert "cuit" not in {k for m in json.loads(crudo)["meses"].values() for k in m}


def test_fetch_guarda_el_mes_y_si_la_red_falla_sigue_con_lo_guardado(tmp_path):
    reg = tmp_path / "reg.json"
    pa.guardar_registro({"2026-10": _conteo("2026-10-24")}, reg)
    r = pa.fetch_padron_arca(reg, descargar=lambda: _conteo("2026-11-07", emp=110, jur=65, hum=45))
    assert r["fresco"] and sorted(pa.leer_registro(reg)) == ["2026-10", "2026-11"]

    def caida():
        raise OSError("sin red")
    r = pa.fetch_padron_arca(reg, descargar=caida)
    assert not r["fresco"] and sorted(r["meses"]) == ["2026-10", "2026-11"]
    assert "Empleadores inscriptos en ARCA" in r["texto"]


def test_el_texto_de_la_card_con_los_datos_versionados():
    t = pa.texto_card(pa.leer_registro())
    assert t == ("Empleadores inscriptos en ARCA: 511.847 (24-oct-2026): 290.897 empresas y "
                 "sociedades y 220.950 personas. El 24-ago-2024 eran 553.057 (−7,5 %). "
                 "No puntúa todavía.")


def test_el_texto_con_un_solo_mes_no_inventa_variacion():
    t = pa.texto_card({"2026-10": _conteo("2026-10-24")})
    assert "contra" not in t and "No puntúa" in t


def test_publicar_agrega_el_texto_al_detalle_de_ocupacion_eph():
    sys.path.insert(0, str(RAIZ / "scripts"))
    import publicar
    raw = {"indec": {"ocupacion_eph": {"valor": 0.4, "tasa": 45.0, "tasa_2023": 44.6,
                                       "fecha": "2026-04-01"}},
           "padron_arca": {"texto": "Empleadores inscriptos en ARCA: 1."}}
    out = publicar.build_vida(raw)
    det = out["ocupacion_eph"]["detalle_txt"]
    assert det.startswith("Tasa de empleo 45,0%") and det.endswith("Empleadores inscriptos en ARCA: 1.")
    assert "padron_arca" not in out and "arca_empleadores" not in out   # no es card propia
