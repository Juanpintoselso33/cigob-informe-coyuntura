---
madr: 4
id: '0377'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [insistencias_vetos, rechazos_decretos, veto_quorum, desafios_legislativos]
archivos: ['scripts/itcp.py', 'scripts/politica.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/datos.ts']
relacionado: ['0069', '0089', '0245', '0330', '0359', '0398']
ambito: 'Cinturón político · ITCP · dimensión Poder legislativo'
origen: 'Reunión de Juan y Luis Babino del 26-oct-2026 (acuerdos enviados por Luis ese día): «sesiones caídas por falta de quórum» y «leyes aprobadas contra el Ejecutivo» están mal formuladas y se reemplazan por insistencias sobre vetos y rechazos de DNU.'
---

# ADR-0377 — Vetos insistidos y decretos derogados reemplazan a quórum y desafíos

## Contexto y planteo del problema

En la dimensión de poder legislativo, `veto_quorum` contaba las sesiones de
Diputados que caían por falta de quórum y `desafios_legislativos`
([[0089-desafios-en-lugar-de-derrotas]]) contaba toda norma del Ejecutivo
llevada al recinto, la ganara o la perdiera. La revisión del 26-oct los
consideró mal formulados: el primero mide si la cámara se reúne y el segundo
mezcla el intento con la derrota. Además, los dos estaban clavados en 100 (pedido
1 de la revisión política de Luis).

## Factores de decisión

- Medir lo que el Congreso efectivamente le da vuelta al Ejecutivo.
- No pedir fuentes nuevas: el registro versionado de vetos y decretos
  (`data/politica/derrotas_legislativas_eventos.json`, verificado a mano contra
  InfoLeg y las actas, y actualizado en cada corrida) ya tiene cada insistencia y
  cada rechazo por cámara.

## Opciones consideradas

- **Dos conteos de lo consumado en las dos cámaras (elegida).**
- Contar también lo aprobado por una sola cámara.

## Decisión

- `insistencias_vetos`: vetos con insistencia de las dos cámaras (ley promulgada
  por insistencia, art. 83 CN), fechados en la segunda cámara.
- `rechazos_decretos`: decretos de la ley 26.122 —DNU y delegados, que siguen el
  mismo trámite— rechazados por las dos cámaras (lo que los deroga, art. 24),
  fechados en el rechazo de la segunda.
- Los dos cuentan 12 meses calendario, menor = mejor, con anclas conceptuales:
  0 → 100 · 1 → 60 · 3 → 35 · 4 o más → 10.
- Toman el 0,15 + 0,15 de los anteriores. `veto_quorum` y
  `desafios_legislativos` pasan a suspendidos: se siguen calculando y sus pesos
  de diseño quedan escritos ([[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]]).
- Card y serie salen de la misma cuenta (`politica.serie_eventos_12m`).

### Consecuencias

- En todo el mandato: 3 insistencias consumadas (discapacidad, 4-sep-2025;
  financiamiento universitario y Garrahan, 2-oct-2025) y 6 decretos derogados
  (fondos de inteligencia, 12-sep-2024; marina mercante y cuatro delegados,
  21-ago-2025). Contrastado contra un relevamiento independiente del Boletín
  Oficial y las actas el 27-oct-2026: coincide.
- Con los datos del 27-oct-2026 las dos ventanas dan cero, como daban los
  anteriores, y el índice político no cambia (72,4 con ADR-0374). El 100 ahora
  significa «el Congreso no le dio vuelta ninguna norma en 12 meses».
- Lo que aprueba una sola cámara (el Senado insistió en los vetos de Bahía
  Blanca y de los ATN; rechazó el DNU 70/2023) no cuenta: queda en el registro.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_insistencias_y_rechazos.py` fija la regla de las dos cámaras, la
ventana y la composición de la dimensión.

## Pros y contras de las opciones

- Lo consumado: es la derrota que cambia una norma; deja afuera señales políticas
  de una sola cámara.
- Una sola cámara: más eventos, pero cuenta como derrota lo que deja la norma en pie.
