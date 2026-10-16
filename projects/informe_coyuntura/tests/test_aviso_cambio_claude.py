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


def test_reemplazar_el_hilo_no_dice_que_main_volvio_a_verde(slack, tmp_path):
    cambio(tmp_path, 60, [], [SEMAFORO])
    cambio(tmp_path, 61, ["web/src/pages/x.astro"], [SEMAFORO])
    cambio(tmp_path, 62, ["web/src/pages/x.astro"], [SEMAFORO, PARRAFO])
    cambio(tmp_path, 63, ["web/src/pages/x.astro"], [SEMAFORO, PARRAFO])
    textos = [c["text"] for c in slack.llamadas]
    assert not any(t.startswith("✅") or "Main vuelve a verde" in t for t in textos)
    [reemplazo] = [t for t in textos if "se reemplaza por un conjunto distinto" in t]
    assert "test_el_parrafo_original_sigue_publicado" in reemplazo     # la lista nueva


def test_un_cierre_que_slack_no_confirma_se_reintenta(slack, tmp_path, monkeypatch):
    cambio(tmp_path, 60, [], [SEMAFORO])
    cambio(tmp_path, 61, ["web/src/pages/x.astro"], [SEMAFORO])
    ts = estado(tmp_path)["main_rojas"]["ts"]
    monkeypatch.setattr(av, "_slack", lambda metodo, **d: {"ok": False, "error": "ratelimited"})
    cambio(tmp_path, 62, ["web/src/pages/x.astro"], [])
    assert estado(tmp_path)["cierres_pendientes"][0]["ts"] == ts
    monkeypatch.setattr(av, "_slack", slack)
    assert av.main(["verde", "--archivo-estado", str(tmp_path / "estado" / "estado.json")], ahora=AHORA) == 0
    assert "cierres_pendientes" not in estado(tmp_path)
    assert slack.ediciones()[-1]["ts"] == ts and slack.ediciones()[-1]["text"].startswith("✅")


def test_la_corrida_nocturna_no_borra_fallas_de_tipos_ni_de_build(slack, tmp_path):
    # De noche sólo corre pytest: lo que dijo tsc no se puede dar por arreglado.
    tsc = "web/src/lib/x.ts(3,5): error TS2322: Type 'string' is not assignable"
    for pr in (60, 61):
        d = tmp_path / f"pr{pr}"
        d.mkdir()
        (d / "tsc.log").write_text(tsc + "\n", encoding="utf-8")
        cambio(tmp_path, pr, ["web/src/pages/x.astro"], [SEMAFORO])
    assert len(estado(tmp_path)["main_rojas"]["lista"]) == 2
    assert av.main(["verde", "--archivo-estado", str(tmp_path / "estado" / "estado.json")], ahora=AHORA) == 0
    assert estado(tmp_path)["rojas"] == [f"tsc: {tsc}"]
    assert estado(tmp_path)["main_rojas"]["lista"] == [f"tsc: {tsc}"]


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


# ── Estado del pedido en el PR (contrato que lee el conector) ──────────────
#
# Un comentario por PR que empieza con `<!-- estado-pedido -->` y lleva un
# bloque ```json. Se crea una vez y se edita: nunca se acumulan.

import re as _re  # noqa: E402

AHORA_ISO = "2026-10-16T15:00:00+00:00"


def _json_del(cuerpo):
    m = _re.search(r"```json\n(.*?)\n```", cuerpo, _re.S)
    assert m, cuerpo
    return json.loads(m.group(1))


def test_el_comentario_de_estado_cumple_el_contrato():
    e = av.nuevo_estado_pedido(AHORA)
    cuerpo = av.comentario_estado(e)
    assert cuerpo.splitlines()[0] == "<!-- estado-pedido -->"
    # Una línea legible en castellano antes del JSON.
    legible = cuerpo.splitlines()[1]
    assert legible and not legible.startswith("```")
    d = _json_del(cuerpo)
    assert set(d) >= {"merge", "deploy_diario", "corrida", "actualizado"}
    assert d["merge"] == "pendiente" and d["deploy_diario"] == "pendiente"
    assert d["corrida"] == {"estado": "no_aplica", "url": None, "snapshot_publicado": None, "generated_at": None}
    assert d["actualizado"].startswith("2026-10-08T19:00")


def test_el_estado_se_lee_de_vuelta_del_comentario():
    e = av.actualizar_estado_pedido(av.nuevo_estado_pedido(AHORA), AHORA, merge="ok",
                                    corrida={"estado": "en_curso", "url": "https://run/1"})
    assert av.leer_estado_pedido(av.comentario_estado(e)) == e
    # Un comentario cualquiera no es el de estado.
    assert av.leer_estado_pedido("✅ Publicado: ```json\n{}\n```") is None


@pytest.mark.parametrize("campo, valor", [
    ("merge", "bloqueado"), ("deploy_diario", "roto"), ("corrida", {"estado": "terminada"}),
])
def test_valores_fuera_del_contrato_no_se_escriben(campo, valor):
    with pytest.raises(ValueError):
        av.actualizar_estado_pedido(av.nuevo_estado_pedido(AHORA), AHORA, **{campo: valor})


def test_actualizar_conserva_lo_que_no_se_toca_y_el_motivo():
    e = av.actualizar_estado_pedido(av.nuevo_estado_pedido(AHORA), AHORA, merge="ok", deploy_diario="ok")
    e = av.actualizar_estado_pedido(e, AHORA, corrida={"estado": "ok", "snapshot_publicado": True,
                                                       "generated_at": "2026-10-16T14:00:00"})
    assert e["merge"] == "ok" and e["deploy_diario"] == "ok"
    assert e["corrida"]["snapshot_publicado"] is True and e["corrida"]["url"] is None
    f = av.actualizar_estado_pedido(av.nuevo_estado_pedido(AHORA), AHORA, merge="fallo",
                                    motivo="bloqueado: toca .github/workflows/x.yml")
    assert f["motivo"].startswith("bloqueado") and "no se publicó" in av.linea_estado(f)


@pytest.mark.parametrize("cambios, dice", [
    (dict(merge="pendiente"), "en curso"),
    (dict(merge="fallo", motivo="GitHub no dejó mergear"), "no se publicó"),
    (dict(merge="ok", deploy_diario="ok"), "seguimiento diario"),
    (dict(merge="ok", deploy_diario="rate_limited"), "tope"),
    (dict(merge="ok", deploy_diario="ok", corrida={"estado": "no_despachada"}), "no se pudo lanzar"),
    (dict(merge="ok", deploy_diario="ok", corrida={"estado": "timeout"}), "dejó de seguir"),
    (dict(merge="ok", deploy_diario="ok", corrida={"estado": "fallo", "snapshot_publicado": True}),
     "después de publicar"),
    (dict(merge="ok", deploy_diario="ok", corrida={"estado": "fallo", "snapshot_publicado": False}),
     "no publicó datos"),
])
def test_la_linea_legible_dice_lo_que_pasa(cambios, dice):
    e = av.actualizar_estado_pedido(av.nuevo_estado_pedido(AHORA), AHORA, **cambios)
    assert dice in av.linea_estado(e)


class GitHubFalso:
    """Los comentarios del PR, en memoria."""

    def __init__(self, comentarios=()):
        self.comentarios = [dict(c) for c in comentarios]
        self.llamadas = []

    def __call__(self, metodo, ruta, datos=None):
        self.llamadas.append((metodo, ruta, datos))
        if metodo == "GET":
            pagina = int(_re.search(r"[?&]page=(\d+)", ruta).group(1))
            return self.comentarios if pagina == 1 else []
        if metodo == "POST":
            c = {"id": 900 + len(self.comentarios), "user": {"login": "github-actions[bot]"}, **datos}
            self.comentarios.append(c)
            return c
        if metodo == "PATCH":
            cid = int(ruta.rsplit("/", 1)[1])
            c = next(c for c in self.comentarios if c["id"] == cid)
            c.update(datos)
            return c
        raise AssertionError(metodo)


def _estado_cli(gh, monkeypatch, *args):
    monkeypatch.setattr(av, "_github", gh)
    assert av.main(["estado", "--pr", "7", "--repo", "o/r", *args], ahora=AHORA) == 0


def test_el_comentario_se_crea_una_vez_y_despues_se_edita(monkeypatch):
    gh = GitHubFalso([{"id": 1, "user": {"login": "luis"}, "body": "<!-- estado-pedido -->\nfalso"}])
    _estado_cli(gh, monkeypatch, "--merge", "pendiente")
    _estado_cli(gh, monkeypatch, "--merge", "ok", "--deploy", "ok")
    _estado_cli(gh, monkeypatch, "--corrida-estado", "en_curso", "--corrida-url", "https://run/5")
    nuestros = [c for c in gh.comentarios if c["user"]["login"] == "github-actions[bot]"]
    assert len(nuestros) == 1                                    # se edita, no se acumula
    assert [m for m, _, _ in gh.llamadas if m != "GET"] == ["POST", "PATCH", "PATCH"]
    d = _json_del(nuestros[0]["body"])
    assert d["merge"] == "ok" and d["deploy_diario"] == "ok"
    assert d["corrida"] == {"estado": "en_curso", "url": "https://run/5", "snapshot_publicado": None,
                            "generated_at": None}
    # El comentario de otra persona que imita la marca no se toca.
    assert gh.comentarios[0]["body"] == "<!-- estado-pedido -->\nfalso"


def test_si_pendiente_no_pisa_un_merge_que_ya_salio(monkeypatch):
    gh = GitHubFalso()
    _estado_cli(gh, monkeypatch, "--merge", "ok")
    _estado_cli(gh, monkeypatch, "--merge-si-pendiente", "fallo", "--motivo", "se canceló")
    d = _json_del(gh.comentarios[0]["body"])
    assert d["merge"] == "ok" and d.get("motivo") is None
    gh2 = GitHubFalso()
    _estado_cli(gh2, monkeypatch, "--merge", "pendiente")
    _estado_cli(gh2, monkeypatch, "--merge-si-pendiente", "fallo", "--motivo", "se canceló")
    assert _json_del(gh2.comentarios[0]["body"])["merge"] == "fallo"


def test_sin_token_de_github_el_estado_no_rompe_el_job(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert av.main(["estado", "--pr", "7", "--repo", "o/r", "--merge", "ok"], ahora=AHORA) == 0


# ── Estado del deploy del seguimiento diario ───────────────────────────────

@pytest.mark.parametrize("estado, descripcion, http, sale", [
    ("success", "Deployment has completed", "200", "ok"),
    ("success", "", "500", "fallo"),
    ("failure", "Deployment failed", "200", "fallo"),
    ("failure", "Deployment rate limited — retry in 24 hours", "200", "rate_limited"),
    ("pending", "", "200", "pendiente"),
    ("", "", "200", "desconocido"),
])
def test_estado_del_deploy_diario(estado, descripcion, http, sale):
    assert av.estado_deploy(estado, descripcion, http) == sale


def test_el_workflow_verifica_el_seguimiento_diario_no_el_mensual():
    pasos = _flujo("cambios-desde-claude.yml")["jobs"]["publicar"]["steps"]
    deploy = next(p for p in pasos if p.get("name") == "Seguir el deploy")["run"]
    assert "cigob-seguimiento-a941210feb.vercel.app" in deploy
    assert "informe.cigob.org" not in deploy
    # Cada commit tiene DOS status de Vercel (mensual y diario): el filtro
    # tiene que elegir el del diario, no el primero que aparezca.
    filtro = next(l for l in deploy.splitlines() if l.strip().startswith("vercel="))
    assert 'test("cigob-seguimiento")' in filtro and "and" in filtro


def test_el_modo_estado_calcula_el_deploy_desde_el_status(monkeypatch):
    gh = GitHubFalso()
    _estado_cli(gh, monkeypatch, "--merge", "ok", "--estado", "failure",
                "--descripcion", "Deployment rate limited — retry in 24 hours", "--http", "200")
    assert _json_del(gh.comentarios[0]["body"])["deploy_diario"] == "rate_limited"
    _estado_cli(gh, monkeypatch, "--estado", "success", "--http", "200")
    assert _json_del(gh.comentarios[0]["body"])["deploy_diario"] == "ok"


# ── Qué dejó la corrida de datos ───────────────────────────────────────────

def _jobs(conclusion_commit):
    pasos = [{"name": "Correr colectores", "conclusion": "success"}]
    if conclusion_commit is not None:
        pasos.append({"name": "Commitear snapshot + caches a main", "conclusion": conclusion_commit})
    return {"jobs": [{"name": "run", "steps": pasos}]}


@pytest.mark.parametrize("jobs, generated, creada, sale", [
    (_jobs("success"), "2026-10-16T15:20:00-03:00", "2026-10-16T18:00:00Z", True),
    (_jobs("success"), "2026-10-15T00:20:00-03:00", "2026-10-16T18:00:00Z", None),
    (_jobs("skipped"), "", "2026-10-16T18:00:00Z", False),
    (_jobs("failure"), "", "2026-10-16T18:00:00Z", False),
    (_jobs(None), "", "2026-10-16T18:00:00Z", False),
    ({}, "", "", None),
    ({"jobs": []}, "", "", None),
])
def test_si_la_corrida_publico_snapshot(jobs, generated, creada, sale):
    assert av.snapshot_publicado(jobs, generated, creada) is sale


def test_texto_corrida_distingue_los_tres_desenlaces():
    sin = av.texto_corrida(3, "u", "t", "q", "failure", "https://run", snapshot=False)
    despues = av.texto_corrida(3, "u", "t", "q", "failure", "https://run", snapshot=True)
    nose = av.texto_corrida(3, "u", "t", "q", "failure", "https://run", snapshot=None)
    assert sin.startswith("🔴") and "no produjo snapshot" in sin
    assert despues.startswith("🟡") and "publicó los datos pero falló después" in despues
    assert nose.startswith("🔴") and "resultado desconocido" in nose
    assert len({sin, despues, nose}) == 3
    # Control positivo: una corrida que salió bien sigue sin avisar.
    assert av.texto_corrida(3, "u", "t", "q", "success", "https://run", snapshot=True) is None
    # Y la que no se pudo lanzar lo dice con esas palabras.
    assert "no se pudo lanzar" in av.texto_corrida(3, "u", "t", "q", "no se pudo lanzar", "https://run")


def test_el_modo_corrida_pasa_el_snapshot_al_texto(slack, tmp_path):
    cambio(tmp_path, 70, ["scripts/itcm.py"], [], modo="corrida",
           extra=["--conclusion", "failure", "--corrida-url", "https://run/9", "--snapshot", "si"])
    [post] = slack.posts()
    assert "publicó los datos pero falló después" in post["text"]


# ── El workflow: secretos, carreras y corrida ──────────────────────────────

def test_las_fichas_se_generan_sin_secretos_y_se_commitean_sin_ejecutar_codigo():
    jobs = _flujo("cambios-desde-claude.yml")["jobs"]
    publicar = "\n".join(p.get("run", "") for p in jobs["publicar"]["steps"])
    assert "generar.py" not in publicar
    gen = next(n for n, j in jobs.items() if any("fichas/generar.py" in p.get("run", "") for p in j["steps"])
               and n != "validar")
    j = jobs[gen]
    assert j["permissions"] == {"contents": "read"}
    assert "secrets." not in json.dumps(j) and "env" not in j
    commit = next(n for n, x in jobs.items() if gen in (x.get("needs") or []))
    c = jobs[commit]
    texto = json.dumps(c)
    assert c["permissions"].get("contents") == "write"
    assert "python" not in texto and "npm" not in texto and "generar.py" not in texto
    assert "output/fichas" in texto


def test_ningun_job_con_secretos_ejecuta_codigo_del_repo():
    """Un job con secretos sólo corre el script de avisos copiado de main
    antes del merge ($RUNNER_TEMP/aviso, o el artifact `aviso/`); nunca un
    `scripts/...` del checkout, ni instala dependencias del repo."""
    jobs = _flujo("cambios-desde-claude.yml")["jobs"]
    con_secretos = [n for n, j in jobs.items() if "secrets." in json.dumps(j)]
    assert {"publicar", "seguir-corrida"} <= set(con_secretos)
    for nombre in con_secretos:
        for p in jobs[nombre]["steps"]:
            run = p.get("run", "")
            assert not _re.search(r"python3?\s+[\"']?(\./)?(projects/|scripts/|-m\b)", run), (nombre, run)
            assert "pip install" not in run and "npm " not in run and "npx " not in run, nombre


def test_publicar_va_en_un_grupo_global_sin_cancelar():
    j = _flujo("cambios-desde-claude.yml")["jobs"]["publicar"]
    assert "github.event" not in j["concurrency"]["group"]
    assert j["concurrency"]["cancel-in-progress"] is False


def test_la_corrida_se_lanza_y_se_busca_por_el_numero_del_pedido():
    jobs = _flujo("cambios-desde-claude.yml")["jobs"]
    corridas = "\n".join(p.get("run", "") for j in jobs.values() for p in j["steps"])
    assert "-f pedido=" in corridas and "Corrida de datos del pedido $PR" in corridas
    assert "displayTitle" in corridas and "createdAt >=" not in corridas
    dp = _flujo("data-pipeline.yml")
    on = dp.get("on", dp.get(True))
    assert "pedido" in on["workflow_dispatch"]["inputs"]
    assert "inputs.pedido" in dp["run-name"] and "Corrida de datos del pedido {0}" in dp["run-name"]
    seguir = jobs["seguir-corrida"]
    finales = [p for p in seguir["steps"] if str(p.get("if", "")).startswith("always()")]
    assert finales and "estado" in finales[-1]["run"]
    assert any("timeout" in p.get("run", "") for p in seguir["steps"])
