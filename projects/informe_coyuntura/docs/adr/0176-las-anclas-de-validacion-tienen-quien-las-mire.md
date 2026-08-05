---
madr: 4
id: '0176'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/gate_calidad.py', 'scripts/validacion_externa.py']
continua: ['0175']
relacionado: ['0133', '0159', '0174']
continuado_por: ['0177']
ambito: 'Gate de calidad · G7, frescura de las anclas de validación externa'
origen: 'ADR-0175 dejó anotado que una serie que es sólo insumo de validación no tiene quién la vigile'
---

# ADR-0176 — Las anclas de validación tienen quién las mire

## Contexto y planteo del problema

ADR-0175 cerró el caso del ICG congelado y dejó la causa estructural abierta:

> Sigue sin haber un gate para series que son sólo insumo de validación. G2 mira
> cards, G3/G3b miran pares card↔serie; una serie sin card no tiene quién la
> vigile.

El ICG de la UTDT estuvo congelado —su fetcher levantaba `NameError` en cada
corrida— y **siguió entrando al factor común** del panel con su última
observación vieja. Las correlaciones del ITCP se publicaron todo ese tiempo como
si el ancla estuviera viva. Lo encontró un aviso lateral agregado para otra cosa,
no un chequeo.

El agujero es general: las 15 estadísticas de `panel_validacion.FAMILIA`
alimentan la validación de ITVC, ITCG e ITCP y **ninguna es indicador de ningún
cinturón**, que es justamente el requisito de ADR-0159. Por eso no tienen card,
y por eso ningún gate las mira.

Al ir a escribirlo apareció una complicación: las anclas llegan por **tres vías
distintas** y sus series crudas **no se persisten**. Cuatro salen de
`resultados` (`consumo_supermercados_mensual`, `merval_usd_mensual`,
`epu_argentina_mensual`, `indice_lider_mensual`), dos de `series.json`
(`icg_utdt`, `clima_electoral`) y el resto se baja en vivo de datos.gob.ar
dentro del propio `validacion_externa.py`. Verificar la frescura desde afuera
era imposible: el panel es insumo, no salida.

## Factores de decisión

- Un ancla congelada es **peor que una ausente**: participa igual del factor
  común y las correlaciones se publican con apariencia de sanas.
- Perseguir cada una de las tres vías desde el gate sería frágil y se rompería
  con el próximo refactor de `validacion_externa.py`.
- El registro de anclas ya existe y es único: `panel_validacion.FAMILIA`. Un
  gate que lo duplique se desincroniza el día que se agregue un ancla.
- Bloquear la publicación de los cinco cinturones porque una estadística externa
  publicó tarde es la sobre-reacción que ADR-0133 y ADR-0174 ya corrigieron.

## Opciones consideradas

- **Que `validacion_externa.py` persista la huella de frescura de cada ancla y
  que el gate la verifique contra `FAMILIA`** — elegida.
- **Que el gate baje las anclas y las revise por su cuenta** — descartada: el
  gate es deliberadamente liviano (`json`, `re`, `sys`, `pathlib`) y ponerlo a
  hacer red lo vuelve otro punto de falla del pipeline.
- **Verificar sólo las anclas que pasan por `series.json`** — descartada: son 2
  de 15, y deja el agujero casi entero.
- **Chequear sólo que cada ancla participe del factor común
  (`factor.cargas`)** — descartada por insuficiente: caza el ancla que
  desaparece, no la que se congela. El ICG estuvo en `cargas` todo el tiempo.

## Decisión

### 1. `validacion_externa.py` registra la huella de cada ancla

```python
resultados["panel_anclas"] = {
    nombre: ({"ultimo": max(panel[nombre]), "n": len(panel[nombre])}
             if panel.get(nombre) else None)
    for nombre in pnl.FAMILIA
}
```

Se recorren las **declaradas**, no las presentes: un ancla vacía queda
registrada como `None` en lugar de desaparecer del registro. Sin eso, "ausente"
y "nunca declarada" serían indistinguibles.

### 2. G7 las verifica, leyendo el registro de `FAMILIA`

El gate importa `panel_validacion` para saber qué anclas se declaran, así que un
ancla nueva entra sola al chequeo sin tocar `gate_calidad.py`.

- **Ancla declarada sin datos → BLOQUEA.** El factor común se calculó sobre
  menos series que las declaradas y su varianza explicada se publica igual: el
  snapshot afirma algo que no es.
- **Ancla congelada → DEMORA, no bloquea.** Es una fuente atrasada, mismo
  criterio que G2 (ADR-0133) y que ADR-0174. Pero queda **nombrada en cada
  corrida**, que es exactamente lo que le faltó al ICG.
- **`panel_anclas` ausente → BLOQUEA.** Si el registro deja de escribirse, el
  gate se queda ciego, y esa ceguera es justo lo que este ADR viene a evitar.

Los prefijos que no bloquean pasan de literales en el filtro a una constante,
`NO_BLOQUEAN = ("G2 ", "G7-frescura ")`.

### 3. Topes calibrados contra el rezago observado

150 días por defecto; 45 para `merval_usd`, 75 para `clima_electoral`, 190 para
el consumo INDEC y 220 para los flujos de capital del BCRA. Medidos el
5-ago-2026 sobre las series reales, con margen.

`--validacion <archivo>` se agrega junto a `--snapshot` para poder testear G7
sin depender de la última corrida real.

### Consecuencias

- Una estadística de validación que se congela aparece nombrada en el log del
  gate en cada corrida, en vez de degradar las correlaciones en silencio.
- Un ancla que desaparece corta la publicación.
- Agregar un ancla a `FAMILIA` la pone bajo vigilancia automáticamente.

### Confirmación

`tests/test_gate_anclas_validacion.py`: anclas frescas pasan; una sin datos
bloquea; una congelada avisa sin bloquear; sin `panel_anclas` bloquea; y toda
ancla declarada en `FAMILIA` se verifica.

## Más información

### Limitaciones

- **Los topes detectan un congelamiento largo, no uno reciente.** Con 150 días
  de default, un ancla mensual puede perder cuatro publicaciones antes de que
  G7 diga algo. Detectar "no se movió respecto de la corrida anterior" sería más
  sensible y necesita guardar historia, que no está hecho.
- **La demora no bloquea, así que depende de que alguien lea el log.** Es una
  mejora enorme sobre no registrar nada, pero un ancla congelada durante meses
  puede seguir publicando correlaciones mientras la línea `[DEMORA]` se repite
  sin que nadie la mire. El aviso por issue de ADR-0173 sólo se dispara con
  fallas.
- **`n` se registra pero no se verifica.** Un ancla que pierde la mitad de su
  historia mantiene su último período fresco y pasa G7 sin problema.
- Este ADR llega por el camino más caro posible: el agujero lo encontró un
  `NameError` de hace meses, destapado por un aviso agregado para otra cosa.
  No hay razón para suponer que es el único insumo sin vigilancia — sí para
  suponer que los que existan se van a descubrir igual de tarde.
