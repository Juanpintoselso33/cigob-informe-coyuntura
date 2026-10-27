---
madr: 4
id: '0371'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [libertad_opcion_salud]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'scripts/itcg.py', 'scripts/procedencia_anclas.py', 'data/gestion/opcion_salud_hitos.json', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts']
relacionado: ['0121', '0361', '0362']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma social y orden'
origen: 'Documento de Marcos (CiGob) «Revisión del indicador Libertad de opción en salud», 26-oct-2026, y decisión de Juan del mismo día («se hace lo que dice Marcos»).'
---

# ADR-0371 — La libre elección en salud se mide por hitos

## Contexto y planteo del problema

`libertad_opcion_salud` puntuaba el porcentaje de usuarios de prepagas con aportes
derivados directo (32,2 % en septiembre de 2026, puntaje 55,2). Marcos objetó que
eso mide una parte de la reforma y que depende de decisiones individuales: quien
no se cambia también ejerce su libertad de elegir.

## Factores de decisión

- Medir lo que depende del Gobierno: que la elección esté habilitada y funcione.
- Que cada hito tenga una regla documental fijada antes de puntuar.

## Opciones consideradas

- **Hitos de implementación (elegida).**
- Seguir con el porcentaje (decisión del 24-oct, que esta reemplaza).
- Renombrarlo «Aportes derivados directo a prepagas» (propuesta de Luis).

## Decisión

Pasa a «Implementación de la libre elección de cobertura de salud», con cinco
hitos:

| Hito | Peso | Norma o prueba | Desde |
|---|---|---|---|
| Marco normativo que habilita la elección | 25 % | DNU 70/2023 (BO 21-dic-2023, aviso 301122) | 29-dic-2023 |
| Fin de la permanencia obligatoria inicial | 20 % | Decreto 170/2024 (BO 21-feb-2024, aviso 302864) | 1-mar-2024 |
| Derivación directa sin intermediación | 20 % | Resolución SSS 3284/2024 (BO 7-oct-2024, aviso 315257) | 1-dic-2024 |
| Trámite de opción de cambio en línea | 20 % | ARCA y SSS, 4-dic-2024 | 4-dic-2024 |
| Funcionamiento efectivo y verificable | 15 % | Padrón SSS: ≥ 10 % de usuarios de prepagas con derivación directa | ene-2025 |

Escala: un ancla por escalón (25 → 10, 45 → 40, 65 → 65, 85 → 85, 100 → 100). El
porcentaje de usuarios queda en la tarjeta como contexto.

### Consecuencias

- El puntaje pasa de 55,2 a 100 desde enero de 2025 y queda estable: como advirtió
  Marcos, no es un defecto, se evalúa implementación.
- Por ser método, llega a la edición mensual y al archivo.

### Confirmación

Los hitos viven en `data/gestion/opcion_salud_hitos.json` con su fuente; la serie y
la tarjeta usan `gestion.salud_indice`.

## Pros y contras de las opciones

- Hitos: mide lo que el Gobierno controla; queda saturado una vez cumplido.
- Porcentaje: se mueve, pero castiga que la gente no se cambie.
