# La lectura del mes

Un archivo por edición, nombrado con el período tal como lo publica el
snapshot: `AAAA-MM.md` (`2026-08.md` para agosto de 2026).

Es markdown y se publica tal cual en la portada, firmado como lectura
editorial del equipo. Puede tener más de un párrafo y usar `**negrita**`.

**Si el mes no tiene archivo, la portada no queda vacía ni vieja**: cae sola a
la síntesis automática que arma `Bluf.astro` desde el tablero, con su nota al
pie diciendo que se generó sola. `gate_calidad.py` avisa (G8) cuando el
período publicado no tiene texto escrito. Ver ADR-0211.

## Borradores

`borradores/` está fuera del alcance del glob (`*.md` no entra en
subcarpetas), así que lo que viva ahí **no se publica y no apaga el aviso
G8**. Es donde se escribe el texto del mes que viene sin riesgo de que el
nocturno lo publique a medio hacer.

Cuando esté listo:

```bash
mv borradores/AAAA-MM.md .
```

Recién ahí sale a la portada, firmado, y el gate deja de avisar.
