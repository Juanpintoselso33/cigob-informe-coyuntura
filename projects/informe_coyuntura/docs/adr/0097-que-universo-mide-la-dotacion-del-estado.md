# ADR-0097 — Qué universo mide la dotación del Estado

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITCG · `reduccion_estado` · ficha pública |
| **Fecha** | 2026-07-20 |
| **Origen** | Auditoría externa del cinturón de gestión (doc 1), prioridad alta |

## El planteo

> "El título y la definición dicen «Administración Pública Nacional», pero el
> campo «Operación estadística» menciona una fuente que incluye «Administración
> Pública Nacional, empresas y sociedades». Conviene confirmar si el −19,8%
> informado corresponde solo a la APN centralizada y descentralizada, o si
> también incorpora empresas del Estado (YPF, Aerolíneas, AySA), **porque son
> dos relatos distintos de la promesa** y hoy la ficha admite ambas lecturas."

La observación es exacta: la ficha decía las dos cosas en campos contiguos.

## La respuesta

El cuadro 1 de la planilla del INDEC abre la dotación así:

```
Total                              341.692
  Administración pública nacional  230.592
    Administración centralizada      57.585
    Administración descentralizada  132.134
    Administración desconcentrada    25.364
    Otros entes                      15.509
  Empresas y sociedades            111.100
```

El colector lee la fila **"Administración pública nacional"**: es **APN pura,
sin empresas del Estado**. El título y la definición eran correctos; lo
incorrecto era el campo "Operación estadística", que había copiado el nombre
completo del dataset en lugar de la serie efectivamente utilizada.

## Y la ambigüedad no tenía consecuencia

Medidos contra dic-2023, los tres universos dan prácticamente lo mismo:

| universo | dic-2023 → may-2026 | variación |
|---|---|---|
| **Administración Pública Nacional** (el publicado) | 231.305 → 185.498 | **−19,80%** |
| Empresas y sociedades del Estado | 110.160 → 87.867 | −20,24% |
| Universo completo | 341.465 → 273.365 | −19,94% |

**La elección de universo no cambia la lectura.** Los "dos relatos distintos"
que la auditoría temía resultan ser el mismo relato: el ajuste de planta fue
parejo entre la administración y las empresas.

## Decisión

1. **Se corrige la ficha** para que diga exactamente qué fila se usa y qué
   agrupa, en lugar del nombre del dataset completo.
2. **El colector publica los tres números.** No alcanza con aclarar cuál se
   usa: publicar los otros dos cierra la objeción en vez de sólo responderla, y
   permite a cualquiera verificar que la elección es indiferente.
3. **El indicador no cambia**: sigue puntuando APN, que es el universo sobre el
   que el Ejecutivo decide directamente su planta. Ni el valor, ni las bandas,
   ni el ITCG se mueven.

## Por qué se elige APN y no el total

Porque la promesa que el indicador opera —achicar el Estado nacional, reducir
ministerios y planta pública— es sobre la estructura administrativa. Las
empresas del Estado tienen lógica de gestión propia: su dotación puede caer por
una privatización, por una reestructuración comercial o por un plan de retiros,
decisiones que no son las mismas que reducir la planta de un ministerio.

Que ambos universos hayan caído casi idéntico en este período es un dato del
período, no una razón para fusionarlos.

## Limitaciones que quedan declaradas

- **Las bandas siguen siendo una convención propia** (~10-12% → banda alta), no
  una meta oficial. Es el punto 3.2 de la misma auditoría; este ADR no lo
  resuelve, lo deja escrito con esas palabras en la ficha.
- **Mide personas, no costo.** La planta puede bajar sin que el gasto salarial
  baje en la misma proporción; por eso el cinturón sigue las dos cosas por
  separado (`reduccion_estado` y `masa_salarial`), un diseño que la propia
  auditoría destaca como buena práctica.
- Los meses recientes vienen imputados y el INDEC los revisa hacia atrás.
