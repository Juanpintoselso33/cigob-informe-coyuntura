---
madr: 4
id: '0357'
estado: 'aceptado'
fecha: 2026-10-15
cinturon: 'transversal'
archivos: ['scripts/aviso_slack.py', 'tests/test_avisos_hilos.py']
modifica: ['0309']
relacionado: ['0350', '0356']
ambito: 'Avisos · #monitor-alertas'
origen: 'Juan, 15-oct-2026: las alertas «no están entrando más» con la corrida caída desde el 12'
---

# ADR-0357 — Un 🔴 que sigue abierto avisa en el canal cada tres corridas

## Contexto y planteo del problema

Del 12 al 15-oct-2026 la corrida nocturna no publicó cuatro noches seguidas
(ADR-0356). El 🔴 salió la primera noche y las otras tres se editó en su lugar
(«lleva 4 corridas»), como manda ADR-0309 para no repetir mensajes. Pero Slack no
notifica una edición: para quien no vio el primer mensaje, el problema no existía.
El diario quedó tres días con datos del 11 sin que nadie se enterara.

## Factores de decisión

- Una corrida caída varias noches seguidas es lo más grave que puede pasar en el
  canal; tiene que volver a notificar.
- Sin volver a un mensaje por noche (ADR-0309, ADR-0350).
- Un 🟡 que sigue no pide acción urgente: su raíz editada alcanza.

## Opciones consideradas

1. Respuesta en el hilo, también al canal, cuando un 🔴 llega a la tercera corrida
   y en cada múltiplo de tres.
2. Mensaje nuevo cada noche mientras siga el 🔴.
3. Respuesta en el hilo sin salir al canal.

## Decisión

Opción 1 (`RECORDAR_CADA = 3` en `scripts/aviso_slack.py`): dice cuántas corridas
lleva, desde cuándo y qué ve la gente, con el link a la corrida. La 2 vuelve al
ruido que sacó ADR-0309; la 3 no notifica a quien no sigue el hilo, que es el
problema.

### Consecuencias

- Buena: un 🔴 abierto vuelve a sonar a los tres días como mucho.
- Mala: un 🔴 que se arregla lento suma un mensaje en el canal cada tres noches.

### Confirmación

`tests/test_avisos_hilos.py`: con dos corridas caídas no hay recordatorio; en la
tercera y en la sexta sí, con broadcast; un 🟡 que sigue seis noches no lo tiene.
