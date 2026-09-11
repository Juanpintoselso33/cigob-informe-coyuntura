# Ratio DNU: cotejo completado y calendario corregido

El nombre del archivo conserva la referencia del pendiente original. El
control se completó el 8-sep-2026 mediante consultas mensuales a InfoLeg,
después de que la consulta anual sin filtro devolviera HTTP 500.

Se reconstruyeron 3.905 decretos desde el 31-dic-2022 al 8-sep-2026. Los 143
rótulos DNU se cotejaron con los originales enlazados por Argentina.gob.ar:
114 identificadores DNU, 28 DECNU (denominación usada en 2023) y un DECTO.
Ese último es el [44/2026](https://www.argentina.gob.ar/normativa/nacional/decreto-44-2026-422549/texto):
su rótulo de catálogo contradice el identificador original y su fundamento
en el artículo 99 inciso 1 y el Código Aduanero. El
[Boletín Oficial del 26-ene-2026](https://otslist.boletinoficial.gob.ar/ots/download/dda28ce45ea1edc374ce51c0666629b526542671d1007ccecbdd473cc6c1ee0b/0/)
lo corrobora. No se incorpora como DNU; el filtro previo tampoco lo contaba.

Para el intervalo vigente hay 35 DNU y 25 leyes publicadas: ratio 1,4.
Las 25 leyes contienen las 22 sancionadas en la ventana de producción y las
27793, 27795 y 27796, sancionadas antes pero publicadas en septiembre/octubre
de 2025. La diferencia de universos y fechas se concilia nominalmente.

Una consulta de leyes desde el 21-oct-2025 hasta ese mismo día devuelve dos
normas: ambos límites son inclusivos. Para contar 365 fechas se debe restar
364 días a la fecha final. La nueva ventana actual comienza el 9-sep-2025;
no hubo normas del numerador ni del denominador en el día eliminado y la
tarjeta no cambia. En la historia cambian cuatro meses:

| Mes | Antes | Corregido | Norma del día adicional eliminado |
|---|---:|---:|---|
| Febrero 2024 | 40/34 = 1,176 | 39/34 = 1,147 | DNU 101/2023, publicado 1-mar-2023 |
| Mayo 2024 | 45/23 = 1,957 | 44/23 = 1,913 | DNU 288/2023, publicado 1-jun-2023 |
| Noviembre 2024 | 51/42 = 1,214 | 50/42 = 1,190 | DNU 647/2023, publicado 1-dic-2023 |
| Abril 2025 | 45/45 = 1,000 | 45/44 = 1,023 | Ley 27741, publicada 30-abr-2024 |

Se recalculó la historia con las fechas de publicación de cada norma y se
conservaron pesos y bandas. ITCP 2026 no cambia; el contraste ITCP–EPU queda
en −0,284 en niveles y −0,259 en diferencias. Son asociaciones, no causalidad.

Este cotejo comprueba el inventario del catálogo y los originales de sus
candidatos DNU al corte. No garantiza que el catálogo no omita una norma o
la rotule de otra manera, ni que el filtro textual siga siendo exhaustivo
en futuras actualizaciones. Automatizar esta comprobación periódica se
anota como mejora operativa; no se declara una garantía permanente.

[Evidencia nominal, originales y huellas, conteos, tarjeta e historia](cotejo-ratio-dnu-calendario.json).

Actualización ADR-0308: producción incorpora siete sanciones de agosto que no aparecen en el inventario de publicaciones. El ratio conserva 35/25; la producción sube a 29. Véase [conciliación](produccion-legislativa-corregida.md).
