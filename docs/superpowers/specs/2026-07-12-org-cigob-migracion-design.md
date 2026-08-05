# Migración a organización GitHub `fundacion-cigob` + limpieza del repo

Fecha: 2026-07-12
Supersede: `2026-07-12-onboarding-colaboradores-no-tecnicos-design.md` (esa
decisión asumía "sin organización" — quedó descartada en esta misma
conversación al conocerse que el repo actual mezcla proyectos no-CIGOB).

## Problema

El plan original de dar acceso a colaboradores no técnicos vía conector
IA + repo (ver spec anterior) asumía compartir `biblitotecario-ai` tal cual.
Pero ese repo es un monorepo personal de Juan que además de
`informe_coyuntura` contiene Votómetro y el prototipo Bibliotecario IA —
cosas que no deberían quedar bajo el nombre institucional de CIGOB.

Decisión ampliada: crear una organización de GitHub para CIGOB, dejar en
ella un repo que contenga **solo** Informe de Coyuntura, y recién ahí sumar
a los colaboradores no técnicos (mismo mecanismo de acceso ya diseñado:
Collaborator con rol Read + conector GitHub de Claude/ChatGPT — eso no
cambia).

## Hallazgos que informan esta decisión

- **`cigob-informe` no es un repo con código fuente.** Es solo el destino
  del build estático (`gh-pages`) para el dominio `informe.cigob.org` —
  lo puebla automáticamente el workflow `pages.yml` de `biblitotecario-ai`
  vía una deploy key (`CIGOB_INFORME_DEPLOY_KEY`). No sirve como base para
  que una IA responda preguntas de metodología: ahí no hay ADRs ni código.
- **Ya existe una cuenta GitHub `CiGob`** (tipo User, no organización, con un
  repo público `Votometro`) — es la cuenta desde la que el equipo de
  España publica su propia versión del Votómetro. **Decisión del
  usuario: no tocarla, no coordinar con ella.** La org nueva usa un nombre
  distinto (`fundacion-cigob`) y esa cuenta queda aparte.
- **El Votómetro y el Bibliotecario IA de `biblitotecario-ai` son
  independientes de lo que public
a el equipo de España** — confirmado por el
  usuario ("la versión que se publica la hacen ellos, no tiene nada que
  ver lo que tengo acá, era una prueba nomás"). Dar de baja lo que hay en
  este repo **no** afecta al equipo de España ni requiere avisarles.

## Decisión

1. Crear la organización de GitHub **`fundacion-cigob`** (nombre confirmado
   disponible).
2. Dar de baja de verdad — no solo remover del repo — el Votómetro y el
   Bibliotecario IA que viven hoy en `biblitotecario-ai`: dejan de estar
   públicamente disponibles.
3. Limpiar el repo hasta que quede solo con `informe_coyuntura` (y los
   scripts/utilidades de raíz que le pertenecen).
4. Renombrar el repo `biblitotecario-ai` → **`cigob-informe-coyuntura`**.
5. Transferir `cigob-informe-coyuntura` a la organización `fundacion-cigob`.
6. Transferir también el repo de deploy `cigob-informe` a la misma
   organización (consistencia — toda la infraestructura de CIGOB bajo un
   mismo lugar).
7. Recién después: sumar a los colaboradores no técnicos como
   *Collaborators* (rol Read) de `fundacion-cigob/cigob-informe-coyuntura`,
   siguiendo el mismo mecanismo ya diseñado (cuenta propia + conector
   GitHub de Claude/ChatGPT pago). La guía
   (`docs/onboarding_colaboradores.md`) se actualiza con el nombre nuevo del
   repo.

## Riesgos y por qué el orden importa

- **`informe.cigob.org` es el sitio público en producción** (lanzamiento
  agosto 2026). Renombrar/transferir repos que alimentan ese dominio puede
  romper el certificado SSL del dominio custom (ya pasó una vez, ver
  historial: quedó trabado en `null` tras un cambio de DNS) o cortar el
  pipeline nocturno (`data-pipeline.yml` commitea a `main` todas las
  noches). Por eso el rename+transferencia va **al final**, después de
  limpiar el contenido, y hay que **verificar el sitio y el pipeline
  después de cada transferencia**, no asumir que quedó bien.
- **Secrets del repo** (`CIGOB_INFORME_DEPLOY_KEY` y cualquier otro):
  deberían persistir a través de rename/transfer (pertenecen al repo, no
  a la cuenta), pero se verifica explícitamente re-corriendo el pipeline
  después.
- **URLs hardcodeadas**: `README.md`, `pages.yml` (`external_repository:
  Juanpintoselso33/cigob-informe` → pasa a
  `fundacion-cigob/cigob-informe`), cualquier link a
  `github.com/Juanpintoselso33/biblitotecario-ai` en docs. Se actualizan
  como parte de la limpieza, no después.
- **Dar de baja Votómetro/Bibliotecario es difícil de deshacer** en el
  sentido de que son URLs públicas que dejan de responder — cualquiera con
  el link viejo ve un 404. Confirmado como aceptable por el usuario, pero
  vale dejarlo explícito acá porque es la parte menos reversible del plan.

## Qué pasa con el código de Votómetro/Bibliotecario

Se elimina del repo (no se preserva como carpeta muerta) — pero sigue
disponible en el historial de git de `biblitotecario-ai`/
`cigob-informe-coyuntura` por si hace falta recuperarlo. No se crea un repo
nuevo para "salvarlos" — es de baja real, no una mudanza (ver respuesta del
usuario: "darlos de baja en serio").

## Fuera de alcance

- Coordinar con el equipo de España — confirmado que no aplica.
- Tocar la cuenta `github.com/CiGob` existente.
- Convertir la org en algo con múltiples equipos/roles — con 2-5
  colaboradores alcanza con Collaborators directos al repo, la org es solo
  para tener la identidad institucional separada de la cuenta personal de
  Juan.
