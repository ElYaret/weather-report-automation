from datetime import datetime
from pathlib import Path
from statistics import mean

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

CARPETA_REPORTES = Path(__file__).resolve().parent.parent / "reports"

# (clave del registro, titulo de la columna, ancho)
COLUMNAS = [
    ("ciudad", "Ciudad", 16),
    ("pais", "País", 8),
    ("temperatura_c", "Temperatura (°C)", 18),
    ("sensacion_c", "Sensación (°C)", 16),
    ("humedad_pct", "Humedad (%)", 14),
    ("presion_hpa", "Presión (hPa)", 15),
    ("viento_ms", "Viento (m/s)", 14),
    ("descripcion", "Descripción", 24),
    ("medicion_utc", "Medición (UTC)", 20),
]

COLOR_ENCABEZADO = "FFD9E1F2"


def generar_reporte(registros: list[dict], errores: list[str], fecha: datetime | None = None) -> Path:
    fecha = fecha or datetime.now()
    CARPETA_REPORTES.mkdir(exist_ok=True)
    ruta = CARPETA_REPORTES / f"clima_{fecha:%Y-%m-%d}.xlsx"

    libro = Workbook()

    # Hoja 1: datos por ciudad
    hoja = libro.active
    hoja.title = "Clima"
    hoja.append([titulo for _, titulo, _ in COLUMNAS])
    for registro in registros:
        fila = [registro.get(clave) for clave, _, _ in COLUMNAS]
        # La fecha se escribe como texto legible: asi se ve igual en cualquier Excel
        if isinstance(fila[-1], datetime):
            fila[-1] = fila[-1].strftime("%Y-%m-%d %H:%M")
        hoja.append(fila)

    for celda in hoja[1]:
        celda.font = Font(bold=True)
        celda.fill = PatternFill(fill_type="solid", start_color=COLOR_ENCABEZADO, end_color=COLOR_ENCABEZADO)
        celda.alignment = Alignment(horizontal="center")
    for indice, (_, _, ancho) in enumerate(COLUMNAS, start=1):
        hoja.column_dimensions[hoja.cell(row=1, column=indice).column_letter].width = ancho
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions

    # Hoja 2: resumen
    resumen = libro.create_sheet("Resumen")
    filas = [
        ("Fecha de generación", fecha.strftime("%Y-%m-%d %H:%M")),
        ("Ciudades consultadas", len(registros) + len(errores)),
        ("Ciudades correctas", len(registros)),
        ("Ciudades con error", len(errores)),
    ]
    if registros:
        mas_calida = max(registros, key=lambda r: r["temperatura_c"])
        mas_fria = min(registros, key=lambda r: r["temperatura_c"])
        filas += [
            ("Temperatura promedio (°C)", round(mean(r["temperatura_c"] for r in registros), 1)),
            ("Ciudad más cálida", f"{mas_calida['ciudad']} ({mas_calida['temperatura_c']} °C)"),
            ("Ciudad más fría", f"{mas_fria['ciudad']} ({mas_fria['temperatura_c']} °C)"),
        ]
    for fila in filas:
        resumen.append(fila)
    if errores:
        resumen.append(())
        resumen.append(("Errores",))
        resumen.cell(row=resumen.max_row, column=1).font = Font(bold=True)
        for error in errores:
            resumen.append((error,))
    for fila in resumen.iter_rows(min_row=1, max_row=len(filas), max_col=1):
        fila[0].font = Font(bold=True)
    resumen.column_dimensions["A"].width = 30
    resumen.column_dimensions["B"].width = 32

    libro.save(ruta)
    return ruta


if __name__ == "__main__":
    ejemplo = [
        {"ciudad": "Lima", "pais": "PE", "temperatura_c": 25.1, "sensacion_c": 25.4,
         "humedad_pct": 65, "presion_hpa": 1013, "viento_ms": 4.1,
         "descripcion": "nubes dispersas", "medicion_utc": datetime(2026, 11, 11, 15, 0)},
        {"ciudad": "Cusco", "pais": "PE", "temperatura_c": 12.3, "sensacion_c": 11.0,
         "humedad_pct": 50, "presion_hpa": 1015, "viento_ms": 2.0,
         "descripcion": "cielo claro", "medicion_utc": datetime(2026, 11, 11, 15, 0)},
    ]
    print("Reporte generado en:", generar_reporte(ejemplo, ["Narnia: la API respondio 404"]))