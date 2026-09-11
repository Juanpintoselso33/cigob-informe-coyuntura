# Evidencia de validación — 8 de septiembre de 2026

Registro cronológico de las etapas de la auditoría. Los conteos y límites de
cada corrida describen ese estado; el resultado más reciente está al final.
Las primeras ejecuciones por tramos fueron seguidas por suites completas.

## Controles

- Censo: 63 indicadores, 24 dimensiones, cero fallas de estructura y aritmética.
  La huella del snapshot final está en `coherencia.json`.
- Gate: sin bloqueos de integridad. Conserva avisos de dos componentes políticos
  en carry-forward y lectura editorial de septiembre pendiente.
- Astro: compilación de 81 páginas completada.
- Visual: portada y ficha de mora, seis capturas en total, páginas completas.
- `codex review`: sin defectos accionables introducidos; segunda ejecución
  cubrió 91 pruebas focalizadas. No certifica fuentes externas.
- Fuentes reparadas: hashes y procedencia en `evidencia-fuentes.json`.

## Suite Python

Se recorrieron los 3.263 casos recolectados en tramos, con un único proceso por
ejecución. **No hubo una única corrida completa ininterrumpida.**

1. Corrida general: 2.674 pasaron; una falla en el índice documental ADR y una
   interrupción del test de integración RON esperando una conexión de red.
2. Continuación desde ese test, más repetición de ADR: 2.230 pasaron, cuatro
   omitidos y una falla en la expectativa histórica de seguridad. Los números
   se solapan por la repetición de ADR y no deben sumarse.
3. Cierre de ambas fallas: 1.677 pasaron y cuatro omitidos. Se sincronizó el
   índice ADR y se sustituyó la premisa incorrecta de ausencia de diciembre
   de 2023 por el dato oficial recuperado (27,8%).
4. Verificación de las últimas explicaciones y salidas: 66 pasaron, cuatro
   omitidos; luego se repitieron los controles de publicación y gate tras
   quitar una referencia ADR del texto público que el gate no permite:
   **55 pasaron y cuatro omitidos**. La compilación final produjo 81 páginas
   y la huella del snapshot coincide con la del informe de coherencia.

Las omisiones pertenecen a casos condicionados del repositorio; no se presentan
como pruebas exitosas. La continuación usó las mismas URLs por transporte curl
con límite total de conexión, sin cambiar las fórmulas ni las respuestas de
las fuentes. Los tests unitarios siguieron usando sus mocks.

## Límites

La continuación corrigió el rezago de ICA: se incorporó julio con el cuadro
original vigente y se completó su contraste histórico. Cinco pruebas nuevas
verifican descubrimiento, extracción, persistencia, ventanas y composición;
la verificación posterior terminó con 65 pruebas aprobadas y cuatro omitidas.
La web volvió a compilar 81 páginas y el gate no detectó bloqueos de integridad.

Se corrigió la confusión entre cero desafíos y tasa sin denominador (ADR-0276).
Pasaron 185 pruebas de bloqueo, cohesión, publicación y gate. Luego pasaron
1.673 pruebas del contrato nuevo y del formato ADR, incluidas la renormalización
efectiva, la publicación sin puntaje y la actualización conjunta ante fallos de
cobertura. Una expectativa inicial no contemplaba el redondeo a cuatro decimales
de los pesos efectivos; se corrigió el test y la repetición completa pasó.
La segunda revisión no encontró regresiones concretas, ejecutó otras 126 pruebas
(cuatro omitidas), gate y build. No verificó las fuentes en vivo.
InfoLeg/Senado actualizó el registro, pero Diputados no permitió descubrir las
actas actuales: la consulta directa terminó en error de conexión sin HTTP.
Siguen en caché ambos resultados hasta completar esa comprobación.
Los controles tampoco
acreditan validez causal, representatividad de
la muestra de prensa o capacidad electoral predictiva. Los documentos Word
históricos se conservaron; se actualizaron las fichas web y Markdown vigentes.

## Continuación: privatizaciones y contraste de consumo

Se incorporó la transición de Belgrano Cargas a etapa 3 desde agosto (ME
1350/2026), sin modificar los meses anteriores. Se corrigieron mecanismo y
prórroga de AySA y se explicitó la licitación desierta de Intercargo. El avance
sube de 51,4 a 55,6 y el ITCG de 80,5 a 80,8; tensión redondeada 1,9.
Se regeneraron tarjeta, serie, informe, validación externa, sensibilidad,
snapshot, fichas y censo. Pasaron 61 pruebas y cuatro quedaron omitidas; el gate
mantiene únicamente los avisos políticos y editoriales ya documentados.

El contraste CAME cubre enero-agosto, conserva las diferencias de ventana y no
convierte una coincidencia general en validación estadística. La matriz
`cobertura-fuentes.csv` evita confundir comprobación de código con verificación
individual de actualidad de las 63 fuentes.

## Continuación: revisión completa de avisos y errores de cobertura

Se leyeron las 23 normas pendientes restantes, se archivaron las 27 revisiones
acumuladas y se corrigió el detector (ADR-0277). Once pruebas focalizadas
pasaron. La revisión adicional de código ejecutó 138 pruebas (cuatro omitidas)
y encontró un error de cobertura dentro del clasificador político: una excepción
interna quedaba oculta y podía habilitar «sin universo». Se corrigió propagando
el fallo, conservando el watermark y rechazando ausencia con triage pendiente;
el recorrido de cohesión también informa si omitió PDFs fallidos.

Pasaron 161 pruebas de integración y después 1.683 pruebas del contrato político
y formato documental. Los controles nuevos cubren errores internos y recorrido
incompleto; no dependen sólo de simular un fallo del colector externo.
La nueva desactualización SSS está documentada como pendiente, sin modificar
todavía tarjeta ni serie.

### SSS: archivos referenciados y reconstrucción histórica

- Cinco pruebas específicas pasaron; `codex review --uncommitted` terminó sin defectos accionables en el estado final. Su build Astro generó 81 páginas.
- Descarga real de los archivos RNAS/RNEMP: junio 2.754.461 / 8.332.458 = 33,1%. Se preserva la salvedad del enlace RNEMP inactivo.
- Tarjeta, serie, informe, validación externa, publicación, sensibilidad, manuales, fichas y censo regenerados. Censo: 63 componentes activos, 24 dimensiones, cero errores aritméticos.
- Comprobación aislada con el motor ITCG: quitar únicamente salud reproduce abril 72,1, mayo 78,0 y junio 79,8; incorporarla da 71,2, 77,1 y 78,9. La diferencia histórica corresponde a cobertura, sin modificar ponderaciones.

### Alcance de las series laborales (ADR-0279)

Se reprodujeron diez tarjetas sociales con consultas reales. Los 28 tests dirigidos de trabajo independiente, universos y actualización de fichas pasan. Una primera ejecución detectó tres entradas faltantes de historial metodológico (ADR-0276/0277); fueron incorporadas y se repitió la comprobación. Build Astro: 81 páginas, finalizado correctamente. No se cambiaron fórmulas ni valores.

### Fecha de la brecha cambiaria (ADR-0280)

17 tests dirigidos pasaron. Consulta real: brecha 5,35%, CCL 1588,70 y mayorista 1508, con marcas temporales. ITCG 80,5; tensión 1,9. Informe, snapshot, sensibilidad, manuales y fichas regenerados. Censo: 63 indicadores, 24 dimensiones, sin fallas aritméticas. Gate correcto con avisos previamente documentados. Segunda revisión finalizada: detectó dos encabezados ADR no canónicos, corregidos en la continuación. Ver comprobaciones siguientes.

### Cierre de revisión de cotizaciones y ADR

La revisión detectó encabezados no admitidos en ADR-0279/0280; se movieron a subsecciones de Más información. Validación de ADR, búsqueda, fecha de cotización y ficha: **1706 passed**. Tres tests adicionales que habían fallado por DNS en el entorno de revisión se repitieron con HTTP real mediante curl: **3 passed** (dotación de fuerzas, relación de puntajes IPI/EMAE y continuidad mensual IPI). Esto cierra esos fallos concretos; no se presenta como una corrida integral nueva de toda la suite.

### Suite integral posterior a ADR-0280

Ejecución serial de `pytest tests -q --tb=short` con transporte GET curl real acotado: **3338 passed, 4 skipped, 5 warnings en 42,17 s**. Las advertencias son deprecaciones SWIG. Los cuatro omitidos no son validaciones superadas. Registro local: `/tmp/cigob-suite-integral.log`. No se actualizaron datos durante esta ejecución.

### Descomposición y cobertura temporal del ITCP

Se recalcularon enero-agosto con el motor vigente y se verificó la suma de aportes contra cada índice publicado. La comparación sobre componentes comunes cambia el signo de agosto (+0,8 a −0,9) y modifica junio (+1,8 a +4,0). Historia/dimensiones: 16 passed y 4 skipped. Los cuatro omitidos comparan el último mes reconstruido con la tarjeta de otro período y se omiten expresamente por ese desajuste temporal; no son comprobaciones aprobadas. Build Astro: 81 páginas.

### Tasa de resolución judicial y cotejos restantes (ADR-0281)

Anuario CSJN 2025 corroborado en la fuente primaria. Nombre y límites corregidos; fórmula conservada. ADR, historial de fichas y fichas regeneradas: **1701 passed**. Build Astro: **81 páginas**. Los seis indicadores que todavía carecían de un cotejo individual tienen ahora una consulta registrada, pero Diputados sigue incompleto y la réplica no certifica por sí sola vigencia. ACLED actualizó una semana parcial de agosto; las tarjetas mensuales siguen en julio.

### Actualización tributaria (ADR-0282/0283)

Diez pruebas iniciales de apertura/ICA y 55 dirigidas de COMARB/apertura pasaron. La corrida integral posterior terminó con **3365 passed, 4 skipped, 5 warnings en 42,20 s**, en ejecución serial con GET real mediante curl. Build Astro: **81 páginas**. Los cuatro omitidos conservan el alcance temporal explicado arriba.

`codex review --uncommitted` identificó el índice ADR todavía no regenerado y la discrepancia transitoria entre informe y snapshot. La regeneración completa posterior y la suite integral verificaron sus contratos. El proceso inicial de validación externa quedó esperando una conexión IPv6 en estado SYN_SENT, confirmado con `sample` y `lsof`; se detuvo ese proceso propio y se completó mediante IPv4 con las mismas consultas. No se sustituyeron respuestas por datos simulados.

Informe, validación externa, snapshot, sensibilidad, censo, manuales, fichas y contraste mensual se recalcularon. Snapshot `c69c2d0e17da151437e812c3b85ced8c557048eb87985810ac233b1b205bf98e`: 63 indicadores y 24 dimensiones, sin fallas estructurales o aritméticas. Portada: ITCM 67,5 e ITCG 79,1. La auditoría de fuentes y validez externa permanece abierta en los casos que la matriz no marca comprobados.

### Procedencia bicameral y cierre de EMAE (ADR-0284)

El valor utilizado publicado muestra Diputados con última acta 24-jun y dato conservado en caché, y Senado con última acta 27-ago. Se conservaron fórmulas y valores. Se corrigió además la descripción de recálculo/conservación en la ficha de alineamiento. La primera prueba detectó una entrada de historial faltante, incorporada antes de regenerar: **1757 passed** en la comprobación dirigida posterior. Build Astro: **81 páginas**.

Censo actualizado sin fallas; SHA del snapshot: `50875581c1bf35b7a587ea490112c700dd02da9fcd0225ae5bab6169f29ca1cf`. Se cerraron dos cotejos más (EMAE y difusión) con informe original y calendario: la matriz distingue ahora 21 comprobaciones, 37 reproducciones aún sin cierre, 3 consultas incompletas, una cartera parcial y salud con salvedad.

### Cierre de tres cotejos laborales

SIPA: portales principal y específico + planilla mayo, hojas A.1 y T.2.2, concilian empleo privado y participación independiente. SRT: catálogo y selector del boletín habilitan hasta mayo y confirman la serie utilizada. No se modifican datos ni cálculos: se cierra su vigencia documentada. Matriz: 24 comprobaciones, 34 reproducciones pendientes de cierre, tres consultas incompletas, una cartera parcial y una comprobación de salud con salvedad.

### Litigiosidad y ventanas completas (ADR-0285)

La tarjeta y la reconstrucción comparten el cálculo con 24 meses consecutivos: rechazan huecos, valores no finitos/negativos y denominador nulo; admiten cero observado. Consulta real: 127.363 / 124.767 juicios = +2,1%, mayo 2026, igual en ambas vistas. El portal SRT confirma el último período. Se corrigieron interpretaciones que atribuían directamente efectos del FAL a otra clase de juicios, y se registró la mejora metodológica aparte.

Pruebas dirigidas: **1748 passed**; build: **81 páginas**. La segunda revisión no encontró defectos accionables. Registró tres fallos DNS, repetidos con IPv4 real: **3 passed**. Para aclarar sus 18 omisiones se ejecutó la suite completa con resumen de motivos: **3386 passed, 4 skipped, 5 warnings en 43,82 s**. Las cuatro omisiones corresponden a la comparación entre el último mes reconstruido y la tarjeta de septiembre, períodos distintos. No se cuentan como pruebas aprobadas.

También se cerró IPC alimentos con el cuadro original de julio y calendario. Cobertura al final de esta etapa: 26 comprobaciones, 32 reproducciones pendientes de cierre, tres consultas incompletas, una cartera parcial y salud con salvedad. Las 63 filas tienen documentos de evidencia existentes.

### EPH: vigencia y universo

El contenido público cargado por el portal INDEC enlaza el informe del primer trimestre y anuncia el siguiente para el 17-sep. PDF y API coinciden en 37,9% de asalariados sin descuento y 7,5% de subocupación demandante sobre PEA. No se equiparan con informalidad total ni subocupación total. Se corrigió únicamente la descripción de redistribución ante faltantes en la ficha de informalidad y se regeneraron fichas. **16 pruebas documentales aprobadas** (`/tmp/cigob-fichas-eph.log`); diff sin errores de whitespace. No se modificaron cifras ni motores, por lo que no se repitió la suite completa.

Cobertura después de EPH: 28 comprobaciones, 30 reproducciones pendientes de cierre, tres consultas incompletas, una cartera parcial y salud con salvedad. El contraste con prensa queda en `contraste-empleo-eph.md` y las fuentes originales, períodos y hashes en `cotejo-eph-publicacion.json`.

### Salario y canasta: mes común y alcance

RIPTE junio y CBT junio conciliados con HTML oficial y cuadro 4 del PDF vigente de canastas julio. Cociente 3,8656 sin cambio numérico. Se añadió a la ficha que remuneración imponible con tope no equivale a ingreso de bolsillo y que la canasta corresponde a adulto equivalente GBA. Se regeneraron fichas; **16 controles documentales aprobados** (`/tmp/cigob-fichas-cbt.log`). Cobertura: 29 comprobaciones y 29 reproducciones pendientes de cierre; los otros cinco casos conservan sus salvedades.

### Reservas: hallazgo sobre identidad y alcance (ADR-0286)

PDF SDDS julio: la aritmética da 11.962,12 M USD, pero el tramo II.1 >3 meses–1 año no identifica BOPREAL. Corregidos fórmula y texto públicos; reservas permanece pendiente de cierre, incluyendo conciliación por instrumento y diferencia de fórmula en `config_fallback`. Evidencia: `cotejo-sdds-reservas.json`.

Publicación y fichas: **52 passed**. Primer control detectó ausencia de la entrada ADR en el historial de la ficha; se añadió y la repetición pasó. Build: **81 páginas**. Censo: 63 indicadores, 24 dimensiones, sin fallas aritméticas; SHA del snapshot `f6fcea99509b8cdf05794f5dc071a723f012b060717e25bc88eccf9c03f9191a`. Segunda revisión iniciada y aún en curso al registrar esta etapa: `/tmp/cigob-review-0286.log`, sesión 31556; no se cuenta como aprobada.

### Reservas: resultado completo o caché (ADR-0287)

Revisión 0286 finalizada: detectó secciones no canónicas en el ADR, corregidas. Retirado respaldo con otra definición, parser exige columna del tramo e historia exige Tesoro observado. Nueve regresiones de reservas aprobadas; con contratos documentales, **1746 passed**. Balance real: 26 meses publicados con Tesoro, julio 11.962 M USD. Portal NEDD BCRA mantiene julio y anuncia agosto para 23-sep: https://www.bcra.gob.ar/normas-especiales-para-la-divulgacion-de-datos-fmi/.

Suite completa con consultas reales por IPv4: **3403 passed, 4 skipped, 5 warnings en 61,49 s** (`/tmp/cigob-suite-0287.log`). Mismos cuatro controles omitidos por meses distintos, no aprobados ficticiamente. Build final **81 páginas** (`/tmp/cigob-build-0287.log`). Revisión 0287 finalizada sin defectos accionables (`/tmp/cigob-review-0287.log`); sus tres errores DNS de pruebas de red quedan cubiertos por la suite completa real.

### Desequilibrio monetario: cinco insumos conciliados

Anexo oficial vigente enlazado por el portal BCRA: suma independiente del concepto 03 por sector y exclusión del público, último mes julio. Cuatro variables monetarias al 31-jul: A 32,9155%, B 3.152,0174 M USD y tensión 58,2702, iguales a la tarjeta redondeada. Los comentarios heredados que aún atribuían fuga fueron corregidos de acuerdo con ADR-0252, sin modificar cálculos ni nombres internos. **27 pruebas aprobadas** (`/tmp/cigob-tests-desequilibrio-auditoria.log`). Evidencia: `cotejo-desequilibrio-insumos.json`. Cobertura: 30 comprobaciones, 28 reproducciones pendientes de cierre y los cinco casos con salvedades ya declarados.

### Fiscal: originales y base caja

Los doce importes del resultado primario, agosto 2025–julio 2026, coinciden con los XLSX de Hacienda; diferencias inferiores a 10⁻⁸ millones por representación decimal. Salarios y otros gastos de funcionamiento concilian con IMIG julio de 2026 y XLS julio de 2023. La fuente declara base caja: se corrigieron dos detalles de gestión que decían devengados (incluida masa salarial, fuera del índice), la ficha de funcionamiento y la explicación del denominador del resultado primario. No se cambiaron cifras, pesos ni fechas.

**43 controles aprobados** (`/tmp/cigob-tests-base-caja.log`). Censo actualizado: 63 indicadores y 24 dimensiones, sin fallas aritméticas. SHA del snapshot `4be082141f1cd478ca6c6cc555d836cde956cea3183db7876e0c8b493749d66b`. Cobertura: 32 comprobaciones y 26 reproducciones pendientes de cierre; se mantienen las otras cinco salvedades. Fuente y cálculos: `cotejo-fiscal-originales.json`.

### Financiamiento de agosto — ADR-0288

Resultados oficiales y llamados concilian cuatro instrumentos fijos en pesos,
liquidados el 14 y el 31 de agosto. Tarjeta e historia: 7,25% real anual,
nominal ponderado 29,77% y REM 21,0%. Se conservan 31 meses desde diciembre
de 2023. La caché de planillas distingue las ventanas de dos y cuatro años.

La primera suite detectó dos fallas: un control textual tomó una negación
partida en dos líneas como afirmación, y la actualización local del caché omitió
anotar los campos de aporte de la tarjeta. Se corrigieron ambos antes de repetir
la suite. El censo regenerado conserva 63 indicadores y 24 dimensiones;
SHA `cd9cf7af924ebd94caf6f96b74cb3690775936de38a85708e6c2a374754c3e27`.
Cobertura: 33 comprobaciones y 25 reproducciones pendientes de cierre, más
las cinco salvedades previamente declaradas.

Suite posterior a la integración de agosto: **3417 passed, 4 skipped, 5 warnings**
en 42,54 s (`/tmp/cigob-suite-0288b.log`); build de 81 páginas. La revisión
0288 detectó un caso adicional en Diputados: PDF descargado sin fecha interpretable
se confundía con 404. Se corrige para marcar recorrido incompleto y evitar tanto
el universo vacío falso como la congelación de un año incompleto. **134 pruebas
legislativas aprobadas**, con regresiones de PDF ilegible y respuesta nula.

### Sensibilidad y aportes coherentes — ADR-0289/0290

El informe separado omitía transformaciones del REM y exposición al error común
del IPC. Con REM anual 21%, una simulación sin ruido repuntuaba 10 en lugar de
83. El informe corregido da ITCM 67,0, rango combinado 65,2–68,7; la web
65,3–68,6, con otra muestra Monte Carlo. El valor central no cambia. Se conserva
la fecha real del snapshot y el número efectivo de corridas. Nueve controles de
sensibilidad aprobados. Una suite posterior señaló la entrada faltante en la
ficha del REM; se incorporó y regeneró antes de repetir la validación.

El generador ahora anota los aportes desde el índice recién calculado. Ocho
controles de recálculo aprobados, incluyendo tarjetas con pertenencia, puntaje
y peso deliberadamente obsoletos. El censo exige también que esos metadatos
coincidan con los componentes efectivos.

Suite integral: **3436 passed, 4 skipped, 5 warnings en 42,96 s**
(`/tmp/cigob-suite-0290.log`). Los cuatro omitidos comparan historia de julio/agosto
con tarjeta de septiembre. Build de 81 páginas (`/tmp/cigob-build-0290.log`).
Censo sin fallas: SHA `258441af1f7b32bfab44a5477fdd979d84768c122ee24b91fe25034dc3acc62d`.
El gate conserva los avisos de datos legislativos arrastrados y lectura editorial
de septiembre sin firma; no se los presenta como observaciones actuales verificadas.

La segunda revisión 0290 terminó sin regresiones concretas atribuibles a los
cambios. Sus tres fallas DNS quedan cubiertas por la suite real anterior
(`3436 passed`); sus omisiones adicionales no se cuentan como verificaciones.
Registro: `/tmp/cigob-review-0290.log`.

### Apertura comercial: conciliación ARCA original

Planilla anual 2026 enlazada por el portal ARCA: derechos de exportación,
importación y estadística coinciden con las dos series de API. A3500 de julio
1487,0038 ARS/USD; intercambio ICA original 15592,5354 M USD; cociente 7,6243%,
coincidente con la tarjeta 7,62. Se evita redondear el intercambio antes de dividir.
ARCA llega a agosto e ICA a julio: último mes común julio. Sin cambios de datos
ni método. Evidencia `cotejo-apertura-arca-original.json`. Cobertura: 34
comprobaciones y 24 reproducciones pendientes de cierre, más cinco salvedades.

### Recaudación: original DGI y réplica independiente

El cuadro visual de la página 12 del PDF ARCA julio muestra subtotal impositivo
12.640.578 M pesos, conciliado con API 12.640.577,9556 y corroborado en el informe
IDEP. La reconstrucción independiente del ajuste estacional sobre 55 meses
reproduce 102,1. Se conservan los insumos, factores y hashes en
`cotejo-recaudacion-original.json`. DGI y COMARB llegan a agosto; IPC limita julio.
La ficha explicita los efectos de vencimientos y reasignaciones de saldos
señalados por el original. Fichas regeneradas; nueve controles documentales
aprobados. Cobertura: 35 comprobaciones, 23 reproducciones pendientes de cierre
y cinco salvedades. Sin cambios del índice ni sus series.

### Alquiler original — ADR-0291

Se reemplaza la API discrepante por niveles originales INDEC de GBA, con
lector compartido para tarjeta e historia. Se valida continuidad mensual,
identidad de región y concepto, niveles positivos y meses cerrados. Doce
regresiones del lector. Prueba real: 3,9242% mensual y componente 50,3189;
publicados 3,92 y 50,3. ITCIS de portada 93,3, tensión 6,3 y global 3,7.

La primera suite terminó con 3453 aprobados y un desfase de series por haber
publicado antes de recalcular la validación externa. Tras sincronizar ambos
artefactos, los 36 controles afectados aprobaron, con cuatro omisiones por
períodos distintos. SHA del snapshot sincronizado:
`4ed94f8eb15fc8c6e3dbfc85bdd92662e54307a349635773af29314c94e1c472`.
Las tablas de Di Tella y CAME y el contraste político usan la nueva historia.
La revisión no se interpreta como deterioro económico nuevo. Cobertura:
36 comprobaciones, 22 reproducciones pendientes de cierre y cinco salvedades.

Suite final sincronizada: **3454 passed, 4 skipped, 5 warnings en 45,19 s**
(`/tmp/cigob-suite-0291-final.log`). Manuales regenerados con ADR-0291.

### Desregulación — ADR-0292

La edición de agosto revisa julio de 16.771 a 16.848 artículos; el incremento
de agosto es 267, con total 17.115. Se verificaron las etiquetas originales
y se corrigieron colector, historial, tarjeta y ficha. Trece pruebas específicas
aprobadas. El censo de 63 indicadores y 24 dimensiones no presenta fallas.
El build produce 81 páginas. Snapshot sincronizado:
`17afdcb108a5a8ef8bde66e6276601ec24e568cf34cf057197eb19eed0e5721d`.
La regeneración inicial del manual detectó metadatos faltantes en el nuevo
ADR; se completaron y los manuales y fichas se regeneraron correctamente.
Cobertura: 37 comprobaciones, 21 reproducciones y cinco salvedades.

La revisión independiente de ADR-0291 terminó sin hallazgos accionables;
su ejecución de tests informó tres fallos de consultas por DNS. La suite
sincronizada de la auditoría anterior, con el transporte de red documentado,
había aprobado 3454 pruebas. La suite de ADR-0292 se registra por separado.

Pendiente concreto detectado en IAI: la tarjeta prevé activar patentamientos
al acumular trece meses, tomando el último mes del store, mientras el historial
conserva siempre ISAC/BK 65/35. El store actual tiene sólo mayo-julio de 2026,
por lo que aún no afecta el valor publicado. Corresponde unificar fórmula y
mes de referencia antes de cerrar su revisión; no es una mejora opcional.

### IAI y cortes — ADR-0293/0294

La discrepancia futura del IAI se corrigió compartiendo la composición por
mes entre tarjeta e historia y excluyendo patentamientos de otros meses.
Tres pruebas específicas aprobadas. Los valores presentes no cambian.

La suite de ADR-0292 se interrumpió con SIGINT después de 246,9 segundos
en una conexión externa: 2845 aprobados y un fallo documental por la entrada
faltante de ADR-0292 en el historial de cambios de su ficha. Se agregó esa
entrada y la de ADR-0293. La repetición con curl terminó con 3471 aprobados,
cuatro omisiones y cinco advertencias en 44,98 segundos.

ADR-0294 explicita base estimada y detector no verificable de cortes. La
prueba HTTP 200 con cuenta suspendida verifica que no se confunda una página
sin informes con ausencia de nuevas publicaciones. La tarjeta y los manuales
y fichas se regeneraron. Snapshot final de esta pasada:
`2c080470278c3208e9efb014ee2d8739b768572d0d64bc4535d66992edf9e4c3`.
El censo no registra fallas de estructura ni aritmética; los índices conservan
67,0 / 69,9 / 79,1 / 93,3 y tensión global 3,7.

Suite: **3479 aprobados, 4 omitidos, 5 advertencias en 38,97 s**
(`/tmp/cigob-suite-0294.log`). Las cuatro omisiones corresponden a comparar
meses distintos de historia y portada. Build: **81 páginas**, 1,52 s.
Revisión independiente de esta pasada iniciada en `/tmp/cigob-review-0294.log`.

Próximo pendiente concreto: la planilla original de jornadas laborales
confirma 4.760.195 para junio de 2025–mayo de 2026. El colector suma doce
filas sin exigir continuidad del calendario ni unicidad; debe rechazar
duplicados o huecos antes de cerrar ese componente. El valor actual coincide.

### Calendario y contraste de jornadas — ADR-0295

Se cerró el pendiente anterior: 19 pruebas del calendario y lector aprobaron.
La ejecución contra la planilla oficial devuelve 234 puntos y termina en
mayo de 2026 con 4.760.195. Se actualizaron ficha, manual e índice de ADR.
La cobertura pasa a 38 comprobaciones, 19 reproducciones y seis salvedades.
El contraste de enero–mayo detecta +15,2% de jornadas pese al puntaje 100:
se declara el límite de lectura y se anota la sensibilidad como mejora opcional.

La revisión independiente de ADR-0294 terminó sin hallazgos accionables.
Su build pasó; reportó 3462 pruebas aprobadas, 18 omisiones y tres fallos de
acceso a fuentes externas. La suite de esta auditoría con transporte curl
había aprobado 3479 pruebas. El control posterior de ADR-0295 fue específico.

### TDPS y cierre de reservas — ADR-0296

Se preservaron filtros y partidas originales de las consultas POST 2026 y
2023, sin credenciales. Los importes corroboran 100% y base 98,312165%.
Se corrigieron unidad, detalle, descripción, fórmula, ficha y unidad de la
serie: se mide clasificación del devengado, no pago efectivo ni intermediación
observada. Los índices no cambian. Snapshot:
`03bbeebac8ae946078bf07e4cf03aec1029110f861df957089b5c26802c3230d`.

Suite integrada: **3497 aprobados, 4 omitidos, 5 advertencias en 41,29 s**
(`/tmp/cigob-suite-0296.log`). Build: **81 páginas**, 1,78 s. Censo sin fallas.
Revisión independiente iniciada en `/tmp/cigob-review-0296.log`.

La página SDDS inglesa enlaza julio y anuncia agosto para el 23 de septiembre;
su PDF coincide con el cotejo español de insumos. Se cierra vigencia y
reproducción de reservas como estimación CIGOB, conservando los límites de
constructo de ADR-0286/0287. Cobertura: 40 comprobaciones, 17 reproducciones,
una revisión parcial, tres consultas incompletas y dos comprobaciones con salvedad.

### Cierre de IAF y notas del Consejo

La revisión independiente de ADR-0296 terminó sin hallazgos accionables.
Su build pasó y registró 3480 pruebas aprobadas, 18 omisiones y tres fallos
de acceso a fuentes externas; la suite con curl de esta auditoría había
aprobado las 3497 indicadas arriba.

IAF: los 24 flujos originales y el IPC reproducen +1,6365% real en 2025;
el PDF OPC confirma +1,6%. Se corrigió la descripción del deflactor implícito,
sin cambiar el cálculo. Los generadores de ADR, manuales y fichas terminaron
correctamente; el control de coherencia de fichas aprobó 9 pruebas.

Consejo: revisión manual de las 20 notas del intervalo consultado, 13 incluidas
en la ventana actual. Corrección documental de fecha editorial, mes abierto
y afirmación antigua sobre inactividad de Disciplina. No cambian cifras.
La cobertura queda en 42 comprobaciones, 15 reproducciones, una revisión parcial,
tres consultas incompletas y dos comprobaciones con salvedad.

### Hallazgo posterior: cobertura judicial todavía incorrecta

El cotejo del catálogo contra normas originales confirmó que la réplica de
69,63% no prueba vigencia: archivos de movimientos al 13 de julio omiten
nombramientos posteriores. Diez designaciones de junio corresponden a
titulares ya presentes en el padrón; deben conciliarse sus cargos de origen.
Se conserva la evidencia y se inicia la lectura de 70 decretos de Justicia
del período posterior. No se recalcularon índices con una lista parcial.
Cobertura actual: 42 comprobaciones, 14 reproducciones, una corrección pendiente,
una revisión parcial, tres consultas incompletas y dos comprobaciones con salvedad.


### Conciliación judicial integrada — ADR-0297 y ADR-0298

Motor y consulta oficial coinciden: ancla original 610, corregida 609;
+103 altas netas, −6 renuncias y −1 otra baja = 705/955 (73,82%). La historia
se recalculó con las mismas reglas y el corte máximo revisado. Permanecen
explícitos el caso Fraga y los límites de juras, habilitaciones y bajas.
No se certifica el stock físico ni se presenta como cierre integral.

La primera suite detectó la base IPC omitida en la ficha IAF y un timeout de
gas que dejaba incompleto el panel. Se restituyó la base diciembre de 2016;
el reintento recuperó la fuente y se recalculó y sincronizó el panel completo.
La corrida final tuvo **3527 aprobados, 4 omitidos y 5 advertencias en 45,87 s**
(`/tmp/cigob-suite-0298-final.log`). Las omisiones corresponden a meses distintos
entre historia y tarjeta. El gate pasó con los avisos conocidos de carry-forward
y lectura editorial aún sin firma. Build: **81 páginas en 1,51 s**.

`codex review --uncommitted` terminó sin defectos nuevos; su propia suite tuvo
3510 aprobados, 18 omitidos y tres fallos de acceso a red. El build de esa
revisión también pasó. Las últimas modificaciones posteriores fueron de texto
y procedencia; la suite completa y build finales cubren ese estado.

Snapshot: `9a4b4303f34a09d5b7e7f94c58ad24117ebf77b7ecb64459fe6cb3b06e6945db`. 63 indicadores, 24 dimensiones,
sin fallas estructurales o aritméticas. Índices 67,0 / 70,7 / 79,1 / 93,3;
tensión global 3,6. ITCP histórico junio/julio/agosto: 67,6/68,0/68,8;
correlación con EPU −0,312 en niveles y −0,279 en cambios. El control de
componentes comunes de junio da +3,8 frente a +1,5 en la serie completa.

Nuevo pendiente confirmado durante la corrida: IPI e ISAC julio ya publicados;
las rutas API todavía en junio. Matriz: 42 comprobados, 11 reproducciones,
4 correcciones con pendiente (judicial integrada, IPI, IAI, ISAC social),
3 consultas incompletas, 1 parcial y 2 comprobados con salvedad.


### Industria y construcción originales — ADR-0299

Las planillas originales sustituyen las rutas API atrasadas para IPI e ISAC,
en variantes original y desestacionalizada. El lector descubre el año vigente,
valida identidad y calendario, conserva niveles precisos y lo comparten macro,
historia y colector social. Julio: IPI promedio i.a. 3 meses −2,82%; ISAC social
140,2 (nivel preciso 140,16334796). La revisión del ISAC mueve IAI junio de
−0,18 a −0,06%; bienes de capital julio continúa pendiente de integración.
También se actualizó ICIP informativo, fuera del índice, por su uso de IPI.

Una actualización parcial del crudo conserva su hora propia de obtención:
no se reemplaza por la hora de la madrugada del resto del archivo. Las fichas
corrigen fuente y rezago. Hay 19 pruebas focalizadas aprobadas, incluyendo
13 del lector/rutas/procedencia y seis del sello temporal existente.

Suite completa: **3546 aprobados, 4 omitidos, 5 advertencias en 42,65 s**
(`/tmp/cigob-suite-0299.log`). Las omisiones comparan meses diferentes entre
historia y tarjeta. Build: **81 páginas en 1,43 s**. Gate aprobado con avisos
conocidos de dos indicadores políticos en caché y lectura editorial sin firma.
`codex review --uncommitted` no encontró defectos nuevos; su build pasó y sus
tres fallos de pytest fueron resolución DNS, con 3529 aprobados y 18 omitidos.

Snapshot `8aeca751e1022e7791a99c1a880b49110ef8f8b13a6f251ec3a5772e6fe2d801`: 63 indicadores y 24 dimensiones,
sin fallas de estructura o aritmética. Índices actuales: 66,9 / 70,7 / 79,1 /
93,1; tensión global 3,7. La historia y las lecturas con CAME/Di Tella se
sincronizaron: ITCM julio 63,7 e ITCIS julio/agosto 93,7/93,3.
El ITCM julio sin IPI reproduce el 69,1 previo; al incorporarlo aparece la
dimensión actividad con un solo componente. Es revisión de cobertura entre
versiones, no un deterioro mensual de 5,4 puntos.

Contraste: ITCM/Líder r=0,713 en niveles y 0,391 en cambios; ITCIS/factor
físico 0,103 y 0,344, con incremento R² 0,056. No equivalen a validación causal.
Matriz de fuentes: 44 comprobados, 11 reproducciones, 2 correcciones pendientes
(judicial y bienes de capital del IAI), 3 consultas incompletas, 1 parcial y
2 comprobados con salvedad. El original de bienes de capital ya quedó
cotejado en dos cuadros y en la serie de 19 meses: próximo paso concreto,
integrarlo sin perder los meses históricos anteriores.

### Inversión original e historia macro completa — ADR-0300/0301

IAI julio −5,66% cotejado con originales INDEC y 96 puntos históricos conservados. La historia macro omitía IAI por una lista paralela y una excepción obsoleta: ambas fueron corregidas. ITCM de portada 64,1; historia junio 64,8 y julio 60,4. A componentes comunes, junio 61,3 y julio 60,4. La declaración pública cuenta los componentes observados y advierte cobertura variable.

Suite completa: 3576 aprobadas, 4 omitidas por diferencia de período entre tarjeta e historia y 5 advertencias (41,79 s). Build: 81 páginas (1,95 s). Gate sin fallas de integridad, con avisos de caché político y editorial de septiembre sin firma. Logs locales: `/tmp/cigob-suite-0301.log`, `/tmp/cigob-build-0301.log`, `/tmp/cigob-gate-0301.log`.

La segunda revisión encontró que una conciliación judicial vencida recibía un sello nuevo. Corregido: conserva el corte y no cuenta como resultado fresco. Pasaron 76 pruebas dirigidas (12,22 s); la nueva revisión debe comprobar el cierre del hallazgo. El primer revisor obtuvo 3559 pruebas aprobadas, 18 omitidas y tres fallos de red; esos fallos no aparecieron en la suite completa con transporte curl real.

Cotejo Votómetro: corpus de agosto con 125 sondeos, último campo de espacios 22-jul, brecha independiente 4,2893 pp. Se corrige la afirmación falsa de deriva diaria en su ficha. Nuevo pendiente detectado en expectativas de construcción: el final del horizonte trimestral se usa como fecha del dato. No se certifica todavía ese componente.

La revisión posterior no volvió a señalar el sello judicial; detectó una frase
temporal en la ficha nueva que bloqueaba `test_texto_publico_no_caduca`. Se
reformuló con la fecha explícita del retiro del cinturón y se regeneraron fichas
y manuales. Cierre dirigido: 26 pruebas aprobadas (0,57 s), incluidas las de
texto temporal, fichas generadas, bandas, pesos y sello judicial. Build final:
81 páginas (1,89 s). Logs: `/tmp/cigob-review-0301-sello.log`,
`/tmp/cigob-tests-0301-final.log`, `/tmp/cigob-build-0301-final.log`.
No se presenta la revisión previa como limpia: sus dos hallazgos fueron
corregidos y verificados mediante las pruebas correspondientes.

Snapshot de este cierre: SHA-256
`1f2dd9d9c669c3426af7f3762986f5d631008fa47a1b702f4153b1469db3e2c4`.
El censo conserva 63 indicadores y 24 dimensiones, sin fallas estructurales
ni aritméticas. La cobertura de fuentes queda en 46 comprobadas, nueve
reproducidas sin cierre de vigencia, dos correcciones pendientes, tres consultas
incompletas, una revisión parcial y dos comprobaciones con salvedad.

### Expectativas de construcción — ADR-0302

Se verificó el Cuadro 7.1 del original INDEC y el informe de julio publicado
el 8 de septiembre. La fecha pasa del final al inicio del horizonte consultado,
con ambos extremos explícitos. Se recuperan filas con «de» antes del año y se
exige calendario consecutivo. Tarjeta: −1,8 pp, horizonte agosto–octubre;
historia: 110 puntos de julio de 2017 a agosto de 2026.

La publicación deja de imprimir correlaciones antiguas: usa la corrida vigente
y declara cuando el contraste no está disponible. Se retiraron explicaciones
causales que no se desprenden de una correlación. ITCP de portada: 70,5;
historia agosto: 68,2, con variación +1,1 frente a −0,5 sobre componentes comunes.

Nueve pruebas dirigidas aprobadas (0,20 s). Suite completa: 3593 aprobadas,
cuatro omitidas por distinto mes entre tarjeta e historia y cinco advertencias
(43,78 s). Build: 81 páginas (1,88 s). Gate aprobado, con los avisos de caché
legislativo y editorial no firmada ya documentados. Logs locales:
`/tmp/cigob-suite-0302.log`, `/tmp/cigob-build-0302.log`,
`/tmp/cigob-gate-0302.log`. Segunda revisión de código pendiente de cierre.

La cobertura de fuentes pasa a 47 comprobadas, nueve reproducidas sin cierre
de vigencia, una corrección judicial pendiente, tres consultas incompletas,
una revisión parcial de cartera y dos comprobaciones con salvedad.

La segunda revisión de ADR-0302 terminó sin hallazgos nuevos. Build propio del revisor aprobado; 3576 pruebas aprobadas, 18 omitidas y tres fallos DNS en su entorno, que no aparecen en la corrida completa con transporte curl real. Log: `/tmp/cigob-review-0302.log`. Censo final de la corrección: 63 indicadores y 24 dimensiones sin fallas; SHA-256 `19d310fa6394993d06a7436bdb3b69ea411b9bbc7c4a7e29b8c74eb7d08c0340`.

Se cerró además el cotejo de concesiones con el universo original de Vialidad y los actos de las cuatro etapas. La ficha se alineó con el uso de Boletín Oficial ya implementado por el colector. La cobertura pasa a 48 comprobadas, ocho reproducciones sin cierre de vigencia, una corrección judicial pendiente, tres consultas incompletas, una revisión parcial y dos comprobaciones con salvedad.

Después de corregir la ficha de concesiones: 24 pruebas de textos y fichas
aprobadas (0,36 s), build de 81 páginas (2,08 s), `git diff --check` sin errores.
Logs: `/tmp/cigob-fichas-rfc-0302.log` y `/tmp/cigob-build-0302-final.log`.
# Calendario ACLED cerrado — ADR-0303

La suite completa terminó con **3611 passed, 4 skipped, 5 warnings en 45,47 s**. Los cuatro omitidos comparan meses distintos de historia y portada; no se cuentan como pruebas aprobadas. Astro compiló 81 páginas en 2,13 s. El gate pasó, conservando los avisos de dos tarjetas legislativas en caché y la lectura editorial de septiembre pendiente.

`codex review --uncommitted` terminó sin hallazgos accionables nuevos. Su propia suite registró 3594 aprobadas, 18 omitidas y tres fallos de DNS en consultas externas; la corrida integral con transporte curl y las mismas fuentes sí pasó. No se simularon respuestas.

El censo conserva 63 indicadores activos, 24 dimensiones y cuatro cinturones, sin fallas de estructura ni aritmética. Snapshot de esta etapa: `2026-09-08T17:07:36.084353-03:00`, SHA-256 `0de14930ec92e2871e5b2a028c0b38112f19bc6efc949d599412bbf53aa72221`. La matriz llega a 49 comprobaciones individuales y siete reproducciones aún sin cierre; mantiene los demás pendientes declarados.

El corte semanal ACLED recupera agosto; ITCP julio 67,1 y agosto 66,7, variación −0,4 también sobre componentes comunes. ITCP–EPU: −0,286 en niveles y −0,273 en primeras diferencias. La discrepancia con el repunte del ICG queda explícita en el contraste cualitativo. Fichas, manuales, sensibilidad, índice ADR y censo regenerados. Cambios locales, sin despliegue.
# Adhesiones RIGI corregidas — ADR-0304

El cotejo en vivo verifica 18 jurisdicciones sobre 24: catálogo MAGyP más las leyes originales de Santa Fe y CABA. Las 126 pruebas focalizadas iniciales pasaron. La suite completa registró **3620 passed, 4 skipped y tres fallos documentales en 67,74 s**: faltaba enumerar las bandas en la ficha y sobraba una excepción del inventario de texto temporal, con su piso asociado. Se corrigieron las bandas y el inventario; las **20 pruebas focalizadas finales pasaron en 0,41 s**. No se presenta esa primera corrida como una suite íntegramente verde.

La compilación posterior detectó que la tabla de bandas requería también puntos de interpolación y unidad. Se completaron con las anclas del motor; el build final compiló **81 páginas en 2,22 s**. Los manuales y fichas Markdown se regeneraron después de ese ajuste.

`codex review --uncommitted` terminó sin defectos accionables nuevos. Su suite registró 3606 aprobadas, 18 omitidas y tres fallos de DNS en fuentes externas. Los fallos documentales ya no aparecen en esa corrida. El gate pasó y conserva los dos avisos legislativos de caché y la lectura editorial de septiembre pendiente.

Censo final de esta etapa: 63 indicadores, 24 dimensiones y cuatro cinturones, sin fallas de estructura o aritmética. Snapshot `2026-09-08T17:20:01.858628-03:00`, SHA-256 `f9cd7890552584715dce7cead4ddd5cb3141903d36eb3ef301005ac5c9510b18`, comprobado nuevamente después de las pruebas. Matriz: **50 comprobados, seis reproducidos sin cierre, tres consultas incompletas, dos comprobados con salvedad, una corrección pendiente y una cartera parcialmente revisada**.

ITCP actual 71,1; historia 2026: 65,7; 64,7; 67,0; 62,6; 66,9; 67,9; 68,1; 67,7. Junio +1,0 frente a +3,3 sobre componentes comunes; agosto −0,4 con los mismos componentes. ITCP–EPU −0,270 en niveles y −0,273 en diferencias; brecha discriminante del panel 0,132. Se actualizaron tabla mensual, contraste cualitativo, informe, fichas, manuales y registro de fuentes. Sin despliegue.
# FAL: fechas de consulta y curaduría — ADR-0305

Se exponen por separado las revisiones normativa (20-jul) y judicial (21-ago), la consulta CNV del 8-sep y la fecha de evaluación. La integración usa las fechas previamente documentadas y conserva el sello de la consulta real; no simula una consulta nueva ni una revisión judicial. Se retiran las garantías infundadas de ausencia de rezago y de integridad del archivo local, y la interpretación de litigiosidad SRT como resultado directo del FAL.

**28 pruebas focalizadas pasaron en 0,62 s**. Astro compiló 81 páginas en 2,21 s. El gate conserva únicamente los avisos conocidos de dos tarjetas legislativas en caché y la lectura editorial de septiembre. `codex review --uncommitted` terminó sin hallazgos nuevos; su build pasó y su suite registró 3616 aprobadas, 18 omitidas y tres fallos por acceso a fuentes externas. Esos fallos no se cuentan como comprobaciones realizadas.

Valor FAL 50 e índices sin cambios. Ficha, manuales, sensibilidad y censo regenerados. Snapshot `2026-09-08T17:30:13.614864-03:00`, SHA-256 `aa26a4e7e55aacc8e0f45d8c5cea43aef19cb667bfb9bce0fc8a2a0ac91276eb`, verificado después de las pruebas. Censo: 63 indicadores, 24 dimensiones, sin fallas estructurales o aritméticas. La fuente FAL sigue sin cierre judicial al corte; la matriz mantiene 50 comprobaciones individuales y seis reproducciones pendientes. Cambios locales, sin despliegue.

# Producción legislativa — ADR-0306

Se corrigieron límites mensuales, duplicados, referencia histórica y gráfico metodológico. API y CSV coinciden tras normalizar tipos. Dos omisiones (27748 y 27774) se cotejaron en otro informe HCDN y en el BO y se integraron sin duplicación. Tarjeta 22 leyes hasta agosto; ITCP actual 71,1. Historia y contraste externo recalculados: julio −0,6, agosto −0,5; EPU niveles −0,287 y diferencias −0,262.

Primera revisión: 3628 pruebas exitosas, 18 omitidas y cuatro fallidas; tres por red y una por encabezados no canónicos del ADR. Se corrigió el formato. Tras incorporar las omisiones, **1851 pruebas documentales y focalizadas pasaron en 1,82 s**. La primera construcción generó 81 páginas en 1,89 s. La verificación final se registra a continuación; no se declara aquella suite íntegramente verde.

Verificación final ADR-0306: `codex review --uncommitted` no encontró nuevos defectos; su suite terminó con **3630 aprobadas, 18 omitidas y tres fallos por DNS de INDEC**, y su build generó 81 páginas en 1,88 s. El build local independiente también pasó (81 páginas, 1,97 s). Censo: 63 indicadores y 24 dimensiones, sin fallas estructurales ni aritméticas; snapshot `22dcf47af24f6f9bed90d952d09ad80c9a7768a4228bc6ce8a16c95b53baeb6e`. La cobertura completa de fuentes sigue abierta.

# Ratio DNU: calendario e inventario — ADR-0307

La consulta de un día confirma extremos inclusivos. Se corrigen tarjeta e historia a 365 fechas (final menos 364). Primeras pruebas: 1866 aprobadas y dos fallos por relaciones/índice ADR aún sin regenerar; después de sincronizarlos, **1868 aprobadas en 3,02 s**. Inventario por meses sin errores: 3.905 decretos; 143 rótulos DNU cotejados con sus originales (114 DNU, 28 DECNU y un DECTO). La tarjeta sigue 35/25=1,4; cambian febrero, mayo y noviembre de 2024, y abril de 2025. Historia 2026 sin cambios; ITCP–EPU −0,287 en niveles y −0,264 en diferencias; brecha del panel 0,166. Artefactos y verificación final se registran a continuación.

Cierre ADR-0307: la revisión independiente registró **3638 aprobadas, 18 omitidas y cuatro fallos**: tres por red y uno por el rótulo temporal de la unidad del CSV. Se corrigió la unidad a «DNUs publicados por ley publicada» en CSV y catálogo del descargador, conservando el control de escalas. También se explicitó el carácter provisional del mes en curso. Las **1884 pruebas focalizadas y documentales finales pasaron en 3,49 s**; construcción final de 81 páginas en 2,28 s. `git diff --check` sin errores. Snapshot `4f84f9ebb8f5ae6e68bdf9d86314ab32b5dace6d32faf7d680e1d0ab0ad74fbc`: 63 indicadores, 24 dimensiones y ninguna falla estructural/aritmética. No se declara que la primera suite haya sido íntegramente verde.

# Sesiones y sanciones — ADR-0308

Se integra el índice oficial de sesiones y cinco sanciones definitivas del
diario de la reunión del 26/27-ago. Se excluye la convocatoria futura del
9-sep y el PCT devuelto al Senado. Pruebas de desarrollo: 67 aprobadas;
selección final de calendario, identidad y fallos de fuente: 41 aprobadas.
Censo: 63 indicadores, 24 dimensiones, cero fallas de estructura y aritmética.

La segunda revisión `codex review --uncommitted` no encontró defectos
introducidos: 3655 pruebas aprobadas, 18 omitidas y tres fallos de resolución
DNS de INDEC. Build: 81 páginas, 2,22 segundos (la revisión repitió el build
con éxito). Se corrigieron después referencias de prosa a cifras previas y
se explicitó la carga manual de complementos en la ficha. Las verificaciones
finales de documentación se registran al concluir.

ITCP de portada 71,8; marzo histórico 66,9; agosto 68,0 frente a julio 67,8.
ITCP–EPU: −0,285 niveles y −0,261 diferencias; panel: brecha 0,166 diferencias.
Snapshot: 2026-09-08T18:17:20.209772-03:00,
SHA-256 29802e5bd931b8ece49f906184c449e53bd7a8a915ba68d8ec5867c40c1bb863.
No se ha desplegado. Queda abierta la exhaustividad de sanciones de ambas cámaras.

Cierre documental ADR-0308: **1889 pruebas aprobadas en 2,75 s**; build final de 81 páginas correcto; `git diff --check` sin errores. El inventario adjunto conserva las 72 coincidencias con fechas desplazadas dos días y las reuniones excluidas.

# Consolidación del cotejo legislativo de agosto

Se verifican siete números de ley omitidos en CKAN: 27.819–27.825. Las cinco
sanciones de Diputados llevan fecha legal 26-ago en los textos comunicados;
la fecha de la noticia (27-ago) no las reemplaza. Senado consigna dos leyes
el 27-ago y remite los otros tres tratados a Diputados. Producción: 29;
ITCP actual 71,9; agosto histórico 68,2 (julio 67,8). Censo de 63 indicadores
y 24 dimensiones sin fallas; snapshot 2026-09-08T18:27:03.632668-03:00,
SHA-256 60ffb61b886c76ffd7634c7c153b25afe3cffb62aaeacd948c7d36c5386fd34e.

Control dirigido de documentación y producción: 1888 aprobadas y un fallo
de encabezado ADR; se corrigió a subsección y las 1851 pruebas de formato
aprobaron. No se repite la revisión completa del repositorio por solicitud
del usuario de reducir consumo. La prueba puntual de acceso al acta 5960
de Diputados terminó con error de conexión (curl 35, HTTP 000), no 404:
no acredita ausencia del acta y se conserva la limitación de cobertura.

La cohorte vigente de eficacia se conserva nominalmente: 2 aprobados de 14
(14,3%). Sus límites son antigüedad de 365 a 730 días inclusivos: no doce
meses calendario exactos. El cotejo del catálogo no reemplaza la verificación
independiente pendiente de integridad de proyectos.

## Eficacia: corte diario de tarjeta y ficha

Se acota el numerador al día evaluado, igual que la historia. Seis pruebas dirigidas de eficacia aprobaron en 0,32 s (112 de otros temas excluidas); se regeneró sólo la ficha política. El dato vigente sigue 14,3%, sin recalcular índices ni repetir el pipeline completo. El control documental posterior: 12 passed in 0.29s. Véase [cotejo](eficacia-corte-y-cohorte.md).

## Transener y precisión documental de privatizaciones

La integración del cierre de Transener en agosto pasó 33 pruebas dirigidas de
gestión, detector y fichas (0,38 s). Build Astro: 81 páginas, 1,67 s. La
corrección afecta junio y julio históricos; el valor actual no cambia. Se
actualizó la correlación del factor ITCG en diferencias a −0,052 y la matriz
de cobertura conserva la revisión parcial de la cartera.

Se cotejaron después SE 75/2026, ME 1181/2025 y ME 1233/2026 para precisar
Enarsa y YCRT: no cambian sus etapas ni la serie. Los USD 1081M contextuales
heredados quedan marcados como pendientes de conciliación contable, sin
presentarlos como cobros verificados. Se regeneraron informe, publicación
local, fichas de gestión y censo. Snapshot 18:46:14.917117-03:00;
SHA-256 66697b11d788d082134041ebef610cb5b8fc5519b08e135bc92c1d8efc3f9337.
63 indicadores y 24 dimensiones, sin fallas estructurales ni aritméticas.
El build citado precede a esta última precisión de prosa.

Control documental posterior a la precisión: 12 pruebas aprobadas en 0,28 s;
`git diff --check` sin errores. No se repite validación externa porque no se
modificaron valores ni series en esta precisión.

## SOFSE, Nucleoeléctrica y explicación del modal

Se retira la suspensión no acreditada del registro de SOFSE y se precisa la
transformación societaria documentada, diferenciándola del procedimiento de
un servicio específico. Para Nucleoeléctrica se explicita que el plazo de ME
1751/2025 no acredita cumplimiento. Las etapas y los valores no cambian.
El modal admite respaldo primario CNV y distingue autorización de cierre;
la tabla de ADR-0101 queda rotulada como ejemplo histórico de julio.

Verificación: 22 pruebas dirigidas aprobadas en 0,31 s; build de 81 páginas
correcto en 1,45 s; `git diff --check` sin errores. Censo: 63 indicadores,
24 dimensiones, cero fallas de estructura/aritmética. Snapshot
2026-09-08T18:49:00.139527-03:00; SHA-256
56e6f8f3250943801a2b5049d1dd33c01677abf17e455c867e69d8ecc153e38b.
Se conserva la salvedad de exhaustividad de novedades de privatizaciones.

## FAL: acceso primario pendiente; quórum: cotejo nominal cerrado

El portal SCW presenta CAPTCHA para consultar CNT 10308/2026. Se preparó
la consulta y se pidió confirmación para resolverlo; no se eludió el control.
Se identificaron falsos positivos de actualidad y de norma en noticias y se
cotejó la copia judicial de mayo, sin adelantar la fecha de revisión del FAL.

El cotejo nominal independiente de quórum selecciona diez reuniones del
inventario oficial conservado y una en minoría. Se comprobó contra la tarjeta
vigente, con límites octubre-2025/8-sep-2026 explícitos; el estado pasa de
reproducción a comprobación. Se guardaron selección y exclusiones en
`cotejo-quorum-nominal.json`. No cambian código, datos numéricos ni salidas:
no se repiten suites o builds.

## Lectura completa del Senado

Se corrigen cuatro funciones de cohesión/alineamiento, vigentes e históricas:
fallo de detalle o HTML sin votos no produce una actualización parcial. Las
tarjetas excluyen actas futuras. Ocho pruebas nuevas y las suites relacionadas:
148 aprobadas en 1,93 s; fichas regeneradas: 12 controles aprobados en 0,27 s.
`git diff --check` sin errores. No se ejecutaron colectores reales ni se
modificaron series o índices por este hallazgo. Véase
[descripción y alcance](senado-lectura-completa.md).

## Cotejo nominal actual del Senado

Captura real completa: POST de listado 2026 (96 actas) y GET de las 16 de
la ventana vigente; todas las respuestas HTTP 200. Extracción independiente
por encabezados: 72 nombres únicos por acta, 1.152 filas coincidentes con el
parser. Agregación provincial independiente: 59,3% en 24 provincias; Rice
Senado 100% en 16 actas. Coinciden con las tarjetas y no cambian índices.
Se guardan hashes, solicitudes y votos en `cotejo-senado-nominal.json`.
Matriz actual: 53 comprobados, 2 reproducidos, 3 consultas incompletas,
3 comprobados con salvedad, 1 corrección pendiente y 1 parcial.

## Cohorte de eficacia — cotejo independiente de trámites

18 trámites diarios de los índices oficiales 2024/2025: 28 entradas PE/JGM,
14 proyectos y 14 mensajes de otro tipo. Comparación exacta de conjuntos
contra los 14 expedientes de la cohorte guardada: coincide. Tres fechas
CKAN difieren del índice; se cotejaron además tres PDFs originales.
Evidencia en `cotejo-cohorte-tramites.json`; integración aún pendiente.
Sin cambios de código, datos ni índices; no corresponde repetir tests/build.
Matriz: 53 comprobados, 1 reproducido, 3 consultas incompletas,
3 comprobados con salvedad, 2 correcciones pendientes y 1 parcial.

## Fechas TP integradas en eficacia

Función compartida de fecha de publicación para tarjeta e historia, sin
mutar las filas originales. TP 223/2024: 20-ene-2025; TP 109/2025:
6-ago-2025. Se comparó toda la serie calculada desde el catálogo capturado:
sólo julio-2026 cambia de 13,3 a 14,3. ITCP julio: 67,8 → 67,9;
actual 71,9 y agosto 68,2 sin cambios. Contraste, contribuciones, fichas,
sensibilidad y publicación regenerados.

19 pruebas dirigidas aprobadas (0,45 s), build de 81 páginas correcto
(1,47 s). Censo: 63 indicadores, 24 dimensiones, cero fallos.
SHA snapshot: ac7905689a022593dbb0ef59a1fff5de03c92331743d6152792c4f7722bda5bc.
Matriz: 53 comprobados, 1 reproducido, 3 consultas incompletas,
4 comprobados con salvedad, 1 corrección pendiente y 1 parcial.
Queda cotejar exhaustividad del origen Senado; no se cierra la auditoría.

## Cohorte vigente — origen Senado comprobado

Cuatro consultas POST (PE/JGM, 2024/2025, PL) y tres fichas originales:
todos HTTP 200. Un PL PE de 2024 y dos de 2025, ya presentes en CKAN;
ingresos fuera de la ventana actual. JGM sin resultados. La cohorte actual
2/14 queda comprobada con Senado y Diputados. No hubo cambios de datos,
código ni salidas; no se repiten tests o build. Matriz: 54 comprobados,
1 reproducido, 3 consultas incompletas, 3 comprobados con salvedad,
1 corrección pendiente y 1 parcial. Véase `cotejo-cohorte-senado.json`.

## Diputados — acceso recuperado, integración pendiente

Listado oficial accesible en navegador y PDF 5995 con requests nativo.
Walk contra máximo observado 5995, con caché temporal: recorrido completo,
42 actas con señal, Rice provisional 100%, última 27-ago. Se detectó una
omisión del parser por nombres largos de bloques: faltan tres afirmativos
en 5995 al comparar con encabezado y extracción independiente. No se
integraron datos; corregir parser y verificar primero. Capturas guardadas.

## Parser PDF Diputados — corrección comprobada

Se infieren inicios de columna desde filas válidas de cada página, evitando
perder bloques largos. Los 29 PDFs nuevos reproducen los totales de sus
encabezados y 256 nombres únicos por acta. Rice LLA sin cambios. Fixture
5959 corregido contra su encabezado original: 107 negativos, no 103;
256 filas, no 252. Las expectativas anteriores copiaban el defecto.
148 pruebas dirigidas aprobaron (1,87 s). Consolidación productiva pendiente
junto con la actualización de eventos; véase `diputados-parser-columnas.md`.

## Integración Diputados y eventos completada

29 actas nuevas verificadas; Diputados pasa a 42 actas con señal, Senado
16, Rice bicameral 100% y 58 actas. Registro InfoLeg/Senado actualizado;
clasificación Diputados hasta 5995 sin pendientes. Desafíos=0; bloqueo sin
universo (sin puntaje). ITCP actual 73,0, tensión 2,7. Historia julio 67,9
y agosto 68,2 sin cambios.

Sensibilidad corregida para redondear dimensiones como el motor: bases
publicada/recomputada iguales en los cuatro índices. 148 pruebas de
cohesión (1,87 s), 37 de sensibilidad/universo/fichas (0,67 s), build 81
páginas (1,41 s). `git diff --check` sin errores. Censo 63 publicados,
62 observados, 1 sin universo, 24 dimensiones, cero fallos aritméticos.
Snapshot 2026-09-08T19:22:19.225561-03:00; SHA
4f4bbf22cb90cb1d962eb7f01f03c0c93717c439a4175d114d4f6eb5316e5a69.
Matriz: 57 comprobados, 1 reproducido (FAL), 3 comprobados con salvedad,
1 corrección pendiente y 1 parcial. No hubo push ni deploy.

## Cobertura judicial — corroboración del Consejo

Mapa oficial actualizado 4-sep y tres exportaciones públicas HTTP 200
(78/279/69 filas) consultados el 8-sep. Concurso 381 identifica Fraga y
Cámara San Justo no habilitada; concurso 447 es otro órgano. La fuente
antecede al decreto y no prueba jura ni baja en Civil 104. Se conserva
705/955 como estimación; no hubo cambios de datos ni repetición de tests.
Evidencia: `cotejo-san-justo-consejo.json`.

## Portada: bandas, alcance y gráficos

Build 81 páginas (1,36 s), 18 controles de semáforos y revisión acotada sin hallazgos. Cuatro curvas comprobadas en navegador tras animación, sin errores JS. Datos sin cambios. Detalles y límites en [portada-coherencia.md](portada-coherencia.md).

## Procedencia de bloqueo y controles

78 pruebas de procedencia/fichas aprobadas (0,12 s), build 81 páginas (1,66 s) antes de la precisión final de texto de controles. Valores sin cambios. [Corrección y fuente](bloqueo-procedencia-corregida.md).

## Cobertura detector privatizaciones

17 verificaciones aprobadas (0,30 s), build 81 páginas (1,35 s), revisión estática acotada sin hallazgos. [Alcance](privatizaciones-cobertura-detector.md). Sin colectores reales ni cambios numéricos.

## Método de obtención judicial y reconciliación

Se corrigió `metodo_obtencion` de cobertura judicial: automática → semiautomática, coherente con la ficha y su conciliación manual. Comparación recursiva de snapshots: única diferencia en ese campo, sin cambios numéricos. 56 automáticos, 5 semiautomáticos y 2 manuales.

La prueba de reconciliación política asumía 17 componentes puntuando, aunque bloqueo sin universo no puntúa. Ahora comprueba 17 tarjetas, exclusión/nulo de bloqueo en ese estado y conserva reconciliación ponderada y pesos. La primera corrección usó un nombre de campo equivocado (`estado_dato`); se corrigió a `estado` y se distinguió sin universo de contexto. Resultado final: 36 pruebas de publicación aprobadas (0,74 s). Build anterior a esos ajustes sólo de tests: 81 páginas (1,51 s). Censo actualizado, sin fallos.

SHA vigente del snapshot: `c61e523fc29ead5ee9978095697b07356347c9f135fc0725cb2887cb4a1ec899`.

## Documentación vigente y entregas Word

Corrección de instrucciones y enlaces; Word históricos preservados. Sin cambios de datos o código ni repetición de tests/build. [Registro](documentacion-vigente-y-word.md).

Importes contextuales reclasificados como antecedente periodístico no conciliado; etapas y snapshot intactos. [Evidencia y verificación](privatizaciones-importes-contextuales.md).

Contraste político: prosa de aportes actualizada; los ocho meses de descomposición se reprodujeron sin diferencias. [Control](contraste-descomposicion-coherencia.md).

Contraste externo: diferencias y adelantos usan meses calendario; 14 pruebas aprobadas y resultados actuales conservados. [Evidencia](contraste-calendario.md).

Panel externo: lectura corregida para asociaciones absolutas, sin garantizar eliminación de tendencia; dirección de la regresión explicada. 25 pruebas aprobadas, publicación local y build correctos. Véase contraste-panel-lectura.md.

Calendario extendido a panel, factores y regresión; 57 pruebas aprobadas. Las regresiones guardadas se reproducen; faltan insumos completos para cotejar el resto del panel. [Detalle](contraste-calendario-panel.md).

Julio ICG recuperado desde XLS oficial; panel completo cotejado y recalculado, con insumos guardados. [Corrección](icg-julio-corregido.md). La falta de insumos señalada en etapas anteriores queda resuelta.

Verificación integral actual: 3.694 pruebas aprobadas, cuatro omisiones por períodos distintos; corregidos cinco fallos documentales/de composición. Build correcto. [Detalle](verificacion-integrada.md).

## Control de publicación y cobertura final

Gate aprobado; único aviso G8 de lectura editorial septiembre ausente. Matriz63filas comprobada contra todas las claves/fechas del snapshot, sin diferencias. Estado-actual consolidado para retirar pendientes superados del panel y reflejar suite integrada vigente. Sin cambios de código/datos ni repetición de tests/build.

## Borrador editorial de septiembre

Se reemplazó la plantilla vacía por una propuesta de dos párrafos. Distingue el corte abierto al 8-sep de los movimientos de agosto; utiliza tensión para comparar cinturones, evita equiparar capacidad política con aprobación y conserva las limitaciones de fuentes. El comentario interno enumera los documentos y cifras de sustento. Permanece en `borradores/`, fuera del glob publicado y sin firma institucional. No cambia datos, cálculos ni la portada; no corresponde repetir la suite ni el build por este texto excluido.

## Explicaciones de indicadores con fuentes pendientes

Corregidos los textos del modal judicial, FAL y privatizaciones para no contradecir estimaciones, fechas de revisión y fórmula de las fichas. Cuatro pruebas de texto aprobadas, build de 81 páginas y comprobación del contenido generado correctos. Sin cambios de datos. Véase [cotejo de modales](modales-fuentes-pendientes.md).

## Alcance de las explicaciones

Corregidas contradicciones entre fórmulas, fichas, explicaciones de indicadores y dimensiones. Nueve pruebas dirigidas aprobadas, build de 81 páginas correcto y SHA del snapshot conservado. [Detalle del cotejo](alcance-explicaciones.md).

## Explicaciones sociales

Peso fijo obsoleto retirado, componentes y límites alineados; ficha de carnes corregida. Nueve pruebas dirigidas, build 81 páginas y comprobación HTML aprobados. [Detalle](explicaciones-sociales.md).

## Lectura generada de carnes

Corregida clasificación que confundía nivel histórico, variación y sustitución. 43 pruebas de publicación y build de 81 páginas aprobados. Comparación JSON completa: sólo cambió el texto `por_que` de carnes. [Detalle y SHA vigente](carne-lectura-generada.md).

## Censo actualizado y balance por requisito

Censo regenerado con SHA 5e048a…: 63 indicadores, 24 dimensiones, cero fallos. Leyenda de carnes y ADR-0217 alineados con el alcance rectificado. Cuatro pruebas de texto y build 81 páginas aprobados. [Balance](balance-requisitos.md), con pendientes explícitos sin declarar cierre integral.

## Cierre autorizado con reservas

Tras la indicación de Juan de cerrar con criterio propio, se consolidaron conclusión, decisiones y reservas en `cierre.md`. No se modificaron datos ni metodología; se conservan los límites judiciales, del FAL y de privatizaciones. No se publicaron cambios ni se atribuyó firma al borrador editorial.
