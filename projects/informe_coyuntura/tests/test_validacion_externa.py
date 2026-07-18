"""Regresiones offline para la reconstrucción externa del ITCM."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validacion_externa


def test_carga_itcm_prioriza_csv_fresco_y_preserva_historico(monkeypatch, tmp_path):
    snapshot = tmp_path / "series.json"
    snapshot.write_text(json.dumps({
        "idm": [{"fecha": "2023-12-01", "valor": 1.0}],
        "presion_dolarizacion": [{"fecha": "2023-12-01", "valor": -99.0}],
    }), encoding="utf-8")
    monkeypatch.setattr(validacion_externa, "SERIES", snapshot)
    monkeypatch.setattr(validacion_externa.publicar, "build_series", lambda: {
        "presion_dolarizacion": [
            {"fecha": "2023-12-01", "valor": -2.0},
            {"fecha": "2024-01-01", "valor": 1.5},
        ],
    })

    series = validacion_externa._cargar_series_itcm()

    assert series["idm"] == [{"fecha": "2023-12-01", "valor": 1.0}]
    assert series["presion_dolarizacion"][-1] == {
        "fecha": "2024-01-01",
        "valor": 1.5,
    }


def test_reconstruccion_itcm_incluye_dolarizacion(monkeypatch):
    monkeypatch.setattr(validacion_externa, "_cargar_series_itcm", lambda: {
        "ipc_total": [{"fecha": "2023-12-01", "valor": 25.5}],
        "presion_dolarizacion": [{"fecha": "2023-12-01", "valor": -2.0}],
    })
    recibidos = []

    def calcular(valores):
        recibidos.append(valores)
        return {"valor": 42.0}

    monkeypatch.setattr(validacion_externa.itcm, "calcular_itcm", calcular)

    assert validacion_externa.construir_serie_itcm() == {"2023-12": 42.0}
    assert recibidos == [{
        "ipc_total": 25.5,
        "rem_ipc_12m": None,
        "saldo_comercial_12m": None,
        "idm": None,
        "presion_dolarizacion": -2.0,
        "recaudacion": None,
        "reservas_bcra": None,
        "idc": None,
        "credito_privado": None,
        "emae_ia": None,
        "ipi_manufacturero": None,
        "tcrm": None,
        "costo_financiamiento_tesoro": None,
        "resultado_primario": None,
    }]


def test_reconstruccion_itcp_mascara_de_era_para_eficacia(monkeypatch, tmp_path):
    # ADR-0070: eficacia_legislativa se excluye de la reconstrucción hasta
    # nov-2025 inclusive (cohorte madura 12-24m 100% de la era actual recién
    # desde dic-2025); desde dic-2025 entra con su valor
    snapshot = tmp_path / "series.json"
    snapshot.write_text(json.dumps({
        "eficacia_legislativa": [
            {"fecha": "2025-11-01", "valor": 30.0},
            {"fecha": "2025-12-01", "valor": 25.0},
        ],
        "votometro_ventaja_lla": [
            {"fecha": "2025-11-01", "valor": 5.0},
            {"fecha": "2025-12-01", "valor": 6.0},
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(validacion_externa, "SERIES", snapshot)
    recibidos = {}

    def calcular(valores):
        if all(v is None for v in valores.values()):
            return None   # como el motor real: sin ningún indicador no hay índice
        recibidos[len(recibidos)] = dict(valores)
        return {"valor": 50.0, "dimensiones": {"x": {"peso": 1.0}}}

    monkeypatch.setattr(validacion_externa.itcp, "calcular_itcp", calcular)

    serie = validacion_externa.construir_serie_itcp()

    assert set(serie) == {"2025-11", "2025-12"}
    por_mes = {"2025-11": recibidos[0], "2025-12": recibidos[1]}
    assert por_mes["2025-11"]["eficacia_legislativa"] is None   # enmascarada
    assert por_mes["2025-12"]["eficacia_legislativa"] == 25.0   # cohorte 100% era
    # bloqueo_sostenido integra la reconstrucción (ADR-0069)
    assert "bloqueo_sostenido" in por_mes["2025-12"]


# ── Guardia estructural de la reconstrucción del ITCM ────────────────────────

def test_todo_indicador_del_itcm_con_serie_entra_a_la_reconstruccion():
    """La reconstrucción histórica arma sus valores desde una lista escrita a
    mano. Ya se coló un error por ahí: cuando entraron costo_financiamiento y
    resultado_primario, la lista quedó vieja y la validación externa se fue
    quedando atrás del índice EN SILENCIO — ningún gate lo detectaba, se
    descubrió por auditoría.

    Este test lo vuelve ruidoso: si un indicador del ITCM tiene serie mensual
    publicada pero no entra a la reconstrucción, falla acá y no seis meses
    después. Las excepciones son explícitas y hay que justificarlas.
    """
    import itcm
    sin_serie = {"iai", "icip"}          # no tienen serie histórica publicada
    del_indice = {ind for d in itcm.DIMENSIONES_ITCM.values() for ind in d["indicadores"]}

    series = json.loads(validacion_externa.SERIES.read_text(encoding="utf-8"))
    con_serie = {k for k in del_indice - sin_serie if series.get(k)}

    valores = validacion_externa._valores_itcm_por_mes()
    assert valores, "la reconstrucción no produjo ningún mes"
    vistos = set().union(*(v.keys() for v in valores.values()))

    faltan = con_serie - vistos
    assert not faltan, (
        f"indicadores del ITCM con serie que la reconstrucción ignora: {sorted(faltan)}. "
        f"Agregalos en _valores_itcm_por_mes() o declaralos como excepción.")


def test_la_matriz_puntua_con_la_misma_escala_que_el_indice():
    """Bug encontrado por auditoría externa (18-jul-2026): la matriz de
    redundancia puntuaba TODO por bandas, pero el motor usa anclas explícitas
    para presion_dolarizacion, y no coinciden (valor 75 → 10 por bandas, 35 por
    anclas). La matriz correlacionaba un puntaje que el índice nunca usa,
    contradiciendo la premisa declarada de ADR-0075.

    Este test compara, para cada indicador con anclas, el puntaje que produce
    la matriz contra el que produce el motor.
    """
    import itcm
    import parametrica

    assert itcm.ANCLAS_ITCM, "sin anclas explícitas este test no prueba nada"
    for ind, anclas in itcm.ANCLAS_ITCM.items():
        for valor in (0.0, 25.0, 50.0, 75.0, 100.0):
            del_motor = parametrica.puntaje_de(valor, ind, itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM)
            por_anclas = parametrica.puntaje_desde_anclas(valor, anclas)
            assert del_motor == por_anclas, (ind, valor, del_motor, por_anclas)

    # y que efectivamente difieran de las bandas: si coincidieran, el test de
    # arriba pasaría por casualidad y no protegería nada
    ind = next(iter(itcm.ANCLAS_ITCM))
    difieren = any(
        parametrica.puntaje_de(v, ind, itcm.BANDAS_ITCM, itcm.ANCLAS_ITCM)
        != parametrica.puntaje_interpolado(v, itcm.BANDAS_ITCM[ind])
        for v in (25.0, 50.0, 75.0))
    assert difieren, f"{ind}: anclas y bandas dan lo mismo, el test no protege nada"


def test_una_serie_constante_no_tumba_la_validacion():
    """Bug encontrado por la auditoría de código: statistics.correlation lanza
    StatisticsError si alguna serie es constante, y _pearson la llamaba sin
    guarda. Un solo par no calculable abortaba la corrida ENTERA y dejaba sin
    actualizar el snapshot publicado.

    Es alcanzable, no teórico: _pearson exige apenas 6 meses en común, y varios
    indicadores pasan más del 60% de los meses saturados en un extremo de su
    banda."""
    constante = {f"2025-{m:02d}": 10.0 for m in range(1, 9)}
    variable = {f"2025-{m:02d}": float(m) for m in range(1, 9)}

    r, n = validacion_externa._pearson(constante, variable)
    assert r is None and n == 8, (r, n)

    r, n = validacion_externa._pearson(constante, constante)
    assert r is None and n == 8, (r, n)

    # el caso normal sigue devolviendo un número
    r, n = validacion_externa._pearson(variable, variable)
    assert r == 1.0 and n == 8, (r, n)


def test_la_matriz_sobrevive_a_un_componente_saturado(monkeypatch):
    """El par no calculable se omite y los otros se calculan igual."""
    real = validacion_externa._valores_itcm_por_mes

    def con_saturado():
        vals = real()
        for v in vals.values():
            if "tcrm" in v and v["tcrm"] is not None:
                v["tcrm"] = 50.0        # nivel fijo → puntaje constante
        return vals

    monkeypatch.setattr(validacion_externa, "_valores_itcm_por_mes", con_saturado)
    m = validacion_externa.matriz_redundancia_itcm()
    assert m["n_pares"] > 0, "la matriz quedó vacía"
    assert "tcrm" not in m["matriz"], "un componente constante no debería tener pares"


def test_los_pares_acoplados_por_diseno_estan_marcados():
    """Los dos pares con mayor correlación del ITCM lo están POR CONSTRUCCIÓN:
    el REM es un pronóstico del IPC, y el IdC y el crédito privado se arman
    sobre los mismos depósitos y préstamos. Publicarlos junto a los demás
    induce a leer como defecto lo que es diseño.

    Este test verifica que sigan marcados: si alguien renombra un indicador y
    la clave del diccionario deja de coincidir, la marca desaparecería en
    silencio y la card volvería a encabezarse con dos falsos hallazgos."""
    m = validacion_externa.matriz_redundancia_itcm()
    por_diseno = {frozenset((p["a"], p["b"])) for p in m["pares_altos"] if p["por_diseno"]}
    assert frozenset(("ipc_total", "rem_ipc_12m")) in por_diseno
    assert frozenset(("credito_privado", "idc")) in por_diseno
    for p in m["pares_altos"]:
        if p["por_diseno"]:
            assert isinstance(p["por_diseno"], str) and len(p["por_diseno"]) > 30, (
                "el motivo del acoplamiento tiene que estar explicado, no ser un booleano")


def test_los_pares_no_explicados_excluyen_los_de_diseno():
    """El número que encabeza la conclusión pública: acoplados, de dimensiones
    distintas y sin razón de diseño."""
    m = validacion_externa.matriz_redundancia_itcm()
    esperado = sum(1 for p in m["pares_altos"]
                   if not p["misma_dimension"] and not p["por_diseno"])
    assert m["pares_no_explicados"] == esperado
    assert m["pares_no_explicados"] <= m["pares_cruzados"]
