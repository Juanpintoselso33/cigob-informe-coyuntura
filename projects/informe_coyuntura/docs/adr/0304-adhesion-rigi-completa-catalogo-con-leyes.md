---
madr: 4
id: '0304'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [adhesion_reformas_provincial]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'data/politica/adhesion_reformas_complementarias.json', 'web/src/lib/fichas.ts', 'tests/test_adhesion_fuentes_complementarias.py']
ambito: 'Catálogo incompleto de adhesiones provinciales al RIGI'
---

# ADR-0304 — La ley publicada completa el catálogo de adhesiones

El catálogo MAGyP conserva 16 jurisdicciones, pero omite Santa Fe y CABA.
La [Ley santafesina 14.386](https://www.santafe.gob.ar/boletinoficial/ver.php?seccion=2024%2F2024-12-30ley14386-2024.html), art. 93, dispone la adhesión; su art. 120 fija vigencia desde el 1 de enero de 2025.
La [Ley porteña 6.949](https://boletinoficial.buenosaires.gob.ar/normativaba/norma/856735), art. 1, adhiere al mismo Título VII de la Ley 27.742 y se publicó el 28 de mayo de 2026.

Se completa el catálogo con un registro de leyes omitidas, sus URLs, textos
comprobables y fechas documentadas. Tarjeta e historia consultan la unión de
ambas fuentes, deduplicando nombres. El total documentado pasa a 18/24 = 75%.
La historia no anticipa Santa Fe al mes de su sanción: usa enero por su
vigencia explícita. CABA se referencia a su publicación, sin identificarla
con una fecha de vigencia jurídica no declarada por el texto.

Si una fuente falla o responde una página que no contiene la ley esperada,
se rechaza el conteo parcial y se conserva la tarjeta anterior mediante el
mecanismo de caché. La relectura del original prueba la adhesión documentada,
no la ausencia de derogaciones posteriores. El descubrimiento de nuevas
omisiones y cambios sigue requiriendo revisión del registro.

Se retiran de la ficha las garantías infundadas de actualización inmediata
del catálogo e irreversibilidad jurídica. La adhesión no prueba inversión
realizada ni alineamiento general. No cambian pesos, bandas ni denominador.
Se regeneran la historia política, los contrastes y la documentación.
