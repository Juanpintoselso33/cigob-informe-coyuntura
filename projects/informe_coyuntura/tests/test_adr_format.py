"""Los 164 ADR son el registro de decisiones metodológicas del informe, y
hasta la migración a MADR (2026-07-31) nada comprobaba su forma: convivían
dos formatos de encabezado, el estado era texto libre con 29 valores
distintos ("Aceptado · modifica 0003 y 0072", uno que decía solo "r"), el
índice del README se mantenía a mano y ya tenía 163 filas para 164 archivos,
y la supersesión se declaraba en un solo sentido -- quien abría el ADR viejo
no tenía forma de saber que ya no regía.

Este test cierra esa clase de deriva. En particular `test_ids_citados` fija
la trampa que más caro salió: en YAML 1.1 un id sin comillas con cero a la
izquierda es octal, así que `id: 0012` se lee 10 y `relacionado: [0036]`
apunta al 30. La primera corrida del generador de índice perdió 38 filas por
eso, en silencio.
"""
import re
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
ARCHIVOS = sorted(ADR_DIR.glob("[0-9]*.md"))

ESTADOS = {"aceptado", "rechazado", "superado", "parcial", "propuesto"}

DIRECTAS_A_INVERSAS = {
    "supersede": "superado_por",
    "supersede_parcialmente": "superado_parcialmente_por",
    "corrige": "corregido_por",
    "modifica": "modificado_por",
    "extiende": "extendido_por",
    "complementa": "complementado_por",
    "revierte": "revertido_por",
    "continua": "continuado_por",
    "cierra": "cerrado_por",
}

SECCIONES_CANONICAS = {
    "Contexto y planteo del problema", "Factores de decisión",
    "Opciones consideradas", "Decisión", "Pros y contras de las opciones",
    "Más información",
}


def _frontmatter(p: Path) -> dict:
    texto = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?)\n---\n", texto, re.S)
    assert m, f"{p.name}: no tiene frontmatter YAML"
    return yaml.safe_load(m.group(1)) or {}


CORPUS = {p.name: _frontmatter(p) for p in ARCHIVOS}
POR_ID = {str(m.get("id")): (n, m) for n, m in CORPUS.items()}


def _lista(meta: dict, clave: str) -> list[str]:
    v = meta.get(clave)
    if v is None:
        return []
    return [str(x) for x in (v if isinstance(v, list) else [v])]


def test_hay_adrs():
    assert len(ARCHIVOS) > 100, "no se encontraron los ADR"


@pytest.mark.parametrize("nombre", sorted(CORPUS))
def test_campos_obligatorios(nombre):
    meta = CORPUS[nombre]
    for campo in ("madr", "id", "estado", "fecha"):
        assert campo in meta, f"{nombre}: falta el campo '{campo}' en el frontmatter"
    assert meta["estado"] in ESTADOS, (
        f"{nombre}: estado '{meta['estado']}' fuera del vocabulario {sorted(ESTADOS)}. "
        "El matiz va en 'nota_estado', no en 'estado'."
    )


@pytest.mark.parametrize("nombre", sorted(CORPUS))
def test_ids_citados(nombre):
    """El id y toda referencia a otro ADR son cadenas de 4 dígitos.

    Sin comillas YAML los lee como octal y la referencia cambia de destino
    sin que nada falle.
    """
    meta = CORPUS[nombre]
    assert isinstance(meta["id"], str), (
        f"{nombre}: 'id' quedó sin comillas -- YAML lo leyó como "
        f"{meta['id']!r} en vez de '{nombre[:4]}'"
    )
    assert meta["id"] == nombre[:4], f"{nombre}: id '{meta['id']}' no coincide con el archivo"

    for clave in (*DIRECTAS_A_INVERSAS, *DIRECTAS_A_INVERSAS.values(), "relacionado"):
        for v in (meta.get(clave) or []):
            assert isinstance(v, str) and re.fullmatch(r"\d{4}", v), (
                f"{nombre}: '{clave}' contiene {v!r}; tiene que ser una cadena "
                "de 4 dígitos entre comillas"
            )


@pytest.mark.parametrize("nombre", sorted(CORPUS))
def test_relaciones_apuntan_a_adrs_existentes(nombre):
    meta = CORPUS[nombre]
    for clave in (*DIRECTAS_A_INVERSAS, *DIRECTAS_A_INVERSAS.values(), "relacionado"):
        for destino in _lista(meta, clave):
            assert destino in POR_ID, (
                f"{nombre}: '{clave}' apunta a ADR-{destino}, que no existe"
            )


@pytest.mark.parametrize("nombre", sorted(CORPUS))
def test_relaciones_bidireccionales(nombre):
    """Si A supersede a B, B tiene que declarar que fue superado por A."""
    meta = CORPUS[nombre]
    propio = meta["id"]
    for directa, inversa in DIRECTAS_A_INVERSAS.items():
        for destino in _lista(meta, directa):
            if destino not in POR_ID:
                continue
            nombre_dest, meta_dest = POR_ID[destino]
            assert propio in _lista(meta_dest, inversa), (
                f"ADR-{propio} declara '{directa}: {destino}' pero {nombre_dest} "
                f"no declara '{inversa}: {propio}'. Corré "
                "`python scripts/adr_coherencia.py`."
            )


@pytest.mark.parametrize("nombre", sorted(CORPUS))
def test_estado_de_los_superados(nombre):
    meta = CORPUS[nombre]
    if _lista(meta, "superado_por"):
        assert meta["estado"] == "superado", (
            f"{nombre}: lo supersede ADR-{_lista(meta, 'superado_por')[0]} "
            f"pero sigue declarándose '{meta['estado']}'"
        )


@pytest.mark.parametrize("nombre", sorted(CORPUS))
def test_secciones_canonicas(nombre):
    texto = (ADR_DIR / nombre).read_text(encoding="utf-8")
    titulos = re.findall(r"^##\s+(.+?)\s*$", texto, re.M)
    ajenas = [t for t in titulos if t not in SECCIONES_CANONICAS]
    assert not ajenas, (
        f"{nombre}: secciones de nivel 2 fuera del esqueleto MADR: {ajenas}. "
        "El contenido idiosincrásico va como '### ...' dentro de 'Más información'."
    )


def test_indice_del_readme_sincronizado():
    """El índice es generado; si alguien agrega un ADR sin regenerarlo, falla."""
    readme = (ADR_DIR / "README.md").read_text(encoding="utf-8")
    citados = set(re.findall(r"^\|\s*\[(\d{4})\]\(", readme, re.M))
    reales = set(POR_ID)
    faltan, sobran = reales - citados, citados - reales
    assert not faltan and not sobran, (
        f"índice desincronizado -- faltan {sorted(faltan)}, sobran {sorted(sobran)}. "
        "Corré `python scripts/adr_coherencia.py`."
    )


def test_adrs_citados_desde_el_codigo_existen():
    """1.352 referencias ADR-XXXX viven fuera de docs/adr/ (scripts, tests,
    web, snapshots generados). Un ADR renumerado o borrado las deja colgadas."""
    huerfanas: dict[str, list[str]] = {}
    for sub in ("scripts", "tests", "web/src"):
        for p in (ROOT / sub).rglob("*"):
            if p.suffix not in (".py", ".ts", ".astro", ".tsx") or not p.is_file():
                continue
            for ref in set(re.findall(r"ADR[-\s]?(\d{4})", p.read_text(encoding="utf-8", errors="replace"))):
                if ref not in POR_ID:
                    huerfanas.setdefault(ref, []).append(str(p.relative_to(ROOT)))
    assert not huerfanas, f"referencias a ADR inexistentes: {huerfanas}"
