# -*- coding: utf-8 -*-
"""Un indicador suspendido se conserva como ARCHIVO, nunca como componente
vigente (ADR-0259).

ADR-0245 lo sacó del CÁLCULO y `publicar.py` lo saca del snapshot público.
Entre esas dos capas quedaba `output/informe.json`, que se armaba copiando el
caché del colector tal cual: al 25-ago-2026 `judicializacion` decía
`en_indice: true`, `peso_efectivo: 0.03` y `puntaje_itcp: 54.4` —los de la
última corrida en que sí puntuó— y `apoyo_empresario` decía `en_indice: true`.
Ninguno aportaba nada; el artefacto afirmaba que sí.

Lo que hace que esto no vuelva a pasar no es marcar esos dos: es que la marca
la ponga `generar_informe.py` recorriendo `INDICADORES_SUSPENDIDOS`, en el
último paso antes de escribir. `gestion.py` ya lo hacía bien para sus dos casos
y `politica.py` no lo hacía para ninguno — que es el modo de falla de toda
regla que hay que acordarse de repetir en cada colector.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import generar_informe as gi  # noqa: E402
import itcp  # noqa: E402


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def informe():
    """El artefacto crudo armado desde los cachés reales, sin escribir nada."""
    caches = gi.load_caches()
    if not caches:
        pytest.skip("sin cachés de colectores en output/cache/")
    return gi.construir_informe(caches)


def _indicador_como_lo_dejo_el_colector():
    """Réplica de lo que `politica.py` deja hoy en el caché para
    `judicializacion`: marcado como componente vivo, con el peso y el puntaje
    de la última corrida en que efectivamente puntuó."""
    return {
        "valor": 1.57,
        "unidad": "% de sumarios",
        "fuente": "SAIJ",
        "fecha_dato": "2026-08-01",
        "detalle_txt": "114 sumarios sobre 7.273",
        "obtenido_en": "2026-08-25",
        "desactualizado": True,
        "en_indice": True,
        "dimension": "poder_judicial",
        "peso_efectivo": 0.03,
        "puntaje_itcp": 54.4,
        "puntaje_banda": 54.4,
    }


# ── El contrato, sobre un indicador armado a mano ─────────────────────────────

def test_pierde_todo_lo_que_solo_tiene_sentido_si_puntua():
    ind = _indicador_como_lo_dejo_el_colector()
    marcados = gi.marcar_suspendidos("politica", {"judicializacion": ind})

    assert marcados == ["judicializacion"]
    assert ind["en_indice"] is False
    assert "peso_efectivo" not in ind, (
        "un peso efectivo en algo que no pesa se suma, se promedia y se grafica")
    assert not [k for k in ind if k.startswith("puntaje_")], (
        f"quedaron puntajes de un indicador que no puntúa: "
        f"{[k for k in ind if k.startswith('puntaje_')]}")


def test_conserva_el_archivo():
    """«No borrar la historia» es la otra mitad del contrato: el dato, su
    fuente, su fecha y su dimensión de origen se quedan."""
    ind = _indicador_como_lo_dejo_el_colector()
    gi.marcar_suspendidos("politica", {"judicializacion": ind})

    assert ind["valor"] == 1.57
    assert ind["unidad"] == "% de sumarios"
    assert ind["fuente"] == "SAIJ"
    assert ind["fecha_dato"] == "2026-08-01"
    assert ind["detalle_txt"] == "114 sumarios sobre 7.273"
    assert ind["dimension"] == "poder_judicial", "dónde pesaba es parte del archivo"


def test_dice_por_que_y_hasta_cuando():
    """Un indicador que desaparece del score sin decir por qué es
    indistinguible de uno que se cayó (misma regla que ADR-0245)."""
    ind = _indicador_como_lo_dejo_el_colector()
    gi.marcar_suspendidos("politica", {"judicializacion": ind})

    susp = ind["suspendido"]
    assert susp["adr"] == "0255"
    assert susp["desde"] and susp["desde_txt"]
    assert len(susp["por_que"]) > 80
    assert len(susp["condicion_reingreso"]) > 60


def test_no_inventa_un_indicador_que_el_colector_no_publica():
    """`sentimiento_digital` está suspendido en el ITVC y no está en el caché
    de vida cotidiana. El contrato es sobre lo que se publica: no crea filas
    fantasma para poder marcarlas."""
    indicadores = {"ipc_total": {"valor": 1.9}}
    assert gi.marcar_suspendidos("vida_cotidiana", indicadores) == []
    assert set(indicadores) == {"ipc_total"}


def test_la_proxima_suspension_no_toca_este_archivo(monkeypatch):
    """La guarda de fondo: el contrato se aplica recorriendo la tabla del
    índice, no una lista de nombres escrita acá.

    Se suspende un indicador que no existía, sin tocar `generar_informe.py`, y
    tiene que quedar archivado igual."""
    tabla = dict(itcp.INDICADORES_SUSPENDIDOS)
    tabla["indicador_inventado"] = {
        "dimension": "sector_privado",
        "desde": "2027-01",
        "desde_txt": "enero de 2027",
        "adr": "9999",
        "por_que": "motivo de prueba",
        "condicion_reingreso": "condición de prueba",
    }
    monkeypatch.setattr(itcp, "INDICADORES_SUSPENDIDOS", tabla)

    ind = {"valor": 1.0, "en_indice": True, "peso_efectivo": 0.5, "puntaje_itcp": 70.0}
    gi.marcar_suspendidos("politica", {"indicador_inventado": ind})

    assert ind["en_indice"] is False
    assert "peso_efectivo" not in ind and "puntaje_itcp" not in ind
    assert ind["suspendido"]["adr"] == "9999"
    assert ind["dimension"] == "sector_privado"


def test_un_cinturon_sin_tabla_de_suspendidos_no_rompe():
    """`itcm` no declara `INDICADORES_SUSPENDIDOS` y no tiene por qué."""
    assert gi.suspendidos_de("macro") == {}
    assert gi.marcar_suspendidos("macro", {"ipc": {"valor": 1.0}}) == []


# ── El contrato, sobre el artefacto real ──────────────────────────────────────

def test_ningun_suspendido_sale_como_componente_vigente(informe):
    """El caso que originó el ADR, mirado de punta a punta: se arma el
    artefacto desde los cachés que hoy dejan los colectores —uno de los cuales
    NO marca nada— y ningún suspendido puede salir con estado activo."""
    fallas = []
    for cinturon, data in informe["cinturones"].items():
        for nombre in gi.suspendidos_de(cinturon):
            ind = data["indicadores"].get(nombre)
            if ind is None:
                continue
            if ind.get("en_indice") is not False:
                fallas.append(f"{cinturon}/{nombre}: en_indice={ind.get('en_indice')!r}")
            sobrantes = [k for k in ind if gi._es_campo_de_componente_vigente(k)]
            if sobrantes:
                fallas.append(f"{cinturon}/{nombre}: conserva {sobrantes}")
            if not ind.get("suspendido"):
                fallas.append(f"{cinturon}/{nombre}: sin bloque `suspendido`")
    assert not fallas, "\n".join(fallas)


def test_los_cuatro_suspendidos_de_agosto_estan_cubiertos(informe):
    """Anclaje explícito: los dos que la reauditoría marcó incompletos y los
    dos que ya estaban bien, para que el test de arriba no pase por vacío si
    alguien vacía las tablas."""
    esperados = {
        ("politica", "apoyo_empresario"),
        ("politica", "judicializacion"),
        ("gestion", "reestructuracion_organismos"),
        ("gestion", "masa_salarial"),
    }
    for cinturon, nombre in esperados:
        ind = informe["cinturones"][cinturon]["indicadores"].get(nombre)
        assert ind is not None, f"{cinturon}/{nombre} desapareció del artefacto crudo"
        assert ind["en_indice"] is False
        assert ind["suspendido"]["desde"]
        assert ind.get("valor") is not None, "el archivo conserva el último valor"


def test_ningun_suspendido_aparece_puntuando_dentro_del_indice(informe):
    for cinturon, data in informe["cinturones"].items():
        sigla = next((k for k in data if k.startswith(("itc", "itv"))), None)
        if sigla is None:
            continue
        dentro = {i for d in data[sigla]["dimensiones"].values()
                  for i in d["indicadores"]}
        assert not (dentro & set(gi.suspendidos_de(cinturon))), (
            f"{cinturon}: {dentro & set(gi.suspendidos_de(cinturon))} puntúa estando suspendido")


def test_la_guarda_grita_si_uno_se_cuela_al_indice():
    """La otra mitad: hoy `calcular_itc*()` filtra, así que esto no puede
    pasar. El día que un índice nuevo se olvide de filtrar, el artefacto
    saldría con el suspendido puntuando y nada lo diría."""
    resultado = {"dimensiones": {"poder_judicial": {"indicadores": {
        "judicializacion": {"peso_efectivo": 0.03, "puntaje_aplicado": 54.4}}}}}
    with pytest.raises(ValueError, match="judicializacion"):
        gi.verificar_que_ninguno_puntua("politica", resultado)

    # y no molesta cuando el índice está sano
    gi.verificar_que_ninguno_puntua("politica", {"dimensiones": {}})
    gi.verificar_que_ninguno_puntua("politica", None)


def test_un_suspendido_desactualizado_no_dispara_el_flag_diario(informe):
    """`judicializacion` tiene `desactualizado: true` en el caché —SAIJ bloquea
    a los runners casi todas las noches (ADR-0175)— y está suspendido desde
    ADR-0255. Avisar por la frescura de un dato que no alimenta nada es ruido
    diario sobre algo que ya nadie usa."""
    for flag in informe["flags"]:
        if not flag.startswith("desactualizado:"):
            continue
        _, cinturon, listado = flag.split(":", 2)
        colados = set(listado.split(",")) & set(gi.suspendidos_de(cinturon))
        assert not colados, f"{flag} avisa por indicadores suspendidos: {colados}"


def test_el_flag_diario_ignora_al_suspendido_pero_no_al_de_al_lado():
    """Lo mismo, forzado: hoy `judicializacion` cae dentro de su ventana
    declarada (ADR-0210) y no llegaría al flag por ese otro camino, así que el
    test de arriba pasaría igual sin el filtro. Acá el caché se arma vencido a
    propósito, y con un indicador vigente igual de vencido al lado para que la
    guarda tenga que distinguir en vez de silenciar todo."""
    viejo = "2020-01-01T00:00:00"
    caches = {"politica": {"score": 5.0, "indicadores": {
        "judicializacion":  {"valor": 1.57, "desactualizado": True, "obtenido_en": viejo},
        "cobertura_judicial": {"valor": 69.6, "desactualizado": True, "obtenido_en": viejo},
    }}}
    flags = [f for f in gi.construir_informe(caches)["flags"]
             if f.startswith("desactualizado:")]
    assert flags == ["desactualizado:politica:cobertura_judicial"], flags


# ── El .md, que es artefacto de ingesta ───────────────────────────────────────

def test_el_md_no_los_mezcla_con_los_vigentes(informe, tmp_path, monkeypatch):
    """Compartir tabla con los vigentes es afirmar que son el mismo tipo de
    cosa. Lo lee quien no tiene el resto del contexto a mano."""
    monkeypatch.setattr(gi, "OUTPUT_DIR", tmp_path)
    gi.escribir_md(informe)
    texto = (tmp_path / "informe.md").read_text(encoding="utf-8")

    assert "NO integran el índice" in texto
    assert "**Suspendidos" in texto, "no se emitió ninguna tabla de suspendidos"

    # Cada fila de tabla, ubicada en su tramo: el rótulo de suspendidos abre el
    # tramo de archivo y el título del cinturón siguiente lo cierra.
    todos_suspendidos = {n for c in informe["cinturones"] for n in gi.suspendidos_de(c)}
    en_archivo = False
    vistos = set()
    for linea in texto.splitlines():
        if linea.startswith("### "):
            en_archivo = False
        elif linea.startswith("**Suspendidos"):
            en_archivo = True
        elif linea.startswith("| ") and not linea.startswith("|---"):
            nombre = linea.split("|")[1].strip()
            if nombre in todos_suspendidos:
                vistos.add(nombre)
                assert en_archivo, (
                    f"{nombre} está suspendido y sale en la tabla de vigentes")
            elif nombre not in ("Indicador",):
                assert not en_archivo, (
                    f"{nombre} no está suspendido y sale en la tabla de archivo")

    assert {"judicializacion", "apoyo_empresario", "reestructuracion_organismos"} <= vistos, (
        "el archivo tiene que seguir figurando en el .md, no borrarse")


def test_el_md_dice_desde_cuando_y_por_que(informe, tmp_path, monkeypatch):
    monkeypatch.setattr(gi, "OUTPUT_DIR", tmp_path)
    gi.escribir_md(informe)
    texto = (tmp_path / "informe.md").read_text(encoding="utf-8")
    assert "ADR-0255" in texto and "ADR-0246" in texto and "ADR-0247" in texto
    assert "agosto de 2026" in texto


def test_el_md_no_deja_el_motivo_partido_en_lineas(informe, tmp_path, monkeypatch):
    """Una celda de tabla Markdown no sobrevive ni a un salto de línea ni a un
    `|`, y el motivo es prosa libre escrita en el ADR de turno.

    Hoy ningún motivo tiene ninguna de las dos cosas, así que mirar los reales
    no prueba nada: se inyecta uno que las tiene. Sin esto la guarda sería
    decorativa — se verificó rompiéndola y pasaba igual."""
    envenenado = copy.deepcopy(informe)
    ind = envenenado["cinturones"]["politica"]["indicadores"]["judicializacion"]
    ind["suspendido"]["por_que"] = ("un motivo escrito\n    en varias líneas, "
                                    "con un | adentro")

    monkeypatch.setattr(gi, "OUTPUT_DIR", tmp_path)
    gi.escribir_md(envenenado)
    filas = [l for l in (tmp_path / "informe.md").read_text(encoding="utf-8").splitlines()
             if l.startswith("| judicializacion |")]
    assert len(filas) == 1, f"la fila se partió en {len(filas)}: {filas}"
    assert filas[0].count("|") - filas[0].count("\\|") == 7, filas[0]
    assert "en varias líneas" in filas[0]


def test_el_md_deja_los_motivos_reales_en_una_sola_fila(informe, tmp_path, monkeypatch):
    monkeypatch.setattr(gi, "OUTPUT_DIR", tmp_path)
    gi.escribir_md(informe)
    for linea in (tmp_path / "informe.md").read_text(encoding="utf-8").splitlines():
        if linea.startswith(("| judicializacion |", "| apoyo_empresario |")):
            assert linea.rstrip().endswith("|") and linea.count("|") == 7, linea


def test_el_json_sigue_siendo_serializable(informe, tmp_path, monkeypatch):
    monkeypatch.setattr(gi, "OUTPUT_DIR", tmp_path)
    gi.escribir_json(informe)
    d = json.loads((tmp_path / "informe.json").read_text(encoding="utf-8"))
    assert d["cinturones"]["politica"]["indicadores"]["judicializacion"]["en_indice"] is False
