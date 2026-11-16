"""Punto 12 del documento de Luis del 11-nov-2026 (decisión de Juan del 13-nov):
una dimensión es crítica cuando está en rojo con la escala de ADR-0427, y el
aviso «Dimensión crítica» se muestra en la card del cinturón y en la de la
dimensión (ADR-0020)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publicar  # noqa: E402


def test_los_umbrales_son_el_borde_del_rojo():
    assert publicar.UMBRAL_CRITICO_BANDAS == 25.0
    assert publicar.UMBRAL_CRITICO_BASE100 == 87.5


def test_el_borde_es_naranja_no_critico():
    bloque = {"dimensiones": {"a": {"puntaje": 25.0}, "b": {"puntaje": 24.9}}}
    publicar._marcar_dimensiones_criticas(bloque, publicar.UMBRAL_CRITICO_BANDAS)
    assert bloque["dimensiones"]["a"]["critica"] is False
    assert bloque["dimensiones"]["b"]["critica"] is True


def test_el_aviso_esta_en_las_dos_cards():
    web = ROOT / "web"
    for archivo in ("src/components/CinturonCard.astro", "src/pages/[slug].astro"):
        texto = (web / archivo).read_text(encoding="utf-8")
        assert "Dimensión crítica" in texto and "no la compensa" in texto, archivo
    css = (web / "public/overrides.css").read_text(encoding="utf-8")
    assert ".cg-itcm-dim.cg-itcm-dim--critica" in css
