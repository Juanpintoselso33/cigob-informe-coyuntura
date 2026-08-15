"""Espeja en BigQuery los outputs ya publicados del informe.

BigQuery es AGUAS ABAJO y de una sola dirección: lee `web/src/data/informe.json`
y `output/series/*.csv` —los mismos artefactos que publica el sitio, después de
que pasaron los gates— y los escribe en BQ. El pipeline nunca lee de BigQuery.
Es deliberado: los gates G1-G7 y la suite de tests protegen los números
publicados, y un camino paralelo hacia los datos no debe poder esquivarlos.

Seis tablas. Las cinco de snapshot llevan `generated_at` como clave de corrida,
así que se ACUMULAN: los CSV ya dan la historia de las series, pero los pesos,
puntajes, bandas y la composición de cada dimensión sólo existen como "la
versión de hoy" más el historial de git. Guardar una fila por corrida convierte
eso en algo consultable — se puede preguntar cómo cambió la composición del
ITCM, no sólo su valor.

    # ver qué se subiría, sin tocar BigQuery ni pedir credenciales
    python scripts/bigquery_export.py --dry-run

    # subir
    python scripts/bigquery_export.py

Corre como último paso del pipeline nocturno, después de los gates: a BigQuery
sólo llega lo que ya pasó G1-G7 y los tests. Va con `continue-on-error` porque
publicar el informe es el camino crítico y una caída de BigQuery no puede
tumbar la corrida.

Requiere GOOGLE_APPLICATION_CREDENTIALS y facturación habilitada en el proyecto:
el sandbox de BigQuery borra las tablas a los 60 días y rechaza DML, lo que
anula el objetivo de tener un archivo histórico.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "web" / "src" / "data" / "informe.json"
DIR_SERIES = RAIZ / "output" / "series"

PROYECTO_POR_DEFECTO = "cigob-analytics"
DATASET_POR_DEFECTO = "informe_coyuntura"
UBICACION = "southamerica-east1"  # São Paulo: la región más cercana a AR

# El nombre del CSV es el cinturón. espiritu_epoca no tiene serie propia.
CINTURONES_CON_SERIE = {"macro", "politica", "gestion", "vida_cotidiana"}


def _indice_de(cinturon: dict) -> tuple[str | None, dict | None]:
    """Devuelve (sigla, bloque) del índice paramétrico del cinturón.

    espiritu_epoca no tiene paramétrica, así que devuelve (None, None) en vez
    de reventar: es un caso legítimo, no un dato faltante.
    """
    for clave, valor in cinturon.items():
        if clave.startswith(("itc", "itv")) and isinstance(valor, dict) and "valor" in valor:
            return clave.upper(), valor
    return None, None


def construir_filas(snapshot: dict) -> dict[str, list[dict]]:
    """Aplana el snapshot anidado en las seis tablas."""
    gen = snapshot["generated_at"]
    filas: dict[str, list[dict]] = {
        "corridas": [],
        "cinturones": [],
        "dimensiones": [],
        "indicadores": [],
        "validacion_cruzada": [],
        "series": [],
    }

    filas["corridas"].append(
        {
            "generated_at": gen,
            "schema_version": snapshot.get("schema_version"),
            "period": snapshot.get("period"),
            "score_global": snapshot.get("score_global"),
            "barbarismo_activo": snapshot.get("barbarismo_activo"),
            "alerta_multicinturon": snapshot.get("alerta_multicinturon"),
            "flags": json.dumps(snapshot.get("flags", []), ensure_ascii=False),
        }
    )

    for nombre_c, c in snapshot.get("cinturones", {}).items():
        sigla, indice = _indice_de(c)
        filas["cinturones"].append(
            {
                "generated_at": gen,
                "cinturon": nombre_c,
                "score": c.get("score"),
                "estado": c.get("estado"),
                "barbarismo_riesgo": c.get("barbarismo_riesgo"),
                "alerta": c.get("alerta"),
                "indice_sigla": sigla,
                "indice_valor": (indice or {}).get("valor"),
                "banda": (indice or {}).get("banda"),
                "banda_legible": (indice or {}).get("banda_legible"),
            }
        )

        # Pesos y puntajes viven en el índice; el detalle del dato (fuente,
        # fecha, frescura) vive en cinturon["indicadores"]. Se cruzan por clave.
        detalle = c.get("indicadores", {}) or {}
        for nombre_d, d in ((indice or {}).get("dimensiones", {}) or {}).items():
            filas["dimensiones"].append(
                {
                    "generated_at": gen,
                    "cinturon": nombre_c,
                    "indice_sigla": sigla,
                    "dimension": nombre_d,
                    "nombre": d.get("nombre"),
                    "peso": d.get("peso"),
                    "puntaje": d.get("puntaje"),
                    "peso_efectivo": d.get("peso_efectivo"),
                    "critica": bool(d.get("critica")),
                }
            )
            for nombre_i, i in (d.get("indicadores", {}) or {}).items():
                det = detalle.get(nombre_i, {}) or {}
                filas["indicadores"].append(
                    {
                        "generated_at": gen,
                        "cinturon": nombre_c,
                        "dimension": nombre_d,
                        "indicador": nombre_i,
                        "valor": i.get("valor", det.get("valor")),
                        "unidad": det.get("unidad"),
                        "fuente": det.get("fuente"),
                        "fecha_dato": det.get("fecha_dato"),
                        "desactualizado": bool(det.get("desactualizado")),
                        "en_indice": True,
                        "peso": i.get("peso"),
                        "peso_efectivo": i.get("peso_efectivo"),
                        "puntaje_banda": i.get("puntaje_banda"),
                        "puntaje_aplicado": i.get("puntaje_aplicado"),
                        "aporte_score": det.get("aporte_score"),
                    }
                )

        # Indicadores del cinturón que NO entran al índice: se registran igual,
        # si no desaparecen del archivo y no se puede distinguir "fuera del
        # índice" de "nunca existió".
        en_indice = {f["indicador"] for f in filas["indicadores"] if f["cinturon"] == nombre_c}
        for nombre_i, det in detalle.items():
            if nombre_i in en_indice:
                continue
            filas["indicadores"].append(
                {
                    "generated_at": gen,
                    "cinturon": nombre_c,
                    "dimension": det.get("dimension"),
                    "indicador": nombre_i,
                    "valor": det.get("valor"),
                    "unidad": det.get("unidad"),
                    "fuente": det.get("fuente"),
                    "fecha_dato": det.get("fecha_dato"),
                    "desactualizado": bool(det.get("desactualizado")),
                    "en_indice": bool(det.get("en_indice")),
                    "peso": None,
                    "peso_efectivo": det.get("peso_efectivo"),
                    "puntaje_banda": det.get("puntaje_banda"),
                    "puntaje_aplicado": None,
                    "aporte_score": det.get("aporte_score"),
                }
            )

    for fila in (snapshot.get("validacion_cruzada", {}) or {}).get("filas", []):
        propio = fila.get("propio")
        for ancla, v in fila.items():
            if not isinstance(v, dict):
                continue
            filas["validacion_cruzada"].append(
                {
                    "generated_at": gen,
                    "indice": fila.get("indice"),
                    "ancla": ancla,
                    "r": v.get("r"),
                    "n": v.get("n"),
                    "rd": v.get("rd"),
                    "es_propio": ancla == propio,
                }
            )

    for csv_path in sorted(DIR_SERIES.glob("*.csv")):
        cinturon = csv_path.stem
        if cinturon not in CINTURONES_CON_SERIE:
            continue
        with csv_path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if not r.get("fecha") or not r.get("indicador"):
                    continue
                try:
                    valor = float(r["valor"]) if r.get("valor") not in (None, "") else None
                except ValueError:
                    valor = None
                filas["series"].append(
                    {
                        "fecha": r["fecha"],
                        "cinturon": cinturon,
                        "indicador": r["indicador"],
                        "valor": valor,
                        "unidad": r.get("unidad"),
                        "fuente": r.get("fuente"),
                    }
                )

    return filas


def _serie_mensual(obj) -> list[tuple[str, float | None]]:
    """{'2024-01': 30.4, ...} -> [('2024-01', 30.4), ...], salteando lo no numérico."""
    if not isinstance(obj, dict):
        return []
    salida = []
    for periodo, valor in obj.items():
        if isinstance(valor, (int, float)):
            salida.append((periodo, float(valor)))
    return salida


def construir_filas_analisis(gen: str) -> dict[str, list[dict]]:
    """Aplana los artefactos de output/*.json que produce el análisis.

    Todo lleva `generated_at` de la corrida del snapshot: así una correlación
    queda atada a la versión del índice con la que se calculó, que es lo único
    que la hace interpretable después.
    """
    filas: dict[str, list[dict]] = {k: [] for k in (
        "series_indices", "series_anclas", "correlaciones", "redundancia",
        "redundancia_matriz", "redundancia_pares", "sensibilidad",
        "sensibilidad_leave_one_out", "sensibilidad_experimentos",
        "revision_bandas", "out_of_sample", "procedencia_anclas",
        "panel_validacion", "giros",
    )}

    def leer(nombre: str):
        ruta = RAIZ / "output" / f"{nombre}.json"
        if not ruta.exists():
            return None
        return json.loads(ruta.read_text(encoding="utf-8"))

    ve = leer("validacion_externa") or {}

    for clave, valor in ve.items():
        # serie_itcm, serie_itvc_sin_icc, ... -> series reconstruidas del índice
        if clave.startswith("serie_"):
            variante = clave[len("serie_"):]
            for periodo, v in _serie_mensual(valor):
                filas["series_indices"].append(
                    {"generated_at": gen, "serie": variante, "periodo": periodo, "valor": v}
                )
        # merval_usd_mensual, epu_argentina_mensual, ... -> anclas externas
        elif clave.endswith("_mensual"):
            for periodo, v in _serie_mensual(valor):
                filas["series_anclas"].append(
                    {"generated_at": gen, "ancla": clave[: -len("_mensual")], "periodo": periodo, "valor": v}
                )
        # correlaciones, correlaciones_itcm, correlaciones_brecha_obra_publica
        elif clave.startswith("correlaciones") and isinstance(valor, dict):
            grupo = clave[len("correlaciones_"):] if "_" in clave else "itvc"
            for par, v in valor.items():
                if isinstance(v, dict) and "r" in v:
                    filas["correlaciones"].append(
                        {"generated_at": gen, "grupo": grupo, "par": par,
                         "r": v.get("r"), "n": v.get("n")}
                    )
        elif clave.startswith("redundancia_") and isinstance(valor, dict):
            indice = clave[len("redundancia_"):].upper()
            filas["redundancia"].append(
                {"generated_at": gen, "indice": indice, "umbral": valor.get("umbral"),
                 "n_indicadores": valor.get("n_indicadores"), "n_pares": valor.get("n_pares"),
                 "r_abs_medio": valor.get("r_abs_medio"), "share_altos": valor.get("share_altos"),
                 "share_bajos": valor.get("share_bajos"),
                 "pares_cruzados": valor.get("pares_cruzados")}
            )
            # La matriz se guarda en formato largo (una fila por par dirigido):
            # así se pivotea con SQL sin tener que conocer los indicadores de
            # antemano, que cambian cuando cambia la composición del índice.
            for a, fila_a in (valor.get("matriz") or {}).items():
                for b, r in (fila_a or {}).items():
                    if isinstance(r, (int, float)):
                        filas["redundancia_matriz"].append(
                            {"generated_at": gen, "indice": indice,
                             "indicador_a": a, "indicador_b": b, "r": float(r)}
                        )
            for p in (valor.get("pares_altos") or []):
                filas["redundancia_pares"].append({"generated_at": gen, "indice": indice, **p})

    for indice, perfil in (ve.get("panel_validacion") or {}).items():
        for e in (perfil or {}).get("perfil", []):
            filas["panel_validacion"].append({"generated_at": gen, "indice": indice.upper(), **e})

    for clave, valor in ve.items():
        if clave.startswith("giros_") and isinstance(valor, dict):
            indice = clave[len("giros_"):].upper()
            for g in valor.get("giros", []):
                filas["giros"].append({"generated_at": gen, "indice": indice, "serie": "propia", **g})
            for g in valor.get("giros_referencia", []):
                filas["giros"].append({"generated_at": gen, "indice": indice, "serie": "referencia", **g})

    sens = leer("sensibilidad") or {}
    for indice, s in sens.items():
        if indice.startswith("_") or not isinstance(s, dict):
            continue
        filas["sensibilidad"].append(
            {"generated_at": gen, "indice": indice.upper(),
             "valor_publicado": s.get("valor_publicado"),
             "valor_recomputado": s.get("valor_recomputado"),
             "tension": s.get("tension")}
        )
        for ind, v in (s.get("leave_one_out") or {}).items():
            filas["sensibilidad_leave_one_out"].append(
                {"generated_at": gen, "indice": indice.upper(), "indicador_excluido": ind,
                 "valor_sin_el": v,
                 "delta": None if v is None or s.get("valor_publicado") is None
                          else round(v - s["valor_publicado"], 4)}
            )
        for exp, v in (s.get("experimentos") or {}).items():
            if isinstance(v, dict):
                filas["sensibilidad_experimentos"].append(
                    {"generated_at": gen, "indice": indice.upper(), "experimento": exp, **v}
                )

    rb = leer("revision_bandas") or {}
    for f in rb.get("filas", []):
        filas["revision_bandas"].append({"generated_at": gen, **f})

    oos = leer("out_of_sample") or {}
    for e in oos.get("evaluados", []):
        fuera = e.get("fuera_de_muestra") or {}
        dentro = e.get("dentro_de_muestra") or {}
        filas["out_of_sample"].append(
            {"generated_at": gen, "corte": oos.get("corte"), "indicador": e.get("indicador"),
             "indice": e.get("indice"), "procedencia": e.get("procedencia"), "evaluable": True,
             **{f"fuera_{k}": v for k, v in fuera.items()},
             **{f"dentro_{k}": v for k, v in dentro.items()}}
        )
    for ne in oos.get("no_evaluables", []):
        item = ne if isinstance(ne, dict) else {"indicador": ne}
        filas["out_of_sample"].append(
            {"generated_at": gen, "corte": oos.get("corte"), "evaluable": False, **item}
        )

    pa = leer("procedencia_anclas") or {}
    for indice, bloque in (pa.get("por_indice") or {}).items():
        for d in (bloque or {}).get("detalle", []):
            filas["procedencia_anclas"].append({"generated_at": gen, "indice": indice, **d})

    return filas


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proyecto", default=os.environ.get("GCP_PROJECT", PROYECTO_POR_DEFECTO))
    parser.add_argument("--dataset", default=DATASET_POR_DEFECTO)
    parser.add_argument("--dry-run", action="store_true", help="arma las filas y no toca BigQuery")
    args = parser.parse_args()

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    filas = construir_filas(snapshot)
    filas.update(construir_filas_analisis(snapshot["generated_at"]))

    print(f"corrida generated_at={snapshot['generated_at']}\n")
    total = 0
    for tabla, rs in sorted(filas.items()):
        print(f"  {tabla:28} {len(rs):>6} filas")
        total += len(rs)
    print(f"  {'TOTAL':28} {total:>6} filas\n")

    if args.dry_run:
        for tabla, rs in sorted(filas.items()):
            if rs:
                print(f"  {tabla}: {json.dumps(rs[0], ensure_ascii=False)[:160]}")
        print("\n[dry-run, no se escribió nada]")
        return 0

    # Dos formas válidas de autenticar y el chequeo sólo miraba una: en CI la
    # credencial llega por GOOGLE_APPLICATION_CREDENTIALS (secret -> archivo
    # temporal), pero en una máquina local lo normal es
    # `gcloud auth application-default login`, que deja el ADC en el directorio
    # de configuración de gcloud y NO exporta ninguna variable. Con el chequeo
    # viejo, una corrida local con credenciales perfectamente válidas salía por
    # 2 sin intentar nada.
    if not _hay_credenciales():
        print("ERROR: sin credenciales de Google Cloud. Correr "
              "`gcloud auth application-default login` o exportar "
              "GOOGLE_APPLICATION_CREDENTIALS.", file=sys.stderr)
        print()
        print("EXPORT A BIGQUERY: FALLÓ — no se subió nada.")
        return 2

    from google.api_core.exceptions import Forbidden, NotFound
    from google.cloud import bigquery

    cliente = bigquery.Client(project=args.proyecto)
    ds_id = f"{args.proyecto}.{args.dataset}"
    ds = bigquery.Dataset(ds_id)
    ds.location = UBICACION
    cliente.create_dataset(ds, exists_ok=True)

    gen = snapshot["generated_at"]
    for tabla, rs in filas.items():
        if not rs:
            print(f"  {tabla}: sin filas, se omite")
            continue
        destino = f"{ds_id}.{tabla}"

        if tabla == "series":
            # La serie completa se reemplaza: son 6k filas y el CSV es la
            # verdad. Acumular versiones acá no aporta y duplicaría.
            disposicion = bigquery.WriteDisposition.WRITE_TRUNCATE
        else:
            # Re-correr la MISMA corrida no debe duplicar: se borran sus filas
            # antes de insertar. Las corridas anteriores no se tocan.
            #
            # Este error NO se traga. La primera versión hacía `except: pass` y
            # el DELETE fallaba con 403 (el free tier de BigQuery no permite
            # DML): el script imprimía "listo" mientras duplicaba cada fila.
            # Sólo se tolera que la tabla no exista todavía.
            try:
                cliente.query(
                    f"DELETE FROM `{destino}` WHERE generated_at = @gen",
                    job_config=bigquery.QueryJobConfig(
                        query_parameters=[bigquery.ScalarQueryParameter("gen", "STRING", gen)]
                    ),
                ).result()
            except NotFound:
                pass  # todavía no existe; la crea el load de abajo
            except Forbidden as e:
                print(
                    f"\nERROR: no se pudo limpiar la corrida en {tabla}: {e}\n"
                    "  Si es 'billingNotEnabled', el free tier no permite DML y\n"
                    "  reintentar DUPLICARIA las filas. Habilitá facturación en el\n"
                    "  proyecto y volvé a correr. No se escribió nada.",
                    file=sys.stderr,
                )
                return 3
            disposicion = bigquery.WriteDisposition.WRITE_APPEND

        job = cliente.load_table_from_json(
            rs,
            destino,
            job_config=bigquery.LoadJobConfig(
                write_disposition=disposicion,
                autodetect=True,
            ),
        )
        job.result()
        print(f"  {tabla:20} {len(rs):>6} filas -> {destino}")

    # El sandbox de BigQuery fuerza expiración a 60 días, lo que convierte el
    # archivo histórico en una bomba de tiempo. Con facturación habilitada esto
    # la saca; en sandbox falla y se avisa, no se rompe la corrida.
    quitadas, con_expiracion = 0, []
    for t in cliente.list_tables(ds_id):
        tabla_obj = cliente.get_table(t)
        vence = tabla_obj.expires  # se guarda ANTES de mutar el objeto
        if vence is None:
            continue
        try:
            tabla_obj.expires = None
            cliente.update_table(tabla_obj, ["expires"])
            quitadas += 1
        except Exception:
            con_expiracion.append((t.table_id, vence))

    if quitadas:
        print(f"\nexpiración quitada de {quitadas} tablas")
    if con_expiracion:
        print(
            f"\n  AVISO: {len(con_expiracion)} tablas EXPIRAN "
            f"(la primera, {min(e for _, e in con_expiracion):%Y-%m-%d}).\n"
            "  Es el sandbox de BigQuery: sin facturación habilitada en el proyecto\n"
            "  borra todo a los 60 días. Habilitá facturación y volvé a correr esto."
        )

    # La vista comparable se REDEFINE en cada corrida (ADR-0208). Su SQL se
    # genera desde config.PESOS_CINTURONES, así que si cambian los pesos —o el
    # conjunto de cinturones, como pasó al sacar espíritu de época— la vista
    # tiene que rehacerse o queda promediando un perímetro que ya no existe.
    # ADR-0207 la dejó de corrida manual y eso era un cabo suelto: nadie se
    # acuerda, y ningún test lo agarra porque vive en BigQuery. Acá no hay que
    # acordarse. `CREATE OR REPLACE VIEW` es metadata: no escanea datos, no
    # cuesta y es idempotente.
    try:
        import bq_vista_comparable
        cliente.query(
            bq_vista_comparable.sql_de_la_vista(args.proyecto, args.dataset),
            location=UBICACION,
        ).result()
        print(f"\nvista {bq_vista_comparable.VISTA} redefinida con los pesos vigentes")
    except Exception as e:
        # No tumba la corrida: el archivo ya está subido, que es lo que importa.
        print(f"\n  AVISO: no se pudo redefinir la vista comparable: {e}")

    print("\nlisto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
