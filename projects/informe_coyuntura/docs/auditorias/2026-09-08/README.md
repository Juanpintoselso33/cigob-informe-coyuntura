# Auditoría integral del Monitor de Gobierno CIGOB

**Corte: 8 de septiembre de 2026. Etapa cerrada con reservas por indicación de Juan. Cambios locales, sin despliegue.**

[Conclusión y decisiones de cierre](cierre.md).

[Estado vigente y continuidad](estado-actual.md). Las secciones de cotejos
adicionales conservan la secuencia de revisiones; sus valores intermedios
no sustituyen el cuadro actual de los cuatro cinturones.

El monitor ofrece una lectura defendible de restricciones del proyecto de
gobierno, pero no acredita por sí solo bienestar general, calidad institucional
ni pronóstico electoral. La revisión encontró cálculos consistentes y problemas
reales de actualización, documentación y presentación. Se corrigieron
fuentes atrasadas, inferencias que excedían los datos y el recorte de la historia
mensual de la portada. La validación externa es parcial: no corresponde afirmar
que los cuatro índices quedaron empíricamente validados.

**Alquiler corregido:** se sustituyó la API discrepante por el original del INDEC
en tarjeta e historia. La revisión de alquiler dejó inicialmente el ITCIS en 93,3; tras actualizar construcción queda en 93,1.
Véase [evidencia y corrección](alquiler-correccion-pendiente.md).

El informe de sensibilidad separado se corrigió para conservar la conversión
del REM y el error compartido del IPC que ya usaba la web (ADR-0289).
Para ITCM 64,1, el rango combinado del informe separado es 62,1–66,0.
La web usa otra muestra Monte Carlo y puede diferir por redondeo y simulación. No son intervalos de confianza de
una encuesta ni modifican el índice central. El recálculo también actualiza
los aportes de las tarjetas, evitando metadatos heredados del caché (ADR-0290).

**Cobertura judicial corregida localmente:** 705/955 = 73,82%, con padrón original,
ancla corregida y flujos netos separados. El traslado de Fraga podría reducir
el numerador en uno; siguen explícitos los límites de juras, habilitaciones y
exhaustividad de bajas. [Cálculo integrado](cotejo-judicial-integrado.json).

## Alcance y evidencia

- Censo completo de **63 indicadores publicados, 62 con observación para puntuar, 24 dimensiones y cuatro índices**:
  [indicadores.csv](indicadores.csv), [dimensiones.csv](dimensiones.csv).
- Verificación reproducible de pesos nominales/efectivos, suspensiones,
  correspondencia entre tarjetas y componentes, agregación y tensión:
  [coherencia.json](coherencia.json), con SHA-256 del snapshot.
- Lectura de motores, colectores, publicación, contratos, manuales, fichas y ADR.
  Regeneración de manuales y fichas Markdown desde sus fuentes canónicas.
- Verificación directa priorizada de BCRA, UTDT, CAME y resumen oficial CEI;
  contraste cualitativo de publicaciones y debate político recientes. No es una
  certificación independiente de cada observación de las 63 series.
  [Cobertura por fuente](cobertura-fuentes.csv): 57 comprobados,
  una reproducción pendiente de cierre judicial (FAL), tres comprobados con
  salvedad (salud, cortes de calle y referencia histórica legislativa), una
  corrección integrada con límites de cobertura judicial y una revisión
  parcial de privatizaciones. No quedan consultas incompletas de actas en
  el corte vigente. La categoría acredita el alcance documentado, no toda
  la historia de la fuente ni su validez causal.
- Comparación mensual enero-agosto de 2026; diagnóstico estadístico con toda
  la historia reconstruida disponible. Las series retrospectivas revisadas no
  equivalen al conjunto de información conocido en cada fecha histórica.

La documentación vigente es la web y los Markdown generados. Los DOCX conservados
en `output/fichas/` son versiones históricas enviadas y no se sobrescribieron.

### Cotejo adicional de fuentes macro y deuda familiar

Las catorce consultas macro del [registro HTTP](cotejo-macro-fuentes.json)
reprodujeron el valor y la fecha de las tarjetas. El registro conserva URLs,
estados y hashes de respuesta: una repetición del mismo colector no basta para
certificar que su ruta siga siendo la última publicación. La matriz de cobertura
registra los cierres posteriores por indicador; el ICA tiene una comprobación separada.

El [calendario oficial INDEC](https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_2sem2026.pdf)
permite distinguir los rezagos: IPC agosto se anuncia para el 10 de septiembre,
EMAE julio para el 24, salarios julio para el 22 y supermercados julio para el
23. El [IPC julio](https://www.indec.gob.ar/uploads/informesdeprensa/ipc_08_2642C82F62AE.pdf)
confirma 2,1% redondeado; el monitor conserva 2,11% calculado con el índice.
Así, julio es el último IPC disponible al momento de la consulta y limita
correctamente los indicadores reales que requieren ese deflactor.
IPI e ISAC julio se publicaron durante esta auditoría. Las planillas originales
confirman julio y revisan junio, mientras las API siguen en junio. IPI e ISAC ya están integrados en tarjetas e historia. El IAI incorpora el original de bienes de capital y llega a julio con −5,66%:
[evidencia y alcance](industria-construccion-julio-pendiente.md).

La [verificación IEF](cotejo-ief-fuentes.json) descubrió la planilla de la edición
del primer semestre de 2026 desde su página oficial; la página del segundo
semestre responde 404. Sus 169 observaciones terminan en abril: carga del
servicio de deuda de **24,076% de la masa salarial registrada**, consistente
con el dato del monitor. La fecha de edición de julio no convierte ese dato
en una observación de julio.

## Correcciones realizadas

La revisión adicional de [privatizaciones](privatizaciones-revision.md) incorpora
el llamado formal de Belgrano Cargas en agosto y corrige los hitos de AySA e
Intercargo. La cartera completa aún requiere cerrar su revisión individual.
El [contraste CAME enero-agosto](contraste-came-2026.md) agrega evidencia externa
de consumo débil y documenta también los meses que no coinciden con el ITCIS.

| Hallazgo | Evidencia y resolución |
|---|---|
| Mora atrasada aunque la descarga respondía HTTP 200 | El anexo viejo terminaba en mayo; el enlazado por la edición vigente llega a junio. Se cambia el origen conservando personales + tarjetas ponderados por saldo: **14,41% en junio**, frente a 14,52% en mayo del snapshot previo. [ADR-0272](../../adr/0272-el-anexo-bancario-con-http-200-puede-estar-viejo.md). |
| Comercio exterior rezagado en la API | Se incorpora el cuadro original vigente de INDEC a la historia compartida de tarjeta y gráfico. El saldo de los doce meses a julio es **USD 23.731 millones**, con revisiones de meses previos y ventana completa. [ADR-0275](../../adr/0275-ica-vigente-completa-la-api-historica.md). |
| Victimización en abril cuando existía julio | El portal actual publica enlaces relativos que el colector no reconocía. Se recuperan los informes: **27,3% en julio**, frente a 28% de abril en el snapshot anterior. PDF verificado por extracción y lectura visual. [ADR-0273](../../adr/0273-victimizacion-descubre-el-portal-vigente-y-enlaces-relativos.md). |
| Falsa ausencia de mediciones de victimización de 2020–2023 | El archivo recuperado incluye diciembre de 2023, con 27,8%. Se rectifica ficha, fórmula explicada y nota del cinturón. Enero de 2024 se conserva como base explícita, sin afirmar que faltan datos de 2023. |
| Patentamientos usados para inferir trayectorias de hogares | Un total mayor no identifica primeras compras, reposición, flotas o sustitución auto/moto. Se corrigen explicación, ficha y prueba sin cambiar fórmula ni pesos. [ADR-0271](../../adr/0271-patentamientos-no-identifican-trayectorias-de-hogares.md). |
| Evolución de portada recortada por el benchmark | Impacto social se dibujaba hasta mayo aunque la reconstrucción llegaba a agosto. La historia propia se publica separada de la muestra común del contraste. [ADR-0274](../../adr/0274-la-historia-del-indice-no-se-recorta-por-su-contraste.md). |
| Documentos con componentes, pesos o validaciones antiguos | Se actualizan README, arquitectura, glosario, catálogo de fuentes, manuales y fichas; se distingue ITCIS público de ITVC interno, suspensiones y panel externo. El texto macro deja de descontar ICIP del conjunto de componentes activos. |
| Demora atribuida sin evidencia al organismo | El gate ahora distingue antigüedad del dato y fallo de descarga: que no haya error HTTP no prueba que la fuente no haya publicado algo nuevo. |

Las reparaciones, incluida la serie original de alquiler, dejan el ITCIS
en 93,1 tras la actualización posterior de construcción, con tensión 6,4/10. No se ajustaron pesos para lograr coincidencia con noticias.

## Coherencia de los cuatro cinturones

| Cinturón | Índice actual | Tensión | Qué puede interpretarse |
|---|---:|---:|---|
| Macro | 64,1 | 3,6/10 | Condiciones para sostener el programa; no distribución de sus beneficios. |
| Política | 73,0 | 2,7/10 | Recursos y restricciones de gobernabilidad; no aprobación ni calidad institucional. |
| Gestión | 79,1 | 2,1/10 | Ejecución del programa según compromisos seleccionados; no eficacia social de cada reforma. |
| Impacto social | 93,1 | 6,4/10 | Condiciones materiales y percepción frente a referencias heterogéneas; no porcentaje de bienestar. |

Las dimensiones nominales suman 100% en cada cinturón. Al suspender un componente,
su peso efectivo se redistribuye dentro de la dimensión. Hay 67 componentes
nominales y 63 no suspendidos, de los cuales 62 puntúan en este corte: apoyo empresario, judicialización, reestructuración de
organismos y sentimiento digital están suspendidos. No son ceros observados. Bloqueo sostenido, sin universo vigente, tampoco puntúa.
ICC tiene actualmente 8,25% efectivo del ITCIS.

La base del ITCIS combina referencias: mayormente 4T-2023, victimización enero
de 2024, pobreza con puente entre mediciones y tarifas con umbrales de carga
salarial. El techo 140 tiene una excepción en motorización. Por ello 93,1 no
significa que el bienestar sea exactamente 6,9% inferior al comienzo del mandato.

### Censo de dimensiones

Los puntajes de impacto social son base-referencia; los otros son puntajes
de bandas. No deben compararse directamente entre columnas de cinturones.

| Cinturón | Dimensión | Peso efectivo | Puntaje | Activos/nominales |
|---|---|---:|---:|---:|
| macro | Estabilidad monetaria-inflacionaria | 26.00% | 68.6 | 3/3 |
| macro | Viabilidad fiscal-comercial | 24.00% | 82.7 | 3/3 |
| macro | Capacidad y costo del financiamiento | 16.00% | 60.9 | 4/4 |
| macro | Actividad económica | 11.00% | 62.8 | 3/3 |
| macro | Competitividad externa | 11.00% | 48.8 | 1/1 |
| macro | Inversión | 12.00% | 36.4 | 1/1 |
| politica | Poder legislativo | 21.00% | 54.1 | 6/6 |
| politica | Alianzas territoriales | 19.00% | 81.1 | 3/3 |
| politica | Cohesión interna del oficialismo | 15.00% | 100.0 | 1/1 |
| politica | Conflicto social | 10.00% | 71.5 | 2/2 |
| politica | Imagen y voto | 7.00% | 73.6 | 1/1 |
| politica | Poder judicial | 15.00% | 57.1 | 3/4 |
| politica | Sector privado | 13.00% | 71.4 | 1/2 |
| gestion | Reformas económicas fundamentales | 35.00% | 73.5 | 3/3 |
| gestion | Reforma del Estado | 25.00% | 100.0 | 2/3 |
| gestion | Reforma laboral | 15.00% | 57.9 | 2/2 |
| gestion | Privatizaciones e inversión | 15.00% | 70.9 | 3/3 |
| gestion | Reforma social y orden | 10.00% | 90.9 | 3/3 |
| vida_cotidiana | Ingresos y consumo | 28.06% | 112.5 | 5/5 |
| vida_cotidiana | Presión de precios | 25.00% | 98.4 | 3/3 |
| vida_cotidiana | Vulnerabilidad financiera | 10.00% | 24.8 | 2/2 |
| vida_cotidiana | Prospectivas de empleo | 24.19% | 91.9 | 6/6 |
| vida_cotidiana | Confianza y percepción | 8.25% | 91.1 | 1/2 |
| vida_cotidiana | Seguridad | 4.50% | 104.8 | 1/1 |

### Límites de cobertura que deben acompañar la lectura

- Competitividad e inversión macro, cohesión, imagen, sector privado político,
  percepción y seguridad social dependen hoy de un único componente activo.
- «Sector privado» político queda representado por la brecha de expectativas de
  obra pública/privada; no representa a todo el empresariado argentino.
- Menor actividad de control judicial puede significar menos restricciones al
  Ejecutivo dentro del constructo político; no es una mejora institucional.
- Reducción de dotación y gasto de funcionamiento están en 100. Esa saturación
  indica cumplimiento según las bandas; no demuestra eficiencia o calidad de servicios.
- Ingresos y consumo pueden tener direcciones distintas. El promedio 112,5 de
  ingresos convive con supermercados debajo de su base y vulnerabilidad en 24,8.
- Comparten fuentes y tendencias varios componentes. Monte Carlo y exclusión
  de componentes prueban estabilidad frente a supuestos, no verdad externa.

## Contraste mensual con Di Tella

Los índices siguientes son **reconstruidos**, sin ajustes del analista. No son
la portada publicada en cada mes. «—» indica cobertura insuficiente para publicar
ese mes, no ausencia de tensión. ICG está en escala 0–5; no es aprobación porcentual.
ICC es variación mensual y además integra el ITCIS: su coincidencia no constituye
una validación independiente.

| Mes 2026 | ITCM | ITCP | ITCG | ITCIS | ICG UTDT | ICC UTDT, % mensual |
|---|---:|---:|---:|---:|---:|---:|
| 2026-01 | 59.4 | 65.7 | 73.4 | 96.1 | 2.40 | +2.2 |
| 2026-02 | 54.9 | 64.7 | 73.7 | 96.1 | 2.38 | -4.7 |
| 2026-03 | 67.5 | 66.9 | 74.3 | 94.6 | 2.30 | -5.3 |
| 2026-04 | 59.5 | 62.6 | 71.2 | 94.1 | 2.02 | -5.7 |
| 2026-05 | 64.4 | 67.4 | 77.1 | 93.4 | 1.99 | +1.3 |
| 2026-06 | 64.8 | 68.4 | 78.7 | 94.6 | 2.07 | +6.4 |
| 2026-07 | 60.4 | 67.9 | 79.1 | 93.7 | 1.94 | -4.8 |
| 2026-08 | — | 68.2 | — | 93.3 | 2.06 | -1.1 |

Fuentes primarias de las ocho observaciones: [ICG UTDT](https://www.utdt.edu/ver_contenido.php?id_contenido=1439&id_item_menu=2964)
y [ICC UTDT](https://www.utdt.edu/ver_contenido.php?id_contenido=2575&id_item_menu=4982), consultadas el 8-sep-2026.

**Lectura:** entre enero y agosto empeoran el ITCIS y la confianza en el Gobierno,
mientras el ITCP termina por encima de enero. No invalida automáticamente al ITCP:
obliga a distinguir poder para gobernar de confianza pública. Abril muestra una
caída compartida entre política, gestión y confianza; junio, una recuperación
de confianza y del índice social; julio vuelve a mostrar debilidad social.
Estas coincidencias temporales no identifican las causas.

**Control de cobertura:** agosto incluye conflicto social tras corregir ACLED. La posterior incorporación de siete sanciones y una reunión omitidas por CKAN lleva el cambio a +0,3 puntos, tras rectificar también la fecha de publicación de PE 7/2025, también con componentes comunes. Coincide en dirección con ICG, sin demostrar identidad entre ambos constructos. Junio conserva un problema de composición: pasa de +1,0 en la serie completa a +3,3 con componentes comunes, por el rezago de jornadas no trabajadas.
La [descomposición](descomposicion-itcp.json) identifica aportes por dimensión
y entradas/salidas; se reproduce con `scripts/auditoria_descomposicion_itcp.py`.
La web explicita que la evolución combina cambios de valores y de cobertura.

**Revisión de cobertura macro:** se corrigió una omisión del IAI en toda
la reconstrucción histórica, aunque inversión ya pesaba 12% en portada.
Además, los originales de INDEC incorporan julio y revisan meses anteriores.
Julio queda en 60,4; sin inversión habría dado 63,7 y sin inversión ni IPI,
69,1. Son variantes de cálculo, no movimientos económicos dentro del mes.
La dimensión de actividad de julio todavía sólo cuenta con industria: EMAE
y difusión terminan en junio. La comparación sobre componentes comunes se
documenta en el [cotejo de composición](revision-macro-julio.json): junio 61,3 y julio 60,4, frente a 64,8 y 60,4 con cobertura variable.

## Contraste cualitativo y fuentes independientes

| Evidencia fechada | Relación con el monitor | Evaluación |
|---|---|---|
| CAME, ventas minoristas agosto, publicado 6-sep: −0,2% interanual real, −2,7% mensual; acumulado −2,4%. | Compatible con dificultades de consumo y presión financiera pese a mejoras en otros planos. | Convergencia parcial; muestra de comercios, no censo de hogares. [Informe CAME](https://www.redcame.org.ar/novedades/574311137/las-ventas-minoristas-pyme-descendieron-02-interanual-en-agosto). |
| CEI, resumen del 24-ago: EMAE junio +2,7% interanual; industria +2% en junio pero −2,2% en el semestre; inflación julio 2,1% mensual. | La actividad agregada puede recuperarse con sectores rezagados. El IPI del monitor promedia tres variaciones interanuales: no comparar su −2% directamente con junio aislado. | Consistencia de órdenes y heterogeneidad; comparte estadísticas INDEC, no es validación independiente. [Resumen oficial CEI](https://cancilleria.gob.ar/userfiles/ut/2026-08_resumen_indicadores_0.pdf). |
| BCRA, informe junio: mora agregada de familias 12,8%; la baja admite efectos de castigos y denominadores. | Persiste vulnerabilidad. El monitor da 14,41% porque limita el universo a personales y tarjetas. | No intercambiar porcentajes de universos diferentes. [BCRA junio](https://www.bcra.gob.ar/publicaciones/informe-sobre-bancos-junio-de-2026/). |
| LICIP, julio: 27,3% de hogares víctimas; +2,3 puntos respecto de junio y +5 frente a julio de 2025. | La comparación contra enero de 2024 puede ser favorable mientras empeora el último año. | Contraste de bases: no titular «mejora la seguridad» sin ventana. [Informe UTDT](https://www.utdt.edu/download.php?fname=_178596896306235900.pdf). |
| Infobae, 7-sep: recuperación de agenda por Malvinas y negociación pendiente de votos para reforma electoral. | Compatible con recursos políticos y dificultades legislativas simultáneas. Cohesión propia no asegura votos ajenos. | Ilustración cualitativa, no conversión de artículos a puntaje. [Crónica política](https://www.infobae.com/politica/2026/09/07/el-gobierno-capitaliza-el-efecto-malvinas-y-se-prepara-para-negociar-los-votos-de-la-reforma-electoral/). |

La muestra de prensa es intencional y acotada; no representa toda la conversación
argentina ni un análisis de sentimiento de redes. Se contrastan hechos, períodos
y constructos, sin buscar sólo artículos favorables al monitor. Se excluyó una
nota que atribuía resultados de todo agosto a una publicación fechada el 20 de
agosto, y no se usaron publicaciones sociales como encuesta de opinión.

## Qué demuestra la validación estadística

Recalculada el 8-sep con las series corregidas, en `output/validacion_externa.json`.

| Índice y contraste | r niveles | r cambios mensuales | Conclusión admisible |
|---|---:|---:|---|
| ITCM / Líder UTDT | 0,732 (32 meses) | 0,427 (31 cambios) | Asociación moderada en cambios; sin prueba causal ni pronóstico fuera de muestra. |
| ITCIS / factor de consumos físicos | 0,103 (30 meses) | 0,344 | Correspondencia parcial; factor explica 37,6% de la varianza del panel. |
| ITCG / factor de capital privado | 0,682 (31 meses) | −0,052 | La asociación en niveles no se sostiene mensualmente; no certifica la ejecución. |
| ITCP / EPU | −0,284 (32 meses) | −0,261 | Asociación débil en la dirección esperada; alcance limitado. |

En el panel, la ventaja de correlación propia sobre ajena en cambios es apenas
0,025 para ITCIS y negativa (−0,028) para ITCG; ITCP alcanza 0,164, con sólo dos
anclas propias y sin factor estimable suficiente. Agregar el ITCIS al modelo que explica el factor social mediante una tendencia
temporal aumenta el R² en 0,056 dentro de la muestra. Estos resultados desaconsejan la palabra
«validado» como conclusión general y no justifican ajustar pesos a posteriori.

## Pendientes concretos y criterio de cierre

1. **Cobertura judicial:** el 705/955 es una estimación reconstruida. El
   Consejo corrobora San Justo no habilitada al 4-sep; falta precisar la
   salida de Fraga de Civil 104 y cerrar cobertura de juras, habilitaciones
   y bajas. [Alcance y evidencia](cobertura-judicial-pendiente.md).
2. **FAL:** falta la consulta judicial posterior al 21-ago. El expediente
   público exige un CAPTCHA, cuya autorización o intervención está pendiente.
   La consulta automática de normas no reemplaza esa revisión.
   [Estado judicial](fal-estado-judicial-pendiente.md).
3. **Privatizaciones:** los hitos de las nueve empresas fueron revisados con
   las salvedades registradas; faltan inventario exhaustivo de novedades y
   conciliación de importes cobrados. Cola vacía o ausencia de noticias no
   acredita ausencia de actos. [Revisión](privatizaciones-revision.md).
4. **Consolidación:** terminar comprobación de presentación local y revisión
   técnica proporcional de los últimos cambios; dejar el resultado y los
   límites en el registro. No hay despliegue de esta auditoría.

La identidad de la cohorte vigente de eficacia y las actas de ambas cámaras
ya están cotejadas. Desafíos está actualizado en cero y bloqueo sin universo,
con redistribución de peso. No son pendientes de fuente del corte actual.

Las decisiones de rediseño —bases comunes, alcance de proxies, unidades de
privatización y descubrimiento de actas— están en
[mejoras-potenciales.md](mejoras-potenciales.md). Se discuten por separado;
no se retocaron pesos para hacer coincidir los índices con la prensa.
Septiembre sigue abierto: el borrador de lectura externa no constituye una
firma editorial institucional. El contraste enero-agosto está documentado
y sus resultados mixtos no prueban validez global, causal o predictiva.

## Reproducción y comprobaciones

Desde `projects/informe_coyuntura`:

```sh
.venv/bin/python scripts/auditoria_coherencia.py --salida /tmp/cigob-auditoria
.venv/bin/python scripts/gate_calidad.py
.venv/bin/python -m pytest tests/ -q --tb=short
```

La web se compila con `npm run build` dentro de `web/`. El censo final no arroja
fallas de estructura ni aritmética. El gate se debe releer después de cada integración; sus avisos históricos
no acreditan pendientes actuales. La inspección visual cubrió la portada y la ficha de mora completas.
La revisión anterior con `codex review` no encontró defectos introducidos
en aquel corte; precede a las correcciones recientes de parser y sensibilidad
y no debe presentarse como revisión de esos cambios. El resultado de la suite completa
se registra en [validacion.md](validacion.md).

Las descargas usaron URLs oficiales con requests y, cuando correspondía,
transporte curl ante conexiones lentas; BCRA se procesó desde el anexo oficial descargado.
No se cambiaron valores a mano ni se desplegó producción.

### Empleo e ingresos: alcance y réplica

Diez tarjetas sociales fueron reproducidas contra INDEC, SIPA y SRT; las respuestas se conservan en [cotejo-social-fuentes.json](cotejo-social-fuentes.json). La ficha de empleo independiente y la de empleadores SRT corrigen inferencias sobre trayectorias individuales y cierres de empresas que los agregados no identifican (ADR-0279). No cambian los valores ni las fórmulas.

El [cotejo social restante](cotejo-social-resto-fuentes.json) reproduce tarifas IIEP agosto (14,5% del salario), carnes SAGYP julio (113,94 kg/hab/año), nowcast UTDT febrero-julio (31,3%; intervalo 29,8–32,7) y motorización DNRPA agosto (31,25 vehículos por mil habitantes en doce meses). La estimación de pobreza corresponde a un semestre móvil, no a incidencia observada exclusivamente en julio.

### Cotejo de gestión

Cinco consultas reales se conservan en [cotejo-gestion-fuentes.json](cotejo-gestion-fuentes.json). Apertura, dotación, gasto y litigiosidad reproducen el snapshot. La brecha CCL/mayorista cambió intradiariamente de 4,74% a 5,35%; se actualizó el snapshot y se corrigió la fecha para tomar el día de la cotización más antigua, conservando ambas marcas de tiempo (ADR-0280). [Cotizaciones utilizadas](cotizacion-brecha.json). La fórmula no cambia; el ITCG de esa etapa era 80,5; la actualización tributaria posterior lo lleva a 79,1.

El [cotejo RIGI, FAL y piquetes](cotejo-rigi-fal-piquetes.json) reproduce sus valores, pero distingue consulta y curaduría. RIGI: USD 49.766 millones aprobados y USD 153.709 millones en evaluación, 24,5% aprobado; no desembolsado. El FAL conserva [revisión pendiente del estado judicial](fal-estado-judicial-pendiente.md). ADR-0305 ya corrige su tarjeta y ficha: separa las fechas de revisión normativa, judicial y consulta CNV, y retira las garantías de ausencia de rezago y de integridad del archivo local. También deja de presentar los juicios SRT como resultado directo del FAL. Piquetes conserva la salvedad de acceso documentada en su cotejo posterior; el detector no transforma ese dato anual en mensual.

### Fuentes y contraste político adicional

El [cotejo de seis fuentes políticas](cotejo-politica-fuentes.json) reproduce votómetro, expectativas de construcción, producción legislativa, sesiones de comisiones de control, cobertura judicial y jornadas no trabajadas. La réplica no certifica la exhaustividad de sus universos. El [contraste cualitativo político](contraste-politico-cualitativo.md) documenta episodios de febrero, abril y agosto y conserva diferencias entre victorias legislativas, confianza y condiciones sociales. El contraste incluye enero-agosto y la descomposición aritmética por dimensión, con control de cambios de cobertura.

El [segundo cotejo político](cotejo-politica-resto-fuentes.json) reproduce DNU, eficacia legislativa, quórum, adhesiones e IAF. El anuario oficial CSJN 2025 corroboró además 26.524 casos resueltos y 58.424 ingresados (45,4%). El indicador pasa a llamarse «Tasa de resolución de la Corte»: no mide duración ni demuestra ventaja gubernamental (ADR-0281). La suite integral terminó con **3338 passed, 4 skipped, 5 warnings**; los omitidos no se cuentan como comprobaciones realizadas.

El [cotejo adicional de gestión](cotejo-gestion-final-fuentes.json) reproduce desregulación, concesiones y asistencia directa. El [cotejo adicional de política](cotejo-politica-final-fuentes.json) reproduce conflicto nacional, Senado y alineamiento provincial. Diputados no permitió determinar el acta más reciente: la cohesión bicameral conserva su componente anterior y queda como consulta incompleta. El cotejo posterior de la metodología ACLED corrigió esa primera lectura: la semana del 29 de agosto empieza ese sábado y termina el 4 de septiembre, por lo que el grupo de agosto sí está completo. Se incorporó a tarjeta e historia (ADR-0303). Los registros distinguen respuestas HTTP conservadas de consultas Session/POST cuyo cuerpo no quedó archivado.

### Actualización tributaria (ADR-0282/0283)

El [cotejo tributario](cotejo-tributario-actualizado.json) completa julio: apertura 7,62% y base imponible 102,1. ITCM de portada 67,5 e ITCG 79,1. La historia también se revisa: ITCG julio pasa de 84,7 a 79,4 al incorporar apertura antes ausente; junio queda en 79,0. ITCM julio pasa de 69,8 a 69,1 y enero de 61,2 a 60,8 por actualización de composición y factores estacionales. La tabla mensual fue recalculada; no se atribuyen estos cambios de cobertura a acontecimientos políticos. Véase [vigencia de catálogos](vigencia-catalogos.md).

El [cotejo del portal RIGI](cotejo-rigi-portal.json) confirma el sheet utilizado y la deduplicación por nombre del propio portal. Los montos repetidos por provincia son consistentes. El 24,5% corresponde a inversión comprometida aprobada sobre aprobada más evaluada; no certifica desembolsos.

El [informe original EMAE de junio](https://www.indec.gob.ar/uploads/informesdeprensa/emae_08_26AADBE275B1.pdf) corrobora 2,7% interanual redondeado y doce de quince sectores en alza: la difusión de 80% coincide. El calendario sitúa julio el 24 de septiembre. Se cierran ambos cotejos en [cotejo-emae-publicacion.json](cotejo-emae-publicacion.json). La difusión amplia no implica aportes uniformes: minería y agro explican 1,1 puntos del crecimiento agregado.

El [cotejo directo de la planilla SIPA](cotejo-sipa-planilla.json) confirma mayo como último período enlazado en ambos portales oficiales. Empleo privado original y participación independiente sin estacionalidad reproducen sus respectivas tarjetas; se conserva el carácter provisorio. El buscador mostraba febrero, por lo que se usó la consulta directa del portal.

El [catálogo SRT y su selector vigente](cotejo-srt-catalogo.json) confirman la fuente de empleadores por tamaño y mayo como último mes habilitado. Se suma a la réplica numérica archivada; no convierte variación del stock de empleadores de 1–50 personas en un conteo de cierres.

El [cotejo de litigiosidad SRT](cotejo-litigiosidad-vigente.json) confirma mayo y +2,1% en ambas vistas. ADR-0285 exige ventanas de calendario completas y corrige la interpretación causal respecto del FAL. El valor actual no cambia.

El [IPC alimentos julio](cotejo-ipc-alimentos-publicacion.json) concilia con el cuadro nacional del informe: 2,0% redondeado frente a 1,98% del monitor. El calendario programa agosto para el 10 de septiembre.

La lectura mensual de litigiosidad exige distinguir ventanas: el portal SRT informa 10.699 juicios en mayo de 2026 frente a 11.937 en mayo de 2025 (−10,4%), mientras los acumulados móviles del monitor crecen 2,1%. Ambas cifras pueden ser correctas: la tarjeta suaviza doce meses y no describe el giro del mes aislado. El contraste está conservado en el cotejo de litigiosidad.

El [contraste de empleo con EPH y prensa](contraste-empleo-eph.md) concilia las dos tasas trimestrales y separa sus universos de las cifras más amplias que suelen aparecer en titulares. Se corrigió una referencia antigua en la ficha de informalidad sobre redistribución de pesos; los valores no cambian.

El [cotejo de salario y canasta](cotejo-salario-canasta.json) confirma el mes común de junio: 1.915.878,76 / 495.622,30 = 3,8656. La canasta de julio ya existe, pero el portal RIPTE continúa en junio. La ficha ahora precisa remuneración imponible y CBT por adulto equivalente del Gran Buenos Aires; no debe interpretarse el cociente como ingreso de bolsillo ni como canastas familiares cubiertas.

**Reservas continúa abierta en su alcance metodológico.** El [original SDDS julio](cotejo-sdds-reservas.json) reproduce la cifra, pero no demuestra que el tramo de vencimientos excluido sea BOPREAL ni que el resultado mida libre disponibilidad. ADR-0286 corrige las equivalencias en la web. ADR-0287 retira el respaldo con otra fórmula y evita sustituir Tesoro ausente por cero en la historia. El [balance real](cotejo-reservas-mes-comun.json) aporta Tesoro para los 26 meses publicados; julio recalcula 11.962 M USD sin cambio. Falta conciliar las exclusiones por instrumento; evaluar alternativas queda en mejoras potenciales. No se certifica la interpretación por el solo hecho de reproducir la aritmética.

El [cotejo fiscal](cotejo-fiscal-originales.json) concilia los doce meses del resultado primario con las planillas originales y el gasto de funcionamiento de julio de 2026 y 2023. Se corrigió «devengados» por base caja y el enlace de la ficha al IMIG, en lugar de Presupuesto Abierto. El ratio fiscal usa recaudación como escala; no representa el porcentaje sobrante de los ingresos del mismo universo contable. Las cifras de 5,96% y −28,69% no cambian.

**Financiamiento actualizado:** [agosto tiene resultados oficiales fuera de la planilla anual](financiamiento-agosto-pendiente.md). Se incorporan cuatro colocaciones fijas en pesos, con tasas, montos y fechas de liquidación comprobados. Tarjeta e historia coinciden en 7,25% real anual; el ITCM de portada pasa a 67,0. El registro de fuentes exige revisar la cobertura de cada nuevo mes (ADR-0288).

El [cotejo original ARCA de apertura](cotejo-apertura-arca-original.json) concilia
1.192.117,217 M pesos de derechos de exportación, 466.938,064 de importación
y 108.728,933 de estadística. Convertidos al A3500 promedio de julio y divididos
por 15.592,535 M USD de intercambio del ICA original, dan 7,6243%: la tarjeta
7,62% coincide. ARCA ya publica agosto; julio sigue siendo el último mes común
porque el ICA llega a julio. Una baja de determinadas alícuotas legales puede
coexistir con subas del cociente mensual por composición y calendario de pagos;
el indicador no mide exclusivamente cambios normativos.

El [contraste de recaudación de julio](contraste-recaudacion-julio.md) verifica
el subtotal DGI del original ARCA y reproduce independientemente los factores
estacionales de 55 meses: la tarjeta 102,1 coincide. La ficha aclara que los
vencimientos excepcionales y reasignaciones de saldos mencionados por ARCA
pueden explicar parte de la mejora; no toda suba equivale a mayor actividad.

El [cotejo de transferencias federales](contraste-federal-transferencias.md)
reconstruye los 24 flujos originales y confirma +1,6% real anual en 2025.
El contraste con la OPC agrega −2,8% para el primer semestre de 2026: son
períodos distintos y la tarjeta anual no describe la coyuntura más reciente.

El [cotejo de control judicial](contraste-control-judicial.md) confirma las 13
sesiones del archivo de notas, con septiembre todavía abierto, y corrige la
afirmación de que Disciplina no publicó acciones. Se conserva el límite entre
frecuencia de reuniones y resultados de las causas.

**Cobertura judicial conserva límites:** el [cotejo del catálogo y del BO](cobertura-judicial-pendiente.md) encontró movimientos posteriores al archivo de julio y renovaciones que no equivalen a vacantes nuevas. La corrección integrada sustituye el anterior 69,63% por 73,82%; aún falta cerrar juras, habilitaciones y exhaustividad de bajas, como se detalla al comienzo de este informe.

### Expectativas de construcción: referencia temporal corregida

La brecha es −1,8 pp, referenciada a agosto como inicio del horizonte agosto–octubre. El promedio vuelve a exigir doce meses consecutivos y recupera filas históricas omitidas. Se recalcularon historia y contrastes: [evidencia y alcance](expectativas-construccion-corregidas.md). Esa corrección dejó ITCP de portada en 70,5; la posterior incorporación de adhesiones omitidas lo lleva a 71,1. No cambian pesos ni bandas.

El [cotejo independiente de concesiones](concesiones-cotejadas.md) confirma el universo de 9.090,85 km y la adjudicación formal de los 16 tramos. La ficha explicita las fuentes y separa ese avance administrativo de obras y operación efectiva.

El [cotejo original ACLED](acled-calendario-corregido.md) corrige el corte sábado–viernes, recupera agosto en la historia política y explicita la convención de agrupación mensual. La descarga fallida ya no renueva el sello del archivo conservado.

El [cotejo de adhesiones provinciales al RIGI](adhesiones-rigi-corregidas.md) identifica Santa Fe y CABA, omitidas por el catálogo nacional. El total pasa de 16 a 18 sobre 24 y se corrige la historia desde sus fechas documentadas. La ficha retira las garantías de actualización inmediata e irreversibilidad.

El [cotejo de producción legislativa](produccion-legislativa-corregida.md) corrige los límites mensuales, las leyes duplicadas, el promedio histórico y el gráfico metodológico (ADR-0306). Esa etapa dejaba 22 leyes; ADR-0308 incorpora siete sanciones omitidas y eleva el total a 29. Julio cae 0,6 y agosto sube 0,4; se actualizan el contraste y la descomposición. La exhaustividad del catálogo sigue pendiente.

El [cotejo nominal del ratio DNU](ratio-dnu-pendiente.md) supera la falla de la consulta anual mediante tramos mensuales y verifica los originales. Corrige el día adicional en cuatro meses históricos; el valor actual sigue en 1,4. La discrepancia de tipificación del decreto 44/2026 queda identificada y no se suma como DNU.

La corrección [de sesiones y sanciones de agosto](sesiones-sanciones-corregidas.md) lleva el ITCP de portada a 71,9 y el cierre histórico de agosto a 68,2 (julio: 67,9). Cinco sanciones definitivas omitidas por CKAN y la reunión que las trató se integran desde originales HCDN. Se revisa también marzo a 66,9 por las fechas del índice. No se cambian pesos ni anclas. La cobertura legislativa posterior sigue pendiente de conciliación completa.

El [cierre del cotejo de sanciones de agosto](senado-sanciones-corregidas.md) incorpora dos leyes del Senado, 27.824 y 27.825, y verifica los números 27.819–27.823 de Diputados. El total vigente es **29 leyes**, ITCP 71,9 y agosto histórico 68,2. La referencia histórica de 2008–2025 conserva salvedad de exhaustividad.

Transener: cierre verificado en el comunicado CNV del 28-ago; la etapa máxima no corresponde a junio. La [corrección](privatizaciones-revision.md) afecta junio y julio históricos, sin modificar el 55,6% de avance actual ni el ITCG de portada (79,1).

Actualización posterior al cotejo legislativo: [actas y eventos integrados](diputados-integracion-actual.md), ITCP actual 73,0; las cifras 71,9 de las etapas anteriores son históricas. Los cierres mensuales de julio (67,9) y agosto (68,2) no cambian.
