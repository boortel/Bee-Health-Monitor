import time
import sys
import os

import piqmp6988 as QMP6988
import grove.grove_temperature_humidity_sensor_sht3x as seed_sht31
from grove.i2c import Bus

config = {
    'temperature' : QMP6988.Oversampling.X4.value,
    'pressure' :    QMP6988.Oversampling.X32.value,
    'filter' :      QMP6988.Filter.COEFFECT_32.value,
    'mode' :        QMP6988.Powermode.NORMAL.value
}

def main():
    sht31 = seed_sht31.GroveTemperatureHumiditySensorSHT3x(bus=Bus(1))

    while True:
        temperatureS, humidity = sht31.read()
        print("\r  Temperature SHT = {:05.2f} *C Humidity = {:05.2f} %  ".format(temperatureS, humidity))

        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)