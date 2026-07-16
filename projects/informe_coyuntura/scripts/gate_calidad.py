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
    # fuentes con rezago estructural largo
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
    "alineamiento_senadores_prov": "ambos usan ventana móvil de 90 días, pero anclada a fechas distintas: card = hoy; serie = fin de cada mes (fetch_alineamiento_senadores_prov_mensual, 2026-07-09)",
    "cohesion_bloque": "mismo caso que alineamiento_senadores_prov: card y serie usan ventana móvil de 90 días anclada a fechas distintas (card = hoy; serie = fin de cada mes). Desde 2026-07-10 ambos son el COMPUESTO bicameral 65/35 (fetch_cohesion_bloque_compuesta_mensual) — la asimetría de anclaje se hereda de las dos cámaras: un acta dividida a mitad de mes los separa más que la tolerancia",
    "votometro_ventaja_lla": "misma familia de anclaje: card = ponderación de encuestas evaluada HOY (recencia exp(-0,015·días) desde hoy); serie = el mismo cálculo evaluado al cierre de cada mes (votometro_serie_mensual). Hoy difieren 0,1pp (5,3 vs 5,2) y pasan por tolerancia de casualidad — una encuesta nueva a mitad de mes los separa más (auditoría 2026-07-09)",
    "derrotas_legislativas": "misma familia de anclaje: card = conteo de 12 meses calendario anclado al MES EN CURSO (parcial); serie = el mismo conteo a cada fin de mes CERRADO. Con eventos discretos difieren de a enteros de forma mecánica cada vez que un evento entra o sale de la ventana durante el mes corriente (p. ej. al mes siguiente de que un grupo de derrotas cumpla 12 meses, la card cae de inmediato y la serie recién al cierre) — no es desincronización de datos (2026-07-09)",
    "bloqueo_sostenido": "misma familia de anclaje que derrotas_legislativas (comparten registro y ventana): card = tasa de 12 meses calendario anclada al MES EN CURSO (parcial); serie = la misma tasa a cada fin de mes CERRADO. Con pocos desafíos en ventana, un desafío que entra o sale durante el mes corriente mueve la tasa varios puntos de forma mecánica (hoy: card 20,0 con la ventana de jul-2026 vs serie 27,3 al cierre de jun-2026, porque el veto de Bahía Blanca salió de la ventana el 1 de julio) — no es desincronización de datos (2026-07-16)",
}
# tolerancia relativa por indicador (default 1% o 0,11 absoluto, redondeos)
G3_TOLERANCIA_REL = {"cepo_mulc": 0.10}   # brecha cambiaria viva: deriva intradiaria

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

    print(f"Gate de calidad — {hoy.isoformat()}")
    for a in avisos:
        print(f"  [AVISO] {a}")
    for f_ in fallas:
        print(f"  [FALLA] {f_}")
    if not fallas:
        n_ind = sum(len(c.get("indicadores", {})) for c in inf["cinturones"].values())
        print(f"  [OK] {n_ind} indicadores en {len(inf['cinturones'])} cinturones: "
              f"estructura, frescura, invariante serie-titular y editorial limpios")
        return 0
    print(f"  → {len(fallas)} falla(s). El snapshot NO debe publicarse.")
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
