# Guía para colaboradores no técnicos

Esta guía es para sumarte al proyecto sin necesidad de programar. Te va a
permitir preguntarle a una IA (Claude o ChatGPT) cualquier cosa sobre cómo
funciona el Informe de Coyuntura — qué mide cada indicador, por qué se tomó
tal decisión, cómo se arma un puntaje — en el momento que quieras, sin
depender de que alguien del equipo te lo explique en vivo.

Son tres pasos. Te van a llevar unos 15-20 minutos la primera vez.

## Paso 1 — Cuenta de GitHub

GitHub es donde vive el proyecto (el "repositorio" o "repo").

1. Si no tenés cuenta, creá una gratis en [github.com](https://github.com/signup).
2. Avisale a Juan tu usuario de GitHub para que te invite como colaborador
   del repo `biblitotecario-ai`.
3. Te va a llegar un mail de invitación de GitHub — aceptala.

No vas a necesitar usar GitHub directamente para nada más que esto: es solo
para darle permiso a la IA de leer el contenido del proyecto en tu nombre.

## Paso 2 — Cuenta de Claude o ChatGPT

Elegí la que prefieras (o la que ya uses) — ambas sirven igual para este uso.

- **Claude**: creá cuenta en [claude.ai](https://claude.ai) y pasate a un
  plan pago (Pro). Es necesario porque conectar un repo de GitHub es una
  función que no está en el plan gratuito.
- **ChatGPT**: creá cuenta en [chatgpt.com](https://chatgpt.com) y pasate a
  un plan pago (Plus). Mismo motivo.

## Paso 3 — Conectar el repo

- **En Claude**: andá a la configuración de tu cuenta → *Connectors* (o
  *Conectores*) → GitHub → conectá tu cuenta de GitHub → cuando te pida
  elegir a qué repos dar acceso, elegí **solo** `biblitotecario-ai` (no
  "todos mis repositorios").
- **En ChatGPT**: andá a Settings → Connectors → GitHub → mismo proceso:
  conectá tu cuenta de GitHub y dale acceso solo a `biblitotecario-ai`.

Una vez conectado, abrí un chat nuevo y empezá a preguntar. Algunos
ejemplos:

- "¿Qué mide el ITCM y cómo se calcula?"
- "¿Por qué el índice de gestión bajó este mes?"
- "Explicame en criollo qué es un 'cinturón' en este proyecto."
- "¿De dónde sale el dato de riesgo país que usa el informe?"

La IA va a leer el contenido del repo (documentación, código, datos) cada
vez que le preguntes algo — no hace falta que sepas dónde está cada archivo,
alcanza con preguntar en lenguaje natural.

## Si algo no te queda claro

Si la IA no te puede responder bien algo, avisale a Juan — probablemente
signifique que hay que mejorar algún documento puntual del proyecto, y es
información útil para el equipo.

## Cómo se revoca el acceso

Si en algún momento dejás de colaborar, Juan te saca de la lista de
colaboradores del repo desde GitHub — un solo paso, no hay nada más que
desconectar de tu lado.
