---
madr: 4
id: '0270'
estado: 'aceptado'
fecha: 2026-09-03
cinturon: 'transversal'
archivos: ['scripts/aviso_slack.py', '.github/workflows/data-pipeline.yml', 'tests/test_aviso_slack.py']
relacionado: ['0133', '0175']
ambito: 'Operación · qué dicen el aviso de Slack y el issue cuando el pipeline se cae'
origen: 'El pipeline falló las noches del 1, 2 y 3-sep-2026 y los tres avisos decían lo mismo: el nombre del paso'
---

# ADR-0270 — El aviso dice qué falló, no en qué paso falló

## Contexto y planteo del problema

El aviso de falla nombraba el **paso** del workflow y nada más:

> 🔴 El pipeline nocturno falló y no publicó.
> \- Tests de reconciliación y robustez (G4-G5)

Para saber qué había pasado había que abrir el run y leer el log — que es
exactamente el trabajo que el aviso venía a evitar. El issue decía lo mismo con
otras palabras.

El 1, 2 y 3 de septiembre de 2026 el pipeline falló tres noches seguidas por
**una sola** causa: un test tomaba el mes parcial de una constante escrita a
mano en agosto, y el 1 de septiembre esa constante pasó a significar otra cosa.
Los tres avisos fueron idénticos, así que se leyeron como tres problemas
distintos y ninguno como uno que seguía abierto. Quien lo notó fue una persona
mirando la web, no el canal.

### Y algo peor, que apareció al escribir esto

`analizar()` —el que decide si una degradación merece aviso— buscaba
`##[notice]` y `##[warning]`. El archivo que lee lo escribe un `tee` dentro del
runner, y ahí los comandos de workflow están en su forma **cruda**:
`::notice::`. `##[notice]` es como GitHub los **renderiza** en el log
descargado.

O sea que dos de los tres avisos que CLAUDE.md describe como «lo que sí grita»
—una fuente caída entera (`exit=2`) y un presupuesto agotado— **nunca se
dispararon en producción**. La rama del `[ERR]` sí funcionaba, porque su regex
no lleva prefijo.

`tests/test_aviso_slack.py` estaba en verde: sus fixtures usaban la forma
renderizada. Una guarda alimentada con un formato que la producción no produce
no prueba nada, y no hace ruido al no probarlo.

## Factores de decisión

- El aviso tiene que alcanzar para decidir si hay que levantarse o no.
- Una falla que sigue abierta tiene que distinguirse de una falla nueva.
- La regla de admisión de `#alertas` no se toca: sólo lo accionable, y una
  corrida limpia no manda nada.
- El issue y Slack no pueden contar cosas distintas.

## Opciones consideradas

1. **Dejar el aviso corto y confiar en el link.** Es lo que había; la evidencia
   de tres noches dice que no alcanza.
2. **Mandar el log entero a Slack.** Ilegible, y el canal se muere de exceso.
3. **Un parser del log de la corrida**, con dos formatos de salida: corto para
   Slack, largo para el issue.

## Decisión

**Opción 3.** Los dos gates duplican su salida a `gates.log` —igual que los
colectores ya hacían con el suyo— y `aviso_slack.py` gana un parser que extrae:
la prueba que falló con su assertion, las `[FALLA]` del gate, los `::error::`
del workflow, el conteo de pruebas y el exit code de cada colector.

De ese parser salen las dos cosas: el mensaje de Slack (`fallo`) y el cuerpo
del issue (`reporte`, markdown por stdout). **Un solo lugar que sabe leer un log
de corrida.** Duplicarlo en bash dentro del YAML es la forma segura de que el
issue y Slack terminen diciendo cosas distintas.

Se suman tres datos que antes no estaban y cambian la lectura:

- **Cuántas noches seguidas.** El issue ya acumulaba un comentario por corrida
  caída, así que la cuenta estaba ahí sin pedirle nada a nadie.
- **Qué está sirviendo producción** — el `generated_at` del snapshot commiteado.
- **Qué sí anduvo**: el exit code de cada colector, para separar «se cayó todo»
  de «falló un test con los ocho colectores en verde».

Y los parsers pasan a aceptar **las dos formas** de los comandos de workflow,
siempre.

### Consecuencias

- El aviso alcanza para decidir sin abrir el run.
- Tres noches con la misma causa se leen como una.
- Los avisos de fuente caída y presupuesto agotado empiezan a existir. Puede
  que aparezcan alertas que llevaban meses mudas: si alguna resulta ser ruido
  conocido, va a `DEGRADACION_ESPERADA` con su motivo, no se vuelve a apagar el
  parser.
- El `reporte` se arma con el log de ESTA corrida. Si el job muere antes de
  escribirlo, cae al mensaje genérico con el link.

### Confirmación

`tests/test_aviso_slack.py` prueba que el aviso nombra la prueba fallada **y su
motivo**, que nombra las fallas del gate, que no repite el «Process completed
with exit code 1» de GitHub, y que un log ilegible no inventa una causa. Las
tres guardas de la forma cruda se verificaron rompiéndolas: con el parser vuelto
a `##[notice]` fallan las tres.

## Pros y contras de las opciones

- **Dejar el aviso corto**: cero trabajo; ya se probó y falló tres noches.
- **Mandar el log entero**: completo e ilegible; mata el canal.
- **Parser con dos salidas**: hay que mantenerlo, pero es el único que deja el
  aviso corto y suficiente a la vez.

## Más información

- ADR-0133 — un crash no es una fuente caída.
- ADR-0175 — `icg_utdt`: un error del código disfrazado de fuente caída, cuatro
  días congelando una serie.
- Corridas que lo motivaron: `33464629590`, `33585499079`, `33713692348`.
