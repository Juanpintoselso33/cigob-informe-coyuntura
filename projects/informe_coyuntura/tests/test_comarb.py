"""El store de recaudación COMARB tiene que estar completo y consistente.

La extracción sale de PDFs cuyo layout cambia entre meses (el orden de columnas
se invierte en enero, que no tiene columna de acumulado) y cuyos nombres de
archivo no siguen un patrón estable. Estos tests corren SIN red, sobre el store
versionado: verifican lo que un cambio de layout rompería en silencio.

El control fuerte es la suma: los seis sistemas (SIFERE, SIRCREB, SIRCAR,
SIRTAC, SIRPEI, SIRCUPA) tienen que sumar el total informado. Si el parseo
agarra un número de otra celda, la suma deja de cerrar.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import comarb

STORE = json.loads(comarb.CACHE.read_text(encoding="utf-8-sig"))
GACETILLAS = STORE["gacetillas"]


def test_hay_gacetillas_desde_2023():
    pers = sorted(GACETILLAS)
    assert pers[0] == "2023-01", f"la serie de gacetillas arranca en {pers[0]}"
    assert len(GACETILLAS) >= 42, f"sólo {len(GACETILLAS)} gacetillas en el store"


def test_no_hay_meses_faltantes():
    """Un hueco sería un mes cuyo nombre de archivo no matcheó el parser."""
    pers = sorted(GACETILLAS)
    y, m = map(int, pers[0].split("-"))
    faltan = []
    while f"{y:04d}-{m:02d}" <= pers[-1]:
        if f"{y:04d}-{m:02d}" not in GACETILLAS:
            faltan.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    assert not faltan, f"meses sin gacetilla: {faltan}"


@pytest.mark.parametrize("periodo", sorted(GACETILLAS))
def test_los_seis_sistemas_suman_el_total(periodo):
    reg = GACETILLAS[periodo]
    sistemas = [k for k in reg if k.startswith("sir") or k == "sifere"]
    assert len(sistemas) >= 5, f"{periodo}: sólo {len(sistemas)} sistemas parseados"
    suma = sum(reg[k] for k in sistemas)
    # tolerancia amplia: el PDF publica millones redondeados
    assert abs(suma / reg["total"] - 1) < 0.005, (
        f"{periodo}: los sistemas suman {suma:,.0f} contra un total de "
        f"{reg['total']:,.0f} — el parseo agarró otra celda")


def test_2022_reconstruido_completo_y_coherente():
    """2022 no tiene gacetilla: sale de la variación i.a. que publica cada
    gacetilla de 2023. El control es contra el nivel de 2023, no contra sí mismo."""
    rec = STORE["reconstruido_2022"]
    assert len(rec) == 12, f"faltan meses de 2022: {sorted(rec)}"
    for mes in range(1, 13):
        p22, p23 = f"2022-{mes:02d}", f"2023-{mes:02d}"
        var = GACETILLAS[p23]["var_ia_publicada"]
        esperado = GACETILLAS[p23]["total"] / (1 + var / 100)
        assert abs(rec[p22] / esperado - 1) < 1e-6, f"{p22} no reproduce la variación publicada"
    # 2022 fue un año de inflación alta: los niveles nominales tienen que crecer
    vals = [rec[f"2022-{m:02d}"] for m in range(1, 13)]
    assert vals[-1] > vals[0], "el nominal de 2022 no crece: revisar la reconstrucción"


def test_niveles_cacheados_cubren_el_piso_de_backfill():
    """Sin 2022 la variación interanual del combinado no llegaría a dic-2023,
    que es el piso que pide el proyecto."""
    niv = comarb.niveles_cacheados()
    assert "2022-12" in niv and "2023-12" in niv
    assert min(niv) <= "2022-01", f"el store arranca en {min(niv)}"
