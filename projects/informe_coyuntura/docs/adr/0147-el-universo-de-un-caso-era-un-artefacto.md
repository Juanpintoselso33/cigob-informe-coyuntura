---
madr: 4
id: '0147'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
relacionado: ['0168', '0230']
ambito: 'cinturón político (ITCP) · bloque judicial'
origen: 'al intentar responder la última decisión editorial abierta'
---

# ADR-0147 — El universo de un caso era un artefacto de la consulta

- **Afecta**: ADR-0131 (universo del veto), ADR-0146 (regla de codificación)

## Contexto y planteo del problema

### La pregunta que se iba a responder

ADR-0131 dejó abierto: con **un caso en treinta y un meses**, ¿puede el ITCP
alojar un indicador de evento que pasa la mayoría de los meses sin novedad, o
conviene agregarlo con otros del bloque judicial?

**No se responde, porque su premisa es falsa.** El uno no es el fenómeno: es un
artefacto de cómo se armó el universo.

## Opciones consideradas

- **Suspender la decisión editorial pendiente, no responderla** — elegida: no tiene sentido decidir si el ITCP admite un indicador de evento antes de saber cuántos eventos hay.
- **Responderla ahora** — descartada: su premisa era falsa. El universo de un caso era un artefacto de la consulta.

## Decisión

1. **La decisión editorial pendiente queda SUSPENDIDA, no respondida.** No tiene
   sentido decidir si el ITCP admite un indicador de evento antes de saber
   cuántos eventos hay. Con dos casos aparecidos en una barrida de cuarenta
   registros, el fenómeno es plausiblemente varias veces más frecuente que uno
   cada treinta y un meses.
2. **El universo hay que reconstruirlo desde el campo controlado del CSJN**
   (`inconstitucional`), no desde texto libre sobre SAIJ. Es la misma corrección
   de fondo que ADR-0140 ya había identificado: el concepto está oficialmente
   operacionalizado como atributo del fallo.
3. **Eso sigue bloqueado por acceso, no por concepto**: el endpoint abierto del
   CSJN topea en 10 registros por consulta y el buscador completo está tras
   CAPTCHA (ADR-0140). El camino es el pedido de acceso a la información pública,
   que ADR-0140 ya dejó formulado con precisión: *cantidad de fallos con
   `inconstitucional = true` por año, 1994-2026*.
4. **La primera pasada de ADR-0131 no se tira.** Sus 17 casos siguen codificados
   y la regla de ADR-0146 sigue en pie; lo que cambia es que ese universo se sabe
   **incompleto**, y así queda anotado en el registro.
5. **El detector sigue acumulando** (ADR-0141). Cada corrida agrega los fallos
   nuevos con su flag, de modo que cuando se pueda contar, habrá historia
   revisada.

## Más información

### La evidencia

El universo de ADR-0131 salió de una consulta de texto libre sobre la
jurisprudencia de SAIJ:

```
(texto:"declaración de inconstitucionalidad" AND texto:decreto
 AND fecha-rango:[20231210 TO 20261231])
```

**La ventana llega hasta el 31-dic-2026. El caso más reciente que devuelve es del
20-feb-2025. Cero casos en todo 2026** — diecisiete meses sin un solo documento.

Mientras tanto, el detector del CSJN (ADR-0141), en **una sola barrida de 40
registros**, encontró **dos fallos con el campo controlado `inconstitucional =
true`, ambos de 2026**:

| fecha | fuero | carátula | materia |
|---|---|---|---|
| 30-abr-2026 | CAF | TORRES ABAD c/ **EN-JGM** s/habeas data | administrativo - constitucional |
| 02-jul-2026 | CSS | JUSTO c/ **ANSES** s/amparos | previsional — «**excesos en las facultades reglamentarias**» |

**Ninguno de los dos está entre los 17.**

### Por qué falló, y por qué importa

Dos causas que se suman:

1. **La consulta es de texto libre y es estrecha.** Exige la frase «declaración
   de inconstitucionalidad» junto con la palabra «decreto». Un fallo que anula
   una resolución por exceso reglamentario no tiene por qué contener ninguna de
   las dos.
2. **La base de sumarios de SAIJ es curada y va con rezago.** No es un censo: es
   lo que la Dirección de Información Jurídica alcanzó a sumariar. El corte de
   hecho en feb-2025 sugiere un rezago del orden de un año y medio.

Es la **quinta** vez que una búsqueda de texto sobre una base legal cuenta lo que
no es —ADR-0068, 0091, 0096, 0131— pero con una vuelta de tuerca nueva: acá el
problema no fue contar de más, fue **contar de menos**. El falso negativo es más
peligroso porque no se nota: un universo chico parece un fenómeno raro.

### Un dato que valida la regla de ADR-0146

El caso **JUSTO c/ ANSES** está titulado «**excesos en las facultades
reglamentarias**» — exactamente la doctrina que ADR-0146 dictaminó ayer que
**sí** cuenta como veto de constitucionalidad (art. 99 inc. 2 CN).

Es decir: la regla escrita para resolver un caso de SAIJ captura un caso hallado
por otra vía, en otra base, con otro método. **Validación independiente de la
regla**, no buscada.

### Consecuencia para el método, más allá de este indicador

Cuando una consulta de texto libre devuelve **cero resultados en un tramo
reciente y largo**, eso no es evidencia de que no pasó nada: es motivo para
sospechar de la consulta o del rezago de la base. Acá el tramo vacío eran
diecisiete meses y se había leído como «el fenómeno es rarísimo».
