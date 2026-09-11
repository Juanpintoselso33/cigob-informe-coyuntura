# Publicación de julio: industria y construcción

**Actualización ADR-0299:** IPI e ISAC integrados en tarjeta e historia desde
las planillas originales. ADR-0300 integra también bienes de capital: IAI julio
−5,66% en tarjeta e historia. ADR-0301 corrige su omisión en la historia del
índice macro. [Cotejo integrado](cotejo-iai-integrado.json).
Los párrafos siguientes describen el hallazgo inicial.

Durante la auditoría, después del horario de difusión del 8 de septiembre,
INDEC publicó julio. Los contenidos se verificaron en las rutas de contenido
que carga su web: `/Nivel4/Tema/3/6/14` y `/Nivel4/Tema/3/3/42`.

Las planillas originales confirman:

- IPI original: julio 118,1646866095709; variación interanual −4,8769703%.
  Su promedio interanual de tres meses, que es la métrica del monitor,
  resulta −2,82%. Junio revisado resulta −1,99% con ese promedio.
- ISAC original: julio 147,37594683640305; variación interanual −4,5398258%.
  ISAC desestacionalizado: julio 140,163347962769.

Fuentes originales:
[IPI](https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipi_manufacturero_2026.xls)
y [ISAC](https://www.indec.gob.ar/ftp/cuadros/economia/sh_isac_2026.xls).
La [evidencia extraída](cotejo-ipi-isac-julio.json) conserva niveles y hash.

Las tres rutas API que usa el monitor todavía terminan en junio y también
difieren del junio revisado. No basta agregar julio manualmente: deben
compartirse las series originales entre tarjeta, historia y compuestos que
usan IPI o ISAC, incorporando revisiones. Pendiente de integrar; el snapshot
local todavía contiene los datos anteriores para estos componentes.


## Bienes de capital: original localizado

La [planilla mensual oficial](https://www.indec.gob.ar/ftp/cuadros/economia/impo_uso_economico_2025_2026.xls)
contiene 19 meses: enero-diciembre de 2025 y enero-julio de 2026. Julio coincide
exactamente con el Cuadro 14 del ICA: 1167,16911031 y 1265,03060453 millones USD.
La caída interanual es −7,73589934%. Con ISAC −4,5398258% y pesos 65/35,
el IAI de julio da −5,66%. Ese valor ya está integrado y verificado en tarjeta e historia.
La evidencia siguiente conserva el cotejo previo a la integración. [Evidencia](cotejo-bienes-capital-original-pendiente.json).
