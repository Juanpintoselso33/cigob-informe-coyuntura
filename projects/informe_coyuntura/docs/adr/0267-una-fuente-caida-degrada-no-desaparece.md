---
madr: 4
id: '0267'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [consumo_carnes_total]
archivos: ['scripts/publicar.py', 'tests/test_una_fuente_caida_degrada_no_desaparece.py']
relacionado: ['0224', '0225']
ambito: 'Publicación · cinturón Impacto social · qué pasa con una card cuando su fuente no contesta'
origen: 'Regresión en vivo el 25-ago-2026: SAGYP devolvió None y el snapshot salió con 62 cards en vez de 63'
---

# ADR-0267 — Una fuente caída degrada el indicador, no lo hace desaparecer

## Contexto y planteo del problema

`_carry_forward` existe para que un corte de una fuente no borre un indicador
del score: cuando una card llega con `valor: None`, restaura el último valor
publicado y la marca `desactualizado`.

**Pero sólo ve las claves que existen.** Si el colector falla y `publicar.py`
directamente no agrega la clave, no hay nada que reparar y el indicador se cae
del snapshot sin que nada avise.

Ya había pasado dos veces, y las dos se repararon **de a una**:

| fecha | indicador | cómo se descubrió |
|---|---|---|
| 2026-07-09 | `sentimiento_digital` | Google Trends con límite de tasa. Se descubrió **después de pushear** |
| 2026-08 | `motorizacion_total` | preventivo, al fundir autos y motos (ADR-0224) |
| 2026-08-25 | `consumo_carnes_total` | SAGYP devolvió `None` en una corrida de esta misma sesión |

En el tercer caso el `_add` vivía **adentro** del `if carnes.get("vacuna") is
not None`, y la rama de respaldo publicaba la carne vacuna desde CICCRA y se
olvidaba del total —que no tiene respaldo—. El snapshot salió con **62 cards en
vez de 63**.

`gate_calidad.py` lo dejó pasar en los tres casos, y no es un olvido: mira
estructura, frescura y card-contra-serie. Un snapshot al que le falta un
indicador está perfectamente bien formado.

### Lo que apareció al escribir la guarda genérica

Buscar el patrón en vez del caso destapó **once sitios más**, todos en
`build_vida`:

- **Dos indicadores más podían desaparecer**: `mortalidad_pymes` y
  `trabajo_independiente`, los dos con su `_add` dentro de un `if`.
- **Ocho se rellenaban con cero**: el patrón `round(x.get("valor", 0), 2)` en
  `brecha_salario_cbt`, `ipc_alimentos`, `alquiler_real`, `informalidad`,
  `despacho_cemento`, `subocupacion_demandante`, `icc_utdt` e `indice_lider`.

**El relleno con cero es peor que la ausencia.** Un cero no es un dato
faltante: es un dato. `_carry_forward` sólo repara los `None`, así que el cero
pasaba de largo y se publicaba como si el organismo lo hubiera informado. Con
el INDEC caído, la card de inflación de alimentos habría salido **0,00% m/m** —
una cifra fabricada, no una vieja.

## Factores de decisión

- **Un corte de fuente es normal**; que borre o invente un número, no.
- **La guarda tiene que ser genérica.** Tres reparaciones por indicador dieron
  tres incidentes: lo que hay que verificar no es que la carne esté.
- **Degradar visible antes que degradar en silencio.**

## Opciones consideradas

1. **Reparar el tercer caso** y seguir.
2. **Reparar el patrón**: que todo indicador que puntúa se agregue siempre, con
   `None` si su fuente no contestó, y vigilarlo con una guarda genérica.

## Decisión

**Opción 2.**

- Todo `_add` de un indicador que puntúa sale de su `if` y se llama siempre,
  con `valor: None` cuando la fuente no trajo el dato. Lo que sí queda adentro
  del `if` es el **detalle** que se arma con varios campos del propio dato.
- El patrón `round(x.get("valor", 0), …)` se reemplaza por `_red(...)`, que
  redondea **conservando el `None`**.
- `tests/test_una_fuente_caida_degrada_no_desaparece.py` construye el cinturón
  con **todas** las fuentes caídas (`build_vida({})`) y exige que aparezca cada
  indicador que hoy integra el índice, y que ninguno traiga un valor de relleno.

### Consecuencias

- Con una fuente caída la card queda con su último valor y el cartel de
  desactualizada, que es lo que el lector necesita ver. Antes, según el
  indicador, o desaparecía o mostraba un cero inventado.
- Los indicadores nuevos quedan cubiertos sin que nadie se acuerde: la guarda
  deriva la lista de `DIMENSIONES_ITVC`, no de una enumeración propia.
- **Quedan dos excepciones declaradas** y son legítimas: `mora_familias` y
  `carga_servicio_deuda_hogares` no tienen colector propio —se sintetizan desde
  la serie ya descargada— así que `build_vida({})` no puede producirlas.
- **Queda un residuo declarado**: `informalidad` y `alquiler_real` siguen
  redondeando sobre un `.get(..., 0)` previo al punto que la guarda vigila. El
  test los nombra en vez de taparlos.
- La guarda cubre **el cinturón de Impacto social**, que es donde estaba el
  incidente y donde vive `_carry_forward`. Extenderla a los otros tres es
  trabajo pendiente y no se hizo a ciegas.

### Confirmación

Tres mutaciones, tres fallas: devolver la carne adentro de su `if`, devolver a
`_red` el relleno con cero, y devolver `mortalidad_pymes` adentro del suyo.

## Pros y contras de las opciones

### 1 · Reparar el tercer caso

- Bueno: una línea, y el snapshot de hoy sale bien.
- Malo: es exactamente lo que se hizo las dos veces anteriores. Habría dejado
  los otros once sitios en pie, incluidos los ocho que fabrican un cero.

### 2 · Reparar el patrón *(elegida)*

- Bueno: cierra la clase entera y cubre lo que venga.
- Malo: toca once sitios de una función central en la misma corrida en que se
  publica. Mitigado con la guarda genérica y las mutaciones.

## Más información

El incidente de julio de 2026 dejó escrito en `CLAUDE.md` que
`gate_calidad.py` pasando **no** significa que la suite pase, y que hay que
correr las dos. Este caso lo confirma por tercera vez: el gate dio `exit=0` con
el indicador ya ausente del snapshot.
