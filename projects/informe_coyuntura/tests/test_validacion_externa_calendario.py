"""El tiempo de un contraste mensual se mide por fechas, no por filas."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validacion_externa import _difs, _lag


def test_diferencias_no_puentean_mes_ausente():
    assert _difs({"2023-12": 10, "2024-01": 12, "2024-03": 18,
                  "2024-04": 19}) == {"2024-01": 2, "2024-04": 1}


def test_adelanto_respeta_calendario_y_conserva_extremo():
    assert _lag({"2023-12": 10, "2024-02": 20}, 1) == {
        "2024-01": 10, "2024-03": 20}


def test_rezago_y_desplazamiento_cero():
    serie = {"2024-01": 10, "2024-03": 20}
    assert _lag(serie, -1) == {"2023-12": 10, "2024-02": 20}
    assert _lag(serie, 0) == serie


def test_panel_y_factor_excluyen_salto_de_dos_meses():
    import factor_comun, panel_validacion
    serie = {"2023-12": 10, "2024-01": 11, "2024-03": 15, "2024-04": 17}
    esperado = {"2024-01": 1, "2024-04": 2}
    assert factor_comun._difs(serie) == esperado
    assert panel_validacion._difs(serie) == esperado


def test_tendencia_mide_meses_transcurridos_aunque_falten_observaciones():
    from regresion_validacion import aporte_sobre_tendencia
    meses = [i for i in range(30) if i not in {2, 7, 13, 19, 24}]
    fechas = {i: f"{2023 + i // 12:04d}-{i % 12 + 1:02d}" for i in meses}
    indice = {fechas[i]: float((i * 7) % 11) for i in meses}
    externa = {fechas[i]: 100.0 + 3 * i for i in meses}
    resultado = aporte_sobre_tendencia(indice, externa)
    assert resultado["suficiente"]
    assert resultado["r2_tendencia"] == 1.0
    assert resultado["aporte"] == 0.0
