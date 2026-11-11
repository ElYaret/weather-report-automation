import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

print("Directorio actual:", os.getcwd())

ruta = find_dotenv()
print("find_dotenv encontro:", repr(ruta))

if ruta:
    crudo = Path(ruta).read_bytes()
    print("Primeros 4 bytes:", crudo[:4])
    print("Tamano del archivo (bytes):", len(crudo))

print("Variable ya definida antes de load_dotenv:", "OPENWEATHER_API_KEY" in os.environ)

load_dotenv()
valor = os.getenv("OPENWEATHER_API_KEY")
print("Despues de load_dotenv -> definida:", valor is not None, "| largo:", len(valor) if valor else 0)
print("Variables con WEATHER en el nombre:", [k for k in os.environ if "WEATHER" in k.upper()])