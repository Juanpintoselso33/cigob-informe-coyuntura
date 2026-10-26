---
madr: 4
id: '0370'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [fal_modernizacion_laboral]
archivos: ['scripts/gestion.py', 'scripts/itcg.py', 'scripts/descargar_series.py', 'data/gestion/fal_hitos.json', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'tests/test_gestion_fal_actos.py']
relacionado: ['0142', '0228', '0361']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma laboral'
origen: 'Propuesta de Marcos (CiGob) del 23 y 24-oct-2026 («rev 2 DIMENSIÓN REFORMA LABORAL») y decisión de Juan del 26-oct-2026.'
---

# ADR-0370 — El FAL cuenta cinco hitos de construcción

## Contexto y planteo del problema

Desde [[0228-el-fal-puntua-lo-que-rige-no-lo-que-se-dicto]] el Fondo de
Asistencia Laboral se medía en tres etapas: dos actos fundamentales vigentes
(50 %), la entrada en vigencia del régimen (20 %) y al menos un fondo inscripto
en la CNV (30 %). Marcos propuso contar también los pasos operativos que se
dieron después: la RG CNV 1167/2026, la RG ARCA 5907/2026 y la oferta de los
bancos, y dar por cumplido el 90 % del FAL, dejando el 10 % para cuando las
empresas empiecen a operar.

## Factores de decisión

- Reconocer pasos de construcción reales, fechados y con fuente.
- No perder el control judicial que introdujo ADR-0228.

## Opciones consideradas

- **Cinco hitos de 18 % y adopción de 10 % (elegida).**
- Mantener ADR-0228: 50 de avance hasta el 1-dic, 70 desde entonces.

## Decisión

- **Construcción, 90 %:** Ley 27.802 (6-mar-2026), Decreto 408/2026 (1-jun),
  RG CNV 1167/2026 (BO 17-sep, aviso 347592), RG ARCA 5907/2026 (BO 1-oct,
  aviso 348365) y oferta bancaria (verificada el 26-oct en las páginas del Banco
  Nación y del Banco Ciudad). Cada uno vale 18. La ley y el decreto cuentan sólo
  si no están suspendidos con efecto general.
- **Adopción, 10 %:** al menos un FAL inscripto en la CNV.
- **Vigencia:** se sigue informando, pero deja de sumar por sí misma.
- Las bandas no cambian: con 90 de avance el puntaje es 100.

Esto cambia la regla de ADR-0228 en un punto: los tres hitos operativos y la
oferta bancaria cuentan antes de que el régimen rija. Es una decisión editorial
declarada; el control judicial de los actos fundamentales se conserva.

### Consecuencias

- Seguimiento diario: avance 50 → 90 y puntaje 55 → 100.
- Edición de septiembre: avance 54 (falta la RG ARCA, de octubre, y la oferta
  bancaria) y puntaje 58,8.
- La oferta bancaria son ofertas comerciales: los fondos no operan antes del
  1-dic-2026, y la ficha lo dice.

### Confirmación

`tests/test_gestion_fal_actos.py` fija los pesos, los hitos con fuente y la serie.

## Pros y contras de las opciones

- Cinco hitos: refleja el avance real de la puesta en marcha; el indicador queda
  en 100 hasta que exista adopción, sin margen para mejorar más.
- ADR-0228: más estricto, pero dejaba afuera normas ya publicadas que hacen
  falta para que el régimen funcione.
