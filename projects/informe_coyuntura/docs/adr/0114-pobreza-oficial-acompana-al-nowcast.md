---
madr: 4
id: '0114'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
indicadores: [pobreza_nowcast, pobreza_indec]
continua: ['0113']
ambito: 'ITVC · `pobreza_nowcast` · serie acompañante `pobreza_indec`'
---

# ADR-0114 — La pobreza oficial acompaña al nowcast en el mismo gráfico

| **Continúa** | ADR-0113 (alta del nowcast como contexto) |
| **Sigue el patrón de** | ADR-0077 (`ipc_nucleo`) · ADR-0080 (`cuenta_corriente`) |

## Contexto y planteo del problema

ADR-0113 incorporó el Nowcast de Pobreza de la UTDT y dejó anotado lo que le
falta: **historia**. Sus informes publicados arrancan en 2025, de modo que la
card muestra el pulso mensual sin el arco que le da sentido.

La tasa **oficial del INDEC** tiene exactamente lo que al nowcast le falta —23
años de serie, la referencia autorizada— y exactamente lo que al nowcast le
sobra: llega dos veces por año y con rezago.

Abrir dos cards de lo mismo habría duplicado el tema en el tablero. El proyecto
ya tiene un patrón para este caso: **serie acompañante**, la misma solución de
ADR-0077 (el IPC núcleo junto al general) y ADR-0080 (la cuenta corriente junto
al saldo comercial).

## Opciones consideradas

- **Publicar `pobreza_indec` como serie acompañante** de `pobreza_nowcast`: una sola card, dos curvas en el modal — elegida. La estimación mensual da el pulso y la medición oficial la referencia.
- **Una card separada para cada una** — descartada. Ninguna de las dos puntúa.

## Decisión

`pobreza_indec` (`64.2_POBLACION_NUA_0_0_34_74`, INDEC EPH continua, total de
aglomerados urbanos, semestral desde 2003) se publica como **serie acompañante**
de `pobreza_nowcast`. Una sola card, dos curvas en el modal: la estimación
mensual da el pulso y la medición oficial la referencia.

No puntúa ninguna de las dos —el nowcast es contexto desde ADR-0113— y la
oficial ni siquiera tiene card propia.

La API entrega la proporción (0,282); se publica en puntos porcentuales para que
las dos curvas compartan unidad en el mismo eje.

### Consecuencias

- La serie oficial se ordena ascendente en el colector: la API la devuelve del
  más nuevo al más viejo y el resto del proyecto asume el orden contrario.
- El nowcast aporta 17 puntos mensuales (2025-01 → 2026-06) y el oficial 28
  semestrales (2003-07 → 2026-01).
- Que las dos curvas no coincidan exactamente es esperable y es parte de lo que
  la card muestra: una proyecta un semestre móvil, la otra mide semestres
  calendario cerrados.

## Más información

### El recorte de la ventana la habría vaciado de sentido

Los gráficos del informe recortan las series a diciembre de 2023, que es la
ventana del mandato. Aplicado a una serie **semestral**, ese recorte se lleva
puestos los puntos previos y deja el primero en enero de 2024 — es decir,
**elimina julio de 2023 (40,1%), la última lectura antes del traspaso**, que es
justamente la referencia contra la que se lee todo lo demás.

`pobreza_indec` se suma entonces a las series que se muestran completas, junto a
`protestas_caba`, que está ahí por la misma razón declarada: su valor está en
comparar contra la era previa.

El arco que ahora se ve:

| | |
|---|---|
| jul-2023 (previo al traspaso) | **40,1%** |
| jul-2024 (pico) | **52,9%** |
| ene-2026 (último oficial) | **28,2%** |
| ene-jun 2026 (nowcast) | **31,6%** |
