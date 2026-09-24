---
madr: 4
id: '0311'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'transversal'
indicadores: [idc, iai, votometro_ventaja_lla, inseguridad, icc_utdt, despacho_cemento, tcrm, asistencia_directa, movilizacion_cepa]
archivos: ['web/src/components/NivelTension.astro', 'web/src/components/Hero.astro', 'web/src/components/Bluf.astro', 'web/src/lib/datos.ts']
relacionado: ['0194', '0204', '0237', '0320', '0337']
ambito: 'Titular del Hero (tensión general) y `LABELS` de `datos.ts` — cómo se presenta el número, no cómo se calcula'
origen: 'Apuntes de Juan del 15-sep-2026 (#monitor-de-proyecto-de-gobierno): sacar la escala de 10 del titular y las siglas internas de los rótulos'
---

# ADR-0311 — El titular sin escala y los rótulos sin siglas internas

## Contexto y planteo del problema

Dos pedidos del mismo hilo de comunicación del Monitor, ambos sobre cómo se
lee el número antes de bajar al detalle:

1. **La tensión general** (el score global del Hero) se mostraba con la misma
   barra que un cinturón o un indicador: "3,7**/10**" y rótulos "0" / "10" a
   los extremos de la pista. Un "/10" en el titular sugiere una escala
   científica que el método no promete —10 no es un tope físico, es el rango
   de la matriz de tensión— y en el número más visible del sitio ese matiz
   importa más que en cualquier otro lugar.
2. **Los rótulos de `LABELS`** repetían la sigla interna del proyecto entre
   paréntesis después de ya haber traducido el concepto: "Capacidad prestable
   (IdC)", "Confianza del consumidor (ICC)". La sigla no agrega información
   para quien lee la card —nombra el método, no la cosa— y compite con el
   criterio de CiGob de "técnico sin ser opaco" (docs del marco de Luis,
   sección C de los apuntes): traducir sin perder precisión, no acumular
   jerga.

Las dos cosas comparten un mismo hilo: qué se le muestra al lector en la capa
más reducida (el titular, la card) y qué se reserva para cuando baja al
detalle (el cinturón, la ficha).

## Factores de decisión

- El semáforo, la lectura cualitativa y la posición del marcador en la barra
  no pueden perder información — sólo se saca el número de la escala.
- La escala SÍ sigue valiendo a nivel de cinturón, dimensión e indicador: ahí
  es donde el lector explícitamente baja a buscar el número exacto.
- Una sigla se saca sólo si es puramente interna del proyecto o del método
  (no tiene reconocimiento público) y el rótulo ya la tradujo en texto plano.
- Una sigla que es el nombre público de la cosa (DNU, RIGI, LLA, PJ, CABA) o
  que da trazabilidad de fuente (ACLED, CEPA) se queda — sacarla la haría
  menos clara, no más.
- Ningún cambio de rótulo puede dejar un indicador sin entrada en `LABELS`
  (gate de `tests/test_web_labels.py`) ni desalinear ficha e indicador
  (`tests/test_la_ficha_no_se_queda_atras.py`).

## Opciones consideradas

**Para el titular:**
1. Sacar `TENSION_MAX` del componente entero — rompe la escala también en
   cinturón/dimensión/indicador, donde sí hace falta.
2. Un componente nuevo sólo para el Hero, duplicando la barra.
3. Una prop `mostrarEscala` en `NivelTension.astro` (default `true`), que el
   Hero apaga.

**Para los rótulos:**
1. Sacar toda sigla de `LABELS` sin excepción — pierde trazabilidad de fuente
   donde el indicador no tiene ficha propia (`protestas_caba`, sin ficha:
   ACLED sólo vive en el rótulo).
2. Aplicar el criterio caso por caso: sigla interna afuera, sigla pública o de
   fuente adentro.

## Decisión

**Titular:** opción 3. `NivelTension.astro` suma la prop `mostrarEscala`
(default `true`); con `false` no dibuja el "/10" del valor ni los rótulos 0/N
bajo la pista, pero conserva la barra, los tramos de color y el marcador —lo
que cambia es sólo el número de la escala, no la posición relativa. Sólo el
Hero (`tensión general`) la apaga; `CinturonCard.astro`, `[slug].astro`
(detalle de cinturón) e `IndicadorModal.astro` la dejan en `true`.

La síntesis automática de `Bluf.astro` ("La tensión global es X/10") citaba el
mismo número que el titular ya no muestra con esa forma: pasa a "La tensión
global es X." sin tocar las frases por cinturón, que sí conservan su "/10"
porque las cards de cinturón sí publican la escala.

**Rótulos:** opción 2, aplicada en `LABELS` de `datos.ts`:

| Antes | Después | Motivo |
|---|---|---|
| Capacidad prestable (IdC) | Capacidad prestable | IdC es sólo la clave interna |
| Inversión física (IAI) | Inversión física | ídem |
| Ventaja LLA−PJ (Votómetro) | Ventaja LLA−PJ | "Votómetro" nombra el método, no el dato; LLA y PJ se quedan: son las siglas públicas de las fuerzas |
| Victimización (IVI) | Victimización | IVI es la clave interna |
| Confianza del consumidor (ICC) | Confianza del consumidor | ídem |
| Construcción (ISAC) | Construcción | ídem |
| Tipo de cambio real (TCRM) | Tipo de cambio real | ídem |
| Asistencia directa (TDPS) | Asistencia directa | ídem |
| Tensión social (CEPA, interno) | Tensión social (CEPA) | se saca "interno" (ya lo explica `descripciones.ts`); CEPA se queda porque es la única trazabilidad de fuente que tiene este indicador (sin ficha propia) |

Se dejan sin tocar, deliberadamente: `Ratio DNU / leyes` y `Inversiones RIGI`
(DNU y RIGI son los nombres públicos, no abreviaturas de método) y
`Protestas en CABA (ACLED)` (CABA es el lugar; ACLED es la única fuente
citada para ese indicador, que no tiene ficha propia en `fichas.ts`). Las
siglas de los cuatro índices paramétricos (ITCM, ITCG, ITCIS, ITCP) en
`config.py:SIGLAS_PUBLICAS` no se tocan: son identificadores con su propio
test (`tests/test_siglas_publicas.py`), no rótulos de indicador.
`web/src/lib/fichas.ts` y `descripciones.ts` no se reescriben: ahí la sigla
es parte del registro metodológico (fichas) o aparece ya explicada en la
misma oración (descripciones), que es exactamente "técnico sin ser opaco".

### Consecuencias

- El número más visible del sitio (tensión general) ya no implica una escala
  de 0 a 10 que el método no necesita para leerse: el color y la lectura
  cualitativa hacen ese trabajo. El lector que quiere el número exacto lo
  encuentra un clic abajo, en la card del cinturón.
- Nueve rótulos quedan más cortos y sin jerga interna, sin perder trazabilidad
  de fuente en los dos casos donde esa trazabilidad no vive en ningún otro
  lado (CEPA, ACLED).
- `aria-label` de la barra sin escala deja de decir "de 10": sigue anunciando
  el valor y la lectura cualitativa, no un número sin contexto.

### Confirmación

`tests/test_web_labels.py` y `tests/test_la_ficha_no_se_queda_atras.py` en
verde tras el cambio de `LABELS` (los nueve indicadores conservan entrada y
ficha coherente). `npx tsc --noEmit` y `npm run build` sin errores; el HTML
generado se inspeccionó a mano: el Hero no emite `/10` ni el bloque de
rótulos 0/10, y `[slug].astro` (detalle de cinturón) sigue emitiéndolos.

## Pros y contras de las opciones

- **Titular — prop en el mismo componente:** una sola implementación de la
  barra sigue sirviendo a los tres niveles; el costo es una prop más que
  documentar.
- **Rótulos — caso por caso:** más trabajo que un barrido ciego, pero es lo
  único que no rompe la trazabilidad de los dos indicadores sin ficha propia.

## Más información

- ADR-0194 y ADR-0204: la barra de tensión y por qué es una pista recta con
  tramos de color, no un velocímetro.
- ADR-0237: el pie del titular nombra al cinturón dominante, no sólo al
  barbarismo — este ADR no toca esa pieza.
- Apuntes de Juan, 15-sep-2026 (`#monitor-de-proyecto-de-gobierno`): pedido
  original de sacar la escala y las siglas innecesarias.
