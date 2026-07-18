"""revision_bandas.py — ¿qué bandas conviene revisar? (ADR-0081)

La auditoría de consistencia macro (jul-2026) pidió "calendarizar las
recalibraciones de bandas de historia corta". Un calendario en un documento se
desactualiza solo; esto lo reemplaza por un diagnóstico ejecutable.

QUÉ MIRA, y por qué esos números

El criterio del proyecto (ADR-0045) es tajante: una banda se recalibra **solo
si su techo o su piso son inalcanzables**, nunca porque el rango observado
quede corto. Si el indicador se pasó dos años pegado al piso porque el país
anduvo mal, correr el piso hacia abajo blanquea la señal en vez de mejorarla.

Distinguir un caso del otro exige dos medidas distintas:

  * SATURACIÓN — qué fracción de los meses cae exactamente en el puntaje
    extremo. Alta saturación significa que el indicador dejó de discriminar en
    ese tramo: doce meses "iguales" que en realidad no lo eran.
  * ALCANCE — si el extremo OPUESTO se tocó alguna vez. Un extremo que nunca
    se alcanzó en toda la historia disponible es el candidato legítimo a
    revisión; uno que se alcanzó alguna vez está bien calibrado y la
    saturación es desempeño real.

La combinación que enciende la alarma es **saturación alta de un lado + el otro
extremo nunca alcanzado**, y aun así el resultado es una CANDIDATA A REVISIÓN
por una persona, nunca un cambio automático: sólo alguien que conozca el
indicador puede decir si el techo es inalcanzable por construcción o porque el
período no dio para tanto.

Uso: python scripts/revision_bandas.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import parametrica
import itcm
import itcg
import itcp

ROOT = Path(__file__).resolve().parents[1]
SERIES = ROOT / "web" / "src" / "data" / "series.json"
SALIDA = ROOT / "output" / "revision_bandas.json"

# Umbrales del diagnóstico. No son verdades: son el punto donde conviene que
# alguien MIRE. Se eligen holgados a propósito — el costo de un falso positivo
# es leer una ficha, el de un falso negativo es una banda mal calibrada durante
# años sin que nadie se entere.
SATURACION_AVISO = 0.35      # 35% de los meses en un mismo extremo
HISTORIA_MINIMA = 18         # con menos meses no se opina: la muestra manda

def _escala(mod, sigla):
    return getattr(mod, f"ESCALA_{sigla}", None) or parametrica.Escala(
        getattr(mod, f"BANDAS_{sigla}"), getattr(mod, f"ANCLAS_{sigla}", None),
        getattr(mod, f"TRANSFORMACIONES_{sigla}", None))


INDICES = {
    "ITCM": (_escala(itcm, "ITCM"), itcm.DIMENSIONES_ITCM),
    "ITCG": (_escala(itcg, "ITCG"), itcg.DIMENSIONES_ITCG),
    "ITCP": (_escala(itcp, "ITCP"), itcp.DIMENSIONES_ITCP),
}


def _extremos(ind, escala):
    """(piso, techo) de puntaje que la escala del indicador puede devolver."""
    if ind in escala.anclas:
        posibles = [y for _, y in escala.anclas[ind]]
    else:
        posibles = [b[2] for b in escala.bandas[ind]]
    return min(posibles), max(posibles)


def _valores_por_indicador(sigla: str, series: dict) -> dict:
    """{indicador: [valores CRUDOS de su serie]}.

    Se pasan tal cual salen de la serie: si un indicador necesita
    transformación previa (el REM se publica anual y se puntúa mensual), la
    aplica `parametrica.puntaje_de` a partir de la tabla declarada junto a las
    bandas (ADR-0082). Este módulo no la conoce ni tiene que conocerla — la
    primera versión sí la conocía a medias y por eso mandó a revisar una banda
    perfectamente calibrada.
    """
    return {ind: [p["valor"] for p in (pts or []) if p.get("valor") is not None]
            for ind, pts in series.items()}


def diagnosticar() -> list:
    series = json.loads(SERIES.read_text(encoding="utf-8"))
    filas = []
    for sigla, (escala, dimensiones) in INDICES.items():
        del_indice = {i for d in dimensiones.values() for i in d["indicadores"]}
        por_indicador = _valores_por_indicador(sigla, series)
        for ind in sorted(del_indice):
            if not escala.puntuable(ind):
                continue
            valores = por_indicador.get(ind) or []
            if len(valores) < HISTORIA_MINIMA:
                filas.append({"indice": sigla, "indicador": ind, "n": len(valores),
                              "estado": "historia_corta", "detalle":
                              f"{len(valores)} meses: por debajo del mínimo de "
                              f"{HISTORIA_MINIMA} para diagnosticar"})
                continue

            puntajes = [escala.puntaje(v, ind) for v in valores]
            piso, techo = _extremos(ind, escala)
            en_piso = sum(1 for p in puntajes if abs(p - piso) < 0.01) / len(puntajes)
            en_techo = sum(1 for p in puntajes if abs(p - techo) < 0.01) / len(puntajes)

            fila = {"indice": sigla, "indicador": ind, "n": len(valores),
                    "piso": piso, "techo": techo,
                    "share_piso": round(en_piso, 3), "share_techo": round(en_techo, 3)}

            # La combinación que importa: saturado de un lado Y el otro extremo
            # nunca alcanzado. Sólo ahí hay sospecha de ancla inalcanzable.
            if en_piso >= SATURACION_AVISO and en_techo == 0:
                fila.update(estado="revisar", detalle=(
                    f"{en_piso:.0%} de los meses en el piso ({piso:.0f}) y el techo "
                    f"({techo:.0f}) nunca se alcanzó en {len(valores)} meses"))
            elif en_techo >= SATURACION_AVISO and en_piso == 0:
                fila.update(estado="revisar", detalle=(
                    f"{en_techo:.0%} de los meses en el techo ({techo:.0f}) y el piso "
                    f"({piso:.0f}) nunca se alcanzó en {len(valores)} meses"))
            elif max(en_piso, en_techo) >= SATURACION_AVISO:
                fila.update(estado="saturado", detalle=(
                    f"{max(en_piso, en_techo):.0%} de los meses en un extremo, pero el "
                    f"otro también se alcanzó: la banda discrimina poco en ese tramo "
                    f"y aun así está bien anclada"))
            else:
                fila.update(estado="ok", detalle="sin saturación relevante")
            filas.append(fila)
    return filas


def main():
    filas = diagnosticar()
    orden = {"revisar": 0, "saturado": 1, "historia_corta": 2, "ok": 3}
    filas.sort(key=lambda f: (orden[f["estado"]], f["indice"], f["indicador"]))

    print("Revisión de bandas —", SERIES.parent.name)
    print(f"(saturación de aviso: {SATURACION_AVISO:.0%} · historia mínima: "
          f"{HISTORIA_MINIMA} meses)\n")
    etiqueta = {"revisar": "[REVISAR]", "saturado": "[satura]",
                "historia_corta": "[corta]", "ok": "[ok]"}
    for f in filas:
        if f["estado"] == "ok":
            continue
        print(f"  {etiqueta[f['estado']]:10} {f['indice']}/{f['indicador']}: {f['detalle']}")

    n_rev = sum(1 for f in filas if f["estado"] == "revisar")
    n_ok = sum(1 for f in filas if f["estado"] == "ok")
    print(f"\n  {n_rev} para revisar · "
          f"{sum(1 for f in filas if f['estado'] == 'saturado')} saturadas pero ancladas · "
          f"{sum(1 for f in filas if f['estado'] == 'historia_corta')} sin historia suficiente · "
          f"{n_ok} sin observaciones")
    if n_rev:
        print("\n  Recordatorio (ADR-0045): 'para revisar' NO significa recalibrar. Una banda")
        print("  se recalibra sólo si el extremo es inalcanzable por construcción. Si el")
        print("  rango corto refleja desempeño real, correr el ancla blanquea la señal.")

    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(
        {"umbral_saturacion": SATURACION_AVISO, "historia_minima": HISTORIA_MINIMA,
         "filas": filas}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {SALIDA}")


if __name__ == "__main__":
    main()
