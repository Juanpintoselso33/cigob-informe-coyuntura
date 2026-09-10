---
madr: 4
id: '0272'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'vida'
indicadores: [mora_familias]
archivos: ['scripts/descargar_series.py', 'scripts/gate_calidad.py', 'tests/test_bcra_anexo_vigente.py']
relacionado: ['0067', '0227', '0273', '0275', '0278']
ambito: 'Frescura del anexo del Informe sobre Bancos'
origen: 'Comparación directa de las dos planillas BCRA el 8-sep-2026'
---

# ADR-0272 — Un anexo bancario con HTTP 200 puede estar viejo

## Contexto y planteo del problema

El monitor leía `InfBanc_Anexo.xlsx`, que responde 200 pero su último mes
es mayo de 2026 (Last-Modified: 24-jul-2026). La edición de junio, publicada
el 21-ago, enlaza `informe-bancos-anexo.xlsx`, actualizado el 24-ago y con
columnas hasta junio en las hojas del sistema financiero y calidad de cartera.

La regla de demora detectaba el rezago, pero su explicación afirmaba que el
organismo no había publicado nada nuevo. Esa conclusión no sale del snapshot.

## Factores de decisión

- Conservar el universo: personales y tarjetas de familias, ponderados por saldo.
- No sustituirlo por el 12,8% agregado de familias citado en el informe: incluye
  otras líneas y no es el mismo indicador.
- Una descarga exitosa sólo demuestra acceso a ese archivo.

## Opciones consideradas

- Mantener el enlace anterior y aumentar el umbral de demora: ocultaría el problema.
- Copiar el porcentaje de portada: cambiaría el universo.
- Leer el anexo vigente con el parser por etiquetas existente.

## Decisión

Cambiar al anexo enlazado por la edición vigente, manteniendo fórmula, universo,
base y peso. No usar la URL antigua como fallback silencioso. El gate informa
rezago del dato disponible en el monitor sin atribuirlo automáticamente al organismo.

## Pros y contras de las opciones

Recupera el mes disponible sin introducir una cifra manual ni un indicador
distinto. Sigue siendo necesario contrastar el último período del anexo con
el catálogo editorial: un código HTTP por sí solo no acredita frescura.

## Más información

- [Edición junio 2026 y enlaces oficiales](https://www.bcra.gob.ar/publicaciones/informe-sobre-bancos-junio-de-2026/).
- [Anexo vigente](https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-bancos-anexo.xlsx).
- Verificación: lectura de fechas de ambas planillas y prueba de ponderación
  por saldo que discrimina entre la media simple y el porcentaje compuesto.
