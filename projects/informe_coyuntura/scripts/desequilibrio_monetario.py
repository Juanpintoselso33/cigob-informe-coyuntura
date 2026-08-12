"""Desequilibrio monetario: confianza DENTRO del sistema x fuga FUERA del sistema.

Implementa la ficha "Desequilibrio Monetario" (Diego, ago-2026). El indicador
nace de una observacion sobre el IDM vigente (ADR-0009): M2 y M3 son agregados
de OFERTA y no dicen con claridad cuanta confianza hay en el peso. La ficha
ataca eso con dos componentes que miden fenomenos distintos y que, por separado,
mienten:

  * Componente A -- que proporcion de la liquidez privada total (pesos + dolares
    depositados) esta en pesos de uso transaccional. Es un STOCK: mide la
    dolarizacion que se ve porque queda dentro del sistema financiero.
  * Componente B -- cuantos dolares netos compra el sector privado no financiero
    en el mercado de cambios. Es un FLUJO: capta la salida aunque no pase por
    ningun deposito.

Por que los dos juntos: si la fuga hacia el colchon es fuerte, A puede mostrarse
estable o hasta mejorando --esos dolares nunca entraron al denominador-- mientras
la situacion de fondo es la peor posible. B es el que expone ese caso, y por eso
el resultado sale de CRUZARLOS, no de promediarlos.

## Como se convierte en un solo numero

El motor parametrico puntua UN valor crudo por indicador y no admite un segundo
camino al puntaje (ADR-0082). Asi que la matriz se resuelve aca y el indicador
publica una TENSION 0-100 (0 = verde, 100 = deterioro total), igual que hacia la
presion de dolarizacion a la que reemplaza.

Cada componente se lleva a una posicion 0-1 interpolando entre los percentiles
de su ventana de calibracion, y la tension sale de interpolar BILINEALMENTE
entre las cuatro esquinas de la matriz de la ficha:

                        | B bajo (poca fuga) | B alto (fuga fuerte)
    --------------------+--------------------+---------------------
     A alto (poca dol.) |  verde        ->  0 |  naranja/rojo -> 77,5
     A bajo (mucha dol.)|  amarillo     -> 40 |  rojo         -> 90

Las cuatro esquinas caen exactamente sobre `puntaje = 100 - tension`, de modo
que las anclas del ITCM son la inversion lineal y no hay una segunda escala que
se pueda desincronizar de esta.

Notese que la matriz NO es simetrica: pasar de verde a amarillo (que se degrade
A) cuesta 40 puntos y pasar de verde a naranja/rojo (que se degrade B) cuesta
77,5. Eso no es una ponderacion inventada aca: sale de las celdas que fijo la
ficha, y refleja su tesis de que la fuga fuera del sistema es la senal grave.
"""
import io
from collections import defaultdict

import openpyxl
import requests

# -- Componente A: confianza dentro del sistema --------------------------------
# Ratio = M2 transaccional del sector privado / M3 ampliado x 100, donde el M3
# ampliado es circulante + depositos privados en pesos + depositos privados en
# dolares expresados en pesos.
#
# El numerador es la var. 197 y no una reconstruccion propia: la ficha define el
# M2 transaccional privado como circulante + cuentas corrientes + cajas de
# ahorro privadas en pesos EXCLUYENDO la vista remunerada de personas juridicas,
# y esa exclusion es exactamente lo que la 197 hace y lo que no se puede
# replicar con las series sueltas. Medido: 17+94+95 corre +22,8% por encima de
# la 197 en promedio (hasta +57%), lo que moveria el ratio +8,7 pp -- mas que el
# rango entero del indicador. Por eso la ventana arranca en 2021-01, que es
# donde la 197 empieza a publicarse, y no en 2016 como pedia la ficha.
BCRA_M2_PRIV_ID    = 197  # M2 transaccional del sector privado (excl. vista rem. PJ)
BCRA_CIRCULANTE_ID = 17   # Billetes y monedas en poder del publico
BCRA_DEP_PRIV_ARS  = 100  # Depositos del SPNF en pesos (incluye cedros)
BCRA_DEP_PRIV_USD  = 104  # Depositos del SPNF en moneda extranjera, EXPRESADOS EN PESOS

# -- Componente B: fuga fuera del sistema ---------------------------------------
# La ficha lo nombra "Formacion de Activos Externos del Sector Privado No
# Financiero". Ese rubro YA NO SE PUBLICA con ese nombre: el anexo del balance
# cambiario reserva "Formacion de activos externos" para el sector financiero y
# el publico, y lo del privado no financiero sale bajo el concepto 03. Se usa
# ese, que es el mismo universo.
#
# Se lee de la hoja TABULAR y no de la matricial: la matricial obliga a contar
# columnas (el neto del concepto vive en la columna anterior al titulo) y se
# rompe sola en cuanto el BCRA agregue un rubro. Reconcilian entre si dentro de
# 0,5% en 14 de los 15 meses de la ventana (3,2% en dic-2025).
BCRA_ANEXO_CAMBIOS_URL = (
    "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/"
    "anexo-estadistico-mercado-cambios-balance-cambiario.xlsx"
)
HOJA_MERCADO_CAMBIOS = "Datos Mercado de Cambios"
CONCEPTO_SIN_FINES_ESPECIFICOS = (
    "03- Compra-venta de billetes y divisas sin fines específicos"
)
# El concepto 03 incluye al sector publico entre sus sectores; el componente es
# del sector privado NO financiero, asi que se excluye explicitamente.
SECTOR_EXCLUIDO = "Sector Público"

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
HTTP_TIMEOUT = 90

# -- Calibracion ----------------------------------------------------------------
# Cortes por PERCENTILES reales de cada serie, como pide la seccion 7 de la
# ficha (reemplazan los valores preliminares de su seccion 4, que no cerraban
# contra el dato: con ellos ninguno de los 15 meses de la ventana daba verde, y
# su ancla ">3.000 = comparable a jul-2025" erraba por ~80%, porque jul-2025
# fueron 5.436 millones).
#
# Van CONGELADOS y no se recalculan en cada corrida: si el corte se moviera con
# el ultimo dato, el puntaje de un mes dejaria de ser reproducible y la serie
# historica cambiaria hacia atras sin que nadie tocara nada.
#
# Percentiles (0/25/50/75/100) por interpolacion lineal sobre la serie ordenada.
POSICIONES = (0.0, 0.25, 0.50, 0.75, 1.0)

# Ventana 2021-01 -> 2026-08 (68 meses), toda la historia de la var. 197.
CORTES_A = (31.62, 34.48, 38.27, 44.34, 49.96)
VENTANA_A = "2021-01 / 2026-08"

# Ventana 2025-04 -> 2026-06 (15 meses), desde la apertura del cepo a personas
# humanas: la ficha la fija asi para no mezclar regimenes cambiarios, y tiene
# razon -- bajo cepo este flujo daba ~0 por falta de acceso, no por confianza.
CORTES_B = (1122.3, 1954.2, 2363.3, 3643.7, 6545.1)
VENTANA_B = "2025-04 / 2026-06"

# Esquinas de la matriz, en tension (0 = verde, 100 = peor). La celda
# "naranja/rojo" de la ficha se toma como el punto medio entre naranja (65) y
# rojo (90): la ficha la dejo escrita con las dos etiquetas y el medio es la
# lectura honesta.
TENSION_A_BAJO_B_BAJO = 40.0   # amarillo -- dolarizacion contenida en el sistema
TENSION_A_ALTO_B_BAJO = 0.0    # verde -- confianza real
TENSION_A_BAJO_B_ALTO = 90.0   # rojo -- deterioro total, dentro y fuera
TENSION_A_ALTO_B_ALTO = 77.5   # naranja/rojo -- fuga oculta fuera del sistema

# El compuesto no existe antes de que exista B bajo el regimen abierto. B se
# puede calcular desde 2003, pero con cepo daba ~0 y la matriz lo leeria como
# "poca fuga" = verde justo cuando no habia acceso al dolar -- la lectura
# invertida que ADR-0055 habia resuelto. Antes de esta fecha el indicador
# simplemente no se publica y el ITCM renormaliza (parametrica.calcular_indice).
MES_INICIO = "2025-04"


def _texto_normalizado(valor) -> str:
    return " ".join(str(valor or "").split())


def posicion(valor: float, cortes: tuple) -> float:
    """Posicion 0-1 del valor entre los percentiles `cortes`, saturando afuera.

    Interpola lineal entre (corte_i, POSICIONES_i). Es la misma forma de
    `puntaje_desde_anclas` de parametrica.py --anclas explicitas + saturacion--
    pero sobre la escala 0-1 de la matriz, no sobre el puntaje.
    """
    if len(cortes) != len(POSICIONES):
        raise ValueError("cortes y POSICIONES deben tener el mismo largo")
    valor = float(valor)
    if valor <= cortes[0]:
        return POSICIONES[0]
    if valor >= cortes[-1]:
        return POSICIONES[-1]
    for (x0, p0), (x1, p1) in zip(zip(cortes, POSICIONES),
                                  zip(cortes[1:], POSICIONES[1:])):
        if x0 <= valor <= x1:
            if x1 == x0:
                return p1
            return p0 + (p1 - p0) * (valor - x0) / (x1 - x0)
    return POSICIONES[-1]


def tension_matriz(pos_a: float, pos_b: float) -> float:
    """Interpolacion bilineal entre las cuatro esquinas de la matriz A x B.

    `pos_a` 0 = mucha dolarizacion visible, 1 = poca. `pos_b` 0 = poca fuga,
    1 = fuga fuerte. Devuelve tension 0-100; el puntaje ITCM es 100 - tension.
    """
    a, b = float(pos_a), float(pos_b)
    return (
        (1 - a) * (1 - b) * TENSION_A_BAJO_B_BAJO
        + a * (1 - b) * TENSION_A_ALTO_B_BAJO
        + (1 - a) * b * TENSION_A_BAJO_B_ALTO
        + a * b * TENSION_A_ALTO_B_ALTO
    )


def _celda(pos_a: float, pos_b: float) -> str:
    """Cuadrante de la matriz donde cae el mes, para la lectura cualitativa."""
    lado_a = "alto" if pos_a >= 0.5 else "bajo"
    lado_b = "alto" if pos_b >= 0.5 else "bajo"
    return {
        ("alto", "bajo"): "verde",
        ("bajo", "bajo"): "amarillo",
        ("alto", "alto"): "naranja_rojo",
        ("bajo", "alto"): "rojo",
    }[(lado_a, lado_b)]


def parsear_fuga_spnf(contenido: bytes) -> dict:
    """{YYYY-MM: USD millones} de compra neta de divisas del SPNF. Positivo = salida.

    Mismo signo que usaba la presion de dolarizacion: el anexo informa el monto
    con signo contable y aca interesa la salida como numero positivo.
    """
    wb = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    try:
        ws = wb[HOJA_MERCADO_CAMBIOS]
        filas = ws.iter_rows(values_only=True)
        encabezado = next(filas)
        columnas = {_texto_normalizado(n): i for i, n in enumerate(encabezado)}
        faltantes = {"Mes", "Sector", "Monto", "B"} - columnas.keys()
        if faltantes:
            raise ValueError(
                "Faltan columnas en el anexo cambiario: " + ", ".join(sorted(faltantes))
            )
        concepto_objetivo = CONCEPTO_SIN_FINES_ESPECIFICOS.casefold()
        sector_excluido = SECTOR_EXCLUIDO.casefold()
        acumulado = defaultdict(float)
        for fila in filas:
            if _texto_normalizado(fila[columnas["B"]]).casefold() != concepto_objetivo:
                continue
            if _texto_normalizado(fila[columnas["Sector"]]).casefold() == sector_excluido:
                continue
            mes, monto = fila[columnas["Mes"]], fila[columnas["Monto"]]
            if mes is None or monto is None:
                continue
            periodo = mes.strftime("%Y-%m") if hasattr(mes, "strftime") else str(mes)[:7]
            acumulado[periodo] -= float(monto) / 1_000_000.0
        if not acumulado:
            raise ValueError("Anexo cambiario: sin filas del SPNF para el concepto 03")
        return {mes: round(valor, 6) for mes, valor in sorted(acumulado.items())}
    finally:
        wb.close()


def fetch_fuga_spnf() -> dict:
    r = requests.get(BCRA_ANEXO_CAMBIOS_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return parsear_fuga_spnf(r.content)


def construir_serie(*, m2_privado, circulante, dep_priv_ars, dep_priv_usd,
                    fuga_spnf) -> list:
    """Serie mensual del indicador. Un mes entra solo si tiene TODOS los insumos.

    No se imputa nada: si falta cualquiera de los cinco, el mes no se calcula.
    """
    meses = (
        set(m2_privado) & set(circulante) & set(dep_priv_ars)
        & set(dep_priv_usd) & set(fuga_spnf)
    )
    serie = []
    for mes in sorted(m for m in meses if m >= MES_INICIO):
        m3_ampliado = circulante[mes] + dep_priv_ars[mes] + dep_priv_usd[mes]
        if m3_ampliado <= 0:
            continue
        ratio_a = m2_privado[mes] / m3_ampliado * 100
        fuga_b = fuga_spnf[mes]
        pos_a = posicion(ratio_a, CORTES_A)
        pos_b = posicion(fuga_b, CORTES_B)
        tension = tension_matriz(pos_a, pos_b)
        serie.append({
            "mes": mes,
            "tension": round(tension, 2),
            "puntaje_itcm": round(100.0 - tension, 1),
            "componente_a": round(ratio_a, 2),
            "componente_b": round(fuga_b, 1),
            "posicion_a": round(pos_a, 4),
            "posicion_b": round(pos_b, 4),
            "celda": _celda(pos_a, pos_b),
        })
    return serie


def obtener_serie(meses_hist: int = 36, *, fetch_bcra_fin_mes=None,
                  fetch_fuga=fetch_fuga_spnf) -> list:
    """Obtiene los insumos y construye la serie unica para card y backfill."""
    if fetch_bcra_fin_mes is None:
        raise ValueError("fetch_bcra_fin_mes es obligatorio")
    meses_consulta = meses_hist + 4
    insumos = {
        "M2 transaccional privado": fetch_bcra_fin_mes(BCRA_M2_PRIV_ID, meses_consulta),
        "circulante": fetch_bcra_fin_mes(BCRA_CIRCULANTE_ID, meses_consulta),
        "depositos privados en pesos": fetch_bcra_fin_mes(BCRA_DEP_PRIV_ARS, meses_consulta),
        "depositos privados en dolares": fetch_bcra_fin_mes(BCRA_DEP_PRIV_USD, meses_consulta),
        "compra neta de divisas del SPNF": fetch_fuga(),
    }
    for nombre, valores in insumos.items():
        if not valores:
            raise ValueError(f"sin datos para {nombre}")
    serie = construir_serie(
        m2_privado=insumos["M2 transaccional privado"],
        circulante=insumos["circulante"],
        dep_priv_ars=insumos["depositos privados en pesos"],
        dep_priv_usd=insumos["depositos privados en dolares"],
        fuga_spnf=insumos["compra neta de divisas del SPNF"],
    )
    if not serie:
        raise ValueError("sin meses con insumos completos")
    return serie[-meses_hist:]
