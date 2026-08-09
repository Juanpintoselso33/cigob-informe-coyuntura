"""Los cuatro colores del semáforo existen en el CSS y no hay cortes duplicados en TS."""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSS = RAIZ / "web" / "public" / "dashboard.css"
LIB = RAIZ / "web" / "src" / "lib"
COMPONENTES = RAIZ / "web" / "src" / "components"

sys.path.insert(0, str(RAIZ / "scripts"))
import publicar  # noqa: E402  (sys.path.insert tiene que ir antes)

COLORES = ("verde", "amarillo", "naranja", "rojo")


class TestTokensCss:
    def test_los_cuatro_colores_tienen_token_y_variante_soft(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert re.search(rf"--{color}:\s*#", css), f"falta el token --{color}"
            assert re.search(rf"--{color}-soft:\s*#", css), f"falta --{color}-soft"

    def test_los_cuatro_colores_pintan_genoma_y_verdict(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert f".cg-genoma-seg.sem-{color}" in css, f"falta .sem-{color}"
            assert f".cg-verdict.{color}" in css, f"falta .cg-verdict.{color}"

    def test_los_cuatro_colores_pintan_el_punto_del_verdict(self):
        css = CSS.read_text(encoding="utf-8")
        for color in COLORES:
            assert re.search(rf"\.cg-verdict\.{color}\s+\.cg-verdict-dot", css), f"falta punto de {color} en verdict"


class TestSinCortesDuplicadosEnTs:
    def test_datos_ts_no_recalcula_el_semaforo(self):
        """Los cortes viven solo en parametrica.py. Si el cliente los repite,
        se desincronizan sin que falle nada."""
        ts = (LIB / "datos.ts").read_text(encoding="utf-8")
        assert "semaforoDimension" not in ts, (
            "semaforoDimension calculaba el color en el cliente; "
            "tiene que leer el color publicado")
        assert "semaforoDe" in ts, "falta el lector semaforoDe"

    def test_ningun_ts_deriva_el_color_de_un_numero(self):
        """El invariante real, no una lista de cortes conocidos.

        La versión anterior de este test prohibía literales puntuales
        (">= 95", ">= 90", ">= 105", ">= 85") — los cortes del ITVC
        base-100. Eso dejaba totalmente afuera los cortes 60/40/20 del
        0-100 que usan ITCM, ITCG e ITCP (el "puntaje >= 60 ? verde : ..."
        original de semaforoDimension no llevaba ningún ">= 9x", así que la
        lista nunca lo habría atrapado). El invariante que de verdad importa
        no es "no aparezcan estos números": es que ninguna línea que nombre
        un color del semáforo lo derive de comparar un número — cualquiera
        sea el corte, hoy o el que se agregue mañana.
        """
        color = re.compile("|".join(COLORES))
        comparacion_numerica = re.compile(r"[<>]=?\s*\d|\d\s*[<>]=?")
        for archivo in LIB.glob("*.ts"):
            for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
                if color.search(linea) and comparacion_numerica.search(linea):
                    raise AssertionError(
                        f"{archivo.name}:{n}: el color se deriva de una "
                        f"comparación numérica en el cliente — {linea.strip()!r}")


class TestLeyendaNoHardcodeaLosCortes:
    """A3 (revisión de coherencia UI, ago-2026): SemaforoLeyenda.astro tiene
    que armar su texto ("tensión ≤ 4") leyendo `informe.semaforo_cortes` (que
    sale de CORTES_SEMAFORO vía publicar._semaforos), no escribiendo los
    tramos a mano -- si no, se desincroniza del motor sin que nada falle.

    No se generalizó esta prohibición a TODO `web/src/**/*.astro` como la de
    arriba hace con `web/src/lib/*.ts`: probado contra el árbol real, ese
    regex da falsos positivos ajenos al semáforo -- p. ej. `Bluf.astro`
    (`rojos.length > 0`, un array de cinturones en rojo) y `TensionPanel.astro`
    ("1 cinturón en rojo es manejable"). Acotarlo al único archivo nuevo que
    puede reintroducir el defecto es lo que le da dientes de verdad sin
    romper código ajeno que ya usa la palabra "rojo" con otro sentido."""

    ARCHIVO = COMPONENTES / "SemaforoLeyenda.astro"
    CORTES_PROHIBIDOS = ("4", "6", "8", "60", "40", "20", "105", "95", "85")

    def test_existe(self):
        assert self.ARCHIVO.exists(), "falta SemaforoLeyenda.astro (A3)"

    def test_lee_semaforo_cortes_del_snapshot(self):
        src = self.ARCHIVO.read_text(encoding="utf-8")
        assert "semaforo_cortes" in src, (
            "la leyenda tiene que leer informe.semaforo_cortes, no "
            "hardcodear los tramos")

    def test_no_hardcodea_ningun_corte_conocido(self):
        """Escanea código, no prosa: un comentario puede decir "los 4 colores"
        sin que eso sea un corte hardcodeado -- lo que este test prohíbe es
        que el número aparezca en una línea de código/template."""
        src = self.ARCHIVO.read_text(encoding="utf-8")
        for n, linea in enumerate(src.splitlines(), 1):
            if linea.strip().startswith("//"):
                continue
            for tok in self.CORTES_PROHIBIDOS:
                if re.search(rf"(?<!\w){tok}(?!\w)", linea):
                    raise AssertionError(
                        f"SemaforoLeyenda.astro:{n}: aparece el literal "
                        f"{tok!r}, uno de los cortes que solo puede vivir en "
                        f"parametrica.CORTES_SEMAFORO -- {linea.strip()!r}")


# ---------------------------------------------------------------------------
# `verdictDeCinturon` (el chip de 3 colores del CINTURÓN, distinto del
# semáforo de 4 colores de arriba -- ADR-0181 documenta por qué siguen
# separados) tiene que conocer exactamente el vocabulario de `_estado()`:
# ni un valor de menos (uno quedaría sin color explícito) ni uno de más
# (una rama muerta que nunca puede activarse).
#
# Bug real, Task 9 del plan semaforo-cuatro-colores: `_estado()`
# (publicar.py y generar_informe.py, réplicas) sólo emite "estable",
# "en_tension" y "tensionado". El chip web comparaba además contra
# "critico" y "alerta" -- valores que ningún cinturón puede tener -- y por
# eso "tensionado", el peor estado, caía en la rama default y se pintaba
# amarillo en vez de rojo. `cinturonesRojos` quedaba estructuralmente en 0.
#
# En vez de hardcodear acá los tres nombres de estado (que volvería a
# divergir si algún día cambian los tramos), se los pide a `_estado()`
# corriéndola sobre un score de cada tramo -- eso además pinea los
# umbrales reales de UMBRALES, no una copia textual de ellos.
# ---------------------------------------------------------------------------

DATOS_TS = LIB / "datos.ts"
GENERAR_INFORME_PY = RAIZ / "scripts" / "generar_informe.py"
COLORES_DEL_CHIP = {"verde", "amarillo", "rojo"}


def _estados_reales() -> set:
    """Los únicos tres valores que `_estado()` puede devolver, derivados
    corriéndola sobre un score de cada tramo (0=estable, 5=en_tension,
    9=tensionado según UMBRALES) en vez de copiar los nombres a mano."""
    return {publicar._estado(0), publicar._estado(5), publicar._estado(9)}


def _cuerpo_verdict_de_cinturon() -> str:
    ts = DATOS_TS.read_text(encoding="utf-8")
    m = re.search(
        r"export function verdictDeCinturon\([^)]*\)[^{]*\{([\s\S]*?)\n\}",
        ts,
    )
    assert m, "No se encontró verdictDeCinturon en web/src/lib/datos.ts"
    return m.group(1)


def _mapa_explicito(cuerpo: str) -> dict:
    """{valor_de_estado: color} para cada `if (estado === "X" [|| estado ===
    "Y"]) return "Z";` del cuerpo -- reproduce, en Python, qué color asigna
    cada comparación explícita del chip."""
    mapa = {}
    for cond, color in re.findall(r'if\s*\(([^)]+)\)\s*return\s*"(\w+)"', cuerpo):
        for valor in re.findall(r'estado\s*===\s*"(\w+)"', cond):
            mapa[valor] = color
    return mapa


def _color_fallback(cuerpo: str) -> str:
    """El color de la rama sin condición (no un `if (...) return`) -- lo que
    recibe cualquier `estado` que ninguna comparación explícita capturó."""
    m = re.search(r'\n\s*return\s*"(\w+)"\s*;', cuerpo)
    assert m, "verdictDeCinturon no tiene un return incondicional al final"
    return m.group(1)


def _resolver(estado: str, mapa: dict, fallback: str) -> str:
    return mapa.get(estado, fallback)


def _mapa_canonico() -> dict:
    """El mapeo estado->color ya decidido en generar_informe.py:192 (el
    emoji que pinta el informe markdown), traducido a los nombres de color
    del chip web -- la fuente de verdad que verdictDeCinturon tiene que
    espejar, no sólo "algún color válido"."""
    fuente = GENERAR_INFORME_PY.read_text(encoding="utf-8")
    m = re.search(
        r'_emoji_estado[\s\S]*?return\s*\{([\s\S]*?)\}\.get',
        fuente,
    )
    assert m, "No se encontró el mapeo estado->emoji en generar_informe.py"
    emoji_a_color = {"🟢": "verde", "🟡": "amarillo", "🔴": "rojo"}
    return {
        estado: emoji_a_color[emoji]
        for estado, emoji in re.findall(r'"(\w+)":\s*"(.)"', m.group(1))
    }


class TestVerdictDeCinturonConoceElVocabularioDeEstado:
    """Las dos direcciones que tienen que sostenerse simultáneamente para que
    web y pipeline no vuelvan a divergir en silencio."""

    def test_todo_estado_real_resuelve_al_color_canonico(self):
        """Dirección 1, con dientes: no alcanza con "algún color válido" --
        eso ya vale hoy incluso con el bug (hay un fallback que atrapa
        cualquier string no reconocido, así que 'tensionado' resuelve a
        'amarillo' sin que este chequeo se entere). Fix round 1: el
        regresion-test real es que cada estado real resuelva EXACTAMENTE
        el color que generar_informe.py:192 ya decidió -- si alguien borra
        la rama 'tensionado' de verdictDeCinturon, este assert tiene que
        fallar acá, no sólo en un test aparte que alguien podría podar como
        redundante."""
        cuerpo = _cuerpo_verdict_de_cinturon()
        mapa = _mapa_explicito(cuerpo)
        fallback = _color_fallback(cuerpo)
        canonico = _mapa_canonico()

        assert set(canonico) == _estados_reales(), (
            "El mapeo de generar_informe.py no cubre los mismos tres "
            "estados que _estado() puede emitir -- revisar el regex o el "
            "archivo fuente"
        )

        for estado, esperado in canonico.items():
            obtenido = _resolver(estado, mapa, fallback)
            assert obtenido == esperado, (
                f"'{estado}' (real, emitido por _estado()) resuelve a "
                f"'{obtenido}' en el chip web, pero generar_informe.py "
                f"(fuente de verdad) lo pinta '{esperado}'"
            )

    def test_verdict_de_cinturon_no_compara_contra_estados_fantasma(self):
        """Dirección 2 -- la que falla hoy: ninguna comparación explícita del
        chip puede mencionar un valor que `_estado()` no produce. Antes del
        fix, 'critico' y 'alerta' están en el cuerpo pero _estado() jamás
        los emite: son ramas muertas que además le roban a 'tensionado' su
        color correcto (cae al fallback amarillo)."""
        cuerpo = _cuerpo_verdict_de_cinturon()
        comparados = set(_mapa_explicito(cuerpo))
        reales = _estados_reales()

        fantasma = comparados - reales
        assert not fantasma, (
            f"verdictDeCinturon compara contra {fantasma}, que _estado() "
            f"nunca produce (vocabulario real: {reales})"
        )


class TestNingunEstadoFantasmaEnTodoElArchivo:
    """Las dos pruebas de arriba solo miran el CUERPO de `verdictDeCinturon`.
    Eso no alcanza: el bug original no nació en el cuerpo de la función, nació
    en el comentario de tipo de `Cinturon.estado` ("estable | en_tension |
    critico") que documentaba mal el vocabulario -- de ahí es de donde
    cualquiera que toque `verdictDeCinturon` copia los nombres. Arreglar solo
    la función y dejar el comentario roto siembra la próxima recurrencia.

    Estos dos tests generalizan la Dirección 2 (ningún fantasma) a TODO
    `datos.ts`, no solo al cuerpo de una función nombrada."""

    def test_el_comentario_de_tipo_de_cinturon_estado_no_lista_un_fantasma(self):
        ts = DATOS_TS.read_text(encoding="utf-8")
        m = re.search(r"estado:\s*string;\s*//\s*(.+)", ts)
        assert m, "no se encontró el comentario de tipo de Cinturon.estado"
        listados = {v.strip() for v in m.group(1).split("|")}
        reales = _estados_reales()
        assert listados == reales, (
            f"el comentario de tipo de Cinturon.estado lista {listados}, "
            f"pero _estado() solo emite {reales}"
        )

    def test_ninguna_comparacion_de_estado_en_todo_el_archivo_es_fantasma(self):
        """Generaliza la Dirección 2 más allá de `verdictDeCinturon`: si
        mañana otra función de datos.ts repitiera el patrón `estado === "X"`
        con un valor fantasma, este test lo atrapa aunque esa función nunca
        se llame `verdictDeCinturon`.

        El identificador bare `estado` (sin objeto por delante) es el
        parámetro de cinturón que usa `verdictDeCinturon` -- `(?<!\\.)`
        excluye a propósito `ind.estado` / `c.estado`, que son el `estado`
        POR INDICADOR (vocabulario "placeholder"/"fresco"/etc., un campo
        distinto sin relación con los tres valores de `_estado()`)."""
        ts = DATOS_TS.read_text(encoding="utf-8")
        comparados = set(re.findall(r'(?<!\.)\bestado\s*===\s*"(\w+)"', ts))
        reales = _estados_reales()
        fantasma = comparados - reales
        assert not fantasma, (
            f"datos.ts compara estado contra {fantasma} en algún lugar del "
            f"archivo, valor que _estado() nunca produce (real: {reales})"
        )
