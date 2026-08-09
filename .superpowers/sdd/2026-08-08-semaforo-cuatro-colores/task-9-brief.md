# Task 9 — `verdictDeCinturon` no conoce el vocabulario real de `estado`

Tarea agregada a pedido del usuario durante la ejecución del plan. No estaba
en el plan original: salió del review de la Task 7.

## El defecto

`web/src/lib/datos.ts:231-235`:

```ts
export function verdictDeCinturon(estado: string): "verde" | "amarillo" | "rojo" {
  if (estado === "estable") return "verde";
  if (estado === "critico" || estado === "alerta") return "rojo";
  return "amarillo"; // en_tension
}
```

`_estado()` —`scripts/publicar.py:342-348`, réplica de
`scripts/generar_informe.py:63-68`— emite exactamente tres valores:

```python
if score <= UMBRALES["ESTABLE_MAX"]:   # 3
    return "estable"
if score <= UMBRALES["EN_TENSION_MAX"]: # 6
    return "en_tension"
return "tensionado"
```

`critico` y `alerta` **no se producen en ningún lado**. Son ramas muertas.
Consecuencias, todas vivas hoy:

- `tensionado`, el peor estado, cae al `else` y se pinta **amarillo**.
- `cinturonesRojos` (`datos.ts:525-527`) cuenta los que dan `"rojo"`, así que
  es **estructuralmente siempre 0**. Lo consumen `Hero.astro`,
  `Archivo.astro`, `Metodologia.astro` y `TensionPanel.astro`.
- `Bluf.astro:10-11` arma su prosa con `porVerdict("rojo")`, que siempre queda
  vacío: la frase "está en zona crítica" nunca puede aparecer.
- Hoy `vida_cotidiana` está en `tensionado` con score 6,9 y se muestra amarillo.

El origen probable de la confusión es que existe un campo **distinto** llamado
`alerta` en cada bloque de cinturón (`generar_informe.py:152,163`), que vale
`None` o `"multicinturon"`. No es el estado.

## Cuál es el mapeo correcto — no hay que decidirlo, ya está decidido

`generar_informe.py:192` ya lo declara para el informe markdown:

```python
return {"estable": "🟢", "en_tension": "🟡", "tensionado": "🔴"}.get(estado, "⚪")
```

Y `web/src/lib/fichas.ts:212` documenta la escala: «0–3 estable, 4–6 en
tensión, 7–10 tensionado».

O sea: **el informe markdown ya pinta `tensionado` de rojo desde siempre**, y
la web viene contradiciéndolo en silencio. Esto no es un cambio editorial ni
una recalibración: es hacer que la web coincida con el informe que genera el
mismo pipeline. No se toca `UMBRALES`, ni `_estado()`, ni ningún score.

## Qué hay que hacer

1. **El test primero.** En `tests/test_web_semaforo.py`, un test que ate el
   mapeo de TypeScript al enum de Python, para que no vuelvan a divergir:
   - Extraer del código Python los valores que `_estado()` puede devolver.
     Importar `publicar` y llamar `_estado()` sobre scores representativos de
     los tres tramos (por ejemplo 0, 5 y 9) es más robusto que parsear el
     archivo, y además pinea los umbrales reales.
   - Leer `web/src/lib/datos.ts` y verificar que `verdictDeCinturon` menciona
     **todos** esos valores y **ninguno** que `_estado()` no pueda emitir.
     El segundo chequeo es el que falla hoy, por `critico` y `alerta`.
2. Corregir `verdictDeCinturon`: `estable` → verde, `tensionado` → rojo,
   `en_tension` → amarillo. Sacar las dos ramas muertas. Mantener el tipo de
   retorno de tres colores: `estado` tiene tres valores y este chip no es el
   semáforo de cuatro.
3. Comentario en castellano explicando por qué son tres colores acá y cuatro
   en el semáforo, y que el mapeo espeja el de `generar_informe.py:192`.
4. `npx tsc --noEmit` y `npm run build` limpios.
5. Verificar el efecto real y reportarlo: con el snapshot vigente,
   `vida_cotidiana` pasa a rojo, `cinturonesRojos` pasa de 0 a 1, y el BLUF
   gana la frase de zona crítica. Confirmar que el texto resultante se lee
   bien y no queda redundante con el resto del párrafo.

## Lo que NO se toca

- `UMBRALES` en `config.py`, `_estado()`, y cualquier score o índice.
- El semáforo de 4 colores. Son dos conceptos distintos y siguen separados
  (ADR-0181 lo documenta).
- `web/dist/` es salida de build.

## Fallos preexistentes conocidos, ajenos

`python -m pytest tests -q` reporta 1 fallo y 1 error que preceden a este
trabajo: `test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`
y un error en `test_gestion_privatizaciones_novedades.py`. Cualquier otra cosa
es nueva.

## Commit

```bash
git add web/src/lib/datos.ts tests/test_web_semaforo.py
git commit -m "fix(web): el chip del cinturon nunca podia ponerse en rojo"
```
