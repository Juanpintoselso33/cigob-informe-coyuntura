"""procedencia_anclas.py — de dónde sale cada ancla del proyecto (ADR-0103).

La auditoría del cinturón de gestión (jul-2026, punto 3.2) planteó el riesgo de
CIRCULARIDAD: si las bandas se fijan mirando lo que el gobierno ya logró, es más
fácil que el puntaje tienda a ser alto. Pidió "distinguir, en la documentación
pública, qué bandas están ancladas a un criterio normativo externo y cuáles son
convenciones internas de CIGOB".

Este archivo es esa distinción, ejecutable. No elimina el sesgo —con 36 de 42
indicadores sin historia previa a dic-2023, la calibración interna es
irreducible— pero lo vuelve CONTABLE: cuánto del peso de cada índice descansa en
anclas que sólo pueden validarse contra el período que se está midiendo.
Cubre los cuatro índices: los tres por bandas (ITCM/ITCG/ITCP) y el ITVC
base-100, que se clasifica por su ancla de rebase (ADR-0123).

LAS CATEGORÍAS, de menor a mayor riesgo:

  externa         Referencia verificable fuera del proyecto y ajena al período
                  medido: un estudio publicado, la práctica histórica de otros
                  gobiernos. Es el estándar al que conviene tender.
  documento       Fijada en el documento de diseño del proyecto ANTES de ver los
                  datos. No es externa, pero tampoco se acomodó al resultado.
  conceptual      Anclada a un valor con significado propio —el cero, la
                  paridad, el 100%— y no a un rango observado.
  historia_larga  Calibrada contra la serie propia del indicador, pero incluyendo
                  períodos anteriores a esta gestión.
  convencion      Calibrada mirando el rango observado desde dic-2023. Es el caso
                  que la auditoría señala: defendible y declarado, pero circular.
  sin_declarar    El código no dice de dónde sale. Peor que una convención: una
                  convención invisible.

CÓMO SE LLENÓ: leyendo, uno por uno, los comentarios de BANDAS_* en itcm.py,
itcg.py e itcp.py, y las bases de rebase de itvc.py. Es una clasificación de CRITERIO y una primera pasada — el
editor debería revisarla, sobre todo los casos marcados `convencion`, que son
los que la auditoría pide vigilar.

Uso: python scripts/procedencia_anclas.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

import itcm
import itcg
import itcp
import itvc

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "output" / "procedencia_anclas.json"

CATEGORIAS = ("externa", "documento", "conceptual", "historia_larga",
              "convencion", "sin_declarar")

# ── El trinquete (ADR-0105) ─────────────────────────────────────────────────
# Estado medido el 2026-07-20. La regla de anclas nuevas es un orden de
# preferencia —externa · conceptual · historia previa · convención, en ese
# orden— y una regla así se erosiona sola si nadie la mira: cada indicador
# nuevo con anclas de conveniencia es defendible de a uno, y la suma no la
# defiende nadie.
#
# Estos techos hacen que la suma tenga dueño. La suite falla si la fracción
# circular de un índice SUBE, de modo que incorporar un indicador con ancla
# circular obliga a editar este bloque a mano: deja de ser gratis y silencioso
# y pasa a verse en el diff, que es donde se puede discutir.
#
# Bajarlos cuando el número mejore es parte del trabajo: un techo que quedó
# muy por encima del valor real deja de frenar nada.
TECHOS = {
    # ITCM bajó de 0,83 a 0,38 el 2026-07-20 (ADR-0120): las siete bandas
    # sin_declarar pasaron a declarar su origen —normativo o conceptual—, y
    # sin_declarar cayó de 0,45 a 0,00. El techo se baja para FIJAR la mejora:
    # a partir de acá el ITCM no puede volver a subir de 0,38 sin que alguien
    # lo firme. El 0,38 que queda es convención irreducible (idm, iai, icip,
    # costo de financiamiento, crédito real: sin historia previa a dic-2023).
    #
    # SUBE a 0,41 el 2026-08-11 (ADR-0192), y es una decisión tomada, no un
    # efecto lateral: `desequilibrio_monetario` entra con cortes calibrados por
    # percentiles de su propia serie —convención— en el lugar de
    # `presion_dolarizacion`, cuyas anclas venían del documento de diseño. El
    # cambio de fuente de las anclas mueve la fracción circular del ITCM de
    # 38,0% a 40,3%.
    #
    # Se acepta porque la alternativa no existe: los cortes preliminares del
    # documento (verde <500, rojo >3.000 millones) no cierran contra el dato
    # —cero meses verdes en los quince de la ventana— y la propia ficha preveía
    # reemplazarlos por percentiles reales en su sección 7. Preferir un ancla de
    # documento que satura el semáforo no es menos circular, es menos útil.
    "ITCM": {"circular": 0.41, "sin_declarar": 0.01},
    # ITCG y ITCP bajaron el 2026-07-20 (ADR-0121) al declarar el origen de sus
    # bandas sin_declarar: los medidores de avance 0-100 (ITCG) y los indicadores
    # anclados al cero (ITCP: ventaja electoral, quórum, transferencias) eran
    # conceptuales, no convención invisible. NO se reclasificó lo que sí es
    # convención real —reduccion_estado, gasto, rigi, cohesion_bloque, etc.
    # quedan como están—, por eso los tres pisos convergen en ~40% y no bajan
    # más: ése es el núcleo irreducible de indicadores que miden lo que este
    # gobierno hizo, calibrados contra lo que se observó.
    "ITCG": {"circular": 0.40, "sin_declarar": 0.01},
    # ITCP baja a 0,34 el 2026-07-25 (ADR-0126): entra cobertura_judicial con
    # ancla CONCEPTUAL —niveles de cobertura de un cuerpo, no el rango 64-73%
    # observado— y diluye la proporción circular del índice. El techo se baja
    # para fijar la mejora, igual que se hizo con el ITCM en ADR-0120.
    "ITCP": {"circular": 0.34, "sin_declarar": 0.01},
    # ITVC entró al registro el 2026-07-20 (ADR-0123) con 0% circular: al no
    # tener bandas —cada componente se mide como distancia a la fecha fija
    # 4T-2023— no hay cortes que calibrar contra el período. Techo en 0,01: si
    # algún día un componente del ITVC pasara a anclarse al rango observado,
    # tiene que verse.
    "ITVC": {"circular": 0.01, "sin_declarar": 0.01},
}

# indicador → (categoría, de dónde sale). El segundo campo es lo que hace
# auditable la clasificación: cualquiera puede ir al comentario y discutirla.
PROCEDENCIA = {
    # ── ITCM ────────────────────────────────────────────────────────────────
    "ipc_total": ("conceptual", "bandas normativas: metas de estabilidad de precios, deliberadamente NO ancladas a la historia para no blanquear la señal (ADR-0120)"),
    "rem_ipc_12m": ("conceptual", "hereda las bandas normativas del ipc_total —misma vara para inflación esperada y realizada— (ADR-0120)"),
    "idm": ("convencion", "«calibrado con la historia 2024-2026»"),
    "desequilibrio_monetario": ("convencion", "cortes por percentiles (p0/p25/p50/p75/p100) de cada componente, como pide la sección 7 de la ficha; la matriz A×B y sus cuatro esquinas vienen del documento (ADR-0192)"),
    "recaudacion": ("conceptual", "bandas de variación real en torno al cero; los cortes caen razonablemente en la distribución 2021-2023 de la serie DGI que se puntúa desde ADR-0127 (mediana +4,5%; p0/p14/p57/p80) y NO se recalibraron al cambiar de fuente (ADR-0120)"),
    "saldo_comercial_12m": ("conceptual", "bandas en torno al equilibrio comercial (cero), techo institucional 85; consistentes con la mediana histórica (ADR-0120)"),
    "reservas_bcra": ("conceptual", "bandas en torno al cero de reservas netas: nivel de cobertura, no distribución observada (ADR-0120)"),
    "idc": ("conceptual", "anclas en desvíos estándar: +1σ ≈ p84 · −1σ ≈ p16 (ADR-0028)"),
    "emae_ia": ("conceptual", "bandas de crecimiento en torno al cero; el corte de crecimiento nulo cae en p26 de la historia 2021-2023 (ADR-0120)"),
    "cobertura_judicial": ("conceptual", "niveles redondos de cobertura de un cuerpo (>90 completa · 80-90 buena · 70-80 aceptable · 60-70 deficitaria · ≤60 crítica), explícitamente NO calibrados contra el rango observado 64-73%, que es desempeño real y bajo (ADR-0126)"),
    "emae_difusion": ("conceptual", "cortes por CANTIDAD DE SECTORES (14-15 generalizado · 11-13 mayoría amplia · 8-10 ajustada · 5-7 minoría · 0-4 contracción), puestos en el hueco entre valores alcanzables; explícitamente NO se ancló en el 50% de manual porque la mediana histórica argentina es 73,3% (ADR-0124)"),
    "ipi_manufacturero": ("conceptual", "hereda las bandas del EMAE a propósito para dejar ver la brecha industria-actividad, con cita a ADR-0045 (ADR-0076/0079)"),
    "tcrm": ("historia_larga", "historia 1997-2026: p10≈75, p25≈87, mediana≈106 — 29 años, cinco gobiernos"),
    "resultado_primario": ("convencion", "referencias dic-2023 (−12,0%) y el programa estabilizado en +6/+8% (ADR-0072)"),
    "costo_financiamiento_tesoro": ("convencion", "extremos tomados de dic-2023 (−12,2%) y ago-2025 (+33,5%) (ADR-0071)"),
    "iai": ("convencion", "el umbral ±2% del documento «no sobrevive al dato»: se reemplazó por bandas calibradas a 2024-2026"),
    "icip": ("convencion", "banda ensanchada por la volatilidad observada del período"),
    "credito_privado": ("convencion", "«calibradas a la remonetización 2024-2026» (ADR-0022)"),

    # ── ITCG ────────────────────────────────────────────────────────────────
    "cepo_mulc": ("documento", "«brecha sostenida <10-15% = condiciones óptimas de unificación» (doc 260702)"),
    "apertura_comercial": ("documento", "anclas sobre la lineal del documento: 0% → 100 · 15% → 0 (ADR-0021)"),
    "desregulacion_normativa": ("convencion", "el conteo pasa a ser OFICIAL (informe mensual del Min. de Desregulación) pero la vara NO: el organismo no publica meta, así que los cortes 100/300/600/1200 los ponemos nosotros — misma limitación que declaraba ADR-0096, con otra fuente para el número (ADR-0125)"),
    "reduccion_estado": ("convencion", "«calibrado con el dato real»: el recorte observado de ~10-12% define la banda 85"),
    "gasto_funcionamiento": ("convencion", "bandas anchas por el ajuste de 2024, que la propia ficha llama históricamente atípico"),
    # masa_salarial salió del índice por ADR-0186 (a pedido de CIGOB, dudas
    # sobre la exposición de la fuente): su banda sigue existiendo pero ya no
    # pondera, así que no entra acá — mismo criterio que asistencia_directa.
    "reestructuracion_organismos": ("conceptual", "medidor de avance 0-100 hacia el plan de disoluciones/cierres; el 100 es el ancla, no el rango observado (ADR-0121)"),
    "fal_modernizacion_laboral": ("conceptual", "cortes sobre los estados que la escala puede tomar, no sobre el rango observado (ADR-0098)"),
    "privatizaciones": ("documento", "etapas 0-4 definidas en el documento de diseño"),
    "rigi_inversiones": ("convencion", "referencia el 22,1% de jun-2026 y la composición del pipeline de ese momento"),
    "concesiones_infraestructura": ("conceptual", "tasa de adjudicación km/plan; el 100 (plan adjudicado) es el ancla (ADR-0121)"),
    # asistencia_directa vuelve a puntuar por ADR-0189: el ITCG mide avance de
    # propuestas y no puede descartar las cumplidas. Su ancla es la más floja
    # del cinturón y conviene que quede contada como tal.
    "asistencia_directa": ("convencion", "el corte de «cumplido» en 95% es propio y queda POR DEBAJO de la línea de base: la TDPS ya marcaba 98,3% en ago-2023 y 100,0 todos los meses del mandato, así que el indicador puntúa 100 sobre un tramo que ya estaba andado (calibración pendiente, ADR-0189)"),
    "protocolo_antipiquetes": ("convencion", "calibrada con la caída observada en CABA en 2024-2025"),
    "libertad_opcion_salud": ("conceptual", "% de usuarios con libre opción; el 100 (libre opción plena) es el ancla (ADR-0121)"),
    "litigiosidad_laboral": ("historia_larga", "calibrada sobre 2021-2026, que incluye dos gobiernos (ADR-0023)"),

    # ── ITCP ────────────────────────────────────────────────────────────────
    "votometro_ventaja_lla": ("conceptual", "ventaja electoral anclada en el cero (empate) con márgenes simétricos redondos (ADR-0121)"),
    "ratio_dnu": ("externa", "ACIJ 2011-2024, cuatro presidencias: 344 DNU / 1.058 leyes ≈ 0,33 (ADR-0058/0059)"),
    "eficacia_legislativa": ("externa", "Directorio Legislativo: 40-50% Macri · 63-67% Alberto Fernández · 75-82% CFK (ADR-0061)"),
    "veto_quorum": ("conceptual", "tasa de fracaso de quórum anclada en el cero (Congreso funcionando), cortes redondos (ADR-0121)"),
    "desafios_legislativos": ("convencion", "anclas sobre el conteo observado (4 a 13 en 22 meses), leído contra el carácter excepcional del acto (ADR-0089)"),
    "produccion_legislativa": ("externa", "el techo es el promedio histórico de 74,4 leyes/año de los 18 años completos del dataset de HCDN (2008-2025, 1.340 leyes, cuatro presidencias), no el rango 15-47 observado bajo esta administración (ADR-0168)"),
    "judicializacion": ("historia_larga", "el techo es el 0,78% de densidad cautelar promedio de 2016-2019 —dos gobiernos anteriores al medido— contra 1,66% del promedio 2020-2026 (ADR-0168)"),
    "velocidad_resolucion": ("conceptual", "el 100% es el punto donde la Corte resuelve exactamente lo que le entra, sin acumular ni descargar atraso; los cortes son márgenes redondos alrededor de ese valor y no el rango observado 26-142 (ADR-0168)"),
    "paralisis_denuncias": ("conceptual", "cortes redondos sobre sesiones por año de dos comisiones —una por semestre, por trimestre, por bimestre—, no calibrados contra el rango observado 2-7 (ADR-0168)"),
    "brecha_obra_publica": ("conceptual", "números redondos alrededor del cero, explícitamente NO calibrados contra el rango observado (ADR-0088)"),
    "apoyo_empresario": ("conceptual", "el rango TEÓRICO del saldo (−1 a +1) partido en cinco tramos iguales y centrado en el cero —apoya tanto como critica—; no se mira el rango observado, que ni siquiera toca los extremos (ADR-0150)"),
    "bloqueo_sostenido": ("externa", "ninguna insistencia exitosa entre 2003 y 2025: ~100% histórico de sostenimiento (ADR-0069)"),
    "iaf_transferencias": ("conceptual", "variación real anclada en el cero con cortes simétricos de 10 pp, como recaudacion/emae del ITCM (ADR-0121)"),
    "alineamiento_senadores_prov": ("convencion", "recalibrada con 29 puntos propios de feb-2024 en adelante (ADR-0038)"),
    "adhesion_reformas_provincial": ("conceptual", "anclas NO tocadas: la adhesión es un evento irreversible y el rango de hoy es un punto de partida, no el rango final (ADR-0044)"),
    "cohesion_bloque": ("convencion", "calibrada contra su propia serie reconstruida desde 2024 (ADR-0042/0048)"),
    "conflictividad_nacional": ("convencion", "calibrada contra los 30 puntos propios de la serie ACLED desde 2024 (ADR-0052)"),

    # ── ITVC (ADR-0123) ──────────────────────────────────────────────────────
    # El ITVC no tiene bandas: cada componente se rebasea a 100 = 4T-2023 y el
    # índice promedia esos niveles. El ancla de TODOS es una FECHA FIJA (el
    # arranque del mandato), no un rango observado, así que no hay dónde
    # calibrar contra el período — son conceptuales por construcción. Es el
    # único índice sin una sola ancla de convención. La winsorización a 140
    # (base +40, ADR-0033) es un tope conceptual redondo, no calibrado al
    # boom observado; toca a dos componentes y se anota en su motivo.
    "brecha_salario_cbt": ("conceptual", "rebase base-100 a la fecha fija 4T-2023 (RIPTE/CBT), no al rango observado (ADR-0123)"),
    "informalidad": ("conceptual", "rebase base-100 a 4T-2023, invertido; ancla en la fecha fija (ADR-0123)"),
    "pobreza_nowcast": ("conceptual", "rebase base-100 al 2º semestre de 2023, invertido (ADR-0153). La base sale de la serie oficial del INDEC porque el nowcast mensual no llega al 4T-2023; el desvío del empalme está medido y declarado en la ficha"),
    "ipc_alimentos": ("conceptual", "encarecimiento relativo rebaseado a 4T-2023 (ADR-0033); ancla en fecha fija"),
    "peso_tarifas": ("conceptual", "nivel de regulados vs salario rebaseado a 4T-2023; ancla en fecha fija"),
    "alquiler_real": ("conceptual", "encarecimiento relativo del alquiler rebaseado a 4T-2023 (ADR-0111)"),
    "mora_familias": ("conceptual", "nivel B100 vs 4T-2023, invertido (ADR-0067); ancla en fecha fija"),
    "mortalidad_pymes": ("conceptual", "nivel del IPI desestacionalizado rebaseado a 4T-2023; ancla en fecha fija"),
    "despacho_cemento": ("conceptual", "nivel del ISAC desestacionalizado rebaseado a 4T-2023; ancla en fecha fija"),
    "pluriempleo": ("conceptual", "subocupación demandante rebaseada a 4T-2023, invertida; ancla en fecha fija"),
    "empleo_registrado": ("conceptual", "asalariados privados registrados (SIPA) rebaseados a 4T-2023, sin invertir (ADR-0130); ancla en fecha fija"),
    "icc_utdt": ("conceptual", "ICC rebaseado a 4T-2023; ancla en fecha fija"),
    "sentimiento_digital": ("conceptual", "canasta de búsquedas rebaseada a 4T-2023, invertida (ADR-0034); ancla en fecha fija"),
    "consumo_carne": ("conceptual", "consumo per cápita rebaseado a 4T-2023; ancla en fecha fija"),
    "patentamiento_motos": ("conceptual", "móvil 12m rebaseado a 4T-2023 (ADR-0024); el tope conceptual de 140 le recorta el boom, no lo calibra"),
    "inseguridad": ("conceptual", "IVI rebaseado a su base declarada ene-2024 (ADR-0032), también fecha fija, no rango observado"),
}


def _indicadores_del_indice():
    """{indicador: (sigla, peso_efectivo_nominal)} de los que PUNTÚAN hoy.

    El ITVC entra igual que los otros tres pese a no tener bandas: su
    DIMENSIONES_ITVC tiene la misma forma (peso de dimensión × peso interno) y
    sus componentes se clasifican por su ancla de rebase, no por cortes de banda
    (ADR-0123)."""
    out = {}
    for mod, sig in ((itcm, "ITCM"), (itcg, "ITCG"), (itcp, "ITCP"), (itvc, "ITVC")):
        dims = getattr(mod, f"DIMENSIONES_{sig}")
        for dim in dims.values():
            peso_dim = dim["peso"]
            for ind, peso_ind in dim["indicadores"].items():
                out[ind] = (sig, peso_dim * peso_ind)
    return out


def informe() -> dict:
    """Cuánto del peso de cada índice descansa en cada tipo de ancla."""
    indicadores = _indicadores_del_indice()
    por_indice = {}
    faltantes = []
    for ind, (sig, peso) in indicadores.items():
        if ind not in PROCEDENCIA:
            faltantes.append(ind)
            continue
        categoria, motivo = PROCEDENCIA[ind]
        bloque = por_indice.setdefault(sig, {"peso_total": 0.0, "categorias": {}, "detalle": []})
        bloque["peso_total"] += peso
        bloque["categorias"][categoria] = bloque["categorias"].get(categoria, 0.0) + peso
        bloque["detalle"].append({"indicador": ind, "categoria": categoria,
                                  "peso": round(peso, 4), "motivo": motivo})

    for sig, bloque in por_indice.items():
        total = bloque["peso_total"] or 1.0
        bloque["share"] = {c: round(p / total, 3) for c, p in bloque["categorias"].items()}
        # el número que la auditoría pide vigilar
        riesgo = sum(p for c, p in bloque["categorias"].items()
                     if c in ("convencion", "sin_declarar"))
        bloque["share_circular"] = round(riesgo / total, 3)
        bloque["detalle"].sort(key=lambda d: (CATEGORIAS.index(d["categoria"]), -d["peso"]))

    return {"por_indice": por_indice, "sin_clasificar": sorted(faltantes)}


def main():
    r = informe()
    if r["sin_clasificar"]:
        print(f"[WARN] indicadores sin procedencia declarada: {r['sin_clasificar']}")
    print("Procedencia de las anclas — cuánto del peso de cada índice es circular\n")
    for sig, b in sorted(r["por_indice"].items()):
        print(f"{sig}  (riesgo de circularidad: {b['share_circular']:.0%} del peso)")
        for cat in CATEGORIAS:
            if cat in b["share"]:
                print(f"    {cat:15s} {b['share'][cat]:5.0%}")
        print()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {SALIDA}")


if __name__ == "__main__":
    main()
