---
madr: 4
id: '0385'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [siniestralidad_laboral, litigiosidad_laboral]
archivos: ['scripts/gestion.py', 'scripts/itcg.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/validacion_externa.py', 'config.py', 'data/gestion/srt_siniestralidad.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0023', '0365', '0379', '0359']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma laboral'
origen: 'Pedido de Marcos (dirección de CiGob) y decisión de Juan del 27-oct-2026.'
---

# ADR-0385 — La siniestralidad reemplaza a los juicios del sistema de riesgos

## Contexto y planteo del problema

[[0379-vuelven-los-juicios-por-riesgos-del-trabajo]] repuso en Reforma laboral los
juicios del sistema de riesgos del trabajo (`litigiosidad_laboral`, [[0023-litigiosidad-al-itcg]])
con el 50/25/25 de [[0365-los-juicios-de-la-justicia-del-trabajo-entran-a-la-reforma-laboral]].
Marcos pidió otra cosa: medir «la siniestralidad registrada en el sistema de
riesgos del trabajo», es decir los accidentes y enfermedades que el sistema
registra, no los juicios que genera. Juan lo decidió el 27-oct-2026.

## Factores de decisión

- Lo pedido es una medida de siniestralidad; los juicios son una consecuencia
  lejana de ella.
- La Superintendencia de Riesgos del Trabajo (SRT) publica el dato oficial, para
  todo el país y con el índice de incidencia ya definido.
- El informe provisorio se sobrescribe en la misma dirección: sin guardar cada
  edición, la fuente no conserva su historia.

## Opciones consideradas

- **Reemplazar los juicios por la siniestralidad, con el mismo 25 % (elegida).**
- Sumar la siniestralidad y mantener los juicios, repartiendo la dimensión en
  cuatro.
- Dejar los juicios.

## Decisión

Reforma laboral queda 50 % Fondo de Asistencia Laboral, 25 % siniestralidad
laboral y 25 % juicios de la Justicia Nacional del Trabajo. `litigiosidad_laboral`
sale de la tabla de pesos y pasa a `INDICADORES_SUSPENDIDOS`: sigue calculándose,
no puntúa ni se publica como tarjeta.

**`siniestralidad_laboral`.** Índice de incidencia de accidentes de trabajo y
enfermedades profesionales con días de baja o secuelas incapacitantes (sin
accidentes in itinere), total del sistema, por mil personas cubiertas. El valor
es la variación porcentual del índice del período acumulado del año contra el
mismo período del año anterior; menos es mejor. Con el informe de enero a junio
de 2026: (149.066 / 9.991.247) contra (159.671 / 10.167.202), 14,92 contra 15,70
por mil, **−5,0 %**.

- **Fuentes.** Informe provisorio de accidentabilidad laboral (PDF trimestral,
  Cuadro 1) y Serie histórica de indicadores de AT y EP, Revisión 4 (Excel, un
  punto por año, 2019-2025, con el índice de incidencia de la propia SRT).
- **Store versionado** `data/gestion/srt_siniestralidad.json`. El PDF se
  publica siempre en la misma URL y se sobrescribe, así que cada corrida guarda
  la edición que lee, con los tres años de su Cuadro 1. Sembrado con la edición
  de enero a junio de 2026 y los seis anuales 2020-2025.
- **Fecha del dato.** Primer día del último mes del período (enero-junio →
  2026-06-01); los anuales, en diciembre.
- **Rezago medido.** La edición de enero a junio de 2026 dice «elaboración:
  septiembre» y ya estaba en línea el 10-oct (captura del archivo web); la de
  enero a marzo de 2025 dice «junio» y estaba en línea el 13-jul-2025. Sale
  entre dos y tres meses después del cierre: hasta ~125 días desde la
  `fecha_dato`, y ~220 justo antes de la edición siguiente. `MAX_DIAS` = 320,
  el margen de un trimestre salteado.
- **Parser.** `pdfplumber`. Falla en voz alta si no encuentra el período o las
  filas, si unidades productivas más casas particulares no suman el total, o si
  las variaciones que el informe imprime en su Cuadro 2 no coinciden con las que
  salen de su Cuadro 1; en ese caso el colector devuelve ausencia y el pipeline
  usa el cache. Las personas cubiertas son promedios y el informe imprime un
  total que puede diferir en 1 de la suma (enero-junio de 2024: 9.716.834 +
  532.197 = 10.249.031, el informe dice 10.249.030): se tolera 1 en esa fila y
  nada en los casos.
- **Serie.** Un punto por año (año completo contra el anterior, desde 2020) más
  un punto por cada edición provisoria leída; escalonada mensual, como la de los
  juicios de la Capital, y de la misma cuenta que la tarjeta
  (`gestion.siniestralidad_puntos`).
- **Escala.** La convención de `litigiosidad_laboral`: variación %, menor =
  mejor, cortes en −15, −5, +5 y +20 %. Se declara `convencion` en
  `procedencia_anclas.py`: seis variaciones anuales no alcanzan para calibrar una
  escala propia, y mover los cortes mirando el rango observado (−31 % en 2020,
  +32 % en 2021) sería ajustarlos al resultado.

### Consecuencias

- Con el snapshot del 27-oct-2026: el valor es −5,0 % y el puntaje 75,0 (cae
  sobre el corte de −5, entre el tramo de 85 y el de 65). `litigiosidad_laboral`
  puntuaba 64,8 (+0,1 %). Reforma laboral pasa de 76,2 a 78,8 y el índice de
  gestión, de 80,1 a 80,5.
- Con el corte de la edición de septiembre (el último dato de cada serie hasta
  septiembre): el store tiene la edición de enero a junio, así que el corte la
  usa; Reforma laboral pasa de 55,6 a 58,2 y el índice de gestión, de 80,6 a
  81,0. La edición se elaboró en septiembre, pero el store no sabe qué día se
  publicó: si salió después del cierre del mes, el corte de septiembre y el de
  junio-agosto estarían leyendo un dato que todavía no estaba en línea, igual que
  la serie semestral de los juicios de la Capital.
- Por ser método, llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).
- El techo de convención del ITCG en `procedencia_anclas.py` sube a 0,33: la
  escala de los juicios era `historia_larga` y la de la siniestralidad es
  `convencion`, como ya había pasado en [[0369-los-juicios-por-riesgos-del-trabajo-salen-de-la-reforma-laboral]].

### Confirmación

`tests/test_siniestralidad_laboral.py` fija el parser contra el texto real del
Cuadro 1 (dos ediciones), el cálculo y el 50/25/25;
`tests/test_juicios_trabajo_capital.py` y `tests/test_publicar.py` fijan la
composición y el conteo de 14 indicadores del índice.

## Pros y contras de las opciones

- Reemplazar: mide lo que se pidió; el peso no se mueve. La serie propia es corta
  y la escala es una convención.
- Sumar los dos: más cobertura, pero obliga a repartir de nuevo la dimensión y
  deja un indicador que nadie pidió.
- Dejar los juicios: no responde al pedido de Marcos.
