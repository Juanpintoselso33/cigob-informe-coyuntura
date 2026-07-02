"""Poller liviano de alertas de manifestación (API Transporte GCBA, GTFS-RT).

Corre 2×/día vía .github/workflows/piquetes-poll.yml (12:00 y 18:00 ART, la
franja típica de piquetes) además de la corrida diaria del colector completo:
los feeds de serviceAlerts son tiempo real puro, así que la cobertura de la
serie acumulada depende de la frecuencia de muestreo. Solo upserta el store
data/gestion/piquetes_alertas.json — no toca el cache del cinturón.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

from gestion import actualizar_alertas_manifestacion


def main() -> None:
    resultado = actualizar_alertas_manifestacion()
    if resultado is None:
        print("[ERROR] piquetes_poll: sin credenciales o feeds caídos.")
        sys.exit(2)
    print(f"[OK] piquetes_poll: {resultado['fecha']} — "
          f"{resultado['nuevas']} alertas nuevas, {resultado['total_dia']} en el día.")
    sys.exit(0)


if __name__ == "__main__":
    main()
