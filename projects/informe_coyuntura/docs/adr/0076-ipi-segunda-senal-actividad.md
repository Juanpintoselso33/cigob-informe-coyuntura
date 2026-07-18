# ADR-0076 — La dimensión de actividad deja de colgar de un único dato

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón macro · ITCM · dimensión Actividad económica · `ipi_manufacturero` (nuevo) · `emae_ia` |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | ADR-0029 (promedio móvil contra el ruido del interanual de un mes suelto) · ADR-0021 (puntaje interpolado) |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 3 |

## Contexto

La dimensión de actividad pesaba 11% del ITCM y tenía **un solo componente**,
el EMAE, con peso 1,0. La auditoría lo marcó como riesgo de fuente única
agravado por el rezago: el EMAE es el indicador simple más rezagado del índice
(~2 meses). La propia ficha del EMAE ya declaraba la limitación —"es la única
variable de su dimensión: el 11% del índice cuelga de un solo dato"— sin que
hubiera un segundo indicador que la resolviera.

### Candidatos descartados

- **Demanda de energía eléctrica (CAMMESA)**: sería la señal de más alta
  frecuencia posible, pero las series de energía disponibles en la API pública
  **terminan en 2015-2016**. Sin fuente automatizable.
- **Patentamientos comerciales**: ya se acumulan en el proyecto como insumo del
  IAI, pero el caché tiene **un solo mes** (may-2026). Sin historia, no puede
  puntuar ni reconstruirse hacia atrás. Vuelve a ser candidato cuando el cron
  acumule suficientes meses.

## Decisión

Entra el **IPI manufacturero** (Índice de Producción Industrial, nivel general)
como variación interanual **promediada a tres meses**, con **35%** de la
dimensión; el EMAE conserva **65%**.

### Por qué el promedio de tres meses

La variación interanual del IPI original **salta hasta 9 puntos porcentuales de
un mes al siguiente** (feriados móviles, días hábiles, paradas de planta): en
2026, feb −8,87%, mar +5,02%, abr −2,53%. Ese ruido no dice nada sobre el
estado de la industria. El promedio de tres meses **reduce el desvío de los
cambios mensuales de 6,2 a 2,5 puntos** —un factor 2,5— sin agregar rezago
apreciable: la serie sigue siendo interanual, sólo deja de vibrar. Es el mismo
criterio que ADR-0029 aplicó a la recaudación.

### Por qué las mismas bandas que el EMAE

Se consideró ensancharlas "porque la industria es más cíclica", y **los datos no
lo respaldan**: sobre el período, el rango del IPI suavizado es de 26,0 puntos y
el del EMAE de 23,5 — comparables. Ensancharlas habría neutralizado justamente
la señal que el indicador viene a aportar. Se usan las bandas del EMAE tal cual,
lo que además deja los dos componentes leíbles en la misma escala.

### Por qué 65/35 y no mitad y mitad

El EMAE es la medida agregada oficial y cubre todos los sectores; el IPI mide
sólo manufactura, alrededor de un sexto del producto. El EMAE debe seguir
mandando. El 35% es peso suficiente para que la segunda señal se note cuando
diverge, sin convertir la dimensión en una lectura industrial.

## Consecuencias

- **Baja el rezago de la dimensión.** El IPI se publica hacia mediados del mes
  siguiente: al momento de este cambio el IPI llegaba a **may-2026** y el EMAE
  a **abr-2026**. La dimensión pasa a tener una lectura un mes más fresca.
- **Las dos señales divergen hoy, que es exactamente el punto.** EMAE +1,64%
  i.a. (puntaje 61,1) contra IPI −1,07% (puntaje 39,4): la actividad agregada
  crece mientras la industria se contrae. Con el EMAE solo, el índice no veía
  nada de eso.
- Dimensión de actividad **61,1 → 53,5**. **ITCM 62,7 → 61,8**, sin cambio de
  banda.
- Serie reconstruida de **30 puntos desde dic-2023**.

### Efecto sobre la validación externa

La correlación del ITCM con el riesgo país **baja levemente, de −0,775 a
−0,764**. Se declara en lugar de omitirse: es el resultado esperable de sumar
una señal sectorial que el mercado no pricea igual que los agregados, y la
magnitud está dentro del ruido de una muestra de 31 meses. No se toma como
argumento en contra: la validación externa mide si el índice acompaña al
mercado, no si describe bien la economía real, y la dimensión de actividad
existe para lo segundo.

## Limitaciones declaradas

- El IPI mide sólo la industria manufacturera: acompaña al EMAE, no lo
  reemplaza.
- El suavizado a tres meses amortigua los quiebres de nivel: un cambio brusco
  tarda dos o tres meses en verse completo.
- Serie original, no desestacionalizada. La comparación interanual absorbe la
  estacionalidad pero no los efectos de calendario, que el suavizado atenúa sin
  eliminar.
- Los dos componentes de la dimensión son **medidas de actividad y correlacionan
  entre sí**: el segundo reduce el riesgo de fuente única, no lo convierte en
  dos lecturas independientes (ver ADR-0075).
