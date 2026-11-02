"""Series del INDEC leídas de su propia API, el Catálogo API-INDEC (ADR-0417, ADR-0418).

La API de series de datos.gob.ar es una copia del INDEC que llega tarde: medido el
2-nov-2026, el EMAE y el índice de salarios llegaban ahí a julio cuando el INDEC
ya había publicado agosto, y sin la revisión que el INDEC publicó junto con agosto
(hasta 0,06 pp en la variación i.a. de marzo de 2026). La API del INDEC
(https://api.indec.gob.ar, en beta desde 2026) tiene la publicación vigente.

Las series se piden con el id de datos.gob.ar que reemplazan, así los colectores
no cambian: `datos_gob.get` deriva acá los pedidos de las series de `SERIES` y
recibe una respuesta con la misma forma (`data` = [[YYYY-MM-01, valor], …],
`meta`, `count`) y en las mismas unidades. Por eso cada serie lleva su escala: la
variación i.a. del EMAE viene del INDEC en %, y datos.gob.ar la daba en fracción.

Tres cosas de la API que no son obvias:

- Pide un token (`INDEC_API_TOKEN`, JWT de la cuenta de Juan). **Vence a los 6
  meses** —el primero, el 1-may-2027—, no a los 12 que dice su ayuda. Si la API
  lo rechaza, o la variable está vacía, se levanta `TokenRechazado` y no se
  vuelve a la copia: el colector
  falla, la card queda desactualizada y #monitor-alertas avisa en la primera
  corrida. El mensaje no dice "client error" a propósito: `aviso_slack` lo
  tomaría como un error de red y esperaría tres noches.
- El índice de salarios trae los valores como texto con coma decimal
  ("9467,78"); el EMAE, como números.
- Devuelve 1.000 filas por pedido como máximo: se pagina con `offset`.

Si la API no contesta por otra causa, `datos_gob.get` vuelve a la copia de
datos.gob.ar y lo anota en el log; `via()` dice de cuál salió cada serie, para que
la fuente de la card no mienta.
"""
import os

import requests

BASE = "https://api.indec.gob.ar/v1/"
PAGINA = 1000
TIMEOUT = 60
LIMITE_DATOS_GOB = 100      # el `limit` por defecto de datos.gob.ar

_EMAE = "estimador-mensual-de-actividad-economica-nivel-general"
_EMAE_SECTORES = "estimador-mensual-de-actividad-economica-sectores"
_INDICE_SECTOR = "Índice base 2004=100"

# id de datos.gob.ar → (servicio, filtros, escala que lleva el valor a las
# unidades de datos.gob.ar). Cada correspondencia se verificó contra la copia
# en todos los meses comunes (2-nov-2026); tests/test_indec_api.py la fija.
SERIES = {
    # EMAE, variación i.a. de la serie original (datos.gob.ar: fracción)
    "143.3_ICE_SERVIA_2004_A_25": (_EMAE, {"tipo_de_indicador_descripcion": "Var % interanual serie original"}, 0.01),
    # EMAE, los 15 sectores de actividad (índices originales). El 16.º código
    # del servicio, T_S (impuestos netos de subsidios), queda afuera como en macro.py.
    "11.3_ISOM_2004_M_39":  (_EMAE_SECTORES, {"codigo": "A", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_VIPAA_2004_M_5":  (_EMAE_SECTORES, {"codigo": "B", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_ISD_2004_M_26":   (_EMAE_SECTORES, {"codigo": "C", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_VMASD_2004_M_23": (_EMAE_SECTORES, {"codigo": "D", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_ITC_2004_M_21":   (_EMAE_SECTORES, {"codigo": "E", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_VMATC_2004_M_12": (_EMAE_SECTORES, {"codigo": "F", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_AGCS_2004_M_41":  (_EMAE_SECTORES, {"codigo": "G", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_P_2004_M_20":     (_EMAE_SECTORES, {"codigo": "H", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_EMC_2004_M_25":   (_EMAE_SECTORES, {"codigo": "I", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_IM_2004_M_25":    (_EMAE_SECTORES, {"codigo": "J", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_SEGA_2004_M_48":  (_EMAE_SECTORES, {"codigo": "K", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_C_2004_M_60":     (_EMAE_SECTORES, {"codigo": "L", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_CMMR_2004_M_10":  (_EMAE_SECTORES, {"codigo": "M", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_HR_2004_M_24":    (_EMAE_SECTORES, {"codigo": "N", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    "11.3_TAC_2004_M_60":   (_EMAE_SECTORES, {"codigo": "O", "tipo_de_indicador": _INDICE_SECTOR}, 1),
    # Índice de salarios, base oct-2016=100
    "149.1_TL_INDIIOS_OCTU_0_21": ("indice_salarios", {"codigo": "0", "tipo_de_indicador": "Indice"}, 1),    # nivel general
    "149.1_TL_REGIADO_OCTU_0_16": ("indice_salarios", {"codigo": "100", "tipo_de_indicador": "Indice"}, 1),  # total registrado
    "149.1_SOR_PUBICO_OCTU_0_14": ("indice_salarios", {"codigo": "120", "tipo_de_indicador": "Indice"}, 1),  # sector público
    # IPC nacional, base dic-2016=100 (ADR-0418). El nivel general ya se
    # completaba desde la planilla (ipc_indec.py); las aperturas se quedaban un
    # mes atrás, y `ipc_alimentos` (alimentos contra general) con ellas.
    "148.3_INIVELNAL_DICI_M_26":  ("ipc_nacional", {"region": "Nacional", "codigo": "0", "tipo_de_indicador": "Indice"}, 1),
    "148.3_INUCLEONAL_DICI_M_19": ("ipc_nacional", {"region": "Nacional", "codigo": "N", "tipo_de_indicador": "Indice"}, 1),
    "148.3_IREGULANAL_DICI_M_22": ("ipc_nacional", {"region": "Nacional", "codigo": "R", "tipo_de_indicador": "Indice"}, 1),
    "146.3_IALIMENNAL_DICI_M_45": ("ipc_nacional", {"region": "Nacional", "codigo": "01", "tipo_de_indicador": "Indice"}, 1),
    "146.3_IVIVIENNAL_DICI_M_52": ("ipc_nacional", {"region": "Nacional", "codigo": "04", "tipo_de_indicador": "Indice"}, 1),
    # Canastas básicas por adulto equivalente, GBA, pesos corrientes (ADR-0418)
    "150.1_CSTA_BARIA_0_D_26":    ("valorizacion_canastas_cba_cbt", {"region": "GBA", "codigo": "CBA", "tipo_de_indicador": "CBA"}, 1),
    "150.1_CSTA_BATAL_0_D_20":    ("valorizacion_canastas_cba_cbt", {"region": "GBA", "codigo": "CBT", "tipo_de_indicador": "CBT"}, 1),
}

# Parámetros de datos.gob.ar que esta lectura sabe responder. Con cualquier otro
# (una variación, un colapso, una página) el pedido sigue yendo a la copia.
PARAMETROS = {"ids", "format", "limit", "sort", "start_date", "metadata", "header"}

_cache: dict[str, list] = {}
_origen: dict[str, str] = {}
# Una vez que la API falló en este proceso, no se le vuelve a pedir: la vuelta a
# la copia parte los 15 sectores en 15 pedidos que pasan otra vez por acá, y con
# la API colgada eran 15 esperas de 30 s, más que el tope de macro (Codex).
_caida = False


class TokenRechazado(RuntimeError):
    """La API no aceptó el token (o no hay token en CI). No se vuelve a la copia."""


def atiende(params: dict) -> bool:
    ids = [i for i in str(params.get("ids", "")).split(",") if i]
    # Sin la variable (local sin .env, pytest) ni se intenta: va a la copia.
    # Vacía sí entra, para que `_token` la rechace.
    return (not _caida and "INDEC_API_TOKEN" in os.environ
            and bool(ids) and all(i in SERIES for i in ids)
            and set(params) <= PARAMETROS
            and str(params.get("format", "json")) == "json")


def via(series_id: str) -> str:
    """De dónde salió la última lectura de la serie, para la fuente de la card."""
    return ("Catálogo API-INDEC" if _origen.get(series_id) == "api"
            else "vía datos.gob.ar")


def marcar_copia(ids: str) -> None:
    """La API no respondió: esta serie y todo lo que siga en el proceso, a la copia."""
    global _caida
    _caida = True
    for sid in ids.split(","):
        _origen[sid] = "datos.gob.ar"


def _token() -> str:
    """El token, o "" si no está en el entorno (local sin .env, pytest).

    Definida pero vacía es otra cosa: es lo que deja GitHub cuando el workflow
    pide `secrets.INDEC_API_TOKEN` y el secreto no existe. Ahí se falla."""
    token = os.environ.get("INDEC_API_TOKEN")
    if token is not None and not token.strip():
        raise TokenRechazado("INDEC_API_TOKEN está vacío en la corrida: cargarlo "
                             "como secreto del repo")
    return (token or "").strip()


def _numero(valor):
    if valor is None or valor == "":
        return None
    return float(str(valor).replace(",", ".")) if isinstance(valor, str) else float(valor)


def _filas(series_id: str, timeout=None) -> list:
    """[[YYYY-MM-01, valor]] ascendente, con la escala de datos.gob.ar."""
    if series_id in _cache:
        return _cache[series_id]
    token = _token()
    if not token:
        raise RuntimeError("no hay INDEC_API_TOKEN en el entorno")
    servicio, filtros, escala = SERIES[series_id]
    consulta = {k: f"eq.{v}" for k, v in filtros.items()}
    filas, offset = [], 0
    while True:
        r = requests.get(BASE + servicio, timeout=timeout or TIMEOUT,
                         headers={"Authorization": f"Bearer {token}"},
                         params={**consulta, "order": "periodo", "limit": PAGINA, "offset": offset})
        if r.status_code in (401, 403):
            raise TokenRechazado(
                f"el Catálogo API-INDEC rechazó INDEC_API_TOKEN (HTTP {r.status_code}): "
                "vencido o inválido. Regenerarlo en https://api.indec.gob.ar "
                "(Gestionar la cuenta) y actualizar el secreto del repo")
        r.raise_for_status()
        pagina = r.json()
        for f in pagina:
            valor = _numero(f.get("valor"))
            periodo = str(f["periodo"])
            if valor is not None:
                filas.append([f"{periodo[:4]}-{periodo[4:6]}-01", valor * escala])
        if len(pagina) < PAGINA:
            break
        offset += PAGINA
    if not filas:
        raise ValueError(f"el Catálogo API-INDEC no trajo filas para {series_id}")
    filas.sort(key=lambda f: f[0])
    _cache[series_id] = filas
    return filas


class _Respuesta:
    """Respuesta con la forma de la de datos.gob.ar."""

    status_code = 200

    def __init__(self, cuerpo):
        self._cuerpo = cuerpo

    def raise_for_status(self):
        pass

    def json(self):
        return self._cuerpo


def get(params: dict, timeout=None) -> _Respuesta:
    """Responde un pedido de datos.gob.ar (`atiende(params)` verdadero) desde la API."""
    ids = str(params["ids"]).split(",")
    columnas, metas = [], []
    for sid in ids:
        filas = _filas(sid, timeout)
        columnas.append(dict((f, v) for f, v in filas))
        metas.append({"field": {"id": sid, "time_index_size": len(filas),
                                "time_index_end": filas[-1][0]}})
    desde = str(params.get("start_date") or "")[:10]
    fechas = sorted((f for f in set().union(*columnas) if f >= desde),
                    reverse=params.get("sort") == "desc")
    data = [[f] + [c.get(f) for c in columnas] for f in fechas]
    for sid in ids:
        _origen[sid] = "api"
    limite = int(params.get("limit", LIMITE_DATOS_GOB))
    return _Respuesta({"data": data[:limite], "count": len(data),
                       "meta": [{"frequency": "month"}] + metas})
