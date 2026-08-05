---
madr: 4
id: '0174'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/gate_calidad.py']
continua: ['0133']
relacionado: ['0172', '0173']
ambito: 'Gate de calidad · alcance del invariante G3'
origen: 'Una card en carry-forward por rate limit de Trends bloqueó la publicación de los cinco cinturones contra su propia serie fresca'
---

# ADR-0174 — G3 verifica cards frescas

## Contexto y planteo del problema

G3 comprueba que el último punto de la serie coincida con el titular de la card.
Comparaba **siempre**, sin mirar si la card era un dato nuevo o un
carry-forward.

El 5-ago-2026 la corrida terminó así:

```
[DEMORA] G2 espiritu_epoca: 1/1 indicadores desactualizados (> 40%)
[FALLA]  G3 espiritu_epoca/indice_intencion_migratoria: serie[-1]=7.0 ≠ card=5.6
```

La secuencia real: Google Trends rate-limiteó el fetch de la **card**
(`intencion_migratoria FAIL (normal si hay rate limit)`), que quedó con el valor
anterior, 5,6. La **serie** del mismo indicador bajó bien —`[OK]
indice_intencion_migratoria: 66 puntos`— con 7,0. La fuente falló de un lado y
del otro no.

Esa discrepancia **es el carry-forward funcionando**. Una card marcada
`desactualizado` es, por definición, un valor de otro momento: si la serie se
movió desde entonces, los dos números tienen que diferir. G3 lo leía como
desincronización y cortaba la publicación de los **cinco** cinturones por una
condición que G2 ya estaba reportando en la línea de arriba.

Es la misma sobre-reacción que ADR-0133 corrigió para los colectores —una fuente
demorada no tira abajo el pipeline— pero del lado del gate.

## Factores de decisión

- La frescura ya tiene dueño: **G2**, con su tope de rezago por indicador y su
  presupuesto de carry-forward por cinturón. Que G3 falle por lo mismo no agrega
  información, sólo bloquea.
- G3 sirve para detectar que card y serie miden cosas distintas o se
  desincronizaron por bug. Contra una card que declara no ser fresca, el
  invariante no es verificable, no está violado.
- El costo del falso positivo es máximo: cinco cinturones sin publicar, y el
  pipeline no avisaba (hasta ADR-0173).
- Silenciarlo del todo tampoco sirve: si un indicador queda desactualizado
  muchos días, quiero verlo en el log del gate y no sólo en el de G2.

## Opciones consideradas

- **Degradar la discrepancia a aviso cuando la card está en carry-forward** —
  elegida. Sigue apareciendo en el log; deja de bloquear.
- **Saltear la comparación por completo cuando la card está desactualizada** —
  descartada: pierde la señal. Un indicador desactualizado con una serie que se
  fue muy lejos es algo que quiero ver.
- **Sumar el indicador a `G3_EXCEPCIONES`** — descartada, y es justamente el
  reflejo que ADR-0172 desarmó: la excepción es permanente y el problema es
  transitorio. Taparía también las desincronizaciones reales del indicador.
- **Que la serie también haga carry-forward cuando la card falla** — descartada:
  obliga a coordinar dos scripts (el colector y `descargar_series.py`) para que
  fallen juntos, y tirar un dato bueno porque otro falló empeora la serie.

## Decisión

La discrepancia G3 bloquea **sólo si la card no está en carry-forward**. Con
`desactualizado: true`, se registra como aviso:

```
G3 espiritu_epoca/indice_intencion_migratoria: serie[-1]=7.0 ≠ card=5.6,
pero la card está en carry-forward — lo vigila G2
```

### Consecuencias

- Una fuente que falla del lado de la card deja de bloquear la publicación de
  los cinco cinturones.
- G2 sigue siendo el que corta por frescura: tope de rezago por indicador y
  ≤40% de carry-forward por cinturón. Ninguno de los dos se tocó.
- Un indicador desactualizado y desincronizado queda visible en el log del gate
  en vez de desaparecer.

### Confirmación

`tests/test_gate_carry_forward.py`: una card `desactualizado` que no coincide con
su serie no genera falla, y la misma card marcada como fresca sí.

## Más información

### Limitaciones

- La ventana de tolerancia queda atada a la calidad de la marca
  `desactualizado`. Un colector que se olvide de setearla en un carry-forward
  hace que G3 falle como antes; uno que la ponga de más apaga el chequeo para
  ese indicador. Ningún test verifica hoy que la marca sea correcta por
  indicador — se confía en el colector.
- No distingue "desactualizado por un día" de "desactualizado hace tres meses".
  El segundo caso lo agarra G2 por rezago, pero mientras esté por debajo del
  tope, G3 no aporta presión adicional.
