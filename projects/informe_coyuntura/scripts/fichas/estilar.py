"""Estilo de las tablas del .docx y control de los cortes de página.

pandoc arma las tablas sin bordes, sin encabezado distinguido y sin ninguna
de las propiedades de Word que gobiernan qué pasa cuando una tabla cruza el
final de la página. Acá se aplican después, sobre el archivo ya convertido.

Lo que resuelve, en orden de lo que más molesta al leer:

1. Una fila partida al medio por el corte de página (`cantSplit`).
2. Una tabla que sigue en la página siguiente sin encabezado, así que las
   columnas quedan sin nombre (`tblHeader` en la primera fila).
3. Un título al pie de página con su contenido recién en la siguiente
   (`keepNext` en los headings y en el párrafo que los sigue).

Y el estilo: bordes finos, encabezado con fondo, filas alternadas, y las
celdas de color pintadas con la paleta del proyecto — misma que
web/public/dashboard.css, para que la ficha impresa y la página no muestren
dos verdes distintos.
"""
import sys
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt

# Paleta del proyecto (web/public/dashboard.css): fondo suave + texto fuerte.
# El texto va en el tono oscuro y no en el vivo porque el vivo sobre su propio
# soft no llega a contraste legible en impresión.
PALETA = {
    "VERDE":    ("DCFCE7", "14532D"),
    "AMARILLO": ("FEF3C7", "713F12"),
    "NARANJA":  ("FFEDD5", "7C2D12"),
    "ROJO":     ("FEE2E2", "7F1D1D"),
}
GRIS_BORDE = "D9DEDC"
GRIS_HEADER = "1F3A34"     # verde CIGOB oscuro, para la fila de encabezado
GRIS_ALTERNA = "F6F8F7"
GRIS_SECCION = "E8EDEB"    # fila separadora de dimensión
MARCA_DIM = "DIMENSIÓN:"


def _sombrear(celda, hex_color):
    tc = celda._tc.get_or_add_tcPr()
    for viejo in tc.findall(qn("w:shd")):
        tc.remove(viejo)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc.append(shd)


def _bordes(tabla):
    tbl_pr = tabla._tbl.tblPr
    for viejo in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(viejo)
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")          # 4 octavos de punto = medio punto
        el.set(qn("w:color"), GRIS_BORDE)
        borders.append(el)
    tbl_pr.append(borders)


def _margenes_celda(tabla, pt=4):
    """Aire dentro de la celda. Sin esto el texto toca el borde y la tabla se
    lee apretada por más bordes finos que tenga."""
    tbl_pr = tabla._tbl.tblPr
    for viejo in tbl_pr.findall(qn("w:tblCellMar")):
        tbl_pr.remove(viejo)
    mar = OxmlElement("w:tblCellMar")
    for lado, val in (("top", pt), ("bottom", pt), ("left", pt + 3), ("right", pt + 3)):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), str(int(val * 20)))   # twips
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.append(mar)


def _no_partir(fila):
    tr_pr = fila._tr.get_or_add_trPr()
    if not tr_pr.findall(qn("w:cantSplit")):
        tr_pr.append(OxmlElement("w:cantSplit"))


def _repetir_encabezado(fila):
    tr_pr = fila._tr.get_or_add_trPr()
    if not tr_pr.findall(qn("w:tblHeader")):
        tr_pr.append(OxmlElement("w:tblHeader"))


def _keep_next(parrafo):
    p_pr = parrafo._p.get_or_add_pPr()
    if not p_pr.findall(qn("w:keepNext")):
        p_pr.append(OxmlElement("w:keepNext"))


def _combinar_fila(fila):
    """La fila separadora de dimensión ocupa el ancho completo."""
    celdas = fila.cells
    if len(celdas) > 1:
        celdas[0].merge(celdas[-1])


def _texto(celda):
    return celda.text.strip()


def _tiene_encabezado(tabla):
    """Si la primera fila es encabezado de columnas o ya es un dato.

    No se puede preguntar por `tblHeader`: pandoc no lo escribe en ninguna
    tabla, así que a esta altura todas llegan iguales. Y cuando el markdown
    declara el encabezado vacío (`| | | |`, como el banner "Hoy:" y la tabla
    de Identificación), pandoc directamente no emite fila de encabezado — la
    primera fila que se ve es un dato. Pintarla como encabezado deja el valor
    del mes en blanco sobre verde oscuro, que fue exactamente lo que pasó.

    Las dos señales vienen de cómo está armado el markdown de las fichas:
      · una tabla de una sola fila es un banner, nunca tiene encabezado;
      · en esta anatomía las etiquetas de una tabla de datos van en negrita
        ("**IDENTIFICADOR TÉCNICO**") y los nombres de columna de una tabla
        con encabezado, no.
    """
    if len(tabla.rows) == 1:
        return False
    return not any(r.bold for c in tabla.rows[0].cells
                   for p in c.paragraphs for r in p.runs)


# Sello para no aplicar el estilo dos veces sobre el mismo archivo.
#
# Hace falta porque este script NO es idempotente: la primera pasada quita el
# prefijo MARCA_DIM de las filas separadoras, así que la segunda ya no las
# reconoce y las trata como filas comunes — les pisa el sombreado de sección
# con el de fila alternada. Pasó de verdad: tres documentos re-estilados
# perdieron el separador de dimensión y ningún chequeo de contenido lo vio,
# porque el texto seguía intacto.
#
# El pipeline correcto es siempre pandoc → estilar sobre un .docx recién
# convertido. Si hay que re-estilar, se vuelve a convertir primero.
SELLO = "fichas-cigob: estilado"


def estilar(path):
    doc = Document(path)
    if SELLO in (doc.core_properties.comments or ""):
        raise SystemExit(
            f"{path}: ya tiene el estilo aplicado. Volvé a convertirlo con "
            f"pandoc antes de estilarlo — una segunda pasada rompe las filas "
            f"separadoras de dimensión.")
    n_color, n_seccion = 0, 0

    for tabla in doc.tables:
        tabla.autofit = True
        _bordes(tabla)
        _margenes_celda(tabla)
        con_encabezado = _tiene_encabezado(tabla)

        for i, fila in enumerate(tabla.rows):
            _no_partir(fila)
            es_seccion = _texto(fila.cells[0]).startswith(MARCA_DIM)

            if i == 0 and con_encabezado:
                _repetir_encabezado(fila)
                for celda in fila.cells:
                    _sombrear(celda, GRIS_HEADER)
                    for p in celda.paragraphs:
                        for r in p.runs:
                            r.bold = True
                            r.font.color.rgb = None
                            r.font.size = Pt(9)
                            # El blanco va por XML: font.color.rgb no alcanza
                            # cuando el estilo del template ya fija un color.
                            rPr = r._r.get_or_add_rPr()
                            for v in rPr.findall(qn("w:color")):
                                rPr.remove(v)
                            col = OxmlElement("w:color")
                            col.set(qn("w:val"), "FFFFFF")
                            rPr.append(col)
                continue

            if es_seccion:
                n_seccion += 1
                _combinar_fila(fila)
                for celda in fila.cells:
                    _sombrear(celda, GRIS_SECCION)
                for p in fila.cells[0].paragraphs:
                    p.text = p.text.replace(MARCA_DIM, "").strip()
                    # El separador se pega a la fila que abre: si no, cae al pie
                    # de página anunciando una dimensión cuyos indicadores están
                    # recién en la página siguiente. Pasó con "Vulnerabilidad
                    # financiera" en vida cotidiana.
                    _keep_next(p)
                    for r in p.runs:
                        r.bold = True
                        r.font.size = Pt(9)
                continue

            if con_encabezado and i % 2 == 0:
                for celda in fila.cells:
                    _sombrear(celda, GRIS_ALTERNA)

            for celda in fila.cells:
                fondo_texto = PALETA.get(_texto(celda))
                if fondo_texto:
                    n_color += 1
                    fondo, tinta = fondo_texto
                    _sombrear(celda, fondo)
                    for p in celda.paragraphs:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for r in p.runs:
                            r.bold = True
                            r.font.size = Pt(9)
                            rPr = r._r.get_or_add_rPr()
                            for v in rPr.findall(qn("w:color")):
                                rPr.remove(v)
                            col = OxmlElement("w:color")
                            col.set(qn("w:val"), tinta)
                            rPr.append(col)
                else:
                    for p in celda.paragraphs:
                        for r in p.runs:
                            r.font.size = Pt(9)

    # Un título nunca se queda solo al pie: se pega al párrafo que lo sigue.
    #
    # Solo al título. Marcar además el párrafo siguiente encadena keepNext —
    # título + primer párrafo + segundo párrafo tienen que entrar juntos— y
    # cuando no entran, Word empuja el bloque completo a la página siguiente:
    # media página en blanco después de "Definición", verificado en el PDF.
    n_keep = 0
    for p in doc.paragraphs:
        if p.style.name.startswith("Heading"):
            _keep_next(p)
            n_keep += 1

    props = doc.core_properties
    props.comments = ((props.comments + " · ") if props.comments else "") + SELLO
    doc.save(path)
    return {"tablas": len(doc.tables), "celdas_color": n_color,
            "filas_seccion": n_seccion, "titulos_pegados": n_keep}


if __name__ == "__main__":
    for archivo in sys.argv[1:]:
        r = estilar(archivo)
        print(f"{archivo:42s} tablas={r['tablas']:3d} color={r['celdas_color']:3d} "
              f"secciones={r['filas_seccion']:2d} keepNext={r['titulos_pegados']:3d}")
