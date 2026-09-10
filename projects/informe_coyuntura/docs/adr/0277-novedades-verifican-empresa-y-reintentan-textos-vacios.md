---
madr: 4
id: '0277'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [privatizaciones]
archivos: ['scripts/gestion.py', 'tests/test_gestion_privatizaciones_novedades.py']
relacionado: ['0129', '0101']
ambito: 'Atribución de normas y persistencia de descartes automáticos'
origen: 'Revisión individual de avisos pendientes de privatizaciones'
---

# ADR-0277 — El detector verifica la empresa y reintenta lecturas vacías

## Contexto y planteo del problema

InfoLeg combina los términos de búsqueda con OR. El detector atribuía cada
resultado a la empresa consultada sin verificar que apareciera en su texto.
Así asignó a YCRT un concurso de exploración offshore y a Belgrano Cargas
normas sanitarias y financieras. Además guardaba un texto vacío por fallo de
descarga como un descarte definitivo.

## Factores de decisión

- La coincidencia del buscador es un candidato, no una atribución comprobada.
- Una lectura fallida no equivale a ausencia de relevancia.
- Las revisiones manuales documentadas deben conservarse.

## Opciones consideradas

- Corregir sólo la lista actual: los errores reaparecerían.
- Automatizar la asignación de etapas: no resuelve la evidencia ni corresponde
  al contrato del detector.
- Verificar menciones, versionar el filtro y reintentar lecturas fallidas.

## Decisión

El texto debe contener al menos un nombre de empresa de la cartera, normalizado
por acentos, mayúsculas y espacios, además de un término de proceso. La
atribución sale del texto, no de la consulta que lo descubrió. Si aparecen varias
empresas se conservan todas las menciones, con una principal para compatibilidad.

Los resultados automáticos anteriores se revalidan cuando reaparecen en la
ventana de búsqueda; el nuevo filtro queda marcado como versión 2. Una lectura
vacía no recibe veredicto y se reintenta en otra corrida. Las revisiones manuales
documentadas quedan excluidas de esa migración. No se cambian etapas.

## Pros y contras de las opciones

Evita atribuciones por coincidencias de palabras sueltas y descartes por fallos
temporales. Una mención y un verbo todavía pueden aparecer en antecedentes de
una norma ajena al proceso: la revisión humana sigue siendo necesaria. Las
normas que sólo nombren un activo o una denominación no contemplada pueden
quedar fuera. La migración cubre lo que se consulta; no acredita haber revisado
automáticamente todo el archivo histórico.

## Más información

Las pruebas cubren ruido por búsqueda OR, acentos y límites de palabra,
varias empresas, reintentos, caché antiguo y respeto de decisiones manuales.
La revisión de las normas queda en la auditoría del 8-sep-2026, con URL y
huella del texto leído.
