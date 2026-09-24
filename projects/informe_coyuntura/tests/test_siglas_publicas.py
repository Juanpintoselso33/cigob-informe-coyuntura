"""El nombre que ve el lector -- la sigla del índice y la etiqueta del
cinturón -- es una decisión editorial, y se DECLARA en dos lugares:
`config.SIGLAS_PUBLICAS` y `web/src/lib/datos.ts::indiceDe`. Pero se NOMBRA
literal en unas cien cadenas de prosa repartidas entre las fichas, la
metodología y los textos que `publicar.py` escribe al snapshot.

Un renombre deja siempre alguna suelta, y no falla nada: la página publica dos
nombres para la misma cosa y el lector no tiene cómo saber que son el mismo
índice. Pasó con el renombre de agosto de 2026 (Vida cotidiana → Impacto
social, ITVC → ITCIS, ADR-0190): el HTML que volvió del editor traía "la
impacto social" en cuatro lugares justamente por un reemplazo a ciegas.

Este test cierra esa clase de bug en vez del síntoma. Cubre la capa de display
de la web entera (comentarios incluidos: si el código habla de otra cosa que
la página, el próximo que lo lea traduce mal) y las cadenas de `publicar.py`,
que son las que viajan al snapshot. NO cubre comentarios ni docstrings de
Python: ahí la clave técnica sigue llamándose `itvc` con todo derecho.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Nombre retirado → con qué se reemplazó. La segunda mitad no se usa para
# buscar; está para que el mensaje del fallo diga qué poner.
RETIRADOS = {
    "ITVC": "ITCIS",
    "Vida cotidiana": "Impacto social",
    "vida cotidiana": "impacto social",
    "Vida Cotidiana": "Impacto Social",
    "Informe de Coyuntura": "Monitor del Plan de Gobierno",
}

# Nombres PROPIOS de documentos anteriores. No son la etiqueta de hoy: son
# cómo se llamaba un papel que existe y se cita. Renombrarlos sería falsear la
# referencia, así que se descuentan antes de contar.
EXCEPCIONES = ("Monitor de la Vida Cotidiana",)

DISPLAY = sorted(
    [*(ROOT / "web" / "src" / "lib").glob("*.ts"),
     *(ROOT / "web" / "src" / "components").glob("*.astro"),
     *(ROOT / "web" / "src" / "pages").rglob("*.astro")]
)


def test_hay_archivos_de_display_que_revisar():
    """Si el layout de la web cambia y el glob deja de encontrar nada, el test
    de abajo pasaría vacío y en verde. Esto lo impide."""
    assert len(DISPLAY) > 15, f"solo {len(DISPLAY)} archivos de display: ¿cambió el layout?"


@pytest.mark.parametrize("ruta", DISPLAY, ids=lambda p: p.name)
def test_la_web_no_nombra_un_indice_ni_un_cinturon_retirado(ruta):
    texto = ruta.read_text(encoding="utf-8")
    for excepcion in EXCEPCIONES:
        texto = texto.replace(excepcion, "")
    encontrados = {v: n for v in RETIRADOS if (n := texto.count(v))}
    assert not encontrados, (
        f"{ruta.relative_to(ROOT)} todavía nombra "
        + ", ".join(f"{v!r} ({n}×) — hoy es {RETIRADOS[v]!r}"
                    for v, n in encontrados.items())
    )


def _textos_del_snapshot(o, ruta=""):
    """Todo string publicado en informe.json, con su ruta. Las CLAVES no se
    miran: `itvc` es la clave técnica y sigue siendo esa."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _textos_del_snapshot(v, f"{ruta}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _textos_del_snapshot(v, f"{ruta}[{i}]")
    elif isinstance(o, str):
        yield ruta, o


def test_el_snapshot_publicado_no_dice_un_nombre_retirado():
    """Buena parte de la prosa que ve el lector no vive en la web sino en el
    snapshot, escrita por publicar.py. Cambiar la cadena en el código NO
    cambia la página: hay que volver a correr publicar.py. Este test es el que
    obliga -- si falla, falta la corrida, no falta el cambio."""
    import json
    snapshot = json.loads(
        (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    sucios = []
    for ruta, texto in _textos_del_snapshot(snapshot):
        for excepcion in EXCEPCIONES:
            texto = texto.replace(excepcion, "")
        sucios += [(ruta, v, texto[:90]) for v in RETIRADOS if v in texto]
    assert not sucios, (
        f"{len(sucios)} texto(s) del snapshot con un nombre retirado — "
        f"¿se corrió publicar.py después de cambiarlo?\n"
        + "\n".join(f"  {r}: {v!r} → {t}" for r, v, t in sucios[:8]))


def test_las_cuatro_siglas_estan_declaradas_en_un_solo_lugar():
    import sys
    sys.path.insert(0, str(ROOT))
    from config import SIGLAS_PUBLICAS
    assert set(SIGLAS_PUBLICAS) == {"itcm", "itcg", "itvc", "itcp"}
    assert "ITVC" not in SIGLAS_PUBLICAS.values(), "la sigla retirada sigue declarada"
    # datos.ts::indiceDe es la otra mitad: las mismas cuatro, o la página y el
    # snapshot dicen cosas distintas.
    datos = (ROOT / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
    for sigla in SIGLAS_PUBLICAS.values():
        assert f'sigla: "{sigla}"' in datos, f"datos.ts no declara {sigla}"


# Siglas de TERCEROS que el informe publica, con el dueño que tiene que ir
# pegado. `ICG` es el caso que motiva la regla: difiere del propio `ITCG` en una
# letra, los dos son índices y conviven en la misma página. Un lector que
# encuentra los dos no tiene cómo saber cuál es nuestro (ADR-0190).
AJENAS = {"ICG": ("UTDT", "Di Tella"), "LICIP": ("UTDT", "Di Tella")}


def test_ninguna_sigla_ajena_se_publica_sin_su_dueno():
    """No es cosmética: es atribución. Publicar «ICG» a secas al lado de «ITCG»
    hace pasar por propio un índice de un tercero, que es el más serio de los
    dos problemas que ADR-0190 nombra."""
    import json
    snapshot = json.loads(
        (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    sueltas = []
    for ruta, texto in _textos_del_snapshot(snapshot):
        for sigla, duenos in AJENAS.items():
            if re.search(rf"\b{sigla}\b", texto) and not any(d in texto for d in duenos):
                sueltas.append(f"{ruta}: «{sigla}» sin {duenos[0]} → {texto[:80]}")
    assert not sueltas, (
        "siglas de terceros publicadas sin decir de quién son:\n  "
        + "\n  ".join(sueltas))


# ── El Monitor habla sin siglas (ADR-0340) ───────────────────────────────────
# Las siglas de los cuatro índices quedaron para la capa metodológica: las
# fichas (`fichas.ts` y la página que las renderiza) las conservan porque ahí
# se documenta el índice como objeto técnico. En todo lo demás que ve el lector
# el índice se nombra por lo que mide. Tampoco se muestran referencias a ADR ni
# el formato de archivo («CSV»): son vocabulario interno.

INDICES = ("ITCM", "ITCP", "ITCIS", "ITCG")
PROHIBIDAS = re.compile(r"\b(?:ITCM|ITCP|ITCIS|ITCG|ITVC|ADR-\d{4}|CSV)\b")
CAPA_METODOLOGICA = {
    ROOT / "web" / "src" / "lib" / "fichas.ts",
    ROOT / "web" / "src" / "pages" / "metodologia" / "[id].astro",
}
VISIBLES = [p for p in DISPLAY if p not in CAPA_METODOLOGICA]


def _sin_comentarios(texto: str) -> str:
    """Saca los comentarios de .ts/.astro: ahí la clave técnica y el número de
    ADR se nombran con todo derecho. `//` precedido de `:` es una URL."""
    texto = re.sub(r"\{/\*.*?\*/\}", " ", texto, flags=re.S)
    texto = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)
    texto = re.sub(r"<!--.*?-->", " ", texto, flags=re.S)
    return re.sub(r"(?<![:\\])//.*", " ", texto)


def test_la_capa_metodologica_existe():
    """Si un archivo de la excepción se renombra, la excepción deja de
    exceptuar y este test lo dice antes que el de abajo falle por él."""
    for p in CAPA_METODOLOGICA:
        assert p.exists(), f"{p.relative_to(ROOT)} no existe: ¿se movió la capa de fichas?"


@pytest.mark.parametrize("ruta", VISIBLES, ids=lambda p: p.name)
def test_la_web_no_muestra_siglas_internas(ruta):
    texto = _sin_comentarios(ruta.read_text(encoding="utf-8"))
    # La sigla sigue declarada como identificador del índice (`indiceDe`): es
    # la clave con la que la matriz cruzada marca su fila, no texto de pantalla.
    texto = re.sub(r'sigla: "(?:ITCM|ITCP|ITCIS|ITCG)"', " ", texto)
    encontradas = sorted(set(PROHIBIDAS.findall(texto)))
    assert not encontradas, (
        f"{ruta.relative_to(ROOT)} muestra {encontradas}: el índice se nombra en llano "
        f"(«índice macroeconómico»), sin ADR ni «CSV» (ADR-0340)")


def test_el_snapshot_no_publica_siglas_internas():
    """La prosa que escribe publicar.py tampoco. `validacion_cruzada.filas[].indice`
    es la clave de la fila (la usan la web para marcar «este cinturón» y
    bigquery_export); lo que se lee es `nombre`."""
    import json
    snapshot = json.loads(
        (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    sucios = [(r, PROHIBIDAS.findall(t), t[:90])
              for r, t in _textos_del_snapshot(snapshot)
              if PROHIBIDAS.search(t)
              and not re.fullmatch(r"\.validacion_cruzada\.filas\[\d+\]\.indice", r)
              # Citas de archivos de la fuente cargadas a mano (datos.jus.gob.ar
              # publica CSV): no es un rótulo del Monitor. Viajan del colector.
              and ".limites_metodologicos" not in r
              and not r.endswith((".detalle_txt", ".aporte_input_txt"))]
    assert not sucios, (
        f"{len(sucios)} texto(s) del snapshot con siglas internas — ¿se corrió "
        f"publicar.py?\n" + "\n".join(f"  {r}: {s} → {t}" for r, s, t in sucios[:8]))


def test_la_matriz_cruzada_trae_el_nombre_que_se_lee():
    import json
    snapshot = json.loads(
        (ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    filas = (snapshot.get("validacion_cruzada") or {}).get("filas") or []
    assert filas, "no hay matriz cruzada en el snapshot"
    for f in filas:
        assert f.get("nombre") and not PROHIBIDAS.search(f["nombre"]), f


def test_los_nombres_llanos_son_los_mismos_en_config_y_en_la_web():
    """Tres lugares declaran el nombre llano: config (prosa de publicar.py),
    `datos.ts::indiceDe` (páginas) y el `INDICE_CFG` del modal. Si divergen, el
    mismo índice se llama de dos maneras en la misma pantalla."""
    import sys
    sys.path.insert(0, str(ROOT))
    from config import NOMBRES_PUBLICOS, SIGLAS_PUBLICAS
    assert set(NOMBRES_PUBLICOS) == set(SIGLAS_PUBLICAS)
    datos = (ROOT / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
    modal = (ROOT / "web" / "src" / "components" / "IndicadorModal.astro").read_text(encoding="utf-8")
    for clave, nombre in NOMBRES_PUBLICOS.items():
        assert f'corto: "{nombre}"' in datos, f"datos.ts no declara {nombre!r}"
        assert f'Corto: "{nombre[0].upper() + nombre[1:]}"' in datos, f"datos.ts: falta la mayúscula de {nombre!r}"
        assert f'key: "{clave}", nombre: "{nombre}"' in modal, f"IndicadorModal no declara {nombre!r}"
        assert not PROHIBIDAS.search(nombre)
