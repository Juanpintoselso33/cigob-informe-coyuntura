# Handoff para Claude: remediación de las 17 discrepancias

**Fecha:** 25 de agosto de 2026  
**Proyecto:** Informe de Coyuntura CIGOB  
**Estado de la auditoría:** 69/69 indicadores revisados; 27 confirmados, 25 compatibles, 17 discrepantes y 0 no verificables  
**Objeto auditado:** snapshot publicado en `web/src/data/informe.json` con corte 25-08-2026

## Mandato

Implementar la remediación de las 17 discrepancias documentadas por la auditoría externa. El trabajo no consiste en cambiar números a mano en el JSON publicado: hay que corregir el colector, universo, fórmula, nombre o participación en el índice según corresponda; agregar regresiones; reconstruir la historia afectada; recalcular los índices; y recién entonces regenerar informe y snapshot.

Trabajar por entregas pequeñas y verificables, en el orden de este documento. Antes de cada entrega:

1. Leer el `AGENTS.md` del repositorio y `projects/informe_coyuntura/README.md`.
2. Ejecutar `git status --short` y preservar todos los cambios locales ajenos.
3. Leer los ADR y tests de los indicadores que se van a modificar.
4. Congelar como fixture el valor anterior y los insumos externos usados para justificar el cambio.
5. No hacer push, merge ni despliegue sin autorización explícita. Cada push a `main` dispara un build de Vercel.

No implementar las 17 correcciones como un único cambio opaco. Completar primero la Entrega 1, informar diff, pruebas e impacto en scores, y continuar con la siguiente entrega según la instrucción del usuario.

## Fuentes de verdad de la auditoría

Leer estos expedientes antes de tocar código. Contienen evidencia, enlaces externos, cálculos, períodos, unidades y nivel de confianza:

- [Resumen de la auditoría completa](260825_auditoria_completa.md)
- [Macroeconomía — 17/17](260825_macro.md)
- [Política — 19/19](260825_politica.md)
- [Impacto social — 19/19](260825_impacto_social.md)
- [Gestión — 14/14](260825_gestion.md)
- [Segundo barrido — 15 casos](260825_segundo_barrido_15.md)
- [Tercer barrido — 3 casos](260825_tercer_barrido_3.md)

Si un valor de este handoff difiere de los expedientes, prevalece el expediente más reciente y luego el dato oficial verificable para el mismo corte, universo y definición. No sustituir una discrepancia documentada por el último dato disponible sin distinguir actualización de corrección metodológica.

## Clasificación de las 17 discrepancias

| Grupo | Cantidad | Tratamiento |
|---|---:|---|
| Dato, corte o cuenta corregible | 7 | Corregir colector/fórmula y reconstruir serie |
| Corpus, universo o denominador no homogéneo | 5 | Cerrar o redefinir explícitamente, reconstruir serie y recalibrar |
| Constructo no identificado por sus insumos | 5 | Sacar del score hasta rediseño; conservar como contexto sólo si el rótulo es descriptivo |
| **Total** | **17** | |

La prioridad no depende sólo del tamaño del error. Un indicador aritméticamente reproducible puede ser más riesgoso si puntúa un fenómeno que sus insumos no miden.

## Decisiones transversales ya recomendadas

Estas decisiones evitan que la implementación quede bloqueada por opciones metodológicas abiertas:

- Para DNU y leyes, usar una convención jurídica homogénea basada en **publicación en el Boletín Oficial**. El rótulo debe decir `DNU publicados / leyes publicadas`. Con el corte auditado, el resultado es `37 / 25 = 1,48`.
- Para series nominales anuales reales, deflactar cada flujo mensual por el IPC del mismo mes llevado a una base común y luego sumar. No dividir el total nominal anual por un único IPC de punta o promedio no ponderado.
- Para crédito privado, el indicador principal debe comparar crédito **en pesos** en un universo homogéneo. El crédito en dólares y su valuación en pesos deben mostrarse por separado como contexto.
- Si el rótulo de trabajo independiente conserva la referencia al empleo registrado, incluir monotributo social en numerador y denominador. Si no hay una historia reproducible, cambiar el rótulo al universo restringido en vez de imputarlo.
- `subocupación demandante` es porcentaje de la PEA. El identificador legado `pluriempleo` no debe sobrevivir en datos, fórmulas, UI ni tests como sinónimo.
- Un indicador suspendido libera su peso y los restantes se renormalizan automáticamente **dentro de su dimensión**. No asignar pesos nuevos a mano para preservar el score anterior.
- Toda suspensión debe conservar, si existe valor informativo, una card de contexto claramente marcada `no integra el índice`, sin semáforo ni aporte al score.
- Un cambio de definición o universo exige una serie histórica homogénea y una nueva calibración de bandas. No empalmar silenciosamente definiciones incompatibles.

## Entrega 0 — línea de base y red de seguridad

Antes de modificar lógica:

1. Guardar un manifiesto reproducible del snapshot auditado: fecha, hash, valor, unidad, fecha del dato, score, peso efectivo y dimensión de los 69 indicadores.
2. Registrar los cuatro scores de cinturón y el índice agregado vigente.
3. Crear fixtures mínimos para los insumos decisivos de las correcciones de la Entrega 1.
4. Asegurar que los tests fallen si reaparecen los valores o definiciones erróneos.
5. Preparar un comparador `antes/después` que reporte por indicador: valor, score de banda, aporte, peso efectivo, dimensión y cinturón.

**Criterio de salida:** existe una línea de base versionada o un fixture estable que permite demostrar qué cambió y por qué. No se modificó todavía ningún output publicado.

## Entrega 1 — hotfix de siete datos objetivos

### 1. Costo real de financiamiento del Tesoro

- **ID:** `costo_financiamiento_tesoro`
- **Publicado:** 8,07% real anual, construido con TIREA 32,17%.
- **Hallazgo:** la LECAP comparable S13N6 publicó TIREA 28,32%.
- **Resultado esperado para el corte:** aproximadamente 4,92% real anual al combinar la tasa correcta con la expectativa REM usada por el indicador.
- **Acción:** corregir la selección/extracción de TIREA en `scripts/macro.py`, revisar la reconstrucción en `scripts/descargar_series.py` y reauditar todas las licitaciones históricas para evitar mezclar instrumentos, tasas o plazos.
- **Regresión mínima:** un fixture de la licitación debe seleccionar 28,32%, reproducir ~4,92% y rechazar 32,17% para ese instrumento.

Archivos candidatos: `scripts/macro.py`, `scripts/descargar_series.py`, `scripts/itcm.py`, `tests/test_macro_costo_financiamiento.py`, `tests/test_itcm.py`.

### 2. Transferencias federales reales

- **ID:** `iaf_transferencias`
- **Publicado:** +0,8% real interanual.
- **Contrastes externos:** IARAF +1,6%; Politikon +1,7% para el agregado anual comparable. El crecimiento nominal local, +43,1%, sí es consistente.
- **Causa probable:** deflación agregada o ponderación temporal incorrecta.
- **Acción:** reconstruir ambos períodos a precios de una base común, deflactando mes por mes; documentar serie de IPC, meses, jurisdicciones incluidas y fórmula de agregación.
- **Regresión mínima:** con un fixture mensual cerrado, el total real debe coincidir con la suma de flujos mensuales deflactados y no con el cociente entre totales nominales e IPC de punta.

Archivos candidatos: `scripts/politica.py`, `scripts/descargar_series.py`, `scripts/itcp.py`, `tests/test_politica_iaf_frescura.py`, `tests/test_itcp.py`.

### 3. Cobertura de vacantes judiciales

- **ID:** `cobertura_judicial`
- **Publicado:** 69,63%.
- **Detalle publicado:** 604 cargos cubiertos sobre 955, que equivale a 63,25%, no 69,63%.
- **Acción:** conciliar el corte y publicar siempre numerador, denominador y fecha de cada uno. Si 69,63% proviene de una actualización válida, el numerador debería rondar 665 y debe incorporarse su inventario verificable. Si no existe esa actualización, publicar 63,25%.
- **Regresión mínima:** `valor == 100 * numerador / denominador` dentro del redondeo; numerador y denominador no pueden provenir de cortes distintos.

No inventar el numerador faltante. Resolverlo contra el expediente y la fuente oficial antes de elegir 63,25% o 69,63%.

Archivos candidatos: `scripts/politica.py`, `scripts/itcp.py`, `tests/test_politica_judicial.py`.

### 4. Ratio DNU / leyes

- **ID:** `ratio_dnu`
- **Publicado:** 1,92, calculado a partir de 48 coincidencias textuales y 25 leyes.
- **Hallazgo:** sólo 37 registros están tipificados como DNU. Hubo 25 leyes publicadas y 22 sancionadas.
- **Decisión:** usar publicación en Boletín Oficial para ambos lados: `37 / 25 = 1,48`.
- **Acción:** filtrar por tipo jurídico, no por coincidencia textual; guardar inventarios de DNU y leyes; aplicar la misma ventana móvil de 365 días y la misma regla de fecha en card y serie.
- **Regresión mínima:** incluir falsos positivos con texto `DNU` que no sean decretos de necesidad y urgencia y comprobar que se excluyen.

Archivos candidatos: `scripts/politica.py`, `scripts/descargar_series.py`, `scripts/itcp.py`, `tests/test_politica_ratio_dnu.py`, `tests/test_descargar_series_ratio_dnu.py`, `tests/test_itcp.py`.

### 5. Confianza del consumidor UTDT

- **ID:** `icc_utdt`
- **Publicado:** 39,9 como total nacional.
- **Hallazgo:** 39,87 corresponde a CABA; el total nacional del mismo corte es 40,23.
- **Acción:** leer la columna nacional por nombre estable, no por posición; validar encabezado, región y período; reconstruir la historia nacional usada por ITVC.
- **Regresión mínima:** fixture con columnas Total/CABA/Interior que demuestre que el colector devuelve 40,23 y no 39,87 aunque cambie el orden de columnas.

Archivos candidatos: `scripts/vida_cotidiana/collectors/utdt_icc.py`, `scripts/vida_cotidiana/main.py`, `scripts/itvc.py`, `tests/test_itvc.py` y un test específico del colector.

### 6. Ventas en supermercados

- **ID:** `consumo_supermercados`
- **Publicado:** mayo de 2026 = 83,2, rotulado base 2004=100.
- **Hallazgo al corte:** junio de 2026 = 82,1; mayo revisado = 83,0; la base correcta es 2017=100.
- **Acción:** redescargar la serie oficial, tolerar revisiones, seleccionar el último período completo y corregir unidad/base en card, serie, documentación y UI. Reconstruir la historia sin empalmar bases incompatibles.
- **Regresión mínima:** fixture con mayo preliminar, mayo revisado y junio debe devolver junio 82,1, conservar mayo 83,0 y declarar base 2017=100.

Archivos candidatos: `scripts/vida_cotidiana/collectors/indec_supermercados.py`, `scripts/vida_cotidiana/main.py`, `scripts/itvc.py`, `scripts/publicar.py`, `tests/test_itvc.py`, `tests/test_panel_validacion.py`.

### 7. Concesiones viales

- **ID:** `concesiones_infraestructura`
- **Publicado:** 28,7% = 2.614 / 9.091 km y Etapa III tratada como no adjudicada.
- **Hallazgo:** la Resolución 1379/2026 adjudicó formalmente los ocho tramos de Etapa III, más de 3.900 km, antes del corte.
- **Resultado mínimo con denominador actual:** `(2.614 + 3.900) / 9.091 ≈ 71,65%`.
- **Acción:** incorporar los ocho tramos con sus kilómetros exactos y fecha jurídica del hito; comprobar que numerador y denominador usan la misma definición de red y que no hay solapamientos.
- **Regresión mínima:** fixture de la resolución con los ocho tramos; el indicador debe superar 71% y la suma debe ser trazable tramo por tramo.

Archivos candidatos: `scripts/gestion.py`, `scripts/itcg.py`, `tests/test_gestion.py`, `tests/test_itcg.py` y un test específico de concesiones.

### Criterio de salida de la Entrega 1

- Los siete colectores/fórmulas están corregidos desde su origen.
- Card y serie usan la misma lógica.
- Cada caso tiene test de regresión y fixture trazable.
- Se reconstruyó la historia sólo donde cambió la definición o una revisión oficial.
- Se presenta una tabla antes/después con impacto en ITCM, ITCP, ITVC, ITCG y agregado.
- No quedan literales de los valores erróneos usados como expectativas en tests, documentación activa o UI.

## Entrega 2 — protección inmediata del score

Suspender del score tres indicadores cuya cifra no es defendible como medida puntuable actual:

### 8. Postura pública de AEA y UIA

- **ID:** `apoyo_empresario`
- **Publicado:** −0,429 sobre siete textos codificados.
- **Hallazgo:** había 14 textos pendientes, incluidos apoyos y críticas sustantivos.
- **Acción inmediata:** `en_indice = false`; retirar semáforo, peso y aporte. Puede permanecer como card contextual si muestra tamaño del corpus, pendientes y reglas de codificación.
- **Condición para reingreso:** corpus cerrado y publicado; criterios previos; doble codificación o control de concordancia; inventario completo; prueba de que card y serie usan la misma cohorte.

### 9. Reestructuración de organismos

- **ID:** `reestructuracion_organismos`
- **Publicado:** 24,4% = 11 / 45.
- **Hallazgo:** 11 cuenta normas que afectan aproximadamente 18 entidades; 45 es una convención documental, no una meta oficial homogénea; el buscador omite cierres conocidos como ENOHSA.
- **Acción inmediata:** sacar del ITCG y conservar sólo un inventario contextual de entidades/actos, sin porcentaje de avance.
- **Condición para reingreso:** numerador y denominador deben tener la misma unidad —preferentemente entidades—, universo cerrado, regla para fusiones/absorciones/disoluciones y fuente reproducible.

### 10. Sentimiento digital

- **ID:** `sentimiento_digital`
- **Publicado:** 58,2.
- **Hallazgo:** la aritmética es estable, pero el volumen de búsquedas no identifica valencia ni bienestar. La validación externa es adversa: Ipsos post-base `r = -0,788`; ICC UTDT en 59 meses `r = -0,126` en niveles y `+0,082` en cambios; 34 de 42 ventanas móviles de 18 meses tuvieron el signo opuesto al esperado.
- **Acción inmediata:** retirar del ITVC. Conservar, si se desea, como `Atención de búsquedas en seis términos`, sin inversión, semáforo, peso ni interpretación afectiva.
- **Condición para reingreso:** términos o topics predeclarados, múltiples vintages congelados, encuesta objetivo definida y validación temporal fuera de muestra.

Archivos candidatos: `scripts/itcp.py`, `scripts/itcg.py`, `scripts/itvc.py`, `scripts/publicar.py`, `scripts/validacion_externa.py`, `config.py`, tests de cada índice, tests web y ADR nuevos.

### Regla de pesos

Al suspender un indicador, renormalizar proporcionalmente los restantes dentro de su dimensión. Agregar tests que comprueben:

- suma de pesos de la dimensión = 1;
- suma de pesos efectivos del cinturón = 1;
- el indicador suspendido no tiene score, semáforo, aporte ni peso efectivo;
- la card contextual declara inequívocamente que no integra el índice;
- la renormalización no cambia pesos de otras dimensiones.

### Criterio de salida de la Entrega 2

Los tres indicadores no afectan ningún score y el pipeline sigue publicando una explicación legible. Existe un ADR por decisión y una tabla antes/después que separa el cambio mecánico por renormalización de cualquier corrección de dato.

## Entrega 3 — universos y denominadores

### 11. Crédito privado real

- **ID:** `credito_privado`
- **Publicado:** +2,5% real con BCRA variable 26 expresada en pesos.
- **Problema:** incluye préstamos en dólares valuados en pesos; la variación mezcla crédito y efecto cambiario. Comparaciones homogéneas en pesos dan aproximadamente +0,5% o −1,4%, según serie y corte.
- **Acción:** definir un headline en pesos constantes con mismo universo y moneda en ambos extremos. Mostrar crédito en dólares y total equivalente como desgloses separados. Documentar qué se deflacta y qué tipo de cambio se usa sólo para cuadros auxiliares.
- **Aceptación:** una devaluación sin nuevos préstamos no puede aparecer como crecimiento real del crédito en pesos.

### 12. Trabajo independiente registrado

- **ID:** `trabajo_independiente`
- **Publicado:** 20,6% del empleo registrado.
- **Problema:** excluye monotributo social tanto del numerador como del denominador, aunque el rótulo promete todo el empleo registrado SIPA.
- **Acción recomendada:** incluir monotributo social y reconstruir la serie completa. Si la fuente no permite historia homogénea, usar un rótulo restringido que enumere las categorías incluidas.
- **Aceptación:** numerador, denominador, ficha, UI y fuente declaran las mismas categorías; la suma se reproduce desde SIPA.

### 13. Subocupación demandante

- **ID actual legado:** `pluriempleo`
- **Publicado:** 7,5% de los ocupados bajo un identificador asociado a pluriempleo.
- **Problema:** INDEC define subocupación demandante como porcentaje de la PEA; pluriempleo es otro fenómeno.
- **Acción:** migrar a un ID semántico, por ejemplo `subocupacion_demandante`; declarar `% de la PEA`; actualizar colector, series, pesos, metadatos, UI, informe y tests. Hacer una migración explícita, no duplicar ambas claves como si fueran indicadores diferentes.
- **Aceptación:** no queda `pluriempleo` como rótulo o definición activa del indicador; cualquier alias técnico temporal está documentado y no se publica.

### 14. Transferencias federales reales

Este caso ya se corrige numéricamente en la Entrega 1, pero aquí debe cerrarse el contrato metodológico del universo: transferencias automáticas/no automáticas incluidas, jurisdicciones, ventana anual, fecha de corte, IPC y regla de agregación. Reconstruir toda la historia homogénea y recalibrar bandas si la distribución cambia materialmente.

### 15. Cobertura judicial

Este caso ya se concilia en la Entrega 1, pero aquí debe quedar cerrado el universo: tipo de cargo, jurisdicción, vacantes, subrogancias, cargos habilitados y fecha de corte. Publicar el inventario o un manifiesto auditable que produzca numerador y denominador.

### Criterio de salida de la Entrega 3

- Cada indicador tiene una definición observable de una oración.
- Numerador, denominador, moneda, geografía, frecuencia y fecha de corte están explícitos.
- La serie histórica completa aplica la misma definición.
- Bandas y polaridad fueron reevaluadas con la serie reconstruida.
- Los tests cubren casos límite que antes producían mezcla de universos.

## Entrega 4 — rediseño de cinco constructos

Estos indicadores no deben seguir puntuando con su interpretación actual mientras se diseña el reemplazo.

### 16. Exceso de pesos sobre demanda

- **ID:** `idm`
- **Publicado:** 4,73 pp.
- **Qué mide realmente:** diferencia entre crecimiento real interanual de M3 privado y M2 privado transaccional.
- **Qué no mide:** oferta monetaria efectiva menos una demanda de dinero estimada.
- **Opción mínima:** renombrar `Brecha de crecimiento real M3–M2`, mantener fórmula y recalibrar su lectura sin hablar de exceso o demanda.
- **Opción sustantiva:** estimar una función de demanda de dinero con variables y validación explícitas. No implementar esta opción sin un diseño/ADR previo.

### 17. Dolarización dentro y fuera del sistema

- **ID:** `desequilibrio_monetario`
- **Publicado:** 50,86 puntos de tensión.
- **Problema:** la compra neta de divisas del sector privado no identifica dinero fuera del sistema. El BCRA estimó que cerca de 80% quedó depositado localmente.
- **Opción mínima:** renombrar el componente como presión compradora de divisas y eliminar toda afirmación `fuera del sistema`.
- **Opción sustantiva:** reemplazarlo por una medida observable de activos externos fuera del sistema, si existe una serie defendible.

### 18. Capitalización digital

- **ID:** `icip`
- **Publicado:** 8,36% interanual ponderado.
- **Problema:** pagos transfronterizos de informática y nube suelen ser consumo intermedio; no son por sí mismos formación bruta de capital.
- **Opción mínima:** renombrar como pagos/importaciones de servicios digitales, sin lenguaje de capitalización.
- **Opción sustantiva:** usar inversión en software, bases de datos y equipos TIC conforme a cuentas nacionales o una fuente equivalente.

### 19. Judicialización de la agenda

- **ID:** `judicializacion`
- **Publicado:** 1,57%, obtenido de 114 / 7.273 menciones de `medida cautelar` en sumarios SAIJ heterogéneos.
- **Problema:** el corpus no identifica causas contra el PEN ni políticas de su agenda.
- **Opción mínima:** card contextual `Densidad de menciones cautelares en sumarios SAIJ`, sin score ni inferencia sobre el Ejecutivo.
- **Opción sustantiva:** construir un universo de causas contra actos o políticas del Poder Ejecutivo, con unidad caso/expediente, deduplicación, estado procesal y corte temporal.

### 20. Sentimiento digital

Ya suspendido en la Entrega 2. El rediseño debe tratarlo como un proyecto nuevo y prospectivo. No reutilizar la correlación favorable de una canasta anterior para validar la canasta actual. La historia obtenida hoy por una consulta retroactiva no equivale a vintages históricos.

> La numeración llega a 20 porque tres indicadores aparecen en dos entregas: transferencias y cobertura primero corrigen su dato y luego cierran formalmente su universo; sentimiento digital primero sale del score y después queda sujeto a rediseño. Siguen siendo 17 indicadores únicos.

### Contrato mínimo para cualquier reingreso al score

Cada constructo rediseñado necesita:

1. Definición observable y fenómeno objetivo.
2. Unidad, universo, frecuencia, rezago, fuente y política de revisiones.
3. Fórmula, polaridad y tratamiento de faltantes.
4. Historia reproducible o, si no existe, período prospectivo explícito.
5. Benchmark externo y signo esperado predeclarados.
6. Validación fuera de muestra o contra períodos no usados para diseñar bandas.
7. Bandas calibradas sin optimizarlas para obtener un score deseado.
8. ADR, fixtures, tests de colector, tests de scoring y ficha pública.

### Criterio de salida de la Entrega 4

Ningún nombre interpreta más de lo que observan sus insumos. Los constructos no validados siguen fuera del score. Cada eventual reingreso cuenta con ADR y evidencia reproducible.

## Entrega 5 — regeneración y validación integral

Ejecutar sólo después de corregir código, contratos y tests de las entregas anteriores.

### Colectores afectados

Desde `projects/informe_coyuntura/`:

```bash
.venv/bin/python scripts/macro.py
.venv/bin/python scripts/politica.py
.venv/bin/python scripts/gestion.py
.venv/bin/python scripts/vida_cotidiana/main.py
.venv/bin/python scripts/vida_cotidiana.py
```

Los códigos de salida `1` y `2` indican uso parcial o total de caché. No tratarlos como actualización validada: identificar qué indicador quedó en caché y comprobar su fecha.

### Tests

Primero ejecutar los tests específicos de cada entrega. Al cierre:

```bash
.venv/bin/python -m pytest -n 6
```

No modificar la configuración del repositorio sólo para limitar workers; el límite `-n 6` es local.

### Informe y publicación

```bash
.venv/bin/python scripts/generar_informe.py
.venv/bin/python scripts/publicar.py
```

Luego, desde `projects/informe_coyuntura/web/`:

```bash
npm run build
```

### Controles obligatorios posteriores

1. Comparar los 69 indicadores antes/después, no sólo los 17 intervenidos.
2. Explicar cada movimiento de score y separar:
   - corrección de valor;
   - reconstrucción histórica;
   - recalibración de banda;
   - suspensión y renormalización de pesos.
3. Verificar que pesos de cada dimensión y cinturón suman 1 dentro de la tolerancia definida.
4. Verificar que ningún indicador suspendido aporta al índice.
5. Comprobar que card, serie, ficha, informe y web muestran el mismo valor, unidad, período y definición.
6. Revisar frescura, caché, `obtenido_en`, `fecha_dato` y fuente.
7. Confirmar que no reaparecieron IDs o rótulos legados, especialmente `pluriempleo`.
8. Hacer una segunda revisión de código de los cambios no triviales.
9. No borrar outputs versionados: en este proyecto son intencionales.

## Entregables esperados de Claude

Por cada entrega, devolver:

- lista de archivos modificados;
- explicación breve de la causa raíz y solución de cada indicador;
- fuentes/fixtures usados y fecha de corte;
- tests agregados o actualizados y su resultado;
- tabla de valores y scores antes/después;
- riesgos o decisiones todavía abiertas;
- ADR correspondientes a cambios de definición, scoring o arquitectura;
- confirmación de que no se tocó trabajo local ajeno.

Al final, producir un informe de remediación que clasifique cada uno de los 17 como:

- `corregido y puntuando`;
- `renombrado y puntuando con constructo acotado`;
- `contextual, fuera del score`;
- `rediseño pendiente, fuera del score`.

## Qué no hacer

- No editar `web/src/data/informe.json` a mano para forzar los valores esperados.
- No fijar números auditados como constantes productivas salvo que la fuente sea oficialmente manual y esté documentada.
- No mezclar corrección de dato con actualización a un período posterior sin reportarlas por separado.
- No conservar el score anterior ajustando pesos o bandas ad hoc.
- No llamar `confirmado` a un indicador sólo porque reproduce su propia fuente.
- No publicar como porcentaje una relación entre normas, entidades y metas documentales de unidades distintas.
- No usar volumen de búsquedas como sentimiento positivo/negativo sin validación.
- No declarar `fuera del sistema`, `capitalización`, `demanda de dinero` o `agenda del PEN` si los insumos no identifican esos fenómenos.
- No borrar artefactos versionados ni cambios locales del usuario.
- No hacer push a `main` durante la investigación o antes de mostrar el impacto completo.

## Definición de terminado

La remediación completa termina cuando:

1. Los siete errores objetivos se corrigen desde el origen y tienen regresiones.
2. Los universos y denominadores de los cinco casos correspondientes son homogéneos y públicos.
3. Los cinco constructos cuestionados tienen nombre defendible o están fuera del score.
4. Los indicadores suspendidos no aportan peso ni semáforo y la renormalización es automática y testeada.
5. Las historias y bandas fueron reconstruidas cuando cambió la definición.
6. Los 69 indicadores pasan el control de consistencia card/serie/ficha/web.
7. Los tests, generación del informe, publicación y build web finalizan correctamente.
8. Existe una tabla auditada antes/después que permite atribuir cada movimiento del índice.
9. Los cambios metodológicos están registrados en ADR y el resultado puede ser reproducido por un tercero.
