---
madr: 4
id: '0173'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/descargar_series.py', '.github/workflows/data-pipeline.yml']
continua: ['0133']
relacionado: ['0172']
ambito: 'Pipeline nocturno · presupuesto de tiempo y preservación de series'
origen: 'Dos corridas del 5-ago-2026 murieron por timeout del job con las series a medio bajar; al diseñar el arreglo apareció que un fetcher caído borraba su serie del CSV'
---

# ADR-0173 — Una fuente lenta no se come la corrida

## Contexto y planteo del problema

ADR-0133 dejó el pipeline bien defendido contra fuentes que **fallan**: los
colectores usan sus exit codes como dato (`0` fresco, `1` mixto, `2` todo
caché), una fuente caída no corta la corrida y el carry-forward conserva el
último valor bueno.

No había ninguna defensa contra una fuente que **tarda**. `correr()` ejecutaba
`python "$1"` sin límite de tiempo, así que un solo origen throttleado consumía
el presupuesto del job entero y dejaba sin correr al gate, a los tests y al
commit. El 5-ago-2026 dos corridas murieron exactamente así, con Google Trends
haciendo backoff: **30 minutos y 45 minutos, cero publicado**. Subir el techo del
job no arregla nada — sólo mueve la pared, y se probó dos veces.

Al diseñar el presupuesto apareció un segundo problema, más grave porque es
silencioso. En `descargar()`, un fetcher que falla no aporta filas; en una
corrida completa `write_csv` sobreescribe el CSV del cinturón entero
(`merge=False`). O sea: **un fetcher caído borraba su serie del CSV** en vez de
dejar la anterior. Con presupuestos de tiempo eso habría pasado de raro a
recurrente. Es la misma forma del bug de `sentimiento_digital` que documenta
`CLAUDE.md` —un indicador desaparece del snapshot sin que nada avise— del otro
lado del pipeline.

Y la misma corrida que validó ADR-0172 mostró un tercero: colectores, gate y
tests en verde, todo el trabajo hecho, y el snapshot **se perdió en la última
línea** porque `git push` salió sin rebase y otro push a `main` durante los ~30
minutos de corrida lo dejó no-fast-forward. `CLAUDE.md` le exige
`git pull --rebase` a las personas; el workflow no se lo exigía a sí mismo.

## Factores de decisión

- El presupuesto tiene que distinguir **fuente lenta** de **script roto**, igual
  que ADR-0133 distingue fuente caída de crash. Si no, un timeout se lee como
  bug y corta la publicación, que es lo contrario de lo que se busca.
- **Dónde** se pone el corte importa más que el corte. `write_csv` escribe un
  CSV por cinturón a medida que los termina: matar `descargar_series.py` desde
  afuera deja unos cinturones frescos y otros de ayer — cards nuevas contra
  series viejas, que es el falso G3 documentado el 2026-07-09 y que cuesta una
  hora de diagnóstico cada vez.
- Perder la serie de un indicador es peor que publicarla desactualizada: el
  gráfico desaparece y ningún gate mira invariantes de conteo de filas.
- Un trabajo de 30 minutos no puede perderse por una condición de carrera de un
  segundo en el push.

## Opciones consideradas

- **Presupuesto por indicador adentro de `descargar()`, más presupuesto por
  script en el workflow** — elegida. El corte fino cae donde ocurre el
  throttling (una fuente), dentro del `try/except` que ya existía; el grueso
  queda de último recurso.
- **Sólo presupuesto por script en el workflow** — descartada: es simple, pero
  para `descargar_series.py` produce el estado inconsistente entre cinturones,
  que es un modo de falla peor que el que se quiere evitar.
- **Timeout por hilo (`ThreadPoolExecutor.result(timeout=)`)** — descartada: no
  puede matar al worker, así que la fuente lenta sigue consumiendo red y el
  proceso se cuelga al salir esperando el hilo. `SIGALRM` interrumpe el código
  bloqueado de verdad.
- **Subir otra vez el techo del job** — descartada: ya se hizo dos veces el
  mismo día y las dos veces volvió a morir contra el techo nuevo.

## Decisión

### 1. Un fetcher caído conserva sus filas

`descargar()` acumula los indicadores que fallaron y, antes de escribir, relee
del CSV las filas que ya tenían. Un indicador sin datos nuevos queda
desactualizado —que G2 vigila— en lugar de desaparecer. Cuando además no hay
filas previas, se avisa explícitamente (`[AVISO] ... quedan sin serie`) en vez
de escribir un CSV mutilado en silencio.

### 2. Presupuesto por indicador

Cada fetcher corre dentro de `presupuesto(...)`, con `SIGALRM` y un default de
300 s. Los que caminan actas de a una (`cohesion_bloque`,
`alineamiento_senadores_prov`) o arman canastas de Trends por tandas
(`sentimiento_digital`) tienen presupuestos propios más largos: son lentos por
diseño, no por estar colgados. Agotarlo levanta `TiempoAgotado`, que cae en el
mismo camino que una fuente caída y dispara la preservación del punto 1.

Sin `SIGALRM` (Windows, donde se desarrolla) no hay presupuesto y el bloque
corre entero. El pipeline corre en `ubuntu-latest`, que es donde importa.

### 3. Presupuesto por script en el workflow

`correr()` envuelve cada script en `timeout`. Agotarlo se mapea a **exit 2**
("todo caché"), el código que el pipeline ya sabe leer, en lugar de contarse
como crash. `descargar_series.py` va con 25 min a propósito: su defensa real es
el presupuesto por indicador de adentro, y este es sólo el último recurso.

### 4. El push se rebasa y reintenta

Hasta 3 intentos con `git pull --rebase --autostash` entre uno y otro.

### Consecuencias

- Una fuente throttleada cuesta su indicador, no la publicación de los cinco
  cinturones.
- El CSV de un cinturón deja de poder perder series por un fallo de red.
- `[LENTO]` y `[CARRY]` en el log distinguen a simple vista qué pasó.

### Confirmación

`tests/test_series_presupuesto.py`: que un fetcher caído conserva sus filas, que
un indicador lento se corta sin arrastrar a los demás, y que el presupuesto no
toca los bloques rápidos. Los que dependen de `SIGALRM` se saltean en Windows y
corren en CI.

## Más información

### Limitaciones

- Los presupuestos por indicador son **estimaciones, no mediciones**. Se
  eligieron holgados para no degradar datos por error; si alguno queda corto se
  va a ver como `[LENTO]` recurrente en el log de un indicador que antes andaba,
  y hay que subirlo. No hay telemetría de cuánto tarda cada fetcher que permita
  calibrarlos de otra forma.
- El corte por `SIGALRM` interrumpe donde esté el código, que puede ser a mitad
  de una escritura de caché por acta (`*_STORE.write_text`). Esas cachés se
  reconstruyen solas en la corrida siguiente, pero una quedaría corta ese día.
- El presupuesto por script sigue pudiendo dejar `descargar_series.py` a mitad
  si los 25 min no alcanzan. Es menos probable con el corte por indicador, pero
  el modo de falla sigue existiendo: la solución completa sería que escriba
  todos los CSV al final, en una sola tanda, y no está hecha.
