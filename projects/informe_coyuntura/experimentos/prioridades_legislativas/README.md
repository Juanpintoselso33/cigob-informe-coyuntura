# Prueba local de aprobación de prioridades legislativas

10 de septiembre de 2026. Experimental; no integrar ni desplegar sin evaluación conjunta y autorización de Juan.

Mide la proporción de una cartera documentada que obtuvo sanción definitiva. No mide por sí sola la salud del plan, implementación, vigencia ni resultados sociales. La regla base da igual peso a cada iniciativa. La variante ponderada sirve exclusivamente para sensibilidad.

Fórmula: 100 × peso sancionado / peso total elegible al corte. Rechazos y retiros permanecen en el denominador. Sin universo, no hay porcentaje. Una sanción histórica respaldada no caduca por falta de revisión posterior. Los demás estados sin revisión suficiente son desconocidos: se informa el rango entre sanciones comprobadas y sanciones más desconocidos, conservando el denominador. No es un intervalo de confianza estadístico.

La reconstrucción usa fechas de hechos con evidencia reunida posteriormente; no reproduce la información disponible en tiempo real. Antes de integrar, definir una cartera representativa y reglas previas de inclusión y revisión, evaluar varios meses y comprobar la interpretación con el equipo. Un 100% sobre una reforma seleccionada no acredita éxito general ni superioridad respecto de la cohorte legislativa del monitor.

## Ejecutar desde projects/informe_coyuntura

```sh
.venv/bin/python -m pytest experimentos/prioridades_legislativas/test_motor.py -q
.venv/bin/python experimentos/prioridades_legislativas/construir.py
.venv/bin/python -m http.server 8772 --bind 127.0.0.1 --directory experimentos/prioridades_legislativas/vista
```

Abrir http://127.0.0.1:8772/. El generador sólo escribe en `vista/`; lee las fuentes del registro `docs/producto/piloto-compromisos-2026-09-10.json`. No importa el motor productivo ni modifica sus datos. Sin servicios externos ni persistencia de selecciones.

## Resultados comprobados

18 pruebas automatizadas aprobadas. Se generan 25 combinaciones de escenario y corte. Interacción verificada en navegador: cuatro simulaciones, reforma antes y desde la sanción; sin errores de consola. Vista de escritorio inspeccionada; controles apilados en móvil y ancho de documento igual al visible (375 px), sin desborde horizontal general.

| Escenario al 8-sep-2026 | Resultado |
| --- | --- |
| Una reforma real seleccionada | 100% (1/1; cartera incompleta) |
| Cuatro iniciativas simuladas, dos sancionadas | 50% |
| Falta documento y revisión de una iniciativa | 25–50%; cobertura 75% |
| Seleccionar sólo las dos exitosas | 100% |
| Dar peso 3 a una sancionada | 66,67% |

La reforma real pasa de 0% el 26-feb a 100% el 27-feb. Es una prueba de fechas, no validación de representatividad. El 14,3% mostrado como referencia pertenece al snapshot local auditado del 8-sep y tiene otro universo (2/14); no se recalcula ni compara en otros cortes.

`codex review` no encontró errores en la primera versión de 17 tests. Después se ajustó la persistencia de sanciones históricas y se verificó con 18 tests y navegador; ese ajuste no tuvo segunda revisión independiente.

Todo lo de arriba se calculó contra el snapshot que había en
`web/src/data/informe.json` el **8-sep-2026**, `sha256
5e048a7d5eca458ed61d8d4171437f2af7e94cb08f0a8463cdc92319f5638c84`. El ancla es
deliberada: sin ella no se puede rehacer la comparación. Pero **no describe el
estado de hoy** — el pipeline nocturno regenera ese archivo todas las noches, y
cuando este experimento se commiteó (15-sep) ya hasheaba
`8e5f5d3d9df77fbf33ee6dd2a3b0f1b450aea8d368bb649b9ffb064f36eb31c3`. Nada en el
repo compara el sha declarado contra el archivo, así que quien quiera
re-verificar tiene que recuperar el snapshot de esa fecha (`git show
a3f9fca9:projects/informe_coyuntura/web/src/data/informe.json`), no hashear el
actual.

Queda pendiente la validación metodológica con una cartera real completa y cortes mensuales.
