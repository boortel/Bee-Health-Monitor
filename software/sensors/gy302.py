import time
import logging
import smbus2 as smbus

from numpy import NaN

class GY302:
    """GY-302 / BH1750 Light Sensor driver"""

    # BH1750 I2C address (default)
    DEFAULT_ADDRESS = 0x23

    # BH1750 commands
    POWER_DOWN = 0x00
    POWER_ON = 0x01
    RESET = 0x07

    # Measurement modes
    CONT_H_RES_MODE = 0x10      # Continuous high resolution (1 lx, 120ms)
    CONT_H_RES_MODE2 = 0x11     # Continuous high res mode 2 (0.5 lx, 120ms)
    CONT_L_RES_MODE = 0x13      # Continuous low resolution (4 lx, 16ms)
    ONE_TIME_H_RES_MODE = 0x20  # One-time high resolution (1 lx, 120ms)
    ONE_TIME_H_RES_MODE2 = 0x21 # One-time high res mode 2 (0.5 lx, 120ms)
    ONE_TIME_L_RES_MODE = 0x23  # One-time low resolution (4 lx, 16ms)

    def __init__(self, bus: int = 1, address: int = DEFAULT_ADDRESS):
        """Initialize the GY-302 sensor on the given I2C bus and address."""
        self.i2cbus = smbus.SMBus(bus)
        self._addr = address

    def begin(self) -> bool:
        """Initialize sensor. Return True if successful."""
        try:
            self.i2cbus.write_byte(self._addr, self.POWER_ON)
            time.sleep(0.01)
            self.i2cbus.write_byte(self._addr, self.RESET)
            time.sleep(0.01)
            return True
        except Exception as e:
            logging.error(": GY302 sensor initialization failed: %s", e)
            return False

    def read_light(self, mode: int = CONT_H_RES_MODE) -> float:
        """Read light intensity in lux.

        Args:
            mode: BH1750 mode (default is CONT_H_RES_MODE)

        Returns:
            Light level in lux as float.
        """
        try:
            self.i2cbus.write_byte(self._addr, mode)
        except Exception as e:
            logging.error(": GY302 failed to send measurement command: %s", e)
            return (NaN)
        
        if mode in [self.ONE_TIME_H_RES_MODE, self.ONE_TIME_H_RES_MODE2]:
            time.sleep(0.18)  # Wait for measurement (max 180ms)
        elif mode == self.ONE_TIME_L_RES_MODE:
            time.sleep(0.024)  # Wait for measurement (max 24ms)
        else:
            time.sleep(0.18)  # Continuous modes still need delay for first read
        
        try:
            data = self.i2cbus.read_i2c_block_data(self._addr, 0x00, 2)
        except Exception as e:
            logging.error(": GY302 failed to read data: %s", e)
            return (NaN)
        
        raw = (data[0] << 8) + data[1]
        lux = raw / 1.2  # Convert to lux

        logging.debug(f"Raw data : {[hex(b) for b in data]}")
        logging.debug("Light intensity: %.2f lux", lux)

        return lux
