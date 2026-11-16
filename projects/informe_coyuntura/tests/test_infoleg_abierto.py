"""Producción legislativa desde la base abierta de InfoLeg (ADR-0435). Sin red."""
import io
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

import infoleg_abierto as ia  # noqa: E402
import politica  # noqa: E402

_LEYES_SANCIONADAS = ia.leyes_sancionadas   # la real, antes del conftest

CSV = ("id_norma,tipo_norma,numero_norma,fecha_sancion,fecha_boletin\n"
       "1,Ley,27828,2026-09-24,2026-10-13\n"
       "2,Decreto,700,2026-09-30,2026-10-01\n"
       "3,Ley,27827,2026-09-17,2026-10-09\n"
       "4,Ley,S/N,2026-09-17,2026-10-09\n")


class _Resp:
    def __init__(self, content=None, json_=None):
        self.content, self._json = content, json_

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


@pytest.fixture
def base(monkeypatch):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("base-infoleg-normativa-nacional.csv", CSV)
    paquete = {"result": {"results": [{"resources": [
        {"format": "CSV", "name": "Base Infoleg Normativa Nacional - Muestreo", "url": "x.csv"},
        {"format": "ZIP", "name": "Base Infoleg Normativa Nacional", "url": "https://x/base.zip"}]}]}}
    monkeypatch.setattr(ia, "_LEYES", None)
    monkeypatch.setattr(ia, "leyes_sancionadas", _LEYES_SANCIONADAS)
    monkeypatch.setattr(ia.requests, "get", lambda url, **k: _Resp(json_=paquete) if "package_search" in url
                        else _Resp(content=buf.getvalue()))


def test_solo_leyes_numeradas_con_su_sancion(base):
    assert sorted(ia.leyes_sancionadas()) == [("ley:27827", date(2026, 9, 17)),
                                             ("ley:27828", date(2026, 9, 24))]


def test_produccion_usa_infoleg_si_el_ckan_no_responde(base, monkeypatch):
    def caido(*a, **k):
        raise requests.ConnectionError("datos.hcdn.gob.ar 503")
    monkeypatch.setattr(politica, "_hcdn_paginate", caido)
    leyes, fuente = politica._leyes_produccion()
    assert len(leyes) == 2 and "InfoLeg" in fuente


def test_un_dato_invalido_del_ckan_no_pasa_a_infoleg(monkeypatch):
    def invalido(*a, **k):
        raise ValueError("leyes-sancionadas vacío")
    monkeypatch.setattr(politica, "_hcdn_paginate", invalido)
    with pytest.raises(ValueError):
        politica._leyes_produccion()
