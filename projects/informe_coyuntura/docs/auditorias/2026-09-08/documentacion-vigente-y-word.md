# Documentación vigente y archivo Word

Se corrigieron el README del proyecto, el procedimiento de fichas y la guía de plantilla para distinguir los cuatro manuales y fichas Markdown vigentes de los Word que conservan entregas anteriores. Se añadió `output/fichas/README.md` para hacer visible esa distinción junto a los archivos.

El procedimiento ya documentaba que los Word conservan la última entrega enviada al equipo. Por ello no se sobrescribieron los Word históricos ni el documento del cinturón retirado Espíritu de época. No se creó ni envió una nueva entrega Word. El script PowerShell de exportación histórica no genera toda la documentación actual; se retiró esa instrucción obsoleta y se precisaron los comandos para cuatro cinturones.

Verificación: destinos de los enlaces relativos de los tres documentos especializados existentes; `git diff --check` sin errores. No cambiaron código, datos, índices ni documentos Word; no se repitieron tests o build por estos cambios de texto.
