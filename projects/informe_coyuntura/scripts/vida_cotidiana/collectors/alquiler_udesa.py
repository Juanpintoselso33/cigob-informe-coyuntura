"""Alquiler real a partir de UdeSA - Mercado Libre Inmuebles (ADR-0386).

La fuente no tiene serie descargable: publica un PDF por mes en una carpeta de
Google Drive y las cifras viven en la prosa del informe. Por eso la carga es
**manual, una vez por mes** (`cargar_alquiler_udesa.py`), y este módulo sólo lee
el registro versionado `data/vida/alquiler_udesa.json`, lo valida y calcula.

    real(t) = (1 + alquiler_nominal_interanual(t)) / (1 + IPC_interanual(t)) − 1

El IPC es el nivel general del GBA de la planilla original del INDEC (la misma
que usa `alquiler_real`, ADR-0291), no el nacional: el alquiler de UdeSA es de
AMBA y dividir por un índice de otra plaza mezclaría dos mercados.

Componente del ITVC: `100 − real` (en puntos porcentuales). 100 = el alquiler
publicado subió igual que los precios en el año; por debajo de 100, se encareció
en términos reales (deterioro). No es un nivel contra el 4T-2023 como los demás
componentes de precios: la fuente sólo da variaciones interanuales y no se
encadenan (ADR-0386).

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
# Puntos de índice por punto porcentual de encarecimiento real.
PUNTOS_POR_PP = 1.0


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
    if mensual is not None and (isinstance(mensual, bool) or not isinstance(mensual, (int, float))
                                 or not -60.0 <= mensual <= 100.0):
        raise ValueError(f"{mes}: intermensual inválido: {mensual!r}")
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


def ipc_interanual_pct(niveles_general: dict, mes: str):
    """% interanual del nivel general en `mes`, o None si falta el mes o su año previo."""
    previo = f"{int(mes[:4]) - 1}{mes[4:]}"
    actual, anterior = niveles_general.get(mes), niveles_general.get(previo)
    if not actual or not anterior:
        return None
    return (actual / anterior - 1) * 100.0


def real_interanual_pct(nominal_pct: float, ipc_pct: float) -> float:
    """Variación real: (1 + nominal) / (1 + IPC) − 1, en %."""
    return ((1 + nominal_pct / 100.0) / (1 + ipc_pct / 100.0) - 1) * 100.0


def indice_componente(real_pct: float) -> float:
    """100 − real: 100 = el alquiler siguió a los precios; < 100 = más caro en términos reales."""
    return round(100.0 - PUNTOS_POR_PP * real_pct, 1)


def serie(meses: dict, niveles_general: dict) -> list:
    """[{mes, nominal, ipc, real}] ascendente, sólo meses con interanual cargado Y IPC publicado.

    Un mes sin carga no se interpola: queda fuera y la serie conserva el último
    punto como desactualizado (lo vigila MAX_DIAS)."""
    out = []
    for mes in sorted(meses):
        nominal = meses[mes].get("interanual_deptos_amba_pct")
        if nominal is None:
            continue
        ipc = ipc_interanual_pct(niveles_general, mes)
        if ipc is None:
            continue
        out.append({"mes": mes, "nominal": nominal, "ipc": round(ipc, 2),
                    "real": round(real_interanual_pct(nominal, ipc), 2)})
    return out


def tarjeta(meses: dict = None, niveles_general: dict = None) -> dict:
    """Último punto real: {valor, fecha, nominal_pct, ipc_pct, mes, fuente_url}."""
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
        raise ValueError("alquiler_udesa: ningún mes con interanual cargado e IPC publicado")
    u = pts[-1]
    return {"valor": u["real"], "fecha": u["mes"] + "-01", "nominal_pct": u["nominal"],
            "ipc_pct": u["ipc"], "indice": indice_componente(u["real"]),
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
