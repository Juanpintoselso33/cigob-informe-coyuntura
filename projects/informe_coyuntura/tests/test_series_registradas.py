"""Todo indicador publicado con valor numérico tiene que tener su serie
registrada en descargar_series.py -- si falta, la card sale sin sparkline y sin
histórico descargable, y nada avisa.

Lo encontró una auditoría de UI (29-jul-2026) por el síntoma visual: de las 25
filas de indicador de la home, `alquiler_real` era la única sin sparkline. No era
un problema de front: su serie tenía UN punto —el valor del día— cuando la regla
del proyecto pide backfill desde dic-2023. Al medir el invariante apareció un
segundo caso idéntico, `indice_lider`, que además puntúa (13% de la dimensión
empleo del ITVC).

Los dos tenían un pariente con historia (`itvc_alquiler`, `itvc_lider`) y ahí
estaba la trampa: parecía que la serie existía. Pero esos son los componentes
REBASEADOS del ITVC (100 = 4T-2023) y las cards publican otra cosa —variación
mensual y nivel—, así que no son intercambiables.

Ningún gate cubría esto: gate_calidad.py compara card contra serie sólo cuando
la serie EXISTE (G3), y si no existe no tiene con qué comparar. Este test cierra
la clase de bug, no los dos casos puntuales.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import descargar_series as ds

INFORME = json.loads((ROOT / "web/src/data/informe.json").read_text(encoding="utf-8-sig"))

# Indicadores cuya serie NO se registra acá, con el motivo. Sumar una clave a
# esta lista es una decisión explícita, no un olvido.
SIN_SERIE_A_PROPOSITO: dict[str, str] = {}


def _registradas() -> set:
    """El registro autoritativo es el que resuelve `--indicador` en el CLI."""
    nombres = set()
    for indec, bcra, derivadas in ds.CINTURONES_SERIES.values():
        nombres |= ds._nombres_de(indec, bcra, derivadas)
    return nombres


def _publicados_numericos() -> list:
    out = []
    for ckey, c in INFORME["cinturones"].items():
        for ikey, ind in (c.get("indicadores") or {}).items():
            if isinstance(ind.get("valor"), (int, float)):
                out.append((ckey, ikey))
    return out


def test_todo_indicador_numerico_tiene_serie_registrada():
    registradas = _registradas()
    faltan = [f"{ck}/{ik}" for ck, ik in _publicados_numericos()
              if ik not in registradas and ik not in SIN_SERIE_A_PROPOSITO]
    assert not faltan, (
        "sin serie registrada en descargar_series.py (card sin sparkline ni "
        f"histórico): {faltan}. Si es a propósito, declararlo en "
        "SIN_SERIE_A_PROPOSITO con el motivo.")


def test_los_dos_casos_de_la_auditoria_quedan_cubiertos():
    """Regresión explícita: son los que motivaron el test."""
    registradas = _registradas()
    assert "alquiler_real" in registradas
    assert "indice_lider" in registradas


def test_el_componente_rebaseado_no_reemplaza_a_la_card():
    """La trampa del caso: `itvc_*` tiene historia pero es OTRA escala.

    Las dos claves tienen que estar registradas por separado; si alguien borra
    la de la card pensando que el componente del ITVC ya la cubre, vuelve el bug.
    """
    registradas = _registradas()
    for card, componente in (("alquiler_real", "itvc_alquiler"),
                             ("indice_lider", "itvc_lider")):
        assert card in registradas and componente in registradas, (
            f"{card} y {componente} miden cosas distintas (variación/nivel vs "
            "índice rebaseado a 4T-2023): las dos series van registradas")
