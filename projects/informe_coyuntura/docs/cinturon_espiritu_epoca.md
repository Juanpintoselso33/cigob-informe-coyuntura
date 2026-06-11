# Cinturón Espíritu de Época

| Campo | Valor |
|---|---|
| Script | `scripts/espiritu_epoca.py` |
| Cache | `output/cache/espiritu_epoca.json` |
| Peso en score global | 20% en fase temprana del mandato · 15% en consolidación (ver `config.py`) |
| Barbarismo de riesgo | político |

## Encuadre

Marco metodológico: **"Marco Conceptual del Informe de Coyuntura"** (Fundación CIGOB, mayo 2026; `260606 MARCO CONCEPTUAL lINFORME DE COYUNTURA.docx`), que amplía los tres cinturones de Matus a cinco. El quinto mide la **sintonía emocional** del gobierno con los sentimientos colectivos: la "política de las emociones", aceleradas y amplificadas por redes sociales. Apretar este cinturón significa desconexión entre el gobierno y el humor social ("este gobierno no nos representa emocionalmente").

Score 0–10: mayor = mayor desconexión con el humor social. **v1 provisional**: promedio simple de tres proxies; el documento conceptual no define indicadores numéricos ni paramétrica propia. Cuando CIGOB formalice una fórmula (como hizo con el ITCM macro), reemplazar este scoring.

## Indicadores activos (v1)

| Indicador | Qué mide | Fuente de lectura | Tensión 0–10 |
|---|---|---|---|
| `icc_utdt` | Confianza del consumidor (humor económico) | Último `scripts/vida_cotidiana/data/vida_cotidiana_*.json` | `(60 − v) / 3` |
| `sentimiento_digital` | Interés de búsqueda en términos de malestar (inflación, precios, inseguridad, trabajo) | Ídem (Google Trends; busca hacia atrás si el último vino null por rate-limit) | `v / 10` |
| `clima_electoral` | Ventaja LLA−PJ del Votómetro (adhesión al oficialismo) | `output/cache/politica.json` → `votometro_ventaja_lla` | `5 − v/3` |

El colector **no re-extrae nada**: lee outputs que el pipeline ya genera (correr después de `vida_cotidiana/main.py` y `politica.py`). `icc_utdt` y `sentimiento_digital` se comparten con el cinturón Vida Cotidiana — miden a la vez bolsillo y humor; en la web cada cinturón muestra su propia ficha (claves namespaced `slug.indicador` en el modal).

## Limitaciones conocidas

- `sentimiento_digital` mide **interés de búsqueda**, no polaridad: un pico puede ser preocupación o simple noticia. Una versión con análisis de sentimiento real (NLP sobre redes) queda para v2.
- `apatia_electoral` (voto en blanco/nulo + ausentismo) está **pendiente**: el Votómetro no publica blanco/nulo por encuesta. Cuando lo incorpore, sumarlo acá.
- La **ponderación temporal** del doc conceptual (en los primeros 2–4 años de gobierno, gestión y espíritu de época pesan más) está implementada en `config.py`: fase temprana (primeros 4 años del mandato, pesos parejos 20%) vs. consolidación (25/25/20/15/15). El doc no fija números: los valores son operacionalización propia, ajustar cuando CIGOB los formalice.

## Ejecución

```bash
cd projects/informe_coyuntura
python scripts/espiritu_epoca.py
```

Códigos de salida: 0 = 3/3 frescos · 1 = al menos uno fresco · 2 = todo desde cache.
