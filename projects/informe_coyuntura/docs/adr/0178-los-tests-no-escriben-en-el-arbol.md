---
madr: 4
id: '0178'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/publicar.py', 'scripts/gate_calidad.py', 'scripts/validacion_externa.py']
continua: ['0177']
relacionado: ['0176', '0206']
continuado_por: ['0179']
ambito: 'Suite de tests · aislamiento de salidas · sensibilidad de G7'
origen: 'Correr la suite completa producía diez fallas G3 fantasma y dos tests que pasan solos y fallan en conjunto'
---

# ADR-0178 — Los tests no escriben en el árbol

## Contexto y planteo del problema

Correr `pytest tests` completo dejaba modificados `web/src/data/informe.json` y
`data/historico/indicadores.json`, y de paso rompía tests que solos pasaban.
Con el snapshot desactualizado, el gate corrido desde la suite reportaba **diez
fallas G3 fantasma**:

```
[FALLA] G3 politica/veto_quorum: serie[-1]=10.0 ≠ card=8.3
[FALLA] G3 politica/desafios_legislativos: serie[-1]=3.0 ≠ card=10.0
...
```

En árbol limpio esos mismos pares coinciden exactos (10,0=10,0 y 3,0=3,0). El
`card=8.3` era el valor de cinco días antes.

El culpable era uno solo, encontrado corriendo la suite archivo por archivo con
`git status` en el medio: `test_publicar.py::test_publicar_genera_snapshot`
ejecutaba `subprocess.run([sys.executable, "scripts/publicar.py"], cwd=ROOT)`.
Es decir, **corría la publicación de verdad contra el repo**. Los tests que
venían después —de ese archivo y de otros— leían el resultado de esa corrida en
lugar del snapshot publicado.

El daño real no es el `git status` sucio: es que **el diagnóstico de cualquier
otra cosa se vuelve poco confiable**. Durante esta jornada esas fallas fantasma
se confundieron dos veces con problemas de datos, y `test_macro_itcm_reconcilia`
y `test_puntaje_unico_camino` aparecían rotos cuando aislados pasan.

Aparte quedaban dos limitaciones anotadas en ADR-0176: G7 detectaba
congelamientos largos pero no recientes, y `transporte_pasajeros` estaba a 126
días de un tope de 150 sin que se supiera si era cadencia o freno.

## Factores de decisión

- Un test que escribe en archivos versionados contamina a todos los que corren
  después, y el síntoma aparece lejos de la causa.
- El test igual tiene valor: correr `publicar.py` de punta a punta es lo único
  que verifica que el snapshot se arma completo. No se trata de borrarlo.
- El rezago absoluto de un ancla **mezcla dos cosas**: el atraso inherente de la
  fuente y el congelamiento. Por eso su tope tiene que ser generoso, y por eso
  tarda meses en avisar.
- Ahora que ADR-0177 dejó `validacion_externa.json` versionado, hay historia
  entre corridas: se puede medir cuándo avanzó un ancla por última vez.

## Opciones consideradas

- **Redirigir la salida de `publicar.py` con una variable de entorno y sembrar
  el temporal con el snapshot vigente** — elegida.
- **Que el test guarde y restaure los archivos** — descartada: si el test falla
  a la mitad, el árbol queda roto, que es la versión peor del mismo problema.
- **Borrar el test** — descartada: es el único que ejercita `publicar.py`
  completo.
- **Bajar los topes absolutos de G7 para que detecten antes** — descartada: da
  demoras falsas en toda fuente con atraso estructural, que son la mayoría.

## Decisión

### 1. `publicar.py` acepta `CIGOB_SALIDA_WEB`

Redirige el snapshot **y el histórico** fuera del repo. Es un escape de test: el
pipeline nunca la setea. El histórico va junto porque `acumular_historico()` lo
reescribe en cada corrida, y sin eso el test seguía dejándolo modificado.

El temporal se **siembra** con el snapshot y el histórico vigentes: `publicar.py`
los lee para el carry-forward, y con un directorio vacío el test estaría
ejercitando el camino de "primera corrida sin previo", que no es el real.

### 2. Un guardián para que no vuelva

`test_publicar_no_toca_el_arbol_cuando_se_le_redirige_la_salida` hashea los tres
archivos antes y después. Si alguien saca el redirect, falla ahí y no tres
archivos de test más adelante como una falla incomprensible.

### 3. G7 mide también hace cuánto que un ancla no avanza

`validacion_externa.py` registra `avanzo` en cada ancla: la fecha en que publicó
por última vez un período nuevo, comparando contra el `panel_anclas` de la
corrida anterior. G7 avisa si pasaron más de **80 días** (todas las anclas del
panel son mensuales, así que eso deja pasar dos publicaciones salteadas).

Esto **descuenta el atraso inherente**: el consumo INDEC puede tener 96 días de
rezago estructural y estar perfectamente sano mientras avance todos los meses.
Un congelamiento se ve en semanas en vez de meses. Sin registro previo, el
primer avance se fecha hoy: suponerlo viejo daría una falla inventada en la
primera corrida.

### 4. `transporte_pasajeros` pasa a 200 días

Verificado contra la fuente: el último dato de INDEC es el mismo que el nuestro
(2026-04), así que los 126 días son cadencia y no freno. Con 150 iba a dar una
demora falsa en tres semanas. Subirlo es seguro **porque el chequeo de avance
lo cubre igual** — es exactamente para lo que sirve tener las dos medidas.

### Consecuencias

- La suite deja de modificar archivos versionados y de producir fallas fantasma.
- Un ancla que se clava se detecta aunque su rezago absoluto siga bajo el tope.
- Se puede subir un tope absoluto por cadencia sin perder detección.

### Confirmación

Suite completa con `git status` limpio al terminar; el guardián de `publicar.py`;
y tres tests nuevos de G7: que un ancla clavada se ve aunque el rezago pase, que
una con atraso estructural que avanza no molesta, y que un registro viejo sin
`avanzo` no inventa una falla.

## Más información

### Limitaciones

- **El aislamiento es puntual, no estructural.** Se arregló el único test que
  escribía, no se impidió que otro lo haga. Un `conftest.py` que falle cualquier
  test que deje el árbol sucio sería la versión general y no está hecha.
- `CIGOB_SALIDA_WEB` es una variable de entorno sin validación: apuntada a un
  lugar equivocado, `publicar.py` escribe ahí sin chistar. Es aceptable para un
  escape de test y sería inaceptable como opción de operación.
- **`avanzo` se pierde si `validacion_externa.json` se borra o no se commitea.**
  Depende enteramente de ADR-0177: si aquello se rompe, este chequeo vuelve a
  fechar todo "hoy" en cada corrida y deja de detectar nada, en silencio.
- Los 80 días son una convención sobre el supuesto de que todas las anclas del
  panel son mensuales. Una ancla trimestral que se agregue mañana daría demora
  falsa hasta que alguien le ponga tope propio.
