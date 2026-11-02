"""ADR-0365: juicios entrados en primera instancia de la Justicia Nacional del
Trabajo (Capital), 12 meses contra los 12 previos, por semestre."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gestion  # noqa: E402
import itcg  # noqa: E402

# CSV real de la Oficina de Estadísticas: 1er semestre de 2026, tal cual se baja.
FIXTURE = ROOT / "tests" / "fixtures" / "pjn_trabajo_2026_s1.csv"

# Totales de primera instancia leídos de los CSV el 26-oct-2026. 2024 y 2025
# suman los 55.337 y 58.504 que citó la auditoría de CiGob.
SEMESTRES = {(2023, 1): 28221, (2023, 2): 30299, (2024, 1): 25859, (2024, 2): 29478,
             (2025, 1): 25562, (2025, 2): 32942, (2026, 1): 28911}


def test_lee_el_total_de_entrados_de_primera_instancia_del_csv_real():
    txt = FIXTURE.read_bytes().decode("latin-1")
    # 28.911 entrados; la columna siguiente (salidos, 30.992) no se confunde.
    assert gestion._pjn_entrados_primera(txt) == 28911


def test_los_anuales_coinciden_con_las_cifras_de_la_auditoria():
    assert SEMESTRES[(2024, 1)] + SEMESTRES[(2024, 2)] == 55337
    assert SEMESTRES[(2025, 1)] + SEMESTRES[(2025, 2)] == 58504


def test_doce_meses_contra_doce_meses_por_semestre():
    var, actual, anterior = gestion._juicios_trabajo_variacion(SEMESTRES, (2026, 1))
    assert (actual, anterior) == (61853, 55040)
    assert var == 12.4
    # Año calendario: 2025 contra 2024.
    assert gestion._juicios_trabajo_variacion(SEMESTRES, (2025, 2))[0] == 5.7


def test_sin_cuatro_semestres_no_compara():
    with pytest.raises(ValueError):
        gestion._juicios_trabajo_variacion(SEMESTRES, (2024, 1))


def test_fecha_del_dato_es_el_ultimo_mes_del_semestre():
    assert gestion._fecha_semestre((2026, 1)) == "2026-06-01"
    assert gestion._fecha_semestre((2025, 2)) == "2025-12-01"


def test_pesa_un_cuarto_de_la_reforma_laboral():
    """ADR-0365 lo sumó con 25 %; ADR-0369 sacó los juicios por riesgos del
    trabajo, ADR-0379 los repuso y ADR-0385 los cambió por la siniestralidad
    registrada: el 50/25/25 queda, con otro indicador en el cuarto del medio."""
    ind = itcg.DIMENSIONES_ITCG["reforma_laboral"]["indicadores"]
    assert ind == {"fal_modernizacion_laboral": 0.50, "siniestralidad_laboral": 0.25,
                   "juicios_trabajo_capital": 0.25}
    assert "litigiosidad_laboral" in itcg.INDICADORES_SUSPENDIDOS
    assert itcg.BANDAS_ITCG["juicios_trabajo_capital"] == itcg.BANDAS_ITCG["litigiosidad_laboral"]
    assert itcg.BANDAS_ITCG["juicios_trabajo_capital"] == itcg.BANDAS_ITCG["siniestralidad_laboral"]


def test_un_csv_con_comillas_se_lee_igual():
    import csv, io
    txt = FIXTURE.read_bytes().decode("latin-1")
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_ALL)
    for fila in csv.reader(io.StringIO(txt), delimiter=";"):
        w.writerow(fila)
    assert gestion._pjn_entrados_primera(buf.getvalue()) == 28911


def test_si_falta_un_semestre_usa_la_ultima_ventana_entera():
    sin_2025_s1 = {k: v for k, v in SEMESTRES.items() if k != (2025, 1)}
    assert gestion._ultimo_semestre_completo(sin_2025_s1) == (2024, 2)
    assert gestion._ultimo_semestre_completo(SEMESTRES) == (2026, 1)


def test_la_serie_es_escalonada_mensual(monkeypatch):
    import descargar_series
    monkeypatch.setattr(gestion, "_pjn_juicios_semestrales", lambda: dict(SEMESTRES))
    serie = dict(descargar_series.fetch_juicios_trabajo_serie())
    assert serie["2024-12-01"] == -5.4
    assert serie["2025-05-01"] == -5.4      # vale hasta que cierra el semestre siguiente
    assert serie["2025-06-01"] == -2.0
    assert serie["2026-06-01"] == 12.4
    assert "2024-11-01" not in serie
    meses = sorted(serie)
    assert serie[meses[-1]] == 12.4         # el último llega al mes en curso


# El 2-nov-2026 el PJN devolvió vacíos los listados de 2025 y 2026: con lo que
# quedaba, la card publicó el 2º semestre de 2024 (−5,4 %) como si fuera vigente.
VIEJOS = {k: v for k, v in SEMESTRES.items() if k[0] < 2025}


def _publicado(monkeypatch, fecha):
    monkeypatch.setattr(gestion, "load_cache", lambda: {"indicadores": {
        "juicios_trabajo_capital": {"valor": 12.4, "fecha_dato": fecha}}})


def test_un_listado_con_menos_semestres_que_lo_publicado_no_se_publica(monkeypatch):
    _publicado(monkeypatch, "2026-06-01")
    with pytest.raises(ValueError, match="incompleto"):
        gestion._pjn_no_retrocede(max(VIEJOS))
    with pytest.raises(ValueError, match="incompleto"):
        gestion._pjn_no_retrocede(None)


def test_la_card_no_cae_en_una_ventana_mas_vieja_por_un_hueco(monkeypatch):
    _publicado(monkeypatch, "2026-06-01")
    con_hueco = {k: v for k, v in SEMESTRES.items() if k != (2025, 2)}
    monkeypatch.setattr(gestion, "_pjn_juicios_semestrales", lambda: con_hueco)
    monkeypatch.setattr(gestion, "_warn", lambda *a: None)
    assert gestion.fetch_juicios_trabajo_capital() is None


def test_el_mismo_semestre_o_uno_nuevo_si_se_publica(monkeypatch):
    _publicado(monkeypatch, "2026-06-01")
    monkeypatch.setattr(gestion, "_pjn_juicios_semestrales", lambda: SEMESTRES)
    assert gestion.fetch_juicios_trabajo_capital()["valor"] == 12.4
    _publicado(monkeypatch, "2025-12-01")
    gestion._pjn_no_retrocede((2026, 1))
    _publicado(monkeypatch, "")
    gestion._pjn_no_retrocede(max(VIEJOS))


def test_la_serie_tampoco_se_arma_con_el_listado_incompleto(monkeypatch):
    """`descargar_series` usa `_pjn_juicios_semestrales` directo: el corte tiene
    que estar ahí, si no la serie se trunca en 2024 (pasó el 2-nov-2026)."""
    _publicado(monkeypatch, "2026-06-01")

    def opciones(step, anio, **kw):
        if step == "titulo":
            return [{"value": "t", "label": "Datos abiertos"}] if anio < 2025 else []
        return [{"value": f"{anio}-{s}", "label": f"Trámite de expedientes {s}º semestre"}
                for s in (1, 2)]

    monkeypatch.setattr(gestion, "_pjn_opciones", opciones)
    monkeypatch.setattr(gestion, "_http_get_resiliente", lambda url: FIXTURE.read_bytes())
    with pytest.raises(ValueError, match="incompleto"):
        gestion._pjn_juicios_semestrales(hasta=2026)
