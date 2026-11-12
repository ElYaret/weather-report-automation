# 🌦️ Reporte automático de clima (Python + API)

## Problema
Automatizar una tarea repetitiva: consultar a diario el clima de varias ciudades, validar los datos y entregar un reporte en Excel, sin intervención manual y con un registro de lo que pasó en cada ejecución.

## Qué hace
1. Consulta la API de [OpenWeatherMap](https://openweathermap.org/api) (clima actual) para una lista de ciudades.
2. Valida y aplana cada respuesta (campos obligatorios, rangos razonables).
3. Genera `reports/clima_AAAA-MM-DD.xlsx` con dos hojas: **Clima** (una fila por ciudad) y **Resumen** (conteos, promedio, ciudad más cálida y más fría, y los errores del día).
4. Registra cada ejecución en `logs/` y puede programarse para correr sola cada día.

## Arquitectura
```
main.py ──► fetch.py ──► transform.py ──► report.py ──► reports/*.xlsx
   │            │              │
   └────────────┴──────────────┴──► logs/clima_AAAA-MM-DD.log
```

| Módulo | Responsabilidad |
|---|---|
| `src/fetch.py` | Llama a la API, con reintentos y espera creciente ante fallos temporales |
| `src/transform.py` | Convierte la respuesta en un registro plano y valida los datos |
| `src/report.py` | Construye el Excel |
| `src/main.py` | Orquesta el flujo, registra en el log y devuelve un código de salida (0 correcto, 1 fallo) |

## Decisiones de diseño
- **La API key vive en `.env`**, que está fuera de Git. En el repositorio solo hay `.env.example`.
- **Reintentos solo donde tienen sentido:** se reintenta ante timeouts, 429 y errores 5xx (hasta 3 intentos, esperando 2 y 4 segundos). Un 401 o un 404 fallarían igual, así que se cortan de inmediato.
- **Una ciudad que falla no tumba el reporte:** el error se anota en el log y en la hoja *Resumen*. Solo se capturan los errores esperados; un bug inesperado detiene el programa a propósito, para que no quede escondido.
- **Validación en la entrada:** temperatura entre -90 y 60 °C y humedad entre 0 y 100 %. Un dato roto no llega al reporte.
- **Los logs no filtran la key:** los errores de conexión registran solo el tipo de error, y el nivel de `urllib3` se mantiene en WARNING.
- **Rutas relativas al archivo, no al directorio de trabajo:** el script funciona igual lanzado a mano o desde el Programador de tareas.

## Tecnologías usadas
Python, requests, python-dotenv, openpyxl, logging, Programador de tareas de Windows

## Cómo ejecutarlo
```powershell
git clone https://github.com/ElYaret/weather-report-automation.git
cd weather-report-automation
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edita `.env` y reemplaza `pon_tu_key_aqui` por tu API key de OpenWeatherMap (el plan gratuito incluye el clima actual). Luego:
```powershell
python src\main.py
```
La lista de ciudades se edita en `CIUDADES`, dentro de `src/main.py`.

## Programarlo cada día (Windows)
```powershell
$ruta = "RUTA_DEL_PROYECTO"
$accion = New-ScheduledTaskAction -Execute "$ruta\venv\Scripts\python.exe" -Argument "`"$ruta\src\main.py`"" -WorkingDirectory $ruta
$disparador = New-ScheduledTaskTrigger -Daily -At 8:00am
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "ReporteClimaDiario" -Action $accion -Trigger $disparador -Settings $config
```
Para comprobar el resultado de la última ejecución:
```powershell
Get-ScheduledTaskInfo -TaskName "ReporteClimaDiario" | Select-Object LastRunTime, LastTaskResult
```
Un `LastTaskResult` en 0 indica que terminó bien.

## Limitaciones
- El reporte del día se sobrescribe si el script corre más de una vez el mismo día.
- La tarea programada necesita que la PC esté encendida y con la sesión iniciada.
- La fecha de medición se escribe como texto (UTC) en el Excel, para que se vea igual en cualquier instalación.
- Cada ejecución guarda solo la foto del momento: no se acumula historial.

## Próximos pasos
- Guardar cada ejecución en PostgreSQL para acumular historial (Proyecto 6).
- Orquestar la ejecución con Airflow en lugar del Programador de tareas (Proyecto 8).
