"""Consumo per cápita de carnes (vacuna + aviar + porcina) — SAGYP.

Componente B y C de la ficha "Consumo de Proteína Animal": el indicador vigente
mira sólo carne vacuna, y una caída ahí se lee como pérdida de poder adquisitivo
cuando muchas veces es sustitución hacia pollo o cerdo. Con el total y el ratio
se puede distinguir una cosa de la otra.

Fuente: SAGYP — Dirección Nacional de Producción Ganadera, tablero
"CONSUMO PER CAPITA CARNES PROMEDIO MÓVIL". PDF mensual, con el promedio móvil
de 12 meses YA calculado por la fuente (no se recalcula acá).

## Por qué el parseo es así

El PDF es un gráfico aplanado: los números salen mezclados con las etiquetas de
los ejes y sin un orden estable. Leerlos por posición sería frágil y —peor—
fallaría en silencio devolviendo el número equivocado.

En vez de eso el parser RESUELVE y se autoverifica: toma todos los niveles
candidatos y los empareja de modo que el cociente de cada par reproduzca la
variación interanual que el propio PDF publica al lado. Si el layout cambia,
ningún emparejamiento cierra y el colector falla en voz alta, que es lo que hay
que hacer cuando ya no se entiende la fuente.
"""
import io
import logging
import re

import requests

logger = logging.getLogger(__name__)

SAGYP_PDF_URL = (
    "https://www.magyp.gob.ar/sitio/areas/bovinos/informacion_sectorial/_archivos/"
    "/000017_Tablero%20de%20consumo%20de%20carnes/"
    "000003_Tablero_CONSUMO_PER_CAPITA_CARNES_PROMEDIO_MOVIL.pdf"
)
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
HTTP_TIMEOUT = 90

MESES = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
         "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11,
         "DICIEMBRE": 12}

# Las etiquetas tal como las escribe el PDF, en el bloque de variaciones.
CATEGORIAS = {
    "vacuna": r"Carne\s+Vacuna",
    "aviar": r"Carne\s+aviar",
    "porcina": r"Carne\s+Porcina",
    "total": r"TOTAL",
}
# Tolerancia del cruce: la variación del PDF viene redondeada a dos decimales,
# así que el cociente reconstruido nunca da exacto.
TOLERANCIA_PP = 0.06


# El PDF tiene dos zonas: arriba, las barras del mes (cuatro categorías × dos
# años); abajo, una serie anual 2021-2026 por categoría. Los niveles se buscan
# SÓLO arriba: abajo hay valores muy parecidos entre sí —el consumo aviar se
# mueve entre 45 y 47 kg hace cinco años— y más de un par reproduciría la misma
# variación, volviendo ambiguo el emparejamiento.
CORTE_CABECERA = "CONSUMO PER CAPITA MÓVIL AL MES DE"


def _numeros(texto: str) -> list:
    """Niveles candidatos de la cabecera: descarta las etiquetas de eje, que son
    múltiplos redondos de 20 terminados en ,00 (20,00 · 40,00 … 140,00)."""
    corte = texto.find(CORTE_CABECERA)
    cabecera = texto[:corte] if corte > 0 else texto
    out = []
    for m in re.finditer(r"\b(\d{2,3},\d{2})\b", cabecera):
        v = float(m.group(1).replace(",", "."))
        if abs(v % 20) < 1e-9 and m.group(1).endswith(",00"):
            continue
        out.append(v)
    return out


def _variaciones(texto: str) -> dict:
    """{categoria: variación i.a. en %} del bloque de variaciones del PDF.

    El porcentaje puede venir DESPUÉS de la etiqueta (`TOTAL -1,69%`) o ANTES
    (`-7,67%` y en la línea siguiente `Carne Vacuna`): al aplanar el gráfico, la
    etiqueta del tramo negativo queda del otro lado. Se busca en las dos
    direcciones.
    """
    out = {}
    for clave, patron in CATEGORIAS.items():
        m = re.search(patron + r"[^%\n]{0,20}?(-?\d{1,2},\d{2})\s*%", texto)
        if not m:
            m = re.search(r"(-?\d{1,2},\d{2})\s*%[^\n]{0,4}\n?\s*" + patron, texto)
        if m:
            out[clave] = float(m.group(1).replace(",", "."))
    return out


def _emparejar(niveles: list, variaciones: dict) -> dict:
    """{categoria: (actual, anterior)} resolviendo por la variación publicada.

    Se prueban todos los pares posibles y se acepta el único cuyo cociente
    reproduce la variación de esa categoría. Si una categoría admite más de un
    par, o ninguno, se considera que el PDF dejó de ser legible."""
    resultado = {}
    for cat, var in variaciones.items():
        candidatos = [
            (a, b) for a in niveles for b in niveles
            if a != b and abs((a / b - 1) * 100 - var) <= TOLERANCIA_PP
        ]
        # Un par puede aparecer con dos niveles iguales de otra categoría; se
        # deduplica por valor, no por posición.
        unicos = {(round(a, 2), round(b, 2)) for a, b in candidatos}
        if len(unicos) != 1:
            raise ValueError(
                f"consumo de carnes: {cat} admite {len(unicos)} emparejamientos "
                f"para una variación de {var}% — el PDF cambió de forma")
        resultado[cat] = unicos.pop()
    return resultado


def parsear_consumo_carnes(pdf_bytes: bytes) -> dict:
    """{mes, total, vacuna, aviar, porcina, ratio_bovina} del tablero SAGYP."""
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        texto = "\n".join(p.extract_text() or "" for p in pdf.pages)

    m_anio = re.search(r"^\s*(20\d{2})\s*$", texto, re.M)
    m_mes = re.search(r"Al mes de\s+([A-ZÁÉÍÓÚÑ]+)", texto)
    if not (m_anio and m_mes and m_mes.group(1).upper() in MESES):
        raise ValueError("consumo de carnes: no se pudo leer el período del tablero")
    mes = f"{int(m_anio.group(1))}-{MESES[m_mes.group(1).upper()]:02d}"

    variaciones = _variaciones(texto)
    faltan = set(CATEGORIAS) - set(variaciones)
    if faltan:
        raise ValueError(f"consumo de carnes: sin variación para {sorted(faltan)}")

    pares = _emparejar(_numeros(texto), variaciones)
    actual = {cat: par[0] for cat, par in pares.items()}

    # El total tiene que ser la suma de los tres, o la fuente cambió de
    # perímetro (¿entró ovina? ¿pescado?) y hay que enterarse.
    suma = actual["vacuna"] + actual["aviar"] + actual["porcina"]
    if abs(suma - actual["total"]) > 0.5:
        raise ValueError(
            f"consumo de carnes: los componentes suman {suma:.2f} y el total "
            f"publicado es {actual['total']:.2f} — cambió el perímetro")

    return {
        "mes": mes,
        "total": round(actual["total"], 2),
        "vacuna": round(actual["vacuna"], 2),
        "aviar": round(actual["aviar"], 2),
        "porcina": round(actual["porcina"], 2),
        # Componente C: qué porción del consumo total sigue siendo vacuna.
        "ratio_bovina": round(actual["vacuna"] / actual["total"] * 100, 2),
        "variaciones": variaciones,
    }


def fetch_consumo_carnes() -> dict:
    r = requests.get(SAGYP_PDF_URL, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    return parsear_consumo_carnes(r.content)
