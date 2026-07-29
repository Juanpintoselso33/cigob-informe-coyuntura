"""Indicador de postura empresaria (ADR-0150).

Lo que se protege acá es distinto de lo que protege el test del detector: que el
NÚMERO que se publica salga del registro codificado y no de otra cosa, que card
y serie sean la misma cuenta, y —lo más importante— que el material sobre el que
se codificó exista de verdad. El bug que motivó este ADR fue que los 57 textos
de UIA eran el menú del sitio, idénticos entre sí, y ningún test lo veía.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import itcp  # noqa: E402
import parametrica  # noqa: E402
import politica  # noqa: E402

REGISTRO = json.loads(politica.APOYO_CODIFICACION_PATH.read_text(encoding="utf-8-sig"))
CASOS = REGISTRO["casos"]


def test_los_textos_del_registro_no_son_todos_iguales():
    """EL test de este ADR. Los 57 comunicados de UIA se habían codificado sobre
    el menú de navegación del sitio —idéntico carácter por carácter— y eso
    significa que más de medio corpus se clasificó sólo por el título. No lo
    encontró ningún gate: lo encontraron dos codificadores ciegos leyendo."""
    for camara in ("UIA", "AEA"):
        txt = [c["texto"] for c in CASOS if c["camara"] == camara]
        assert len(set(txt)) == len(txt), (
            f"{camara}: {len(txt)} comunicados pero {len(set(txt))} textos distintos "
            f"— el scraper está guardando la misma plantilla para todos")
        assert all(len(t) > 200 for t in txt), f"{camara}: hay textos vacíos o mínimos"
        # El texto completo distinto no alcanza: una plantilla que variara en un
        # byte final pasaría. Se mira también el arranque, con tolerancia — AEA
        # tiene comunicados del mismo ciclo («Encuentros con Gobernadores») que
        # legítimamente abren con el mismo párrafo de contexto y siguen distinto.
        repetido = max(sum(1 for t in txt if t[:150] == p) for p in {t[:150] for t in txt})
        assert repetido <= 3, (
            f"{camara}: {repetido} comunicados comparten los primeros 150 caracteres "
            f"— eso es una plantilla del sitio, no el cuerpo del comunicado")


def test_la_concordancia_alcanza_el_umbral():
    """Sin kappa ≥ 0,70 el indicador no se publica (ADR-0131). Se deja fijo en el
    test para que bajarlo exija tocar esta línea a propósito."""
    c = REGISTRO["_meta"]["concordancia"]
    assert c["kappa_postura"] >= 0.70 and c["kappa_destinatario"] >= 0.70
    assert c["estado"] == "ALCANZADA"


def test_ningun_caso_entra_al_conteo_sin_pasar_por_la_adjudicacion():
    """Este test antes exigía que las dos pasadas coincidieran EXACTAMENTE en el
    conjunto computable. Era una propiedad del corpus viejo —codificado sobre
    textos truncados, donde casi todo caía en «neutro» y quedaba poco sobre lo
    que discrepar—, no una garantía del método: con el texto completo aparecen
    desacuerdos que sí tocan lo que puntúa, y exigir que no existan presionaría
    a codificar para que el test pase.

    La garantía que corresponde es otra: que ninguno de esos casos entre al
    conteo por omisión. Si las dos pasadas difieren en si un caso computa, tiene
    que estar marcado `adjudicado`, o sea resuelto a mano por el autor del
    manual (ADR-0131)."""
    comp = lambda p, d: d == "ejecutivo_nacional" and p in ("apoyo", "critica")
    for c in CASOS:
        difieren = (comp(c["postura"], c["destinatario"])
                    != comp(c["pasada_2"]["postura"], c["pasada_2"]["destinatario"]))
        if difieren:
            assert c["concordancia"] == "adjudicado", (
                f"{c['fecha']} {c['camara']}: las dos pasadas difieren en si el caso "
                f"cuenta y nadie lo adjudicó")


def test_solo_cuentan_los_dirigidos_al_ejecutivo_con_postura():
    """La regla de conteo es la que evita el error que hundió a ADEBA: contar
    como crítica al Gobierno una crítica a un municipio."""
    comp = [c for c in CASOS if c["destinatario"] == "ejecutivo_nacional"
            and c["postura"] in ("apoyo", "critica")]
    assert len(comp) < len(CASOS), "estarían entrando todos"
    assert not [c for c in comp if c["postura"] in ("neutro", "dudoso")]
    assert {c["destinatario"] for c in comp} == {"ejecutivo_nacional"}


def test_la_card_es_el_ultimo_punto_de_la_serie():
    """G3 por construcción: una sola implementación del cálculo (ADR-0086/0087)."""
    serie = politica.apoyo_empresario_serie()
    card = politica.fetch_apoyo_empresario()
    assert [card["fecha_dato"], card["valor"]] == serie[-1]


def test_la_serie_no_rellena_los_meses_vacios_con_cero():
    """Cero significa equilibrio entre apoyo y crítica, que es una afirmación
    distinta de «no se pronunció»."""
    reg = json.loads(politica.APOYO_CODIFICACION_PATH.read_text(encoding="utf-8-sig"))
    assert "serie_12m" not in reg, "la serie se calcula, no se guarda: dos fuentes divergen"
    serie = politica.apoyo_empresario_serie()
    assert all(v is not None for _, v in serie)
    assert all(-1.0 <= v <= 1.0 for _, v in serie)


def test_la_serie_arranca_en_el_periodo_y_es_mensual_ascendente():
    serie = politica.apoyo_empresario_serie()
    assert serie[0][0] == "2023-12-01", "el período arranca con la asunción"
    fechas = [f for f, _ in serie]
    assert fechas == sorted(fechas) and len(fechas) == len(set(fechas))
    assert len(serie) >= 30, "la serie se acortó: revisar el registro"


@pytest.mark.parametrize("saldo,esperado", [
    (1.0, 100), (0.6, 100),      # todo apoyo
    (0.0, 65),                   # equilibrio: el ancla con significado propio
    (-0.6, 10), (-1.0, 10),      # todo crítica
])
def test_las_bandas_puntuan_el_rango_teorico(saldo, esperado):
    """Anclas sobre el rango teórico (−1 a +1), no sobre el observado: ADR-0045
    sólo autoriza calibrar contra lo observado si el extremo es inalcanzable."""
    assert parametrica.puntaje_interpolado(saldo, itcp.BANDAS_ITCP["apoyo_empresario"]) == esperado


def test_integra_la_dimension_de_sector_privado():
    dim = itcp.DIMENSIONES_ITCP["sector_privado"]["indicadores"]
    assert dim["apoyo_empresario"] == 0.5 and dim["brecha_obra_publica"] == 0.5
    assert abs(sum(dim.values()) - 1.0) < 1e-9
    assert itcp.FAMILIAS_ITCP["apoyo_empresario"] == "tension"
    assert itcp.REZAGO_MESES_ITCP["apoyo_empresario"] == 6.0


def test_la_card_muestra_cuantos_faltan_codificar():
    """Es el único indicador del cinturón cuyo dato lo actualiza una persona: si
    nadie codifica, la serie se congela sin que falle nada."""
    card = politica.fetch_apoyo_empresario()
    assert isinstance(card["pendientes_de_codificar"], int)
    assert card["apoyos_ventana"] + card["criticas_ventana"] == card["comunicados_ventana"]


def test_cada_caso_tiene_los_dos_ejes_y_su_segunda_lectura():
    validas_p = {"apoyo", "critica", "neutro", "dudoso"}
    validas_d = {"ejecutivo_nacional", "congreso", "provincias_municipios",
                 "judicial", "externo_o_propio"}
    for c in CASOS:
        assert c["postura"] in validas_p and c["destinatario"] in validas_d
        assert c["pasada_2"]["postura"] in validas_p
        assert c["concordancia"] in ("acuerdo", "adjudicado")
        assert c["fecha"] and c["titulo"] and c["camara"] in ("AEA", "UIA")
