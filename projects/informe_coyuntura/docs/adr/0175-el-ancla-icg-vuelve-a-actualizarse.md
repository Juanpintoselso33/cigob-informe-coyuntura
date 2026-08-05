---
madr: 4
id: '0175'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'ITCG'
archivos: ['scripts/descargar_series.py', 'output/series/validacion.csv']
continua: ['0173']
relacionado: ['0167']
continuado_por: ['0176']
ambito: 'Validación externa · serie ICG UTDT'
origen: 'El aviso de series sin filas previas que agregó ADR-0173 destapó que fetch_icg_serie levantaba NameError en cada corrida'
---

# ADR-0175 — El ancla ICG vuelve a actualizarse

## Contexto y planteo del problema

El aviso que ADR-0173 agregó para los indicadores sin filas previas disparó en
la primera corrida limpia:

```
[AVISO] sin filas previas para: icg_utdt -- quedan sin serie
```

Tirando del hilo aparecieron **tres cosas encadenadas**, ninguna visible desde
afuera:

1. **`fetch_icg_serie` nunca funcionó.** Usaba `UTDT_ICG_LISTADO` y
   `UTDT_ICG_REFERER`, que no estaban definidas en ningún lado. Levantaba
   `NameError` en cada corrida, no un error de red. El `try/except` de
   `descargar()` lo tragaba como "fuente caída" y seguía.
2. **`icg_utdt` nunca aportó una fila a `gestion.csv`**, donde está registrado
   (`GESTION_DERIVADAS`): 0 filas en el snapshot del 31-jul-2026 y 0 en el del
   5-ago.
3. **Se publicaba igual**, con 296 puntos, desde `output/series/validacion.csv`
   — un archivo **que ningún script escribe**. `CINTURONES_SERIES` tiene cuatro
   cinturones y ninguno es "validacion"; `write_csv` se llama desde un solo
   lugar. Quedó de una versión anterior del código y `publicar.py`, que arma
   `series.json` con `glob` sobre `output/series/*.csv`, lo levantaba igual.

El resultado neto: **el ICG de la validación cruzada estaba congelado** en el
último valor que alguien bajó a mano, y no había forma de que avanzara.
`validacion_externa.py` lo usa como ancla externa (`series_json["icg_utdt"]`) y
`publicar.py` publica un texto que compara el nivel del ICG contra el ITCG.

No lo agarró ningún gate: G2 mira la `fecha_dato` de las **cards** y el ICG no
es indicador de cinturón; G3/G3b sólo miran pares card↔serie. Una serie que es
sólo insumo de validación no tiene quién la vigile.

## Factores de decisión

- Un ancla de validación congelada es peor que una ausente: las correlaciones
  publicadas se calculan igual y parecen sanas.
- El archivo huérfano no es inocuo. `build_series()` deduplica por fecha con el
  último CSV leído ganando, y en orden alfabético `validacion.csv` va **después**
  de `gestion.csv`: con el fetcher arreglado, el huérfano le ganaría a los datos
  frescos en toda fecha compartida.
- El aviso de ADR-0173 afirmaba de más. `publicar.py` junta todos los CSV, así
  que "no hay filas en este cinturón" no implica "el indicador queda sin serie".

## Opciones consideradas

- **Arreglar el fetcher y borrar el huérfano** — elegida.
- **Borrar la registración de `icg_utdt` de `GESTION_DERIVADAS`** y dejar el
  archivo — descartada: congela el ancla para siempre y deja un archivo que
  nadie escribe como única fuente de un dato publicado.
- **Dejar todo y sólo suavizar el aviso** — descartada: es tapar el hallazgo con
  el mensaje que lo destapó.

## Decisión

### 1. Se definen las dos constantes que faltaban

```python
UTDT_ICG_LISTADO = "https://www.utdt.edu/listado_contenidos.php?id_item_menu=28756"
UTDT_ICG_REFERER = "https://www.utdt.edu/ver_contenido.php?id_contenido=1439&id_item_menu=2964"
```

El ICG no cuelga de `listado_contenidos.php` como el ICC (16458) o el Índice
Líder (16461) —por eso no aparece sondeando ids vecinos—: su ficha vive en
`ver_contenido.php` y la descarga en una página aparte, "Descarga de datos".

El parseo transpuesto que ya tenía la función es correcto y no se tocó: el XLS
trae las fechas en una fila y los valores del ICG en la siguiente, con dos
hojas ("Evolución ICG 2001-2022" y "a partir de 2023").

Verificado contra la fuente viva: **296 puntos, de 2001-11 a 2026-06**, con el
último en 2,07 — idéntico al que venía publicándose, o sea que el dato del
huérfano era correcto y lo que faltaba era poder refrescarlo.

### 2. Se elimina `output/series/validacion.csv`

Ningún script lo escribe y su único contenido (`icg_utdt`, 296 filas) lo produce
ahora `descargar_series.py` en `gestion.csv`. Queda en el historial de git si
alguna vez hace falta.

### 3. El aviso de ADR-0173 dice lo que realmente sabe

Nombra el CSV donde faltaron las filas y aclara que el indicador puede tener su
serie desde otro archivo.

### Consecuencias

- El ICG vuelve a actualizarse solo, y con él las correlaciones del ITCG y el
  texto que compara ICG contra ITCG.
- Desaparece la trampa de que un archivo que nadie escribe le gane en el dedup
  a los datos frescos.

### Confirmación

`fetch_icg_serie()` devuelve 296 puntos contra la fuente viva. La corrida
siguiente debe dejar `icg_utdt` en `gestion.csv` y `series.json` debe seguir
teniendo sus 296 puntos, ahora por la vía sana.

## Más información

### Limitaciones

- **Sigue sin haber un gate para series que son sólo insumo de validación.** El
  ICG estuvo congelado quién sabe cuánto y lo encontró un aviso lateral, no un
  chequeo. G2 mira cards, G3/G3b miran pares card↔serie; una serie sin card no
  tiene quién la vigile. Es el mismo agujero que dejaría a cualquier otra ancla
  externa congelarse en silencio, y no está cerrado.
- El `try/except` de `descargar()` sigue tragando `NameError` como si fuera una
  fuente caída. Un error de programación y una fuente que no responde deberían
  distinguirse, igual que ADR-0133 distingue crash de fuente caída en los
  colectores. No está hecho.
- Las dos URL de la UTDT son ids opacos de un CMS. Si la universidad reorganiza
  el sitio se rompen, y esta vez el fallo va a ser un error de red honesto —
  visible como `[ERR]`— en lugar de un `NameError` silencioso.
