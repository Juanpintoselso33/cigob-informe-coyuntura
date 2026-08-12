---
madr: 4
id: '0054'
estado: 'superado'
nota_estado: 'Superado por ADR-0055'
fecha: 2026-07-13
cinturon: 'macro'
relacionado: ['0009', '0012', '0021', '0030', '0053', '0192']
superado_por: ['0055']
ambito: 'Cinturón macro · ITCM · colector BCRA/INDEC · series históricas · validación externa · web metodológica'
---

# ADR-0054 — Dolarización de depósitos como indicador del ITCM

## Contexto y planteo del problema

La auditoría documentada en ADR-0053 rechazó reemplazar el M3 privado en pesos
del IDM por un M3 ampliado con depósitos en dólares. Esa sustitución mezclaba
liquidez en dos monedas con demanda transaccional exclusivamente en pesos,
incorporaba valuación cambiaria y quedaba afectada por ingresos regulatorios
extraordinarios como las Cuentas Especiales de Regularización de Activos (CERA).

La señal económica subyacente sí es relevante para el cinturón macro: la
preferencia relativa por depósitos en moneda extranjera frente a depósitos en
pesos. Para medirla sin alterar el constructo del IDM se requiere un indicador
independiente, con unidad, serie, bandas y ponderación propias.

## Opciones consideradas

- Reemplazar el IDM por M3 ampliado
- Publicar la señal sólo como contexto
- Medir una participación de depósitos en dólares sobre el total convertido a pesos
- Reconstruir depósitos USD mediante BCRA 104 / BCRA 84
- Corregir o recortar el período CERA
- Mantener los pesos 40/30/30 y agregar el indicador por fuera de la dimensión

## Decisión

### 1. Crear `dolarizacion_depositos` como indicador puntuable

Se incorpora **Dolarización de depósitos** como decimotercer indicador del ITCM
y cuarto componente de la dimensión `estabilidad_monetaria`.

Su valor mensual, expresado en puntos porcentuales, es:

```text
dolarización de depósitos = crecimiento i.a. de depósitos privados en USD
                           − crecimiento i.a. real de depósitos privados en pesos

crecimiento USD i.a. = (depósitos USD_t / depósitos USD_t-12 − 1) × 100

crecimiento pesos real i.a. =
  ((depósitos pesos_t / IPC_t) /
   (depósitos pesos_t-12 / IPC_t-12) − 1) × 100
```

Una brecha positiva indica que los depósitos en dólares crecen más que los
depósitos reales en pesos y, por lo tanto, mayor presión de dolarización. Una
brecha negativa indica que los depósitos reales en pesos crecen más.

El indicador complementa, pero no reemplaza:

- al **IDM**, que compara agregados monetarios exclusivamente en pesos;
- al **TCRM**, que mide competitividad cambiaria multilateral;
- a las **reservas**, que miden capacidad externa del BCRA.

### 2. Usar stocks por moneda en su unidad original

Las fuentes operativas son:

- **BCRA 108**: depósitos del sector privado no financiero en moneda extranjera,
  expresados en millones de USD;
- **BCRA 100**: depósitos del sector privado no financiero en moneda local,
  expresados en millones de ARS;
- **IPC nacional de INDEC**: deflactor del stock en pesos.

Los depósitos en moneda extranjera se miden directamente en USD para separar la
variación del stock de la mera valuación por tipo de cambio.

Las variables **BCRA 104** —depósitos privados en moneda extranjera expresados en
pesos— y **BCRA 84** —tipo de cambio de referencia— se admiten únicamente como
control aproximado de identidad:

```text
BCRA 104 ≈ BCRA 108 × BCRA 84
```

No son fuente operativa ni fallback. Si falta BCRA 108, el indicador no se
reconstruye mediante `104 / 84`.

### 3. Cerrar en el último mes común

Para cada mes se toma el último dato BCRA disponible. El período puntuado es el
último mes común entre depósitos en USD, depósitos en pesos e IPC, y el mismo
panel completo debe existir doce meses antes.

Este criterio evita combinar stocks monetarios parciales con un IPC aún no
cerrado y aplica el principio de borde irregular de ADR-0030.

### 4. Aplicar bandas calibradas antes del quiebre CERA

Las bandas iniciales se calibran sobre 72 observaciones mensuales de 2018–2023:

- mínimo: −77,5 pp;
- percentil 20: −25,2 pp;
- mediana: −0,6 pp;
- percentil 75: 11,1 pp;
- percentil 90: 18,5 pp;
- máximo: 22,9 pp.

Se adoptan las siguientes anclas, con límite inferior exclusivo, superior
inclusivo e interpolación lineal mediante el motor común de ADR-0021:

| Valor de la brecha | Puntaje de banda |
|---|---:|
| ≤ −25 pp | 100 |
| −25 a 0 pp | 85 |
| 0 a 10 pp | 60 |
| 10 a 20 pp | 35 |
| > 20 pp | 10 |

La dirección es deliberada: una brecha elevada concentra tensión y recibe un
puntaje bajo.

### 5. Conservar y declarar el quiebre regulatorio de CERA

La serie registra valores extraordinarios durante el ingreso de fondos a CERA,
entre septiembre de 2024 y agosto de 2025. Entre los puntos observados se
encuentran 138,88 pp en septiembre, 165,43 pp en octubre y 135,80 pp en noviembre
de 2024.

Esos valores:

- permanecen en la serie publicada;
- no se corrigen, empalman, winsorizan ni neutralizan;
- no se interpretan como una presión monetaria ordinaria;
- se excluyen únicamente de futuras calibraciones o recalibraciones.

No existe una serie oficial suficientemente desagregada de CERA que permita
restar el efecto de manera reproducible sin introducir supuestos discrecionales.

### 6. Redistribuir estabilidad monetaria a 40/25/25/10

La dimensión conserva su peso de 26% dentro del ITCM. Su composición interna
pasa a:

| Indicador | Peso interno | Peso nominal efectivo en el ITCM |
|---|---:|---:|
| IPC mensual | 40% | 10,4% |
| Expectativa de inflación REM | 25% | 6,5% |
| IDM | 25% | 6,5% |
| Dolarización de depósitos | 10% | 2,6% |

La sensibilidad directa máxima del nuevo indicador entre sus anclas extremas es:

```text
(100 − 10) × 0,026 = 2,34 puntos del ITCM
```

Con los insumos frescos de mayo de 2026, el indicador registra:

```text
crecimiento de depósitos USD:       +27,76% i.a.
crecimiento real de depósitos pesos: −1,31% i.a.
brecha de dolarización:              +29,07 pp
puntaje aplicado:                     10/100
```

La dimensión de estabilidad monetaria queda en 63,4/100 y el ITCM en 57,5/100.
El contrafactual con los mismos insumos y puntajes, pero con la composición
anterior 40/30/30 y sin el nuevo indicador, es 59,0/100. El efecto aritmético de
la decisión en esa foto es, por lo tanto, **−1,5 puntos del ITCM**.

### 7. Publicar backfill y tratar faltantes sin imputación

La serie auditable se reconstruye desde diciembre de 2023 y su último punto debe
coincidir con el valor titular. La reconstrucción histórica de la validación
externa incorpora el nuevo componente mediante el mismo motor `calcular_itcm()`;
no existe una fórmula paralela del índice.

Ante un fallo de fuente:

1. el colector reutiliza el último valor válido del cache macro y lo marca como
   desactualizado;
2. si nunca existió un valor válido, omite el indicador;
3. el motor renormaliza los pesos disponibles;
4. nunca se imputa cero ni se reconstruye el stock en USD desde valores en pesos.

El CSV de series macro se versiona también en el commit nocturno. De ese modo, el
backfill que alimenta el snapshot público conserva su fuente auditable entre
corridas del pipeline.

### Consecuencias

- El ITCM pasa de 12 a 13 indicadores puntuables; el colector macro conserva cuatro
  insumos internos ocultos adicionales.
- El IDM mantiene su fórmula pesos/pesos y deja de cargar con una señal económica
  conceptualmente distinta.
- La preferencia relativa por depósitos en dólares queda medida sin contaminación
  directa de valuación cambiaria.
- La dimensión de estabilidad monetaria gana una cuarta señal con peso acotado de
  2,6% efectivo del ITCM.
- La card y la ficha publican valor, componentes, fórmula, puntaje, peso interno,
  peso efectivo y aporte aritmético.
- La serie conserva el episodio CERA como quiebre visible y auditable.
- El último mes publicado queda condicionado a la disponibilidad conjunta de BCRA
  e IPC, por lo que puede rezagarse respecto de otros indicadores mensuales.
- El pipeline nocturno versiona `output/series/*.csv`, evitando que el snapshot y
  su fuente histórica queden desincronizados.
- La decisión complementa ADR-0009 y ADR-0053; no los reemplaza.

## Pros y contras de las opciones

### Reemplazar el IDM por M3 ampliado

Rechazada por ADR-0053. Cambia el constructo, mezcla monedas e incorpora
valuación cambiaria dentro de una comparación concebida para agregados en pesos.

### Publicar la señal sólo como contexto

Rechazada. La regla institucional vigente no publica cards que no puntúan. La
señal tiene definición, serie y calibración suficientes para integrarse al ITCM
con peso acotado.

### Medir una participación de depósitos en dólares sobre el total convertido a pesos

Rechazada. Reintroduce el tipo de cambio en numerador y denominador, mezcla
variaciones de cantidad con valuación y vuelve más difícil interpretar el signo.

### Reconstruir depósitos USD mediante BCRA 104 / BCRA 84

Rechazada como fuente y fallback. La medición directa en USD existe y evita
propagar diferencias de cierre, valuación o perímetro entre series.

### Corregir o recortar el período CERA

Rechazada. No hay una resta oficial reproducible; corregir, empalmar o winsorizar
ocultaría un cambio real del stock. Se conserva el dato y se declara el quiebre.

### Mantener los pesos 40/30/30 y agregar el indicador por fuera de la dimensión

Rechazada. Los pesos internos deben sumar 100% y todo indicador puntuable debe
tener una incidencia explícita y reconciliable.

## Más información

### Precedentes directos

ADR-0009 (IDM y TCRM) · ADR-0012 (backfill) · ADR-0021 (interpolación) · ADR-0030 (último mes común) · ADR-0053 (auditoría de agregados monetarios)
