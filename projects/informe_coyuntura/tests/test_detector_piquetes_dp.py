"""El detector de cierres anuales de piquetes de Diagnóstico Político (ADR-0025).

El sitio de la consultora se rehízo en 2026 (/monitoreos-politicos da 404 y el
contenido nuevo no tiene piquetes) y el cierre anual sale en enero por prensa.
Desde el 16-nov-2026 el detector busca en Google Noticias."""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gestion  # noqa: E402

RSS = """<rss><channel>
<item><title>Los piquetes se redujeron 52,7% desde que asumió Milei - La Nación</title>
<pubDate>Tue, 13 Jan 2026 10:00:00 GMT</pubDate></item>
<item><title>Ciudad de piquetes: crecieron un 32% en 2017 - Clarin.com</title>
<pubDate>Thu, 04 Jan 2018 10:00:00 GMT</pubDate></item>
</channel></rss>"""


def test_lee_el_anio_del_titulo_y_de_la_url():
    f = gestion.anios_de_piquetes_dp
    assert f("3.893 piquetes en 2025, la cifra más baja desde 2011") == {2025}
    assert f("/2026/01/11/3-893-piquetes-2025-la-cifra-mas-baja-desde-2011/") == {2025}
    assert f("sin novedades") == set()


def test_el_cierre_de_2025_lo_habria_detectado():
    """Con el anclaje en 2024, la nota de La Nación de enero de 2026 avisa."""
    nuevos = gestion.cierres_nuevos_dp(RSS, 2024)
    assert nuevos and nuevos[0][0] == "2026-01-13"


def test_con_el_anclaje_al_dia_no_avisa():
    assert gestion.cierres_nuevos_dp(RSS, 2025) == []


def test_un_titulo_con_anio_posterior_avisa_aunque_sea_viejo():
    rss = "<item><title>Hubo 2.000 piquetes en 2026</title><pubDate>Mon, 30 Nov 2026 10:00:00 GMT</pubDate></item>"
    assert gestion.cierres_nuevos_dp(rss, 2025)


def _rss(monkeypatch, texto):
    monkeypatch.setattr(gestion.requests, "get",
                        lambda *a, **k: SimpleNamespace(text=texto, raise_for_status=lambda: None))


def test_sin_cierre_nuevo_la_card_no_dice_nada(monkeypatch):
    _rss(monkeypatch, RSS)
    r = gestion.fetch_protocolo_antipiquetes()
    assert r["advertencia_fuente"] == ""


def test_con_cierre_nuevo_la_card_avisa(monkeypatch):
    _rss(monkeypatch, RSS.replace("13 Jan 2026", "12 Jan 2027"))
    r = gestion.fetch_protocolo_antipiquetes()
    assert "relevamiento nuevo" in r["advertencia_fuente"] and "2027-01-12" in r["advertencia_fuente"]


def test_sin_notas_no_certifica(monkeypatch):
    _rss(monkeypatch, "<rss></rss>")
    r = gestion.fetch_protocolo_antipiquetes()
    assert "No se pudo verificar" in r["advertencia_fuente"]
