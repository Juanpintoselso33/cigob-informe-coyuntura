---
madr: 4
id: '0112'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
indicadores: [empleo, indice_lider, itvc_lider]
corrige: ['0111']
complementado_por: ['0130']
ambito: 'ITVC · dimensión `empleo` · `indice_lider` (nuevo) · serie `itvc_lider`'
origen: 'Auditoría de Vida Cotidiana, punto 3.6 (expectativas a futuro)'
---

# ADR-0112 — El cinturón incorpora su primera medida prospectiva

| **Corrige** | ADR-0111, que declaró la ausencia irresoluble |

## Contexto y planteo del problema

### Qué corrige de ADR-0111

ADR-0111 cerró el frente de expectativas así: *"las únicas series vivas son de
inflación esperada y terminan en 2026-01 — seis meses de rezago"*.

**Eso era falso, y el error fue de método.** Se consultó el espejo de la serie
en datos.gob.ar, que efectivamente está desactualizado, y se dio por cerrado el
punto sin ir a la fuente. La **Encuesta de Expectativas de Inflación de la
UTDT** publica mensualmente y su último dato es de **junio de 2026** —tan fresco
como el resto del cinturón—, con serie propia desde agosto de 2006.

Es exactamente el modo de falla que el proyecto ya tiene documentado: declarar
un negativo tras una consulta, cuando la fuente existía con otro nombre o en
otro lugar.

## Opciones consideradas

- **Incorporar la Encuesta de Expectativas** como primera medida prospectiva del cinturón — elegida.
- **Mantener el cierre de ADR-0111** («las únicas series vivas terminan en 2026-01, seis meses de rezago») — descartada: **era falso, y el error fue de método**. Se consultó el espejo de la serie en datos.gob.ar, que sí está desactualizado, y se dio el punto por cerrado sin ir a la fuente.

## Decisión

### Consecuencias

- El scraper de la UTDT se generalizó: `_utdt_xls(listado_url)` sirve para
  cualquiera de sus páginas de serie histórica, que comparten el mismo patrón.
  El colector trae ICC e Índice Líder, y un fallo del segundo no tumba al
  primero.
- El ITVC pasa a **16 componentes** y el tablero a **60 indicadores**.

## Más información

### Limitaciones

- **Anticipa el ciclo económico, no el humor de los hogares.** Un giro señala
  hacia dónde va la actividad, no cómo la están viviendo las familias. Es la
  aproximación disponible a "expectativas", no la medida ideal.
- **Como todo índice líder, da señales falsas**: puede moverse sin que el giro
  se produzca.
- Es un compuesto y no publica el detalle mensual de qué lo movió.

### Por qué la inflación esperada tampoco entra

Corregido el dato, el indicador **sigue sin poder entrar al ITVC**, pero por una
razón distinta y verificable: **su rango dinámico no cabe en la escala.**

Las expectativas cayeron de 149,7% (4T-2023) a 32,1% (jun-2026). Rebaseado como
cualquier otro componente, el índice llega a **466** contra un techo de
winsorización de 140 (ADR-0033). Cruzaría el tope a mediados de 2024 y quedaría
clavado ahí dos años: un componente constante, que no aporta información y
además arrastra la winsorización agregada.

Una variable que mejoró 78% no entra en un índice base-100 diseñado para
movimientos de ±40%. Ninguna reexpresión monótona lo arregla.

### Lo que sí entra: el Índice Líder

**UTDT — Índice Líder (IL)**, mensual desde enero de 1993, último dato mayo de
2026. Es un compuesto de señales tempranas construido para **anticipar puntos de
giro del ciclo**.

| | |
|---|---|
| rango rebaseado (dic-23 → hoy) | **85,2 – 103,4** |
| techo de winsorización | 140 (no lo toca) |
| redundancia máxima en niveles | +0,730 (`endeudamiento_familiar`) |
| redundancia máxima en **diferencias** | **+0,423** (`brecha_salario_cbt`) |

Cabe en la escala y aporta señal propia: un solo par sobre el umbral en niveles
y ninguno al destendenciar.

### Dónde entra y por qué

**Prospectivas de empleo, con 20%** (IPI 36 · ISAC 32 · subocupación 12 · líder
20). La dimensión se llama prospectiva pero **sus tres componentes describen lo
que ya pasó**: el IPI y el ISAC son contemporáneos y la subocupación llega con
dos trimestres de rezago. El Índice Líder es lo único del cinturón que mira
adelante.

Los tres existentes ceden proporcionalmente (×0,8), conservando su orden
relativo. **El peso nominal de la dimensión no se toca**: la arquitectura de
cinco dimensiones queda intacta, igual que en ADR-0111.

**ITVC 94,6 → 94,7.** El efecto es mínimo porque el índice del componente (94,8)
está muy cerca del promedio de su dimensión; lo que aporta no es nivel sino
capacidad de anticipar.

### Otras fuentes relevadas

La UTDT publica además el **Índice de Confianza en el Gobierno (ICG)** y el
**Índice de la Confianza en la Justicia (ICJ)**. Ninguno tiene página de serie
histórica descargable —el ICG sólo difunde informes— así que quedan fuera por
acceso, no por pertinencia. El ICG en particular es candidato natural del
cinturón de espíritu de época si alguna vez publica su serie.

El ICC de la UTDT **no** se desagrega en presente vs. futuro: sus subíndices son
situación personal, situación macro y bienes durables. El corte de expectativas
que la auditoría imaginaba no existe en esa fuente.
