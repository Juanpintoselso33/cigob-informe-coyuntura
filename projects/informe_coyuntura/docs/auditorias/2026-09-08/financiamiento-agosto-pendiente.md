# Financiamiento: agosto existe fuera de la planilla anual

Verificado el 8-sep-2026. El [catálogo anual](https://www.argentina.gob.ar/economia/finanzas/deudapublica/colocacionesdedeuda)
mantiene 31-jul-2026 como último corte. No basta para afirmar que no hay cifras
posteriores: la Secretaría publicó los resultados por licitación.

| Licitación | Instrumento fijo en pesos | Valor efectivo, M pesos | TIREA oficial |
|---|---|---:|---:|
| 12-ago | S30N6 | 3.286.206 | 28,54% |
| 27-ago | S30N6 | 6.085.000 | 29,75% |
| 27-ago | LECAP 29-ene-2027 | 2.379.233 | 30,60% |
| 27-ago | T31Y7 | 2.448.505 | 30,69% |

Fuentes originales:

- [Resultado 12-ago](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-10).
- [Llamado 10-ago](https://www.argentina.gob.ar/noticias/llamado-licitacion-de-instrumentos-del-tesoro-nacional-denominados-en-pesos-y-en-dolares-10): liquidación el 14-ago, confirmada explícitamente; la fixture anterior la infería.
- [Resultado 27-ago](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-11).
- [Llamado 25-ago](https://www.argentina.gob.ar/noticias/llamado-licitacion-de-instrumentos-del-tesoro-nacional-denominados-en-pesos-y-en-dolares-11): liquidación el 31-ago.
- [Conversión 18-ago](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-para-la-conversion-de-la-lelink-d31g6-con-vencimiento-31-de): los títulos recibidos son dólar linked, fuera del universo fijo en pesos del indicador.

## Corrección aplicada — ADR-0288

Se completa el cálculo mensual con los resultados oficiales posteriores al corte
de la planilla, sin mezclar CER, dólar linked ni dólares con tasa fija en pesos.
Conservar tasas, valores efectivos y fechas por instrumento, y verificar la
cobertura del mes antes de incorporarlo. Usar liquidación y REM del mismo mes.
La fuente directa publica TIREA: no hace falta inferirla a partir del cupón.

La tarjeta y la historia incorporan agosto: TIREA nominal ponderada 29,77%,
REM 21,0% y costo real anual 7,25%, frente a 4,13% de julio. Se conservaron
los 31 puntos históricos desde diciembre de 2023. El inventario y las respuestas
están en [cotejo-financiamiento-agosto.json](cotejo-financiamiento-agosto.json).
El registro exige revisar la cobertura antes de agregar otro mes y la planilla
anual tiene prioridad cuando lo incorpora; no se suman ambos universos.
