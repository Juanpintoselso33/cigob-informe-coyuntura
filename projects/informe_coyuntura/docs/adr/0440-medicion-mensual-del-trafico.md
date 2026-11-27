---
madr: 4
id: '0440'
estado: 'aceptado'
fecha: 2026-11-26
cinturon: 'transversal'
archivos: ['scripts/medir_trafico.py', '../../.github/workflows/trafico-mensual.yml', 'tests/test_medir_trafico.py']
relacionado: ['0180', '0439', '0442']
ambito: 'Medición · informe mensual de tráfico con GA4 y Search Console'
origen: 'Juan, 26-nov-2026, sobre la investigación de SEO y tráfico: «8 dale programa».'
---

# ADR-0440 — Medición mensual del tráfico

## Contexto y planteo del problema

En los 30 días al 25-nov-2026 el Monitor tuvo 187 usuarios. Con ese volumen un A/B no distingue nada del azar,
y los cambios para mejorar el tráfico (ADR-0439 y los que sigan) necesitan una forma de ver si movieron algo.
Hasta ahora los números se sacaban a mano en cada consulta.

## Factores de decisión

- Comparar antes y después, de a un cambio por vez.
- Que no dependa de que alguien se acuerde.
- Sin dependencias ni credenciales nuevas.

## Opciones consideradas

1. Un script mensual que lee GA4 y Search Console con la cuenta de servicio de ADR-0180 y deja un informe en
   `output/trafico/`, lanzado por un workflow el día 2.
2. Un tablero en Looker Studio.
3. Seguir a mano.

## Decisión

**Opción 1.** `scripts/medir_trafico.py` mide el mes anterior (usuarios, orígenes con WhatsApp, IA y buscadores
separados, páginas, eventos y el muro, consultas y páginas de Search Console), lo compara con el mes previo y
lista los ADR de presentación de ese mes, que son los cambios que pueden explicar una diferencia. Looker Studio no
tiene API (se descartó en agosto) y no deja registro versionado.

El informe trae diez preguntas fijas para hacer a mano en ChatGPT, Gemini y Perplexity: ninguno ofrece gratis una
API de respuestas con búsqueda, y lo que sirve es repetir las mismas preguntas mes a mes.

### Consecuencias

- Un commit del bot por mes a `main` (un deploy más por mes).
- Si la cuenta de servicio no tiene una propiedad de Search Console, el informe lo dice en vez de fallar.

### Confirmación

Corrido en local el 26-nov-2026 para octubre y noviembre con datos reales; `tests/test_medir_trafico.py` cubre
fechas, el filtro de cambios y el informe.

## Pros y contras de las opciones

- **Opción 1.** A favor: automático y versionado. En contra: las preguntas a la IA siguen siendo a mano.
- **Opción 2.** A favor: gráficos. En contra: se arma a mano y no queda en el repo.
- **Opción 3.** En contra: no se hace.

## Más información

Investigación de SEO y tráfico del 26-nov-2026, recomendación 8.
