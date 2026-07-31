---
madr: 4
id: '0104'
estado: 'aceptado'
nota_estado: 'Aceptado (resultado negativo)'
fecha: 2026-07-20
cinturon: 'transversal'
archivos: ['scripts/out_of_sample.py']
continua: ['0103']
ambito: 'Validación del método · `scripts/out_of_sample.py`'
---

# ADR-0104 — El out-of-sample no puede resolver la circularidad, y por qué

| **Continúa** | ADR-0103 (procedencia de las anclas) |

## Opciones consideradas

- **Conservar `out_of_sample.py` pero sin que emita veredictos** — elegida: marca candidatos (`mirar` / `sin señal`) y publica al lado el rango crudo de cada ventana, que es el dato que permite decidir.
- **Que emita un veredicto** — descartada: el out-of-sample no puede resolver la circularidad.

## Decisión

`scripts/out_of_sample.py` se conserva, pero **no emite veredictos**. Marca
candidatos (`mirar` / `sin señal`) y publica al lado el **rango crudo de cada
ventana**, que es el dato que permite decidir cuál de las dos causas está
operando. La decisión queda en quien lee, que es donde puede estar.

`brecha_obra_publica` funciona como **control positivo** del método: 100 meses
de serie y anclas que ADR-0088 declara explícitamente no calibradas contra el
rango observado. Sale `sin señal`, como debe. Si algún día dispara, lo primero
a sospechar es el test.

## Más información

### Qué se intentó

ADR-0103 dejó medido que entre el 51% y el 83% del peso de cada índice descansa
en anclas calibradas contra el período que se está midiendo. El paso natural
era ponerlas a prueba: **aplicar las bandas de hoy a los años anteriores a
dic-2023 y ver si siguen discriminando**. Una banda dibujada alrededor del rango
2024-2026 debería aplastarse fuera de él; una que mide algo real debería seguir
separando meses buenos de malos en cualquier período.

El intento falló por dos razones independientes. Las dos importan más que el
resultado que se buscaba.

### Razón 1 — No hay contra qué medir

Sólo 6 de los 42 indicadores tienen una ventana previa utilizable (≥12 puntos
anteriores a dic-2023). En peso:

| índice | peso con historia previa real |
|---|---|
| ITCM | 31% |
| ITCP | 24% |
| ITCG | **4%** |

Reconstruir "el ITCM de Macri" con un tercio de sus indicadores produciría un
número con apariencia de dato y sin contenido — el error que ADR-0095 y
ADR-0085 ya obligaron a no cometer. La unidad de análisis posible es el
indicador suelto, no el índice.

Dos exclusiones que parecen bugs y no lo son: `iaf_transferencias` tiene serie
desde dic-2018 pero es **anual** (cinco puntos previos), y `tcrm` declara
calibrarse con la historia 1997-2026 pero esa serie vive en el BCRA y no en el
repositorio — la afirmación es plausible y no verificable localmente.

### Razón 2 — La prueba no distingue lo que dice distinguir

Ésta es la razón de fondo, y se descubrió porque la primera versión del script
**dio un resultado falso**.

Esa versión marcaba "circular" toda banda que se aplastara fuera de muestra y
discriminara dentro. Marcó tres: `ipc_total`, `litigiosidad_laboral` y
`emae_ia`. Contrastados contra los valores crudos, los tres estaban bien:

| indicador | crudo previo | crudo actual | qué era en realidad |
|---|---|---|---|
| `ipc_total` | 6,42 %/mes (≈112% anual) | 4,87 | la inflación previa **era** catastrófica |
| `litigiosidad_laboral` | +39,2% de juicios | +6,7% | la litigiosidad **se derrumbó** de verdad |
| `emae_ia` | +4,7% i.a. | +1,4% | el rebote post-COVID **fue** extraordinario |

Puntuar cerca del piso una inflación de tres dígitos no es una banda fallando:
es una banda funcionando. El test estaba detectando **cambio de régimen** y
etiquetándolo *circularidad*.

El defecto no es de umbral, es de diseño: una banda circular y un cambio de
régimen genuino **producen la misma firma** en la distribución de puntajes.
Separarlos exige mirar si la realidad subyacente fue de verdad extrema — que es
exactamente lo que ADR-0045 ya obliga a verificar antes de recalibrar contra el
rango observado. El out-of-sample no aporta un atajo a ese juicio: lo replica
con menos información.

### Consecuencia para la pregunta original

**La circularidad señalada por la auditoría no se puede resolver empíricamente
con los datos disponibles.** No es una limitación del esfuerzo puesto: es que
36 de 42 indicadores no existían antes de esta gestión, y para los 6 que sí, la
prueba no discrimina entre las dos explicaciones posibles.

De ahí que la respuesta correcta sea la de ADR-0103 —declarar la procedencia de
cada ancla y publicar cuánto del puntaje descansa en cada tipo— más una regla
que gobierne las anclas **futuras**, donde sí se puede elegir el criterio antes
de ver el dato. Esa regla es el trabajo que sigue.

Publicar un out-of-sample con veredictos habría sido peor que no publicarlo: le
habría dado a la circularidad una respuesta tranquilizadora y equivocada.
