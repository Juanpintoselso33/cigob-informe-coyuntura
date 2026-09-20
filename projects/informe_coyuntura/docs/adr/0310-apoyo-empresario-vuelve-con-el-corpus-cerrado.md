---
madr: 4
id: '0310'
estado: 'aceptado'
nota_estado: 'Aceptado (supersede al ADR-0246: se cumple su condición de reingreso)'
fecha: 2026-09-14
cinturon: 'politica'
indicadores: [apoyo_empresario]
archivos: ['scripts/itcp.py', 'scripts/politica.py', 'web/src/lib/fichas.ts', 'data/politica/apoyo_empresario_codificacion.json', 'tests/test_apoyo_corpus_cerrado.py']
supersede: ['0246']
relacionado: ['0131', '0149', '0150', '0245', '0332', '0334']
ambito: 'Cinturón política · ITCP · `apoyo_empresario` · reingreso al score y qué significa «corpus cerrado»'
origen: 'Se vació la cola de comunicados pendientes y quedó por decidir si se cumplía la condición de reingreso de ADR-0246'
---

# ADR-0310 — El saldo empresario vuelve al ITCP con el corpus cerrado

## Contexto y planteo del problema

ADR-0246 sacó el indicador del score porque el saldo −0,429 salía de siete
comunicados codificados con catorce detectados sin codificar: medía qué se
alcanzó a clasificar. Dejó una condición de reingreso en cinco partes: corpus
cerrado y publicado, criterios fijados de antemano, doble codificación con
control de concordancia, inventario completo y card y serie sobre la misma
cohorte.

El 14-sep-2026 la cola tenía 23 comunicados de la UIA (abril a septiembre). Se
codificaron 22 —el 23º era la misma nota con otro slug— con el protocolo de la
pasada completa: dos codificadores IA ciegos entre sí, sólo el manual v2 y el
texto crudo, kappa 0,850 en postura y 0,933 en destinatario, dos desacuerdos
adjudicados con los criterios generales ya escritos. El saldo pasó a −0,111
con el inventario en cero.

Cuatro partes de la condición quedaban cumplidas. La quinta, «corpus cerrado»,
nunca se había definido, y es la que importa: el detector encuentra
comunicados nuevos casi todas las semanas, así que el corpus no se cierra
nunca en el sentido literal. Reponer el indicador sin definirla es volver a la
situación de ADR-0246 la próxima vez que alguien no llegue a codificar.

## Factores de decisión

- El saldo no puede volver a calcularse sobre un inventario incompleto.
- Un dato que no avanza tiene que verse viejo, no parecer fresco.
- Card y serie siguen saliendo de una sola implementación (gate G3).
- El trabajo pendiente tiene que llegar a alguien, no quedar en un JSON.

## Opciones consideradas

1. Reponerlo sin más: el inventario está en cero hoy.
2. Reponerlo y suspenderlo de nuevo cada vez que haya pendientes.
3. Reponerlo con corte de serie: el cálculo llega hasta el último mes con el
   inventario completo.

## Decisión

Opción 3. «Corpus cerrado» deja de ser un estado del archivo y pasa a ser una
regla del cálculo: **la serie se calcula sólo hasta el último mes con el
inventario completo y comprobado.** Tres cosas la frenan antes del mes en curso:

- un comunicado pendiente: corta en el mes anterior al más viejo;
- un pendiente con fecha inválida o faltante: no se sabe dónde cae, así que
  corta en el mes anterior al actual;
- un inventario sin comprobar: `inventario_verificado` guarda la última
  corrida en la que respondieron **las dos** cámaras, y la serie no pasa de ese
  mes. Sin esto el detector fallaba abierto: con la UIA caída, sus comunicados
  nuevos no existían para el cálculo y el saldo avanzaba igual.

Como la card es el último punto de la serie, corta igual; y cuando está
cortada se declara `desactualizado` y su detalle cuenta sólo la ventana del
punto publicado.

Tres piezas acompañan la regla:

- `apoyo_empresario` sale de `INDICADORES_SUSPENDIDOS`: vuelve con su 50% de
  diseño de la dimensión de sector privado, que el mecanismo de ADR-0245 dejó
  escrito durante la suspensión.
- Cada pendiente se registra como cotejo manual y llega a #monitor-alertas en
  su hilo (ADR-0309).
- El detector corre **antes** que la card en `politica.main`. Estaba al final:
  un comunicado detectado esa noche habría cortado la serie —que
  `descargar_series` calcula después, con el inventario ya actualizado— pero no
  la card, y el gate G3 las habría encontrado distintas.

### Consecuencias

- El ITCP incorpora la tensión con el sector privado organizado que había
  dejado de medir. Con el saldo en −0,111 el componente puntúa en la banda
  moderada, no en la más baja como con −0,429.
- Un pendiente sin codificar congela el dato en vez de sesgarlo, y la card lo
  declara desactualizado desde el primer día. Si se deja más de 110 días, G2
  **corta la publicación entera**: es un freno duro, con meses de avisos en
  #monitor-alertas antes de llegar a él.
- Límites conocidos, sin resolver a propósito: el invariante card↔serie
  depende del orden nocturno (el detector antes que `descargar_series`); una
  corrida manual en orden inverso puede desalinearlos hasta la corrida
  siguiente. Y un corte que deje la serie con un solo punto lo taparía el
  histórico de publicación, que completa las series de menos de dos puntos:
  haría falta un pendiente de enero de 2024.
- La dimensión de sector privado vuelve a tener dos componentes; deja de
  depender de uno solo.

### Confirmación

`tests/test_apoyo_corpus_cerrado.py`: sin pendientes la serie llega al mes en
curso; un pendiente corta la serie y la card en el mes anterior (también en
enero, cruzando el año); una fecha inválida corta igual; un inventario sin
comprobar no avanza; sólo una corrida con las dos cámaras lo comprueba; la card
cortada se declara desactualizada y no cuenta lo posterior; cada pendiente sale
como cotejo manual; el detector corre antes que la card; y el indicador ya no
está suspendido. Mutar el corte para que incluya el mes del pendiente hace
fallar dos pruebas. Codex revisó el diff y encontró el detector que fallaba
abierto, las fechas sin validar y el `desactualizado` que nunca se prendía.

## Pros y contras de las opciones

- **1. Sin más:** vuelve a ADR-0246 en cuanto aparezca el primer pendiente.
- **2. Suspender cada vez:** el índice cambiaría de composición cada semana
  por un motivo operativo, y la serie del ITCP dejaría de ser comparable.
- **3. Corte de serie:** el índice mantiene su composición; lo que no se
  codificó no entra, y el retraso queda a la vista con la fecha del dato.

## Más información

- ADR-0246: la suspensión y su condición de reingreso.
- ADR-0245: suspender libera el peso sin reescribir la tabla de diseño.
- ADR-0131 y ADR-0150: protocolo de codificación y concordancia.
- La tanda del 14-sep-2026 está documentada en `_meta.tandas` de
  `apoyo_empresario_codificacion.json`.
