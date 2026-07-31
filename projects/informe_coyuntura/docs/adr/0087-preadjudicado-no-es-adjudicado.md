---
madr: 4
id: '0087'
estado: 'aceptado'
fecha: 2026-07-19
cinturon: 'gestion'
indicadores: [concesiones_infraestructura]
archivos: ['gestion.py', 'descargar_series.py']
relacionado: ['0086']
ambito: '`concesiones_infraestructura` · ITCG · `gestion.py` · `descargar_series.py`'
origen: 'Lo encontró el test generalizado que introdujo ADR-0086, en su primera corrida'
---

# ADR-0087 — "Preadjudicado" contiene "Adjudicado"

## Contexto y planteo del problema

El indicador mide qué porcentaje de los kilómetros de la Red Federal de
Concesiones ya fue adjudicado. Una etapa contaba como adjudicada así:

```python
adjudicado = "ADJUDICADO" in estado.upper()
```

CONTRAT.AR informa cuatro estados para las etapas de la Red Federal. Uno de
ellos es **"Preadjudicado"** — y `"ADJUDICADO" in "PREADJUDICADO"` es `True`.

La etapa **II-B** estaba preadjudicada y se contó como adjudicada:

| | |
|---|---|
| km mal contados | **2.557,11 de 9.091** |
| indicador publicado | 56,9% |
| indicador correcto | **28,7%** |
| puntaje del indicador | 76,9 → **44,6** |

El error entró en julio de 2026, cuando la etapa II-B pasó a preadjudicada.
Hasta entonces el chequeo era correcto por casualidad: ninguna etapa había
estado en ese estado.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

El estado se evalúa con **frontera de palabra**:

```python
def _esta_adjudicado(estado: str) -> bool:
    return bool(re.search(r"\bADJUDICADO\b", (estado or "").upper()))
```

`\b` no matchea dentro de PREADJUDICADO —la `E` anterior es carácter de
palabra— y sigue aceptando variantes legítimas como "Adjudicado Parcial".

La misma comparación estaba **duplicada** en `descargar_series.py`, que es lo
que hizo que el error entrara también a la serie histórica y al store de fechas.
Ahora las dos usan la misma función.

### El store había quedado contaminado

`concesiones_fechas.json` sólo agrega etapas, nunca las saca: arreglar el código
no bastaba porque la etapa II-B ya estaba escrita con fecha 2026-07. Se eliminó
a mano, dejando el motivo en el propio archivo. Volverá a entrar sola cuando
CONTRAT.AR la muestre adjudicada de verdad.

Es una consecuencia general de los stores acumulativos que conviene tener
presente: **un bug de detección no se arregla sólo arreglando el detector**, hay
que revisar qué escribió mientras estuvo mal.

### Tests

Dos, en `tests/test_gestion.py`:

1. `_esta_adjudicado` contra los cuatro estados reales que CONTRAT.AR devolvía
   el 19-jul-2026, más las variantes de borde (`""`, `None`, "Adjudicado
   Parcial").
2. Que II-B **no** esté en el store. Si vuelve, el test obliga a verificar en el
   portal que esté adjudicada antes de aceptar el cambio.

### Consecuencias

- `concesiones_infraestructura`: 56,9% → **28,7%**, puntaje 76,9 → 44,6.
- La serie histórica corrige su último punto (jul-2026): 56,9 → 28,7. Los meses
  anteriores no cambian: el error existió sólo en julio.
- La lectura pública del indicador cambia de signo cualitativo. Con 56,9% el
  proceso aparecía pasada la mitad; con 28,7% está por debajo de un tercio, y lo
  que hay adjudicado son las etapas I y II-A.

## Más información

### Cómo apareció

No lo encontró el gate ni una revisión: lo encontró **el test que ADR-0086
acababa de generalizar a los tres índices**, en su primera corrida. El test
compara el puntaje del último punto de cada serie contra el puntaje publicado y
avisa si difieren en más de 20 puntos. Acá diferían en 32,3.

Vale registrar la secuencia, porque es el argumento a favor de escribir la
guardia y no sólo arreglar el caso: la guardia se escribió para un bug de
magnitudes en gestión (ADR-0086), y **su primer hallazgo fue un bug distinto,
de otra causa, en el mismo cinturón**. El G3 también lo marcaba, pero como
"card ≠ serie", que es el síntoma que produce cualquier desincronización y que
uno tiende a leer como frescura.

### Limitación que el episodio deja a la vista

El indicador cuenta una etapa como **todo o nada**, y ya estaba anotado en el
código que "las etapas II-B y III adjudican por renglones — refinamiento
pendiente, cuentan al cierre". Con la etapa II-B preadjudicada, esa
simplificación es la que separa 28,7% de 56,9%: no hay estado intermedio
posible. Mientras el proceso siga abierto, el indicador va a saltar 28 puntos de
golpe el mes que II-B se adjudique. **Se deja anotado como escalón conocido**,
no como algo que este ADR resuelva.
