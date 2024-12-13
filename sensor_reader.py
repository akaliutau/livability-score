import asyncio
import configparser
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import List

import geojson
from bleak import BleakClient

# Retrieve Job-defined env vars
from constants import SENSOR_READER_READ_FREQ_SEC, SENSOR_DATASET, SENSOR_READER_BATCH_SIZE
from utils import publish_messages


# Function to return a byte array as zero padded, space separated, hex values
def convert_to_text(results):
    return " ".join(["{:x}".format(v).zfill(2) for v in results])


# Function to send a string to the device as a bytearray and return the results received
def write_bytes(tx, rx, vals):
    write_val = bytearray.fromhex(vals)
    tx.write(write_val)
    read_val = rx.read()
    return read_val


def convert_to_readings(response) -> List[float]:
    readings = []
    for v in [0, 3]:
        results_position = 6 + (v * 2)
        point = int.from_bytes(response[results_position:results_position + 2], byteorder='little')
        point = point * 0.0625
        if point > 2048:
            point = -1 * (4096 - point)
        readings.append(point)
    return readings


def mac2int(mac_addr):
    """Converts a MAC address string to an integer.
    Args:
        mac_addr (str): The MAC address in standard format (e.g., "00:11:22:33:44:55").
    Returns:
        int: The integer representation of the MAC address.
    Raises:
        ValueError: If the input MAC address is invalid.
    """

    mac_addr = mac_addr.lower().replace(":", "")
    match = re.match(r"^[0-9a-f]{12}$", mac_addr)
    if not match:
        raise ValueError("Invalid MAC address format")

    return int(mac_addr, 16)


async def notification_handler(sender, data):
    print(f"Received data: {data}")


def get_param(d: dict, sensor_name: str, param_name: str):
    return d[f'{sensor_name}.{param_name}']


async def dummy_sensor(sensor_name: str, sensor_data: dict):
    print('starting dummy sensor')
    print('finishing dummy sensor')


async def ws07_thermo_beacon(sensor_name: str, sensor_data: dict):
    print(f'reading sensor {sensor_name}')
    mac_address = get_param(sensor_data, sensor_name, 'mac_address')
    tx_char_uuid = get_param(sensor_data, sensor_name, 'tx_char_uuid')
    rx_char_uuid = get_param(sensor_data, sensor_name, 'rx_char_uuid')
    table_name = get_param(sensor_data, sensor_name, 'table')
    lat, long = get_param(sensor_data, sensor_name, 'location').split(',')
    point_feature = geojson.Point((float(long), float(lat)))

    async with BleakClient(mac_address) as client:
        if not client.is_connected:
            print(f'cannot connect to sensor {sensor_name}')
            return
        print(sensor_data)
        if 'prev_offset' not in sensor_data:  # 1st time run
            sensor_data['prev_offset'] = -1
            sensor_data['data'] = []
        prev_data_point = sensor_data['prev_offset']
        t = datetime.utcnow()
        cur_time = f"{t.utcnow().isoformat()[:-3]}Z"
        date = t.date().isoformat()
        data_to_write = bytearray([0x01, 0x00, 0x00, 0x00, 0x00])  # get the stat
        # Write to the characteristic
        await client.write_gatt_char(tx_char_uuid, data_to_write)
        # Read the response from the characteristic
        response = await client.read_gatt_char(rx_char_uuid)
        # The number of available values is stored in the 2nd and 3rd bytes of the response, little endian
        available = int.from_bytes(response[1:3], byteorder='little')
        print("There are {} available data points from this device ({})".format(available, sensor_name))
        if prev_data_point != available:
            sensor_data['prev_offset'] = available
            try:
                # Data is returned as three pairs of temperature and humidity values
                index = available - 1
                # print index for reference
                print(str(index).zfill(4), ": ", end='')
                # convert index to hex, padded with leading zeroes
                offset = hex(index)[2:].zfill(4)
                # reverse the byte order of the hex values
                offset_rev = offset[2:] + offset[0:2]
                # build the request string to be sent to the device
                hex_string = "07" + offset_rev + "000003"
                # send the request and get the response
                await client.write_gatt_char(tx_char_uuid, bytearray.fromhex(hex_string))
                # Read the response from the characteristic
                response = await client.read_gatt_char(rx_char_uuid)
                # Print the response as text
                print(convert_to_text(response))
                # convert the response to temperature and humidity readings
                read = convert_to_readings(response)
                print(read)
                avr_tempr = round(read[0], 3)
                avr_humid = round(read[1], 3)
                rec = {
                    'day': date,
                    'timestamp': cur_time,
                    'data': {
                        'mac': mac2int(mac_address),
                        'home_id': home_id,
                        'temperature': avr_tempr,
                        'humidity': avr_humid,
                        'location': geojson.dumps(point_feature)
                    }
                }
                sensor_data['data'].append(rec)
                if len(sensor_data['data']) > SENSOR_READER_BATCH_SIZE:
                    publish_messages(messages=sensor_data['data'], dataset=SENSOR_DATASET, table=table_name)
                    sensor_data['data'] = []
            except Exception as e:
                print(e)


handlers = {
    'ws07_thermo_beacon': ws07_thermo_beacon,
    'dummy_sensor': dummy_sensor
}

home_id = os.getenv('HOME_ID')


async def main():
    config = configparser.RawConfigParser()
    config.read('sensor_reader.properties')
    sensors = config.sections()
    print(sensors)
    sensor_local_data = defaultdict()
    while True:
        tasks = []
        for sensor in sensors:
            if sensor not in handlers:
                print(f'sensor {sensor} is not supported')
                continue
            if sensor not in sensor_local_data:
                sensor_local_data[sensor] = {o: config.get(sensor, o) for o in config.options(sensor)}
            task = asyncio.create_task(
                handlers[sensor](sensor_name=sensor, sensor_data=sensor_local_data[sensor])
            )
            tasks.append(task)
            # Keep the script running to receive notifications
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"script error: {str(e)}")
        await asyncio.sleep(SENSOR_READER_READ_FREQ_SEC)


if __name__ == "__main__":
    asyncio.run(main())
