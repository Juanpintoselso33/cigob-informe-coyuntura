"""Experimento autónomo: no importa ni escribe el pipeline productivo."""
from datetime import date
import math

ESTADOS = {"presentado", "media_sancion", "sancionado", "rechazado", "retirado"}
TERMINALES_NEGATIVOS = {"rechazado", "retirado"}


def fecha(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Fecha no canónica")
    return parsed


def campo(item, clave):
    if clave not in item:
        raise ValueError(f"Falta el campo obligatorio: {clave}")
    return item[clave]


def calcular(cartera, corte):
    """Reconstrucción retrospectiva por fecha del hecho, nunca un vintage."""
    limite = fecha(corte)
    ids, filas = set(), []
    for item in cartera:
        if not item.get("id") or item["id"] in ids:
            raise ValueError("Identificador ausente o duplicado")
        ids.add(item["id"])
        peso = item.get("peso", 1)
        if isinstance(peso, bool) or not isinstance(peso, (int, float)) or not math.isfinite(peso) or peso <= 0:
            raise ValueError("Peso inválido")
        inicio = fecha(campo(item, "prioridad_desde"))
        revisado = fecha(campo(item, "verificado_hasta"))
        if revisado < inicio or not item.get("fuente_prioridad"):
            raise ValueError("Prioridad sin respaldo o revisión anterior al ingreso")
        vistos, aplicables = set(), []
        for evento in campo(item, "eventos"):
            dia = fecha(evento["fecha"])
            if dia < inicio or dia > revisado or dia in vistos:
                raise ValueError("Cronología inconsistente o eventos ambiguos")
            if evento["estado"] not in ESTADOS or not evento.get("fuente"):
                raise ValueError("Estado sin respaldo")
            vistos.add(dia)
            if dia <= limite:
                aplicables.append(evento)
        if inicio > limite:
            continue
        # Falta de verificación no equivale a rechazo ni elimina el denominador.
        # Sanción y los terminales negativos (rechazo/retiro) son hechos ya
        # ocurridos: no caducan por falta de revisión posterior, igual que la
        # sanción. "Ningún evento aplicable" con el período ya revisado es un
        # cero conocido (sin_avance), no un desconocido.
        sanciones = [e for e in aplicables if e["estado"] == "sancionado"]
        terminales = [e for e in aplicables if e["estado"] in TERMINALES_NEGATIVOS]
        ultimo_evento = max(aplicables, key=lambda e: e["fecha"]) if aplicables else None
        if sanciones:
            ultimo, estado = max(sanciones, key=lambda e: e["fecha"]), "sancionado"
        elif terminales:
            ultimo = max(terminales, key=lambda e: e["fecha"])
            estado = ultimo["estado"]
        elif ultimo_evento and revisado >= limite:
            ultimo, estado = ultimo_evento, ultimo_evento["estado"]
        elif ultimo_evento:
            ultimo, estado = ultimo_evento, "sin_verificar"
        elif revisado >= limite:
            ultimo, estado = None, "sin_avance"
        else:
            ultimo, estado = None, "sin_verificar"
        filas.append({"id": item["id"], "nombre": campo(item, "nombre"), "peso": peso,
                      "estado": estado, "fecha_estado": ultimo["fecha"] if ultimo else None,
                      "fuente": ultimo["fuente"] if ultimo else item["fuente_prioridad"],
                      "verificado_hasta": item["verificado_hasta"]})
    total = sum(f["peso"] for f in filas)
    aprobado = sum(f["peso"] for f in filas if f["estado"] == "sancionado")
    desconocido = sum(f["peso"] for f in filas if f["estado"] == "sin_verificar")
    porcentaje = lambda x: round(100 * x / total, 2) if total else None
    return {"corte": corte, "iniciativas": len(filas), "denominador": total,
            "peso_sancionado": aprobado, "peso_sin_verificar": desconocido,
            "porcentaje": porcentaje(aprobado) if total and not desconocido else None,
            "minimo": porcentaje(aprobado), "maximo": porcentaje(aprobado + desconocido),
            "cobertura": porcentaje(total - desconocido),
            "estado": "sin_universo" if not total else "parcial" if desconocido else "calculable",
            "filas": filas}
