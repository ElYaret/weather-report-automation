from datetime import datetime

import pytest

from transform import ErrorDeValidacion, transformar


def respuesta_valida():
    return {
        "name": "Lima",
        "sys": {"country": "PE"},
        "main": {"temp": 25.1, "feels_like": 25.4, "humidity": 65, "pressure": 1013},
        "wind": {"speed": 4.1},
        "weather": [{"description": "nubes dispersas"}],
        "dt": 1731300000,
    }


def test_respuesta_valida_se_aplana():
    registro = transformar("Lima,PE", respuesta_valida())
    assert registro["ciudad"] == "Lima"
    assert registro["pais"] == "PE"
    assert registro["temperatura_c"] == 25.1
    assert registro["humedad_pct"] == 65
    assert isinstance(registro["medicion_utc"], datetime)


def test_campos_opcionales_pueden_faltar():
    datos = respuesta_valida()
    del datos["sys"], datos["wind"]
    del datos["main"]["feels_like"], datos["main"]["pressure"]
    registro = transformar("Lima,PE", datos)
    assert registro["pais"] is None
    assert registro["viento_ms"] is None
    assert registro["sensacion_c"] is None


def test_falta_un_campo_obligatorio():
    datos = respuesta_valida()
    del datos["main"]
    with pytest.raises(ErrorDeValidacion):
        transformar("Lima,PE", datos)


def test_temperatura_no_numerica():
    datos = respuesta_valida()
    datos["main"]["temp"] = "abc"
    with pytest.raises(ErrorDeValidacion):
        transformar("Lima,PE", datos)


@pytest.mark.parametrize("temperatura, humedad", [(80, 65), (-95, 65), (25, 150), (25, -1)])
def test_valores_fuera_de_rango(temperatura, humedad):
    datos = respuesta_valida()
    datos["main"]["temp"] = temperatura
    datos["main"]["humidity"] = humedad
    with pytest.raises(ErrorDeValidacion):
        transformar("Lima,PE", datos)

@pytest.mark.parametrize("humedad", [0, 100])
def test_humedad_en_los_limites_es_valida(humedad):
    datos = respuesta_valida()
    datos["main"]["humidity"] = humedad
    assert transformar("Lima,PE", datos)["humedad_pct"] == humedad


@pytest.mark.parametrize("temperatura", [-90, 60])
def test_temperatura_en_los_limites_es_valida(temperatura):
    datos = respuesta_valida()
    datos["main"]["temp"] = temperatura
    assert transformar("Lima,PE", datos)["temperatura_c"] == temperatura
