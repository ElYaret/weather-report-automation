from datetime import datetime, timezone


class ErrorDeValidacion(Exception):
    pass


def transformar(ciudad_consultada: str, datos: dict) -> dict:
    try:
        registro = {
            "ciudad": datos["name"],
            "pais": datos.get("sys", {}).get("country"),
            "temperatura_c": float(datos["main"]["temp"]),
            "sensacion_c": datos["main"].get("feels_like"),
            "humedad_pct": int(datos["main"]["humidity"]),
            "presion_hpa": datos["main"].get("pressure"),
            "viento_ms": datos.get("wind", {}).get("speed"),
            "descripcion": datos["weather"][0]["description"],
            "medicion_utc": datetime.fromtimestamp(datos["dt"], tz=timezone.utc).replace(tzinfo=None),
        }
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ErrorDeValidacion(
            f"{ciudad_consultada}: respuesta con formato inesperado ({type(error).__name__})"
        ) from error

    if not -90 <= registro["temperatura_c"] <= 60:
        raise ErrorDeValidacion(
            f"{ciudad_consultada}: temperatura fuera de rango ({registro['temperatura_c']})"
        )
    if not 0 <= registro["humedad_pct"] <= 100:
        raise ErrorDeValidacion(
            f"{ciudad_consultada}: humedad fuera de rango ({registro['humedad_pct']})"
        )

    return registro


if __name__ == "__main__":
    ejemplo = {
        "name": "Lima",
        "sys": {"country": "PE"},
        "main": {"temp": 25.11, "feels_like": 25.4, "humidity": 65, "pressure": 1013},
        "wind": {"speed": 4.1},
        "weather": [{"description": "nubes dispersas"}],
        "dt": 1731300000,
    }
    print(transformar("Lima,PE", ejemplo))

    ejemplo_malo = {**ejemplo, "main": {**ejemplo["main"], "humidity": 150}}
    try:
        transformar("Lima,PE", ejemplo_malo)
    except ErrorDeValidacion as error:
        print("Error controlado:", error)