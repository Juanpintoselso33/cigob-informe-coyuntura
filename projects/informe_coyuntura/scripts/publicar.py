"""Arma el snapshot de datos que consume la web del informe de coyuntura.

Lee output/informe.json + el ultimo vida_cotidiana_*.json + output/series/*.csv
y escribe web/src/data/informe.json (con vida cotidiana enriquecido con los
indicadores automáticos vigentes) y web/src/data/series.json.
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
from config import (PESOS_CINTURONES, UMBRALES, SIGLAS_PUBLICAS,  # pesos, umbrales y siglas
                    estado_de_score, nombre_publico)
import itcm                                           # bandas y pesos del ITCM macro
import itcg                                           # bandas y pesos del ITCG gestión
import itcp                                           # bandas y pesos del ITCP política
import itvc                                           # pesos y rebase del ITVC vida cotidiana
import series_io                                     # lectura de output/series/*.csv
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


def _red(valor, dec, factor=1):
    """Redondea, **conservando el None**. Es el punto entero de la función.

    El patrón que reemplaza era `round(x.get("valor", 0), 2)`: con la fuente
    caída publicaba **0**, y un cero no es un dato faltante — es un dato. Peor
    que la ausencia: `_carry_forward` sólo repara los `None`, así que el cero
    pasaba de largo y se publicaba como si el organismo lo hubiera informado.
    Con el INDEC caído, la inflación de alimentos habría salido 0,00% m/m.
    Descubierto el 25-ago-2026 al escribir
    `tests/test_una_fuente_caida_degrada_no_desaparece.py`.
    """
    if valor is None:
        return None
    return round(valor * factor, dec)


def _add(out, key, valor, unidad, fuente, fecha, **extra):
    d = {"valor": valor, "unidad": unidad, "fuente": fuente,
         "fecha_dato": fecha, "desactualizado": False}
    d.update(extra)
    out[key] = d


def agregar_carga_servicio_deuda(enriquecido, series):
    serie = series.get("carga_servicio_deuda_hogares") or []
    if not serie:
        return
    ultimo = serie[-1]
    _add(enriquecido, "carga_servicio_deuda_hogares",
         ultimo["valor"], "% de la masa salarial registrada",
         "BCRA — Informe de Estabilidad Financiera (carga de la deuda sobre la masa salarial)",
         ultimo["fecha"][:7],
         detalle_txt=("Cuotas de capital e intereses de las familias como "
                      "porcentaje de la masa salarial registrada; el BCRA "
                      "promedia tres meses tanto en el numerador como en el "
                      "denominador. Más carga implica menor capacidad de pago."))


def build_vida(raw):
    """Mapea el JSON crudo (por fuente) a indicadores estilo informe.json."""
    indec = raw.get("indec", {}); bcra = raw.get("bcra", {})
    utdt = raw.get("utdt", {})
    ciccra = raw.get("ciccra", {}); snic = raw.get("snic", {})
    trends = raw.get("trends", {})
    out = {}

    bs = indec.get("brecha_salario_cbt", {})
    _add(out, "brecha_salario_cbt", _red(bs.get("valor"), 2),
         "canastas (RIPTE/CBT)", "Sec. Trabajo (RIPTE) + INDEC (CBT)", bs.get("fecha"),
         detalle_txt=bs.get("nota"))
    al = indec.get("ipc_alimentos", {})
    _add(out, "ipc_alimentos", _red(al.get("variacion_mensual_pct"), 2),
         "% m/m", "INDEC — IPC alimentos y bebidas (vía datos.gob.ar)", al.get("fecha"))
    cc = bcra.get("credito_consumo_total", {})
    # El crédito de consumo viene en millones de pesos; pasar a billones para
    # que el número no sea gigante (43.560.544 millones = 43,56 billones).
    cc_val = cc.get("valor")
    _add(out, "endeudamiento_familiar",
         round(cc_val / 1e6, 2) if isinstance(cc_val, (int, float)) else cc_val,
         "billones de pesos (consumo)",
         "BCRA — crédito de consumo (API) + Informe sobre Bancos", cc.get("fecha"))
    servicios = raw.get("iiep_tarifas") or {}
    valor_servicios = servicios.get("valor")
    # La clave debe existir aun durante un outage: _carry_forward sólo puede
    # restaurar indicadores presentes. Omitirla dejaba la serie puntuando sin
    # card visible, exactamente el estado que ADR-0153 prohíbe.
    _add(
        out, "peso_tarifas",
        round(valor_servicios, 1) if isinstance(valor_servicios, (int, float)) else None,
        "% del salario RIPTE",
        "IIEP UBA-CONICET — Canasta de Servicios Públicos del AMBA",
        servicios.get("fecha"),
        variacion_mensual_pct=servicios.get("variacion_mensual_pct"),
        cobertura_costos_pct=servicios.get("cobertura_costos_pct"),
        transporte_pct_canasta=servicios.get("transporte_pct_canasta"),
        fuente_url=servicios.get("url"),
    )
    alq = indec.get("ipc_alquiler_gba", {})
    _add(out, "alquiler_real", _red(alq.get("variacion_mensual_pct"), 2),
         "% m/m alquileres", "INDEC — IPC-GBA alquiler de la vivienda (planilla original)",
         alq.get("fecha"), fuente_url=alq.get('fuente_url'))
    # ADR-0322: la vacuna y el resto (aviar+porcina) puntúan cada uno por su
    # cuenta — antes (ADR-0217) sólo el total puntuaba y la vacuna era
    # diagnóstico puro. Los DOS salen del MISMO PDF de SAGYP: misma
    # metodología de promedio móvil 12m, mismo corte temporal y mismo
    # perímetro. CICCRA queda como respaldo de la vacuna si el tablero no
    # trae el mes — el resto no tiene respaldo alternativo, así que si SAGYP
    # no trajo el mes esa card queda en None (la repara `_carry_forward`).
    #
    # Se llaman SIEMPRE, aunque SAGYP no haya traído el mes, por el mismo
    # motivo que la motorización, sentimiento_digital y el supermercado: una
    # clave AUSENTE es invisible para `_carry_forward`, que sólo repara las
    # que ya están en None. Pasó de verdad el 25-ago-2026 —el colector
    # devolvió `consumo_carnes: None` y el snapshot salió con 62 cards en vez
    # de 63—, y `gate_calidad.py` lo dejó pasar porque mira estructura,
    # frescura y card-contra-serie, no invariantes de conteo.
    carnes = raw.get("consumo_carnes") or {}
    carne = ciccra.get("consumo_carne_per_capita", {})
    if carnes.get("vacuna") is not None:
        _add(out, "consumo_carne_vacuna", carnes["vacuna"],
             "kg/hab/año", "SAGYP — tablero consumo per cápita de carnes (promedio móvil 12m)",
             f"{carnes['mes']}-01")
    else:
        _add(out, "consumo_carne_vacuna", carne.get("valor"),
             "kg/hab/año", "CICCRA", carne.get("fecha"))
    # ADR-0339: puntúan el TOTAL de las tres carnes y la vacuna sola
    # (aspiracional). Aviar + porcina deja de ser card: su nivel viaja colgado
    # del total, que es donde se lee la composición.
    _add(out, "consumo_carnes_total", carnes.get("total"),
         "kg/hab/año",
         "SAGYP — tablero consumo per cápita de carnes (vacuna + aviar + porcina, promedio móvil 12m)",
         f"{carnes['mes']}-01" if carnes.get("mes") else None)
    otras = None
    if carnes.get("aviar") is not None and carnes.get("porcina") is not None:
        otras = round(carnes["aviar"] + carnes["porcina"], 2)
    # Las variaciones i.a. las publica la misma fuente y las consume la matriz
    # que arma `_por_que_carne`. Viajan COLGADAS de los dos indicadores, como
    # ya hacen `componentes` en el IAI o `regimen` en otros: meterlas como
    # clave suelta del dict las convertiría en un indicador fantasma.
    variaciones = carnes.get("variaciones") or {}
    out["consumo_carne_vacuna"]["variaciones"] = variaciones
    out["consumo_carnes_total"]["variaciones"] = variaciones
    out["consumo_carnes_total"]["otras_kg"] = otras
    out["consumo_carnes_total"]["ratio_bovina"] = carnes.get("ratio_bovina")
    inf = indec.get("informalidad_trimestral") or indec.get("informalidad_anual", {})
    _add(out, "informalidad", _red(inf.get("valor"), 1, 100),
         "%", "INDEC EPH", inf.get("fecha"))
    # ADR-0218: el indicador pasa a medir lo que su nombre promete — el cierre
    # neto de PyMEs — con la base de empleadores con cobertura de ART de la SRT.
    # Antes publicaba la variación mensual del IPI manufacturero.
    ind_ = raw.get("trabajo_independiente") or {}
    # ADR-0250: el universo es restringido y el rótulo lo dice. Antes decía
    # «% del empleo registrado» mientras dejaba el monotributo social afuera de
    # los dos lados del cociente.
    #
    # Se agrega SIEMPRE, con `valor: None` si SIPA no contestó: una clave
    # ausente es invisible para `_carry_forward` y el indicador desaparecería
    # de la web en vez de quedar marcado como desactualizado. El detalle sí va
    # adentro del `if`, porque se arma con cinco campos del propio dato.
    _add(out, "trabajo_independiente", ind_.get("participacion"),
         "% del empleo registrado SIPA, sin monotributo social",
         "SIPA — autónomos y monotributo general sobre el empleo registrado total (asalariados privados, públicos y casas particulares)",
         f"{ind_['mes']}-01" if ind_.get("mes") else None)
    if ind_.get("participacion") is not None:
        card = out["trabajo_independiente"]
        for k in ("categorias_numerador", "categorias_denominador",
                  "excluido", "excluido_quiebre", "participacion_con_excluido"):
            if ind_.get(k) is not None:
                card[k] = ind_[k]
        # SIPA publica en MILES de personas: 2.587 son 2,59 millones de
        # puestos, y decir "2.587 independientes" los convierte en dos mil.
        millones = lambda x: f"{x / 1000:.2f}".replace(".", ",")
        total = ind_["independientes"] + ind_["asalariados"]
        con = ind_.get("participacion_con_excluido")
        card["detalle_txt"] = (
            f"{millones(ind_['independientes'])} millones de independientes sobre "
            f"{millones(total)} millones de puestos registrados · numerador: "
            f"{', '.join(ind_.get('categorias_numerador') or [])} · denominador: "
            f"{', '.join(ind_.get('categorias_denominador') or [])} · queda afuera "
            f"el monotributo social, cuyo padrón cayó de 653 a 259 mil personas en "
            f"un solo mes ({ind_.get('excluido_quiebre')}) por un cambio de régimen "
            f"y no del mercado de trabajo"
            + (f" · con ese régimen adentro daría {con:.1f}%".replace(".", ",")
               if con else "")
        )
    emp = raw.get("empleadores_pyme") or {}
    # Igual que arriba: SIEMPRE, con None si la SRT no contestó.
    _add(out, "mortalidad_pymes", emp.get("pyme"),
         "empleadores", "SRT — partes empleadoras con cobertura de ART, hasta 50 trabajadores",
         f"{emp['mes']}-01" if emp.get("mes") else None)
    isac = indec.get("isac", {})
    _add(out, "despacho_cemento", _red(isac.get("valor"), 1),
         "índice ISAC", "INDEC — ISAC desestacionalizado (planilla original vigente)", isac.get("fecha"),
         obtenido_en=isac.get("obtenido_en"))
    sub = indec.get("subocupacion_demandante", {})
    # ADR-0249: la tasa la calcula INDEC sobre la PEA, no sobre los ocupados.
    _add(out, "subocupacion_demandante", _red(sub.get("valor"), 1, 100),
         "% de la PEA", "INDEC — EPH, tasa de subocupación demandante",
         sub.get("fecha"))
    emp = indec.get("empleo_registrado", {})
    _add(out, "empleo_registrado", emp.get("valor"),
         "miles de puestos", "Min. de Capital Humano — SIPA (vía datos.gob.ar)",
         emp.get("fecha"))
    seg = snic.get("inseguridad_snic", {})
    _add(out, "inseguridad", seg.get("total_hechos"),
         "hechos/año", "SNIC — Ministerio de Seguridad (calidad UNODC grado A)",
         str(seg.get("anio")))
    # ADR-0327: los dos tipos del SNIC que PUNTÚAN como indicador propio.
    # `tasa_hechos` la calcula la fuente; acá sólo se toma el último año.
    # Se llaman SIEMPRE (valor None si el colector falló), mismo motivo que
    # motorización/supermercados: una clave ausente es invisible para
    # `_carry_forward`.
    tasas_snic = seg.get("tasas_por_tipo") or {}
    homicidios_tasas = tasas_snic.get("Homicidios dolosos") or {}
    anio_hom = max(homicidios_tasas) if homicidios_tasas else None
    _add(out, "tasa_homicidios",
         round(homicidios_tasas[anio_hom], 2) if anio_hom else None,
         "homicidios dolosos cada 100.000 hab.",
         "SNIC — Ministerio de Seguridad (tasa oficial, calidad UNODC grado A)",
         f"{anio_hom}-12-31" if anio_hom else None)
    robos_tasas = tasas_snic.get(
        "Robos (excluye los agravados por el resultado de lesiones y/o muertes)") or {}
    anio_rob = max(robos_tasas) if robos_tasas else None
    _add(out, "tasa_robos",
         round(robos_tasas[anio_rob], 1) if anio_rob else None,
         "robos (excl. agravados) cada 100.000 hab.",
         "SNIC — Ministerio de Seguridad (tasa oficial, calidad UNODC grado A)",
         f"{anio_rob}-12-31" if anio_rob else None,
         detalle_txt=("La tasa cae de 1.002,8 (2024) a 778,1 (2025), −22,4% en un "
                       "año sin evento conocido que lo explique; Hurtos cae en "
                       "proporción similar (−17,4%) mientras Robos agravados por "
                       "el resultado de lesiones/muertes SUBE 45,5% el mismo año. "
                       "El patrón es compatible con reporte incompleto de alguna "
                       "jurisdicción al cierre de 2025 y no se pudo confirmar ni "
                       "descartar contra un informe metodológico público del "
                       "SNIC. Se publica el dato oficial vigente con esta "
                       "limitación declarada.") if anio_rob == "2025" else None)
    icc = utdt.get("icc_utdt", {})
    _add(out, "icc_utdt", _red(icc.get("valor"), 1),
         "índice", "UTDT — Índice de Confianza del Consumidor (CIF)", icc.get("fecha"))
    pn = (raw.get("pobreza") or {}).get("pobreza_nowcast", {})
    _add(out, "pobreza_nowcast", pn.get("valor"),
         "% de personas", "UTDT — Nowcast de Pobreza (González-Rozada)", pn.get("fecha"))
    il = utdt.get("indice_lider", {})
    _add(out, "indice_lider", _red(il.get("valor"), 1),
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
    # `interes_relativo` trae el ÍNDICE por término del último mes cerrado, así
    # que este promedio simple ES la canasta (ADR-0222): card y serie salen del
    # mismo store y del mismo cálculo, y el par volvió a reconciliar en G3.
    #
    # `fecha_dato` es el MES del dato y no el timestamp de la corrida. Antes era
    # el timestamp porque la card salía de una consulta en tiempo real: si esa
    # consulta fallaba, la card quedaba en None y el carry-forward la marcaba
    # desactualizada, que era la única señal de que Trends estaba caído. Ahora la
    # card sale del store, así que con Trends muerto seguiría publicando un valor
    # con fecha de hoy y nadie se enteraría. Con el mes del dato, esa demora la
    # ve G2 como en cualquier fuente mensual (tope general de 110 días; el rezago
    # estructural de esta serie llega a ~62, porque el mes en curso no cuenta).
    sd_raw = trends.get("sentimiento_digital", {})
    sd = sd_raw.get("interes_relativo") or {}
    sd_mes = f"{sd_raw['mes']}-01" if sd and sd_raw.get("mes") else None
    _add(out, "sentimiento_digital", round(sum(sd.values()) / len(sd), 1) if sd else None,
         "índice (100 = 4T-2023)", "Google Trends", sd_mes,
         detalle_txt=("Promedio simple de seis términos de búsqueda —inflación, precios, "
                      "dólar, empleo, inseguridad y corrupción—, cada uno comparado contra "
                      "su propio 4º trimestre de 2023 en una ventana fija desde 2021. "
                      "Mayor = más búsquedas de urgencia. El índice de impacto social lo puntúa invertido."))
    # ADR-0224: el que PUNTÚA es la motorización total —autos + motos 0km per
    # cápita—, no cada vehículo por su lado. Las dos patas se siguen relevando
    # y se agregan acá abajo porque son los Componentes A y B de la matriz A×B
    # que explica el color; se descartan como card DESPUÉS de `_semaforos`.
    #
    # Los tres se llaman SIEMPRE (aunque el colector haya fallado y vengan
    # None) por el mismo motivo que sentimiento_digital: una clave ausente es
    # invisible para `_carry_forward`, que sólo repara las que ya están con
    # valor None.
    moto = raw.get("motorizacion") or {}
    mt = moto.get("motorizacion_total", {})
    _add(out, "motorizacion_total", mt.get("valor"),
         mt.get("unidad") or "vehículos 0km por cada 1.000 habitantes (12 meses)",
         mt.get("fuente") or ("DNRPA — inscripciones iniciales de automotores y "
                              "motovehículos, per cápita (INDEC)"),
         f"{mt['fecha']}-01" if mt.get("fecha") else None)
    # La composición viaja COLGADA del indicador, como las `variaciones` de la
    # carne: meterla como clave suelta del dict la convertiría en un indicador
    # fantasma.
    if out.get("motorizacion_total") is not None and mt.get("composicion"):
        out["motorizacion_total"]["composicion"] = mt["composicion"]
    # ADR-0328: entra a puntuar por su cuenta. El colector ya calcula el
    # cociente para el mes vigente dentro de `composicion` (ADR-0323); acá se
    # publica como card propia con card = último mes, serie = histórica
    # rebaseada (misma separación card/índice que `motorizacion_total`).
    comp = mt.get("composicion") or {}
    _add(out, "ratio_motos_autos", comp.get("ratio_motos_autos"),
         "motos por cada auto patentado (móvil 12m)",
         "DNRPA — inscripciones iniciales de automotores y motovehículos, "
         "sin Tierra del Fuego",
         f"{mt['fecha']}-01" if mt.get("fecha") else None,
         detalle_txt=("Más motos por auto se lee como DETERIORO: la "
                       "motorización total cuenta todo patentamiento como "
                       "señal positiva sin distinguir de qué vehículo viene, "
                       "y este ratio existe para detectar que ese crecimiento "
                       "sea un corrimiento hacia la moto y no una mejora "
                       "pareja."))
    autos = moto.get("patentamiento_autos", {})
    _add(out, "patentamiento_autos", autos.get("valor"),
         "unidades", "DNRPA — inscripciones iniciales de automotores",
         f"{autos['fecha']}-01" if autos.get("fecha") else None)
    motos = moto.get("patentamiento_motos", {})
    _add(out, "patentamiento_motos", motos.get("valor"),
         "unidades", "DNRPA — inscripciones iniciales de motovehículos",
         f"{motos['fecha']}-01" if motos.get("fecha") else None)
    # ADR-0225: el único componente del cinturón que mide volumen efectivamente
    # comprado. Se llama SIEMPRE, aunque el colector haya fallado, por el mismo
    # motivo que la motorización y sentimiento_digital: una clave ausente es
    # invisible para `_carry_forward`, que sólo repara las que ya están en None.
    super_ = (raw.get("indec_supermercados") or {}).get("consumo_supermercados", {})
    _add(out, "consumo_supermercados", super_.get("valor"),
         # la base la declara la fuente y la lee el colector (ADR-0243); el
         # literal que había acá decía «2004 = 100» y la serie ni siquiera
         # empieza antes de 2017
         super_.get("unidad") or "índice (desestacionalizado)",
         "INDEC — Encuesta de supermercados (ventas a precios constantes)",
         f"{super_['fecha']}-01" if super_.get("fecha") else None)
    return out


def build_series():
    """Agrupa output/series/*.csv en {indicador: [{fecha, valor}, ...]} asc.

    La implementación se mudó a series_io para que generar_informe.py pueda
    leer las mismas series y calcular el ITVC (ADR-0208)."""
    return series_io.build_series(OUT / "series")


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
    for sustituido in ("dolarizacion_depositos", "presion_dolarizacion"):
        store.pop(sustituido, None)
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
#
# ⚠ HOY ESTE MAPA NO SE EJECUTA. Los cuatro cinturones salen de aplicar_scoring()
# por `continue` antes de llegar al bucle que lo consulta: vida cotidiana puntúa
# por el ITCIS base-100 desde julio de 2026 y los otros tres por su propio índice
# paramétrico. Queda como el fallback de un cinturón que no tenga índice propio.
#
# Consecuencia práctica, y el motivo de esta nota: sus textos son de la
# metodología PREVIA a los índices base-100 y describen cosas que ya no son
# —`mortalidad_pymes` acá dice «IPI m/m» y hace un año que mide empleadores de la
# SRT—. No es una fuente de verdad de nada: para saber qué mide un indicador van
# la paramétrica del cinturón, su ficha y `web/src/lib/formulas.ts`.
SCORING = {
    # ── vida cotidiana ── (metodología CIGOB validada may-2026; anclas de dominio)
    "ipc_alimentos":       (lambda v: v,                "0% → 0 · 5% → 5 · 10% → 10 (mensual)"),
    "brecha_salario_cbt":  (lambda v: (4 - v) * 10 / 3, "4 canastas → 0 · 2,5 → 5 · 1 → 10 (salario formal / CBT)"),
    "consumo_carne_vacuna": (lambda v: (55 - v) / 2,    "55 → 0 · 45 → 5 · 35 → 10 (kg/hab/año)"),
    "informalidad":        (lambda v: (v - 25) / 2.5,   "25% → 0 · 37,5% → 5 · 50% → 10"),
    "mortalidad_pymes":    (lambda v: 5 - v,            "+5% → 0 · 0% → 5 · −5% → 10 (IPI m/m)"),
    "despacho_cemento":    (lambda v: (180 - v) / 10,   "180 → 0 · 130 → 5 · 80 → 10 (índice ISAC)"),
    "subocupacion_demandante":         (lambda v: v - 5,            "5% → 0 · 10% → 5 · 15% → 10 (subocupación demandante)"),
    "icc_utdt":            (lambda v: (60 - v) / 3,     "60 → 0 · 45 → 5 · 30 → 10 (índice de confianza)"),
    # sentimiento_digital lo puntúa VIDA COTIDIANA. Vivía acá abajo del rótulo
    # de espíritu de época porque el cinturón lo espejaba; el cinturón salió
    # (ADR-0205) y la entrada se queda, que es de quien siempre fue.
    "sentimiento_digital": (lambda v: v / 10,           "0 → 0 · 50 → 5 · 100 → 10 (canasta de seis búsquedas de urgencia vs 4T-2023: mayor = más preocupación)"),
    "inseguridad":         (lambda v: (v / POB_AR * 100_000 - 3000) / 400,
                                                        "tasa/100k hab (pob. 46,7M): 3.000 → 0 · 5.000 → 5 · 7.000 → 10"),
    # Se puntúa sobre la variación interanual REAL (deflactada), no el stock nominal.
    "endeudamiento_familiar": (lambda v: 5 + v / 4,     "−20% real → 0 · 0% → 5 · +20% real → 10 (var. interanual real del crédito)", "var_real_12m"),
}

VIDA_CONTEXTO = ("Indicador de contexto — no integra el índice de impacto social (paramétrica CIGOB jul-2026) "
                 "o su componente no pudo calcularse en esta corrida.")

MACRO_CONTEXTO = "Indicador de contexto — no integra el índice macroeconómico (paramétrica CIGOB may-2026)."
GESTION_CONTEXTO = "Indicador de contexto — no integra el índice de gestión (paramétrica CIGOB jul-2026)."
# Texto de respaldo para una card de política que no integre el índice. Los
# seguimientos internos vigentes se excluyen mediante POLITICA_OCULTOS.
POLITICA_CONTEXTO = "Indicador de contexto — no integra el índice político (paramétrica CIGOB jul-2026)."

SCORE_EXPLICACION = {
    "macro":          ("Índice macroeconómico (paramétrico, 0–100, mayor = menos tensión) ponderado por 6 dimensiones: "
                       "estabilidad monetaria 26%, viabilidad fiscal-comercial 24%, financiamiento 16%, "
                       "actividad 11%, competitividad externa 11%, inversión 12%. La tensión del cinturón es (100 − índice) / 10."),
    "politica":       ("Índice político (paramétrico, 0–100, mayor = más capital político) ponderado por 7 dimensiones: "
                       "poder legislativo 21%, alianzas territoriales 19%, cohesión interna del oficialismo 15%, "
                       "conflicto social 10%, imagen y voto 7%, poder judicial 15%, sector privado 13%. "
                       "La tensión del cinturón es (100 − índice) / 10."),
    "gestion":        ("Índice de gestión (paramétrico, 0–100, mayor = agenda de reformas ejecutándose) ponderado por 5 dimensiones: "
                       "reformas económicas 35%, reforma del Estado 25%, reforma laboral 15%, "
                       "privatizaciones e inversión 15%, reforma social y orden 10%. La tensión del cinturón es (100 − índice) / 10."),
    "vida_cotidiana": ("Índice de impacto social (de seguimiento: los componentes usan 100 = promedio del 4º trimestre de 2023, salvo "
                       "servicios públicos, que usa umbrales internacionales por rubro; mayor = mejores condiciones de vida) "
                       "ponderado por 6 dimensiones: ingresos y consumo 28%, precios 25%, "
                       "vulnerabilidad financiera 10%, empleo 24%, confianza y percepción 8%, seguridad 5%. "
                       "La tensión del cinturón es 5 − (índice − 100) × 0,2."),
}


# Era una "réplica" escrita a mano de generar_informe._estado. Una réplica es
# una copia que puede desincronizarse, y de hecho el criterio de la alerta ya se
# había desincronizado de las dos (ADR-0195). Ahora las tres son la misma.
_estado = estado_de_score


def _reconciliar_intermedio(informe):
    """Le devuelve a `output/informe.json` los scores que sólo este script sabe.

    `output/informe.json` (y su `informe.md`) es el artefacto de schema público
    —"v1.0.0 para dev externo"— y lo escribe `generar_informe.py`, que corre
    ANTES y **no puede** calcular el ITVC: sólo ve el caché del colector viejo,
    con 3 indicadores y un score legacy de vida cotidiana. El snapshot que
    publica el sitio lo arma este script, con 17 indicadores y el ITVC real.

    Resultado, hasta el 2026-08-14: los dos artefactos publicaban números
    distintos del mismo mes y nadie fallaba. Con la corrida de agosto, vida
    cotidiana decía 2,9 en el intermedio y 6,9 en el sitio, y el global 2,7
    contra 3,5. La condición estaba documentada en la docstring de
    `recomputar_vida_y_global` desde siempre; lo que faltaba era cerrar la
    consecuencia.

    Esto **no es el arreglo de fondo**. El de fondo es que la máquina del ITVC
    (`_itvc_indices`, el rebase, los ajustes, la robustez, la validación) viva
    en un módulo que importen los dos scripts, y que `generar_informe.py`
    registre vida cotidiana en `_INDICES_PARAMETRICOS` como los otros tres.
    Eso es refactorizar el camino de publicación entero y se hace aparte
    (ADR-0206). Mientras tanto, acá se corrigen los números para que los dos
    artefactos no se contradigan, y `test_artefactos_coherentes.py` impide que
    la brecha se reabra en silencio.
    """
    path = OUT / "informe.json"
    if not path.exists():
        return
    intermedio = json.loads(path.read_text(encoding="utf-8"))
    cambios = []
    for ckey, c in informe["cinturones"].items():
        destino = intermedio.get("cinturones", {}).get(ckey)
        if destino is None:
            continue
        if destino.get("score") != c["score"]:
            cambios.append(f"{ckey} {destino.get('score')}→{c['score']}")
        destino["score"] = c["score"]
        if "estado" in c:
            destino["estado"] = c["estado"]
        # El ITVC también se calcula recién en publicar.py. Copiar sólo su
        # tensión dejaba una contradicción interna: score 6,2 junto al bloque
        # viejo de ITVC 89,3 (que equivale a 7,1). El bloque completo es un
        # único hecho calculado y debe viajar junto.
        if ckey == "vida_cotidiana" and c.get("itvc"):
            if (destino.get("itvc") or {}).get("valor") != c["itvc"].get("valor"):
                cambios.append(
                    f"ITCIS {(destino.get('itvc') or {}).get('valor')}"
                    f"→{c['itvc'].get('valor')}"
                )
            destino["itvc"] = c["itvc"]
    if intermedio.get("score_global") != informe["score_global"]:
        cambios.append(f"global {intermedio.get('score_global')}→{informe['score_global']}")
    intermedio["score_global"] = informe["score_global"]
    # El veredicto de portada viaja con los scores: si acá se copiara el score
    # y no el barbarismo que sale de él, el intermedio quedaría diciendo un
    # riesgo dominante que sus propios números ya no sostienen — el ADR-0208
    # otra vez, en el artefacto de al lado (ADR-0237).
    for campo in ("barbarismo_activo", "cinturon_dominante", "alerta_multicinturon"):
        if intermedio.get(campo) != informe.get(campo):
            cambios.append(f"{campo} {intermedio.get(campo)}→{informe.get(campo)}")
        intermedio[campo] = informe.get(campo)
    path.write_text(json.dumps(intermedio, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8")
    # El .md sale del MISMO dict, así que se regenera con el escritor de
    # generar_informe en vez de parchearle líneas sueltas al texto.
    sys.path.insert(0, str(ROOT / "scripts"))
    import generar_informe as _gi
    _gi.escribir_md(intermedio)
    if cambios:
        print(f"[OK] intermedio reconciliado: {' · '.join(cambios)}")


def recomputar_barbarismo(informe):
    """Re-deriva el veredicto de portada DESPUÉS de que los scores son finales.

    `detectar_barbarismo()` corre en `generar_informe.py`, y hasta acá el
    snapshot lo heredaba tal cual — pero `recomputar_vida_y_global` puede
    haber movido el score de vida cotidiana entre un script y el otro. Esa es
    exactamente la forma del ADR-0208: un veredicto editorial calculado sobre
    scores que después cambiaron. Aquella vez se arregló haciendo que el
    intermedio naciera bien; esto es el cinturón de seguridad del otro lado.
    Hoy es no-op —si imprime algo, algo se movió y hay que mirarlo.

    Publica además `cinturon_dominante`: qué cinturón produjo el barbarismo.
    Ver ADR-0237.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import generar_informe as _gi
    barbarismo, dominante, alerta = _gi.detectar_barbarismo(informe["cinturones"])
    cambios = []
    if informe.get("barbarismo_activo") != barbarismo:
        cambios.append(f"barbarismo {informe.get('barbarismo_activo')}→{barbarismo}")
    if informe.get("alerta_multicinturon") != alerta:
        cambios.append(f"alerta {informe.get('alerta_multicinturon')}→{alerta}")
    informe["barbarismo_activo"] = barbarismo
    informe["cinturon_dominante"] = dominante
    informe["alerta_multicinturon"] = alerta
    if cambios:
        print(f"[OK] barbarismo recomputado sobre scores finales: {' · '.join(cambios)}")
    return informe


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


# Mínimo de meses para publicar la serie de una dimensión. Con menos, la
# "evolución" es un segmento y el lector le lee una pendiente que no está
# medida. Es el mismo criterio de los 12 puntos que ya pide la validación
# externa antes de emitir una correlación.
MIN_MESES_SERIE_DIMENSION = 12


def _series_dimensiones(bloque, sigla, base100=False):
    """Anexa a cada dimensión del índice su serie mensual (ADR-0233).

    El índice se publica con 31-33 meses y cada componente con los suyos, pero
    la capa del medio —la dimensión— existía sólo como el valor del mes. Y ahí
    está la lectura: el ITCIS cae 6 puntos entre dic-2023 y ago-2026 escondiendo
    que ingresos sube 24 y vulnerabilidad financiera se derrumba 82. Un índice
    plano puede ser calma o dos fuerzas opuestas del mismo tamaño, y hasta acá
    no había forma de distinguirlas.

    La serie viene de `validacion_externa.py`, del MISMO resultado mensual del
    motor con el que se arma la serie del índice — no hay una segunda
    agregación. Y por eso hereda su procedencia y hay que decirla: se
    reconstruye desde las series de componentes, sin overrides del analista, y
    termina en el último mes que pasó el piso de cobertura, que en los tres
    índices por bandas es anterior al mes de la card.
    """
    dims = (bloque or {}).get("dimensiones") or {}
    if not dims:
        return
    historia = _cargar_validacion().get(f"serie_{sigla}") or {}
    bloque["serie_mensual"] = [[m, v] for m, v in sorted(historia.items())]
    por_dim = ((_cargar_validacion().get("series_dimensiones") or {}).get(sigla)) or {}
    publicadas, meses = 0, set()
    for dkey, dim in dims.items():
        serie = (por_dim.get(dkey) or {}).get("serie") or {}
        if len(serie) < MIN_MESES_SERIE_DIMENSION:
            continue
        dim["serie"] = [[ym, serie[ym]] for ym in sorted(serie)]
        publicadas += 1
        meses |= set(serie)
    if not publicadas:
        return

    escala = ("base 100 = promedio del 4T-2023" if base100
              else "puntaje 0-100 de las bandas del índice")
    faltan = [d["nombre"] for k, d in dims.items() if "serie" not in d]
    partes = [
        f"El índice es el promedio ponderado de estas dimensiones, y su valor "
        f"agregado puede quedarse quieto porque nada se mueve o porque dos cosas "
        f"grandes se mueven en direcciones opuestas. Estas series separan los dos "
        f"casos: cada una es la misma dimensión que se lee arriba, mes a mes, en "
        f"la misma escala ({escala}).",
        "Se calculan con el motor del índice y no con una cuenta aparte: el "
        "promedio ponderado de los componentes de la dimensión, renormalizando "
        "por el peso que efectivamente tiene dato ese mes, es el mismo paso que "
        "el índice ya da para llegar a su propio número.",
        "Vienen de la reconstrucción histórica —las series de cada componente "
        "pasadas por el motor, sin ajustes del analista—, así que llegan hasta el "
        "último mes con cobertura suficiente y ese mes puede ser anterior al de "
        "la card. Un mes en el que ninguna componente de la dimensión tiene dato "
        "no deja punto: el hueco se muestra como hueco, no se arrastra ni se "
        "interpola.",
    ]
    if faltan:
        partes.append(
            f"Sin serie publicable: {', '.join(sorted(faltan)).lower()} — sus "
            f"componentes no tienen historia mensual reconstruible, así que la "
            f"dimensión puntúa en la card y no puede dibujarse hacia atrás.")

    bloque["dimensiones_serie"] = {
        "titulo": "Qué dimensión movió el índice",
        "sub": ("La capa del medio: entre el índice y sus indicadores están las "
                "dimensiones, y son ellas las que explican el movimiento."),
        "escala": escala,
        "base100": bool(base100),
        "desde": min(meses), "hasta": max(meses), "n": len(meses),
        "n_dimensiones": publicadas,
        "nota": " ".join(partes),
    }


def _scoring_indice(c, clave, mod, contexto_txt, input_txt_fn):
    """Cinturones con índice paramétrico (macro → ITCM, gestión → ITCG,
    política → ITCP): el puntaje lo computa el colector; acá solo se traduce
    cada puntaje 0-100 a tensión equivalente (para la semántica 0-10 del
    modal) y se anota la tabla de bandas + peso en el índice. Los indicadores
    con en_indice=false son contexto y no aportan."""
    ajustes = {a["indicador"]: a for a in (c.get(clave) or {}).get("ajustes_aplicados", [])}
    sigla = clave.upper()
    nombre = nombre_publico(clave)   # lo que lee el lector (ADR-0340)
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
        _series_dimensiones(bloque, clave)
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
            if p >= 95:
                lectura = (f"Leído solo en la escala del {nombre}, este indicador está en "
                           f"{_lectura_tension(aporte)}: puntaje pleno o casi pleno — este "
                           f"frente está logrado y hoy no agrega tensión al índice.")
            elif p <= 15:
                lectura = (f"Leído solo en la escala del {nombre}, este indicador está en "
                           f"{_lectura_tension(aporte)}: puntaje mínimo — este frente "
                           f"concentra la tensión del cinturón.")
            else:
                lectura = (f"Leído solo en la escala del {nombre}, este indicador está en "
                           f"{_lectura_tension(aporte)}.")
            peso = ind.get("peso_efectivo")
            peso_txt = f"; pesa {peso * 100:.1f}%".replace(".", ",") + f" del {nombre}" if peso else ""
            formula = (f"Anclas del {nombre}: {mod.texto_bandas(ikey)} "
                       f"(puntaje interpolado entre anclas: {p}{peso_txt})")
            if ikey in ajustes:
                aj = ajustes[ikey]
                origen = "automático" if aj.get("origen") == "automatico" else "del analista"
                nota = f"Ajuste {origen}: banda {aj['de']} → {aj['a']}. {aj.get('justificacion', '')}"
        elif ind.get("en_indice") is False:
            nota = ind.get("detalle_txt") if ind.get("estado") == "sin_universo" else contexto_txt
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
                f"+ tramo II.1 >3 meses–1 año {int(ind.get('bopreal_12m', 0))} (M USD; fórmula CIGOB)")
    if ikey == "idc" and ind.get("componentes"):
        c, n = ind["componentes"], ind.get("niveles") or {}
        # `banda_idc` es el semáforo de 3 colores propio del IdC (por
        # z-score, ajeno al motor paramétrico -- ver macro.py:fetch_idc). El
        # punto de color de la card sale del semáforo de 4 colores que
        # _semaforos() calcula sobre el puntaje ITCM del indicador: otra
        # escala, con sus propios cortes. Hoy suelen coincidir, pero no
        # siempre -- con z = −0,6 esta banda da "rojo" mientras el semáforo
        # de 4 colores da "naranja" (revisión de coherencia UI, Tanda B,
        # ago-2026). Por eso el paréntesis dice explícitamente de qué escala
        # es, en vez de un color suelto sin dueño; se omite entero si el
        # colector no corrió y `banda_idc` no está (clave vieja `semaforo`).
        banda_idc = ind.get("banda_idc")
        # Sin la sigla "IdC" (ADR-0311): el rótulo público ya no la usa, así que
        # en el detalle quedaba huérfana. "Este indicador" nombra la misma escala.
        banda_idc_txt = f" (banda propia de este indicador: {banda_idc})" if banda_idc else ""
        txt = (f"{coma(ind.get('valor'))} σ = precio {coma(c.get('precio'))} · "
               f"volumen {coma(c.get('volumen'))} · asignación {coma(c.get('asignacion'))}"
               f"{banda_idc_txt}")
        if n:
            txt += (f" — niveles: tasa real {coma(n.get('tasa_real_pp'))} pp · "
                    f"depósitos {coma(n.get('dep_real_ia_pct'))}% i.a. real · "
                    f"holgura {coma(n.get('holgura_pct'))}%")
        return txt
    if ikey == "idm" and ind.get("m3_real_ia") is not None:
        return (f"brecha {coma(ind.get('valor'))} pp = M3 priv. real i.a. "
                f"{coma(ind['m3_real_ia'])}% − M2 priv. real i.a. {coma(ind['m2_real_ia'])}%")
    if ikey == "desequilibrio_monetario" and ind.get("componente_a") is not None:
        # ADR-0252: las etiquetas describen la COMBINACIÓN observada, no dónde
        # terminó el dinero. La compra neta de divisas no identifica salida del
        # sistema financiero — el BCRA estimó que ~80% quedó depositado acá.
        # ADR-0257: los cuadrantes se nombran por lo que se degradó, no por un
        # color. Las dos combinaciones cruzadas puntúan IGUAL —la matriz es
        # simétrica— así que un nombre que sugiriera que una es más grave que
        # la otra contradiría el número de al lado.
        celdas = {
            "sin_tension": "liquidez transaccional alta y poca compra de divisas",
            "solo_liquidez": "menos pesos transaccionales, sin presión compradora",
            "solo_presion": "presión compradora alta pese a liquidez transaccional alta",
            "liquidez_y_presion": "menos pesos transaccionales y presión compradora alta",
        }
        # «Alta» y «baja» son posiciones dentro de la ventana de calibración, no
        # niveles absolutos, y desde ADR-0257 esa ventana es el régimen abierto
        # para los DOS componentes. Sin decirlo, «liquidez transaccional alta»
        # con el ratio en 33,5% se lee como una afirmación sobre el nivel — y
        # contra la era del cepo ese mismo número era de los más bajos.
        lectura = celdas.get(ind.get("celda"), "")
        return (f"tensión {coma(ind.get('valor'))} pts = liquidez privada en pesos "
                f"transaccionales {coma(ind['componente_a'])}% × compra neta de "
                f"divisas del sector privado US$ {coma(ind['componente_b'])} M"
                + (f" — {lectura}, medidos contra el régimen abierto"
                   if lectura else ""))
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
                  + f" · última acta {c.get('fecha_dato') or 'sin fecha'}"
                  + (" · dato conservado en caché" if c.get('desactualizado') else "")
                  for nombre, peso, c in camaras]
        if partes:
            detalle = f"{coma(ind.get('valor'))}% = " + " · ".join(partes)
            if len(camaras) == 1:
                detalle += " · una sola cámara con dato: su peso se renormaliza al 100%"
            return detalle
    return None


# ── ITVC (vida cotidiana) — doc 260702, ADR-0018 ──────────────────────────────

AJUSTES_ITVC_PATH = ROOT / "data" / "vida" / "ajustes_itvc.json"
ITVC_BASELINES_PATH = ROOT / "data" / "vida" / "itvc_baselines.json"
# La construcción de los índices base-100 se mudó a itvc.py (ADR-0208): era el
# único lugar donde vivía, y por eso generar_informe.py —que corre antes— no
# podía calcular el ITVC y publicaba un score legacy. Acá quedan sólo las rutas,
# que son layout del repo y no metodología del índice.
ITVC_BASE_MESES = itvc.BASE_MESES
ITVC_WINSOR_TOPE = itvc.WINSOR_TOPE
ITVC_SERIES_REBASEADAS = itvc.SERIES_REBASEADAS
_itvc_rebase_movil12 = itvc.rebase_movil12
_itvc_rebase_de_serie = itvc.rebase_de_serie


def _itvc_indices(vida_ind, series):
    """Los índices del ITVC, con los baselines de este repo ya cargados."""
    return itvc.indices_desde_series(vida_ind, series, _itvc_baselines())


def _itvc_baselines() -> dict:
    try:
        return json.loads(ITVC_BASELINES_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


VALIDACION_EXTERNA_PATH = ROOT / "output" / "validacion_externa.json"


def _cargar_validacion():
    try:
        return json.loads(VALIDACION_EXTERNA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _validacion_itvc(bloque, series):
    """Anexa al bloque ITCIS su validación externa. **Sin ancla única** desde
    ADR-0225: el contraste es el PANEL y su factor común.

    Por qué no hay una sola serie enfrente, que es lo que el lector espera y
    hay que explicarle:

    - El ancla era el consumo en supermercados (ADR-0155) y **pasó a ser
      componente del índice**. Medía condiciones materiales del hogar, así que
      integra el ITCIS en vez de juzgarlo — la misma regla que sacó al ICC.
    - El reemplazo conceptualmente correcto existe y está identificado: el
      **consumo privado de las Cuentas Nacionales** del INDEC, que no es una
      faceta del consumo del hogar sino su agregado. Pero es trimestral y
      arranca con la base del índice, así que hoy tiene nueve trimestres: su
      correlación en diferencias oscila entre 0,17 y 0,73 según qué trimestre
      se saque. No es un número publicable, y se declara como serie de
      referencia en formación en la ficha metodológica.
    - Las candidatas mensuales que quedan son todas facetas —naftas, luz, gas,
      transporte, los otros dos canales de comercio— y ninguna sostiene un
      titular sin un párrafo de salvedades.

    Así que el titular es el factor común de los volúmenes físicos que consume
    el hogar, que es contra lo que el gráfico ya venía comparando. `pares` sale
    del factor y no de un par suelto: la matriz de validación cruzada (ADR-0031)
    lee justamente esa clave, y dejarla apuntando a una serie que ahora compone
    el índice habría vuelto circular la matriz entera sin que nada avisara.
    """
    val = _cargar_validacion()
    itvc_serie = val.get("serie_itvc") or {}
    panel = (val.get("panel_validacion") or {}).get("itvc") or {}
    factor = panel.get("factor") or {}
    pares = factor.get("pares") or []
    if len(pares) < 12 or not itvc_serie:
        return
    r_niv, r_dif = factor.get("r_niveles"), factor.get("r_diferencias")
    if r_niv is None:
        return
    corr = val.get("correlaciones", {})
    icc_niv = (corr.get("ITCIS vs ICC UTDT (niveles)") or {}).get("r")

    partes = [
        "No hay una sola serie externa que confirme el índice, y el motivo es parte del "
        "resultado. La que cumplía ese papel —las ventas en supermercados a precios "
        "constantes— mide condiciones materiales del hogar, así que pasó a integrar el "
        "índice: un indicador no puede ser componente y juez del mismo índice.",
        "El reemplazo natural sería el consumo privado que publica el Instituto Nacional de "
        "Estadística y Censos (INDEC) en las Cuentas "
        "Nacionales, que no es un canal del consumo del hogar sino su total; pero es "
        "trimestral y arranca junto con el índice, así que todavía son nueve trimestres y "
        "la correlación se mueve demasiado según cuál se saque. Queda declarado como la "
        "referencia que va a reemplazar a este panel cuando tenga historia, con el umbral "
        "fijado de antemano para que la decisión no dependa de mirar el número.",
        "Mientras tanto el contraste es el panel completo, y el gráfico compara el índice "
        "contra el factor común de lo que el hogar consume en volumen físico —luz, gas, "
        "transporte, combustible—, que es lo que esas series comparten en vez de cualquiera "
        "de ellas suelta.",
    ]
    if icc_niv is not None:
        partes.append(
            f"El Índice de Confianza del Consumidor (ICC) de la Universidad Torcuato Di Tella sigue "
            f"publicándose como contraste que distingue en vez de confirmar: contra ella la correlación es {coma(icc_niv)}. Un "
            f"número más bajo ahí no es una falla del índice, es el resultado — este cinturón "
            f"mide lo que les pasa a los hogares, no lo que opinan.")

    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": factor.get("n"),
        "pares": pares,
        "plot": "minmax",
        "titulo": "¿El índice de impacto social acompaña lo que el hogar efectivamente consume?",
        "sub": ("Paso 9 del manual de indicadores compuestos de la Organización para la "
                "Cooperación y el Desarrollo Económicos (OCDE) y el Centro Común de Investigación "
                "de la Comisión Europea (JRC): un índice válido debe co-moverse con variables "
                "externas relacionadas que no lo componen. Para confirmar el índice no hay una "
                "única serie de referencia —la que hacía ese papel pasó a ser componente del "
                "índice, y su reemplazo natural, el consumo privado de las Cuentas Nacionales, "
                "todavía tiene nueve trimestres—, así que se compara contra un panel de "
                "estadísticas externas y se mira si acompaña más a las de su propio terreno que "
                "a las ajenas. El gráfico muestra el factor común de las que miden volúmenes "
                "consumidos por los hogares —luz, gas, transporte, combustible—: lo que todas "
                "ellas comparten, en vez de una sola. Para discriminar sí hay una serie externa "
                "dedicada, el Índice de Confianza del Consumidor de la Universidad Torcuato Di Tella, que salió del índice y "
                "pasó a ser su ancla. El detalle —las cargas de cada una, el panel completo y "
                "la referencia en formación— está en la ficha metodológica."),
        "serie_label": "Índice de impacto social (reconstrucción mensual)",
        "externa_label": "factor común de los volúmenes consumidos por el hogar",
        "trans_label": ("series normalizadas al rango del período; el factor es un puntaje "
                        "estandarizado y cruza el cero"),
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
                      f"adelanta el índice macroeconómico ({coma(itcm_ade)}) y empeora cuando se adelanta el "
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
    _activos = {k for d in bloque.get("dimensiones", {}).values()
                for k in d.get("indicadores", {})}
    _observados = set(val.get("componentes_historia_itcm") or [])
    _sin_serie = tuple(sorted(_activos - _observados))
    _total = sum(len(d.get("indicadores", {}))
                 for d in bloque.get("dimensiones", {}).values())
    _usados = _total - len(_sin_serie)
    _componentes = f"{_usados} de sus {_total} componentes"

    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], lider[m]] for m in comunes],
        "plot": "minmax",
        "titulo": "¿El índice macroeconómico se mueve con la marcha de la actividad?",
        "sub": ("El contraste del cinturón macro es el Índice Líder de la Universidad Torcuato "
                "Di Tella, que resume la marcha de la actividad económica y no integra el "
                f"índice. El índice macroeconómico se reconstruye mes a mes desde las series de {_componentes} "
                f"(sin serie histórica: {', '.join(k.upper() for k in _sin_serie) or 'ninguno'}; tampoco ingresan los "
                "ajustes del analista; la cobertura varía entre meses: el nivel puede diferir del publicado — lo que valida es "
                "su evolución). La correlación esperada es positiva: menos tensión "
                "macroeconómica, más actividad."),
        "serie_label": "Índice macroeconómico (reconstrucción mensual)",
        "externa_label": "Índice Líder (Di Tella)",
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
    —`consumo_carne_vacuna`, `inseguridad`, `patentamiento_motos`— y el `except
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
    # El más nuevo se elige entre los que NO están rotulados hacia adelante.
    # Los que sí (la encuesta del ISAC rotula por el mes de cierre de la
    # ventana que pregunta) cuentan como antigüedad cero para el promedio —eso
    # es correcto y está arriba—, pero su fecha no puede salir impresa: el
    # texto dice "el dato más reciente es del <fecha>" y publicar ahí un día
    # que todavía no pasó es afirmar algo falso.
    #
    # Estaba latente y no lo destapó ningún cambio de código: mientras algún
    # componente tuviera el dato de HOY había empate en 0 días y `min` devolvía
    # el otro. Al correr el calendario un día, el rotulado hacia adelante queda
    # solo en el mínimo y sale su fecha. Encontrado el 2026-08-15, con
    # brecha_obra_publica en 2026-09-01.
    no_futuros = [f for f in filas if f["fecha"] <= str(hoy)]
    mas_nuevo = min(no_futuros or filas, key=lambda f: f["dias"])
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
    tres índices con contraste externo contra los TRES contrastes a la vez (el
    ITCG no tiene, ADR-0336). Validez convergente + discriminante: cada índice
    debe correlacionar más fuerte con su par teórico (ITCM ↔ actividad ·
    ITCIS ↔ el volumen que consume el hogar · ITCP ↔ EPU Argentina) que con el
    contraste ajeno — la prueba
    de que no miden "todo junto". Hoy no se cumple en todos, y la conclusión lo
    declara con el detalle derivado de los números."""
    try:
        bloques = {
            "ITCM": informe["cinturones"]["macro"]["itcm"]["validacion"]["pares"],
            "ITVC": informe["cinturones"]["vida_cotidiana"]["itvc"]["validacion"]["pares"],
            "ITCP": informe["cinturones"]["politica"]["itcp"]["validacion"]["pares"],
        }
    except (KeyError, TypeError):
        return
    indices = {k: {p[0]: p[1] for p in v} for k, v in bloques.items()}
    # El indicador de mercado que era el ancla de macro YA NO EXISTE en el
    # informe: se reemplazó por el Índice Líder y el reemplazo es total, no una
    # suma — decisión del editor. La matriz es 3×3 (sin el ITCG, ADR-0336), un contraste propio por
    # índice.
    # ADR-0225: el contraste propio del ITCIS ya no es el consumo en
    # supermercados —que ahora COMPONE el índice— sino el factor común de los
    # volúmenes físicos que consume el hogar. La clave se renombra: dejarla
    # como "consumo" habría dicho en el tablero que el índice se contrasta
    # contra una serie que en realidad lleva adentro.
    externas = {"lider": {p[0]: p[2] for p in bloques["ITCM"]},
                "volumen_hogar": {p[0]: p[2] for p in bloques["ITVC"]},
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

    # Sin el ITCG (ADR-0336): un índice de ejecución no tiene contraste externo
    # por definición, así que no tiene par propio que poner en la matriz.
    PAR_PROPIO = {"ITCM": "lider", "ITVC": "volumen_hogar", "ITCP": "epu"}
    filas = []
    for ik in ("ITCM", "ITVC", "ITCP"):
        # `indice` es la clave de la fila (la sigla: la usan la matriz de la web
        # para marcar «este cinturón» y bigquery_export); `nombre` es lo que se
        # lee en pantalla (ADR-0340).
        fila = {"indice": SIGLAS_PUBLICAS[ik.lower()],
                "nombre": nombre_publico(ik, mayuscula=True), "propio": PAR_PROPIO[ik]}
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
    f_itcm, f_itvc, f_itcp = filas

    # El poder discriminante se DERIVA, no se afirma. Antes el texto decía que
    # las celdas cruzadas eran "del mismo orden en más de un caso" con un ejemplo
    # escrito a mano; eso quedó corto cuando el ancla de macro pasó a ser la
    # actividad y su par propio quedó por debajo de dos ajenos. La frase se
    # recalcula en cada corrida para que no pueda sobreafirmar.
    ETIQ = {"lider": "la actividad",
            "volumen_hogar": "el volumen que consume el hogar",
            "epu": "la incertidumbre de política"}
    superados = []
    for f in filas:
        propio = abs(f[f["propio"]]["r"])
        ajenas = {k: abs(f[k]["r"]) for k in externas if k != f["propio"]}
        mayor = max(ajenas, key=ajenas.get)
        if ajenas[mayor] > propio:
            superados.append((f["nombre"], ETIQ[mayor], f[mayor]["r"], f[f["propio"]]["r"]))
    if superados:
        detalle = "; ".join(f"el {ik[:1].lower() + ik[1:]} correlaciona {fmt(r_aj)} con {lbl} contra {fmt(r_pr)} con su "
                            f"propio par" for ik, lbl, r_aj, r_pr in superados)
        discriminante = (f"La separación es parcial, y se declara: en {len(superados)} de los "
                         f"{len(filas)} índices la correlación más fuerte no es con su par propio "
                         f"({detalle}). En una muestra de unos treinta meses en la que toda la "
                         f"economía y la política se movieron juntas, los contrastes externos "
                         f"comparten buena parte de la tendencia del período, así que el nivel no "
                         f"alcanza para separarlos; los cambios mes a mes que acompañan a cada "
                         f"celda son la lectura más exigente.")
    else:
        discriminante = ("En los tres casos la correlación más fuerte es con el par propio, que "
                         "es la prueba de que cada índice mide su terreno y no «todo junto».")
    informe["validacion_cruzada"] = {
        "filas": filas,
        "externas": [["lider", "Actividad (Índice Líder de Di Tella)"],
                     ["volumen_hogar", "Volumen consumido por el hogar (factor común)"],
                     ["epu", "Incertidumbre de política en la prensa"]],
        "titulo": "¿Cada índice mide lo suyo?",
        "sub": ("Los tres índices que tienen contraste externo se reconstruyen mes a mes y se "
                "comparan contra los tres contrastes a la vez. Cada uno tiene el propio: la "
                "macroeconomía con la marcha de la actividad, el impacto social "
                "con el factor común de los "
                "volúmenes que el hogar consume —luz, gas, transporte, combustible—, la política "
                "con la incertidumbre de política que mide la prensa argentina (el índice de "
                "incertidumbre de política económica, EPU por su sigla en inglés). La gestión no "
                "figura: mide lo que el gobierno "
                "hace y no tiene contraste externo posible. Si cada índice mide su propio terreno, debería "
                "correlacionar con su par natural al menos tanto como con los ajenos. Es la "
                "prueba clásica de que un indicador no mide \"todo junto\"."),
        # La primera oración es la que va sola en la card (ADR-0165): corta y con
        # el veredicto. El detalle par por par queda para el desarrollo.
        "conclusion": (f"Los tres pares propios dan el signo esperado. Índice macroeconómico "
                       f"{fmt(f_itcm['lider']['r'])} con la actividad, índice de impacto social "
                       f"{fmt(f_itvc['volumen_hogar']['r'])} con el volumen que consume el "
                       f"hogar, índice político "
                       f"{fmt(f_itcp['epu']['r'])} con la incertidumbre de política — este último "
                       f"más moderado que los otros dos, coherente con un índice con varios "
                       f"componentes recién automatizados y con historia corta. "
                       + discriminante),
    }




def _validacion_itcg(bloque):
    """El ITCG no tiene validación externa, por definición (ADR-0336).

    Mide lo que el gobierno HIZO. Una serie externa puede medir dos cosas: lo
    que el gobierno hace —y entonces es un instrumento de la misma agenda, y
    correlacionar con ella es una identidad— o lo que pasa como consecuencia —el
    valor de las empresas, la entrada de capital, la confianza—, que mezcla la
    ejecución con todo lo demás que mueve a la economía y a la política. No hay
    una tercera clase de serie. Hasta ADR-0336 la sección publicaba el factor
    común del capital privado como contraste y declaraba el problema «abierto»;
    una casilla de validación con un número adentro se lee como aprobada, y ese
    número no podía confirmar un índice de ejecución.

    Se publica la DECLARACIÓN (sin pares, sin r, sin gráfico) para que el
    tablero diga por qué no hay contraste en vez de omitirlo en silencio."""
    bloque["validacion"] = {
        "sin_contraste": True,
        "titulo": "Un índice de ejecución no tiene contraste externo",
        "sub": ("Este índice mide lo que el gobierno hace: cuánto avanzó la agenda de reformas "
                "que se propuso. Por eso no tiene validación externa, y no por falta de "
                "búsqueda. Una estadística de afuera puede medir lo que el gobierno hace, y "
                "entonces es parte de la misma agenda —compararse con ella es compararse "
                "consigo mismo—, o lo que pasa como consecuencia —el valor de las empresas, la "
                "entrada de capital, la confianza—, que mezcla la ejecución con todo lo demás "
                "que mueve a la economía y a la política. No hay una tercera clase de "
                "estadística."),
        "conclusion": ("La solidez del índice se sostiene en los otros dos controles que se "
                       "publican en cada edición: cuánta información distinta aporta cada "
                       "componente y cuánto se mueve el resultado si cambian los pesos. Por el "
                       "mismo motivo este índice no figura en la matriz de validación cruzada."),
    }


def _validacion_itcp(bloque):
    """Anexa al bloque ITCP su validación externa: la serie mensual del índice
    (reconstruida por el estudio desde las series de componentes) contra el
    EPU de Argentina (Economic Policy Uncertainty, minería de texto de prensa
    local — Banco de España + SECMCA, misma familia metodológica que
    Baker/Bloom/Davis) — correlación negativa esperada. No es un precio de
    mercado como los otros tres pares: es la lectura pública de la política
    misma, ajena a los componentes del índice."""
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
    n_componentes = sum(
        len(d.get("indicadores", {}))
        for d in bloque.get("dimensiones", {}).values()
    )
    corr_brecha = val.get("correlaciones_brecha_obra_publica") or {}
    brecha_niv = (corr_brecha.get("niveles (brecha obra pública vs Construya var. i.a., ambas 12m)") or {}).get("r")
    brecha_dif = (corr_brecha.get("primeras diferencias (brecha vs Construya)") or {}).get("r")
    contraste_brecha = (
        f" El contraste propio de expectativas de construcción con el volumen de insumos "
        f"vendidos (Construya), ambas series suavizadas a doce meses, da "
        f"{coma(brecha_niv)} en niveles y {coma(brecha_dif)} en cambios mensuales. "
        "La fecha de expectativas representa el inicio de su horizonte trimestral; "
        "el contraste retrospectivo no demuestra anticipación ni causalidad."
        if brecha_niv is not None and brecha_dif is not None else
        " El contraste propio con Construya no está disponible en esta corrida.")
    bloque["validacion"] = {
        "r_niveles": r_niv, "r_diferencias": r_dif, "n": niveles.get("n"),
        "pares": [[m, serie[m], epu[m]] for m in comunes],
        "plot": "minmax_inv",
        "titulo": "¿El capital político se refleja en menos incertidumbre de política percibida?",
        "sub": ("El contraste natural del cinturón político no es un precio de mercado sino la "
                "lectura pública de la política misma: el índice de incertidumbre de política "
                "económica (EPU, por su sigla en inglés) de la Argentina mide, con minería de "
                "texto sobre diarios locales, cuánto se habla de incertidumbre alrededor del "
                "gobierno y sus políticas. Lo elaboran el Banco de España y el Consejo Monetario "
                "Centroamericano con la misma familia metodológica que el índice de Baker, Bloom "
                "y Davis. El índice político se reconstruye mes a mes desde las series de sus componentes (sin los "
                "ajustes del analista: el nivel puede diferir del publicado — lo que valida es "
                f"su evolución); varios de los {n_componentes} componentes tienen historia corta o recién "
                "se automatizaron en julio de 2026 (cohesión del bloque oficialista, alineamiento "
                "de senadores por provincia, adhesión provincial al Régimen de Incentivo para "
                "Grandes Inversiones), así que la reconstrucción de los "
                "meses más antiguos se apoya sobre todo en poder legislativo, el votómetro y la "
                "protesta social — límite que se declara, no se esconde."),
        "serie_label": "Índice político (reconstrucción mensual)",
        "externa_label": "Incertidumbre de política en la prensa (EPU, invertido)",
        "trans_label": ("series normalizadas al rango del período; la incertidumbre de política "
                        "se muestra invertida"),
        "r_sin_sector_privado": r_sin_priv,
        "por_gobierno": val.get("brecha_obra_publica_por_gobierno") or {},
        "conclusion": (
            f"Contra la incertidumbre de política en la prensa sola —una de las tres estadísticas "
            f"del panel— la correlación es {coma(r_niv)} en niveles y "
            f"{coma(r_dif)} en los cambios mes a mes: el signo negativo es el esperado, más "
            f"moderado que en macro o gestión."
            + (f" Sin la dimensión de sector privado —incorporada en julio de 2026— la "
               f"correlación sería {coma(r_sin_priv)}, y conviene explicar la diferencia en "
               f"lugar de omitirla. "
               if r_sin_priv is not None else " ")
            + "El contraste mide incertidumbre de política económica en la prensa, y no cubre "
              "la relación del Gobierno con los empresarios: pedirle que valide una dimensión "
              "que no abarca es pedirle lo que no mide."
            + contraste_brecha
            + (" La comparación por gobierno permite examinar la estabilidad del signo. "
               "Una asociación distinta no identifica por sí sola su causa: el recorte de "
               "obra pública puede formar parte del programa y afectar las expectativas "
               "del sector. Esa interpretación debe contrastarse con evidencia adicional."
               if val.get("brecha_obra_publica_por_gobierno") else "")),
    }


# Indicador → serie de la que sale su índice. Los que no figuran acá usan una
# serie homónima (`rebase_de_serie(series, "mora_familias")` y compañía).
_SERIE_DEL_INDICADOR_ITVC = {i: s for s, i in itvc.SERIES_REBASEADAS.items()}


def _fecha_del_indice_itvc(ikey, series):
    """Mes del último punto de la serie que produjo el índice del componente.

    La card trae `fecha_dato` de la fuente y el índice sale de la serie, que
    puede ir un mes atrás. `IndicadorModal.astro` ya leía `fecha_indice_itvc`
    para decir de cuándo es el nivel que puntúa —lo único para lo que existe
    esa fila— pero no lo escribía nadie, así que el sufijo nunca renderizaba.
    Devuelve None si la serie no resuelve: entonces el modal omite el sufijo,
    como venía haciendo.
    """
    skey = _SERIE_DEL_INDICADOR_ITVC.get(ikey, ikey)
    serie = (series or {}).get(skey) or []
    return ((serie[-1].get("fecha") or "")[:10] or None) if serie else None


# La card guarda la carga redondeada a un decimal (`build_vida`) y la serie se
# arma con el valor sin redondear, así que la card no identifica una carga sino
# el intervalo de cargas que redondean a ella.
_BORDE_REDONDEO_CARGA = 0.05


def _rango_indice_compatible_con_card(valor, transporte_pct):
    """Índices que la card puede estar representando, extremos incluidos.

    Comparar el índice publicado contra UNA recomputación desde la card es
    comparar cosas distintas: cualquier carga en [v−0,05, v+0,05] produce esa
    misma card. Con el transporte al 43% de la canasta esos 0,05 valen 0,215
    puntos de índice — cuatro veces la tolerancia fija de 0,05 que había acá,
    así que el guard se disparaba por redondeo y no por desalineación.

    El índice es monótono no creciente en la carga (las dos tensiones crecen
    con ella y se toma la mayor), así que los extremos del intervalo lo acotan.
    """
    carga = float(valor)
    piso_carga = max(carga - _BORDE_REDONDEO_CARGA, 1e-9)   # más carga → menos índice
    techo = itvc.indice_asequibilidad_tarifas(piso_carga, transporte_pct)
    piso = itvc.indice_asequibilidad_tarifas(carga + _BORDE_REDONDEO_CARGA, transporte_pct)
    return piso, techo


def _series_tarifas_alineadas_con_card(c, series):
    """Impide mezclar la card IIEP de un mes con el índice tarifario de otro.

    Si no se puede acreditar que card y serie hablan del mismo mes, el
    componente **se cae** en vez de publicarse mal: `indices_desde_series` lo
    deja en None y `calcular_itvc` renormaliza sobre el resto de la dimensión.
    Antes esto era un `raise` sin captura —`aplicar_scoring` no lo envuelve—,
    así que una desalineación de un mes mataba la publicación nocturna entera.
    Y es alcanzable con ruido de infraestructura común: la card sale de un
    fetch corto y la serie de una descarga larga que, si expira, conserva las
    filas del mes anterior.

    Degradar en silencio sería el otro error (ver `sentimiento_digital`), así
    que el motivo queda en la card y G9 del gate lo levanta.
    """
    tarjeta = (c.get("indicadores") or {}).get("peso_tarifas")
    if not tarjeta:
        return series
    tarjeta.pop("desalineacion_serie", None)
    fecha = (tarjeta.get("fecha_dato") or "")[:7]
    puntos = [p for p in (series.get("itvc_tarifas") or [])
              if (p.get("fecha") or "")[:7] == fecha]
    motivo = None
    if not fecha or len(puntos) != 1:
        motivo = (f"card {fecha or 'sin fecha'} sin un único punto coincidente "
                  f"en itvc_tarifas")
    elif tarjeta.get("valor") is None or tarjeta.get("transporte_pct_canasta") is None:
        # Carry-forward desde un snapshot anterior a que la card llevara
        # desglose: `_carry_forward` sólo restaura los campos que el previo
        # tenía, así que el titular vuelve y el desglose no. Recalcular acá
        # reventaba con TypeError —`float(None)`— sobre exactamente los datos
        # para los que existe el texto de fórmula sin desglose, que por eso
        # era inalcanzable. El mes sí se pudo cotejar: alcanza para publicar.
        pass
    else:
        publicado = puntos[0].get("valor")
        piso, techo = _rango_indice_compatible_con_card(
            tarjeta.get("valor"), tarjeta.get("transporte_pct_canasta")
        )
        if publicado is None or not piso - 1e-9 <= float(publicado) <= techo + 1e-9:
            motivo = (f"índice de serie {publicado} fuera del rango "
                      f"[{piso}, {techo}] que admite la card")
    if motivo:
        tarjeta["desalineacion_serie"] = motivo
        print(f"[AVISO] peso_tarifas: {motivo}; el componente se omite del ITCIS "
              f"y la dimensión renormaliza", file=sys.stderr)
        degradada = dict(series)
        degradada.pop("itvc_tarifas", None)
        return degradada
    alineadas = dict(series)
    alineadas["itvc_tarifas"] = puntos
    return alineadas


def _scoring_vida_itvc(c, series):
    """Vida cotidiana se puntúa con el ITVC-B100: cada componente es un índice
    rebaseado a 100 = promedio 4T-2023, salvo tarifas (anclas externas por rubro),
    y se agrega con los pesos vigentes.
    La tensión del cinturón y el aporte por indicador usan el mapeo lineal
    5 − (índice − 100) × 0,2 (topeado a 0-10)."""
    from datetime import datetime as _dt
    series_indice = _series_tarifas_alineadas_con_card(c, series)
    indices = _itvc_indices(c["indicadores"], series_indice)
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
        _series_dimensiones(resultado, "itvc", base100=True)
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
            fecha_indice = _fecha_del_indice_itvc(ikey, series_indice)
            if fecha_indice:
                ind["fecha_indice_itvc"] = fecha_indice
            else:
                ind.pop("fecha_indice_itvc", None)
            ind["peso_efectivo"] = info["peso_efectivo"]
            if ikey in winsorizados:
                ind["indice_itvc_crudo"] = winsorizados[ikey]
                ind["recorte_itvc"] = round(winsorizados[ikey] - itvc.WINSOR_TOPE, 1)
            else:
                ind.pop("indice_itvc_crudo", None)
                ind.pop("recorte_itvc", None)
            # La exención actúa antes de los ajustes del analista. Mirar el
            # puntaje aplicado atribuiría falsamente al techo un override que
            # lo cruza por sí solo.
            if (ikey in itvc.WINSOR_EXENTOS
                    and info["puntaje_banda"] > itvc.WINSOR_TOPE):
                ind["winsor_exento"] = True
            else:
                ind.pop("winsor_exento", None)
            aporte = itvc.tension_de_itvc(info["puntaje_aplicado"])
            # tensión SIN topear: el 0 de un componente en mejora fuerte no es
            # "no incide" — es tensión negativa cortada por la escala, y hay
            # que decirlo (varios componentes distintos mostraban el mismo 0)
            cruda = round(5 - (info["puntaje_aplicado"] - 100) * 0.2, 1)
            if cruda < 0:
                lectura = (f"Este componente está en {coma(info['puntaje_aplicado'])} contra una "
                           f"base de 100: mejora tanto que no solo no suma tensión — empuja el "
                           f"índice del cinturón hacia arriba.")
            elif cruda > 10:
                lectura = (f"Este componente está en {_lectura_tension(aporte)}, más allá del "
                           f"tope de la escala: deterioro profundo contra el arranque del mandato.")
            else:
                lectura = (f"En la escala del cinturón, este componente está en "
                           f"{_lectura_tension(aporte)}.")
            # bases DECLARADAS distintas del 4T-2023 (fuente sin medición en la base del doc)
            base_lbl = {"inseguridad": "ene-2024 (base declarada conservada; archivo 2023 recuperado en septiembre de 2026)"} \
                .get(ikey, "4T-2023")
            formula = (f"Índice base-100 vs {base_lbl}: {coma(info['puntaje_aplicado'])} "
                       f"(100 = arranque del mandato; más = mejora); pesa "
                       f"{coma(round(info['peso_efectivo'] * 100, 1))}% del índice de impacto social.")
            if ikey == "peso_tarifas":
                carga = ind.get("valor")
                proporcion_t = ind.get("transporte_pct_canasta")
                carga_t = carga * proporcion_t / 100 if carga is not None and proporcion_t is not None else None
                carga_ae = carga - carga_t if carga is not None and carga_t is not None else None
                if carga_ae is not None and carga_t is not None:
                    formula = (f"Canasta de servicios públicos del Instituto Interdisciplinario de Economía "
                               f"Política sobre el salario registrado promedio: {coma(carga)}% = agua+energía "
                               f"{coma(round(carga_ae, 1))}% + transporte {coma(round(carga_t, 1))}%. "
                               f"Se toma la mayor tensión contra sus límites (10% y 5%): "
                               f"índice {coma(info['puntaje_aplicado'])}. "
                               f"Pesa {coma(round(info['peso_efectivo'] * 100, 1))}% del índice de impacto social.")
                    lectura = (f"Agua y energía representan {coma(round(carga_ae, 1))}% del salario; "
                               f"transporte, {coma(round(carga_t, 1))}%. La mayor de las dos "
                               f"señales fija el color: {_lectura_tension(aporte)}.")
                else:
                    formula = (f"Índice de asequibilidad por rubro: "
                               f"{coma(info['puntaje_aplicado'])}; pesa "
                               f"{coma(round(info['peso_efectivo'] * 100, 1))}% del índice de impacto social.")
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
#
# Se DERIVA de `itcm.INDICADORES_CONTEXTO`, como en política, gestión y vida.
# Era el único de los cuatro que repetía la lista como literal, y esa copia no
# es un detalle de estilo: un indicador que sale del score y entra a la lista
# del módulo se seguía publicando como card sin puntuar, que es justo lo que
# ADR-0153 y ADR-0216 prohíben y que vuelve por omisión —cae en el `else` de
# `_scoring_indice` y se lleva la nota de contexto—. Apareció el 25-ago-2026 al
# sacar `idm` e `icip` del índice: los dos habrían quedado visibles y mudos.
# `tests/test_ocultos_derivan_de_la_fuente.py` lo vigila para los cuatro.
MACRO_OCULTOS = set(itcm.INDICADORES_CONTEXTO)

# Indicadores de política OCULTOS del snapshot (ADR-0048, mismo criterio que
# ADR-0022): la revisión editorial los sacó del ITCP y el tablero solo
# muestra lo que integra las dimensiones. Siguen en la pipeline completa
# (colector, registro curado, cache y series) como seguimiento interno.
POLITICA_OCULTOS = set(itcp.INDICADORES_CONTEXTO) | set(itcp.INDICADORES_SUSPENDIDOS)

# Indicadores de gestión OCULTOS del snapshot (ADR-0051, cierra la regla de
# ADR-0048/0049 sobre el último cinturón que publicaba contexto visible): el
# tablero solo muestra lo que integra las dimensiones del ITCG. Colector,
# stores y series siguen corriendo como seguimiento interno (razones de no
# puntuar documentadas en itcg.INDICADORES_CONTEXTO).
#
# ADR-0189: se les suman los cumplidos y los suspendidos. ADR-0100 y ADR-0186
# los habían dejado visibles sin puntuar, cada uno con su propio estado; la
# revisión editorial de agosto de 2026 cerró la excepción y volvió a la regla
# de ADR-0051 sin casos especiales: si no puntúa, no se muestra — ni en el
# tablero ni en las fichas metodológicas, que salen de este mismo snapshot.
# Las constantes siguen existiendo: son las que documentan POR QUÉ no puntúan
# y las que `anotar_indicadores()` usa para sacarlos del cálculo.
GESTION_OCULTOS = (set(itcg.INDICADORES_CONTEXTO)
                   | set(itcg.INDICADORES_CUMPLIDOS)
                   | set(itcg.INDICADORES_SUSPENDIDOS))

# Indicadores de vida cotidiana OCULTOS del snapshot (ADR-0154, mismo criterio
# que ADR-0022): la revisión editorial los sacó del ITVC y el tablero solo
# muestra lo que integra las dimensiones. Series y colector siguen corriendo —
# `indice_lider` además pasó a ser el validador externo del ITCM, así que su
# serie es un insumo vivo de validacion_externa.py. Lo mismo desde ADR-0314
# con `icc_utdt`: sale del ITVC y pasa a ancla externa del ITCIS en
# validacion_externa.py — la misma regla que sacó a `indice_lider`: un
# indicador no puede ser componente y juez del mismo índice, y el que deja de
# ser componente no puede seguir siendo card.
#
# Es el quinto cinturón en tener lista de ocultos, y con eso los cinco usan el
# mismo patrón: entra al índice o se oculta. No hay cards de contexto (ADR-0153).
VIDA_OCULTOS = ({"endeudamiento_familiar", "indice_lider", "icc_utdt"}
                | set(itvc.INDICADORES_SUSPENDIDOS))


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
    bordes = [b for b in (actual["desde"], actual["hasta"]) if b is not None]
    if not bordes:
        return f"{coma(valor)} {unidad}: {color.capitalize()} en todo el rango."
    borde = min(bordes, key=lambda b: abs(valor - b))
    return (f"{coma(valor)} {unidad} cae en el tramo que corresponde a "
            f"{color.capitalize()}, a {coma(round(abs(valor - borde), 2))} "
            f"del corte más cercano.")


def _semaforo_de(color, tension, umbrales, unidad, valor):
    return {"color": color,
            "tension": None if tension is None else round(tension, 1),
            "umbrales": umbrales,
            "unidad": unidad,
            "por_que": _por_que(color, valor, unidad, umbrales)}


# Cómo se dice un tramo en los textos publicados. La web no muestra la tensión
# como número (ADR-0337): los textos nombran el color y su palabra, las mismas
# que `LECTURA_SEMAFORO` en web/src/lib/datos.ts.
_LECTURA_COLOR = {"verde": "sin tensión relevante", "amarillo": "tensión moderada",
                  "naranja": "tensión alta", "rojo": "tensión crítica"}


def _lectura_tension(tension) -> str:
    """«amarillo (tensión moderada)» para una tensión 0-10."""
    color = parametrica.color_de_tension(float(tension))
    return f"{color} ({_LECTURA_COLOR[color]})"


def _por_que_dimension(puntaje, tension, base100):
    """`por_que` de una DIMENSIÓN: no hay tabla de tramos como la de un
    indicador (ADR-0182) porque el puntaje de una dimensión YA está en la
    escala del semáforo -- 0-100, o el índice base-100 del ITVC -- no hay
    unidad cruda a la que traducir los cortes de CORTES_SEMAFORO. Los cortes
    en sí los explica `SemaforoLeyenda.astro`, presente en toda página que
    puede abrir este modal (home y detalle de cinturón); esta frase solo ata
    el puntaje concreto de la dimensión a la tensión que produce su color,
    en vez de dejar el bloque en blanco como si no hubiera nada que decir.
    """
    etiqueta = "El índice de la dimensión" if base100 else "El puntaje de la dimensión"
    sufijo = "" if base100 else "/100"
    return (f"{etiqueta}, {coma(round(float(puntaje), 1))}{sufijo}, está en "
            f"{_lectura_tension(tension)} en la escala del informe.")


# Referencia descriptiva del nivel de consumo aparente (BCR, promedio de diez
# años). No es un corte del puntaje ni permite deducir la variación interanual.
CARNES_TOTAL_REFERENCIA = 112.8


def _snic_desglose_txt(tipos_principales: dict) -> str:
    """"; Homicidios dolosos: 1.613; Robos: 360.946" — el desglose del SNIC
    por tipo de delito (ADR-0324/0325), tal como lo devuelve
    `snic._parse_snic_csv` en `tipos_principales`.

    Antes este dict se calculaba, se guardaba en el snapshot interno del
    colector y no lo leía nadie río abajo (ni `publicar.py`, ni `web/src`,
    ni el sitio construido): los homicidios se bajaban del CSV oficial y se
    tiraban en la cañería antes de llegar al lector. Esta función es lo que
    hace que sí lleguen, colgados del contraste SNIC que ya se publica en el
    detalle de `inseguridad`.
    """
    if not tipos_principales:
        return ""
    partes = "; ".join(
        f"{nombre}: {format(int(cant), ',').replace(',', '.')}"
        for nombre, cant in tipos_principales.items()
    )
    return f". Por tipo: {partes}"


def _por_que_carne(ikey, vacuna, otras, total, variaciones):
    """Nivel, variación y composición agregados; no identifica trayectorias.

    El color usa la evolución de faena per cápita contra 4T-2023. El consumo
    aparente oficial y su referencia histórica se explican como contexto.

    Las dos cards que puntúan (`consumo_carnes_total` y `consumo_carne_vacuna`,
    ADR-0339) comparten los mismos números, pero el párrafo de cada una habla
    de SU nivel: el total cuenta la composición de las tres carnes, la vacuna
    su nivel contra ese total.
    """
    import math

    var_v = (variaciones or {}).get("vacuna")
    var_t = (variaciones or {}).get("total")
    var_a = (variaciones or {}).get("aviar")
    var_p = (variaciones or {}).get("porcina")
    valores = (vacuna, otras, total, var_v, var_t)
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in valores):
        return None
    if total <= 0 or vacuna < 0 or otras < 0 or vacuna > total:
        return None

    ratio_vacuna = vacuna / total * 100
    ratio_otras = 100 - ratio_vacuna
    posicion = ("por encima de" if total > CARNES_TOTAL_REFERENCIA else
                "por debajo de" if total < CARNES_TOTAL_REFERENCIA else "igual a")
    nivel_total = (f"{coma(round(total, 1))} kg por habitante y año "
                   f"({coma(round(var_t, 1))}% interanual)")
    referencia = (f"El nivel total está {posicion} la referencia histórica de "
                  f"{coma(CARNES_TOTAL_REFERENCIA)} kg; esa comparación no indica si "
                  f"subió o bajó respecto del año anterior.")
    contexto_total = f"total de las tres carnes, {nivel_total}. {referencia}"
    cierre = (" Estos agregados no identifican sustitución dentro de los "
              "mismos hogares ni proteína ingerida. El color y el aporte al "
              "índice usan la evolución de faena por habitante frente a "
              "4T-2023, no esta comparación de consumo aparente con el "
              "promedio histórico.")

    if ikey == "consumo_carne_vacuna":
        cuerpo = (
            f"Consumo aparente de carne vacuna: {coma(round(vacuna, 1))} kg "
            f"por habitante y año ({coma(round(var_v, 1))}% interanual), el "
            f"{coma(round(ratio_vacuna, 1))}% del {contexto_total} El resto "
            f"(aviar + porcina) suma {coma(round(otras, 1))} kg, el "
            f"{coma(round(ratio_otras, 1))}% restante.")
    else:
        var_a_txt = f"{coma(round(var_a, 1))}%" if isinstance(var_a, (int, float)) else "s/d"
        var_p_txt = f"{coma(round(var_p, 1))}%" if isinstance(var_p, (int, float)) else "s/d"
        cuerpo = (
            f"Consumo aparente de las tres carnes: {nivel_total}. {referencia} La carne "
            f"vacuna aporta {coma(round(vacuna, 1))} kg, el "
            f"{coma(round(ratio_vacuna, 1))}%, y se sigue además como indicador "
            f"propio; aviar y porcina suman {coma(round(otras, 1))} kg, el "
            f"{coma(round(ratio_otras, 1))}% (aviar {var_a_txt} y porcina "
            f"{var_p_txt} interanual).")
    return cuerpo + cierre


def _por_que_motorizacion(composicion):
    """La matriz A×B de la ficha de motorización, dicha en una frase.

    La ficha quiere distinguir dos cosas que el patentamiento de motos solo no
    puede separar, y que fueron el desacuerdo editorial que originó ADR-0224:

    - que la gente pase del auto a la moto porque no sostiene el auto
      (sustitución descendente, empobrecimiento), o
    - que compre su primera moto sin haber tenido nunca un auto (acceso).

    Las dos empujan el patentamiento de motos hacia arriba. El total y la mezcla
    describen el flujo agregado, pero NO identifican compradores ni transiciones
    de hogares: acceso, reposición y sustitución pueden coexistir (ADR-0271).

    Esto NO cambia el color ni el aporte al índice —el color sale del nivel
    rebaseado, como en toda card del cinturón—; entra como el `por_que`, que es
    el campo que explica un color. Mismo criterio que `_por_que_carne`.
    """
    if not composicion:
        return None
    ratio = composicion.get("ratio_motos")
    ratio_base = composicion.get("ratio_motos_base")
    var_t = composicion.get("total_var")
    var_a = composicion.get("autos_var")
    var_m = composicion.get("motos_var")
    if None in (ratio, ratio_base, var_t, var_a, var_m):
        return None

    corrimiento = ratio - ratio_base
    # Control pedido por Juan (15-sep, ADR-0322): motos/autos, no motos/total.
    # Es la magnitud que separa "sube la motorización porque se compran más
    # autos" de "sube porque se baja a la moto" — algo que `ratio` (motos
    # sobre el TOTAL) no distingue de un total que crece parejo en las dos
    # patas. Opcional: series viejas pueden no tenerlo todavía cacheado.
    ratio_ma = composicion.get("ratio_motos_autos")
    ratio_ma_base = composicion.get("ratio_motos_autos_base")
    texto_ratio_ma = ""
    if ratio_ma is not None and ratio_ma_base is not None:
        texto_ratio_ma = (
            f". Por cada auto patentado se patentan {coma(round(ratio_ma, 2))} "
            f"motos, contra {coma(round(ratio_ma_base, 2))} al arranque del "
            f"mandato")
    # En millones el total y en miles las dos patas: "1352 mil vehículos" es
    # un número que nadie dice en voz alta.
    base = (f"en los últimos doce meses se patentaron "
            f"{coma(round(composicion['total_12m'] / 1_000_000, 2))} millones de "
            f"vehículos 0 km ({coma(round(var_t, 1))}% interanual): "
            f"{coma(round(composicion['autos_12m'] / 1000))} mil autos "
            f"({coma(round(var_a, 1))}%) y "
            f"{coma(round(composicion['motos_12m'] / 1000))} mil motos "
            f"({coma(round(var_m, 1))}%). Las motos son el "
            f"{coma(round(ratio, 1))}% de lo que se patenta, contra "
            f"{coma(round(ratio_base, 1))}% al arranque del mandato"
            f"{texto_ratio_ma}")

    sube_total = var_t > 0
    mas_motos = corrimiento > 0

    if sube_total and mas_motos:
        lectura = "Más patentamientos y mayor participación de motos"
    if not sube_total and mas_motos:
        lectura = ("Menos patentamientos y mayor participación de motos" if var_t < 0
                   else "Total estable y mayor participación de motos")
    if sube_total and not mas_motos:
        lectura = "Más patentamientos, sin aumento de la participación de motos"
    if not sube_total and not mas_motos:
        lectura = ("Menos patentamientos, sin aumento de la participación de motos" if var_t < 0
                   else "Total estable, sin aumento de la participación de motos")
    return (f"{lectura}: {base}. El registro cuenta vehículos, no hogares: "
            "no permite distinguir primeras compras, reposición, flotas ni "
            "sustitución entre autos y motos. Estas situaciones pueden coexistir.")


def _semaforos(informe):
    """Adjunta el bloque `semaforo` a cada indicador, dimensión e índice."""
    for cinturon, bloque in informe["cinturones"].items():
        clave, mod, sigla = _ESCALAS_SEMAFORO.get(cinturon, (None, None, None))
        escala = _escala_de(mod, sigla) if mod else None

        for ikey, ind in bloque["indicadores"].items():
            idx100 = ind.get("indice_itvc")
            p = ind.get(f"puntaje_{clave}") if clave else None
            if isinstance(p, (int, float)) and ind.get("en_indice"):
                tension = parametrica.tension_de_puntaje(float(p))
                color = parametrica.color_de_puntaje(float(p))
                umbrales = parametrica.umbrales_en_unidad(ikey, escala)
                unidad = ind.get("unidad")
            elif isinstance(idx100, (int, float)):
                # El COLOR usa la tensión cruda (sin acotar): es lo que hace
                # que 0/10 en un componente lea "empujó el índice hacia
                # arriba" en vez de "no aporta" (ver _scoring_vida_itvc). La
                # TENSIÓN PUBLICADA sí se acota a [0, 10] — es la misma
                # convención 0-10 que usa el resto del informe, y
                # itvc.tension_de_itvc ya hace exactamente ese corte.
                tension = itvc.tension_de_itvc(float(idx100))
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
            # El consumo aparente y su composición dan contexto agregado.
            # El texto distingue ese contexto del color basado en faena.
            # ADR-0339: las dos cards que puntúan (el total y la vacuna) leen
            # los mismos números; cada una cuenta su parte.
            if ikey in ("consumo_carne_vacuna", "consumo_carnes_total"):
                vacuna_ind = bloque["indicadores"].get("consumo_carne_vacuna") or {}
                total_ind = bloque["indicadores"].get("consumo_carnes_total") or {}
                por_que = _por_que_carne(ikey, vacuna_ind.get("valor"), total_ind.get("otras_kg"),
                                         total_ind.get("valor"), ind.get("variaciones"))
                if por_que:
                    ind["semaforo"]["por_que"] = por_que
            # Lo mismo para la motorización (ADR-0224): el color dice "subió
            # contra el arranque" y nada más, que es justo la lectura ambigua
            # que el editorial discutía. La matriz A×B no lo cambia: lo explica.
            if ikey == "motorizacion_total":
                por_que = _por_que_motorizacion(ind.get("composicion"))
                if por_que:
                    ind["semaforo"]["por_que"] = por_que

        indice_key = _INDICE_DE_CINTURON.get(cinturon)
        if not indice_key:
            continue
        indice = bloque.get(indice_key)
        if not indice:
            continue
        base100 = indice_key == "itvc"
        color_idx = (parametrica.color_de_indice_base100 if base100
                     else parametrica.color_de_puntaje)
        indice["semaforo"] = {"color": color_idx(indice["valor"]),
                              "umbrales": None, "unidad": None, "por_que": None,
                              "tension": None}
        # A diferencia del índice de arriba (que ningún modal muestra hoy),
        # la dimensión SÍ tiene un modal propio (revisión de coherencia UI,
        # ago-2026: el de indicador nombraba el color en texto, el de
        # dimensión solo lo pintaba) -- por eso acá sí vale la pena la
        # tensión y el "por qué", y en el índice no. El puntaje de una
        # dimensión ya vive en la escala del semáforo (0-100, o el índice
        # base-100 del ITVC), así que no hace falta -ni existe- una tabla de
        # tramos en unidad cruda como la de un indicador: `umbrales` y
        # `unidad` siguen en None.
        for dim in indice.get("dimensiones", {}).values():
            puntaje_dim = float(dim["puntaje"])
            tension_dim = (itvc.tension_de_itvc(puntaje_dim) if base100
                           else round(parametrica.tension_de_puntaje(puntaje_dim), 1))
            dim["semaforo"] = {
                "color": color_idx(puntaje_dim),
                "umbrales": None, "unidad": None,
                "por_que": _por_que_dimension(puntaje_dim, tension_dim, base100),
                "tension": tension_dim,
            }

    # Cortes de CORTES_SEMAFORO expuestos en el snapshot (Tanda A, revisión de
    # coherencia de la UI, ago-2026): la leyenda web arma su texto ("tensión
    # ≤ 4", "tensión ≤ 6"...) leyendo esto, en vez de tener los números
    # escritos a mano y desincronizables. `hasta=None` es el equivalente
    # serializable de parametrica.INF (rojo no tiene techo) — JSON no
    # tiene infinito.
    informe["semaforo_cortes"] = [
        {"color": color, "hasta": None if tope == parametrica.INF else tope}
        for color, tope in parametrica.CORTES_SEMAFORO
    ]


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
                    lectura = (f"Entra al promedio del cinturón en {_lectura_tension(aporte)}." +
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

    # REGLA (ADR-0153/0216): o integra el índice, o no es card.
    #
    # ADR-0339: puntúan el total de las tres carnes y la vacuna; las DOS son
    # cards. Aviar + porcina no tiene `_add` (su nivel viaja en `otras_kg` del
    # total), así que no hace falta popearla.
    #
    # ADR-0224: la motorización sigue con el patrón viejo. El que puntúa es
    # el total; autos y motos son los Componentes A y B de su matriz A×B, o sea
    # diagnóstico, y su valor se lee ahí adentro. Se descarta DESPUÉS de
    # `_semaforos` porque la matriz los lee ahí: sacarlos antes deja al total
    # sin su explicación y nada falla en voz alta — probado con VIDA_OCULTOS,
    # el `por_que` quedó vacío y el gate pasó. Su composición viaja colgada
    # del propio total, así que no depende del orden de este `pop` como sí
    # dependía la carne antes de ADR-0322.
    vida = informe["cinturones"].get("vida_cotidiana", {})
    for descartada in ("patentamiento_autos", "patentamiento_motos"):
        vida.get("indicadores", {}).pop(descartada, None)
    return informe


# Procedencia de los insumos que no son íntegramente automáticos. El default
# es automático porque ése es el contrato de los colectores; las excepciones
# viven acá para que el snapshot —y no una heurística de la UI— diga cómo se
# obtuvo cada dato. "Semiautomático" significa detección automática con una
# clasificación humana necesaria para que el valor avance.
METODO_OBTENCION_EXCEPCIONES = {
    "apoyo_empresario": "semiautomatico",
    # CSV automático conciliado con movimientos y bajas de revisión humana.
    "cobertura_judicial": "semiautomatico",
    # Los dos leen el mismo registro legislativo: las actas inequívocas se
    # clasifican solas y las ambiguas no avanzan hasta el triage humano.
    "desafios_legislativos": "semiautomatico",
    # bloqueo_sostenido comparte el registro pero salió del tablero (ADR-0330,
    # ver POLITICA_OCULTOS) — no se publica, así que no necesita excepción acá
    # (mismo criterio que derrotas_legislativas, comisiones_caidas, etc.).
    # El anuario de la Corte se releva una vez por año sin extractor.
    "velocidad_resolucion": "manual",
    # Detectan novedades automáticamente, pero el dato sólo incorpora los
    # hechos asentados o clasificados por una persona en el registro curado.
    "reestructuracion_organismos": "semiautomatico",
    "fal_modernizacion_laboral": "semiautomatico",
    "protocolo_antipiquetes": "semiautomatico",
    "privatizaciones": "manual",
}


def anotar_metodo_obtencion(informe):
    """Adjunta a cada indicador la procedencia que debe declarar la web."""
    for cinturon in informe.get("cinturones", {}).values():
        for clave, indicador in cinturon.get("indicadores", {}).items():
            indicador["metodo_obtencion"] = METODO_OBTENCION_EXCEPCIONES.get(
                clave, "automatico")
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


def _sellar_vida(indicadores, raw):
    """Sella cuándo se obtuvo en vivo cada indicador de vida (ADR-0191).

    Vida no pasa por el patrón `frescos`/cache de los otros cinturones: el
    colector escribe un JSON crudo por corrida y acá se reconstruyen las cards.
    El sello sale del `metadata.timestamp` de ESE archivo, no de `datetime.now()`,
    porque si el colector no corrió hoy la card se rearma igual desde el crudo
    viejo — y sellarla con la hora de esta corrida diría que es fresca cuando no
    lo es. Los indicadores que se agregan después de acá (mora_familias, que sale
    de la serie y no del crudo) quedan sin sello a propósito: su frescura la
    controla G3 contra la serie, no este chequeo.
    """
    sello = (raw.get("metadata", {}) or {}).get("timestamp") or ""
    if not sello:
        return indicadores
    for ind in indicadores.values():
        if ind.get("valor") is not None:
            ind["obtenido_en"] = ind.get("obtenido_en") or sello
    return indicadores


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
            # El sello viejo se arrastra SIN tocar: es la fecha que deja de
            # moverse la que mide hace cuánto que la fuente no contesta.
            if prev.get("obtenido_en"):
                ind["obtenido_en"] = prev["obtenido_en"]
            # Insumos que forman el score tarifario. Restaurar sólo el titular
            # mezclaría 14,5% viejo con un desglose nulo/nuevo y la fórmula ya
            # no reproduciría el punto que entra al índice.
            if key == "peso_tarifas":
                for campo in ("variacion_mensual_pct", "cobertura_costos_pct",
                              "transporte_pct_canasta", "fuente_url"):
                    if campo in prev:
                        ind[campo] = prev[campo]
            print(f"[carry-forward] vida.{key}: sin dato nuevo, se mantiene {prev.get('valor')} ({prev.get('fecha_dato')})")
    return enriquecido


def _elegir_crudo_vida(vida_files, fuente_previa=None):
    """El crudo local nunca puede hacer retroceder el bloque ya publicado.

    **El nombre NO ordena cronológicamente entre máquinas**, y eso costó una
    corrida (2026-08-21). Lleva `YYYYMMDD_HHMM` en la hora LOCAL de quien lo
    escribió: la CI corre en UTC y la Mac en hora argentina, tres horas atrás.
    Una corrida manual de las 12:06 ART —que son las 15:06 UTC— produce
    `..._1206.json` y pierde el orden alfabético contra el `..._1408.json` que
    el nocturno escribió 58 minutos ANTES. El timestamp de adentro del archivo
    tiene el mismo defecto: es hora local sin zona.

    Lo que pasa cuando se elige mal no es un error visible: se publica el crudo
    del cron creyendo que es el de la corrida manual. Ese día se notó sólo
    porque la corrida agregaba un indicador nuevo y el gate lo vio faltar (G1,
    sin fecha_dato). Sin un indicador nuevo, habría pasado en silencio.

    Se ordena entonces por **mtime**, que es lo único que dice qué archivo se
    escribió último en ESTA máquina, y se desempata por nombre para que dos
    archivos con la misma marca queden en orden estable. Sigue en pie el
    resguardo de más arriba: si el snapshot previo declara un crudo más nuevo
    que todos los presentes, no se publica.
    """
    if not vida_files:
        return None
    candidato = Path(max(vida_files, key=lambda f: (Path(f).stat().st_mtime, f)))
    if not fuente_previa:
        return candidato
    # El resguardo se compara por mtime igual que la elección. Comparándolo por
    # NOMBRE —como estaba— rechazaba el crudo recién escrito a mano por ser
    # alfabéticamente menor que el del nocturno, y arrastraba el bloque
    # anterior: la corrida manual "publicaba" y no cambiaba nada.
    anterior = candidato.parent / os.path.basename(fuente_previa)
    if not anterior.exists():
        # El crudo que declara el snapshot previo no llegó a esta máquina, así
        # que no hay con qué comparar y publicar el disponible podría pisar
        # datos frescos con viejos. Se corta, que es el motivo del resguardo.
        return None
    return candidato if candidato.stat().st_mtime >= anterior.stat().st_mtime else None


def main():
    informe = json.loads((OUT / "informe.json").read_text(encoding="utf-8"))
    series = build_series()

    # Snapshot publicado anterior → fuente para carry-forward ante outages.
    prev_vida, prev_vida_block = {}, None
    prev_path = DATA / "informe.json"
    if prev_path.exists():
        try:
            prev_snap = json.loads(prev_path.read_text(encoding="utf-8"))
            prev_vida_block = prev_snap["cinturones"]["vida_cotidiana"]
            prev_vida = prev_vida_block["indicadores"]
        except (json.JSONDecodeError, KeyError):
            prev_vida = {}

    vida_files = sorted(glob.glob(str(ROOT / "scripts" / "vida_cotidiana" / "data" / "vida_cotidiana_*.json")))
    fuente_previa = (prev_vida_block or {}).get("fuente_enriquecida")
    vida_path = _elegir_crudo_vida(vida_files, fuente_previa)
    if vida_path is None and prev_vida_block and vida_files:
        informe["cinturones"]["vida_cotidiana"] = prev_vida_block
        print(f"[carry-forward] vida: el crudo local más nuevo "
              f"({Path(vida_files[-1]).name}) es anterior al publicado "
              f"({fuente_previa}); se preserva el bloque publicado")
    elif vida_path:
        raw = json.loads(vida_path.read_text(encoding="utf-8"))
        enriquecido = build_vida(raw)
        if enriquecido:
            enriquecido = _sellar_vida(enriquecido, raw)
            enriquecido = _carry_forward(enriquecido, prev_vida)
            vida = informe["cinturones"]["vida_cotidiana"]
            vida["indicadores"] = enriquecido
            vida["fuente_enriquecida"] = vida_path.name
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
            # Carga del servicio de deuda (ADR-0231): segunda pata de
            # vulnerabilidad. La planilla del IEF contiene una serie mensual,
            # aunque el BCRA la libera por lotes semestrales; por eso el dato
            # se fecha con el último mes observado y no con la publicación.
            agregar_carga_servicio_deuda(enriquecido, series)
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
                    # ADR-0325/0324: el desglose por tipo del SNIC (homicidios,
                    # robos, hurtos, etc.) se descargaba y se guardaba en
                    # `tipos_principales`, pero nada lo leía río abajo —
                    # nunca llegaba al lector, sólo al snapshot interno del
                    # colector. Se suma acá, al mismo contraste anual que ya
                    # se publica, en vez de convertirlo en indicador nuevo
                    # que puntúe (fuera de alcance: es anual, con ~8,5 meses
                    # de rezago desde el cierre del año).
                    tipos_snic = ((raw.get("snic") or {}).get("inseguridad_snic") or {}).get(
                        "tipos_principales") or {}
                    snic_txt += _snic_desglose_txt(tipos_snic)
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
    informe = anotar_metodo_obtencion(informe)
    informe = aplicar_scoring(informe, series)
    informe = recomputar_vida_y_global(informe)
    informe = recomputar_barbarismo(informe)   # sobre los scores ya finales
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

    # Sólo al publicar de verdad: con CIGOB_SALIDA_WEB los tests corren este
    # script fuera del árbol (ADR-0178) y tocar output/ acá lo ensuciaría igual,
    # que es exactamente el defecto que aquel ADR arregló.
    if not os.environ.get("CIGOB_SALIDA_WEB"):
        _reconciliar_intermedio(informe)


if __name__ == "__main__":
    main()
