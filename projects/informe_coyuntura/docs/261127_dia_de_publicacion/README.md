# Día de publicación del informe mensual (27-nov-2026)

Pedido de Luis (24 y 25-nov, y otra vez el 27-nov): fijar el día de publicación de cada mes de modo que el
atraso de los indicadores sea siempre el mismo. Juan sumó dos criterios: el día con más datos entregados (lo
principal) y el día que conviene por redes y prensa. Sin decidir todavía.

## Recomendación

Publicar el mes M el **miércoles que cae entre el 21 y el 27 del mes siguiente, a las 9 h**. Si es feriado, el
jueves. Para noviembre de 2026 sería el miércoles 23-dic (en plena semana de fiestas). Las alternativas son el
martes 22-dic o el miércoles 16-dic; esta última queda antes de la meseta y sale sin el resultado fiscal ni el
comercio exterior. Diciembre se define con Luis.

## Datos: cuándo llega cada cosa

Cruce entre dos fechas:

- **Llegada al Monitor:** los 482 snapshots del sitio guardados en git (29-may a 27-nov-2026).
- **Publicación de la fuente:**
  - INDEC: calendario oficial de jul-2025 a dic-2026.
  - Economía: comunicados del resultado fiscal.
  - BCRA: calendario de informes.

Peso de los indicadores mensuales con dato del mes M, según el día D del mes siguiente. El escenario «fuente»
supone que el dato entra la noche en que la fuente lo publica.

| D | Fuente (peor–mejor de 16 meses) | Observado en el Monitor (jul–oct 2026) |
|---|---|---|
| 10 | 10 % – 10 % | 9 % – 15 % |
| 15 | 37 % – 37 % | 14 % – 38 % |
| 18 | 41 % – 61 % | 16 % – 41 % |
| **21 a 25** | **61 % – 61 %** | 30 % – 61 % |
| 31 | 63 % – 70 % | 38 % – 71 % |
| 40 (día 9 del mes subsiguiente) | 71 % – 78 % | 39 % – 76 % |

Los porcentajes son del 49 % del peso que depende del día. El otro 51 % no cambia con la fecha: indicadores
continuos (votaciones, Boletín Oficial, cepo), del mismo mes (ICG, tarifas) o trimestrales y anuales.

Del 21 al 25 la cobertura no se mueve en ningún mes: ya publicaron todas estas fuentes.

| Fuente | Día de publicación |
|---|---|
| IPC | 10 a 14 |
| Pobreza nowcast de la Di Tella | 15 |
| Resultado fiscal | 16 a 18 |
| Comercio exterior | 17 a 20 |
| REM, recaudación, tipo de cambio real y patentamientos | antes del 10 |

Lo siguiente llega a partir del día 26:

| Indicadores | Día de llegada |
|---|---|
| Dotación del Estado y dinero | 26 a 31 |
| IPI e indicador de la construcción | 34 a 40 |
| Brecha salario–canasta | 46 |
| Supermercados, EMAE y mora | 48 a 57 |
| Jornadas no trabajadas | 59 |

## Redes y prensa

La búsqueda en internet del 27-nov no encontró estudios argentinos ni de canales de WhatsApp: todo es global.

- **Redes:** de martes a jueves son los mejores días; el lunes y el fin de semana, los peores (Sprout Social
  nov-2025 a feb-2026; Buffer 2026).
- **Prensa:** el 78 % de los periodistas quiere el material antes del mediodía (Muck Rack, State of Journalism
  2026).
- **Días a evitar:**
  - el del IPC (martes o jueves entre el 10 y el 15, a las 16 h);
  - el último lunes del mes, cuando sale el ICG de la Di Tella.
- **Entre el 21 y el 27:** no choca con ninguno de los dos. El EMAE suele salir entre el 20 y el 24.

## Por qué hoy el Monitor no llega a lo que dan las fuentes

Estos son problemas nuestros, no de las fuentes.

1. **Fiscal (resultado primario y gasto de funcionamiento, 5 % del peso).** Se lee de la API de datos.gob.ar
   (serie `452.3_RESULTADO_RIO_0_M_18_54`), que se atrasa semanas respecto de Economía:

   | Mes | Lo publicó Economía | Entró al Monitor |
   |---|---|---|
   | Julio | 18-ago | 3-sep |
   | Agosto | 18-sep | 23-sep |
   | Septiembre | 16-oct | 15-nov |
   | Octubre | 16-nov | todavía no entró; la API sigue en septiembre al 27-nov |

   Hay que leerlo directo de Economía.
2. **Demoras puntuales de colectores:**

   | Dato | Días de atraso |
   |---|---|
   | IPC de septiembre (INDEC 13-oct, entró 20-oct) | 7 |
   | IPC de alimentos de septiembre | 21 |
   | Comercio exterior de julio (INDEC 20-ago, entró 8-sep) | 19 |
   | EMAE de agosto (INDEC 21-oct, entró 3-nov) | 13 |
   | Pobreza nowcast de septiembre (cambio de formato del PDF) | 28 |

   Parte de esto puede ser días sin corrida: faltan snapshots en 49 días de los 179.
3. **El informe publicado se sigue llenando después.** `scripts/archivo.py` (`_cortar`) corta las series por
   período (`fecha[:7] <= mes`), no por fecha de llegada. Así, el mes publicado se rearma en cada push con los
   datos que llegaron después. Para que el atraso sea siempre el mismo hay que congelar los datos el día de la
   publicación.

## Cálculo

En `calculo/`:

| Archivo | Qué hace |
|---|---|
| `g1_git.py` | Extrae los snapshots de git |
| `g2_llegadas.py` | Calcula la llegada de cada período |
| `g4_indec.py` | Lee el calendario del INDEC |
| `g5_modelo.py` | Modela la curva y su tabla |

Fechas de los comunicados fiscales: Ámbito y MDZ (16-oct), Continental (18-ago), iProfesional (18-sep) y
Prensa Mercosur (17-nov). El calendario del BCRA está en bcra.gob.ar/calendario-de-informes. Los calendarios del
INDEC, en indec.gob.ar/ftp/cuadros/publicaciones/calendario_*.pdf.

Límites:

- Las fuentes que no son del INDEC ni fiscales se tomaron con su atraso típico (BCRA, Trabajo, SAGyP, ACLED,
  la Di Tella). No se cotejaron mes a mes.
- La brecha salario–canasta no se cotejó con la fecha de la Secretaría de Trabajo.
