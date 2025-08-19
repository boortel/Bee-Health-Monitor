# -*- coding: utf-8 -*

"""
### Raspberry Pi Python library for DHT20 Temperature and Humidity Sensor with CRC verification.
### https://github.com/cjee21/RPi-DHT20

Originally from https://github.com/DFRobot/DFRobot_DHT20/tree/master/python/raspberrypi

| Modified by https://github.com/cjee21/
| MIT License
| Copyright (c) 2022-2023 cjee21

Modifications:
- 25 February 2022
  - use `smbus2`
  - add decimal to temperature formula
  - add `get_temperature_and_humidity` function for getting temperature and humidity in a single read
- 16 January 2023
  - correct sensor initialization check and clean up init (begin) function
  - improve `get_temperature_and_humidity` function
  - add CRC-8 checking
  - remove functions no longer needed
  - add debug logging
- 18 August 2025
  - improved error handling

Note:
  Sensor initialization and CRC-8 calculation is based on Aosong sample code from
  http://aosong.com/userfiles/files/software/AHT20-21%20DEMO%20V1_3(1).rar

Original:
  *@file DFRobot_DHT20.py
  *@brief Define the basic structure of class DFRobot_DHT20
  *@copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  *@licence     The MIT License (MIT)
  *@author [fengli](li.feng@dfrobot.com)
  *@version  V1.0
  *@date  2021-6-25
  *@get from https://www.dfrobot.com
  *@https://github.com/DFRobot/DFRobot_DHT20
"""

import os
import sys
import time
import logging

import smbus2 as smbus

from numpy import NaN

                
class DHT20(object):
    ''' Conversion data '''

    def __init__(self, bus: int, address: int) -> None:
        """Initialize the class.

        Args:
        bus: The I2C bus that DHT20 is connected to. For example:
          0x01
        address: The I2C address of DHT20. It is:
          0x38
        """
        self.i2cbus = smbus.SMBus(bus)
        self._addr = address


    def begin(self) -> bool:
        """Sensor initialization.

        Returns:
        True if initialization succeeds, otherwise False.
        """

        # After power-on, wait no less than 100ms
        time.sleep(0.5)

        try:
            data = self.__read_reg(0x71,1)
            time.sleep(0.01)
        except Exception as e:
            logging.error(": DHT20 sensor initialization failed: %s", e)
            return False
        
        if (data[0] & 0x18) != 0x18:
            logging.error(": DHT20 sensor initialization was not successful: %s", e)
            return False
        else:
            return True


    def get_temperature_and_humidity(self) -> tuple[float, float, bool]:
        """Get both temperature and humidity in a single read.

        [!] Do not call this function more often than 2 seconds as recommended by the
        datasheet to prevent rise in sensor temperature that will affect its accuracy. 

        Returns:
        The temperature (±0.5℃), humidity (±3%) and 
        CRC result (True if error else False) as a tuple.
        """

        # Trigger measurement
        try:
            self.__write_reg(0xac,[0x33,0x00])
        except Exception as e:
            logging.error(": DHT20 failed to send measurement command: %s", e)
            return (NaN, NaN, False)

        # Read sensor data
        try:
            # Wait 80 ms and keep waiting until the measurement is completed. Read sensor data afterwards.
            while True:
                time.sleep(0.08)
                data = self.__read_reg(0x71,1)
                if (data[0] & 0x80) == 0:
                    break
                
            data = self.__read_reg(0x71,7)
        except Exception as e:
            logging.error(": DHT20 failed to read data: %s", e)
            return (NaN, NaN, False)

        # Extract and convert temperature and humidity from data
        temperature_rawData: int = ((data[3]&0xf) << 16) + (data[4] << 8) + data[5]
        humidity_rawData: int = ((data[3]&0xf0) >> 4) + (data[1] << 12) + (data[2] << 4)
        temperature: float = float(temperature_rawData) / 5242.88 - 50
        humidity: float = float(humidity_rawData) / 0x100000 * 100

        logging.debug(f"Raw data : {[hex(b) for b in data]}")
        logging.debug("Read CRC      : " + hex(data[6]))
        logging.debug("Calculated CRC: " + hex(self.__calc_CRC8(data)))
        logging.debug(f"Temperature  : {temperature} °C")
        logging.debug(f"Humidity     : {humidity} %")
        
        # Check CRC
        crc_error: bool = self.__calc_CRC8(data) != data[6]
        if crc_error:
            logging.warning(": DHT20 CRC check failed")
            return (NaN, NaN, True)

        return (temperature, humidity, crc_error)


    def __calc_CRC8(self, data: list[int]) -> int:
        """Calculate CRC-8.

        Args:
        data: Data from sensor which its CRC-8 is to be calculated.

        Returns:
        Calculated CRC-8
        """

        crc: int = 0xFF

        for i in data[:-1]:
            crc ^= i
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1)^0x31
                else:
                    crc = crc << 1

        return (crc & 0xFF)


    def __write_reg(self, reg: int, data: list[int]) -> None:
        time.sleep(0.01)
        self.i2cbus.write_i2c_block_data(self._addr,reg,data)


    def __read_reg(self, reg: int, len: int) -> list[int]:
        time.sleep(0.01)
        rslt: list[int] = self.i2cbus.read_i2c_block_data(self._addr,reg,len)
        return rslt
    