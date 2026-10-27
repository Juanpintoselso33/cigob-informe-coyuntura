---
madr: 4
id: '0383'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [ocupacion_eph, informalidad, empleo_registrado, mortalidad_pymes, subocupacion_demandante, trabajo_independiente, despacho_cemento]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/vida_cotidiana/collectors/indec_series.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/datos.ts']
relacionado: ['0130', '0214', '0218', '0219', '0245', '0373', '0389']
ambito: 'Cinturón de impacto social · ITCIS · dimensión Empleo (ex Prospectivas de empleo)'
origen: 'Reunión del 26-oct-2026: «se replantea, si se puede. Principal: la variación de la ocupación según la EPH continua (trimestral, 31 aglomerados). Complemento: el padrón de ARCA de inscriptos como empleadores, incluidos los que no tienen personal a cargo.»'
---

# ADR-0383 — La prospectiva de empleo pasa a «Empleo»

## Contexto y planteo del problema

La dimensión «Prospectivas de empleo» se armó por acumulación: informalidad,
empleo registrado (SIPA), empleadores PyME con ART, construcción (ISAC),
subocupación demandante y trabajo independiente. Sólo dos miden cuánta gente
trabaja o en qué condiciones; la construcción no es empleo y los empleadores
con ART no ven a los inscriptos sin personal. En la reunión del 26-oct-2026 se
resolvió replantearla alrededor de la **ocupación de la EPH continua** como
principal y el **padrón de ARCA de empleadores** como complemento. El documento
del colaborador que debía detallar el resto no llegó; esta decisión aplica sólo
lo dicho en la reunión y la consigna de Luis (sacar construcción; no tomar
empleo registrado, empleadores PyME, subocupación demandante ni trabajo
independiente; informalidad «analizar»).

## Factores de decisión

- Que la dimensión mida cuánta gente trabaja, no proxies de actividad.
- Una serie oficial, automática y reproducible por componente (regla del repo:
  si no se puede reproducir, no puntúa).
- No mover el peso de las otras dimensiones.
- El rezago se mide, no se copia.

## Opciones consideradas

- **Entra `ocupacion_eph`; informalidad queda como complemento; los otros cinco
  se suspenden (elegida).**
- Dejar los seis y sumar la ocupación: contradice la consigna.
- Sacar también informalidad: la consigna dice «analizar», no «sacar»; la
  dimensión quedaría con un solo componente.

## Decisión

**Fuente del principal.** Tasa de empleo del INDEC, EPH continua, total de 31
aglomerados urbanos, trimestral: serie `42.3_EPH_PUNTUATAL_0_M_24` de la API de
datos.gob.ar (llega a 2T-2026 y está en 94 trimestres desde 2003).

**Qué se mide.** `ocupacion_eph` es la **diferencia de la tasa de empleo contra
el mismo trimestre de 2023, en puntos porcentuales** (2T-2026: 45,0 % contra
44,6 % en el 2T-2023, +0,4 pp). Se eligió la tasa y no el total de ocupados
porque es la cifra que el INDEC publica y absorbe el crecimiento demográfico; y
se compara la misma estación porque la EPH no viene desestacionalizada.

**Escala (decisión de Juan del 27-oct-2026).** La primera versión comparaba
contra el año anterior y valía `100 + pp ÷ 45,8 × 100`: un punto de tasa movía
2,2 puntos del índice y el componente quedaba siempre cerca de 100. La tasa se
mueve poco —en veinte años, salvo la pandemia, cambió menos de un punto por año
casi siempre— y un punto son cientos de miles de puestos. Por eso se compara
contra 2023 (si hoy trabaja más o menos gente que cuando empezó el Gobierno,
mismo criterio que el gasto de funcionamiento) y **cada décima de punto vale 1
punto del índice**: `100 + 10 × pp`. 2T-2026 da 104; el 4T-2025 (−0,8 pp) daba 92.

**Rezago.** Medido en los snapshots del repo: el 1T-2026 (fecha 2026-01-01)
apareció entre el 10-may y el 27-jun, y el 2T-2026 (2026-04-01) antes del
20-sep, o sea ~80 días después del cierre del trimestre y ≤ 177 días desde la
fecha del dato. Con el ciclo siguiente suma ≤ 268: el tope de 280 días de
`informalidad` y `subocupacion_demandante` alcanza y se aplica igual a
`ocupacion_eph` (`config.MAX_DIAS`).

**Pesos.** La dimensión se llama «Empleo», con su peso nominal intacto
(0,2419). Adentro, `ocupacion_eph` 0,5128 e `informalidad` 0,3419 (su peso de
siempre) — 60 / 40 de lo que puntúa — y los cinco suspendidos ceden
proporcionalmente (×0,2208) para que la tabla siga sumando 1. Pesos efectivos
en el ITCIS: ocupación 14,51 %, informalidad 9,68 % (antes 8,27 %).

**Suspendidos** (mecanismo de ADR-0245: salen del cálculo y de la web, se
conservan como archivo con motivo y condición de reingreso):
`empleo_registrado`, `mortalidad_pymes`, `subocupacion_demandante`,
`trabajo_independiente`, `despacho_cemento`. Siguen recolectándose.

**Informalidad** queda mientras se decide («analizar»): es EPH, trimestral y
mide calidad del empleo, que la ocupación no ve.

**Padrón de ARCA: queda afuera.** Se buscó en ARCA/AFIP (estadísticas
tributarias) y en datos.gob.ar y no hay ninguna serie pública periódica de
empleadores inscriptos; lo más cercano es la base de empleadores de OEDE, que
ADR-0218 ya encontró sin actualizar desde octubre de 2023, y la serie de la
SRT, que sólo cuenta empleadores con ART y personal declarado. Sin serie
reproducible no hay indicador: no se inventa ni se propone un pedido de acceso.
La dimensión queda con la ocupación y la informalidad; si ARCA publica el
padrón, entra con su propio ADR.

### Consecuencias

- Con el snapshot del 27-oct-2026 (ocupación +0,5 pp → índice 101,1; el resto
  de los índices sin cambio): la dimensión Empleo pasa de 91,6 a
  alrededor de 100 y el índice de impacto social de 93,6 a alrededor de 95,7
  (con la escala final; el número exacto sale de la corrida). El salto viene de sacar los
  componentes en rojo (construcción 78,1, subocupación 85,0), no de la
  ocupación, que casi no se mueve.
- El componente nuevo varía poco: la tasa de empleo cambia décimas por año. Es
  una señal de fondo.
- Los números del archivo mensual se releen con el método vigente (ADR-0359).

### Confirmación

`tests/test_itvc.py` fija pesos y suspendidos; `tests/test_ocupacion_eph.py`
prueba el cálculo interanual, el índice y el rezago sin red;
`tests/test_la_ficha_no_se_queda_atras.py` exige las fichas.

## Pros y contras de las opciones

- Elegida: la dimensión mide empleo de verdad con dos series EPH oficiales;
  pierde el SIPA y la mirada de empresas.
- Dejar los seis: no cambia nada de lo que se quería cambiar.
- Sacar informalidad: simplifica, pero deja un solo componente y pasa por
  arriba la palabra «analizar».
