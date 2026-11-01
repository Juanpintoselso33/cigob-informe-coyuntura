---
madr: 4
id: '0416'
estado: 'aceptado'
fecha: 2026-11-01
cinturon: 'transversal'
indice: 'ITCM'
indicadores: [idc, saldo_comercial_12m, recaudacion, cohesion_bloque, alineamiento_senadores_prov, inseguridad]
archivos: ['scripts/macro.py', 'scripts/itcm.py', 'scripts/validacion_externa.py', 'scripts/descargar_series.py', 'scripts/politica.py', 'scripts/itvc.py', 'web/src/lib/fichas.ts', 'tests/test_idc_badlar_tna.py', 'tests/test_historia_itcm_regla_saldo.py', 'tests/test_macro_recaudacion_dgi.py', 'tests/test_senado_lectura_completa.py', 'tests/test_itvc_sin_respaldo_inseguridad.py', 'tests/test_redundancia_sin_suspendidos.py']
relacionado: ['0028', '0056', '0404', '0321', '0401', '0393', '0082', '0086']
ambito: 'Correcciones de cálculo, sin cambio de método: conversión de la BADLAR, regla del saldo comercial en la historia, texto de la base imponible, ventana del Senado entre años, respaldo de victimización y control de redundancia de gestión'
origen: 'Revisión de Codex de todo el Monitor pedida por Juan el 1-nov-2026; Juan: «arreglá 1 y 2».'
---

# ADR-0416 — Correcciones de cálculo de la revisión del 1 de noviembre de 2026

## Contexto y planteo del problema

Cinco revisiones de Codex, una por cinturón y una transversal, buscaron errores en todo el
Monitor. Además de textos que contradecían el cálculo, encontraron seis errores en el cálculo
mismo. Ninguno cambia qué mide un indicador ni el método decidido: son implementaciones que no
hacían lo que el método dice.

## Factores de decisión

- Un indicador tiene que calcular lo que su ficha declara.
- La tarjeta y la serie histórica tienen que salir de la misma función.

## Opciones consideradas

1. Corregir cada error en el código, con una prueba que falle antes y pase después.
2. Dejarlos anotados como pendientes.

## Decisión

Opción 1.

1. **Capacidad prestable (`idc`).** La BADLAR del Banco Central es una tasa nominal anual y se
   pasaba a mensual con raíz doceava, como si fuera efectiva. Ahora se divide por 12
   ([[0028-idc-z-scores]] define el componente de precio como tasa mensual menos inflación
   mensual). Septiembre de 2026: −0,21 → −0,03 puntos reales. Se recalcula toda la serie y su
   estandarización.
2. **Saldo comercial (`saldo_comercial_12m`).** La regla automática que descuenta el superávit
   explicado sobre todo por la caída de importaciones ([[0056-suavizado-ajuste-automatico-saldo-comercial]],
   [[0404-inversion-credito-y-saldo-comercial-con-cortes-de-la-historia-previa]]) se aplicaba en la tarjeta y no en la historia del índice.
   Ahora las dos usan `itcm.ajustes_automaticos()`, y se guardan dos series auxiliares que no se
   muestran ni puntúan (`saldo_comercial_expo_12m`, `saldo_comercial_impo_12m`). Hasta que haya
   historia guardada, los meses viejos siguen sin el ajuste: no se reconstruye la composición a
   partir de cifras redondeadas.
3. **Base imponible (`recaudacion`).** El texto de control informa el sentido del impuesto al
   valor agregado y del cheque por separado, y deja de nombrar la aduana, que está excluida de esa
   base. El puntaje no cambia.
4. **Senado (`cohesion_bloque`, `alineamiento_senadores_prov`).** La tarjeta lee las actas de
   todos los años que cruza la ventana de 90 días y agrega con la misma función que la historia
   ([[0401-la-cohesion-mide-las-votaciones-divididas-contra-la-historia]]). Antes, en enero y febrero la ventana quedaba cortada.
5. **Victimización (`inseguridad`).** Se quita un respaldo que dividía hechos delictivos por un
   porcentaje de hogares. La serie ya se rebasea al 4.º trimestre de 2023
   ([[0393-la-victimizacion-se-rebasea-al-4t-2023]]); si falta, el componente queda sin dato.
6. **Control de redundancia de gestión.** La matriz de correlaciones se arma con los indicadores
   vigentes del índice (sin los suspendidos), manteniendo afuera al RIGI
   ([[0086-serie-y-banda-tienen-que-medir-lo-mismo]]). Cambian las estadísticas publicadas del control, no el
   índice.

### Consecuencias

- Cambian el valor y la serie de capacidad prestable y, por arrastre, el índice macro.
- Cambian las estadísticas del control de redundancia de gestión.
- Los meses de enero y febrero de las series del Senado pueden cambiar en la próxima
  reconstrucción.

### Confirmación

Las pruebas nombradas en `archivos` fallan con el código anterior y pasan con el nuevo.

## Pros y contras de las opciones

- Opción 1: arregla números publicados; mueve la serie de capacidad prestable hacia atrás.
- Opción 2: deja publicado un cálculo que no hace lo que dice su ficha.

## Más información

Hallazgos de Codex: revisión del 1-nov-2026 (macro, política, gestión, impacto social,
transversal).
