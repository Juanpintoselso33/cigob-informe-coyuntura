---
madr: 4
id: '0273'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'vida'
indicadores: [inseguridad]
archivos: ['scripts/descargar_series.py', 'tests/test_ivi_descubrimiento.py']
corrige: ['0032']
relacionado: ['0032', '0272']
ambito: 'Descubrimiento de informes mensuales IVI'
origen: 'Auditoría contra el catálogo oficial LICIP'
---

# ADR-0273 — Victimización descubre el portal vigente y enlaces relativos

## Contexto y planteo del problema

El monitor conservaba abril de 2026. El portal LICIP de contenido 968 ya
enlaza julio mediante `/download.php?fname=...pdf`. El colector consultaba
otro listado y sólo reconocía URLs absolutas. Además marcaba como procesados
PDFs cuya extracción no devolvía período y valor.

## Factores de decisión

- Conservar la encuesta, universo y ventana de doce meses.
- Recuperar publicaciones disponibles sin cambiar pesos ni base.
- No confundir descarga con extracción exitosa.

## Opciones consideradas

- Aumentar el umbral de demora: oculta un problema de descubrimiento.
- Cargar julio manualmente: no repara las próximas corridas.
- Corregir portal y resolución de enlaces, conservando el archivo histórico.

## Decisión

Consultar el portal vigente además del archivo, resolver enlaces absolutos y
relativos, y marcar un PDF como procesado sólo después de extraer su dato.
Los PDFs ilegibles se reintentan y generan advertencia.

El archivo recuperado incluye 2020–2023 y el 4T-2023. La afirmación de que
la encuesta estaba suspendida era incorrecta: diciembre de 2023 informa 27,8%.
Se conserva enero de 2024 como base explícita para no cambiar la metodología
silenciosamente al reparar la extracción. Se actualizan ficha, comentarios y
la prueba que confundía un faltante del colector con ausencia en la fuente.
La eventual armonización de la base requiere comparar y documentar su efecto.

## Pros y contras de las opciones

Se recupera actualidad sin cambiar metodología. El descubrimiento sigue
dependiendo del catálogo público; las advertencias deben revisarse cuando
un documento cambia de forma.

## Más información

- [Portal oficial LICIP](https://www.utdt.edu/ver_contenido.php?id_contenido=968&id_item_menu=2156).
- [Informe julio 2026](https://www.utdt.edu/download.php?fname=_178596896306235900.pdf):
  27,3% de hogares víctimas, verificado por extracción y lectura visual.
- Test de enlace relativo, caché válida y reintento de PDF ilegible.
- [Informe diciembre de 2023](https://www.utdt.edu/download.php?fname=_170834892758439900.pdf).
