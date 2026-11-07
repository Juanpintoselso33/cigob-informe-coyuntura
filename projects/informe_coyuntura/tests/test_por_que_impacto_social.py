"""Toda tarjeta del cinturón de impacto social explica su color.

Revisión de Luis (7-nov-2026): la ocupación —la tarjeta más pesada del
cinturón— salía en amarillo sin el «por qué», y lo mismo 13 de las 19. Los
componentes que puntúan como índice base-100 no tienen tramos en su unidad, así
que la frase se arma en la escala del cinturón, con los mismos cortes que el
color.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import parametrica  # noqa: E402
import publicar  # noqa: E402

SNAPSHOT = json.loads((RAIZ / "web/src/data/informe.json").read_text(encoding="utf-8"))


def test_toda_tarjeta_social_que_puntua_explica_su_color():
    informe = copy.deepcopy(SNAPSHOT)
    publicar._semaforos(informe)
    sin = [k for k, i in informe["cinturones"]["vida_cotidiana"]["indicadores"].items()
           if i.get("semaforo") and i.get("en_indice") and not i["semaforo"].get("por_que")]
    assert not sin, f"tarjetas sin «por qué»: {sin}"


@pytest.mark.parametrize("indice", [84.9, 85.0, 94.9, 95.0, 104.0, 104.99, 105.0, 122.3])
def test_la_frase_nombra_el_mismo_color_que_el_semaforo(indice):
    color = parametrica.color_de_indice_base100(indice)
    frase = publicar._por_que_indice_base100(color, indice)
    assert f"está en {color.capitalize()}" in frase
    vecino = frase.split("límite con ")[1].split(" ")[0].lower()
    assert vecino != color


@pytest.mark.parametrize("carga,transporte", [(13.0, 49.0), (16.0, 50.0), (14.0, 60.0),
                                              (20.0, 20.0), (9.0, 40.0), (17.0, 55.0)])
def test_tarifas_la_frase_y_el_color_salen_de_la_misma_cuenta(carga, transporte):
    """Revisión de Luis (7-nov-2026): el transporte en 6,4% parecía pasado de un
    «límite» de 5% estando en verde. La frase nombra el rubro que manda y el
    color que dice tiene que ser el del índice."""
    import itvc
    color = parametrica.color_de_indice_base100(itvc.indice_asequibilidad_tarifas(carga, transporte))
    assert f"está en {color.capitalize()}" in publicar._por_que_tarifas(color, carga, transporte)


def test_la_card_de_tarifas_no_llama_limite_a_la_referencia():
    informe = copy.deepcopy(SNAPSHOT)
    publicar._semaforos(informe)
    tarifas = informe["cinturones"]["vida_cotidiana"]["indicadores"]["peso_tarifas"]
    assert tarifas["semaforo"]["por_que"].startswith(("El transporte", "Agua y energía"))


@pytest.mark.parametrize("peso,web", [(0.1125, "11,3"), (0.0825, "8,3"), (0.0705, "7"), (0.0115, "1,2")])
def test_el_peso_se_redondea_como_la_web(peso, web):
    """Los valores de `web` son los de Intl.NumberFormat('es-AR',
    {maximumFractionDigits: 1}).format(peso * 100), que es como lo muestra la
    tarjeta. 11,25 salía 11,2 en la fórmula y 11,3 en la tarjeta (Luis, 7-nov);
    7,0499… y 1,15 los encontró Codex el mismo día."""
    sys.path.insert(0, str(RAIZ / "scripts" / "fichas"))
    from comun import coma
    assert publicar.pct_peso(peso).removesuffix(",0") == web
    assert coma(peso * 100, 1) == web


@pytest.mark.parametrize("carga,transporte", [(14.1, 50.0), (14.0, 50.0)])
def test_en_el_borde_la_frase_no_redondea_hacia_el_otro_color(carga, transporte):
    """Codex, 7-nov: con 7,05 % redondeado a 7,0 la frase decía «7,0 está en
    Amarillo» con el verde «hasta 7 %»."""
    import itvc
    color = parametrica.color_de_indice_base100(itvc.indice_asequibilidad_tarifas(carga, transporte))
    frase = publicar._por_que_tarifas(color, carga, transporte)
    assert "a 0,0 del" not in frase or carga * transporte / 100 == 7.0
