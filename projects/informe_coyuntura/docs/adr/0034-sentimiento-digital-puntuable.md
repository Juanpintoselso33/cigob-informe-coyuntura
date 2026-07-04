# ADR-0034 — Sentimiento digital: de contexto a componente del ITVC

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-04 |
| **Ámbito** | `sentimiento_digital` (10% de Confianza = 1,5% del ITVC) + pesos internos de Confianza |
| **Disparador** | El editor pidió probar alternativas empíricamente ("a ver si alguna funciona") |

## Contexto

`sentimiento_digital` (interés de búsqueda en Google sobre inflación, precios,
inseguridad y trabajo) era contexto: la escala de Trends es relativa a la
ventana consultada y se renormaliza en cada corrida, lo que parecía impedir
un B100 contra el 4T-2023.

## El banco de pruebas (04-jul-2026)

| Variante | B100 | Estabilidad | r vs IPC m/m |
|---|---|---|---|
| pytrends ventana fija oct-23→hoy (semanal→mensual) | 143,9 | 3 corridas idénticas (amplitud 0,0) | — |
| **pytrends 2021→hoy (mensual nativo)** | 138,1 | ✓ | **+0,76** |
| Wikipedia pageviews (conteos absolutos) | 573 | perfecta | +0,62 |

**El cociente intra-consulta cancela la renormalización**: base y valor
actual salen de la MISMA respuesta, así que el B100 no depende de la escala.
Verificado empíricamente (amplitud 0,0 entre corridas). Wikipedia quedó
descartada: las visitas a "Inflación en Argentina" colapsaron 6× desde el
pánico de dic-2023 — detector de eventos, no índice.

## Decisión

1. **Puntúa en Confianza con 10%**: le cede el ICC (50→45 — mide lo mismo por
   encuesta; el Trends lo mide por conducta) y motos (10→5 — el componente
   más eufórico). Reparto: ICC 45 / IVI 30 / sentimiento 10 / carne 10 /
   motos 5. Enmienda a los pesos internos del doc 260702, documentada acá.
2. **Serie mensual de ventana fija** (2021→hoy, resolución mensual nativa,
   canasta de las 4 keywords, mes en curso descartado por incompleto), B100
   vs 4T-2023 invertido (más búsquedas de urgencia = peor).
3. **Store persistente con REEMPLAZO TOTAL** en cada descarga sana: valores
   de corridas distintas tienen escalas distintas y NUNCA se mezclan. Si
   Google throttlea (429), la serie sale del store.
4. **La card conserva el pulso en tiempo real** (ventana 3 meses, diaria) —
   el doble registro card/serie queda declarado en el detalle. El cinturón
   espíritu de época (que comparte el indicador) no se toca: su barrido lo
   revisará.

## Validez y límites declarados

- r = +0,76 con la inflación mensual — la validación de constructo más alta
  del cinturón (la gente googlea "inflación" cuando los precios queman).
- Constructo blando: mide *atención*, no sentimiento (una noticia dispara
  búsquedas sin que cambie el bolsillo). Peso chico (1,5% del ITVC) acorde.
- Fuente no-oficial (pytrends) con rate limits — amortiguado por el store.
- B100 hoy: 135,9 (la urgencia digital es ~26% menor que en el pánico del
  4T-2023) — bajo el techo de winsorización de 140 (ADR-0033), que lo acota
  si algún día la euforia lo pasa.

## Consecuencias

- ITVC 90,5 → **90,7** · Confianza 102,1 → 103,8 · 13/13 indicadores puntúan
  (cero contexto en vida).
- Bonus del mismo push: verdes/rojos con polaridad en las series de vida que
  cruzan el cero (IPI m/m, endeudamiento) — paridad visual con macro.
