from datetime import datetime

from openpyxl import load_workbook

import report


def registro(ciudad, temperatura):
    return {
        "ciudad": ciudad, "pais": "PE", "temperatura_c": temperatura, "sensacion_c": temperatura,
        "humedad_pct": 60, "presion_hpa": 1013, "viento_ms": 3.0,
        "descripcion": "cielo claro", "medicion_utc": datetime(2026, 11, 11, 15, 0),
    }


def test_reporte_tiene_dos_hojas_y_resumen_correcto(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "CARPETA_REPORTES", tmp_path)
    ruta = report.generar_reporte(
        [registro("Lima", 25.0), registro("Cusco", 12.0)],
        ["Narnia: la API respondio 404"],
        fecha=datetime(2026, 11, 11, 8, 0),
    )

    assert ruta.name == "clima_2026-11-11.xlsx"
    libro = load_workbook(ruta)
    assert libro.sheetnames == ["Clima", "Resumen"]
    assert libro["Clima"].max_row == 3  # encabezado + 2 ciudades

    resumen = {fila[0]: fila[1] for fila in libro["Resumen"].iter_rows(values_only=True) if fila[0]}
    assert resumen["Ciudades consultadas"] == 3
    assert resumen["Ciudades correctas"] == 2
    assert resumen["Ciudades con error"] == 1
    assert resumen["Temperatura promedio (°C)"] == 18.5