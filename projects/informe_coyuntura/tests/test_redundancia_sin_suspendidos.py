"""Hallazgo Codex (gestión #1): la matriz de redundancia del ITCG incluía
indicadores suspendidos (masa_salarial, reestructuracion_organismos) que el
índice excluye, y publicaba estadísticas de un índice que no es el publicado.
Los componentes ahora salen de `parametrica.indicadores_vigentes`, igual que en
ITVC e ITCP; rigi_inversiones sigue fuera de la reconstrucción (ADR-0086)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import itcg
import itcp
import itvc
import parametrica
import validacion_externa as ve


def _vigentes(dims, susp):
    return {i for d in parametrica.indicadores_vigentes(dims, susp).values() for i in d}


def test_itcg_series_son_los_componentes_vigentes_del_indice():
    assert set(ve.ITCG_SERIES) == _vigentes(itcg.DIMENSIONES_ITCG, itcg.INDICADORES_SUSPENDIDOS)
    for susp in itcg.INDICADORES_SUSPENDIDOS:
        assert susp not in ve.ITCG_SERIES


def test_la_matriz_de_gestion_no_puntua_suspendidos(monkeypatch):
    captura = {}

    def falsa(escala, dimensiones, valores, por_diseno, umbral):
        captura["dims"] = dimensiones
        return {}

    monkeypatch.setattr(ve, "matriz_redundancia", falsa)
    monkeypatch.setattr(ve, "_valores_itcg_por_mes", lambda: {})
    ve.matriz_redundancia_itcg()
    en_matriz = {i for d in captura["dims"].values() for i in d["indicadores"]}
    assert en_matriz == _vigentes(itcg.DIMENSIONES_ITCG, itcg.INDICADORES_SUSPENDIDOS)
    assert not en_matriz & set(itcg.INDICADORES_SUSPENDIDOS)


def test_valores_itcg_no_trae_suspendidos_ni_rigi(monkeypatch):
    serie = [{"fecha": "2024-01-01", "valor": 1.0}, {"fecha": "2024-02-01", "valor": 2.0}]
    monkeypatch.setattr(ve, "cargar_series", lambda: {k: serie for k in ve.ITCG_SERIES + ["rigi_inversiones",
                                                      "masa_salarial", "reestructuracion_organismos"]})
    claves = set(next(iter(ve._valores_itcg_por_mes().values())))
    assert "rigi_inversiones" not in claves
    assert not claves & set(itcg.INDICADORES_SUSPENDIDOS)


def test_itvc_e_itcp_ya_derivan_de_los_vigentes():
    """Los otros cinturones con suspendidos tienen que seguir sin tener el defecto."""
    assert not set(ve.ITCP_SERIES) & set(itcp.INDICADORES_SUSPENDIDOS)
    vivos_itvc = _vigentes(itvc.DIMENSIONES_ITVC, itvc.INDICADORES_SUSPENDIDOS)
    assert not vivos_itvc & set(itvc.INDICADORES_SUSPENDIDOS)
