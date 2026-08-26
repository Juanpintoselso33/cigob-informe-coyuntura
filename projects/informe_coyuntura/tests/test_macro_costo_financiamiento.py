"""Tests de costo_financiamiento_tesoro (ADR-0071): TIREA implícita de una
colocación, filtro de instrumentos comparables, escala de U invertida y
composición de la dimensión de financiamiento.

Los casos de la TIREA usan colocaciones REALES verificadas contra las
gacetillas de la Secretaría de Finanzas, para que el test falle si alguien
cambia la convención de cálculo sin querer.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import macro
import itcm
import parametrica


def _d(iso: str) -> datetime:
    return datetime.strptime(iso, "%Y-%m-%d")


# ── TIREA de una colocación ──────────────────────────────────────────────────
# ADR-0238: la TIREA de una emisión nueva a la par no se estima, se lee. Lo que
# había antes reconstruía esa tasa desde precio y fechas capitalizando por meses
# de CALENDARIO enteros, y en la S13N6 eso publicó 32,17% donde la Secretaría
# informó 28,32%.
#
# ADR-0258: pero leer el cupón sólo es correcto A LA PAR. En una reapertura el
# cupón fija el flujo y el precio de corte fija el rendimiento, y son cosas
# distintas: en la S30N6 del 15-jul-2026 el cupón anualizado daba 31,37% contra
# una TIREA de corte oficial de 25,59%. Ahora hay una sola cuenta —descontar el
# flujo contra el precio— que a la par devuelve exactamente el cupón anualizado.

FIXTURE = Path(__file__).parent / "fixtures" / "colocaciones_2026_06.json"
FIXTURE_JULIO = Path(__file__).parent / "fixtures" / "colocaciones_2026_07.json"
FIXTURE_OFICIALES = Path(__file__).parent / "fixtures" / "tireas_corte_oficiales.json"


def _colocaciones_de_junio():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _colocaciones_de_julio():
    return json.loads(FIXTURE_JULIO.read_text(encoding="utf-8"))


def _tirea(f, precio=None):
    """TIREA de corte de una fila de fixture."""
    return macro._tirea_de_fila(
        f["cupon"], _d(f["emision"]), _d(f["vencimiento"]), _d(f["colocacion"]),
        f["precio_emision"] if precio is None else precio,
    )


def _ponderada(doc):
    """(TIREA ponderada por valor efectivo, n) de las filas comparables."""
    suma = peso = 0.0
    n = 0
    for f in doc["filas"]:
        if f["moneda_origen"] != "ARP":
            continue
        t = _tirea(f)
        if t is None:
            continue
        suma += t * f["valor_efectivo"]
        peso += f["valor_efectivo"]
        n += 1
    return suma / peso, n


def test_la_lecap_de_la_licitacion_auditada_da_la_tasa_oficial():
    """S13N6, emitida a la par el 30-06-2026 a TEM 2,1%.

    Es EL caso de la auditoría del 25-ago-2026: $4,18 billones adjudicados, la
    única colocación a tasa fija en pesos del mes. (1,021)^12-1 = 28,32%, que
    es lo que informaron la Secretaría y el mercado."""
    doc = _colocaciones_de_junio()
    lecap = [f for f in doc["filas"] if f["instrumento"] == "LECAP/$/13-11-2026"]
    assert len(lecap) == 1, "la licitación auditada tiene una sola LECAP"
    t = _tirea(lecap[0])
    assert t is not None
    assert abs(t * 100 - 28.32) < 0.01, f"TIREA {t * 100:.2f}% ≠ 28,32% oficial"


def test_el_valor_erroneo_no_puede_volver():
    """32,17% salía de capitalizar 5 meses de calendario sobre 4,5 corridos.

    Este test no comprueba una convención: comprueba que ESE número, el que se
    publicó cuatro semanas, no puede reaparecer para este instrumento."""
    doc = _colocaciones_de_junio()
    f = [x for x in doc["filas"] if x["instrumento"] == "LECAP/$/13-11-2026"][0]
    assert abs(_tirea(f) * 100 - 32.17) > 1.0, "volvió la TIREA por meses de calendario"


def test_la_licitacion_completa_reproduce_el_dato_real_corregido():
    """La cuenta entera de junio: TIREA ponderada contra el REM del mes.

    Con 22,3% de inflación esperada, 28,32% nominal son ~4,9% reales, no los
    8,07% publicados. Recorre las 17 filas de la licitación, no sólo la que
    puntúa, así que también prueba que las otras 16 quedan afuera.

    Junio es además la comprobación de que ADR-0258 NO tocó el caso a la par:
    su única colocación se emitió a la par y tiene que seguir dando lo mismo."""
    doc = _colocaciones_de_junio()
    tirea, n = _ponderada(doc)
    assert n == 1, f"{n} colocaciones a tasa fija en pesos; la licitación tuvo una"
    real = ((1 + tirea) / (1 + doc["_rem_ipc_12m_2026_06"] / 100.0) - 1) * 100.0
    assert abs(real - 4.92) < 0.05, f"{real:.2f}% real; la auditoría verificó ~4,92%"
    assert abs(real - 8.07) > 1.0, "volvió el valor publicado que la auditoría rechazó"


# ── La reapertura: el caso de ADR-0258 ───────────────────────────────────────

def test_la_reapertura_auditada_usa_la_tasa_de_corte_y_no_el_cupon():
    """S30N6 reabierta el 15-07-2026 a un precio de corte de $1.194.

    La Secretaría publicó **TIREA de corte 25,59%** (TEM marginal 1,92%) para
    esa reapertura; su cupón contractual es TEM 2,30%, que anualizado da
    31,37%. El indicador publicaba 31,37%. Son 578 puntos básicos sobre el
    costo real de la colocación."""
    doc = _colocaciones_de_julio()
    filas = [f for f in doc["filas"] if f["instrumento"] == "LECAP/$/30-11-2026"]
    assert len(filas) == 1, "julio tuvo una sola reapertura de la S30N6"
    f = filas[0]
    assert f["precio_emision"] == 1194.0, "el fixture perdió el precio de corte"
    t = _tirea(f) * 100
    oficial = doc["_tirea_corte_oficial"]["S30N6"]["tirea"]
    assert abs(t - oficial) < 0.5, f"TIREA de corte {t:.2f}% ≠ {oficial}% oficial"
    assert abs(t - 31.37) > 3.0, "volvió el cupón anualizado en una reapertura"


def test_el_costo_de_julio_no_puede_volver_a_dar_5_80():
    """La cuenta entera de julio de 2026, las dos colocaciones a tasa fija.

    Ponderando por valor efectivo (S30N6 $2,38 bill. + S16O6 $4,61 bill.) la
    TIREA de corte del mes es ~26,8%, no 28,87%; contra un REM de 21,8% eso son
    ~4,1% reales, no los 5,80% que se publicaron. Recorre las 15 filas del mes
    para probar de paso que las de dólar, CER y TAMAR quedan afuera."""
    doc = _colocaciones_de_julio()
    tirea, n = _ponderada(doc)
    assert n == 2, f"{n} colocaciones a tasa fija en pesos; julio tuvo dos"
    real = ((1 + tirea) / (1 + doc["_rem_ipc_12m_2026_07"] / 100.0) - 1) * 100.0
    assert abs(real - 4.13) < 0.15, f"{real:.2f}% real; se reconstruyó ~4,13%"
    assert abs(real - 5.80) > 1.0, "volvió el 5,80% que la reauditoría rechazó"


def test_la_emision_nueva_de_julio_si_sale_del_cupon():
    """La otra colocación de julio, la S16O6 del 29-07: nueva y a la par.

    Ahí el precio no aporta información y la tasa de corte ES el cupón
    anualizado: TEM 2,05% → 27,57%, que es lo que informó la Secretaría. Es la
    mitad del mes que ya estaba bien, y tiene que seguir estándolo."""
    doc = _colocaciones_de_julio()
    f = [x for x in doc["filas"] if x["instrumento"] == "LECAP/$/16-10-2026"][0]
    assert abs(_tirea(f) * 100 - 27.57) < 0.01
    assert abs(macro._tirea_contractual(f["cupon"]) * 100 - 27.57) < 0.01


def test_a_la_par_la_tasa_de_corte_es_el_cupon_anualizado():
    """El invariante que sostiene toda la corrección, y es EXACTO.

    Con `precio = 1000` y `colocación = emisión`, descontar el flujo contra el
    precio devuelve `(1+TEM)^12 - 1` idénticamente: los exponentes se cancelan.
    Por eso ADR-0258 pudo reemplazar las dos ramas por una sin cambiar ningún
    valor a la par. Si esta igualdad deja de ser exacta, la convención de días
    del payoff y la de la anualización dejaron de ser la misma.

    La tolerancia es 1e-12 (una diezmilmillonésima de punto porcentual) y está
    sólo para el redondeo del punto flotante: la identidad es algebraica, no
    aproximada. ADR-0238 admitía acá 5 pb, que es 10^8 veces más."""
    casos = [("Tasa efectiva mensual capitalizable 2,10%.", "2026-06-30", "2026-11-13"),
             ("Tasa efectiva mensual capitalizable 2,05%.", "2026-07-31", "2026-10-16"),
             ("Tasa efectiva mensual capitalizable 3,53%.", "2025-09-30", "2026-04-30"),
             ("Tasa efectiva mensual capitalizable 2,30%.", "2025-12-15", "2026-11-30")]
    for cup, emi, ven in casos:
        corte = macro._tirea_de_fila(cup, _d(emi), _d(ven), _d(emi), 1000.0)
        assert abs(corte - macro._tirea_contractual(cup)) < 1e-12, (
            f"{cup}: a la par {corte} ≠ cupón {macro._tirea_contractual(cup)}")
    # y también sobre las filas reales de los fixtures
    for doc in (_colocaciones_de_junio(), _colocaciones_de_julio()):
        a_la_par = [f for f in doc["filas"]
                    if f["moneda_origen"] == "ARP"
                    and abs(f["precio_emision"] - 1000) < 1e-9
                    and f["emision"] == f["colocacion"]
                    and macro._tem_capitalizable(f["cupon"]) is not None]
        assert a_la_par, "el fixture perdió la emisión nueva a la par"
        for f in a_la_par:
            assert abs(_tirea(f) - macro._tirea_contractual(f["cupon"])) < 1e-12, (
                f["instrumento"])


def test_la_tasa_de_corte_si_depende_del_precio():
    """El test que ADR-0258 tuvo que dar vuelta.

    Hasta agosto de 2026 acá se afirmaba lo contrario —«una reapertura fuera de
    la par conserva la tasa de su cupón»— y esa afirmación ERA el error: dejaba
    el indicador midiendo la tasa contractual del instrumento en vez del costo
    de la colocación. El flujo de una reapertura ya está fijado por el cupón, así
    que pagar más por él rinde menos: la tasa tiene que caer monótonamente con el
    precio de corte, y a la tasa contractual no le pasa nada."""
    args = ("Tasa efectiva mensual capitalizable 2,30%.",
            _d("2025-12-15"), _d("2026-11-30"), _d("2026-07-17"))
    tasas = [macro._tirea_de_fila(*args, p) for p in (1100.0, 1150.0, 1194.0, 1250.0)]
    assert all(a > b for a, b in zip(tasas, tasas[1:])), tasas
    assert len(set(tasas)) == 4, "el precio de corte volvió a ser irrelevante"
    # el cupón, en cambio, no se entera del precio: por eso no sirve acá
    assert macro._tirea_contractual(args[0]) is not None
    # y el caso real: la S30N6 a $1.194 rinde la tasa de corte oficial, 25,59%
    assert abs(tasas[2] * 100 - 25.59) < 0.5
    assert abs(macro._tirea_contractual(args[0]) * 100 - 31.37) < 0.01


def test_la_convencion_reproduce_las_tireas_de_corte_publicadas():
    """El gate de la convención: mes = 365/12 días, año = 365 días.

    No es una elección de estilo. Se determinó ajustando las dos bases contra
    catorce TIREA de corte publicadas por la Secretaría entre julio de 2025 y
    agosto de 2026 —precios de $1.010 a $1.518, plazos de 15 a 518 días, tasas
    de 25% a 65%—. Con 30 y 360, que es lo que se había supuesto, el desvío
    crece cuanto más corto es el plazo remanente y llega a 2,7 pp.

    Cada observación trae la URL de su gacetilla en el fixture."""
    doc = json.loads(FIXTURE_OFICIALES.read_text(encoding="utf-8"))
    obs = [o for o in doc["observaciones"] if "descuento_hasta" not in o]
    assert len(obs) >= 13, "el fixture perdió observaciones"
    desvios = []
    for o in obs:
        t = macro._tirea_de_fila(o["cupon"], _d(o["emision"]), _d(o["vencimiento"]),
                                 _d(o["colocacion"]), o["precio_de_corte"])
        assert t is not None, o["ticker"]
        desvios.append(abs(t * 100 - o["tirea_oficial"]))
    rmse = (sum(d * d for d in desvios) / len(desvios)) ** 0.5
    assert rmse < 0.6, f"RMSE {rmse:.3f} pp contra las TIREA de corte oficiales"
    assert max(desvios) < 1.5, f"desvío máximo {max(desvios):.2f} pp"


def test_el_cupon_anualizado_no_sirve_para_una_reapertura():
    """La otra mitad del gate anterior: sirve para probar que la alternativa es
    peor, no sólo que la elegida es buena.

    Sobre las mismas observaciones, publicar el cupón anualizado —lo que hacía
    el colector— se desvía un orden de magnitud más, y en los dos sentidos: la
    S30A6 de nov-2025 lo sobreestimaba 16 pp y la S31O5 de jul-2025 lo
    subestimaba 14 pp. No es un sesgo que se pueda corregir con un ajuste."""
    doc = json.loads(FIXTURE_OFICIALES.read_text(encoding="utf-8"))
    obs = [o for o in doc["observaciones"] if "descuento_hasta" not in o]
    cupon = [macro._tirea_contractual(o["cupon"]) * 100 - o["tirea_oficial"] for o in obs]
    corte = [macro._tirea_de_fila(o["cupon"], _d(o["emision"]), _d(o["vencimiento"]),
                                  _d(o["colocacion"]), o["precio_de_corte"]) * 100
             - o["tirea_oficial"] for o in obs]
    rmse = lambda xs: (sum(x * x for x in xs) / len(xs)) ** 0.5
    assert rmse(cupon) > 10 * rmse(corte), (
        f"cupón {rmse(cupon):.2f} pp vs corte {rmse(corte):.2f} pp")
    assert max(cupon) > 10 and min(cupon) < -10, "el desvío del cupón va en los dos sentidos"


def test_la_reapertura_con_feriado_queda_declarada_y_no_se_silencia():
    """La única observación que la convención NO reproduce, y por qué.

    La S15G5 del 29-jul-2025 cayó en un feriado y la propia gacetilla aclara
    que el cálculo se hizo a la fecha de pago, 18/8, no al vencimiento, 15/8.
    El colector no puede saberlo: la planilla sólo trae el vencimiento. Con la
    fecha correcta la convención vuelve a dar la tasa oficial, así que el
    desvío es del dato de entrada y no de la fórmula — y este test lo prueba en
    vez de dejar el caso afuera sin explicación."""
    doc = json.loads(FIXTURE_OFICIALES.read_text(encoding="utf-8"))
    o = [x for x in doc["observaciones"] if x["ticker"] == "S15G5"][0]
    assert o["descuento_hasta"] == "2025-08-18"
    con_vencimiento = macro._tirea_de_fila(
        o["cupon"], _d(o["emision"]), _d(o["vencimiento"]), _d(o["colocacion"]),
        o["precio_de_corte"]) * 100
    assert con_vencimiento - o["tirea_oficial"] > 5, "el caso dejó de ser el borde que era"
    # misma fórmula, descontando hasta la fecha de pago que declara la gacetilla
    payoff = 1000.0 * (1.0 + macro._tem_capitalizable(o["cupon"])) ** (
        (_d(o["vencimiento"]) - _d(o["emision"])).days / macro._MES_DIAS)
    dias = (_d(o["descuento_hasta"]) - _d(o["colocacion"])).days
    con_pago = ((payoff / o["precio_de_corte"]) ** (365.0 / dias) - 1.0) * 100
    assert abs(con_pago - o["tirea_oficial"]) < 0.6, (
        f"{con_pago:.2f}% con la fecha de pago; oficial {o['tirea_oficial']}%")


def test_el_inventario_muestra_las_dos_tasas():
    """La card tiene que poder mostrar de qué salió el número.

    Publicar 26,8% de promedio sin decir que una de las dos colocaciones fue
    una reapertura que cortó casi 6 pp por debajo de su cupón es lo que dejó
    pasar 31,37% sin que nadie lo revisara. `_entrada_inventario` es lo que
    arma esa fila; acá se la ejercita con los datos reales de julio."""
    doc = _colocaciones_de_julio()
    entradas = []
    for f in doc["filas"]:
        if f["moneda_origen"] != "ARP":
            continue
        t = _tirea(f)
        if t is None:
            continue
        entradas.append(macro._entrada_inventario(
            f["instrumento"], f["cupon"], _d(f["emision"]), _d(f["colocacion"]),
            f["precio_emision"], f["valor_efectivo"], t))
    assert len(entradas) == 2, "julio aporta dos colocaciones al inventario"
    reaperturas = [e for e in entradas if e["reapertura"]]
    nuevas = [e for e in entradas if not e["reapertura"]]
    assert len(reaperturas) == 1 and len(nuevas) == 1, entradas

    reap = reaperturas[0]
    assert reap["instrumento"] == "LECAP/$/30-11-2026"
    assert reap["precio_corte"] == 1194.0
    assert reap["tirea_contractual"] == 31.37, "el cupón anualizado dejó de viajar"
    assert reap["tirea"] < reap["tirea_contractual"] - 3.0, (
        f'una reapertura sobre la par no puede rendir {reap["tirea"]}% '
        f'contra un cupón de {reap["tirea_contractual"]}%')

    nueva = nuevas[0]
    assert nueva["instrumento"] == "LECAP/$/16-10-2026"
    assert nueva["tirea"] == nueva["tirea_contractual"] == 27.57


def test_tirea_a_descuento_letra_de_2023():
    """Las LEDE de 2023 no capitalizan ni publican TEM: pagan 1.000 al
    vencimiento, así que ahí la tasa SÍ hay que reconstruirla desde el precio.
    La primera licitación de la gestión cortó muy por debajo de la par.

    ADR-0258 no las tocó: son el mismo descuento contra el precio con un payoff
    de 1.000 en vez de uno capitalizado."""
    t = macro._tirea_de_fila(
        "A descuento",
        datetime(2023, 12, 20), datetime(2024, 1, 18), datetime(2023, 12, 20),
        926.0,
    )
    assert t is not None and t > 1.0, f"TIREA {t} — se esperaba > 100% anual"


def test_instrumentos_no_comparables_quedan_afuera():
    """CER, dólar linked y tasa variable no tienen una tasa fija comparable:
    promediarlos con las LECAP mezclaría semánticas distintas.

    `TAMAR TEM` importa aparte: dice «capitalizable» pero no trae número, así
    que el filtro no puede ser la palabra."""
    for cupon in ("Cupón cero con ajuste por CER",
                  "Tasa efectiva mensual “TAMAR TEM”",
                  'Tasa efectiva mensual capitalizable “TAMAR TEM" + margen',
                  "Vinculada al dólar estadounidense"):
        assert macro._tirea_de_fila(
            cupon, datetime(2025, 1, 1), datetime(2026, 1, 1),
            datetime(2025, 6, 1), 1000.0,
        ) is None, f"{cupon!r} no debería puntuar"


def test_las_filas_no_comparables_de_julio_quedan_afuera():
    """Julio de 2026 trae BONAR y LELINK en dólares, un BONCER dual y dos TAMAR
    en pesos. Ninguna puede aportar a una tasa fija en pesos."""
    doc = _colocaciones_de_julio()
    assert [f for f in doc["filas"] if f["moneda_origen"] == "USD"], "faltan las de dólar"
    tamar = [f for f in doc["filas"]
             if f["moneda_origen"] == "ARP" and "TAMAR" in f["cupon"]]
    assert tamar, "el fixture perdió las colocaciones TAMAR"
    for f in tamar:
        assert _tirea(f) is None, f'{f["instrumento"]} no debería puntuar'


def test_fila_corrupta_no_rompe():
    """Vencimiento anterior a la colocación → sin TIREA, sin excepción."""
    assert macro._tirea_de_fila(
        "Tasa efectiva mensual capitalizable 2,00%.",
        datetime(2025, 1, 1), datetime(2025, 6, 1), datetime(2025, 12, 1), 1000.0,
    ) is None


def test_fila_sin_vida_no_rompe():
    """Vencimiento igual o anterior a la emisión: el payoff no existe.

    Es la fila corrupta peligrosa, porque sin la guarda **no falla**: el payoff
    queda en 1.000 —capitalizar cero meses— y un precio por debajo de la par
    devuelve una tasa de aspecto perfectamente normal. Con `emi = ven` y un
    precio de $950 salen 35,9% anual salidos de la nada, y entrarían al
    promedio ponderado del mes sin que nada avise."""
    for emi, ven in ((datetime(2026, 1, 1), datetime(2026, 1, 1)),
                     (datetime(2026, 6, 1), datetime(2026, 1, 1))):
        assert macro._tirea_de_fila(
            "Tasa efectiva mensual capitalizable 2,00%.",
            emi, ven, datetime(2025, 11, 1), 950.0,
        ) is None, f"emisión {emi:%Y-%m-%d} / vencimiento {ven:%Y-%m-%d}"


# ── Escala de U invertida ────────────────────────────────────────────────────

def _p(valor):
    return parametrica.puntaje_interpolado(
        valor, itcm.BANDAS_ITCM["costo_financiamiento_tesoro"])


def test_los_dos_extremos_estan_castigados():
    """Es la única banda no monótona del ITCM: represión y bola de nieve
    puntúan mal, el óptimo está en el medio."""
    assert _p(-12.2) == 20.0      # dic-2023, licuación
    assert _p(33.5) == 15.0       # ago-2025, bola de nieve
    assert _p(3.0) == 100.0       # zona sana


def test_la_curva_sube_y_despues_baja():
    """Verificación explícita de la forma de U invertida."""
    tramo_sube = [_p(v) for v in (-10, -5, -2.5, 0, 3)]
    tramo_baja = [_p(v) for v in (3, 6, 9, 16, 20, 30)]
    assert tramo_sube == sorted(tramo_sube), tramo_sube
    assert tramo_baja == sorted(tramo_baja, reverse=True), tramo_baja


def test_valor_vigente_puntua_en_zona_alta():
    """+4,9% real (jun-2026, ya corregido) sigue en la zona sana de la U.

    El 8,07% anterior también caía en verde, así que el color no cambió: lo que
    cambió es el nivel, y por eso el test mira el puntaje y no el semáforo."""
    assert 90.0 < _p(4.92) <= 100.0


# ── Dimensión de financiamiento ──────────────────────────────────────────────

def test_la_dimension_incluye_el_costo_y_suma_uno():
    dim = itcm.DIMENSIONES_ITCM["financiamiento"]
    assert "costo_financiamiento_tesoro" in dim["indicadores"]
    assert abs(sum(dim["indicadores"].values()) - 1.0) < 1e-9


def test_el_costo_toma_un_cuarto_de_la_dimension():
    """ADR-0071: el nuevo indicador toma 25%, y reservas conserva el recorte
    proporcional (45 × 0,75)."""
    ind = itcm.DIMENSIONES_ITCM["financiamiento"]["indicadores"]
    assert ind["costo_financiamiento_tesoro"] == 0.25
    assert abs(ind["reservas_bcra"] - 0.45 * 0.75) < 0.011


def test_la_capacidad_de_fondeo_no_pesa_mas_que_el_credito_realizado():
    """ADR-0074: el IdC declara en su propia validación que NO anticipa el
    crédito futuro; es un descriptor de condiciones, no un pronóstico. Que
    pesara 2,7× el crédito efectivamente otorgado invertía la jerarquía."""
    ind = itcm.DIMENSIONES_ITCM["financiamiento"]["indicadores"]
    assert abs(ind["idc"] - ind["credito_privado"]) <= 0.01, (
        f'idc {ind["idc"]} vs credito {ind["credito_privado"]}')


def test_el_indicador_esta_declarado_como_esperado():
    assert "costo_financiamiento_tesoro" in macro.INDICADORES_ESPERADOS
