---
madr: 4
id: '0427'
estado: 'aceptado'
fecha: 2026-11-12
cinturon: 'todos'
archivos: ['config.py', 'scripts/parametrica.py', 'scripts/itcm.py', 'scripts/itcg.py', 'scripts/itcp.py']
relacionado: ['0181', '0195', '0333']
ambito: 'Semáforo, estado de cada cinturón y alertas: cortes de tensión 2,5 / 5 / 7,5'
origen: 'Pedido de la dirección del Monitor, 12-nov-2026'
---

# ADR-0427 — Escala de tensión en cuatro tramos iguales: 2,5 / 5 / 7,5

## Contexto y planteo del problema

Desde ADR-0181 y ADR-0333 el semáforo y el estado de cada cinturón cortaban
la tensión 0-10 en 4 / 6 / 8 (índice 60 / 40 / 20). El verde ocupaba 40% de
la escala y el rojo 20%. La dirección del Monitor pidió una escala más
equilibrada, con cuatro tramos iguales.

Simulación previa con los cierres de junio a octubre de 2026: el general pasa
de verde a amarillo todos los meses (3,8 a 4,0); impacto social de amarillo a
naranja; político de verde a amarillo; macro sigue amarillo y gestión verde.
La simulación es anterior a ADR-0426, que sube el índice político.

## Decisión

Se mueve todo junto, para que color y estado sigan atados (ADR-0333):

| Color | Tensión | Índice 0-100 | Estado |
|---|---|---|---|
| Verde | hasta 2,5 | 75 o más | estable |
| Amarillo | 2,5 a 5 | 50 a 75 | en tensión |
| Naranja | 5 a 7,5 | 25 a 50 | tensionado |
| Rojo | más de 7,5 | menos de 25 | tensionado |

- `config.UMBRALES`: `ESTABLE_MAX` 4 → 2,5 y `EN_TENSION_MAX` 6 → 5. De ahí
  salen el estado, la alerta multicinturón (dos o más tensionados, ahora desde
  5) y el riesgo dominante.
- `parametrica.CORTES_SEMAFORO`: el tercer corte pasa de 8 a 7,5.
- `BANDAS_INTERPRETACION` de los índices macroeconómico, de gestión y político
  se alinean con los cortes nuevos: 25 / 50 / 75, y 87,5 para separar
  «moderadamente aflojado» de «aflojado» dentro del verde.

La misma escala colorea los puntajes de cada indicador, así que las tarjetas
también se recolorean, salvo las que tienen cortes propios. Los meses
archivados se leen con el método vigente (ADR-0359) y también cambian.

### Consecuencias

- El índice de impacto social no se toca en sus bandas de lectura
  (deterioro / sin cambios / mejora alrededor de 100): con su fórmula de
  tensión, 5 − (índice − 100) × 0,2, los cortes nuevos caen en 112,5 / 100 /
  87,5, así que «sin cambios» contra 2023 queda en el borde entre amarillo y
  naranja. Las palabras y el color de ese índice ya no coinciden en todos los
  tramos; queda a revisar.
- Las alertas se vuelven más sensibles: un cinturón entre 5 y 6 pasa a contar
  como tensionado.
