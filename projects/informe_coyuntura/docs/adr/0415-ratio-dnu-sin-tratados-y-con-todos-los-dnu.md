---
madr: 4
id: '0415'
estado: 'aceptado'
fecha: 2026-10-29
cinturon: 'politica'
indice: 'ITCP'
indicadores: [ratio_dnu]
parametros: ['BANDAS_ITCP']
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'scripts/itcp.py', 'scripts/procedencia_anclas.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_ratio_dnu_tratados.py', 'tests/test_politica_ratio_dnu.py', 'tests/test_descargar_series_ratio_dnu.py', 'tests/test_itcp.py']
relacionado: ['0058', '0059', '0241', '0410']
ambito: 'Cinturón político · ITCP · dimensión Poder legislativo · qué leyes cuentan en el denominador del cociente de decretos de necesidad y urgencia, cómo se encuentran todos esos decretos y con qué referencia se calibran las bandas'
origen: 'Decisión de Juan del 29-oct-2026 sobre la investigación del indicador «Decretos de necesidad y urgencia por ley» contra el informe de la Asociación Civil por la Igualdad y la Justicia (ACIJ).'
---

# ADR-0415 — Decretos de necesidad y urgencia por ley: sin tratados, con todos los decretos y bandas recalibradas

## Contexto y planteo del problema

El cociente cuenta los decretos de necesidad y urgencia publicados en el Boletín Oficial
por cada ley publicada, en una ventana móvil de 365 días ([[0058-ratio-dnu-ventana-movil-12m]],
[[0241-un-dnu-es-un-tipo-juridico-no-una-frase]], [[0410-el-tipo-del-decreto-sale-del-original-y-la-insistencia-de-la-segunda-camara]]).
Sus bandas están ancladas desde [[0059-ratio-dnu-no-recalibrar-anclas]] al relevamiento de
ACIJ (2011-2024, cuatro presidencias): 344 decretos de necesidad y urgencia sobre 1.058
leyes, ≈ 0,325, «cada 3 leyes hay 1 DNU».

La revisión del 29-oct-2026 encontró tres problemas.

**1. Más de la mitad de las leyes de la ventana aprueban tratados.** De las 31 leyes
publicadas entre el 30-oct-2025 y el 29-oct-2026, 17 aprueban tratados, convenios o
protocolos con otros países u organismos internacionales (extradiciones, seguridad
social, doble imposición, el acuerdo Mercosur–Unión Europea). Un tratado sólo lo aprueba
el Congreso (arts. 75 inc. 22 y 99 inc. 11 de la Constitución): no existe la alternativa
del decreto, así que esas leyes no informan nada sobre si el Ejecutivo legisla por
decreto en lugar de por ley, y sí inflan el denominador cada vez que llega al Congreso
una tanda de tratados.

**2. La búsqueda de texto pierde decretos de necesidad y urgencia.** El filtro previo
(la frase «necesidad y urgencia») no trae los que no la dicen. Listando todos los
decretos 2011-2026 semestre por semestre y cruzando el rótulo `Decreto DNU` de la grilla
con la regla de [[0410-el-tipo-del-decreto-sale-del-original-y-la-insistencia-de-la-segunda-camara]],
aparecen 26 que el filtro no encontraba entre 2011 y 2019 (el 609/2019 del cepo, el
1043/2018 de la asignación no remunerativa, cinco modificaciones de la Ley de Ministerios,
fondos fiduciarios de 2014-2015) y ninguno desde septiembre de 2019. No mueve la ventana
de hoy, pero sí cualquier referencia histórica: la de las bandas se calcula sobre
2011-2023.

**3. La referencia de las bandas no se mide igual que el indicador.** ACIJ, en su informe
de septiembre de 2025 (datos a diciembre de 2024):

- denominador: «En el mismo período se sancionaron 1.058 leyes […]. En el cómputo de
  leyes sancionadas se encuentran contempladas las 8 leyes que fueron vetadas de forma
  total por el Poder Ejecutivo» (nota 33; fuente: Secretaría Parlamentaria de Diputados).
  Son leyes **sancionadas**, todas, tratados incluidos;
- numerador: «un análisis pormenorizado de los 344 decretos emitidos» entre el
  10-dic-2011 y el 9-dic-2024: **todos** los decretos de necesidad y urgencia, también los
  de rutina (tropas, viajes del Presidente);
- **no** cuenta decretos delegados (el informe trata sólo los del art. 99 inc. 3).

El indicador cuenta publicaciones en los dos lados. Si además deja de contar tratados, la
referencia tiene que medirse con la misma regla, o las bandas comparan un cociente con
otro.

## Factores de decisión

- El denominador debe contar sólo leyes que podrían haberse reemplazado por un decreto.
- Card, serie y referencia de las bandas, con la misma regla y la misma función.
- Ninguna clasificación cae en silencio: lo que no se puede leer o decidir corta el
  conteo, como en [[0410-el-tipo-del-decreto-sale-del-original-y-la-insistencia-de-la-segunda-camara]].
- Las bandas siguen ancladas a una referencia externa anterior al mandato, escaladas
  —no recalibradas al rango observado ([[0059-ratio-dnu-no-recalibrar-anclas]])—.

## Opciones consideradas

Resultados de la investigación (InfoLeg, por publicación; referencia 2011-2023 y
2011-2024; «hoy» = ventana al 29-oct-2026; puntaje con las bandas vigentes y con los cortes
escalados por referencia / 0,325). DNU completos (filtro de texto + rotulados):

| Versión | Ref. 2011-2023 | Ref. 2011-2024 | Hoy | Puntaje actual | Puntaje escalado (2011-2023) |
|---|---|---|---|---|---|
| A. Como hoy | 313/1.079 = 0,290 | 360/1.121 = 0,321 | 37/32 = 1,156 | 57,1 | 51,7 |
| B. Sin tratados | 313/872 = 0,359 | 360/883 = 0,408 | 37/14 = 2,643 | 10,0 | 10,0 |
| C. Sin decretos de rutina | 312/1.079 = 0,289 | 356/1.121 = 0,318 | 29/32 = 0,906 | 66,9 | 62,3 |
| D. Sin tratados ni rutina | 312/872 = 0,358 | 356/883 = 0,403 | 29/14 = 2,071 | 10,0 | 18,8 |
| E. Como hoy + delegados | 382/1.079 = 0,354 | 451/1.121 = 0,402 | 45/32 = 1,406 | 47,5 | 51,9 |
| F. Sin tratados + delegados | 382/872 = 0,438 | 451/883 = 0,511 | 45/14 = 3,214 | 10,0 | 10,0 |

La investigación contaba la conciliación con Bainbridge Ltd. (27.818) como tratado, no
contaba la 27.531 ni la 27.699 y tomaba 32 leyes de hoy (el total declarado, ver
«Registros invisibles»). Con la regla decidida el denominador de hoy queda igual (31
listadas − 17 tratados = 14) y la referencia queda en 313/872 (ver Decisión: se mueven cuatro leyes en sentidos opuestos).

- **B (elegida): sin tratados, todos los decretos de necesidad y urgencia, sin delegados.**
- A: dejar el cociente como está.
- C/D: sacar además los decretos de rutina.
- E/F: sumar los decretos delegados.

## Decisión

**Denominador.** Dejan de contar las leyes que aprueban o ratifican un tratado, convenio,
acuerdo, protocolo o enmienda internacional (con otro Estado o con un organismo
internacional). Una sola función decide (`politica._es_ley_de_tratado`, sobre
`clasificar_ley_tratado`), y la usan la card y la serie:

- regla de texto sobre el sumario de InfoLeg: verbo de aprobación (o ratificación,
  adhesión, denuncia) de un instrumento + una contraparte extranjera o internacional (o una materia que sólo se
  acuerda con otro Estado: extradición, doble imposición, canje de notas…) ⇒ tratado;
  Nación con provincias, con la Ciudad, pactos federales ⇒ no;
- no son tratados aunque la contraparte sea extranjera: los acuerdos de conciliación con
  empresas (27.818, Bainbridge Ltd.), las operaciones de crédito público del art. 75 inc. 7
  (27.668, el programa con el Fondo Monetario Internacional) y el convenio con Repsol por
  la expropiación de YPF (26.932) — son operaciones financieras o administrativas, no
  instrumentos internacionales a ratificar;
- sí son tratados: 27.531 (protocolo de la Unión Postal Universal) y 27.699 (protocolo del
  convenio de datos personales del Consejo de Europa);
- esos cinco quedan fijados por número en `_LEYES_TRATADO_DECIDIDAS`;
- si el sumario viene recortado («...») y parece un instrumento, se lee el resumen
  completo de la ficha `verNorma.do`; si no se puede leer, `RuntimeError`; si con el
  resumen completo sigue sin saberse con quién es, `ValueError` con el número de ley. En los
  dos casos el conteo se corta y la card queda en cache marcada desactualizada.

**Numerador.** Candidatos = búsqueda «necesidad y urgencia» ∪ decretos rotulados
`Decreto DNU` en el listado completo de decretos (mes a mes); cada uno se decide por el
identificador del original como en [[0410-el-tipo-del-decreto-sale-del-original-y-la-insistencia-de-la-segunda-camara]].
Los decretos con número anterior a 1994 no cuentan: son decretos secretos de la dictadura
publicados décadas después con rótulo DNU (179/1979, 33/1980), anteriores a la figura del
art. 99 inc. 3. Los decretos de rutina **se siguen contando** (hasta 2023 esas
autorizaciones las daba una ley); los decretos delegados **no** se suman (los autoriza el
Congreso de antemano).

**Registros invisibles.** InfoLeg declara a veces un registro que no muestra en ninguna
fila (sept-2026: declara 8 leyes y lista 7, con todos los números 27.798 a 27.828
presentes; mayo-2026: 101 decretos declarados, 100 listados). Si se recorrieron todas las
páginas declaradas y faltan una o dos filas, se cuentan las listadas con un aviso en el
log; si faltan páginas, se corta. Por eso la ventana de hoy cuenta 31 leyes publicadas y
no las 32 que declaraba el total del buscador.

**Una sola bajada.** `ratio_dnu_insumos` baja leyes (marcadas) y decretos de un tramo, y
`ratio_dnu_contar` cuenta cualquier ventana dentro de él sin red. La card la pide para su
ventana; la serie, una vez para todo el tramo (ene-2023 a hoy). Presupuesto de la serie:
900 s.

**Bandas.** Se escalan los cortes de [[0059-ratio-dnu-no-recalibrar-anclas]] por
referencia nueva / 0,325, con referencia nueva = cociente 2011-2023 (antes del mandato)
con la regla de este ADR, por fecha de publicación en InfoLeg, calculado con el código
nuevo (un año por vez, sumado; `ratio_dnu_insumos` + `ratio_dnu_contar`):

| Año | DNU | Leyes publicadas | De tratados | Leyes que cuentan |
|---|---|---|---|---|
| 2011 | 10 | 74 | 18 | 56 |
| 2012 | 11 | 75 | 24 | 51 |
| 2013 | 12 | 120 | 21 | 99 |
| 2014 | 12 | 119 | 49 | 70 |
| 2015 | 17 | 198 | 38 | 160 |
| 2016 | 13 | 102 | 5 | 97 |
| 2017 | 17 | 82 | 17 | 65 |
| 2018 | 12 | 53 | 8 | 45 |
| 2019 | 28 | 59 | 8 | 51 |
| 2020 | 77 | 65 | 10 | 55 |
| 2021 | 41 | 61 | 4 | 57 |
| 2022 | 28 | 37 | 3 | 34 |
| 2023 | 35 | 34 | 2 | 32 |
| **2011-2023** | **313** | **1.079** | **207** | **872** |

Referencia nueva = 313 / 872 = 0,3589. Factor = 0,3589 / (344 / 1.058 = 0,3251) = 1,104.
Cortes 0,3 · 0,7 · 1,2 · 2,0 × 1,104 = 0,331 · 0,773 · 1,325 · 2,208, **redondeados a
centésimos: 0,33 · 0,77 · 1,32 · 2,21** (puntajes 100 · 85 · 65 · 40 · 10, sin cambio). Se
redondea a centésimos porque es la precisión de la propia referencia; redondear a 0,05
(0,35 · 0,75 · 1,3 · 2,2) habría corrido el corte del máximo un 6 % y achicado el segundo
tramo, rompiendo la proporción entre tramos que es lo único que se hereda de ACIJ. Se
usa 2011-2023 y no 2011-2024 para que la referencia sea anterior al mandato medido.
`procedencia_anclas.py` sigue clasificándola como externa.

### Consecuencias

- Ventana del 29-oct-2026 (consulta en vivo con el código nuevo, sin escribir output):
  **37 DNU / 14 leyes = 2,643** (31 leyes listadas, 17 de tratados: 27.800, 27.803,
  27.806 a 27.817, 27.819, 27.824, 27.825). Antes: 37 / 32 = 1,156.
- El puntaje del componente pasa de **57,1 a 10** (piso: 2,64 > 2,21). Con su peso
  efectivo en el índice político (≈ 0,052), el índice baja unos 2,4 puntos con el resto
  de los datos de la última corrida (de 70,0 a ≈ 67,6) y la dimensión de poder legislativo
  unos 11 (de 72,1 a ≈ 61). Se ve con la próxima corrida; los meses ya publicados se
  releen con el método vigente.
- El valor queda muy sensible al número de leyes que no son tratados: con 14, una ley de
  más o de menos lo mueve un 7 %.
- La card lista todos los decretos de la ventana mes a mes (unos 90 s en total) y la serie
  todo el tramo desde enero de 2023 (presupuesto de 900 s). La card publica además
  `leyes_publicadas`, `tratados_excluidos` e `inventario_tratados`.
- Ninguna ley 2011-2026 queda sin decidir con la regla (barrido de las 1.163 publicadas
  del 29-oct-2026; la 27.028 se resolvió sumando a la regla la cita de la ley de
  publicación de tratados, 24.080).
- Ajustes tras la revisión de Codex del mismo día: (a) **el verbo es obligatorio**: un
  encabezado de instrumento sin aprobación, ratificación, adhesión o denuncia no alcanza, y
  otorgar jerarquía constitucional a una convención ya aprobada no es aprobar un tratado
  (27.700 y 27.044 cuentan como leyes; también la 27.778, que sólo corrige el nombre de un
  convenio de La Haya ya aprobado, y la 26.745, que aprueba un aumento del aporte al capital
  del Banco Interamericano de Desarrollo —una operación financiera, como la del FMI—);
  (b) **un sumario recortado que menciona un instrumento en cualquier orden se lee
  completo**: la 26.986 (modificaciones al convenio constitutivo de FONPLATA) pasa a
  tratado. Neto en 2011-2023: 207 tratados en vez de 208; el corte del tramo moderado pasa
  de 1,33 a 1,32.
- **Marca de método.** La card fresca lleva `"metodo": "0415"`. Un valor guardado sin esa
  marca se calculó con los tratados en el denominador: no puntúa (`_valor_itcp` devuelve
  None y el índice renormaliza) y, si la primera corrida no logra un cálculo nuevo, no se
  arrastra (`_arrastre` devuelve None): el indicador queda sin dato —sin tarjeta, fuera del
  índice— como uno que nunca se pudo calcular, en vez de puntuar 1,156 con las bandas
  nuevas (65 en lugar de 10). Una tarjeta con valor que no puntúa rompería la auditoría
  de coherencia (tarjetas = componentes). Hasta la primera corrida con el código nuevo, las
  pruebas que leen el snapshot publicado (`test_publicar_semaforo`, `test_politica_sin_universo`)
  ven el valor viejo sin marca y fallan; se resuelven con esa corrida.

### Confirmación

`tests/test_ratio_dnu_tratados.py` fija ejemplos reales de cada clase (tratados
bilaterales, del Mercosur, con un organismo internacional, de la Organización
Internacional del Trabajo; convenios con provincias y con la Ciudad; los cinco dudosos
decididos), la lectura de la ficha cuando el sumario viene recortado, el corte cuando no
se puede leer o decidir, la unión de candidatos de decretos (y la exclusión de los
anteriores a 1994), el listado mes a mes, la tolerancia a registros invisibles y que la
serie baja una vez y termina en el valor de la card. `tests/test_itcp.py` fija los cortes.

## Pros y contras de las opciones

- B: el denominador mide lo que el indicador dice; el valor queda muy sensible a cuántas
  leyes que no son tratados publica el Congreso (con 14, una ley mueve el cociente un 7 %).
- A: no toca nada, pero el valor sube y baja con la llegada de tandas de tratados.
- C/D: miden mejor «decretos de contenido legislativo», pero sacan justamente las
  autorizaciones que hasta 2023 eran ley.
- E/F: los delegados ejecutan una delegación del Congreso; sumarlos mezcla dos figuras
  que la Constitución separa y que ACIJ tampoco suma.

## Más información

- Investigación del 29-oct-2026 (scripts y datos fuera del repo): listado de todos los
  decretos 2011-2026, cotejo contra la planilla de ACIJ y tabla de versiones.
- ACIJ, «De la excepción a la regla. Un análisis de los decretos de necesidad y urgencia
  dictados desde 2011 hasta 2024», septiembre de 2025 (https://acij.org.ar/?p=71606).
