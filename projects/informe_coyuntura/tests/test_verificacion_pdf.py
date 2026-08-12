# -*- coding: utf-8 -*-
"""El segundo lector de PDF avisa, no decide, y nunca rompe la corrida (ADR-0198).

Ningún test de acá llama al modelo: se fija la LÓGICA —qué cuenta como
discrepancia, cuándo se ahorra la consulta, y que un fallo del verificador no
se propague—. La calidad del modelo se midió aparte, con un benchmark contra la
verdad leída a mano, y está registrada en el docstring del script.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import verificacion_pdf as vp  # noqa: E402

CAMPOS = {"vacuna": 1, "aviar": 1, "total": 1}


def test_lecturas_iguales_no_son_discrepancia():
    assert vp.comparar({"vacuna": 47.28, "aviar": 47.24, "total": 114.45},
                       {"vacuna": 47.28, "aviar": 47.24, "total": 114.45},
                       CAMPOS) == []


def test_el_caso_real_que_motiva_todo_esto():
    """gemini-2.5-flash leía aviar=51,21, que es el valor de carne VACUNA del
    año anterior en el mismo gráfico aplanado. Agarrar la columna de al lado es
    exactamente el modo de falla que el parser de regex también tiene, y el que
    ningún gate ve: el número es plausible y está mal."""
    fuera = vp.comparar({"vacuna": 47.28, "aviar": 47.24, "total": 114.45},
                        {"vacuna": 47.28, "aviar": 51.21, "total": 114.45},
                        CAMPOS)
    assert [d["campo"] for d in fuera] == ["aviar"]
    assert fuera[0]["parser"] == 47.24 and fuera[0]["modelo"] == 51.21


def test_el_modelo_que_se_abstiene_no_dispara_alarma():
    """Un None del modelo es abstención, no contradicción. Flash-Lite devolvía
    nulos en el documento difícil: inútil, pero no una acusación contra el
    parser. Tratarlo como discrepancia llenaría el informe de ruido."""
    assert vp.comparar({"vacuna": 47.28}, {"vacuna": None}, {"vacuna": 1}) == []


def test_si_el_parser_no_leyo_y_el_modelo_si_tambien_se_reporta():
    """El caso inverso importa igual: el parser devolviendo None puede ser la
    fuente que cambió de layout, y el modelo leyendo bien es la evidencia."""
    fuera = vp.comparar({"vacuna": None}, {"vacuna": 47.28}, {"vacuna": 1})
    assert len(fuera) == 1 and fuera[0]["modelo"] == 47.28


def test_la_tolerancia_cubre_redondeo_y_no_un_digito_distinto():
    assert vp.comparar({"x": 47.28}, {"x": 47.29}, {"x": 1}) == []      # redondeo
    assert len(vp.comparar({"x": 47.28}, {"x": 47.38}, {"x": 1})) == 1  # otro número


def test_la_huella_cambia_con_el_documento():
    """El ahorro depende de esto: si el PDF no cambió, no se paga la consulta."""
    a, b = vp._huella("consumo 47,28"), vp._huella("consumo 47,29")
    assert a != b
    assert vp._huella("consumo 47,28") == a


def test_sin_credenciales_sale_por_cero(monkeypatch, capsys):
    """En modo sombra un verificador que no puede correr NO es un fallo del
    pipeline. Si esto devolviera != 0, un secreto vencido frenaría la
    publicación de datos que están perfectamente bien."""
    monkeypatch.setattr(vp, "_hay_credenciales", lambda: False)
    monkeypatch.setattr(sys, "argv", ["verificacion_pdf.py"])
    assert vp.main() == 0
    assert "sin credenciales" in capsys.readouterr().out


def test_un_fallo_del_modelo_no_tumba_la_corrida(monkeypatch, tmp_path, capsys):
    """Vertex caído, cuota agotada o un timeout: se omite el caso y se sigue.
    El verificador es opinión sobre el dato, no el dato."""
    def explota(*a, **k):
        raise RuntimeError("503 Service Unavailable")

    monkeypatch.setattr(vp, "_hay_credenciales", lambda: True)
    monkeypatch.setattr(vp, "SALIDA", tmp_path)
    monkeypatch.setattr(vp, "leer_con_modelo", explota)
    monkeypatch.setattr(vp, "casos", lambda: [
        {"clave": "falso", "campos": {"x": 1}, "pedido": "p",
         "obtener": lambda: ("texto del documento", {"x": 1.0})}])
    monkeypatch.setitem(sys.modules, "google.genai",
                        type(sys)("google.genai"))
    sys.modules["google.genai"].Client = lambda **k: object()
    monkeypatch.setattr(sys, "argv", ["verificacion_pdf.py"])
    assert vp.main() == 0
    assert "falló la consulta al modelo" in capsys.readouterr().out


def test_un_caso_omitido_no_borra_su_ultima_lectura(monkeypatch, tmp_path):
    """La segunda corrida del día no consulta nada. Si además pisara el informe,
    se perdería la evidencia que este script existe para acumular."""
    monkeypatch.setattr(vp, "SALIDA", tmp_path)
    texto = "documento"
    h = vp._huella(texto)
    (tmp_path / "estado.json").write_text(
        json.dumps({"falso": {"huella": h, "discrepancias": 0}}), encoding="utf-8")
    (tmp_path / "ultima.json").write_text(json.dumps(
        {"casos": [{"caso": "falso", "parser": {"x": 1.0}, "modelo": {"x": 1.0},
                    "discrepancias": []}]}), encoding="utf-8")

    monkeypatch.setattr(vp, "_hay_credenciales", lambda: True)
    monkeypatch.setattr(vp, "casos", lambda: [
        {"clave": "falso", "campos": {"x": 1}, "pedido": "p",
         "obtener": lambda: (texto, {"x": 1.0})}])
    monkeypatch.setitem(sys.modules, "google.genai", type(sys)("google.genai"))
    sys.modules["google.genai"].Client = lambda **k: object()
    monkeypatch.setattr(sys, "argv", ["verificacion_pdf.py"])
    assert vp.main() == 0

    guardado = json.loads((tmp_path / "ultima.json").read_text(encoding="utf-8"))
    assert [c["caso"] for c in guardado["casos"]] == ["falso"]
    assert guardado["casos"][0]["reusado"] is True


def test_el_modelo_esta_declarado_en_una_constante():
    """Se eligió midiendo, y las bajas de modelo son frecuentes: cambiarlo tiene
    que ser una línea, no una búsqueda por el archivo."""
    assert vp.MODELO.startswith("gemini-")
    assert vp.UBICACION == "global", (
        "los endpoints regionales sólo ofrecen la familia 2.5, que se da de baja "
        "no antes del 2026-10-16")
