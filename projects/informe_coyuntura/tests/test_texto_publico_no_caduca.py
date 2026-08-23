# -*- coding: utf-8 -*-
"""El texto público no puede afirmar el estado de HOY (ADR-0156).

EL PROBLEMA. Las fichas y descripciones son prosa escrita a mano sobre datos que
cambian todos los meses. Cuando una frase dice «hoy la vulnerabilidad financiera
(endeudamiento con mora) está marcada crítica», queda mentirosa el día que el
endeudamiento sale del índice — y no falla nada: `gate_calidad.py` valida datos y
estructura del snapshot, y ningún test lee la prosa.

Pasó exactamente eso. El 30-jul-2026, en la misma sesión en que
`endeudamiento_familiar` salió del ITVC, quedaron publicadas DOS frases que lo
nombraban como componente vigente. Y antes, al barrer el resto, apareció la peor:
la sección de metodología afirmaba que «la matriz cruzada verifica que cada índice
correlacione más con su ancla propia» cuando ya era falso en 2 de los 4.

`test_fichas_pesos.py` cubre una parte de la familia —los pesos, que se cruzan
contra el snapshot— pero no las afirmaciones que no son un número comparable.

QUÉ HACE ESTE TEST. No prohíbe la deixis: obliga a declararla. Cada aparición de
«hoy», «actualmente», «por ahora» y compañía en la prosa pública tiene que estar
en el inventario de abajo con su motivo. Una frase nueva rompe el test, y ahí hay
que elegir: reescribirla como método (que es casi siempre lo correcto) o sumarla
al inventario asumiendo que alguien la va a tener que mantener.

Se excluye `cambios`, que es un changelog: sus entradas dicen lo que era cierto
ESE día y tienen que quedar como están.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LIB = RAIZ / "web" / "src" / "lib"

# Deixis temporal: las palabras que fechan una afirmación en el presente y por lo
# tanto la hacen expirar sin que nadie la edite.
DEIXIS = re.compile(r"\bhoy\b|\bactualmente\b|\bpor ahora\b|\ben este momento\b"
                    r"|\bhasta ahora\b|\bpor el momento\b|\bde momento\b", re.I)

CADENA = re.compile(r'"((?:[^"\\]|\\.){20,}?)"')
CAMPO = re.compile(r"^\s{4}(\w+):", re.M)

# Inventario de deixis ACEPTADA, con el motivo. Clave: (ficha, campo) o el
# archivo; valor: por qué esa frase puede decir «hoy» sin caducar.
#
# El criterio para aceptarla es uno solo: que la frase remita a algo que el
# pipeline recalcula —una tabla, una serie, una ficha— en vez de afirmar el valor.
# Las cuatro entradas `(itcX, "seleccion")` salieron cuando las fichas de índice
# dejaron de afirmar un conteo en prosa —«Diecisiete indicadores… con los
# puntajes de hoy»— y pasaron a remitir a la tabla de composición, que se
# genera. Sin frase no hay deixis que aceptar, y dejarlas era la puerta abierta
# que este inventario existe para cerrar.
ACEPTADAS = {
    ("alineamiento_senadores_prov", "incidenciaTexto"):
        "«la mejor señal automatizable disponible hoy» declara un límite del "
        "estado del arte, no un valor: si aparece una fuente mejor se cambia el "
        "indicador, no el texto",
    ("adhesion_reformas_provincial", "incidenciaTexto"):
        "«el rango observado hoy es el arranque de un proceso» es justamente la "
        "advertencia de que el rango NO está cerrado — la frase envejece bien",
    ("bloqueo_sostenido", "limitaciones"):
        "«un acta publicada hoy se clasifica al día siguiente» describe el rezago "
        "del proceso, no un estado",
    ("concesiones_infraestructura", "limitaciones"):
        "«cuentan hoy solo al cierre total» declara un refinamiento pendiente",
}

# descripciones.ts no tiene estructura de campos; se lleva su propio inventario
# por recorte de frase.
ACEPTADAS_DESCRIPCIONES = (
    "la historia 2018→hoy",              # define la ventana de cálculo
    "hoy es insumo del Índice de Capacidad Prestable",   # relación estructural
    "mide por ahora la capacidad de nombrar",            # declara el alcance
)


def _fichas(texto):
    out = {}
    for m in re.finditer(r"^  (\w+): \{$", texto, re.M):
        fin = texto.find("\n  },", m.end())
        out[m.group(1)] = texto[m.end():fin]
    return out


def _deixis_en_fichas():
    texto = (LIB / "fichas.ts").read_text(encoding="utf-8")
    hallazgos = []
    for clave, cuerpo in _fichas(texto).items():
        campos = [(mm.group(1), mm.start()) for mm in CAMPO.finditer(cuerpo)]
        for i, (nombre, ini) in enumerate(campos):
            fin = campos[i + 1][1] if i + 1 < len(campos) else len(cuerpo)
            if nombre == "cambios":
                continue
            for s in CADENA.findall(cuerpo[ini:fin]):
                for mm in DEIXIS.finditer(s):
                    hallazgos.append((clave, nombre, mm.group(0), s))
    return hallazgos


def test_toda_deixis_temporal_en_fichas_esta_declarada():
    sin_declarar = [(c, campo, palabra, frase[:150])
                    for c, campo, palabra, frase in _deixis_en_fichas()
                    if (c, campo) not in ACEPTADAS]
    assert not sin_declarar, (
        "prosa pública que afirma el estado de hoy y va a quedar vieja sola:\n  "
        + "\n  ".join(f"[{c} · {campo}] «{p}» → {f}" for c, campo, p, f in sin_declarar)
        + "\n\nReescribila como método (remitir a la tabla o a la serie, que se "
          "recalculan) o sumala al inventario ACEPTADAS de este test con el motivo."
    )


def test_toda_deixis_temporal_en_descripciones_esta_declarada():
    texto = (LIB / "descripciones.ts").read_text(encoding="utf-8")
    sin_declarar = []
    for s in CADENA.findall(texto):
        for mm in DEIXIS.finditer(s):
            recorte = s[max(0, mm.start() - 40):mm.end() + 40]
            if not any(ok in s for ok in ACEPTADAS_DESCRIPCIONES):
                sin_declarar.append(recorte)
    assert not sin_declarar, (
        "descripciones que afirman el estado de hoy:\n  " + "\n  ".join(sin_declarar)
    )


def test_el_inventario_no_tiene_entradas_de_mas():
    """Si una frase se reescribió, su entrada del inventario sobra — y dejarla
    permite que vuelva a entrar deixis por esa puerta sin que el test avise."""
    presentes = {(c, campo) for c, campo, _, _ in _deixis_en_fichas()}
    sobrantes = sorted(set(ACEPTADAS) - presentes)
    assert not sobrantes, (
        f"entradas del inventario que ya no corresponden a ninguna frase: {sobrantes}. "
        f"Sacalas: si no, dejan la puerta abierta."
    )


def test_el_test_mira_algo():
    """Contra el falso verde: si el parseo se rompe y no encuentra ninguna
    cadena, los tres tests de arriba pasan vacíos."""
    hallazgos = _deixis_en_fichas()
    # El piso era 5 mientras las cuatro fichas de índice afirmaban un conteo en
    # prosa. Al reescribirlas contra la tabla generada quedaron las cuatro
    # frases de indicador, que son las que declaran un límite del método y no
    # un estado. Baja a 4 por eso, no porque el parseo encuentre menos.
    assert len(hallazgos) >= 4, (
        f"sólo {len(hallazgos)} apariciones de deixis; el parseo de fichas.ts "
        f"probablemente se rompió y los otros tests están pasando en falso"
    )
    # Y el piso solo dice algo mientras el inventario no esté vacío: si alguien
    # borra ACEPTADAS entero, los tres tests de arriba pasan sin mirar nada.
    assert len(ACEPTADAS) >= 4
