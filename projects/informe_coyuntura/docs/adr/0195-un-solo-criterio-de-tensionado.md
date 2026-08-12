---
madr: 4
id: '0195'
estado: 'aceptado'
fecha: 2026-08-12
cinturon: 'transversal'
parametros: ['UMBRALES["EN_TENSION_MAX"]']
archivos: ['config.py', 'scripts/generar_informe.py', 'scripts/publicar.py', 'tests/test_estado_un_solo_criterio.py']
relacionado: ['0082', '0194']
ambito: 'Estado de los cinturones · alerta multicinturón · snapshot publicado'
origen: 'Revisión adversarial del rediseño visual (ADR-0194): al intentar mostrar en la web si un cinturón contaba para la alerta, el dato no cerraba'
---

# ADR-0195 — Un cinturón "tensionado" cuenta para la alerta, siempre

## Contexto y planteo del problema

El informe tenía **tres criterios distintos para la misma pregunta**: ¿este
cinturón está tensionado?

| Dónde | Criterio |
|---|---|
| `generar_informe._estado` | `score > EN_TENSION_MAX` |
| `publicar._estado` | copia a mano del anterior, declarada "réplica" |
| `detectar_barbarismo` | `score >= EN_TENSION_MAX + 1` |

El `+1` sólo coincide con `> EN_TENSION_MAX` **si los scores son enteros**, y no
lo son: tienen un decimal. Entre 6 y 7 quedaba una **zona muerta** donde un
cinturón estaba clasificado `tensionado` y a la vez **no contaba** para la regla
de alerta multicinturón.

Con el snapshot de agosto de 2026 le pasaba a vida cotidiana, en **6,9**: el
informe la llamaba tensionada, la card la mostraba tensionada, y la regla "dos o
más cinturones tensionados señalan inestabilidad sistémica" la ignoraba.

Con dos cinturones cualesquiera entre 6,01 y 6,99 la interfaz habría dicho que
hay dos tensionados mientras `alerta_multicinturon` seguía en `false`.

### Cómo apareció

No lo encontró un test: los tests no miraban la coherencia entre las tres
definiciones. Apareció montando el rediseño visual
([[0194-la-aguja-es-la-lectura-primaria]]). Al querer mostrar en la página de
cada cinturón si contaba para la alerta, hubo que elegir un criterio, y ahí se
vio que no había uno. Una versión intermedia llegó a publicar un chip que decía
"Cuenta para la alerta sistémica: Sí" para vida cotidiana, que era falso; se
retiró y quedó anotado como pendiente de metodología.

## Factores de decisión

- Una sola definición, no tres que puedan desincronizarse ([[0082-un-solo-camino-al-puntaje]]).
- No mover los umbrales: la discusión de si el corte debe ser 6 o 7 es otra, y
  no se resuelve de contrabando dentro de un arreglo de coherencia.
- El arreglo tiene que ser el que NO cambia la lectura publicada hoy, si existe.

## Opciones consideradas

- **Unificar en `> EN_TENSION_MAX`, el criterio de `_estado`** — elegida.
- **Unificar en `>= EN_TENSION_MAX + 1`**, el de la alerta. Descartada: dejaría
  cinturones clasificados "tensionados" que no lo son para ninguna otra cosa, y
  además obliga a cambiar la etiqueta que ve el lector.
- **Subir `EN_TENSION_MAX` a 7 y quedarse con el `+1`.** Descartada: eso sí
  mueve la metodología —reclasifica cinturones entre 6 y 7— y no es lo que este
  ADR viene a decidir.

## Decisión

`config.estado_de_score()` y `config.es_tensionado()` son la **única**
definición. `generar_informe._estado` y `publicar._estado` pasan a ser esa misma
función, no copias, y `detectar_barbarismo` cuenta con `es_tensionado()`.

```python
def estado_de_score(score):
    if score <= UMBRALES["ESTABLE_MAX"]:   return "estable"
    if score <= UMBRALES["EN_TENSION_MAX"]: return "en_tension"
    return "tensionado"

def es_tensionado(score):
    return estado_de_score(score) == "tensionado"
```

Los umbrales **no se tocan**: siguen en 3 y 6.

### Consecuencias

- Desaparece la zona muerta: todo cinturón por encima de 6 cuenta.
- **La lectura publicada hoy no cambia.** Vida cotidiana pasa a integrar la
  lista de tensionados, pero es el único, y la alerta necesita dos: sigue en
  `false`. El arreglo corrige el mecanismo sin mover el resultado, que es la
  mejor forma de corregirlo.
- Queda una divergencia **que este ADR no resuelve y no pretende resolver**: los
  cortes del semáforo (4 · 6 · 8) no coinciden con los de `estado` (3 · 6). Son
  dos particiones de la misma tensión 0-10 y siguen conviviendo. La diferencia
  es que ahora conviven dos y no tres, y ninguna se contradice a sí misma.

### Confirmación

`tests/test_estado_un_solo_criterio.py` fija la **propiedad**, no los números:
recorre la escala 0-10 de a centésimos y verifica que no exista ningún score que
sea "tensionado" y no cuente para la alerta. Si mañana se mueven los umbrales,
el test sigue valiendo. Verifica además que las tres definiciones sean la misma
función, no funciones equivalentes.

## Pros y contras de las opciones

**Unificar en `> EN_TENSION_MAX`** (elegida)

- Bueno, porque no cambia lo publicado hoy: corrige el mecanismo, no el
  resultado.
- Bueno, porque la etiqueta que ve el lector y el conteo pasan a decir lo mismo.
- Malo, porque amplía en los hechos qué cuenta para la alerta —de ≥7 a >6—, y
  eso puede levantar la alerta antes en algún mes futuro. Es el precio de que
  "tensionado" signifique una sola cosa.

**Unificar en `>= EN_TENSION_MAX + 1`**

- Bueno, porque conserva exactamente el comportamiento histórico de la alerta.
- Malo, porque obliga a decirle "tensionado" a algo que no cuenta como tal.

## Más información

- Los umbrales viven en `config.UMBRALES`; si alguna vez se discuten, el test de
  propiedad sigue siendo válido sin tocarlo.
