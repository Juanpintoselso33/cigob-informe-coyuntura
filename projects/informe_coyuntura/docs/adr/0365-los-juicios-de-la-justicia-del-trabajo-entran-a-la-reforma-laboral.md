---
madr: 4
id: '0365'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [juicios_trabajo_capital, litigiosidad_laboral]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'scripts/itcg.py', 'scripts/procedencia_anclas.py', 'config.py', 'web/src/lib/fichas.ts', 'tests/test_juicios_trabajo_capital.py']
relacionado: ['0023', '0128', '0361', '0369', '0379', '0385']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma laboral'
origen: 'Observación L2 de la auditoría externa del cinturón de Gestión (oct-2026) y decisión de Juan del 26-oct-2026.'
---

# ADR-0365 — Los juicios de la Justicia del Trabajo entran a la reforma laboral

## Contexto y planteo del problema

La auditoría de CiGob ([[0361-respuesta-a-la-auditoria-del-cinturon-de-gestion]])
propuso medir la litigiosidad con los juicios iniciados en la Justicia Nacional
del Trabajo y citó 55.337 y 58.504. No los habíamos encontrado. El 26-oct
aparecieron: son los expedientes entrados en primera instancia en 2024 y 2025,
que publica la Oficina de Estadísticas del Consejo de la Magistratura
(estadisticas.pjn.gov.ar, Fuero del Trabajo), por semestre y en CSV desde 2023.

Hasta ahora el resultado de la reforma se medía sólo con los juicios del sistema
de riesgos del trabajo (SRT): todo el país, mensual, pero sin despidos ni
diferencias salariales.

## Factores de decisión

- Medir lo que la auditoría pidió, con la fuente que ella misma usaba.
- No perder la medida nacional y mensual que ya había.
- Mantener la regla de [[0128-fuerzas-en-la-dotacion-y-peso-del-fal]]:
  mitad instrumento, mitad resultado.

## Opciones consideradas

- Reemplazar la medida de la SRT por la de la Justicia del Trabajo.
- **Sumarla como segunda medida del resultado (elegida).**
- No sumarla: sólo cubre la Capital y es semestral.

## Decisión

Entra `juicios_trabajo_capital`: juicios entrados en primera instancia de los
dos últimos semestres publicados contra los dos anteriores, en porcentaje.

- **Pesos de la dimensión:** el Fondo de Asistencia Laboral sigue con 50 %;
  `litigiosidad_laboral` pasa de 50 % a 25 % y la nueva medida toma el otro 25 %.
- **Escala:** la misma de `litigiosidad_laboral` (≤ −15 → 100 · −15 a −5 → 85 ·
  −5 a 5 → 65 · 5 a 20 → 40 · > 20 → 10). Es la misma cuenta sobre otro
  universo, y la serie propia (cuatro puntos) no alcanza para calibrar.
  Procedencia: `convencion`.
- **Frescura:** tope de 400 días. El dato se fecha al día 1 del último mes del
  semestre y queda hasta que sale el siguiente; el segundo semestre de 2025 salió
  cerca del 20-may-2026.
- **Serie:** escalonada mensual desde diciembre de 2024: cada mes lleva el último
  semestre cerrado, como la de concesiones. Con un punto cada seis meses, la
  reconstrucción mensual del índice lo perdía diez meses por año (lo encontró la
  revisión de Codex).
- **Semestre faltante:** si falta uno intermedio, se usa la última ventana de
  cuatro semestres completa.

Datos al 26-oct-2026 (entrados en primera instancia): 2023 S1 28.221 · S2 30.299 ·
2024 S1 25.859 · S2 29.478 · 2025 S1 25.562 · S2 32.942 · 2026 S1 28.911. Los
12 meses hasta junio de 2026 suman 61.853 contra 55.040: **+12,4 %**.

### Consecuencias

- Con +12,4 % la medida puntúa cerca de 40 y baja la dimensión Reforma laboral y
  el índice de Gestión. El efecto exacto queda en el commit de la corrida.
- Por ser método, el cambio llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]). Los meses anteriores a
  diciembre de 2024 no tienen punto y la dimensión se renormaliza.

### Confirmación

`tests/test_juicios_trabajo_capital.py` lee un CSV real de la fuente y fija la
cuenta de 12 contra 12 meses; `tests/test_itcg.py` fija los pesos.

## Pros y contras de las opciones

- Reemplazar: mide todos los juicios laborales, pero pierde el país y el ritmo
  mensual.
- Sumar: conserva las dos miradas; a cambio, la dimensión depende de un dato que
  se actualiza dos veces por año.
- No sumar: deja sin respuesta un pedido de la auditoría que sí se puede medir.

## Más información

Oficina de Estadísticas del PJN, «Justicia Nacional del Trabajo 2025» (datos
actualizados al 20 de mayo de 2026) y CSV «Resumen - Trámite de expedientes»
por semestre, 2023-2026.
