import logging
import sys
from datetime import datetime
from pathlib import Path

import psycopg

from fetch import ErrorDeApi, obtener_clima
from load import cargar
from report import generar_reporte
from transform import ErrorDeValidacion, transformar

CIUDADES = [
    "Lima,PE", "Cusco,PE", "Quito,EC", "Bogota,CO", "Santiago,CL",
    "Buenos Aires,AR", "Mexico City,MX", "Madrid,ES", "Tokyo,JP", "New York,US",
]

CARPETA_LOGS = Path(__file__).resolve().parent.parent / "logs"
logger = logging.getLogger("clima")


def configurar_logging() -> None:
    CARPETA_LOGS.mkdir(exist_ok=True)
    archivo = CARPETA_LOGS / f"clima_{datetime.now():%Y-%m-%d}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(archivo, encoding="utf-8"), logging.StreamHandler()],
    )
    # Si algun dia subes el nivel a DEBUG, urllib3 escribiria la URL con la key en el log
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def main() -> int:
    configurar_logging()
    logger.info("Inicio: %d ciudades", len(CIUDADES))

    registros, errores = [], []
    for ciudad in CIUDADES:
        try:
            datos = obtener_clima(ciudad)
            registros.append(transformar(ciudad, datos))
            logger.info("%s: OK", ciudad)
        except (ErrorDeApi, ErrorDeValidacion) as error:
            logger.error("%s", error)
            errores.append(str(error))

    if not registros:
        logger.error("Ninguna ciudad se pudo procesar: no se genera reporte")
        return 1

    codigo = 0

    try:
        nuevos, existentes = cargar(registros)
        logger.info("Base de datos: %d filas nuevas, %d ya existian", nuevos, existentes)
    except psycopg.Error as error:
        # Solo el tipo de error: el mensaje completo puede traer datos de la conexion
        logger.error("No se pudo cargar a PostgreSQL (%s)", type(error).__name__)
        codigo = 1

    try:
        ruta = generar_reporte(registros, errores)
    except PermissionError:
        logger.error("No se pudo guardar el reporte: el Excel esta abierto? Cierralo y reintenta")
        return 1
    logger.info("Reporte generado: %s (%d correctas, %d con error)", ruta, len(registros), len(errores))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
