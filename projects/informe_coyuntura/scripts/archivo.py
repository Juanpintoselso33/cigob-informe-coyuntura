"""Archivo de informes mensuales del Monitor (ADR-0348).

Cada mes publicado queda como una FOTO navegable en `/archivo/AAAA-MM/`: el
informe entero en un solo archivo (`web/tools/emitir-artifact.mjs`), con el
código y los datos del día de la foto, y una tarjeta con su resumen en la página
`/archivo/`.

La foto de un mes es la última corrida nocturna cuyo snapshot dice ese `period`
(`mensual.elegir`). Se reconstruye así, en orden de preferencia:

1. «exacta»: el sitio de ESE commit, empaquetado con el emisor de ese commit o,
   si todavía no existía (antes del 16-ago-2026), con el de hoy.
2. «código actual»: si el código viejo no se deja empaquetar, el código de hoy
   con los dos archivos de datos de ese commit, como el mensual (ADR-0347).
   Queda marcado en la tarjeta: la metodología que se lee es la de hoy.

Uso:
    python scripts/archivo.py construir 2026-09     # arma la foto y la tarjeta
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
            print(f"    ✗ {' '.join(paso)}: {(r.stderr or r.stdout)[-400:]}")
            return None
    destino = web / "tools" / "emitir-artifact.mjs"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(emisor, destino)
    r = _run(["node", "tools/emitir-artifact.mjs"], web, env)
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


def construir(mes: str) -> dict:
    sha = mensual.elegir(mes)
    snap = json.loads(mensual._git("show", f"{sha}:{mensual.DATOS}/informe.json"))
    print(f"· {mes}: corrida {sha[:10]} ({snap.get('generated_at')})")
    html, modo = None, None
    with tempfile.TemporaryDirectory(prefix=f"archivo-{mes}-") as tmp:
        arbol = Path(tmp) / "arbol"
        mensual._git("worktree", "add", "--detach", str(arbol), sha)
        try:
            html = _empaquetar(arbol / WEB_REL, EMISOR_HOY)
            if html:
                modo = "exacta"
                datos = html.read_bytes()
            else:
                print("    → código viejo no empaquetable: código de hoy con los datos de ese día")
                mensual._git("worktree", "remove", "--force", str(arbol))
                mensual._git("worktree", "add", "--detach", str(arbol), "HEAD")
                for nombre in mensual.ARCHIVOS:
                    contenido = subprocess.run(["git", "show", f"{sha}:{mensual.DATOS}/{nombre}"], cwd=RAIZ,
                                               check=True, capture_output=True).stdout
                    (arbol / mensual.DATOS / nombre).write_bytes(contenido)
                html = _empaquetar(arbol / WEB_REL, EMISOR_HOY)
                if not html:
                    raise SystemExit(f"{mes}: no se pudo armar la foto ni con el código de hoy")
                modo = "codigo_actual"
                datos = html.read_bytes()
        finally:
            mensual._git("worktree", "remove", "--force", str(arbol))
    salida = WEB / "public" / "archivo" / mes / "index.html"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(datos)
    tarjeta = _resumen(snap, mes, sha, modo)
    tarjeta["peso_kb"] = round(len(datos) / 1024)
    indice = json.loads(INDICE.read_text(encoding="utf-8")) if INDICE.exists() else {"meses": []}
    indice["meses"] = sorted([m for m in indice["meses"] if m["mes"] != mes] + [tarjeta],
                             key=lambda m: m["mes"], reverse=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"    ✓ {modo}, {tarjeta['peso_kb']} KB → {salida.relative_to(RAIZ)}")
    return tarjeta


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "construir" or not all(re.fullmatch(r"\d{4}-\d{2}", m) for m in sys.argv[2:]):
        raise SystemExit(__doc__)
    for m in sys.argv[2:]:
        construir(m)
