# Julio ICG recuperado y panel recalculado

La respuesta oficial UTDT, https://www.utdt.edu/download.php?fname=_178759382938737800.xls, tiene julio como texto `jul-26` en la columna 44 (índice cero), hoja Evolución ICG a partir de 2023. La fila ICG contiene 1,93555262226756. El colector aceptaba sólo fechas Excel: omitía julio mientras incluía agosto.

Se corrigió la lectura de etiquetas mensuales españolas y se añadió una regresión que mezcla fechas y texto. Julio se incorpora como 1,936 en la serie, coherente con 1,94 del contraste documental. Las nueve consultas de anclas API respondieron y se reconstruyó el panel con los ajustes existentes; se conservaron todos los insumos en panel-insumos-cotejados.json, junto con IDs, fuente ICG y hash del XLS.

Se recalcularon los tres perfiles y las correlaciones ITCG/ICG, sin cambiar índices del monitor. ITCG/ICG pasa a −0,695 en niveles (32 meses) y 0,102 en diferencias (31); brechas en diferencias del panel: ITCIS 0,025, ITCG −0,028, ITCP 0,164. La conclusión sigue siendo convergencia parcial, sin validación causal ni predictiva. Comparación detallada en icg-julio-correccion.json.

Publicación y censo regenerados, build 81 páginas correcto. El script temporal de integración inserta un registro y NO debe repetirse. La reconstrucción previa aisló primero el efecto calendario; luego se reparó la omisión de fuente antes de integrar. No se ejecutaron colectores generales ni se desplegó.
