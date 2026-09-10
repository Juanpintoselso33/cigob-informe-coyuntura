"""El portal vigente publica PDFs relativos; un fallo de parseo debe reintentarse."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import descargar_series as ds


def test_ivi_descubre_relativos_y_no_consume_pdf_ilegible(tmp_path, monkeypatch):
    store = tmp_path / 'ivi.json'
    monkeypatch.setattr(ds, 'IVI_SERIE_STORE', store)
    urls = []
    def get(url, **kwargs):
        urls.append(url)
        html = ('<a href="/download.php?fname=julio.pdf">Julio</a>'
                '<a href="https://www.utdt.edu/download.php?fname=mal.pdf">Error</a>')
        return SimpleNamespace(text=html, content=url.encode(), raise_for_status=lambda: None)
    monkeypatch.setattr(ds.requests, 'get', get)
    monkeypatch.setattr(ds, '_ivi_parse_pdf', lambda b: ('2026-07', 27.3) if b.endswith(b'julio.pdf') else None)
    assert ds.fetch_ivi_serie() == [['2026-07-01', 27.3]]
    assert 'https://www.utdt.edu/ver_contenido.php?id_contenido=968&id_item_menu=2156' in urls
    saved = json.loads(store.read_text())
    assert saved['procesados'] == ['https://www.utdt.edu/download.php?fname=julio.pdf']
    urls.clear()
    ds.fetch_ivi_serie()
    assert 'https://www.utdt.edu/download.php?fname=mal.pdf' in urls
    assert 'https://www.utdt.edu/download.php?fname=julio.pdf' not in urls


def test_pdf_ilegible_va_al_final_de_la_cola_y_sale_tras_tres_intentos(tmp_path, monkeypatch, capsys):
    from cotejo_manual import avisos
    store = tmp_path / 'ivi.json'
    monkeypatch.setattr(ds, 'IVI_SERIE_STORE', store)
    urls = []
    listado = ['<a href="/download.php?fname=julio.pdf">Julio</a>',
               '<a href="https://www.utdt.edu/download.php?fname=mal.pdf">Error</a>']
    def get(url, **kwargs):
        urls.append(url)
        return SimpleNamespace(text=''.join(listado), content=url.encode(), raise_for_status=lambda: None)
    monkeypatch.setattr(ds.requests, 'get', get)
    valores = {b'julio.pdf': ('2026-07', 27.3), b'abril.pdf': ('2026-04', 26.0)}
    monkeypatch.setattr(ds, '_ivi_parse_pdf',
                        lambda b: next((v for fin, v in valores.items() if b.endswith(fin)), None))
    mal = 'https://www.utdt.edu/download.php?fname=mal.pdf'
    abril = 'https://www.utdt.edu/download.php?fname=abril.pdf'
    ds.fetch_ivi_serie()
    listado.append('<a href="/download.php?fname=abril.pdf">Abril</a>')
    urls.clear()
    ds.fetch_ivi_serie()
    assert urls.index(abril) < urls.index(mal)
    ds.fetch_ivi_serie()
    guardado = json.loads(store.read_text())
    assert guardado['fallidos'][mal]['intentos'] == 3
    assert avisos(capsys.readouterr().err) == []
    urls.clear()
    assert ds.fetch_ivi_serie() == [['2026-04-01', 26.0], ['2026-07-01', 27.3]]
    assert mal not in urls
    mensajes = avisos(capsys.readouterr().err)
    assert len(mensajes) == 1 and 'mal.pdf' in mensajes[0] and 'inseguridad' in mensajes[0]
