"""Todo indicador que puntúa en algún índice paramétrico (ITCM/ITCG/ITCP) o
integra una dimensión del ITVC debe tener label + unidad corta + unidad
larga en web/src/lib/datos.ts -- si falta una clave, datos.ts::label() cae
a `key.replace(/_/g, " ")` y la card pública muestra el nombre crudo en
minúsculas ("cohesion bloque senado" en vez de "Cohesión del bloque LLA
(Senado)"). Ya pasó tres veces en este proyecto (Plan2-Task10/11,
alineamiento_senadores_prov, y cohesion_bloque_senado/adhesion_reformas_provincial
el 2026-07-09) sin que ningún gate lo detectara -- gate_calidad.py chequea
que la CARD tenga datos completos, nunca cruzó contra la capa de display.
Este test cierra la clase de bug en vez de solo el síntoma puntual.
"""
import csv
import json
import unicodedata
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import itcm
import itcg
import itcp
import itvc

DATOS_TS = (ROOT / "web" / "src" / "lib" / "datos.ts").read_text(encoding="utf-8")
INDICADOR_MODAL_ASTRO = (ROOT / "web" / "src" / "components" / "IndicadorModal.astro").read_text(encoding="utf-8")
METODOLOGIA_ASTRO = (ROOT / "web" / "src" / "pages" / "metodologia" / "[id].astro").read_text(encoding="utf-8")
METODOLOGIA_INDEX_ASTRO = (ROOT / "web" / "src" / "pages" / "metodologia" / "index.astro").read_text(encoding="utf-8")
METODOLOGIA_HOME_ASTRO = (ROOT / "web" / "src" / "components" / "Metodologia.astro").read_text(encoding="utf-8")
DESCRIPCIONES_TS = (ROOT / "web" / "src" / "lib" / "descripciones.ts").read_text(encoding="utf-8")
FORMULAS_TS = (ROOT / "web" / "src" / "lib" / "formulas.ts").read_text(encoding="utf-8")
FICHAS_TS = (ROOT / "web" / "src" / "lib" / "fichas.ts").read_text(encoding="utf-8")
ASTRO_CONFIG = (ROOT / "web" / "astro.config.mjs").read_text(encoding="utf-8")

CINTURON_DE_INDICE = {"itcm": "macro", "itcg": "gestion", "itvc": "vida_cotidiana", "itcp": "politica"}
DIMENSIONES_POR_INDICE = {
    "itcm": itcm.DIMENSIONES_ITCM, "itcg": itcg.DIMENSIONES_ITCG,
    "itvc": itvc.DIMENSIONES_ITVC, "itcp": itcp.DIMENSIONES_ITCP,
}


def _todos_los_indicadores() -> dict:
    """{indicador: cinturon} de todo lo que puntúa en un índice paramétrico
    o integra el ITVC -- la misma superficie que necesita display en la web."""
    todos = {}
    todos.update({k: "macro" for k in itcm.BANDAS_ITCM})
    todos.update({k: "gestion" for k in itcg.BANDAS_ITCG})
    todos.update({k: "politica" for k in itcp.BANDAS_ITCP})
    for dim in itvc.DIMENSIONES_ITVC.values():
        todos.update({k: "vida" for k in dim["indicadores"]})
    todos.update({k: "vida" for k in itvc.INDICADORES_CONTEXTO})
    return todos


def _apariciones_en_datos_ts(clave: str) -> int:
    """Cuenta cuántas de las 3 tablas de datos.ts (LABELS, unidad corta,
    unidad larga) declaran esta clave como propiedad -- 3 = completo."""
    patron = re.compile(r"(?<![a-zA-Z_])" + re.escape(clave) + r":")
    return len(patron.findall(DATOS_TS))


def test_todo_indicador_paramétrico_tiene_label_y_unidades_en_datos_ts():
    faltantes = [
        f"{cinturon}/{clave} ({_apariciones_en_datos_ts(clave)}/3)"
        for clave, cinturon in sorted(_todos_los_indicadores().items())
        if _apariciones_en_datos_ts(clave) < 3
    ]
    assert not faltantes, (
        "Faltan entradas en LABELS/unidad-corta/unidad-larga de datos.ts "
        f"(o el key.replace(/_/g,' ') de datos.ts::label() se activa en la "
        f"card pública): {faltantes}"
    )


def test_todo_cinturon_con_parametrica_esta_en_indice_cfg_del_modal():
    # regresión real 2026-07-09: politica/itcp tenía su propia paramétrica
    # (DIMENSIONES_ITCP) desde ADR-0036, pero INDICE_CFG/INDICE_KEY de
    # IndicadorModal.astro nunca se actualizaron para incluirlo -- las cards
    # de dimensión de política se veían clickeables (mismo HTML genérico que
    # macro/gestión/vida) pero el click no hacía nada: el modal buscaba
    # DIMS["politica.<dim>"], que no existía, y salía en silencio (`if (!d)
    # return;`), sin error visible. Ningún gate/test lo detectó porque
    # ninguno ejercita el JS del cliente. Este test cierra la clase de bug
    # a nivel de wiring estático (¿aparece la clave del cinturón en los dos
    # mapas?), no solo el caso puntual de política.
    for indice, cinturon in CINTURON_DE_INDICE.items():
        assert re.search(rf'\b{cinturon}:\s*"{indice}"', INDICADOR_MODAL_ASTRO), (
            f"INDICE_KEY de IndicadorModal.astro no mapea {cinturon!r} -> {indice!r} "
            "(el breadcrumb de dimensión del indicador no se va a mostrar)"
        )
        assert re.search(rf'\b{cinturon}:\s*\{{\s*key:\s*"{indice}"', INDICADOR_MODAL_ASTRO), (
            f"INDICE_CFG de IndicadorModal.astro no tiene entrada para {cinturon!r} "
            f"(-> {indice!r}) -- el modal de dimensión de ese cinturón queda mudo al clickear"
        )


def test_el_modal_no_esconde_la_advertencia_cuando_hay_score():
    """Regresión encontrada al revisar el rojo de `peso_tarifas`.

    `aporte_nota` viajaba en el snapshot (incluida la nota de winsorización de
    sentimiento), pero el modal sólo la dibujaba en un `else if`: todo
    indicador con `aporte_score` —justamente los que pueden tener recorte o
    caveat de lectura— la ocultaba.
    """
    rama_score = INDICADOR_MODAL_ASTRO.index("if (d.aporteScore != null)")
    nota_visible = INDICADOR_MODAL_ASTRO.index('if (d.aporteNota && d.aporteScore != null)', rama_score)
    armado_final = INDICADOR_MODAL_ASTRO.index("score.innerHTML", rama_score)
    assert rama_score < nota_visible < armado_final
    assert "Advertencia de lectura:" in INDICADOR_MODAL_ASTRO


def test_tarifas_usa_canasta_real_y_ancla_internacional():
    """IPC Regulados/RIPTE no es una factura ni una participación del gasto."""
    assert 'peso_tarifas: "Canasta de servicios públicos / salario"' in DATOS_TS
    assert "2(E-10)" in FORMULAS_TS and "2(P-5)" in FORMULAS_TS
    assert "entra la mayor tensión" in DESCRIPCIONES_TS
    assert "no puntúa hasta" not in DESCRIPCIONES_TS


def test_ficha_markdown_de_tarifas_no_recae_en_la_base_temporal():
    """El entregable versionado debe decir lo mismo que la ficha web."""
    ficha = (ROOT / "output/fichas/fichas-vida_cotidiana.md").read_text(encoding="utf-8")
    bloque = ficha.split("# Canasta de servicios públicos / salario", 1)[1].split(
        "CIGOB · INFORME DE COYUNTURA", 1
    )[0]
    assert "**Hoy: 14,5 % del salario RIPTE** (2026-08)" in bloque
    assert "**Color vigente: VERDE**" in bloque
    assert "100 equivale a tensión 5" in bloque
    assert "no al nivel tarifario del 4º trimestre de 2023" in bloque
    assert "2,13 % m/m regulados" not in bloque


def test_toda_dimension_parametrica_tiene_descripcion_en_dim_descripciones():
    # mismo hallazgo 2026-07-09: aunque se arregle el wiring de arriba, sin
    # esto el modal de dimensión de política abriría con el campo "qué mide"
    # vacío -- DIM_DESCRIPCIONES nunca tuvo ninguna de las 5 claves de
    # DIMENSIONES_ITCP (imagen_voto, poder_legislativo, alianzas_territoriales,
    # cohesion_interna, conflicto_social).
    faltantes = []
    for indice, dims in DIMENSIONES_POR_INDICE.items():
        for dkey in dims:
            if not re.search(r"(?<![a-zA-Z_])" + re.escape(dkey) + r":", DESCRIPCIONES_TS):
                faltantes.append(f"{indice}/{dkey}")
    assert not faltantes, f"Faltan entradas en DIM_DESCRIPCIONES de descripciones.ts: {faltantes}"


def test_modal_y_ficha_metodologica_publican_aporte_efectivo_del_indicador():
    """La contribución sumable usa puntaje aplicado × peso efectivo.

    `aporte_score` es una tensión equivalente sobre 10 y no puede reutilizarse
    como aporte al índice (ADR-0053).
    """
    for nombre, fuente in {
        "modal": INDICADOR_MODAL_ASTRO,
        "ficha metodológica": METODOLOGIA_ASTRO,
    }.items():
        assert "peso_efectivo" in fuente, f"{nombre}: no lee el peso efectivo publicado"
        assert "puntaje_aplicado" in fuente, f"{nombre}: no lee el puntaje aplicado"
        assert "aporteIndice" in fuente, f"{nombre}: no calcula el aporte al índice"
        assert re.search(
            r"aporteIndice[\s\S]{0,240}?pesoEfectivo\s*\*\s*puntaje",
            fuente,
        ), f"{nombre}: el aporte no se deriva de peso efectivo × puntaje aplicado"
        assert not re.search(
            r"aporteIndice\s*[:=][^\n;]*aporte_?[Ss]core",
            fuente,
        ), f"{nombre}: confunde aporte_score con aporte aritmético"


def test_transparencia_de_pesos_respeta_contexto_e_itvc_base_100():
    assert "ind.en_indice === false" in INDICADOR_MODAL_ASTRO
    assert "ind?.en_indice !== false" in METODOLOGIA_ASTRO
    assert "nivel aplicado" in INDICADOR_MODAL_ASTRO.lower()
    assert "nivel aplicado" in METODOLOGIA_ASTRO.lower()
    assert "100 = 4T-2023" in INDICADOR_MODAL_ASTRO
    assert "100 = 4T-2023" in METODOLOGIA_ASTRO


def test_idm_explica_la_composicion_oficial_del_m2_transaccional():
    componentes = [
        "circulante en poder del público",
        "cuentas corrientes privadas en pesos",
        "cajas de ahorro privadas en pesos",
        "depósitos a la vista remunerados de personas jurídicas",
    ]
    for componente in componentes:
        assert componente in DESCRIPCIONES_TS, f"Falta {componente!r} en la definición pública del IDM"
        assert componente in FICHAS_TS, f"Falta {componente!r} en la ficha técnica del IDM"

    aporta_idm = re.search(
        r'idm:\s*\{[\s\S]*?aporta:\s*"([^"]+)"',
        DESCRIPCIONES_TS,
    )
    assert aporta_idm, "No se encontró DESCRIPCIONES.idm.aporta"
    assert "BCRA" not in aporta_idm.group(1) and "IPC" not in aporta_idm.group(1), (
        "DESCRIPCIONES.idm.aporta debe explicar relevancia conceptual, no fuentes o plumbing"
    )


def test_desequilibrio_monetario_tiene_capa_publica_completa_y_sin_jerga_interna():
    clave = "desequilibrio_monetario"
    fuentes = {
        "datos": DATOS_TS,
        "descripciones": DESCRIPCIONES_TS,
        "formulas": FORMULAS_TS,
        "fichas": FICHAS_TS,
    }
    for nombre, fuente in fuentes.items():
        assert re.search(r"(?<![a-zA-Z_])" + clave + r":", fuente), (
            f"Falta {clave} en {nombre}.ts"
        )
        for sustituida in ("dolarizacion_depositos", "presion_dolarizacion"):
            assert not re.search(r"(?<![a-zA-Z_])" + sustituida + r":", fuente), (
                f"La clave sustituida {sustituida} sigue activa en {nombre}.ts"
            )

    descripcion = re.search(
        r'desequilibrio_monetario:\s*\{[\s\S]*?aporta:\s*"([^"]+)"',
        DESCRIPCIONES_TS,
    )
    assert descripcion
    assert "BCRA" not in descripcion.group(1) and "ADR-" not in descripcion.group(1)

    formula = re.search(
        r'desequilibrio_monetario:\s*\{([\s\S]*?)\n\s*\},',
        FORMULAS_TS,
    )
    assert formula
    formula_txt = formula.group(1)
    # Los dos componentes y la matriz que los cruza tienen que estar dichos:
    # sin eso la fórmula parece un promedio y el indicador no es un promedio.
    # Se pide «matriz» y las cuatro esquinas, no la palabra «bilineal»: es
    # jerga del método y lo que el lector necesita saber es que se cruzan y que
    # una esquina sana no compensa a la otra (ADR-0257).
    assert "M2" in formula_txt and "divisas" in formula_txt
    assert "matriz" in formula_txt and "esquinas" in formula_txt
    assert "0" in formula_txt and "100" in formula_txt

    ficha = re.search(
        r'desequilibrio_monetario:\s*\{([\s\S]*?)\n\s*\},\n\n\s*iai:',
        FICHAS_TS,
    )
    assert ficha
    texto = ficha.group(1)
    assert 'id: "desequilibrio_monetario"' in texto
    assert "20%" in texto and "5,2%" in texto
    assert "abril de 2025" in texto and "enero de 2021" in texto
    assert "BCRA" in texto
    assert "ADR-" not in texto


def test_urls_metodologicas_anteriores_redirigen_a_la_ficha_vigente():
    assert "redirects" in ASTRO_CONFIG
    for vieja in ("dolarizacion_depositos", "presion_dolarizacion"):
        assert re.search(
            r"['\"]?/metodologia/" + vieja + r"/?['\"]?\s*:\s*"
            r"['\"]/metodologia/desequilibrio_monetario/?['\"]",
            ASTRO_CONFIG,
        ), f"falta el redirect de {vieja} a la ficha vigente"


def test_los_enlaces_de_indices_usan_el_id_de_ficha_y_no_la_sigla_publica():
    """ITCIS es la sigla pública, pero la ficha conserva el id técnico itvc."""
    assert "fichaId" in DATOS_TS
    for fuente in (METODOLOGIA_HOME_ASTRO, METODOLOGIA_INDEX_ASTRO):
        assert "indice.fichaId" in fuente or "indice!.fichaId" in fuente
        assert "sigla.toLowerCase()" not in fuente


def test_un_dato_automatico_rezagado_no_se_rotula_como_carga_manual():
    bloque = re.search(
        r"export function badgeEstado\(ind: Indicador\)([\s\S]*?)\n}",
        DATOS_TS,
    )
    assert bloque, "no se encontró badgeEstado()"
    assert "desactualizado" not in bloque.group(1), (
        "la frescura del dato no define su método de obtención"
    )
    assert "badgeEstado(ind)" in INDICADOR_MODAL_ASTRO, (
        "el modal debe usar la misma clasificación de procedencia que las cards"
    )


def test_metodologia_describe_anclas_declaradas_sin_afirmar_puntos_medios():
    assert "Los puntos declarados anclan el puntaje" in METODOLOGIA_ASTRO
    assert "Cada banda finita ancla su puntaje en su punto medio" not in METODOLOGIA_ASTRO


# ── El gráfico no puede rotular la serie con la unidad de la card ────────────
# G3_EXCEPCIONES son, por definición, los indicadores cuya card y cuya serie NO
# coinciden. Cuando además están en ESCALAS distintas, el modal necesita
# `UNIDADES_SERIE` o el gráfico hereda la unidad de la card y miente.
#
# Pasó con `consumo_carnes_total` (ADR-0217): la card publicaba 114,45 kg/hab y
# el gráfico, para el MISMO mes, mostraba "95 kg/hab" — que no eran kilos sino
# el índice base 100. El lector lo leyó como un dato desactualizado.
#
# El corte del 10% separa la escala distinta del redondeo: hoy deja afuera a
# `cepo_mulc` (3,1% de brecha, las dos en %) y a `sentimiento_digital` (8,4%,
# las dos en puntos), y adentro a los dos que sí cambian de magnitud.
# ── El gráfico no puede rotularse con la unidad de otra escala ──────────────
# Primera versión (20-ago-2026): infería "otra escala" desde el TAMAÑO de la
# brecha entre la card y el último punto de la serie, con un corte en 10%. Duró
# un día. Rompió el nocturno con `sentimiento_digital` —card 29,9 contra serie
# 26,8, un 10,4%— que está en la MISMA escala: son dos consultas distintas a
# Google Trends y difieren por ruido, no por unidad. Un umbral puesto al lado
# del ruido dispara con el ruido.
#
# La magnitud era un proxy, y había algo directo que comparar: los CSV de
# `output/series/` declaran su propia `unidad`, y la card declara la suya. Se
# comparan esas dos declaraciones — pero por FAMILIA y no por texto, porque la
# misma unidad se redacta de veinte maneras ("% de sesiones" y "% sesiones en
# minoría (12m móviles)" son la misma cosa). Comparando texto crudo saltan 28
# de 66; por familia quedan 3, y los 3 son reales.
#
# Y se autodiagnostica, que es lo que la primera versión no hacía. Si la familia
# difiere pero card y serie son el MISMO número, no hay dos escalas: hay un
# metadato viejo. Así apareció `recaudacion`, que decía "% i.a. real" desde que
# el 29-jul-2026 pasó a devolver un índice base 100. G3 no podía verlo —compara
# números, y los números coincidían— y ninguna otra guarda mira las unidades.
FAMILIAS_DE_UNIDAD = (
    ("índice",      r"\bindice\b|base 100|100 ="),
    ("pp",          r"\bpp\b|puntos porcentuales"),
    ("porcentaje",  r"%|\bporcentaje\b"),
    ("moneda",      r"us\$|\bm usd\b|millones de usd|\$"),
    ("escala 0100", r"0[\-–]100"),
    ("días",        r"\bdias\b"),
)
# Coincidencia numérica por debajo de la cual card y serie son "el mismo dato":
# la misma tolerancia con la que G3 reconcilia card contra serie.
IGUAL_NUMERO = 0.01


def _familia(unidad: str) -> str:
    s = unicodedata.normalize("NFD", unidad or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    for nombre, patron in FAMILIAS_DE_UNIDAD:
        if re.search(patron, s):
            return nombre
    return "conteo"


def _unidad_de_cada_serie() -> dict:
    out = {}
    for archivo in sorted((ROOT / "output" / "series").glob("*.csv")):
        with archivo.open(encoding="utf-8") as fh:
            for fila in csv.DictReader(fh):
                if fila.get("unidad"):
                    out[fila["indicador"]] = fila["unidad"]
    return out


def test_hay_unidades_que_comparar():
    assert len(_unidad_de_cada_serie()) > 50, "revisá el lector de los CSV de series"


def test_ninguna_serie_se_rotula_con_la_unidad_de_otra_escala():
    snapshot = json.loads((ROOT / "web" / "src" / "data" / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((ROOT / "web" / "src" / "data" / "series.json").read_text(encoding="utf-8"))
    cards = {k: i for c in snapshot["cinturones"].values()
             for k, i in c.get("indicadores", {}).items()}
    unidad_serie = _unidad_de_cada_serie()

    bloque = DATOS_TS[DATOS_TS.index("UNIDADES_SERIE"):]
    bloque = bloque[:bloque.index("};")]
    declarados = set(re.findall(r"^\s*([a-z_0-9]+):", bloque, re.M))

    metadato_viejo, sin_declarar = [], []
    for clave, card in sorted(cards.items()):
        us, uc = unidad_serie.get(clave), card.get("unidad")
        if not us or not uc or _familia(uc) == _familia(us):
            continue
        puntos = series.get(clave) or []
        ultimo = puntos[-1].get("valor") if puntos else None
        mismo_numero = (
            isinstance(ultimo, (int, float))
            and isinstance(card.get("valor"), (int, float))
            and card["valor"]
            and abs(card["valor"] - ultimo) / abs(card["valor"]) <= IGUAL_NUMERO
        )
        detalle = (f"{clave}: la card dice «{uc}» ({_familia(uc)}) y la serie "
                   f"«{us}» ({_familia(us)})")
        if mismo_numero:
            # Publicar el mismo número con unidades de distinta familia es un
            # metadato viejo, y declararlo en UNIDADES_SERIE no lo arregla:
            # rotularía el gráfico con una etiqueta que ya no describe el dato.
            metadato_viejo.append(detalle)
        elif clave not in declarados:
            sin_declarar.append(detalle)

    assert not metadato_viejo, (
        "card y serie publican EL MISMO número con unidades de distinta "
        "familia, así que no son dos escalas: una de las dos etiquetas quedó "
        "vieja. Corregí la que ya no describe lo que se calcula — en "
        "`descargar_series.py` si es la de la serie:\n  "
        + "\n  ".join(metadato_viejo))
    assert not sin_declarar, (
        "estas series están en otra escala que su card, y el gráfico las va a "
        "rotular con la unidad de la card. Agregalas a UNIDADES_SERIE en "
        "datos.ts:\n  " + "\n  ".join(sin_declarar))
