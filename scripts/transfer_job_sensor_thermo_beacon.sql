DECLARE today DATE DEFAULT CURRENT_DATE();
DECLARE start_date DATE DEFAULT DATE_SUB(today, INTERVAL 14 day);

EXPORT DATA
  OPTIONS ( uri = CONCAT('gs://livability-score-archive-data/', CAST(start_date AS STRING), '/sensor_thermo_beacon/*.gz'),
    format='JSON',
    compression='GZIP',
    overwrite=FALSE ) AS
SELECT
  *
FROM
  `dev-iot-application.sensor_data.sensor_thermo_beacon`
WHERE
  day BETWEEN start_date AND today
ORDER BY timestamp ASC
LIMIT 100000