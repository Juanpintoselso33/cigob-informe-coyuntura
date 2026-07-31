"""Recupera a «Opciones consideradas» las alternativas que quedaron en prosa.

115 ADR no tenían sección de opciones y la migración les dejó una
declaración explícita de que el original no las registró. De esos, 54 sí
discuten alternativas evaluadas y descartadas, pero adentro del Contexto o
de la Decisión: «se descartó X porque…», «era la otra opción», «Rutas
investigadas y descartadas: …».

Este script las sube a la sección que les corresponde en MADR. Cada viñeta
es un resumen fiel de lo que ese ADR ya dice — con sus cifras y su motivo
de descarte. No se inventa ninguna alternativa: los 61 ADR que no discuten
ninguna conservan la declaración de que no fueron registradas.

La tabla es el juicio; el script solo la aplica. Se audita renglón por
renglón contra el cuerpo de cada ADR.

Uso:
    python scripts/adr_opciones.py --simular
    python scripts/adr_opciones.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"

PLACEHOLDER = "_El ADR original no registró opciones alternativas._"

OPCIONES: dict[str, list[str]] = {
    "0011": [
        "**Plataforma oficial del RIGI** (Google Sheet de Economía): dato oficial, "
        "estructurado y en vivo — elegida.",
        "**Proxy por conteo de normas de InfoLeg**, con calibración manual — descartada: "
        "no da cifras concretas de inversión ni de proyectos.",
        "**Ratio `proyectos aprobados / presentados`** (17/41 = 41,5%) — descartado por "
        "estar dominado por los proyectos chicos; la versión ponderada por monto es más "
        "fiel al fenómeno económico.",
    ],
    "0016": [
        "**Scraping de la tasa de adjudicación en CONTRAT.AR** — elegida.",
        "**Datos abiertos de CONTRAT.AR (CKAN)** — descartada: congelados en mar-2023 "
        "(verificado: 482 procesos, máximo 2023-03-16).",
        "**OCDS de obra pública** — no existe.",
        "**Búsqueda del Boletín Oficial** — descartada: bloquea la automatización "
        "(302 a `/error/show`).",
    ],
    "0029": [
        "**Promedio móvil de 3 meses sobre IPC cerrado** — elegida.",
        "**X-13-ARIMA con regresores de calendario y tendencia-ciclo** — el óptimo "
        "técnico, descartado acá porque introduce un modelo estimado: rompe la "
        "reproducibilidad simple del pipeline y sus coeficientes cambian con cada "
        "dato nuevo.",
    ],
    "0031": [
        "**Validación cruzada contra benchmarks externos contemporáneos** — elegida.",
        "**Validación predictiva (lead-lag)** — probada y descartada como claim: la "
        "correlación del ITCG con el riesgo país es máxima en el mes contemporáneo "
        "(−0,86) y decae con el adelanto; la del ITCM mejora apenas a 5 meses "
        "(−0,755 contra −0,731), indistinguible con n=25.",
    ],
    "0032": [
        "**IVI mensual** — elegida.",
        "**Bases SAT del Ministerio** — descartadas: mensuales, pero publicadas en "
        "tandas anuales cada diciembre, un año detrás del consolidado y solo con "
        "subconjuntos de delitos.",
        "**Fuentes jurisdiccionales mensuales (CABA)** — descartadas: cambian el "
        "alcance nacional de la métrica.",
        "**SNIC mensual** — no existe.",
    ],
    "0072": [
        "**Resultado primario como cociente contra la recaudación** — elegida.",
        "**Deflactar por IPC** — era la otra opción y se descartó por la razón que la "
        "propia auditoría plantea en su sección IV.2: el IPC ya deflacta recaudación, "
        "crédito, IDM y la tasa real del IdC, y sumarle un quinto uso concentraría "
        "todavía más el riesgo de una fuente única.",
    ],
}


def aplicar(texto: str, viñetas: list[str]) -> str | None:
    if PLACEHOLDER not in texto:
        return None
    lista = "\n".join(f"- {v}" for v in viñetas)
    return texto.replace(PLACEHOLDER, lista)


def main() -> int:
    simular = "--simular" in sys.argv
    hechos, saltados = 0, []
    for propio, viñetas in OPCIONES.items():
        candidatos = list(ADR_DIR.glob(f"{propio}*.md"))
        if not candidatos:
            saltados.append(f"{propio}: no existe")
            continue
        p = candidatos[0]
        nuevo = aplicar(p.read_text(encoding="utf-8"), viñetas)
        if nuevo is None:
            saltados.append(f"{propio}: ya tenía opciones, no se toca")
            continue
        if not simular:
            p.write_text(nuevo, encoding="utf-8", newline="\n")
        hechos += 1
        print(f"  {propio}: {len(viñetas)} opciones recuperadas")

    print(f"\n{'Simulación' if simular else 'Aplicado'}: {hechos} ADR")
    for s in saltados:
        print(f"  AVISO  {s}")
    restantes = sum(
        1 for p in ADR_DIR.glob("[0-9]*.md")
        if PLACEHOLDER in p.read_text(encoding="utf-8")
    )
    print(f"Siguen con la declaración de «no registradas»: {restantes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
