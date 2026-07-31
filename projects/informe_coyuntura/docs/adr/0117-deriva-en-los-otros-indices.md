---
madr: 4
id: '0117'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
archivos: ['tests/test_redundancia_itvc.py']
continua: ['0116']
ambito: 'ITCM · ITCG · ITCP · `tests/test_redundancia_itvc.py`'
---

# ADR-0117 — Los otros tres índices: sólo el ITCG tenía deriva

| **Continúa** | ADR-0116 (la robustez del ITVC estaba vieja) |

## Contexto y planteo del problema

### Qué se revisó

ADR-0116 encontró la sección de robustez del ITVC desactualizada. La pregunta
siguiente era obvia: **¿los otros tres también?** Se comparó, para cada uno, la
serie reconstruida y la matriz de redundancia publicadas contra un recálculo.

| índice | serie | matriz | veredicto |
|---|---|---|---|
| ITCM | 0 meses difieren | 91 pares, coincide | **fresco** |
| **ITCG** | **27 de 32 meses difieren** | **64 pares publicados vs 70 reales** | **deriva** |
| ITCP | 0 meses difieren | 53 pares, coincide | **fresco** |

## Opciones consideradas

- **Extender el guard a los cuatro índices y compararlo por pares**, no por indicadores — elegida. Verificado que dispara.
- **Dejarlo sólo en el índice donde apareció la deriva** — descartada.

## Decisión

El guard se extiende a los cuatro índices y pasa a comparar **pares**, no
indicadores. Verificado que dispara: forzando el ITCG a 64 falla con *"itcg: la
matriz publicada mide 64 pares y la reconstrucción da 70"*.

Estado final: las cuatro series y las cuatro matrices coinciden con su
recálculo, 0 meses de diferencia en las cuatro.

## Más información

### El ITCG

Su reconstrucción cambió con las altas y correcciones del día
—`desregulacion_normativa`, `fal_modernizacion_laboral`, la salida de
`asistencia_directa`— y la validación no se volvió a correr.

**El impacto en las conclusiones es mínimo**: contra el Merval en dólares la
correlación va de 0,739 a 0,735 en niveles y de 0,082 a 0,079 en diferencias. La
serie se movió de nivel pero conservó su forma.

La matriz sí cambia de forma visible: **64 → 70 pares** y |r| medio 0,494 →
0,478. No faltaban componentes —el conteo de indicadores coincidía en 14— sino
que la serie creció y más pares pasaron a tener datos suficientes.

**Eso es lo que hace insuficiente al guard de ADR-0116**, que comparaba el
número de indicadores: acá ese número estaba bien y la matriz igual estaba
vieja.

### El ITCM no tiene deriva, pero sí una cobertura parcial declarada

Su matriz mide **14 de los 16 componentes**: `iai` e `icip` no tienen serie y
quedan afuera con 0 meses de dato. No es desactualización —el recálculo da los
mismos 14— y **la card lo dice**: *"se cruzan los puntajes mensuales de los 14
componentes que tienen serie histórica"*. Se deja como está.

### Un error propio, encontrado y corregido en el camino

Al recalcular en lote, las correlaciones **con rezago** del ITCM se computaron
con una función de desplazamiento propia en vez de `_lag`, la del script, y
quedaron mal: los dos valores colapsaron al contemporáneo (−0,769), pisando
−0,759 y −0,81.

Rehechas con `ve._lag` **vuelven exactamente a −0,759 y −0,81**: los rezagos del
ITCM nunca habían estado desactualizados. Los del ITVC, recalculados con la
misma función, sí se movieron algo (0,523 → 0,536 y 0,377 → 0,383), deriva real
de sus componentes nuevos.

La lección es la de siempre en este archivo: reimplementar una función que el
proyecto ya tiene es una forma de introducir el error que se está tratando de
arreglar.
