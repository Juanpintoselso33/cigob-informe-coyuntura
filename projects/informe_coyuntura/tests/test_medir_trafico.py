"""Medición mensual del tráfico (ADR-0440): fechas, cambios del mes e informe."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import medir_trafico as mt  # noqa: E402


def test_rango_y_mes_anterior():
    assert mt.rango_del_mes("2026-02") == ("2026-02-01", "2026-02-28")
    assert mt.rango_del_mes("2028-02") == ("2028-02-01", "2028-02-29")
    assert mt.mes_anterior("2027-01") == "2026-12"
    assert mt.mes_anterior("2026-11") == "2026-10"


def test_cambios_del_mes_solo_presentacion():
    cambios = mt.cambios_del_mes("2026-11")
    assert any(c.startswith("ADR-0439") for c in cambios)
    # Un ADR de cálculo de noviembre no es un cambio del sitio.
    assert not any(c.startswith("ADR-0427") for c in cambios)


def _datos(usuarios, enviados):
    return {
        "mes": "2026-11",
        "totales": {"activeUsers": usuarios, "newUsers": usuarios, "sessions": usuarios * 2,
                    "screenPageViews": usuarios * 4, "engagementRate": 0.5},
        "origenes": [
            {"sessionSource": "(direct)", "sessionMedium": "(none)", "sessionCampaignName": "(direct)",
             "sessions": 10, "activeUsers": 5, "engagementRate": 0.5},
            {"sessionSource": "chatgpt.com", "sessionMedium": "ai-assistant", "sessionCampaignName": "",
             "sessions": 3, "activeUsers": 2, "engagementRate": 0.75},
        ],
        "paginas": [{"pagePath": "/", "screenPageViews": 10, "activeUsers": 5}],
        "eventos": {"muro_visto": {"veces": 20, "usuarios": 10},
                    "muro_enviado": {"veces": enviados, "usuarios": enviados}},
        "busqueda": {"https://monitor.cigob.org/": None},
        "cambios": [],
    }


def test_informe_compara_con_el_mes_anterior_y_cuenta_el_muro():
    md = mt.informe_md(_datos(200, 2), _datos(100, 1))
    assert "| Usuarios | 200 (+100%) | 100 |" in md
    assert "IA · chatgpt.com" in md
    assert "Directo (sin dato de origen)" in md
    assert "2 de 10 personas que lo vieron dejaron el mail (20%)" in md
    assert "no tiene acceso a esta propiedad" in md
    assert "Ningún cambio de presentación" in md
    assert md.count("\n1. ") == 1  # las preguntas fijas a la IA, numeradas


def test_informe_sin_mes_anterior():
    md = mt.informe_md(_datos(50, 0), None)
    assert "| Usuarios | 50 |  |" in md


class _Resp:
    def __init__(self, cuerpo):
        self._c = cuerpo

    def json(self):
        return self._c


def test_un_403_por_cuota_no_pasa_por_falta_de_acceso():
    cuota = {"error": {"code": 403, "message": "Quota exceeded", "errors": [{"reason": "quotaExceeded"}]}}
    permiso = {"error": {"code": 403, "message": "User does not have sufficient permission for site",
                         "errors": [{"reason": "forbidden"}]}}
    assert mt._sin_permiso(_Resp(cuota)) is False
    assert mt._sin_permiso(_Resp(permiso)) is True
