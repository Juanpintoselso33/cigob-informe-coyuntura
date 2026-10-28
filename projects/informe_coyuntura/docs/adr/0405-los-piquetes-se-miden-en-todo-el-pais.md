---
madr: 4
id: '0405'
estado: 'superado'
nota_estado: 'Superado por ADR-0408 (28-oct-2026): los piquetes vuelven a la Ciudad de Buenos Aires, que era lo decidido; los totales nacionales quedan como contexto.'
fecha: 2026-10-28
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [protocolo_antipiquetes]
archivos: ['data/gestion/dp_piquetes.json', 'data/gestion/manuales.json', 'scripts/gestion.py', 'scripts/descargar_series.py', 'scripts/itcg.py', 'scripts/procedencia_anclas.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_piquetes_detector.py', 'tests/test_serie_piquetes_anio_cerrado.py', 'tests/test_gestion_adr0405_0407.py']
relacionado: ['0025', '0105', '0121', '0395', '0406', '0407']
superado_por: ['0408']
ambito: 'ITCG · dimensión Reforma social y orden · universo de `protocolo_antipiquetes`'
origen: 'Revisión del 28-oct-2026, a pedido de Juan, de las escalas del cinturón de gestión calibradas sobre el propio mandato.'
---

# ADR-0405 — Los piquetes se miden en todo el país

## Contexto y planteo del problema

`protocolo_antipiquetes` medía la reducción de cortes en la Ciudad de Buenos Aires
contra 2023 ([[0025]]). Tres problemas:

- La Res. 943/23 es un protocolo de las fuerzas federales, no de la Ciudad.
- La Ciudad era el 11,3 % de los cortes de 2023, y su base (931) no es un conteo: se
  estimó multiplicando 8.239 por una participación publicada ya redondeada.
- Las bandas (0/25/50/75 %) se habían fijado mirando la caída porteña de 2024-2025, y
  la tarjeta de octubre de 2026 puntuaba 99,0 con 74,2 %.

Diagnóstico Político publica, con la misma definición de corte, el total nacional de
cada año. Cada cifra se verificó el 28-oct-2026 contra su fuente, que queda registrada
en `data/gestion/dp_piquetes.json`:

| Año | Cortes | Fuente |
|---|---|---|
| 2014 | 6.805 | DP, relevamiento anual de ene-2020 (Wayback) |
| 2016 | 6.491 | El Cronista, 5-ene-2018 |
| 2017 | 5.221 | El Cronista, 5-ene-2018 |
| 2018 | 5.857 | DP ene-2020; Diario de Cuyo, 22-ene-2019 |
| 2019 | 5.430 | DP ene-2020 |
| 2021 | 6.658 | Semanario Argentino, 13-may-2022 (Wayback) |
| 2022 | 9.778 | Infobae, 13-may-2024 |
| 2023 | 8.239 | Infobae 2024; Chequeado, 1-mar-2026 |
| 2024 | 5.996 | La Nación, 13-ene-2026; Hoy Día; Chequeado |
| 2025 | 3.893 | La Nación, 13-ene-2026; Hoy Día; Chequeado |

2015 y 2020 no tienen total anual publicado que se haya podido verificar y quedan fuera.

## Factores de decisión

- El indicador tiene que medir el universo del protocolo que nombra.
- Una base publicada es mejor que una estimada desde un porcentaje redondeado.
- No ajustar la escala al nuevo resultado.

## Opciones consideradas

- **Total nacional con las bandas actuales, declaradas como convención (elegida).**
- Total nacional con bandas por desvíos de la variación anual 2016-2023.
- Seguir con la Ciudad.

## Decisión

El indicador pasa al total nacional de cortes de Diagnóstico Político: reducción =
(1 − cortes del último año cerrado / 8.239) × 100. Las bandas no se mueven
(0 → 10 · 12,5 → 40 · 37,5 → 65 · 62,5 → 85 · 75 → 100) y se declaran como
convención: cuartos redondos de la reducción con el cero como piso. La serie mensual
sigue la regla de [[0395]]: cada mes usa el último año cerrado. La clave `caba` del
registro se conserva y no puntúa. Tarjeta, unidad, descripción, fórmula y ficha pasan
a decir «país».

### Consecuencias

- La tarjeta de octubre de 2026 pasa de 74,2 % (Ciudad, 2025) a 52,7 % (país, 2025) y
  su puntaje, de 99,0 a 77,2. La dimensión Reforma social y orden, de 99,6 a 90,9.
- La serie pasa de 52,7 (2025) / 74,2 (2026) a 27,2 / 52,7.
- El respaldo manual de `manuales.json` pasa al mismo universo (52,7).
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_gestion_adr0405_0407.py` fija los diez totales, que la tarjeta use el
total nacional y no la Ciudad, y que la unidad diga «país»;
`tests/test_serie_piquetes_anio_cerrado.py` fija la serie nueva.

## Pros y contras de las opciones

- País con bandas actuales: universo correcto, base publicada; las bandas siguen siendo
  una convención, ahora declarada.
- País con bandas por desvíos: la historia es corta (seis variaciones sin pandemia) y
  2022 es un año extremo; se dejó para otra revisión.
- Ciudad: base estimada y universo ajeno al protocolo federal.

## Más información

[[0025]] creó el indicador; [[0395]] fijó la regla del año cerrado; [[0406]] y
[[0407]] son las otras dos decisiones de la misma revisión del cinturón.
