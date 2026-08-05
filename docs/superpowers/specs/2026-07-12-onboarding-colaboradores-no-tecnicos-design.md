# Onboarding de colaboradores no técnicos al Informe de Coyuntura

Fecha: 2026-07-12

## Problema

Se necesita incorporar colaboradores no técnicos (2-5 personas, grupo estable)
al proyecto Informe de Coyuntura, de forma que puedan entender qué hace el
programa preguntando libremente y en cualquier momento — sin depender de que
Juan les explique todo en vivo cada vez.

## Decisión

Cada colaborador obtiene acceso de lectura al repo privado `biblitotecario-ai`
y conecta su propia cuenta de Claude.ai o ChatGPT (plan pago) al repo vía el
conector de GitHub de esa plataforma. Sin organización de GitHub.

### Por qué no una organización de GitHub

El grupo es chico (2-5) y estable. Una organización agrega estructura
(transferir el repo, revalidar que `informe.cigob.org` / Pages / Actions
sigan funcionando igual bajo la org, gestionar equipos) sin ningún beneficio
funcional sobre agregar colaboradores directos al repo actual. Se justificaría
con muchos repos o mucha rotación de gente — no es el caso hoy. Migrar a una
org más adelante sigue siendo una opción si el equipo escala.

### Por qué acceso completo al repo (no una copia curada)

Estos colaboradores ya son del círculo de confianza (mismo grupo que el
memory de reparto del repo ya contempla como colaboradores). Ver ADRs y docs
internos ayuda a que entiendan el *por qué* de cada decisión, no solo el qué.
No hay secretos técnicos versionados en el repo (ya verificado en un reparto
previo).

### Por qué cada colaborador con cuenta propia (no un asistente centralizado)

Se prefirió acceso genuinamente independiente y self-serve a largo plazo,
aceptando la fricción de arranque (cada uno crea GitHub + upgrade a
Claude/ChatGPT pago) a cambio de no depender de la cuenta de Juan ni de que
él sea un cuello de botella para cada pregunta.

## Setup

1. **Acceso al repo**: agregar a cada colaborador como *Collaborator* de
   `biblitotecario-ai` con rol **Read** (Settings → Collaborators). No Write:
   solo necesitan que la IA pueda leer, no pushear.
2. **Cuenta de IA**: cada colaborador crea su propia cuenta en Claude.ai o
   ChatGPT (la que prefiera) y la sube a un plan pago (Pro/Plus) — requisito
   del conector de GitHub en ambas plataformas, no hay forma de evitarlo con
   acceso self-serve individual por persona.
3. **Conector GitHub**: cada uno conecta su cuenta de GitHub a su cuenta de
   Claude/ChatGPT y autoriza el conector solo para `biblitotecario-ai` (no
   "todos mis repos").
4. **Base de conocimiento**: sin trabajo nuevo de documentación para arrancar.
   El repo ya tiene `README.md`, `docs/adr/`, `docs/arquitectura/`, y la web
   pública `/metodologia` en lenguaje llano. Si en el uso real aparecen
   preguntas mal respondidas, eso señala qué doc puntual mejorar — no
   rehacer el enfoque.

## Entregable de esta iteración

Una guía corta en español, no técnica, con los pasos 1-3 de arriba, para que
Juan no tenga que explicarlo en vivo a cada colaborador.

## Revocación de acceso

Sacar al colaborador de Collaborators del repo. Un click, sin tocar
infraestructura (no hay org que gestionar).

## Fuera de alcance

- Migrar el repo a una organización de GitHub.
- Armar un asistente/bot centralizado (requeriría mantenimiento de Juan y
  fue descartado a favor de acceso independiente por persona).
- Escribir documentación nueva para estos colaboradores — se apoya en la
  documentación ya existente (README, ADRs, `/metodologia` pública).
