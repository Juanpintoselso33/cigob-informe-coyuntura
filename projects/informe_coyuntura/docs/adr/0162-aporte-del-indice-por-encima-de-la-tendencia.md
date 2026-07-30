# ADR-0162 — Aporte del índice por encima de la tendencia (regresión)

- **Estado**: Aceptado, **implementado y no cableado**
- **Fecha**: 2026-07-30
- **Ámbito**: `scripts/regresion_validacion.py`
- **Relacionados**: ADR-0159 (lo dejó como pendiente explícito), ADR-0161

## Contexto

El paso 9 del handbook OCDE/JRC pide correlacionar con otros indicadores **y**
"identificar vínculos mediante regresiones". Lo primero está (ADR-0155, 0159,
0161); esto es lo segundo, y no es un adorno: ataca el problema que aparece en
todas las mediciones de este proyecto — **en estos años casi todas las series
argentinas comparten la tendencia del período**, así que una correlación alta en
niveles puede ser sólo eso.

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

## Estado

Implementado y con tests (10), **no integrado al pipeline ni publicado**. Se
declara así en lugar de dejarlo como si estuviera en producción.
