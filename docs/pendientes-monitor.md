# Pendientes del Monitor

Armado el 26-oct-2026 con lo que pidió Juan y los documentos de Luis y Marcos por
WhatsApp hasta el 26-oct a las 16:54 (originales en `docs/pedidos/originales/`, texto en `docs/pedidos/texto/`).
**No se arranca nada de acá sin que Juan lo pida.**

Marcas: **[J]** pedido de Juan · **[L]** documento de Luis · **[M]** documento de Marcos ·
**decidido** = Juan ya dijo que sí · **decidir** = falta su decisión · **choca** = contradice
algo ya hecho o decidido.

Fechas acordadas (reunión del Votómetro, 21-oct): Monitor general a principios de
noviembre; Votómetro a fines de noviembre.

## Hecho el 26-oct (ADR-0366, publicado)

Textos y rótulos, sin mover números: 1 (el color se explica), 3 (siglas en rótulos y
unidades; quedan las de impacto social, que se rehacen con su reestructuración), 4
(«5e+06»), 2 (fichas de los índices macro y gestión), 8 (escala de expectativas con
su equivalente anual), 12 y 17 (declarados en la ficha del índice), 14 (textos en
llano), 15 (31,3 % y excepción de reservas), los textos de 21 (rótulos, descripciones,
fuentes, decreto del FAL, RIGI, comentarios de `itcg.py`, piquetes con fecha y estado
judicial) y los rótulos y signos de 27 (Corte, comisiones, leyes sancionadas vs.
publicadas). Dos datos de Luis no se usaron por falsos: el protocolo no está anulado (la
Cámara revocó la nulidad) y el pico del costo del Tesoro fue 33,8 % (ago-2025), no 58,8 %.

## Hecho el 26-oct, cambios de cálculo (publicado)

7 inflación con los cortes de Luis (ADR-0367) · 10 sale IVA y cheque (ADR-0368) ·
juicios por riesgos del trabajo fuera, Reforma laboral FAL 50 / Justicia del Trabajo 50
(ADR-0369) · 20 FAL a cinco hitos (ADR-0370) · 21b salud por hitos (ADR-0371) ·
juicios de la Justicia del Trabajo al índice (ADR-0365). 22 y cohesión: esperan el índice de
votos (decisión de Juan).

23 sale la brecha de obra pública: sector privado queda con la UIA, 55,6 → 40,0 e índice
político 73,8 → 71,6 (ADR-0372) · 28 «Ingresos y consumo» se parte en Ingresos (114,6) y
Consumo (94,6) sin mover el índice de impacto social, 93,6 (ADR-0373). La carne: nivel de
consumo aparente (SAGyP), movimiento mensual de faena (producción) — dicho en la ficha.

## Hecho el 27-oct (publicado en un push; verificado en el diario; BigQuery cargado)

- **Político (74,3; antes 71,6):** Poder judicial sólo con cobertura de cargos (ADR-0374);
  vetos insistidos y decretos derogados por las dos cámaras en lugar de quórum y desafíos
  (ADR-0377, DNU y delegados juntos); votos de otros bloques al aprobar leyes del
  Ejecutivo, sin tratados, 22,1 % de la cámara (ADR-0376, opción de Juan: votos a favor
  menos bancas de LLA); transferencias no automáticas en lugar de las automáticas
  (ADR-0378; Luis revisa los rubros excluidos); postura del comercio (CAC) en sector
  privado, que sube de 40 a 70 (ADR-0380).
- **Macro (53,9, igual):** tipo de cambio real y términos del intercambio como dos
  tarjetas, cruce en la dimensión (ADR-0375); fichas sin cifras fijas; riesgo país y
  meses mezclados declarados; reservas contrastadas.
- **Gestión (septiembre 77,1; Reforma laboral 55,6):** vuelven los juicios por riesgos
  del trabajo, 50/25/25 (ADR-0379, supera a ADR-0369); verificaciones de Luis (brecha,
  dotación, gasto); explicación del puntaje 100 en todas las tarjetas.
- **Impacto social (95,7):** «Empleo» con la tasa de empleo de la EPH contra el mismo
  trimestre de 2023, cada décima = 1 punto (ADR-0383); salen construcción, empleo
  registrado, pymes, subocupación y trabajo independiente.
- **Entregados:** Excel v6 de gestión y mensaje a Marcos (Juan los manda); revisión macro
  de Luis anotada punto por punto (Descargas).
- **No se puede medir hoy:** padrón de empleadores de ARCA con y sin personal (no es
  público; lo más cercano es la serie mensual de empleadores afiliados a una ART de la
  SRT, que sí cuenta los que no tienen personal: **decidir** si entra y cómo). Superado esa noche: el padrón de ARCA sí se consiguió (ADR-0389).

## Hecho el 27-oct, tarde (publicado en un push; verificado en el diario; BigQuery cargado)

- **Político (73,6):** postura del campo (Coninagro, SRA, CRA) en sector privado, con los
  13 desacuerdos que decidían el puntaje adjudicados por Juan (ADR-0384).
- **Gestión (septiembre 77,5; Reforma laboral 58,2):** la siniestralidad de la SRT
  reemplaza a los juicios por riesgos del trabajo, FAL 50 / siniestralidad 25 / Justicia
  del Trabajo 25, como pidió Marcos (ADR-0385).
- **Impacto social (97,2):** alquiler real de UdeSA–Mercado Libre en precios, 10 % de la
  dimensión, cargado a mano una vez por mes desde el PDF (ADR-0386; historia desde
  jun-2025, antes el informe no trae la interanual de AMBA).
- **Entregados:** Excel v7 de gestión y mensaje a Marcos (reemplazan a la v6, que no se
  mandó).

## Hecho el 27-oct, noche (publicado en un push; verificado en el diario; BigQuery cargado)

- **Macro (53,9, igual):** «Cuentas fiscales» (19,2 %) y «Sector externo» (21,2 %) pasan a
  ser dos dimensiones, con los mismos pesos efectivos (ADR-0387). Cierra el 9.
- **Político (75,7):**
  - jornadas no trabajadas con cortes de los percentiles previos al mandato: el
    componente pasa de 100 a 87 (ADR-0388);
  - conflictividad con cortes de uno y dos desvíos de 2020-2023: el componente pasa de
    63,9 a 94,4 (ADR-0390). Cierra la observación 5 de Luis en el 27;
  - sector privado (70,2) suma la construcción (CAMARCO), y la industria promedia la UIA
    con las autopartistas (AFAC). Los bancos (ADEBA, ABA, ABAPPRA) se clasificaron pero
    quedan afuera por no llegar al mínimo de comunicados (ADR-0391). De 41 cámaras
    relevadas, sólo esas dos llegan al mínimo.
- **Impacto social (97,2):** padrón de empleadores de ARCA, 511.847 al 24-oct-2026 (−7,5 %
  contra ago-2024), como dato dentro de la tarjeta de ocupación. Puntúa cuando tenga 12
  meses; la historia previa se reconstruyó con copias del Internet Archive (ADR-0389).
  Cierra el «no se puede medir» del padrón.
- **Prensa y Presidente (25): colectado y pendiente**, ver el punto 25.

## Hecho el 28-oct

- Propuesta macro del 11-oct de Luis: aplicada (estructura de la página), con las
  dimensiones que después cambió su propia revisión del 26-oct (19).
- Votaciones: 99 en 90 días (46 Diputados, 53 Senado), LLA unida en todas. **Corrección
  (auditoría del 28-oct):** no son «divididas»: el código no filtra, entran todas las
  actas donde votó LLA, unas 28 casi unánimes, y las 53 del Senado son 4 sesiones
  votadas artículo por artículo. Ver auditoría, punto B4 (27).
- RIGI provincial: el rótulo ya se había corregido (ADR-0366); la ficha aclara que no se
  superpone con el RIGI de gestión (27).
- La carne puntúa el consumo de SAGYP, no la faena del INDEC; tarjeta y puntaje son el
  mismo dato y el mismo mes (ADR-0392) (C).
- Revisión de bases «fines de 2023»: todas usan oct-dic 2023 salvo la victimización,
  que pasa de ene-2024 al 4T-2023 (ADR-0393).

## Auditoría indicador por indicador (28-oct, un agente por cinturón)

Verificada contra código y snapshot. Los errores (pobreza corrida un semestre, piquetes
con el año sin cerrar, lectura ≠ color en los bordes, rótulo de la victimización, rojo
faltante en jornadas) se corrigen el 28-oct (ADR-0394 a 0396). Queda para ir viendo:

**B. Decisiones de método (mueven puntajes)**
1. Transferencias no automáticas: compara contra los 12 meses previos y premia el
   rebote (−85 % en 2024, +32 % en 2025: hoy +6 %, verde, con un nivel ~1/5 del de
   2023). Recomendación: compararlas contra 2023, como conflictividad. 8,2 % del ITCP.
2. Cortes calibrados sobre el propio mandato: resultado primario (12 % de macro),
   alineamiento de senadores, piquetes, RIGI, cohesión. Llevarlos a historia previa,
   uno por uno, como ADR-0390.
3. Saturados casi siempre en 10 o 100: IAI (23 de 33 meses), crédito privado (19 de 34),
   saldo comercial (7 meses seguidos en el techo), postura del comercio (siempre 1,0).
4. Cohesión: filtrar de verdad las actas divididas, que es lo que dicen los textos.
5. Privatizaciones y concesiones viales: la Res. ST 80/2025 sube las dos en nov-2025,
   misma dimensión (~0,7 pts de peso). Recomendación: declararlo en las dos fichas.
6. Producción legislativa: las bandas premian más leyes, pero en 2025 las de la
   oposición (después vetadas) le suman al Gobierno. Definir la pregunta (con Luis).
7. Hipótesis a chequear: conflictividad compara contra 2023 fijo con horizonte de hasta
   3 años, pero los cortes salen del desvío interanual; victimización sin informe nuevo
   desde julio (¿la UTDT no publicó o el descubrimiento falla?).

**C. Sólo texto (no mueven números)**
- Fichas con cifras o pesos viejos: EMAE, IPI y emae_difusion (no registran ADR-0368),
  dotación (cifras de mayo), saldo comercial (cuenta corriente vieja), ejemplo «100
  normas» de desregulación, historial del índice de gestión sin ADR-0370/0371,
  desequilibrio monetario («11 %», «competitividad externa»), reservas en el registro de
  ADR-0387 de idc/crédito/costo del Tesoro, ipc_total «tres» deflactores (son cuatro).
- Afirmaciones falsas: el ISAC ya no está en el índice de impacto social (ficha del
  IAI); el ratio motos/autos sí puntúa (ficha de motorización); salud ya no es
  «derivación de aportes a prepagas» (dimensión Reforma social); apoyo_empresario
  «32 meses sin huecos» (tiene huecos) y limitación de AEA que ya no entra; ficha del
  índice de macro: recaudación «promedio móvil de 3 meses» (ya no); peso_tarifas
  renormaliza también con alquiler UdeSA.
- Rótulos que prometen de más: «Base imponible real (nación + provincias)» (sólo IIBB
  del Convenio Multilateral); «Costo real del alquiler» muestra variación nominal;
  «canasta del hogar» es por adulto equivalente; resultado primario «de cada cien pesos
  recaudados» incluye seguridad social y coparticipación; siniestralidad «resultado de
  la reforma en seguridad laboral»; brecha «sobre el dólar oficial» (es el mayorista).
- Rezagos mal declarados: ICG (dice 55-60 días, llega en ~27), conteos legislativos de
  12 meses (deberían ser 6, hoy 0-1,5), resultado primario («un mes»), EMAE «el más
  rezagado» (términos del intercambio lo es).
- Tablas de cortes que no coinciden con el motor: FAL «>90 → 100» (90 da 100), votos
  sobre bancas, insistencias/rechazos «3–4 → 35» (4 da 10), eficacia legislativa
  (comentario de rango viejo, «15 a 20 proyectos»).
- Comentarios internos viejos: itcp.py «AEA y UIA», «CAC y CAME»; procedencia_anclas
  desregulación «100/300/600/1200», recaudación «en torno al cero».

## Lo que queda abierto (actualizado el 28-oct)

- **Alquiler del IPC: que sea alquiler real** (Juan, 28-oct). Hoy la tarjeta «Alquiler (IPC
  del Gran Buenos Aires)» muestra la variación mensual nominal (1,88 %) y el puntaje usa el
  alquiler relativo al IPC general. Que la tarjeta y el puntaje sean el alquiler real
  (descontada la inflación) contra fines de 2023, con su rótulo. Opción de Juan: en vez
  del IPC, expresarlo en canastas (cuántas canastas básicas vale el alquiler). Revisar con
  Juan cuál.

- **Alquiler de UdeSA – Mercado Libre: conseguir el 4T-2023 o sacarlo** (Juan, 28-oct). Hoy
  se mide como variación interanual porque el informe no trae datos para comparar contra
  fines de 2023 (ADR-0386). Buscar los valores de octubre a diciembre de 2023 (informes
  viejos, archivo de Internet, pedido público de datos no); si no aparecen, el indicador sale
  del índice (lleva ADR).

- **Verificar el universo de la dotación** (Juan, 28-oct; Luis, gestión 3.1). Ver si la
  serie del INDEC de empleados de la administración nacional cambió qué organismos cuenta
  desde dic-2023 (cierres, traspasos a empresas o provincias) y cuánto del −21,4 % es eso
  y no recorte.

- **Ficha de la brecha cambiaria desactualizada** (Juan, 28-oct). Revisarla entera. Visto:
  el contraste del 27-oct cita una brecha de 9,2 % y hoy es 7,8 %; quedan siglas
  (contado con liquidación, comunicación A3500, Banco Central); verificar el resto contra
  lo que hace el cálculo hoy.

- **Sin abreviaturas en el sitio** (Juan, 28-oct): nada de siglas ni abreviaturas en
  rótulos, unidades, tarjetas, fichas y textos (CABA → Ciudad de Buenos Aires, ATN, RIGI,
  DNU, EPH, REM, FAL, etc.: el nombre completo o una forma llana). Barrer todo el sitio.
  Amplía el punto 3 (siglas).

- **Piquetes: volver a la Ciudad de Buenos Aires** (Juan, 28-oct). Estaba decidido mantener
  la Ciudad y el ADR-0405 (28-oct) lo pasó al total del país (99 → 77) contra esa decisión.
  Revertir a CABA (otro ADR) y revisar lo que dicen la tarjeta y la ficha de la fuente
  (consultora Diagnóstico Político) y del protocolo (vigencia: anulado en primera
  instancia y apelado; verificar el estado actual).

- **Revisar vetos, decretos y DNU** (Juan, 28-oct): «DNU por ley» (ratio_dnu), «Vetos que el
  Congreso dio vuelta» (insistencias_vetos) y «Decretos derogados por el Congreso»
  (rechazos_decretos, ADR-0377). Hoy 1,09 / 0 / 0.

- **Reservas netas a «Estabilidad monetaria-inflacionaria»** (Juan, 28-oct). Hoy están en
  «Sector externo» (ADR-0387). Conservando su peso en el índice (5,44 %), estabilidad
  pasaría de 26 % a 31,4 % y sector externo de 21,2 % a 15,8 %; el índice no se mueve.
  Lleva ADR.

- **Error de datos (sin decisión): bloques del Senado.** El sitio asigna a cada senador un
  bloque para todo su mandato: Juez, Paoltroni y Álvarez Rivero cuentan como LLA en meses
  en que no lo eran. Explica casi todos los rojos de la cohesión (ago-2025: 77,8 → 100) y
  toca alineamiento y votos ajenos. Arreglo: lista de pases con fecha y fuente.
- **Decisiones de método B, auditadas caso por caso (28-oct):** documento «Decisiones de
  método del Monitor — auditoría del 28-oct» (https://claude.ai/artifact/DrXmpa1BhLJH8niWRmzeoU).

- **Para la reunión con Luis (28-oct, 15 h):** contarle lo de arriba; pedirle el
  documento de Ever y la revisión de los rubros de transferencias.
- **Opcional:** completar la historia de la carne vacuna antes de oct-2023 (hoy el
  gráfico arranca ahí): ediciones viejas de Internet Archive, o la copia de 2023
  ajustada por población. No cambia puntajes.
- **Sin cerrar del 27 (Luis 7):** DNU por ley cuenta leyes publicadas y producción
  legislativa, sancionadas; la ficha del DNU ya lo dice, falta aclararlo en los rótulos.
- **Esperan a otro:**
  - el resto de la EPH (desocupación, informalidad, ingresos): Luis manda el documento
    de Ever (30);
  - los rubros excluidos de las transferencias no automáticas: los revisa Luis (26).
- **Mensuales, a mano:**
  - alquiler UdeSA (PDF de octubre);
  - prensa y Presidente (`prensa_presidente.py --mes`);
  - padrón de ARCA (semanal en la fuente; se baja una vez por mes).
- **Con fecha:** verificar antes del 1-dic que no haya otra suspensión del FAL.
- **Cuando aparezca:** convenios colectivos, todavía sin lista publicada.
- **Adjudicación de Juan, no decide ningún puntaje:**
  - 69 desacuerdos del campo;
  - 42 de las cámaras nuevas (CAMARCO 40, bancos 2);
  - 818 de la prensa, sólo si el indicador se retoma.
- **Más adelante:** Votómetro (32 a 34, lanzamiento a fines de noviembre); elasticidad
  empleo-producto (18, es una idea).

## Acuerdos de la reunión Juan–Luis del 26-oct (documento de Luis, 21:00)

Llegó después de armar esta lista (`docs/pedidos/texto/2026-10-26_Luis_261026 decisiones
de la reunión JP y MJ.txt`). Próxima revisión: **miércoles 28-oct, 15 h**.

- **Choca con lo hecho:**
  - A. Reforma laboral con los DOS juicios (Justicia del Trabajo y riesgos del trabajo);
    ADR-0369 sacó los de riesgos del trabajo. **cerrado**: volvieron (ADR-0379) y después
    los reemplazó la siniestralidad, como pidió Marcos (ADR-0385).
  - B. Político: sacar «control sobre los jueces» (`paralisis_denuncias`) y «velocidad
    de resolución de la Corte» (`velocidad_resolucion`); en ADR-0366 sólo se renombraron.
    **hecho (ADR-0374)**: Poder judicial queda sólo con la cobertura de cargos.
  - C. La carne: Luis dice que es consumo per cápita y que la duda era un error. El nivel sí
    es consumo (SAGyP), pero el movimiento que puntúa sale de la faena del INDEC. Aclarárselo.
    **hecho (ADR-0392)**: puntúa el consumo.
- **Nuevo:**
  - D. Competitividad: tarjetas separadas de términos del intercambio y tipo de cambio
    real; el color lo da el cuadrante del cruce de los dos (resuelve el 13). Como no
    puntúan solas, van dentro de la tarjeta de competitividad (regla ADR-0153/0216).
    **hecho (ADR-0375)**
  - E. «Veto por quórum» y «desafíos legislativos» se reemplazan por **insistencias sobre
    vetos** y **rechazos de DNU** (resoluciones de cada cámara; Marcos tiene las fuentes). **hecho (ADR-0377)**
  - F. Fichas: sacar los datos fijos del texto y remitir al último dato publicado (no
    quedó cerrado). **hecho** (27-oct): fichas sin cifras fijas.
  - G. El documento de revisión macro es el documento madre del cinturón: lo no tomado
    se marca «no considerado». **hecho**: revisión anotada punto por punto (27-oct).
- **Confirma lo hecho o lo decidido:** inflación, expectativas, ficha del índice, riesgo
  país **no** entra (cierra el 11), brecha de obra fuera, cohesión se mantiene, Ingresos y
  Consumo, FAL al 90 %, salud, Excel. Transferencias: sólo lo no automático (26).
  Precios: se mantienen alimentos y servicios; el alquiler UdeSA/Mercado Libre, a evaluar
  (29, sin rebautizar). Empleo: principal, la variación de la ocupación de la EPH;
  complemento, el padrón de empleadores de ARCA; Luis manda el documento de Ever (30).
  Cámaras: oficiales si hay; si no, sentimiento en prensa de sus referentes; si nada,
  queda como está (24). A futuro, consumo por canales de Scentia.

## Transversal (todo el sitio)

1. **Que el color se entienda.** La tarjeta muestra la escala de puntaje (100/85/65/40/10)
   pero el color sale de otros cortes; «¿por qué este color?» nombra cortes que no se ven.
   Mostrar los cortes de color y que la frase nombre el corte y el color vecino.
   [L macro 2.2, político 8]
2. **Fichas de los índices.** Las de macro y gestión dicen que umbrales y pesos vienen del
   documento institucional, pero buena parte es elaboración propia; y el historial de
   cambios está incompleto y con siglas. [L macro 3.3 y 3.5, gestión 3.6 y 3.7]
3. **Siglas que quedan en rótulos, unidades y fichas** (EMAE, IPI, REM, DGI, «i.a.», APN,
   SRT, RIGI, IRPC, IDM, TCRM…). [L macro 2.1 y 2.8, gestión 2.1, sept «falta»]
4. **Formato «5e+06»** en la escala de jornadas no trabajadas. [L político 8]
5. **Lectura del mes.** Aclarar que el índice mezcla datos de distintos meses y mirar qué
   indicador explica el cambio antes de titular. [L macro 3.8, gestión 3.8]
6. **Lectura sistémica de octubre** (texto editorial de Luis, 12-oct): decidir si se
   publica y dónde. **hecho**: publicada en el informe del mes. [L]

## Macroeconomía (revisión de Luis, 26-oct)

7. **Inflación en verde hasta ~2,8 % mensual.** Luis propone: verde < 1 % mensual,
   amarillo < 2 %, naranja < 3 %, rojo arriba. Cambio de cálculo: mueve el índice.
   **hecho (ADR-0367)** (26-oct): cortes de Luis, y el puntaje acompaña (hoy 1,93 % pasa a
   amarillo). Revisar expectativas con el mismo criterio. [J, L 3.1]
8. **Expectativas: valor anual contra escala mensual.** Mostrar «21,1 % anual (≈1,6 % por
   mes)» y la escala en anual. [L 3.2]
9. **Reagrupar el sector externo**: «Cuentas fiscales» (resultado primario, base imponible)
   y «Sector externo» (saldo comercial, reservas, tipo de cambio real), conservando los
   pesos efectivos. **hecho (ADR-0387)** [L 1.1]
10. **Sacar «Actividad tributaria (IVA + cheque)»** por redundante con la actividad.
    Entró a pedido de Luis en septiembre (ADR-0329). **hecho (ADR-0368)** (26-oct): sale, con su
    tarjeta; su peso vuelve a los otros indicadores de actividad. [J, L 1.2]
11. **Riesgo soberano / resultado financiero.** Falta riesgo país; el resultado primario
    excluye intereses (en septiembre Luis ya pedía el financiero, porque el Gobierno
    anuncia superávit con intereses). Evaluar o declararlo en la ficha. **cerrado**
    (reunión del 26-oct): el riesgo país no entra y queda declarado en la ficha. [L 1.3, sept]
12. **Escalas calibradas contra el período** (crédito privado, inversión física, términos
    del intercambio; ~38 % del índice): declararlo en cada ficha y, a mediano plazo,
    anclas normativas. [L 1.4]
13. **Tipo de cambio real × términos del intercambio**: ver si se muestran los dos y el
    combinado. **hecho (ADR-0375)**: dos tarjetas, y el cruce en la dimensión. [L 1]
14. **Textos en llano**: capacidad prestable, reservas, liquidez y compra de dólares;
    polaridades mezcladas («pts de tensión»); resultado primario en % de la recaudación
    con equivalencia en PBI; crédito privado (rótulo «en pesos», frecuencia mensual, sacar
    jerga interna); explicar el 0,17 de los cortes de inversión física. [L 2.3–2.7]
15. **Datos viejos de la ficha del índice**: «24 % depende del IPC» hoy es 31,3 %; el
    criterio de selección (serie desde dic-2023) tiene la excepción de reservas
    (jun-2024). [L 3.4, 3.6]
16. **Reservas netas en verde con 10.725 M**: contrastar con dos estimaciones públicas.
    **hecho** (27-oct). [L 3.7]
17. **Costo del Tesoro satura** sobre 20 % real: declararlo en su ficha. [L 3.9]
18. **Elasticidad empleo-producto** (EMAE × SIPA por sector). Idea. [L sept]
19. Verificar que la propuesta de Luis del 11-oct (tarjetas por dimensión e indicador)
    quedó aplicada. **abierto** [L 11-oct]

## Gestión

20. **FAL a 90 % de avance**, como propuso Marcos: a la ley y el decreto se suman la RG
    CNV 1167, la RG ARCA 5907/2026 y la oferta de los bancos; puntaje 55 → 100. Cambia la
    regla de ADR-0228 («cuenta lo que rige»): lleva ADR. La RG ARCA 5907 no la
    encontramos el 23-oct. Recalcular el efecto con el 50/25/25 de ADR-0365. Al hacerlo,
    corregir el mensaje a Marcos (hoy dice «FAL en 90: por ahora no»). **hecho (ADR-0370)**: cinco hitos. [J, M]
21. **Revisión de gestión de Luis (26-oct, la reenvió Marcos).** Está escrita sobre los
    datos de la mañana: dotación ya no está en 100 (ADR-0364) y los juicios ya cambiaron
    (ADR-0365). Lo que sigue en pie:
    - **Juicios por riesgos del trabajo**: no miden la reforma, que apunta a despidos.
      **superado**: salieron (ADR-0369), volvieron (ADR-0379) y los reemplazó la
      siniestralidad (ADR-0385). Lo decidido el 26-oct: salen del índice y de las tarjetas; Reforma laboral queda
      FAL 50 % · juicios de la Justicia del Trabajo 50 % (incluyen despidos). Corregir
      el mensaje a Marcos. [J, L 1.1]
    - **Gasto de funcionamiento** en 100: ¿incluye remuneraciones (la masa salarial salió
      del índice)? Compara contra ago-2023 y dotación contra dic-2023: unificar. [L 1.5,
      2.4]
    - **Orden público** puntúa 99 con dato anual 2025 de una consultora y el protocolo
      anulado (en apelación): ajuste del analista, suspenderlo, o mostrar el estado
      judicial en la tarjeta. **hecho (ADR-0366)** (26-oct): sigue puntuando y la tarjeta muestra
      «dato del año 2025» y que el protocolo está anulado en primera instancia y
      apelado. [J, L 3.2]
    - **Rótulos que digan lo que miden**: «Brecha cambiaria» (sin «cepo»), «Impuestos
      sobre el comercio exterior», «Empleados de la administración nacional», «Grandes
      inversiones aprobadas», «Cortes de calle por protestas en la Ciudad», «Aportes
      derivados directo a prepagas»; unidades con su base. [L 1.2–1.4, 2.1, 2.6]
    - **Descripciones viejas**: «Reforma social y orden» todavía describe la composición
      presupuestaria; «cepo desarmado» en reformas económicas. [L 2.2, 2.3]
    - **Puntaje 100 sin explicación** en la tarjeta (gasto, concesiones). [L 2.5]
    - **Fuentes**: la brecha sale de dolarapi.com (contrastar con otra fuente); la
      desregulación la cuenta el ministerio que la ejecuta (decirlo y verificar una
      muestra en el Boletín). [L 3.4]
    - **FAL**: la descripción cita el Decreto 408 y el código fecha la vigencia en el
      1228; unificar la cita y verificar antes del 1-dic que no haya otra suspensión.
      [L 3.5]
    - **RIGI**: el porcentaje baja si entran muchos proyectos; declararlo o medir la
      demora de aprobación. [L 1.6]
    - **Dotación**: verificar si parte del −21,4 % es cambio de universo en la serie del
      INDEC. [L 3.1]
    - Comentarios de `itcg.py` sobre suspendidos que dicen «la card se sigue mostrando».
      [L 3.9]

21b. **Libertad de opción en salud: pasarlo a hitos** (Marcos, 26-oct, segundo documento).
    Propone cambiar el objeto: medir la implementación de la libre elección, no la
    derivación de aportes a prepagas. Nombre «Implementación de la libre elección de
    cobertura de salud», por hitos verificables: marco normativo que habilita elegir
    entre agentes 25 % · fin de la permanencia obligatoria inicial 20 % · procedimiento de
    opción de cambio habilitado 20 % · derivación directa sin intermediación 20 % ·
    funcionamiento efectivo y verificable 15 %. Fuentes: SSSalud, ARCA (publicación del
    4-dic-2024), Boletín (DNU 70/2023). El porcentaje de usuarios quedaría como dato
    complementario. Advierte que el puntaje quedaría alto y estable si los hitos están
    cumplidos. **hecho (ADR-0371)** (Juan, 26-oct: «se hace lo que dice Marcos»): reemplaza lo
    decidido el 24-oct y la propuesta de Luis de renombrarlo «Aportes derivados directo
    a prepagas». Cada hito necesita su regla documental de verificación antes de
    puntuar. Lleva ADR. [J, M]

## Político

22. **Índice de votos por encima de las bancas propias**: cuántos votos más que sus
    bancas consigue el Gobierno al aprobar leyes. Cohesión de bloque **se mantiene**.
    **hecho (ADR-0376)**: 22,1 % de la cámara; la dimensión se reparte 50/50 con la
    cohesión. [J]
23. **Sacar Brecha de obra pública.** **hecho (ADR-0372)** [J; también L 18-oct]
24. **Postura empresarial con más cámaras.** Luis propone tres sectores con el método de
    la UIA, promediando entidades: campo (SRA, CRA, FAA, Coninagro), comercio (CAC y
    CAME), tecnología (CESSI y Argencon); mínimo 4 comunicados con postura por entidad en
    12 meses; serie desde dic-2023; codificación doble; renombrar la card a «Postura
    pública de la industria». Las cuatro posturas reemplazan a la dimensión actual a
    partes iguales. Propone además clasificar con un modelo de lenguaje validado contra
    los ~100 comunicados ya codificados, lo que cambia la regla «el juicio no se
    automatiza» y lleva ADR. (Hoy ya se codifica con dos modelos a ciegas y adjudicación
    humana: ADR-0131/0150.) **decidido y hecho** (26-oct): se suman
    cámaras con el método actual (dos modelos a ciegas y adjudicación humana); la
    propuesta de un solo modelo queda descartada. **hecho**: comercio (ADR-0380), campo
    (ADR-0384), construcción y autopartistas (ADR-0391); bancos clasificados y afuera.
    [J, L 18-oct]
25. **Menciones de los políticos principales en la prensa.** [J]
    **Colectado y pendiente** (decisión de Juan, 27-oct). Se midió el tono de los titulares
    hacia el Presidente: 6.800 títulos de Milei y 1.632 de Macri y Fernández (GDELT), dos
    lectores ciegos, acuerdo 90 % (kappa 0,82). Con Milei sigue los escándalos y acompaña
    a la confianza UTDT (r −0,42); la escala no tiene contra qué compararse: con los
    presidentes anteriores no sigue a la encuesta y comparar contra el arranque depende
    del mes base. **Tarea mensual**: `scripts/prensa_presidente.py --mes AAAA-MM --lotes DIR`
    (unos 4 GB de BigQuery) y los dos lectores sobre el lote. Se retoma en oct-2027.
    Los 818 desacuerdos no se adjudican hasta entonces. Datos en
    `data/politica/prensa_presidente_*.json`.
26. **Transferencias no automáticas a provincias**: anticipos financieros (adelantos
    transitorios), ATN, transferencias por programa. Hoy sólo se miden las automáticas.
    Pista: Presupuesto Abierto, inciso 5, partidas 5.7 y 5.8; los anticipos son operaciones
    de tesorería y hay que buscarlos en el Boletín. **hecho (ADR-0378)**; Luis revisa
    los rubros excluidos. [J]
27. **Revisión del político de Luis (26-oct):**
    - Un cuarto del peso clavado en 100 (cohesión, jornadas no trabajadas, veto por
      quórum, desafíos legislativos): ampliar anclas o pasar a contexto. Para cohesión
      propone bajar el peso a 6–8 % y un mínimo de actas divididas. **hecho (ADR-0376)**
      (26-oct): cohesión espera al índice de votos por encima de las bancas (22), que
      entra a su misma dimensión; ahí se reparte el peso. Jornadas no trabajadas: **hecho
      (ADR-0388)**, cortes en percentiles de 2006-2023, pasa de 100 a 87. Veto y desafíos
      salieron del índice (ADR-0377).
      [J, L 1, 2]
    - Renombrar «Velocidad de resolución» → «Tasa de resolución de la Corte» y «Parálisis
      de denuncias» → «Actividad de las comisiones de control del Consejo», explicando el
      signo. [L 3, 4]
    - Revisar si las anclas de conflictividad están calibradas sobre el propio mandato.
      **hecho (ADR-0390)** [L 5]
    - Nombres: apoyo empresario es sólo la UIA; adhesión de provincias es sólo el RIGI
      (fuente MAGyP) y se superpone con RIGI de gestión. [L 6]
    - DNU por ley usa leyes publicadas; producción legislativa, sancionadas: unificar o
      aclarar. [L 7]
    - Verificaciones: regla de color en `publicar.py`, cuántas actas divididas entran en
      90 días, que los 0 de veto y desafíos sean reales.

## Impacto social (Luis, 26-oct)

28. **Separar «Ingresos» en dos**: Ingresos (salario real, pobreza) y Consumo (carnes
    —chequear si es consumo o producción—, motorización, supermercados; ver la
    publicación de Scienta). **hecho (ADR-0373)** [J, L]
29. **«Presión de precios» pasa a «Poder de compra»**: inflación de alimentos, canasta de
    servicios públicos sobre salario y costo real del alquiler con el índice de la
    Universidad de San Andrés y Mercado Libre. **hecho**: el alquiler entra (ADR-0386) y
    la dimensión no se rebautiza (reunión del 26-oct). [J, L]
30. **«Prospectiva de empleo» pasa a «Empleo»** con indicadores nuevos: EPH continua
    (desocupación, empleo, informalidad, subocupación, ingresos; trimestral) y padrón de
    contribuyentes de ARCA (empleadores inscriptos; sin serie histórica). Sacar
    construcción; no tomaría empleo registrado, empleadores pyme, subocupación
    demandante ni trabajo independiente; informalidad «analizar». **en parte**: tasa de
    empleo (ADR-0383) y padrón de ARCA (ADR-0389); el resto espera el documento de Ever.
    [J, L]
31. Se mantienen: Vulnerabilidad financiera (mora y carga de la deuda), Confianza (ver su
    lectura) y Seguridad (victimización, homicidios, robos). [L]

## Votómetro (repo aparte; reunión del 21-oct con Luis y Diego Dequino)

32. Usar el método Silver Bulletin original, sin ajustes propios (se discutió el de
    contar sólo la última encuesta de Delfos), y documentarlo como fundamento. [L]
33. Nombre «Votómetro argentino» (las notas automáticas dicen «Botómetro»). [L]
34. Sacar el balotaje y el mapa provincial del lanzamiento. Lanzamiento a fines de
    noviembre. [L]

## Nota

Los documentos de WhatsApp anteriores a agosto (unos 60, de febrero a julio) no están
bajados en esta Mac: WhatsApp sólo guarda los que se abrieron. Son pedidos ya
incorporados (paramétricas, auditorías de julio, fichas de semáforo).
