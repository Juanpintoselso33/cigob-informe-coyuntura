# -*- coding: utf-8 -*-
"""La búsqueda sobre ADR indexa el cuerpo entero, no lo que quede después del
primer guión.

El bug que motivó estos tests: partir el archivo por "---" a secas para sacar el
frontmatter también parte por las reglas horizontales del cuerpo, que en MADR
están en casi todos los ADR. El encabezado quedaba fuera del índice y el título
volvía como nombre de archivo — o sea que la búsqueda no encontraba por título,
que es justo donde está enunciada la decisión.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import adr_buscar as ab  # noqa: E402


def _escribir(tmp_path, nombre, texto):
    p = tmp_path / nombre
    p.write_text(texto, encoding="utf-8")
    return p


CON_REGLA = """---
madr: 4
id: '0001'
---

# ADR-0001 — El título que hay que encontrar

Un párrafo cualquiera con la palabra jacaranda.

---

## Otra sección
Más texto, con la palabra tarambana.
"""


def test_saca_el_frontmatter_y_conserva_el_cuerpo(tmp_path):
    p = _escribir(tmp_path, "0001-x.md", CON_REGLA)
    titulo, cuerpo = ab._cuerpo(p)
    assert titulo == "ADR-0001 — El título que hay que encontrar"
    assert "madr: 4" not in cuerpo          # el frontmatter no entra al índice
    assert "jacaranda" in cuerpo
    assert "tarambana" in cuerpo            # lo que estaba después de la regla


def test_el_titulo_no_degrada_a_nombre_de_archivo(tmp_path):
    p = _escribir(tmp_path, "0002-y.md", CON_REGLA.replace("0001", "0002"))
    titulo, _ = ab._cuerpo(p)
    assert not titulo.startswith("0002-")


def test_normalizar_saca_tildes_y_vacias():
    """Nadie escribe tildes al buscar desde la terminal; una consulta sin
    tildes no puede quedarse sin resultados por eso."""
    assert ab._normalizar("La RENORMALIZACIÓN de los pesos") == ["renormalizacion", "pesos"]
    assert ab._normalizar("el de la y con") == []


def test_el_titulo_pesa_mas_que_el_cuerpo(tmp_path):
    """Un acierto en el título casi siempre es el resultado bueno, así que el
    ranking tiene que preferirlo sobre una mención suelta en el cuerpo."""
    _escribir(tmp_path, "0010-a.md", "---\nid: '0010'\n---\n\n"
              "# ADR-0010 — Cobertura de las series\n\nTexto sin relación.\n")
    _escribir(tmp_path, "0011-b.md", "---\nid: '0011'\n---\n\n"
              "# ADR-0011 — Otra cosa\n\nAcá se menciona cobertura una vez.\n")
    ab.ADR, previo = tmp_path, ab.ADR
    try:
        docs = ab.cargar()
        ranking = ab.puntuar(docs, ab._normalizar("cobertura"))
    finally:
        ab.ADR = previo
    assert ranking[0][1]["id"] == "0010"


def test_el_corpus_real_se_indexa_entero():
    """Contrato sobre los ADR de verdad: todos tienen título extraído. Si vuelve
    a fallar el recorte del frontmatter, este test lo agarra."""
    docs = ab.cargar()
    assert len(docs) > 150
    sin_titulo = [d["id"] for d in docs if d["titulo"] == d["archivo"][:-3]]
    assert not sin_titulo, f"ADR sin título extraído: {sin_titulo}"


def test_busca_algo_conocido_del_corpus_real():
    docs = ab.cargar()
    ranking = ab.puntuar(docs, ab._normalizar("piso de cobertura de las series reconstruidas"))
    assert ranking, "una consulta con vocabulario del corpus no puede dar vacío"
    assert "0197" in [d["id"] for _, d in ranking[:5]]
