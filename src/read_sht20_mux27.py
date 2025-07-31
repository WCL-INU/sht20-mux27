import smbus2
import time
from mux_controller import DualMuxController

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
    while True:
        data = []
        for channel in range(sum(number_of_channels)):
            try:
                mux.select_channel(channel)

                temp = read_temperature()
                humi = read_humidity()
                data.append((channel, temp, humi))
            except Exception as e:
                print(f"오류 발생: {e}")
                data.append((channel, None, None))
            
        # Print all collected data
        for channel, temperature, humidity in data:
            if temperature == None or humidity == None:
                print(f"Channel {channel} - Temperature: {temperature}, Humidity: {humidity}")
            else:
                print(f"Channel {channel} - Temperature: {temperature:.2f} C, Humidity: {humidity:.2f} %")

        time.sleep(1)