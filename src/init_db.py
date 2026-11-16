from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

RUTA_SCHEMA = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def crear_esquema() -> None:
    sql = RUTA_SCHEMA.read_text(encoding="utf-8")
    with psycopg.connect() as conexion:
        conexion.execute(sql)


if __name__ == "__main__":
    crear_esquema()
    print("Esquema aplicado")
