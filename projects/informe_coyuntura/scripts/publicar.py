"""Arma el snapshot de datos que consume la web del informe de coyuntura.

Lee output/informe.json + el ultimo vida_cotidiana_*.json + output/series/*.csv
y escribe web/src/data/informe.json (con vida cotidiana enriquecido a ~13
indicadores automaticos) y web/src/data/series.json.
"""
import csv, glob, json, os, re, statistics, sys
from datetime import date, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]          # projects/informe_coyuntura
OUT = ROOT / "output"
# CIGOB_SALIDA_WEB redirige el snapshot fuera del repo. Existe para los tests
# (ADR-0178): `test_publicar_genera_snapshot` corría publicar.py de verdad
# contra el árbol y dejaba web/src/data/informe.json y el histórico reescritos,
# así que los tests POSTERIORES —los de este archivo y los de otros— leían ese
# resultado en vez del snapshot publicado. Con el snapshot desactualizado eso
# producía diez fallas G3 fantasma en el gate y dos tests que pasan solos y
# fallan en conjunto. Es un escape de TEST, no una opción de operación: el
# pipeline nunca la setea.
DATA = Path(os.environ["CIGOB_SALIDA_WEB"]) if os.environ.get("CIGOB_SALIDA_WEB") \
    else ROOT / "web" / "src" / "data"
DATA.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from config import PESOS_CINTURONES, UMBRALES        # pesos y umbrales del informe
import itcm                                           # bandas y pesos del ITCM macro
import itcg                                           # bandas y pesos del ITCG gestión
import itcp                                           # bandas y pesos del ITCP política
import itvc                                           # pesos y rebase del ITVC vida cotidiana
import sensibilidad                                   # rango de robustez (ADR-0019)
import parametrica                                    # motor de puntaje y semáforo


def coma(x) -> str:
    """Número para texto PÚBLICO: coma decimal es-AR y menos tipográfico (U+2212).

    Había trece copias de `coma = lambda x: str(x).replace(".", ",")` en este
    archivo, todas sin el signo menos — y por eso las conclusiones de validación
    salían con guion («ITCP -0,49 con la incertidumbre») mientras las unidades y
    las anclas que escribe el pipeline usan «−». Lo encontró la auditoría de UI
    del 29-jul-2026, que vio los dos signos en la misma página.

    Sólo se convierte el menos INICIAL, a propósito: el guion interno de una
    fecha o de un rango («2026-06-01», «1997-2026») no es un signo menos y
    convertirlo rompería el texto.
    """
    s = str(x).replace(".", ",")
    return ("−" + s[1:]) if s.startswith("-") else s


def _add(out, key, valor, unidad, fuente, fecha, **extra):
    d = {"valor": valor, "unidad": unidad, "fuente": fuente,
         "fecha_dato": fecha, "desactualizado": False}
    d.update(extra)
    out[key] = d


def build_vida(raw):
    """Mapea el JSON crudo (por fuente) a indicadores estilo informe.json."""
    indec = raw.get("indec", {}); bcra = raw.get("bcra", {})
    utdt = raw.get("utdt", {}); cafam = raw.get("cafam", {})
    ciccra = raw.get("ciccra", {}); snic = raw.get("snic", {})
    trends = raw.get("trends", {})
    ts = raw.get("metadata", {}).get("timestamp", "")[:10]
    out = {}

    bs = indec.get("brecha_salario_cbt", {})
    _add(out, "brecha_salario_cbt", round(bs.get("valor", 0), 2),
         "canastas (RIPTE/CBT)", "Sec. Trabajo (RIPTE) + INDEC (CBT)", bs.get("fecha"),
         detalle_txt=bs.get("nota"))
    al = indec.get("ipc_alimentos", {})
    _add(out, "ipc_alimentos", round(al.get("variacion_mensual_pct", 0), 2),
         "% m/m", "INDEC — IPC alimentos y bebidas (vía datos.gob.ar)", al.get("fecha"))
    cc = bcra.get("credito_consumo_total", {})
    # El crédito de consumo viene en millones de pesos; pasar a billones para
    # que el número no sea gigante (43.560.544 millones = 43,56 billones).
    cc_val = cc.get("valor")
    _add(out, "endeudamiento_familiar",
         round(cc_val / 1e6, 2) if isinstance(cc_val, (int, float)) else cc_val,
         "billones de pesos (consumo)",
         "BCRA — crédito de consumo (API) + Informe sobre Bancos", cc.get("fecha"))
    reg = indec.get("ipc_regulados", {})
    _add(out, "peso_tarifas", round(reg.get("variacion_mensual_pct", 0), 2),
         "% m/m regulados", "INDEC — IPC precios regulados (vía datos.gob.ar)", reg.get("fecha"))
    alq = indec.get("ipc_alquiler_gba", {})
    _add(out, "alquiler_real", round(alq.get("variacion_mensual_pct", 0), 2),
         "% m/m alquileres", "INDEC — IPC-GBA alquiler de la vivienda (vía datos.gob.ar)",
         alq.get("fecha"))
    carne = ciccra.get("consumo_carne_per_capita", {})
    _add(out, "consumo_carne", carne.get("valor"),
         "kg/hab/año", "CICCRA", carne.get("fecha"))
    inf = indec.get("informalidad_trimestral") or indec.get("informalidad_anual", {})
    _add(out, "informalidad", round(inf.get("valor", 0) * 100, 1),
         "%", "INDEC EPH", inf.get("fecha"))
    ipi = indec.get("ipi", {})
    _add(out, "mortalidad_pymes", round(ipi.get("variacion_mensual_pct", 0), 2),
         "% m/m (IPI desest.)", "INDEC — IPI manufacturero desestacionalizado (vía datos.gob.ar)",
         ipi.get("fecha"))
    isac = indec.get("isac", {})
    _add(out, "despacho_cemento", round(isac.get("valor", 0), 1),
         "índice ISAC", "INDEC — ISAC desestacionalizado (vía datos.gob.ar)", isac.get("fecha"))
    sub = indec.get("subocupacion_demandante", {})
    _add(out, "pluriempleo", round(sub.get("valor", 0) * 100, 1),
         "%", "INDEC EPH", sub.get("fecha"))
    emp = indec.get("empleo_registrado", {})
    _add(out, "empleo_registrado", emp.get("valor"),
         "miles de puestos", "Min. de Capital Humano — SIPA (vía datos.gob.ar)",
         emp.get("fecha"))
    seg = snic.get("inseguridad_snic", {})
    _add(out, "inseguridad", seg.get("total_hechos"),
         "hechos/año", "SNIC — Ministerio de Seguridad (calidad UNODC grado A)",
         str(seg.get("anio")))
    icc = utdt.get("icc_utdt", {})
    _add(out, "icc_utdt", round(icc.get("valor", 0), 1),
         "índice", "UTDT — Índice de Confianza del Consumidor (CIF)", icc.get("fecha"))
    pn = (raw.get("pobreza") or {}).get("pobreza_nowcast", {})
    _add(out, "pobreza_nowcast", pn.get("valor"),
         "% de personas", "UTDT — Nowcast de Pobreza (González-Rozada)", pn.get("fecha"))
    il = utdt.get("indice_lider", {})
    _add(out, "indice_lider", round(il.get("valor", 0), 1),
         "índice", "UTDT — Índice Líder (CIF)", il.get("fecha"))
    # sd puede venir {} (nunca corrió) o {"...": null} (Trends 429/timeout,
    # ver "nota" del dump crudo) -- en ambos casos _add() se llama SIEMPRE
    # (con valor=None si no hay dato) para que _carry_forward pueda
    # detectar el indicador y restaurar el último valor publicado. Antes
    # `if sd:` omitía la llamada entera cuando Trends fallaba: el indicador
    # quedaba AUSENTE del dict (no solo desactualizado), invisible para
    # _carry_forward (que solo repara claves ya presentes con valor=None) --
    # hallazgo real 2026-07-09, sentimiento_digital desapareció del índice
    # tras varias corridas seguidas que agotaron el rate limit de Trends.
    sd = trends.get("sentimiento_digital", {}).get("interes_relativo") or {}
    _add(out, "sentimiento_digital", round(sum(sd.values()) / len(sd), 1) if sd else None,
         "interés 0–100", "Google Trends", ts,
         detalle_txt=("El titular es el pulso de los últimos 3 meses (escala relativa "
                      "de esa ventana). El gráfico y el puntaje del ITVC usan la "
                      "canasta mensual de ventana fija desde 2021, cuyo cociente "
                      "contra el 4T-2023 es inmune a la renormalización de Trends."))
    motos = cafam.get("patentamiento_motos", {})
    _add(out, "patentamiento_motos", motos.get("valor"),
         "unidades", "CAFAM", motos.get("fecha"))
    return out


def build_series():
    """Agrupa output/series/*.csv en {indicador: [{fecha, valor}, ...]} asc."""
    series = {}
    for csv_path in sorted(glob.glob(str(OUT / "series" / "*.csv"))):
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ind = row["indicador"]
                try:
                    val = float(row["valor"])
                except (TypeError, ValueError):
                    continue
                series.setdefault(ind, []).append({"fecha": row["fecha"], "valor": val})
    for ind in series:
        # Deduplicar por fecha: si un indicador aparece en más de un CSV de
        # cinturón con la MISMA métrica, colapsar a un punto por fecha. (Las
        # métricas distintas van bajo claves distintas — ej. ipc_total en % m/m
        # vs ipc_nivel como insumo deflactor.)
        por_fecha = {p["fecha"]: p for p in series[ind]}
        series[ind] = sorted(por_fecha.values(), key=lambda p: p["fecha"])
    # Alias: algunos indicadores del informe tienen su serie historica bajo otra
    # clave en los CSV. Exponer la serie tambien bajo la clave del indicador para
    # que el sparkline y el modal la encuentren.
    alias = {
        "saldo_comercial_12m": "saldo_comercial",
        "clima_electoral": "votometro_ventaja_lla",   # espíritu reusa la serie del Votómetro
    }
    for ind_key, serie_key in alias.items():
        if serie_key in series and ind_key not in series:
            series[ind_key] = series[serie_key]
    return series


# Histórico acumulado: red de seguridad para NO PERDER DATOS. Cada corrida persiste
# el valor actual de todos los indicadores keyed por mes; los que no tienen serie
# oficial (política, vida sin fuente, espíritu, avances de gestión) construyen así
# su serie temporal mes a mes.
# Se redirige junto al snapshot: acumular_historico() lo REESCRIBE en cada
# corrida, así que sin esto un test que ejecute publicar.py deja el histórico
# versionado modificado aunque el snapshot ya no lo esté (ADR-0178).
HISTORICO_PATH = (Path(os.environ["CIGOB_SALIDA_WEB"]) / "indicadores.json"
                  if os.environ.get("CIGOB_SALIDA_WEB")
                  else ROOT / "data" / "historico" / "indicadores.json")


def _valor_historico(ind):
    """Número a persistir de un indicador: el avance si es reforma; si no, el valor."""
    v = ind.get("avance_pct")
    if not isinstance(v, (int, float)):
        v = ind.get("valor")
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def acumular_historico(informe):
    """Upserta el valor actual de CADA indicador en data/historico/indicadores.json,
    keyed por mes (YYYY-MM). Aunque la fuente no publique serie, el histórico se va
    armando solo y no se pierde ningún dato."""
    store = {}
    if HISTORICO_PATH.exists():
        store = json.loads(HISTORICO_PATH.read_text(encoding="utf-8"))
    store.pop("dolarizacion_depositos", None)
    ym = datetime.now().strftime("%Y-%m")
    for c in informe["cinturones"].values():
        for ik, ind in c["indicadores"].items():
            v = _valor_historico(ind)
            if v is not None:
                store.setdefault(ik, {})[ym] = round(v, 4)
    HISTORICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORICO_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return store


def fusionar_historico(series, store):
    """Inyecta el histórico acumulado como serie de los indicadores que NO tienen
    serie oficial (o tienen <2 puntos). No pisa las oficiales (macro, etc.), que
    traen más historia y otra métrica (ej. IPC: el oficial es el índice nivel, no
    la variación). Nota: inseguridad pasó a mensual (IVI, ADR-0032) con store
    persistente propio — el viejo bug del fallback anual (totales con fecha de
    corrida durante el apagón SNIC del 04-jul-2026) ya no aplica."""
    for ik, meses in store.items():
        if len(series.get(ik, [])) >= 2:
            continue
        puntos = [{"fecha": f"{ym}-01", "valor": v} for ym, v in sorted(meses.items())]
        if puntos:
            series[ik] = puntos
    return series


_LOCAL_PATH = re.compile(r"^[A-Za-z]:[\\/]|[\\/]Users[\\/]|\\\\")

# Jerga técnica que no debe llegar al chip de fuente público (el lector no
# necesita saber que la fuente es un portal CKAN ni que el dato se obtiene por
# scraping). Se normaliza al publicar: es el punto único: aunque el colector
# guarde la jerga en el caché, el snapshot sale limpio.
_FUENTE_JERGA = [
    (re.compile(r"\s*\(scraping directo\)", re.IGNORECASE), ""),
    (re.compile(r"\s+CKAN\b", re.IGNORECASE), ""),
    (re.compile(r"\bscraping\b", re.IGNORECASE), "relevamiento"),
]


def _limpiar_jerga_fuente(fuente: str) -> str:
    for pat, repl in _FUENTE_JERGA:
        fuente = pat.sub(repl, fuente)
    return re.sub(r"\s{2,}", " ", fuente).strip()


def sanitizar_fuentes(informe):
    """Normaliza los campos `fuente` para el snapshot público: reemplaza rutas
    locales del filesystem (no filtrar paths del equipo) y quita la jerga
    técnica de plataforma (CKAN, scraping) que no aporta al lector."""
    for cint in informe["cinturones"].values():
        for key, ind in cint["indicadores"].items():
            fuente = ind.get("fuente")
            if not isinstance(fuente, str):
                continue
            if _LOCAL_PATH.search(fuente):
                ind["fuente"] = ("Votómetro CIGOB" if "votometro" in key.lower()
                                 else "Elaboración propia — CIGOB")
            else:
                ind["fuente"] = _limpiar_jerga_fuente(fuente)
    return informe


# ── Aporte al score por indicador ──────────────────────────────────────────────
# Fuente única de verdad de la transparencia del scoring: replica EXACTAMENTE las
# fórmulas de tensión documentadas en los colectores (macro.py, politica.py,
# gestion.py). El texto de mapeo viene verbatim de esas docstrings. Un test de
# reconciliación (tests/test_publicar.py) verifica que el promedio de los aportes
# reproduce el score publicado de cada cinturón — si una fórmula cambia, el test
# avisa y esto deja de ser una caja negra.

def _clamp10(x):
    return round(max(0.0, min(10.0, x)), 1)

# Población usada para pasar conteos absolutos a tasa por 100.000 hab (INDEC 2024).
POB_AR = 46_700_000

# clave de indicador → (valor → tensión 0–10, texto de mapeo de referencia)
# Los indicadores macro, gestión y política NO están acá: su puntaje viene del
# ITCM/ITCG/ITCP calculado por el colector (macro.py+itcm.py, gestion.py+itcg.py,
# politica.py+itcp.py) y se traduce en aplicar_scoring() vía _scoring_indice().
SCORING = {
    # ── vida cotidiana ── (metodología CIGOB validada may-2026; anclas de dominio)
    "ipc_alimentos":       (lambda v: v,                "0% → 0 · 5% → 5 · 10% → 10 (mensual)"),
    "peso_tarifas":        (lambda v: v,                "0% → 0 · 5% → 5 · 10% → 10 (regulados, m/m)"),
    "brecha_salario_cbt":  (lambda v: (4 - v) * 10 / 3, "4 canastas → 0 · 2,5 → 5 · 1 → 10 (salario formal / CBT)"),
    "consumo_carne":       (lambda v: (55 - v) / 2,     "55 → 0 · 45 → 5 · 35 → 10 (kg/hab/año)"),
    "informalidad":        (lambda v: (v - 25) / 2.5,   "25% → 0 · 37,5% → 5 · 50% → 10"),
    "mortalidad_pymes":    (lambda v: 5 - v,            "+5% → 0 · 0% → 5 · −5% → 10 (IPI m/m)"),
    "despacho_cemento":    (lambda v: (180 - v) / 10,   "180 → 0 · 130 → 5 · 80 → 10 (índice ISAC)"),
    "pluriempleo":         (lambda v: v - 5,            "5% → 0 · 10% → 5 · 15% → 10 (subocupación demandante)"),
    "patentamiento_motos": (lambda v: (70_000 - v) / 5000, "70.000 → 0 · 45.000 → 5 · 20.000 → 10 (unidades/mes)"),
    "icc_utdt":            (lambda v: (60 - v) / 3,     "60 → 0 · 45 → 5 · 30 → 10 (índice de confianza)"),
    # ── espíritu de época ── único puntuable del cinturón (ADR-0049); los ex
    # proxies clima_electoral/sentimiento_digital/icc_utdt están en
    # ESPIRITU_OCULTOS y ya no llegan a este loop
    "clima_electoral":     (lambda v: 5 - v / 3,        "+15pp → 0 · 0 → 5 · −15pp → 10 (gap LLA−PJ, Votómetro)"),
    "sentimiento_digital": (lambda v: v / 10,           "0 → 0 · 50 → 5 · 100 → 10 (interés en inflación/precios/inseguridad/trabajo: mayor = más preocupación)"),
    "indice_intencion_migratoria": (lambda v: v / 10,   "0 → 0 · 50 → 5 · 100 → 10 (interés en términos de intención de emigrar: mayor = más desconexión)"),
    "inseguridad":         (lambda v: (v / POB_AR * 100_000 - 3000) / 400,
                                                        "tasa/100k hab (pob. 46,7M): 3.000 → 0 · 5.000 → 5 · 7.000 → 10"),
    # Se puntúa sobre la variación interanual REAL (deflactada), no el stock nominal.
    "endeudamiento_familiar": (lambda v: 5 + v / 4,     "−20% real → 0 · 0% → 5 · +20% real → 10 (var. interanual real del crédito)", "var_real_12m"),
}

VIDA_CONTEXTO = ("Indicador de contexto — no integra el ITVC (paramétrica CIGOB jul-2026) "
                 "o su componente no pudo calcularse en esta corrida.")

MACRO_CONTEXTO = "Indicador de contexto — no integra el ITCM (paramétrica CIGOB may-2026)."
GESTION_CONTEXTO = "Indicador de contexto — no integra el ITCG (paramétrica CIGOB jul-2026)."
# Sin uso hoy: los 12 indicadores de política puntúan en el ITCP (itcp.py no
# declara indicadores de contexto todavía) — se deja igual que MACRO/GESTION_CONTEXTO
# por si un futuro indicador de política entra como contexto puro.
POLITICA_CONTEXTO = "Indicador de contexto — no integra el ITCP (paramétrica CIGOB jul-2026)."

SCORE_EXPLICACION = {
    "macro":          ("ITCM (índice paramétrico 0–100, mayor = menos tensión) ponderado por 6 dimensiones: "
                       "estabilidad monetaria 26%, viabilidad fiscal-comercial 24%, financiamiento 16%, "
                       "actividad 11%, competitividad externa 11%, inversión 12%. La tensión del cinturón es (100 − ITCM) / 10."),
    "politica":       ("ITCP (índice paramétrico 0–100, mayor = más capital político) ponderado por 5 dimensiones: "
                       "poder legislativo 30%, alianzas territoriales 25%, cohesión interna del oficialismo 20%, "
                       "conflicto social 15%, imagen y voto 10%. La tensión del cinturón es (100 − ITCP) / 10."),
    "gestion":        ("ITCG (índice paramétrico 0–100, mayor = agenda de reformas ejecutándose) ponderado por 5 dimensiones: "
                       "reformas económicas 35%, reforma del Estado 25%, reforma laboral 15%, "
                       "privatizaciones e inversión 15%, reforma social y orden 10%. La tensión del cinturón es (100 − ITCG) / 10."),
    "vida_cotidiana": ("ITVC-B100 (índice de seguimiento, 100 = promedio del 4T-2023; mayor = mejora acumulada de la vida "
                       "cotidiana) ponderado por 6 dimensiones: ingresos y consumo 37%, precios 25%, "
                       "vulnerabilidad financiera 10%, empleo 15%, confianza y percepción 8%, seguridad 5%. "
                       "La tensión del cinturón es 5 − (ITVC − 100) × 0,2."),
    "espiritu_epoca": ("Tensión (0–10) de la intención migratoria, único indicador del cinturón "
                       "(v1 provisional). Mayor = más desconexión entre el gobierno y el humor social."),
}


def _estado(score):
    """Réplica de generar_informe._estado: traduce el score 0–10 a estado."""
    if score <= UMBRALES["ESTABLE_MAX"]:
        return "estable"
    if score <= UMBRALES["EN_TENSION_MAX"]:
        return "en_tension"
    return "tensionado"


def recomputar_vida_y_global(informe):
    """Vida cotidiana se puntúa con el ITVC-B100 calculado en aplicar_scoring
    (el colector vida_cotidiana.py sigue emitiendo su score legacy en el cache;
    esta es la fuente de verdad del snapshot publicado). Acá solo se recalcula
    el score global ponderado para que el snapshot sea internamente coherente."""
    num = sum(c["score"] * PESOS_CINTURONES.get(k, 0.0)
              for k, c in informe["cinturones"].items())
    den = sum(PESOS_CINTURONES.get(k, 0.0) for k in informe["cinturones"])
    if den:
        informe["score_global"] = round(num / den, 1)
    return informe


# Umbral de dimensión CRÍTICA (ADR-0020): la agregación lineal compensa entre
# dimensiones; por debajo del umbral la dimensión se marca explícitamente como
# "no compensada" — señal visible en la web, sin tocar la fórmula.
UMBRAL_CRITICO_BANDAS = 30.0    # índices 0-100 por bandas: la peor banda
UMBRAL_CRITICO_BASE100 = 85.0   # base-100: "deterioro sustancial" (escala del doc)


def _marcar_dimensiones_criticas(bloque, umbral):
    for dim in (bloque or {}).get("dimensiones", {}).values():
        dim["critica"] = dim["puntaje"] < umbral


def _scoring_indice(c, clave, mod, contexto_txt, input_txt_fn):
    """Cinturones con índice paramétrico (macro → ITCM, gestión → ITCG,
    política → ITCP): el puntaje lo computa el colector; acá solo se traduce
    cada puntaje 0-100 a tensión equivalente (para la semántica 0-10 del
    modal) y se anota la tabla de bandas + peso en el índice. Los indicadores
    con en_indice=false son contexto y no aportan."""
    ajustes = {a["indicador"]: a for a in (c.get(clave) or {}).get("ajustes_aplicados", [])}
    sigla = clave.upper()
    # Rango de robustez (ADR-0019): pesos ±20% + bandas vecinas, MC con semilla
    # fija → p05-p95 publicado junto al valor puntual del índice.
    bloque = c.get(clave)
    if bloque and bloque.get("dimensiones"):
        try:
            bloque["robustez"] = sensibilidad.robustez_compacta(
                bloque, getattr(mod, f"BANDAS_{sigla}"),
                lambda v: round((100 - v) / 10, 1),
                anclas=getattr(mod, f"ANCLAS_{sigla}", None),
                # Solo el ITCM tiene indicadores deflactados por el IPC
                # (ADR-0078); los demás índices no comparten deflactor.
                exposicion=(sensibilidad.EXPOSICION_DEFLACTOR_ITCM
                            if sigla == "ITCM" else None),
                transformaciones=getattr(mod, f"TRANSFORMACIONES_{sigla}", None))
        except Exception as e:
            print(f"[WARN] robustez {sigla}: {e}")
        _marcar_dimensiones_criticas(bloque, UMBRAL_CRITICO_BANDAS)
    for ikey, ind in c["indicadores"].items():
        aporte = formula = nota = lectura = None
        p = ind.get(f"puntaje_{clave}")
        if ind.get("en_indice") and isinstance(p, (int, float)):
            aporte = round((100 - p) / 10, 1)
            # El score del cinturón NO es la suma de estos números: el índice
            # agrega puntajes ponderados y la tensión sale del agregado. Este
            # número es la tensión EQUIVALENTE del indicador leído solo — y el
            # texto lo dice, con lectura especial en los extremos (un "0" pelado
            # parecía dato roto y un logro terminado leía como irrelevante).
            cm = lambda x: str(x).replace(".", ",")
            if p >= 95:
                lectura = (f"Leído solo en la escala del {sigla}, equivale a una tensión de "
                           f"{cm(aporte)}/10: puntaje pleno o casi pleno — este frente está "
                           f"logrado y hoy no agrega tensión al índice.")
            elif p <= 15:
                lectura = (f"Leído solo en la escala del {sigla}, equivale a una tensión de "
                           f"{cm(aporte)}/10: puntaje mínimo — este frente concentra la "
                           f"tensión del cinturón.")
            else:
                lectura = (f"Leído solo en la escala del {sigla}, este indicador equivale a "
                           f"una tensión de {cm(aporte)}/10.")
            peso = ind.get("peso_efectivo")
            peso_txt = f"; pesa {peso * 100:.1f}%".replace(".", ",") + f" del {sigla}" if peso else ""
            formula = (f"Anclas {sigla}: {mod.texto_bandas(ikey)} "
                       f"(puntaje interpolado entre anclas: {p}{peso_txt})")
            if ikey in ajustes:
                aj = ajustes[ikey]
                origen = "automático" if aj.get("origen") == "automatico" else "del analista"
                nota = f"Ajuste {origen}: banda {aj['de']} → {aj['a']}. {aj.get('justificacion', '')}"
        elif ind.get("en_indice") is False:
            nota = contexto_txt
        ind["aporte_score"] = aporte
        ind["aporte_formula"] = formula
        ind["aporte_nota"] = nota
        ind["aporte_lectura"] = lectura
        ind["aporte_input_txt"] = input_txt_fn(ikey, ind)


def _macro_input_txt(ikey, ind):
    """'Valor usado' que muestra el modal: la descomposición del número que
    realmente se puntúa (no siempre coincide con el valor mostrado)."""
    if ikey == "rem_ipc_12m" and ind.get("equivalente_mensual") is not None:
        return (f"equiv. mensual {coma(ind['equivalente_mensual'])}% "
                f"(raíz-12 del {coma(ind.get('valor'))}% anual)")
    if ikey == "reservas_bcra" and ind.get("netas_sdds_estricto") is not None:
        return (f"netas {int(ind.get('valor', 0))} = SDDS estricto {int(ind['netas_sdds_estricto'])} "
                f"+ Tesoro {int(ind.get('depositos_tesoro', 0))} "
                f"+ Bopreal {int(ind.get('bopreal_12m', 0))} (M USD)")
    if ikey == "idc" and ind.get("componentes"):
        c, n = ind["componentes"], ind.get("niveles") or {}
        txt = (f"{coma(ind.get('valor'))} σ = precio {coma(c.get('precio'))} · "
               f"volumen {coma(c.get('volumen'))} · asignación {coma(c.get('asignacion'))} "
               f"({ind.get('semaforo', '')})")
        if n:
            txt += (f" — niveles: tasa real {coma(n.get('tasa_real_pp'))} pp · "
                    f"depósitos {coma(n.get('dep_real_ia_pct'))}% i.a. real · "
                    f"holgura {coma(n.get('holgura_pct'))}%")
        return txt
    if ikey == "idm" and ind.get("m3_real_ia") is not None:
        return (f"brecha {coma(ind.get('valor'))} pp = M3 priv. real i.a. "
                f"{coma(ind['m3_real_ia'])}% − M2 priv. real i.a. {coma(ind['m2_real_ia'])}%")
    if ikey == "presion_dolarizacion" and ind.get("metrica") is not None:
        meses = int(ind.get("ventana_meses") or 0)
        periodo = f"{meses} {'mes' if meses == 1 else 'meses'}"
        if ind.get("regimen") == "precio":
            return (f"presión {coma(ind.get('valor'))} pts = brecha CCL/mayorista "
                    f"{coma(ind['metrica'])}% (promedio móvil {periodo})")
        if ind.get("regimen") == "flujo":
            ventana = (f"ventana de transición: {periodo}" if ind.get("ventana_parcial")
                       else f"ventana móvil {periodo}")
            return (f"presión {coma(ind.get('valor'))} pts = compras netas de USD "
                    f"de personas humanas {coma(ind['metrica'])}% del M2 privado "
                    f"({ventana})")
    if ikey == "iai" and ind.get("componentes"):
        c = ind["componentes"]
        partes = [f"ISAC {coma(c.get('isac'))}%", f"BK importados {coma(c.get('bk_importados'))}%"]
        if c.get("patentamientos_comerciales") is not None:
            partes.append(f"patentamientos {coma(c['patentamientos_comerciales'])}%")
        return f"{coma(ind.get('valor'))}% i.a. = " + " · ".join(partes)
    if ikey == "icip" and ind.get("componentes"):
        c = ind["componentes"]
        return (f"{coma(ind.get('valor'))}% i.a. = servicios tech {coma(c.get('servicios_tech'))}% · "
                f"productividad {coma(c.get('productividad'))}%")
    return None


def _gestion_input_txt(ikey, ind):
    """'Valor usado' del modal para gestión: la descomposición del número que
    puntúa (compuestos como el ILCE o el Fondo de Cese exponen componentes)."""
    if ind.get("detalle_txt"):                       # detalle rico (ej. RIGI oficial)
        return ind["detalle_txt"]
    if ikey == "fal_modernizacion_laboral" and ind.get("componentes"):
        c = ind["componentes"]
        partes = [f"{n} {coma(v)}" for n, v in c.items() if v is not None]
        return f"índice {coma(ind.get('valor'))} = " + " · ".join(partes)
    if ikey == "privatizaciones" and ind.get("etapa_promedio") is not None:
        return (f"etapa promedio {coma(ind['etapa_promedio'])}/4 sobre "
                f"{ind.get('empresas', '?')} empresas de la cartera Ley Bases")
    return None


def _politica_input_txt(ikey, ind):
    """'Valor usado' del modal para política: la descomposición del número que
    puntúa (protestas_caba puntúa sobre la variación vs. 2023, no el conteo
    crudo de eventos; adhesion_reformas_provincial expone la cuenta de
    provincias detrás del %)."""
    if ind.get("detalle_txt"):                       # detalle rico (ej. protestas_caba, ACLED)
        return ind["detalle_txt"]
    if ikey == "adhesion_reformas_provincial" and ind.get("n_provincias") is not None:
        # "jurisdicciones", NO "provincias": de las 24, una es CABA, que no
        # es una provincia -- llamarlas "24 provincias" sería impreciso.
        return f"{ind['n_provincias']} de 24 jurisdicciones adheridas al RIGI"
    if ikey == "cohesion_bloque" and ind.get("componentes"):
        # Compuesto bicameral (ADR-0048): la descomposición por cámara,
        # mismo patrón que el Fondo de Cese en gestión. El peso nominal
        # (65/35) solo se muestra cuando ambas cámaras aportan — con una
        # sola, el compuesto renormaliza y el 65/35 sería engañoso.
        camaras = [(nombre, peso, ind["componentes"].get(clave) or {})
                   for nombre, clave, peso in (("Diputados", "diputados", 65),
                                                ("Senado", "senado", 35))]
        camaras = [(n, p, c) for n, p, c in camaras if c.get("valor") is not None]
        partes = [f"{nombre} {coma(c['valor'])}% "
                  + (f"(peso {peso}%, {c.get('n_actas', '?')} actas)" if len(camaras) == 2
                     else f"({c.get('n_actas', '?')} actas)")
                  for nombre, peso, c in camaras]
        if partes:
            return f"{coma(ind.get('valor'))}% = " + " · ".join(partes)
    return None


# ── ITVC (vida cotidiana) — doc 260702, ADR-0018 ──────────────────────────────

AJUSTES_ITVC_PATH = ROOT / "data" / "vida" / "ajustes_itvc.json"
ITVC_BASELINES_PATH = ROOT / "data" / "vida" / "itvc_baselines.json"
ITVC_BASE_MESES = ("2023-10", "2023-11", "2023-12")
ITVC_WINSOR_TOPE = 140.0   # techo de componentes B100 (ADR-0033) — SOLO techo:
                           # un boom (motos 166,7) no compra compensación
                           # ilimitada; las crisis NO se recortan — se señalizan
                           # con el flag de dimensión crítica (ADR-0020)

# Serie transformada (ya rebaseada en descargar_series) → indicador del cinturón
ITVC_SERIES_REBASEADAS = {
    "itvc_alimentos":     "ipc_alimentos",
    "itvc_tarifas":       "peso_tarifas",
    "itvc_alquiler":      "alquiler_real",
    "itvc_ipi":           "mortalidad_pymes",
    "itvc_isac":          "despacho_cemento",
    "itvc_pobreza":       "pobreza_nowcast",
}


def _itvc_rebase_movil12(series, skey):
    """Índice base-100 por ACUMULADO MÓVIL de 12 meses (ADR-0024): promedio de
    los últimos 12 meses de la serie vs el promedio de las ventanas móviles que
    terminan en el 4T-2023. Desestacionaliza flujos con calendario fuerte
    (motos: enero ≈ 2× junio) — misma lógica que la carne (CICCRA ya publica
    su PM-12m). Si la serie no alcanza para las ventanas base, devuelve None
    (cae al fallback de baselines)."""
    serie = series.get(skey) or []
    vals = {p["fecha"][:7]: p["valor"] for p in serie if p.get("valor")}
    yms = sorted(vals)

    def ventana(fin):
        i = yms.index(fin) if fin in yms else -1
        if i < 11:
            return None
        win = yms[i - 11:i + 1]
        # 12 meses CONSECUTIVOS (sin huecos): compara el rango real
        a0, m0 = int(win[0][:4]), int(win[0][5:7])
        af, mf = int(win[-1][:4]), int(win[-1][5:7])
        if (af * 12 + mf) - (a0 * 12 + m0) != 11:
            return None
        return sum(vals[k] for k in win) / 12.0

    bases = [v for v in (ventana(f) for f in ITVC_BASE_MESES) if v]
    actual = ventana(yms[-1]) if yms else None
    if not bases or not actual:
        return None
    return round(actual / (sum(bases) / len(bases)) * 100.0, 1)


def _itvc_rebase_de_serie(series, skey, invertido=False, base_meses=None):
    """Índice base-100 del ÚLTIMO punto de una serie vs su promedio 4T-2023.
    En series trimestrales el 4T-2023 es un único punto (2023-10), que coincide
    naturalmente con la base del doc; en mensuales, el promedio oct-nov-dic.
    `base_meses` permite una base DECLARADA distinta cuando la fuente no midió
    el 4T-2023 (ej. IVI: encuesta suspendida 2020-2023, reanudada ene-2024)."""
    serie = series.get(skey) or []
    vals = {p["fecha"][:7]: p["valor"] for p in serie}
    base_vals = [vals[m] for m in (base_meses or ITVC_BASE_MESES) if vals.get(m) is not None]
    if not serie or not base_vals:
        return None
    base = sum(base_vals) / len(base_vals)
    ult = serie[-1]["valor"]
    if not ult or not base:
        return None
    return round((base / ult if invertido else ult / base) * 100.0, 1)


def _itvc_indices(vida_ind, series):
    """Índices base-100 por componente del ITVC (None = componente sin dato)."""
    idx = {}
    for skey, ikey in ITVC_SERIES_REBASEADAS.items():
        serie = series.get(skey) or []
        idx[ikey] = serie[-1]["valor"] if serie else None
    # Rebase directo desde las series oficiales existentes
    idx["brecha_salario_cbt"] = _itvc_rebase_de_serie(series, "brecha_salario_cbt")
    # Mora del crédito familiar (ADR-0067): % de cartera irregular, invertido
    # (más mora = peor). Desde ADR-0154 sostiene sola la dimensión de
    # vulnerabilidad: endeudamiento_familiar salió del índice.
    idx["mora_familias"] = _itvc_rebase_de_serie(series, "mora_familias", invertido=True)
    idx["icc_utdt"] = _itvc_rebase_de_serie(series, "icc_utdt")
    idx["pluriempleo"] = _itvc_rebase_de_serie(series, "pluriempleo", invertido=True)
    # Empleo registrado privado (ADR-0130): NO invertido — más empleo es mejor.
    # Es el único componente de la dimensión que mide empleo de verdad; los
    # otros tres son proxies (producción, construcción, pluriempleo) — el
    # líder salió del cinturón en ADR-0154.
    idx["empleo_registrado"] = _itvc_rebase_de_serie(series, "empleo_registrado")
    # Informalidad TRIMESTRAL (52.2_ASDJ, barrido vida 2/13): la 303.1 murió en
    # 2020 pero la 52.2 sigue viva — base = 4T-2023 exacto (punto 2023-10),
    # invertida (menos informalidad = mejora). Reemplaza la excepción anual.
    idx["informalidad"] = _itvc_rebase_de_serie(series, "informalidad", invertido=True)
    # Motos (CAFAM), carne (CICCRA PM-12m) e inseguridad (SNIC anual: su serie
    # emite el total del año en YYYY-12, así el 4T-2023 resuelve al año 2023 —
    # la excepción declarada del doc): rebase de la serie reconstruida.
    # Motos por acumulado móvil 12m (ADR-0024): el flujo mensual crudo tiene
    # estacionalidad fuerte y contra la base fija 4T-2023 mide calendario.
    idx["patentamiento_motos"] = (_itvc_rebase_movil12(series, "patentamiento_motos")
                                  or _itvc_rebase_de_serie(series, "patentamiento_motos"))
    idx["consumo_carne"] = _itvc_rebase_de_serie(series, "consumo_carne")
    # IVI (ADR-0032): base = ene-2024, la primera medición tras la reanudación
    # de la encuesta (suspendida 2020-2023; su ventana de 12 meses captura
    # mayormente el año PRE-mandato, así que aproxima bien el arranque).
    idx["inseguridad"] = _itvc_rebase_de_serie(series, "inseguridad", invertido=True,
                                               base_meses=("2024-01",))
    # Sentimiento digital (ADR-0034): canasta mensual Trends de ventana fija —
    # el cociente intra-consulta es inmune a la renormalización. Invertido:
    # más búsquedas de inflación/precios = más urgencia percibida.
    idx["sentimiento_digital"] = _itvc_rebase_de_serie(series, "sentimiento_digital",
                                                       invertido=True)
    # Fallback: constante 4T-2023 documentada en itvc_baselines.json (con
    # fuente) × valor actual del indicador, si la serie no está disponible.
    try:
        bas = json.loads(ITVC_BASELINES_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        bas = {}
    for ikey, invertido in (("consumo_carne", False), ("inseguridad", True),
                            ("patentamiento_motos", False)):
        if idx[ikey] is not None:
            continue
        b = (bas.get(ikey) or {}).get("valor")
        v = (vida_ind.get(ikey) or {}).get("valor")
        idx[ikey] = (round((b / v if invertido else v / b) * 100.0, 1)
                     if b and isinstance(v, (int, float)) and v else None)
    # WINSORIZACIÓN ASIMÉTRICA (ADR-0033, tratamiento de outliers JRC): los
    # componentes B100 se acotan al TECHO de 140 — un boom puntual (motos
    # 166,7: +67% vs base) no debe comprar compensación ilimitada en la
    # agregación lineal. SIN piso deliberadamente: las crisis (endeudamiento
    # 31,7) no se recortan, se señalizan (flag crítica, ADR-0020). El crudo
    # queda en _winsor para la nota del modal.
    idx["_winsor"] = {}
    for ikey, v in list(idx.items()):
        if ikey.startswith("_") or v is None:
            continue
        if v > ITVC_WINSOR_TOPE:
            idx["_winsor"][ikey] = v
            idx[ikey] = ITVC_WINSOR_TOPE
    return idx


VALIDACION_EXTERNA_PATH = ROOT / "output" / "validacion_externa.json"


def _cargar_validacion():
    try:
        return json.loads(VALIDACION_EXTERNA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _validacion_itvc(bloque, series):
    """Anexa al bloque ITVC su validación externa: el índice contra el CONSUMO
    medido (ventas en supermercados a precios constantes, serie
    desestacionalizada del INDEC) — correlación positiva esperada.

    Fue el ICC de UTDT hasta jul-2026 (ADR-0155). Se cambió por dos razones que
    se miden: el ICC ES un componente del ITVC (6,75%), lo que obligaba a
    publicar un índice artificial «sin ICC» para no ser circular; y un tercio del
    peso del índice correlaciona NEGATIVO contra el ICC, porque en el período la
    confianza subió mientras alquiler, pobreza, mora e informalidad empeoraban.
    El consumo no compone el índice y ajusta mejor.

    El ICC no se descarta: queda como contraste DISCRIMINANTE en la conclusión —
    mide si la percepción sigue a las condiciones materiales, y el hallazgo es
    que en estos años lo hizo flojo.
    """
    val = _cargar_validacion()
    itvc_serie = val.get("serie_itvc") or {}
    consumo = val.get("consumo_supermercados_mensual") or {}
    comunes = sorted(set(itvc_serie) & set(consumo))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones", {})
    niveles = corr.get("niveles (ITVC vs consumo)") or {}
    difs = corr.get("primeras diferencias (ITVC vs consumo)") or {}
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    if r_niv is None:
        return
    icc_niv = (corr.get("discriminante: ITVC sin ICC vs ICC (niveles)") or {}).get("r")

    partes = [f"Contra el consumo en supermercados solo —una sola del panel— la correlación es "
              f"{coma(r_niv)} en niveles"
              + (f" y {coma(r_dif)} en los cambios mes a mes" if r_dif is not None else "")
              + ": cuando las condiciones materiales mejoran respecto del arranque del "
                "mandato, la gente efectivamente compra más en términos reales."]
    # El contraste discriminante: percepción contra condiciones. Se emite sólo si
    # el número lo sostiene, y con la lectura puesta — un r bajo acá NO es una
    # falla del índice, es el hallazgo.
    if icc_niv is not None and icc_niv < r_niv:
        partes.append(f"El ánimo, en cambio, acompaña menos: contra la confianza del consumidor "
                      f"(ICC de UTDT) la correlación es {coma(icc_niv)}. No es una falla del "
                      f"índice sino un resultado — en estos años la confianza se movió con más "
                      f"independencia de las condiciones materiales que las condiciones entre sí. "
                      f"Se publica porque distingue: este cinturón mide lo que le pasa a los "
                      f"hogares, no lo que opinan.")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, itvc_serie[m], consumo[m]] for m in comunes],
        "plot": "rebase100",
        "titulo": "¿El ITVC acompaña lo que la gente puede comprar?",
        "sub": ("Paso 9 del estándar JRC/OCDE: un índice válido debe co-moverse con variables "
                "externas relacionadas que no lo componen. Este cinturón no tiene una única "
                "serie de referencia, así que se compara contra un panel de estadísticas "
                "externas y se mira si acompaña más a las de su propio terreno que a las "
                "ajenas. El gráfico compara el índice contra el factor común de las "
                "estadísticas de su terreno que miden volúmenes consumidos por los hogares "
                "—luz, gas, transporte, combustible—: lo que todas ellas comparten, en vez de "
                "una sola. El detalle —las cargas de cada una y el panel completo— está en la "
                "ficha metodológica."),
        "serie_label": "ITVC (reconstrucción mensual)",
        "externa_label": "consumo en supermercados (precios constantes)",
        "trans_label": "ambas series con base 100 en el cuarto trimestre de 2023",
        "conclusion": " ".join(partes),
    }

def _validacion_itcm(bloque):
    """Anexa al bloque ITCM su validación externa: la serie mensual del índice
    (reconstruida desde las series de componentes) contra el ÍNDICE LÍDER de la
    UTDT — correlación positiva esperada.

    Fue el riesgo país hasta jul-2026. Se cambió porque validaba en niveles y en
    ventanas semestrales pero daba ~0 en los saltos de un mes, que es la prueba
    exigente — la que no se puede satisfacer con la tendencia común del período.
    El líder mantiene el co-movimiento mes a mes. Por decisión del editor el
    cambio es un REEMPLAZO: el indicador de mercado no se calcula ni se nombra
    más en ninguna parte del informe (ADR-0154 y sus enmiendas).

    Cada afirmación extra se emite solo si su número la respalda en la corrida.
    """
    val = _cargar_validacion()
    serie = val.get("serie_itcm") or {}
    lider = val.get("indice_lider_mensual") or {}
    comunes = sorted(set(serie) & set(lider))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones_itcm", {})
    niveles = corr.get("niveles (ITCM vs índice líder)") or {}
    difs = corr.get("primeras diferencias (ITCM vs líder)") or {}
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    if r_niv is None or r_dif is None:
        return
    lider_ade = (corr.get("líder adelantado 1 mes vs ITCM") or {}).get("r")
    itcm_ade = (corr.get("ITCM adelantado 1 mes vs líder") or {}).get("r")
    partes = [f"Correlación {coma(r_niv)} en niveles y {coma(r_dif)} en los cambios mes a mes: "
              f"cuando la tensión macroeconómica afloja, la actividad acompaña — y lo hace "
              f"también en el corto plazo, no sólo en la tendencia del período."]

    # Que la correlación aguante en los cambios mes a mes es lo que distingue a
    # este contraste del que había antes, así que se dice — y sólo si el número
    # lo sostiene.
    if abs(r_dif) >= 0.3:
        partes.append("Que el co-movimiento aguante mes a mes es lo que se le pide a un "
                      "ancla externa: es la parte que no se explica por la tendencia común "
                      "del período, que en estos años arrastró a casi todas las series "
                      "argentinas en la misma dirección.")

    # La lectura del adelanto va en contra de lo que sugiere el nombre del índice
    # externo, así que se publica explícita — y sólo si los números la sostienen.
    if (itcm_ade is not None and lider_ade is not None and itcm_ade > r_niv > lider_ade):
        partes.append(f"Un punto que conviene no leer al revés: el ajuste mejora cuando se "
                      f"adelanta el ITCM ({coma(itcm_ade)}) y empeora cuando se adelanta el "
                      f"índice externo ({coma(lider_ade)}). Pese a su nombre, acá funciona como "
                      f"validación del mismo mes y no como alerta temprana.")
    # Puntos de giro (ADR-0158): el régimen de validación que corresponde a un
    # compuesto económico con serie de referencia. Se publica la concordancia,
    # que usa todos los meses, y NO el desfase medio cuando está calculado sobre
    # uno o dos giros confirmados — un promedio de n=1 no es un promedio.
    g = val.get("giros_itcm") or {}
    if g.get("concordancia") is not None:
        conf = len(g.get("giros") or []) - g.get("provisorios", 0)
        partes.append(f"Además del co-movimiento, se mira si los dos ciclos giran juntos, que es "
                      f"la prueba que usan los sistemas de indicadores líderes: el índice y la "
                      f"actividad están en la misma fase —las dos subiendo o las dos bajando— en "
                      f"el {coma(round(g['concordancia'] * 100))}% de los {g['n_meses']} meses "
                      f"comparados, contra el 50% que daría el azar.")
        if conf < 2:
            partes.append(f"El adelanto todavía no se puede estimar: de los "
                          f"{len(g['giros'])} cambios de dirección que el índice registra desde "
                          f"2023, sólo {conf} está lo bastante lejos de los extremos de la serie "
                          f"como para darse por confirmado. Los cercanos al último dato se "
                          f"mueven cuando entran meses nuevos, así que se declaran provisorios "
                          f"en lugar de promediarlos.")
        elif g.get("desfase_medio") is not None:
            partes.append(f"Los cambios de dirección confirmados llegan {coma(abs(g['desfase_medio']))} "
                          f"meses {'antes' if g['desfase_medio'] > 0 else 'después'} que los de la "
                          f"actividad.")
    # ¿El índice agrega algo sobre mirar sus partes? (ADR-0158)
    s = val.get("senales_itcm") or {}
    if s.get("evaluables") and s.get("compuesto"):
        tot = s["compuesto"]["total"]
        partes.append(f"Queda una pregunta más, que es la que justifica construir un índice en "
                      f"vez de mirar los indicadores sueltos: ¿se equivoca menos el conjunto que "
                      f"cada una de sus partes? Contando los cambios de dirección que cada serie "
                      f"marca sin que la actividad los acompañe, y los que la actividad marca sin "
                      f"que la serie los registre, "
                      + ("el índice no acumula ninguno" if tot == 0
                         else f"el índice acumula {coma(tot)}")
                      + f"; de sus {s['evaluables']} componentes medidos, {s['peores']} se "
                      f"equivocan más, {s['iguales']} empatan y {s['mejores']} lo superan.")
    conclusion = " ".join(partes)

    # El recuento de componentes se DERIVA de la composición vigente del índice:
    # escrito a mano quedó viejo cuando entró costo_financiamiento_tesoro
    # (decía "once de sus trece" con catorce indicadores en el ITCM).
    _sin_serie = ("iai", "icip")          # no ingresan a la reconstrucción histórica
    _total = sum(len(d.get("indicadores", {}))
                 for d in bloque.get("dimensiones", {}).values())
    _usados = _total - len(_sin_serie)
    _componentes = (f"{_usados} de sus {_total} componentes"
                    if _total > len(_sin_serie) else "la mayoría de sus componentes")

    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], lider[m]] for m in comunes],
        "plot": "minmax",
        "titulo": "¿El ITCM se mueve con la marcha de la actividad?",
        "sub": ("El contraste del cinturón macro es el Índice Líder de la Universidad Torcuato "
                "Di Tella, que resume la marcha de la actividad económica y no integra el "
                f"índice. El ITCM se reconstruye mes a mes desde las series de {_componentes} "
                "(el IAI y el ICIP no ingresan en esta reconstrucción histórica, ni tampoco los "
                "ajustes del analista: el nivel puede diferir del publicado — lo que valida es "
                "su evolución). La correlación esperada es positiva: menos tensión "
                "macroeconómica, más actividad."),
        "serie_label": "ITCM (reconstrucción mensual)",
        "externa_label": "Índice Líder (UTDT)",
        "trans_label": "series normalizadas al rango del período",
        "conclusion": conclusion,
    }

def _panel_socioeconomico(bloque, sigla: str):
    """Anexa a un bloque el perfil contra el PANEL de estadísticas externas.

    Los compuestos socioeconómicos no tienen serie de referencia (ADR-0159): se
    comparan contra varias y las diferencias se explican. Se agrega a la
    conclusión de la sección de validación, que es donde el lector ya está
    mirando el contraste — no como sección aparte.
    """
    if not bloque or not bloque.get("validacion"):
        return
    panel = (_cargar_validacion().get("panel_validacion") or {}).get(sigla) or {}
    if not panel:
        return
    # el texto se arma ACÁ y no se lee del JSON intermedio: si viniera guardado,
    # corregir una redacción obligaría a re-correr validacion_externa, que sale
    # a la red. Los números sí vienen calculados de allá.
    import panel_validacion as pnl
    texto = pnl.lectura(panel)
    if not texto:
        return
    bloque["validacion"]["panel"] = {
        # La prosa del panel (convergente vs discriminante) va SÓLO a la ficha
        # metodológica: ahí la acompaña la tabla que dice lo mismo con números,
        # y en el tablero era medio kilo de texto antes de llegar al gráfico.
        "lectura": texto,
        "nota_factor": pnl.NOTA_FACTOR,
        "perfil": panel["perfil"],
        "niveles": panel["niveles"],
        "diferencias": panel["diferencias"],
        "n_propias": panel["n_propias"],
        "n_ajenas": panel["n_ajenas"],
    }
    # El factor común (ADR-0161) va PRIMERO —es el contraste contra las tres
    # estadísticas juntas, no contra una— pero sólo con una línea: el desarrollo
    # queda en `detalle`, que la ficha metodológica muestra y el tablero no. La
    # conclusión del tablero ya es larga y sumarle cuatro oraciones la arruina.
    factor = panel.get("factor")
    if factor:
        bloque["validacion"]["panel"]["factor"] = dict(
            factor, detalle=pnl.lectura_factor_detalle(panel))
        # ADELANTE de la conclusión, no atrás: cuando hay factor, es el factor lo
        # que el gráfico dibuja y lo que el titular informa. Si el texto siguiera
        # abriendo con el par suelto, la primera oración describiría una
        # comparación que el lector no tiene a la vista.
        bloque["validacion"]["conclusion"] = (
            pnl.lectura_factor(panel) + " " + bloque["validacion"]["conclusion"])


def _dispersion_itvc(bloque):
    """Anexa al ITVC la dispersión de sus componentes (ADR-0160).

    El índice se mueve muy poco —5 puntos netos en 32 meses— porque sus
    componentes se compensan entre sí. Publicar el neto solo dice «sin cambios»
    donde el dato dice «no cambió en neto pero se recompuso fuerte por dentro».

    Va dentro de la sección de consistencia interna, que es donde el lector ya
    está mirando cómo se relacionan los componentes: la dispersión explica el
    resultado de esa misma sección — si se separaron tanto es porque no repiten.

    La prosa NO nombra componentes: en este archivo se emiten las claves y las
    etiquetas legibles viven en el front. Los nombres van en el campo de datos.
    """
    if not bloque or not bloque.get("redundancia"):
        return
    d = _cargar_validacion().get("dispersion_itvc") or {}
    if not d.get("ultimo") or not d.get("primero"):
        return
    pri, ult = d["primero"], d["ultimo"]
    bloque["dispersion"] = d
    bloque["redundancia"]["conclusion"] += (
        f" Hay un dato que conviene leer junto a éste, porque explica por qué el índice se mueve "
        f"tan poco: sus componentes se compensan. Al arranque del período iban de "
        f"{coma(pri['min']['valor'])} a {coma(pri['max']['valor'])} —un rango de "
        f"{coma(pri['rango'])} puntos— y en el último mes van de {coma(ult['min']['valor'])} a "
        f"{coma(ult['max']['valor'])}, un rango de {coma(ult['rango'])}. El índice, en cambio, se "
        f"movió {coma(d['movimiento_neto'])} puntos netos en todo el período. El promedio dice "
        f"que las condiciones materiales no cambiaron mucho en conjunto, y es cierto; lo que el "
        f"número solo no muestra es que por dentro se recompusieron: unas mejoraron tanto como "
        f"otras empeoraron{_veces_mas_separadas(pri, ult)}."
    )


def _veces_mas_separadas(pri, ult) -> str:
    """«N veces más separadas» DERIVADO, no escrito a mano (ADR-0156): es una
    afirmación sobre el estado de hoy y caduca sola."""
    if not pri.get("rango"):
        return ""
    veces = ult["rango"] / pri["rango"]
    if veces < 1.5:
        return ""
    palabra = {2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete",
               8: "ocho", 9: "nueve", 10: "diez"}.get(round(veces))
    cuanto = palabra + " veces" if palabra else f"{coma(round(veces, 1))} veces"
    return f", y hoy están {cuanto} más separadas entre sí que al principio"


def _redundancia(bloque, clave_val: str):
    """Anexa a un bloque de índice la matriz de correlación ENTRE SUS PROPIOS
    componentes (auditoría de consistencia, jul-2026; genérica desde ADR-0085).

    Es una pregunta distinta de la validación externa: no si el índice acierta,
    sino cuánta información realmente distinta aporta cada componente. Si todos
    se mueven juntos, promediar quince indicadores no da quince lecturas
    independientes, da una sola repetida quince veces.

    El texto se apoya en la comparación NIVELES vs PRIMERAS DIFERENCIAS, que es
    lo que separa co-tendencia de co-movimiento: si el acoplamiento se
    desarma al mirar los cambios mes a mes, lo que había era tendencia
    compartida, no información repetida.
    """
    red = _cargar_validacion().get(clave_val) or {}
    if red.get("r_abs_medio") is None:
        return
    n_alt = len(red.get("pares_altos") or [])
    dif = red.get("diferencias") or {}
    # Se emiten las CLAVES: las etiquetas legibles viven en el front
    # (web/src/lib/datos.ts), que es la fuente única de nombres públicos.
    top = [{"a": p["a"], "b": p["b"], "r": p["r"],
            "cruzado": not p["misma_dimension"],
            "por_diseno": p.get("por_diseno")}
           for p in (red.get("pares_altos") or [])[:6]]

    # El hallazgo central: qué queda del acoplamiento al quitar la tendencia.
    if dif.get("r_abs_medio") is not None:
        veredicto = (
            f"El dato decisivo es qué queda de ese acoplamiento al mirar los cambios "
            f"mes a mes en vez de los niveles, que es lo que separa una tendencia "
            f"compartida de información repetida: la correlación media cae a "
            f"{coma(dif['r_abs_medio'])} y "
            + (f"ningún par supera el umbral. "
               if dif.get("share_altos") == 0 else
               f"sólo un {dif['share_altos']:.0%} de los pares lo supera. ")
            + f"Es decir que los componentes suben y bajan con el ciclo, pero sus "
              f"movimientos de cada mes son en buena medida propios: lo que parecía "
              f"redundancia es sobre todo una época en común. ")
    else:
        veredicto = ("No hay suficientes meses para contrastar los niveles contra los "
                     "cambios mes a mes, que es lo que separaría una tendencia "
                     "compartida de información repetida. ")

    bloque["redundancia"] = {
        "n_indicadores": red["n_indicadores"],
        "n_pares": red["n_pares"],
        "r_abs_medio": red["r_abs_medio"],
        "share_altos": red["share_altos"],
        "share_bajos": red["share_bajos"],
        "umbral": red["umbral"],
        "pares_cruzados": red["pares_cruzados"],
        "diferencias": dif,
        "top": top,
        "titulo": "¿Cuánta información distinta aporta cada componente?",
        "sub": (f"Un índice que promedia sus componentes supone que cada uno aporta algo "
                f"que los demás no. Para comprobarlo se cruzan los puntajes mensuales de "
                f"los {red['n_indicadores']} componentes que tienen serie histórica, "
                f"{red['n_pares']} pares en total, y se mide cuánto se mueven juntos."),
        "conclusion": (
            f"La correlación media entre pares es {coma(red['r_abs_medio'])}: ni componentes "
            f"independientes ni una sola señal repetida. Un {red['share_altos']:.0%} de los pares "
            f"se mueve muy junto (por encima de {coma(red['umbral'])}) y un "
            f"{red['share_bajos']:.0%} es prácticamente independiente. "
            + veredicto
            + (f"De los {n_alt} pares que superan el umbral en niveles, "
               f"{red.get('pares_no_explicados', 0)} acoplan indicadores de dimensiones "
               f"distintas sin una razón de diseño que lo explique, y son los que conviene "
               f"seguir. Los demás, o comparten dimensión —donde su peso conjunto está "
               f"acotado— o están acoplados a propósito. " if n_alt else
               "Ningún par supera el umbral: no hay dos componentes que se muevan "
               "prácticamente al unísono. ")
            + ("La consecuencia práctica para el lector se mantiene: cuando varias "
               "dimensiones coinciden en el diagnóstico, eso no debe leerse como varias "
               "confirmaciones independientes del mismo resultado.")),
    }


COBERTURA_MINIMA_BASE = 0.6


def _linea_base(bloque):
    """Anexa al ITCM su punto de partida y la distancia recorrida (ADR-0106).

    La auditoría de macro observó que el índice puntúa el estado actual contra
    anclas fijas: diciembre de 2023 y hoy se evalúan con la misma tabla. Eso es
    correcto para medir tensión vigente, pero el objetivo declarado incluye
    avanzar respecto de lo recibido en la transición, y esa mitad quedaba sin
    responder. La propia auditoría marcó que no hace falta tocar el índice —es
    un cambio de presentación— y esto es exactamente eso: el mismo número, con
    su referencia al lado.

    El valor de base viene de la misma reconstrucción con la que el índice se
    valida contra su ancla externa, no de un cálculo nuevo, así que no pueden
    divergir.

    No se publica si la cobertura del mes de base no alcanza el piso: el
    traspaso es el mes peor cubierto de toda la serie —varias series arrancan
    con el mandato— y una base calculada sobre media docena de componentes
    daría una distancia recorrida que parece medida y no lo está.
    """
    base = (_cargar_validacion().get("linea_base_itcm") or {})
    valor_base = base.get("valor")
    cobertura = base.get("cobertura") or 0
    actual = bloque.get("valor")
    if valor_base is None or actual is None:
        return
    if cobertura < COBERTURA_MINIMA_BASE:
        return

    brecha = actual - valor_base
    mes_base = "diciembre de 2023"
    signo = "arriba del" if brecha >= 0 else "abajo del"

    bloque["linea_base"] = {
        "periodo": base.get("periodo"),
        "valor": valor_base,
        "brecha": round(brecha, 1),
        "cobertura": cobertura,
        # Se emiten las CLAVES: las etiquetas legibles viven en el front.
        "sin_dato": base.get("sin_dato") or [],
        "titulo": "¿Cuánto se avanzó desde el punto de partida?",
        "sub": ("El índice mide la situación de cada mes contra una tabla fija, de modo "
                "que un mes del traspaso y uno de hoy se evalúan con la misma vara. Eso "
                "responde qué tan tensa está la macroeconomía hoy, pero no cuánto se "
                "movió desde lo que se recibió. Reconstruido con el mismo método, el "
                "índice del mes del traspaso funciona como referencia permanente."),
        "conclusion": (
            f"En {mes_base} el índice marcaba {coma(round(valor_base, 1))}. Hoy marca "
            f"{coma(round(actual, 1))}: {coma(abs(round(brecha, 1)))} puntos {signo} "
            f"punto de partida. "
            + (f"La base se calcula sobre el {cobertura:.0%} del peso del índice —el resto "
               f"de los componentes todavía no tenía serie en esa fecha—, de modo que es "
               f"una referencia de orden de magnitud y no una medición exacta."
               if cobertura < 0.95 else
               "La base cubre la totalidad del peso del índice.")),
    }


def _rezago(bloque, rezago_meses: dict, pulso: float, estructural: float):
    """Anexa a un bloque de índice el perfil temporal de sus componentes
    (ADR-0092, prioridad 5 de la auditoría de jul-2026).

    La auditoría observó que en un mismo puntaje mensual conviven indicadores
    casi en tiempo real con otros que describen una realidad de hace uno o dos
    años, y que al combinarse "pueden dar la sensación de que todo el índice
    describe julio de 2026 cuando en rigor una porción relevante describe
    2024-2025". La ficha de cada indicador ya declaraba su rezago; lo que
    faltaba era decirlo en el informe.

    Se pondera por peso EFECTIVO, que es el que el indicador tiene realmente en
    el índice una vez renormalizado, no por su peso nominal dentro de la
    dimensión.
    """
    filas = []
    for dim in bloque.get("dimensiones", {}).values():
        for k, ind in dim.get("indicadores", {}).items():
            meses = rezago_meses.get(k)
            peso = ind.get("peso_efectivo")
            if meses is not None and peso:
                filas.append((k, float(peso), float(meses)))
    if not filas:
        return
    total = sum(p for _, p, _ in filas)
    promedio = sum(p * m for _, p, m in filas) / total
    share_pulso = sum(p for _, p, m in filas if m <= pulso) / total
    share_estr = sum(p for _, p, m in filas if m >= estructural) / total
    rezagados = [{"indicador": k, "meses": m}
                 for k, _, m in sorted(filas, key=lambda x: -x[2]) if m >= estructural]

    prom_txt = coma(round(promedio, 1))
    bloque["rezago"] = {
        "promedio_meses": round(promedio, 1),
        "share_pulso": round(share_pulso, 3),
        "share_estructural": round(share_estr, 3),
        "umbral_pulso": pulso,
        "umbral_estructural": estructural,
        # Se emiten las CLAVES: las etiquetas legibles viven en el front.
        "mas_rezagados": rezagados,
        "titulo": "¿De cuándo es la foto que describe el índice?",
        "sub": ("Cada indicador mira una ventana de tiempo distinta. Uno que promedia "
                "los últimos doce meses describe, en promedio, la situación de hace "
                "seis, aunque su último dato sea de ayer. Ponderando cada componente "
                "por el peso que realmente tiene en el índice, se obtiene de cuándo es "
                "la foto completa."),
        "conclusion": (
            f"El índice describe, en promedio ponderado, la situación de hace "
            f"{prom_txt} meses. Un {share_pulso:.0%} de su peso corresponde a "
            f"indicadores de pulso inmediato, que reflejan las últimas semanas"
            + (f", y un {share_estr:.0%} a indicadores que describen el año anterior. "
               if share_estr else ". ")
            + ("La consecuencia práctica: un cambio de la coyuntura política no se ve "
               "de inmediato en el número. Los indicadores rápidos lo registran enseguida "
               "y los de ventana larga lo van incorporando durante los meses siguientes, "
               "de modo que el índice tiende a moverse después —y de forma más suave— que "
               "los hechos que lo motivan. Leerlo como una fotografía del mes en curso "
               "sobreestima su inmediatez.")),
    }


def _familias(bloque, familias: dict, meta_familias: dict):
    """Anexa a un bloque de índice su lectura descompuesta en tipos de señal
    (ADR-0094, prioridad 2 de la auditoría de jul-2026).

    La auditoría observó que el cinturón mezclaba bajo una misma etiqueta la
    tensión que otros actores ejercen, la capacidad propia del gobierno y los
    recursos con que negocia — tres preguntas distintas cuyo promedio no
    responde ninguna con precisión.

    La separación es de lectura y no de cálculo: el índice se computa igual y
    los pesos no cambian. Cada familia es el promedio de los puntajes de sus
    componentes, ponderado por peso efectivo, de modo que las tres reconstruyen
    el índice general.
    """
    acc = {}
    for dim in bloque.get("dimensiones", {}).values():
        for k, ind in dim.get("indicadores", {}).items():
            fam = familias.get(k)
            peso = ind.get("peso_efectivo")
            if not fam or not peso:
                continue
            a = acc.setdefault(fam, {"peso": 0.0, "suma": 0.0, "componentes": []})
            a["peso"] += float(peso)
            a["suma"] += float(peso) * float(ind["puntaje_banda"])
            a["componentes"].append({"indicador": k, "puntaje": ind["puntaje_banda"]})
    if len(acc) < 2:
        return

    familias_out = []
    for clave, a in acc.items():
        m = meta_familias.get(clave, {})
        familias_out.append({
            "clave": clave,
            "nombre": m.get("nombre", clave),
            "glosa": m.get("glosa", ""),
            "puntaje": round(a["suma"] / a["peso"], 1),
            "share": round(a["peso"], 3),
            # ordenados de peor a mejor: el que primero conviene mirar va arriba
            "componentes": sorted(a["componentes"], key=lambda c: c["puntaje"]),
        })
    familias_out.sort(key=lambda f: f["puntaje"])

    peor, mejor = familias_out[0], familias_out[-1]
    brecha = round(mejor["puntaje"] - peor["puntaje"], 1)
    # Distancia entre las DOS más flojas. El guard de `brecha` compara el peor
    # contra el mejor, así que no ve un empate abajo: con tensión 63,2 y
    # capacidad 63,5 la card llegó a nombrar a una "lo más flojo del cinturón"
    # por 0,3 puntos, mientras la brecha contra recursos daba 11,7 y pasaba el
    # umbral (ADR-0171). Ordenar dos números indistinguibles y publicarlo como
    # hallazgo es leer ruido.
    empate_abajo = (len(familias_out) > 2 and
                    round(familias_out[1]["puntaje"] - peor["puntaje"], 1) < 2.0)

    bloque["familias"] = {
        "familias": familias_out,
        "titulo": "¿Qué tipo de cosa está midiendo el índice?",
        "sub": ("El índice reúne tres preguntas distintas: cuánta presión ejercen sobre el "
                "Gobierno los demás actores, cuánto consigue el Gobierno por su cuenta, y con "
                "qué recursos cuenta para negociar. El promedio de las tres no responde "
                "ninguna por separado, así que acá se muestran abiertas. Es una separación de "
                "lectura: el índice se calcula igual y los pesos no cambian. Cada familia "
                "muestra qué porción del índice carga, porque ese reparto se mueve cuando "
                "entran o salen indicadores y explica parte de lo que cambia entre lecturas."),
        "conclusion": (
            (f"Leído por partes, las dos partes más flojas del cinturón "
             f"—«{peor['nombre'].lower()}» ({coma(peor['puntaje'])}) y "
             f"«{familias_out[1]['nombre'].lower()}» ({coma(familias_out[1]['puntaje'])})— "
             f"están hoy empatadas, y la más sólida es «{mejor['nombre'].lower()}» "
             f"({coma(mejor['puntaje'])}): "
             if empate_abajo else
             f"Leído por partes, lo más flojo del cinturón es «{peor['nombre'].lower()}» "
             f"({coma(peor['puntaje'])}) y lo más sólido, «{mejor['nombre'].lower()}» "
             f"({coma(mejor['puntaje'])}): ")
            + (f"una diferencia de {coma(brecha)} puntos. " if brecha >= 5 else
               "una diferencia pequeña, de modo que las tres dimensiones del problema están "
               "hoy en un estado parecido. ")
            + ("Importa para leer el número general, porque las tres cosas no se compensan "
               "entre sí: un Gobierno puede tener con qué negociar y aun así no lograr que "
               "sus normas prosperen, y esas dos situaciones exigen respuestas distintas.")),
    }


def _fecha_dato_a_date(valor):
    """`fecha_dato` → date, aceptando el rótulo mensual además del día exacto.

    No todas las fichas fechan al día: las de frecuencia mensual rotulan su dato
    como «2026-05», que `date.fromisoformat` rechaza. Cuando el ITVC se sumó al
    perfil de vintages, tres de sus catorce componentes venían así
    —`consumo_carne`, `inseguridad`, `patentamiento_motos`— y el `except
    ValueError` los descartaba EN SILENCIO: la card habría dicho que describe el
    cinturón entero cubriendo once. Un rótulo mensual se lee como el primero de
    ese mes, que es la lectura conservadora (la más antigua posible).
    """
    s = str(valor)[:10]
    for fmt in (s, f"{s}-01" if len(s) == 7 else s):
        try:
            return date.fromisoformat(fmt)
        except ValueError:
            continue
    return None


def _vintages(cinturon, indice_key):
    """Anexa al bloque de índice el perfil de VINTAGES de sus componentes: de
    qué fecha es el dato de cada uno (ADR-0099).

    Es la observación 3.3 de la auditoría del cinturón de gestión: los
    componentes llegan con rezagos de publicación muy distintos y el índice los
    combina en un puntaje mensual, de modo que "el mes del índice es en rigor un
    mosaico de vintages" y conviene decirlo en la presentación, no sólo en cada
    ficha.

    No hace falta declarar nada: cada card ya trae su `fecha_dato`. Eso es
    deliberado — un diccionario paralelo se desactualiza en silencio, que es el
    modo de falla de ADR-0082 y ADR-0089.

    Distinto del rezago de ADR-0092, que mide el centroide de la VENTANA de cada
    indicador. Acá se mide la antigüedad del DATO. Un indicador puede tener el
    dato de ayer y describir el promedio del último año, o al revés.
    """
    bloque = cinturon.get(indice_key)
    if not bloque:
        return
    hoy = date.today()
    filas = []
    for clave, ind in (cinturon.get("indicadores") or {}).items():
        if not ind.get("en_indice"):
            continue
        fecha, peso = ind.get("fecha_dato"), ind.get("peso_efectivo")
        if not fecha or not peso:
            continue
        d_fecha = _fecha_dato_a_date(fecha)
        if d_fecha is None:
            print(f"  [WARN] vintages {indice_key}: {clave} tiene fecha_dato "
                  f"ilegible ({fecha!r}) y queda fuera del perfil")
            continue
        # Algunas fichas rotulan su ventana por el mes de CIERRE, que puede
        # caer adelante de hoy (la encuesta del ISAC pregunta por los tres
        # meses siguientes). Eso no es un dato del futuro: es antigüedad cero.
        dias = max(0, (hoy - d_fecha).days)
        filas.append({"indicador": clave, "fecha": str(fecha)[:10],
                      "dias": dias, "peso": float(peso)})
    if len(filas) < 3:
        return

    total = sum(f["peso"] for f in filas)
    dias_medio = sum(f["dias"] * f["peso"] for f in filas) / total
    mas_viejo = max(filas, key=lambda f: f["dias"])
    mas_nuevo = min(filas, key=lambda f: f["dias"])
    # los que arrastran el promedio: más de un trimestre de antigüedad
    rezagados = sorted([f for f in filas if f["dias"] >= 90],
                       key=lambda f: -f["dias"])

    meses = lambda d: round(d / 30.44, 1)
    _MESES_ES_LARGO = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                       "agosto", "septiembre", "octubre", "noviembre", "diciembre")

    def _en_prosa(iso):
        """'2025-12-31' → '31 de diciembre de 2025'. El texto es público y el
        resto del informe no usa fechas en formato técnico.

        Un rótulo mensual ('2026-04') se escribe SIN día: la fuente sólo conoce
        el mes, y decir «1 de abril» sería una precisión que el dato no tiene.
        """
        d = _fecha_dato_a_date(iso)
        if d is None:
            return iso
        if len(str(iso)) == 7:      # rótulo mensual, sin día real
            return f"{_MESES_ES_LARGO[d.month - 1]} de {d.year}"
        return f"{d.day} de {_MESES_ES_LARGO[d.month - 1]} de {d.year}"
    bloque["vintages"] = {
        "dias_promedio": round(dias_medio),
        "meses_promedio": meses(dias_medio),
        "fecha_mas_vieja": _en_prosa(mas_viejo["fecha"]),
        "fecha_mas_nueva": _en_prosa(mas_nuevo["fecha"]),
        "span_dias": mas_viejo["dias"] - mas_nuevo["dias"],
        "rezagados": [{"indicador": f["indicador"], "fecha": _en_prosa(f["fecha"]),
                       "meses": meses(f["dias"])} for f in rezagados],
        "titulo": "¿De qué fecha es cada dato del índice?",
        "sub": ("Los componentes no se publican al mismo ritmo: algunos son diarios y "
                "otros llegan con meses de demora. El índice los combina igual en un "
                "puntaje mensual, así que el «mes» del índice es en rigor un mosaico de "
                "datos de distintas fechas. Acá se muestra ese rango."),
        "conclusion": (
            f"El dato más reciente es del {_en_prosa(mas_nuevo['fecha'])} y el más antiguo "
            f"del {_en_prosa(mas_viejo['fecha'])}: un rango de "
            f"{mas_viejo['dias'] - mas_nuevo['dias']} días. "
            f"Ponderando cada componente por el peso que tiene en el índice, la antigüedad "
            f"media del dato es de {coma(meses(dias_medio))} meses."
            + (f" Los que más la arrastran son los que se publican con mayor demora"
               f" o cuya fuente dejó de actualizarse. "
               if rezagados else " Ningún componente supera el trimestre de antigüedad. ")
            + "Conviene tenerlo presente al leer el número del mes: no todos sus "
              "componentes describen el mismo momento."),
    }


def _redundancia_itcm(bloque):
    _redundancia(bloque, "redundancia_itcm")


def _validacion_cruzada(informe):
    """Matriz de validación cruzada (ADR-0031, tercer pilar de robustez): los
    cuatro índices reconstruidos contra los CUATRO contrastes externos a la
    vez. Validez convergente + discriminante: cada índice debe correlacionar
    más fuerte con su par teórico (ITCM ↔ actividad · ITCG ↔ Merval ·
    ITVC ↔ consumo · ITCP ↔ EPU Argentina) que con el contraste ajeno — la prueba
    de que no miden "todo junto". Hoy no se cumple en todos, y la conclusión lo
    declara con el detalle derivado de los números."""
    try:
        bloques = {
            "ITCM": informe["cinturones"]["macro"]["itcm"]["validacion"]["pares"],
            "ITCG": informe["cinturones"]["gestion"]["itcg"]["validacion"]["pares"],
            "ITVC": informe["cinturones"]["vida_cotidiana"]["itvc"]["validacion"]["pares"],
            "ITCP": informe["cinturones"]["politica"]["itcp"]["validacion"]["pares"],
        }
    except (KeyError, TypeError):
        return
    indices = {k: {p[0]: p[1] for p in v} for k, v in bloques.items()}
    # El indicador de mercado que era el ancla de macro YA NO EXISTE en el
    # informe: se reemplazó por el Índice Líder y el reemplazo es total, no una
    # suma — decisión del editor. La matriz es 4×4, un contraste propio por
    # índice.
    externas = {"lider": {p[0]: p[2] for p in bloques["ITCM"]},
                "merval": {p[0]: p[2] for p in bloques["ITCG"]},
                "consumo": {p[0]: p[2] for p in bloques["ITVC"]},
                "epu": {p[0]: p[2] for p in bloques["ITCP"]}}

    def _r(a, b):
        comunes = sorted(set(a) & set(b))
        if len(comunes) < 12:
            return None, len(comunes)
        return (round(statistics.correlation([a[m] for m in comunes],
                                             [b[m] for m in comunes]), 2), len(comunes))

    def _difs(s):
        ms = sorted(s)
        return {ms[i]: s[ms[i]] - s[ms[i - 1]] for i in range(1, len(ms))}

    PAR_PROPIO = {"ITCM": "lider", "ITCG": "merval", "ITVC": "consumo", "ITCP": "epu"}
    filas = []
    for ik in ("ITCM", "ITCG", "ITVC", "ITCP"):
        fila = {"indice": ik, "propio": PAR_PROPIO[ik]}
        for ek, ext in externas.items():
            r, n = _r(indices[ik], ext)
            # rd: correlación de los cambios mes a mes — la prueba exigente,
            # inmune a la tendencia común del período (los niveles pueden
            # inflar una correlación espuria O enmascarar/invertir el signo
            # de un co-movimiento genuino).
            rd, _ = _r(_difs(indices[ik]), _difs(ext))
            fila[ek] = {"r": r, "n": n, "rd": rd}
        filas.append(fila)
    if any(f[e]["r"] is None for f in filas for e in externas):
        return
    fmt = lambda r: ("+" if r > 0 else "") + str(r).replace(".", ",")
    f_itcm, f_itcg, f_itvc, f_itcp = filas

    # El poder discriminante se DERIVA, no se afirma. Antes el texto decía que
    # las celdas cruzadas eran "del mismo orden en más de un caso" con un ejemplo
    # escrito a mano; eso quedó corto cuando el ancla de macro pasó a ser la
    # actividad y su par propio quedó por debajo de dos ajenos. La frase se
    # recalcula en cada corrida para que no pueda sobreafirmar.
    ETIQ = {"lider": "la actividad", "merval": "el Merval",
            "consumo": "el consumo medido", "epu": "la incertidumbre de política"}
    superados = []
    for f in filas:
        propio = abs(f[f["propio"]]["r"])
        ajenas = {k: abs(f[k]["r"]) for k in externas if k != f["propio"]}
        mayor = max(ajenas, key=ajenas.get)
        if ajenas[mayor] > propio:
            superados.append((f["indice"], ETIQ[mayor], f[mayor]["r"], f[f["propio"]]["r"]))
    if superados:
        detalle = "; ".join(f"{ik} correlaciona {fmt(r_aj)} con {lbl} contra {fmt(r_pr)} con su "
                            f"propio par" for ik, lbl, r_aj, r_pr in superados)
        discriminante = (f"La separación es parcial, y se declara: en {len(superados)} de los "
                         f"{len(filas)} índices la correlación más fuerte no es con su par propio "
                         f"({detalle}). En una muestra de unos treinta meses en la que toda la "
                         f"economía y la política se movieron juntas, los contrastes externos "
                         f"comparten buena parte de la tendencia del período, así que el nivel no "
                         f"alcanza para separarlos; los cambios mes a mes que acompañan a cada "
                         f"celda son la lectura más exigente.")
    else:
        discriminante = ("En los cuatro casos la correlación más fuerte es con el par propio, que "
                         "es la prueba de que cada índice mide su terreno y no «todo junto».")
    informe["validacion_cruzada"] = {
        "filas": filas,
        "externas": [["lider", "Actividad (Índice Líder UTDT)"], ["merval", "Merval en USD"],
                     ["consumo", "Consumo en supermercados (precios constantes)"],
                     ["epu", "Incertidumbre de política (EPU Argentina)"]],
        "titulo": "¿Cada índice mide lo suyo?",
        "sub": ("Los cuatro índices se reconstruyen mes a mes y se comparan contra los cuatro "
                "contrastes externos a la vez. Cada uno tiene el propio: la macroeconomía "
                "(ITCM) con la marcha de la actividad, la gestión (ITCG) con el valor de "
                "las empresas en dólares, la vida cotidiana (ITVC) con el consumo medido en "
                "supermercados, la política (ITCP) con la incertidumbre de política que mide la "
                "prensa (EPU Argentina). Si cada índice mide su propio terreno, debería "
                "correlacionar con su par natural al menos tanto como con los ajenos. Es la "
                "prueba clásica de que un indicador no mide \"todo junto\"."),
        # La primera oración es la que va sola en la card (ADR-0165): corta y con
        # el veredicto. El detalle par por par queda para el desarrollo.
        "conclusion": (f"Los cuatro pares propios dan el signo esperado. ITCM "
                       f"{fmt(f_itcm['lider']['r'])} con la actividad, ITCG "
                       f"{fmt(f_itcg['merval']['r'])} con el Merval en dólares, ITVC "
                       f"{fmt(f_itvc['consumo']['r'])} con el consumo medido, ITCP "
                       f"{fmt(f_itcp['epu']['r'])} con la incertidumbre de política — este último "
                       f"más moderado que los otros tres, coherente con un índice con varios "
                       f"componentes recién automatizados y con historia corta. "
                       + discriminante),
    }




def _validacion_itcg(bloque):
    """Anexa al bloque ITCG su validación externa CONTRA SU PAR PROPIO
    (ADR-0031): el Merval en dólares — el mercado de acciones pricea la
    transformación estructural (convergente, positiva esperada). El
    contraste con el ICG UTDT sigue como hallazgo DISCRIMINANTE en la
    conclusión: la ejecución se acumula, la popularidad cicla."""
    val = _cargar_validacion()
    serie = val.get("serie_itcg") or {}
    merval = val.get("merval_usd_mensual") or {}
    comunes = sorted(set(serie) & set(merval))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones_itcg", {})
    niveles = corr.get("niveles (ITCG vs Merval USD)") or {}
    difs = corr.get("primeras diferencias (ITCG vs Merval USD)") or {}
    icg_niv = (corr.get("niveles (ITCG vs ICG)") or {}).get("r")
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    icg_txt = ""
    if icg_niv is not None:
        icg_txt = (f" El contraste discriminante también informa: la confianza en el gobierno "
                   f"(ICG UTDT) diverge del ITCG ({coma(icg_niv)}) — la ejecución se acumula "
                   f"mientras el capital político sigue su propio ciclo. El índice mide "
                   f"gestión, no popularidad.")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], merval[m]] for m in comunes],
        "plot": "minmax",
        "titulo": "¿La transformación se pricea en el valor de las empresas?",
        "sub": ("El contraste natural del cinturón de gestión es el capital de riesgo: si la "
                "agenda de reformas efectivamente se ejecuta, las empresas argentinas deberían "
                "valer más en dólares. El ITCG se reconstruye mes a mes desde las series de sus "
                "componentes (sin los ajustes del analista: el nivel puede diferir del publicado "
                "— lo que valida es su evolución) y se compara con el índice Merval medido en "
                "dólares (cierre mensual sobre el contado con liquidación), que no integra el "
                "índice. El Merval es una de las cuatro estadísticas del terreno propio de este "
                "cinturón —las otras tres miden cuánto capital de afuera decide entrar: "
                "inversión directa, inversión de cartera y financiamiento a empresas— y el "
                "gráfico compara el índice contra el factor común de las cuatro. El detalle "
                "está en la ficha metodológica."),
        "serie_label": "ITCG (reconstrucción mensual)",
        "externa_label": "Merval en dólares",
        "trans_label": "series normalizadas al rango del período",
        "conclusion": (f"Contra el Merval solo —una de las cuatro— la correlación es "
                       f"{coma(r_niv)} en niveles: cuando la ejecución de reformas "
                       f"avanza, el mercado revaloriza a las empresas argentinas.{icg_txt}"),
    }


def _validacion_itcp(bloque):
    """Anexa al bloque ITCP su validación externa: la serie mensual del índice
    (reconstruida por el estudio desde las series de componentes) contra el
    EPU de Argentina (Economic Policy Uncertainty, minería de texto de prensa
    local — Banco de España + SECMCA, misma familia metodológica que
    Baker/Bloom/Davis) — correlación negativa esperada. No es un precio de
    mercado como los otros tres pares: es la lectura pública de la política
    misma, ajena a los once componentes del índice."""
    val = _cargar_validacion()
    serie = val.get("serie_itcp") or {}
    epu = val.get("epu_argentina_mensual") or {}
    comunes = sorted(set(serie) & set(epu))
    if len(comunes) < 12:
        return
    corr = val.get("correlaciones_itcp", {})
    niveles = corr.get("niveles (ITCP vs EPU Argentina)") or {}
    # Contrafáctico: cuánto valdría la correlación sin la dimensión empresaria,
    # que es la más nueva y la que este contraste no cubre. Se publica.
    r_sin_priv = (corr.get("niveles, sin la dimensión de sector privado") or {}).get("r")
    difs = corr.get("primeras diferencias (ITCP vs EPU)") or {}
    r_niv, r_dif = niveles.get("r"), difs.get("r")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], epu[m]] for m in comunes],
        "plot": "minmax_inv",
        "titulo": "¿El capital político se refleja en menos incertidumbre de política percibida?",
        "sub": ("El contraste natural del cinturón político no es un precio de mercado sino la "
                "lectura pública de la política misma: el EPU (Economic Policy Uncertainty) de "
                "Argentina mide, con minería de texto sobre diarios locales (Banco de España y "
                "SECMCA, la misma familia metodológica que el índice de Baker/Bloom/Davis), "
                "cuánto se habla de incertidumbre alrededor del gobierno y sus políticas. El "
                "ITCP se reconstruye mes a mes desde las series de sus componentes (sin los "
                "ajustes del analista: el nivel puede diferir del publicado — lo que valida es "
                "su evolución); varios de los once componentes tienen historia corta o recién "
                "se automatizaron en julio de 2026 (cohesión del bloque oficialista, alineamiento "
                "de senadores por provincia, adhesión provincial al RIGI), así que la reconstrucción de los "
                "meses más antiguos se apoya sobre todo en poder legislativo, el votómetro y la "
                "protesta social — límite que se declara, no se esconde."),
        "serie_label": "ITCP (reconstrucción mensual)",
        "externa_label": "EPU Argentina (incertidumbre de política, invertido)",
        "trans_label": "series normalizadas al rango del período; el EPU se muestra invertido",
        "r_sin_sector_privado": r_sin_priv,
        "por_gobierno": val.get("brecha_obra_publica_por_gobierno") or {},
        "conclusion": (
            f"Contra el EPU solo —una de las tres— la correlación es {coma(r_niv)} en niveles y "
            f"{coma(r_dif)} en los cambios mes a mes: el signo negativo es el esperado, más "
            f"moderado que en macro o gestión."
            + (f" Sin la dimensión de sector privado —incorporada en julio de 2026— la "
               f"correlación sería {coma(r_sin_priv)}, y conviene explicar la diferencia en "
               f"lugar de omitirla. "
               if r_sin_priv is not None else " ")
            + "El contraste mide incertidumbre de política económica en la prensa, y no cubre "
              "la relación del Gobierno con los empresarios: pedirle que valide una dimensión "
              "que no abarca es pedirle lo que no mide. Esa dimensión tiene su propio contraste, "
              "el volumen de insumos de construcción efectivamente vendidos, contra el que "
              "correlaciona 0,79 en niveles y 0,47 en los cambios."
            + (" Hay además un hallazgo que conviene declarar: el indicador de expectativas de "
               "obra pública acompaña a la incertidumbre de política durante las dos "
               "administraciones anteriores y se invierte con la actual. La razón es "
               "sustantiva, no estadística: para gobiernos anteriores la tensión con las "
               "empresas que dependen del Estado era un síntoma de dificultades, mientras que "
               "para el actual el recorte de la obra pública es el programa de gobierno, de "
               "modo que ejecutarlo reduce la incertidumbre sobre la política económica al "
               "mismo tiempo que tensa la relación con ese sector. El indicador mide bien la "
               "tensión; lo que no distingue es cuándo esa tensión es un costo que el Gobierno "
               "sufre y cuándo es un precio que decide pagar."
               if val.get("brecha_obra_publica_por_gobierno") else "")),
    }


def _scoring_vida_itvc(c, series):
    """Vida cotidiana se puntúa con el ITVC-B100: cada componente es un índice
    rebaseado a 100 = promedio 4T-2023, agregado con los pesos del doc 260702.
    La tensión del cinturón y el aporte por indicador usan el mapeo lineal
    5 − (índice − 100) × 0,2 (topeado a 0-10)."""
    from datetime import datetime as _dt
    indices = _itvc_indices(c["indicadores"], series)
    winsorizados = indices.pop("_winsor", {})
    ajustes = itvc.cargar_ajustes(AJUSTES_ITVC_PATH, _dt.now().strftime("%Y-%m"))
    resultado = itvc.calcular_itvc(indices, ajustes)
    c["itvc"] = resultado
    if resultado:
        c["score"] = itvc.tension_de_itvc(resultado["valor"])
        c["estado"] = _estado(c["score"])
        try:
            resultado["robustez"] = sensibilidad.robustez_compacta(
                resultado, None, itvc.tension_de_itvc)
        except Exception as e:
            print(f"[WARN] robustez ITVC: {e}")
        _marcar_dimensiones_criticas(resultado, UMBRAL_CRITICO_BASE100)
        _validacion_itvc(resultado, series)

    ajustados = {a["indicador"]: a for a in (resultado or {}).get("ajustes_aplicados", [])}
    por_ind = {}
    if resultado:
        for dkey, dim in resultado["dimensiones"].items():
            for ikey, info in dim["indicadores"].items():
                por_ind[ikey] = (dkey, info)
    en_itvc = {k for d in itvc.DIMENSIONES_ITVC.values() for k in d["indicadores"]}
    for ikey, ind in c["indicadores"].items():
        aporte = formula = nota = lectura = None
        if ikey in por_ind:
            dkey, info = por_ind[ikey]
            ind["en_indice"] = True
            ind["dimension"] = dkey
            ind["indice_itvc"] = info["puntaje_aplicado"]
            ind["peso_efectivo"] = info["peso_efectivo"]
            aporte = itvc.tension_de_itvc(info["puntaje_aplicado"])
            # tensión SIN topear: el 0 de un componente en mejora fuerte no es
            # "no incide" — es tensión negativa cortada por la escala, y hay
            # que decirlo (varios componentes distintos mostraban el mismo 0)
            cruda = round(5 - (info["puntaje_aplicado"] - 100) * 0.2, 1)
            if cruda < 0:
                lectura = (f"Este componente está en {coma(info['puntaje_aplicado'])} contra una "
                           f"base de 100: su tensión equivalente daría negativa "
                           f"({coma(cruda)}) y la escala se corta en 0. No solo no suma "
                           f"tensión — empuja el índice del cinturón hacia arriba. Por eso "
                           f"más de un componente en mejora fuerte puede mostrar el mismo 0.")
            elif cruda > 10:
                lectura = (f"La tensión equivalente excede el tope de la escala "
                           f"({coma(cruda)}) y se corta en 10: deterioro profundo contra el "
                           f"arranque del mandato.")
            else:
                lectura = (f"En la escala del cinturón, este componente equivale a una "
                           f"tensión de {coma(aporte)}/10.")
            # bases DECLARADAS distintas del 4T-2023 (fuente sin medición en la base del doc)
            base_lbl = {"inseguridad": "ene-2024 (base declarada: la encuesta se reanudó ese mes)"} \
                .get(ikey, "4T-2023")
            formula = (f"Índice base-100 vs {base_lbl}: {coma(info['puntaje_aplicado'])} "
                       f"(100 = arranque del mandato; más = mejora); pesa "
                       f"{coma(round(info['peso_efectivo'] * 100, 1))}% del ITVC. "
                       f"Tensión = 5 − (índice − 100) × 0,2.")
            if ikey in winsorizados:
                nota = (f"Winsorizado (tratamiento de outliers): índice crudo "
                        f"{coma(winsorizados[ikey])} acotado al techo de {coma(ITVC_WINSOR_TOPE)} "
                        f"— un boom puntual de un componente no compra compensación "
                        f"ilimitada en el promedio. El tope es solo hacia arriba: las "
                        f"caídas no se recortan, se señalizan como dimensión crítica.")
            if ikey in ajustados:
                aj = ajustados[ikey]
                nota = f"Ajuste del analista: índice {coma(aj['de'])} → {coma(aj['a'])}. {aj.get('justificacion', '')}"
        else:
            ind["en_indice"] = ikey in en_itvc     # del índice pero sin dato
            if ikey in itvc.INDICADORES_CONTEXTO:
                ind["en_indice"] = False
            if ind["en_indice"] is False:
                nota = VIDA_CONTEXTO
        ind["aporte_score"] = aporte
        ind["aporte_formula"] = formula
        ind["aporte_nota"] = nota
        ind["aporte_lectura"] = lectura


# Indicadores macro OCULTOS del snapshot (ADR-0022): siguen en la pipeline
# (colector, cache y series — son insumos del IdC/IDM/TCRM y del crédito
# real), pero no se publican como tiles: su única señal no redundante entra
# al índice vía credito_privado.
MACRO_OCULTOS = {"badlar", "prestamos_privados", "base_monetaria", "tc_mayorista"}

# Indicadores de política OCULTOS del snapshot (ADR-0048, mismo criterio que
# ADR-0022): la revisión editorial los sacó del ITCP y el tablero solo
# muestra lo que integra las dimensiones. Siguen en la pipeline completa
# (colector, registro curado, cache y series) como seguimiento interno.
POLITICA_OCULTOS = set(itcp.INDICADORES_CONTEXTO)

# Indicadores de espíritu de época OCULTOS del snapshot (ADR-0049, mismo
# criterio): el cinturón queda con la intención migratoria como único
# puntuable; estos tres son lecturas duplicadas de cards que ya viven en
# vida cotidiana (icc_utdt, sentimiento_digital) y política (clima_electoral
# = votometro_ventaja_lla). El colector los sigue cacheando como seguimiento
# interno.
ESPIRITU_OCULTOS = {"icc_utdt", "sentimiento_digital", "clima_electoral"}

# Indicadores de gestión OCULTOS del snapshot (ADR-0051, cierra la regla de
# ADR-0048/0049 sobre el último cinturón que publicaba contexto visible): el
# tablero solo muestra lo que integra las dimensiones del ITCG. Colector,
# stores y series siguen corriendo como seguimiento interno (razones de no
# puntuar documentadas en itcg.INDICADORES_CONTEXTO).
GESTION_OCULTOS = set(itcg.INDICADORES_CONTEXTO)

# Indicadores de vida cotidiana OCULTOS del snapshot (ADR-0154, mismo criterio
# que ADR-0022): la revisión editorial los sacó del ITVC y el tablero solo
# muestra lo que integra las dimensiones. Series y colector siguen corriendo —
# `indice_lider` además pasó a ser el validador externo del ITCM, así que su
# serie es un insumo vivo de validacion_externa.py.
#
# Es el quinto cinturón en tener lista de ocultos, y con eso los cinco usan el
# mismo patrón: entra al índice o se oculta. No hay cards de contexto (ADR-0153).
VIDA_OCULTOS = {"endeudamiento_familiar", "indice_lider"}


# ── Semáforo de 4 colores (ADR-0181) ──────────────────────────────────────────
# Capa de LECTURA: no toca ningún puntaje, peso ni índice. El color sale de la
# tensión sin redondear — `aporte_score` está redondeado y usarlo rompe el borde
# (ver test_no_usa_la_tension_redondeada en test_semaforo.py). Por eso cada
# rama recalcula la tensión desde el dato más crudo disponible: el puntaje
# 0-100 del indicador (no su `aporte_score`) para ITCM/ITCG/ITCP, el
# `indice_itvc` base-100 para vida cotidiana, y solo para espíritu de época
# —donde no hay otro dato— el propio `aporte_score`.
_ESCALAS_SEMAFORO = {
    "macro": ("itcm", itcm, "ITCM"),
    "gestion": ("itcg", itcg, "ITCG"),
    "politica": ("itcp", itcp, "ITCP"),
}

# Bloque de índice que cuelga de cada cinturón, y si es base-100 (ITVC) o
# puntaje 0-100 por bandas (ITCM/ITCG/ITCP) — determina qué fórmula de color
# corresponde al índice y a sus dimensiones.
_INDICE_DE_CINTURON = {"macro": "itcm", "gestion": "itcg", "politica": "itcp",
                       "vida_cotidiana": "itvc"}


def _escala_de(mod, sigla):
    return parametrica.Escala(
        getattr(mod, f"BANDAS_{sigla}"),
        getattr(mod, f"ANCLAS_{sigla}", None),
        getattr(mod, f"TRANSFORMACIONES_{sigla}", None),
    )


def _por_que(color, valor, unidad, tramos):
    """Una frase que explica el color con la misma aritmética que lo produjo.

    Se genera y no se escribe: es lo que evita que la prosa de la ficha se
    desincronice del dato (ADR-0182). Membresía de tramo low-exclusivo /
    high-inclusivo, la misma convención del motor (parametrica.puntaje_banda).
    """
    if valor is None or not tramos:
        return None
    actual = next((t for t in tramos
                   if (t["desde"] is None or valor > t["desde"])
                   and (t["hasta"] is None or valor <= t["hasta"])), None)
    if actual is None:
        return None
    borde = actual["desde"] if actual["desde"] is not None else actual["hasta"]
    if borde is None:
        return f"{coma(valor)} {unidad}: {color.capitalize()} en todo el rango."
    return (f"{coma(valor)} {unidad} cae en el tramo que corresponde a "
            f"{color.capitalize()}, a {coma(round(abs(valor - borde), 2))} "
            f"del corte más cercano.")


def _semaforo_de(color, tension, umbrales, unidad, valor):
    return {"color": color,
            "tension": None if tension is None else round(tension, 1),
            "umbrales": umbrales,
            "unidad": unidad,
            "por_que": _por_que(color, valor, unidad, umbrales)}


def _semaforos(informe):
    """Adjunta el bloque `semaforo` a cada indicador, dimensión e índice."""
    for cinturon, bloque in informe["cinturones"].items():
        clave, mod, sigla = _ESCALAS_SEMAFORO.get(cinturon, (None, None, None))
        escala = _escala_de(mod, sigla) if mod else None

        for ikey, ind in bloque["indicadores"].items():
            idx100 = ind.get("indice_itvc")
            p = ind.get(f"puntaje_{clave}") if clave else None
            if isinstance(p, (int, float)) and ind.get("en_indice"):
                tension = (100.0 - float(p)) / 10.0
                color = parametrica.color_de_puntaje(float(p))
                umbrales = parametrica.umbrales_en_unidad(ikey, escala)
                unidad = ind.get("unidad")
            elif isinstance(idx100, (int, float)):
                tension = 5.0 - (float(idx100) - 100.0) * 0.2
                color = parametrica.color_de_indice_base100(float(idx100))
                umbrales, unidad = None, None
            elif ind.get("aporte_score") is not None:
                tension = float(ind["aporte_score"])
                color = parametrica.color_de_tension(tension)
                umbrales, unidad = None, None
            else:
                continue
            ind["semaforo"] = _semaforo_de(color, tension, umbrales, unidad,
                                           ind.get("valor"))

        indice_key = _INDICE_DE_CINTURON.get(cinturon)
        if not indice_key:
            continue
        indice = bloque.get(indice_key)
        if not indice:
            continue
        color_idx = (parametrica.color_de_indice_base100 if indice_key == "itvc"
                     else parametrica.color_de_puntaje)
        indice["semaforo"] = {"color": color_idx(indice["valor"]),
                              "umbrales": None, "unidad": None, "por_que": None,
                              "tension": None}
        for dim in indice.get("dimensiones", {}).values():
            dim["semaforo"] = {"color": color_idx(dim["puntaje"]),
                               "umbrales": None, "unidad": None,
                               "por_que": None, "tension": None}


def aplicar_scoring(informe, series):
    """Anota cada indicador con su aporte de tensión (0–10) y el mapeo que lo
    explica, y cada cinturón con cómo se compone su score."""
    for ckey, c in informe["cinturones"].items():
        c["score_explicacion"] = SCORE_EXPLICACION.get(ckey, "")
        if ckey == "macro":
            for oculto in MACRO_OCULTOS:
                c["indicadores"].pop(oculto, None)
            _scoring_indice(c, "itcm", itcm, MACRO_CONTEXTO, _macro_input_txt)
            if c.get("itcm"):
                _validacion_itcm(c["itcm"])
                _redundancia_itcm(c["itcm"])
                _linea_base(c["itcm"])
                _vintages(c, "itcm")
            continue
        if ckey == "gestion":
            for oculto in GESTION_OCULTOS:
                c["indicadores"].pop(oculto, None)
            _scoring_indice(c, "itcg", itcg, GESTION_CONTEXTO, _gestion_input_txt)
            if c.get("itcg"):
                _validacion_itcg(c["itcg"])
                _panel_socioeconomico(c["itcg"], "itcg")
                _redundancia(c["itcg"], "redundancia_itcg")
                _vintages(c, "itcg")
            continue
        if ckey == "vida_cotidiana":
            for oculto in VIDA_OCULTOS:
                c["indicadores"].pop(oculto, None)
            _scoring_vida_itvc(c, series)
            # Responde la pregunta explícita de la auditoría sobre si
            # patentamiento_motos aporta señal propia frente al ICC (ADR-0108).
            _panel_socioeconomico(c["itvc"], "itvc")
            _redundancia(c["itvc"], "redundancia_itvc")
            _dispersion_itvc(c["itvc"])
            # El ITVC es el cinturón con más dispersión de vintages de los
            # cuatro: la EPH es trimestral y sostiene dos componentes, uno de
            # ellos en la dimensión de mayor peso. Prioridad alta de la
            # auditoría de vida cotidiana (punto 3.2).
            _vintages(c, "itvc")
            continue
        if ckey == "politica":
            for oculto in POLITICA_OCULTOS:
                c["indicadores"].pop(oculto, None)
            _scoring_indice(c, "itcp", itcp, POLITICA_CONTEXTO, _politica_input_txt)
            if c.get("itcp"):
                _validacion_itcp(c["itcp"])
                _panel_socioeconomico(c["itcp"], "itcp")
                _redundancia(c["itcp"], "redundancia_itcp")
                _rezago(c["itcp"], itcp.REZAGO_MESES_ITCP,
                        itcp.REZAGO_PULSO, itcp.REZAGO_ESTRUCTURAL)
                _familias(c["itcp"], itcp.FAMILIAS_ITCP, itcp.FAMILIAS_ITCP_META)
                _vintages(c, "itcp")
            continue
        if ckey == "espiritu_epoca":
            # sin continue: el puntuable que queda (intención migratoria)
            # se anota abajo con el loop genérico de SCORING
            for oculto in ESPIRITU_OCULTOS:
                c["indicadores"].pop(oculto, None)
        for ikey, ind in c["indicadores"].items():
            aporte = formula = nota = lectura = None
            if ikey in SCORING:
                spec = SCORING[ikey]
                fn, mapa = spec[0], spec[1]
                campo = spec[2] if len(spec) > 2 else "valor"   # input alternativo
                entrada = ind.get(campo)
                if isinstance(entrada, (int, float)):
                    aporte = _clamp10(fn(float(entrada)))
                    formula = mapa
                    # acá el score del cinturón SÍ es el promedio de estas tensiones
                    cm = lambda x: str(x).replace(".", ",")
                    lectura = (f"Entra al promedio del cinturón con una tensión de "
                               f"{cm(aporte)}/10." +
                               (" Hoy no registra tensión." if aporte == 0 else ""))
                    if campo == "var_real_12m":                  # mostrar el input real, no el stock
                        ind["aporte_input_txt"] = f"{entrada:+.1f}% interanual real (no el stock nominal)".replace(".", ",")
                elif ckey == "vida_cotidiana":
                    nota = VIDA_CONTEXTO                          # input ausente → contexto
            elif ckey == "vida_cotidiana":
                nota = VIDA_CONTEXTO
            ind["aporte_score"] = aporte
            ind["aporte_formula"] = formula
            ind["aporte_nota"] = nota
            ind["aporte_lectura"] = lectura
    _semaforos(informe)
    return informe


def _val_en(serie, objetivo_ym):
    """Último valor de `serie` (lista {fecha, valor}) con mes <= objetivo (YYYY-MM)."""
    cand = [d for d in serie if d["fecha"][:7] <= objetivo_ym]
    return cand[-1]["valor"] if cand else (serie[0]["valor"] if serie else None)


def var_real_credito_12m(cc_serie, ipc_serie):
    """Variación interanual REAL del crédito de consumo, deflactada por IPC.
    Ancla al último mes de IPC disponible para comparar exactamente el mismo
    período en ambas series. Devuelve % real o None si faltan datos."""
    if not cc_serie or not ipc_serie:
        return None
    anchor = ipc_serie[-1]["fecha"][:7]                  # ej '2026-03'
    prev = f"{int(anchor[:4]) - 1}{anchor[4:]}"          # mismo mes, año previo
    cc_now, cc_old = _val_en(cc_serie, anchor), _val_en(cc_serie, prev)
    ipc_now, ipc_old = ipc_serie[-1]["valor"], _val_en(ipc_serie, prev)
    if not all(isinstance(x, (int, float)) and x for x in (cc_now, cc_old, ipc_now, ipc_old)):
        return None
    return round(((cc_now / cc_old) / (ipc_now / ipc_old) - 1) * 100, 1)


def _carry_forward(enriquecido, previo):
    """Si una fuente falla y un indicador de vida viene sin valor (None), mantener
    el último dato publicado en lugar de perderlo. Evita que un outage puntual
    (ej. SNIC, cuyo dato es anual y sin novedad) haga caer el indicador del score.
    `previo` = indicadores de vida del snapshot publicado anterior."""
    for key, ind in enriquecido.items():
        if ind.get("valor") is None and key in previo and previo[key].get("valor") is not None:
            prev = previo[key]
            ind["valor"] = prev.get("valor")
            ind["fecha_dato"] = prev.get("fecha_dato")
            if prev.get("fuente"):
                ind["fuente"] = prev["fuente"]
            print(f"[carry-forward] vida.{key}: sin dato nuevo, se mantiene {prev.get('valor')} ({prev.get('fecha_dato')})")
    return enriquecido


def main():
    informe = json.loads((OUT / "informe.json").read_text(encoding="utf-8"))
    series = build_series()

    # Snapshot publicado anterior → fuente para carry-forward ante outages.
    prev_vida = {}
    prev_path = DATA / "informe.json"
    if prev_path.exists():
        try:
            prev_snap = json.loads(prev_path.read_text(encoding="utf-8"))
            prev_vida = prev_snap["cinturones"]["vida_cotidiana"]["indicadores"]
        except (json.JSONDecodeError, KeyError):
            prev_vida = {}

    vida_files = sorted(glob.glob(str(ROOT / "scripts" / "vida_cotidiana" / "data" / "vida_cotidiana_*.json")))
    if vida_files:
        raw = json.loads(Path(vida_files[-1]).read_text(encoding="utf-8"))
        enriquecido = build_vida(raw)
        if enriquecido:
            enriquecido = _carry_forward(enriquecido, prev_vida)
            vida = informe["cinturones"]["vida_cotidiana"]
            vida["indicadores"] = enriquecido
            vida["fuente_enriquecida"] = os.path.basename(vida_files[-1])
            # Endeudamiento: scoreable vía variación interanual real del crédito.
            real = var_real_credito_12m(
                raw.get("bcra", {}).get("credito_consumo_serie"), series.get("ipc_nivel"))
            if real is not None and "endeudamiento_familiar" in enriquecido:
                enriquecido["endeudamiento_familiar"]["var_real_12m"] = real
            # Mora de las familias (ADR-0067): sin colector propio — la card
            # se sintetiza desde la serie del anexo del Informe sobre Bancos
            # (el titular ES el último punto, invariante serie-titular por
            # construcción). Mismo patrón que la card de inseguridad (IVI).
            serie_mora = series.get("mora_familias") or []
            if serie_mora:
                ult_mora = serie_mora[-1]
                _add(enriquecido, "mora_familias", ult_mora["valor"],
                     "% de la cartera en situación irregular",
                     "BCRA — Informe sobre Bancos (personales + tarjetas de familias)",
                     ult_mora["fecha"][:7],
                     detalle_txt=("Porcentaje del crédito de consumo de las familias "
                                  "(préstamos personales y tarjetas) con atrasos de pago, "
                                  "ponderado por el saldo de cada línea."))
            # Inseguridad: la card muestra el IVI mensual (LICIP-UTDT), la
            # métrica del ITVC desde el ADR-0032. El SNIC anual (denuncias
            # registradas) queda como contraste declarado en el detalle.
            ivi = series.get("inseguridad") or []
            if ivi and enriquecido.get("inseguridad"):
                ins = enriquecido["inseguridad"]
                snic_txt = ""
                v_snic = ins.get("valor")
                if isinstance(v_snic, (int, float)) and v_snic > 10000:
                    snic_txt = (f" — contraste SNIC (denuncias registradas, año "
                                f"{ins.get('fecha_dato')}): "
                                f"{format(int(v_snic), ',').replace(',', '.')} hechos")
                ult = ivi[-1]
                ins.update({
                    "valor": ult["valor"],
                    "unidad": "% de hogares víctimas (últimos 12 meses)",
                    "fuente": "UTDT — Índice de Victimización (LICIP)",
                    "fecha_dato": ult["fecha"][:7],
                    "detalle_txt": ("Encuesta mensual de victimización en 40 centros urbanos: "
                                    "incluye los delitos NO denunciados (la cifra negra)"
                                    + snic_txt),
                })

    informe = sanitizar_fuentes(informe)
    informe = aplicar_scoring(informe, series)
    informe = recomputar_vida_y_global(informe)
    _validacion_cruzada(informe)   # matriz discriminante (ADR-0031): necesita los 3 bloques

    # Red de seguridad: persistir el valor de cada indicador y construir su serie
    # histórica mes a mes (los que no tienen serie oficial la arman así).
    store = acumular_historico(informe)
    series = fusionar_historico(series, store)

    # Resumen de card para toda sección con conclusión (ADR-0165). Va acá, al
    # final y de una sola pasada, en vez de en cada constructor: una sección
    # nueva queda cubierta sin que nadie tenga que acordarse. No recorta la
    # conclusión — la deja intacta para el modal y el desplegable.
    import resumir
    resumir.anotar(informe)

    (DATA / "informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "series.json").write_text(
        json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Snapshot escrito en {DATA} · histórico: {len(store)} indicadores en {HISTORICO_PATH.name}")


if __name__ == "__main__":
    main()
