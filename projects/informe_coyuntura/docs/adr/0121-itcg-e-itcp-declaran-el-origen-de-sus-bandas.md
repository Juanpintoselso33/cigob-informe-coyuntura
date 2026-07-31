---
madr: 4
id: '0121'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
archivos: ['procedencia_anclas.py']
continua: ['0120']
cierra: ['0103']
ambito: 'ITCG · ITCP · comentarios de bandas · `procedencia_anclas.py` · trinquete'
---

# ADR-0121 — El ITCG y el ITCP declaran el origen de sus bandas; los tres convergen en ~40%

| **Cierra** | El backlog de circularidad de ADR-0103 en los tres índices con `sin_declarar` |
| **Continúa** | ADR-0120 (lo mismo en el ITCM) |
| **Bajo** | ADR-0045 (no recalibrar para blanquear) · ADR-0105 (trinquete) |

## Contexto y planteo del problema

ADR-0120 cerró el ITCM (83% → 38%) escribiendo el origen de sus siete bandas
`sin_declarar`. Quedaban las de gestión (4) y política (3). Ningún ancla se
movió: **ITCG sigue en 72,5 e ITCP en 69,0.**

## Opciones consideradas

- **Escribir el origen de las bandas del ITCG y del ITCP** — elegida: los tres índices convergen en ~40%.
- **Dejarlas como convención invisible** — descartada: las que siguen siendo convención quedan declaradas como tales.
- **Recalibrar para bajar el número** — prohibido por ADR-0045 y el trinquete de ADR-0105.

### Consecuencias

- Único cambio de código: comentarios en `BANDAS_ITCG`/`BANDAS_ITCP` y la
  reclasificación en `procedencia_anclas.py`. Cero cambios de puntaje —
  verificado: ITCG 72,5 e ITCP 69,0 antes y después.
- El backlog de circularidad de ADR-0103 queda cerrado en su totalidad: no hay
  una sola banda `sin_declarar` en ningún índice.
- Lo que no se resolvió, y no se resuelve escribiendo comentarios: ninguno de
  los cuatro índices tiene cobertura fuerte de anclas **externas**. El ITCP es
  el único con algo (18%: ACIJ, Directorio Legislativo). Subir eso exige
  fuentes de comparación entre gobiernos que en su mayoría no existen — es un
  límite del dominio, no una tarea pendiente.

## Decisión

### La disciplina, distinta a la del ITCM

En el ITCM las siete `sin_declarar` resultaron ser todas bandas normativas o
conceptuales mal etiquetadas, así que la circularidad cayó parejo. **Acá no se
podía asumir lo mismo**: varias bandas de gestión dicen textualmente "calibrado
con el dato real". Reclasificarlas a conceptual para bajar el número sería
gamear el trinquete — exactamente lo que ADR-0045 prohíbe.

Se juzgó una por una, con el criterio: ¿la banda se fijó mirando el rango
observado, o contra un valor con significado propio (el cero, el 100% del plan)?

### Se movieron a conceptual (7)

| indicador | por qué es conceptual |
|---|---|
| `reestructuracion_organismos` (ITCG) | medidor de avance 0-100; el 100 = plan completo |
| `libertad_opcion_salud` (ITCG) | ídem, libre opción plena = 100 |
| `concesiones_infraestructura` (ITCG) | tasa de adjudicación km/plan; 100 = plan adjudicado |
| `votometro_ventaja_lla` (ITCP) | ventaja electoral anclada en el cero (empate), márgenes simétricos |
| `veto_quorum` (ITCP) | tasa de fracaso de quórum anclada en el cero (Congreso funcionando) |
| `iaf_transferencias` (ITCP) | variación real anclada en el cero, como `recaudacion`/`emae` del ITCM |

### Se quedaron como convención (honesto)

`masa_salarial` era `sin_declarar` y **no** se movió a conceptual: es la gemela
de `gasto_funcionamiento` —misma medida de variación real del gasto en personal—
y sus cortes (−5/−12/−20) son grados de recorte fijados contra la magnitud del
ajuste 2024. Se escribió ese origen y se la clasificó `convencion`, que es lo
honesto.

Tampoco se tocaron las que ya eran convención y lo son de verdad:
`reduccion_estado`, `gasto_funcionamiento`, `protocolo_antipiquetes`,
`rigi_inversiones`, `desregulacion_normativa` (ITCG); `cohesion_bloque`,
`conflictividad_nacional`, `alineamiento_senadores_prov`, `desafios_legislativos`
(ITCP). Sus comentarios ya declaraban que se calibraron contra lo observado.

### Resultado: los tres convergen, y el piso tiene sentido

| índice | circular antes | ahora | sin declarar |
|---|---|---|---|
| ITCM | 83% | 38% | 0% |
| ITCG | 51% | **40%** | 0% |
| ITCP | 61% | **40%** | 0% |

Que los tres terminen en ~40% no es coincidencia: **es el núcleo irreducible**.
Lo que queda como convención en cada índice son los indicadores que miden lo que
este gobierno hizo —reducción del Estado, desregulación, RIGI, cohesión del
bloque, alineamiento provincial— calibrados contra lo que efectivamente se
observó, porque no existían antes de dic-2023 y no hay contra qué otra cosa
anclarlos. Es la circularidad que ADR-0103 llamó "irreducible", ahora medida y
declarada en vez de invisible.

### El trinquete, otra vez

Bajar los dos disparó `test_el_techo_sigue_a_la_mejora`. Los techos pasan a 0,40
(ITCG e ITCP) y 0,01 de `sin_declarar` en los dos. Con esto los cuatro índices
—los tres de acá más el ITVC— tienen su circularidad medida, declarada y con
techo que impide que vuelva a subir sin firma.
