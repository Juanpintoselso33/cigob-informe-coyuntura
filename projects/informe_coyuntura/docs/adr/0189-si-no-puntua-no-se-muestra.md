---
madr: 4
id: '0189'
estado: 'aceptado'
fecha: 2026-08-09
cinturon: 'gestion'
indicadores: [asistencia_directa, masa_salarial, social_orden, reforma_estado]
continua: ['0051', '0100', '0186']
relacionado: ['0190', '0212']
ambito: 'ITCG · qué puntúa y qué se publica, en el tablero y en las fichas'
origen: 'Instrucción del editor, 2026-08-09: "si los indicadores no puntean, no se muestran y no van ni en la ficha ni en el cinturón" y "si está cumplida tiene que puntear, si es un índice que busca medir cuánto avanzó el gobierno en sus propuestas no tiene sentido excluir una ya cumplida."'
---

# ADR-0189 — Si no puntúa no se muestra, y una promesa cumplida sí puntúa

## Contexto y planteo del problema

ADR-0051 dejó una regla sin excepciones para los cinco cinturones: **el
tablero solo muestra lo que integra las dimensiones de su índice**, y los
ocultos tampoco llevan ficha metodológica.

Después se abrieron dos excepciones, cada una con su estado propio:

- **ADR-0100** creó *promesa cumplida* para `asistencia_directa`: le sacó el
  puntaje por estar clavada en el techo, pero dejó la card visible.
- **ADR-0186** creó *suspendido* para `masa_salarial`, a pedido de CIGOB, con
  la fórmula "lo que se retira es el puntaje, no el dato".

En agosto de 2026 la página de gestión mostraba 15 cards de las cuales 2 no
puntuaban, y las fichas metodológicas —que salen del mismo snapshot— las
arrastraban: 15 fichas, 2 sin semáforo, en un documento cuyo objeto es el
semáforo. Eso puso las dos excepciones sobre la mesa a la vez, y quedó a la
vista que no eran el mismo caso.

## Factores de decisión

- **El ITCG es un índice de AVANCE, no de coyuntura.** Mide cuánto avanzó el
  gobierno en sus propuestas. El argumento de ADR-0100 —"un indicador clavado
  en su máximo no aporta información al promedio mensual"— es el criterio
  correcto para un índice de variación y el equivocado para éste: un índice de
  avance que descarta las propuestas ya cumplidas informa menos avance del que
  hubo, y el sesgo se agranda justamente a medida que el gobierno cumple.
- **`masa_salarial` no salió por estar en el techo, salió por una duda
  metodológica sin saldar.** No hay nada que reportar todavía: no es que el
  dato no se mueva, es que no se sabe qué afirma. Son dos situaciones
  distintas y la respuesta no puede ser la misma.
- **Una card sin puntaje se lee como parte del índice.** Dentro de una
  dimensión es indistinguible a simple vista de una que sí pesa, y el chip
  explicativo no alcanza a corregir esa lectura.
- **Nada de esto exige dejar de medir.** El precedente de ADR-0051 separa las
  dos cosas: los ocultos siguen corriendo como seguimiento interno.

## Opciones consideradas

1. **Devolver `asistencia_directa` al cálculo y ocultar `masa_salarial`**
   (elegida).
2. Ocultar las dos, aplicando "si no puntúa no se muestra" sin revisar por qué
   cada una había dejado de puntuar.
3. Dejar las dos visibles sin puntuar, como estaban.
4. Sacarlas de las fichas solamente, dejando el tablero como estaba.

## Decisión

**`asistencia_directa` vuelve a puntuar.** `INDICADORES_CUMPLIDOS` queda
vacío y `social_orden` recupera el 40/40/20 del documento, deshaciendo el
reparto 67/33 que ADR-0100 había hecho con su peso.

**`masa_salarial` deja de publicarse**, además de no puntuar.
`GESTION_OCULTOS` pasa a incluir cumplidos y suspendidos:

```python
# scripts/publicar.py
GESTION_OCULTOS = (set(itcg.INDICADORES_CONTEXTO)
                   | set(itcg.INDICADORES_CUMPLIDOS)
                   | set(itcg.INDICADORES_SUSPENDIDOS))
```

Las constantes de `itcg.py` se conservan aunque `INDICADORES_CUMPLIDOS` quede
vacío: son las que documentan por qué un indicador dejó de puntuar y las que
`anotar_indicadores()` usa para sacarlo del cálculo. La regla queda otra vez
sin excepciones — **todo lo que se ve, puntúa** — y el criterio para decidir
qué puntúa vuelve a ser el que corresponde a un índice de avance.

Se descartó la opción 2 porque aplicaba la regla de visibilidad sin mirar el
motivo de fondo, y habría dejado fuera del ITCG una propuesta cumplida.

### Consecuencias

- **ITCG 76,8 → 77,5.** `social_orden` 84,4 → 90,6, con
  `asistencia_directa` 100,0 · `protocolo_antipiquetes` 99,0 ·
  `libertad_opcion_salud` 54,8. Misma banda ("Moderadamente aflojado").
- Gestión pasa de 15 cards a 14, y de 15 fichas a 14. Las 14 tienen semáforo.
- El colector sigue midiendo `masa_salarial` y su serie sigue en
  `output/series/gestion.csv`: el dato no se pierde, deja de publicarse. Si se
  salda la duda, vuelve por donde salió.
- **Queda pendiente un problema de calibración**, que este ADR no resuelve
  porque es otra discusión: `asistencia_directa` marcaba 98,3% en la base de
  agosto de 2023 y 100,0 todos los meses del mandato, así que su recorrido
  real es de menos de dos puntos. Puntúa 100 sobre una escala que no está
  anclada al punto de partida — el indicador le acredita al gobierno un tramo
  que ya estaba andado. Eso se arregla recalibrando las anclas, no
  excluyéndolo del índice.

### Confirmación

`tests/test_publicar.py::test_gestion_itcg_reconcilia` deja de exigir que las
dos cards existan y pasa a exigir lo contrario: que el snapshot de gestión no
traiga ningún indicador con `en_indice is False`, y que los ocultos no
aparezcan. `tests/test_itcg.py` fija el nuevo puntaje de `social_orden` y el
ITCG del fixture. El test es el gate de la regla, no una descripción de ella.

## Pros y contras de las opciones

**1. Devolver una, ocultar la otra.** A favor: cada indicador se trata por su
motivo real; el índice de avance vuelve a contar lo cumplido; la regla de
visibilidad queda sin excepciones. En contra: sube el ITCG apoyándose en un
indicador mal calibrado, que es una deuda que queda abierta y anotada.

**2. Ocultar las dos.** A favor: la lectura más literal de "si no puntúa no se
muestra", y la más simple de implementar. En contra: deja fuera del índice una
propuesta cumplida, que es exactamente lo que un índice de avance tiene que
contar; arrastra el error de ADR-0100 en vez de corregirlo.

**3. Dejar todo como estaba.** A favor: cero cambios. En contra: sostiene dos
excepciones que entre las dos vaciaron la regla de ADR-0051 en el único
cinturón donde esa regla se había escrito.

**4. Sacarlas solo de las fichas.** A favor: no toca lo publicado. En contra:
el documento y la página dirían cosas distintas del mismo cinturón, que es
peor que cualquiera de los dos estados coherentes.

## Más información

- [ADR-0051](0051-gestion-contexto-oculto.md) — la regla de visibilidad que
  este ADR restituye sin excepciones.
- [ADR-0100](0100-promesa-cumplida-no-es-contexto.md) — creó el estado
  *promesa cumplida*; queda sin efecto por completo, incluido el retiro del
  puntaje.
- [ADR-0186](0186-masa-salarial-sale-del-itcg.md) — creó el estado
  *suspendido*; el retiro del puntaje sigue vigente, la card deja de verse.
- La revisión de CIGOB que originó el 0186 está en
  `260808 Fichas_Semaforo_Gestion observaciones.docx`: `masa_salarial` con
  "CREO QUE DEBERIAMOS SACARLO", `asistencia_directa` con "SIN OBSERVACIONES".
