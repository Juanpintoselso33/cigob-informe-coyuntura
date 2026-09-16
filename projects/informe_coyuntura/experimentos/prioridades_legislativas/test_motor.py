import copy
import pytest
from motor import calcular


def item(id="a", estado="sancionado", peso=1):
    return {"id": id, "nombre": id, "peso": peso, "prioridad_desde": "2026-01-01",
            "fuente_prioridad": "simulado", "verificado_hasta": "2026-09-08",
            "eventos": [{"fecha": "2026-02-01", "estado": estado, "fuente": "simulado"}]}


def test_fecha_no_anticipa_sancion():
    a = item()
    a["eventos"].insert(0, {"fecha": "2026-01-01", "estado": "presentado", "fuente": "simulado"})
    assert calcular([a], "2026-01-31")["porcentaje"] == 0
    assert calcular([a], "2026-02-01")["porcentaje"] == 100


def test_sin_universo_no_es_cero():
    assert calcular([], "2026-09-08")["porcentaje"] is None
    assert calcular([item()], "2025-12-31")["estado"] == "sin_universo"


def test_faltantes_conservan_denominador_y_dan_limites():
    b = item("b", "presentado"); b["verificado_hasta"] = "2026-08-01"
    r = calcular([item(), b], "2026-09-08")
    assert (r["porcentaje"], r["minimo"], r["maximo"], r["cobertura"]) == (None, 50, 100, 50)


@pytest.mark.parametrize("estado", ["presentado", "media_sancion", "rechazado", "retirado"])
def test_solo_sancion_definitiva_cuenta(estado):
    r = calcular([item(), item("b", estado)], "2026-09-08")
    assert r["porcentaje"] == 50 and r["denominador"] == 2


def test_pesos_sensibilidad_sin_alterar_entradas():
    portfolio = [item(peso=3), item("b", "presentado")]
    before = copy.deepcopy(portfolio)
    assert calcular(portfolio, "2026-09-08")["porcentaje"] == 75
    assert before == portfolio


@pytest.mark.parametrize("peso", [0, -1, float("nan"), float("inf"), True])
def test_peso_invalido(peso):
    with pytest.raises(ValueError): calcular([item(peso=peso)], "2026-09-08")


def test_duplicados_rechazados():
    with pytest.raises(ValueError): calcular([item(), item()], "2026-09-08")


def test_cronologia_y_fuentes():
    a = item(); a["eventos"][0]["fecha"] = "2025-12-31"
    with pytest.raises(ValueError): calcular([a], "2026-09-08")
    a = item(); a["eventos"][0]["fuente"] = ""
    with pytest.raises(ValueError): calcular([a], "2026-09-08")


def test_lectura_posterior_al_corte_verificado_es_desconocida():
    assert calcular([item(estado="presentado")], "2026-09-10")["porcentaje"] is None


def test_sancion_historica_no_caduca_por_falta_de_revision():
    assert calcular([item()], "2026-09-10")["porcentaje"] == 100


def test_cambiar_orden_no_cambia_resultado():
    a, b = item(), item("b", "presentado")
    assert calcular([a,b], "2026-09-08")["porcentaje"] == calcular([b,a], "2026-09-08")["porcentaje"]


def test_documentado_sin_avance_no_es_desconocido():
    # Sin evento aplicable pero con el período ya revisado hasta el corte:
    # es un cero conocido (issue #27, punto 1), no una banda 0-100.
    a = item()  # evento sancionado el 2026-02-01, verificado_hasta 2026-09-08
    r = calcular([a], "2026-01-15")
    assert r["filas"][0]["estado"] == "sin_avance"
    assert (r["porcentaje"], r["cobertura"], r["estado"]) == (0, 100, "calculable")


def test_retirado_y_rechazado_no_cuentan_como_posible_ley():
    # Terminales negativos son absorbentes como la sanción: no vuelven a
    # "sin_verificar" ni inflan el máximo (issue #27, punto 2).
    a = item()
    b = item("b", "retirado"); b["verificado_hasta"] = "2026-08-01"
    c = item("c", "rechazado"); c["verificado_hasta"] = "2026-08-01"
    r = calcular([a, b, c], "2026-09-08")
    assert {f["id"]: f["estado"] for f in r["filas"]} == {"a": "sancionado", "b": "retirado", "c": "rechazado"}
    assert r["minimo"] == pytest.approx(33.33, abs=0.01)
    assert r["maximo"] == pytest.approx(33.33, abs=0.01)


@pytest.mark.parametrize("clave", ["eventos", "nombre", "prioridad_desde", "verificado_hasta"])
def test_cartera_malformada_da_valueerror_no_keyerror(clave):
    # Contrato de los 18 tests: cualquier malformación es ValueError,
    # nunca un KeyError que se escapa (issue #27, punto 5).
    a = item()
    del a[clave]
    with pytest.raises(ValueError):
        calcular([a], "2026-09-08")
