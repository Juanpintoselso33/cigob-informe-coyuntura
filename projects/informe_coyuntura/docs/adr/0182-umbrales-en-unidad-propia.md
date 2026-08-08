---
madr: 4
id: '0182'
estado: 'aceptado'
fecha: 2026-08-08
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/parametrica.py', 'tests/test_semaforo.py']
relacionado: ['0181']
ambito: 'Umbrales de color expresados en la unidad propia de cada índice'
origen: 'El semáforo de 4 colores (ADR-0181) define cortes en tensión; se necesita también exponerlos en puntos 0-100 e índices base-100'
---

# ADR-0182 — Umbrales de color en unidad propia de cada índice

## Contexto y planteo del problema

ADR-0181 define el semáforo en términos de tensión 0-10. Para que el frontend
y análisis posterior trabajen cómodamente, se necesita expresar esos mismos
umbrales en las unidades nativas de cada índice:
- Puntaje 0-100 para ITCM, ITCG, ITCP
- Índice base-100 para ITVC (con su propia fórmula de tensión)

## Factores de decisión

- La conversión debe ser exacta y reversible desde tensión.
- No debe redondearse la tensión intermedia (ver ADR-0181).
- Cada índice tiene su fórmula de tensión; se aplica la inversa para obtener umbrales.

## Decisión

Cada función de color recibe un valor en su unidad nativa y lo convierte a tensión
sin redondear, luego aplica los cortes de ADR-0181. No se definen umbrales separados.

## Más información

Ver ADR-0181 para los cortes en tensión y la lógica de color.
