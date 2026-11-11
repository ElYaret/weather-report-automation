import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

URL = "https://api.openweathermap.org/data/2.5/weather"
MAX_INTENTOS = 3
TIMEOUT_SEGUNDOS = 10
ESTADOS_REINTENTABLES = {429, 500, 502, 503, 504}


class ErrorDeApi(Exception):
    pass


def obtener_clima(ciudad: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ErrorDeApi("Falta OPENWEATHER_API_KEY en el .env")

    params = {"q": ciudad, "appid": api_key, "units": "metric", "lang": "es"}

    for intento in range(1, MAX_INTENTOS + 1):
        try:
            respuesta = requests.get(URL, params=params, timeout=TIMEOUT_SEGUNDOS)
        except requests.exceptions.RequestException as error:
            logger.warning("%s: fallo de conexion (%s), intento %d/%d",
                           ciudad, type(error).__name__, intento, MAX_INTENTOS)
        else:
            if respuesta.status_code == 200:
                return respuesta.json()
            if respuesta.status_code not in ESTADOS_REINTENTABLES:
                raise ErrorDeApi(f"{ciudad}: la API respondio {respuesta.status_code}")
            logger.warning("%s: la API respondio %d, intento %d/%d",
                           ciudad, respuesta.status_code, intento, MAX_INTENTOS)

        if intento < MAX_INTENTOS:
            time.sleep(2 ** intento)

    raise ErrorDeApi(f"{ciudad}: sin respuesta despues de {MAX_INTENTOS} intentos")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for ciudad in ["Lima,PE", "CiudadQueNoExiste"]:
        try:
            datos = obtener_clima(ciudad)
            print(ciudad, "->", datos["main"]["temp"], "C")
        except ErrorDeApi as error:
            print("Error controlado:", error)