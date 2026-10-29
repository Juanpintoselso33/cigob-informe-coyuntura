"""Carga mensual del alquiler de UdeSA - Mercado Libre (ADR-0386).

Una vez por mes, cuando sale el PDF de AMBA en
https://www.udesa.edu.ar/indices-mercado-libre :

  1. Abrir el PDF de AMBA del mes y buscar el apartado ALQUILER.
  2. Copiar la frase que da la variación interanual de los DEPARTAMENTOS de AMBA
     en pesos corrientes (hoy: «Si consideramos la variación interanual
     (respecto a …), se observan cambios en el precio de alquiler en pesos
     corrientes de casas y departamentos del X% y Y%»). Ojo al orden: según el
     año el informe nombra primero casas o primero departamentos.
  3. Correr:

     .venv/bin/python scripts/vida_cotidiana/cargar_alquiler_udesa.py \\
         --mes 2026-10 --valor 19.8 \\
         --url "https://drive.google.com/file/d/<id>/view" \\
         --frase "Si consideramos la variación interanual …"

  3b. Cargar también `--intermensual <departamentos AMBA, %>` cuando el informe
     la dé: la reconstrucción del nivel (ADR-0411) la usa en los meses en que no
     hay interanual publicada.
  4. Commitear data/vida/alquiler_udesa.json. Si el informe del mes trae sólo la
     intermensual, se carga sólo --intermensual (sin --valor). Si no trae ninguna
     de las dos, NO se carga (no se interpola): se anota con --sin-dato y un motivo.

Valida el formato y rechaza un mes duplicado (usar --reemplazar para corregir
uno ya cargado). Nunca toca nada fuera del registro.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "collectors"))
import alquiler_udesa as au  # noqa: E402


def agregar(registro: dict, mes: str, valor, url: str, frase: str, hoy: date = None,
            intermensual=None, reemplazar: bool = False) -> dict:
    """Agrega (o reemplaza) un mes. Devuelve el registro; levanta ValueError si no valida."""
    hoy = hoy or date.today()
    meses = registro.setdefault("meses", {})
    if mes in meses and not reemplazar:
        raise ValueError(f"{mes} ya está cargado (usar --reemplazar para corregirlo)")
    entrada = {
        "interanual_deptos_amba_pct": valor,
        "intermensual_deptos_amba_pct": intermensual,
        "frase": frase.strip(),
        "url_pdf": url.strip(),
        "archivo": None,
        "cargado_en": hoy.isoformat(),
    }
    if valor is None and intermensual is None:
        raise ValueError("falta el valor: cargar --valor o --intermensual "
                         "(si el informe no trae ninguno, usar --sin-dato)")
    au.validar_entrada(mes, entrada)
    if mes > hoy.strftime("%Y-%m"):
        raise ValueError(f"{mes} es un mes futuro")
    meses[mes] = entrada
    registro["meses"] = {k: meses[k] for k in sorted(meses)}
    registro.get("sin_dato", {}).pop(mes, None)
    return registro


def anotar_sin_dato(registro: dict, mes: str, motivo: str) -> dict:
    if not au.RE_MES.match(mes):
        raise ValueError(f"mes inválido: {mes!r}")
    if not motivo.strip():
        raise ValueError("el motivo no puede estar vacío")
    # un mes anotado sin dato deja de puntuar: si tenía un valor, se retira
    registro.get("meses", {}).pop(mes, None)
    registro.setdefault("sin_dato", {})[mes] = motivo.strip()
    registro["sin_dato"] = {k: registro["sin_dato"][k] for k in sorted(registro["sin_dato"])}
    return registro


def main(argv=None, path: Path = au.REGISTRO) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mes", required=True, help="AAAA-MM del informe")
    ap.add_argument("--valor", type=float, help="variación interanual nominal de departamentos en AMBA, en %%")
    ap.add_argument("--intermensual", type=float, help="opcional: intermensual de departamentos en AMBA, en %%")
    ap.add_argument("--url", help="URL del PDF")
    ap.add_argument("--frase", help="frase textual del PDF de donde sale el valor")
    ap.add_argument("--sin-dato", dest="sin_dato", help="motivo, si el informe no trae el dato")
    ap.add_argument("--reemplazar", action="store_true")
    a = ap.parse_args(argv)
    registro = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        if a.sin_dato:
            anotar_sin_dato(registro, a.mes, a.sin_dato)
        else:
            if not (a.url and a.frase):
                raise ValueError("faltan --url y --frase (la frase textual es obligatoria)")
            agregar(registro, a.mes, a.valor, a.url, a.frase,
                    intermensual=a.intermensual, reemplazar=a.reemplazar)
        au.validar_registro(registro)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    Path(path).write_text(json.dumps(registro, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {a.mes} guardado en {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
