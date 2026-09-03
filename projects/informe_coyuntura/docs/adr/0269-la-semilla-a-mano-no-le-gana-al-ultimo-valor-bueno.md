---
madr: 4
id: '0269'
estado: 'aceptado'
fecha: 2026-08-29
cinturon: 'gestion'
indicadores: [concesiones_infraestructura, desregulacion_normativa, fal_modernizacion_laboral]
archivos: ['scripts/gestion.py', 'data/gestion/manuales.json', 'tests/test_la_semilla_no_le_gana_al_cache.py']
relacionado: ['0191', '0244', '0267']
ambito: 'Cinturón Gestión · qué valor publica una card cuando su fuente no contesta'
origen: 'El pipeline nocturno del 29-ago-2026 falló: contratar.gob.ar dio timeout y la card de concesiones retrocedió de 100% a 28,7%'
---

# ADR-0269 — La semilla escrita a mano no le gana al último valor bueno

## Contexto y planteo del problema

`data/gestion/manuales.json` guarda un valor por indicador para cuando el
colector automático no consigue el dato. Seis indicadores tienen una entrada, y
todas se escribieron entre el 30-jun y el 15-jul-2026.

`_manual_entry()` las consultaba **antes** que el cache de la corrida anterior.
Como el cache guarda el último valor que sí salió de la fuente en vivo, el orden
estaba invertido: ante un corte, la card publicaba el número tipeado a mano en
julio en vez del que se había bajado la noche anterior.

Mientras la fuente no se caiga no se nota. El 29-ago-2026 se cayó:

- `contratar.gob.ar` dio *connect timeout* a los 60 s.
- La card de `concesiones_infraestructura` cayó al fallback y publicó **28,7%**
  —Etapas I y II-A, la foto del 2-jul— cuando el plan estaba **entero
  adjudicado** desde el 24-ago (ADR-0244) y el cache de esa misma madrugada
  tenía el **100%** bueno.
- La serie no depende de CONTRAT.AR: se reconstruye desde
  `concesiones_fechas.json` y marcó 100% correctamente.

Esa divergencia —serie 100, card 28,7— es lo que hizo fallar la corrida, y ahí
está lo que importa: **no falló por el retroceso, falló de casualidad.** G3 vio
la diferencia y la excusó, correctamente, porque la card estaba en
carry-forward. La atajó `test_puntaje_unico_camino.py`, que compara el puntaje
del último punto de la serie contra el publicado y encontró 100 contra 44,6.

Sin serie propia no hay quién compare. Y de los seis indicadores con semilla,
el que más lejos está de su cache no es concesiones:

| indicador | semilla (jun/jul) | último valor en vivo (28-ago) |
|---|---|---|
| `desregulacion_normativa` | 57 | 16.771 |
| `fal_modernizacion_laboral` | 0,4 | 50,0 |
| `concesiones_infraestructura` | 28,7 | 100,0 |
| `asistencia_directa` | 100 | 100 |
| `protocolo_antipiquetes` | 74,2 | 74,2 |
| `libertad_opcion_salud` | 31,8 | 31,8 |

Las dos primeras filas no son datos viejos: son **otra magnitud**. Un corte de
la fuente las habría hecho saltar dos órdenes de magnitud con el badge de
"desactualizado" puesto, que es exactamente lo que ese badge NO comunica.

## Factores de decisión

- Un valor que salió de la fuente es mejor evidencia que uno tipeado a mano.
- La degradación tiene que ser monótona: perder frescura, nunca retroceder a
  otro número.
- La semilla sigue haciendo falta: un clon nuevo, o un indicador que nunca
  fetcheó bien, no tienen cache del cual tirar.

## Opciones consideradas

1. **Actualizar las seis semillas a mano.** Arregla hoy y garantiza la
   repetición: envejecen solas y nada avisa cuándo.
2. **Borrar `manuales.json`.** Deja sin red al clon nuevo y al indicador que
   nunca fetcheó.
3. **Invertir la precedencia**: primero el último valor en vivo, la semilla
   como piso.

## Decisión

**Opción 3.** `_manual_entry()` devuelve primero la entrada del cache anterior
cuando tiene valor y `obtenido_en`, y sólo si no la hay cae a la semilla.

`obtenido_en` es el discriminador y ya existía: lo pone `_sellar()` y **sólo
sobre lo que devolvió un colector** (ADR-0191). No prueba que haya habido
tráfico de red —hay colectores que calculan sobre un archivo curado del repo,
como `protocolo_antipiquetes`— y no hace falta que lo pruebe: lo que produce el
colector sigue siendo mejor evidencia que la copia a mano de ese mismo número.
El carry-forward lo arrastra intacto, que es justo lo que hay que conservar.

**Con una puerta**: si la semilla declara un `fecha_dato` más nuevo que el del
cache, gana la semilla. Sin ella este mismo ADR se repetiría con los papeles
invertidos —una recalibración de metodología quedaría bloqueada mientras la
fuente esté caída, porque el cache sellado bajo la fórmula vieja le ganaría
para siempre a la semilla corregida—. Las fechas son ISO y se comparan por
prefijo común: un empate, una precisión distinta o una fecha ausente dejan
ganar al cache.

De paso se corrigieron las tres semillas desfasadas —incluida la `unidad` del
FAL, que seguía describiendo la fórmula anterior a ADR-0228 y que
`_manual_entry()` copia tal cual a la card—. La de
`concesiones_infraestructura` pasa a 100% con las cuatro etapas y sus
resoluciones: aunque ya no la lea nadie que tenga cache, un
clon nuevo la lee, y dejarla en 28,7 es dejar la trampa armada.

### Consecuencias

- Una fuente caída ahora degrada de verdad: mismo número, badge de viejo.
- La semilla queda como lo que era, un piso para arrancar sin cache.
- Las semillas siguen envejeciendo, pero ya no pisan nada mejor.

### Confirmación

`tests/test_la_semilla_no_le_gana_al_cache.py` construye el caso exacto del
29-ago —cache con 100 sellado, semilla con 28,7— y falla si vuelve a ganar la
semilla. Prueba además que la semilla sí se usa cuando el cache no tiene nada
sellado, que es la razón por la que el archivo existe, y que una semilla más
nueva sí entra.

La guarda que importa es la cuarta: ninguna semilla puede mover más de **20
puntos de banda** el puntaje de su indicador respecto del último valor del
colector —el mismo criterio de `test_puntaje_unico_camino`—. Un umbral por
cociente no habría servido: la regresión del 29-ago fue 100 → 28,7, apenas
3,5×, y contra la banda del ITCG son 100 contra 44,6.

## Pros y contras de las opciones

- **Actualizar a mano**: fácil hoy, repetible mañana; no cambia el mecanismo.
- **Borrar el archivo**: simple, pero rompe el arranque sin cache.
- **Invertir la precedencia**: el cambio más chico que arregla la clase entera
  de error; deja las semillas envejeciendo, ahora sin efecto.

## Más información

- ADR-0191 — `obtenido_en` sella el momento en que un valor salió de la fuente.
- ADR-0244 — el acto publicado en el Boletín manda sobre el estado de CONTRAT.AR.
- ADR-0267 — una fuente caída degrada el indicador, no lo hace desaparecer.
- Corrida que lo destapó: run `33230315111`, 29-ago-2026 03:00 UTC.
