---
madr: 4
id: '0208'
estado: 'aceptado'
fecha: 2026-08-15
cinturon: 'vida'
archivos: ['scripts/itvc.py', 'scripts/series_io.py', 'scripts/generar_informe.py', 'scripts/publicar.py', 'scripts/bigquery_export.py', 'tests/test_generar_informe.py', 'tests/test_itvc_empleo_registrado.py']
supersede_parcialmente: ['0206', '0207']
relacionado: ['0060', '0205']
ambito: 'Construcción del ITVC · qué script puede calcularlo y de dónde sale el barbarismo dominante'
origen: 'ADR-0206 dejó el arreglo de fondo pendiente y ADR-0207 dejó la vista de BigQuery a merced de que alguien se acordara'
---

# ADR-0208 — El ITVC vive en su módulo, y el intermedio nace bien

## Contexto y planteo del problema

[[0206-los-dos-artefactos-publicados-dicen-lo-mismo]] tapó un síntoma y dejó la
causa escrita: `generar_informe.py` no podía calcular el ITVC porque la máquina
que lo arma vivía **dentro de `publicar.py`**, que corre después. El intermedio
nacía con el score legacy del colector viejo (2,9 contra los 6,9 reales) y
`publicar.py` se lo corregía al final.

Al desarmarlo apareció que la consecuencia era peor que dos JSON discordantes.

**El barbarismo dominante que publicaba el sitio estaba mal.**
`detectar_barbarismo()` corre en `generar_informe.py` y elige el cinturón con
el score más alto. Con vida cotidiana en su valor legacy de 2,9, el más alto
era macroeconomía (3,9) → *tecnocrático*. Con vida en su valor real de 6,9 —el
más tensionado del tablero por lejos— el dominante es *político*.

`publicar.py` **no recalcula el barbarismo**: lo hereda del intermedio. Así que
la portada venía anunciando "Riesgo dominante: Tecnocrático" mientras mostraba,
tres centímetros más abajo, vida cotidiana en 6,9 y macro en 3,9. El número
correcto estaba a la vista al lado del veredicto que lo contradecía.

[[0207-la-serie-comparable-es-una-vista-no-un-backfill]] dejó su propio cabo:
la vista `corridas_comparables` se genera desde `config.PESOS_CINTURONES`, pero
era de corrida manual. Si cambian los pesos y nadie la regenera, promedia un
perímetro que ya no existe — y ningún test lo agarra, porque vive en BigQuery.

## Factores de decisión

- Lo que decide un número publicado tiene que estar donde lo pueda usar quien
  lo calcula primero.
- Mover metodología entre archivos no puede cambiar ni un decimal.
- Un cabo suelto que depende de que alguien se acuerde no es un arreglo.

## Opciones consideradas

- **Mudar la construcción de índices a `itvc.py` y que `generar_informe.py` la
  use** — elegida.
- **Que `publicar.py` recalcule también el barbarismo.** Descartada: arregla el
  síntoma visible y deja el intermedio mintiendo igual. Es la venda de la venda.
- **Que `generar_informe.py` importe `publicar.py`.** Descartada: `publicar.py`
  ya importa `generar_informe` para regenerar el `.md`; el ciclo rompe los dos.

## Decisión

### 1. La construcción de los índices se muda a `itvc.py`

`BASE_MESES`, `WINSOR_TOPE`, `SERIES_REBASEADAS`, `rebase_movil12`,
`rebase_de_serie` e `indices_desde_series` salen de `publicar.py` y pasan a
`itvc.py`, que ya era el dueño de los pesos, las bandas y la agregación. Ahora
el módulo tiene el índice entero.

`indices_desde_series` recibe los baselines **como dict, no como ruta**:
`itvc.py` sigue sin conocer el layout del repo, que es lo que lo hace
importable desde los dos scripts y testeable sin tocar disco.

`publicar.py` conserva sus nombres privados como alias finos, así que sus otras
2.100 líneas no se tocaron.

### 2. `series_io.build_series()`, compartido

Leer `output/series/*.csv` también vivía sólo en `publicar.py`. Es I/O puro y
ahora lo importan los dos.

### 3. `generar_informe.py` calcula el ITVC

Vida cotidiana no entra en `_INDICES_PARAMETRICOS` —su índice no sale del caché
del colector sino de las series— así que tiene su propio `_recalcular_itvc()`.
El intermedio nace con 6,9, con su bloque `itvc`, y el global con 4,2.

**La reconciliación de ADR-0206 queda, y ahora es no-op.** Cubre el único camino
por el que los dos scripts todavía pueden separarse: los tres fallbacks de
baseline (`consumo_carne`, `inseguridad`, `patentamiento_motos`), que sólo
entran si falta la serie del componente y que `publicar.py` alimenta con 17
indicadores contra los 3 del caché. Verificado el 2026-08-15: con las series
completas el resultado es idéntico —90,3— pase lo que pase por ese argumento.

### 4. El barbarismo dominante se corrige solo

No hubo que tocar `detectar_barbarismo()`: siempre estuvo bien. Le llegaba mal
el insumo. Con vida en 6,9 el dominante pasa a **político**, que es lo que el
tablero venía mostrando sin decirlo.

### 5. La vista comparable se redefine en cada corrida

`bigquery_export.py` termina redefiniéndola con los pesos vigentes.
`CREATE OR REPLACE VIEW` es metadata: no escanea datos, no cuesta y es
idempotente. Va en `try/except` porque el archivo ya está subido y una caída
acá no puede tumbar la corrida. Esto **reemplaza** la decisión de ADR-0207 de
dejarla de corrida manual: el argumento de "redefinirla cada noche es ruido"
no compensa que quede vieja en silencio.

### Consecuencias

- La portada corrige su riesgo dominante: tecnocrático → **político**. Es una
  corrección, no un cambio de coyuntura, y conviene decirlo si alguien compara
  con la edición de ayer.
- `publicar.py` baja de 2.260 a ~2.020 líneas; `itvc.py` sube a 460.
- Los dos scripts comparten el motor del índice: cambiarlo en un lado ya no
  puede dejar al otro atrás.
- Queda un residuo declarado: los tres fallbacks de baseline (punto 3).

### Confirmación

- **El refactor no movió ningún número**: se corrió `publicar.py` antes y
  después y se diffeó el snapshot entero. Las 22 diferencias son todas de
  antigüedad del dato (`vintages`: meses, días) corridas un día, porque el
  snapshot previo era del 14 y la corrida del 15. Ni un score, ni un índice, ni
  una banda.
- `generar_informe.py` solo: `score_global=4.2`, vida 6,9, ITVC 90,3,
  barbarismo político.
- La reconciliación de ADR-0206 no imprimió nada en la corrida siguiente, que
  es la prueba de que el intermedio ya nace bien.
- `gate_calidad.py` y la suite en verde.

## Pros y contras de las opciones

**Mudar a itvc.py** (elegida)

- Bueno, porque el intermedio nace bien y el barbarismo se corrige de arrastre.
- Bueno, porque el motor del índice deja de tener un solo consumidor posible.
- Malo, porque toca `publicar.py`, que es el archivo más delicado del repo — se
  compensó verificando el snapshot byte a byte antes y después.

**Que publicar recalcule el barbarismo**

- Bueno, porque es un cambio de tres líneas.
- Malo, porque el artefacto público sigue mintiendo y la causa queda intacta.

## Más información

- Dos tests cambiaron de premisa y se conservan dados vuelta:
  `test_vida_recalcula_el_itvc_y_no_usa_el_score_cacheado` (antes afirmaba que
  vida NO tenía paramétrica) y el guard de `empleo_registrado`, que ahora
  vigila `itvc.py` en vez de `publicar.py`.
- El barbarismo por cinturón (`BARBARISMO_MAP` en `config.py`) no se tocó: vida
  cotidiana siempre declaró "político".
