# ADR-0001 — Todos los indicadores se calculan de datos oficiales; nunca valores hardcodeados

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-06-26 |
| **Ámbito** | Transversal a todo el informe (principio rector) |

## Contexto

El informe debe ser **reproducible y defendible**: cualquier número que publica
tiene que poder rastrearse hasta un dato oficial y recalcularse solo cada día/mes.
Durante el rediseño del cinturón macro aparecieron varias tentaciones de "cerrar"
un indicador con un valor cargado a mano (una calibración, un componente que no se
encontraba en una API, un override de criterio). En todos los casos, un número
hardcodeado:

- se desactualiza en silencio (nadie lo refresca y nadie se entera),
- rompe la trazabilidad (no se sabe de dónde salió ni cuándo se tocó),
- y vuelve frágil al pipeline diario (un dato congelado contamina el score).

## Decisión

**Ningún indicador del informe puede depender de un valor numérico hardcodeado o
de una constante de calibración cargada a mano.** Todo se calcula a partir de
datos oficiales obtenidos en tiempo de ejecución (APIs, planillas, balances).

Corolarios:
- Si un dato no está en una fuente automatizable, se busca **la fórmula sobre
  datos** que lo reproduzca (ver ADR-0005, donde el Bopreal salió del bucket de
  vencimiento de la planilla SDDS en vez de cargarse a mano).
- El **único** valor admitido en un archivo de configuración es el **juicio
  cualitativo y fechado del analista** (`data/macro/ajustes_itcm.json`): un
  override de puntaje con justificación y `vigente_hasta`, que se ignora al
  vencer. No es un dato de mercado; es una decisión humana con caducidad.
- Cualquier término que se lea de un config como *fallback* debe ser solo eso:
  un respaldo ante caída de la fuente primaria, nunca la fuente primaria.

## Opciones consideradas

- **Calibración con constante documentada** (ej. sumar −2.500 para alinear las
  reservas al consenso). Rechazada: aunque esté documentada, es un número a mano
  que se desactualiza y rompe la trazabilidad.
- **Config con componentes nombrados** (ej. Bopreal y Tesoro cargados a mano).
  Rechazada por la misma razón: nombrarlo no lo hace automático.
- **Aceptar el principio sin excepción.** Elegida.

## Consecuencias

- A veces el número "perfecto" del mercado no es 100% reproducible de datos; en
  ese caso se acepta el número que **sí** es calculable y se documenta la
  diferencia (ver ADR-0005), antes que hardcodear.
- Obliga a invertir más en encontrar la fuente correcta (planillas, balances,
  buckets de vencimiento), pero el resultado es auditable y se mantiene solo.
- Este ADR es la vara contra la que se evalúan los demás: si una decisión
  introduce un valor a mano, viola ADR-0001.
