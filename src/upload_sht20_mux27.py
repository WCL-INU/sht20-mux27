import smbus2
import time
from mux_controller import DualMuxController
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
import os

HIVE_ID = os.getenv("HIVE_ID")
TYPE_ID = os.getenv("SENSOR_TYPE_ID")
DEVICE_ID = list(map(int, os.getenv("SENSOR_DEVICE_IDs").split()))
url = os.getenv("SERVER_URL")

mux_select_pins = [18, 17, 27, 22]
mux_enable_pins = [23, 24]
number_of_channels = [15, 12]  # 첫번째 MUX 15채널, 두번째 MUX 12채널

mux = DualMuxController(mux_select_pins, mux_enable_pins, number_of_channels)

# SHT20 default I2C address
SHT20_ADDR = 0x40

# SHT20 commands
TRIG_TEMP_MEASURE_HOLD = 0xE3
TRIG_HUMI_MEASURE_HOLD = 0xE5

def read_sensor(command):
    bus = smbus2.SMBus(1)  # Use I2C bus 1
    bus.write_byte(SHT20_ADDR, command)
    time.sleep(0.1)
    data = bus.read_i2c_block_data(SHT20_ADDR, command, 3)
    bus.close()
    return data

def read_temperature():
    data = read_sensor(TRIG_TEMP_MEASURE_HOLD)
    raw_temp = (data[0] << 8) + data[1]
    raw_temp &= 0xFFFC
    temp = -46.85 + 175.72 * raw_temp / 65536.0
    return temp

def read_humidity():
    data = read_sensor(TRIG_HUMI_MEASURE_HOLD)
    raw_humi = (data[0] << 8) + data[1]
    raw_humi &= 0xFFFC
    humi = -6 + 125.0 * raw_humi / 65536.0
    return humi

if __name__ == "__main__":
    # # 로그 설정 1
    # logging.basicConfig(
    #     filename='/home/pi/sensing_and_uplink.log',  # 로그 파일 경로
    #     level=logging.DEBUG,              # 로그 레벨 설정
    #     format='%(asctime)s %(levelname)s: %(message)s',  # 로그 포맷 설정
    #     datefmt='%Y-%m-%d %H:%M:%S'       # 날짜 형식 설정
    # )

    # 로그 설정 2
    handler = TimedRotatingFileHandler(
        '/home/pi/sensing_and_uplink.log',  # 로그 파일 경로
        when='midnight',         # 회전 시간 간격 (예: 'S', 'M', 'H', 'D', 'midnight', 'W0'-'W6')
        interval=1,              # 간격의 단위 수 (예: 1일)
        backupCount=7            # 보관할 백업 파일 수
    )

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    logger.info("Running...")
    logger.info(f"HIVE ID: {HIVE_ID}")
    logger.info(f"TYPE ID: {TYPE_ID}")
    logger.info(f"DEVICE IDs: {DEVICE_ID}")
    logger.info(f"SERVER URL: {url}")

    while True:
        data = []
        for channel in range(sum(number_of_channels)):
            try:
                mux.select_channel(channel)
                time.sleep(0.1)  # Give some time for the channel to switch

                temp = read_temperature()
                humi = read_humidity()
                data.append((channel, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), temp, humi))
            except Exception as e:
                logger.error(f"오류 발생: {e}")
            
        # # Print all collected data
        # for channel, temperature, humidity in data:
        #     print(f"Channel {channel} - Temperature: {temperature:.2f} C, Humidity: {humidity:.2f} %")
        json = {
            "type": TYPE_ID,
            "data": [
                {
                    "id": DEVICE_ID[channel],
                    "time": measure_time,
                    "temp": temperature,
                    "humi": humidity
                }
                for channel, measure_time, temperature, humidity in data
            ]
        }

        print(json)
        response = requests.post(url, json=json)
        print(response.status_code)
        print(response.text)
        # Clear data for next iteration

        time.sleep(10)