---
madr: 4
id: '0129'
estado: 'aceptado'
fecha: 2026-07-25
cinturon: 'gestion'
indicadores: [privatizaciones]
archivos: ['privatizaciones_novedades.json']
complementa: ['0101']
ambito: 'ITCG · `privatizaciones` · `privatizaciones_novedades.json` (nuevo)'
origen: 'Aporte externo sobre el cinturón de gestión (doc 260723)'
---

# ADR-0129 — Privatizaciones: se automatiza la detección, no la clasificación

| **Complementa** | ADR-0101 (la card publica la norma de cada etapa) |

## Contexto y planteo del problema

> "Cada una de las 4 etapas del proceso de privatización depende del dictado de
> un acto administrativo publicable, por lo tanto el indicador puede correr en
> automático y no requiere del juicio de analista que evalúe."

La primera parte es correcta: cada transición **sí** deja rastro normativo. La
segunda no se sigue de la primera.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

Un detector que, para cada una de las nueve empresas de la cartera, busca en
InfoLeg las normas del Boletín Oficial que la nombran y **marca como pendientes
de revisión** las que hablan del proceso privatizador. No toca etapas.

El resultado se publica en la card (`novedades_pendientes`) y se versiona en
`data/gestion/privatizaciones_novedades.json`, **agregado al `git add` del cron
en el mismo cambio**: un caché que no se commitea vuelve a avisar lo mismo cada
noche.

## Más información

### Limitaciones

- **Sigue sin haber fuente en vivo para la etapa.** Esto no lo resuelve y no
  pretende resolverlo: lo que elimina es el riesgo de omisión, no el juicio.
- **El filtro puede tener falsos negativos.** Una norma que avanza el proceso
  con una redacción que no use ninguno de los verbos listados no se detecta. Es
  el precio de bajar de 180 a 12, y se prefiere ese error al inverso: una lista
  que nadie lee no detecta nada.
- **La búsqueda es por nombre de empresa.** Si el Boletín nombra a una empresa
  de una forma que el término no cubre, la norma no aparece. Hay un test que
  exige que cada empresa del registro tenga término asignado, pero no puede
  verificar que el término sea el correcto.
- El detector **no distingue** una norma que crea una etapa nueva de una que
  reglamenta algo ya registrado. Las dos van a la lista; separarlas es
  justamente lo que hace el analista.

### Por qué la clasificación NO se automatiza

ADR-0101 dejó publicado un caso concreto: en Nucleoeléctrica el registro dice
*"la Res. ME 1751/2025 inició el proceso; el analista la mantiene en etapa 1
hasta que haya llamado"*. Una norma habilitaba avanzar y el equipo decidió no
hacerlo.

Automatizar la clasificación **borraría ese juicio**, que hoy está publicado y
se puede discutir, y lo reemplazaría por una regla implícita en una expresión
regular, que no se discute porque nadie la ve. La transparencia no mejoraría:
empeoraría, porque el criterio pasaría de estar escrito a estar escondido.

**Lo que sí es un problema real es la omisión**: que salga una norma y nadie la
vea. Eso sí se automatiza.

### El filtro, que es lo que hace la diferencia

La primera versión buscaba sólo el nombre de la empresa y devolvió **180
"novedades" en tres meses**. Casi todas eran trámites de rutina —designaciones,
cuadros tarifarios, licencias—: exactamente el ruido que haría que el analista
dejara de mirar la lista al tercer día.

Se exige además un **verbo del proceso**: privatiza · desestatiza ·
transferencia accionaria · venta de acciones · paquete accionario · pliego ·
licitación pública · adjudica · concurso público · sujeta a privatización.

| | |
|---|---|
| sin filtro | 180 pendientes |
| **con filtro** | **12 pendientes** |

### Validación

Entre las 12 aparece **AySA, Resolución 704/2026**, que es exactamente la norma
que el registro ya tiene anotada como el llamado a licitación por el 90%
accionario de mayo. **El detector encuentra el evento conocido**, que es la
prueba mínima que tenía que pasar.

Las otras once son candidatas reales para que el analista mire.

### Costo

El texto de una norma publicada es inmutable, así que cada norma se evalúa una
sola vez y el veredicto queda cacheado, pase o no el filtro. La ventana por
defecto es de tres meses, de modo que en régimen cada corrida procesa apenas
las normas nuevas.

El detector **no puede tumbar el indicador**: si InfoLeg no responde, el avance
se publica igual y la lista queda vacía. Lo que se pierde es un aviso, no el
dato.
