# Pendientes del Monitor

Armado el 26-oct-2026 con lo que pidió Juan y los documentos de Luis y Marcos por
WhatsApp hasta el 26-oct a las 16:54 (originales en `docs/pedidos/originales/`, texto en
`docs/pedidos/texto/`). Reordenado el 29-oct-2026: arriba lo que falta; abajo, condensado,
lo hecho. **No se arranca nada de acá sin que Juan lo pida.**

Marcas: **[J]** pedido de Juan · **[L]** documento de Luis · **[M]** documento de Marcos ·
**decidido** = Juan ya dijo que sí · **decidir** = falta su decisión · **sin verificar** = no
se pudo confirmar contra los ADR ni el código.

Fechas acordadas (reunión del Votómetro, 21-oct): Monitor general a principios de
noviembre; Votómetro a fines de noviembre.

Las decisiones de método de la auditoría del 28-oct están en el documento «Decisiones de
método del Monitor — auditoría del 28-oct» (https://claude.ai/artifact/DrXmpa1BhLJH8niWRmzeoU).

---

## 1. Abierto: decide Juan

**Revisión de Luis (3-nov, Word «261103 Pendientes revisada por Luis», por WhatsApp):**
«amarillos cambiar, verdes la próxima». Los números entre paréntesis son los de esta lista.

- **Cambiar ahora (amarillo):**
  - DNU por ley (7) pasa a poder legislativo.
  - Cobertura judicial (8) pasa a legislativo, y legislativo suma el 16 % entero de la
    dimensión que desaparece.
  - Producción legislativa (1): sacarla, sin alternativa.
  - Votos ajenos (5 y 6): sólo Diputados, con la escala 129/119/109. **En un mes sin votación
    queda el puntaje de la última votación.**
  - Transferencias no automáticas (2): revisar el dato y su historia previa.
  - «Sector empresarial» (9).
  - RIGI (18): cortes contra una meta esperada de inversiones.
  - IVA + cheque (3) en cuentas fiscales: el peso y la escala con historia previa «lo calcula la IA».
  - Ítem 10: Luis lo rotuló **«Alquileres»**, no el gráfico de impacto social. Pide pasarlo a
    base oct-dic 2023 y revisar el empalme INDEC / Di Tella.
  - Pobreza (11): verde con 15 % o menos, tomando a Uruguay como aspiración. Siguen faltando
    los otros cortes.
  - kg en el hover de carne (12).
  - Mora (15) y carga de la deuda (16).
  - Victimización (17): está en amarillo, pero el texto dice «para la próxima». Hay que
    preguntárselo a Luis.
- **Para la próxima (verde):**
  - Los dos de carne puntuando igual (13).
  - Presión de precios (14): falta salud, y la ponderación alimentos / servicios públicos
    escribió «para la próxima publicación».
- **Sin cambios:** alineamiento por provincia (4) «se deja como está». No se suma Diputados.

1. **Producción legislativa: puede salir; buscar una alternativa** (Juan, 3-nov). Hoy: 31
   leyes sancionadas en 12 meses, 45,8 puntos, amarillo, 3,8 % del peso. Además cuenta leyes
   sancionadas mientras decretos por ley cuenta leyes publicadas (lo marcó Luis el 26-oct).
   Estado: relevar alternativas antes de sacarla.
2. **Transferencias no automáticas: verificar el dato** (Juan, 3-nov: «no me convence
   mucho»). Hoy: −82,1 % real frente a 2023, 10 puntos, rojo, 8,2 % del peso (ADR-0378 y
   0397). Revisar que esté bien construido y que correlacione con la historia previa.
3. **Recaudación de IVA y cheque vuelve, en cuentas fiscales** (Juan, 3-nov: «sumémoslo de
   vuelta»; esta vez en la dimensión cuentas fiscales, no en actividad). Salió el 26-oct
   (ADR-0368) a pedido de Luis por repetir al EMAE (r = 0,84) dentro de actividad. Se sigue
   calculando oculta (`actividad_tributaria`), así que el dato está. Para hacerlo: ADR nuevo que
   reemplace a 0368, peso dentro de cuentas fiscales, y escala con cortes de la historia previa
   como el resto (ADR-0404; la de 0329 se había calibrado sobre 2017-2026, mandato incluido).
4. **Alineamiento por provincia: sumar Diputados** (Juan, 3-nov). Hoy
   `alineamiento_senadores_prov` mira sólo el Senado: 61,6 % de los votos de senadores que no
   son de La Libertad Avanza alineados con ella, 80 puntos, 6,1 % del peso (alianzas
   territoriales; ADR-0400 y 0402). Sumar los diputados por provincia.
5. **Votos ajenos al aprobar leyes: promedio del mes, no de 12 meses** (Juan, 3-nov). Hoy
   `votos_sobre_bancas` promedia 12 meses: 22,3 % de las bancas (Diputados 18,5 % con 12
   votaciones, Senado 29,3 % con 12), 8,1 % del peso (cohesión; ADR-0376). Con cerca de una
   votación de ley por mes y cámara, hay que definir qué muestra un mes sin votaciones (receso
   de enero y febrero incluido).
6. **Votos ajenos: sólo Diputados, sin Senado, y revisar los límites** (Juan, 3-nov). Si la
   ley se aprueba, siempre hace falta un mínimo de votos ajenos, y eso da verde casi seguro.
   Con mayoría absoluta, el piso en el Senado es (37 − 21 de LLA) / 72 = 22,2 %, por encima del
   corte del verde (18 %): el Senado da verde por construcción. En Diputados el piso es
   (129 − 94) / 257 = 13,6 %. El origen del Ejecutivo sí está medido (ADR-0376): en el Senado
   por el expediente (`PE`/`JGM`) y en Diputados cruzando el Orden del Día con el dictamen y el
   catálogo de proyectos del Ejecutivo; hoy quedan 3 votaciones con origen sin confirmar.
   **Escala propuesta por Juan (3-nov):** medir la cantidad de diputados que votaron a favor
   de la ley (no los votos ajenos como % de la cámara). Más de 129 → verde · 119 a 129 →
   amarillo · 109 a 119 → naranja · menos de 109 → rojo. Falta definir de qué lado cae el
   borde exacto (129, 119, 109).
7. **Decretos de necesidad y urgencia por ley: tiene que ir en poder legislativo** (Juan,
   3-nov). En el cálculo (`informe.json`) `ratio_dnu` ya figura en la dimensión
   `poder_legislativo`; revisar dónde aparece en otro lado (página, ficha, agrupación de
   tarjetas) y moverlo ahí.
   **Causa encontrada (3-nov): es un error del informe mensual, no del diario.** Desde
   ADR-0415, `ratio_dnu` sólo puntúa si trae la marca `metodo` del cálculo nuevo
   (`politica._valor_itcp`). Al rearmar el mes, `archivo.cortar_indicadores` copia sólo
   `CAMPOS_CARD` (valor, unidad, fuente, fecha, dimensión…) y la marca se pierde. Resultado en
   informe.cigob.org (octubre): la tarjeta sale con 2,643, pero queda fuera del índice político
   (el índice se renormaliza sin ella) y por eso aparece sin dimensión. El diario está bien.
   Arreglo probable: sumar `metodo` a `CAMPOS_CARD` en `scripts/archivo.py`, con un test, y
   rearmar la rama mensual. El índice político de octubre publicado va a cambiar.
8. **La dimensión poder judicial se va; cobertura de cargos judiciales pasa a poder
   legislativo** (Juan, 3-nov). Hoy poder judicial tiene sólo `cobertura_judicial` (73,61 %,
   61,5 puntos) y pesa 16,13 % del índice político (ADR-0374). Al moverla, definir el peso de
   la cobertura dentro de legislativo y qué pasa con el 16 % de la dimensión que desaparece
   (repartirlo entre las otras cinco o sumarlo a legislativo). ADR nuevo que reemplace a 0374.
   **Juan (3-nov): darle más peso a la dimensión poder legislativo** (hoy 22,58 %). Falta
   definir cuánto. Opción que planteó: que el 16,13 % de poder judicial pase entero a
   legislativo (22,58 + 16,13 = 38,71 %, las otras cuatro dimensiones sin cambios).
9. **La dimensión «Sector privado» pasa a llamarse «Sector empresarial»** (Juan, 3-nov). Sólo
    el nombre: industria, comercio, campo y construcción siguen igual. Cambiar en el sitio,
    fichas, textos y manuales.
10. **Impacto social: el gráfico no está en base al 4T-2023; revisar cómo se empalman las series
    del INDEC y de la Di Tella** (Juan, 3-nov). Llevarlo a base oct-dic 2023 como el resto. Las
    series del INDEC y de la Di Tella se quedan (corrección de Juan): ver cómo se empalman y si
    necesitan algún ajuste para ser comparables.
11. **Pobreza: colores con cortes fijos, como la inflación** (Juan, 3-nov; igual que ADR-0367,
    los cortes de Luis para la inflación). Juan: «15 sería verde» (pobreza de 15 % o menos en
    verde). Faltan los cortes de amarillo, naranja y rojo.
12. **Consumo de carne: en el hover del gráfico, además del índice, el consumo en kg** (Juan,
    3-nov). Kilos por habitante del mes de SAGyP (la serie que puntúa, ADR-0392), junto al
    valor del índice.
13. **Los dos indicadores de carne miden cosas distintas: revisar si deben puntuar igual**
    (Juan, 3-nov). Uno es aspiracional (la carne vacuna como bien deseado) y el otro es
    material/nutricional (la proteína que efectivamente se come). Revisar cómo puntúa cada uno
    (peso, escala, dimensión) y si tiene sentido que pesen lo mismo.
14. **Presión de precios: falta salud, y revisar la ponderación de alimentos contra servicios
    públicos** (Juan, 3-nov). Sumar un indicador de precios de salud (por ejemplo, el capítulo
    salud del IPC o las cuotas de prepagas) y revisar cuánto pesa la inflación de alimentos
    frente a la canasta de servicios públicos.
15. **Mora: cortes fijos basados en análisis comparado, no sólo contra 2023** (Juan, 3-nov).
    Compararla con 2023 engaña porque entonces casi no había crédito, y la mora era baja por
    eso. Fijar los cortes de color con niveles de referencia de otros países o de otros
    períodos argentinos con crédito, declarados como convención.
16. **Carga del servicio de la deuda: igual que la mora** (Juan, 3-nov). Cortes fijos basados
    en análisis comparado, no sólo contra 2023, por el mismo motivo: en 2023 casi no había
    crédito.
17. **Inseguridad: revisar la ponderación y la referencia de los cortes** (Juan, 3-nov).
    Revisar cuánto pesa, y decidir si los cortes se fijan comparando con países similares o
    se dejan como están hoy (victimización rebaseada al 4T-2023, ADR-0393).
18. **RIGI: revisar los cortes de color** (Juan, 3-nov: «a mí no me cierra»). **Hecho el 3-nov
    (ADR-0419)**: Marcos definió la vara, lo aprobado contra la promesa de US$ 100.000 M (76,2 %,
    verde). La escala de ADR-0406 sigue igual; falta que Juan o Marcos confirmen si los cortes
    sirven para la promesa.

## 2. Esperan a otro

1. **Victimización** (fuente: Universidad Torcuato Di Tella): no publicó desde el informe de
   julio (subido el 5-ago). Ver sección 3.
2. **Bancos (ADEBA, ABA, ABAPPRA):** clasificados pero fuera de la postura empresaria por no
   llegar al mínimo de comunicados (ADR-0391); entran si lo llegan.

## 3. Con fecha y cargas mensuales

- **Antes de publicar cada lectura del mes de gestión** (Luis, revisión de gestión 26-oct, 3.8): mirar qué indicador explica el cambio antes de titular «la gestión mejora/empeora» (con reforma del Estado en 100, casi todo el movimiento viene de la brecha y la alícuota). Es una práctica editorial, no un cambio de código.

- **Antes del 1-dic: verificar que no haya otra suspensión del Fondo de Asistencia Laboral**
  (Luis, gestión 3.5; el código fecha la vigencia en el decreto 1228).
- **Fines de noviembre: victimización** (Juan, 29-oct: sin cambios). Si la Universidad
  Torcuato Di Tella sigue sin publicar, se revisa; el sitio la marca desactualizada solo a los
  150 días. El colector anda.
- **Fines de noviembre: lanzamiento del Votómetro** (repo aparte; reunión del 21-oct con Luis y
  Diego Dequino): método original de Silver Bulletin sin ajustes propios y documentado como
  fundamento (32, [L]); nombre «Votómetro argentino», las notas automáticas dicen «Botómetro»
  (33, [L]); sacar el balotaje y el mapa provincial del lanzamiento (34, [L]).
- **Mensual, a mano:** alquiler de UdeSA – Mercado Libre (cargar el PDF de octubre, ADR-0386 y
  0411) · prensa y Presidente (`scripts/prensa_presidente.py --mes AAAA-MM --lotes DIR`, unos
  4 GB de BigQuery, y los dos lectores sobre el lote; el indicador se retoma en oct-2027) ·
  padrón de ARCA (semanal en la fuente; se baja una vez por mes como archivo, sin publicarlo,
  ADR-0412).
- **Cuando aparezca:** convenios colectivos, todavía sin lista publicada.

## 4. Adjudicaciones de Juan que no deciden puntaje, e ideas para más adelante

Adjudicaciones (no deciden ningún puntaje):
- 69 desacuerdos del campo (los 13 que decidían el puntaje ya los adjudicó, ADR-0384).
- 42 de las cámaras nuevas (construcción 40, bancos 2).
- 818 de la prensa, sólo si el indicador se retoma (oct-2027). Datos en
  `data/politica/prensa_presidente_*.json`; con Milei el tono sigue los escándalos y acompaña a la
  confianza de la UTDT (r −0,42); 6.800 títulos de Milei y 1.632 de Macri y Fernández, dos lectores
  ciegos, acuerdo 90 % (kappa 0,82).

Ideas (nada de esto se arranca solo):
- **Elasticidad empleo-producto** (EMAE × SIPA por sector; Luis, septiembre; punto 18).
- **Historia de la carne vacuna antes de oct-2023** (hoy el gráfico arranca ahí): ediciones
  viejas de Internet Archive, o la copia de 2023 ajustada por población. No cambia puntajes.
- **Serie de empleadores como contexto:** no hay serie pública de inscriptos sin personal con
  historia a 2023. Lo más cercano: Boletín anual de Seguridad Social de ARCA, cuadro 3.1
  (empleadores con al menos un empleado): 537.678 en dic-2023, 519.531 en dic-2025 (−3,4 %),
  hasta un año de rezago; OEDE anual 573.008 (2023) → 558.317 (2024). Podría ir en la
  explicación de otra tarjeta sólo si puntúa.
- **Consumo por canales de Scentia** (Luis, a futuro).

---

## 5. Hecho

- Resueltos el 3-nov, quedan como están (Juan): escala de piquetes (convención declarada),
  empleo sin sumar trabajo registrado total ni desocupación, alquiler del INDEC se queda, y el
  planteo de Marcos sobre qué mide el RIGI (lo de hoy sobre sus cortes sigue abierto, punto 18).

- Internos, 1-nov: los dos comentarios del bloque C (itcp.py «CAC y CAME»; procedencia_anclas.py,
  recaudación «en torno al cero») corregidos, y `verificacion_remediacion.py` al día (decretos con
  ADR-0415, saldo empresario vuelto por ADR-0310, IAF fuera por ADR-0378): pasa.

- Decretos por ley sin tratados y con todos los DNU (ADR-0415, f1d1a6a2; Juan: «Aplicarlo», 29-oct). Ley 26.745 (BID) contada como no tratado (Juan, «Sí»). Se dejan los DNU de rutina; los delegados no se suman.
- Vetos insistidos (Marcos, 31-oct, «3 insistencias Congreso quebraron veto MILEI»): el registro tiene las mismas tres (Discapacidad 4-sep-2025; Universitario y Garrahan 2-oct-2025). La tarjeta da 0 porque cuenta 12 meses y ya salieron de la ventana. Juan, 1-nov: se dejan los 12 meses y se le explica a Marcos.
- Revisión de gestión de Marcos (30-oct): litigiosidad, insistencia y decretos derogados «está bien». Cortes: «Por qué importa» con el texto de Marcos. FAL: se deja como está (Juan, 30-oct); el 54 del mensual es el corte a septiembre, con 3 de 5 hitos.
- Gasto de funcionamiento: los sueldos se quedan (Juan, 29-oct: «yo diría que no»); la ficha ya lo declara.
- Rótulos de los alquileres: «Alquiler real (INDEC)» y «Alquiler real (Universidad de San Andrés – Mercado Libre)» (Juan, 29-oct; commit 2dff1ea3).

- Excel v7 de gestión y mensaje a Marcos: enviado por Juan («ok listo ya le pasé», 28-oct).

### 26-oct
- Textos y rótulos sin mover números (ADR-0366): color explicado, siglas en rótulos y unidades,
  «5e+06», fichas de macro y gestión, escala de expectativas, escalas declaradas, textos en llano,
  datos viejos de la ficha del índice, rótulos de gestión y político. Dos datos de Luis no se
  usaron por falsos: el protocolo no está anulado (la Cámara revocó la nulidad) y el pico del costo
  del Tesoro fue 33,8 % (ago-2025), no 58,8 %.
- Inflación con los cortes de Luis (ADR-0367) · sale IVA y cheque (ADR-0368) · juicios de la
  Justicia del Trabajo al índice (ADR-0365) · Fondo de Asistencia Laboral a cinco hitos
  (ADR-0370) · libre elección en salud por hitos (ADR-0371).
- Sale la brecha de obra pública, sector privado queda con la UIA (ADR-0372) · «Ingresos y
  consumo» se parte en dos (ADR-0373).
- Riesgo país no entra (cerrado, reunión del 26-oct). Reunión Juan–Luis del 26-oct, documento de
  las 21:00: cohesión se mantiene, salud, Excel confirmados.

### 27-oct
- Poder judicial sólo con cobertura de cargos (ADR-0374) · competitividad: dos tarjetas y el cruce
  en la dimensión (ADR-0375) · votos sobre bancas en cohesión, 22,1 % (ADR-0376) · vetos
  insistidos y decretos derogados reemplazan quórum y desafíos (ADR-0377) · transferencias no
  automáticas (ADR-0378) · juicios por riesgos del trabajo de vuelta (ADR-0379) y reemplazados por
  la siniestralidad como pidió Marcos (ADR-0385).
- Postura empresaria: comercio (ADR-0380), campo (ADR-0384), construcción y autopartistas
  (ADR-0391; bancos fuera). Propuesta de Luis de un solo modelo de lenguaje: descartada.
- Empleo con tasa de ocupación de la EPH (ADR-0383) · alquiler real de UdeSA (ADR-0386) · padrón de
  ARCA como dato (ADR-0389; superado el 29-oct por ADR-0412) · fichas sin cifras fijas, reservas
  contrastadas, revisión macro de Luis anotada punto por punto.
- Cuentas fiscales y Sector externo en dos dimensiones (ADR-0387) · jornadas no trabajadas con
  escala de percentiles previos, 100 → 87 (ADR-0388) · conflictividad con cortes de 2020-2023,
  63,9 → 94,4 (ADR-0390).
- Prensa y Presidente: colectado y pendiente (punto 25).
- Lectura sistémica de octubre de Luis: publicada en el informe del mes.

### 28-oct
- Propuesta macro del 11-oct de Luis aplicada (punto 19). Carne puntúa el consumo de SAGyP
  (ADR-0392) · victimización rebaseada al 4T-2023 (ADR-0393); todas las demás bases usan oct-dic 2023.
- Auditoría indicador por indicador: pobreza fechada, piquetes con año cerrado, lectura = color
  (ADR-0394 a 0396).
- Bloque B de la auditoría, todo aplicado: transferencias no automáticas contra 2023 (ADR-0397)
  · producción legislativa sin leyes vetadas (ADR-0398) · rezago suma la demora de publicación
  (ADR-0399) · bloque del senador del día de la votación (ADR-0400, el error de datos del Senado)
  · cohesión sólo con votaciones divididas, anclas del bloque PRO (ADR-0401) · alineamiento de
  senadores contra la historia (ADR-0402) · resultado primario por desvíos de su historia
  (ADR-0403) · inversión, crédito privado y saldo comercial con cortes de la historia previa
  (ADR-0404; comercio, decidido sin cambios) · RIGI con la escala de las concesiones (ADR-0406) ·
  Corredores Viales fuera de privatizaciones, sin doble conteo (ADR-0407).
- Piquetes: ADR-0405 los pasó al país, ADR-0408 los devuelve a la Ciudad; el protocolo está
  vigente (la Cámara revocó la nulidad el 31-mar-2026, caso en la Corte Suprema sin fallo).
- Reservas netas a estabilidad monetaria, índice macro sin moverse (ADR-0409).
- Decretos de necesidad y urgencia por identificador del texto original (ADR-0410).
- Sin abreviaturas en el sitio (tanda 2, commit 597ec270) · rótulo de decretos por ley
  publicada · ficha de la brecha cambiaria revisada · dotación: el universo no cambió
  (sólo salieron INADI, 408 personas, y ENOHSA, 356: a lo sumo 0,3 de los 21,4 puntos) y la ficha
  lo dice.
- Votaciones: la corrección es que no son «divididas» en el código viejo (ahora sí, ADR-0401).
  RIGI provincial: rótulo corregido, la ficha aclara que no se superpone con el de gestión.
- Semáforo: el naranja pasa a `#FB8C00`. Páginas de cinturón con títulos en tres niveles (#84 a #88).

### 29-oct (commits 871ea1ff y d5ae41bc)
- Alquileres: «contratos vigentes» (INDEC) con nivel real contra el 4T-2023 (hoy ≈ el doble) y
  «avisos nuevos» (UdeSA – Mercado Libre) reconstruido contra el 4T-2023, 42 % más barato a
  sep-2026; la ficha declara la cadena (ADR-0411). Canastas descartadas.
- Padrón de ARCA fuera de la tarjeta y sin publicarse; se sigue bajando (ADR-0412).
- Informalidad: asalariados informales sin aportes propios, 30,0 % en 4T-2023 y 31,9 % en 2T-2026
  (ADR-0413). Resuelve la preocupación de Juan del 28-oct por los monotributistas contados como
  empleo precario.
- Gasto de funcionamiento: 12 meses contra todo 2023 (ADR-0414).
- Comercio, victimización y conflictividad: sin cambios (decisión de Juan).
- Ficha de mortalidad de pymes corregida (la serie del Observatorio de Empleo y Dinámica Empresarial no está congelada).
- Tanda 1 (commit 4767d976): piquetes a la Ciudad, reservas a estabilidad, decretos por identificador.
  Tanda 2 (597ec270): textos sin siglas. Cerrada la búsqueda de una serie de empleadores (ver ideas).

## Nota

Los documentos de WhatsApp anteriores a agosto (unos 60, de febrero a julio) no están
bajados en esta Mac: WhatsApp sólo guarda los que se abrieron. Son pedidos ya
incorporados (paramétricas, auditorías de julio, fichas de semáforo).
