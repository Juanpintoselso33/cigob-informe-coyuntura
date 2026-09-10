# Recaudación de julio: valor correcto y lectura condicionada

El [informe original de ARCA](https://www.arca.gob.ar/institucional/documentos/ARCA-Recaudacion-072026.pdf),
página 12, publica un subtotal impositivo de 12.640.578 millones de pesos.
La API conserva 12.640.577,9556. Se verificó el cuadro visualmente y se
reconstruyó el índice con los insumos DGI, COMARB e IPC: 55 meses, desde
enero de 2022 hasta julio de 2026. La tarjeta de 102,1 coincide. Las respuestas,
hashes, factores y resultado están en [el cotejo](cotejo-recaudacion-original.json).

Las páginas 4, 5 y 10 del mismo informe señalan reasignaciones de saldos entre
impuestos y vencimientos trasladados de junio a julio. Son motivos para no
atribuir todo el incremento a actividad o formalización: el ajuste estacional
estima patrones habituales y no aísla esas intervenciones excepcionales.

El [informe de IDEP/ATE](https://ate.org.ar/wp-content/uploads/2026/08/Recaudacion-tributaria-Julio-26-IDEP-1.pdf)
también advierte sobre la concentración de la mejora y el calendario tributario.
Reelabora datos de ARCA: aporta una interpretación externa, no una observación
estadística independiente. No se ajustan pesos para acercar el monitor a esa lectura.

Se incorpora esta limitación a la ficha. Cambiar el indicador por una serie
calculada a legislación y calendario constantes requeriría otro diseño; se
conserva como posibilidad metodológica, sin confundirla con esta corrección.
