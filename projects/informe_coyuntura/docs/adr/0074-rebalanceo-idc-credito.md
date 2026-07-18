# ADR-0074 — El crédito otorgado deja de pesar un tercio de la capacidad de prestar

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón macro · ITCM · dimensión Capacidad y costo del financiamiento · `idc` · `credito_privado` |
| **Fecha** | 2026-07-18 |
| **Precedentes directos** | ADR-0022 (crédito privado real como señal no redundante) · ADR-0028 (construcción del IdC) · ADR-0071 (entrada del costo de financiamiento, que dejó este rebalanceo explícitamente pendiente) |
| **Origen** | Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 4 |

## Contexto

La dimensión repartía así sus cuatro componentes: reservas 34%, **IdC 30%**,
costo del financiamiento 25%, **crédito privado 11%**. La capacidad de prestar
pesaba **2,7 veces** el crédito efectivamente otorgado.

El argumento para ese reparto sería que el IdC anticipa al crédito: mediría la
condición que después se realiza. Pero **la propia ficha del IdC declara lo
contrario**, y con la validación hecha:

> "Sin pretensión predictiva, y con la validación en contra documentada: sobre
> más de cien meses, el IdC no anticipa el crédito futuro. Es un descriptor del
> estado de las condiciones de fondeo, no un pronóstico."

Si el IdC no adelanta al crédito, no hay jerarquía que justifique el 2,7×: son
dos miradas del mismo fenómeno —el financiamiento bancario al sector privado—,
una por el lado de la condición y otra por el del resultado, sin evidencia de
que una mande sobre la otra.

## Decisión

Repartir el 41% conjunto casi en partes iguales:

| componente | antes | ahora |
|---|---|---|
| reservas_bcra | 34% | 34% |
| costo_financiamiento_tesoro | 25% | 25% |
| **idc** | **30%** | **21%** |
| **credito_privado** | **11%** | **20%** |

Reservas y costo quedan intactos: la decisión es entre esos dos componentes,
no una redistribución de toda la dimensión.

## Consecuencias

**Hoy no mueve nada: +0,014 puntos de ITCM.** El IdC puntúa 52,0 y el crédito
53,0 — con los dos casi empatados, el reparto entre ellos es indiferente. El
cambio no se hace para mover el número corriente.

**Importa cuando divergen, y divergieron mucho.** Sobre los 31 meses de serie
comparable:

| mes | puntaje IdC | puntaje crédito | brecha | efecto del nuevo reparto |
|---|---|---|---|---|
| dic-2024 | 54,7 | 100,0 | 45,3 | ITCM +0,65 |
| nov-2025 | 59,0 | 100,0 | 41,0 | ITCM +0,59 |
| oct-2025 | 59,0 | 100,0 | 41,0 | ITCM +0,59 |
| dic-2025 | 56,7 | 95,8 | 39,1 | ITCM +0,56 |

El sesgo tenía una dirección consistente: durante todo el ciclo de expansión
del crédito de 2024-2025 —crédito en el techo de su banda mientras las
condiciones de fondeo se mantenían en torno a lo típico— el reparto viejo
**subrepresentaba sistemáticamente el hecho realizado** y sobrerrepresentaba la
condición. El índice leía menos expansión crediticia de la que hubo.

## Limitaciones declaradas

- Los dos indicadores siguen midiendo el mismo fenómeno desde ángulos
  distintos: su correlación no es cero y el 41% conjunto tiene algo de
  redundancia, que este ADR reparte mejor pero no elimina.
- El reparto casi parejo (21/20) no es una estimación: es la ausencia de razón
  para preferir uno. Si aparece evidencia de que alguno de los dos anticipa al
  otro, el reparto debería reflejarla.
