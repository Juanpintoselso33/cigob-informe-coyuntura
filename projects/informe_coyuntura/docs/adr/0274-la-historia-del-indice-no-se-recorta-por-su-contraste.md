---
madr: 4
id: '0274'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'transversal'
archivos: ['scripts/publicar.py', 'web/src/components/Evolucion.astro', 'web/src/lib/datos.ts', 'tests/test_historia_indice_independiente.py']
relacionado: ['0233', '0225']
ambito: 'Historia mensual de los cuatro índices'
origen: 'Inspección visual de portada y contraste con validacion_externa.json'
---

# ADR-0274 — La historia del índice no se recorta por su contraste

## Contexto y planteo del problema

La portada construía su evolución desde los pares comunes con la referencia
externa. Mostraba impacto social sólo hasta mayo aunque la reconstrucción
propia llegaba a agosto. El rezago del benchmark recortaba el monitor.

## Factores de decisión

- Separar trayectoria propia y muestra común de validación.
- Mantener los filtros de cobertura del constructor de cada índice.
- No mezclar la reconstrucción revisada con el snapshot conocido en cada fecha.

## Opciones consideradas

- Mantener los pares externos como fuente de la portada.
- Publicar la serie mensual completa que ya calcula el motor.

## Decisión

Agregar `serie_mensual` al bloque de cada índice y usarla en la evolución de
portada. Los gráficos externos conservan su muestra de meses comunes.
Se rectifica también el texto de cobertura macro: ICIP ya no es componente
vigente y no debe restarse del denominador de activos.

## Pros y contras de las opciones

Se recuperan meses existentes sin estimar puntos nuevos. El contrato suma un
campo explícito y conserva el aviso de reconstrucción sin ajustes del analista.

## Más información

El test verifica que una referencia que termina en mayo no recorte agosto de
la historia propia. El snapshot y la compilación verifican los cuatro cinturones.
