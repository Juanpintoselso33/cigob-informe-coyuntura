"""Alquiler real a partir de UdeSA - Mercado Libre Inmuebles (ADR-0386, ADR-0411).

La fuente no tiene serie descargable ni publica niveles: sale un PDF por mes en
una carpeta de Google Drive y las cifras viven en la prosa del informe. Por eso la
carga es **manual, una vez por mes** (`cargar_alquiler_udesa.py`), y este módulo
sólo lee el registro versionado `data/vida/alquiler_udesa.json`, lo valida y calcula.

Desde ADR-0411 el indicador es un NIVEL contra el 4T-2023, como los demás
componentes de precios, y no una variación interanual. Como la fuente sólo da
variaciones, el nivel nominal es una RECONSTRUCCIÓN de CIGOB, en orden cronológico:

  1. sep-2023 = 100 (semilla).
  2. Desde oct-2023, para cada mes t: si la interanual nominal de t está
     publicada y el nivel de t−12 es conocido, nivel(t) = nivel(t−12) x (1 + ia).
  3. Si no, y la intermensual de t está publicada y el nivel de t−1 es conocido,
     nivel(t) = nivel(t−1) x (1 + mm).
  4. Si no, el mes queda SIN nivel: no se imputa ni se interpola.

Se prefiere la interanual publicada porque encadenar las mensuales da
sistemáticamente menos que las interanuales que el propio informe publica.

    real(t) = 100 x [nivel(t) / base_nominal] / [IPC general GBA(t) / base_IPC]

con base = promedio oct-dic 2023 de cada uno. El IPC es el nivel general del GBA
de la planilla original del INDEC (la misma que usa `alquiler_real`, ADR-0291), no
el nacional: el alquiler de UdeSA es de AMBA y dividir por un índice de otra plaza
mezclaría dos mercados.

Componente del índice de impacto social: 100 x 100 / real, la misma construcción
que `itvc_alquiler`. 100 = igual que a fines de 2023; por encima, el alquiler
pedido bajó en términos reales (alivio); por debajo, se encareció.

Sin red: todo lo que calcula recibe los niveles del IPC por argumento.
"""
import json
import re
from datetime import date
from pathlib import Path

REGISTRO = Path(__file__).resolve().parents[3] / "data" / "vida" / "alquiler_udesa.json"

URL_PAGINA = "https://www.udesa.edu.ar/indices-mercado-libre"
RE_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
RE_URL = re.compile(r"^https://[^\s]+$")
# Techos de sanidad para un alquiler nominal interanual: la inflación llegó a
# ~290 % interanual (abr-2024), así que 400 sirve de tope sin tapar la historia.
INTERANUAL_MIN, INTERANUAL_MAX = -50.0, 400.0
DIAS_SIN_CARGA_AVISO = 45
SEMILLA_MES = "2023-09"       # nivel nominal = 100 (ADR-0411)
BASE_MESES = ("2023-10", "2023-11", "2023-12")   # 4T-2023, la base de los dos niveles


def validar_entrada(mes, entrada) -> None:
    """Levanta ValueError si la entrada del mes no está bien formada."""
    if not RE_MES.match(str(mes)):
        raise ValueError(f"mes inválido: {mes!r} (se espera AAAA-MM)")
    if not isinstance(entrada, dict):
        raise ValueError(f"{mes}: la entrada no es un objeto")
    inter = entrada.get("interanual_deptos_amba_pct")
    if inter is not None:
        if isinstance(inter, bool) or not isinstance(inter, (int, float)):
            raise ValueError(f"{mes}: interanual no numérico: {inter!r}")
        if not (INTERANUAL_MIN <= inter <= INTERANUAL_MAX):
            raise ValueError(f"{mes}: interanual fuera de rango: {inter}")
        if not str(entrada.get("frase") or "").strip():
            raise ValueError(f"{mes}: un valor sin la frase textual del PDF no entra")
    mensual = entrada.get("intermensual_deptos_amba_pct")
    if mensual is not None:
        if (isinstance(mensual, bool) or not isinstance(mensual, (int, float))
                or not -60.0 <= mensual <= 100.0):
            raise ValueError(f"{mes}: intermensual inválido: {mensual!r}")
        if not str(entrada.get("frase") or "").strip():
            raise ValueError(f"{mes}: una intermensual sin la frase textual del PDF no entra")
    if not RE_URL.match(str(entrada.get("url_pdf") or "")):
        raise ValueError(f"{mes}: url_pdf ausente o no https")
    try:
        date.fromisoformat(str(entrada.get("cargado_en")))
    except ValueError:
        raise ValueError(f"{mes}: cargado_en no es una fecha ISO") from None


def validar_registro(registro: dict) -> dict:
    """Devuelve {mes: entrada} validada, o levanta ValueError."""
    meses = registro.get("meses")
    if not isinstance(meses, dict) or not meses:
        raise ValueError("registro sin «meses»")
    for mes, entrada in meses.items():
        validar_entrada(mes, entrada)
    return meses


def leer_registro(path: Path = REGISTRO) -> dict:
    return validar_registro(json.loads(Path(path).read_text(encoding="utf-8")))


def _mes_antes(mes: str, k: int) -> str:
    t = int(mes[:4]) * 12 + int(mes[5:]) - 1 - k
    return f"{t // 12}-{t % 12 + 1:02d}"


def reconstruir_niveles(meses: dict) -> dict:
    """{mes: nivel nominal} con sep-2023 = 100, según la regla de ADR-0411.

    Prefiere la interanual publicada (sobre el nivel de hace 12 meses); si no
    hay, usa la intermensual (sobre el mes anterior); si tampoco, el mes queda
    sin nivel. Nunca imputa ni interpola."""
    niveles = {SEMILLA_MES: 100.0}
    for mes in sorted(meses):
        if mes <= SEMILLA_MES:
            continue
        e = meses[mes]
        ia = e.get("interanual_deptos_amba_pct")
        mm = e.get("intermensual_deptos_amba_pct")
        previo_12, previo_1 = niveles.get(_mes_antes(mes, 12)), niveles.get(_mes_antes(mes, 1))
        if ia is not None and previo_12 is not None:
            niveles[mes] = previo_12 * (1 + ia / 100.0)
        elif mm is not None and previo_1 is not None:
            niveles[mes] = previo_1 * (1 + mm / 100.0)
    return niveles


def _base(serie: dict) -> float:
    faltan = [m for m in BASE_MESES if m not in serie]
    if faltan:
        raise ValueError(f"base 4T-2023 incompleta (faltan {faltan})")
    return sum(serie[m] for m in BASE_MESES) / 3.0


def indice_componente(real: float) -> float:
    """100 x 100 / real: 100 = igual que a fines de 2023; > 100 = más barato en términos reales."""
    return round(10000.0 / real, 1)


def serie(meses: dict, niveles_general: dict) -> list:
    """[{mes, nivel_nominal, ipc, real}] ascendente, desde oct-2023, sólo meses con
    nivel reconstruido Y IPC publicado.

    Un mes sin nivel no se interpola: queda fuera y la serie conserva el último
    punto como desactualizado (lo vigila MAX_DIAS)."""
    nominal = reconstruir_niveles(meses)
    base_nom = _base(nominal)
    base_ipc = _base(niveles_general)
    out = []
    for mes in sorted(nominal):
        if mes < BASE_MESES[0]:
            continue
        ipc = niveles_general.get(mes)
        if not ipc:
            continue
        real = 100.0 * (nominal[mes] / base_nom) / (ipc / base_ipc)
        out.append({"mes": mes, "nivel_nominal": round(nominal[mes], 2), "ipc": ipc,
                    "real": round(real, 2)})
    return out


def tarjeta(meses: dict = None, niveles_general: dict = None) -> dict:
    """Último punto real: {valor, fecha, indice, nivel_nominal, frase, fuente_url}."""
    if meses is None:
        meses = leer_registro()
    if niveles_general is None:
        try:
            from .ipc_alquiler import niveles
        except ImportError:
            from ipc_alquiler import niveles
        niveles_general = niveles()["general"]
    pts = serie(meses, niveles_general)
    if not pts:
        raise ValueError("alquiler_udesa: ningún mes con nivel reconstruido e IPC publicado")
    u = pts[-1]
    return {"valor": u["real"], "fecha": u["mes"] + "-01", "indice": indice_componente(u["real"]),
            "nivel_nominal": u["nivel_nominal"],
            "frase": meses[u["mes"]].get("frase"), "fuente_url": meses[u["mes"]]["url_pdf"]}


def dias_sin_carga(meses: dict, hoy: date = None) -> int:
    """Días desde la última carga (`cargado_en` más reciente)."""
    hoy = hoy or date.today()
    ultima = max(date.fromisoformat(e["cargado_en"]) for e in meses.values())
    return (hoy - ultima).days


def avisar_si_atrasado(meses: dict, hoy: date = None, emisor=None) -> bool:
    """Registra un `[COTEJO_MANUAL]` si pasaron más de 45 días sin carga nueva.

    El pipeline no puede cargar este dato solo: el aviso es el recordatorio.
    `emisor` reemplaza a `cotejo_manual.registrar` en las pruebas."""
    hoy = hoy or date.today()
    dias = dias_sin_carga(meses, hoy)
    if dias <= DIAS_SIN_CARGA_AVISO:
        return False
    if emisor is None:
        import sys
        scripts = str(Path(__file__).resolve().parents[2])
        if scripts not in sys.path:
            sys.path.append(scripts)
        from cotejo_manual import registrar as emisor
    ultimo = max(meses)
    emisor("alquiler_udesa_real", f"último mes cargado: {ultimo}",
           f"Pasaron {dias} días sin cargar el informe mensual de UdeSA - Mercado Libre "
           "(el pipeline no puede leerlo solo). El indicador sigue con el último valor, "
           "como desactualizado. Leer el PDF de AMBA del mes y cargarlo con "
           "scripts/vida_cotidiana/cargar_alquiler_udesa.py (guía en el README).",
           URL_PAGINA)
    return True


def fetch_alquiler_udesa() -> dict:
    """Colector del pipeline: la tarjeta con el último mes cargado + el aviso de atraso."""
    meses = leer_registro()
    avisar_si_atrasado(meses)
    return {"alquiler_udesa_real": tarjeta(meses)}
