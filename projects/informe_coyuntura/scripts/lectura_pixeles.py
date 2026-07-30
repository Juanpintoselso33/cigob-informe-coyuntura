"""Controles obligatorios para datos leídos de PÍXELES.

Hay fuentes cuyo dato sólo existe como imagen: los tableros de la CSJN publican
un PNG estático y deshabilitaron la descarga, y el Monitor de Recaudación de la
OPC se publica como JPG por página, sin planilla ni PDF con texto.

**Ningún gate del informe detecta un dígito mal leído.** `gate_calidad.py`
verifica estructura, frescura y card-vs-serie; los tests de reconciliación
verifican invariantes de conteo. Un 23.803 transcripto como 23.303 pasa todos.
Por eso un número que viene de píxeles no entra a nada sin control aritmético
cruzado, y este módulo es el que lo hace obligatorio en vez de dejarlo a la
memoria de quien transcribe.

## Por qué la LECTURA no está automatizada

Se probó OCR (easyocr) sobre el PNG del tablero de la CSJN, que es el caso real:
de las 36 etiquetas de dato reconoció **2**, con confianzas de 0,32 y 0,52. Lee
perfecto los rótulos del eje —los años, sobre fondo plano— y falla en los
números, que van en negrita, en color y encima de la curva. Un colector que
dependiera de eso no publicaría nunca, porque los controles de acá lo
rechazarían con razón.

La lectura entonces es un paso ASISTIDO y a demanda —una persona o un modelo de
visión mira la imagen— y su resultado se versiona en un store JSON. El cron
consume el store, que es texto. Mismo patrón que el resto de las fuentes caras
del proyecto (`acled_cortes.json`, `apoyo_empresario_codificacion.json`).

Lo que sí está automatizado, y es lo que importa: **los controles corren en cada
corrida de CI**, para siempre, sobre el store versionado. Una transcripción mala
—de hoy o de dentro de dos años— no sobrevive al test.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class ControlFallido(Exception):
    """Un control no se cumplió: el dato NO se publica."""


@dataclass
class Control:
    """Un control cruzado sobre una lectura de píxeles.

    `verifica` devuelve (ok, detalle). `aplica` permite declarar que un control
    NO corresponde a esta fuente, que es distinto de que falle — la diferencia
    importa: al leer la tabla de la OPC, sumar los renglones de impuestos da 70%
    de más porque «Otros impuestos» ya es un agregado, y eso no es un error de
    lectura sino un control que no aplica.
    """
    nombre: str
    verifica: object
    aplica: bool = True
    motivo_no_aplica: str = ""


@dataclass
class Lectura:
    """Un conjunto de números leídos de una imagen, con su procedencia."""
    fuente: str                      # URL de la imagen
    leido_por: str                   # cómo se leyó (modelo de visión, persona)
    fecha_lectura: str               # YYYY-MM-DD
    datos: dict
    controles: list = field(default_factory=list)

    def verificar(self) -> list[dict]:
        """Corre los controles. Levanta `ControlFallido` si alguno no pasa.

        Devuelve el detalle de cada uno para dejarlo registrado: un control que
        pasa sin decir contra qué pasó no sirve de auditoría.
        """
        resultados, fallos = [], []
        for c in self.controles:
            if not c.aplica:
                resultados.append({"control": c.nombre, "estado": "no_aplica",
                                   "detalle": c.motivo_no_aplica})
                continue
            ok, detalle = c.verifica(self.datos)
            resultados.append({"control": c.nombre,
                               "estado": "ok" if ok else "FALLA",
                               "detalle": detalle})
            if not ok:
                fallos.append(f"{c.nombre}: {detalle}")
        if fallos:
            raise ControlFallido(
                f"lectura de {self.fuente} rechazada — " + " · ".join(fallos))
        return resultados


# ── Controles reutilizables ───────────────────────────────────────────────────

def identidad_contable(a: str, b: str, resultado: str, tolerancia: float = 0.0):
    """`resultado` = `a` − `b`, para todas las claves. El control más fuerte que
    puede tener una lectura: si un dígito se leyó mal, la identidad no cierra."""
    def _v(datos):
        malos = []
        for k in sorted(datos[resultado]):
            esperado = datos[a][k] - datos[b][k]
            if abs(datos[resultado][k] - esperado) > tolerancia:
                malos.append(f"{k}: {datos[resultado][k]} ≠ {esperado}")
        n = len(datos[resultado])
        return (not malos,
                f"{n - len(malos)}/{n} cierran" + (f" · fallan {malos}" if malos else ""))
    return Control(f"{resultado} = {a} − {b}", _v)


def contra_fuente_de_texto(clave: str, obtener_oficial, tolerancia_pct: float = 0.5):
    """Compara un valor leído contra la MISMA magnitud publicada como texto.

    Es el control más valioso cuando existe: ancla la lectura de píxeles a una
    fuente verificable. No siempre existe — si existiera para toda la tabla, no
    haría falta leer la imagen."""
    def _v(datos):
        oficial = obtener_oficial()
        if oficial is None:
            return False, "la fuente de texto no respondió"
        leido = datos[clave] if not isinstance(datos[clave], dict) else None
        if leido is None:
            return False, f"{clave} no es un valor escalar"
        d = abs(leido / oficial - 1) * 100
        return d <= tolerancia_pct, f"leído {leido:,} vs oficial {oficial:,.0f} · desvío {d:.3f}%"
    return Control(f"{clave} contra fuente de texto", _v)


def rango_plausible(serie: str, minimo: float, maximo: float):
    """Cota de sanidad: un dígito de más se sale del rango del fenómeno."""
    def _v(datos):
        fuera = {k: v for k, v in datos[serie].items() if not (minimo <= v <= maximo)}
        return not fuera, f"{len(datos[serie])} valores en [{minimo:,}, {maximo:,}]" + (
            f" · fuera: {fuera}" if fuera else "")
    return Control(f"{serie} en rango plausible", _v)


def sin_huecos(serie: str, desde: int, hasta: int):
    """Todas las claves del período están presentes: una fila salteada al
    transcribir es tan grave como un dígito mal leído, y es más fácil que pase."""
    def _v(datos):
        faltan = [str(a) for a in range(desde, hasta + 1) if str(a) not in datos[serie]]
        return not faltan, (f"{hasta - desde + 1} períodos completos" if not faltan
                            else f"faltan {faltan}")
    return Control(f"{serie} sin huecos {desde}-{hasta}", _v)
