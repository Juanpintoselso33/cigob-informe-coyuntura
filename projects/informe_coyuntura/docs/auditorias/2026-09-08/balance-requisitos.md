# Balance de requisitos de la revisión integral

Corte del 8-sep-2026. La etapa se cierra con reservas por indicación posterior de Juan. Este balance conserva qué quedó verificado y qué no; véase [cierre](cierre.md).

| Pedido | Evidencia conservada | Alcance alcanzado y pendiente |
|---|---|---|
| Coherencia entre cinturones, dimensiones e indicadores | `coherencia.json`, `indicadores.csv`, `dimensiones.csv`, `verificacion-integrada.md` | Censo actualizado: 4 cinturones, 24 dimensiones, 63 indicadores, 62 observados y uno sin universo; cero fallos estructurales/aritméticos. Los tests no prueban validez del constructo. |
| Datos y fuentes actualizados | `cobertura-fuentes.csv` y cotejos por fuente | Las 63 filas están documentadas. Persisten los límites de cobertura judicial, FAL y privatizaciones detallados en el estado vigente; no se certifica actualidad exhaustiva. |
| Documentación y ficha metodológica | Manuales, fichas regeneradas, ADR y cotejos de explicaciones | Se corrigieron contradicciones detectadas de cálculo, fechas, pesos y alcance. Los Word conservan entregas históricas. El ADR-0217 conserva su título y decisión originales con rectificación explícita de interpretación. |
| Presentación del monitor | `portada-coherencia.md`, cotejos de gráficos y explicaciones, builds | Portada y contenido generado verificados; el último build produce 81 páginas. La lectura editorial de septiembre es una propuesta sin publicar. |
| Contraste con la realidad argentina mes a mes | `contraste-politico-cualitativo.md`, contraste CAME y descomposición ITCP | Enero-agosto cotejados con episodios y fuentes contemporáneas. Muestra intencional, no censo de la conversación argentina; se conservan discrepancias. Septiembre sigue abierto. |
| Comparación con Di Tella y otras referencias | `icg-julio-corregido.md`, `panel-insumos-cotejados.json`, `contraste-calendario-panel.md` | Serie ICG y calendario corregidos; panel recalculado. Asociación parcial, sin demostrar causalidad ni predicción. No ajustar pesos para forzar coincidencias. |
| Separar mejoras de correcciones | `mejoras-potenciales.md` | Propuestas de rediseño separadas: proxies, unidades, cobertura homogénea, evaluación fuera de muestra y otros puntos. No se ejecutan como supuestas reparaciones técnicas. |
| Continuidad y límite de uso | Recuento y `LIMITE_DE_USO.md` en la carpeta de tarea | Última consulta: 42% usado, 58% restante. Corte solicitado al 50% restante. Cambios locales, sin push ni despliegue. |

## Comprobación de esta etapa

Se volvió a ejecutar el censo sobre el snapshot SHA-256 `5e048a7d5eca458ed61d8d4171437f2af7e94cb08f0a8463cdc92319f5638c84`, actualizando su evidencia. Se comprobó la existencia de los insumos y cotejos de validación y las 63 filas de fuentes. Cuatro pruebas de texto aprobadas; build de 81 páginas correcto. La suite integrada previa continúa documentada; después se ejecutaron pruebas dirigidas para cada cambio, incluidas 43 de publicación tras corregir la lectura de carnes. No se presenta este balance como una nueva revisión completa de todas las observaciones históricas.

## Reservas conservadas en el cierre

El estado vigente enumera los pendientes concretos y su evidencia: corroborar movimientos efectivos del universo judicial, completar la consulta judicial del FAL y la cobertura de novedades de privatizaciones. La conciliación total de cobros es contexto externo y no entra en el índice de etapas; mientras no esté acreditada, no publicar una cifra como recaudación efectiva. La propuesta editorial requiere revisión del equipo antes de atribuirle firma institucional. Ningún pendiente queda resuelto por tener tests verdes.
