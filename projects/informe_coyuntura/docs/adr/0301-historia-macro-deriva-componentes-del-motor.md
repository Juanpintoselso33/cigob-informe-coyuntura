---
madr: 4
id: '0301'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [iai]
archivos: ['scripts/validacion_externa.py', 'scripts/publicar.py', 'tests/test_publicar.py', 'tests/test_validacion_externa.py', 'tests/test_historia_itcm_inversion.py']
ambito: 'Consistencia entre portada, historia y validación externa'
---

# ADR-0301 — La historia macro deriva sus componentes del motor

La portada incluía inversión con 12% de peso, pero la reconstrucción mensual
omitía el IAI de su lista de insumos. La serie existía en el CSV y en los datos
web. Una excepción obsoleta en el test afirmaba que IAI no tenía historia,
por lo que ocultaba el defecto. Compartir el motor no bastaba: recibía entradas
distintas en portada e historia.

La reconstrucción toma los componentes activos de `DIMENSIONES_ITCM`. Conserva
las transformaciones específicas de IPC, REM y saldo comercial acumulado;
los demás se buscan por su identificador en la serie mensual. Un mes ausente
permanece ausente, no cero. IDM, suspendido, deja de entrar como insumo inerte.

Se elimina la excepción histórica de IAI y se verifica que su valor mensual
llegue efectivamente a la dimensión de inversión. Otro test exige el conjunto
exacto de componentes activos, además del control existente contra las series
publicadas. La corrección obliga a regenerar historia, línea base, dimensiones,
redundancia y contrastes externos; no modifica los pesos del índice.

El texto público cuenta los componentes observados en los meses reconstruidos,
registrados en la salida de validación. No conserva una lista de excepciones
escrita a mano. Tener historia no implica tener observaciones en todos los meses:
la declaración pública distingue ambas cosas.

Las comparaciones anteriores de ITCM que excluían inversión quedan superadas
por la reconstrucción corregida. No se interpreta el cambio entre versiones
como un acontecimiento económico del mes revisado.
