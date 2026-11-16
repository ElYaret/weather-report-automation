import os
from datetime import datetime
from pathlib import Path

import psycopg
import pytest

from load import cargar

BASE_DE_PRUEBA = "weather_pipeline_test"
RUTA_SCHEMA = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


@pytest.fixture
def base_de_prueba(monkeypatch):
    # Las pruebas nunca tocan tu base real: usan una base aparte
    monkeypatch.setenv("PGDATABASE", BASE_DE_PRUEBA)
    try:
        conexion = psycopg.connect()
    except psycopg.OperationalError:
        if os.getenv("CI"):
            raise  # en CI, que no haya base es un error y no un salto
        pytest.skip(f"No hay una base {BASE_DE_PRUEBA} disponible")
    with conexion:
        nombre = conexion.execute("select current_database()").fetchone()[0]
        assert nombre == BASE_DE_PRUEBA  # seguro extra antes de borrar datos
        conexion.execute(RUTA_SCHEMA.read_text(encoding="utf-8"))
        conexion.execute("truncate clima_observaciones")


def registro(ciudad_consulta="Lima,PE", hora=datetime(2026, 11, 11, 15, 0), temperatura=25.0):
    return {
        "ciudad_consulta": ciudad_consulta, "medicion_utc": hora,
        "ciudad": ciudad_consulta.split(",")[0], "pais": "PE",
        "temperatura_c": temperatura, "sensacion_c": temperatura, "humedad_pct": 60,
        "presion_hpa": 1013, "viento_ms": 3.0, "descripcion": "cielo claro",
    }


def contar():
    with psycopg.connect() as conexion:
        return conexion.execute("select count(*) from clima_observaciones").fetchone()[0]


def test_carga_registros_nuevos(base_de_prueba):
    assert cargar([registro("Lima,PE"), registro("Cusco,PE")]) == (2, 0)
    assert contar() == 2


def test_cargar_dos_veces_lo_mismo_no_duplica(base_de_prueba):
    registros = [registro("Lima,PE"), registro("Cusco,PE")]
    cargar(registros)
    assert cargar(registros) == (0, 2)
    assert contar() == 2


def test_una_medicion_nueva_de_la_misma_ciudad_si_se_guarda(base_de_prueba):
    cargar([registro("Lima,PE", hora=datetime(2026, 11, 11, 15, 0))])
    nuevos, _ = cargar([registro("Lima,PE", hora=datetime(2026, 11, 11, 16, 0))])
    assert nuevos == 1
    assert contar() == 2


def test_si_un_registro_es_invalido_no_se_guarda_ninguno(base_de_prueba):
    malo = registro("Cusco,PE", temperatura=500)  # viola el CHECK de la tabla
    with pytest.raises(psycopg.errors.CheckViolation):
        cargar([registro("Lima,PE"), malo])
    assert contar() == 0
