# Cobertura del detector de privatizaciones

Corrección del 8-sep-2026. Antes, consultas fallidas y textos vacíos se omitían del recorrido, pero el almacén guardaba una fecha de corrida y cero novedades sin registrar cobertura; además reemplazaba metadatos previos. Un fallo global vaciaba los avisos que la tarjeta mostraba.

Ahora se preservan metadatos de revisión, consultas fallidas por empresa/mes y normas con texto no recuperado. La tarjeta incorpora `novedades_cobertura`, conserva pendientes conocidos ante fallo global y agrega «consulta de novedades incompleta» a su detalle. El avance curado no depende del éxito del detector. `sin_fallos_detectados` describe errores observados; no certifica exhaustividad ni cobros.

Se actualizó ADR-0129, ficha web y ficha generada de gestión. Pruebas aisladas cubren fallo parcial, recuperación, texto vacío y fallo global con avisos previos. Selección final: 17 aprobadas (0,30 s). Build 81 páginas, 1,35 s. Segunda revisión `codex review` acotada: sin regresiones concretas, estática. No se ejecutaron colectores reales ni se asignó retroactivamente cobertura a una corrida antigua. Snapshot y valores sin cambios.
