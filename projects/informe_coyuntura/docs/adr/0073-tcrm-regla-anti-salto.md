# ADR-0073 — El TCRM alto por salto cambiario deja de puntuar como competitividad

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón macro · ITCM · dimensión Competitividad externa · `tcrm` |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | ADR-0056 (ajuste automático del saldo por contracción, del que esta regla copia la forma) · ADR-0021 (puntaje interpolado) |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 5 |

## Contexto

Las bandas del TCRM miran **solo el nivel**: por encima de 110 puntúan 100, el
máximo de competitividad externa. La auditoría señaló que eso premia igual dos
situaciones opuestas —una depreciación real gradual y sostenida, y un salto
cambiario cuyo traspaso a precios todavía no ocurrió— cuando la segunda no es
competitividad ganada sino una posición transitoria.

El caso no es hipotético, está en la propia serie:

| mes | ITCRM | var. m/m | puntaje que daba la banda |
|---|---|---|---|
| nov-2023 | 83,2 | — | 45,5 |
| **dic-2023** | **124,9** | **+50,1%** | **100,0** |
| ene-2024 | 132,8 | +6,3% | 100,0 |
| feb-2024 | 115,8 | −12,8% | 100,0 |
| mar-2024 | 105,9 | −8,5% | 89,0 |
| abr-2024 | 97,0 | −8,4% | 71,2 |

La devaluación de diciembre de 2023 le dio al índice **tres meses de puntaje
perfecto en competitividad externa**. Cuatro meses después el TCRM estaba en
97,0 y la ganancia se había evaporado entera: el salto se lo comió la
inflación, exactamente como cabía esperar. El índice registró una mejora
máxima donde había un desequilibrio sin resolver.

## Decisión

Entra una regla automática que **descuenta el puntaje de banda cuando el nivel
alto se alcanzó por un salto**, no por depreciación gradual.

### Medida de abruptez

El **máximo de las variaciones mensuales de los últimos tres meses**
(`salto_3m`), no la variación del mes corriente. La ventana es indispensable:
en ene-2024 el TCRM seguía en 132,8 *por el salto de diciembre*, pero la
variación de ese mes era apenas +6,3% — mirando el mes suelto, el índice habría
vuelto a puntuar 100 al mes siguiente del salto.

### Umbrales

Calibrados contra los dos casos reales del período, que acotan el umbral por
arriba y por abajo:

- **jul-2025: +6,6% m/m**, tras ampliarse la banda cambiaria. El TCRM pasó de
  86,1 a 99,1 en tres meses y **se sostuvo**. Es una corrección genuina y la
  regla no debe tocarla.
- **dic-2023: +50,1% m/m**, que se revirtió por completo en cuatro meses.

El umbral se fija en **8% m/m** —arriba del caso benigno más fuerte, muy por
debajo del salto— y la saturación en **25%**.

### Forma del descuento

Interpolada, sin acantilado, calcando ADR-0056:

```
frac    = (salto_3m − 8) / (25 − 8),  acotado a [0, 1]
puntaje = puntaje_banda − frac × (puntaje_banda − 55)
```

El **piso de 55** queda apenas por debajo de los 60 puntos de la banda
"moderadamente depreciado": un salto cambiario no se lee como buena
competitividad ni como catástrofe, se lee como una posición todavía sin
resolver. La regla no opina si la banda ya puntúa en el piso o por debajo (un
salto sobre un TCRM apreciado no tiene nada que descontar).

## Consecuencias

Replicada sobre los 31 meses de serie disponible, la regla se activa en
**exactamente tres**: dic-2023, ene-2024 y feb-2024, los del salto, bajando el
puntaje de 100 a 55 en los tres. **Ningún otro mes se mueve** — incluida toda
la recuperación de 2025 y el valor vigente (85,0 en jun-2026, puntaje 47,5, muy
por debajo del piso de la regla).

El ITCM publicado **no cambia hoy**: la regla es retroactivamente correctiva y
prospectivamente protectora, no un ajuste al valor corriente.

## Limitaciones declaradas

- La regla corre sobre la **ficha viva**, no sobre la serie reconstruida que
  usa `validacion_externa.py` — igual que el ajuste automático del saldo
  (ADR-0056), que tampoco entra en la reconstrucción. Las correlaciones
  externas del ITCM siguen calculándose sobre puntajes de banda sin ajustar.
- El umbral está calibrado contra un único salto observado. Una devaluación
  gradual pero sostenida —varios meses seguidos de +7%— pasaría por debajo del
  radar sin activar la regla, aunque acumule un salto comparable.
- La regla penaliza el salto pero **no premia** su ausencia: un TCRM alto
  alcanzado gradualmente sigue puntuando lo que dice la banda, sin bonus.
