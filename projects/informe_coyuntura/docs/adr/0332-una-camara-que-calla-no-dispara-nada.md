---
madr: 4
id: '0332'
estado: 'aceptado'
fecha: 2026-09-20
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_empresario]
archivos: ['scripts/politica.py', 'tests/test_camara_muda.py']
relacionado: ['0149', '0310']
ambito: 'Cinturón política · ITCP · `apoyo_empresario` · detectar que una cámara dejó de publicar; no cambia el cálculo del saldo'
origen: 'Al desbloquear la card el 20-sep-2026 (tanda de 4 comunicados UIA) se midió de dónde venían los computables y AEA no aparecía desde marzo. Juan lo empujó preguntando «pero no hay más datos?».'
---

# ADR-0332 — Una cámara que calla no dispara nada, y el saldo sigue saliendo

## Contexto y planteo del problema

`apoyo_empresario` publica el saldo de postura de **dos** cámaras —AEA y UIA—
hacia el Ejecutivo nacional, y su card se rotula «Postura pública de las cámaras
empresarias». Al 20-sep-2026 **una de las dos lleva 173 días sin publicar**.

AEA no emite un comunicado desde el **2026-03-31**. Verificado contra su propia
página (`aeanet.net/prensa.html`): la fecha más nueva que existe ahí es ésa, así
que no es el extractor, es la fuente. Y no es su cadencia normal: sobre los 42
huecos observados en el corpus, AEA tiene **mediana 43 días, p90 116, p95 151 y
máximo 154**. Los 173 días actuales **no tienen precedente**. UIA, en cambio,
está en 3 días contra un máximo de 112.

El efecto sobre el número publicado, medido en la ventana móvil de 12 meses que
produce el punto de 2026-09 (valor −0,2):

| | computables en la ventana |
|---|---|
| UIA | **9** |
| AEA | **1** (un apoyo del 2026-03-03) |

O sea: el indicador que se llama «las cámaras empresarias» es hoy **90% UIA**, y
cuando marzo salga de la ventana móvil será 100% UIA sin que nada cambie en la
card.

**Lo que falla no es el cálculo: es que nadie lo mira.** ADR-0310 puso dos
guardas sobre este indicador y AEA pasa las dos:

- los **pendientes** cortan la serie cuando hay un comunicado sin codificar —
  pero AEA no tiene comunicados nuevos, así que no genera ninguno;
- **`inventario_verificado`** exige que las dos cámaras **respondan** en la misma
  corrida — y la página de AEA responde perfectamente, con sus 46 comunicados de
  siempre.

Una fuente que contesta y no publica es indistinguible, para el pipeline, de una
fuente que no tiene novedades. El manual del indicador ya lo tenía anticipado en
una línea de `lo_que_este_indicador_NO_dice`: *«Una cámara puede callar por
conveniencia y eso no aparece»*. Está pasando, y no aparece.

## Factores de decisión

- El umbral no puede ser un número elegido a mano: es lo que este repo llama
  copiar el rezago del documento en vez de medirlo.
- Tiene que ser **por cámara**. AEA publica cada 43 días de mediana y UIA cada 7:
  un tope único daría falsos positivos en una y taparía a la otra.
- **Sólo lo accionable.** Un aviso que salte en cada hueco normal de AEA entrena
  a ignorar el canal, que es la regla que mantiene vivo `#monitor-alertas`.
- No se toca el cálculo del saldo. Que una cámara calle es un hecho del mundo,
  no un error de cómputo.

## Opciones consideradas

1. **Renombrar la card a «Postura pública de la UIA»** mientras AEA calle.
2. **Un tope fijo de días** igual para las dos cámaras.
3. **Avisar cuando el silencio de una cámara supera su propio máximo
   histórico**, medido sobre el corpus — elegida.
4. No hacer nada y anotar el hallazgo.

## Decisión

**Opción 3.** `politica.silencio_por_camara()` calcula, por cámara, los días sin
publicar y el hueco más largo que esa misma cámara ya se tomó entre dos
comunicados. `_avisar_camara_muda()` registra una incidencia `[COTEJO_MANUAL]`
—el mismo mecanismo que el vencimiento de la conciliación judicial— **sólo
cuando el silencio supera ese máximo**, o sea cuando deja de tener precedente.

El umbral se autocalibra: no hay ningún número de días en el código. Con menos
de `CAMARA_MUDA_PISO_HUECOS = 10` huecos observados la guarda se abstiene, porque
un corpus corto subestima la cadencia real y avisaría de más.

**No se renombra la card (opción 1 descartada).** El universo de diseño sigue
siendo las dos cámaras y el manual ya declara que una puede callar; renombrar
haría que el rótulo oscile cada vez que AEA publique o deje de publicar, y
perdería la información de que una se calló. Si el silencio resulta permanente,
cambiar el perímetro del indicador es **otra** decisión y pide su propio ADR —
es lo que el texto del aviso le pide explícitamente a quien lo lea.

La opción 2 se descartó porque con un tope único AEA quedaba en falso positivo
permanente o UIA sin vigilancia; la 4, porque un hallazgo sin guarda se
redescubre a los golpes, que es la lección de ADR-0220.

### Consecuencias

- La corrida nocturna va a avisar por AEA **desde la próxima**, y va a seguir
  avisando hasta que publique o hasta que se decida el perímetro. Es el
  comportamiento buscado: hoy el hallazgo vive en este ADR y en nada más.
- El saldo, el peso y la banda **no cambian**. La card sigue publicando −0,2 con
  fecha 2026-09.
- La guarda sirve para las dos cámaras: si mañana UIA se calla —que es la que
  sostiene 9 de los 10 computables— también avisa.
- Queda sin resolver, a propósito, que la ficha no publique la composición por
  cámara de la ventana. Se decide cuando se decida el perímetro.

### Confirmación

`tests/test_camara_muda.py`, cinco casos, y lo que prueba de verdad es lo que la
guarda **no** tiene que hacer:

- avisa cuando el silencio no tiene precedente;
- **NO** avisa con un hueco largo que la cámara ya se había tomado antes;
- no opina con un corpus por debajo del piso de huecos;
- el umbral es por cámara: dos cámaras con el mismo silencio y cadencias
  distintas no se juzgan igual;
- y un caso contra el corpus versionado, no un fixture, que falla si AEA vuelve a
  publicar — o sea, este ADR deja de estar vigente y el test lo dice.

Probada rompiéndola en las dos direcciones, con el bytecode borrado antes de
cada corrida: mutada a «nunca avisa» caen 2 tests; mutada a «avisa siempre» caen
otros 2, entre ellos el del hueco con precedente. Restaurada, 5 passed.

## Pros y contras de las opciones

**Opción 3 (elegida).** Bueno: sin números mágicos, por cámara, y se calibra sola
a medida que el corpus crece. Malo: si una cámara arrastra un hueco enorme
histórico, el umbral queda alto y tarda en avisar.

**Opción 1.** Bueno: el rótulo diría la verdad hoy mismo. Malo: oscila con cada
publicación, y tapa el hallazgo en vez de mostrarlo.

**Opción 2.** Bueno: trivial de implementar y de explicar. Malo: no existe un
número que sirva para una cámara que publica cada 7 días y otra cada 43.

## Más información

- ADR-0149 — el detector de novedades empresarias, que no clasifica.
- ADR-0310 — el corpus cerrado y `inventario_verificado`, las dos guardas que
  AEA pasa sin activar.
- El hallazgo salió de una pregunta, no de un gate: al desbloquear la card se
  midió de dónde venían los 10 computables de 2026 y AEA no aparecía desde
  marzo. Agosto de 2026 es el caso que lo resume: **11 comunicados codificados y
  cero computables**.
