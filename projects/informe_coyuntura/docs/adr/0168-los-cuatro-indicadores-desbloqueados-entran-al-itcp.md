---
madr: 4
id: '0168'
estado: 'aceptado'
fecha: 2026-07-31
cinturon: 'politica'
indice: 'ITCP'
indicadores: [produccion_legislativa, judicializacion, velocidad_resolucion, paralisis_denuncias]
archivos: ['scripts/itcp.py', 'scripts/politica.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts']
corrige: ['0166']
cierra: ['0134', '0135', '0137', '0139']
relacionado: ['0045', '0048', '0090', '0094', '0105', '0126', '0147', '0171', '0191', '0230']
continuado_por: ['0169', '0170']
ambito: 'Cinturón político (ITCP) · dimensiones `poder_judicial` y `poder_legislativo`'
origen: 'Implementación de los cuatro indicadores que ADR-0166 desbloqueó al fijar la orientación'
---

# ADR-0168 — Los cuatro indicadores desbloqueados entran al ITCP

## Contexto y planteo del problema

ADR-0166 resolvió la única decisión que bloqueaba a cuatro indicadores ya
construidos y versionados: la orientación. Faltaba construirlos.

La dimensión `poder_judicial` era el caso más urgente. ADR-0126 la abrió con un
solo indicador y dejó escrito que eso *"es una limitación real, no un diseño
terminado"*: `cobertura_judicial` mide la **capacidad** de integrar el Poder
Judicial —cuántos cargos tienen juez— y no su **comportamiento**. El 15% del
cinturón colgaba de un dato.

## Factores de decisión

- Los cuatro datasets ya estaban relevados y versionados; lo que faltaba era
  banda, peso y cableado, no fuente.
- ADR-0105 fija el orden para justificar anclas: referencia externa primero,
  valor con significado propio después, conceptual al final. Dos de los cuatro
  admiten ancla externa real, y eso baja la circularidad en vez de subirla.
- ADR-0045 prohíbe calibrar contra el rango observado bajo la administración
  medida. Ninguna de las cuatro bandas se calibró así.

## Opciones consideradas

- **Entrar los cuatro con las anclas de mayor jerarquía disponible** — elegida.
- **Entrar sólo los que tienen serie mensual**, dejando los dos anuales fuera —
  descartada: el bloque judicial seguiría colgando de un indicador y la
  frecuencia se declara, no se esconde.
- **Esperar a después del lanzamiento** — descartada por decisión del editor.

## Decisión

### 1. `poder_judicial` pasa de 1 a 4 indicadores

`cobertura_judicial` conserva el peso mayor (0,40) por ser el único mensual y el
de menor rezago —1 mes contra 2 a 12 de los otros tres—. Los tres nuevos entran
parejos en 0,20, sin razón para ordenarlos entre sí: es el mismo criterio con
el que ADR-0074 repartió la dimensión de financiamiento.

### 2. `poder_legislativo` pasa de 5 a 6

Entra `produccion_legislativa` con 0,15 y los cinco existentes ceden
proporcionalmente (×0,85), de modo que el orden relativo no se toca — mismo
procedimiento que ADR-0069. Los pesos entre dimensiones no se mueven.

### 3. Se puntúa el denominador de la agenda común, no el cociente

ADR-0137 midió que el cociente de origen se mueve por abajo: el numerador
—leyes de origen Ejecutivo en 12 meses— es estable entre 5 y 10 en todo el
período, y lo que se derrumbó fue la producción propia del Congreso. Puntuar el
cociente publicaría *"el Ejecutivo domina la agenda"* exactamente cuando lo que
pasó es que el Congreso dejó de sancionar. Se puntúa el total de leyes, que es
el número que efectivamente se mueve; el cociente queda como lectura de
composición en el detalle.

### 4. Las anclas

| Indicador | Ancla | Categoría |
|---|---|---|
| `produccion_legislativa` | 74,4 leyes/año, promedio de 18 años completos y cuatro presidencias (2008-2025, 1.340 leyes) | `externa` |
| `judicializacion` | 0,78% de densidad cautelar promedio 2016-2019, contra 1,66% de 2020-2026 | `historia_larga` |
| `velocidad_resolucion` | 100% = la Corte resuelve exactamente lo que le entra | `conceptual` |
| `paralisis_denuncias` | cortes redondos sobre sesiones por año de dos comisiones | `conceptual` |

Los valores vigentes caen en bandas intermedias —40, 40, 85 y 65— o sea que
discriminan en todo el recorrido y no saturan.

### Consecuencias

- La circularidad del ITCP **no sube**: el trinquete de ADR-0105 pasa, porque
  las dos anclas ajenas al período compensan a las dos conceptuales.
- **El signo de `velocidad_resolucion` es incómodo y está asumido**: una Corte
  más lenta le da más puntaje al Gobierno. El ITCP mide capacidad de gobernar
  sin fricción (ADR-0048), no salud institucional, y una causa que tarda años
  deja en pie mientras tanto lo que se discute. Es la misma incomodidad que
  ADR-0090 resolvió para `ratio_dnu`, por la misma vía: el signo sale de la
  pregunta declarada, no de si el resultado agrada. Queda escrito en la ficha.
- La familia `tension` de ADR-0094 gana cuatro indicadores. Al leer la card de
  lectura por partes hay que tener presente que parte del movimiento de esa
  familia es composición y no señal — ADR-0166 lo anotó como limitación y acá
  se materializa.

### Confirmación

`tests/test_politica_judicial.py` fija la composición nueva de la dimensión y
que `cobertura_judicial` conserve el peso mayor; `tests/test_itcp.py` fija los
pesos internos de `poder_legislativo` y que eficacia siga primera;
`tests/test_procedencia_anclas.py` exige que los cuatro declaren de dónde sale
su ancla y que la circularidad no suba; `tests/test_web_labels.py` y
`tests/test_fichas_bandas.py` cubren la capa de display.

El colector de `produccion_legislativa` se validó contra el relevamiento
independiente de ADR-0137: calculado desde la fuente reproduce **exacto** el
rango 15-47 y los 32 puntos que ese ADR documentó por separado.

## Más información

### Corrección a ADR-0166

ADR-0166 anotó que, fijada la orientación, el propio ADR-0134 derivaba medir
*"Disciplina sola"*. **Es incorrecto y los datos crudos lo desmienten**: la
comisión de Disciplina tiene **8 sesiones en cuatro años** —una cada seis meses
y medio— lo que la convierte en un indicador de evento, que es exactamente la
clase que ADR-0147 dejó suspendida hasta saber cuántos eventos hay. Se
implementa la opción (a) de ADR-0134: sesiones de **ambas** comisiones en
ventana móvil de 12 meses, 32 puntos mensuales y rango 2 a 7.

Es el mismo modo de falla que ADR-0139 corrigió tres veces: cerrar un punto
razonando sobre el ADR en vez de mirar el dato.

### Limitaciones

- **Dos de los cuatro son anuales** (`judicializacion`, `velocidad_resolucion`)
  y están declarados con el rezago más alto del índice, 9 y 12 meses. La card
  de rezago de ADR-0092 los va a mostrar como lo que son: descripción de otro
  año, no pulso de hoy.
- **Tres de los cuatro leen un relevamiento versionado y no la fuente en vivo.**
  Sólo `produccion_legislativa` consulta el CKAN de HCDN en cada corrida. Para
  `velocidad_resolucion` la fuente no admite consulta automática (ADR-0140); en
  `judicializacion` y `paralisis_denuncias` el refresco automático es trabajo
  pendiente y se declara acá para que no se confunda un store curado con un
  indicador vivo.
- `paralisis_denuncias` cuenta que la comisión se reúna, no que resuelva. Las
  acciones concretas contra un magistrado son cuatro en veinte meses y siguen
  siendo el fenómeno que ADR-0147 mantiene suspendido.
