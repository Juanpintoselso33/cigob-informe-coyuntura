---
madr: 4
id: '0095'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
indicadores: [brecha_obra_publica]
corrige: ['0088']
ambito: 'ITCP · `brecha_obra_publica` · validación externa'
origen: 'Observación del editor: "quedó descalzadísimo de su contraste externo"'
---

# ADR-0095 — La brecha de obra pública cambia de signo según el gobierno

| **Corrige** | ADR-0088 (afirmó que la validación del indicador era sólida sin haber mirado el efecto sobre el índice) |

## Contexto y planteo del problema

Cerrada la auditoría del cinturón, el editor observó que el ITCP había quedado
desalineado de su validación externa. Tenía razón:

| | |
|---|---|
| ITCP ↔ EPU Argentina, antes de la auditoría | **−0,599** |
| ITCP ↔ EPU Argentina, después | **−0,372** |

Un tercio de la validez convergente, perdido. **`validacion_externa.py` corrió
después de cada cambio, pero nadie miró el resultado** — el mismo defecto que la
auditoría macro había marcado como "uso asimétrico de la validación externa":
se la invoca cuando confirma y se la ignora cuando incomoda.

Un leave-one-out sobre la reconstrucción aisló la causa de inmediato:

| reconstrucción | r con EPU |
|---|---|
| índice completo | −0,372 |
| **sin `brecha_obra_publica`** | **−0,589** |
| sin `desafios_legislativos` | −0,297 |
| sin `veto_quorum` | −0,416 |
| sin `cohesion_bloque` | −0,271 |

Toda la caída la produce el indicador nuevo de la dimensión empresaria. Medido
solo, correlaciona **+0,291** con el EPU: el signo contrario al que el índice
necesita.

Antes de tocarlo se descartó que fuera un problema de métrica. Los tres
candidatos disponibles en la misma fuente fallan igual sobre 2024-2026:

| candidato | r del puntaje con EPU |
|---|---|
| brecha de expectativas (el elegido) | +0,304 |
| atrasos en la cadena de pagos, obra pública | +0,499 |
| atrasos, brecha pública − privada | +0,488 |

La pregunta de fondo —¿la tensión con un sector que depende del gasto público
resta capital político, o lo demuestra?— se contestó con los 100 meses de serie
disponibles, midiendo el indicador contra el EPU **por presidencia**:

| gobierno | r del puntaje con EPU | n |
|---|---|---|
| Macri (desde nov-2017) | **−0,562** | 21 |
| Alberto Fernández | **−0,643** | 46 |
| **Milei** | **+0,326** | 31 |

**El indicador está correctamente orientado durante 67 meses y dos gobiernos, y
se invierte sólo con el actual.**

Eso descarta un error de diseño y da la explicación. Para las administraciones
anteriores, la tensión con las empresas que dependen del Estado era un
**síntoma** de gobierno en dificultades, y como tal acompañaba a la
incertidumbre de política. Para la actual, el recorte de la obra pública **es el
programa de gobierno**: ejecutarlo reduce la incertidumbre sobre la política
económica —el ancla fiscal se vuelve creíble— al mismo tiempo que maximiza la
tensión con el sector.

El caso testigo es 2024: el indicador marcó **−29,8**, el peor valor de sus diez
años de serie, y puntuó 10 sobre 100. Fue el año de la Ley Bases, con el EPU en
su nivel más bajo del período. **El indicador dijo "tensión máxima" exactamente
cuando el Gobierno estaba en su mejor momento.**

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

**El indicador se mantiene puntuando con su 15%, y el hallazgo se publica.**
Decisión editorial explícita, tomada sobre tres opciones planteadas: retirarlo a
contexto (habría devuelto la correlación a −0,589), reducirle el peso, o
mantenerlo y declarar todo.

Se descartó reducir el peso por una razón de método: **mover un peso para que un
test dé mejor es exactamente lo que ADR-0045 prohíbe hacer con las anclas**, y
la prohibición vale igual acá.

Lo que se publica:

- **La card de validación externa muestra el contrafáctico**: −0,372 con la
  dimensión empresaria y −0,589 sin ella, con la explicación de por qué el EPU
  no cubre esa dimensión. El número no se esconde ni se maquilla.
- **La ficha del indicador abre sus limitaciones con la dependencia de régimen**,
  con los tres coeficientes y el caso de 2024.
- **El texto del modal lo advierte antes del dato**, no sólo la ficha —
  aprendizaje de ADR-0093: la salvedad que vive donde nadie la lee no cumple su
  función.
- **El cálculo por gobierno queda en el pipeline**
  (`validacion_externa._corr_brecha_por_gobierno`), no como una cuenta de una
  sola vez: si el patrón cambia, el informe se entera.

## Más información

### Lo que este ADR admite sobre el anterior

ADR-0088 presentó la validación del indicador contra el Índice Construya
(+0,79 en niveles, +0,47 en diferencias) como evidencia de solidez, y lo es —
pero es validación **del indicador**, no del efecto de incorporarlo **al
índice**. Nunca se miró lo segundo. Son dos preguntas distintas y el ADR trató
la primera como si respondiera las dos.

La validación externa del índice debería revisarse en cualquier cambio de
composición, no sólo cuando se cambia una banda. Queda como práctica.

### Limitación que queda abierta

El índice puntúa esta tensión **como costo**. Los datos de este período sugieren
que para este gobierno es un precio deliberado, y el indicador no distingue una
cosa de la otra — ninguna fuente permitiría distinguirlas automáticamente. La
consecuencia práctica está escrita en la ficha: leer este componente junto con
lo que el Gobierno consiguió en el mismo período, no de forma aislada. La card
de lectura por partes (ADR-0094) existe justamente para eso.
