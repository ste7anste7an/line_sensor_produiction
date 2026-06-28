"""MicroPython driver for the LMS Line Sensor over I2C or uRemote (Pybricks)."""

__all__ = ["LineSensorI2C", "LineSensorUR"]
__version__ = "0.2.1"

# version 0.2.1
# - added extra commands for reading/writeing config values, debug, serial en/disable, gpio for test, etc.
# - disabled check_line_type
# to do:
# reading and writing config values , e.g. auto load calibartion, etc.
#
# version 0.2.2
# added 'set_load_cal_startup(self, calibrated)' and
#       'set_ir_emitter_startup(self, emitter)'

from time import sleep_ms

class BaseLineSensor:
    """Base class for LMS Line Sensor implementations. Defines shared constants."""

    RAW_BYTES = 13
    SENSOR_COUNT = 8

    MODE_RAW = 0
    MODE_CALIBRATED = 1
    MODE_SAVING = 2
    MODE_CALIBRATING = 3

    POSITION = 8
    MIN = 9
    MAX = 10
    DERIVATIVE = 11
    SHAPE = 12
    VALUES = -1

    LEDS_OFF = 0
    LEDS_VALUES = 1
    LEDS_VALUES_INVERTED = 2
    LEDS_POSITION = 3
    LEDS_MAX = 4

    SHAPE_NONE = " "
    SHAPE_STRAIGHT = "|"
    SHAPE_T = "T"
    SHAPE_L_LEFT = "<"
    SHAPE_L_RIGHT = ">"
    SHAPE_Y = "Y"

    CONFIG_MAJ_VERSION = 0
    CONFIG_MIN_VERSION = 1
    CONFIG_LOAD_CAL_STARTUP = 2
    CONFIG_CAL_DURATION = 3
    CONFIG_SHAPE_THRESHOLD_BLACK = 4
    CONFIG_IR_POWER = 5

    def _decode_index(self, raw, idx, invert_values=False):
        if idx == self.VALUES:
            values = raw[: self.SENSOR_COUNT]
            if invert_values:
                return tuple(255 - v for v in values)
            return tuple(values)
        if idx == self.POSITION or idx == self.DERIVATIVE:
            return raw[idx] - 128
        if idx == self.SHAPE:
            return chr(raw[idx])
        return raw[idx]

    def data(self, *indices) -> tuple:
        """Implemented in subclasses."""
        raise RuntimeError("Subclasses must implement data().")

    def _select_indices(self, raw, indices, invert_values=False):
        if not indices:
            return tuple(raw)

        if len(indices) == 1:
            return self._decode_index(raw, indices[0], invert_values=invert_values)

        out = []
        for idx in indices:
            decoded = self._decode_index(raw, idx, invert_values=invert_values)
            if idx == self.VALUES:
                out.extend(decoded)
            else:
                out.append(decoded)
        return tuple(out)

    def sensors(self):
        """Read the 8 sensor channel values."""
        return self.data(self.VALUES)

    def position(self):
        """Read the line position (-128 to 127, where 0 is center)."""
        return self.data(self.POSITION)

    def derivative(self):
        """Read the position derivative (rate of position change)."""
        return self.data(self.DERIVATIVE)

    def shape(self):
        """Read the line shape as an ASCII character."""
        return self.data(self.SHAPE)

    def position_derivative_shape(self) -> tuple:
        """Read line position, derivative, and shape."""
        return self.data(self.POSITION, self.DERIVATIVE, self.SHAPE)


class LineSensorUR(BaseLineSensor):
    """LMS Line Sensor via uRemote (Pybricks)."""

    def __init__(self, port):
        try:
            from uremote import uRemote
            from pybricks.tools import wait
        except ImportError:
            raise RuntimeError(
                "LineSensorUR requires Pybricks and uRemote. "
                "Use LineSensorI2C for direct I2C access on MicroPython."
            )
        self.ur = uRemote(port)
        self.wait = wait

    def read_all(self):
        """Read all 13 sensor bytes from firmware."""
        self.wait(1)
        ack, data = self.ur.call("all")
        if ack == "!ERROR":
            return [0] * 13
        else:
            return data

    def data(self, *indices) -> tuple:
        """
        Read sensor data with optional index-based filtering.

        With no indices, this returns the raw 13-byte payload as a tuple.
        With one index, this returns a single value directly.
        With multiple indices, this returns a tuple in the same order as requested.

        Example:
            sensor.data(sensor.POSITION) -> -12
            sensor.data(sensor.POSITION, sensor.SHAPE) -> (-12, '|')
        """
        raw = self.read_all()
        return self._select_indices(raw, indices)

    def mode_raw(self):
        """Set sensor to raw mode."""
        self.ur.call("mode", 0)

    def mode_calibrated(self):
        """Set sensor to calibrated mode."""
        self.ur.call("mode", 1)

    def leds(self, mode):
        """Set LED display mode."""
        self.ur.call("led", mode)

    def save_calibration(self):
        """Save calibration values to EEPROM."""
        self.ur.call("save")

    def load_calibration(self):
        """Load calibration values from EEPROM."""
        self.ur.call("load")

    def calibrate(self, duration=5):
        """
        Convenience method to calibrate for a certain duration and then save if desired.

        Args:
            duration: Duration in seconds to run the calibration (default 5)
            Calibration is always saved to EEPROM after calibration.
        """
        self.leds(self.LEDS_OFF)
        self.start_calibration()
        self.wait(1000 * (duration + 1))
        self.wait(1500)
        print("Calibration stored in EEPROM")
        self.save_calibration()

    def start_calibration(self):
        """Start calibration."""
        self.leds(self.LEDS_OFF)
        self.ur.call("calibrate")

    def ir_power(self, power):
        """Set the IR emitter power (True or False)."""
        self.ur.call("emitter", power)

    def neopixel(self, led_nr, r, g, b):
        """Control onboard NeoPixel LED (backend-specific)."""
        self.ur.call("neopixel", led_nr, r, g, b)


class LineSensorI2C(BaseLineSensor):
    """LMS Line Sensor via I2C (MicroPython)."""

    # I2C command constants (backend-specific)
    # firmware version 3.85
    CMD_GET_VERSION = 2
    CMD_DEBUG = 3
    CMD_CALIBRATE = 4
    CMD_IS_CALIBRATED = 5
    CMD_LOAD_CAL = 6
    CMD_SAVE_CAL = 7
    CMD_GET_MIN = 8
    CMD_GET_MAX = 9
    CMD_SET_MIN = 10
    CMD_SET_MAX = 11
    CMD_NEOPIXEL = 12
    CMD_LEDS = 13
    CMD_SET_EMITTER = 14
    CMD_GET_VALUE = 15
    CMD_SET_VALUE = 16
    CMD_SHOW_CONFIG = 17
    CMD_LOAD_CONFIG = 18
    CMD_SAVE_CONFIG = 19
    CMD_GPIO_OUT = 20
    CMD_GPIO_IN = 21
    CMD_SERIAL_DISABLE = 22
    CMD_SERIAL_ENABLE = 23
    CMD_GET_UID = 24
    MAX_CMDS = 25

    def __init__(self, i2c_id = 1, scl_pin=4, sda_pin=5, device_addr=51, mode = BaseLineSensor.MODE_RAW, freq=100000):
        try:
            from machine import I2C, Pin
            from time import sleep, ticks_ms, ticks_diff
            from collections import deque
        except ImportError:
            raise RuntimeError(
                "LineSensorI2C requires machine, time, and collections modules. "
                "Use LineSensorUR for Pybricks, which doesn't have these modules."
            )

        self.device_addr = device_addr
        self.i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=freq)
        self.pos_history = deque([(0, 0)] * 5, 5)
        self.current_leds_mode = self.LEDS_OFF
        self.save_start_time = 0
        self.current_mode = mode
        self.last_mode = mode
        #self.write_command(mode)
        self.black_line = False
        #self.load_calibration()
        #self.mode_calibrated()
        #self.check_line_type()

        # Store module references for later use in methods
        self.sleep = sleep
        self.ticks_ms = ticks_ms
        self.ticks_diff = ticks_diff


    def robust_i2c_readfrom(self, device_addr, raw_bytes):
        ntry = 4
        while ntry>0:
            ntry-=1
            try:
                response = self.i2c.readfrom(device_addr, raw_bytes)
                if ntry<3:
                    print("error robust_iec_readfrom",ntry)
                
                return response
            except:
                pass
        print("ntry >0")
        return 
        
    def _read_all(self):
        if self.current_mode < self.MODE_SAVING:
            try:
                return list(self.robust_i2c_readfrom(self.device_addr, self.RAW_BYTES))
            except:
                return list(self.robust_i2c_readfrom(self.device_addr, self.RAW_BYTES))

        if self.current_mode == self.MODE_SAVING:
            if self.ticks_diff(self.ticks_ms(), self.save_start_time + 1500) > 0:
                self.write_command(self.last_mode)
                self.current_mode = self.last_mode
                print("Calibration stored in EEPROM")

        return [0] * self.RAW_BYTES

    def data(self, *indices):
        """
        Read sensor data from I2C with optional index-based filtering.

        With no indices, this returns the raw 13-byte payload as a tuple.
        With one index, this returns a single value directly.
        With multiple indices, this returns a tuple in the same order as requested.

        Example:
            sensor.data(sensor.POSITION) -> -12
            sensor.data(sensor.POSITION, sensor.SHAPE) -> (-12, '|')
        """
        raw = self._read_all()
        return self._select_indices(raw, indices, invert_values=self.black_line)

    def write_command(self, command):
        """
        Write a 1-byte command to the sensor.
        """
        if type(command) is int:
            command = [command]
        ntry = 4 
        while ntry>0:
            ntry-=1
            try:
                self.i2c.writeto(self.device_addr, bytes(command))
                if ntry<3:
                    print("error write_command",ntry)
                return
            except:
                pass
        print("write_command: ntry>4")
        

    def mode_raw(self):
        """Set sensor to raw mode."""
        self.current_mode = self.last_mode = self.MODE_RAW
        self.write_command(self.MODE_RAW)

    def mode_calibrated(self):
        """Set sensor to calibrated mode."""
        self.current_mode = self.last_mode = self.MODE_CALIBRATED
        self.write_command(self.MODE_CALIBRATED)

    def start_calibration(self):
        """Start sensor calibration."""
        # Firmware TODO: turn off LEDs during calibration, which can interfere with light readings.
        # Firmware TODO: implement calibration timer
        # so you can self.write_command((self.CMD_CALIBRATE, 5)) to calibrate for 5 seconds,
        # then automatically switch back to the previous mode.
        print("Starting calibration")
        self.last_mode = self.current_mode
        self.current_mode = self.MODE_CALIBRATING
        self.write_command((self.CMD_LEDS, self.LEDS_OFF))
        self.write_command(self.CMD_CALIBRATE)

    def save_calibration(self):
        """Stop calibration and save values to EEPROM."""
        print("Stopping calibration and saving new values")
        self.write_command(self.MODE_CALIBRATED)
        self.write_command((self.CMD_LEDS, self.current_leds_mode))
        #self.check_line_type()
        self.write_command(self.last_mode)
        self.write_command(self.CMD_SAVE_CAL)
        self.save_start_time = self.ticks_ms()
        self.current_mode = self.MODE_SAVING

    def check_line_type(self):
        """Check if the line is black or white after calibration."""
        # Firmware TODO: implement auto-inversion after calibration
        values = list(self.robust_i2c_readfrom(self.device_addr, 8))
        avg = sum(values) // len(values)
        self.black_line = avg > 128  # Most sensors return white, lots of light.
        print(values, avg, self.black_line)
        print("Line is", "black" if self.black_line else "white")

    def calibrate(self, duration=5):
        """
        Convenience method to calibrate for a certain duration and then save if desired.

        Args:
            duration: Duration in seconds to run the calibration (default 5)
            Calibration is always saved to EEPROM after calibration.
        """
        self.start_calibration()
        self.sleep(duration)
        self.save_calibration()
        self.sleep(1.5)
        print("Calibration stored in EEPROM")
        self.current_mode = self.last_mode

    def ir_power(self, power):
        """Set the IR emitter power (True or False)."""
        self.write_command((self.CMD_SET_EMITTER, 1 if power else 0))

    def leds(self, mode):
        """Set LED display mode."""
        self.current_leds_mode = mode
        self.write_command((self.CMD_LEDS, mode))

    def load_calibration(self):
        """Load calibration values from EEPROM."""
        self.write_command(self.CMD_LOAD_CAL)

    def neopixel(self, led_nr, r, g, b):
        """Control onboard NeoPixel LED over I2C."""
        self.write_command((self.CMD_NEOPIXEL, led_nr, r, g, b))

    def set_neopixel(self, nr_led, r, g, b):
        """Alias for neopixel()."""
        self.neopixel(nr_led, r, g, b)

    def rgb_mode(self, mode):
        """Alias for leds()."""
        self.leds(mode)

    def led_mode(self, mode):
        """Alias for leds()."""
        self.leds(mode)

    def get_cal_min(self):
        """Return calibration minimum values."""
        self.write_command(self.CMD_GET_MIN)
        return list(self.robust_i2c_readfrom(self.device_addr, self.SENSOR_COUNT))

    def get_cal_max(self):
        """Return calibration maximum values."""
        self.write_command(self.CMD_GET_MAX)
        return list(self.robust_i2c_readfrom(self.device_addr, self.SENSOR_COUNT))

    def set_cal_min(self, values):
        """Set calibration minimum values."""
        if len(values) != self.SENSOR_COUNT:
            raise ValueError("values must contain 8 items")
        self.write_command(tuple([self.CMD_SET_MIN] + [int(v) & 0xFF for v in values]))

    def set_cal_max(self, values):
        """Set calibration maximum values."""
        if len(values) != self.SENSOR_COUNT:
            raise ValueError("values must contain 8 items")
        self.write_command(tuple([self.CMD_SET_MAX] + [int(v) & 0xFF for v in values]))

    def version(self):
        """Return firmware version as [major, minor]."""
        self.write_command(self.CMD_GET_VERSION)
        return list(self.robust_i2c_readfrom(self.device_addr, 2))

    def set_debug(self, debug):
        """Set debug level."""
        self.write_command((self.CMD_DEBUG, debug))

    def is_calibrated(self):
        """Return firmware calibration status."""
        self.write_command(self.CMD_IS_CALIBRATED)
        return self.robust_i2c_readfromm(self.device_addr, 1)[0]

    def get_config_field(self, field):
        """Return a configuration field value from EEPROM."""
        self.write_command((self.CMD_GET_VALUE, field))
        val = self.robust_i2c_readfrom(self.device_addr, 1)
        sleep_ms(10)
        if isinstance(val, (bytes, bytearray)):
            return val[0]
        return val

    def set_config_field(self, field, value):
        """Set a configuration field value in EEPROM."""
        self.write_command((self.CMD_SET_VALUE, field, value))

    def show_config(self):
        """Print configuration values."""
        # self.write_command(self.CMD_SHOW_CONFIG)
        print("current configuration")
        print("Major version:", self.get_config_field(self.CONFIG_MAJ_VERSION))
        print("Minor version:", self.get_config_field(self.CONFIG_MIN_VERSION))
        print("Load calibration at startup:", self.get_config_field(self.CONFIG_LOAD_CAL_STARTUP))
        print("Calibration duration:", self.get_config_field(self.CONFIG_CAL_DURATION))
        print("Shape threshold black:", self.get_config_field(self.CONFIG_SHAPE_THRESHOLD_BLACK))
        print("IR power:", self.get_config_field(self.CONFIG_IR_POWER))

    def set_load_cal_startup(self, calibrated):
        """Set default startup mode for loading calibrated  values"""
        if type(calibrated)==bool:
            cal=1 if calibrated else 0
        else:
            cal = calibrated
        self.set_config_field(self.CONFIG_LOAD_CAL_STARTUP, cal)

    def set_ir_emitter_startup(self, emitter):
        """Set default startup mode for enabling ir emitters"""
        if isinstance(emitter, bool):
            emit=1 if emitter else 0
        else:
            emit = emitter
        self.set_config_field(self.CONFIG_LOAD_CAL_STARTUP, emit)

    def set_threshold_shape(self, threshold):
        """Set default threshold for detecting shapes"""
        self.set_config_field(self.CONFIG_SHAPE_THRESHOLD_BLACK, threshold)
    
    def save_config(self):
        """Save config to EEPROM."""
        self.write_command(self.CMD_SAVE_CONFIG)

    def load_config(self):
        """Load config from EEPROM."""
        self.write_command(self.CMD_LOAD_CONFIG)

    def gpio_out(self, pin, value):
        """Set a GPIO output pin to value."""
        self.write_command((self.CMD_GPIO_OUT, pin, value))

    def gpio_in(self, pin):
        """Read a GPIO input pin."""
        self.write_command((self.CMD_GPIO_IN, pin))
        return self.robust_i2c_readfrom(self.device_addr, 1)[0]

    def serial_disable(self):
        self.write_command(self.CMD_SERIAL_DISABLE)

    def serial_enable(self):
        self.write_command(self.CMD_SERIAL_ENABLE)

    def get_uid(self):
        self.write_command(self.CMD_GET_UID)
        uid = self.robust_i2c_readfrom(self.device_addr, 12)
        return ':'.join(["%02X"%i for i in uid])

# Example usage on LMS_ESP32
# with the line sensor connected to I2C pins (GPIO 4 for SCL, GPIO 5 for SDA):
if __name__ == "__main__":
    from time import sleep

    sensor = LineSensorI2C()

    sensor.ir_power(True)
    sensor.leds(sensor.LEDS_VALUES)

    # Read and display line position, derivative, and shape
    for i in range(100):
        pos, der, shape = sensor.position_derivative_shape()
        print(f"Position: {pos}, Derivative: {der}, Shape: {shape}")
        sleep(0.1)