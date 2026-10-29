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

1. **Piquetes: escala de convención.** Las bandas 0/25/50/75 % se fijaron mirando la caída
   porteña de 2024-2025 y siguen así, declaradas como convención (ADR-0408 las deja sin
   mover; el resto de las escalas calibradas sobre el propio mandato ya pasó a historia
   previa). Fuente: auditoría del 28-oct, B2. Estado: decidir si se llevan a historia
   previa o se dejan declaradas.
2. **Restos del bloque C de la auditoría del 28-oct.** Verificado el 29-oct en fichas.ts,
   datos.ts, itcp.py y procedencia_anclas.py: los textos públicos ya están corregidos. Quedan
   sólo dos comentarios internos del código, que no se publican (itcp.py «CAC y CAME»;
   procedencia_anclas.py, recaudación «en torno al cero»). Se arreglan en la próxima tanda.

## 2. Para la reunión con Luis

Temas para la próxima revisión con Luis (la del 28-oct, 15 h, ya fue; lo que quedó esperando
a Luis está en la sección 3).

1. **Gasto de funcionamiento: ¿con o sin sueldos?** (Luis, revisión de gestión 26-oct, 1.5 y
   2.4; base decidida por Juan el 29-oct, ADR-0414: promedio de los últimos 12 meses contra el
   promedio de todo 2023, −28,0 % a ago-2026.) Los sueldos son el 78 % del gasto; sin ellos,
   −45 % y queda el 22 % del gasto. Recomendado: dejarlos y decirlo en la ficha. Para tener a
   mano, la grilla base × ventana (dato a ago-2026): último mes −36,0 % (contra todo 2023) /
   −39,4 % (oct–dic 2023); últimos 3 meses −26,0 / −30,0; últimos 12 meses −28,0 / −31,9.
   Otras bases: mismo mes de 2023 −35,9 %; dic-2023 −50,3 % (pico de aguinaldo); 4T-2024
   contra 4T-2023 −20,2 % (puntaje 85). Con cualquier base puntúa 100 (todas pasan −25 %).
   Se descartó oct–dic 2023 porque trae medio aguinaldo en 3 meses y exagera la caída 4 a 7 puntos.
2. **Decretos de necesidad y urgencia por ley** (Juan, 28-oct; ADR-0410). Hoy 1,09 por ley
   (puntaje 57). Los ceros de vetos dados vuelta y de decretos derogados son correctos.
   - **Tratados en el denominador:** de las 32 leyes de la ventana, unas 19 aprueban
     tratados. Sin ellos el cociente sería 2,85 (puntaje 10 en vez de 57); habría que
     recalcular la referencia histórica con el mismo criterio.
   - **Decretos de rutina** (siete de ejercicios militares y uno de viaje del Presidente): sin
     ellos 0,91 (puntaje ~67).
   - Recordar lo ya acordado: «decretos de necesidad y urgencia + delegados juntos» (ADR-0377).
3. **Empleo: sumar el trabajo registrado total y la desocupación** (Juan, 29-oct; para
   proponer en la próxima). Reemplaza al complemento del padrón de ARCA, que salió (ADR-0412).
   - Trabajo registrado total del sistema previsional, con monotributistas y autónomos y sin
     el monotributo social (Secretaría de Trabajo, «Situación y evolución del trabajo
     registrado», mensual): 12.758 mil en nov-2023, 12.505 mil en jul-2026 (−2,0 %). No es el
     «empleo registrado privado» que Luis descartó (sólo asalariados privados, −4,7 %).
     Alternativa medida el 28-oct: −1,5 % contra −3,8 % de asalariados privados.
   - Y además, no en lugar de: la desocupación de la Encuesta Permanente de Hogares, 5,7 % en
     4T-2023 y 7,9 % en 2T-2026.
   - **Superposición, para decirlo en la reunión:** ninguno repite a otro, pero se pisan en
     parte. La desocupación se mueve en buena medida con la ocupación (misma encuesta; se
     separan cuando mucha gente sale a buscar trabajo o cuando el que lo pierde deja de buscar).
     El registrado total se pisa con la ocupación (los registrados son ~6 de cada 10 ocupados)
     y con la informalidad (las dos miran si el trabajo es en blanco). Lo propio de cada uno: la
     desocupación es el dato más citado; el registrado es registro oficial, mensual, y cuenta
     al monotributista como trabajo en blanco. Si entran, con poco peso dentro de empleo para
     no contar tres veces la misma caída.
4. **¿Sacar el alquiler del INDEC?** (Juan, 29-oct: «me van a pedir que lo saque».) El
   documento de Luis del 22-oct tenía un solo alquiler («COSTO REAL DEL ALQUILER (VER EL INDICE
   DE SAN ANDRES…)»); la reunión del 26-oct no pidió sacar el del INDEC. Para que quede: es lo
   que paga la mayoría de los inquilinos (contratos vigentes), es el dato oficial, y sacarlo deja
   sólo el alquiler que favorece al Gobierno. Para sacarlo: buena parte de la suba es la puesta
   al día de contratos atrasados por la ley de alquileres. Si sale, el de UdeSA queda con el 20 %.

No quedan otros temas para Luis marcados como abiertos: producción legislativa, cohesión,
transferencias y bandas ya los resolvió Juan con ADR (ver «Hecho»).

## 3. Esperan a otro

1. **Documento de Ever** (Luis, acuerdos del 26-oct: «Luis le pasa el documento de Ever»; punto
   30). Con él se decide el resto de la Encuesta Permanente de Hogares: desocupación,
   subocupación, ingresos. Nota: «el resto espera a Ever» no es un pedido en sí; lo acordado en
   empleo (ocupación como principal) ya está hecho.
2. **Rubros excluidos de las transferencias no automáticas** (Luis los revisa; ADR-0378, punto 26).
3. **Victimización** (fuente: Universidad Torcuato Di Tella): no publicó desde el informe de
   julio (subido el 5-ago). Ver sección 4.
4. **Bancos (ADEBA, ABA, ABAPPRA):** clasificados pero fuera de la postura empresaria por no
   llegar al mínimo de comunicados (ADR-0391); entran si lo llegan.

## 4. Con fecha y cargas mensuales

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

## 5. Adjudicaciones de Juan que no deciden puntaje, e ideas para más adelante

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

## 6. Hecho

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
