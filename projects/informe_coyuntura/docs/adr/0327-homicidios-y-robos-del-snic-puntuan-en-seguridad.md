---
madr: 4
id: '0327'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'vida'
indicadores: [inseguridad, tasa_homicidios, tasa_robos]
archivos: ['scripts/vida_cotidiana/collectors/snic.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/validacion_externa.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'config.py', 'data/vida/snic_serie.json']
relacionado: ['0032', '0108', '0115', '0324', '0325']
ambito: 'ITCIS · dimensión de seguridad · homicidios y robos del SNIC pasan de contraste a indicador propio'
origen: 'Juan, 16-sep-2026: revierte ADR-0324/0325 — "los dos tienen que ser indicadores que puntúen, con su card y su peso"'
---

# ADR-0327 — Homicidios y robos del SNIC entran a puntuar en la dimensión de seguridad

## Contexto y planteo del problema

ADR-0324/0325 (15-sep-2026) restituyeron el desglose de delitos del SNIC por
NOMBRE en `tipos_principales`, pero lo dejaron como contraste dentro de la
ficha de `inseguridad`: homicidios y robos se bajan del CSV oficial y no
puntúan. El argumento explícito de esa decisión fue que "el SNIC es anual, no
puede puntuar en un tablero mensual".

Ese argumento es falso, y está medido contra el propio snapshot vigente al
16-sep-2026:

| indicador | cinturón | rezago del dato |
|---|---|---|
| `velocidad_resolucion` | política | 244 días |
| `iaf_transferencias` | política | 244 días |
| `protocolo_antipiquetes` | gestión | 244 días |
| `informalidad` | impacto social | 243 días |
| `subocupacion_demandante` | impacto social | 243 días |

Cinco indicadores puntúan hoy con 243-244 días de rezago del dato. El rezago
se **declara y se gestiona** con `MAX_DIAS` en `config.py` (ADR pendiente de
cita: ver el bloque "G2" de ese archivo), no descalifica a una fuente de
integrar un índice.

Además, el CSV oficial (`snic-pais.csv`) trae una columna `tasa_hechos` —la
tasa cada 100.000 habitantes YA CALCULADA por la fuente— con series completas
de **26 años (2000-2025)** para Homicidios dolosos y para Robos (excluye los
agravados por el resultado de lesiones y/o muertes). No hace falta reconstruir
una tasa con población propia: sería duplicar un cálculo que la fuente ya
publica y que es el que se cita en cualquier lectura pública de seguridad.

## Factores de decisión

- El rezago anual no descalifica (tabla de arriba): se gestiona con
  `MAX_DIAS`, igual que las otras cinco fuentes anuales/trimestrales del
  snapshot.
- La `tasa_hechos` del SNIC es un dato de 26 años, con pico y mínimo propios:
  no hace falta inventar un ancla externa ni una convención — el ancla sale de
  la propia serie (ADR-0327 no depende de referencias regionales/históricas
  traídas de afuera, a diferencia de lo que este mismo encargo consideró al
  principio y luego se descartó por innecesario).
- Homicidios y robos son señales de **calidad distinta** y no se pueden
  promediar entre sí sin perder información: el homicidio casi no tiene
  subregistro (hay un cuerpo); el robo depende de que la víctima denuncie.
  Entran como DOS componentes separados de la dimensión, no como un
  compuesto.
- El IVI (`inseguridad`, ADR-0032) y el SNIC son **complementarios, no
  redundantes**: el IVI es mensual y capta delito denunciado y no denunciado
  (cifra negra) pero no distingue TIPO de delito; el SNIC es anual, capta sólo
  lo denunciado, pero por tipo específico.
- Robos tiene una limitación de calidad propia, declarada y no resuelta: la
  tasa cae 22,4% de 2024 a 2025 (1.002,8 → 778,1) sin evento conocido que lo
  explique, mientras Hurtos cae en proporción similar (−17,4%) y Robos
  agravados por el resultado de lesiones/muertes SUBE 45,5% el mismo año — un
  patrón inconsistente con una baja real y pareja del delito violento, y
  compatible con reporte incompleto de alguna jurisdicción. No se pudo
  confirmar ni descartar contra ningún informe metodológico público del SNIC.

## Opciones consideradas

1. Dos indicadores nuevos (`tasa_homicidios`, `tasa_robos`), cada uno con su
   card, ficha y peso propio dentro de la dimensión de seguridad.
2. Un único indicador compuesto (promedio de las dos tasas).
3. Sólo homicidios como indicador nuevo, robos se queda de contraste.
4. Mantener la decisión de ADR-0324/0325 (ninguno puntúa).

## Decisión

**Opción 1.** Entran `tasa_homicidios` y `tasa_robos`, cada uno con su card,
ficha (ADR-0220) y peso propio, sin promediarse entre sí. La dimensión de
seguridad pasa de un componente a tres:

```
alta_proporcional(alta_proporcional({"inseguridad": 1.0}, "tasa_homicidios", 0.30),
                  "tasa_robos", 0.15)
→ inseguridad 0,595 · tasa_homicidios 0,255 · tasa_robos 0,150
```

El IVI conserva la mayoría (59,5%) por ser mensual y más fresco. Homicidios
pesa más que robos (25,5% contra 15%) porque es la medida sin subregistro del
desglose, y porque robos tiene la limitación de calidad de 2025 declarada
arriba. El peso NOMINAL de la dimensión (4,5%) no se toca — sigue siendo una
alta, no una recalibración.

Se descartó la Opción 2 porque promediar homicidios (sin subregistro) con
robos (con subregistro y una limitación de calidad propia) diluye la señal
limpia del primero con el ruido del segundo — el mismo problema que evitó
separar `consumo_carne_vacuna` de `consumo_carnes_otras` en ADR-0322. Se
descartó la Opción 3 porque los datos ya estaban: robos tiene la misma serie
de 26 años con `tasa_hechos` que homicidios, así que dejarlo afuera hubiera
sido arbitrario y no una limitación de la fuente. Se descarta la Opción 4
—mantener ADR-0324/0325— porque su argumento de fondo (el SNIC no puede
puntuar por ser anual) es falso y está medido en la tabla de arriba.

### Ancla

Se rebasea contra el propio 2023 (mismo mecanismo que ya usa `inseguridad`, y
que ya predecía el comentario de `itvc.indices_desde_series`: una serie anual
del SNIC resuelve sola al año 2023 porque la ventana BASE_MESES=oct/nov/dic-
2023 sólo tiene un punto poblado, diciembre). No es una elección arbitraria:
2023 cae cerca de la mediana de los 26 años de homicidios (4,32 contra
mediana ~5,7 de la serie 2000-2025, con pico 9,21 en 2002 y mínimo 3,48 en
2025) y dentro del rango histórico de robos (985,1, contra el rango 832-1.128
de la serie completa). No es un año extremo elegido para que el índice quede
mejor o peor.

### Verificación de la premisa (antes de escribir código)

Medido contra el snapshot del 16-sep-2026 (ver tabla de rezagos arriba) y
contra `snic-pais.csv` descargado en vivo el mismo día: 26 filas por tipo,
2000-2025, columna `tasa_hechos` presente y consistente con lo citado.

## Pros y contras de las opciones

**1. Dos indicadores separados.** A favor: no diluye la señal de homicidios
con el ruido de robos; usa el dato que la fuente ya publica. En contra: la
dimensión de seguridad pasa a depender de tres series en vez de una, más
superficie de fuente caída (mitigado por el store persistente).

**2. Compuesto.** A favor: un solo indicador nuevo. En contra: mezcla señales
de calidad distinta.

**3. Sólo homicidios.** A favor: menor alcance. En contra: descarta un dato
ya disponible sin ninguna limitación de la fuente que lo justifique.

**4. Statu quo.** A favor: ninguno — el argumento que lo sostenía es falso.

## Más información

- `config.py`, bloque "G2": `MAX_DIAS["tasa_homicidios"] = MAX_DIAS["tasa_robos"] = 560`,
  mismo critero que `iaf_transferencias`/`velocidad_resolucion` (anual, fecha
  del dato al 31-dic).
- [[0324-el-snic-conserva-homicidios-por-nombre-no-por-ranking]] y
  [[0325-correcciones-a-la-tanda-carne-motos-snic]] — decisiones que este ADR
  revierte parcialmente: el desglose por nombre se conserva (sigue siendo la
  fuente de `tipos_principales`), lo que cambia es que dos de esos tipos pasan
  a puntuar.
- [[0108]] — matriz de redundancia del ITVC, ADR de referencia para no repetir
  una misma señal dos veces.
