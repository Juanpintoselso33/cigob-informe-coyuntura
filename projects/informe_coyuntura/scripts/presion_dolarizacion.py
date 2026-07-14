"""Presión de dolarización de carteras sensible al régimen cambiario."""
import io
from collections import defaultdict
from statistics import fmean

import openpyxl
import requests

ARGENTINA_DATOS_CCL_URL = (
    "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui"
)
BCRA_MONETARIAS_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
BCRA_TC_A3500_ID = 5
BCRA_M2_PRIV_ID = 197
BCRA_ANEXO_CAMBIOS_URL = (
    "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/"
    "anexo-estadistico-mercado-cambios-balance-cambiario.xlsx"
)
HOJA_MERCADO_CAMBIOS = "Datos Mercado de Cambios"
CONCEPTO_SIN_FINES_ESPECIFICOS = (
    "03- Compra-venta de billetes y divisas sin fines específicos"
)
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
HTTP_TIMEOUT = 90

ANCLAS_PRECIO = (
    (5.0, 0.0),
    (15.0, 25.0),
    (30.0, 50.0),
    (50.0, 75.0),
    (70.0, 100.0),
)
ANCLAS_FLUJO = (
    (0.0, 0.0),
    (3.0, 25.0),
    (6.0, 50.0),
    (10.0, 75.0),
    (15.0, 100.0),
)
ANCLAS_PUNTAJE = (
    (0.0, 100.0),
    (25.0, 85.0),
    (50.0, 60.0),
    (75.0, 35.0),
    (100.0, 10.0),
)
FECHA_APERTURA = "2025-04"


def interpolar(
    valor: float,
    anclas: tuple[tuple[float, float], ...],
) -> float:
    """Interpola linealmente y satura fuera del rango de anclas."""
    if valor <= anclas[0][0]:
        return float(anclas[0][1])
    if valor >= anclas[-1][0]:
        return float(anclas[-1][1])
    for (x0, y0), (x1, y1) in zip(anclas, anclas[1:]):
        if valor <= x1:
            return y0 + (valor - x0) * (y1 - y0) / (x1 - x0)
    raise AssertionError("anclas vacías o desordenadas")


def _desplazar_mes(mes: str, cantidad: int) -> str:
    total = int(mes[:4]) * 12 + int(mes[5:7]) - 1 + cantidad
    return f"{total // 12}-{total % 12 + 1:02d}"


def _fila(
    mes: str,
    regimen: str,
    metrica: float,
    presion: float,
    ventana_meses: int,
) -> dict:
    return {
        "mes": mes,
        "regimen": regimen,
        "metrica": round(metrica, 2),
        "presion": round(presion, 2),
        "puntaje_itcm": round(interpolar(presion, ANCLAS_PUNTAJE), 2),
        "ventana_meses": ventana_meses,
        "ventana_parcial": regimen == "flujo" and ventana_meses < 3,
    }


def construir_serie(
    brecha_ccl: dict[str, float],
    demanda_neta_usd: dict[str, float],
    m2_privado_ars: dict[str, float],
    tc_a3500: dict[str, float],
    desde: str = "2023-12",
) -> list[dict]:
    """Construye la presión mensual con el observable válido en cada régimen."""
    meses = sorted(
        set(brecha_ccl)
        | set(demanda_neta_usd)
        | set(m2_privado_ars)
        | set(tc_a3500)
    )
    out = []
    for mes in meses:
        if mes < desde:
            continue
        if mes < FECHA_APERTURA:
            ventana = [_desplazar_mes(mes, i) for i in (-2, -1, 0)]
            if any(m not in brecha_ccl for m in ventana):
                continue
            metrica = sum(brecha_ccl[m] for m in ventana) / 3.0
            presion = interpolar(metrica, ANCLAS_PRECIO)
            out.append(_fila(mes, "precio", metrica, presion, 3))
            continue

        if mes == FECHA_APERTURA:
            ventana = [mes]
        elif mes == _desplazar_mes(FECHA_APERTURA, 1):
            ventana = [FECHA_APERTURA, mes]
        else:
            ventana = [_desplazar_mes(mes, i) for i in (-2, -1, 0)]
        if any(
            m not in demanda_neta_usd
            or m not in m2_privado_ars
            or m not in tc_a3500
            or not tc_a3500[m]
            for m in ventana
        ):
            continue
        denominador = sum(m2_privado_ars[m] / tc_a3500[m] for m in ventana)
        if denominador <= 0:
            continue
        metrica = 100.0 * sum(demanda_neta_usd[m] for m in ventana) / denominador
        presion = interpolar(metrica, ANCLAS_FLUJO)
        out.append(_fila(mes, "flujo", metrica, presion, len(ventana)))
    return out


def _texto_normalizado(valor) -> str:
    return " ".join(str(valor or "").split())


def parsear_demanda_neta_personas_humanas(
    contenido: bytes,
) -> dict[str, float]:
    """Extrae compras netas mensuales de personas humanas, en millones de USD."""
    wb = openpyxl.load_workbook(
        io.BytesIO(contenido),
        read_only=True,
        data_only=True,
    )
    try:
        ws = wb[HOJA_MERCADO_CAMBIOS]
        filas = ws.iter_rows(values_only=True)
        encabezado = next(filas)
        columnas = {
            _texto_normalizado(nombre): indice
            for indice, nombre in enumerate(encabezado)
        }
        requeridas = {"Mes", "Sector", "Monto", "B"}
        faltantes = requeridas - columnas.keys()
        if faltantes:
            raise ValueError(
                "Faltan columnas en el anexo cambiario: "
                + ", ".join(sorted(faltantes))
            )

        acumulado = defaultdict(float)
        sector_objetivo = "Personas Humanas".casefold()
        concepto_objetivo = CONCEPTO_SIN_FINES_ESPECIFICOS.casefold()
        for fila in filas:
            if _texto_normalizado(fila[columnas["Sector"]]).casefold() != sector_objetivo:
                continue
            if _texto_normalizado(fila[columnas["B"]]).casefold() != concepto_objetivo:
                continue
            mes = fila[columnas["Mes"]]
            monto = fila[columnas["Monto"]]
            if mes is None or monto is None:
                continue
            if hasattr(mes, "strftime"):
                periodo = mes.strftime("%Y-%m")
            else:
                periodo = str(mes)[:7]
            acumulado[periodo] -= float(monto) / 1_000_000.0
        if not acumulado:
            raise ValueError(
                "Anexo cambiario: sin filas de Personas Humanas para el concepto 03"
            )
        return {
            mes: round(valor, 6)
            for mes, valor in sorted(acumulado.items())
        }
    finally:
        wb.close()


def _promedios_mensuales(
    detalle: list[dict],
    campo_valor: str,
    desde: str,
) -> dict[str, float]:
    valores = defaultdict(list)
    for fila in detalle:
        mes = str(fila.get("fecha", ""))[:7]
        valor = fila.get(campo_valor)
        if mes >= desde and valor is not None:
            valores[mes].append(float(valor))
    return {
        mes: fmean(muestras)
        for mes, muestras in valores.items()
        if muestras
    }


def fetch_brecha_ccl_mensual(
    desde: str = "2023-10",
) -> dict[str, float]:
    """Calcula brecha mensual entre CCL y tipo de cambio mayorista A3500."""
    respuesta_ccl = requests.get(
        ARGENTINA_DATOS_CCL_URL,
        headers=HTTP_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    respuesta_ccl.raise_for_status()
    ccl = _promedios_mensuales(
        respuesta_ccl.json(),
        "venta",
        desde,
    )
    if not ccl:
        raise ValueError("ArgentinaDatos: sin datos mensuales de CCL")

    respuesta_mayorista = requests.get(
        f"{BCRA_MONETARIAS_URL}/{BCRA_TC_A3500_ID}",
        params={"desde": f"{desde}-01", "limit": 3000},
        headers=HTTP_HEADERS,
        timeout=HTTP_TIMEOUT,
        verify=False,
    )
    respuesta_mayorista.raise_for_status()
    resultados = respuesta_mayorista.json().get("results") or []
    detalle = resultados[0].get("detalle", []) if resultados else []
    mayorista = _promedios_mensuales(
        detalle,
        "valor",
        desde,
    )
    if not mayorista:
        raise ValueError("BCRA: sin datos mensuales de A3500")

    brechas = {
        mes: round(100.0 * (ccl[mes] / mayorista[mes] - 1.0), 2)
        for mes in sorted(ccl.keys() & mayorista.keys())
        if mayorista[mes]
    }
    if not brechas:
        raise ValueError("CCL y A3500: sin meses comunes")
    return brechas


def fetch_demanda_neta_personas_humanas() -> dict[str, float]:
    """Descarga el anexo acumulativo del BCRA y devuelve compras netas mensuales."""
    respuesta = requests.get(
        BCRA_ANEXO_CAMBIOS_URL,
        headers=HTTP_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    respuesta.raise_for_status()
    return parsear_demanda_neta_personas_humanas(respuesta.content)


def obtener_serie(
    meses_hist: int = 36,
    *,
    fetch_brecha=fetch_brecha_ccl_mensual,
    fetch_demanda=fetch_demanda_neta_personas_humanas,
    fetch_bcra_fin_mes=None,
) -> list[dict]:
    """Obtiene todos los insumos y construye la serie única para card y backfill."""
    if fetch_bcra_fin_mes is None:
        raise ValueError("fetch_bcra_fin_mes es obligatorio")
    meses_consulta = meses_hist + 4
    brecha_ccl = fetch_brecha(desde="2023-10")
    demanda_neta_usd = fetch_demanda()
    m2_privado_ars = fetch_bcra_fin_mes(BCRA_M2_PRIV_ID, meses_consulta)
    tc_a3500 = fetch_bcra_fin_mes(BCRA_TC_A3500_ID, meses_consulta)
    for nombre, valores in (
        ("brecha CCL/A3500", brecha_ccl),
        ("demanda neta de Personas Humanas", demanda_neta_usd),
        ("M2 privado", m2_privado_ars),
        ("A3500", tc_a3500),
    ):
        if not valores:
            raise ValueError(f"sin datos para {nombre}")
    serie = construir_serie(
        brecha_ccl=brecha_ccl,
        demanda_neta_usd=demanda_neta_usd,
        m2_privado_ars=m2_privado_ars,
        tc_a3500=tc_a3500,
    )
    if not serie:
        raise ValueError("sin meses con insumos completos")
    return serie[-meses_hist:]
