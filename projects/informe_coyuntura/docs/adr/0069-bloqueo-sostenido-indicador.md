---
madr: 4
id: '0069'
estado: 'aceptado'
fecha: 2026-07-16
cinturon: 'politica'
indicadores: [bloqueo_sostenido]
relacionado: ['0021', '0046', '0062', '0070']
modificado_por: ['0089']
ambito: 'Cinturón política · ITCP · dimensión Poder legislativo · `bloqueo_sostenido` (nuevo)'
---

# ADR-0069 — bloqueo_sostenido: la cara ganada del pulso legislativo entra al ITCP

## Contexto y planteo del problema

La revisión de la validación externa del ITCP (correlación con el EPU
Argentina) mostró que la reconstrucción histórica del índice cae 32 puntos a
lo largo de 2024 (77,7 en febrero → 46,0 en noviembre) en un año que fue,
en términos de pulso legislativo, bueno para el Ejecutivo: sostuvo el veto
jubilatorio (sep-2024) y el universitario (oct-2024) con el tercio del art.
83 CN, y mantuvo vivo el DNU 70/2023 todo el año pese al rechazo del Senado.

Nada de eso puntúa en el índice. La dimensión Poder legislativo mide la
producción propia (`eficacia_legislativa`, `ratio_dnu`) y las derrotas
consumadas (`derrotas_legislativas`, conteo absoluto), pero **nunca acredita
los bloqueos ganados**: un gobierno que sostiene seis vetos desafiados
puntúa igual que uno al que nadie desafió. Para un Ejecutivo sin mayoría
propia —que gobierna sosteniendo el tercio de una cámara y la vigencia de
sus decretos— esa es justamente la forma principal de su capital
legislativo (en términos matusianos: la capacidad de veto como recurso de
poder).

El costo empírico del hueco: la dimensión no tenía ninguna pata que midiera
2024 a favor, y la correlación ITCP↔EPU por año daba r=−0,03 en 2024 contra
−0,74 en 2025 (con el agravante de que `eficacia_legislativa` en 2024 medía
la cohorte de la gestión anterior, ver ADR-0070).

## Opciones consideradas

- Arreglar solo eficacia_legislativa (madurez 4m / cohorte acumulada de la gestión)
- ICG UTDT (confianza en el gobierno) como indicador del ITCP
- Contar solo vetos sostenidos (sin decretos)
- Ventana más corta (6m) para acelerar la recuperación post-crisis

## Decisión

1. **`bloqueo_sostenido` nuevo indicador**: % de normas propias DESAFIADAS
   en el recinto en los últimos 12 meses calendario que siguen EN PIE al
   cierre del mes. Desafiada = con al menos una votación en el recinto
   (insistencia de una ley vetada, gane quien gane; validez/rechazo de un
   decreto bajo la ley 26.122). En pie = la insistencia no se completó en
   ambas cámaras / el decreto no fue rechazado por las dos (ley 26.122,
   art. 24 — el rechazo de una sola cámara no deroga, caso DNU 70/2023).
   Mayor = mejor. Vetos sin insistencia votada y decretos nunca tratados no
   entran al denominador: sin desafío no hay prueba del bloqueo.

2. **Misma ventana y mismo registro que derrotas_legislativas**: 12 meses
   calendario (`_bloqueo_tasa_12m` calca `_derrotas_conteo_12m`), estado
   evaluado al cierre de cada mes histórico (reproducible: un punto
   publicado no cambia porque la norma cayera después). El registro
   versionado de eventos (ADR-0046) se extiende con campos aditivos:
   `insistencias_votadas` por veto y `sostenimientos` por decreto — el
   indicador de derrotas no los lee y queda intacto.

3. **Detección automática de los desafíos** (el requisito central del
   pedido). Diputados: clasificador incremental de actas PDF con watermark
   por id — cada acta se descarga y clasifica UNA vez en la vida del
   proyecto, usando como universo de ids el caché permanente del walk de
   cohesión; una insistencia de veto se reconoce por el número de ley en el
   motivo ("INSISTENCIA PROYECTO DE LEY 27.791.", formato 2025+) o — en el
   formato 2024 — por mayoría "Dos tercios" + motivo "EXPTE. N-PE-AAAA" (el
   mensaje del PE, mapeado a la ley vetada vía el CKAN de HCDN: TIPO
   MENSAJE con "OBSERVA" en el título; verificado con 0015-PE-2024→27.756 y
   0017-PE-2024→27.757); las HABILITACIONES de tratamiento (la moción
   procesal previa, también de 2/3 y sobre el mismo expediente) se excluyen
   por palabra clave — hallazgo de la primera corrida real: la habilitación
   de la 27.791 salió AFIRMATIVA (159-75) y la insistencia real NEGATIVA
   (160-83), confundirlas invierte el registro. Una votación de decreto se
   reconoce por el número en el motivo, con la dirección de la moción
   estándar de la bicameral (se vota el RECHAZO; AFIRMATIVO lo consuma —
   verificado contra los 7 casos reales 2024-2025). Senado: filtro
   "Insistencia…" del listado anual de actas (excluyendo habilitaciones
   sobre tablas), con el número de ley del título; insistió = afirmativos ≥
   2/3 de los emitidos. **Los casos ambiguos nunca se adivinan**: quedan en
   una cola de `pendientes` con aviso en cada corrida (dictámenes de
   aprobación de decretos —caso real DNU 179/2025 FMI—, mensajes
   multiproyecto, decretos que el registro no conoce — que pueden ser
   decretos simples fuera de la 26.122, caso real 681/25).

4. **Anclas 90/75/50/25 con referencia externa** (puntaje interpolado,
   ADR-0021): entre 2003 y 2025 el Congreso no revirtió NINGÚN veto
   presidencial (tasa histórica ~100%, incluso con Macri en minoría), así
   que ≥90 = dominio normal del bloqueo; <25 = tercio perdido. El período
   real recorre casi todo el rango: 100 (H1-2024) → 75 (H2-2024, cae el DNU
   656 pero se sostienen dos vetos) → 55→33 (ago-oct 2025, primera
   insistencia exitosa desde 2003 + 5 decretos derogados) → 20 (jul-2026,
   la resaca de la ventana de 12m). No se calibra contra el rango propio
   (disciplina de ADR-0059).

5. **Pesos de Poder legislativo: 20/25/15/20/20** (ratio_dnu / eficacia /
   veto_quorum / derrotas / bloqueo): cada indicador cede 0,05 y el nuevo
   toma 0,20, conservando el orden relativo previo (antes 25/30/20/25,
   ADR-0064). Los pesos ENTRE dimensiones (ADR-0036) no se tocan.
   Provisorio, sujeto a revisión editorial CIGOB (mismo compromiso que
   ADR-0052/0064/0067).

### Consecuencias

- El ITCP pasa de 10 a **11 indicadores puntuables**; el tablero publica la
  card y la serie (desde mar-2024, primer desafío votado — antes el motor
  renormaliza, igual que veto_quorum entre períodos).
- El valor actual de la card (~20%: 2 de 10 normas desafiadas en pie en la
  ventana ago-2025→jul-2026) puntúa 10 y BAJA el ITCP publicado hoy — no es
  un bug: la ventana de 12m todavía contiene la ola de sep-oct 2025, y el
  indicador de derrotas ya carga la misma memoria (valor 8). Ambos
  descargan juntos hacia oct-2026.
- La detección de Diputados mejora de paso la cobertura declarada de
  derrotas_legislativas (los rechazos de decretos votados primero en
  Diputados ahora se detectan sin esperar al Senado), sin cambiar su regla
  de conteo.
- Pendiente declarado: mostrar el indicador, sus anclas y el reparto de
  pesos al editor CIGOB en la próxima revisión editorial, junto con
  ADR-0070 (y los ya comprometidos 0052/0064).

## Pros y contras de las opciones

### Arreglar solo eficacia_legislativa (madurez 4m / cohorte acumulada de la gestión)

Insuficiente: eficacia pesa ~9% del ITCP y "arreglarla" mueve el piso de
2024 apenas 2 puntos; la madurez de 4 meses además reintroduce el sesgo de
inmadurez que ADR-0061 eliminó, y en 2024 sigue midiendo expedientes de la
gestión anterior. La parte honesta de ese diagnóstico quedó en ADR-0070
(máscara de era en la reconstrucción, sin tocar la card).

### ICG UTDT (confianza en el gobierno) como indicador del ITCP

Rechazada: es percepción encuestada — duplica el rol de la dimensión imagen
y voto, y conviene mantenerlo fuera del índice como referencia externa
discriminante (rol que ya cumple para el ITCG, ADR-0031).

### Contar solo vetos sostenidos (sin decretos)

Rechazada: el bloqueo de un Ejecutivo sin mayoría se juega en ambas vías
(art. 83 CN y ley 26.122), y la ola de ago-2025 fue de decretos — un
indicador solo-vetos se habría perdido la mitad de la crisis.

### Ventana más corta (6m) para acelerar la recuperación post-crisis

Descartado por ahora: rompería la consistencia con derrotas_legislativas
(misma familia de eventos, misma ventana) y duplicaría el ruido de un
indicador de eventos raros. El rezago de recuperación queda declarado en la
ficha como limitación; revisable si el editor lo pide.

## Más información

### Precedentes directos

ADR-0046 (derrotas_legislativas y su registro de eventos) · ADR-0062 (numerador desde fuentes que ven ambas cámaras) · ADR-0021 (puntaje interpolado, tramos extremos abiertos)

### Efecto en la validación externa (declarado)

Con la serie reconstruida del indicador dentro del motor (y junto con la
máscara de era de ADR-0070), la correlación de niveles ITCP↔EPU pasa de
−0,448 a ≈−0,60 (n=30): el indicador levanta el H2-2024 reconstruido con
señal real (+3 a +4 puntos: los vetos sostenidos ocurrieron) y profundiza
el pozo de sep-2025 justo cuando el EPU pica a 183. El r anual de 2024
sigue ≈0 — eso es del lado del EPU (serie plana en 2024, desvío 10 sobre
media 85, sin varianza que correlacionar) y ninguna recomposición del
índice lo puede arreglar; queda documentado para no perseguirlo como bug.
