---
madr: 4
id: '0334'
estado: 'aceptado'
fecha: 2026-09-20
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_empresario]
archivos: ['scripts/politica.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts']
relacionado: ['0310', '0332']
ambito: 'Cinturón política · ITCP · `apoyo_empresario` · qué cámaras entran al cálculo y cómo se llama la card'
origen: 'Juan, 20-sep-2026, después de que ADR-0332 midiera el silencio de AEA: «sacale AEA al rótulo entonces, que diga solo UIA».'
---

# ADR-0334 — AEA sale del perímetro y el rótulo dice lo que mide

## Contexto y planteo del problema

ADR-0332 midió que **AEA no publica un comunicado desde el 2026-03-31** —173 días
al 20-sep, contra un umbral de 134— y decidió **no** renombrar la card, con el
argumento de que el rótulo oscilaría cada vez que la cámara publicara o dejara de
publicar.

Ese argumento era débil en un punto que el propio ADR-0332 dejó medido: de los
**10 comunicados computables** de la ventana móvil que produce el valor
publicado, **9 son de UIA y 1 de AEA** (un apoyo del 2026-03-03). La card se
llamaba «Postura pública de las cámaras empresarias» y medía, en los hechos, una.
Es el patrón que ADR-0217 y ADR-0218 dejaron prohibido: un rótulo que promete más
que el contenido.

## Factores de decisión

- **Si el rótulo dice UIA, el cálculo tiene que ser UIA.** Cambiar sólo el rótulo
  y dejar el comunicado de AEA adentro es reemplazar una imprecisión por otra.
- El recorte **adelgaza la base de cada mes**, y hay que medir cuánto antes de
  decidir si eso se acepta o se corrige en el mismo movimiento.
- Los 46 comunicados de AEA están codificados con doble codificación ciega: son
  trabajo hecho y **no se borran**.
- Reponer AEA tiene que costar una línea, no una arqueología.

## Opciones consideradas

1. **Cambiar sólo el rótulo**, dejando a AEA en el cálculo.
2. **Sacar a AEA del perímetro y renombrar** — elegida.
3. **Dejar todo como estaba** (la decisión de ADR-0332).

## Decisión

**Opción 2.** `APOYO_CAMARAS_PERIMETRO = ("UIA",)` en `politica.py` filtra el
cálculo, y la card pasa a llamarse **«Postura pública de la UIA»**. La
descripción pública y el `organismo` de la ficha dejan de nombrar dos cámaras.

**No se agrega un mínimo de observaciones por ventana, y conviene decir por qué
no**: se probó `APOYO_MIN_OBSERVACIONES = 3` y se retiró. Rompía siete pruebas, y
una de ellas —`test_la_card_cortada_se_declara_desactualizada_y_no_cuenta_lo_posterior`—
afirma `comunicados_ventana == 2`, o sea que el diseño **espera** que una ventana
de dos comunicados publique. Cambiar eso es otra decisión de método, con su propio
ADR, y no entra por la ventana de un cambio de perímetro. Queda como hallazgo
declarado en las consecuencias.

Los comunicados de AEA **siguen en el registro**, codificados y con su
concordancia. La guarda de ADR-0332 **sigue vigilándola**, y eso ahora tiene un
uso nuevo: el día que AEA vuelva a publicar, el aviso es la señal para reponerla
en `APOYO_CAMARAS_PERIMETRO`.

La opción 1 se descartó porque el rótulo seguiría siendo falso, con menos ruido
pero igual de falso. La opción 3 —la de ADR-0332— queda **sin efecto en este
punto**: su objeción del rótulo oscilante es real, pero se resuelve con una
constante y un ADR, no dejando publicada una card que promete dos cámaras y mide
una.

### Consecuencias

El costo es real y se declara acá, no en una nota al pie:

| | con AEA | solo UIA |
|---|---|---|
| Puntos de serie | **34** | **30** |
| Arranque | 2023-12 | **2024-04** |
| Meses con menos de 3 observaciones | 1 de 34 | **9 de 30** |
| Saldo publicado del mes | **−0,20** | **−0,333** |

- Se pierden **4 puntos de serie**: arranca en abr-2024 en vez de dic-2023,
  porque UIA tiene menos corpus relevado —su primer comunicado es de diciembre de
  2023— y AEA venía desde 2020.
- **Nueve de los treinta meses quedan con una o dos observaciones** contra uno de
  treinta y cuatro antes, y los tres primeros dan −1,0 sobre dos comunicados. Es
  la consecuencia más incómoda del recorte y no se tapa: un saldo de ±1 sobre esa
  base no describe una postura. Corregirlo pide un mínimo por ventana, que es
  otra decisión (ver arriba) y queda pendiente.
- El valor del mes se mueve de −0,20 a −0,333 **sin que haya cambiado ningún
  dato**: cambió qué se cuenta. Cualquier lectura de la serie que cruce el
  20-sep-2026 compara dos perímetros.
- De los 38 computables del registro, **quedan 15 en el cálculo**; los 23 de AEA
  pasan a archivo activo.
- La dimensión de sector privado del ITCP no cambia de peso: el indicador sigue
  puntuando con su 50%.

### Confirmación

- `tests/test_camara_muda.py` sigue en verde: la guarda vigila a las dos cámaras
  y no depende del perímetro de cálculo, que es lo que la hace útil para
  detectar el regreso de AEA.
- `test_la_ficha_no_se_queda_atras` exige que la ficha registre este ADR: la
  entrada de `cambios` del 2026-09-20 declara el recorte, el costo en puntos de
  serie y el cambio de −0,20 a −0,333.
- `npx tsc --noEmit` limpio sobre los tres archivos de la capa pública.
- `test_la_serie_no_empieza_antes_del_periodo_y_es_mensual_ascendente` fija el
  arranque en 2024-04 y dice, en su propio mensaje de error, que si volvió a
  2023-12 es porque alguien repuso AEA y hay que revisar este ADR.
- Reproducible: con `APOYO_CAMARAS_PERIMETRO = ("AEA", "UIA")` la serie vuelve a
  dar 34 puntos desde 2023-12 y el saldo −0,20.

## Pros y contras de las opciones

**Opción 2 (elegida).** Bueno: el rótulo dice lo que mide y el recorte es una
constante reversible. Malo: acorta la serie, mueve un número publicado sin que
haya cambiado ningún dato de origen, y deja nueve meses con base de una o dos
observaciones.

**Opción 1.** Bueno: no toca el número ni la serie. Malo: el rótulo seguiría
prometiendo dos cámaras mientras una aporta 1 de 10 observaciones.

**Opción 3.** Bueno: conserva la serie larga y la base más ancha. Malo: deja
publicada la imprecisión que ADR-0217 y ADR-0218 prohibieron, y el aviso de
ADR-0332 la repetiría cada noche sin que nada la resuelva.

## Más información

- ADR-0332 — la guarda que midió el silencio de AEA y decidió no renombrar.
  Este ADR revisa esa decisión con el dato que ella misma produjo.
- ADR-0310 — el corpus cerrado, que sigue rigiendo: la serie se detiene en el
  último mes con todo clasificado.
- ADR-0217 y ADR-0218 — los dos casos en que un indicador midió algo distinto de
  lo que su nombre decía, y por los que este recorte no era opcional.
