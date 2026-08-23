"""Las fichas metodológicas públicas no pueden afirmar ponderaciones que el
índice ya no usa.

Las fichas de /metodologia dicen cosas como «Pertenece a la dimensión de
prospectivas de empleo (20% interno · 3% del ITVC)». Ese número es verdadero el
día que se escribe y queda mentiroso la próxima vez que entra un indicador a la
misma dimensión: los existentes ceden peso proporcionalmente y nadie vuelve al
texto. Cuando `empleo_registrado` entró con 35%, los cuatro componentes de
prospectivas de empleo cedieron ×0,65 y las cuatro fichas siguieron publicando
los pesos viejos.

Lo encontró una auditoría de UI (29-jul-2026) de casualidad, mirando el Índice
Líder: la ficha decía 20% interno · 3% del ITVC cuando el real era 13% · 1,95%.
Al medirlo en todas, había DOCE fichas con el peso stale, y varias además con el
nombre de la dimensión anterior a su reorganización («confianza y seguridad»,
que hoy son dos dimensiones distintas).

Ningún gate podía verlo: gate_calidad.py valida datos y estructura del snapshot,
nunca cruza la prosa de la capa de display contra los pesos que usa el motor.
Mismo hueco que cerró test_web_labels.py para los rótulos.

Qué NO se valida acá, a propósito: las entradas de `cambios`, que son un
changelog — dicen el peso que tenía el indicador ESE día y tienen que quedar
como están. En el cuerpo vigente se cruzan tanto el par «N% interno · M% del
ÍNDICE» como la forma «dimensión (N% del total), donde pesa M%».
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FICHAS = (ROOT / "web/src/lib/fichas.ts").read_text(encoding="utf-8")
INFORME = json.loads((ROOT / "web/src/data/informe.json").read_text(encoding="utf-8-sig"))

TOLERANCIA_PP = 0.6      # el texto redondea; 0,6 pp deja pasar 3,15 vs 3,1


def _pesos_reales() -> dict:
    out = {}
    for c in INFORME["cinturones"].values():
        for sigla in ("itvc", "itcm", "itcg", "itcp"):
            idx = c.get(sigla)
            if not idx:
                continue
            for dv in (idx.get("dimensiones") or {}).values():
                for ikey, iv in (dv.get("indicadores") or {}).items():
                    out[ikey] = {"interno": (iv.get("peso") or 0) * 100,
                                 "efectivo": (iv.get("peso_efectivo") or 0) * 100,
                                 "dimension": (dv.get("peso") or 0) * 100}
    return out


def _incidencia_por_ficha() -> dict:
    """{clave: texto de incidenciaTexto}. Excluye `cambios` (changelog)."""
    out = {}
    for m in re.finditer(r"^  (\w+): \{$", FICHAS, re.M):
        fin = FICHAS.find("\n  },", m.end())
        cuerpo = FICHAS[m.end():fin]
        inc = re.search(r"incidenciaTexto:\s*\[(.*?)\]", cuerpo, re.S)
        if inc:
            out[m.group(1)] = inc.group(1)
    return out


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def test_los_pesos_que_afirman_las_fichas_son_los_vigentes():
    reales = _pesos_reales()
    problemas = []
    for clave, texto in _incidencia_por_ficha().items():
        real = reales.get(clave)
        if not real:
            continue
        mi = re.search(r"(\d+(?:,\d+)?)\s*%\s*interno", texto)
        if mi and abs(_num(mi.group(1)) - real["interno"]) > TOLERANCIA_PP:
            problemas.append(f"{clave}: ficha dice {mi.group(1)}% interno, "
                             f"real {real['interno']:.1f}%")
        # sólo la forma "· M% del ÍNDICE", que acompaña al peso interno; la que
        # cita el peso de la dimensión tiene otra redacción y no se toca
        me = re.search(r"·\s*(\d+(?:,\d+)?)\s*%\s*del\s*(?:ITVC|ITCM|ITCG|ITCP)", texto)
        if me and abs(_num(me.group(1)) - real["efectivo"]) > TOLERANCIA_PP:
            problemas.append(f"{clave}: ficha dice {me.group(1)}% del índice, "
                             f"real {real['efectivo']:.2f}%")

        # La otra forma que quedó fuera de la primera guarda fue «dimensión de
        # poder legislativo (25% del total), donde pesa 20%». Es una afirmación
        # pública tan concreta como el par interno/efectivo y debe cruzarse con
        # la misma fuente de verdad.
        md = re.search(
            r"dimensi[oó]n[^.()]{0,180}\((\d+(?:,\d+)?)\s*%\s*del\s*total\)",
            texto,
            re.I,
        )
        if md and abs(_num(md.group(1)) - real["dimension"]) > TOLERANCIA_PP:
            problemas.append(f"{clave}: ficha dice dimensión {md.group(1)}%, "
                             f"real {real['dimension']:.1f}%")

        mp = re.search(r"donde\s+pesa\s+(\d+(?:,\d+)?)\s*%", texto, re.I)
        if mp and abs(_num(mp.group(1)) - real["interno"]) > TOLERANCIA_PP:
            problemas.append(f"{clave}: ficha dice que pesa {mp.group(1)}% dentro "
                             f"de la dimensión, real {real['interno']:.1f}%")
    assert not problemas, (
        "fichas públicas con ponderación stale (entró un indicador a la dimensión "
        "y los demás cedieron peso sin que se actualice el texto):\n  "
        + "\n  ".join(problemas))


def _cuerpo_ficha(clave: str) -> str:
    m = re.search(rf"^  {re.escape(clave)}: \{{$", FICHAS, re.M)
    assert m, f"no se encontró la ficha {clave}"
    fin = FICHAS.find("\n  },", m.end())
    cuerpo = FICHAS[m.end():fin]
    # Los números del changelog son históricos y no describen la estructura
    # vigente; el contrato alcanza hasta el campo `cambios`.
    return cuerpo.split("\n    cambios:", 1)[0]


NUMERO_EN_LETRAS = {
    5: "cinco", 6: "seis", 7: "siete", 14: "catorce",
    17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
}


def test_las_fichas_de_indices_declaran_la_composicion_vigente():
    problemas = []
    for c in INFORME["cinturones"].values():
        for clave in ("itcm", "itcg", "itvc", "itcp"):
            idx = c.get(clave)
            if not idx:
                continue
            cuerpo = _cuerpo_ficha(clave).lower()
            n_dim = len(idx["dimensiones"])
            n_ind = sum(len(d.get("indicadores") or {})
                        for d in idx["dimensiones"].values())
            palabra_dim = NUMERO_EN_LETRAS[n_dim]
            palabra_ind = NUMERO_EN_LETRAS[n_ind]
            sustantivo = "componentes" if clave == "itvc" else "indicadores"
            if f"{palabra_dim} dimensiones" not in cuerpo:
                problemas.append(f"{clave}: no declara {n_dim} dimensiones")
            if f"{palabra_ind} {sustantivo}" not in cuerpo:
                problemas.append(f"{clave}: no declara {n_ind} {sustantivo}")
    assert not problemas, "fichas de índice con composición anterior:\n  " + "\n  ".join(problemas)


def test_la_leyenda_de_agregacion_itcp_usa_los_pesos_vigentes():
    idx = INFORME["cinturones"]["politica"]["itcp"]
    esperados = [round(d["peso"] * 100, 2) for d in idx["dimensiones"].values()]
    cuerpo = _cuerpo_ficha("itcp")
    leyenda = re.search(r'leyenda:\s*"([^"]+)"', cuerpo)
    assert leyenda, "la ficha del ITCP no declara su regla de agregación"
    publicados = [_num(n) for n in re.findall(r"\d+(?:,\d+)?", leyenda.group(1))]
    assert publicados == esperados, (
        f"ITCP publica pesos de dimensiones {publicados}, pero usa {esperados}"
    )


def test_el_test_mira_algo():
    """Guarda contra que el parseo quede vacío y el test pase por no leer nada."""
    inc = _incidencia_por_ficha()
    reales = _pesos_reales()
    con_peso = [k for k, t in inc.items()
                if k in reales and re.search(r"\d+(?:,\d+)?\s*%\s*interno", t)]
    # Al 29-jul-2026: 32 fichas con incidenciaTexto, 12 de ellas declarando peso
    # interno — que son justo las 12 que estaban stale. Los pisos van por debajo
    # para no romper cada vez que se suma una ficha, pero lo bastante alto como
    # para que un parseo roto no pase inadvertido.
    assert len(inc) >= 28, f"sólo se parsearon {len(inc)} fichas: ¿cambió el formato?"
    assert len(con_peso) >= 10, f"sólo {len(con_peso)} fichas declaran peso interno"
