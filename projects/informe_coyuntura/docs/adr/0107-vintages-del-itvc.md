---
madr: 4
id: '0107'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
archivos: ['publicar._vintages', 'publicar._fecha_dato_a_date']
extiende: ['0099']
ambito: 'ITVC · card pública "Fechas de los datos" · `publicar._vintages` · `publicar._fecha_dato_a_date` (nuevo)'
origen: 'Auditoría metodológica del cinturón Vida Cotidiana, punto 3.2 (prioridad alta)'
---

# ADR-0107 — El cinturón de vida cotidiana declara de cuándo es cada dato

| **Extiende** | ADR-0099 (la card, creada para ITCM/ITCG/ITCP) |

## Contexto y planteo del problema

La auditoría de vida cotidiana señaló que la lectura "hoy" del cinturón combina
datos de entre enero y julio de 2026 sin una vista consolidada:

> "Cada ficha documenta honestamente su propio rezago, pero el cinturón no
> ofrece una vista consolidada de a qué mes corresponde realmente cada pieza del
> dato «hoy». […] conviene hacerlo explícito a nivel de cinturón para que un
> lector no interprete el ITVC de «hoy» como una fotografía de un único mes."

Marcó además por qué acá pesa más que en otros cinturones: los dos componentes
más rezagados —informalidad laboral y subocupación demandante— vienen de la EPH
trimestral del INDEC, y uno de ellos está en **la dimensión de mayor peso
nominal del cinturón (35%)**.

La card que resuelve esto ya existía desde ADR-0099. Nunca se le había puesto al
ITVC.

## Opciones consideradas

- **Calcular la antigüedad de cada dato del ITVC** y publicarla — elegida: 2,8 meses de antigüedad media ponderada y 198 días entre el dato más nuevo y el más viejo.
- **No declararla** — es el estado que este ADR cierra.

## Decisión

`_vintages(c, "itvc")`. El resultado publicado: **2,8 meses** de antigüedad
media ponderada y **198 días** entre el dato más nuevo y el más viejo, con
informalidad y subocupación a 6,6 meses encabezando la lista.

### Consecuencias

- `tests/test_vintages_itvc.py` (4 casos). El que importa es el tercero: recorre
  **los cuatro índices** y falla si algún componente que puntúa tiene una fecha
  que el perfil no puede leer. Es el guard que faltaba — una card que cubre
  menos de lo que dice es peor que no tenerla.
- ITCM, ITCG e ITCP no cambian de valor: ninguno tenía fechas mensuales, que es
  por lo que el defecto no había aparecido antes.

## Más información

### Limitaciones

La auditoría trae cuatro hallazgos de prioridad alta y éste es uno. Quedan
abiertos, en orden de peso: la **saturación de la escala de tensión** (cinco de
catorce componentes contra el techo o el piso), la **taxonomía de la dimensión
"Confianza y seguridad"** y los **vacíos temáticos** (pobreza, alquileres,
expectativas). Los tres exigen decisión editorial, no sólo implementación.

### El bug que apareció al conectarla

Conectarla no era una línea. `_vintages` parseaba `fecha_dato` con
`date.fromisoformat` dentro de un `try/except ValueError: continue`, y **tres de
los catorce componentes del ITVC fechan su dato con rótulo mensual**
(`consumo_carne`, `inseguridad`, `patentamiento_motos` traen `"2026-04"`, que
`fromisoformat` rechaza).

Agregar la línea sin más habría publicado una card que dice describir el
cinturón entero **calculada sobre once componentes**, sin ningún aviso — y dos
de los tres que se caían son justamente indicadores que la misma auditoría
discute. El modo de falla es el de ADR-0082 y ADR-0089: lo que se descarta en
silencio no se descubre hasta que alguien lo busca.

Se corrige en el nivel general, no sólo para el ITVC: `_fecha_dato_a_date` lee
el rótulo mensual como el primero de ese mes —la lectura conservadora, la más
antigua posible— y lo que sigue siendo ilegible ahora **avisa por consola** en
vez de desaparecer.

### Precisión en el texto público

Un rótulo mensual se escribe **sin día**: "abril de 2026", no "1 de abril de
2026". La fuente sólo conoce el mes, y agregar un día es una precisión que el
dato no tiene. Antes de este cambio la card habría mezclado "1 de enero de 2026"
con `2026-04` crudo en la misma lista.
