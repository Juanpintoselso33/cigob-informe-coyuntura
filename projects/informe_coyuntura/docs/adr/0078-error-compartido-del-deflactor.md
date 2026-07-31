---
madr: 4
id: '0078'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
archivos: ['scripts/sensibilidad.py']
relacionado: ['0019', '0031', '0075']
ambito: 'Todas las paramétricas · `scripts/sensibilidad.py` · rango de robustez publicado del ITCM'
origen: 'Revisión adversarial externa (18-jul-2026) + observación IV.2 de la auditoría de consistencia macro'
---

# ADR-0078 — El error del deflactor deja de tratarse como independiente

## Contexto y planteo del problema

La simulación de Monte Carlo que produce el rango de robustez publicado
perturbaba **cada indicador con un sorteo independiente**
(`rng.uniform(-RUIDO_INSUMO, RUIDO_INSUMO)` dentro del bucle por indicador).
Bajo ese supuesto los errores se cancelan parcialmente al promediar, y el rango
resultante es más angosto que el real si los errores en verdad se mueven juntos.

### Una precisión sobre el argumento que originó esta revisión

La revisión externa planteó que, con la correlación media de 0,506 entre
componentes que midió ADR-0075, los errores no se cancelan como asume la
simulación. **El argumento apunta bien pero la magnitud citada no es la
correcta**, y conviene dejarlo escrito para no repetir el error: ADR-0075 mide
la correlación entre los **valores** de los indicadores, no entre sus **errores
de medición**. Son cosas distintas. Dos indicadores pueden moverse juntos de
forma perfecta —porque la economía los mueve juntos— y tener errores de
medición completamente independientes, si los miden fuentes distintas con
metodologías distintas.

Lo que sí genera error compartido es **compartir una fuente**. Y ahí hay un caso
concreto, que es justamente la observación **IV.2** de la auditoría: el IPC se
usa como deflactor en varios indicadores a la vez. Si el IPC está mal medido,
todos ellos se equivocan **al mismo tiempo y de forma coordinada**.

## Opciones consideradas

- **Un único error de deflactor por corrida**, compartido por todos los indicadores que lo heredan — elegida.
- **Un error independiente por indicador** — descartada: asume una cancelación entre errores que no ocurre.

## Decisión

Se sortea **un único error de deflactor por corrida**, compartido por los
indicadores que lo heredan, en lugar de un error independiente por indicador.

### El signo importa, y no es el mismo para todos

Este es el punto que hace que la corrección no sea trivial. Si el IPC está
**sobreestimado**:

| indicador | exposición | por qué |
|---|---|---|
| `ipc_total` | **+1** | la inflación medida es esa, y puntúa peor |
| `recaudacion` | **−1** | deflactar de más hunde la variación real |
| `credito_privado` | **−1** | ídem |
| `idc` | **−1** | la BADLAR real queda más baja |
| `idm` | **0 — excluido** | compara M3 **real** contra M2 **real**: el deflactor se cancela en la resta |

La exclusión del IDM no es un olvido: su construcción real-real lo inmuniza
contra el error del deflactor, aunque lo use. Una primera versión de este
análisis aplicó el shock con el mismo signo a los cinco indicadores y **midió un
estrechamiento del rango**, porque los efectos se compensaban artificialmente.
Con los signos correctos el rango se ensancha, que es lo que corresponde.

### Cuánto del error es del deflactor

Se adopta **50%**: una variación real se construye con dos series de precisión
comparable —la nominal y el deflactor—, así que repartir el error mitad y mitad
es el punto de partida neutral. La mezcla preserva la varianza total del ruido
(la parte compartida **reemplaza** a la idiosincrática, no se le suma):

```
ruido_i = √f · exposición_i · shock_deflactor + √(1−f) · idiosincrático_i
```

### Consecuencias

Sobre el rango de robustez publicado del ITCM, con 1.000 y con 20.000 corridas
(resultado idéntico, no es ruido de simulación):

| | p05 | p95 | ancho |
|---|---|---|---|
| errores independientes (anterior) | 60,1 | 63,4 | 3,3 |
| **deflactor compartido (vigente)** | **60,1** | **63,6** | **3,5** |

**El rango se ensancha 9,1%.** El rango de tensión publicado pasa de
[3,7 – 4,0] a [3,6 – 4,0].

La dirección de la crítica era correcta —el rango estaba subestimado— y la
magnitud es modesta. Se corrige igual: un intervalo de incertidumbre que se
publica como medida de robustez no debería apoyarse en un supuesto que el propio
sistema sabe que no se cumple.

El peso efectivo expuesto al deflactor es **24,2%** del ITCM.

Sólo el ITCM recibe el tratamiento: es el único índice con indicadores
deflactados por el IPC. Los demás pasan `exposicion=None` y se comportan igual
que antes.

### Relación con la observación IV.2 de la auditoría

IV.2 pedía documentar la propagación del IPC como riesgo sistémico. Queda
**modelada** en la incertidumbre publicada, no sólo declarada en prosa, que es
un cumplimiento más fuerte del pedido. La observación puede cerrarse.

## Más información

### Precedentes directos

ADR-0019 (análisis de sensibilidad, paso 7 del Handbook JRC/OCDE) · ADR-0031 (ruido aditivo scale-free) · ADR-0075 (matriz de redundancia interna)

### Limitaciones

- El 50% es una elección razonada, no una estimación. Con 30% el ensanche sería
  menor y con 100% mayor; el orden de magnitud no cambia (entre +10% y +28% de
  ancho en el experimento de insumos aislado).
- Las exposiciones son ±1: se modela la **dirección** del contagio, no la
  elasticidad exacta de cada indicador al error del deflactor.
- El deflactor es la única fuente compartida modelada. Puede haber otras —dos
  indicadores que dependan de la misma planilla del BCRA, por ejemplo— que
  siguen tratándose como independientes.
- El experimento de **pesos** no cambia: perturbar ponderaciones es una
  pregunta distinta de la del error de medición.
