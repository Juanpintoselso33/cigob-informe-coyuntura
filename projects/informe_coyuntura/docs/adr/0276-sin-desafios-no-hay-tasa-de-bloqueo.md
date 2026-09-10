---
madr: 4
id: '0276'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [bloqueo_sostenido, desafios_legislativos]
archivos: ['scripts/politica.py', 'scripts/publicar.py', 'scripts/gate_calidad.py', 'tests/test_politica_sin_universo.py']
relacionado: ['0069', '0089']
ambito: 'Universo vacío y vigencia de las ventanas legislativas'
origen: 'Auditoría integral: tarjeta en caché frente a conteo mensual cero'
---

# ADR-0276 — Sin desafíos no hay tasa de bloqueo

## Contexto y planteo del problema

El colector trataba un universo vacío como un fallo de consulta. Arrastraba
entonces el conteo y la tasa de una ventana anterior, aunque el registro no
contuviera desafíos en los doce meses calendario actuales. La ficha ya preveía
excluir la tasa sin denominador: la implementación no cumplía esa regla.

## Factores de decisión

- Un conteo observado puede valer cero; una razón con denominador cero no existe.
- Un fallo de fuente no prueba ausencia de eventos.
- La tarjeta debe explicar por qué un componente no participa ese mes.

## Opciones consideradas

- Arrastrar la última tasa: mezcla universos temporales.
- Asignar cero o cien: inventa un resultado de bloqueo sin desafíos.
- Publicar el estado sin universo y renormalizar la dimensión, como prevé la ficha.

## Decisión

Con consulta exitosa y cero desafíos se publica el conteo cero y la tasa nula
con estado `sin_universo`. La tasa no recibe puntaje, peso efectivo ni semáforo;
el motor redistribuye el peso entre los componentes observados. La tarjeta
permanece visible con explicación y acceso a la metodología.

La actualización conjunta exige que se hayan actualizado el registro de eventos,
el recorrido de Diputados y los clasificadores de ambas cámaras. Si falla una
etapa se conservan ambos resultados anteriores, marcados como desactualizados.
Los desafíos fechados después del día de corte se excluyen incluso si pertenecen
al mismo mes. El gate admite un valor nulo sólo bajo el contrato explícito de
universo vacío; cualquier combinación contradictoria sigue bloqueando.

## Pros y contras de las opciones

Corrige la aplicación de la metodología sin cambiar bandas ni pesos nominales.
La composición efectiva puede variar entre meses: debe distinguirse de una
mejora de la capacidad del Ejecutivo para sostener normas. El descubrimiento
semiautomático conserva las limitaciones de cobertura y clasificación de actas.

## Más información

La ventana incluye el mes en curso y los once anteriores. No equivale a los
últimos 365 días. El histórico conserva las tasas de los meses con denominador;
no se rellena con cero ni se extiende el último punto a meses sin universo.

Un PDF descargado cuya fecha no puede interpretarse es un fallo de lectura,
no un hueco de numeración. Sólo un 404 explícito acredita acta inexistente.
El recorrido queda incompleto y tampoco se congela un año histórico con ese
fallo. Una respuesta interna nula sin estado HTTP conserva la misma cautela.
