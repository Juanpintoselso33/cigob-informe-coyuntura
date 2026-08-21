"""Gate de calidad del snapshot — corre en el pipeline nocturno ANTES de
publicar al dominio. Si falla, el workflow se corta y producción sigue
sirviendo el snapshot anterior (que ya pasó su gate).

Gates (ver docs/arquitectura/05-operaciones.md):
  G1 Estructura   — todo indicador publicado con valor/fecha/fuente/unidad;
                    todo cinturón con score 0-10.
  G2 Frescura     — rezago máximo por indicador (calibrado a la cadencia real
                    de cada fuente) + presupuesto de carry-forward por
                    cinturón (≤40% de indicadores desactualizados).
  G3 Invariante   — el último punto de la serie coincide con el titular de la
                    card (la desincronización serie↔titular del IdC de
                    jul-2026 motivó este gate). Excepciones DECLARADAS para
                    los pares card/serie con semántica distinta.
  G6 Editorial    — cero jerga interna en los textos del snapshot (números de
                    ADR, IDs de serie de datos.gob.ar).

G4 (reconciliación paramétrica) y G5 (robustez encierra el valor) son los
pytest de tests/ — el workflow los corre como paso aparte.

Uso: python scripts/gate_calidad.py [--warn-only] [--snapshot <dir>]
                                    [--validacion <archivo>]
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import (DIAS_SIN_FETCH, DIAS_SIN_FETCH_DEFAULT,  # noqa: E402
                    cache_es_esperable)
SNAPSHOT = (Path(sys.argv[sys.argv.index("--snapshot") + 1])
            if "--snapshot" in sys.argv else ROOT / "web" / "src" / "data")
# Las anclas de validación no viven en el snapshot publicado sino en la salida
# de validacion_externa.py. Inyectable por la misma razón que SNAPSHOT: para
# poder testear G7 sin depender de la última corrida real.
VALIDACION = (Path(sys.argv[sys.argv.index("--validacion") + 1])
              if "--validacion" in sys.argv
              else ROOT / "output" / "validacion_externa.json")

# ── G2: rezago máximo en días por indicador (default: mensual con margen) ──
MAX_DIAS_DEFAULT = 110
MAX_DIAS = {
    # trimestrales EPH (fecha = inicio del trimestre, publica ~70d después del cierre)
    "informalidad": 280, "pluriempleo": 280,
    # SIPA: son declaraciones de las empresas que se consolidan y se revisan,
    # con ~3 meses de rezago estructural (ADR-0130). 150 días deja margen sobre
    # ese ritmo sin dejar de avisar si la fuente se muere de verdad.
    "empleo_registrado": 150,
    # fuentes con rezago estructural largo
    # ANUAL: la serie RON de Hacienda es por año calendario ejecutado y el
    # archivo del año nuevo aparece bien entrado el año siguiente. La fecha del
    # dato es el cierre del año de referencia (31-dic), así que el rezago crece
    # todo el año hasta que se publica el archivo siguiente: 560 días cubre ese
    # ciclo completo sin dejar de avisar si la fuente se muere de verdad. Hasta
    # el 29-jul-2026 la card declaraba `date.today()` y este tope no existía
    # porque el indicador se mostraba fresco siempre.
    "iaf_transferencias": 560,
    # ANUALES del bloque judicial (ADR-0168). Sin tope propio, un indicador
    # anual queda marcado como desactualizado siempre, que es exactamente el
    # falso positivo que ADR-0133 separó de una falla de integridad.
    # velocidad_resolucion: el anuario del año N sale bien entrado N+1, y la
    # fecha del dato es el cierre del año de referencia — mismo ciclo que
    # iaf_transferencias.
    "velocidad_resolucion": 560,
    # judicializacion: el punto del año en curso se recalcula en cada corrida y
    # se fecha al 1-ene de ese año, así que el rezago crece hasta 365 días antes
    # de que aparezca el punto siguiente. 430 cubre el ciclo con margen.
    "judicializacion": 430,
    "protocolo_antipiquetes": 430,      # DP publica monitoreos esporádicos
    "litigiosidad_laboral": 220,        # SRT
    "libertad_opcion_salud": 220,       # SSS
    # mensuales con ~2-3 meses de rezago de publicación
    "emae_ia": 140, "iai": 140, "icip": 140, "brecha_salario_cbt": 150,
    # ADR-0218: la SRT publica con ~3 meses de rezago (verificado: en agosto
    # de 2026 el último dato era mayo). El tope de 140 venía del IPI, que es
    # más rápido; con esta fuente dejaría menos de un mes de margen.
    "mortalidad_pymes": 165, "despacho_cemento": 140, "consumo_carne": 140,
    # SIPA publica con el mismo rezago de ~3 meses que la SRT (ADR-0219).
    "trabajo_independiente": 165,
    # DNRPA (ADR-0223). El rezago está MEDIDO sobre el historial de
    # actualizaciones del catálogo, no copiado de ningún documento: el mes M
    # aparece entre el día 1 y el 4 de M+1 (sep-2025 a ago-2026), con un solo
    # caso más tardío, el 13-mar-2026. Es dato registral, no una encuesta.
    # Con esa cadencia la card nunca pasa de ~72 días de antigüedad; 90 es el
    # punto donde una publicación se corrió más allá del mes siguiente entero,
    # o sea un mes salteado, que es justo lo que el tope tiene que agarrar.
    # ADR-0224: el tope pasa al componente que quedó. Es el MISMO número y por
    # la misma medición —los dos registros de la DNRPA publican con la misma
    # cadencia y el colector exige que lleguen al mismo mes—, así que el tope
    # de autos vale para la suma sin recalibrar nada.
    "motorizacion_total": 90,
    "endeudamiento_familiar": 140, "inseguridad": 150,
}
CARRY_FORWARD_MAX = 0.40                # tope de desactualizados por cinturón

# ── G2b: días máximos SIN un fetch exitoso, por indicador (ADR-0191) ──────────
# G2 mide el rezago del DATO (`fecha_dato`). G2b mide el rezago del FETCH
# (`obtenido_en`, que sella el colector sólo cuando la fuente contestó). Son
# cosas distintas y G2 solo no alcanza: en una serie anual `fecha_dato` no se
# mueve aunque el fetch ande perfecto, así que su tope tiene que ser generoso
# —judicializacion tiene 430 días— y esa misma holgura tapa que la fuente lleve
# meses sin contestar. Pasó: judicializacion estuvo 12 días en carry-forward
# desde el 31-jul-2026 sin que nada fallara, y se encontró mirando a mano.
#
# Un indicador SIN `obtenido_en` se saltea: son los manuales y los derivados de
# series, que no tienen fetch propio que medir. El campo aparece la primera vez
# que el indicador se obtiene bien, así que el chequeo se enciende solo.
#
# El default es 14 días y no 30 porque el sello mide el FETCH, no el dato: una
# fuente mensual igual se consulta todas las noches y renueva su sello aunque
# devuelva el mismo valor. O sea que 14 días sin un fetch exitoso ya es una
# fuente caída, no un dato que todavía no salió. Se deja margen para un outage
# de una semana larga sin cortar la publicación por algo que se va a recuperar
# solo (CONTRAT.AR y CAFAM fallan de a ratos y vuelven).
# La tabla se mudó a `config.py` (ADR-0210): la comparten el gate y
# `generar_informe.py`, que arma los `flags` del snapshot con el mismo
# criterio. Acá sólo se consume.
G2B_MAX_DIAS_DEFAULT = DIAS_SIN_FETCH_DEFAULT
G2B_MAX_DIAS = DIAS_SIN_FETCH

# ── G3: pares card/serie con semántica DISTINTA (excepción con motivo) ──
G3_EXCEPCIONES = {
    "sentimiento_digital": "card = pulso 3m en tiempo real; serie = canasta mensual ventana fija (ADR-0034)",
    "rigi_inversiones": "card = % de la meta; serie = monto acumulado en M USD",
    "protestas_caba": "card = eventos acumulados 12m; serie = eventos semanales",
    "cepo_mulc": "card = brecha CCL/mayorista SPOT del día; serie = brecha entre el PROMEDIO MENSUAL del CCL y el promedio mensual del A3500 (fetch_brecha_serie). No es un problema de anclaje sino de estadístico: un promedio mensual no puede igualar un spot diario en una serie que oscila ±30% m/m, y acercar las anclas no lo arreglaría. La tolerancia especial del 10% que hubo acá falló el 16-jul-2026 (11,5%) y ese mismo día el par pasaba por 0,02 de margen: era un parche que iba a fallar todos los meses volátiles. La frescura de la serie la sigue vigilando G3b (reclasificado 2026-08-05: hasta ADR-0172 estaba anotado como 'misma familia de anclaje que votometro/derrotas', que era un diagnóstico equivocado)",
    # ADR-0217: la card publica el NIVEL per cápita oficial que informa SAGYP
    # (kg/hab/año, el número que le sirve al lector); la serie es el ÍNDICE
    # base 100 = 4T-2023 reconstruido desde la faena del INDEC, que es lo
    # único que tiene historia para rebasear. Miden lo mismo en dos unidades
    # y desde dos fuentes, así que nunca van a coincidir por construcción.
    # NO es un caso de anclaje: que las dos fuentes no se separen lo vigila
    # tests/test_carne_compuesto.py contra la variación i.a. que publica SAGYP.
    "consumo_carnes_total": "card = nivel kg/hab (SAGYP); serie = índice base-100 desde faena INDEC (ADR-0217)",
    # ADR-0224: la card publica el NIVEL —vehículos 0km por cada mil
    # habitantes, que es el número con significado para el lector— y la serie
    # el ÍNDICE base 100 = 4T-2023, que es lo que puntúa. A diferencia de la
    # carne, acá NO hay dos fuentes: las dos salen de la misma descarga de la
    # DNRPA y de la misma serie de población del INDEC, así que no pueden
    # separarse. Es sólo un cambio de unidad, y por eso el par no coincide.
    "motorizacion_total": "card = vehículos 0km por mil habitantes; serie = índice base-100, misma fuente (ADR-0224)",
    # Acá vivía la FAMILIA DE ANCLAJE: siete indicadores perdonados porque la
    # card evaluaba su ventana en date.today() y la serie a fin de mes cerrado.
    # Ya no queda ninguno. ADR-0172 les puso a las series un punto final
    # anclado a HOY, así que card y serie miran la MISMA ventana y coinciden
    # por construcción, sin tolerancia:
    #
    #   veto_quorum 10,0=10,0 · derrotas_legislativas 3=3
    #   bloqueo_sostenido 33,3=33,3 · desafios_legislativos 3,0=3,0
    #   alineamiento_senadores_prov 70,6=70,6 · cohesion_bloque 99,8=99,8
    #   votometro_ventaja_lla 4,0=4,0
    #
    # Los siete volvieron a estar bajo vigilancia de G3, que es de lo que nunca
    # deberían haber salido: el waiver tapaba una contradicción real
    # (desafios_legislativos publicaba 3 en el titular y 10 en el último punto
    # del gráfico, 90 contra 43,6 de puntaje) y hacía falta un test distinto,
    # en otro paso del pipeline, para que se viera.
    #
    # Si algún día vuelve a aparecer un par card/serie que no coincide por
    # anclaje, la salida NO es agregarlo acá: es alinear las anclas.
}
# tolerancia relativa por indicador (default 1% o 0,11 absoluto, redondeos)
G3_TOLERANCIA_REL = {}   # (cepo_mulc tuvo 0.10 acá hasta 2026-07-16 — hoy es excepción G3)

# G3b: tope de rezago propio de la SERIE cuando difiere del de la card. Las
# series de eventos esporádicos pueden pasar meses sin punto nuevo aunque el
# colector siga vivo — el default (MAX_DIAS de la card) les daría falso
# positivo.
G3B_MAX_DIAS = {
    "rigi_inversiones": 430,   # solo suma un punto cuando se aprueba un proyecto
}

# ── G7: anclas de la validación externa (ADR-0176) ────────────────────────────
# Las series que sólo son INSUMO de validación no tenían quién las vigilara: G2
# mira la fecha_dato de las cards y G3/G3b los pares card↔serie, y un ancla
# externa no es indicador de ningún cinturón. El ICG de la UTDT estuvo congelado
# —su fetcher levantaba NameError en cada corrida— y siguió entrando al factor
# común con su última observación vieja, publicando correlaciones como si nada.
# Lo encontró un aviso lateral que se agregó para otra cosa (ADR-0175), no un
# chequeo.
#
# Topes calibrados contra el rezago REAL observado el 5-ago-2026, con margen:
# consumo INDEC iba en 2-3 meses, EPU/ICG/Índice Líder en ~65 días, Merval y
# clima electoral al mes en curso.
# Días sin publicar un período NUEVO. Es el chequeo sensible: el rezago
# absoluto de abajo mezcla el atraso inherente de la fuente con el
# congelamiento, así que su tope tiene que ser generoso y tarda meses en
# avisar. Todas las anclas del panel son mensuales, así que avanzar cada ~31
# días es lo sano y 80 deja pasar dos publicaciones salteadas antes de hablar.
G7_MAX_SIN_AVANZAR = 80
G7_MAX_DIAS_DEFAULT = 150
G7_MAX_DIAS = {
    "merval_usd": 45,                       # mercado, cierra todos los meses
    "clima_electoral": 75,                  # Votómetro, mensual propio
    "consumo_supermercados": 190,           # INDEC, publica con 2-3 meses
    "consumo_mayoristas": 190,
    "consumo_shoppings": 190,
    "inversion_directa_externa": 220,       # balance cambiario BCRA
    "inversion_portafolio_externa": 220,
    "financiamiento_externo_privado": 220,
    # INDEC publica el transporte de pasajeros con ~4 meses, bastante más que
    # los otros volúmenes físicos (electricidad y naftas van a 2). Verificado
    # contra la fuente el 5-ago-2026: su último dato es el mismo que el
    # nuestro, así que los 126 días de rezago son cadencia y no congelamiento.
    # Con 150 iba a dar una demora falsa en tres semanas. Subirlo es seguro
    # porque un congelamiento real lo agarra igual G7_MAX_SIN_AVANZAR, que
    # descuenta el atraso estructural.
    "transporte_pasajeros": 200,
}

# Prefijos que NO bloquean la publicación: son fuentes demoradas, no
# inconsistencias del snapshot (ADR-0133).
NO_BLOQUEAN = ("G2 ", "G7-frescura ")

# ── G6: patrones de jerga interna prohibidos en texto público ──
G6_PATRONES = [
    (re.compile(r"ADR-\d"), "referencia a ADR"),
    (re.compile(r"\d+\.\d+_[A-Z0-9]{3,}"), "ID de serie de datos.gob.ar"),
]


def _parse_fecha(f):
    """'YYYY' | 'YYYY-MM' | 'YYYY-MM-DD' → date (al día 1 / año-12-31)."""
    if not isinstance(f, str):
        return None
    p = f.split("-")
    try:
        if len(p) == 1:
            return date(int(p[0]), 12, 31)
        if len(p) == 2:
            return date(int(p[0]), int(p[1]), 1)
        return date(int(p[0]), int(p[1]), int(p[2]))
    except ValueError:
        return None


def main() -> int:
    warn_only = "--warn-only" in sys.argv
    fallas, avisos = [], []
    inf = json.loads((SNAPSHOT / "informe.json").read_text(encoding="utf-8"))
    series = json.loads((SNAPSHOT / "series.json").read_text(encoding="utf-8"))
    hoy = date.today()

    for ck, c in inf["cinturones"].items():
        # G1 — cinturón
        score = c.get("score")
        if not isinstance(score, (int, float)) or not (0 <= score <= 10):
            fallas.append(f"G1 {ck}: score inválido ({score})")
        desactualizados = 0
        indicadores = c.get("indicadores", {})
        for ik, i in indicadores.items():
            # G1 — indicador completo
            for campo in ("valor", "fecha_dato", "fuente", "unidad"):
                if i.get(campo) in (None, ""):
                    fallas.append(f"G1 {ck}/{ik}: sin {campo}")
            # G2 — frescura
            f = _parse_fecha(i.get("fecha_dato"))
            if f:
                rezago = (hoy - f).days
                tope = MAX_DIAS.get(ik, MAX_DIAS_DEFAULT)
                if rezago > tope:
                    fallas.append(f"G2 {ck}/{ik}: rezago {rezago}d > tope {tope}d "
                                  f"(fecha_dato {i.get('fecha_dato')})")
            elif i.get("fecha_dato"):
                fallas.append(f"G2 {ck}/{ik}: fecha_dato no parseable ({i.get('fecha_dato')})")
            # G2b — frescura del FETCH, no del dato
            sello = i.get("obtenido_en")
            dias_sin_fetch = None
            if sello:
                try:
                    dias_sin_fetch = (hoy - datetime.fromisoformat(str(sello)).date()).days
                except ValueError:
                    fallas.append(f"G2b {ck}/{ik}: obtenido_en no parseable ({sello})")
                else:
                    tope_b = G2B_MAX_DIAS.get(ik, G2B_MAX_DIAS_DEFAULT)
                    if dias_sin_fetch > tope_b:
                        fallas.append(f"G2b {ck}/{ik}: {dias_sin_fetch}d sin un fetch exitoso "
                                      f"> tope {tope_b}d (último: {sello}) — la card "
                                      f"se sigue publicando desde cache")
            # Un indicador con ventana DECLARADA y todavía adentro no es
            # carry-forward: está andando como se decidió que ande (ADR-0210).
            # judicializacion se refresca a mano porque SAIJ bloquea a los
            # runners, así que avisaba todas las noches — y un aviso que suena
            # siempre deja de leerse. Cuando se pase de su ventana lo agarra
            # G2b de arriba, que además CORTA la publicación en vez de avisar.
            if i.get("desactualizado") and not cache_es_esperable(ik, dias_sin_fetch):
                desactualizados += 1
            # G3 — invariante serie ↔ titular
            s = series.get(ik)
            v = i.get("valor")
            if s and isinstance(v, (int, float)) and ik not in G3_EXCEPCIONES:
                ult = s[-1]["valor"]
                if isinstance(ult, (int, float)):
                    tol = max(0.11, abs(v) * G3_TOLERANCIA_REL.get(ik, 0.01))
                    if abs(ult - v) > tol:
                        # G3 verifica que una card FRESCA coincida con su serie.
                        # Si la card viene de carry-forward, es por definición un
                        # valor de otro momento y la discrepancia es el
                        # carry-forward funcionando, no una desincronización: la
                        # fuente falló de un lado (la card) y del otro no. Pasó
                        # el 5-ago-2026 con espiritu_epoca/indice_intencion_
                        # migratoria — Trends rate-limiteó la card (5,6 viejo) y
                        # la serie bajó fresca (7,0)— y bloqueó la publicación de
                        # los CINCO cinturones por una condición que G2 ya estaba
                        # reportando como [DEMORA]. Se avisa igual, para que no
                        # desaparezca del log, pero el dueño de la frescura es G2
                        # (ADR-0174, y el mismo criterio de ADR-0133: una fuente
                        # demorada no tira abajo el pipeline).
                        if i.get("desactualizado"):
                            avisos.append(f"G3 {ck}/{ik}: serie[-1]={ult} ≠ card={v}, pero la "
                                          f"card está en carry-forward — lo vigila G2")
                        else:
                            fallas.append(f"G3 {ck}/{ik}: serie[-1]={ult} ≠ card={v} "
                                          f"(tolerancia {round(tol, 3)})")
            # G3b — los exentos de reconciliación no quedan sin NINGÚN control:
            # su card y su serie difieren por semántica/anclaje (motivo
            # documentado arriba), pero la serie igual tiene que seguir viva.
            # Sin esto, una serie que dejara de actualizarse pasaría el gate
            # para siempre (G2 solo mira la fecha_dato de la card). Corre
            # también con la serie AUSENTE o vacía: una excepción existe
            # justamente porque hay una serie con otra semántica — si la
            # serie desapareció, eso es una regresión, no un caso benigno.
            if ik in G3_EXCEPCIONES:
                if not s:
                    fallas.append(f"G3b {ck}/{ik}: exento de reconciliación pero SIN serie "
                                  f"publicada — la excepción presupone una serie viva")
                else:
                    f_ult = _parse_fecha(s[-1].get("fecha"))
                    if f_ult is None:
                        fallas.append(f"G3b {ck}/{ik}: última fecha de la serie no parseable "
                                      f"({s[-1].get('fecha')})")
                    else:
                        rezago_serie = (hoy - f_ult).days
                        tope = G3B_MAX_DIAS.get(ik, MAX_DIAS.get(ik, MAX_DIAS_DEFAULT))
                        if rezago_serie > tope:
                            fallas.append(f"G3b {ck}/{ik}: serie exenta de reconciliación con "
                                          f"último punto de hace {rezago_serie}d > tope {tope}d "
                                          f"({s[-1].get('fecha')}) — la serie dejó de actualizarse")
        # G2 — presupuesto de carry-forward del cinturón
        if indicadores and desactualizados / len(indicadores) > CARRY_FORWARD_MAX:
            fallas.append(f"G2 {ck}: {desactualizados}/{len(indicadores)} indicadores "
                          f"desactualizados (> {int(CARRY_FORWARD_MAX*100)}%)")
        elif desactualizados:
            avisos.append(f"G2 {ck}: {desactualizados}/{len(indicadores)} en carry-forward")

    # G6 — jerga interna en cualquier string del snapshot
    def _strings(x, ruta=""):
        if isinstance(x, dict):
            for k, v in x.items():
                yield from _strings(v, f"{ruta}.{k}")
        elif isinstance(x, list):
            for j, v in enumerate(x):
                yield from _strings(v, f"{ruta}[{j}]")
        elif isinstance(x, str):
            yield ruta, x
    for ruta, texto in _strings(inf):
        for patron, nombre in G6_PATRONES:
            m = patron.search(texto)
            if m:
                fallas.append(f"G6 {ruta}: {nombre} en texto público («{m.group(0)}»)")

    # G7 — las anclas de la validación externa siguen vivas
    ve_path = VALIDACION
    if not ve_path.exists():
        avisos.append("G7: sin output/validacion_externa.json — anclas no verificadas")
    else:
        try:
            ve = json.loads(ve_path.read_text(encoding="utf-8"))
        except Exception as e:
            ve = None
            fallas.append(f"G7: validacion_externa.json ilegible ({e})")
        anclas = ve.get("panel_anclas") if isinstance(ve, dict) else None
        if ve is not None and anclas is None:
            # No se degrada a aviso: si el registro deja de escribirse, el gate
            # se queda ciego y esa ceguera es justamente lo que hay que evitar.
            fallas.append("G7: validacion_externa.json sin 'panel_anclas' — la "
                          "frescura de las anclas dejó de registrarse; correr "
                          "validacion_externa.py")
        elif anclas is not None:
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                import panel_validacion as _pnl
                declaradas = sorted(_pnl.FAMILIA)
            except Exception as e:
                declaradas = sorted(anclas)
                avisos.append(f"G7: no se pudo leer el registro de anclas ({e}); se "
                              f"verifican sólo las {len(declaradas)} registradas")
            for nombre in declaradas:
                info = anclas.get(nombre)
                if not info:
                    # BLOQUEA: el factor común se calculó sobre menos series que
                    # las declaradas, y su varianza explicada se publica igual.
                    fallas.append(f"G7 {nombre}: ancla declarada del panel SIN datos — "
                                  f"el factor común se calculó sin ella")
                    continue
                f_ult = _parse_fecha(info.get("ultimo"))
                if f_ult is None:
                    fallas.append(f"G7 {nombre}: último período no parseable "
                                  f"({info.get('ultimo')})")
                    continue
                rezago_ancla = (hoy - f_ult).days
                tope_ancla = G7_MAX_DIAS.get(nombre, G7_MAX_DIAS_DEFAULT)
                if rezago_ancla > tope_ancla:
                    # NO bloquea: es una fuente demorada, mismo criterio que G2.
                    # Pero queda nombrada en cada corrida, que es exactamente lo
                    # que le faltó al ICG durante meses.
                    fallas.append(f"G7-frescura {nombre}: último punto de hace "
                                  f"{rezago_ancla}d > tope {tope_ancla}d "
                                  f"({info.get('ultimo')}) — el ancla se congeló y sus "
                                  f"correlaciones se siguen publicando")
                # Sin avanzar: descuenta el atraso inherente de la fuente y por
                # eso avisa semanas antes que el rezago absoluto. Una corrida
                # anterior a ADR-0178 no tiene el campo — se saltea en vez de
                # inventar una falla de migración.
                f_avanzo = _parse_fecha(info.get("avanzo"))
                if f_avanzo is not None:
                    sin_avanzar = (hoy - f_avanzo).days
                    if sin_avanzar > G7_MAX_SIN_AVANZAR:
                        fallas.append(f"G7-frescura {nombre}: hace {sin_avanzar}d que no "
                                      f"publica un período nuevo (> {G7_MAX_SIN_AVANZAR}d); "
                                      f"sigue clavada en {info.get('ultimo')}")

    # ── G8 — la lectura del mes ──────────────────────────────────────────────
    # AVISA, no bloquea: sin archivo del período la portada cae sola a la
    # síntesis automática, que es publicable y dice de dónde sale (ADR-0211).
    # Lo que este aviso evita es lo otro: que el mes arranque, nadie escriba la
    # lectura y nadie se entere hasta que un lector lo note.
    periodo = inf.get("period")
    if periodo:
        editorial = ROOT / "web" / "src" / "contenido" / "lectura-del-mes" / f"{periodo}.md"
        if not editorial.exists():
            avisos.append(f"G8: {periodo} sin lectura editorial "
                          f"({editorial.relative_to(ROOT)}) — la portada publica la "
                          f"síntesis automática")

    # ── Bloqueantes vs. no bloqueantes (ADR-0133) ────────────────────────────
    # Una fuente que se atrasa NO puede impedir que se publique todo lo demás.
    # El indicador ya queda marcado `desactualizado`, publicar.py hace
    # carry-forward del último valor bueno y el tablero lo muestra como viejo:
    # el lector no se entera de nada falso. Bloquear la publicación entera por
    # eso deja al informe SIN ACTUALIZAR NADA, que es peor que mostrar un
    # indicador viejo señalado como viejo.
    #
    # Lo que sí bloquea es la INCONSISTENCIA: un indicador sin valor (G1), una
    # card que no coincide con su serie (G3) o jerga interna en texto público
    # (G6). Ahí el snapshot afirma algo que no es cierto, y eso no se publica.
    bloqueantes = [f_ for f_ in fallas if not f_.startswith(NO_BLOQUEAN)]
    demorados = [f_ for f_ in fallas if f_.startswith(NO_BLOQUEAN)]

    print(f"Gate de calidad — {hoy.isoformat()}")
    for a in avisos:
        print(f"  [AVISO] {a}")
    for f_ in demorados:
        print(f"  [DEMORA] {f_}")
    for f_ in bloqueantes:
        print(f"  [FALLA] {f_}")

    n_ind = sum(len(c.get("indicadores", {})) for c in inf["cinturones"].values())
    if not fallas:
        print(f"  [OK] {n_ind} indicadores en {len(inf['cinturones'])} cinturones: "
              f"estructura, frescura, invariante serie-titular, anclas de "
              f"validación y editorial limpios")
        return 0
    if not bloqueantes:
        print(f"  → {len(demorados)} fuente(s) demorada(s), ninguna falla de "
              f"integridad. El snapshot SE PUBLICA: los indicadores atrasados "
              f"van marcados como desactualizados.")
        return 0
    print(f"  → {len(bloqueantes)} falla(s) de integridad. El snapshot NO debe "
          f"publicarse." + (f" (+{len(demorados)} fuente(s) demorada(s))"
                            if demorados else ""))
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
