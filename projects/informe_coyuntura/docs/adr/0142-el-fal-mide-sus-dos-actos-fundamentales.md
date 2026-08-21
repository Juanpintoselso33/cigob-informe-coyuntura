---
madr: 4
id: '0142'
estado: 'superado'
nota_estado: 'Superado por ADR-0228'
fecha: 2026-07-26
cinturon: 'gestion'
indicadores: [fal_modernizacion_laboral]
relacionado: ['0221']
superado_por: ['0228']
revertido_por: ['0228']
ambito: 'ITCG · `fal_modernizacion_laboral` · bandas · serie · card · ficha'
origen: 'revisión externa del cinturón de gestión (documento del 23-jul-2026)'
---

# ADR-0142 — El FAL mide sus dos actos fundamentales

- **Reemplaza**: ADR-0098 (índice compuesto en tres etapas)
  + **decisión editorial explícita** del 26-jul-2026

## Contexto y planteo del problema

El documento de revisión propone:

> "Cambiar el valor de los indicadores, y tomar un 50% para el FAL y otro 50%
> para Litigiosidad. Para el FAL se tendría en esta instancia dos medidores como
> actos fundamentales, cada uno por el 25% que serían: 1ro) el Congreso de la
> Nación que instauró el FAL mediante la Ley 27.802 de Reforma Laboral, 2) la
> reglamentación del FAL por el PEN mediante el Decreto 408/2026. Eso pone las
> bases para el funcionamiento del FAL (entrada en vigencia recién en noviembre)
> y cumple hasta aquí el cumplimiento de la promesa del Gobierno."

El 50/50 con litigiosidad ya se implementó en ADR-0128. Lo que faltaba —y es lo
que hace este ADR— es la **subdivisión del FAL en los dos actos**.

## Opciones consideradas

- **Medir los dos actos fundamentales** (`100 × actos_cumplidos / 2`), identificados por número de norma y no por posición en una lista — elegida.
- **El compuesto anterior** — lo que puntuaba se sigue relevando y viaja como contexto, sin incidir en el puntaje.

## Decisión

### Lo que se implementó

- **`gestion.py`**: `fetch_fal_modernizacion_laboral()` calcula
  `100 × actos_cumplidos / 2` leyendo `fal_hitos.json`. Los dos actos se
  identifican por número de norma, no por posición en una lista.
- **Todo lo que el compuesto puntuaba se sigue relevando y viaja como
  contexto**, sin incidir en el puntaje: fondos registrados en CNV, menciones
  del FAL en el Boletín Oficial, fecha de vigencia. Si se quiere volver a un
  indicador vivo, los insumos están.
- **`itcg.py`**: bandas nuevas `(75, INF, 100) · (25, 75, 50) · (-INF, 25, 10)`,
  con los cortes en los huecos de una escala que sólo toma tres valores.
- **`descargar_series.py`**: la serie se reconstruye con la misma regla desde
  dic-2023 — 0 hasta feb-2026, 50 desde mar-2026 (Ley 27.802), 100 desde
  jun-2026 (Decreto 408/2026). Ya no necesita red.
- **Web**: `fichas.ts`, `datos.ts`, `descripciones.ts`, `formulas.ts` y
  `charts.ts` — los cinco archivos del checklist.
- **Tests**: `tests/test_gestion_fal_actos.py`, seis casos. Uno verifica que el
  compuesto de ADR-0098 no vuelva a colarse en el cálculo; otro, que la
  limitación esté declarada **en el texto público** y no sólo en este ADR.

### Consecuencias

- La ficha pública dice explícitamente que el indicador «dice que las bases
  quedaron puestas, no que el Fondo funcione», y que el valor queda fijo en cien.
  Es una limitación asumida y tiene que estar a la vista del lector.
- `validacion_externa.py` reconstruye el ITCG con estas bandas y esta serie: se
  corre en el mismo cambio, como pide el checklist que ya falló dos veces
  (`bloqueo_sostenido` y `mora_familias`).
- **Pendiente con fecha**: el 1-nov-2026, cuando el régimen entre en vigencia,
  hay que rediseñar el indicador. Hoy no tiene forma de reflejar ese hecho.

## Más información

### El desacuerdo, que conviene dejar escrito

ADR-0098 (20-jul-2026, tres días antes del documento) atacó el mismo problema y
llegó a otra respuesta: compuso el índice como `0,40 · construcción + 0,20 ·
vigencia + 0,40 · adopción`, con los dos actos incluidos entre los hitos de
construcción, y **topeó el puntaje en 30 hasta noviembre**, con este argumento
textual:

> "Es exigente a propósito: sancionar y reglamentar la ley es progreso real sobre
> la promesa, pero mientras nada rija el efecto es cero."

La revisión externa sostiene lo contrario: que sancionar y reglamentar **agota**
lo que el Gobierno podía cumplir hasta la vigencia. Las dos lecturas son
defendibles. **Ganó la segunda, por decisión editorial.**

### Efecto, sin maquillaje

| | antes (ADR-0098) | ahora |
|---|---|---|
| valor del indicador | 40,2 | **100** |
| puntaje | 30,8 | **100** |
| dimensión `reforma_laboral` | 45,1 | **79,7** |
| ITCG | — | **+5,2 puntos** |

**El cambio mejora el número y la justificación es editorial, no empírica.** No
se puede invocar neutralidad como defensa, igual que en ADR-0128. Queda escrito
acá, en el comentario de las bandas y en la ficha pública.

### El costo, que es serio

Los dos actos ya ocurrieron y **no se pueden deshacer**. El indicador queda
**fijo en 100** y ningún hecho futuro lo mueve: ni la entrada en vigencia del
1-nov-2026, ni que el Fondo se use o no se use.

Es decir: **deja de discriminar**, contra ADR-0042. La escala sólo puede tomar
tres valores (0 / 50 / 100) y ya está en el último. Se publica así sabiendo esto,
y obliga a rediseñar el indicador cuando el régimen entre en vigencia.
