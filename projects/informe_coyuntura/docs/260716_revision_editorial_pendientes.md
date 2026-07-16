# Revisión editorial — decisiones pendientes del cinturón político y vida cotidiana

**Fecha:** 16 de julio de 2026 · **Preparado por:** equipo técnico
**Contexto:** con el lanzamiento público previsto para agosto, quedan **tres decisiones abiertas** que requieren criterio editorial (no son bugs: son elecciones de constructo con números distintos según el camino) y **cuatro decisiones ya tomadas de forma provisoria** que piden ratificación. Todos los escenarios de este documento están calculados sobre los datos reales publicados al 16-jul; los contrafácticos son reproducibles.

**Referencia rápida del estado actual:** ITCP 66,4 (tensión 3,4) · ITVC 95,5 (tensión 5,9) · validación externa ITCP↔EPU r = −0,599 · ITVC↔ICC r = 0,556 (sin ICC) / 0,664 (completo).

---

## Resumen ejecutivo

| # | Tema | Tipo | Qué mueve |
|---|------|------|-----------|
| D1 | Bandas de cohesión del bloque | **Decisión abierta** | ITCP hoy ±4 pts; lectura de todo 2024 |
| D2 | Peso de entrada de bloqueo_sostenido | **Decisión abierta** | ITCP hoy ±1,5 pts |
| D3 | Eficacia legislativa: máscara vs rediseño | **Decisión abierta** | card 22% → 38% si se rediseña |
| R1 | bloqueo_sostenido: constructo y anclas (ADR-0069) | Ratificación | — |
| R2 | Mora de las familias 50/50 (ADR-0067) | Ratificación | — |
| R3 | Conflictividad nacional (ADR-0052) y salida de comisiones (ADR-0064) | Ratificación | — |
| R4 | Máscara de era en la validación (ADR-0070) | Ratificación | — |

---

## D1 — Cohesión del bloque: ¿bandas del rango observado o del benchmark histórico?

**La decisión de fondo de esta tanda.** Las bandas vigentes (99,9 / 99 / 97 / 95, ADR-0039/0048) están ancladas al rango real del bloque LLA en esta gestión (Rice 90,3–100, mediana 97,4). La alternativa es anclarlas a la disciplina partidaria argentina histórica (índices de Rice de los bloques mayores ≈ 85–95 en la literatura comparada), por ejemplo 98 / 95 / 90 / 85.

La diferencia no es técnica sino de **qué pregunta responde el indicador**:

- *Bandas actuales:* "¿cómo está la cohesión de **este** bloque respecto de sí mismo?" — un Rice de 96,6 (hoy) puntúa **48**: cohesión disputada dentro de su propio rango.
- *Bandas históricas:* "¿cómo está este bloque respecto de **cualquier** bloque argentino?" — el mismo 96,6 puntúa **86**: disciplina alta para el estándar histórico.

**Evidencia (ambos escenarios corridos sobre los 31 meses reales):**

| | Bandas actuales | Bandas históricas |
|---|---|---|
| ITCP 2024 reconstruido (mín / mediana) | 49,7 / 63,6 | 59,7 / 71,0 |
| Correlación total vs EPU (validación) | **−0,599** | −0,541 |
| Puntaje hoy (Rice 96,6) | 48 | 86 |
| ITCP publicado hoy (aprox.) | 66,4 | ~70 |
| Discriminación (distribución en 31 meses) | usa las 5 bandas | comprime hacia arriba |

**Los argumentos honestos de cada lado:**
- A favor de las históricas: la lectura de 2024 con las actuales es dura (mediana 63,6) para un año en que el bloque no perdió ninguna votación clave por indisciplina propia; y el benchmark externo es la vara que este equipo usa para anclar (ratio DNU vs ACIJ, eficacia vs Directorio Legislativo).
- A favor de las actuales: el rango 90–100 es desempeño real, no un artefacto estructural (hubo 12 meses en 100 — el techo se alcanza), así que no cumple la condición para recalibrar; discriminan mejor los movimientos que el benchmark externo aplana; y el par externo (EPU) acompaña mejor la serie que producen (−0,599 vs −0,541).

**Recomendación del equipo técnico:** mantener las actuales. La caída de cohesión de 2024 (Rice 100 → 95,5: ruptura del MID, salidas de Pagano/Arrieta) fue un deterioro real del capital del bloque y las bandas actuales lo registran; las históricas lo declararían irrelevante. Si el editor prefiere la lectura histórica, es defendible — pero implica aceptar ~0,06 menos de validación externa y una serie más plana.

---

## D2 — bloqueo_sostenido: ¿con qué peso entra a la dimensión?

El indicador nuevo (ver R1) entró a Poder legislativo con **0,20** (reparto 20/25/15/20/20 con ratio DNU / eficacia / quórum / derrotas). Como su ventana de 12 meses todavía carga la ola de insistencias y derogaciones de sep-oct 2025, hoy vale 20% (2 de 10 normas desafiadas en pie) → puntaje 10, y ese peso explica la mayor parte de la baja del ITCP publicado (71,3 → 66,4).

**Opciones:**
- **0,20 (como está):** paridad con derrotas — las dos caras del mismo pulso pesan igual. Costo: el golpe de entrada es fuerte y el indicador va a seguir en el piso hasta que la ola salga de la ventana (octubre 2026).
- **0,10–0,15 (entrada prudente):** amortigua el escalón de adopción (~+1,5 pts de ITCP con 0,15) devolviendo el excedente a eficacia y derrotas; se puede subir a 0,20 en la revisión siguiente con el indicador ya rodado.

**Recomendación del equipo técnico:** 0,20. El análisis de sensibilidad muestra que el indicador dominante del ITCP sigue siendo la cohesión, no el bloqueo — el indicador nuevo no captura el índice; y el escalón de adopción es un hecho declarado en la ficha, no un defecto a esconder. Pero es la decisión con menos costo de cambiar si el editor prefiere gradualismo.

---

## D3 — Eficacia legislativa: ¿máscara en la validación o rediseño del indicador?

Con la cohorte madura vigente (proyectos del Ejecutivo publicados 12–24 meses antes, ADR-0061), todo el 2024 del indicador midió la cartera de la gestión **anterior** muriendo con el cambio de congreso — no la eficacia de esta gestión. Para la validación externa eso ya se resolvió con una máscara (el indicador no entra a la reconstrucción histórica hasta dic-2025, cuando la cohorte es 100% de la era actual — ADR-0070). La card pública no se tocó: su cohorte actual ya es de esta gestión.

**La decisión restante es si eso alcanza o si se rediseña el indicador:**
- **Mantener máscara (statu quo):** costo cero. El histórico público de 2024 sigue mostrando la cohorte heredada — defendible como dato ("la cartera heredada no prosperó") mientras no contamine la validación.
- **Rediseñar a cohorte acumulada de la era** (todos los proyectos de la gestión con al menos 4 meses de maduración): el indicador "habla" de esta gestión desde el día uno y la máscara se vuelve innecesaria. Costos: la card salta de 22,2% a ~38,5% (la cohorte corta descuenta los proyectos viejos sin sancionar), hay que re-anclar las bandas de ADR-0061, y los primeros meses de cualquier gestión futura tendrían n muy chico (1–3 proyectos).

**Recomendación del equipo técnico:** mantener la máscara. El rediseño solo se justifica si al editor le importa que el histórico público de eficacia cubra el primer año de cada gestión con datos propios — es más honesto conceptualmente pero cuesta una recalibración completa a semanas del lanzamiento.

---

## Ratificaciones (decisiones ya tomadas, provisorias)

**R1 — bloqueo_sostenido como indicador (ADR-0069).** % de las normas propias desafiadas en el recinto (insistencias de veto votadas + decretos bajo la ley 26.122) que siguen en pie, ventana 12 meses. Es la cara *ganada* del pulso legislativo que el conteo de derrotas no acredita: los vetos sostenidos de sep-oct 2024 y la supervivencia del DNU 70/2023 no puntuaban en ningún indicador — y son la forma principal de capital legislativo de un Ejecutivo sin mayoría. Anclas 90/75/50/25 con referencia externa dura: entre 2003 y 2025 el Congreso no revirtió ningún veto presidencial. Detección 100% automática en actas de ambas cámaras, verificada contra los 16 casos reales del período. *Se pide ratificar el constructo y las anclas (el peso es D2).*

**R2 — Mora de las familias separada, 50/50 con endeudamiento (ADR-0067).** La mora salió del compuesto multiplicativo y puntúa como indicador propio invertido; la dimensión Vulnerabilidad reparte 50/50. Efecto de agregación declarado: ITVC 90,7 → 95,5 (el producto castigaba la interacción; el promedio no) — es metodología, no mejora de coyuntura. *Se pide ratificar el reparto 50/50 — sin un criterio sustantivo para asimetría, es el menos arbitrario.*

**R3 — Conflictividad nacional (ADR-0052) y salida de comisiones_caidas (ADR-0064).** Ya comprometidos en revisiones anteriores: la conflictividad ACLED país reemplazó al índice CEPA (serie real de 30 meses vs 2 puntos no comparables), y comisiones salió del índice porque su fuente es ciega a las sanciones del Senado (mismo defecto que se corrigió en eficacia) y solapa con ella.

**R4 — Máscara de era en la validación (ADR-0070).** La parte ya aplicada de D3: la reconstrucción histórica del ITCP no usa eficacia antes de dic-2025. Criterio a priori por composición de la cohorte (la misma doctrina que excluye dic-2023 de toda la reconstrucción), no calibración contra el benchmark.

---

## Notas cerradas con evidencia (no requieren decisión)

1. **La rampa de adhesión provincial al RIGI no se toca.** Se auditó el contrafáctico: enmascarar sus primeros meses (4,2% en jul-2024, recién creado el régimen) *empeora* la validación (−0,599 → −0,575), porque desde oct-2024 el indicador aporta señal real que sostiene su dimensión. El artefacto se limita a jul-sep 2024 y no altera ninguna conclusión.
2. **La correlación ITCP↔EPU de 2024 (~0) no es un defecto del índice.** El EPU argentino fue una serie sin varianza ese año (desvío 10 sobre media 85: la desinflación planchó la incertidumbre de prensa mientras el capital legislativo se erosionaba). Ninguna recomposición del índice puede correlacionar contra una constante. En 2025 r = −0,79 y en 2026 r = −0,71.
3. **La anti-fase ITVC↔ICC de ago-2025 a abr-2026 es divergencia real de constructos.** El ICC se movió con el ciclo político (derrumbe preelectoral 47→37, euforia post-electoral 40→48) mientras las condiciones materiales se deterioraron con rezago justo en el rebote (brecha salario/canasta 118→109 desde noviembre, mora en aumento). Ningún rezago de 1 a 4 meses correlaciona en la ventana; fuera del episodio, el contemporáneo sigue siendo el mejor ajuste (0,556).

---

## Anexo — validación externa vigente (16-jul-2026)

| Par | r (niveles) | n | Esperado |
|---|---|---|---|
| ITCM ↔ riesgo país | −0,726 | 31 | negativa ✓ |
| ITCG ↔ Merval USD | +0,767 | 32 | positiva ✓ |
| ITCG ↔ riesgo país | −0,886 | 32 | negativa ✓ |
| ITCP ↔ EPU Argentina | −0,599 | 30 | negativa ✓ |
| ITVC (sin ICC) ↔ ICC UTDT | +0,556 | 30 | positiva ✓ |
