# Devolución de Luis Babino sobre el artifact de agosto — qué pidió y qué se hizo

Bitácora del cambio. Las decisiones viven en los ADR
[0211](adr/0211-la-lectura-del-mes-la-escribe-el-equipo.md),
[0212](adr/0212-el-monitor-del-plan-de-gobierno-y-el-cinturon-de-impacto-social.md)
y [0213](adr/0213-la-portada-dice-que-mide-cada-cinturon.md); este documento es
el rastro de dónde salieron y qué quedó afuera.

## De dónde salió

Luis devolvió `informe-artifact (4).html`: el artifact autocontenido que emite
`web/tools/emitir-artifact.mjs`, con sus ediciones encima. Comparado contra el
artifact del repo (16-ago; entre medio sólo hubo commits de datos), **no tocó
ni un número ni una sección**: 149 líneas de diferencia, todas nomenclatura y
prosa.

## Los cinco cambios, y qué se hizo con cada uno

| Pidió | Se hizo | Dónde |
|---|---|---|
| `Informe de Coyuntura` → **Monitor del Plan de Gobierno** | sí | ADR-0212 |
| `Vida cotidiana` → **Impacto social** | sí | ADR-0212 |
| (mantuvo la sigla ITVC) | **se corrigió a ITCIS** — era un descuido, no una decisión | ADR-0212 |
| Bajada del hero fija, posicional | sí | ADR-0213 |
| Lectura del mes escrita por el equipo | sí, **con fallback al automático** | ADR-0211 |
| La portada define cada cinturón; sale la escala 0-10 | sí | ADR-0213 |

Dos cosas que **no** se replicaron del HTML, porque eran artefactos de un
buscar-y-reemplazar a ciegas y no decisiones suyas: **"la impacto social"** (4
veces) y **"y vida cotidiana"** donde la conjunción pide *e*.

## Lo que hay que confirmarle a Luis

1. **La sigla pasó a ITCIS.** Él había dejado ITVC sobre un índice llamado
   "Impacto Social".
2. **La escala 0-10 salió de la portada.** Queda en `/metodologia#marco`. Es
   una modificación declarada de ADR-0200, que la había puesto ahí a propósito.
3. **Las otras tres siglas siguen sin definir** (ITCM, ITCG, ITCP), y con ellas
   el problema más caro que nombra ADR-0190: **ITCG se confunde con el ICG de
   la UTDT**, que el propio informe publica. Son decisión editorial de la
   Fundación; el código ya está preparado para que sean una línea cada una.

## Cómo escribir la lectura del mes

Un archivo por edición en `web/src/contenido/lectura-del-mes/AAAA-MM.md`. Es
markdown, se publica firmado por el equipo. Si el mes no tiene archivo, la
portada cae sola a la síntesis automática y lo dice; `gate_calidad.py` avisa
(G8) en cada corrida hasta que se escriba. Ver el README de esa carpeta.

## Lo que quedó pendiente y no es de este cambio

Rastreando un recuerdo de cambios perdidos en el cinturón (ver el informe de
abajo) aparecieron tres incoherencias reales entre la web y el motor, **todas
anteriores a este trabajo**:

- `descripciones.ts` dice que `pobreza_nowcast` *"se publica como contexto: no
  integra el índice"*. Es falso desde ADR-0153: pesa 9,31%. La ficha del mismo
  indicador, en `fichas.ts`, dice lo correcto — la web se desmiente a sí misma.
- `endeudamiento_familiar` e `indice_lider` siguen descritos como si puntuaran.
  Salieron del índice en ADR-0154.
- Tres de las seis glosas de dimensión están desactualizadas: la de ingresos
  omite pobreza (25% de la dimensión), la de empleo omite `empleo_registrado`
  (40,23%, su componente principal), y la de vulnerabilidad describe dos patas
  cuando hoy tiene una.

### El recuerdo de los cambios perdidos

Se rastreó a fondo (211 ADR, 135 versiones de `itvc.py`/`publicar.py` en todas
las refs y el reflog, 154 snapshots publicados). **No hubo ninguna reversión.**

- **`informalidad` en la dimensión equivocada**: el problema es real y está
  registrado —ADR-0033 lo deja abierto con estas palabras: *"«Prospectivas de
  empleo» no contiene medidas directas de empleo (…) la informalidad vive en
  Ingresos"*—, pero **el cambio nunca se hizo**: no existe en ningún commit ni
  en ningún snapshot. Lo que sí se hizo, y es probablemente el recuerdo, fue
  ADR-0130 (`bea17c8`, 25-jul): *"la dimensión de empleo pasa a medir empleo"*,
  que atacó el mismo diagnóstico por otro lado — metiendo `empleo_registrado`
  como componente principal en vez de mover `informalidad`.
- **Carne**: los cinco commits están enteros. Lo que pudo confundirse: en
  `d3a0d31` el propio editor corrigió una lectura y el cambio de peso se
  deshizo **antes** de commitear; y `bdab21c` (18-ago) arregló una pérdida real
  **de datos, no de código** — la serie de carnes totales faltaba en el
  `git add` del workflow, así que el cron la acumulaba y la tiraba cada noche.
- **Cierre de empresas**: nunca existió tal indicador. `mortalidad_pymes` es el
  IPI industrial con nombre legado, y ADR-0119 §3 decidió explícitamente **no**
  renombrarlo.

Mover `informalidad` sigue siendo una decisión de metodología abierta: cambia
el número publicado y, por la regla de ADR-0115, hay que conservar el peso
efectivo y derivar los nominales de ahí. Va con ADR propio.
