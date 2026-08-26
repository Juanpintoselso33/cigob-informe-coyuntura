# Fichas metodológicas en Word

Genera un `.docx` por cinturón, con una ficha por indicador, para que el
equipo las revise fuera de la web. Misma anatomía que las fichas que circuló
Luis para gestión en agosto de 2026: encabezado CIGOB, banner «Hoy:», tabla
de Identificación, y las secciones de prosa con títulos fijos. Nada
interactivo — es un documento para leer y anotar al lado.

Todo sale del snapshot (`web/src/data/informe.json`) y de los textos que ya
usa la web (`web/src/lib/{descripciones,fichas,datos}.ts`). No hay una sola
cifra ni definición escrita a mano acá: si las fichas dijeran otra cosa que
la página, tendríamos dos versiones del mismo dato.

## Cómo se generan

Desde `projects/informe_coyuntura/`, después de una corrida del pipeline:

```bash
python scripts/fichas/generar.py --todos     # o un cinturón suelto por nombre
# El .md ya está en output/fichas/; falta el Word con la marca CIGOB.
pandoc "output/fichas/fichas-macro.md" -o "output/fichas/Fichas Semaforo Macro.docx" `
       --reference-doc=docs/template/cigob_reference.docx
# …ídem los otros cuatro…
python scripts/fichas/estilar.py output/fichas/*.docx
python scripts/fichas/verificar.py
```

`verificar.py` es el gate: si sale con fallas, el documento no se manda.

## Los tres pasos

- **`generar.py <cinturon>`** (o `--todos`) — arma el Markdown en `output/fichas/`. Abre con
  una portada de resumen (el índice, las dimensiones y todos los indicadores
  con su color y su peso) y sigue con una ficha por indicador, cada una en
  página nueva.
- **`estilar.py <docx…>`** — lo que pandoc no puede hacer: bordes, encabezado
  con fondo, filas alternadas, las celdas de color pintadas con la paleta de
  `web/public/dashboard.css`, y las propiedades de Word que gobiernan los
  cortes de página (encabezado que se repite al cruzar, filas que no se
  parten, separador de dimensión pegado a su primera fila).
- **`verificar.py`** — contrasta cada `.docx` contra el snapshot: banner,
  color, peso, portada completa y restos de plantilla.

## Por qué el verificador mira el banner y no «el texto de la ficha»

La primera versión buscaba cada valor en el texto completo de su ficha. Una
prueba de mutación la pasó por arriba: se alteró a mano el valor del banner y
el color de una celda, y siguió diciendo OK — los dos vuelven a aparecer más
abajo, en la prosa de «Color vigente y por qué». Ahora cada chequeo está
anclado a la celda concreta que debe contener el dato, y la portada se
verifica aparte, porque el segundo caso de esa prueba cayó justamente ahí.

Si se toca el verificador, conviene repetir esa prueba: mutar un valor y un
color a mano y confirmar que falla. Un chequeo que no falla con el documento
mal no está verificando nada.

## Cuándo se regeneran

**Los `.md` los regenera el pipeline nocturno** (ADR-0260): `generar.py --todos`
corre después de `publicar.py` y antes de los gates, y `output/fichas/*.md`
entra en el commit de la corrida. Antes de eso no lo hacía nadie y el artefacto
derivaba en silencio — la auditoría del 25-ago-2026 encontró la ficha del
supermercado publicando mayo mientras la card ya publicaba junio.
`tests/test_fichas_generadas_al_dia.py` cruza período, valor, color, peso e
índice base-100 de **todos** los indicadores contra el snapshot, así que una
corrida a mano que publique sin regenerar las fichas ya no pasa.

**Los `.docx` siguen siendo manuales**, y a propósito: son la última versión
*enviada* al equipo, no un espejo del snapshot de hoy. Pasan por pandoc y
`estilar.py`, y `verificar.py` es el gate antes de mandarlos. Regenerarlos sin
publicar el snapshot correspondiente los deja diciendo algo que la web no dice.
