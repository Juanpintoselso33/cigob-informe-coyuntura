"""Colector de gestión: estados de las fuentes licitatorias."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ── Estados de CONTRAT.AR: preadjudicado NO es adjudicado (ADR-0087) ────────

def test_preadjudicado_no_cuenta_como_adjudicado():
    """`"ADJUDICADO" in "PREADJUDICADO"` es True, y por eso la etapa II-B de la
    Red Federal de Concesiones —2.557 km, 28,1 puntos porcentuales del
    indicador— se contó como adjudicada estando sólo preadjudicada.

    Los strings de abajo son los que CONTRAT.AR devolvía el 19-jul-2026.
    """
    import gestion
    assert gestion._esta_adjudicado("Adjudicado")
    assert gestion._esta_adjudicado("ADJUDICADO")
    assert gestion._esta_adjudicado("Adjudicado Parcial")
    assert not gestion._esta_adjudicado("Preadjudicado")
    assert not gestion._esta_adjudicado("Pendiente Acto Administrativo de Preselección")
    assert not gestion._esta_adjudicado("Desierto")
    assert not gestion._esta_adjudicado("")
    assert not gestion._esta_adjudicado(None)


def _problemas_store_concesiones(store: dict) -> list:
    """Integridad del store de concesiones (ADR-0244): toda etapa entra por una
    resolución del Boletín, con su fecha de publicación real, y el mes del
    escalón es el de esa publicación. Devuelve la lista de problemas; vacía
    sólo si hay etapas y todas cumplen (un store vacío NO cumple)."""
    import re
    etapas = store.get("etapas") or {}
    if not etapas:
        return ["el store no tiene ninguna etapa"]
    out = []
    for etapa, m in etapas.items():
        if not (m.get("resolucion") and m.get("proceso")):
            out.append(f"{etapa}: sin resolución o sin proceso")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", m.get("fecha_pub") or ""):
            out.append(f"{etapa}: fecha_pub ausente o no YYYY-MM-DD ({m.get('fecha_pub')!r})")
        elif m.get("fecha") != m["fecha_pub"][:7]:
            out.append(f"{etapa}: fecha {m.get('fecha')} no es el mes de fecha_pub {m['fecha_pub']}")
        if not m.get("km"):
            out.append(f"{etapa}: sin km")
        if not re.search(r"(RESOL|Resoluci[oó]n)", m.get("fuente") or "", re.I):
            out.append(f"{etapa}: la fuente no nombra la resolución")
    return out


def _store_concesiones() -> dict:
    import json
    from pathlib import Path
    return json.loads((Path(__file__).resolve().parents[1] / "data" / "gestion" /
                       "concesiones_fechas.json").read_text(encoding="utf-8-sig"))


def test_toda_etapa_del_store_de_concesiones_declara_de_donde_salio():
    """Una etapa entra al store por una resolución, y el store dice cuál (ADR-0087
    nació como «II-B no puede estar acá»; ADR-0244 lo generalizó).

    Discrimina: el store real tiene que traer las 4 etapas y cumplir, y el mismo
    chequeo falla con un store vacío, con una fecha_pub ausente y con un mes que
    no coincide con la publicación."""
    store = _store_concesiones()
    assert len(store["etapas"]) >= 4
    assert _problemas_store_concesiones(store) == []
    assert _problemas_store_concesiones({"etapas": {}})
    sin_fecha = {"etapas": {**store["etapas"], "II": {**store["etapas"]["II"], "fecha_pub": None}}}
    assert any("fecha_pub" in p for p in _problemas_store_concesiones(sin_fecha))
    mes_mal = {"etapas": {**store["etapas"], "III": {**store["etapas"]["III"], "fecha": "2026-09"}}}
    assert any("no es el mes" in p for p in _problemas_store_concesiones(mes_mal))
    solo_portal = {"etapas": {"IV": {"fecha": "2026-10", "km": 1, "fuente": "CONTRAT.AR x (detectado 2026-10)"}}}
    assert _problemas_store_concesiones(solo_portal)


def test_preadjudicado_nunca_alcanza_para_entrar_al_store():
    """La guarda de ADR-0087, ahora dicha de frente en vez de por la ausencia de
    una etapa: es la frontera de palabra la que separa las dos cosas."""
    import gestion
    assert not gestion._esta_adjudicado("Preadjudicado")
    assert not gestion._esta_adjudicado("PREADJUDICADO")
    assert not gestion._esta_adjudicado("Disponible Para Adjudicar")
    assert gestion._esta_adjudicado("Adjudicado")


def test_las_etapas_del_store_se_fechan_con_la_publicacion():
    """Para una función escalonada, la fecha ES el escalón. La Etapa II tenía
    fecha_pub null y el código la rellenaba con «2026-05» cableado; ahora la fecha
    de InfoLeg (2026-05-15) vive en el store y se valida contra `fecha`."""
    store = _store_concesiones()
    assert store["etapas"]["II"]["fecha_pub"] == "2026-05-15"
    for etapa, meta in store["etapas"].items():
        assert meta["fecha"] == meta["fecha_pub"][:7], etapa


# ── Desregulación: sólo cuenta lo que deroga de verdad (ADR-0096) ───────────

def test_solo_cuenta_derogaciones_en_la_parte_dispositiva():
    """La mitad de lo que contaba la versión anterior no derogaba nada: la
    búsqueda de InfoLeg matchea la palabra en los considerandos, donde la norma
    cuenta lo que derogó OTRA. El caso testigo era una resolución de Cancillería
    sobre un nombramiento episcopal."""
    import gestion
    considerando = ("VISTO... Que la Resolución ANAC N° 247 deroga en su Artículo 1° "
                    "la mencionada Resolución ANAC N° 754/16. Por ello, EL ADMINISTRADOR "
                    "RESUELVE: ARTÍCULO 1°.- Apruébase el procedimiento.")
    assert gestion._DISPOSITIVA.search(considerando)
    cuerpo = considerando[gestion._DISPOSITIVA.search(considerando).end():]
    assert not gestion._VERBO_DEROGA.search(cuerpo), "una mención en considerandos no debe contar"

    dispositivo = "Por ello, LA COMISIÓN RESUELVE: ARTÍCULO 1°.- Derógase la Ley N° 20.680."
    cuerpo2 = dispositivo[gestion._DISPOSITIVA.search(dispositivo).end():]
    assert gestion._VERBO_DEROGA.search(cuerpo2)


def test_derogacion_parcial_no_cuenta_como_norma_completa():
    """Eliminar «el punto 9) del apartado E) del artículo 20» no es comparable
    con derogar una ley entera; se releva aparte."""
    import gestion
    for parcial in ("el artículo 5° BIS del Capítulo V de las NORMAS",
                    "la Sección XI del Capítulo V del Título II",
                    "el punto 9) del apartado E) del artículo 20",
                    "el título VII (artículos 7° a 18) de la ley 23.905"):
        assert gestion._PARTE_DE_NORMA.match(parcial), f"debería ser parcial: {parcial}"
    for completa in ("la Ley N° 20.680", "las Resoluciones N° 71/2020 y N° 190/2020"):
        assert not gestion._PARTE_DE_NORMA.match(completa), f"debería ser completa: {completa}"


def test_el_dnu_70_2023_esta_contado():
    """La ficha afirmaba que el DNU 70/23 no figuraba en la fuente y el auditor
    externo lo tomó como cierto. Es falso: figura, y aporta 38 normas."""
    import json
    from pathlib import Path
    store = Path(__file__).resolve().parents[1] / "data" / "gestion" / "desregulacion_normas.json"
    if not store.exists():
        import pytest
        pytest.skip("caché por norma todavía no generada")
    normas = json.loads(store.read_text(encoding="utf-8-sig"))["normas"]
    dnu = normas.get("395521")
    assert dnu is not None, "el DNU 70/2023 debería estar en la caché"
    assert dnu["derogadas"] >= 30, f"el DNU 70/2023 deroga decenas de normas, no {dnu['derogadas']}"


# ── Privatizaciones: la etapa de cada empresa es auditable (ADR-0101) ───────

def test_privatizaciones_publica_la_norma_de_cada_etapa():
    """Es el único indicador del cinturón cuya etapa asigna el analista, sin
    fuente en vivo. La revisión externa lo marcó como "vulnerable a
    cuestionamientos de sesgo si no se publica el detalle empresa por empresa
    con su norma de respaldo". El detalle ya existía en el registro; este test
    exige que llegue al snapshot."""
    import json
    from pathlib import Path
    snap = json.loads((Path(__file__).resolve().parents[1] / "web" / "src" / "data" /
                       "informe.json").read_text(encoding="utf-8"))
    priv = snap["cinturones"]["gestion"]["indicadores"]["privatizaciones"]
    detalle = priv.get("empresas_detalle")
    assert detalle, "privatizaciones debe publicar el detalle por empresa"
    assert len(detalle) == priv["empresas"], "el detalle debe cubrir todas las empresas"

    sin_norma = [e["empresa"] for e in detalle if not e.get("norma")]
    assert not sin_norma, f"empresas sin norma de respaldo publicada: {sin_norma}"

    for e in detalle:
        assert e.get("etapa") is not None
        assert 0 <= float(e["etapa"]) <= 4, f"{e['empresa']}: etapa fuera de 0-4"
        assert e.get("mecanismo"), f"{e['empresa']}: sin mecanismo declarado"

    # el promedio publicado tiene que salir del detalle, no de otro lado
    prom = sum(float(e["etapa"]) for e in detalle) / len(detalle)
    assert abs(prom - priv["etapa_promedio"]) < 0.01
    assert abs(round(prom / 4 * 100, 1) - priv["valor"]) < 0.05


# ── RIGI: el % puede bajar sin que nada empeore (ADR-0102) ─────────────────

def test_rigi_avisa_cuando_el_porcentaje_baja_por_el_denominador():
    """El indicador es inversión aprobada sobre el pipeline total. Cada proyecto
    grande que entra "en evaluación" agranda el denominador, así que el % puede
    caer aunque el capital aprobado crezca. Caso real ocurrido entre junio y
    julio de 2026: 22,1% → 22,0% con la inversión aprobada subiendo de US$
    27.760M a US$ 31.192M."""
    import gestion
    nota = gestion._rigi_nota_denominador(22.0, 31192, pct_ant=22.1, usd_ant=27760)
    assert nota, "debería avisar: el % bajó y el capital aprobado subió"
    assert "3.432" in nota, "debe cuantificar cuánto capital entró"
    assert "no es un retroceso" in nota.lower()


def test_rigi_no_avisa_cuando_el_retroceso_es_genuino():
    """Si caen las dos cosas, es un retroceso real y no hay nada que excusar.
    Tampoco avisa cuando el porcentaje sube."""
    import gestion
    assert gestion._rigi_nota_denominador(20.0, 26000, pct_ant=22.1, usd_ant=27760) is None
    assert gestion._rigi_nota_denominador(25.0, 31192, pct_ant=22.1, usd_ant=27760) is None
    # sin datos previos utilizables tampoco inventa un aviso
    assert gestion._rigi_nota_denominador(22.0, 31192, pct_ant=None, usd_ant="x") is None
