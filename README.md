# About

This is the coding part of the IoT project "Designing Scalable System to estimate the Livability Score using readings from multiple sensors"

The CoLab with EDA can be found here:

https://colab.research.google.com/drive/1HkPLzr-0rOI0DGFfpil3vhfFbePAtYSA

# Architecture

![High level architecture](pict/gcp_arch.png?raw=true "GCP Architecture")

# Big Query table schema

Schema for the table `dev-iot-application.sensor_data.sensor_thermo_beacon`

```json
[
  {
    "mode": "REQUIRED",
    "name": "day",
    "type": "DATE"
  },
  {
    "mode": "REQUIRED",
    "name": "timestamp",
    "type": "TIMESTAMP"
  },
  {
    "name": "data",
    "type": "RECORD",
    "mode": "REQUIRED",
    "fields": [
      {
        "mode": "REQUIRED",
        "name": "mac",
        "type": "INTEGER"
      },
      {
        "mode": "REQUIRED",
        "name": "home_id",
        "type": "INTEGER"
      },
      {
        "mode": "NULLABLE",
        "name": "temperature",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "humidity",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "location",
        "type": "GEOGRAPHY"
      }
    ]
  }
]
```

Schema for the table `dev-iot-application.sensor_data.weather_data`

```json
[
  {
    "mode": "REQUIRED",
    "name": "day",
    "type": "DATE"
  },
  {
    "mode": "REQUIRED",
    "name": "timestamp",
    "type": "TIMESTAMP"
  },
  {
    "name": "data",
    "type": "RECORD",
    "mode": "REQUIRED",
    "fields": [
      {
        "mode": "NULLABLE",
        "name": "temperature",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "humidity",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "pressure",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "wind_direction",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "wind_speed",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "sunrise",
        "type": "TIMESTAMP"
      },
      {
        "mode": "NULLABLE",
        "name": "sunset",
        "type": "TIMESTAMP"
      },
      {
        "mode": "NULLABLE",
        "name": "clouds",
        "type": "FLOAT64"
      },
      {
        "mode": "NULLABLE",
        "name": "description",
        "type": "STRING"
      },
      {
        "mode": "NULLABLE",
        "name": "location",
        "type": "GEOGRAPHY"
      }
    ]
  }
]
```

# Installation

Create a new project at GCP:

```shell
gcloud --version
bq version
source ./set_env.sh 
gcloud projects create "$PROJECT_ID"
gcloud config set project "$PROJECT_ID"
gcloud config get-value project
```

After creation enable billing (could take up to 5 min for GCP to move it from the sandbox mode)

Create necessary infrastructure (SAs, PubSub topics, BigQuery tables, etc)
```shell
gcloud services enable pubsub.googleapis.com``
gcloud services enable biqquery.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable eventarc.googleapis.com

gcloud pubsub topics create sensor_data
gcloud pubsub topics create meteo_data
./create_dataset.sh
```

Create SA with role `roles/pubsub.publisher` to send messages to PubSub topic:

```shell
gcloud iam service-accounts create dev-sensor-sa --display-name="Sensor SA"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:dev-sensor-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role=roles/pubsub.publisher
gcloud iam service-accounts keys create dev-sensor-sa-key.json \
  --iam-account=dev-sensor-sa@$PROJECT_ID.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com  \
    --role=roles/secretmanager.secretAccessor
```

The folders `cf_sensor_event` contains the python code for CF which inserts records into appropriate table

One can test them locally:

```shell
{\"day\": \"2024-11-29\", \"timestamp\": \"2024-11-29T14:33:35.855Z\", \"data\": {\"mac\":\"47:EF:00:00:01:12\",\"temperature\": 22.938,\"humidity\": 43.312}}
```

```shell
curl localhost:8888 \
  -X POST \
  -H "Content-Type: application/json" \
  -H "ce-id: 123451234512345" \
  -H "ce-specversion: 1.0" \
  -H "ce-time: 2020-01-02T12:34:56.789Z" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-source: //pubsub.googleapis.com/projects/MY-PROJECT/topics/MY-TOPIC" \
  -d '{"message": {"data": "eyJkYXkiOiAiMjAyNC0xMS0yOSIsICJ0aW1lc3RhbXAiOiAiMjAyNC0xMS0yOVQxNDozMzozNS44NTVaIiwgImRhdGEiOiB7Im1hYyI6IjQ3OkVGOjAwOjAwOjAxOjEyIiwidGVtcGVyYXR1cmUiOiAyMi45MzgsImh1bWlkaXR5IjogNDMuMzEyfX0K", 
  "attributes": {"dataset_id":"sensor_data", "table_id":"thermo_beacon_data"}}, 
  "subscription": "projects/MY-PROJECT/subscriptions/MY-SUB"}'
```

or, for testing in the cloud console:
```shell
{
  "_comment": "data is base64 encoded string",
  "data": "eyJkYXkiOiAiMjAyNC0xMS0yOSIsICJ0aW1lc3RhbXAiOiAiMjAyNC0xMS0yOVQxNDozMzozNS44NTVaIiwgImRhdGEiOiB7Im1hYyI6IjQ3OkVGOjAwOjAwOjAxOjEyIiwidGVtcGVyYXR1cmUiOiAyMi45MzgsImh1bWlkaXR5IjogNDMuMzEyfX0K",
  "attributes": {"dataset_id":"sensor_data","table_id":"thermo_beacon_data"}
}
```

# Deployment

```shell
gcloud functions deploy event_processor \
--region=us-central1 \
--runtime=python310 \
--source=. \
--entry-point=event_processor \
--trigger-topic=sensor_data \
--allow-unauthenticated \
--set-env-vars PROJECT_ID=$PROJECT_ID
```

```shell
gcloud functions deploy meteodata_event \
--region=us-central1 \
--runtime=python310 \
--source=. \
--entry-point=meteodata_event \
--trigger-topic=meteo_data \
--allow-unauthenticated \
--set-env-vars PROJECT_ID=$PROJECT_ID
```

```shell
gcloud scheduler jobs create pubsub meteo_data_job  \
  --schedule="*/5 * * * *"  \
  --topic=meteo_data \
  --message-body="event" \
  --location=us-central1
```

# Testing

```shell
functions-framework --target=event_processor --port=8888
```

```shell
gcloud alpha functions deploy local cf_test \
    --entry-point=event_processor \
    --port=8888 \
    --runtime=python312

```

# References

[1] https://cloud.google.com/functions/docs/running/functions-emulator

[2] https://colab.research.google.com/drive/1HkPLzr-0rOI0DGFfpil3vhfFbePAtYSA

