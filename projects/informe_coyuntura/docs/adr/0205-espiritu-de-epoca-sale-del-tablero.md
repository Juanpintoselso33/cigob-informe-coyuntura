---
madr: 4
id: '0205'
estado: 'aceptado'
fecha: 2026-08-14
cinturon: 'transversal'
archivos: ['config.py', 'scripts/generar_informe.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/components/Nav.astro', 'web/src/pages/metodologia/index.astro', 'web/src/pages/frontada.astro', 'tests/test_publicar.py', 'tests/test_marco_conceptual.py', '.github/workflows/data-pipeline.yml']
supersede: ['0035', '0049']
supersede_parcialmente: ['0199']
relacionado: ['0181', '0206', '0207']
ambito: 'El perímetro del tablero: qué cinturones publica y pondera el informe'
origen: 'Luis Babino: un cinturón provisorio, con un solo indicador, no puede pesar el 20% del global'
---

# ADR-0205 — Espíritu de época sale del tablero: el informe pondera cuatro cinturones

## Contexto y planteo del problema

El informe publicaba cinco cinturones y el `score_global` era su promedio
ponderado. Cuatro de ellos —macroeconomía, política, vida cotidiana y gestión—
derivan su tensión de un índice paramétrico propio, con dimensiones, pesos,
validación externa y robustez Monte Carlo. El quinto no.

**Espíritu de época pesaba lo mismo que los otros y no tenía con qué.** Su
recorrido lo dice solo: nació con cuatro proxies, [[0049-espiritu-epoca-solo-intencion-migratoria]]
lo dejó con **uno** —la intención migratoria medida por interés de búsqueda en
Google Trends ([[0035-indice-expectativa-futuro-emigracion]])— y los otros tres
quedaron ocultos por ser lecturas duplicadas de cards que ya viven en vida
cotidiana y política. Desde entonces el cinturón era un indicador solo,
declarado "v1 provisional" en su propia descripción publicada, a la espera de
una paramétrica que nunca se escribió.

Ese indicador único aportaba, en la fase temprana del mandato, el **20% del
número que titula el informe**.

Y no era un 20% neutro. Con el snapshot de agosto de 2026:

| Cinturón | Tensión |
|---|---:|
| Vida cotidiana | 6,9 |
| Macroeconomía | 3,9 |
| Política | 3,5 |
| Gestión | 2,4 |
| **Espíritu de época** | **0,7** |

Era el más bajo del tablero por un margen amplio, o sea que **estaba tirando el
global para abajo de forma sistemática**. El informe se presentaba más flojo de
tensión de lo que sus cuatro mediciones sólidas indicaban, y la quinta parte de
esa lectura la ponía un proxy de búsquedas en Google.

## Factores de decisión

- Lo que pesa en el global tiene que poder auditarse como los demás.
- Un cinturón provisorio no puede ponderar como uno consolidado.
- Sacar un cinturón no es ocasión para recalibrar la importancia de los otros.
- El marco CIGOB-Matus es del encuadre conceptual, no del tablero: son cosas
  distintas y pueden divergir mientras se diga.

## Opciones consideradas

- **Sacarlo del tablero y ponderar cuatro** — elegida.
- **Escribirle una paramétrica y dejarlo.** Descartada por ahora: es trabajo de
  metodología de la Fundación, no de implementación, y no hay fecha. Nada
  impide que vuelva por esa puerta.
- **Dejarlo publicado pero con peso 0.** Descartada: publica una card que dice
  una tensión que no incide en nada, que es peor que no publicarla.
- **Bajarle el peso sin sacarlo.** Descartada: elegir un peso menor es tan
  arbitrario como el 20% y no arregla que el indicador no se pueda auditar.

## Decisión

### 1. El tablero pondera cuatro cinturones

`PESOS_FASE_TEMPRANA` pasa a cuatro cinturones al 25%.
`PESOS_FASE_CONSOLIDACION` conserva los pesos **relativos** que los cuatro
tenían entre sí (25/25/20/15 sobre 0,85), renormalizados a 1: 29/29/24/18.
Sacar un cinturón no es la ocasión para recalibrar la importancia de los otros;
si eso hay que discutirlo, se discute aparte.

### 2. El global sube de 3,5 a 4,2, y cruza de verde a amarillo

Es la consecuencia principal y hay que decirla sin adornos. Con el snapshot de
agosto de 2026 el titular pasa de **3,5 · "Sin tensión relevante"** a **4,2 ·
"Tensión moderada"**, porque el corte verde/amarillo está en 4,0.

**Ese salto no es coyuntura: es el cambio de perímetro.** No pasó nada en la
Argentina entre un número y el otro. Lo que pasó es que se dejó de promediar el
cinturón más bajo del tablero, que además era el que menos podía justificar su
peso. Leído al derecho, el 3,5 nunca fue la lectura buena que ahora se rompe:
era la lectura distorsionada, y el 4,2 la corrige.

Toda comparación con ediciones anteriores tiene que decir de qué lado del
cambio está. El archivo histórico en BigQuery ([[0180-integracion-con-la-plataforma-google]])
acumula por `generated_at` y conserva los `score_global` viejos calculados con
cinco: **la serie tiene una discontinuidad en esta fecha** y no se restató hacia
atrás. Restatearla sería recomputar cada snapshot pasado sin espíritu de época;
es posible —los scores por cinturón están archivados— pero es otro trabajo.

### 3. El indicador se retira; no se muda

`indice_intencion_migratoria` sale del informe. El colector se apaga
(`scripts/espiritu_epoca.py` se borra, y con él su paso del workflow nocturno) y
la serie queda congelada en el archivo histórico, sin publicarse. Se evaluó
mudarlo a vida cotidiana, que es su vecino conceptual: se descartó porque
entrar al ITVC obliga a recalibrar ese índice, y eso es una decisión de
metodología que no corresponde tomar de arrastre.

Los datos duros de migración real (`CONTEXTO_DURO_META`) quedan en el código:
el bloque `contexto_duro` del modal es genérico y esas etiquetas son las únicas
escritas. Si en unos meses nadie las usa, se borran.

### 4. El marco conceptual conserva el cinturón; el tablero no

Acá hay una distinción que el sitio tiene que sostener explícitamente. El marco
CIGOB-Matus **sigue teniendo** su cinturón de espíritu de época: es una
categoría analítica de la Fundación y este ADR no la deroga. Lo que se retira es
su **operacionalización** en este informe.

Por eso /metodologia dice ahora que el marco contempla ese cinturón y que este
informe dejó de publicarlo en agosto de 2026, en vez de hacer de cuenta que
nunca existió.

### 5. El párrafo institucional cambia un número, y sólo uno

[[0199-el-marco-conceptual-vuelve-en-metodologia]] estableció que el párrafo de
apertura del marco es texto de la Fundación y se publica palabra por palabra,
con `tests/test_marco_conceptual.py` como guard. Ese guard falló al hacer este
cambio, que es exactamente para lo que existe, y su mensaje pide un ADR que
supersede al 0199 en vez de una poda silenciosa. Esto es ese ADR.

El único cambio al párrafo es **"cinco cinturones analíticos" → "cuatro"**. El
resto sigue palabra por palabra y el guard lo sigue vigilando.

### 6. La portada anatómica pierde la piel como órgano

`/frontada` mapeaba cada cinturón a una parte del cuerpo y espíritu de época era
la **piel**. El contorno queda como borde del organismo: sin dato, sin color de
semáforo y sin área clickeable.

### Consecuencias

- El tablero baja de 5 a 4 cinturones; `/espiritu/` deja de existir (el sitio
  pasa de 81 a 80 páginas) y sale del nav.
- Se pierde la única lectura de humor social del informe. Es un hueco real y
  queda anotado como tal: si la Fundación escribe la paramétrica, vuelve.
- La serie de `score_global` tiene un quiebre metodológico en esta fecha.
- El pipeline nocturno corre un colector menos.

### Confirmación

- `python -m pytest tests -q` y `npx tsc --noEmit` en verde tras regenerar el
  snapshot con la corrida completa.
- Los dos guards que fallaron —el del párrafo institucional y el del set de
  pesos— se actualizaron con el motivo escrito, no se aflojaron: el de pesos
  ahora afirma que son CUATRO y falla si vuelven a ser cinco sin ADR.
- Verificado en la URL de producción, no en el commit.

## Pros y contras de las opciones

**Sacarlo del tablero** (elegida)

- Bueno, porque todo lo que pondera el global vuelve a ser auditable igual.
- Bueno, porque corrige un sesgo sistemático a la baja en el número del titular.
- Malo, porque el informe pierde su lectura de humor social y no la reemplaza.
- Malo, porque quiebra la serie histórica del global.

**Escribirle una paramétrica**

- Bueno, porque conserva el cinturón con la misma vara que los otros.
- Malo, porque no hay fecha y mientras tanto el sesgo sigue publicándose.

## Más información

- Los pesos viven en `config.py` (`PESOS_FASE_*`); `calcular_score_global()` en
  `generar_informe.py` normaliza por la suma, así que la renormalización a 1 es
  cosmética para el cálculo y explícita para quien lee el snapshot.
- La distinción marco/tablero del punto 4 es la que hay que sostener si alguien
  pregunta por qué el sitio nombra un cinturón que no publica.
