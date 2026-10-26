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
    python scripts/archivo.py datos 2026-09     # sólo informe.json/series.json, para la rama mensual
"""
from __future__ import annotations

import contextlib
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


# ── Reconstrucción desde las series de hoy cortadas a fin de mes ───────────────
# Cada card toma el ÚLTIMO punto de su serie hasta el fin del mes (el mismo dato
# que la card mostraba ese día, porque el gate G3 exige card = último punto) y
# pierde el desglose del día (detalle_txt, inventarios, cotizaciones): ese texto
# describe HOY, no el mes. Una card sin ningún punto hasta ese mes no se muestra.
CAMPOS_CARD = ("valor", "unidad", "fuente", "fecha_dato", "en_indice", "dimension", "suspendido")
# Lo que la tarjeta muestra al lado del valor y describe ESE dato, no el día:
# se conserva sólo si el dato del mes es el mismo que el de hoy (ver abajo).
# normas_por_sector: el desglose del mismo informe del Ministerio (ADR-0363).
CAMPOS_MISMO_DATO = ("derivados", "usuarios_prepagas", "fecha_numerador", "fecha_denominador",
                     "normas_por_sector")
CACHES = ("macro", "politica", "gestion", "vida_cotidiana", "espiritu_epoca")


def _fin_de_mes(mes: str) -> str:
    import calendar
    a, m = map(int, mes.split("-"))
    return f"{mes}-{calendar.monthrange(a, m)[1]:02d}"


def _cortar(proyecto: Path, mes: str) -> None:
    import csv
    ultimo: dict[str, tuple[str, float]] = {}
    for ruta in sorted((proyecto / "output" / "series").glob("*.csv")):
        with open(ruta, encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            campos, filas = lector.fieldnames, [r for r in lector if r["fecha"][:7] <= mes]
        with open(ruta, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(filas)
        for r in filas:
            try:
                v = float(r["valor"])
            except (TypeError, ValueError):
                continue
            if r["indicador"] not in ultimo or r["fecha"] >= ultimo[r["indicador"]][0]:
                ultimo[r["indicador"]] = (r["fecha"], v)
    ultimo = con_cards_exentas(ultimo, *_exentas_de_la_foto(mes))
    # validacion_externa lee las series del snapshot publicado (el de hoy).
    ruta_s = proyecto / "web" / "src" / "data" / "series.json"
    if ruta_s.exists():
        sj = json.loads(ruta_s.read_text(encoding="utf-8"))
        sj = {k: [p for p in v if str(p.get("fecha", ""))[:7] <= mes] for k, v in sj.items()}
        ruta_s.write_text(json.dumps(sj, ensure_ascii=False), encoding="utf-8")
    ruta_h = proyecto / "data" / "historico" / "indicadores.json"
    if ruta_h.exists():
        store = json.loads(ruta_h.read_text(encoding="utf-8"))
        store = {k: {m: v for m, v in vals.items() if m <= mes} for k, vals in store.items()}
        ruta_h.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    (proyecto / "output" / "archivo_corte.json").write_text(
        json.dumps({k: list(v) for k, v in ultimo.items()}), encoding="utf-8")
    for nombre in CACHES:
        ruta = proyecto / "output" / "cache" / f"{nombre}.json"
        if not ruta.exists():
            continue
        cache = json.loads(ruta.read_text(encoding="utf-8"))
        cache["indicadores"] = cortar_indicadores(cache.get("indicadores", {}), ultimo, mes)
        ruta.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


# Las cards exentas de G3 (gate_calidad.G3_EXCEPCIONES) miden otra cosa que su
# serie: RIGI publica el % de la cartera aprobada y su serie guarda el MONTO en
# M USD; carne y motorización publican el nivel y su serie es un índice base
# 100. Darles el último punto de la serie publicaba septiembre-2026 con RIGI en
# «49.766 %» (los US$ M aprobados), puntuado 100 contra bandas de porcentaje, e
# inflaba el ITCG ~3 puntos. Su valor del mes sólo puede salir de la card que
# publicó la última corrida nocturna de ese mes (la foto, `mensual.elegir`).
# Sin foto (meses anteriores a las corridas) la card queda como estaba en el
# caché, y si su dato es posterior al mes no se muestra.
def _exentas_de_la_foto(mes: str) -> tuple[set, dict]:
    from gate_calidad import G3_EXCEPCIONES
    try:
        sha = mensual.elegir(mes)
        snap = json.loads(mensual._git("show", f"{sha}:{mensual.DATOS}/informe.json"))
    except (SystemExit, subprocess.CalledProcessError, json.JSONDecodeError):
        print(f"    · {mes}: sin corrida nocturna del mes; las cards exentas de G3 no se cortan")
        snap = {}
    foto = {}
    for cint in (snap.get("cinturones") or {}).values():
        for k, ind in (cint.get("indicadores") or {}).items():
            if k not in G3_EXCEPCIONES or not isinstance(ind, dict):
                continue
            # Hasta julio de 2026 la card de RIGI publicaba el monto como texto
            # («US$ 31.192M aprobados · 17 proyectos») y el % en `avance_pct`,
            # con la misma fórmula de hoy: aprobada / (aprobada + en evaluación).
            valor = ind.get("valor") if isinstance(ind.get("valor"), (int, float)) else ind.get("avance_pct")
            if isinstance(valor, (int, float)):
                foto[k] = (str(ind.get("fecha_dato") or f"{mes}-01"), float(valor))
    return set(G3_EXCEPCIONES), foto


def con_cards_exentas(ultimo: dict, exentas: set, foto: dict) -> dict:
    """`ultimo` sin el último punto de serie de las exentas, y con su card de la foto."""
    salida = {k: v for k, v in ultimo.items() if k not in exentas}
    salida.update({k: v for k, v in foto.items() if k in exentas})
    return salida


_CLAVE_FECHA = re.compile(r"\d{4}-\d{2}")


def podar_meses(obj, mes: str):
    """`obj` sin las entradas de diccionario cuya clave es una fecha posterior a
    `mes`. validacion_externa.py baja el Merval y el CCL del día, y al rehacer
    septiembre en octubre las series de contraste traían octubre (Codex,
    24-oct-2026)."""
    if isinstance(obj, dict):
        return {k: podar_meses(v, mes) for k, v in obj.items()
                if not (_CLAVE_FECHA.match(str(k)) and str(k)[:7] > mes)}
    if isinstance(obj, list):
        return [podar_meses(v, mes) for v in obj]
    return obj


def _meses_posteriores(obj, mes: str, ruta: str = "") -> list[str]:
    if isinstance(obj, dict):
        tarde = [f"{ruta}/{k}" for k in obj if _CLAVE_FECHA.match(str(k)) and str(k)[:7] > mes]
        return tarde or [x for k, v in obj.items() for x in _meses_posteriores(v, mes, f"{ruta}/{k}")]
    if isinstance(obj, list):
        return [x for v in obj for x in _meses_posteriores(v, mes, ruta)]
    return []


def cortar_indicadores(inds: dict, ultimo: dict, mes: str) -> dict:
    """Lleva cada indicador a su último punto hasta `mes` (ver arriba)."""
    salida = {}
    for k, ind in inds.items():
        if not isinstance(ind, dict):
            continue
        nuevo = {c: ind[c] for c in CAMPOS_CARD if c in ind}
        if k in ultimo:
            fecha, valor = ultimo[k]
            # Un dato anual (piquetes) se repite en la serie mes a mes: el
            # último punto hasta septiembre es «2026-09-01» aunque el dato sea
            # de 2025. Si la card de hoy trae ese mismo valor con una fecha que
            # no pasa del mes, la fecha buena es la suya.
            propia = str(ind.get("fecha_dato") or "")
            if propia and propia[:7] <= mes and ind.get("valor") == valor:
                fecha = propia
                # El total de salud viaja con las fechas de sus dos padrones: si
                # alguno ya es posterior al mes, ese total no es el del mes.
                if all(str(ind.get(c))[:7] <= mes for c in CAMPOS_MISMO_DATO if c.startswith("fecha_") and ind.get(c)):
                    nuevo.update({c: ind[c] for c in CAMPOS_MISMO_DATO if c in ind})
            nuevo["valor"], nuevo["fecha_dato"] = valor, fecha
        elif not str(ind.get("fecha_dato") or "9")[:7] <= mes:
            continue
        nuevo["desactualizado"] = False
        salida[k] = nuevo
    return salida


# publicar.py con el corte aplicado a lo que NO sale de los cachés: el bloque de
# vida (se arma desde el crudo del colector), el histórico que fusiona a las
# series y el arrastre desde el snapshot anterior (que es el de hoy).
PUBLICAR_CORTE = """
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.argv = ["publicar.py"]
import importlib.util
_spec = importlib.util.spec_from_file_location("archivo_corte", Path(__file__).with_name("archivo.py"))
archivo = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(archivo)
import publicar
MES = os.environ["ARCHIVO_MES"]
ULTIMO = {k: tuple(v) for k, v in json.loads((Path.cwd() / "output" / "archivo_corte.json").read_text()).items()}
def _corte(series):
    return {k: [p for p in v if str(p.get("fecha", ""))[:7] <= MES] for k, v in series.items()}
_bs, _fh, _as = publicar.build_series, publicar.fusionar_historico, publicar.aplicar_scoring
publicar.build_series = lambda: _corte(_bs())
publicar.fusionar_historico = lambda series, store: _corte(_fh(series, store))
publicar._carry_forward = lambda enriquecido, previo: enriquecido
def _aplicar(informe, series):
    vida = informe["cinturones"].get("vida_cotidiana") or {}
    vida["indicadores"] = archivo.cortar_indicadores(vida.get("indicadores") or {}, ULTIMO, MES)
    return _as(informe, series)
publicar.aplicar_scoring = _aplicar
publicar.main()
"""


@contextlib.contextmanager
def _reconstruido(mes: str, desde: str = "series", completo: bool = False):
    """Arma en un árbol temporal el snapshot del mes con el Monitor de HOY y
    lo entrega como (arbol, proyecto, snap, fuera, sha). Lo usan el archivo
    (que además lo empaqueta) y la rama mensual (que sólo toma los datos).

    desde="series" (el modo de hoy): los datos de HOY cortados a fin del mes
    (`_cortar`). desde="corrida": los datos crudos de la última corrida de ese
    mes; sólo sirve si ningún indicador cambió de fuente o de definición desde
    entonces (7-oct-2026: junio salía muy tenso por eso).

    completo=True corre además sensibilidad y fichas, para que la rama mensual
    lleve TODOS sus archivos del mismo corte (ver `datos_del_mes`)."""
    if desde == "corrida":
        sha = mensual.elegir(mes)
        snap_viejo = json.loads(mensual._git("show", f"{sha}:{mensual.DATOS}/informe.json"))
        ahora = snap_viejo.get("generated_at")
        print(f"· {mes}: datos de la corrida {sha[:10]} ({ahora})")
    else:
        sha = mensual._git("rev-parse", "HEAD").strip()
        ahora = f"{_fin_de_mes(mes)}T23:00:00"
        print(f"· {mes}: datos de hoy ({sha[:10]}) cortados al {_fin_de_mes(mes)}")
    with tempfile.TemporaryDirectory(prefix=f"archivo-{mes}-") as tmp:
        arbol = Path(tmp) / "arbol"
        mensual._git("worktree", "add", "--detach", str(arbol), "HEAD")
        try:
            reloj = Path(tmp) / "reloj"
            reloj.mkdir()
            (reloj / "sitecustomize.py").write_text(RELOJ, encoding="utf-8")
            proyecto = arbol / "projects" / "informe_coyuntura"
            if desde == "corrida":
                for ruta in CRUDOS:
                    shutil.rmtree(arbol / ruta, ignore_errors=True)
                    tar = subprocess.run(["git", "archive", sha, ruta], cwd=RAIZ, capture_output=True, check=True).stdout
                    subprocess.run(["tar", "-x", "-C", str(arbol)], input=tar, check=True)
                publicar = "scripts/publicar.py"
            else:
                _cortar(proyecto, mes)
                (reloj / "publicar_corte.py").write_text(PUBLICAR_CORTE, encoding="utf-8")
                # cortar_indicadores sale de ESTE archivo, no del de HEAD.
                shutil.copy(__file__, reloj / "archivo.py")
                publicar = str(reloj / "publicar_corte.py")
            # En GitHub no hay .venv: el job instala las dependencias en el
            # Python del runner, que es el que corre este script.
            py = RAIZ / "projects" / "informe_coyuntura" / ".venv" / "bin" / "python"
            if not py.exists():
                py = Path(sys.executable)
            env = {"ARCHIVO_AHORA": ahora, "ARCHIVO_MES": mes, "PYTHONPATH": f"{reloj}:{proyecto / 'scripts'}",
                   "PYTHONDONTWRITEBYTECODE": "1"}
            # El mismo orden que el pipeline: validacion_externa arma la serie
            # mensual de cada índice («Cómo va la película»); sin ella, el mes
            # salía con la sección vacía.
            pasos = [["scripts/validacion_externa.py"], ["scripts/generar_informe.py"], [publicar]]
            if completo:
                pasos += [["scripts/sensibilidad.py"], ["scripts/fichas/generar.py", "--todos"]]
            for paso in pasos:
                r = _run([str(py), *paso], proyecto, env)
                if r.returncode:
                    raise SystemExit(f"{mes}: {paso[0]} falló:\n{(r.stderr or r.stdout)[-1500:]}")
                if paso[0].endswith("validacion_externa.py") and desde != "corrida":
                    ruta_v = proyecto / "output" / "validacion_externa.json"
                    if ruta_v.exists():
                        v = podar_meses(json.loads(ruta_v.read_text(encoding="utf-8")), mes)
                        ruta_v.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
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
            yield arbol, proyecto, snap, fuera, sha
        finally:
            mensual._git("worktree", "remove", "--force", str(arbol))


# Lo que la rama mensual lleva del corte del mes, relativo al proyecto. Hasta
# oct-2026 llevaba sólo los dos JSON del sitio y el resto era el de main: la
# página decía septiembre y las fichas .md, la robustez y los CSV de `output/`
# decían octubre (auditoría externa del cinturón de Gestión, 23-oct-2026).
# Los cachés no van: el corte los deja sólo con los campos de la card.
CORTE_RAMA = ("web/src/data/informe.json", "web/src/data/series.json",
              "output/informe.json", "output/informe.md", "output/sensibilidad.json",
              "output/validacion_externa.json", "output/series/*.csv",
              "output/fichas/fichas-*.md", "data/historico/indicadores.json")


def datos_del_mes(mes: str, destino: Path) -> dict:
    """Los archivos de CORTE_RAMA del mes con la metodología de HOY, para la
    rama mensual (`destino` = el proyecto): el informe del mes publicado se lee
    con el método vigente, igual que su foto en /archivo/ (16-oct-2026: el #75
    cambió el índice macro y informe.cigob.org seguía mostrando el de antes)."""
    with _reconstruido(mes, completo=True) as (_arbol, proyecto, snap, _fuera, _sha):
        (proyecto / "web" / "src" / "data" / "informe.json").write_text(
            json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
        for patron in CORTE_RAMA:
            for origen in sorted(proyecto.glob(patron)):
                rel = origen.relative_to(proyecto)
                (destino / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(origen, destino / rel)
    print(f"· {mes}: datos del mensual rehechos con la metodología de hoy")
    return snap


def verificar_corte(proyecto: Path, mes: str) -> list[str]:
    """Lo que en los archivos de CORTE_RAMA no es del corte de `mes`: una fecha
    de dato posterior al mes, o un número que no coincide con el del sitio.
    Vacía = todo sale del mismo corte. Lo corre mensual.yml antes de publicar
    la rama: si algo falla, informe.cigob.org sigue con la edición anterior."""
    import csv
    errores = []
    fin = _fin_de_mes(mes)
    leer = lambda rel: json.loads((proyecto / rel).read_text(encoding="utf-8"))
    sitio = leer("web/src/data/informe.json")
    gen = str(sitio.get("generated_at") or "")
    if sitio.get("period") != mes:
        errores.append(f"web/src/data/informe.json: period {sitio.get('period')}, no {mes}")
    if gen[:10] > fin:
        errores.append(f"web/src/data/informe.json: generado el {gen[:10]}, después del {fin}")
    for ck, c in (sitio.get("cinturones") or {}).items():
        for ik, ind in (c.get("indicadores") or {}).items():
            if isinstance(ind, dict) and str(ind.get("fecha_dato") or "")[:7] > mes:
                errores.append(f"{ck}.{ik}: dato del {ind['fecha_dato']}")
    for k, puntos in leer("web/src/data/series.json").items():
        tarde = [p["fecha"] for p in puntos if str(p.get("fecha", ""))[:7] > mes]
        if tarde:
            errores.append(f"series.json {k}: {len(tarde)} puntos después de {mes} ({tarde[-1]})")
    for ruta in sorted((proyecto / "output" / "series").glob("*.csv")):
        with open(ruta, encoding="utf-8", newline="") as f:
            tarde = sum(1 for r in csv.DictReader(f) if r["fecha"][:7] > mes)
        if tarde:
            errores.append(f"output/series/{ruta.name}: {tarde} filas después de {mes}")
    hist = leer("data/historico/indicadores.json")
    tarde = sorted({m for vals in hist.values() for m in vals if m > mes})
    if tarde:
        errores.append(f"data/historico/indicadores.json: meses {', '.join(tarde[:3])}")
    val = leer("output/validacion_externa.json")
    if str((val.get("_meta") or {}).get("generated_at") or "")[:10] > fin:
        errores.append(f"output/validacion_externa.json: generada el {val['_meta']['generated_at'][:10]}")
    tarde = _meses_posteriores({k: v for k, v in val.items() if k != "_meta"}, mes)
    if tarde:
        errores.append(f"output/validacion_externa.json: {len(tarde)} meses después de {mes} ({tarde[0]})")
    out = leer("output/informe.json")
    if out.get("generated_at") != sitio.get("generated_at"):
        errores.append(f"output/informe.json: generado {out.get('generated_at')}, el sitio {gen}")
    sens = leer("output/sensibilidad.json")
    if (sens.get("_meta") or {}).get("snapshot") != sitio.get("generated_at"):
        errores.append(f"output/sensibilidad.json: de {(sens.get('_meta') or {}).get('snapshot')}, el sitio {gen}")
    for ck, c in (sitio.get("cinturones") or {}).items():
        for clave, bloque in c.items():
            publicado = (sens.get(clave) or {}).get("valor_publicado") if isinstance(sens.get(clave), dict) else None
            if isinstance(bloque, dict) and isinstance(bloque.get("valor"), (int, float)) and isinstance(publicado, (int, float)):
                if abs(publicado - bloque["valor"]) > 0.05:
                    errores.append(f"output/sensibilidad.json {clave}: {publicado}, el sitio {bloque['valor']}")
    for ruta in sorted((proyecto / "output" / "fichas").glob("fichas-*.md")):
        m = re.search(r"Datos al (\d{4}-\d{2}-\d{2})", ruta.read_text(encoding="utf-8"))
        if not m or m.group(1) != gen[:10]:
            errores.append(f"output/fichas/{ruta.name}: datos al {m.group(1) if m else '?'}, el sitio {gen[:10]}")
    return errores


def construir(mes: str, desde: str = "series") -> dict:
    """Reconstruye el mes con el Monitor de HOY (código, metodología y diseño)
    y lo suma al archivo, empaquetado en un solo HTML."""
    with _reconstruido(mes, desde) as (arbol, proyecto, snap, fuera, sha):
        # La foto de un mes no lleva el archivo adentro: ni las fotos de los
        # otros meses ni sus enlaces (el emisor exige un archivo autocontenido).
        shutil.rmtree(arbol / WEB_REL / "public" / "archivo", ignore_errors=True)
        (arbol / WEB_REL / "src" / "contenido" / "archivo.json").write_text('{"meses": []}\n', encoding="utf-8")
        html = _empaquetar(arbol / WEB_REL, EMISOR_HOY)
        if not html:
            raise SystemExit(f"{mes}: no se pudo empaquetar el sitio reconstruido")
        datos = html.read_bytes()
    salida = WEB / "public" / "archivo" / mes / "index.html"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(datos)
    tarjeta = _resumen(snap, mes, sha, "reconstruido" if desde == "corrida" else "series_cortadas")
    # La foto completa sólo se enlaza si no trae ningún dato con fecha posterior
    # al mes (la verificación que faltó el 7-oct-2026).
    futuros = [i for c in snap.get("cinturones", {}).values() for i, v in c.get("indicadores", {}).items()
               if str(v.get("fecha_dato") or "")[:7] > mes]
    tarjeta["pagina"] = not futuros
    if futuros:
        print(f"    ⚠ datos con fecha posterior al mes: {', '.join(futuros[:6])} — la foto no se enlaza")
    tarjeta["quitados"] = fuera
    tarjeta["peso_kb"] = round(len(datos) / 1024)
    indice = json.loads(INDICE.read_text(encoding="utf-8")) if INDICE.exists() else {"meses": []}
    indice["meses"] = sorted([m for m in indice["meses"] if m["mes"] != mes] + [tarjeta],
                             key=lambda m: m["mes"], reverse=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"    ✓ reconstruido con el Monitor de hoy, {tarjeta['peso_kb']} KB → {salida.relative_to(RAIZ)}")
    return tarjeta


# ── Tarjetas del archivo desde la serie de hoy ─────────────────────────────────
# La tabla de /archivo/ toma la tensión de cada cinturón de la SERIE MENSUAL que
# arma validacion_externa con la metodología vigente (la de «Cómo va la
# película»): es la única vara que es la misma para todos los meses. Reconstruir
# un mes desde sus datos crudos no sirve cuando un indicador cambió de fuente o
# de definición (mortalidad_pymes, la canasta de tarifas): el cálculo de hoy
# sobre el dato viejo da cualquier cosa (7-oct-2026, junio salía muy tenso).
INDICES = {"macro": ("itcm", "itcm"), "politica": ("itcp", "itcp"),
           "vida_cotidiana": ("itvc", "itvc"), "gestion": ("itcg", "itcg")}


def _tension(cint: str, valor: float) -> float:
    sys.path.insert(0, str(RAIZ / "projects" / "informe_coyuntura" / "scripts"))
    import itvc, parametrica  # noqa: E402
    return itvc.tension_de_itvc(valor) if cint == "vida_cotidiana" else parametrica.tension_de_indice(valor)


def resumen(meses: list[str]) -> None:
    """Rehace las tarjetas de `meses` desde la serie mensual del snapshot de hoy.
    Un cinturón sin el mes en la serie (la fuente todavía no publicó o no pasa
    el piso de cobertura) toma el valor de la reconstrucción del mes si existe
    y quedó verificada (`pagina`), y si no queda pendiente."""
    sys.path.insert(0, str(RAIZ / "projects" / "informe_coyuntura"))
    sys.path.insert(0, str(RAIZ / "projects" / "informe_coyuntura" / "scripts"))
    import generar_informe as gi  # noqa: E402
    hoy = json.loads((WEB / "src" / "data" / "informe.json").read_text(encoding="utf-8"))["cinturones"]
    series = {k: dict(hoy[k][ik].get("serie_mensual") or []) for k, (ik, _) in INDICES.items() if k in hoy and ik in hoy[k]}
    indice = json.loads(INDICE.read_text(encoding="utf-8"))
    previas = {m["mes"]: m for m in indice["meses"]}
    for mes in meses:
        tarjeta = dict(previas.get(mes, {"mes": mes}))
        cints, pendientes = {}, []
        for k in INDICES:
            v = series.get(k, {}).get(mes)
            if v is not None:
                cints[k] = {"score": _tension(k, v), "fuente": "serie"}
            elif tarjeta.get("pagina") and (tarjeta.get("cinturones") or {}).get(k, {}).get("score") is not None:
                cints[k] = {"score": tarjeta["cinturones"][k]["score"], "fuente": "reconstruccion"}
            else:
                cints[k] = {"score": None, "fuente": "pendiente"}
                pendientes.append(k)
        datos = {k: {"score": c["score"]} for k, c in cints.items() if c["score"] is not None}
        completo = len(datos) == len(INDICES)
        tarjeta["cinturones"] = cints
        tarjeta["score_global"] = gi.calcular_score_global(datos) if completo else None
        barb, dom, alerta = gi.detectar_barbarismo(datos) if completo else (None, None, False)
        tarjeta["riesgo_dominante"], tarjeta["cinturon_dominante"], tarjeta["alerta_multicinturon"] = barb, dom, alerta
        tarjeta["pendientes"] = pendientes
        tarjeta["modo"] = "serie_vigente"
        previas[mes] = tarjeta
        print(f"· {mes}: " + " · ".join(f"{k} {c['score']}" for k, c in cints.items()) + f" → global {tarjeta['score_global']}")
    indice["meses"] = sorted(previas.values(), key=lambda m: m["mes"], reverse=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("construir", "resumen", "datos", "verificar") or not all(re.fullmatch(r"\d{4}-\d{2}", m) for m in sys.argv[2:]):
        raise SystemExit(__doc__)
    if sys.argv[1] == "datos":
        # Rama mensual: los datos del mes publicado, rehechos con el método de hoy.
        datos_del_mes(sys.argv[2], RAIZ / "projects" / "informe_coyuntura")
    elif sys.argv[1] == "verificar":
        errores = verificar_corte(RAIZ / "projects" / "informe_coyuntura", sys.argv[2])
        for e in errores:
            print(f"::error::corte de {sys.argv[2]}: {e}")
        if errores:
            raise SystemExit(f"{len(errores)} archivos de la rama mensual no son del corte de {sys.argv[2]}")
        print(f"· {sys.argv[2]}: todos los archivos de la rama salen del mismo corte")
    elif sys.argv[1] == "resumen":
        resumen(sys.argv[2:])
    else:
        for m in sys.argv[2:]:
            construir(m, os.environ.get("ARCHIVO_DESDE", "series"))
