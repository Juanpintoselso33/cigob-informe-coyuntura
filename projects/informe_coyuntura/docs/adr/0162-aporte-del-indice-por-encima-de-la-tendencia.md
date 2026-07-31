---
madr: 4
id: '0162'
estado: 'aceptado'
nota_estado: 'Aceptado, **implementado y publicado** (cableado 2026-07-30)'
fecha: 2026-07-30
cinturon: 'transversal'
archivos: ['scripts/regresion_validacion.py']
ambito: '`scripts/regresion_validacion.py`'
---

# ADR-0162 — Aporte del índice por encima de la tendencia (regresión)

- **Relacionados**: ADR-0159 (lo dejó como pendiente explícito), ADR-0161

## Contexto y planteo del problema

El paso 9 del handbook OCDE/JRC pide correlacionar con otros indicadores **y**
"identificar vínculos mediante regresiones". Lo primero está (ADR-0155, 0159,
0161); esto es lo segundo, y no es un adorno: ataca el problema que aparece en
todas las mediciones de este proyecto — **en estos años casi todas las series
argentinas comparten la tendencia del período**, así que una correlación alta en
niveles puede ser sólo eso.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

Se comparan dos modelos y se reporta el **aporte incremental de R²**:

    modelo A:  externa = a + b·t
    modelo B:  externa = a + b·t + c·índice

La pregunta que responde: *¿el índice explica algo del contraste externo que una
simple tendencia temporal no explique ya?*

Mínimos cuadrados resuelto a mano (eliminación gaussiana sobre las ecuaciones
normales): son tres parámetros y no justifica una dependencia nueva. Se verifica
contra casos de respuesta conocida —ajuste perfecto, predictor irrelevante,
colinealidad— porque una regresión mal resuelta es peor que no tenerla: publica
un número con aire de autoridad.

**La colinealidad exacta se declara como tal, no como falta de datos.** Si el
índice es una función lineal del tiempo, el sistema sale singular. La primera
implementación devolvía "datos insuficientes" ahí — es decir, se callaba
exactamente en el caso que motiva la prueba. Ahora devuelve aporte 0 con la
marca `colineal`, y el texto público dice que el índice, en ese período, no se
distingue de la tendencia. El defecto quedó **commiteado con su test en rojo** y
se detectó recién al correr la suite completa; el test estaba bien y la
implementación mal.

### Consecuencias

| | tendencia sola | + el índice | **aporte** |
|---|---|---|---|
| **ITCP** | 22,6% | 47,6% | **+25,0 pp** |
| **ITVC** | 0,8% | 0,9% | +0,1 pp |
| **ITCG** | **46,6%** | 47,0% | **+0,4 pp** |

**El ITCP pasa**: un cuarto del comportamiento del contraste externo lo explica
el índice y no el paso del tiempo.

**El ITCG es el hallazgo.** Su correlación en niveles contra el factor era 0,678
—el número más alto de los tres— y resulta que **casi todo es la tendencia común
del período**: el tiempo solo ya explica el 46,6%, y sumar el índice agrega 0,4
puntos porcentuales. Confirma por un camino independiente el veredicto negativo
de ADR-0164, que se había apoyado en el mes a mes (−0,015). Sin esta prueba, un
lector razonable habría leído 0,678 como el mejor resultado de validación del
informe.

**El ITVC no aporta nada en niveles**, que es lo esperado y ya estaba dicho: se
movió 5 puntos netos en 32 meses, así que en niveles no hay nada que explicar.
Su validación vive en el mes a mes (+0,478, ADR-0163).

## Más información

### Dónde se aplica

Sobre el **factor común** de cada cinturón que lo tiene (ADR-0161/0163/0164), en
**niveles**: diferenciar ya le quita la tendencia, así que en ese plano la
pregunta no tiene sentido. El texto va al final del detalle de la ficha
metodológica, porque califica a todo lo anterior.

El signo no se declara a priori —la orientación del factor la fija su carga
dominante— sino que se usa como **chequeo de coherencia**: el coeficiente tiene
que apuntar para el mismo lado que la correlación ya publicada, y si no, se dice.

### Detalle de presentación

Un aporte de 0,4 puntos porcentuales se mostraba como «0» por redondeo, que es
una afirmación más fuerte que la real. Por debajo de 10 puntos se muestra un
decimal. Hay test.
