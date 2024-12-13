import json
import os

from google.cloud import pubsub_v1

from constants import TOPIC_ID


def publish_messages(messages, dataset, table):
    project_id = os.getenv('PROJECT_ID', '')
    is_local = os.getenv('LOCAL_ENV', '')
    print(f"is_local={is_local}")
    if is_local:
        print('using SA to access cloud')
        publisher = pubsub_v1.PublisherClient().from_service_account_json(filename='dev-sensor-sa-key.json')
    else:
        publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, TOPIC_ID)

    # Data must be a bytestring
    data = json.dumps(messages).encode("utf-8")
    print(messages)
    attr = {'dataset_id': dataset, 'table_id': table}
    print(attr)
    print(topic_path)
    future = publisher.publish(topic_path, data, **attr)
    print(future.result())
