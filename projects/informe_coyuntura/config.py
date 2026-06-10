import sys
sys.stdout.reconfigure(encoding='utf-8')

# Pesos de cada cinturón en el score agregado (deben sumar 1.0).
# PROVISIONALES tras la ampliación a 5 cinturones del "Marco Conceptual del
# Informe de Coyuntura" (CIGOB, may-2026): el doc no fija pesos numéricos
# entre cinturones; ajustar cuando la fundación los formalice.
PESOS_CINTURONES = {
    "macro": 0.25,
    "politica": 0.25,
    "vida_cotidiana": 0.20,
    "gestion": 0.15,
    "espiritu_epoca": 0.15,
}

# Umbrales de clasificación de estado por cinturón (score 0-10)
# score <= ESTABLE_MAX → "estable" | <= EN_TENSION_MAX → "en_tension" | > EN_TENSION_MAX → "tensionado"
UMBRALES = {
    "ESTABLE_MAX": 3,
    "EN_TENSION_MAX": 6,
}

# Mapping cinturón dominante → barbarismo activo (marco PES de Matus)
BARBARISMO_MAP = {
    "macro": "tecnocrático",
    "politica": "político",
    "gestion": "gerencial",
    "vida_cotidiana": "político",
    "espiritu_epoca": "político",
}
