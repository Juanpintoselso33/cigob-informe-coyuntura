---
madr: 4
id: '0027'
estado: 'aceptado'
nota_estado: 'RESUELTO el 2026-07-04 — el editor eligió la opción (a); implementada en el [ADR-0028](0028-idc-z-scores.md)'
fecha: 2026-07-04
cinturon: 'macro'
indicadores: [idc]
ambito: 'Dimensión Capacidad de financiamiento · indicador `idc` (ADR-0004, ADR-0022)'
---

# ADR-0027 — Auditoría adversarial del IdC: hallazgos y opciones de rediseño

| **Disparador** | Barrido uno-por-uno de macro (indicador 3/12): el editor pidió revisión adversarial contra la literatura de índices comparables |

## Contexto y planteo del problema

El IdC (ADR-0004, doc `260626 aportes`) puntúa el 40% de la dimensión de
financiamiento (6,4% del ITCM):

```
IdC = 0,30·Precio + 0,40·Volumen + 0,30·Asignación   (~1,0)
Precio     = 1 + (TEM BADLAR − IPC m/m)
Volumen    = (dep_t / dep_{t−1}) / (1 + IPC m/m)
Asignación = (1 − R_t) / (1 − R_{t−1}),  R = préstamos/depósitos privados
```

Se lo contrastó con los índices de condiciones financieras de referencia:
**Chicago Fed NFCI** (105 indicadores, modelo de factores dinámicos, z-scores,
pesos estimados, ajuste estacional), **Goldman Sachs FCI** (5 variables, pesos
por impacto en PIB vía modelo macro), **Bloomberg FCI** (promedio de z-scores),
**FCI-G de la Fed** (pesos por contribución al crecimiento esperado, con rezagos)
y el uso del concepto "capacidad prestable" del propio BCRA (regulatorio, no
compuesto).

### Hallazgos de la auditoría (04-jul-2026)

1. **Leyenda pública contradecía el signo de la fórmula** — decía "si el dinero
   está barato…" cuando `Precio` premia la tasa real POSITIVA (incentivo del
   depositante, no costo del deudor). **CORREGIDO** el 04-jul-2026 (leyenda
   reescrita con los signos reales; llave de asignación pasa de
   "préstamos/depósitos" a "holgura para prestar").
2. **Doble conteo de los depósitos (~70% efectivo)**: entran en Volumen (40%) y
   en el denominador de R en Asignación (30%). Un salto de depósitos mueve ambos
   a la vez (jun-2026: +4,4% real explicó el 1,044 de Volumen y buena parte del
   1,149 de Asignación). Los componentes no son ortogonales.
3. **Asignación mal condicionada**: `(1−R)/(1−R_prev)` explota cuando R→1 y se
   hace NEGATIVA si R>1 (posible: los bancos también se fondean con ON y líneas
   externas). Con R≈0,9, 1 punto de R mueve el componente ~10%. Ningún índice de
   referencia usa una razón cuyo denominador puede cruzar cero.
4. **Premia la desaceleración del crédito**: la holgura crece cuando se presta
   MENOS en relación a los depósitos. En jun-2026 el IdC marcó 100 por el mismo
   hecho que hizo caer a `credito_privado` (13,8→8,6% real) — dos indicadores de
   la misma dimensión en sentidos opuestos por el mismo evento (pesos 40 y 15).
5. **Mide derivada, no estado**: compara t contra t−1; los FCI de referencia
   miden el NIVEL contra la distribución histórica (z-scores). Un sistema en el
   piso que rebota 1% marca "verde 100".
6. **Sin estandarización de varianzas**: Precio se mueve ±0,5%, Asignación ±15%;
   con pesos fijos sobre componentes sin escalar, el más volátil domina de facto.
7. **Sin ajuste estacional**: los depósitos tienen estacionalidad fuerte
   (aguinaldos jun/dic, liquidación gruesa) y los ratios m/m la heredan — mismo
   problema que motivó el rebase de motos (ADR-0024), acá sin tratamiento.
8. **Deflactor rezagado sin declarar**: el valor "al 30-jun" deflacta stocks de
   junio con el IPC de mayo; en desinflación el sesgo es sistemático.
9. **Pesos 30/40/30 sin justificación empírica** (mitigante: el Monte Carlo del
   ADR-0019 perturba pesos ±20%).
10. **Anclas sin distribución histórica** (¿qué percentil es 1,02?) y **sin
    validación externa propia** (el ITCM agregado valida contra riesgo país; el
    IdC no demostró anticipar nada observable).

**Mitigantes**: fórmula única compartida entre indicador vivo y serie histórica;
datos 100% oficiales diarios (BCRA var. 7/100/117 + IPC); puntaje interpolado;
peso efectivo bajo (6,4% del ITCM); volatilidad capturada por la simulación de
robustez publicada.

## Opciones consideradas

### Opciones de rediseño (a decidir con CIGOB)

- **(a) Rediseño tipo FCI simplificado** — 3 z-scores de NIVEL contra la propia
  historia: tasa real (nivel), crédito privado real (tendencia interanual, ya
  colectado por ADR-0022) y ratio de liquidez/holgura (nivel de 1−R, no su
  ratio mensual). Estandarizados y promediados; resuelve 2–7 de un golpe.
  Costo: rompe la letra del doc `260626 aportes`; requiere serie larga para las
  medias (el var. 100/117 del BCRA da 10+ años).
- **(b) Parche mínimo** — desestacionalizar Volumen (interanual en vez de m/m),
  reemplazar Asignación por el crédito real i.a. que ya existe (fusiona con
  `credito_privado` y elimina el doble conteo) y declarar el deflactor rezagado
  en la ficha. Menos ruptura, resuelve 2, 4 y 7 parcialmente.
- **(c) Degradar a contexto** — el IdC deja de puntuar (financiamiento queda
  reservas 55 / crédito real 45, renormalizado) y se publica como semáforo de
  contexto con la advertencia de que es un pulso mensual direccional. Honesto y
  barato; pierde la señal de fondeo en el índice.
- **(d) Statu quo documentado** — se mantiene con la leyenda corregida (hecho) y
  esta ADR como descargo público de sus límites. Riesgo: no resiste una
  auditoría metodológica externa si el informe gana visibilidad.

## Decisión

### Consecuencias mientras esté abierto

- La leyenda y las llaves de la fórmula ya no contradicen el cálculo (hallazgo 1
  cerrado).
- El IdC sigue puntuando 40% de financiamiento con las anclas del ADR-0004; su
  volatilidad mensual queda a la vista en la serie del modal (32 puntos).
- Cualquier rediseño debe versionarse como nueva ADR que superseda al ADR-0004 y
  recalibrar las anclas de `itcm.py`.
