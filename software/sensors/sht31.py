import os
import sys
import time
import logging
import smbus2 as smbus


class SHT31:
    def __init__(self, bus: int, address: int) -> None:
        """Initialize the class for SHT31 sensor.

        Args:
            bus: I2C bus number (e.g., 1)
            address: I2C address of the sensor (default 0x44 or 0x45)
        """
        self.i2cbus = smbus.SMBus(bus)
        self._addr = address

    def begin(self) -> bool:
        """Initialize the sensor.

        Returns:
            True if initialization succeeds.
        """
        # Soft reset
        try:
            self.i2cbus.write_i2c_block_data(self._addr, 0x30, [0xA2])
            time.sleep(0.01)
            return True
        except Exception as e:
            logging.error("Sensor initialization failed: %s", e)
            return False

    def get_temperature_and_humidity(self) -> tuple[float, float, bool]:
        """Read temperature and humidity from the sensor.

        Returns:
            Tuple containing temperature in Celsius, relative humidity, and CRC status (False = OK, True = error).
        """
        # Send measurement command (High repeatability, clock stretching disabled)
        try:
            self.i2cbus.write_i2c_block_data(self._addr, 0x24, [0x00])
        except Exception as e:
            logging.error("Failed to send measurement command: %s", e)
            return (0.0, 0.0, True)

        time.sleep(0.015)  # Wait for measurement

        try:
            data = self.i2cbus.read_i2c_block_data(self._addr, 0x00, 6)
        except Exception as e:
            logging.error("Failed to read data: %s", e)
            return (0.0, 0.0, True)

        # Unpack data
        temp_raw = data[0] << 8 | data[1]
        temp_crc = data[2]
        hum_raw = data[3] << 8 | data[4]
        hum_crc = data[5]

        # CRC check
        if self.__crc8(data[0:2]) != temp_crc or self.__crc8(data[3:5]) != hum_crc:
            logging.warning("CRC check failed")
            return (0.0, 0.0, True)

        # Convert to temperature and humidity
        temperature = -45 + (175 * temp_raw / 65535.0)
        humidity = 100 * hum_raw / 65535.0

        logging.debug(f"Temperature: {temperature:.2f}°C, Humidity: {humidity:.2f}%, CRC OK")
        return (temperature, humidity, False)

    def __crc8(self, data: list[int]) -> int:
        """Calculate CRC8 for 2 bytes.

        Args:
            data: List of 2 bytes

        Returns:
            Calculated CRC byte
        """
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    