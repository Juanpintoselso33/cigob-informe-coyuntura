# ADR-0118 — El índice y la tensión son dos escalas, y ahora se dice dónde

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITVC · ficha metodológica del índice · descripción pública |
| **Fecha** | 2026-07-20 |
| **Origen** | Auditoría de Vida Cotidiana, punto 3.3 y recomendación de prioridad media |

## Contexto

La auditoría observó que el cinturón corre **dos sistemas de puntuación en
paralelo** sin explicarlo en ningún lado:

> "Oscurece la relación entre el «nivel aplicado» que alimenta los puntos del
> ITVC y la «tensión» que alimenta la escala del cinturón, que en los hechos son
> dos sistemas de puntuación en paralelo."

Y pidió documentarlo **en una nota única, no repetida en cada ficha**, más
evaluar si el recorte a nivel de componente en el patentamiento de motos sigue
haciendo falta.

## La nota

Va en la ficha metodológica del índice (`/metodologia/itvc`), sección de
agregación, que es el único lugar donde el lector busca cómo se arma el número.
Dice tres cosas:

1. **El índice suma niveles; la tensión es una lectura del resultado.** Al índice
   entra el nivel base-100 de cada componente, nunca su tensión. La tensión
   —5 − (índice − 100) × 0,2, recortada a 0-10— existe para poner el resultado
   en la misma vara que los otros cinturones.
2. **Por qué varios componentes muestran 0 o 10 a la vez**: la escala se corta
   ahí, no es que midan lo mismo. Cada ficha ya publica el valor sin recortar
   junto al recortado.
3. **El segundo recorte, el que sí entra al índice**: ningún componente supera
   140. Hoy afecta al endeudamiento de consumo y al patentamiento de motos.

## El recorte de motos: se mantiene, y ahora está medido

La auditoría lo llamaba "redundante para el lector" porque *"no cambia el
resultado final"*. Medido, **cambia 0,10 puntos de ITVC** (94,8 con tope contra
94,9 sin él). Es cierto que la tensión del componente satura en 0 de las dos
formas, así que la observación es correcta en lo que importa: la lectura no
cambia.

Se mantiene igual, por una razón que la auditoría no consideró: **el techo de
140 no es una regla de motos, es la política de winsorización de ADR-0033
aplicada a todos los componentes por igual**. Sacarlo sólo para uno la volvería
una excepción sin criterio. Su costo total —1,9 puntos de índice, de los cuales
0,1 son de motos— quedó medido en ADR-0109 y ahora está publicado en la ficha.

## De paso, tres números viejos

La ficha del índice todavía decía **"Trece componentes en cinco dimensiones"** y
su fórmula sumaba sobre 5. Con las altas de ADR-0111/0112 y la reorganización de
ADR-0115 son **dieciséis en seis**. Corregidos el resumen, el LaTeX de la
agregación, la leyenda con los pesos y la descripción del índice en el tablero.

Es la misma clase de desactualización que ADR-0116 y ADR-0117 encontraron en la
sección de robustez: texto que describe una estructura que ya cambió, sin que
nada falle.
