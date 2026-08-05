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
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (Path(sys.argv[sys.argv.index("--snapshot") + 1])
            if "--snapshot" in sys.argv else ROOT / "web" / "src" / "data")

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
    "mortalidad_pymes": 140, "despacho_cemento": 140, "consumo_carne": 140,
    "endeudamiento_familiar": 140, "inseguridad": 150,
}
CARRY_FORWARD_MAX = 0.40                # tope de desactualizados por cinturón

# ── G3: pares card/serie con semántica DISTINTA (excepción con motivo) ──
G3_EXCEPCIONES = {
    "sentimiento_digital": "card = pulso 3m en tiempo real; serie = canasta mensual ventana fija (ADR-0034)",
    "rigi_inversiones": "card = % de la meta; serie = monto acumulado en M USD",
    "protestas_caba": "card = eventos acumulados 12m; serie = eventos semanales",
    "cepo_mulc": "card = brecha CCL/mayorista SPOT del día; serie = brecha entre el PROMEDIO MENSUAL del CCL y el promedio mensual del A3500 (fetch_brecha_serie). No es un problema de anclaje sino de estadístico: un promedio mensual no puede igualar un spot diario en una serie que oscila ±30% m/m, y acercar las anclas no lo arreglaría. La tolerancia especial del 10% que hubo acá falló el 16-jul-2026 (11,5%) y ese mismo día el par pasaba por 0,02 de margen: era un parche que iba a fallar todos los meses volátiles. La frescura de la serie la sigue vigilando G3b (reclasificado 2026-08-05: hasta ADR-0172 estaba anotado como 'misma familia de anclaje que votometro/derrotas', que era un diagnóstico equivocado)",
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
            if i.get("desactualizado"):
                desactualizados += 1
            # G3 — invariante serie ↔ titular
            s = series.get(ik)
            v = i.get("valor")
            if s and isinstance(v, (int, float)) and ik not in G3_EXCEPCIONES:
                ult = s[-1]["valor"]
                if isinstance(ult, (int, float)):
                    tol = max(0.11, abs(v) * G3_TOLERANCIA_REL.get(ik, 0.01))
                    if abs(ult - v) > tol:
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
    bloqueantes = [f_ for f_ in fallas if not f_.startswith("G2 ")]
    demorados = [f_ for f_ in fallas if f_.startswith("G2 ")]

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
              f"estructura, frescura, invariante serie-titular y editorial limpios")
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
