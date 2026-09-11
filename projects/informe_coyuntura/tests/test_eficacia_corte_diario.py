"""La tarjeta no anticipa una sanción que la historia todavía excluye."""
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica
import descargar_series


def test_sancion_futura_no_se_computa_en_tarjeta_ni_historia(monkeypatch):
    hoy = date.today()
    publicado = (hoy - timedelta(days=500)).isoformat()
    proyectos = [
        {'PROYECTO_ID': f'HCDN{i}', 'TIPO': 'MENSAJE Y PROYECTO DE LEY',
         'EXP_DIPUTADOS': f'{i:04d}-PE-2025', 'PUBLICACION_FECHA': publicado}
        for i in (1, 2)
    ]
    leyes = [
        {'PROYECTO_ID': 'HCDN1', 'SANCION_DEFINITIVA': hoy.isoformat()},
        {'PROYECTO_ID': 'HCDN2',
         'SANCION_DEFINITIVA': (hoy + timedelta(days=1)).isoformat()},
    ]
    monkeypatch.setattr(politica, '_hcdn_paginate',
                        lambda rid, **kw: proyectos if rid == politica.HCDN_PROYECTOS_RID else leyes)
    tarjeta = politica.fetch_eficacia_legislativa()
    serie = descargar_series.fetch_eficacia_serie()
    assert tarjeta['aprobados_n'] == 1
    assert tarjeta['enviados_n'] == 2
    assert tarjeta['valor'] == serie[-1][1] == 50.0
