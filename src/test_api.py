import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not API_KEY:
    raise SystemExit("Falta la key: revisa el archivo .env")

URL = "https://api.openweathermap.org/data/2.5/weather"
params = {"q": "Lima,PE", "appid": API_KEY, "units": "metric", "lang": "es"}

try:
    response = requests.get(URL, params=params, timeout=10)
except requests.exceptions.RequestException as error:
    # No imprimo el mensaje completo: puede incluir la URL con la key
    raise SystemExit(f"Error de conexion: {type(error).__name__}")

data = response.json()
print("Codigo de respuesta:", response.status_code)

if response.status_code == 200:
    print("Ciudad:", data["name"])
    print("Temperatura (C):", data["main"]["temp"])
    print("Humedad (%):", data["main"]["humidity"])
    print("Descripcion:", data["weather"][0]["description"])
else:
    print("Mensaje de la API:", data.get("message"))