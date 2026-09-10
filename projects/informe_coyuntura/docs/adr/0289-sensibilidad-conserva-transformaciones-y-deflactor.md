---
madr: 4
id: '0289'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [rem_ipc_12m]
archivos: ['scripts/sensibilidad.py']
complementa: ['0078', '0082']
ambito: 'Informe de sensibilidad'
---

# ADR-0289 — Sensibilidad conserva transformaciones y deflactor

## Contexto y planteo del problema

La web simulaba con la transformación anual-mensual del REM y el error
compartido del IPC. El informe separado omitía ambos argumentos. Con REM
21% anual, repuntuaba 10 en lugar de 83, incluso sin ruido. El intervalo
macro quedaba artificialmente desplazado. El índice central no cambia.

## Decisión

Pasar al informe las transformaciones del motor y la exposición al error
compartido ya empleadas por la web. Verificar que ruido cero conserva los
puntajes y que la parte común se propaga con el signo de la exposición.
Respetar el número de corridas solicitado y registrar `generated_at` del
snapshot, en lugar de consultar una clave inexistente.

## Más información

Los intervalos del informe y la web pueden diferir levemente: usan cantidades
de simulaciones y secuencias aleatorias distintas. Deben evaluar el mismo
modelo; no se exige igualdad decimal entre muestras Monte Carlo.
