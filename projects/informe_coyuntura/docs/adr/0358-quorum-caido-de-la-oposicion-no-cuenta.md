---
madr: 4
id: '0358'
estado: 'aceptado'
fecha: 2026-10-15
cinturon: 'politica'
indice: 'ITCP'
indicadores: [veto_quorum]
archivos: ['scripts/politica.py', 'scripts/publicar.py', 'data/politica/sesiones_minoria_convocante.json', 'tests/test_quorum_convocante.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0091', '0308', '0313']
ambito: 'ITCP · `veto_quorum` · registro de convocantes'
origen: 'Juan, 15-oct-2026, tras caer sin quórum la sesión opositora por el DNU 70/2023: «hagámoslo sí, porque está mal esto»'
---

# ADR-0358 — Una sesión caída que pidió la oposición no cuenta como Congreso trabado

## Contexto y planteo del problema

`veto_quorum` («Sesiones caídas por falta de quórum») mide qué parte de las
sesiones convocadas en Diputados queda en minoría. Menos es mejor para el
gobierno: una sesión que no arranca se lee como un oficialismo que no logra
reunir a la cámara.

El 15-oct-2026 la oposición pidió una sesión especial para derogar el DNU
70/2023 y no la pudo abrir: 121 presentes de 129 necesarios. Fue una victoria
del oficialismo y sus aliados, que se quedaron afuera. El indicador la contó al
revés: pasó de 1 de 10 sesiones caídas (10 %) a 2 de 11 (18,2 %), y la otra
caída de la ventana, la del 23-jun-2026, también era opositora (pedidos de
informes y mociones de censura contra el jefe de Gabinete).

En septiembre Juan ya había pedido contar sólo las caídas propuestas por el
oficialismo. ADR-0313 lo rechazó porque ninguna fuente de la Cámara publica el
convocante, y el proyecto no adivina con heurísticas. Ese límite no cambió: lo
que cambia es que el dato se carga a mano, como otros registros curados del
cinturón (`derrotas_legislativas_eventos.json`, `gabinete_salidas.json`).

## Factores de decisión

- Un indicador tiene que medir lo que su nombre dice: «el oficialismo no logra
  reunir a la cámara» no describe una sesión opositora que el oficialismo dejó
  caer a propósito.
- Las sesiones caídas son pocas (12 desde 2024) y la prensa dice quién pidió cada
  una: la carga manual es chica y verificable.
- Nada se infiere: cada entrada lleva la fuente que lo dice.

## Opciones consideradas

- **Registro a mano del convocante de cada sesión caída; las de la oposición
  salen del numerador y del denominador** — elegida.
- **Contar la caída opositora como victoria del gobierno (restarla o premiarla)**
  — descartada: el indicador mide fracasos propios con el ideal en 0 %, y no
  tiene una escala para victorias. Sacarla alcanza para que deje de penalizar.
- **Dejarlo como está (ADR-0313)** — descartada: con la ventana actual, el
  100 % de las caídas que el indicador cuenta son derrotas de la oposición.

## Decisión

- `data/politica/sesiones_minoria_convocante.json` registra, por id de reunión
  del índice oficial, `convocante` (`oposicion` | `oficialismo`), quién la pidió
  y la `fuente`. Una entrada sin fuente o con otro valor hace fallar el colector.
- `_sesiones_para_veto()` en `scripts/politica.py` aplica la regla, y la usan la
  card (`fetch_veto_quorum`) y la serie (`descargar_series.fetch_veto_quorum_serie`
  vía `_hcdn_sesiones_legislativas`), así que card y serie no se separan.
- Una caída que todavía no está en el registro cuenta como hasta ahora (caída
  del oficialismo) y la card registra un `[COTEJO_MANUAL]` para cargarla.
- Las sesiones que sí se realizaron siguen todas en el denominador, sin importar
  quién las pidió.

### Consecuencias

- La card pasa de 18,2 % (2 de 11) a 0 % (0 de 9) y el texto dice cuántas caídas
  opositoras quedaron afuera.
- La serie histórica se recalcula con el mismo registro desde 2024.
- Cada sesión caída nueva pide su carga: es trabajo manual, chico y avisado.

### Confirmación

`tests/test_quorum_convocante.py`: una caída opositora no cuenta, una del
oficialismo sí, una sin cargar cuenta y pide cotejo, una entrada sin fuente
falla, y el registro versionado tiene fuente en cada entrada.

## Más información

- ADR-0091: criterio de minoría y ventana de 12 meses.
- ADR-0308: índice oficial de sesiones como fuente.
- ADR-0313: por qué la fuente no alcanza para saber el convocante.
