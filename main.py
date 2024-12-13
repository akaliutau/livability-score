import base64
import json
import os

import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import bigquery

# Triggered from a message on a Cloud Pub/Sub topic.
from constants import SENSOR_DATASET, METEODATA_TABLE
from utils import publish_messages
from weather_bot import get_all_data
from google.cloud import secretmanager


@functions_framework.cloud_event
def event_processor(cloud_event: CloudEvent) -> None:
    try:
        print(os.environ.keys())
        project_id = os.getenv('PROJECT_ID', '')
        print(project_id)
        print(cloud_event)
        message = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        attributes = cloud_event.data["message"]["attributes"]
        print(f"message {message}")
        print(attributes)
        data = json.loads(message)

        # Construct the BigQuery client and table reference
        client = bigquery.Client(project=project_id)
        table_ref = bigquery.DatasetReference(
            project=project_id,
            dataset_id=attributes['dataset_id']).table(attributes['table_id'])

        # Insert the data into BigQuery
        errors = client.insert_rows_json(table_ref, data)
        print(f"inserting to table: {table_ref.table_id}")
        print(f"records: {data}")
        print(f"errors: {errors}")
    except Exception as e:
        print(e)


@functions_framework.cloud_event
def meteodata_event(cloud_event: CloudEvent) -> None:
    try:
        print(cloud_event)
        project_id = os.getenv('PROJECT_ID', '')
        api_key = os.getenv('OPENWEATHER_API_KEY', '')
        if not api_key:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/OPENWEATHER_API_KEY/versions/latest"
            response = client.access_secret_version(request={"name": name})
            api_key = response.payload.data.decode('UTF-8')
        data = get_all_data(api_key)
        if data:
            publish_messages(messages=data, dataset=SENSOR_DATASET, table=METEODATA_TABLE)
    except Exception as e:
        print(e)
