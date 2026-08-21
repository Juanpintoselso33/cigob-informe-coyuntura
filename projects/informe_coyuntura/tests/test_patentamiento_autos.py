"""El espejo de las motos (ADR-0223).

`patentamiento_autos` existe para contestar una pregunta que `patentamiento_motos`
no puede contestar solo: si el patentamiento sube porque los hogares compran más
o porque bajan de categoría. La moto es a la vez bien de consumo, medio de
trabajo y sustituto barato del auto, así que con una sola serie toda suba se lee
como mejora.

Estos tests cuidan cuatro cosas que pueden volver a romperse:

1. **La fuente sigue siendo el registro.** ACARA republica el dato de la DNRPA y
   ADEFA mide ventas de fábrica a concesionario, que no es patentamiento. Un
   indicador que se llama de una manera y mide otra ya pasó dos veces acá.
2. **El colector revienta ante un cambio de forma** en vez de devolver una serie
   recortada. Una serie a la que le falta el último mes no se distingue a ojo de
   una serie sana, y alimenta un componente que se publica en una web.
3. **Card y serie son el mismo número**, y la serie llega al 4T-2023 con las
   ventanas móviles de doce meses completas.
4. **Autos y motos no se volvieron la misma serie.** Si algún día lo fueran, el
   segundo componente dejaría de aportar y sólo diluiría al resto del índice.
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path
from statistics import mean

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itvc                      # noqa: E402
import validacion_externa        # noqa: E402

# El colector se carga POR RUTA: `scripts/vida_cotidiana/` tiene su propio
# `config.py` y ponerlo al frente del path tapa al del proyecto.
sys.path.insert(0, str(ROOT / "scripts" / "vida_cotidiana"))
_spec = importlib.util.spec_from_file_location(
    "dnrpa_autos", ROOT / "scripts" / "vida_cotidiana" / "collectors" / "dnrpa_autos.py")
_dnrpa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dnrpa)

SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
ITVC_PY = (ROOT / "scripts" / "itvc.py").read_text(encoding="utf-8")
VIDA = SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"]
IND = VIDA["patentamiento_autos"]

BASE_4T = ("2023-10", "2023-11", "2023-12")


# ── 1 · La fuente es el registro, no una cámara ─────────────────────────────
def test_la_fuente_es_el_registro_y_no_una_camara():
    fuente = IND.get("fuente", "")
    assert "DNRPA" in fuente, f"la fuente dejó de ser el registro: {fuente!r}"
    for camara in ("ACARA", "ADEFA"):
        assert camara not in fuente, (
            f"la fuente pasó a {camara}: ACARA republica lo que la DNRPA "
            f"registra y ADEFA mide ventas de fábrica a concesionario, que "
            f"ocurren antes del patentamiento y pueden quedar en stock")


def test_la_card_cuenta_unidades_patentadas():
    assert IND.get("unidad") == "unidades", IND.get("unidad")
    assert 5_000 < IND["valor"] < 200_000, (
        f"{IND['valor']} no es un mes de patentamientos de autos del país")


# ── 2 · El colector falla en voz alta ante un cambio de forma ───────────────
COLUMNAS = ["tipo_vehiculo", "anio_inscripcion_inicial", "mes_inscripcion_inicial",
            "provincia_inscripcion_inicial", "letra_provincia_inscripcion_inicial",
            "cantidad_inscripciones_iniciales", "provincia_id"]
JURISDICCIONES = [f"J{i:02d}" for i in range(_dnrpa.JURISDICCIONES)]


def _csv_falso(desde=(2022, 11), hasta=(2026, 7), tipo="Automotores",
               columnas=None, jurisdicciones=None, jurisdicciones_ultimo=None):
    """Un CSV con la MISMA forma que el de la DNRPA, para poder deformarlo."""
    filas = [",".join(columnas or COLUMNAS)]
    y, m = desde
    meses = []
    while (y, m) <= hasta:
        meses.append((y, m))
        m += 1
        if m > 12:
            m, y = 1, y + 1
    for i, (y, m) in enumerate(meses):
        provs = (jurisdicciones_ultimo if (jurisdicciones_ultimo and i == len(meses) - 1)
                 else (jurisdicciones or JURISDICCIONES))
        for j, prov in enumerate(provs):
            filas.append(f'"{tipo}",{y},{m},"{prov}","X",{1000 + j},"06"')
    return "\n".join(filas) + "\n"


def _correr(monkeypatch, texto, declarado=("202211", "202607")):
    class _Resp:
        status_code = 200
        content = texto.encode("utf-8")

        def raise_for_status(self):
            pass

    monkeypatch.setattr(_dnrpa, "_url_del_recurso",
                        lambda: ("http://falso/x.csv", declarado[0], declarado[1]))
    monkeypatch.setattr(_dnrpa.requests, "get", lambda *a, **k: _Resp())
    return _dnrpa.fetch_patentamiento_autos()


def test_el_colector_sano_devuelve_card_y_serie(monkeypatch):
    """La guarda de las guardas: si el CSV falso ya no pasara, los tests de
    abajo estarían comprobando que revienta por el motivo equivocado."""
    d = _correr(monkeypatch, _csv_falso())
    assert d["patentamiento_autos"]["fecha"] == "2026-07"
    assert min(d["serie"]) == "2022-11"


def test_revienta_si_falta_una_columna(monkeypatch):
    roto = [c for c in COLUMNAS if c != "tipo_vehiculo"]
    texto = _csv_falso(columnas=roto)
    # sin la columna, las filas tienen un campo de más: se recorta a mano
    texto = "\n".join([texto.splitlines()[0]]
                      + [l.split(",", 1)[1] for l in texto.splitlines()[1:]])
    with pytest.raises(ValueError, match="columnas"):
        _correr(monkeypatch, texto)


def test_revienta_si_cambia_el_rotulo_del_universo(monkeypatch):
    """Si la DNRPA renombrara «Automotores» o metiera motovehículos en el mismo
    archivo, filtrar en silencio daría cero o el doble sin avisar."""
    with pytest.raises(ValueError, match="tipo"):
        _correr(monkeypatch, _csv_falso(tipo="Automotores y motovehículos"))


def test_revienta_si_el_periodo_declarado_no_es_el_que_trae(monkeypatch):
    """El anclaje central: el nombre del recurso declara hasta qué mes llega. Un
    mes a medio cargar rompe esa igualdad antes de publicar un derrumbe falso."""
    with pytest.raises(ValueError, match="período"):
        _correr(monkeypatch, _csv_falso(hasta=(2026, 6)))


def test_revienta_si_un_mes_viene_con_menos_jurisdicciones(monkeypatch):
    with pytest.raises(ValueError, match="jurisdicciones"):
        _correr(monkeypatch, _csv_falso(jurisdicciones_ultimo=JURISDICCIONES[:5]))


def test_revienta_si_la_serie_no_cubre_la_base_del_indice(monkeypatch):
    with pytest.raises(ValueError, match="base del índice"):
        _correr(monkeypatch, _csv_falso(desde=(2024, 1)),
                declarado=("202401", "202607"))


def test_el_recurso_se_descubre_por_catalogo_y_no_por_url_fija():
    """La dirección de descarga lleva el período adentro y cambia todos los
    meses: fijarla congelaría el indicador en un archivo viejo sin avisar."""
    fuente = (ROOT / "scripts" / "vida_cotidiana" / "collectors"
              / "dnrpa_autos.py").read_text(encoding="utf-8")
    assert "package_show" in fuente
    assert not re.search(r'https?://\S*\d{4}-\d{2}-\d{4}-\d{2}\.csv', fuente), (
        "hay una URL con el período adentro escrita a mano en el colector")


# ── 3 · Card, serie y base del índice ───────────────────────────────────────
def test_card_y_serie_son_el_mismo_numero():
    serie = SERIES.get("patentamiento_autos") or []
    assert serie, "sin serie publicada"
    assert abs(serie[-1]["valor"] - IND["valor"]) < 1, (
        f"card {IND['valor']} ≠ serie {serie[-1]['valor']}")


def test_la_serie_llega_al_4t_2023_con_ventanas_moviles_completas():
    """No alcanza con tocar el 4T-2023: el rebase compara ventanas de DOCE meses
    que terminan en oct, nov y dic de 2023, así que la serie tiene que empezar
    once meses antes (nov-2022) y no tener huecos."""
    meses = [p["fecha"][:7] for p in SERIES["patentamiento_autos"]]
    assert meses[0] <= "2022-11", (
        f"la serie arranca en {meses[0]}: las ventanas móviles de la base "
        f"quedan incompletas y el rebase cae al simple")
    for base in BASE_4T:
        assert base in meses
    a0, m0 = int(meses[0][:4]), int(meses[0][5:7])
    af, mf = int(meses[-1][:4]), int(meses[-1][5:7])
    assert (af * 12 + mf) - (a0 * 12 + m0) + 1 == len(meses), "la serie tiene huecos"


def test_el_indice_lo_transforma_por_movil_12m_como_a_las_motos():
    """La misma transformación en los DOS lugares que la aplican: el índice vivo
    y la reconstrucción histórica. Si divergen, la serie publicada del ITCIS deja
    de ser el índice que se publica."""
    linea = next(l for l in ITVC_PY.splitlines()
                 if 'idx["patentamiento_autos"]' in l)
    assert "rebase_movil12" in linea, linea
    assert "patentamiento_autos" in validacion_externa.MOVIL12
    assert "patentamiento_motos" in validacion_externa.MOVIL12


# ── 4 · Integra el índice, y no es la misma serie que motos ─────────────────
def test_integra_el_indice_y_no_es_una_card_de_contexto():
    pesos = {i: interno for d in itvc.DIMENSIONES_ITVC.values()
             for i, interno in d["indicadores"].items()}
    assert "patentamiento_autos" in pesos, (
        "se publica como card sin puntuar: o integra el índice, o no es card")
    assert pesos["patentamiento_autos"] == pesos["patentamiento_motos"] / 0.98, (
        "el espejo dejó de tener el peso de las motos sin que ningún ADR lo diga")
    assert IND.get("en_indice") is True
    assert IND.get("peso_efectivo")


def test_autos_y_motos_no_se_volvieron_la_misma_serie():
    """En NIVELES correlacionan alto y eso ya está explicado: es la época en
    común que ADR-0108 documentó para todo el cinturón. Lo que este test cuida
    es lo otro — que al destendenciar sigan aportando señal distinta.

    Se mide sobre las series COMO LAS PUBLICA LA FUENTE, a propósito. La matriz
    de redundancia del informe mide los componentes después del techo de recorte
    de 140 y para este par da +0,801, porque motos está apoyada contra el techo y
    el tramo en que las dos se separan no entra en la cuenta (ADR-0223). Esa es
    una propiedad del índice; ésta, del fenómeno, y es la que dice si el segundo
    componente aporta algo.
    """
    def movil12(puntos):
        vals = {p["fecha"][:7]: p["valor"] for p in puntos}
        ks = sorted(vals)
        return {ks[i]: mean(vals[k] for k in ks[i - 11:i + 1])
                for i in range(11, len(ks))}

    a, m = movil12(SERIES["patentamiento_autos"]), movil12(SERIES["patentamiento_motos"])
    comunes = sorted(set(a) & set(m))
    assert len(comunes) >= 24, f"sólo {len(comunes)} meses en común"
    da = [a[comunes[i]] / a[comunes[i - 1]] - 1 for i in range(1, len(comunes))]
    dm = [m[comunes[i]] / m[comunes[i - 1]] - 1 for i in range(1, len(comunes))]
    mx, my = mean(da), mean(dm)
    num = sum((x - mx) * (y - my) for x, y in zip(da, dm))
    den = (sum((x - mx) ** 2 for x in da) * sum((y - my) ** 2 for y in dm)) ** 0.5
    r = num / den
    assert abs(r) < 0.7, (
        f"autos y motos destendenciadas correlacionan {r:+.3f}: el segundo "
        f"componente dejó de aportar señal propia y sólo diluye al resto")


def test_la_serie_de_autos_no_es_la_de_motos():
    autos = {p["fecha"]: p["valor"] for p in SERIES["patentamiento_autos"]}
    motos = {p["fecha"]: p["valor"] for p in SERIES["patentamiento_motos"]}
    comunes = set(autos) & set(motos)
    iguales = [f for f in comunes if autos[f] == motos[f]]
    assert not iguales, f"los dos indicadores publican el mismo valor en {iguales[:5]}"


def test_el_tope_de_frescura_esta_puesto_y_es_el_medido():
    """El default de 110 días no avisaría nunca de un mes salteado: la DNRPA
    publica el mes M entre el día 1 y el 4 de M+1 (medido sobre el historial del
    catálogo), así que la card nunca pasa de ~72 días."""
    import gate_calidad
    assert gate_calidad.MAX_DIAS.get("patentamiento_autos") == 90


def _fila_csv(indicador):
    with open(ROOT / "output" / "series" / "vida_cotidiana.csv",
              encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r["indicador"] == indicador]


def test_la_serie_declara_la_misma_fuente_que_la_card():
    """El CSV de la serie lleva su propia columna de fuente, escrita a mano en
    `descargar_series.py`. Si divergen, el modal dice una cosa y el gráfico
    viene de otra."""
    filas = _fila_csv("patentamiento_autos")
    assert filas, "el CSV del cinturón no tiene filas de patentamiento_autos"
    fuentes = {r["fuente"] for r in filas}
    assert len(fuentes) == 1, fuentes
    assert "DNRPA" in fuentes.pop()
