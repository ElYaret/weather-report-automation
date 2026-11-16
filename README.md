# 🌦️ Pipeline de clima: API → PostgreSQL + reporte Excel

![tests](https://github.com/ElYaret/weather-report-automation/actions/workflows/tests.yml/badge.svg)

## Problema
Automatizar una tarea repetitiva: consultar a diario el clima de varias ciudades, validar los datos, guardar el historial en una base de datos y entregar un reporte en Excel, sin intervención manual y con un registro de lo que pasó en cada ejecución.

## Qué hace
1. Consulta la API de [OpenWeatherMap](https://openweathermap.org/api) (clima actual) para una lista de ciudades.
2. Valida y aplana cada respuesta (campos obligatorios, rangos razonables).
3. Carga las mediciones en PostgreSQL (`clima_observaciones`) sin duplicar filas.
4. Genera `reports/clima_AAAA-MM-DD.xlsx` con dos hojas: **Clima** (una fila por ciudad) y **Resumen** (conteos, promedio, ciudad más cálida y más fría, y los errores del día).
5. Registra cada ejecución en `logs/` y puede programarse para correr sola cada día.

## Arquitectura
```
main.py ─► fetch.py ─► transform.py ─┬─► load.py ─► PostgreSQL (clima_observaciones)
   │                                 └─► report.py ─► reports/*.xlsx
   └──────────────────────────────────► logs/clima_AAAA-MM-DD.log
```

| Módulo | Responsabilidad |
|---|---|
| `src/fetch.py` | Llama a la API, con reintentos y espera creciente ante fallos temporales |
| `src/transform.py` | Convierte la respuesta en un registro plano y valida los datos |
| `src/load.py` | Inserta los registros en PostgreSQL, de forma idempotente y en una sola transacción |
| `src/report.py` | Construye el Excel |
| `src/main.py` | Orquesta el flujo, registra en el log y devuelve un código de salida (0 correcto, 1 fallo) |
| `src/init_db.py` | Crea la tabla a partir de `sql/schema.sql` |

## Base de datos
Una fila por ciudad y por medición, en `clima_observaciones` (definida en [`sql/schema.sql`](./sql/schema.sql)).

- **Llave primaria `(ciudad_consulta, medicion_utc)`:** `ciudad_consulta` es el texto exacto con el que se pidió la ciudad (`Lima,PE`), porque dos ciudades distintas pueden llamarse igual. `medicion_utc` es la hora de la observación que reporta la API.
- **Restricciones `CHECK`** (humedad de 0 a 100, temperatura de -90 a 60): la base repite las reglas de `transform.py`, así que rechaza datos inválidos aunque lleguen por otra vía.
- **`cargado_en`:** cuándo entró la fila a la base, distinto de la hora de la medición.

## Decisiones de diseño
- **Carga idempotente:** el `INSERT` usa `ON CONFLICT (ciudad_consulta, medicion_utc) DO NOTHING`. Si el script corre dos veces y la API devuelve la misma observación, la segunda vez no duplica nada.
- **Una sola transacción:** si algo falla a mitad de la carga, no se guarda ninguna fila. Todo o nada.
- **SQL con parámetros**, nunca con texto armado a mano.
- **La API key y las credenciales de la base viven en `.env`**, que está fuera de Git. En el repositorio solo hay `.env.example`.
- **Reintentos solo donde tienen sentido:** timeouts, 429 y errores 5xx (hasta 3 intentos, esperando 2 y 4 segundos). Un 401 o un 404 fallarían igual, así que se cortan de inmediato.
- **Una ciudad que falla no tumba el reporte:** el error se anota en el log y en la hoja *Resumen*. Solo se capturan los errores esperados; un bug inesperado detiene el programa, para que no quede escondido.
- **Si la base falla**, el Excel se genera igual, pero la ejecución termina con código 1 para que el Programador de tareas lo detecte.
- **Los logs no filtran secretos:** los errores de conexión registran solo el tipo de error.
- **Rutas relativas al archivo, no al directorio de trabajo:** el script funciona igual lanzado a mano o desde el Programador de tareas.

## Tests y CI
```powershell
pytest
```
- Pruebas de `transform` (incluidos los valores en los límites), `report` y `load`.
- Las pruebas de carga usan una **base aparte**, `weather_pipeline_test`, para no tocar los datos reales. En local se saltan si esa base no existe; en CI fallan si falta.
- **GitHub Actions** corre los tests en cada push y pull request, con un contenedor temporal de PostgreSQL.
- Se verificó que las pruebas detectan errores reales rompiendo a propósito la validación de rangos y la cláusula `ON CONFLICT`.

## Tecnologías usadas
Python, PostgreSQL, psycopg, requests, python-dotenv, openpyxl, pytest, GitHub Actions, Programador de tareas de Windows

## Cómo ejecutarlo
```powershell
git clone https://github.com/ElYaret/weather-report-automation.git
cd weather-report-automation
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```
1. Edita `.env`: pon tu API key de OpenWeatherMap (el plan gratuito incluye el clima actual) y los datos de tu PostgreSQL local (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`).
2. Crea la base de datos (`CREATE DATABASE weather_pipeline;`) con el cliente que prefieras.
3. Crea la tabla y ejecuta el pipeline:
```powershell
python src\init_db.py
python src\main.py
```
La lista de ciudades se edita en `CIUDADES`, dentro de `src/main.py`.

Para correr los tests, crea también la base `weather_pipeline_test` e instala `pip install -r requirements-dev.txt`.

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
- El Excel del día se sobrescribe si el script corre más de una vez el mismo día. El historial completo está en la base de datos.
- Las estaciones publican mediciones nuevas cada cierto tiempo: correr el script más seguido que eso no agrega filas nuevas.
- La tarea programada necesita que la PC esté encendida y con la sesión iniciada, y que PostgreSQL esté activo.
- `fetch.py` y `main.py` no tienen tests automáticos, porque dependen de la red.
- La fecha de medición se escribe como texto (UTC) en el Excel, para que se vea igual en cualquier instalación.

## Próximos pasos
- Analizar el historial acumulado con SQL (variación entre mediciones con window functions).
- Orquestar la ejecución con Airflow en lugar del Programador de tareas.
