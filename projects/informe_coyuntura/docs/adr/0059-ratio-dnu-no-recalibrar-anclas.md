# ADR-0059 — ratio_dnu: se revierte la recalibración de anclas de ADR-0058

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-15 |
| **Ámbito** | Cinturón política · ITCP · `ratio_dnu` · `BANDAS_ITCP` |
| **Precedentes directos** | ADR-0058 (ventana móvil, parcialmente revertido por este ADR) · ADR-0045 (patrón de recalibración que este ADR determina que NO aplica acá) |

## Contexto

ADR-0058 (mismo día) cambió `ratio_dnu` de acumulado del año calendario a
ventana móvil de 365 días, y en el mismo commit recalibró
`BANDAS_ITCP["ratio_dnu"]` de 0,3/0,7/1,2/2,0 a 1,5/2,0/3,0/4,5, usando el
mismo procedimiento que ADR-0045 (comisiones_caidas): tomar el rango
observado real (32 meses, 1,176–5,545) y elegir anclas redondas que
distribuyan esos puntos entre las cinco bandas, porque con las anclas viejas
31 de 32 meses caían en las dos bandas del piso.

Pedido explícito de auditoría: *"analizate bien el dato, porque puede ser
que esté mal, parece muy bajo — buscate benchmarks en la web y fijate si
estamos haciendo algo mal"*, en referencia al puntaje resultante (73,3 sobre
100, tensión baja) para un ratio de 2,19 (46 DNU / 21 leyes, últimos 365
días).

**Los conteos verificados contra fuentes externas independientes son
correctos.** Comparación con estudios y relevamientos periodísticos:

| Fuente | Período | DNU | Leyes | Ratio |
|---|---|---:|---:|---:|
| Universidad Austral / ODCL (Ámbito, feb-2026) | 2025 completo | 35 | 13 (11 ordinarias) | ~2,7–3,2 |
| Directorio Legislativo (La Nación/TN, dic-2025) | 2025 ordinario | — | 11 (mínimo en 10 años) | — |
| HCDN oficial (estadísticas parlamentarias) | dic-2023→feb-2026 (27m) | — | 64 | — |
| Nuestro InfoLeg (este indicador) | últimos 365 días (a jul-2026) | 46 | 21 | 2,19 |

Los conteos son del orden correcto: no hay evidencia de un error de conteo
en el scraper de InfoLeg. **El problema está en la recalibración de
anclas**, no en los datos.

ADR-0045 recalibró `comisiones_caidas` porque el defecto era **estructural,
no sustantivo**: un proyecto con dictamen reciente casi nunca alcanza a
sancionarse dentro de su propia ventana de 12 meses — es una imposibilidad
matemática de la construcción de la métrica, no una señal real de mal
desempeño. Corregir esas anclas no borra ninguna información real.

`ratio_dnu` es distinto. El rango elevado observado (nunca por debajo de
1,176 en 32 meses reales) **no es un artefacto de la ventana móvil — es una
señal sustantiva real**: este gobierno, con este Congreso, efectivamente
gobierna con una dependencia del decreto muy superior a la práctica
histórica. Un informe de ACIJ ("De la excepción a la regla", 2011-2024,
comparando el segundo mandato de CFK, Macri, Alberto Fernández y el primer
año de Milei) encontró que, sumadas las cuatro presidencias, hubo 344 DNU
sobre 1.058 leyes sancionadas — **ratio ≈0,325, "cada 3 leyes, 1 DNU"**. Ese
número es casi exactamente el corte de 0,3 que ADR-0036 fijó para el puntaje
máximo del indicador: no era un umbral arbitrario del documento, estaba
ya ancorado —aunque sin cita explícita— a una práctica institucional real
de más de una década y cuatro gobiernos distintos.

Recalibrar las anclas contra el rango observado bajo esta única
administración, como hizo ADR-0058, equivale a redefinir "buena práctica
institucional" como "lo mejor que este gobierno ha logrado" — que es
precisamente la señal que el indicador existe para medir, no un defecto de
medición a corregir.

## Decisión

### 1. Revertir `BANDAS_ITCP["ratio_dnu"]` a los valores previos a ADR-0058

```python
"ratio_dnu": [
    (-INF, 0.3, 100), (0.3, 0.7, 85), (0.7, 1.2, 65), (1.2, 2.0, 40), (2.0, INF, 10),
],
```

### 2. Mantener el cambio de ventana de ADR-0058

La ventana móvil de 365 días (en vez del acumulado del año calendario que
resetea en enero) sigue vigente y sigue siendo correcta — ese defecto sí era
estructural (comparabilidad mes a mes rota), igual que el que sacó a
`movilizacion_cepa` del tablero en ADR-0052. ADR-0058 no queda superado en
su decisión principal, solo se revierte la recalibración de anclas que
llevaba adjunta.

### 3. Criterio para distinguir cuándo recalibrar y cuándo no

Para dejar este criterio explícito de cara a futuras recalibraciones:
recalibrar contra el rango observado (patrón ADR-0038/0039/0042/0043/0045)
es correcto cuando el techo o piso es **matemáticamente inalcanzable por la
construcción de la métrica** (ventanas que se solapan con su propio
resultado, normalización contra un máximo que nunca se toca, etc.). NO es
correcto cuando el rango elevado u observado es simplemente **el
desempeño real de la administración vigente** — en ese caso, recalibrar
borra la señal en vez de corregir un defecto de medición. La diferencia se
verifica con un benchmark externo e independiente (otra fuente, otro
período, otro gobierno), no solo con la propia serie del indicador.

## Opciones consideradas

### Mantener la recalibración de ADR-0058 (dejar 1,5/2,0/3,0/4,5)

Rechazada. Verificado contra ACIJ que el corte de 0,3 corresponde a la
práctica histórica real (2011-2024, cuatro presidencias), no a un número
arbitrario. Subir el techo a 1,5 le daría 100 puntos (el máximo) a un ratio
que es 5 veces peor que el promedio histórico — grade inflation, no
corrección metodológica.

### Punto medio: recalibrar solo el piso, mantener el techo en 0,3

Rechazada por ahora. No hay un benchmark externo que sugiera dónde debería
estar el piso "correcto"; ADR-0036 no documentó el fundamento original de
2,0 como corte del piso. Cambiar solo la mitad de la tabla sin un benchmark
que lo sostenga sería tan arbitrario como la recalibración que se revierte.
Queda abierto si en el futuro aparece un benchmark específico para el
extremo superior del ratio.

## Limitaciones

- El benchmark de ACIJ (0,325) es un promedio de cuatro presidencias con
  estilos de gobierno muy distintos entre 2011 y 2024, no un óptimo
  normativo ni un estándar internacional — es la mejor referencia externa
  disponible, no una verdad definitiva.
- Con las anclas originales, prácticamente toda la serie real reciente
  (32 meses, mínimo 1,176) queda en las dos bandas más bajas del puntaje
  (40 o 10) — es un resultado esperado y correcto dado el diagnóstico, no
  un defecto a corregir: refleja que la dependencia del decreto de esta
  gestión está muy por encima de la práctica histórica, que es exactamente
  lo que el indicador debe mostrar.

## Consecuencias

- `BANDAS_ITCP["ratio_dnu"]` vuelve a 0,3/0,7/1,2/2,0.
- El puntaje de `ratio_dnu` para el valor vigente (2,19) pasa de 73,3
  (con la recalibración de ADR-0058) a un puntaje bajo, consistente con
  estar muy por encima del benchmark histórico — la dimensión
  `poder_legislativo` y el ITCP se regeneran en la misma corrida scoped.
- Este ADR deja un criterio explícito y reusable para futuras
  recalibraciones de anclas: distinguir defecto estructural (recalibrar)
  de desempeño real capturado por la métrica (no recalibrar), verificado
  contra un benchmark externo independiente de la propia serie.
- `tests/test_itcp.py::test_banda_low_exclusivo_high_inclusivo` vuelve a
  usar 0,3/0,30001 como en el estado previo a ADR-0058.
