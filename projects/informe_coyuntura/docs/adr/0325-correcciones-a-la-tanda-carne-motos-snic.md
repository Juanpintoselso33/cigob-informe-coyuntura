---
madr: 4
id: '0325'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'vida'
indicadores: [consumo_carne_vacuna, consumo_carnes_otras, inseguridad]
archivos: ['scripts/publicar.py', 'scripts/vida_cotidiana/collectors/snic.py', 'scripts/itvc.py', 'web/src/lib/fichas.ts', 'tests/test_carne_compuesto.py', 'tests/test_snic_homicidios.py']
relacionado: ['0322', '0323', '0324']
ambito: 'Correcciones a la tanda ADR-0322/0323/0324, encontradas por revisión adversarial'
origen: 'Revisión adversarial del PR #31, 16-sep-2026'
---

# ADR-0325 — Correcciones a la tanda carne/motos/SNIC (ADR-0322/0323/0324)

## Contexto y planteo del problema

Una revisión adversarial del PR que implementa ADR-0322/0323/0324 encontró
nueve problemas, cuatro de ellos graves porque hacían que el PR no entregara
lo que prometía. Este ADR corrige los cuatro graves y las inconsistencias de
nomenclatura menores; no toca la aritmética de ADR-0322 (verificada correcta
por la misma revisión).

## Factores de decisión

- El arreglo del SNIC (ADR-0324) tenía que hacer que homicidios y demás tipos
  de delito **lleguen al lector**, no sólo a un campo interno del colector.
- Las dos cards de carne tienen que explicar, cada una, **su propio** nivel —
  no repetir la misma matriz textual.
- Una guarda que no distingue la sustitución exacta que el ADR dice evitar
  (contar la faena vacuna dos veces) no cumple su función.
- Un cambio pensado para no perder categorías del SNIC no puede perder otras
  dos en silencio.

## Opciones consideradas

Para cada uno de los cuatro problemas graves había, en el fondo, la misma
disyuntiva: arreglar el mecanismo (que el dato SIEMPRE llegue, que las dos
cards SIEMPRE difieran, que la guarda mire la categoría concreta) o
parchear el síntoma puntual (agregar homicidios a mano en un texto, ajustar
sólo el número de esta corrida, agregar sólo el caso que encontró el
revisor). Se optó por el mecanismo en los cuatro casos — ver el detalle de
cada uno en "Decisión" — porque un parche puntual dejaría el mismo agujero
abierto para la próxima corrida o el próximo tipo de delito que la fuente
agregue o renombre.

## Decisión

**1. El desglose del SNIC llega al contraste que se publica.** Antes,
`tipos_principales` (homicidios, robos, etc.) se calculaba en
`snic.py` y quedaba en el snapshot interno de `scripts/vida_cotidiana/data/`:
ni `publicar.py`, ni `web/src`, ni el HTML construido lo leían. Se agrega
`_snic_desglose_txt()` en `publicar.py`, que cuelga el desglose del contraste
SNIC que ya viaja en el detalle del indicador `inseguridad` (el IVI mensual
sigue siendo la métrica que puntúa; el SNIC sigue siendo contraste anual, con
~8,5 meses de rezago, que no puntúa). No se convierte en indicador nuevo:
sería una segunda medida de seguridad fuera del alcance de esta tarea.

**2. Cada card de carne explica su propio nivel.** `_por_que_carne()` recibe
ahora el `ikey` de la card que está explicando y arma un párrafo distinto
para cada una: `consumo_carne_vacuna` abre hablando de la vacuna, y
`consumo_carnes_otras` abre hablando de aviar+porcina, nombra sus propios
kg y sus variaciones interanuales de aviar y porcina por separado. Las dos
siguen mencionando a la otra (comparten la composición completa, que es el
punto de la matriz A×B), pero ya no son el mismo texto.
`tests/test_carne_compuesto.py` pasa de asertar sólo `"vacuna" in por_que`
(que las dos cumplían con el bug) a asertar que los dos textos son distintos
y que el de "otras" nombra su propio valor y sus componentes.

**3. Guarda directa contra la sustitución que ADR-0322 dice evitar.** Se
agrega `test_otras_no_se_reconstruye_con_las_categorias_del_total`, que
mockea `_fetch_faena_indice` y verifica las categorías EXACTAS con las que se
llama para cada serie: `("vacuna",)` para `consumo_carne_vacuna` y
`("aviar", "porcina")` para `consumo_carnes_otras`. Probado rompiéndolo:
sustituir la tupla de "otras" por `tuple(FAENA_TONELADAS)` (las tres carnes,
contando la faena vacuna dos veces) hace fallar el test; restaurado, pasa.

**4. Amenazas y Lesiones dolosas vuelven a la lista, y una categoría
faltante deja de ser silenciosa.** La primera versión de `TIPOS_RELEVANTES`
sacó "Amenazas" (217.883 hechos) y "Lesiones dolosas" (179.710) sin decirlo
— las dos estaban en el top-5 por volumen que el cambio reemplazó. Se
restituyen: el objetivo de ADR-0324 era dejar de perder categorías al
filtrar por ranking, no reemplazar una pérdida por otra. Queda afuera
"Otros delitos contra la propiedad" (249.754): es un cajón residual sin
identidad de tipo de delito propia, no comparable a los demás.

Con lista fija por nombre, el modo de falla más probable es que la fuente
renombre una categoría — antes esto sólo generaba un `logger.warning` y la
corrida seguía, con `tests/test_snic_homicidios.py` bendiciendo el silencio.
Ahora `_parse_snic_csv` levanta `ValueError` si falta cualquiera de los tipos
esperados. Eso no tumba la corrida completa: lo atrapa el try/except que ya
tiene `fetch_snic()` alrededor de la descarga del SNIC nacional (que loguea
"SNIC FAIL" y sigue con CABA y el resto del cinturón) y, un nivel más arriba,
`_seguro()` en `main.py` marca al colector como caído — el mismo circuito que
ya usan `consumo_carnes.py` y otros colectores de este cinturón para
degradaciones de formato, y que alimenta el exit code 1/2 del pipeline y el
aviso de `#monitor-alertas`. Es ruidoso en el lugar correcto, no un crash sin
red de contención.

**5. Correcciones menores de nomenclatura y una cifra sin fuente.**

- El comentario de `itvc.py` y la ficha de `consumo_carnes_otras` decían
  "52,0% / 48,0%"; el cálculo real usa 0,523/0,477 (52,3%/47,7%, medido
  sobre la faena INDEC). Se corrige el texto para que coincida con el número
  que efectivamente se usa.
- La ficha de `consumo_carne_vacuna` publicaba «promedio histórico de
  referencia ~73 kg/hab/año» sin fuente citable, admitiendo en el propio
  texto que no se puede verificar. Se retira de la descripción pública; la
  limitación explica por qué (no hay fuente citable y verificable dentro de
  este repo).
- Se declara explícitamente la divergencia entre SAGYP (46,75 kg, jul-2026,
  fuente del titular) y CICCRA (46,0 kg, ago-2026, respaldo): antes CICCRA
  se nombraba como respaldo sin decir que su número no coincide con el
  publicado.

### Confirmación

- `tests/test_carne_compuesto.py`: 8 tests, incluida la guarda de
  categorías (probada roja→verde a mano) y la de textos distintos.
- `tests/test_snic_homicidios.py`: 7 tests, incluida la falla ruidosa
  (roja→verde) y la restitución de Amenazas/Lesiones dolosas.
- El ITCIS publicado no se mueve por ninguno de estos cambios (son de texto,
  guardas y desglose de contraste, no de cálculo): 93,1 antes y después.

## Pros y contras de las opciones

**Arreglar el mecanismo (elegido).** A favor: cierra la clase de error, no
sólo el caso puntual que encontró la revisión — la próxima corrida no puede
volver a tirar el desglose del SNIC, ni las dos cards de carne pueden volver
a publicar el mismo texto sin que un test lo note. En contra: más superficie
de código y de tests que mantener.

**Parchear el síntoma puntual.** A favor: cambio mínimo, rápido de revisar.
En contra: no hay garantía de que sobreviva a la próxima corrida — es
exactamente el patrón que produjo los cuatro problemas graves de esta
revisión (código que funcionaba para el caso que se tuvo en mente al
escribirlo, sin una guarda que mirara el mecanismo).

## Más información

- [[0322-la-vacuna-vuelve-a-puntuar-junto-al-resto-de-las-carnes]]
- [[0323-ratio-motos-autos-como-control-de-la-motorizacion]]
- [[0324-el-snic-conserva-homicidios-por-nombre-no-por-ranking]]
