"""Segundo lector de los PDF de origen. Uso INTERNO, en MODO SOMBRA.

## Qué problema resuelve

Los indicadores que salen de un PDF los lee un parser de regex sobre el texto
aplanado por pdfplumber. Cuando la fuente mueve una columna, el parser no falla:
devuelve **el número de al lado**, en silencio, y ese número entra al índice.
`gate_calidad.py` no lo agarra —valida estructura, frescura y card-contra-serie,
no si el número es el que decía el documento— y los tests de reconciliación
tampoco, porque reconcilian el snapshot contra sí mismo.

Acá se lee el MISMO texto con un modelo y se comparan las dos lecturas. Es el
patrón que la industria llama *LLM challenge*: dos extracciones independientes, y
la discrepancia es la señal. No reemplaza al parser —el parser sigue siendo la
fuente del dato— y no vota: sólo avisa que las dos lecturas no coinciden.

## Por qué modo sombra

Porque todavía no sabemos la tasa de falsas alarmas sobre datos reales. En modo
sombra esto registra discrepancias y **siempre sale por 0**: no puede romper el
pipeline ni bloquear una publicación. Cuando haya un mes de historial se decide
si pasa a fallar de verdad, con el dato en la mano y no de arranque.

## Por qué este modelo y no otro (medido 2026-08-12)

Benchmark sobre estos mismos tres documentos, 3 corridas por modelo, contra la
verdad leída a mano (SAGYP además cierra por suma: 47,28+47,24+19,93 = 114,45):

    gemini-3.6-flash      27/27 correctos, consistente     ← este
    gemini-3.5-flash      27/27 correctos, consistente
    gemini-2.5-flash      24/27 · dice aviar=51,21, que es el valor de VACUNA
                          de 2025: agarra la columna de al lado, con seguridad
    gemini-2.5-flash-lite 15/27 · 12 nulos (quema los 65.535 tokens de salida)
    gemini-2.5-pro        27/27 vía BigQuery pero 22/27 vía Vertex directo,
                          y ahí encima INCONSISTENTE entre corridas

Esa última fila es la advertencia importante: el mismo model id da resultados
distintos según el harness. Si esto se reescribe para llamar de otra forma, hay
que volver a medirlo — no heredar el número de acá.

Se llama a Vertex directo y no por `AI.GENERATE` de BigQuery porque los endpoints
REGIONALES sólo ofrecen la familia 2.5, que se da de baja no antes del
2026-10-16. La generación actual sólo aparece con `location='global'`. Además así
no hace falta tabla intermedia ni conexión, y `informe_coyuntura` se queda en
`southamerica-east1` como manda ADR-0180.

Uso:
    python scripts/verificacion_pdf.py
    python scripts/verificacion_pdf.py --forzar     # ignora el caché de hash
    python scripts/verificacion_pdf.py --caso ciccra
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "output" / "verificacion_pdf"

MODELO = "gemini-3.6-flash"
# Los endpoints regionales no tienen la generación actual: ver el docstring.
UBICACION = "global"
PROYECTO = os.environ.get("GCP_PROJECT", "cigob-analytics")

# Tolerancia al comparar. No es holgura para el modelo: es que el parser y el
# documento pueden redondear distinto en el último decimal.
TOLERANCIA = 0.011


def _hay_credenciales() -> bool:
    """GOOGLE_APPLICATION_CREDENTIALS (CI) o el ADC de gcloud (local)."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    for base in (os.environ.get("CLOUDSDK_CONFIG"),
                 os.path.join(os.path.expanduser("~"), ".config", "gcloud"),
                 os.path.join(os.environ.get("APPDATA", ""), "gcloud")):
        if base and os.path.exists(os.path.join(base, "application_default_credentials.json")):
            return True
    return False


def comparar(parser: dict, modelo: dict, campos: dict,
             tolerancia: float = TOLERANCIA) -> list[dict]:
    """Las dos lecturas, campo por campo. Devuelve SÓLO las que no coinciden.

    Un campo que el modelo no pudo leer (None) NO es una discrepancia: es el
    modelo absteniéndose, que es su falla segura. Lo que importa es que las dos
    lecturas afirmen cosas distintas.
    """
    fuera = []
    for campo in campos:
        p, m = parser.get(campo), modelo.get(campo)
        if p is None or m is None:
            if p is None and m is not None:
                fuera.append({"campo": campo, "parser": None, "modelo": m,
                              "tipo": "el parser no leyó y el modelo sí"})
            continue
        try:
            if abs(float(p) - float(m)) > tolerancia:
                fuera.append({"campo": campo, "parser": float(p), "modelo": float(m),
                              "tipo": "discrepancia"})
        except (TypeError, ValueError):
            if str(p) != str(m):
                fuera.append({"campo": campo, "parser": p, "modelo": m,
                              "tipo": "discrepancia no numérica"})
    return fuera


def _huella(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def _estado_previo() -> dict:
    try:
        return json.loads((SALIDA / "estado.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def leer_con_modelo(texto: str, pedido: str, campos: dict, cliente=None) -> dict:
    """Le pide al modelo los mismos campos que saca el parser, como JSON.

    `response_schema` restringe la decodificación, así que el JSON no puede
    salir malformado: el modo de falla que queda es leer el número equivocado,
    no devolver basura. Por eso el benchmark midió números y no parseabilidad.
    """
    from google.genai import types

    esquema = {"type": "object", "required": list(campos),
               "properties": {k: {"type": "number"} for k in campos}}
    r = cliente.models.generate_content(
        model=MODELO,
        contents=pedido + "\n\n--- TEXTO DEL DOCUMENTO ---\n" + texto,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=esquema,
            max_output_tokens=8000))
    return json.loads(r.text) if r.text else {}


# ── Los casos ───────────────────────────────────────────────────────────────
# Cada caso dice cómo conseguir el PDF, cómo lo lee el parser de producción y
# qué se le pide al modelo. Las funciones de descarga y parseo se IMPORTAN de
# los colectores: si el colector cambia de URL o de parser, esto lo sigue solo.


def _cargar_colectores():
    """Import diferido y por ruta.

    `scripts/vida_cotidiana/` tiene su propio `config.py`. Meterlo en el sys.path
    a nivel módulo tapa el `config.py` de la raíz para todo el proceso — rompió
    doce módulos de test una vez (ver tests/test_consumo_carnes.py). Acá se carga
    por ruta y sólo cuando hace falta de verdad.
    """
    import importlib.util

    def por_ruta(nombre, ruta, extra_path=()):
        for p in extra_path:
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        spec = importlib.util.spec_from_file_location(nombre, ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    vc = RAIZ / "scripts" / "vida_cotidiana"
    col = vc / "collectors"
    return {
        "consumo_carnes": por_ruta("vp_consumo_carnes", col / "consumo_carnes.py", (vc,)),
        "ciccra": por_ruta("vp_ciccra", col / "ciccra.py", (vc,)),
    }


def casos() -> list[dict]:
    import requests
    from datetime import date
    import io
    import pdfplumber

    mods = _cargar_colectores()
    cc, cic = mods["consumo_carnes"], mods["ciccra"]
    sys.path.insert(0, str(RAIZ / "scripts"))
    import macro

    def bajar(url, headers):
        r = requests.get(url, headers=headers, timeout=90, verify=False)
        if r.status_code != 200 or len(r.content) < 3000:
            return None
        return r.content

    def texto_de(b):
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)

    def sagyp():
        b = bajar(cc.SAGYP_PDF_URL, cc.HTTP_HEADERS)
        if not b:
            return None, None
        t = texto_de(b)
        var = cc._variaciones(t)
        pares = cc._emparejar(cc._numeros(t), var)
        return t, {k: v[0] for k, v in pares.items()}

    def ciccra():
        hoy = date.today()
        for retro in range(1, 5):
            y, m = hoy.year, hoy.month - retro
            if m <= 0:
                m += 12
                y -= 1
            b = bajar(cic._url_pdf(y, m), cc.HTTP_HEADERS)
            if b:
                return texto_de(b), {"consumo_per_capita_vacuna": cic._extraer_per_capita(b)}
        return None, None

    def sdds():
        hoy = date.today()
        y, m = hoy.year, hoy.month
        for _ in range(4):
            b = bajar(macro.SDDS_URL_BASE.format(f"temp{m:02d}{y % 100:02d}"),
                      macro.HTTP_HEADERS)
            if b:
                s = macro._parse_sdds_content(b)
                if s:
                    return texto_de(b), {"activos_reserva_oficiales": s.get("brutas"),
                                         "prestamos_valores_depositos": s.get("prestamos_dep"),
                                         "posiciones_cortas": s.get("swaps"),
                                         "otros": s.get("repos")}
            m -= 1
            if m == 0:
                m, y = 12, y - 1
        return None, None

    return [
        {"clave": "sagyp", "obtener": sagyp,
         "campos": {"vacuna": 1, "aviar": 1, "porcina": 1, "total": 1},
         "pedido": ("Este PDF es un tablero de SAGYP con el consumo per capita promedio "
                    "movil de 12 meses de carnes en Argentina, en kg por habitante por "
                    "anio. Trae DOS anios: el actual y el anterior. Extrae los valores "
                    "del anio MAS RECIENTE para carne vacuna, carne aviar, carne porcina "
                    "y el total.")},
        {"clave": "ciccra", "obtener": ciccra,
         "campos": {"consumo_per_capita_vacuna": 1},
         "pedido": ("Este es el informe economico mensual de CICCRA sobre la industria de "
                    "la carne vacuna en Argentina. Extrae el CONSUMO PER CAPITA de carne "
                    "vacuna en kilos por anio (promedio movil de los ultimos 12 meses) "
                    "que informa el documento. Es un solo numero, en kilos/anio.")},
        {"clave": "sdds", "obtener": sdds,
         "campos": {"activos_reserva_oficiales": 1, "prestamos_valores_depositos": 1,
                    "posiciones_cortas": 1, "otros": 1},
         "pedido": ("Esta es la planilla SDDS de Reservas Internacionales y Liquidez en "
                    "Moneda Extranjera del BCRA, en millones de dolares. Extrae, con su "
                    "signo tal como figura: (1) 'A. Activos de reserva oficiales'; (2) el "
                    "TOTAL de la fila '1. Prestamos en moneda extranjera, valores, y "
                    "depositos' (la primera columna de esa fila); (3) el total de "
                    "'(a) Posiciones cortas'; (4) el total de la fila "
                    "'3. Otros (especificar)'.")},
    ]


def subir_a_bigquery(informe: list[dict], corrida: str) -> str | None:
    """Una fila por CAMPO comparado, con las dos lecturas y si coinciden.

    Va a BigQuery y no sólo al JSON local porque el JSON está gitignoreado: sin
    esto, el modo sombra acumula evidencia que nadie puede abrir. Se acumula por
    `generated_at`, igual que las tablas de snapshot (ADR-0180), así que la serie
    de discrepancias es consultable en el tiempo — que es exactamente el dato con
    el que después se decide si esto pasa a fallar de verdad.
    """
    try:
        from google.cloud import bigquery
    except ImportError:
        return None

    filas = []
    for caso in informe:
        disc = {d["campo"]: d for d in caso.get("discrepancias", [])}
        for campo, valor in (caso.get("parser") or {}).items():
            d = disc.get(campo)
            filas.append({
                "generated_at": corrida, "modelo": MODELO, "caso": caso["caso"],
                "campo": campo,
                "valor_parser": None if valor is None else float(valor),
                "valor_modelo": (None if (caso.get("modelo") or {}).get(campo) is None
                                 else float(caso["modelo"][campo])),
                "coincide": d is None,
                "tipo": (d or {}).get("tipo"),
                "reusado": bool(caso.get("reusado")),
            })
    if not filas:
        return None
    tabla = f"{PROYECTO}.informe_coyuntura.verificacion_pdf"
    cliente = bigquery.Client(project=PROYECTO)
    cliente.load_table_from_json(filas, tabla, job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        autodetect=True)).result()
    return tabla


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--caso", help="correr uno solo (sagyp | ciccra | sdds)")
    p.add_argument("--forzar", action="store_true",
                   help="re-consultar aunque el documento no haya cambiado")
    args = p.parse_args()

    if not _hay_credenciales():
        print("[i] verificacion_pdf: sin credenciales de Google Cloud, no se corre.")
        print("    (modo sombra: esto NO es un fallo del pipeline)")
        return 0

    from google import genai
    cliente = genai.Client(vertexai=True, project=PROYECTO, location=UBICACION)

    previo = _estado_previo()
    # El informe anterior, para que un caso OMITIDO por hash no borre su última
    # lectura real: si no, la segunda corrida del día deja `ultima.json` vacío y
    # se pierde justo la evidencia que este script existe para juntar.
    try:
        informe_previo = {c["caso"]: c for c in json.loads(
            (SALIDA / "ultima.json").read_text(encoding="utf-8")).get("casos", [])}
    except (OSError, json.JSONDecodeError, KeyError):
        informe_previo = {}
    estado, informe, total_disc = {}, [], 0

    for caso in casos():
        if args.caso and caso["clave"] != args.caso:
            continue
        clave = caso["clave"]
        try:
            texto, parser = caso["obtener"]()
        except Exception as e:
            print(f"  [!] {clave}: no se pudo obtener el documento ({type(e).__name__})")
            continue
        if not texto or not parser:
            print(f"  [!] {clave}: documento no disponible hoy")
            continue

        h = _huella(texto)
        if not args.forzar and previo.get(clave, {}).get("huella") == h:
            print(f"  [=] {clave}: el documento no cambió, no se consulta")
            estado[clave] = previo[clave]
            if clave in informe_previo:
                informe.append({**informe_previo[clave], "reusado": True})
            continue

        try:
            leido = leer_con_modelo(texto, caso["pedido"], caso["campos"], cliente)
        except Exception as e:
            # Un verificador que rompe la corrida es peor que no tener verificador.
            print(f"  [!] {clave}: falló la consulta al modelo ({type(e).__name__}), se omite")
            continue

        disc = comparar(parser, leido, caso["campos"])
        total_disc += len(disc)
        estado[clave] = {"huella": h, "discrepancias": len(disc)}
        informe.append({"caso": clave, "parser": parser, "modelo": leido,
                        "discrepancias": disc})
        if disc:
            print(f"  [!] {clave}: {len(disc)} discrepancia(s)")
            for d in disc:
                print(f"        {d['campo']}: parser={d['parser']}  modelo={d['modelo']}")
        else:
            print(f"  [ok] {clave}: las dos lecturas coinciden en "
                  f"{len(caso['campos'])} campo(s)")

    if informe:
        subida = subir_a_bigquery(informe, datetime.now().isoformat(timespec="seconds"))
        if subida:
            print(f"  → {subida}")

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "estado.json").write_text(
        json.dumps({**previo, **estado}, ensure_ascii=False, indent=1), encoding="utf-8")
    (SALIDA / "ultima.json").write_text(
        json.dumps({"generado": datetime.now().isoformat(timespec="seconds"),
                    "modelo": MODELO, "casos": informe},
                   ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"\n  {total_disc} discrepancia(s) · MODO SOMBRA: no altera el pipeline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
