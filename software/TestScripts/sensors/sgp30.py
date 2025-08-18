import os
import sys
import time
import logging

import smbus2 as smbus

# Debug logging
logging.basicConfig()
logger = logging.getLogger(__name__)
# Uncomment to enable debug logging
# logger.setLevel(logging.DEBUG)

class SGP30:
    def __init__(self, bus: int, address: int = 0x58) -> None:
        """Initialize the class.

        Args:
            bus: The I2C bus that SGP30 is connected to (e.g., 0x01)
            address: The I2C address of SGP30 (default 0x58)
        """
        self.i2cbus = smbus.SMBus(bus)
        self._addr = address

    def begin(self) -> bool:
        """Initialize the SGP30 sensor.

        Returns:
            True if initialization succeeds.
        """
        try:
            # Send "Init Air Quality" command (0x20 0x03)
            self.__write_cmd([0x20, 0x03])
            time.sleep(0.01)
            return True
        except Exception as e:
            logger.error(f"SGP30 init failed: {e}")
            return False

    def get_air_quality(self) -> tuple[int, int, bool]:
        """Read eCO₂ and TVOC values.

        Returns:
            Tuple: (eCO2 ppm, TVOC ppb, CRC error flag)
        """
        self.__write_cmd([0x20, 0x08])  # Measure Air Quality command
        time.sleep(0.05)

        try:
            data = self.i2cbus.read_i2c_block_data(self._addr, 0, 6)
            eCO2 = (data[0] << 8) | data[1]
            eCO2_crc_ok = self.__check_crc(data[0:2], data[2])

            TVOC = (data[3] << 8) | data[4]
            TVOC_crc_ok = self.__check_crc(data[3:5], data[5])

            crc_error = not (eCO2_crc_ok and TVOC_crc_ok)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Raw data : {[hex(b) for b in data]}")
                logger.debug(f"eCO2     : {eCO2} ppm, CRC OK: {eCO2_crc_ok}")
                logger.debug(f"TVOC     : {TVOC} ppb, CRC OK: {TVOC_crc_ok}")

            return (eCO2, TVOC, crc_error)
        except Exception as e:
            logger.error(f"Failed to read air quality: {e}")
            return (0, 0, True)

    def __check_crc(self, data: list[int], crc: int) -> bool:
        """Check CRC of 2-byte data using 0x31 polynomial."""
        calc_crc = 0xFF
        for byte in data:
            calc_crc ^= byte
            for _ in range(8):
                if calc_crc & 0x80:
                    calc_crc = ((calc_crc << 1) ^ 0x31) & 0xFF
                else:
                    calc_crc = (calc_crc << 1) & 0xFF
        return calc_crc == crc

    def __write_cmd(self, cmd: list[int]) -> None:
        """Write a command to the sensor."""
        self.i2cbus.write_i2c_block_data(self._addr, cmd[0], cmd[1:])
        