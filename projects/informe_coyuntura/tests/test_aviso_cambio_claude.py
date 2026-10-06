"""Los avisos de los cambios pedidos desde claude.ai: qué avisa y, sobre todo,
qué NO avisa. Un cambio de texto que pasa todo no puede mandar nada: el canal
vive de que el bot hable sólo cuando hay algo que mirar."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aviso_cambio_claude as av  # noqa: E402

P = "projects/informe_coyuntura/"
CUERPO = "Pedido por **Luis Babino** conversando con Claude en claude.ai.\n\nArchivos: ..."


def test_quien_lo_pidio_sale_del_cuerpo_del_pr():
    assert av.pedido_por(CUERPO) == "Luis Babino"
    assert av.pedido_por("") == "alguien desde claude.ai"


def test_un_cambio_de_texto_que_pasa_todo_no_avisa():
    archivos = [P + "web/src/components/Hero.astro", P + "web/src/components/NivelTension.astro"]
    assert av.motivos(archivos, 11, "success", []) == []


def test_las_fichas_regeneradas_no_cuentan_como_cambio_grande():
    archivos = [P + "web/src/lib/fichas.ts"] + [P + f"output/fichas/fichas-{c}.md"
                                                for c in ("macro", "politica", "gestion", "vida_cotidiana", "x", "y")]
    assert av.motivos(archivos, 40, "success", []) == []


def test_pruebas_en_rojo_avisan_con_lo_que_fallo(tmp_path):
    (tmp_path / "pytest.log").write_text(
        "....\nFAILED tests/test_siglas_publicas.py::test_x - AssertionError\n1 failed\n", encoding="utf-8")
    lista = av.motivos([P + "web/src/lib/datos.ts"], 3, "failure", av.fallas(str(tmp_path)))
    assert lista[0][0] == "🔴"
    assert "test_siglas_publicas" in lista[0][1]


@pytest.mark.parametrize("ruta, zona", [
    ("scripts/itcm.py", "cálculo"),
    ("scripts/parametrica.py", "cálculo"),
    ("config.py", "configuración"),
    ("scripts/publicar.py", "card"),
    ("scripts/politica.py", "colector"),
    ("scripts/vida_cotidiana/collectors/snic.py", "colector"),
    ("data/gestion/x.json", "datos"),
])
def test_tocar_lo_sensible_avisa(ruta, zona):
    lista = av.motivos([P + ruta], 2, "success", [])
    assert lista and lista[0][0] == "🟡" and zona in lista[0][1]


def test_muchos_cambios_de_golpe_avisan():
    seis = [P + f"web/src/components/C{i}.astro" for i in range(6)]
    assert any("muchas cosas" in t for _, t in av.motivos(seis, 20, "success", []))
    assert any("muchas cosas" in t for _, t in av.motivos([P + "web/src/lib/fichas.ts"], 301, "success", []))
    assert not av.motivos(seis[:5], 300, "success", [])


def test_el_aviso_dice_quien_que_cambio_y_el_pr():
    t = av.texto_cambio(52, "https://github.com/x/pull/52", "Sacar la leyenda del hero", "Luis Babino",
                        [P + "scripts/itcm.py"], [("🟡", "Toca el cálculo de los índices.")])
    assert "Luis Babino" in t and "Sacar la leyenda del hero" in t and "#52" in t
    assert t.startswith("🟡 *Monitor del Plan de Gobierno")
    assert "`scripts/itcm.py`" in t


def test_un_rojo_manda_sobre_un_amarillo_en_la_cabecera():
    t = av.texto_cambio(1, "u", "t", "q", [P + "scripts/itcm.py"],
                        [("🔴", "pruebas en rojo"), ("🟡", "toca el cálculo")])
    assert t.startswith("🔴")


def test_deploy_y_pagina_bien_no_avisa():
    assert av.texto_deploy(1, "u", "t", "q", "success", "200") is None


@pytest.mark.parametrize("estado, http, dice", [
    ("failure", "200", "falló"),
    ("pending", "200", "no terminó"),
    ("success", "500", "no carga"),
    ("success", "", "no carga"),
])
def test_deploy_o_pagina_mal_avisa(estado, http, dice):
    t = av.texto_deploy(7, "u", "t", "Juan", estado, http)
    assert t and dice in t and "#7" in t and "Juan" in t


def test_corrida_bien_no_avisa_y_mal_si():
    assert av.texto_corrida(1, "u", "t", "q", "success", "c") is None
    t = av.texto_corrida(3, "u", "t", "q", "failure", "https://run")
    assert t and "#3" in t and "https://run" in t


def test_sin_credenciales_no_hace_nada_y_sale_con_cero(tmp_path, monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    datos = tmp_path / "pr.json"
    datos.write_text(json.dumps({"title": "t", "url": "u", "body": CUERPO,
                                 "files": [{"path": P + "scripts/itcm.py"}],
                                 "additions": 1, "deletions": 1}), encoding="utf-8")
    assert av.main(["evaluar", "--pr", "1", "--datos-pr", str(datos)]) == 0


def test_evaluar_publica_una_vez_y_deja_el_hilo(tmp_path, monkeypatch):
    enviados = []
    monkeypatch.setattr(av, "publicar", lambda texto, hilo="": enviados.append((texto, hilo)) or "123.4")
    salida = tmp_path / "out"
    monkeypatch.setenv("GITHUB_OUTPUT", str(salida))
    datos = tmp_path / "pr.json"
    datos.write_text(json.dumps({"title": "Recalibrar inversión", "url": "u", "body": CUERPO,
                                 "files": [{"path": P + "scripts/itcm.py"}],
                                 "additions": 4, "deletions": 2}), encoding="utf-8")
    av.main(["evaluar", "--pr", "9", "--datos-pr", str(datos)])
    assert len(enviados) == 1 and "Recalibrar inversión" in enviados[0][0]
    assert "hilo=123.4" in salida.read_text()
