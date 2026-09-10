from datetime import date, timedelta
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import politica


@pytest.mark.parametrize('fin', [date(2024,2,29),date(2024,12,31),date(2026,9,8)])
def test_365_fechas_incluidas_incluso_en_bisiesto(fin):
    inicio=politica.inicio_ventana_365(fin)
    universo=[fin-timedelta(days=i) for i in range(367)]
    seleccion=[f for f in universo if inicio <= f <= fin]
    assert len(seleccion)==365
    assert fin in seleccion and inicio in seleccion
    assert inicio-timedelta(days=1) not in seleccion
