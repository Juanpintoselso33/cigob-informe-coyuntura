---
madr: 4
id: '0336'
estado: 'aceptado'
fecha: 2026-09-22
cinturon: 'gestion'
indice: 'ITCG'
archivos: ['scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/panel_validacion.py', 'web/src/pages/[slug].astro', 'web/src/pages/metodologia/index.astro', 'web/src/pages/metodologia/[id].astro', 'web/src/lib/fichas.ts', 'tests/test_itcg_sin_validacion_externa.py']
supersede: ['0226']
relacionado: ['0031', '0164']
ambito: 'ITCG · validación externa · si un índice de ejecución puede tener un contraste externo'
origen: 'Juan, 22-sep-2026: «sacá validación externa del índice de gestión, por propia definición no tiene validación externa».'
---

# ADR-0336 — El ITCG no tiene validación externa, por definición

## Contexto y planteo del problema

ADR-0226 llegó a la conclusión correcta y la publicó a medias. Dejó escrito que
**el ITCG mide lo que el gobierno HIZO y un validador tiene que medir lo que PASÓ
como consecuencia**, y con ese criterio descartó el gasto en subsidios. Pero en
vez de sacar la conclusión de fondo —que para un índice de ejecución no existe
contraste externo posible—, puso de titular el factor común del panel de
«respuesta del capital privado» y declaró la validez externa como **problema
abierto**, con cuatro condiciones para promover una candidata futura.

El mismo criterio de ADR-0226 cierra ese problema en vez de dejarlo abierto:

- Una serie que mida **lo que el gobierno hace** es un instrumento de la misma
  agenda: correlacionar con ella es una identidad, no una validación.
- Una serie que mida **lo que pasa como consecuencia** —el valor de las empresas,
  la entrada de capital, la confianza— mezcla la ejecución con todo lo demás que
  mueve a la economía y a la política: el precio internacional, el ciclo
  electoral, las expectativas. Validar la ejecución contra eso es validarla contra
  lo que el mercado **espera** de ella, que es lo que ADR-0226 ya le objetó al
  Merval.

No hay una tercera clase de serie. El factor del capital privado que hoy encabeza
la sección es de la segunda clase, y seguir publicándolo como «validación» le da
al lector una cifra (+0,68 en niveles) que parece confirmar el índice cuando por
construcción no puede hacerlo.

## Factores de decisión

- Una casilla de validación con un número adentro se lee como aprobada, diga lo
  que diga la prosa de al lado.
- La matriz cruzada ([[0031-validacion-cruzada-tercer-pilar]]) pone al ITCG en pie
  de igualdad con los índices que sí tienen contraste propio.
- Las cuatro estadísticas del capital privado siguen siendo útiles como contraste
  **ajeno** para los otros índices del panel.

## Opciones consideradas

1. Dejar todo como está ([[0226-el-itcg-se-queda-sin-validacion-externa-y-lo-declara]]).
2. Sacar el número de la card y dejar el panel y la matriz.
3. Sacar la validación externa del ITCG entera —sección, panel propio, matriz y
   correlaciones— y declarar por qué no existe.

## Decisión

**Opción 3.**

- `publicar._validacion_itcg` deja de publicar pares, r y gráfico. El bloque
  `validacion` del ITCG pasa a ser sólo la declaración (`sin_contraste: true`, un
  título y el motivo), para que el tablero diga por qué no hay sección en vez de
  omitirla en silencio.
- El ITCG sale de la matriz cruzada: pasa a ser **3 × 3** (ITCM, ITCIS, ITCP contra
  sus tres contrastes propios), y los textos que decían «los cuatro índices» se
  ajustan.
- `panel_validacion.FACTOR` pierde la entrada `itcg` y `validacion_externa` deja de
  construir el perfil de panel del ITCG y las correlaciones contra el Merval y el
  ICG. Las cuatro estadísticas del capital privado **siguen en el panel**, en
  `FAMILIA`, como contraste ajeno para los demás índices.
- La serie mensual reconstruida del ITCG **se sigue calculando**: la usan la
  matriz de redundancia y el archivo histórico.

### Consecuencias

- Las cuatro condiciones de ADR-0226 para promover un validador futuro quedan sin
  efecto: no hay candidata que pueda cumplir la primera y la segunda a la vez sin
  caer en uno de los dos casos de arriba.
- El ITCG queda con dos pilares de robustez —redundancia interna y sensibilidad a
  pesos— en vez de tres, y lo declara.

### Confirmación

`tests/test_itcg_sin_validacion_externa.py` verifica que el snapshot publicado no
tenga pares ni r para el ITCG, que la matriz cruzada no tenga fila ni columna del
ITCG y que el panel no construya perfil del ITCG.

## Pros y contras de las opciones

- **Opción 1.** A favor: no toca nada. En contra: publica una confirmación que el
  propio método dice que no puede existir.
- **Opción 2.** A favor: cambio mínimo. En contra: la matriz cruzada sigue
  tratando al ITCG como un índice con contraste propio.
- **Opción 3.** A favor: el tablero dice lo mismo que el método. En contra: el
  cinturón pierde una sección que el lector podía esperar; se compensa con la
  declaración.

## Más información

Precedentes: [[0164-familia-del-itcg-la-respuesta-del-capital-privado]] armó la
familia del capital privado; [[0226-el-itcg-se-queda-sin-validacion-externa-y-lo-declara]]
sacó al Merval de titular y dejó el problema abierto. Este ADR lo cierra.
