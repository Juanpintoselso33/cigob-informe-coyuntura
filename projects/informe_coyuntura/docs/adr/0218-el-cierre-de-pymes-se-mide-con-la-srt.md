---
madr: 4
id: '0218'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [mortalidad_pymes]
archivos: ['scripts/vida_cotidiana/collectors/srt_empleadores.py', 'scripts/vida_cotidiana/main.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/gate_calidad.py', 'tests/test_cierre_pymes.py']
cierra: ['0119']
relacionado: ['0012', '0018', '0130']
ambito: 'ITCIS · dimensión de prospectivas de empleo · qué mide mortalidad_pymes'
origen: 'Documento de fuentes "260811 cierre de pymes" y el plan de adopción del 12-ago-2026'
---

# ADR-0218 — El cierre de PyMEs se mide con la SRT, no con la producción industrial

## Contexto y planteo del problema

`mortalidad_pymes` pesa 3,97% del ITCIS y **no medía mortalidad ni PyMEs**. Su
fuente era el **IPI manufacturero desestacionalizado del INDEC**: producción
industrial, tomada como proxy de la salud del entramado PyME. El informe decía
"cierre de PyMEs" y publicaba actividad fabril.

No era un secreto. [[0119-pendientes-de-baja-prioridad-vida]] lo detectó en
julio de 2026 y decidió **no** renombrar la clave, porque el rótulo público ya
decía "Actividad industrial (IPI)" y renombrar tocaba series, CSV, snapshot y
mapeos con riesgo real y cero ganancia para el lector. La decisión era correcta
para lo que había entonces: no existía una fuente mensual del dato verdadero.

En agosto de 2026 llegó un documento de fuentes que la identificó, y el plan de
adopción del 12-ago lo dejó **explícitamente diferido** —*"necesita una ficha
primero"*— con tres cosas por definir: la métrica, el recorte PyME y las bandas.

## Factores de decisión

- **Un indicador tiene que medir lo que su nombre promete.** El costo de que no
  lo haga no es cosmético: entra al índice con 3,97% y mueve el número.
- **La fuente tiene que llegar al 4T-2023**, que es la base de los dieciséis
  componentes, y tiene que actualizarse mensualmente.
- **El recorte PyME hay que fijarlo, no dejarlo abierto**, o el indicador
  cambia de significado cuando cambie la composición del padrón.
- **Card y serie deberían ser el mismo número.** El arreglo anterior publicaba
  DOS series para este indicador —la card en % m/m y el índice en base 100— y
  por eso G3 nunca podía reconciliarlas.

## Opciones consideradas

1. Base de partes empleadoras de la SRT, tramos de hasta 50 trabajadores.
2. Base de empleadores de OEDE/CEP (AFIP), que es el equivalente por el lado
   tributario.
3. Padrón de ARCA: CUITs empleadores más monotributistas y autónomos.
4. Dejar el IPI y renombrar el indicador a lo que mide.

## Decisión

**Opción 1.** `mortalidad_pymes` pasa a medir la **cantidad de empleadores de
hasta 50 trabajadores con cobertura de ART**, de la serie histórica de la
Superintendencia de Riesgos del Trabajo.

Por qué esta fuente y no la de AFIP: **la base de empleadores de OEDE dejó de
actualizarse en octubre de 2023**, o sea justo antes del mandato que el informe
evalúa —verificado el 2026-08-21: los cinco archivos del dataset terminan en
`2023-10`—. La SRT publica todos los meses y su serie llega a mayo de 2026, con
359 puntos desde julio de 1996.

Las tres definiciones que el plan había dejado abiertas:

- **La métrica**: el **nivel** de empleadores activos, rebaseado a 100 = promedio
  del 4T-2023, como los otros quince componentes. No la variación neta mensual:
  el nivel acumulado dice cuántas empresas quedan respecto del arranque, que es
  la pregunta del informe, y no depende de la estacionalidad de un mes.
- **El recorte PyME**: se **suman los tramos** 1 · 2 · 3 a 5 · 6 a 10 · 11 a 25 ·
  26 a 40 · 41 a 50. No se toma el total del sistema aunque hoy el tramo sea el
  95,6% de los empleadores: el total incluye a las grandes y el indicador
  dejaría de decir PyME apenas cambie la proporción.
- **Las bandas**: ninguna propia. El componente puntúa por nivel base-100 como
  el resto del ITCIS; no hay tabla de umbrales que calibrar.

**Una sola serie**, en unidades, para la card y para el índice: el rebase lo
hace `itvc.rebase_de_serie`. La serie `itvc_ipi` se retira.

### Consecuencias

- **El componente pasa de 97,4 a 93,8.** El IPI subestimaba el fenómeno: la
  producción industrial recuperó más que el número de empresas. En unidades:
  **491.484 empleadores PyME en el 4T-2023 contra 460.777 en mayo de 2026, o
  sea 30.707 menos, un −6,2%.**
- **El ITCIS baja de 90,7 a 90,6**, tensión 6,9. El componente pesa 3,97%.
- La dimensión de prospectivas de empleo queda con **tres medidas directas** de
  empleo —informalidad, empleo registrado y ahora cierre de empresas— y un solo
  proxy de actividad, la construcción. Era el diagnóstico de ADR-0033 y termina
  de cerrarse acá.
- **El IPI manufacturero sale del ITCIS.** No es una pérdida: la actividad
  industrial ya se mide en macro, y esta dimensión no la necesitaba para hablar
  de empleo.
- La clave `mortalidad_pymes` **no se renombra**, siguiendo ADR-0119: ahora es
  correcta. El rótulo público pasa de "Actividad industrial (IPI)" a
  **"Empleadores PyME activos"**.
- El tope de frescura sube de 140 a **165 días**: la SRT publica con ~3 meses de
  rezago, contra el mes y medio del IPI. Con el tope viejo quedaba menos de un
  mes de margen y el gate habría empezado a marcar demoras falsas.

### Lo que este indicador NO mide, y queda anotado

El documento de fuentes traía una segunda mitad —monotributistas y autónomos
como sustitución del empleo tradicional— que **es otro indicador**, no una
mejora de éste. Un país donde cierran PyMEs y crecen los monotributos de
servicios no es lo mismo que uno donde cierran y no aparece nada; esta serie no
distingue los dos casos. Vale la pena, con su propia ficha.

### Confirmación

`tests/test_cierre_pymes.py` cuida que la fuente siga siendo la SRT y no vuelva
a ser el IPI, que la card cuente empleadores, que **card y serie sean el mismo
número** —lo que el arreglo anterior no podía—, que el recorte se declare por
tramo y no por total, y que la serie llegue al 4T-2023.

El parser se ancla en el texto de cada tramo y en las celdas de fecha, nunca en
posiciones: si la SRT agrega un tramo, los que busca siguen encontrándose; si
desaparece alguno, el colector falla en voz alta en vez de devolver una suma
incompleta.

## Pros y contras de las opciones

**1. SRT.** A favor: mensual, viva, con serie desde 1996 y con el corte por
tamaño de nómina ya hecho por la fuente; la baja de una PyME aparece rápido
porque el contrato con la ART se rescinde al cesar la actividad. En contra: ~3
meses de rezago, y sólo ve empleadores con al menos una persona declarada —una
empresa que despide a todos y sigue existiendo cuenta como baja.

**2. OEDE/CEP (AFIP).** A favor: sería el universo tributario completo. En
contra: **congelada en octubre de 2023**. No sirve para evaluar este mandato.

**3. Padrón de ARCA.** A favor: permitiría medir la sustitución hacia
monotributo, que es la pregunta interesante. En contra: no se publica como serie
mensual descargable, y es otro indicador — no el cierre de empresas.

**4. Dejar el IPI y renombrar.** A favor: cero trabajo y honestidad recuperada.
En contra: deja al informe sin ninguna medida de cierre de empresas, que es
justo lo que el editor pidió.

## Más información

- El archivo es `Serie_historica_Segun_Tamaño_de_la_nomina_del_empleador - UP.xlsx`,
  hoja "Cuadro 4.2: Parte empleadora".
- Contraste declarado que el colector también releva: las empresas de más de
  500 trabajadores cayeron 3,8% en el mismo período contra el 6,2% de las
  PyMEs. El fenómeno es del tramo chico, no de toda la economía.
