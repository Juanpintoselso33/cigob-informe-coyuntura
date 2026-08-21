# -*- coding: utf-8 -*-
"""La canasta de búsquedas del sentimiento digital (ADR-0222).

Lo que se cuida acá no es que el número esté bien —eso no se puede testear sin
Google— sino las cinco cosas que pueden romperse en silencio:

1. **El tope de cinco términos por consulta.** Es el límite de la fuente. Si
   alguien vuelve a armar un payload con la canasta entera, `build_payload`
   falla, el colector se lo come en su `except` y publica caché para siempre:
   la corrida termina bien y el dato no se mueve nunca más.

2. **El empalme de escalas.** Cada término se rebasa contra su propio 4T-2023
   DENTRO de su consulta, y de ahí sale que el escalar de la fuente se cancele.
   Es la propiedad que reemplaza al término ancla, y no se nota rota mirando el
   resultado: dos series con escalas distintas promediadas dan un número
   perfectamente creíble.

3. **La composición constante.** Una canasta que emite un mes con los términos
   que haya se mueve por composición y no por búsquedas.

4. **El formato del archivo.** El store anterior a ADR-0222 tiene la MISMA forma
   y otra unidad —promedio crudo 0-100 contra índice base 100—. Leído como si
   fuera nuevo publica una escala por otra sin que falle nada, que es el modo de
   falla más caro de este proyecto.

5. **Que una fuente muerta se note.** La card salía de una consulta en vivo y su
   fracaso la dejaba en None, que era la señal. Ahora sale del store: si además
   se fechara con la corrida, Trends podría estar caído un mes y la card se
   vería fresca todas las noches.

Todo corre contra el módulo del colector, sin red: las funciones de cálculo
están separadas de la descarga justamente para poder ejercitarlas así.

Las 26 se probaron rompiéndolas a propósito. Dos pasaban por el motivo
equivocado y hubo que rehacerlas —la del store viejo se cumplía por una clave
ausente y no por la marca de formato; la de la ficha se conformaba con que los
términos aparecieran en la lista de cambios—, así que el ejercicio no es
ceremonia.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Hay DOS `config.py` en el repo —el de la raíz y el del cinturón— y el
# colector importa el segundo por nombre pelado. Corriendo la suite entera, el
# de la raíz ya está en `sys.modules` cuando llega este archivo y `import
# trends` levantaría constantes de otro módulo. Se carga cada uno por ruta y se
# presta el nombre sólo mientras se ejecuta el colector.
_CFG = _cargar("vida_config", RAIZ / "scripts" / "vida_cotidiana" / "config.py")
_previo = sys.modules.get("config")
sys.modules["config"] = _CFG
try:
    t = _cargar("trends_vida",
                RAIZ / "scripts" / "vida_cotidiana" / "collectors" / "trends.py")
finally:
    if _previo is not None:
        sys.modules["config"] = _previo
    else:
        del sys.modules["config"]

TRENDS_KEYWORDS = _CFG.TRENDS_KEYWORDS
TRENDS_GEO = _CFG.TRENDS_GEO
TRENDS_BASE_MESES = _CFG.TRENDS_BASE_MESES
TRENDS_MIN_MESES = _CFG.TRENDS_MIN_MESES
TRENDS_VENTANA_DESDE = _CFG.TRENDS_VENTANA_DESDE

# Tope duro de la fuente: Google Trends no acepta más de cinco términos por
# consulta. No es una preferencia nuestra.
MAX_TERMINOS_POR_CONSULTA = 5


def _mensual(valores, desde="2021-01"):
    """{YYYY-MM: valor} correlativo desde `desde`, para no escribir 68 meses."""
    ano, mes = int(desde[:4]), int(desde[5:])
    salida = {}
    for v in valores:
        salida[f"{ano:04d}-{mes:02d}"] = v
        mes += 1
        if mes == 13:
            ano, mes = ano + 1, 1
    return salida


def _serie_larga(escala=1.0, n=68):
    """Serie sana: arranca en 2021-01, pasa por el 4T-2023 y varía mes a mes."""
    return _mensual([round(escala * (50 + (i % 17)), 4) for i in range(n)])


def _store(terminos=None, esquema=None):
    ts = terminos or {kw: _serie_larga(escala=1 + i)
                      for i, kw in enumerate(TRENDS_KEYWORDS)}
    return {"_meta": {"esquema": esquema if esquema is not None else t.SENTIMIENTO_ESQUEMA},
            "terminos": {kw: {"actualizado": "2026-08-21", "mensual": m} for kw, m in ts.items()}}


# ── 1 · La canasta y el tope de la fuente ───────────────────────────────────
def test_la_canasta_son_seis_terminos_sin_repetidos():
    assert len(TRENDS_KEYWORDS) == 6, "ADR-0222 fija seis términos con peso igual"
    assert len(set(TRENDS_KEYWORDS)) == len(TRENDS_KEYWORDS), "hay un término repetido"
    for pedido in ("dolar", "empleo", "corrupcion"):
        assert pedido in TRENDS_KEYWORDS, f"falta «{pedido}» (ADR-0222)"
    assert "trabajo" not in TRENDS_KEYWORDS, (
        "«trabajo» salió en ADR-0222: sus búsquedas asociadas son derecho "
        "laboral, un plan social, el feriado y la tarea escolar")


def test_ninguna_consulta_supera_el_tope_de_cinco_terminos(monkeypatch):
    """La guarda real: que el colector pida UN término por vez.

    Se intercepta `build_payload` y se mira con cuántos términos lo llaman. Con
    la canasta de seis en un solo payload, esto es lo que falla — y en
    producción no fallaría: lo taparía el `except` del colector.
    """
    pedidos = []

    class _PTFalso:
        def build_payload(self, kw_list, **kw):
            pedidos.append(list(kw_list))
            raise RuntimeError("corta acá: sólo interesa cómo se pidió")

        def interest_over_time(self):
            raise AssertionError("no debería llegar")

    monkeypatch.setattr(t, "_patch_urllib3", lambda: None)
    monkeypatch.setitem(sys.modules, "pytrends.request",
                        type(sys)("pytrends.request"))
    sys.modules["pytrends.request"].TrendReq = lambda **kw: _PTFalso()

    t.fetch_sentimiento_store(Path("/tmp/no-existe-sentimiento-test.json"))

    assert pedidos, "el colector no llegó a consultar nada"
    assert len(pedidos) == len(TRENDS_KEYWORDS), (
        "se esperaba una consulta por término y hubo "
        f"{len(pedidos)} para {len(TRENDS_KEYWORDS)} términos")
    for kws in pedidos:
        assert len(kws) <= MAX_TERMINOS_POR_CONSULTA, (
            f"payload de {len(kws)} términos: Google Trends acepta "
            f"{MAX_TERMINOS_POR_CONSULTA} y devuelve error con más")


def test_la_ventana_y_la_base_son_las_declaradas():
    assert TRENDS_VENTANA_DESDE == "2021-01-01"
    assert TRENDS_BASE_MESES == ("2023-10", "2023-11", "2023-12"), (
        "la base es el 4T-2023, igual que el resto del ITCIS")
    assert TRENDS_MIN_MESES >= 36
    assert TRENDS_GEO == "AR"


# ── 2 · El empalme: el rebase por término cancela la escala de la consulta ──
def test_el_rebase_por_termino_es_invariante_al_escalar_de_la_consulta():
    """La propiedad que reemplaza al término ancla.

    Trends devuelve `c · real(t)` con `c` propio de cada consulta. Si el rebase
    está bien hecho, multiplicar la serie entera por cualquier `c` no cambia el
    índice. Verificado empíricamente el 20-ago-2026 contra el mismo término en
    payloads distintos (CV del cociente 0,0% en `trabajo` y `dolar`).
    """
    base = _serie_larga()
    referencia = t.indice_de_termino(base)
    assert referencia, "la serie de prueba tendría que dar índice"
    for c in (0.013, 0.5, 3.7, 41.0):
        escalada = {m: v * c for m, v in base.items()}
        assert t.indice_de_termino(escalada) == referencia, (
            f"el índice cambió al escalar la consulta por {c}: el rebase no "
            "está cancelando la normalización de Trends")


def test_el_indice_del_termino_vale_100_en_la_base():
    idx = t.indice_de_termino(_serie_larga())
    promedio = sum(idx[m] for m in TRENDS_BASE_MESES) / len(TRENDS_BASE_MESES)
    assert round(promedio, 1) == 100.0


def test_un_termino_sin_los_tres_meses_de_la_base_no_da_indice():
    incompleta = {m: v for m, v in _serie_larga().items() if m != "2023-11"}
    assert t.indice_de_termino(incompleta) == {}, (
        "sin la base no hay contra qué comparar: devolver algo igual sería "
        "inventar una escala")


# ── 3 · La canasta: peso igual, composición constante, base alcanzada ───────
def test_la_canasta_es_el_promedio_simple_de_los_indices():
    store = _store()
    canasta = t.compuesto_sentimiento(store)
    assert canasta, "la canasta salió vacía con seis términos sanos"
    mes = "2026-01"
    esperado = sum(t.indice_de_termino(store["terminos"][kw]["mensual"])[mes]
                   for kw in TRENDS_KEYWORDS) / len(TRENDS_KEYWORDS)
    assert canasta[mes] == round(esperado, 1)


def test_los_seis_terminos_pesan_lo_mismo():
    """Un término que se mueve solo tiene que mover la canasta 1/6 de eso.

    Es la diferencia con el promedio crudo de antes, donde el peso lo fijaba el
    volumen de búsqueda y `trabajo` se llevaba el 53%.
    """
    store = _store()
    antes = t.compuesto_sentimiento(store)
    for kw in TRENDS_KEYWORDS:
        movido = json.loads(json.dumps(store))
        # duplicar el término duplica su índice: +100 puntos de ese índice
        movido["terminos"][kw]["mensual"]["2026-01"] *= 2
        idx = t.indice_de_termino(store["terminos"][kw]["mensual"])["2026-01"]
        delta = t.compuesto_sentimiento(movido)["2026-01"] - antes["2026-01"]
        assert abs(delta - idx / len(TRENDS_KEYWORDS)) < 0.11, (
            f"«{kw}» movió la canasta {delta:.1f} y le tocaba "
            f"{idx / len(TRENDS_KEYWORDS):.1f}: el peso no es 1/6")


def test_la_canasta_solo_emite_meses_con_los_seis_terminos():
    store = _store()
    del store["terminos"][TRENDS_KEYWORDS[0]]["mensual"]["2026-01"]
    canasta = t.compuesto_sentimiento(store)
    assert "2026-01" not in canasta, (
        "un mes calculado con los términos que haya cambia de composición: el "
        "salto sería de composición y no de búsquedas")
    assert "2025-12" in canasta, "los meses completos tienen que seguir estando"


def test_sin_uno_de_los_terminos_no_hay_canasta():
    store = _store()
    del store["terminos"][TRENDS_KEYWORDS[-1]]
    assert t.compuesto_sentimiento(store) == {}


def test_la_canasta_llega_hasta_la_base_4t_2023():
    """Sin el 4T-2023 el componente no se puede rebasear y el ITCIS lo pierde."""
    canasta = t.compuesto_sentimiento(_store())
    for mes in TRENDS_BASE_MESES:
        assert mes in canasta, f"la canasta no llega a {mes}"
    assert min(canasta) <= "2023-10"


# ── 4 · El formato del archivo ──────────────────────────────────────────────
def test_un_store_del_formato_viejo_no_se_publica_como_indice(tmp_path, monkeypatch):
    """El de antes de ADR-0222 guardaba interés crudo 0-100 en `mensual`.

    Misma forma, otra unidad. Sin la marca de esquema, 26,2 puntos de interés se
    publicarían como un índice de 26,2 contra base 100 y el componente saldría
    invertido en 382 en vez de 148: creíble, publicable y falso. Con la fuente
    caída —que es cuando el store manda— no tiene que salir nada.
    """
    destino = tmp_path / "sentimiento.json"
    viejo = {"_meta": {"fuente": "Google Trends (canasta mensual, ventana fija 2021→)",
                       "actualizado": "2026-08-18"},
             "mensual": _serie_larga()}
    crudo = json.dumps(viejo, ensure_ascii=False)
    destino.write_text(crudo, encoding="utf-8")

    monkeypatch.setattr(t, "_patch_urllib3",
                        lambda: (_ for _ in ()).throw(RuntimeError("rate limit")))
    store = t.fetch_sentimiento_store(destino)
    assert store.get("mensual") == {}, (
        "el `mensual` del formato viejo está en interés crudo: publicarlo como "
        "índice base 100 cambia la unidad sin que falle nada")
    assert destino.read_text(encoding="utf-8") == crudo, (
        "no hay canasta nueva: el archivo no se toca")


def test_la_canasta_ignora_un_store_de_otro_esquema():
    """Segunda cerradura, para el día que el esquema vuelva a cambiar: un store
    con los términos completos pero marcado con otra versión no se promedia."""
    assert t.compuesto_sentimiento(_store(esquema="adr-9999")) == {}
    assert t.compuesto_sentimiento(_store()) != {}, "el esquema vigente sí tiene que pasar"


def test_el_store_nuevo_declara_su_esquema_y_su_unidad(tmp_path, monkeypatch):
    """Con Trends caído y sin store previo, no se publica nada inventado."""
    monkeypatch.setattr(t, "_patch_urllib3",
                        lambda: (_ for _ in ()).throw(RuntimeError("sin red")))
    store = t.fetch_sentimiento_store(tmp_path / "sentimiento.json")
    assert store["_meta"]["esquema"] == t.SENTIMIENTO_ESQUEMA
    assert store.get("mensual") == {}
    assert not (tmp_path / "sentimiento.json").exists(), (
        "sin canasta no se escribe el archivo: un store a medias es peor que "
        "ninguno")


def test_un_termino_que_falla_conserva_su_serie_previa(tmp_path, monkeypatch):
    """Lo que habilita el rebase por término: ya no es todo-o-nada.

    Con la canasta cruda anterior, mezclar términos de corridas distintas
    mezclaba escalas y por eso el store se reemplazaba entero. Rebaseado por
    término cada serie es adimensional y puede convivir con las demás.
    """
    destino = tmp_path / "sentimiento.json"
    previo = _store()
    previo["mensual"] = t.compuesto_sentimiento(previo)
    destino.write_text(json.dumps(previo, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(t, "_patch_urllib3",
                        lambda: (_ for _ in ()).throw(RuntimeError("rate limit")))
    store = t.fetch_sentimiento_store(destino)
    assert store["mensual"] == previo["mensual"], (
        "con la fuente caída la canasta tiene que salir entera del store")
    for kw in TRENDS_KEYWORDS:
        assert store["terminos"][kw]["mensual"], f"se perdió la serie de «{kw}»"


def test_la_card_publica_el_desglose_del_ultimo_mes_cerrado(tmp_path, monkeypatch):
    """Card y serie son el mismo número (ADR-0222): se terminó la excepción G3.

    `publicar.py` promedia `interes_relativo`, así que el desglose por término
    tiene que promediar exactamente la canasta de ese mes.
    """
    destino = tmp_path / "sentimiento.json"
    previo = _store()
    previo["mensual"] = t.compuesto_sentimiento(previo)
    destino.write_text(json.dumps(previo, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(t, "SENTIMIENTO_STORE", destino)
    monkeypatch.setattr(t, "_patch_urllib3",
                        lambda: (_ for _ in ()).throw(RuntimeError("rate limit")))
    card = t.fetch_trends()["sentimiento_digital"]
    ultimo = max(previo["mensual"])
    assert card["mes"] == ultimo
    assert set(card["interes_relativo"]) == set(TRENDS_KEYWORDS)
    promedio = sum(card["interes_relativo"].values()) / len(card["interes_relativo"])
    assert abs(round(promedio, 1) - previo["mensual"][ultimo]) <= 0.11, (
        "la card y la serie tienen que dar el mismo número: G3 ya no los exime")


def test_sin_canasta_la_serie_levanta_en_vez_de_devolver_vacio():
    """Devolver [] borraría la serie del CSV; levantar la conserva.

    `descargar_series._correr` trata la excepción como fuente caída y
    `_filas_previas` arrastra las filas anteriores. Con una lista vacía, la
    escritura completa deja el indicador sin serie y el gráfico se vacía sin que
    nada avise — el modo de falla que ese mismo archivo documenta.
    """
    ds = (RAIZ / "scripts" / "descargar_series.py").read_text(encoding="utf-8")
    cuerpo = ds[ds.index("def fetch_sentimiento_serie("):]
    cuerpo = cuerpo[:cuerpo.index("\nVIDA_DERIVADAS.append(")]
    assert "raise ValueError" in cuerpo, (
        "sin canasta hay que levantar: devolver [] borra la serie del CSV")
    assert "return [[f\"{ym}-01\", v]" in cuerpo, "el parser no encontró el retorno"


def test_la_card_se_fecha_con_el_mes_del_dato_y_no_con_la_corrida():
    """Si Trends muere, alguien tiene que enterarse.

    Antes la card salía de una consulta en vivo: si fallaba quedaba en None, el
    carry-forward la marcaba desactualizada y G2 hablaba. Ahora sale del store,
    así que con la fuente caída seguiría publicando un valor — y con la fecha de
    la corrida se vería fresco para siempre. Con el mes del dato, la demora la
    ve G2 como en cualquier fuente mensual.
    """
    sys.path.insert(0, str(RAIZ / "scripts"))
    publicar = _cargar("publicar_para_test", RAIZ / "scripts" / "publicar.py")
    raw = {"metadata": {"timestamp": "2026-08-21T09:00:00"},
           "trends": {"sentimiento_digital": {
               "interes_relativo": {"a": 60.0, "b": 70.0}, "mes": "2026-07"}}}
    card = publicar.build_vida(raw)["sentimiento_digital"]
    assert card["fecha_dato"] == "2026-07-01", (
        "la card se está fechando con el día de la corrida: una fuente muerta "
        "se vería fresca todas las noches")
    assert card["valor"] == 65.0
    assert card["unidad"] == "índice (100 = 4T-2023)"

    sin_datos = publicar.build_vida({"metadata": {"timestamp": "2026-08-21T09:00:00"},
                                     "trends": {"sentimiento_digital": {"interes_relativo": None}}})
    assert sin_datos["sentimiento_digital"]["valor"] is None
    assert sin_datos["sentimiento_digital"]["fecha_dato"] is None


def test_sentimiento_digital_ya_no_esta_exento_de_g3():
    """Se lee el fuente y no se importa el módulo a propósito: este archivo ya
    tiene en `sys.path` el `config.py` del colector, y `gate_calidad` importa
    otro `config.py` distinto que se llama igual."""
    fuente = (RAIZ / "scripts" / "gate_calidad.py").read_text(encoding="utf-8")
    bloque = fuente[fuente.index("G3_EXCEPCIONES = {"):]
    bloque = bloque[:bloque.index("\n}\n")]
    assert '"sentimiento_digital":' not in bloque, (
        "card y serie salen del mismo store y del mismo cálculo desde "
        "ADR-0222: el par tiene que reconciliar como los demás")
    assert '"rigi_inversiones":' in bloque, "el parser de G3_EXCEPCIONES no encontró el bloque"


LEGIBLE = {"inflacion": "inflación", "precios": "precios", "dolar": "dólar",
           "empleo": "empleo", "inseguridad": "inseguridad", "corrupcion": "corrupción"}


def _operacion_de_la_ficha():
    """El campo `operacion` de la ficha: lo que la web dice que se mide.

    Se mira ése y no el bloque entero a propósito. Buscar los términos en
    cualquier parte del bloque da por buena una ficha que los nombre sólo en la
    lista de cambios —o sea, que cuente que entraron y siga describiendo la
    canasta vieja—, que es exactamente la forma en que una ficha se queda atrás.
    """
    ficha = (RAIZ / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
    bloque = ficha[ficha.index("\n  sentimiento_digital: {"):]
    bloque = bloque[:bloque.index("\n  },\n")]
    inicio = bloque.index('operacion: "') + len('operacion: "')
    return bloque[inicio:bloque.index('"', inicio)]


@pytest.mark.parametrize("kw", TRENDS_KEYWORDS)
def test_la_ficha_describe_la_canasta_que_se_consulta(kw):
    """El editor pidió tres términos por nombre; la web tiene que decir cuáles
    son los seis que se consultan, no una canasta que ya no existe."""
    operacion = _operacion_de_la_ficha()
    assert LEGIBLE[kw] in operacion, (
        f"la ficha describe la canasta sin nombrar «{LEGIBLE[kw]}»: «{operacion}»")


def test_la_ficha_ya_no_dice_que_la_canasta_incluye_trabajo():
    assert "trabajo" not in _operacion_de_la_ficha(), (
        "«trabajo» salió de la canasta en ADR-0222 y la ficha lo sigue "
        "declarando como una de las búsquedas que se consultan")
