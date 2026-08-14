"""Sincroniza las dimensiones personalizadas de GA4 con lo que declara este archivo.

Un parámetro que se manda con gtag pero NO está dado de alta como dimensión
personalizada se guarda igual, pero no se puede usar en ningún informe de GA4.
O sea: agregar un parámetro en `web/src/lib/analytics.ts` sin agregarlo acá
produce datos invisibles.

Es idempotente: crea las que faltan, corrige nombre y descripción de las que
difieren, y no toca las que ya coinciden. Nunca borra — archivar una dimensión
en GA4 es irreversible para el histórico, así que eso queda a mano y a
conciencia.

    # ver qué haría, sin escribir
    uv run --with google-analytics-admin python scripts/ga4_dimensiones.py --dry-run

    # aplicar
    uv run --with google-analytics-admin python scripts/ga4_dimensiones.py

Requiere GOOGLE_APPLICATION_CREDENTIALS apuntando a la clave del service
account, y que ese service account tenga rol **Editor** sobre la propiedad
(con Lector alcanza para leer pero create/update devuelven 403).

La dependencia se pasa con `uv run --with` a propósito: es una herramienta de
configuración, no del pipeline de datos, y no tiene por qué instalarse en cada
corrida nocturna.
"""

from __future__ import annotations

import argparse
import os
import sys

PROPIEDAD_POR_DEFECTO = "548827028"  # CIGOB → Informe de Coyuntura

# Espejo de los parámetros que manda web/src/lib/analytics.ts. Si agregás uno
# allá, agregalo acá y corré el script.
DIMENSIONES = [
    {
        "parameter_name": "indicador",
        "display_name": "indicador",
        "description": "Clave del indicador del informe (ver_indicador, descargar_csv, ver_ficha)",
    },
    {
        "parameter_name": "cinturon",
        "display_name": "cinturon",
        "description": "Cinturon del informe: macro, politica, gestion, vida",
    },
    {
        "parameter_name": "dimension",
        "display_name": "dimension",
        "description": "Dimension del indice dentro del cinturon (ver_dimension, fijar_dimension)",
    },
    {
        "parameter_name": "estado",
        "display_name": "estado",
        # Ojo: es badgeEstado(), o sea CÓMO se obtiene el dato. No es la
        # frescura ni el semáforo estable/en_tension del cinturón.
        "description": "Modo de obtencion del dato: Automatico, Carga manual o Estimacion",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--propiedad", default=os.environ.get("GA4_PROPERTY_ID", PROPIEDAD_POR_DEFECTO))
    parser.add_argument("--dry-run", action="store_true", help="muestra los cambios sin escribir")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: falta GOOGLE_APPLICATION_CREDENTIALS", file=sys.stderr)
        return 2

    from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
    from google.analytics.admin_v1beta.types import CustomDimension
    from google.protobuf import field_mask_pb2

    cliente = AnalyticsAdminServiceClient()
    parent = f"properties/{args.propiedad}"

    existentes = {d.parameter_name: d for d in cliente.list_custom_dimensions(parent=parent)}
    print(f"propiedad {args.propiedad}: {len(existentes)} dimensiones existentes\n")

    creadas = actualizadas = iguales = 0
    for esperada in DIMENSIONES:
        param = esperada["parameter_name"]
        actual = existentes.get(param)

        if actual is None:
            print(f"  CREAR      {param}")
            if not args.dry_run:
                cliente.create_custom_dimension(
                    parent=parent,
                    custom_dimension=CustomDimension(
                        parameter_name=param,
                        display_name=esperada["display_name"],
                        description=esperada["description"],
                        scope=CustomDimension.DimensionScope.EVENT,
                    ),
                )
            creadas += 1
            continue

        difieren = [
            campo
            for campo in ("display_name", "description")
            if getattr(actual, campo) != esperada[campo]
        ]
        if not difieren:
            print(f"  OK         {param}")
            iguales += 1
            continue

        print(f"  ACTUALIZAR {param} ({', '.join(difieren)})")
        for campo in difieren:
            print(f"               antes: {getattr(actual, campo)}")
            print(f"               ahora: {esperada[campo]}")
        if not args.dry_run:
            cliente.update_custom_dimension(
                custom_dimension=CustomDimension(
                    name=actual.name,
                    display_name=esperada["display_name"],
                    description=esperada["description"],
                ),
                update_mask=field_mask_pb2.FieldMask(paths=difieren),
            )
        actualizadas += 1

    # Las que están en GA4 y no acá: se avisan, no se tocan.
    sobrantes = set(existentes) - {d["parameter_name"] for d in DIMENSIONES}
    for param in sorted(sobrantes):
        print(f"  AJENA      {param} (existe en GA4 y no en este archivo; no se toca)")

    sufijo = " [dry-run, no se escribió nada]" if args.dry_run else ""
    print(f"\ncreadas={creadas} actualizadas={actualizadas} sin_cambios={iguales}{sufijo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
