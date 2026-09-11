---
madr: 4
id: '0279'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'vida'
indicadores: [trabajo_independiente, mortalidad_pymes]
archivos: ['web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'scripts/vida_cotidiana/collectors/trabajo_independiente.py', 'scripts/vida_cotidiana/collectors/srt_empleadores.py']
corrige: ['0218', '0219', '0250']
ambito: 'Alcance de las inferencias laborales'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0279 — Las series laborales no identifican transiciones

## Contexto y planteo del problema

El texto atribuía al cociente SIPA la capacidad de reconocer empresas cerradas
que se transforman en trabajadores independientes. Son agregados sin seguimiento
de individuos. Además, la cantidad de empleadores SRT de hasta 50 trabajadores
se describía como cierre neto directo: también cambia cuando una empresa cruza
el umbral de tamaño o deja de tener personal declarado sin cerrar.

## Decisión

Corregir descripciones, fichas y comentarios del colector. Explicitar los
universos, los cambios de composición y la ausencia de identificación de
trayectorias o quiebras. Conservar datos, signos y ponderaciones; cualquier
rediseño de la interpretación normativa del trabajo independiente es una
mejora metodológica que requiere una decisión separada.

## Más información

### Consecuencias

La interpretación queda acotada a lo que observan SIPA y SRT. El criterio de
puntuar invertido el peso independiente sigue visible como decisión del monitor.
Excluir monotributo social evita incorporar su quiebre administrativo, pero no
convierte el universo restante en la única descripción válida de la economía.

### Validación

El cotejo HTTP de estas fuentes se conserva en la auditoría del 8-sep-2026.
La validación comprueba que las cifras y fórmulas permanecen iguales al
regenerar las fichas y construir la web.
