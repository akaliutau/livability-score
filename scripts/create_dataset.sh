bq mk --dataset \
   --description "Dataset to keep sensor data" \
   --project_id="$PROJECT_ID" \
   "sensor_data"
scripts/create_table.sh "$PROJECT_ID" "sensor_data.sensor_thermo_beacon" scripts/sensor_thermo_beacon_schema_v1.json
scripts/create_table.sh "$PROJECT_ID" "sensor_data.weather_data" scripts/weather_data_schema_v1.json
