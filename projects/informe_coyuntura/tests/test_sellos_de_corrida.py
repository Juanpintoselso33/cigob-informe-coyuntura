"""Los sellos de corrida que viajan a BigQuery llevan offset de zona horaria.

`generated_at` es la clave de corrida del archivo histórico (ADR-0180). Se
escribía con `datetime.now().isoformat()` —naive, sin offset— y BigQuery lee un
timestamp sin offset COMO UTC. En la CI salía bien de casualidad, porque el
runner de GitHub corre en UTC; cualquier corrida manual desde una máquina en ART
quedaba 3 horas adelantada en el archivo. Medido el 2026-08-14: 3 de 11 corridas
archivadas, y todas las de las tablas ML. Ver ADR-0203.

Dos cosas se protegen acá:

1. Que los sellos que llegan a BigQuery se sigan escribiendo con
   `.astimezone()`. Es el bug puntual.
2. Que el sello del snapshot y el de validacion_externa NO se separen: el test
   de frescura los RESTA, y aware menos naive es `TypeError`. O sea que una
   migración a medias no falla en el sello — falla en otro test, con un mensaje
   que no menciona zonas horarias.
"""
import json
import re
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

# Sitios que serializan un sello que termina siendo clave de corrida en
# BigQuery. La ruta es del repo; el patrón, la línea exacta que tiene que
# seguir usando `.astimezone()`.
SELLOS_A_BIGQUERY = {
    "scripts/generar_informe.py": r"now\s*=\s*datetime\.now\(\)\.astimezone\(\)",
    "scripts/validacion_externa.py": r'"generated_at":\s*datetime\.now\(\)\.astimezone\(\)\.isoformat\(\)',
    "scripts/verificacion_pdf.py": r"subir_a_bigquery\(informe,\s*datetime\.now\(\)\.astimezone\(\)",
    "scripts/bq_ml.py": r'"generado":\s*datetime\.now\(\)\.astimezone\(\)\.isoformat\(',
}


@pytest.mark.parametrize("ruta", sorted(SELLOS_A_BIGQUERY))
def test_el_sello_que_va_a_bigquery_lleva_offset(ruta):
    texto = (RAIZ / ruta).read_text(encoding="utf-8")
    assert re.search(SELLOS_A_BIGQUERY[ruta], texto), (
        f"{ruta} dejó de sellar con `.astimezone()`. Sin offset, BigQuery lee "
        "el timestamp como UTC y toda corrida hecha fuera de UTC queda "
        "desplazada en el archivo histórico — 3 horas acá. No falla nada: el "
        "dato entra, mal fechado, y no se puede corregir después sin reescribir "
        "filas. Ver ADR-0203."
    )


def test_el_reloj_de_pared_no_cambia():
    """El offset se agrega al final, así que los primeros 19 caracteres son los
    de siempre. De eso dependen todos los consumidores: `[:10]` en las fichas,
    `[:19]` en generar_informe, `.slice(0, 10)` y `slice(8, 10)` en la web."""
    sello = datetime.now().astimezone().isoformat()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?", sello[:19] + sello[19:19]), \
        f"el prefijo dejó de ser YYYY-MM-DDTHH:MM:SS: {sello[:19]!r}"
    assert datetime.fromisoformat(sello).tzinfo is not None, "el sello quedó sin zona"


def test_el_snapshot_y_validacion_externa_no_se_separan():
    """`test_salidas_versionadas_frescas` resta estos dos sellos. Si uno migra a
    aware y el otro no, la resta explota con un TypeError que no dice nada sobre
    zonas horarias. Tienen que moverse juntos."""
    def _tiene_zona(ruta, camino):
        """(existe, tiene_zona). Los dos datos por separado: un sello naive
        también da `tzinfo is None`, así que devolver sólo la zona haría que el
        test se saltee justo el caso que tiene que comparar."""
        d = json.loads((RAIZ / ruta).read_text(encoding="utf-8"))
        for k in camino:
            d = (d or {}).get(k)
            if d is None:
                return False, None
        return True, datetime.fromisoformat(str(d)).tzinfo is not None

    hay_snap, snap = _tiene_zona("output/informe.json", ("generated_at",))
    hay_vali, vali = _tiene_zona("output/validacion_externa.json", ("_meta", "generated_at"))
    if not (hay_snap and hay_vali):
        pytest.skip("alguna de las dos salidas todavía no tiene sello")
    assert snap == vali, (
        "El sello del snapshot y el de validacion_externa quedaron en "
        f"convenciones distintas (snapshot con zona={snap}, validación con zona={vali}). "
        "test_salidas_versionadas_frescas los resta y va a fallar con "
        "TypeError. Corré el pipeline completo para que los dos se regeneren "
        "con la misma convención. Ver ADR-0203."
    )
