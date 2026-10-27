"""Empleadores inscriptos en ARCA, del padrón público sin nombres (ADR-0389).

ARCA publica un zip con un registro de ancho fijo por CUIT, sin nombres, que
reemplaza cada semana. Cada registro tiene 21 caracteres:

    CUIT (1-11) · ganancias (12-13) · IVA (14-15) · monotributo (16-17)
    · integrante de sociedad (18) · empleador (19, 'S'/'N'/blanco)
    · actividad del monotributo (20-21)

Se cuenta sin cargar el archivo en memoria y sin guardarlo en el repo: el zip
baja a un temporal que se borra. **Nunca se guarda un CUIT.** Lo único que queda
es el registro versionado `data/vida/arca_empleadores.json`, un valor por mes
(el del último archivo visto en el mes), porque ARCA no conserva historia.

La marca de empleador es de inscripción, no de empleo efectivo: cuenta CUIT con
la marca activa, tengan o no personal declarado.
"""
import json
import logging
import os
import re
import tempfile
import zipfile
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

REGISTRO = Path(__file__).resolve().parents[3] / "data" / "vida" / "arca_empleadores.json"
URL_ZIP = "https://www.afip.gob.ar/genericos/cInscripcion/archivos/SINapellidoNombreDenominacion.zip"
URL_PAGINA = "https://www.afip.gob.ar/genericos/cInscripcion/archivoCompleto.asp"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
HTTP_TIMEOUT = (30, 120)  # conexión, lectura entre bloques

# Disposición de un registro: (largo, índice de la marca de empleador, índice
# donde empieza el monotributo). El archivo CON nombres (sólo para el backfill
# del Wayback) agrega una denominación de 30 caracteres antes de esos campos.
LAYOUT_SIN_NOMBRES = (21, 18, 15)
LAYOUT_CON_NOMBRES = (51, 48, 45)
JURIDICAS = ("30", "33", "34")
# Proporción plausible de empleadores sobre el total de CUIT: en oct-2026 es
# 8,2 %. Fuera de 2-30 % el formato cambió o se leyó mal.
PROPORCION_MIN, PROPORCION_MAX = 0.02, 0.30
MIN_REGISTROS = 1_000_000
MESES_PARA_PUNTUAR = 12
MESES_ES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
RE_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
RE_FECHA_NOMBRE = re.compile(r"\.(\d{8})\.tmp$")
CAMPOS = ("empleadores", "juridicas", "humanas", "monotributistas", "blanco", "cuit_total")
MES_INICIO_MENSUAL = "2026-10"  # desde acá el registro es mensual; antes son copias sueltas del Wayback


class FormatoInesperado(ValueError):
    """El archivo no tiene el formato documentado del padrón."""


def contar(lineas, minimo_registros: int = MIN_REGISTROS, layout=LAYOUT_SIN_NOMBRES) -> dict:
    """Cuenta sobre un iterable de líneas (bytes o str, con o sin salto).

    Devuelve los cinco conteos. Levanta FormatoInesperado si el archivo no
    cumple el formato: largo de registro, CUIT numérico, marca en {S,N,blanco}
    y una proporción plausible de empleadores."""
    largo, i_emp, i_mono = layout
    total = emp = jur = hum = mono = blanco = 0
    for linea in lineas:
        if isinstance(linea, bytes):
            linea = linea.decode("latin-1")
        linea = linea.rstrip("\r\n")
        if not linea:
            continue
        if len(linea) != largo:
            raise FormatoInesperado(
                f"registro {total + 1} de {len(linea)} caracteres (se esperan {largo})")
        if not linea[:11].isdigit():
            raise FormatoInesperado(f"registro {total + 1}: el CUIT no es numérico")
        marca = linea[i_emp]
        if marca not in ("S", "N", " "):
            raise FormatoInesperado(f"registro {total + 1}: marca de empleador inesperada {marca!r}")
        total += 1
        if marca == " ":
            blanco += 1
        if marca == "S":
            emp += 1
            if linea[:2] in JURIDICAS:
                jur += 1
            else:
                hum += 1
                if linea[i_mono:i_mono + 2] != "NI":
                    mono += 1
    if total < minimo_registros:
        raise FormatoInesperado(f"sólo {total} registros (se esperan al menos {minimo_registros})")
    if not PROPORCION_MIN <= emp / total <= PROPORCION_MAX:
        raise FormatoInesperado(f"{emp} empleadores sobre {total} CUIT: proporción implausible")
    return {"empleadores": emp, "juridicas": jur, "humanas": hum,
            "monotributistas": mono, "blanco": blanco, "cuit_total": total}


def _lineas(fileobj, bloque=1 << 20):
    """Líneas de un archivo binario leído por bloques (memoria acotada)."""
    resto = b""
    while True:
        datos = fileobj.read(bloque)
        if not datos:
            break
        partes = (resto + datos).split(b"\n")
        resto = partes.pop()
        yield from partes
    if resto:
        yield resto


def contar_zip(path_zip, minimo_registros: int = MIN_REGISTROS, layout=LAYOUT_SIN_NOMBRES) -> tuple:
    """(conteos, fecha_archivo ISO o None) del zip ya bajado."""
    with zipfile.ZipFile(path_zip) as z:
        miembros = [i for i in z.infolist() if not i.is_dir()]
        if len(miembros) != 1:
            raise FormatoInesperado(f"el zip trae {len(miembros)} archivos (se espera 1)")
        m = miembros[0]
        fecha = None
        r = RE_FECHA_NOMBRE.search(m.filename)
        if r:
            fecha = datetime.strptime(r.group(1), "%Y%m%d").date().isoformat()
        with z.open(m) as f:
            return contar(_lineas(f), minimo_registros, layout), fecha


def descargar_y_contar(url: str = URL_ZIP, sesion=None) -> dict:
    """Baja el zip en streaming a un temporal, cuenta y lo borra.

    Devuelve {fecha_archivo, empleadores, juridicas, humanas, monotributistas,
    cuit_total}. Falla con excepción clara si no baja o el formato no cierra."""
    sesion = sesion or requests
    fd, tmp = tempfile.mkstemp(suffix=".zip", prefix="padron_arca_")
    os.close(fd)
    try:
        with sesion.get(url, headers=HTTP_HEADERS, stream=True, timeout=HTTP_TIMEOUT) as r:
            r.raise_for_status()
            modificado = r.headers.get("Last-Modified")
            with open(tmp, "wb") as out:
                for bloque in r.iter_content(1 << 20):
                    out.write(bloque)
        conteos, fecha = contar_zip(tmp)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if fecha is None and modificado:
        try:
            fecha = parsedate_to_datetime(modificado).date().isoformat()
        except (TypeError, ValueError):
            pass
    if fecha is None:
        raise FormatoInesperado("no se pudo saber la fecha del archivo (ni nombre ni Last-Modified)")
    return {"fecha_archivo": fecha, **conteos}


# ── Registro versionado ──────────────────────────────────────────────────────

def validar_registro(registro: dict) -> dict:
    meses = registro.get("meses")
    if not isinstance(meses, dict) or not meses:
        raise ValueError("registro sin «meses»")
    for mes, e in meses.items():
        if not RE_MES.match(str(mes)):
            raise ValueError(f"mes inválido: {mes!r}")
        date.fromisoformat(str(e.get("fecha_archivo")))
        if str(e["fecha_archivo"])[:7] != mes:
            raise ValueError(f"{mes}: la fecha del archivo es de otro mes")
        for c in CAMPOS:
            if isinstance(e.get(c), bool) or not isinstance(e.get(c), int) or e[c] < 0:
                raise ValueError(f"{mes}: «{c}» no es un entero")
        if e["juridicas"] + e["humanas"] != e["empleadores"]:
            raise ValueError(f"{mes}: jurídicas + humanas no suman los empleadores")
    return meses


def leer_registro(path: Path = REGISTRO) -> dict:
    return validar_registro(json.loads(Path(path).read_text(encoding="utf-8")))


def anotar(meses: dict, conteo: dict) -> dict:
    """Copia de `meses` con el conteo en su mes: un valor por mes, el del
    archivo más nuevo visto en ese mes (uno más viejo no lo pisa)."""
    mes = conteo["fecha_archivo"][:7]
    nuevo = {k: conteo[k] for k in ("fecha_archivo",) + CAMPOS}
    if conteo.get("url"):
        nuevo["url"] = conteo["url"]
    out = dict(meses)
    previo = out.get(mes)
    if previo is None or previo["fecha_archivo"] <= nuevo["fecha_archivo"]:
        out[mes] = nuevo
    return dict(sorted(out.items()))


def guardar_registro(meses: dict, path: Path = REGISTRO) -> None:
    validar_registro({"meses": meses})
    cuerpo = {
        "fuente": URL_PAGINA,
        "nota": "Un valor por mes: el del último archivo visto. ARCA reemplaza el archivo cada "
                "semana y no conserva historia, por eso el registro mensual arranca en oct-2026; lo anterior son tres copias del Wayback (ver `url`, reproducibles con scripts/vida_cotidiana/padron_arca_backfill.py). "
                "Cuenta CUIT con la marca de empleador activa (ADR-0389). Sin CUIT individuales.",
        "meses": meses,
    }
    Path(path).write_text(json.dumps(cuerpo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ── Texto de la card ─────────────────────────────────────────────────────────

def _n(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def _fecha(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day}-{MESES_ES[d.month - 1]}-{d.year}"


def texto_card(meses: dict) -> str:
    """La oración que la card de ocupacion_eph muestra. No puntúa."""
    if not meses:
        raise ValueError("registro vacío")
    ult_mes = max(meses)
    u = meses[ult_mes]
    t = (f"Empleadores inscriptos en ARCA: {_n(u['empleadores'])} ({_fecha(u['fecha_archivo'])}), "
         f"de los cuales {_n(u['juridicas'])} son personas jurídicas y {_n(u['humanas'])} personas "
         f"humanas ({_n(u['monotributistas'])} de ellas monotributistas)")
    previos = [m for m in meses if m < ult_mes]
    if previos:
        p = meses[max(previos)]
        dif = u["empleadores"] - p["empleadores"]
        pct = f"{abs(dif) / p['empleadores'] * 100:.1f}".replace(".", ",")
        signo = "+" if dif >= 0 else "−"
        t += (f"; contra {_fecha(p['fecha_archivo'])}: {signo}{_n(abs(dif))} ({signo}{pct}%), "
              f"humanas de {_n(p['humanas'])} a {_n(u['humanas'])} y jurídicas de {_n(p['juridicas'])} a {_n(u['juridicas'])}")
        if u["blanco"] != p["blanco"]:
            t += (f". Ojo: la marca en blanco (CUIT sin datos consistentes) pasó de {_n(p['blanco'])} a "
                  f"{_n(u['blanco'])}, así que una limpieza del padrón puede mover los conteos")
        t += ". No hay copia de dic-2023, así que no hay base del mandato"
    mensuales = sum(1 for m in meses if m >= MES_INICIO_MENSUAL)
    t += (". Es una marca de inscripción, no de empleo efectivo. No puntúa: lo hará con "
          f"{MESES_PARA_PUNTUAR} meses de registro mensual (lleva {mensuales}), con ADR propio.")
    return t


# ── Colector del pipeline ────────────────────────────────────────────────────

def fetch_padron_arca(path: Path = REGISTRO, descargar=descargar_y_contar) -> dict:
    """Baja el padrón, anota el mes en el registro y devuelve {meses, texto, fresco}.

    Si la red o el formato fallan, sigue con lo guardado y lo dice en el log:
    el dato no puntúa, así que no corresponde tumbar la corrida."""
    meses = leer_registro(path)
    fresco = False
    try:
        conteo = descargar()
        nuevos = anotar(meses, conteo)
        if nuevos != meses:
            guardar_registro(nuevos, path)
            meses = nuevos
        fresco = True
    except Exception as e:  # noqa: BLE001 — red, zip o formato: se sigue con lo guardado
        logger.error("padron_arca: no se pudo actualizar, sigo con lo guardado: %s", e)
    return {"meses": meses, "texto": texto_card(meses), "fresco": fresco}
