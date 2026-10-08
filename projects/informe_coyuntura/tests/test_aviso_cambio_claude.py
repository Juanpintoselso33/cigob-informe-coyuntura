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


# ── ADR-0350: no culpar a un cambio por lo que ya estaba roto ───────────────
#
# El 8-oct-2026 los PR #59 a #62 de Luis mandaron cuatro 🔴 «se publicó con algo
# roto». #59 rompió una prueba, #60 otras dos; #61 y #62 no rompieron nada y sus
# 🔴 repetían las tres. El log está en la forma que escribe el `tee` del job
# `validar` (salida de `pytest -q`).

SEMAFORO = ("FAILED tests/test_web_semaforo.py::TestLeyendaNoHardcodeaLosCortes::"
            "test_no_hardcodea_ningun_corte_conocido - AssertionError: SemaforoLeyenda.astro:58: "
            "aparece el literal '8', uno de los cortes")
PARRAFO = ("FAILED tests/test_marco_conceptual.py::test_el_parrafo_original_sigue_publicado - "
           "AssertionError: El encuadre conceptual del informe se borró o se reescribió")
ESCALA = ("FAILED tests/test_marco_conceptual.py::test_la_escala_sigue_explicada_en_metodologia - "
          "AssertionError: /metodologia dejó de explicar qué significa cada color")
from datetime import datetime, timezone  # noqa: E402

AHORA = datetime(2026, 10, 8, 19, 0, tzinfo=timezone.utc)


class SlackFalso:
    def __init__(self):
        self.llamadas = []

    def __call__(self, metodo, **datos):
        self.llamadas.append(dict(metodo=metodo, **datos))
        return {"ok": True, "ts": f"300.{len(self.llamadas)}"}

    def posts(self):
        return [c for c in self.llamadas if c["metodo"] == "chat.postMessage"]

    def en_el_canal(self):
        return [c for c in self.posts() if "thread_ts" not in c or c.get("reply_broadcast")]

    def ediciones(self):
        return [c for c in self.llamadas if c["metodo"] == "chat.update"]


@pytest.fixture
def slack(monkeypatch):
    s = SlackFalso()
    monkeypatch.setattr(av, "_slack", s)
    return s


def cambio(tmp_path, pr, archivos, rojas, ahora=AHORA, modo="evaluar", extra=()):
    d = tmp_path / f"pr{pr}"
    d.mkdir(exist_ok=True)
    (d / "pr.json").write_text(json.dumps({
        "title": f"Cambio {pr}", "url": f"https://github.com/x/pull/{pr}", "body": CUERPO,
        "files": [{"path": P + a} for a in archivos], "additions": 3, "deletions": 1}), encoding="utf-8")
    if rojas:
        (d / "pytest.log").write_text("....F..\n" + "\n".join(rojas) + f"\n{len(rojas)} failed, 3300 passed\n",
                                      encoding="utf-8")
    args = [modo, "--pr", str(pr), "--datos-pr", str(d / "pr.json"),
            "--archivo-estado", str(tmp_path / "estado" / "estado.json")]
    if modo == "evaluar":
        args += ["--pruebas", "failure" if rojas else "success", "--logs", str(d)]
    assert av.main(args + list(extra), ahora=ahora) == 0


def estado(tmp_path):
    return json.loads((tmp_path / "estado" / "estado.json").read_text())


def test_el_8_oct_con_las_reglas_nuevas(slack, tmp_path):
    cambio(tmp_path, 59, ["web/src/components/SemaforoLeyenda.astro", "web/src/pages/index.astro"], [SEMAFORO])
    cambio(tmp_path, 60, ["web/src/pages/metodologia/index.astro"], [PARRAFO, ESCALA, SEMAFORO])
    cambio(tmp_path, 61, ["web/src/pages/metodologia/index.astro"], [PARRAFO, ESCALA, SEMAFORO])
    cambio(tmp_path, 62, ["web/src/pages/[slug].astro"], [PARRAFO, ESCALA, SEMAFORO])
    canal = slack.en_el_canal()
    assert len(canal) == 3                                           # antes: 4, dos de ellos falsos
    r59, r60, main_rojo = canal
    assert r59["text"].startswith("🔴") and "#59" in r59["text"] and "test_web_semaforo" in r59["text"]
    # #60 sólo carga con lo suyo; la prueba de #59 se nombra como heredada.
    assert "#60" in r60["text"] and "test_marco_conceptual" in r60["text"]
    assert "test_web_semaforo" not in r60["text"] and "1 ya estaba en rojo en main" in r60["text"]
    # #61 y #62 no rompieron nada: ni un 🔴 con su número.
    assert not any(c["text"].startswith("🔴") and ("#61" in c["text"] or "#62" in c["text"])
                   for c in slack.posts())
    assert main_rojo["text"].startswith("🟡 *Monitor del Plan de Gobierno — main tiene 3 pruebas en rojo")
    assert "deshaga" not in main_rojo["text"]
    ultima = slack.ediciones()[-1]
    assert ultima["ts"] == estado(tmp_path)["main_rojas"]["ts"]
    assert "Lleva 2 cambios encima:* #61, #62" in ultima["text"]
    assert estado(tmp_path)["main_rojas"]["cambios"] == [61, 62]


def test_main_en_verde_cierra_el_hilo_sin_salir_al_canal(slack, tmp_path):
    cambio(tmp_path, 60, [], [SEMAFORO])
    cambio(tmp_path, 61, ["web/src/pages/x.astro"], [SEMAFORO])
    cambio(tmp_path, 62, ["web/src/pages/x.astro"], [SEMAFORO])
    abierto = estado(tmp_path)["main_rojas"]
    cambio(tmp_path, 63, ["web/src/pages/x.astro"], [])
    assert "main_rojas" not in estado(tmp_path) and estado(tmp_path)["rojas"] == []
    assert slack.ediciones()[-1]["ts"] == abierto["ts"] and slack.ediciones()[-1]["text"].startswith("✅")
    respuesta = slack.posts()[-1]
    assert respuesta["thread_ts"] == abierto["ts"] and not respuesta.get("reply_broadcast")


def test_la_corrida_nocturna_en_verde_tambien_lo_cierra(slack, tmp_path):
    cambio(tmp_path, 60, [], [SEMAFORO])
    cambio(tmp_path, 61, ["web/src/pages/x.astro"], [SEMAFORO])
    assert "main_rojas" in estado(tmp_path)
    assert av.main(["verde", "--archivo-estado", str(tmp_path / "estado" / "estado.json")], ahora=AHORA) == 0
    assert "main_rojas" not in estado(tmp_path) and estado(tmp_path)["rojas"] == []
    assert slack.ediciones()[-1]["text"].startswith("✅")


def test_otro_conjunto_heredado_reemplaza_el_hilo(slack, tmp_path):
    cambio(tmp_path, 60, [], [SEMAFORO])
    cambio(tmp_path, 61, ["web/src/pages/x.astro"], [SEMAFORO])          # abre {SEMAFORO}
    cambio(tmp_path, 62, ["web/src/pages/x.astro"], [SEMAFORO, PARRAFO])   # PARRAFO es nueva: 🔴 del #62
    cambio(tmp_path, 63, ["web/src/pages/x.astro"], [SEMAFORO, PARRAFO])   # {SEMAFORO, PARRAFO} heredadas
    raices = [c for c in slack.posts() if "thread_ts" not in c and "main tiene" in c["text"]]
    assert len(raices) == 2 and "main tiene 2 pruebas" in raices[-1]["text"]
    assert estado(tmp_path)["main_rojas"]["cambios"] == [63]


def test_sin_estado_previo_se_culpa_como_antes(slack, tmp_path):
    cambio(tmp_path, 61, ["web/src/pages/x.astro"], [PARRAFO, SEMAFORO])
    [r] = slack.en_el_canal()
    assert r["text"].startswith("🔴") and "test_marco_conceptual" in r["text"]


def test_una_falla_sin_log_legible_culpa_y_deja_el_estado_desconocido(slack, tmp_path):
    cambio(tmp_path, 60, [], [SEMAFORO])
    d = tmp_path / "pr70"
    d.mkdir()
    (d / "pr.json").write_text(json.dumps({"title": "t", "url": "u", "body": CUERPO, "files": [],
                                           "additions": 1, "deletions": 1}), encoding="utf-8")
    av.main(["evaluar", "--pr", "70", "--datos-pr", str(d / "pr.json"), "--pruebas", "failure",
             "--logs", str(d), "--archivo-estado", str(tmp_path / "estado" / "estado.json")], ahora=AHORA)
    assert "ver el detalle en el PR" in slack.posts()[-1]["text"]
    assert estado(tmp_path)["rojas"] is None


# ── ADR-0350: el tope de deploys de Vercel no es una falla del cambio ───────

TOPE = ["--estado", "failure", "--http", "200", "--descripcion", "Deployment rate limited — retry in 24 hours",
        "--fecha-status", "2026-10-07T19:48:00Z"]


def test_el_tope_de_vercel_avisa_en_amarillo_sin_pedir_que_se_deshaga(slack, tmp_path):
    cambio(tmp_path, 57, ["web/src/pages/index.astro"], [], modo="deploy", extra=TOPE)
    [r] = slack.en_el_canal()
    assert r["text"].startswith("🟡 *Monitor del Plan de Gobierno — Vercel llegó al tope de deploys")
    assert "thread_ts" not in r                                       # aparte, no en el hilo del cambio
    assert "deshaga" not in r["text"] and "nada que deshacer" in r["text"]
    assert "la versión anterior" in r["text"]
    assert "16:48 del 8-oct" in r["text"]                              # 19:48 UTC + 24 h, en hora argentina


def test_un_tope_avisa_una_vez_y_suma_los_cambios_que_caen_adentro(slack, tmp_path):
    cambio(tmp_path, 57, [], [], modo="deploy", extra=TOPE)
    cambio(tmp_path, 58, [], [], modo="deploy", extra=TOPE)
    assert len(slack.en_el_canal()) == 1
    assert "#57" in slack.ediciones()[-1]["text"] and "#58" in slack.ediciones()[-1]["text"]
    despues = datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc)
    cambio(tmp_path, 59, [], [], modo="deploy", extra=TOPE, ahora=despues)
    assert len(slack.en_el_canal()) == 2                              # otro tope, otro aviso


def test_sin_la_hora_del_status_dice_24_horas(slack, tmp_path):
    cambio(tmp_path, 57, [], [], modo="deploy",
           extra=["--estado", "error", "--http", "200", "--descripcion", "Resource is limited"])
    assert "≈24 h" in slack.posts()[0]["text"]


def test_si_no_se_lee_el_status_es_el_rojo_de_siempre(slack, tmp_path):
    cambio(tmp_path, 57, [], [], modo="deploy", extra=["--estado", "failure", "--http", "200"])
    [r] = slack.posts()
    assert r["text"].startswith("🔴") and "deshaga" in r["text"]


def test_tope_y_pagina_caida_avisa_las_dos_cosas(slack, tmp_path):
    cambio(tmp_path, 57, [], [], modo="deploy", extra=[*TOPE[:2], "--http", "500", *TOPE[4:]])
    textos = [c["text"] for c in slack.posts()]
    assert any(t.startswith("🟡") and "tope" in t for t in textos)
    assert any(t.startswith("🔴") and "no carga" in t and "Vercel falló" not in t for t in textos)


# ── El workflow pasa y guarda el estado ─────────────────────────────────────

def _flujo(nombre):
    import yaml
    return yaml.safe_load((Path(__file__).resolve().parents[3] / ".github" / "workflows" / nombre)
                          .read_text(encoding="utf-8"))


def test_el_workflow_trae_pasa_y_guarda_el_estado():
    pasos = _flujo("cambios-desde-claude.yml")["jobs"]["publicar"]["steps"]
    corridas = "\n".join(p.get("run", "") for p in pasos)
    assert "actions/artifacts?name=estado-avisos-cambios" in corridas
    evaluar = next(p for p in pasos if p.get("id") == "evaluar")["run"]
    assert "--archivo-estado" in evaluar
    deploy = next(p for p in pasos if p.get("name") == "Seguir el deploy")["run"]
    assert "--descripcion" in deploy and "--fecha-status" in deploy and "--archivo-estado" in deploy
    [guardar] = [p for p in pasos if p.get("uses", "").startswith("actions/upload-artifact@")
                 and p["with"]["name"] == "estado-avisos-cambios"]
    assert guardar["if"].startswith("always()")


def test_la_corrida_nocturna_en_verde_vacia_las_pruebas_rojas_de_main():
    flujo = _flujo("data-pipeline.yml")
    assert flujo["permissions"].get("actions") in ("read", "write")
    pasos = flujo["jobs"]["run"]["steps"]
    verde = next(p for p in pasos if "aviso_cambio_claude.py verde" in p.get("run", ""))
    assert verde["if"].startswith("success()") and "refs/heads/main" in verde["if"]
    assert any(p.get("uses", "").startswith("actions/upload-artifact@")
               and p["with"]["name"] == "estado-avisos-cambios" for p in pasos)
