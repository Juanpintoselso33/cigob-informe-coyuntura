---
madr: 4
id: '0271'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'vida'
indicadores: [motorizacion_total]
archivos: ['scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'tests/test_motorizacion_total.py']
corrige: ['0224']
relacionado: ['0323', '0328']
ambito: 'Alcance de la interpretación del flujo de patentamientos'
origen: 'Auditoría integral solicitada por Juan el 8 de septiembre de 2026'
---

# ADR-0271 — Los patentamientos no identifican trayectorias de hogares

## Contexto y planteo del problema

La explicación de la matriz de motorización infería que un total creciente
descarta sustitución de autos por motos y demuestra primeras compras de hogares.
El registro utilizado cuenta inscripciones iniciales, no hogares ni sus vehículos
anteriores. El razonamiento confunde un flujo agregado con trayectorias individuales.

Un contraejemplo basta: algunos hogares sustituyen un auto por una moto y otros
compran vehículos adicionales. El total puede subir mientras existe sustitución.
También puede crecer por reposición o flotas sin incorporar nuevos hogares al parque.
Un total sin variación tampoco demuestra caída; se lo debe describir como estable.

## Factores de decisión

- La interpretación no debe afirmar más que lo observado.
- Conservar la serie, el peso y la agregación evita confundir corrección del texto
  con un cambio de metodología numérica.
- La hipótesis de acceso requiere identificar propietarios y tenencia previa.

## Opciones consideradas

- Mantener la inferencia: no identifica el fenómeno que afirma.
- Retirar el componente: excede lo necesario para corregir esta afirmación.
- Describir flujo y composición, explicitando lo que no se identifica.

## Decisión

Aplicar la tercera opción. La explicación, descripción y ficha hablan de
patentamientos y participación de motos. Declaran que primeras compras,
reposición, flotas y sustitución pueden coexistir. No cambian polaridad,
pesos, universo, base, exención del recorte ni fórmula.

## Pros y contras de las opciones

Se pierde una conclusión atractiva pero no demostrada y se gana correspondencia
entre fuente y texto. Persiste la limitación de usar unidades heterogéneas como
proxy de consumo durable; su rediseño requeriría evidencia y decisión propia.

## Más información

- [Registro de automotores DNRPA](https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores).
- El contrato del colector conserva fecha, jurisdicción y unidades agregadas;
  no incorpora una identificación longitudinal de hogares.
- Validación: los cuatro casos de la matriz y el caso de variación nula; las
  cifras e índices publicados deben permanecer iguales tras regenerar la prosa.
