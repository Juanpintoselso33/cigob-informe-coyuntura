---
madr: 4
id: '0057'
estado: 'aceptado'
fecha: 2026-07-15
cinturon: 'macro'
indicadores: [presion_dolarizacion]
relacionado: ['0055', '0083']
ambito: 'Cinturón macro · ITCM · `presion_dolarizacion` · régimen abierto (desde abr-2025)'
---

# ADR-0057 — Canal informal (dólar cripto) en la presión de dolarización

## Contexto y planteo del problema

ADR-0055 mide la presión de dolarización de carteras con un observable
distinto por régimen cambiario: brecha CCL/A3500 antes de abril de 2025
(régimen restringido), y compras netas de moneda extranjera de Personas
Humanas sobre M2 privado transaccional (convertido a USD) desde abril de 2025
(régimen abierto).

El numerador del régimen abierto es **exclusivamente formal**: proviene del
concepto "03- Compra-venta de billetes y divisas sin fines específicos" del
anexo estadístico del Mercado de Cambios del BCRA — compras declaradas y
bancarizadas vía MULC. Ningún indicador del proyecto capta dolarización por
fuera de ese circuito (verificado: no hay proxy de blue, cuevas, atesoramiento
en efectivo ni cripto en `scripts/` ni en `docs/adr/` previos a este). Además,
el denominador del régimen abierto (M2 privado transaccional, un agregado en
pesos) hace que la métrica se mueva en parte por la dinámica del circulante y
los depósitos transaccionales en pesos, no solo por cuánto se compra en
dólares.

Verificación empírica (ArgentinaDatos, cotización "cripto" — USDT vía
exchanges locales, serie diaria desde 2023-02-07, misma fuente ya usada para
el CCL) contra el tipo de cambio mayorista/A3500:

| Período | Brecha cripto/mayorista (promedio mensual) |
|---|---:|
| 2023 (cepo estricto) | 90%–174% |
| 2024 (cepo, aflojando) | 12%–52% |
| ene–mar 2025 (pre-apertura) | 15%–20% |
| may–ago 2025 (apertura reciente) | 1,5%–3,1% |
| sep 2025–jul 2026 (régimen abierto sostenido) | 3,8%–6,7% |

El dato clave: incluso con el cepo minorista levantado y con `Blue≈0%` frente
al oficial (`scripts/gestion.py`, comentario de `cepo_mulc`), el dólar cripto
sostiene una brecha de 4-7% contra el mayorista desde septiembre de 2025, con
tendencia ascendente. Esa brecha no depende de ninguna restricción de acceso
—hoy no la hay— sino de motivos que persisten con o sin cepo (evitar la
retención de Ganancias/Bienes Personales que aplica a la compra bancaria,
anonimato, practicidad). Es una demanda de dolarización real que el canal
formal, por construcción, no puede ver.

## Opciones consideradas

- Usar la brecha CCL o blue en vez de cripto para el canal informal
- Reemplazar el canal formal por el informal en vez de combinarlos
- Ponderación 50/50 o usar el máximo de las dos señales
- Sumar el canal informal también al régimen restringido (pre-abril-2025)

## Decisión

### 1. Agregar un segundo observable, exclusivo del régimen abierto

Se calcula `brecha_informal` = brecha entre el dólar cripto (ArgentinaDatos,
promedio mensual de `venta`) y el A3500 fin de mes (`tc_a3500`, el mismo dato
que ya usa el denominador formal), sobre la MISMA ventana que el flujo formal
—incluida la transición de 1 y 2 meses de abril/mayo de 2025—, para no
introducir una segunda convención de suavizado:

```text
brecha_informal_t = 100 × (cripto_prom(ventana) / A3500_prom(ventana) − 1)
```

`brecha_informal` se traduce a `presion_informal` (0-100) con las mismas
anclas que ya tiene `ANCLAS_FLUJO` (0%→0, 3%→25, 6%→50, 10%→75, 15%→100): no
es una calibración nueva sin respaldo, es la reutilización deliberada de una
tabla ya aceptada, justificada porque el rango observado del canal informal
desde mayo de 2025 (1,5%–19,5%, con el grueso de los meses en 3-7%) es del
mismo orden de magnitud.

El régimen restringido (pre-abril-2025) no se toca: el CCL/A3500 ya captura
ahí la presión reprimida razonablemente bien, y es un período cerrado.

### 2. Combinar formal e informal con un promedio ponderado 70/30

```text
presion = 0,7 × presion_formal + 0,3 × presion_informal
```

El canal formal conserva más peso porque es flujo efectivamente transaccionado
(una cantidad real, no un proxy de precio); el informal aporta una señal
complementaria que hoy el formal no puede ver. El mismo patrón de "traducir
cada observable a una escala latente común y combinar" ya lo usa ADR-0055
entre regímenes (secuencialmente) y `cohesion_bloque` entre cámaras
(ADR-0048, compuesto 65/35); acá se aplica de forma simultánea a dos señales
del mismo mes.

### 3. Degradar a 100% formal si falta el dato informal, sin omitir el mes

Si el dólar cripto no cubre los tres meses de la ventana (fuente caída, mes
sin publicar), `presion_informal` queda `None` y `presion = presion_formal`
—el mes se sigue publicando con la métrica formal sola, igual que antes de
este ADR. El canal informal es complementario, no obligatorio: un fallo en
`fetch_cripto_mensual` no debe tumbar el indicador entero, que descansa en
las cuatro fuentes ya validadas por ADR-0055.

### 4. Exponer la composición para transparencia

`presion_formal`, `presion_informal` y `brecha_informal` quedan expuestos en
la fila de la serie y en el indicador publicado (`macro.fetch_presion_dolarizacion`),
igual que `saldo_comercial_12m` expone su composición expo/impo — para que
la ficha y cualquier auditoría del snapshot puedan mostrar de dónde sale el
número, no solo el resultado combinado.

### Consecuencias

- `presion_dolarizacion` dentro del régimen abierto deja de ser 100% formal:
  ahora es 70% formal / 30% informal cuando hay dato de dólar cripto para la
  ventana completa, y 100% formal cuando no lo hay.
- El régimen restringido (pre-abril-2025) no cambia.
- Nuevos campos de transparencia (`presion_formal`, `presion_informal`,
  `brecha_informal`) en la serie y en el indicador publicado.
- La serie histórica del régimen abierto (mayo-2025 en adelante) cambia al
  regenerarse el pipeline, porque ahora incorpora el canal informal donde hay
  dato; los resultados coyunturales y la validación externa deben provenir de
  esa regeneración, este ADR no fija cifras vigentes.
- ADR-0055 no queda superado: su estructura de dos regímenes y la fórmula del
  régimen restringido siguen vigentes tal cual; este ADR solo extiende el
  régimen abierto con un segundo componente.

## Pros y contras de las opciones

### Usar la brecha CCL o blue en vez de cripto para el canal informal

Rechazada. Post-apertura (abr-2025) el blue converge al oficial (`Blue≈0%`,
`gestion.py`) y el CCL ya es la base del régimen restringido — ninguno de los
dos aporta señal incremental hoy. El dólar cripto es el único observable con
brecha sostenida y no nula en el período que este ADR necesita cubrir.

### Reemplazar el canal formal por el informal en vez de combinarlos

Rechazada. El canal formal es la única medida de flujo EFECTIVAMENTE
transaccionado (cantidad real, no precio) y sigue siendo la señal más directa
de demanda de dólares. Descartarlo perdería esa información dura a cambio de
un proxy de precio.

### Ponderación 50/50 o usar el máximo de las dos señales

Consideradas y descartadas por el analista a favor de 70/30 (promedio
ponderado): el máximo sería más conservador (cualquier canal en alerta
dispara el indicador) pero no fue la opción elegida; queda documentado como
alternativa razonable si la calibración 70/30 no valida bien en el próximo
stress test.

### Sumar el canal informal también al régimen restringido (pre-abril-2025)

Rechazada. Es un período cerrado y ya resuelto por ADR-0055 con CCL/A3500;
además, en ese tramo la brecha cripto es tan extrema (90%-174% en 2023) que
introduce ruido de escala distinta sin aportar nada que el CCL no capture ya.

## Más información

### Precedentes directos

ADR-0055 (presión de dolarización por régimen, no supersedida — este ADR la extiende)

### Limitaciones

- ArgentinaDatos no es el organismo oficial del mercado cripto (no existe
  tal organismo); es una serie pública y reproducible, pero de un mercado sin
  regulación centralizada — el precio puede diferir entre exchanges.
- El peso 70/30 y las anclas reutilizadas de `ANCLAS_FLUJO` son juicio de
  calibración, no umbrales naturales; deben someterse al mismo stress test
  que el resto de las anclas de la Paramétrica (ADR-0019).
- El proxy no captura otros canales informales (efectivo fuera del sistema,
  atesoramiento físico, dolarización corporativa no declarada) — sigue siendo
  parcial, solo amplía la cobertura respecto del 100% formal anterior.
- La ventana de transición de abril/mayo de 2025 (1 y 2 meses) hereda la
  misma menor suavización que ya declaraba ADR-0055 para el flujo formal.
