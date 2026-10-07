"""Archivo de informes mensuales del Monitor (ADR-0348).

Cada mes se RECONSTRUYE CON EL MONITOR DE HOY (código, metodología y diseño)
sobre los datos crudos de su última corrida nocturna, y queda navegable en
`/archivo/AAAA-MM/` (el informe entero en un solo archivo, con
`web/tools/emitir-artifact.mjs`), con una tarjeta en `/archivo/`. Así los meses
se leen y se comparan con la misma vara que el mes vigente.

Cómo: una copia del código de hoy recibe de la corrida de cierre (`mensual.elegir`)
sólo los datos crudos —`output/` (cachés de los colectores y series),
`scripts/vida_cotidiana/data/` y `data/historico/`— y corre `generar_informe.py`
y `publicar.py` con el reloj de Python fijado en el instante de esa corrida
(sitecustomize), así el mes, la fecha y la antigüedad de cada dato son los de
entonces. Después construye el sitio sin muro y lo empaqueta.

Uso:
    python scripts/archivo.py construir 2026-09
    python scripts/archivo.py construir 2026-06 2026-07 2026-08 2026-09
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mensual  # noqa: E402

RAIZ = mensual.RAIZ
WEB_REL = "projects/informe_coyuntura/web"
WEB = RAIZ / WEB_REL
INDICE = WEB / "src" / "contenido" / "archivo.json"
EMISOR_HOY = WEB / "tools" / "emitir-artifact.mjs"
ORDEN = ("macro", "politica", "vida_cotidiana", "gestion")


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **(env or {})})


def _empaquetar(web: Path, emisor: Path) -> Path | None:
    """npm ci + build + emisor en `web`. Devuelve el HTML o None si algo falla."""
    # DEPLOY_TARGET=dominio: hasta julio de 2026 el sitio se construía también
    # para GitHub Pages, con otra base; ésta es la de informe.cigob.org.
    env = {"PUBLIC_MURO": "0", "PUBLIC_SITIO": "archivo", "DEPLOY_TARGET": "dominio"}
    # El emisor necesita ApexCharts en su propio paquete (`vendor-apexcharts`),
    # algo que la configuración de build sumó en agosto de 2026. A una foto
    # anterior se le agrega SÓLO esa línea de empaquetado: no cambia nada de lo
    # que la página muestra.
    config = web / "astro.config.mjs"
    texto = config.read_text(encoding="utf-8")
    # Y sale a web/dist/, donde lo busca el emisor (junio de 2026 construía fuera).
    texto = re.sub(r"^\s*outDir:.*\n", "", texto, flags=re.M)
    config.write_text(texto, encoding="utf-8")
    if "manualChunks" not in texto and "vite:" not in texto:
        config.write_text(texto.replace("export default defineConfig({", """export default defineConfig({
  vite: { build: { rollupOptions: { output: { manualChunks(id) {
    if (id.includes('/node_modules/apexcharts/')) return 'vendor-apexcharts';
  } } } } },""", 1), encoding="utf-8")
    for paso in (["npm", "ci", "--prefer-offline", "--no-audit", "--no-fund"], ["npm", "run", "build"]):
        r = _run(paso, web, env)
        if r.returncode:
            salida = r.stderr + r.stdout
            causa = [l for l in salida.splitlines() if re.search(r"rror|Cannot|undefined|sin ficha|vivos", l) and not l.strip().startswith("at ")]
            print(f"    ✗ {' '.join(paso)}: " + (" | ".join(causa[:6]) or salida[-400:]))
            return None
    destino = web / "tools" / "emitir-artifact.mjs"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(emisor, destino)
    # --sin-aviso: en el archivo del sitio no va el renglón del informe suelto.
    r = _run(["node", "tools/emitir-artifact.mjs", "--sin-aviso"], web, env)
    html = web / "dist-artifact" / "informe-artifact.html"
    if r.returncode or not html.exists():
        print(f"    ✗ emisor: {(r.stderr or r.stdout)[-400:]}")
        return None
    return html


def _resumen(snap: dict, mes: str, sha: str, modo: str) -> dict:
    cint = snap.get("cinturones", {})
    dom = snap.get("cinturon_dominante") or ""
    return {
        "mes": mes,
        "corrida": sha[:10],
        "generado": snap.get("generated_at"),
        "modo": modo,
        "score_global": snap.get("score_global"),
        "riesgo_dominante": snap.get("barbarismo_activo"),
        "cinturon_dominante": dom,
        "alerta_multicinturon": snap.get("alerta_multicinturon"),
        "cinturones": {k: {"score": (cint.get(k) or {}).get("score"),
                           "estado": (cint.get(k) or {}).get("estado")} for k in ORDEN if k in cint},
    }


RELOJ = """
# Fija el reloj de Python en el instante de la corrida que se reconstruye
# (archivo.py, ADR-0348): el mes del informe, la fecha de generación y los días
# de antigüedad de cada dato salen de datetime.now()/date.today().
import datetime as _d, os as _os
_T = _d.datetime.fromisoformat(_os.environ["ARCHIVO_AHORA"])
class _Dt(_d.datetime):
    @classmethod
    def now(cls, tz=None):
        t = _T if _T.tzinfo else _T.replace(tzinfo=_d.timezone.utc)
        return t.astimezone(tz) if tz else t.astimezone().replace(tzinfo=None)
    @classmethod
    def today(cls):
        return cls.now()
class _Date(_d.date):
    @classmethod
    def today(cls):
        return _Dt.now().date()
_d.datetime = _Dt
_d.date = _Date
"""

# Lo que se trae de la corrida de cierre: los datos crudos que leen
# generar_informe.py y publicar.py. La metodología (scripts, config, bandas,
# data/vida/*.json) es la de HOY: eso es lo que hace comparables los meses.
#
# web/src/data/ también: publicar.py completa con el snapshot ANTERIOR lo que no
# tiene dato nuevo, y validacion_externa fusiona sus series. Sin traerlo, ese
# «anterior» era el de hoy y se colaban datos del futuro en el mes (7-oct-2026:
# junio salía con valores de septiembre y muy tensionado por eso).
CRUDOS = ("projects/informe_coyuntura/output",
          "projects/informe_coyuntura/scripts/vida_cotidiana/data",
          "projects/informe_coyuntura/data/historico",
          "projects/informe_coyuntura/web/src/data")


def construir(mes: str) -> dict:
    """Reconstruye el mes con el Monitor de HOY (código, metodología y diseño)
    sobre los datos crudos de la última corrida de ese mes."""
    sha = mensual.elegir(mes)
    snap_viejo = json.loads(mensual._git("show", f"{sha}:{mensual.DATOS}/informe.json"))
    ahora = snap_viejo.get("generated_at")
    print(f"· {mes}: datos de la corrida {sha[:10]} ({ahora})")
    with tempfile.TemporaryDirectory(prefix=f"archivo-{mes}-") as tmp:
        arbol = Path(tmp) / "arbol"
        mensual._git("worktree", "add", "--detach", str(arbol), "HEAD")
        try:
            for ruta in CRUDOS:
                shutil.rmtree(arbol / ruta, ignore_errors=True)
                tar = subprocess.run(["git", "archive", sha, ruta], cwd=RAIZ, capture_output=True, check=True).stdout
                subprocess.run(["tar", "-x", "-C", str(arbol)], input=tar, check=True)
            reloj = Path(tmp) / "reloj"
            reloj.mkdir()
            (reloj / "sitecustomize.py").write_text(RELOJ, encoding="utf-8")
            proyecto = arbol / "projects" / "informe_coyuntura"
            py = RAIZ / "projects" / "informe_coyuntura" / ".venv" / "bin" / "python"
            env = {"ARCHIVO_AHORA": ahora, "PYTHONPATH": str(reloj), "PYTHONDONTWRITEBYTECODE": "1"}
            # El mismo orden que el pipeline: validacion_externa arma la serie
            # mensual de cada índice («Cómo va la película»); sin ella, el mes
            # salía con la sección vacía.
            for script in ("scripts/validacion_externa.py", "scripts/generar_informe.py", "scripts/publicar.py"):
                r = _run([str(py), script], proyecto, env)
                if r.returncode:
                    raise SystemExit(f"{mes}: {script} falló:\n{(r.stderr or r.stdout)[-1500:]}")
            ruta_snap = proyecto / "web" / "src" / "data" / "informe.json"
            snap = json.loads(ruta_snap.read_text(encoding="utf-8"))
            # Los cachés viejos traen cards de indicadores que el Monitor de hoy
            # ya no tiene (dados de baja o renombrados, como presion_dolarizacion →
            # desequilibrio_monetario). No puntúan en la metodología de hoy, así
            # que sacarlas no mueve ningún índice: sólo deja el mes con las cards
            # que hoy existen. Se registran en la tarjeta.
            vigentes = json.loads((WEB / "src" / "data" / "informe.json").read_text(encoding="utf-8"))["cinturones"]
            fuera = []
            for ck in list(snap.get("cinturones", {})):
                if ck not in vigentes:
                    fuera.append(ck)
                    del snap["cinturones"][ck]
                    continue
                inds = snap["cinturones"][ck].get("indicadores", {})
                for ik in list(inds):
                    if ik not in vigentes[ck].get("indicadores", {}):
                        fuera.append(ik)
                        del inds[ik]
            if fuera:
                ruta_snap.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"    · sin card hoy, se quitan: {', '.join(fuera)}")
            if os.environ.get("ARCHIVO_GUARDAR"):
                destino_snap = Path(os.environ["ARCHIVO_GUARDAR"]) / f"{mes}.informe.json"
                destino_snap.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
            if snap.get("period") != mes:
                raise SystemExit(f"{mes}: la reconstrucción salió con period={snap.get('period')}")
            # La foto de un mes no lleva el archivo adentro: ni las fotos de los
            # otros meses ni sus enlaces (el emisor exige un archivo autocontenido).
            shutil.rmtree(arbol / WEB_REL / "public" / "archivo", ignore_errors=True)
            (arbol / WEB_REL / "src" / "contenido" / "archivo.json").write_text('{"meses": []}\n', encoding="utf-8")
            html = _empaquetar(arbol / WEB_REL, EMISOR_HOY)
            if not html:
                raise SystemExit(f"{mes}: no se pudo empaquetar el sitio reconstruido")
            datos = html.read_bytes()
        finally:
            mensual._git("worktree", "remove", "--force", str(arbol))
    salida = WEB / "public" / "archivo" / mes / "index.html"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(datos)
    tarjeta = _resumen(snap, mes, sha, "reconstruido")
    tarjeta["quitados"] = fuera
    tarjeta["peso_kb"] = round(len(datos) / 1024)
    indice = json.loads(INDICE.read_text(encoding="utf-8")) if INDICE.exists() else {"meses": []}
    indice["meses"] = sorted([m for m in indice["meses"] if m["mes"] != mes] + [tarjeta],
                             key=lambda m: m["mes"], reverse=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"    ✓ reconstruido con el Monitor de hoy, {tarjeta['peso_kb']} KB → {salida.relative_to(RAIZ)}")
    return tarjeta


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "construir" or not all(re.fullmatch(r"\d{4}-\d{2}", m) for m in sys.argv[2:]):
        raise SystemExit(__doc__)
    for m in sys.argv[2:]:
        construir(m)
