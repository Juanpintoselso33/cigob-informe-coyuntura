---
madr: 4
id: '0361'
estado: 'aceptado'
fecha: 2026-10-24
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [cepo_mulc, desregulacion_normativa, reduccion_estado, gasto_funcionamiento, fal_modernizacion_laboral, litigiosidad_laboral, rigi_inversiones, concesiones_infraestructura, asistencia_directa, protocolo_antipiquetes, libertad_opcion_salud]
archivos: ['scripts/archivo.py', 'scripts/gestion.py', '.github/workflows/mensual.yml', 'web/src/components/IndicadorTile.astro', 'web/src/components/NivelTension.astro', 'web/src/components/IndicadorModal.astro', 'web/src/components/Evolucion.astro', 'web/src/pages/[slug].astro', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'web/public/overrides.css', 'tests/test_archivo.py', 'tests/test_gestion_fal_actos.py']
relacionado: ['0228', '0347', '0359', '0189']
ambito: 'Cinturón de gestión · ITCG · edición mensual'
origen: 'Auditoría del cinturón de Gestión de la edición de septiembre de 2026 enviada por Marcos (CiGob) el 23-oct-2026 (14 observaciones), con sus propuestas de Reforma laboral (rev 2, 24-oct) y de Libertad de opción en salud. Decisiones de Juan del 24-oct-2026.'
---

# ADR-0361 — Respuesta a la auditoría del cinturón de Gestión (septiembre de 2026)

## Contexto y planteo del problema

Una auditoría externa de la edición de septiembre de 2026 encontró catorce
problemas en el cinturón de Gestión. Tres eran errores de datos o de cálculo:

- RIGI publicaba «49.766 %», que eran los millones de dólares aprobados. Ya se
  corrigió el 24-oct: la edición rehecha toma la card de la foto del mes.
- La portada y la página del cinturón mostraban números distintos: venían de
  dos ediciones distintas.
- La rama mensual mezclaba meses en sus archivos: fichas .md, robustez y CSV de
  `output/` eran de octubre.

El resto eran rótulos y textos que prometían más de lo que el número mide.
Además se encontró que la barra de Reforma laboral se pintaba verde con 59,9,
que es amarillo, y que piquetes salía fechado en 2026 con un dato de 2025.

La pregunta: qué se corrige, qué se aclara y qué se deja como está.

## Factores de decisión

- Un indicador tiene que medir lo que su nombre dice (regla del tablero).
- Lo que no se publica no se mide: no se proponen series que dependen de
  pedidos de información que nadie hizo.
- El FAL cuenta lo que rige, no lo anunciado ([[0228-el-fal-puntua-lo-que-rige-no-lo-que-se-dicto]]).
- La edición mensual se lee con el método vigente
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]), pero todos sus archivos
  tienen que salir del mismo corte de datos.

## Opciones consideradas

- Adoptar todas las propuestas de la auditoría, incluidos el FAL en 90 y las
  nuevas medidas de salud y de viales.
- Corregir lo que es error y aclarar los rótulos, sin cambiar lo que mide
  ningún indicador (elegida).
- No tocar nada hasta rediseñar el cinturón.

## Decisión

**Errores corregidos.**

- La rama mensual lleva del corte del mes todos los archivos de
  `archivo.CORTE_RAMA`, no sólo los dos JSON del sitio. Antes de publicarla,
  `archivo.py verificar` exige que nada tenga fecha posterior al mes y que la
  robustez, `output/informe.json` y las fichas sean de la misma corrida que el
  sitio. Si falla, informe.cigob.org sigue con la edición anterior.
- Un dato anual conserva su fecha en el mes rehecho (piquetes: 2025, no 2026).
- La barra y el popup de cada dimensión toman el color que calculó el pipeline.
  La tensión publicada viene redondeada y 59,9 daba 4,0, el borde del verde.
- El detector de fondos FAL reconoce la sigla suelta («Pionero FAL Liquidez»),
  no sólo «Asistencia Laboral».

**Rótulos y textos.**

- En las tarjetas de Gestión, el puntaje del índice va aparte del valor: el FAL
  muestra avance 50 y puntaje 55.
- Salud muestra el total («2,75 M de 8,33 M usuarios de prepagas») y el mes.
- Concesiones viales dice que mide adjudicación y no toma de posesión. Lleva
  como reserva que la toma consta en 7.885 de 9.133 km y que dos tramos de la
  Etapa II-B no tienen fuente oficial.
- Otros rótulos nuevos: «Inversiones RIGI aprobadas», «Juicios por riesgos del
  trabajo (SRT)» (con la feria de julio), piquetes «cortes en CABA, no
  aplicación del protocolo», desregulación «volumen, no importancia».
- Brecha, Reforma del Estado, robustez e introducción usan la redacción de la
  auditoría. Se corrige la fuente de gasto de funcionamiento.
- El gráfico de evolución dice que llega al último mes completo.

**Lo que no se adopta.**

- **FAL en 90.** Las normas de la CNV y de ARCA operativizan un régimen ya
  construido. Los bancos ofrecen cartas de intención para fondos que no
  funcionan antes del 1-dic. Queda en 50 (puntaje 55); ese día pasa a 70
  (puntaje 74). Se revisa cuando haya fondos inscriptos.
- **Salud como «porcentaje que se cambió de agente».** Esa serie no se publica.
  Con los padrones sólo hay una cota anual («al menos 5,6 %» en 12 meses), que
  queda en la ficha.
- **Viales en 93 % (adjudicación más posesión) o contra la red nacional.** El
  93 % da el mismo puntaje y depende de prensa para dos tramos. La red nacional
  cambia lo que mide el indicador.
- **Convenios colectivos en Reforma laboral.** La lista de los 446 no está
  publicada y no hay ningún convenio adecuado comprobado: el indicador daría 0.
  Se suma cuando exista la lista.
- **Asistencia directa**: cambia sólo la unidad, a lo que la fórmula calcula. Su
  saturación (98,3 % en 2023) sigue abierta, como en
  [[0189-si-no-puntua-no-se-muestra]].

### Consecuencias

- Ningún puntaje cambia por este ADR. Lo que cambia en la edición de septiembre
  es lo que ya había movido RIGI.
- El rearmado de la rama mensual corre dos scripts más (unos segundos) y puede
  fallar si un archivo no es del corte, en vez de publicar mezclado.

### Confirmación

- `tests/test_archivo.py`: el control del corte único rompe a propósito un
  archivo por vez y tiene que verlo. La fecha del dato anual tiene su prueba.
- `tests/test_gestion_fal_actos.py`: el detector ve «… FAL» y no «FALCON».

## Pros y contras de las opciones

- Adoptarlo todo: responde a la letra de la auditoría, pero sube el FAL por
  anuncios y publica medidas sin fuente.
- Corregir y aclarar: cierra los errores y deja cada número diciendo lo que es,
  sin inventar series.
- No tocar: deja publicados errores ya identificados.

## Más información

El seguimiento observación por observación está en
`docs/auditorias/2026-10-marcos-cinturon-gestion.md`
([[0347-el-monitor-se-publica-como-informe-mensual]]).
