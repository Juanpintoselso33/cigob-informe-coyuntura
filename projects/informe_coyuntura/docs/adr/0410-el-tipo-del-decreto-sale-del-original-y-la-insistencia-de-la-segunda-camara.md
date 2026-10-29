---
madr: 4
id: '0410'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [ratio_dnu, insistencias_vetos, rechazos_decretos]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'data/politica/derrotas_legislativas_eventos.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_politica_ratio_dnu.py', 'tests/test_insistencias_y_rechazos.py']
relacionado: ['0241', '0307', '0377', '0415']
ambito: 'Cinturón político · ITCP · dimensión Poder legislativo · cómo se tipifica un decreto de necesidad y urgencia y cómo se fecha una insistencia'
origen: 'Revisión pedida por Juan el 28-oct-2026 de «Decretos de necesidad y urgencia por ley», «Vetos que el Congreso dio vuelta» y «Decretos derogados por el Congreso» (hoy 1,13 / 0 / 0).'
---

# ADR-0410 — El tipo del decreto sale del original, y la insistencia se fecha en la segunda cámara

## Contexto y planteo del problema

Se revisaron los tres indicadores contra las fuentes oficiales el 28-oct-2026.

**Decretos de necesidad y urgencia por ley.** [[0241-un-dnu-es-un-tipo-juridico-no-una-frase]]
decidió contar por el rótulo de la grilla de InfoLeg (`Decreto DNU 771 / 2026`) y usar la
frase «necesidad y urgencia» sólo como filtro previo. [[0307-ratio-dnu-ventana-inclusiva]]
ya había encontrado que el rótulo se equivoca en un sentido: «Decreto DNU 44/2026» es,
en el original, `DECTO-2026-44-APN-PTE` (un decreto común del Código Aduanero). Al
abrir el texto original de los 174 decretos que trae el filtro desde el 10-dic-2023
aparecen errores en el otro sentido, que sí cambian el conteo: InfoLeg rotula como
decretos comunes a tres decretos firmados como de necesidad y urgencia.

| Norma | Publicación | Rótulo de InfoLeg | Identificador del original |
|---|---|---|---|
| 493/2025 (marco regulatorio de agua potable) | 22-jul-2025 | Decreto | `DNU-2025-493-APN-PTE` |
| 521/2025 (ejercicios militares combinados) | 31-jul-2025 | Decreto | `DNU-2025-521-APN-PTE` |
| 867/2026 (modificación del presupuesto) | 4-sep-2026 | Decreto | `DNU-2026-867-APN-PTE` |

Texto original: `https://servicios.infoleg.gob.ar/infolegInternet/anexos/425000-429999/429670/norma.htm`
(867/2026) y los equivalentes de los ids 415379 y 415709.

El filtro textual, en cambio, está completo: de los 458 decretos de la ventana que citan
el «inciso 3» del artículo 99, los 412 que no dicen «necesidad y urgencia» se abrieron
uno por uno y ninguno es de necesidad y urgencia. Con el conteo correcto la ventana del
28-oct-2026 tiene **37** decretos de necesidad y urgencia (no 36) sobre 32 leyes:
**1,156** en vez de 1,125.

**Vetos insistidos.** El conteo es correcto: tres insistencias consumadas en el mandato
(discapacidad, 4-sep-2025; financiamiento universitario y Garrahan, 2-oct-2025), las tres
fuera de la ventana nov-2025→oct-2026. InfoLeg no tiene decretos de veto desde el 652/2025
(12-sep-2025) ni leyes promulgadas por insistencia después de las 27.795 y 27.796
(decretos 759 y 760/2025, 21-oct-2025). Las insistencias del Senado sobre los vetos de
Bahía Blanca (27.790) y de los aportes del Tesoro (27.794) siguen sin la de Diputados; la
ley de combustibles de los gobernadores nunca se sancionó, así que no hubo veto. Pero el
código no fechaba como dice [[0377-vetos-insistidos-y-decretos-derogados-reemplazan-quorum-y-desafios]]:
la detección automática anota la **publicación** de la ley, que llega semanas después del
voto (la 27.795 se insistió el 2-oct y se publicó el 21-oct). Los tres casos actuales
estaban fechados a mano en el voto; uno nuevo habría quedado fechado en la publicación.

**Decretos derogados.** El conteo es correcto: seis en el mandato (656/2024 el
12-sep-2024; 340, 345, 351, 461 y 462/2025 el 21-ago-2025). Las resoluciones de las dos
cámaras que rechazan decretos en los términos de la ley 26.122 publicadas desde agosto de
2025 son sólo las diez del 25-ago-2025 (resoluciones 39, 43, 44, 94 y 95/2025 de Diputados;
53 a 57/2025 del Senado). El decreto 70/2023 lo rechazó sólo el Senado y sigue vigente.

## Factores de decisión

- El tipo jurídico es el del acto firmado, no el del catálogo (la regla de [[0241-un-dnu-es-un-tipo-juridico-no-una-frase]],
  aplicada a la fuente primaria que ya usó [[0307-ratio-dnu-ventana-inclusiva]]).
- Que el código feche como dice [[0377-vetos-insistidos-y-decretos-derogados-reemplazan-quorum-y-desafios]].
- No tocar escalas ni definiciones: eso es método y queda como propuesta.

## Opciones consideradas

- **Leer el identificador del texto original de cada candidato (elegida).**
- Seguir con el rótulo de la grilla y corregir a mano los casos conocidos.

## Decisión

- `ratio_dnu`: cada decreto del filtro previo se clasifica por el identificador que
  encabeza su texto original: `DNU-` (o `DECNU-` hasta 2023) cuenta; `DECTO-`/`DCTO-` no.
  Se exige que el identificador tenga el número y el año de la propia norma. Si el texto
  se lee y no trae identificador, decide el rótulo de InfoLeg; si no se puede bajar (tras
  un reintento), el conteo se corta y la card queda en cache marcada desactualizada. El tipo leído se
  memoriza por norma dentro de la corrida, así que la serie abre cada texto una sola vez.
- `insistencias_vetos`: el evento se fecha en el voto de insistencia de la segunda cámara
  cuando los dos votos están en el registro; si falta alguno, en la publicación, hasta que
  se registre.
- `rechazos_decretos`: sin cambio de cálculo. En el registro los nombres de los decretos
  derogados se escriben sin siglas, porque viajan al texto de la tarjeta.
- Textos de las tres tarjetas sin siglas; la ficha del cociente deja de citar cifras de un
  relevamiento de julio que además mezclaba decretos delegados con los de necesidad y
  urgencia («de los ocho votados, seis cayeron»: dos eran de necesidad y urgencia, cuatro
  delegados).

### Consecuencias

- `ratio_dnu` pasa de 1,125 a 1,156 con la ventana del 28-oct-2026 (puntaje de banda de
  58,3 a 57,1). En la serie suman dos decretos los cierres de julio de 2025 a junio de 2026
  y uno los de septiembre y octubre de 2026. Se ve con la próxima corrida.
- La corrida abre unos 50 textos para la tarjeta y unos 200 para la serie (probado el
  28-oct-2026: 206 textos, 3 minutos y medio, con pausa entre pedidos). Sólo el veto
  254/2024 no trae identificador y queda por el rótulo, que es correcto.
- Serie reconstruida en memoria con el código nuevo: jul-2025 0,953 → 1,000; oct-2025
  3,273 → 3,455; jun-2026 1,450 → 1,550; sep-2026 1,062 → 1,094; oct-2026 1,125 → 1,156;
  jul y ago-2026 sin cambio.
- Vetos y decretos: ningún conteo publicado cambia; las dos ventanas dan cero de verdad.

### Confirmación

`tests/test_politica_ratio_dnu.py` fija los casos reales (867 y 521 cuentan aunque el
rótulo diga decreto común; 44/2026 no cuenta aunque diga DNU; `DECNU`/`DCTO` de 2023; un
identificador de otra norma no decide; texto sin identificador decide el rótulo; un original que no se baja corta el conteo; cada texto se pide una
vez). `tests/test_insistencias_y_rechazos.py` fija la fecha de la segunda cámara y los
casos verificados del registro.

## Pros y contras de las opciones

- Identificador del original: es el tipo con el que se firmó y se corrige solo; cuesta
  unos pedidos más por corrida y depende de que InfoLeg siga publicando el texto.
- Corrección a mano: no cuesta pedidos, pero el próximo error de catálogo pasa sin aviso.

## Más información

Propuestas de método que este ADR no toma (decisión de Juan y Luis): ver el reporte de la
revisión del 28-oct-2026 — si los decretos que autorizan la salida o el ingreso de tropas
y los viajes del Presidente deben contar como «gobernar por decreto».
