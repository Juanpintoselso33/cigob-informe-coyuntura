# SDD ledger — plan: projects/informe_coyuntura/docs/superpowers/plans/2026-08-08-semaforo-cuatro-colores.md

Rama: semaforo-cuatro-colores (desde 14a6d27 en main)
Acuerdo con el usuario: tareas 1-7 en la rama; la 8 (pipeline + snapshot +
produccion) se corre en main despues del merge, para no chocar con el cron
nocturno en web/src/data/informe.json.
Supuesto declarado: el ITVC va con la vara unificada (verde = tension 4,
cortes 105/95/85). Si CIGOB prefiere la excepcion, son dos lineas en
color_de_indice_base100 mas el texto de ADR-0181.

Task 1: DEFECTO DEL PLAN detectado en ejecucion. Los comentarios de codigo
  citan ADR-0181/0182 y tests/test_adr_format.py exige que todo ADR citado
  desde codigo exista, asi que el implementador creo dos ADR stub (43 y 37
  lineas, slugs distintos a los del plan) para que pasara el gate. Los ADR
  reales son Task 7 y llevan las tablas de efecto honesto. Ruling: los stubs
  quedan como placeholder; Task 7 los REESCRIBE completos conservando los ids
  0181/0182 y renombrando los archivos a los slugs del plan.
Task 1: review limpia (spec OK, calidad aprobada). Resueltos los 2 items
  "cannot verify": (a) orden TDD no se ve en un commit unico, pero el reporte
  trae RED/GREEN consistentes y el plan pedia un solo commit -> no es gap;
  (b) convivencia con verdictDeCinturon -> ruling: NO se unifica. Ese chip sale
  del enum `estado`, que alimenta BLUF, panel de tension, cinturonesRojos y
  score_global; tocarlo seria cambio de indice, prohibido por la spec 4.4.
  Declarado en Global Constraints del plan.
Task 1: minor (deferred): return inalcanzable en color_de_tension (solo dispara
  con NaN, devolveria "rojo" en vez de fallar).
Task 1: minor (deferred): unificar el chip del cinturon con el color de su
  indice — pendiente real, fuera de alcance de este plan.
Task 1: complete (commits 14a6d27..72892a1, review clean)
Task 2: DEFECTO DEL PLAN confirmado. test_reversibilidad_en_las_57_tablas,
  como lo escribi, era matematicamente insatisfacible: exigia que los DOS
  bordes de un tramo puntuaran el corte de SU color, cuando los bordes de un
  tramo interior son los cortes de sus dos VECINOS (cepo_mulc amarillo (14,20):
  puntaje(14)=60, puntaje(20)=40). El implementador lo detecto con prueba
  empirica (116/286 chequeos fallando en 57/57 tablas) y lo reescribio a
  "cada borde puntua ALGUN corte". Revisor independiente lo verifico a mano y
  confirmo que conserva poder de deteccion. Ruling: la correccion queda.
Task 2: segunda desviacion verificada correcta — deriva los cortes de
  CORTES_SEMAFORO en vez del segundo literal (60,40,20) que traia mi Step 3,
  que violaba la propia restriccion del plan.
Task 2: verificado por el controlador que los 2 fallos de la suite
  (test_el_valor_vigente_del_ipi_no_cambio, error en
  test_gestion_privatizaciones_novedades) son PREEXISTENTES: reproducen con
  parametrica.py revertido al base y test_semaforo.py borrado. Ajenos a este
  trabajo. Nota: hay un stash ajeno en el repo (stash@{0} adr-0048-wip).
Task 2: minor (deferred): redondeo de umbrales a 4 decimales, no pineado.
Task 2: minor (deferred): el docstring de umbrales_en_unidad no repite la
  convencion de bordes (low exclusivo / high inclusivo).
Task 2: fix round 1/5 (1 addressed, 0 open — rama muerta de reordenamiento
  reemplazada por guarda explicita con ValueError; commits 174eed4..f93c673)
Task 2: complete (commits 08d87c5..f93c673, review clean)
Task 3: review spec NO / calidad Needs work. 2 Critical + 2 Important:
  C1 tension del ITVC sin clampear (venia de MI codigo del plan): publicaba
     21,6 en mora_familias y -3,0 en patentamiento_motos. itvc.tension_de_itvc()
     ya existe y clampea. El color no se ve afectado (los cortes estan dentro
     de [0,10]), por eso ningun test lo agarro.
  C2 el reporte afirmaba que el campo `semaforo` de idc era dato muerto. ES
     FALSO: publicar.py:454 lo lee y llega a produccion via aporte_input_txt e
     IndicadorModal.astro:133 — hoy sale "(amarillo)" en el modal. Funciona
     solo por orden de ejecucion.
  I1 6 de 7 tests nuevos rojos en el arbol commiteado, y quedarian rojos
     durante Tasks 4-7. Los tests leian el snapshot commiteado, que no se
     regenera hasta Task 8. DEFECTO DEL PLAN mio.
  I2 colision de nombres: se renombra el campo del colector a banda_idc.
  Ruling: los 4 van al fix round 1. Las 2 divergencias declaradas por el
  implementador (wrappers de color, _INDICE_DE_CINTURON) verificadas correctas
  y se conservan.
Task 3: verificado por el controlador que los 2 fallos extra que reporto el
  implementador (test_gate_bloqueante_vs_demora) eran TRANSITORIOS por el
  snapshot regenerado a mitad de corrida: con el arbol limpio pasan 4/4.
Task 3: fix round 1/5 (4 addressed, 0 open — C1 clamp via itvc.tension_de_itvc
  (6 indicadores vuelven a [0,10], colores sin cambio), C2/I2 rename a
  banda_idc, I1 tests en memoria sobre copia + invariancia directa y fixture
  congelado eliminado; commits 3c99d3b..2253c13)
Task 3: minor (deferred): output/cache/macro.json conserva la clave vieja
  `semaforo` hasta la proxima corrida de macro.py; degrada a parentesis vacio,
  no a un valor equivocado. Se cura solo en Task 8.
Task 3: complete (commits f93c673..2253c13, review clean)
Task 4: review spec OK / 1 Critical real: faltaba
  .cg-verdict.naranja .cg-verdict-dot (las otras tres estan en dashboard.css
  346-348). Va al fix round 1, y se extiende el test para que cubra el set
  completo por color, no el subconjunto que el brief enumeraba.
Task 4: FALSO POSITIVO adjudicado por el controlador. El revisor (haiku)
  calculo 3,47:1 de contraste para #7C2D12 sobre #FFEDD5 y acuso al
  implementador de afirmar WCAG AA en falso. Recalculado: naranja 8,18:1,
  verde 8,30:1, amarillo 7,79:1, rojo 8,20:1. El revisor se equivoco y el
  implementador tenia razon. Ruling: no se cambia el color.
Task 4: FALSO POSITIVO adjudicado: "claim de fallo preexistente sin verificar"
  — ya lo verifico el controlador revirtiendo los archivos del semaforo.
Task 4: minor (deferred): los regex del test verifican presencia de hex, no
  validez (--naranja: #ZZZZZZ pasaria).
Task 4: fix round 1/5 (1 addressed, 0 open — regla del punto naranja + test de
  completitud, dientes verificados empiricamente por el revisor borrando una
  regla; commits 88ef1f6..bc08b4f)
Task 4: complete (commits 2253c13..bc08b4f, review clean)
Nota: .superpowers/sdd/.gitignore quedo modificado por el propio script
  review-package (amplia *.diff a *). Es scratch, se commitea al final.
Task 5: review spec OK / calidad Needs work. 2 Important, ambos heredados de
  MI brief:
  (a) el fallback "amarillo" de semaforoDe fabrica una senal. asistencia_directa
      es el unico que cae ahi y ADR-0100 lo enmarca como promesa cumplida
      (TDPS 100%, fuera del score por saturado). Pintarlo amarillo afirma algo
      falso e indistinguible de un amarillo real. Fix: el dot se renderiza solo
      si hay color; el contrato de semaforoDe no cambia. NO se cura en Task 8:
      _semaforos() nunca le va a asignar bloque.
  (b) test_ningun_corte_del_semaforo_hardcodeado_en_ts solo prohibia los cortes
      base-100 (95/90/105/85) y dejaba fuera 60/40/20, que es la escala de
      ITCM/ITCG/ITCP. Fix: testear el invariante real — ninguna linea .ts que
      mencione un color puede tener ademas una comparacion numerica.
Task 5: la divergencia declarada (overrides.css, flexbox de .cg-tile-head)
  verificada real, minima y con convencion existente. Se conserva.
Task 5: fix round 1/5 (2 addressed, 0 open — dot condicionado a que exista
  color, y test del invariante real con dientes verificados empiricamente por
  el revisor; commits f27e7f3..e6730ee)
Task 5: PARKED para Task 6: el fallback "amarillo" sigue dentro de semaforoDe
  por diseno (mantiene el contrato de 4 colores). Cualquier consumidor NUEVO
  que llame semaforoDe(x) sin chequear antes x.semaforo?.color reintroduce la
  senal fabricada en ese call site. Task 6 agrega consumidores.
Task 5: complete (commits bc08b4f..e6730ee, review clean)
Task 6: review spec OK / calidad aprobada. Revisor verifico contra el HTML
  construido en dist/, no contra el reporte: apertura_comercial 4 filas,
  costo_financiamiento_tesoro 6 filas en orden naranja/amarillo/verde/amarillo/
  naranja/rojo (no monotono confirmado), alquiler_real sin las tres secciones.
  Las 2 divergencias declaradas (clases CSS inexistentes en el brief, chip en
  span y no en td) verificadas correctas.
Task 6: minor (deferred): la referencia ADR-0181/0182 quedo en un comentario
  HTML de template, no de frontmatter. Hoy no llega al navegador porque
  compressHTML lo elimina (verificado empiricamente en dist/), pero el resto
  del repo confina las citas de ADR al frontmatter justamente para no depender
  de un flag del compilador. La regla editorial de no mostrar ADR en fichas
  publicas tiene gate propio. Fix de una linea, para la review final.
Task 6: complete (commits e6730ee..8086782, review clean)
Task 7: review spec OK / calidad aprobada. Revisor (opus) recalculo las tres
  correcciones a la spec y confirmo las tres, derivando los cruces del no
  monotono a mano. Verifico que el efecto honesto muestra las dos mitades.
Task 7: 2 Important al fix round 1:
  I-1 ADR-0181 nombraba un enum inexistente. ERROR MIO, venia de las Global
      Constraints del plan: _estado() emite estable/en_tension/tensionado, no
      alerta/critico, y score_global NO se alimenta de estado (es al reves).
  I-2 ADR-0183 le atribuia a ADR-0045 una prohibicion que no tiene: 0045 ES
      una recalibracion de bandas defendida como legitima.
Task 7: HALLAZGO AJENO AL PLAN, verificado por el controlador. Bug vivo del
  sitio: verdictDeCinturon (datos.ts:231-235) ramifica sobre "critico"/"alerta"
  y ninguno de los dos se produce nunca. El peor estado (tensionado) cae al
  else y pinta AMARILLO; cinturonesRojos (datos.ts:526) es estructuralmente
  siempre 0 — el sitio no puede mostrar un cinturon en rojo. Hoy
  vida_cotidiana esta tensionado y se ve amarillo. Preexistente y FUERA DE
  ALCANCE (tocarlo es cambio de indice), pero el semaforo lo hace visible: el
  indice ITVC ahora pinta naranja mientras el chip dice amarillo. Queda
  declarado como pendiente en ADR-0181 y se reporta al usuario.
Task 7: minors (deferred): claim R-vs-A/D del rename en el reporte; atribucion
  brief-vs-spec en el reporte; fecha del ADR pegada al ITCP 66,9; serie
  bicameral de 0048 citada en presente con 2 meses de atraso; histeresis en
  Opciones sin entrada en Pros y contras.
Task 7: fix round 1/5 (2 addressed, 0 open — I-1 enum corregido y pendiente
  declarado en Consecuencias; I-2 cita cambiada a ADR-0105, que el revisor
  leyo completo y confirmo que SI sostiene la regla; commits 2ba34e0..8b4d9cf)
Task 7: complete (commits 8086782..8b4d9cf, review clean)
Task 9 (AGREGADA a pedido del usuario, no estaba en el plan): arreglar
  verdictDeCinturon. Evidencia que zanja el mapeo: generar_informe.py:192 ya
  hace {"estable":"green","en_tension":"yellow","tensionado":"red"} para el
  informe markdown. La web viene contradiciendo al informe que genera el mismo
  pipeline. No es cambio editorial: es alinear. No se toca UMBRALES ni
  _estado() ni ningun score.
Task 9: review spec OK / calidad aprobada. 1 Important: los dos tests
  bidireccionales que pedia el brief NO atrapan la regresion (verificado
  empiricamente: sacando la rama tensionado ambos pasan); solo la atrapa el
  tercer test que el implementador agrego por iniciativa propia. Fix: que la
  asercion sea el MAPEO, derivado del dict de emojis de generar_informe.py:192.
Task 9: el BLUF confirmado desde el HTML construido:
  "Vida cotidiana esta en zona critica; Con una tension global de 3,4/10,
   vida cotidiana es el cinturon mas exigido del tablero (6,9/10); ..."
  Dos defectos: "Con" mayuscula a mitad de frase (Bluf.astro:27 capitaliza
  asumiendo que su clausula es siempre frases[0], y la 36 une con "; ") y el
  mismo cinturon nombrado en dos clausulas seguidas. Bug latente que NUNCA
  pudo dispararse porque cinturonesRojos era estructuralmente 0. Va al fix:
  ampliacion de alcance deliberada, porque sale a la home al mergear.
PENDIENTE tras Task 9: ADR-0181 declara el bug de verdictDeCinturon como
  "pendiente, fuera de alcance". Al arreglarlo esa frase queda falsa. Hay que
  actualizar ese parrafo antes del merge.
Task 9: fix round 1/5 (2 addressed, 0 open — el test parsea el dict canonico
  de generar_informe.py en vez de duplicarlo, dientes verificados en ambas
  direcciones por el revisor; BLUF capitaliza una sola vez en el join y no
  repite el nombre. Caso sin rojos verificado construyendolo y restaurando el
  snapshot byte a byte; commits f333b0c..29d698e)
Task 9: minor (deferred): el cuerpo del commit 29d698e tiene una frase
  confusa. No se enmienda.
Task 9: minor (deferred): el caso multi-rojo con masTenso adentro no se puede
  construir con los datos de hoy (solo un cinturon puede llegar a tensionado).
Task 9: complete (commits 8b4d9cf..29d698e, review clean)
Task 10: complete (commits 29d698e..c8e4266, review clean). El revisor
  recalculo el conteo de tests colectando (28 hoy, 26 antes del fix) y releyo
  0182/0183 completos confirmando que no quedaron pasajes obsoletos.
