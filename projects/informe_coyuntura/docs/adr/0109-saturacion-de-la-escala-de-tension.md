---
madr: 4
id: '0109'
estado: 'aceptado'
nota_estado: 'Aceptado (observación verificada, sin cambio de método)'
fecha: 2026-07-20
cinturon: 'vida'
archivos: ['itvc.tension_de_itvc']
relacionado: ['0231', '0233', '0235']
ambito: 'ITVC · `itvc.tension_de_itvc` · presentación por componente'
origen: 'Auditoría de Vida Cotidiana, punto 3.1 y recomendación 1 (prioridad alta)'
---

# ADR-0109 — Saturación de la escala de tensión: verificada, no requiere cambio

## Contexto y planteo del problema

La auditoría marcó como su recomendación de mayor prioridad "desaturar la escala
de tensión". Cinco de los catorce componentes operan contra el techo o el piso
de la escala 0-10, y de ahí concluía:

> "El efecto práctico es que, para estos cinco componentes, el cinturón deja de
> distinguir entre «malo» y «muy malo» (o entre «bueno» y «muy bueno»): una mora
> que siga deteriorándose o un patentamiento que siga en boom no mueven más la
> aguja."

Proponía recalibrar la pendiente por componente o migrar a percentil/z-score.

La saturación medida al tomar esta decisión era real: `mora_familias` daba
tensión cruda 21,3 y el entonces `peso_tarifas` 10,7 contra un techo de 10;
`endeudamiento_familiar`, `patentamiento_motos` y
`sentimiento_digital` dan −3,0, −3,0 y −2,5 contra un piso de 0.

**Estado del caso tarifario:** ADR-0235 reemplazó IPC Regulados/RIPTE por la
canasta IIEP y anclas internacionales por rubro. La tabla siguiente conserva
el contrafáctico que justificó esta decisión general, pero esos valores de
`peso_tarifas` ya no describen el indicador vigente.

## Opciones consideradas

- **No tocar la escala de tensión** — elegida: la recomendación de la auditoría pasa a «verificada, no requiere cambio».
- **Recalibrar la escala** — descartada por la evidencia medida.

## Decisión

- La escala de tensión **no se toca**.
- La recomendación 1 de la auditoría pasa a **"verificada, no requiere cambio"**,
  con la evidencia de arriba como respuesta.
- Queda anotado el efecto de la winsorización como el recorte que sí merece
  seguimiento.

## Más información

### Por qué no requiere cambio

**La conclusión no se sostiene: la aguja sí se mueve.**

El ITVC promedia los **índices base 100** de sus componentes, no sus tensiones.
La tensión por componente (`aporte_score`) se calcula sólo para mostrarla en el
modal — `IndicadorModal.astro` es su único consumidor — y no entra en ningún
cálculo. El recorte a [0,10] es un recorte **de presentación**.

Simulando el deterioro que la auditoría describe:

| componente | índice | ITVC | tensión del cinturón |
|---|---|---|---|
| `mora_familias` | 18,3 → 0,0 | 95,40 → 94,50 | 5,9 → 6,1 |
| `peso_tarifas` | 71,5 → 30,0 | 95,40 → **89,20** | 5,9 → **7,2** |

Un componente saturado que sigue empeorando mueve el índice de forma
proporcional a su peso, sin tope. Que `mora_familias` mueva poco es su peso
efectivo del 5%, no la escala: `peso_tarifas`, con 15%, mueve 6,2 puntos de
ITVC ante el mismo ejercicio.

**Y el mínimo que pedía ya está implementado, con más alcance del que el
documento le atribuye.** La auditoría dice "como mínimo, publicar junto al valor
recortado el valor crudo (ya lo hacen mora y tarifas) de forma sistemática".
Los **cinco** componentes saturados lo hacen hoy, en las dos direcciones, y el
texto viaja pegado al número: el gauge muestra 10/10 y la línea inmediatamente
debajo dice que la tensión equivalente era 21,3 y que la escala se corta. Los
winsorizados declaran además su índice crudo (173,3 y 166,8).

Recalibrar la pendiente cambiaría la escala pública de todo el cinturón —la
misma fórmula produce la tensión del cinturón— para corregir un problema que no
existe en el cálculo. Es la doctrina de ADR-0045 aplicada a la inversa: no se
mueve un parámetro para que un número quede mejor, tampoco cuando lo pide una
auditoría.

### Lo que la verificación sí encontró

Hay un recorte que **sí** entra al índice, y es otro: la **winsorización al
techo de 140** (ADR-0033). Su efecto agregado nunca se había medido:

| | ITVC | tensión |
|---|---|---|
| con winsorización (publicado) | **95,40** | 5,9 |
| sin winsorización | 97,30 | 5,5 |
| efecto | **−1,90 puntos** | −0,4 |

Es deliberado y está declarado en cada card afectada —"un boom puntual de un
componente no compra compensación ilimitada en el promedio"— pero conviene
tener el número: hoy la winsorización empeora el ITVC en 1,9 puntos, y ese
efecto crece si más componentes se van al techo.

Se conecta con ADR-0108: `endeudamiento_familiar` está en el techo 19 de 31
meses, lo que además degrada su medición de redundancia. Si algún día conviene
revisar un recorte del ITVC, es éste y no la escala de tensión.
