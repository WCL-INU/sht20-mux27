import time
import RPi.GPIO as GPIO
import smbus2


class DualMuxController:
    def __init__(self, mux_select_pins, mux_enable_pins, number_of_channels, i2c_bus=1):
        self.mux_select_pins = mux_select_pins
        self.mux_enable_pins = mux_enable_pins
        self.number_of_channels = (
            number_of_channels  # [첫번째 MUX 채널 수, 두번째 MUX 채널 수]
        )
        self.bus = smbus2.SMBus(i2c_bus)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self.mux_enable_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1)
        for pin in self.mux_select_pins:
            GPIO.setup(pin, GPIO.OUT)

    def select_channel(self, channel):
        if 0 <= channel < self.number_of_channels[0]:
            GPIO.output(self.mux_enable_pins[0], 0)
            GPIO.output(self.mux_enable_pins[1], 1)
            select_channel = channel
        elif self.number_of_channels[0] <= channel < sum(self.number_of_channels):
            GPIO.output(self.mux_enable_pins[0], 1)
            GPIO.output(self.mux_enable_pins[1], 0)
            select_channel = channel - self.number_of_channels[0]
        else:
            GPIO.output(self.mux_enable_pins[0], 1)
            GPIO.output(self.mux_enable_pins[1], 1)
            return  # Invalid channel

        for i in range(4):
            GPIO.output(self.mux_select_pins[i], (select_channel >> i) & 1)
        # time.sleep(0.1)  # 채널 전환 대기

    def scan_channel(self, channel):
        self.select_channel(channel)
        found = []
        for address in range(0x03, 0x78):
            try:
                self.bus.write_quick(address)
                found.append(address)
            except OSError:
                continue
        return found

    def cleanup(self):
        self.bus.close()
        GPIO.cleanup()
