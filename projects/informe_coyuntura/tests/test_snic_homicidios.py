"""ADR-0324: el SNIC conserva homicidios por NOMBRE, no por ranking de volumen.

Antes `tipos_principales` era el top-5 por cantidad de hechos, y eso
descartaba "Homicidios dolosos" (bajo volumen por diseño) mientras conservaba
categorías de bulto como "Robos". El control negativo es la parte que
importa: un corte por volumen que sólo agregara homicidios a mano no
demostraría que el MECANISMO cambió — hay que ver que homicidios sobrevive
pese a estar en el fondo de la tabla de volumen, y que la lista no se infla
con cualquier categoría.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_VIDA = ROOT / "scripts" / "vida_cotidiana"


def _cargar_por_ruta(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# El colector se carga POR RUTA, y su `config` también: `scripts/vida_cotidiana/`
# tiene el suyo, y corrido dentro de la suite completa el nombre `config` ya
# puede haber quedado tomado por el de la raíz del proyecto en `sys.modules`.
# Misma trampa que ya documentan `utdt_icc`, `indec_supermercados` y `dnrpa_autos`.
_previo = sys.modules.get("config")
sys.modules["config"] = _cargar_por_ruta("config", _VIDA / "config.py")
try:
    snic = _cargar_por_ruta("snic", _VIDA / "collectors" / "snic.py")
finally:
    if _previo is not None:
        sys.modules["config"] = _previo
    else:
        sys.modules.pop("config", None)


def _csv(filas):
    header = "anio;codigo_delito_snic_nombre;cantidad_hechos"
    cuerpo = "\n".join(f"{a};{t};{h}" for a, t, h in filas)
    return (header + "\n" + cuerpo + "\n").encode("utf-8")


# Los 7 tipos de TIPOS_RELEVANTES, todos presentes: desde ADR-0325 falta
# CUALQUIERA de ellos hace que el parseo levante (ver
# test_falta_un_tipo_relevante_es_ruidoso_no_silencioso), así que los tests
# que ejercitan otra cosa (filtrado por nombre, categorías irrelevantes)
# necesitan el set completo para no disparar ese camino por accidente.
_FILAS_COMPLETAS = [
    ("2025", "Robos (excluye los agravados por el resultado de lesiones y/o muertes)", 360946),
    ("2025", "Hurtos", 308523),
    ("2025", "Amenazas", 217883),
    ("2025", "Lesiones dolosas", 179710),
    ("2025", "Robos agravados por el resultado de lesiones y/o muertes", 40000),
    ("2025", "Abusos sexuales con acceso carnal (violaciones)", 5000),
    ("2025", "Homicidios dolosos", 1613),
]


def test_homicidios_sobrevive_aunque_sea_bajisimo_volumen():
    """Control positivo Y negativo en la misma corrida: siete categorías con
    volumen decreciente, homicidios último. Con el top-5 viejo, homicidios
    quedaba afuera por uno solo — el caso más ajustado posible."""
    filas = _FILAS_COMPLETAS + [("2025", "Otros delitos contra la propiedad", 249754)]
    out = snic._parse_snic_csv(_csv(filas))
    assert "Homicidios dolosos" in out["tipos_principales"], (
        "homicidios sigue afuera: el corte sigue siendo por ranking de volumen")
    assert out["tipos_principales"]["Homicidios dolosos"] == 1613


def test_una_categoria_irrelevante_no_entra_aunque_tenga_mucho_volumen():
    """Control negativo: que el fix no se haya convertido en 'conservar todo'.
    Una categoría de bulto que NO está en TIPOS_RELEVANTES tiene que quedar
    afuera aunque sea la de mayor volumen del CSV."""
    filas = _FILAS_COMPLETAS + [("2025", "Contravenciones", 999_999_999)]
    out = snic._parse_snic_csv(_csv(filas))
    assert "Contravenciones" not in out["tipos_principales"], (
        "una categoría fuera de TIPOS_RELEVANTES entró igual: el filtro no es "
        "por nombre, es un top-N disfrazado")
    assert "Homicidios dolosos" in out["tipos_principales"]


def test_robos_tambien_se_conserva():
    """Pedido explícito de Juan: "buscar datos de homicidios y rapiñas". Robos
    (la categoría SNIC más cercana a "rapiñas" en el desglose oficial) tiene
    que seguir en la lista, no sólo homicidios."""
    out = snic._parse_snic_csv(_csv(_FILAS_COMPLETAS))
    assert "Robos (excluye los agravados por el resultado de lesiones y/o muertes)" in out["tipos_principales"]


def test_falta_un_tipo_relevante_es_ruidoso_no_silencioso():
    """ADR-0325: con lista fija por NOMBRE, el modo de falla más probable es
    que la fuente renombre una categoría. Antes esto sólo generaba un
    `logger.warning` y la corrida seguía como si nada — el dato faltante se
    perdía sin que nadie se enterara. Ahora tiene que levantar, ruidoso,
    con el/los tipos faltantes nombrados en el mensaje."""
    filas = [("2025", "Homicidios dolosos", 1613)]
    try:
        snic._parse_snic_csv(_csv(filas))
        assert False, ("faltan 6 de los 7 tipos esperados y no reventó: "
                        "la ausencia se sigue perdiendo en silencio")
    except ValueError as e:
        msg = str(e)
        for faltante in ("Hurtos", "Amenazas", "Lesiones dolosas"):
            assert faltante in msg, f"el mensaje de error no nombra '{faltante}': {msg}"


def test_con_todos_los_tipos_relevantes_no_revienta():
    """Control positivo del test anterior: si el CSV trae los 7 tipos
    esperados, no hay nada ruidoso que levantar."""
    out = snic._parse_snic_csv(_csv(_FILAS_COMPLETAS))
    assert set(out["tipos_principales"]) == set(snic.TIPOS_RELEVANTES)


def test_amenazas_y_lesiones_dolosas_se_conservan():
    """ADR-0325: la primera versión de la lista fija sacó Amenazas (217.883)
    y Lesiones dolosas (179.710) sin decirlo — estaban en el top-5 por
    volumen que el cambio reemplazó. Se restituyen explícitamente."""
    assert "Amenazas" in snic.TIPOS_RELEVANTES
    assert "Lesiones dolosas" in snic.TIPOS_RELEVANTES


def test_el_desglose_llega_al_texto_que_se_publica():
    """ADR-0325: `tipos_principales` se calculaba y quedaba en el snapshot
    interno del colector — ni `publicar.py`, ni `web/src`, ni `dist/` lo
    leían. `_snic_desglose_txt` (en publicar.py) es lo que lo cuelga del
    contraste SNIC que sí se publica en el detalle de `inseguridad`."""
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    import publicar

    txt = publicar._snic_desglose_txt({
        "Robos (excluye los agravados por el resultado de lesiones y/o muertes)": 360946,
        "Homicidios dolosos": 1613,
    })
    assert "Homicidios dolosos: 1.613" in txt, txt
    assert "Robos" in txt and "360.946" in txt, txt
    assert publicar._snic_desglose_txt({}) == "", "sin datos, no agrega texto"
