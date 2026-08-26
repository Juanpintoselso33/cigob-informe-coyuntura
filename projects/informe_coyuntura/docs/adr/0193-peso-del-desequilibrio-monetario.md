---
madr: 4
id: '0193'
estado: 'aceptado'
fecha: 2026-08-11
cinturon: 'macro'
indicadores: [desequilibrio_monetario, rem_ipc_12m, idm, ipc_total]
parametros: ['DIMENSIONES_ITCM["estabilidad_monetaria"]["indicadores"]', 'TECHOS["ITCM"]["circular"]']
archivos: ['scripts/itcm.py', 'scripts/procedencia_anclas.py', 'tests/test_itcm.py', 'fichas.ts']
continua: ['0192']
relacionado: ['0009', '0055', '0105', '0120', '0192', '0261']
ambito: 'ITCM · dimensión estabilidad monetaria · ponderación interna'
origen: 'Ficha "Desequilibrio Monetario" (Diego): «peso similar al de los indicadores cambiarios/de reservas ya existentes», con el número final deliberadamente abierto'
---

# ADR-0193 — El desequilibrio monetario pesa como las reservas, no como el indicador que reemplazó

## Contexto y planteo del problema

[[0192-desequilibrio-monetario-stock-por-flujo]] incorporó el indicador al ITCM
dejándole el **10%** interno que tenía `presion_dolarizacion`, la que reemplaza.
Eso fue una decisión de mínimo cambio, explícitamente provisoria: la ficha pide
otra cosa.

> «incorporar como un indicador más de la dimensión Macro, con un peso similar
> al de los indicadores cambiarios/de reservas ya existentes, dado que la
> dolarización de carteras suele anticipar tensión cambiaria antes de que esta
> se manifieste en el tipo de cambio»

Con 10% interno sobre una dimensión de 26%, el peso nominal efectivo era **2,6%**
del índice. Los indicadores que la ficha toma como referencia pesan:

| Indicador | Dimensión | Interno | **Nominal en el ITCM** |
|---|---|---:|---:|
| `tcrm` | competitividad externa (11%) | 100% | **11,00%** |
| `reservas_bcra` | financiamiento (16%) | 34% | **5,44%** |
| `desequilibrio_monetario` (antes) | estabilidad monetaria (26%) | 10% | **2,60%** |

O sea: menos de la mitad del más chico de los dos. La directiva no se estaba
cumpliendo.

## Factores de decisión

- Cumplir la directiva de la ficha con un número, no con una aproximación vaga.
- No dejar que un artefacto de la estructura de dimensiones haga de ancla.
- Que lo que ceda peso sea defendible, no lo primero que cierre la cuenta.
- La ponderación interna de una dimensión suma 1: subir a uno es bajar a otros.

## Opciones consideradas

- **20% interno → 5,2% nominal, a la altura de `reservas_bcra`** — elegida.
- **Dejarlo en 10%** (2,6%). Descartada: no cumple la directiva.
- **~31% interno → 8% nominal**, el punto medio entre reservas y TCRM.
  Descartada: obliga a bajar el IPC y toma el TCRM como si fuera comparable.
- **42% interno → 11% nominal, a la altura del TCRM.** Descartada por lo mismo,
  en su forma extrema: dominaría la dimensión.

### Por qué el TCRM no sirve de ancla

El TCRM pesa 11% porque es **el único indicador de su dimensión**
([[0009-idm-y-tcrm-en-el-itcm]] le dio una propia), no porque alguien lo haya
juzgado el doble de importante que las reservas. Su peso nominal es una
consecuencia de cómo quedó armado el índice. Anclar a ese número sería leer un
artefacto de la estructura como si fuera un juicio sobre la importancia
relativa.

`reservas_bcra` es el comparable honesto: mide capacidad externa, convive con
otros indicadores dentro de su dimensión, y es la mitad «de reservas» de la
frase de la ficha.

## Decisión

La dimensión `estabilidad_monetaria` pasa de **40/25/25/10** a **40/20/20/20**:

| Indicador | Interno antes | Interno ahora | Nominal antes | **Nominal ahora** |
|---|---:|---:|---:|---:|
| `ipc_total` | 40% | 40% | 10,40% | **10,40%** |
| `rem_ipc_12m` | 25% | 20% | 6,50% | **5,20%** |
| `idm` | 25% | 20% | 6,50% | **5,20%** |
| `desequilibrio_monetario` | 10% | 20% | 2,60% | **5,20%** |

5,20% queda al lado del 5,44% de las reservas: la directiva se cumple.

**Lo que cede son el REM y el IDM, no el IPC.** No es para cerrar la cuenta: los
tres son lecturas distintas de la misma tensión monetaria —expectativa de
inflación, exceso de pesos sobre la demanda, dolarización de la liquidez— y
ninguna es más autoritativa que las otras, así que pesar las tres igual es más
defendible que el escalón anterior. La inflación **realizada** sí es el núcleo
de la dimensión y conserva su 40%.

### Consecuencias

- El ITCM baja **0,27 puntos** con los datos vigentes: la dimensión pasa de
  65,56 a 64,52, y ×0,26 da −0,27. El indicador que gana peso puntúa 49,1,
  bastante por debajo del REM (81,9) que cede.
- La **circularidad del ITCM sube de 40,3% a 41,6%**, y el techo de
  [[0105-el-trinquete-de-la-procedencia-de-anclas]] pasa de 0,41 a 0,42. No
  cambió ninguna banda: la circularidad se mide ponderada por peso, así que
  duplicar el peso de un indicador con anclas de convención la mueve sola. Es el
  costo declarado de cumplir la directiva.
- Los tres puntajes del fixture de `tests/test_itcm.py` se recalcularon a mano y
  se verificaron contra el motor, no al revés.

### Confirmación

- `tests/test_itcm.py::test_estabilidad_monetaria_usa_pesos_40_20_20_20` pinea el
  reparto.
- `tests/test_itcm.py::test_el_desequilibrio_pesa_como_las_reservas_y_no_como_el_tcrm`
  pinea la directiva en sí: compara el peso nominal contra el de `reservas_bcra`
  y falla si alguien mueve cualquiera de los dos sin mirar al otro.

## Pros y contras de las opciones

**20% interno → 5,2% nominal** (elegida)

- Bueno, porque cumple la directiva contra el comparable correcto.
- Bueno, porque el reparto resultante es plano y explicable: tres lecturas de lo
  mismo pesan lo mismo.
- Malo, porque sube la circularidad del índice.

**Dejarlo en 10%**

- Bueno, porque es el mínimo cambio y no toca nada más.
- Malo, porque incumple la única instrucción explícita que la ficha dejó abierta.

**31% o 42% interno**

- Bueno, porque toma en serio el argumento de la ficha de que la dolarización
  anticipa la tensión cambiaria.
- Malo, porque obliga a bajar la inflación realizada y toma como referencia un
  peso que existe por la estructura del índice, no por un juicio.

## Más información

- El peso de dimensión (26%) no se toca: esto es sólo reparto interno.
- Si más adelante se revisa la estructura de dimensiones y el TCRM deja de estar
  solo en la suya, su 11% deja de ser un artefacto y el comparable cambia.
