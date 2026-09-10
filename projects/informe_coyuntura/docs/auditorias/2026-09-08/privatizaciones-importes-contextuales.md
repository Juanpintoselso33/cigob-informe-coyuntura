# Importes contextuales de privatizaciones

La nota de [TN del 23 de mayo de 2026](https://tn.com.ar/economia/2026/05/23/el-gobierno-espera-duplicar-el-ingreso-por-privatizaciones-y-captar-hasta-us3000-millones-este-ano/) coincide con los importes heredados del registro. No se demostró que fuera su fuente original. Su desglose suma 1.083 millones frente al total declarado de 1.081; por tanto no constituye una conciliación. También anticipa Transener a abril, mientras el [cotejo del comunicado CNV](cotejo-transener-cierre.json) sitúa el perfeccionamiento en agosto. La meta es una expectativa histórica, no un resultado.

Se retiraron las claves `recaudacion_efectiva_musd` y `meta_recaudacion_2026_musd` del contexto y se conservaron sus valores bajo `antecedente_periodistico`, con fecha, fuente, estado no conciliado y límites explícitos. No se reemplazó el total por la suma: tampoco está acreditada como cobro efectivo.

La búsqueda de consumidores en scripts, pruebas, datos y frontend sólo encontró las claves en el registro. El colector calcula desde `empresas`, sin usar ese contexto. Las nueve empresas y sus etapas permanecen idénticas; avance 55,6 y hash del snapshot sin cambios. No se ejecutaron colectores, publicación ni build por esta reclasificación de metadatos.

Queda pendiente la conciliación contable con respaldo primario y un universo de operaciones explícito. No sumar Enarsa y Transener como operaciones independientes. Esta corrección evita que una clave estructurada afirme lo que la nota de cautela ya negaba.
