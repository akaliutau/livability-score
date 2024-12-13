import configparser
import os
import time
from datetime import datetime
from enum import Enum
from typing import List

import requests
import json
import geojson


def to_flat_json(data, j, name=''):
    if type(data) is dict:
        for x in data:
            to_flat_json(data[x], j, name + x + '.')
    elif type(data) is list:
        i = 0
        for node in data:
            to_flat_json(node, j, name + str(i) + '.')
            i += 1
    else:
        j[name[:-1]] = data


def sec_to_timestamp(t: int):
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.localtime(t))


def str_to_string(s: str):
    return str(s)


def float_to_float64(f: float):
    return float(f)


class DataEntry(Enum):
    TIMESTAMP = 1
    DATE = 2
    FLOAT64 = 3
    INTEGER = 4
    STRING = 5


weather_api_schema = [
    ('weather.0.description', 'description', str, DataEntry.STRING),
    ('main.temp', 'temperature', float, DataEntry.FLOAT64),
    ('main.pressure', 'pressure', float, DataEntry.FLOAT64),
    ('main.humidity', 'humidity', float, DataEntry.FLOAT64),
    ('wind.speed', 'wind_speed', float, DataEntry.FLOAT64),
    ('wind.deg', 'wind_direction', float, DataEntry.FLOAT64),
    ('clouds.all', 'clouds', float, DataEntry.FLOAT64),
    ('sys.sunrise', 'sunrise', int, DataEntry.TIMESTAMP),
    ('sys.sunset', 'sunset', int, DataEntry.TIMESTAMP),
]

type_convertors = {
    DataEntry.STRING: str_to_string,
    DataEntry.FLOAT64: float_to_float64,
    DataEntry.TIMESTAMP: sec_to_timestamp
}


def get_weather_data(api_key, latitude, longitude) -> any:
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}" \
          f"&appid={api_key}&units=metric"

    response = requests.get(url)
    if response.status_code != 200:
        return
    flatten = {}
    to_flat_json(json.loads(response.text), flatten)

    print(flatten)

    data = {}
    for path, field_name, json_type, output_type in weather_api_schema:
        if path in flatten:
            data[field_name] = type_convertors[output_type](json_type(flatten[path]))
    # Create a GeoJSON Point feature
    point_feature = geojson.Point((float(longitude), float(latitude)))
    data['location'] = geojson.dumps(point_feature)
    t = datetime.now()
    cur_time = f"{t.utcnow().isoformat()[:-3]}Z"
    date = t.date().isoformat()
    rec = {
        'day': date,
        'timestamp': cur_time,
        'data': data
    }

    print(f"Weather: {rec}")
    return rec


def get_all_data(api_key) -> List[any]:
    config = configparser.RawConfigParser()
    config.read('main.properties')
    sections = config.sections()
    data = []
    for section in sections:
        try:
            for o in config.options(section):
                lat, long = config.get(section, o).split(',')
                data.append(get_weather_data(api_key, float(lat), float(long)))
        except Exception as e:
            print(e)
    return data


if __name__ == "__main__":
    data_points = get_all_data(os.getenv('OPENWEATHER_API_KEY', ''))
    print(data_points)
