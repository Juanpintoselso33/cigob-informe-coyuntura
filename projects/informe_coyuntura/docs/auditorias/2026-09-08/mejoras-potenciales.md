# Mejoras potenciales separadas de las correcciones

Este documento reúne decisiones opcionales de alcance metodológico. No se usan
para postergar inconsistencias de implementación, datos o documentación.

| Mejora | Motivo | Evaluación necesaria antes de adoptarla |
|---|---|---|
| Unidad de observación en privatizaciones | Enarsa y Transener aparecen como filas separadas aunque la venta de Citelec forma parte de la privatización por unidades de Enarsa. El promedio de etapas no mide dinero vendido. | Definir si se sigue a empresas, grupos o transacciones y cuantificar la sensibilidad antes de cambiar la cartera. La aclaración de alcance se incorpora ahora; no sumar importes entre matriz y participación vendida. |
| Recaudación con calendario y legislación constantes | Julio incluye vencimientos trasladados y reasignaciones fiscales. El ajuste estacional habitual no elimina esos efectos. | Evaluar una serie complementaria por tributo que separe actividad, cambios normativos y desplazamientos de caja. La ficha ya corrige la interpretación; el valor actual fue conciliado con ARCA y no se modifica para seguir una narrativa. |
| Revisar la correspondencia entre litigiosidad SRT y reforma laboral | Los juicios por riesgos del trabajo no miden directamente el canal indemnizatorio del FAL. Su caída tampoco identifica el mérito de reclamos ni un efecto causal de la reforma. | Buscar una serie del universo relevante y evaluar denominadores de exposición antes de reemplazar o reponderar. Se corrigen ahora las afirmaciones de causalidad y la continuidad de las ventanas, sin cambiar el constructo por iniciativa técnica (ADR-0285). |
| Validar el signo de la tasa de resolución judicial | El anuario CSJN verifica el cociente de flujos, pero una tasa menor no demuestra menor fricción con el Gobierno: mezcla causas sin identificar sus efectos. | Contrastar con duración y contenido de causas relevantes antes de cambiar polaridad o reemplazar la variable. El nombre y los límites se corrigen ahora, sin alterar pesos ni puntajes (ADR-0281). |
| Comparaciones mensuales con cobertura homogénea | ITCP junio sube 1,0 con cobertura variable y 3,3 con componentes comunes. La ausencia de conflicto social en agosto era un error de calendario ACLED ya corregido (ADR-0303), no una mejora opcional. ITCM julio sólo tiene IPI en actividad; junio también incluye EMAE y difusión. La omisión histórica del IAI era un error ya corregido (ADR-0301), no una mejora opcional. El piso actual evita cobertura muy baja, pero no elimina cambios de composición. | Evaluar una variación complementaria sobre componentes comunes o una reconstrucción con tratamiento explícito de rezagos. Conservar el índice vigente y cuantificar diferencias históricas antes de cambiarlo. La advertencia pública y el contraste se corrigen ahora. |
| Armonizar la base de victimización a 4T-2023 | La auditoría recuperó datos que antes faltaban en el colector. Enero de 2024 sigue siendo una base explícita válida, pero diferente de la mayoría de componentes. | Comparar toda la serie con ambas bases. En julio, el componente pasaría de 104,8 a 115,6 y el ITCIS subiría alrededor de 0,49 puntos con lo demás constante. Requiere decidir y documentar el cambio. |
| Ampliar cobertura de sector privado político | Hoy depende de expectativas de construcción; no cubre todo el empresariado. | Definir el constructo y conseguir series independientes y estables antes de sumar pesos. |
| Validación de gestión con cumplimiento externo | Las series de capital privado capturan expectativas y entorno, no verifican ejecución por sí solas. | Construir una matriz de hitos verificables, diferenciar ejecución, resultados y efectos; no optimizar pesos según correlaciones retrospectivas. |
| Validación cualitativa mensual con protocolo estable | Una muestra intencional permite detectar contradicciones pero no representa toda la conversación argentina. | Fijar corpus, pluralidad de fuentes, criterios de inclusión y fechas de corte; conservar desacuerdos y exclusiones. |
| Evaluación fuera de muestra | Las reconstrucciones revisadas no son pronósticos con información disponible en tiempo real. | Conservar versiones mensuales y separar calibración de evaluación antes de hablar de capacidad predictiva. |
| Regla explícita ante licitaciones desiertas | Intercargo conserva una etapa intermedia histórica aunque el llamado de julio quedó desierto. Corregir el hito no define por sí solo cuántos puntos debe perder. | Decidir si se mide máximo hito alcanzado o estado operativo actual; aplicar la misma regla a toda la cartera, admitir retrocesos en la historia y revisar las etapas intermedias. No convertir una licitación desierta en venta cerrada. |

Las correcciones técnicas siguen en el informe y los ADR. La lista se completará
con hallazgos adicionales a medida que avance la verificación integral.

La corrección de fechas del FAL (ADR-0305) hace visible la revisión manual
separada de la consulta CNV. Evaluar una regla operativa de antigüedad máxima
para esos registros curados y su frecuencia de revisión, con responsables y
fuentes primarias identificadas. El cierre del estado judicial al corte sigue
siendo una comprobación pendiente de esta auditoría, no una mejora opcional.
# Reservas: evaluar las exclusiones del diseño

La fórmula vigente agrega depósitos del Tesoro y un tramo de vencimientos de
II.1 (>3 meses–1 año) después de restar los flujos SDDS. ADR-0286 retiró su
identificación no demostrada con BOPREAL y su presentación como libre
disponibilidad; ADR-0287 evita cambiar de fórmula ante fallos de fuente.
Elegir qué pasivos excluir exige una decisión distinta: comparar alternativas
con y sin Tesoro, vencimientos por instrumento y activos líquidos frente a oro,
manteniendo constantes las fechas. No elegir una variante por reproducir una
banda de un analista en tres meses. Una alternativa debe tener justificación,
serie comparable y sensibilidad de sus anclas antes de reemplazar el diseño.

### Sensibilidad dentro de la banda baja de jornadas laborales

Las jornadas de enero–mayo de 2026 crecen aproximadamente 15,2% frente a
los mismos meses de 2025, pero el acumulado móvil de 4,76 millones sigue
en la banda de puntaje 100 (hasta cinco millones). No es un error del cálculo:
responde a las anclas históricas adoptadas. Evaluar si conviene mostrar una
señal de cambio junto al nivel o revisar la sensibilidad del tramo bajo,
sin recalibrar retrospectivamente para seguir las noticias. El contraste
actual ya distingue nivel y movimiento en `contraste-jornadas-laborales.md`.

## Protestas por fecha efectiva del evento

ACLED publica semanas sábado–viernes. El monitor agrupa esas semanas por el mes del sábado inicial, tanto en la base 2023 como en los doce grupos móviles. Es una convención reproducible, pero una semana que cruza mes o año no se divide. Evaluar el acceso a microdatos por fecha del evento para construir meses calendario exactos, cuantificar el cambio y decidir una revisión metodológica explícita. La corrección del corte semanal y su explicación ya están hechas; no se reparte cada semana uniformemente entre días sin evidencia.

## Control periódico de clasificación de decretos

El cotejo de ADR-0307 verificó todos los rótulos DNU de la historia reconstruida contra sus originales. Automatizar periódicamente el inventario completo y el cotejo de identificadores DNU/DECNU/DECTO permitiría detectar nuevas omisiones del filtro textual o errores de catalogación. No basta eliminar el filtro: eso habría incorporado erróneamente el 44/2026. La corrección del calendario ya está integrada; este control periódico adicional queda como mejora operativa.

### Descubrimiento de actas de Diputados

El listado volvió a ser accesible en navegador el 8-sep y mostró el máximo
5995. Evaluar usar su inventario como primera vía de descubrimiento,
conservando el respaldo PDF y la tolerancia a huecos cuando el listado falle.
El sondeo vigente recorre hasta 450 huecos seguidos: es robusto frente a los
saltos documentados, pero costoso. La auditoría usó un máximo observado y
no cambió esa política productiva. No reducir el margen sin reemplazar su
garantía de cobertura.

## Validación de anclas de bloqueo

La corrección del 8-sep retira la procedencia externa no demostrada de los cortes 90/75/50/25. Se conservan como criterio conceptual editorial sobre una tasa 0–100. Una eventual calibración necesita reconstruir el mismo universo de vetos y decretos efectivamente desafiados en otros gobiernos, distinguir sus reglas y analizar la incertidumbre con pocos eventos. No basta contar vetos emitidos ni convertir porcentaje de normas en porcentaje de bancas. Comparar sensibilidad y justificar cualquier cambio antes de modificar puntajes; no se implementó un rediseño.

## Consumo de carnes frente a faena

Evaluar una serie histórica mensual de consumo aparente comparable para el componente que puntúa, o redefinir explícitamente el constructo como producción. La faena no netea exportaciones y rebasarla no elimina divergencias de evolución; toneladas de carne tampoco miden proteína ingerida ni acceso individual. La ficha ya corrige esas afirmaciones. No se sustituye la serie ni se cambia su peso sin comparar cobertura, revisiones, diferencias históricas y efectos sobre el índice.
