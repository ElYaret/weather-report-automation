-- Una fila por ciudad y por medicion. La llave evita guardar dos veces la misma observacion.
CREATE TABLE IF NOT EXISTS clima_observaciones (
    ciudad_consulta TEXT         NOT NULL,   -- como la pedimos a la API, ej. 'Lima,PE'
    medicion_utc    TIMESTAMP    NOT NULL,   -- hora de la observacion segun la API
    ciudad          TEXT         NOT NULL,
    pais            CHAR(2),
    temperatura_c   NUMERIC(5,2) NOT NULL CHECK (temperatura_c BETWEEN -90 AND 60),
    sensacion_c     NUMERIC(5,2),
    humedad_pct     SMALLINT     NOT NULL CHECK (humedad_pct BETWEEN 0 AND 100),
    presion_hpa     INTEGER,
    viento_ms       NUMERIC(5,2),
    descripcion     TEXT         NOT NULL,
    cargado_en      TIMESTAMPTZ  NOT NULL DEFAULT now(),   -- cuando entro a nuestra base
    PRIMARY KEY (ciudad_consulta, medicion_utc)
);
