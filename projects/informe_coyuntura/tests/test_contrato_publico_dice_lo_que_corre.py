# -*- coding: utf-8 -*-
"""El texto público describe el método que corre, no el que corría.

Las tres discrepancias de esta entrega no tenían mal ningún número. Tenían mal
la frase que dice qué se midió, y ninguna guarda podía verlo porque todas las
que existían cruzan la ficha contra el SNAPSHOT — y el snapshot estaba bien:

- `ratio_dnu` publica 1,48 = 37/25 contado por el tipo jurídico de InfoLeg y con
  la publicación en el Boletín Oficial en los dos lados; la fórmula seguía
  diciendo «DNU dictados / leyes sancionadas» y describiendo la búsqueda textual
  descartada (ADR-0241 → ADR-0263).
- `iaf_transferencias` deflacta cada flujo mensual por el IPC de su propio mes;
  la fórmula seguía mostrando dos sumas anuales divididas por un IPC promedio
  (ADR-0239 → ADR-0263).
- `subocupacion_demandante` es un porcentaje de la PEA; la descripción decía «de
  los ocupados» (ADR-0249 → ADR-0263).

Y dos clases más, que son la misma enfermedad en otro órgano:

- un renombre que no llega a la fórmula ni a la página de metodología deja la
  interpretación refutada donde más se lee (ADR-0264);
- un indicador suspendido que sigue publicando su tabla de bandas bajo el
  encabezado «Cómo entra al índice» describe un cálculo que ya no ocurre, y una
  dimensión que promete cuatro vías cuando quedan tres se reconstruye mal
  (ADR-0265).

Lo que se verifica acá NO es prosa: es que cada afirmación pública tenga detrás
la línea de colector, la tabla de pesos o el campo del snapshot que la sostiene.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import itcg   # noqa: E402
import itcm   # noqa: E402
import itcp   # noqa: E402
import itvc   # noqa: E402
import politica  # noqa: E402

WEB = RAIZ / "web" / "src"
LIB = {n: (WEB / "lib" / n).read_text(encoding="utf-8")
       for n in ("datos.ts", "descripciones.ts", "fichas.ts", "formulas.ts", "charts.ts")}
PAGINAS = {str(p.relative_to(WEB)): p.read_text(encoding="utf-8")
           for p in (WEB / "pages").rglob("*.astro")}
CAPA_PUBLICA = {**LIB, **PAGINAS}
SNAPSHOT = json.loads((WEB / "data" / "informe.json").read_text(encoding="utf-8"))

INDICES = {"macro": ("itcm", itcm.DIMENSIONES_ITCM,
                     getattr(itcm, "INDICADORES_SUSPENDIDOS", {})),
           "politica": ("itcp", itcp.DIMENSIONES_ITCP, itcp.INDICADORES_SUSPENDIDOS),
           "gestion": ("itcg", itcg.DIMENSIONES_ITCG, itcg.INDICADORES_SUSPENDIDOS),
           "vida_cotidiana": ("itvc", itvc.DIMENSIONES_ITVC, itvc.INDICADORES_SUSPENDIDOS)}
SUSPENDIDOS = {k for _, _, s in INDICES.values() for k in s}
# `idm` e `icip` no están suspendidos: se declararon CONTEXTO (siguen publicando
# card y serie, sin puntaje). Para lo que verifica este archivo son lo mismo —un
# indicador que conserva su tabla de bandas y ya no la usa— así que entran acá.
NO_PUNTUAN = SUSPENDIDOS | set(itcm.INDICADORES_CONTEXTO)


def _bloque(texto: str, clave: str) -> str:
    """El objeto literal de una clave de primer nivel, acotado a sí mismo.

    Misma trampa que en `test_la_ficha_no_se_queda_atras`: la sangría va con
    `[ \\t]*` y no con `\\s*`, o el bloque se lleva el archivo entero y toda
    aserción sobre él pasa sin mirar nada."""
    m = re.search(rf"^([ \t]*){re.escape(clave)}: \{{$", texto, re.M)
    if not m:
        return ""
    fin = re.compile(rf"^{m.group(1)}\}},?$", re.M).search(texto, m.end())
    return texto[m.end():fin.start()] if fin else texto[m.end():]


# Una frase se juzga por su CLÁUSULA, no por su línea. Todas estas guardas
# eximen a la línea que cita una afirmación para negarla, y en `fichas.ts` una
# «línea» es un párrafo entero: alcanzaba con que el párrafo negara la tesis en
# algún lado para que también pudiera afirmarla en otro. Tres mutaciones reales
# se colaron así —el deflactor promedio del IAF, «sobran pesos» en la leyenda
# del IDM y «inversión intangible» en la del ICIP—, las tres en párrafos cuya
# última oración negaba lo que la primera acababa de afirmar.
#
# Se corta en punto y en punto y coma, NO en dos puntos: los dos puntos
# introducen la elaboración de la misma afirmación («No se usa un deflactor
# único: el IPC promedio anual le da a cada mes el mismo peso»), y separarlos
# dejaría la negación de un lado y su explicación del otro.
_CORTE = re.compile(r"(?<![A-Z])[.;]")


def _clausulas(linea: str):
    return [c for c in _CORTE.split(linea) if c.strip()]


# La contracara: una entrada de `cambios:` es, por construcción, la crónica de
# lo que el texto DECÍA. Citar ahí la redacción vieja es su trabajo, y hacerlo
# frase por frase la volvería incontable. Se exime la entrada entera —y sólo
# ella: el patrón exige la forma literal del changelog, no basta con nombrar un
# ADR en medio de un párrafo—.
_CHANGELOG = re.compile(r'^\s*\{\s*fecha:\s*"[0-9-]+"\s*,\s*cambio:\s*"')


def _afirma(linea: str, frase: str, niega) -> bool:
    """¿Alguna cláusula de la línea dice `frase` sin negarla?"""
    if _CHANGELOG.match(linea):
        return False
    return any(frase in c.lower() and not any(n in c.lower() for n in niega)
               for c in _clausulas(linea))


def test_la_exencion_del_changelog_es_solo_para_el_changelog():
    """Si el patrón se aflojara, cualquier párrafo que nombre un ADR quedaría
    fuera de control y estas guardas dejarían de mirar la mitad del archivo."""
    entrada = '      { fecha: "2026-08-25", cambio: "se publicaba como sobran pesos" },'
    assert not _afirma(entrada, "sobran pesos", ())
    prosa = '      "Positivo = sobran pesos, como decía ADR-0254",'
    assert _afirma(prosa, "sobran pesos", ())


def _capas(clave: str) -> dict:
    """Las cuatro capas que describen un indicador, por archivo."""
    return {n: _bloque(LIB[n], clave)
            for n in ("descripciones.ts", "formulas.ts", "fichas.ts")}


def test_el_extractor_de_bloques_no_desborda():
    """La guarda de la guarda: sin esto, todo lo de abajo pasa vacío."""
    for archivo in ("descripciones.ts", "formulas.ts", "fichas.ts"):
        claves = re.findall(r"^  ([a-z_0-9]+): \{$", LIB[archivo], re.M)
        assert len(claves) > 10, f"{archivo}: cambió el formato, revisá el parser"
        gordos = [k for k in claves if len(_bloque(LIB[archivo], k)) > 20_000]
        assert not gordos, f"{archivo}: bloques desbordados {gordos[:5]}"


# ── ratio_dnu: publicación en los dos lados, tipo jurídico y no frase ───────

def test_el_colector_tipifica_el_dnu_por_el_rotulo_de_la_grilla():
    """La afirmación que la ficha hace sobre CÓMO se identifica un DNU."""
    assert politica._RE_INFOLEG_DNU.match("Decreto DNU 771 / 2026")
    assert not politica._RE_INFOLEG_DNU.match("Decreto Reglamentario 58 / 2026")
    assert not politica._RE_INFOLEG_DNU.match("Decreto 710 / 2026")


def test_ninguna_capa_del_ratio_dnu_sigue_diciendo_dictados_ni_sancionadas():
    malos = []
    for archivo, cuerpo in _capas("ratio_dnu").items():
        assert cuerpo, f"{archivo}: no se encontró el bloque de ratio_dnu"
        exime = ("adr-", "decían", "en vez de publicadas")
        for linea in cuerpo.splitlines():
            if any(_afirma(linea, f, exime) for f in ("dnu dictados", "leyes sancionadas")):
                malos.append(f"{archivo}: {linea.strip()[:120]}")
    assert not malos, (
        "el ratio DNU vuelve a mezclar convenciones: el colector cuenta "
        "PUBLICADOS sobre PUBLICADAS (ADR-0241).\n  " + "\n  ".join(malos))


def test_las_tres_capas_del_ratio_dnu_nombran_la_publicacion():
    for archivo, cuerpo in _capas("ratio_dnu").items():
        assert "publicad" in cuerpo.lower(), (
            f"{archivo}: la ficha/fórmula/descripción del ratio DNU no dice que "
            "los dos lados se cuentan por publicación en el Boletín Oficial")


def test_la_ficha_del_ratio_dnu_declara_el_filtro_por_tipo():
    ficha = _capas("ratio_dnu")["fichas.ts"].lower()
    assert "decreto dnu" in ficha, "la ficha no dice por qué rótulo se filtra"
    assert "filtro previo" in ficha, (
        "la ficha no aclara que la búsqueda por «necesidad y urgencia» ya no "
        "decide: hoy sólo acota el listado")


# ── iaf_transferencias: deflación mes a mes, universo y base común ──────────

def test_el_colector_deflacta_mes_a_mes_y_no_por_promedio_anual():
    """ADR-0239 borró `_ipc_promedio_indec`. Si volviera, la ficha vuelve a
    tener razón y este test es el que hay que releer, no el que hay que borrar."""
    assert hasattr(politica, "_ipc_indice_mensual")
    assert not hasattr(politica, "_ipc_promedio_indec")
    assert politica.RON_FILAS_JURISDICCION == ("provincias", "c.a.b.a", "fdo.compensador")
    assert politica.RON_NO_PROVINCIA == {"tesoro nacional", "seguridad social", "fondo a.t.n."}


def test_la_formula_del_iaf_deflacta_dentro_de_la_suma():
    latex = _bloque(LIB["formulas.ts"], "iaf_transferencias")
    assert r"\sum" in latex, "la fórmula del IAF volvió a comparar dos sumas ya hechas"
    assert "IPC}_{m}" in latex, (
        "la fórmula del IAF no muestra el IPC del MES dentro de la suma: así "
        "escrita describe el deflactor promedio que ADR-0239 reemplazó")


def test_ninguna_capa_del_iaf_promete_un_ipc_promedio_anual():
    malos = []
    for archivo, cuerpo in _capas("iaf_transferencias").items():
        exime = ("adr-", "no se usa", "pasó de")
        for linea in cuerpo.splitlines():
            if any(_afirma(linea, f, exime)
                   for f in ("ipc promedio", "inflación promedio anual")):
                malos.append(f"{archivo}: {linea.strip()[:120]}")
    assert not malos, (
        "vuelve el deflactor promedio anual en el texto del IAF; el colector "
        "deflacta mes a mes (ADR-0239).\n  " + "\n  ".join(malos))


def test_el_contrato_del_iaf_declara_sus_cinco_terminos():
    """Jurisdicciones, clase de transferencia, ventana, deflactor y base común:
    sin los cinco, la diferencia con otra estimación pública no es discutible."""
    ficha = _capas("iaf_transferencias")["fichas.ts"]
    formula = _bloque(LIB["formulas.ts"], "iaf_transferencias")
    desc = _capas("iaf_transferencias")["descripciones.ts"]
    for texto, nombre in ((ficha, "ficha"), (formula, "fórmula")):
        assert "Fondo Compensador" in texto, f"{nombre}: falta una jurisdicción del universo"
        assert "Consenso Fiscal" in texto, f"{nombre}: falta la compensación del Consenso Fiscal"
        assert "A.T.N." in texto, f"{nombre}: no dice qué queda afuera"
        assert "propio mes" in texto, f"{nombre}: no dice que el deflactor es el del mes"
    assert "2016" in ficha and "2016" in formula, "no se declara la base común del IPC"
    assert "automáticas" in desc, "la descripción no dice qué clase de transferencia mide"


# ── subocupación demandante: el denominador es la PEA ───────────────────────

def test_ninguna_capa_dice_que_la_subocupacion_es_sobre_los_ocupados():
    malos = []
    for archivo, cuerpo in _capas("subocupacion_demandante").items():
        assert cuerpo, f"{archivo}: no se encontró el bloque"
        exime = ("adr-", "no de los ocupados", "no sobre", "y no el total")
        for linea in cuerpo.splitlines():
            if any(_afirma(linea, f, exime)
                   for f in ("de los ocupados", "% de ocupados")):
                malos.append(f"{archivo}: {linea.strip()[:120]}")
    assert not malos, (
        "INDEC calcula la tasa sobre la PEA, no sobre los ocupados "
        "(ADR-0249).\n  " + "\n  ".join(malos))


def test_las_capas_que_definen_el_universo_dicen_pea():
    desc = _capas("subocupacion_demandante")["descripciones.ts"]
    ficha = _capas("subocupacion_demandante")["fichas.ts"]
    assert "económicamente activa" in desc.lower()
    assert "económicamente activa" in ficha.lower()


def test_la_unidad_de_la_subocupacion_es_la_que_escribio_el_colector():
    """Cierra el otro extremo del denominador: el tablero y el colector tienen
    que decir el mismo universo, no sólo la ficha."""
    real = (SNAPSHOT["cinturones"]["vida_cotidiana"]["indicadores"]
            ["subocupacion_demandante"]["unidad"])
    assert real == "% de la PEA", f"el colector cambió la unidad: {real!r}"
    for mapa in ("UNIDADES_CORTAS", "UNIDADES_LARGAS"):
        dicha = _bloque_mapa(mapa)["subocupacion_demandante"]
        assert dicha == real, f"{mapa}: dice «{dicha}» y el colector escribió «{real}»"


def _bloque_mapa(nombre: str) -> dict:
    m = re.search(rf"export const {nombre}: Record<string, string> = \{{(.*?)\n\}};",
                  LIB["datos.ts"], re.S)
    assert m, f"no se encontró el mapa {nombre} en datos.ts"
    return dict(re.findall(r'([a-z_0-9]+):\s*"((?:[^"\\]|\\.)*)"', m.group(1)))


def _indicadores_publicados():
    for ck, c in SNAPSHOT["cinturones"].items():
        for ik, ind in (c.get("indicadores") or {}).items():
            yield ck, ik, ind


# ── idm / icip: el renombre llega a la fórmula y a las páginas ──────────────

# Una línea que cita la afirmación para negarla no es la afirmación. La lista es
# explícita a propósito, igual que en `test_constructos_no_prometen_de_mas`.
NIEGA = ("no es", "no son", "no dice", "no mide", "se llamaba", "se publicaba",
         "decía", "decían", "hasta agosto", "adr-", "ya no", "consumo intermedio")

REFUTADAS = {
    "sobran pesos": "M2 es un stock observado, no lo que la economía quiere retener",
    "pesos que la gente": "la fórmula no puede rotular M2 como demanda",
    "inversión intangible": "los pagos al exterior por informática son consumo intermedio",
    "capitalización digital": "el rótulo se retiró: no hay formación de capital",
    "capitalización inteligente": "el rótulo se retiró: no hay formación de capital",
}


def test_ninguna_capa_publica_repone_la_lectura_refutada():
    malos = []
    for frase, motivo in REFUTADAS.items():
        for archivo, texto in CAPA_PUBLICA.items():
            for linea in texto.splitlines():
                if _afirma(linea, frase, NIEGA):
                    malos.append(f"«{frase}» en {archivo}: {linea.strip()[:100]} — {motivo}")
    assert not malos, (
        "vuelve una interpretación que los ADR de esta jornada declararon "
        "insostenible:\n  " + "\n  ".join(malos))


def test_las_paginas_astro_entran_al_corpus():
    """Contra el falso verde: la guarda anterior miraba sólo `web/src/lib`, y
    por eso la página de metodología siguió diciendo «capitalización digital»."""
    assert len(PAGINAS) >= 3, f"sólo {len(PAGINAS)} páginas .astro en el corpus"
    assert any("[slug].astro" in n for n in PAGINAS)


def test_el_rem_declara_solo_los_componentes_que_renormalizan_si_falta():
    """IDM salió del ITCM y la presión de dolarización fue reemplazada.

    Si falta el REM, los únicos pares vigentes que absorben su peso dentro de
    estabilidad monetaria son IPC y desequilibrio monetario (ADR-0261).
    """
    ficha = _capas("rem_ipc_12m")["fichas.ts"]
    pares_vigentes = (
        set(itcm.DIMENSIONES_ITCM["estabilidad_monetaria"]["indicadores"])
        - {"rem_ipc_12m"}
    )
    assert pares_vigentes == {"ipc_total", "desequilibrio_monetario"}, (
        "cambió la composición de estabilidad monetaria: actualizá también la "
        "política de faltantes del REM")
    m = re.search(r'faltantes:\s*"([^"]+)"', ficha)
    assert m, "la ficha del REM no declara qué hace ante faltantes"
    texto = m.group(1).lower()
    assert "ipc" in texto and "desequilibrio monetario" in texto
    assert "idm" not in texto and "presión de dolarización" not in texto, (
        "la ficha del REM conserva componentes que ya no integran estabilidad monetaria")


def test_el_desequilibrio_no_reintroduce_constructos_retirados_en_campos_activos():
    """La crónica puede citar el texto viejo; la definición vigente, no.

    Estas cuatro expresiones fueron el residuo exacto encontrado por la
    reverificación. `_afirma` excluye sólo las entradas literales de `cambios:`.
    """
    ficha = _capas("desequilibrio_monetario")["fichas.ts"]
    prohibidas = ("demanda transaccional", "salida efectiva", "misma fuga", "poca fuga")
    malos = []
    for linea in ficha.splitlines():
        for frase in prohibidas:
            if _afirma(linea, frase, ()):
                malos.append(f"«{frase}»: {linea.strip()[:120]}")
    assert not malos, (
        "la ficha vigente vuelve a interpretar agregados o compras de divisas "
        "como constructos que no observa:\n  " + "\n  ".join(malos))


def test_la_ficha_del_desequilibrio_publica_los_cortes_vigentes_de_a():
    """La ventana cambió al régimen abierto; sus percentiles también."""
    import desequilibrio_monetario as dm

    ficha = _capas("desequilibrio_monetario")["fichas.ts"]
    m = re.search(r'"Cada componente se convierte.*?Componente A:(.*?)Componente B:',
                  ficha)
    assert m, "no se encontró la declaración de cortes del componente A"
    declarados = m.group(1)
    for corte in dm.CORTES_A:
        literal = str(corte).replace(".", ",")
        assert literal in declarados, (
            f"la ficha no publica el corte vigente {literal}; "
            f"el motor usa {dm.CORTES_A}")
    for viejo in ("31,62", "34,48", "38,27", "44,34", "49,96"):
        assert viejo not in declarados, f"la ficha conserva el corte viejo {viejo}"


def test_un_indicador_de_contexto_no_tiene_ficha_ni_formula():
    """La regla del proyecto (ADR-0189): si no puntúa, no se muestra — ni en el
    tablero ni en las fichas metodológicas, que salen del mismo snapshot.

    `badlar`, `prestamos_privados`, `base_monetaria` y `tc_mayorista` la venían
    cumpliendo: conservan etiqueta y descripción, y no tienen ficha ni fórmula.
    `idm` e `icip` entraron a contexto el 25-ago-2026 (ADR-0261 y ADR-0262) y
    hasta entonces arrastraban las dos, con su tabla de bandas publicada bajo el
    encabezado «Cómo entra al ITCM». Esta guarda iguala a los seis."""
    incoherentes = []
    for clave in itcm.INDICADORES_CONTEXTO:
        for archivo in ("fichas.ts", "formulas.ts"):
            if _bloque(LIB[archivo], clave):
                incoherentes.append(f"{clave}: no puntúa y conserva bloque en {archivo}")
        if not _bloque(LIB["descripciones.ts"], clave):
            incoherentes.append(f"{clave}: es contexto y no tiene descripción pública")
    assert len(itcm.INDICADORES_CONTEXTO) >= 4, "revisá el parser: se vació la lista"
    assert not incoherentes, "\n  ".join(incoherentes)


def test_el_contexto_conserva_su_etiqueta_en_el_tablero():
    """La contracara: sacarles la ficha no puede dejarlos sin nombre. La serie se
    sigue publicando y el gráfico la rotula desde `datos.ts`."""
    labels = _bloque_mapa("LABELS")
    sin_etiqueta = [k for k in itcm.INDICADORES_CONTEXTO if k not in labels]
    assert not sin_etiqueta, (
        "estos indicadores de contexto quedaron sin etiqueta: " + ", ".join(sin_etiqueta))


# ── dimensiones e indicadores suspendidos ──────────────────────────────────

def _vivos_por_dimension() -> dict:
    out = {}
    for _, (_, dims, susp) in INDICES.items():
        for dim, info in dims.items():
            out[dim] = [k for k in info["indicadores"] if k not in susp]
    return out


NUMERAL = {"una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
           "seis": 6, "siete": 7, "ocho": 8}
# El sustantivo enumera los COMPONENTES de la dimensión sólo cuando NO viene
# calificado por un «de …»: «cuatro señales del entorno que demanda ese empleo»
# cuenta un subconjunto dentro de una dimensión de seis, y contarlo daría un
# falso positivo. El lookahead es esa distinción.
CUENTA = re.compile(
    r"\b(una|dos|tres|cuatro|cinco|seis|siete|ocho)\s+(vías|medidas|señales)\b(?!\s+d[eo]l?\b)",
    re.I)


def test_ninguna_dimension_promete_mas_componentes_de_los_que_puntuan():
    vivos = _vivos_por_dimension()
    m = re.search(r"export const DIM_DESCRIPCIONES: Record<string, string> = \{(.*?)\n\};",
                  LIB["descripciones.ts"], re.S)
    assert m, "no se encontró DIM_DESCRIPCIONES"
    textos = dict(re.findall(r'([a-z_0-9]+):\s*"((?:[^"\\]|\\.)*)"', m.group(1)))
    revisadas, malas = 0, []
    for dim, txt in textos.items():
        if dim not in vivos:
            continue
        hallado = CUENTA.search(txt)
        if not hallado:
            continue
        revisadas += 1
        dichos = NUMERAL[hallado.group(1).lower()]
        if dichos != len(vivos[dim]):
            malas.append(f"{dim}: promete «{hallado.group(0)}» y hoy puntúan "
                         f"{len(vivos[dim])} ({', '.join(vivos[dim])})")
    assert revisadas >= 2, f"sólo {revisadas} dimensiones con enumeración: revisá el parser"
    assert not malas, (
        "una descripción de dimensión enumera componentes que ya no puntúan; "
        "quien la lea reconstruye otro índice:\n  " + "\n  ".join(malas))


def _fichas_de(claves):
    for k in claves:
        b = _bloque(LIB["fichas.ts"], k)
        if b:
            yield k, b


def test_la_ficha_de_un_suspendido_no_afirma_en_presente_que_pesa():
    malos = []
    for clave, cuerpo in _fichas_de(sorted(NO_PUNTUAN)):
        for linea in cuerpo.splitlines():
            if re.match(r'^\s*"(Pesa|Integra|Pertenece|Aporta|Es\s+el)\b', linea):
                malos.append(f"{clave}: {linea.strip()[:110]}")
    assert not malos, (
        "un indicador suspendido sigue describiendo su peso en presente. El peso "
        "de diseño se conserva (ADR-0245), pero hay que decir que es de diseño:\n  "
        + "\n  ".join(malos))


def test_la_escala_de_un_suspendido_se_declara_historica():
    """La tabla de bandas se conserva para poder leer la serie; el encabezado que
    la precede dice «Cómo entra al índice», así que la ficha tiene que aclarar
    que hoy no entra."""
    mudos = []
    for clave, cuerpo in _fichas_de(sorted(NO_PUNTUAN)):
        if "anclas: {" not in cuerpo:
            continue
        if "ya no se aplica" not in cuerpo.lower():
            mudos.append(clave)
    assert not mudos, (
        "estas fichas publican su tabla de bandas sin decir que el indicador ya "
        "no puntúa: " + ", ".join(mudos))


def test_una_ficha_no_dice_que_pesa_la_mitad_de_una_dimension_de_uno():
    """El error del otro lado del par: el que QUEDA describe su peso con el
    reparto anterior. Es el que ninguna auditoría marcó."""
    vivos = _vivos_por_dimension()
    dim_de = {k: d for d, ks in vivos.items() for k in ks}
    malos = []
    for clave, cuerpo in _fichas_de(sorted(dim_de)):
        if "la mitad de la dimensión" not in cuerpo.lower():
            continue
        if len(vivos[dim_de[clave]]) != 2:
            malos.append(f"{clave}: dice «la mitad de la dimensión» y "
                         f"{dim_de[clave]} tiene {len(vivos[dim_de[clave]])} "
                         "componentes vivos")
    assert not malos, "\n  ".join(malos)


def test_el_peso_efectivo_que_declara_una_ficha_es_el_del_snapshot():
    """Cuando una ficha se anima a publicar un porcentaje efectivo, tiene que
    ser el que el índice calculó esa corrida."""
    comparados, malos = 0, []
    for ck, clave, _ in _indicadores_publicados():
        cuerpo = _bloque(LIB["fichas.ts"], clave)
        m = re.search(r"(\d{1,2}(?:,\d)?)% efectivo del (ITC[MPG]|ITCIS)", cuerpo)
        if not m:
            continue
        sigla = INDICES[ck][0]
        idx = (SNAPSHOT["cinturones"][ck].get(sigla) or {}).get("dimensiones") or {}
        real = next((i["peso_efectivo"] for d in idx.values()
                     for k, i in (d.get("indicadores") or {}).items() if k == clave), None)
        if real is None:
            continue
        comparados += 1
        dicho = float(m.group(1).replace(",", "."))
        if abs(dicho - real * 100) > 0.15:
            malos.append(f"{clave}: la ficha dice {dicho}% y el índice calculó "
                         f"{round(real * 100, 1)}%")
    assert comparados >= 1, "ninguna ficha declara peso efectivo: revisá el parser"
    assert not malos, "\n  ".join(malos)


def test_la_ficha_de_un_retirado_no_se_renderiza_vacia():
    """Un indicador retirado «conserva ficha histórica» — lo dicen los cinco ADR
    que retiran alguno—, y el cuerpo entero de la página estaba gateado contra
    su fila del snapshot. Como un retirado no tiene fila, la página existía y
    quedaba en el callout de «sin dato vigente»: 7,7 kB contra 15,6 de una viva,
    sin fuente, sin método, sin escala, sin limitaciones y sin changelog. La
    ficha existía y no decía nada, que es peor que no existir — el enlace desde
    la serie promete una explicación que no está.

    Se verifica sobre el código y no sobre el HTML porque la guarda tiene que
    correr sin build: lo que no puede volver es el gate contra `ind`."""
    pagina = (WEB / "pages" / "metodologia" / "[id].astro").read_text(encoding="utf-8")
    assert "{esIndicador && (\n      <Fragment>" in pagina, (
        "el cuerpo de la ficha volvió a depender de la fila del snapshot: los "
        "indicadores retirados vuelven a publicar una página vacía")
    assert "{esIndicador && ind && (" not in pagina
    # y los campos de la corrida siguen protegidos uno por uno
    for campo in ("ind.aporte_formula", "ind.aporte_lectura", "ind.unidad"):
        crudo = re.findall(rf"(?<![?.\w]){re.escape(campo)}", pagina)
        assert not [c for c in crudo if True] or f"{campo.replace('ind.', 'ind?.')}" in pagina, (
            f"{campo} quedó sin protección: la página revienta al construir la "
            "ficha de un indicador sin fila en el snapshot")


# ── el LaTeX es código, no decoración ──────────────────────────────────────
# La matriz de `desequilibrio_monetario` publicó durante horas sus dos esquinas
# cruzadas en 40 y 77,5 mientras el motor ya usaba 58,75 y la LEYENDA DEL MISMO
# OBJETO, dos líneas más abajo, decía 58,75. O sea: la fórmula pública se
# contradecía consigo misma y nada falló. Es la clase de residuo que deja una
# recalibración — se corrige la prosa, que es lo que uno lee, y el LaTeX queda.

def test_la_matriz_publicada_es_la_del_motor():
    """Las cuatro esquinas, término por término contra sus constantes. No se
    compara el conjunto de números: dos esquinas valen lo mismo, así que
    intercambiarlas no cambiaría el conjunto y sí cambiaría la fórmula."""
    import desequilibrio_monetario as dm
    latex = _bloque(LIB["formulas.ts"], "desequilibrio_monetario")
    m = re.search(r"T_t=.*?(?=\\\\\[6pt\])", latex)
    assert m, "no se encontró la matriz en el LaTeX de desequilibrio_monetario"
    esperado = {r"(1-a)(1-b)": dm.TENSION_A_BAJO_B_BAJO,
                r"a(1-b)": dm.TENSION_A_ALTO_B_BAJO,
                r"(1-a)b": dm.TENSION_A_BAJO_B_ALTO,
                r"ab": dm.TENSION_A_ALTO_B_ALTO}
    malos = []
    for termino, valor in esperado.items():
        hallado = re.search(r"(?<![a-z(])" + re.escape(termino) + r"\\,([0-9{},]+)", m.group(0))
        leido = float(hallado.group(1).replace("{,}", ".")) if hallado else None
        if leido != valor:
            malos.append(f"{termino}: el LaTeX dice {leido} y el motor usa {valor}")
    assert not malos, (
        "la fórmula pública de la matriz no es la que calcula el motor:\n  "
        + "\n  ".join(malos))


_PESO_LATEX = re.compile(r"0\{,\}(\d{2})\s*\\cdot")


def test_los_pesos_de_un_compuesto_suman_uno_en_el_LaTeX():
    """La otra mitad de lo mismo: cuando una fórmula reparte pesos, una
    recalibración a medias deja el reparto sin cerrar. No se compara contra el
    motor —cada compuesto lo calcula su propio colector— pero un reparto que no
    suma 1 está mal sin necesidad de saber cuál es el bueno."""
    revisados, malos = 0, []
    for clave, cuerpo in re.findall(r"\n  ([a-z_0-9]+): \{\n(.*?)\n  \},",
                                    LIB["formulas.ts"], re.S):
        m = re.search(r"latex: String\.raw`(.*?)`,\n", cuerpo, re.S)
        if not m:
            continue
        pesos = [int(x) / 100 for x in _PESO_LATEX.findall(m.group(1))]
        if len(pesos) < 2:
            continue
        revisados += 1
        if abs(sum(pesos) - 1.0) > 0.001:
            malos.append(f"{clave}: {pesos} suma {round(sum(pesos), 4)}")
    assert revisados >= 3, f"sólo {revisados} fórmulas con reparto de pesos: revisá el parser"
    assert not malos, "reparto de pesos que no cierra en la fórmula pública:\n  " + "\n  ".join(malos)
