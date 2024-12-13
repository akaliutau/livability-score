#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: send_local_message.sh message"
    exit 1
fi
msg64="$(echo $1 | base64)"
# shellcheck disable=SC2089
msg="{\"message\": {\"data\":\"$msg64\"}}"

echo "$msg"


curl -m 70 localhost:8080 \
  -H "Content-Type: application/json" \
  -H "ce-id: 1234567890" \
  -H "ce-specversion: 1.0" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-time: 2020-08-08T00:11:44.895529672Z" \
  -H "ce-source: //pubsub.googleapis.com/projects/dev-iot-application/topics/sensor_data" \
  -d "$msg"

