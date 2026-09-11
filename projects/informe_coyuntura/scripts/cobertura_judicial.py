"""Conciliación de bajas verificadas con una foto del padrón judicial.

Las funciones preservan la foto original. Una baja anterior al padrón puede
estar incorporada o seguir pendiente en él; no se descuenta dos veces.
"""
from datetime import date
import calendar
import unicodedata


def _nombre(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    return " ".join("".join(c for c in texto if not unicodedata.combining(c)).upper().split())


def conciliar_bajas(padron, fecha_padron, eventos):
    """Devuelve bajas únicas y correcciones de vacancia necesarias en el ancla.

    Cada persona representa una baja en este registro; la suspensión o la
    absolución no son bajas. Para corregir la foto se exige persona y órgano
    coincidentes, habilitado y expresamente no vacante. Una persona ausente
    no se descuenta del ancla, aunque su baja sí sirve para reconstruir atrás.
    """
    date.fromisoformat(fecha_padron)
    unicos = {}
    for evento in eventos:
        date.fromisoformat(evento["fecha"])
        if evento["tipo"] not in {"remocion", "fallecimiento"}:
            raise ValueError("Sólo una baja efectiva puede cambiar el stock")
        if not evento.get("fuente") or not evento.get("organo") or not evento.get("persona"):
            raise ValueError("Baja sin procedencia, persona u órgano")
        persona = _nombre(evento["persona"])
        if persona in unicos and unicos[persona] != evento:
            raise ValueError("Bajas contradictorias de la misma persona")
        unicos[persona] = dict(evento)

    correcciones = []
    for evento in unicos.values():
        if evento["fecha"] > fecha_padron:
            continue
        coincidencias = [fila for fila in padron
                         if _nombre(fila.get("organo_habilitado")) == "SI"
                         and _nombre(fila.get("cargo_vacante")) == "NO"
                         and _nombre(fila.get("organo_nombre")) == _nombre(evento["organo"])
                         and (_nombre(fila.get("magistrado_nombre")) == _nombre(evento["persona"])
                              or _nombre(fila.get("titular_con_licencia")) == _nombre(evento["persona"]))]
        if len(coincidencias) > 1:
            raise ValueError("La baja corresponde a más de un cargo del padrón")
        if coincidencias:
            correcciones.append(evento)
    return sorted(unicos.values(), key=lambda e: (e["fecha"], e["persona"])), correcciones


def conciliar_movimientos(base, ajustes):
    """Reemplaza el efecto por norma y tipo, sin sumar dos veces un suplemento.

    Una norma con varios movimientos requiere desagregación explícita: no se
    adivina a quién corresponde el ajuste. La base debe haber sido recortada al
    período de reconstrucción y al universo de tribunales inferiores.
    """
    por_clave = {}
    for movimiento in base:
        clave = (movimiento["norma"], movimiento["tipo"])
        if clave in por_clave:
            raise ValueError("Norma con varios movimientos: desagregación requerida")
        por_clave[clave] = dict(movimiento)
    vistas = set()
    for ajuste in ajustes:
        clave = (ajuste["norma"], ajuste["tipo"])
        if clave in vistas:
            raise ValueError("Ajuste repetido para la misma norma y tipo")
        vistas.add(clave)
        if type(ajuste["delta"]) is not int or ajuste["delta"] not in {-1, 0, 1}:
            raise ValueError("Efecto neto inválido")
        if not ajuste.get("fuente") or not ajuste.get("motivo"):
            raise ValueError("Ajuste sin fuente o motivo")
        date.fromisoformat(ajuste["fecha"])
        por_clave[clave] = dict(ajuste)
    return sorted(por_clave.values(), key=lambda e: (e["fecha"], e["norma"], e["tipo"]))


def reconstruir_meses(total, cubiertos_padron, fecha_padron, movimientos, hasta):
    """Stock mensual desde un ancla corregida y movimientos netos documentados."""
    ancla = date.fromisoformat(fecha_padron)
    fin = date.fromisoformat(hasta)
    if type(total) is not int or not 0 <= cubiertos_padron <= total or total <= 0:
        raise ValueError("Ancla judicial inválida")
    fechas = [(date.fromisoformat(e["fecha"]), e["delta"]) for e in movimientos]
    if any(type(delta) is not int or delta not in {-1, 0, 1} for _, delta in fechas):
        raise ValueError("Efecto neto inválido")
    serie = {}
    anio, mes = 2023, 12
    while date(anio, mes, 1) <= fin:
        corte = min(date(anio, mes, calendar.monthrange(anio, mes)[1]), fin)
        if corte <= ancla:
            cubiertos = cubiertos_padron - sum(delta for fecha, delta in fechas if corte < fecha <= ancla)
        else:
            cubiertos = cubiertos_padron + sum(delta for fecha, delta in fechas if ancla < fecha <= corte)
        if not 0 <= cubiertos <= total:
            raise ValueError("Los movimientos llevan el stock fuera del universo")
        serie[f"{anio}-{mes:02d}"] = {"cubiertos": cubiertos, "corte": corte.isoformat(),
                                     "valor": round(100.0 * cubiertos / total, 2)}
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return serie
