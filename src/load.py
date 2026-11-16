import logging

import psycopg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SQL_INSERTAR = """
    INSERT INTO clima_observaciones (
        ciudad_consulta, medicion_utc, ciudad, pais, temperatura_c, sensacion_c,
        humedad_pct, presion_hpa, viento_ms, descripcion
    ) VALUES (
        %(ciudad_consulta)s, %(medicion_utc)s, %(ciudad)s, %(pais)s, %(temperatura_c)s, %(sensacion_c)s,
        %(humedad_pct)s, %(presion_hpa)s, %(viento_ms)s, %(descripcion)s
    )
    ON CONFLICT (ciudad_consulta, medicion_utc) DO NOTHING
"""


def cargar(registros: list[dict]) -> tuple[int, int]:
    """Inserta los registros en una sola transaccion. Devuelve (nuevos, ya_existian)."""
    nuevos = 0
    with psycopg.connect() as conexion:
        with conexion.cursor() as cursor:
            for registro in registros:
                cursor.execute(SQL_INSERTAR, registro)
                nuevos += cursor.rowcount
    return nuevos, len(registros) - nuevos
