"""Motorización total: qué puntúa, con qué serie y con qué techo (ADR-0224).

El componente existe porque el patentamiento de motos solo no puede contestar
la pregunta que el editorial discutía: si la gente pasa del auto a la moto
porque no sostiene el auto (empobrecimiento) o porque accede a su primer
vehículo (acceso). Las dos lecturas empujan las motos hacia arriba. El TOTAL
las separa: la sustitución descendente dejaría el total plano.

Estos tests cuidan siete cosas que pueden volver a romperse:

1. **La fuente sigue siendo el registro.** ACARA republica el dato de la DNRPA y
   ADEFA mide ventas de fábrica a concesionario, que no es patentamiento.
2. **El colector revienta ante un cambio de forma** en vez de devolver una serie
   recortada, que no se distingue a ojo de una serie sana.
3. **Puntúa el total y no un vehículo**, y autos y motos no vuelven como cards.
4. **La matriz A×B explica el color** — sin ella el componente publica "subió" y
   nada más, que es la lectura ambigua que el ADR vino a desarmar.
5. **Tierra del Fuego sigue excluida**, que es lo único que separa al indicador
   de un artefacto registral de 29.000 unidades.
6. **El puente CAFAM→DNRPA no movió el número**: un cambio de fuente en un
   componente que puntúa se verifica, no se declara.
7. **La excepción al techo sigue acotada a un componente** y no se volvió un
   permiso general.
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
    "motorizacion", ROOT / "scripts" / "vida_cotidiana" / "collectors" / "motorizacion.py")
_mot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mot)

SNAPSHOT = json.loads(
    (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
SERIES = json.loads(
    (ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
ITVC_PY = (ROOT / "scripts" / "itvc.py").read_text(encoding="utf-8")
VIDA = SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"]
IND = VIDA["motorizacion_total"]

BASE_4T = ("2023-10", "2023-11", "2023-12")
COLUMNAS = ["tipo_vehiculo", "anio_inscripcion_inicial", "mes_inscripcion_inicial",
            "provincia_inscripcion_inicial", "letra_provincia_inscripcion_inicial",
            "cantidad_inscripciones_iniciales", "provincia_id"]
JURISDICCIONES = [f"P{i:02d}" for i in range(23)] + ["Tierra del Fuego"]


# ── 1 · La fuente es el registro, no una cámara ─────────────────────────────
def test_la_fuente_es_el_registro_y_no_una_camara():
    fuente = IND.get("fuente", "")
    assert "DNRPA" in fuente, f"la fuente dejó de ser el registro: {fuente!r}"
    for camara in ("ACARA", "ADEFA", "CAFAM"):
        assert camara not in fuente, (
            f"la fuente pasó a {camara}: las cámaras republican lo que la DNRPA "
            f"registra, y ADEFA mide ventas de fábrica a concesionario, que "
            f"ocurren antes del patentamiento y pueden quedar en stock")


def test_la_card_publica_el_nivel_per_capita_y_no_el_indice():
    """"31 vehículos por cada mil habitantes" dice algo; "142,9 de índice" no.
    Mismo criterio que los kg de carne por habitante en ADR-0217."""
    assert "1.000 habitantes" in IND.get("unidad", ""), IND.get("unidad")
    assert 5 < IND["valor"] < 100, (
        f"{IND['valor']} no es un nivel plausible de vehículos 0km por mil "
        f"habitantes: el máximo histórico de la serie ronda 45")


def test_el_recurso_se_descubre_por_catalogo_y_no_por_url_fija():
    """La dirección de descarga lleva el período adentro y cambia todos los
    meses: fijarla congelaría el indicador en un archivo viejo sin avisar."""
    fuente = (ROOT / "scripts" / "vida_cotidiana" / "collectors"
              / "motorizacion.py").read_text(encoding="utf-8")
    assert "package_show" in fuente
    assert not re.search(r'https?://\S*\d{4}-\d{2}-\d{4}-\d{2}\.csv', fuente), (
        "hay una URL con el período adentro escrita a mano en el colector")


# ── 2 · El colector revienta en vez de publicar una serie recortada ─────────
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


def _correr(monkeypatch, texto_autos, texto_motos=None,
            declarado=("202211", "202607")):
    """Corre el colector contra CSVs sintéticos y una población fija."""
    class _Resp:
        status_code = 200

        def __init__(self, cuerpo):
            self.content = cuerpo.encode("utf-8")

        def raise_for_status(self):
            pass

    textos = {"autos": texto_autos, "motos": texto_motos or texto_autos.replace(
        '"Automotores"', '"Motovehículos"')}
    estado = {"proximo": None}

    def _url(dataset, patron):
        estado["proximo"] = "autos" if "automotores" in dataset else "motos"
        return ("http://falso/x.csv", declarado[0], declarado[1])

    monkeypatch.setattr(_mot, "_url_del_recurso", _url)
    monkeypatch.setattr(_mot, "_fetch_poblacion",
                        lambda: [("2022-01-01", 45_000_000.0),
                                 ("2026-10-01", 47_000_000.0)])
    monkeypatch.setattr(_mot.requests, "get",
                        lambda *a, **k: _Resp(textos[estado["proximo"]]))
    return _mot.fetch_motorizacion()


def test_el_colector_sano_devuelve_card_serie_y_composicion(monkeypatch):
    """La guarda de las guardas: si el CSV falso ya no pasara, los tests de
    abajo estarían comprobando que revienta por el motivo equivocado."""
    d = _correr(monkeypatch, _csv_falso())
    assert d["motorizacion_total"]["fecha"] == "2026-07"
    assert d["motorizacion_total"]["composicion"]["ratio_motos"] > 0
    assert min(d["serie_autos"]) == "2022-11"


def test_revienta_si_falta_una_columna(monkeypatch):
    roto = [c for c in COLUMNAS if c != "tipo_vehiculo"]
    texto = _csv_falso(columnas=roto)
    texto = "\n".join([texto.splitlines()[0]]
                      + [l.split(",", 1)[1] for l in texto.splitlines()[1:]])
    with pytest.raises(ValueError, match="columnas"):
        _correr(monkeypatch, texto, texto)


def test_revienta_si_cambia_el_rotulo_del_universo(monkeypatch):
    """Si la DNRPA renombrara «Automotores» o metiera los dos vehículos en el
    mismo archivo, filtrar en silencio daría cero o el doble sin avisar."""
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


def test_revienta_si_los_dos_registros_no_llegan_al_mismo_mes(monkeypatch):
    """Sumar un mes de autos con uno de motos de otra fecha daría un total con
    una pata corta, y el derrumbe se leería como caída del acceso."""
    autos = _csv_falso()
    motos = _csv_falso(hasta=(2026, 6)).replace('"Automotores"', '"Motovehículos"')
    with pytest.raises(ValueError, match="período|mismo mes"):
        _correr(monkeypatch, autos, motos)


def test_revienta_si_la_fuente_le_cambia_el_rotulo_a_tierra_del_fuego(monkeypatch):
    """La exclusión se aplica por NOMBRE de jurisdicción. Si la DNRPA lo
    cambiara, el artefacto volvería a entrar al índice en silencio — que es
    exactamente el modo de falla que este indicador vino a cerrar."""
    otras = [p for p in JURISDICCIONES if p != "Tierra del Fuego"] + ["T. del Fuego"]
    with pytest.raises(ValueError, match="Tierra del Fuego"):
        _correr(monkeypatch, _csv_falso(jurisdicciones=otras))


# ── 3 · Puntúa el total; autos y motos no vuelven como cards ───────────────
def test_puntua_el_total_y_no_un_vehiculo():
    pesos = {i: interno for d in itvc.DIMENSIONES_ITVC.values()
             for i, interno in d["indicadores"].items()}
    assert "motorizacion_total" in pesos, "el componente dejó de puntuar"
    for viejo in ("patentamiento_autos", "patentamiento_motos"):
        assert viejo not in pesos, (
            f"{viejo} volvió a puntuar por su cuenta: la suba de motos vuelve a "
            f"admitir dos lecturas opuestas y el índice no puede distinguirlas")
    assert IND.get("en_indice") is True
    assert IND.get("peso_efectivo")


def test_el_peso_es_la_suma_de_los_dos_que_reemplaza():
    """0,0196 (motos) + 0,0200 (autos) = 0,0396. Si alguien lo cambia sin un
    ADR, la fusión habría movido el peso del bloque de vehículos de contrabando."""
    ingresos = itvc.DIMENSIONES_ITVC["ingresos"]["indicadores"]
    assert ingresos["motorizacion_total"] == pytest.approx(0.0396)
    # Y los otros tres quedaron intactos, que es lo que hace que el cambio sea
    # sólo del bloque de vehículos.
    assert ingresos["brecha_salario_cbt"] == pytest.approx(0.5959)
    assert ingresos["pobreza_nowcast"] == pytest.approx(0.3253)
    assert ingresos["consumo_carnes_total"] == pytest.approx(0.0392)


def test_autos_y_motos_no_son_cards():
    """ADR-0216: o integra el índice, o no es card. Son los Componentes A y B
    de la matriz, y su valor se lee ahí adentro."""
    for viejo in ("patentamiento_autos", "patentamiento_motos"):
        assert viejo not in VIDA, (
            f"{viejo} se publica como card sin puntuar: es la categoría de "
            f"«indicador de contexto» que ADR-0153 dio de baja")


def test_las_series_de_las_dos_patas_se_siguen_publicando():
    """Dejaron de puntuar, no de existir: son la mitad de la explicación."""
    for pata in ("patentamiento_autos", "patentamiento_motos"):
        assert SERIES.get(pata), f"desapareció la serie de {pata}"


# ── 4 · La matriz A×B explica el color ──────────────────────────────────────
def test_la_matriz_explica_el_color():
    por_que = (IND.get("semaforo") or {}).get("por_que")
    assert por_que, (
        "el componente publica su color sin explicación: es la lectura ambigua "
        "—«subió contra el arranque»— que la matriz A×B vino a desarmar")
    assert "%" in por_que and "motos" in por_que


def test_la_composicion_viaja_colgada_del_indicador():
    """Como las `variaciones` de la carne: si fuera una clave suelta del dict
    sería un indicador fantasma, y si no estuviera la matriz quedaría muda."""
    comp = IND.get("composicion") or {}
    for k in ("autos_12m", "motos_12m", "total_12m", "ratio_motos",
              "ratio_motos_base", "total_var"):
        assert k in comp, f"falta {k} en la composición"
    assert 0 < comp["ratio_motos"] < 100


def test_la_composicion_reconcilia_con_las_series_publicadas():
    """El ratio que dice el texto tiene que poder recalcularse sumando los dos
    gráficos que el informe publica. Si no, el lector que haga la cuenta
    encuentra otro número — y ahí es donde se nota una exclusión aplicada de un
    lado y no del otro."""
    comp = IND["composicion"]
    autos = {p["fecha"][:7]: p["valor"] for p in SERIES["patentamiento_autos"]}
    motos = {p["fecha"][:7]: p["valor"] for p in SERIES["patentamiento_motos"]}
    ult = sorted(set(autos) & set(motos))[-12:]
    assert len(ult) == 12
    a, m = sum(autos[k] for k in ult), sum(motos[k] for k in ult)
    assert abs(m / (a + m) * 100 - comp["ratio_motos"]) < 0.15, (
        f"la matriz dice {comp['ratio_motos']}% de motos y las series "
        f"publicadas dan {m / (a + m) * 100:.1f}%")


# ── 5 · Tierra del Fuego sigue afuera ───────────────────────────────────────
def test_tierra_del_fuego_esta_excluida_y_con_su_motivo_escrito():
    fuente = (ROOT / "scripts" / "vida_cotidiana" / "collectors"
              / "motorizacion.py").read_text(encoding="utf-8")
    assert _mot.JURISDICCION_EXCLUIDA == "Tierra del Fuego"
    assert _mot.ARTEFACTO_TDF == ("2025-04", "2025-11")
    assert "29.005" in fuente, (
        "la exclusión perdió la cifra que la justifica: sin el número, el "
        "próximo que la lea no puede saber si sigue haciendo falta")


def test_la_exclusion_se_nota_en_la_serie_publicada():
    """La prueba de que la exclusión se aplica de verdad y no sólo está escrita:
    en el pico del artefacto, la serie publicada tiene que quedar por DEBAJO de
    lo que la misma fuente informa para el país entero."""
    motos = {p["fecha"][:7]: p["valor"] for p in SERIES["patentamiento_motos"]}
    puente = json.loads((ROOT / "data" / "vida" / "puente_cafam_dnrpa.json")
                        .read_text(encoding="utf-8"))["serie"]
    pico = "2025-10"
    assert motos[pico] < puente[pico] * 0.95, (
        f"en {pico} la serie publicada ({motos[pico]}) no está por debajo del "
        f"total país ({puente[pico]}): la exclusión de Tierra del Fuego dejó "
        f"de aplicarse")


def test_las_tres_series_declaran_la_exclusion_en_su_fuente():
    """Una exclusión que no se ve es una exclusión silenciosa. Va en la línea
    de fuente del CSV, que es lo que termina en el modal."""
    with open(ROOT / "output" / "series" / "vida_cotidiana.csv",
              encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    for ind in ("motorizacion_total", "patentamiento_autos", "patentamiento_motos"):
        fuentes = {r["fuente"] for r in filas if r["indicador"] == ind}
        assert len(fuentes) == 1, f"{ind} declara varias fuentes: {fuentes}"
        fuente = fuentes.pop()
        assert "DNRPA" in fuente, f"{ind}: {fuente}"
        assert "sin Tierra del Fuego" in fuente, (
            f"{ind} no declara la exclusión en su fuente: {fuente}")


# ── 6 · El puente entre CAFAM y la DNRPA ────────────────────────────────────
def test_el_cambio_de_fuente_no_movio_el_numero():
    """ADR-0224 mudó las motos de CAFAM a la DNRPA para poder excluir Tierra del
    Fuego. Un cambio de fuente en un componente que puntúa se VERIFICA.

    Fuera del período del artefacto las dos fuentes tienen que dar lo mismo: es
    la cámara republicando el registro, con su día de corte. Dentro, tienen que
    separarse — y esa separación es la exclusión funcionando.
    """
    puente = json.loads((ROOT / "data" / "vida" / "puente_cafam_dnrpa.json")
                        .read_text(encoding="utf-8"))["serie"]
    motos = {p["fecha"][:7]: p["valor"] for p in SERIES["patentamiento_motos"]}
    a0, a1 = _mot.ARTEFACTO_TDF

    fuera = [(k, motos[k] / puente[k]) for k in sorted(set(motos) & set(puente))
             if not (a0 <= k <= a1)]
    assert len(fuera) >= 30, f"sólo {len(fuera)} meses para comparar"
    peor = max(fuera, key=lambda x: abs(x[1] - 1))
    assert abs(peor[1] - 1) < 0.02, (
        f"CAFAM y la DNRPA se separaron {abs(peor[1] - 1) * 100:.1f}% en "
        f"{peor[0]}: las dos fuentes dejaron de medir lo mismo y el puente "
        f"entre la serie vieja y la nueva ya no se sostiene")

    dentro = [motos[k] / puente[k] for k in sorted(set(motos) & set(puente))
              if a0 <= k <= a1]
    assert min(dentro) < 0.95, (
        "dentro del período del artefacto la serie publicada no se separa del "
        "total país: la exclusión de Tierra del Fuego no está haciendo nada")


# ── 7 · La excepción al techo, y que siga siendo una excepción ─────────────
def test_el_componente_entra_sin_recortar():
    serie = SERIES.get("motorizacion_total") or []
    assert serie, "sin serie publicada"
    ultimo = serie[-1]["valor"]
    puntaje = IND.get("puntaje_itvc") or IND.get("indice_itvc")
    assert puntaje == pytest.approx(ultimo, abs=0.11), (
        f"el índice publica {puntaje} y la serie termina en {ultimo}")
    if ultimo > itvc.WINSOR_TOPE:
        assert puntaje > itvc.WINSOR_TOPE, (
            f"el componente está exento del techo y sin embargo se publicó "
            f"recortado a {puntaje}")


def test_la_excepcion_al_techo_esta_acotada_a_un_componente():
    """Lo más delicado del cambio: el techo de 140 está declarado en la ficha
    del ITCIS y rige para todos. Si esta lista crece sin un ADR, la excepción se
    volvió el permiso general que expresamente no quiso ser."""
    assert itvc.WINSOR_EXENTOS == frozenset({"motorizacion_total"}), (
        f"la exención dejó de estar acotada a un componente: {itvc.WINSOR_EXENTOS}")


def test_el_indice_vivo_y_la_reconstruccion_eximan_a_los_mismos():
    """Si divergen, la serie histórica del ITCIS deja de ser el índice que se
    publica — que es justo lo que la reconstrucción existe para poder afirmar."""
    assert validacion_externa.TECHO_EXENTOS == itvc.WINSOR_EXENTOS
    assert validacion_externa.ITVC_TECHO == itvc.WINSOR_TOPE


def test_la_excepcion_tiene_sus_dos_argumentos_medidos_escritos():
    """No alcanza con eximir: el motivo tiene que estar donde se lee el código,
    o el próximo que lo mire sólo ve un `if` que perdona a un componente."""
    bloque = ITVC_PY.split("WINSOR_EXENTOS")[0].split("WINSOR_TOPE")[-1]
    assert "0,33 puntos" in bloque, "falta el argumento del peso"
    assert "64%" in bloque, "falta el argumento de la base deprimida"
    assert "propio ADR" in bloque, (
        "falta decir que el problema del techo es más grande que este "
        "componente y que acá no se resuelve")


# ── 8 · Serie, base y frescura ──────────────────────────────────────────────
def test_la_serie_llega_al_4t_2023_con_ventanas_moviles_completas():
    """No alcanza con tocar el 4T-2023: el rebase compara ventanas de DOCE meses
    que terminan en oct, nov y dic de 2023, así que las series crudas tienen que
    empezar once meses antes (nov-2022) y no tener huecos."""
    for pata in ("patentamiento_autos", "patentamiento_motos"):
        meses = [p["fecha"][:7] for p in SERIES[pata]]
        assert meses[0] <= "2022-11", (
            f"{pata} arranca en {meses[0]}: las ventanas móviles de la base "
            f"quedan incompletas")
        a0, m0 = int(meses[0][:4]), int(meses[0][5:7])
        af, mf = int(meses[-1][:4]), int(meses[-1][5:7])
        assert (af * 12 + mf) - (a0 * 12 + m0) + 1 == len(meses), f"{pata} tiene huecos"
    idx = [p["fecha"][:7] for p in SERIES["motorizacion_total"]]
    for base in BASE_4T:
        assert base in idx, f"el índice no llega a {base}"


def test_la_serie_ya_llega_rebaseada_y_no_se_re_rebasea():
    """Entra por SERIES_REBASEADAS, como la de carnes: `itvc.py` toma su último
    punto sin transformarlo. Si alguien la moviera a los rebases normales, el
    componente se rebasearía dos veces y quedaría clavado en 100."""
    assert itvc.SERIES_REBASEADAS.get("motorizacion_total") == "motorizacion_total"
    assert 'idx["motorizacion_total"]' not in ITVC_PY, (
        "el componente se arma dos veces: por SERIES_REBASEADAS y a mano")
    base = [p["valor"] for p in SERIES["motorizacion_total"]
            if p["fecha"][:7] in BASE_4T]
    assert abs(mean(base) - 100.0) < 0.15, (
        f"el promedio del 4T-2023 da {mean(base):.2f} y tiene que dar 100: la "
        f"serie no está rebaseada contra la base del índice")


def test_el_tope_de_frescura_esta_puesto_y_es_el_medido():
    """El default de 110 días no avisaría nunca de un mes salteado: la DNRPA
    publica el mes M entre el día 1 y el 4 de M+1 (medido sobre el historial del
    catálogo), así que la card nunca pasa de ~72 días."""
    import gate_calidad
    assert gate_calidad.MAX_DIAS.get("motorizacion_total") == 90


def test_card_y_serie_estan_en_unidades_distintas_y_el_gate_lo_sabe():
    """La card publica el nivel per cápita y la serie el índice base-100. No
    pueden coincidir por construcción, así que el par tiene que estar declarado
    en G3 — o el gate bloquea la publicación todos los días."""
    import gate_calidad
    assert "motorizacion_total" in gate_calidad.G3_EXCEPCIONES
