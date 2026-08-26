---
madr: 4
id: '0246'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [apoyo_empresario]
archivos: ['scripts/itcp.py', 'scripts/publicar.py', 'web/src/lib/descripciones.ts', 'tests/test_suspension_libera_el_peso.py']
relacionado: ['0148', '0149', '0245', '0259', '0265']
ambito: 'Cinturón política · ITCP · `apoyo_empresario` · por qué sale del score hasta cerrar el corpus'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «había 14 textos pendientes, incluidos apoyos y críticas sustantivos»'
---

# ADR-0246 — El saldo empresario se calculaba sobre un corpus abierto

## Contexto y planteo del problema

`apoyo_empresario` publicaba **−0,429**: siete comunicados de AEA y UIA
codificados en la ventana de doce meses, dos de apoyo y cinco de crítica. Con
6,5% del ITCP, aportaba **6,4 sobre 10 de tensión**.

La card declaraba, en su propio texto, **catorce comunicados detectados sin
codificar**. Ese detector existe a propósito
([[0149-detector-de-postura-empresaria]]) para que el registro no se quede viejo.
Lo que la auditoría del 25-ago-2026 verificó es que entre esos catorce había
apoyos y críticas sustantivos: no era una cola de textos irrelevantes.

Un saldo sobre siete casos con catorce pendientes no mide la postura del sector
empresario. Mide **qué se alcanzó a codificar**. Y el sesgo no es simétrico ni
estimable: dos apoyos y cinco críticas sobre veintiún textos podrían dar
cualquier cosa entre −1 y +1.

Que el denominador sea chico no es el problema en sí —el indicador nació sabiendo
que las cámaras se pronuncian poco ([[0148-apoyo-empresario-con-uia-la-metrica-funciona]])—.
El problema es que el corpus está **abierto y se sabe que lo está**: el propio
tablero publica cuántos faltan.

## Factores de decisión

- **Un saldo exige un corpus cerrado.** Con textos pendientes conocidos, el
  numerador y el denominador dependen del ritmo de codificación, no del mundo.
- **El indicador aportaba tensión alta** con muy poco peso muestral detrás.
- **La codificación es humana** y no hay control de concordancia: hoy nada
  distingue una clasificación discutible de una firme.
- **El detector ya hace su trabajo**: el problema no es no saber que faltan
  textos, es puntuar igual.

## Opciones consideradas

- **A — Codificar los catorce pendientes** y recalcular.
- **B — Sacarlo del score** hasta que el corpus esté cerrado y el criterio de
  codificación, fijado y controlado.
- **C — Dejarlo puntuando** con una nota que declare los pendientes.

## Decisión

**Opción B.** `apoyo_empresario` sale del ITCP por el mecanismo de
[[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]]: libera su 50% de
la dimensión de sector privado y `brecha_obra_publica` queda como su único
componente, con el 13% del índice que la dimensión ya tenía. No se movió ningún
peso a mano.

Sigue relevándose y su serie se sigue publicando. No se muestra como card,
por la regla del tablero ([[0189-si-no-puntua-no-se-muestra]]).

La opción A es el camino de vuelta, no una alternativa: codificar catorce textos
sin criterios predeclarados ni doble codificación reproduce el problema con más
casos. La C mantiene puntuando un número que la propia card admite incompleto.

**Condición de reingreso**: corpus cerrado y publicado, criterios de codificación
fijados de antemano, doble codificación con control de concordancia, inventario
completo, y prueba de que la card y la serie usan la misma cohorte.

### Consecuencias

- El ITCP pierde el componente que aportaba más tensión de su dimensión. El
  índice **sube** —la crítica empresaria era lo que lo empujaba abajo— y eso hay
  que leerlo como lo que es: se dejó de puntuar una medición mal fundada, no
  mejoró la relación con el sector privado.
- La dimensión de sector privado queda con un solo componente. Es una fragilidad
  real y declarada: si `brecha_obra_publica` se cae, la dimensión desaparece.

### Confirmación

`tests/test_suspension_libera_el_peso.py` cubre el caso: no puntúa, no pesa, no
se muestra, `brecha_obra_publica` absorbe el hueco en proporción, el reparto
entre dimensiones no se mueve, y sacar la suspensión devuelve el 50/50 original.

## Pros y contras de las opciones

### A — Codificar los pendientes

- Bueno, porque cierra la ventana actual.
- Malo, porque sin criterios predeclarados ni concordancia, veintiún casos
  codificados a posteriori tienen el mismo problema que siete.

### B — Sacarlo del score

- Bueno, porque deja de puntuar una medición que su propia card declara
  incompleta.
- Malo, porque la dimensión queda con un solo componente.

### C — Dejarlo con una nota

- Bueno, porque conserva la serie continua.
- Malo, porque una nota no corrige un saldo: el número entra al índice igual.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_politica.md`.
