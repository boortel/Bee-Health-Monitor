import os
import sys
import time
import logging

from numpy import NaN

# Import the sensor libraries
from sensors.sgp30 import SGP30
from sensors.dht20 import DHT20
from sensors.sht31 import SHT31
from sensors.gy302 import GY302

import sensors.piqmp6988SM as QMP6988

# Debug logging
logging.basicConfig()
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)  # Uncomment to enable debug logging

# Configuration of the QMP6988 atmospheric pressure sensor
config = {
    'temperature' : QMP6988.Oversampling.X4.value,
    'pressure' :    QMP6988.Oversampling.X32.value,
    'filter' :      QMP6988.Filter.COEFFECT_32.value,
    'mode' :        QMP6988.Powermode.NORMAL.value
}

# SGP30 sensor has to be run every 1s in background to ensure a correct online calibration 

# Read data from all sensors
def main():
    
    # Create the sensor objects
    sht31 = SHT31(0x01, 0x44)
    dht20 = DHT20(0x01, 0x38)
    sgp30 = SGP30(0x01, 0x58)
    #self.gy302 = GY302(0x01, 0x23)
    qmp = QMP6988.PiQmp6988(0x01, config)
    
    # Initialize the sensors
    if not sht31.begin():
        print("SHT31 sensor initialization failed") 
    if not dht20.begin():
        print("DHT20 sensor initialization failed")
    if not sgp30.begin():
        print("SGP30 sensor initialization failed")
    #if not gy302.begin():
    #    print("GY302 sensor initialization failed")


    while True:
        # Get the measurement start time
        measurement_duration_start = time.time()
            
        # Get the data from SGP30
        co2_eq_ppm, tvoc_ppb, sgp_error = sgp30.get_air_quality()
        if sgp_error:
            co2_eq_ppm = NaN
            tvoc_ppb = NaN
            print("SGP30 CRC error\n")
        else:
            print(f"eCO2                  : {co2_eq_ppm} ppm")
            print(f"TVOC                  : {tvoc_ppb} ppb")
            print("SGP30 CRC             : OK\n")
        
        # DHT20 - inner temperature and humidity
        TempIn, HumIn, dht_error = dht20.get_temperature_and_humidity()
        if dht_error:
            TempIn = NaN
            HumIn = NaN
            print("DHT20 CRC error\n")
        else:
            print(f"Temperature           : {TempIn:.2f}°C")
            print(f"Relative Humidity     : {HumIn:.2f} %")
            print("DHT20 CRC             : OK\n")

        # SHT31 - outer temperature, humidity and pressure
        TempOut, HumOut, sht_err = sht31.get_temperature_and_humidity()
        if sht_err:
            TempOut = NaN
            HumOut = NaN
            print("SHT31 CRC error\n")
        else:
            print(f"Temperature           : {TempOut:.2f}°C")
            print(f"Relative Humidity     : {HumOut:.2f} %")
            print("SHT31 CRC             : OK\n")
            
        # GY302 - light intensity
        #LightOut = gy302.read_light()
        #if LightOut = -1:
        #    LightOut = NaN
        #    print("GY302 reading error")
        #else:
        #    print(f"Light intensity      : {LightOut:.2f} lux\n")
        
        # QMP6988 - outer temperature, atmospheric pressure
        values = qmp.read()
        TempOutBMP = values['temperature']
        PressOut = values['pressure']
        if PressOut == False:
            PressOut = NaN
            print("QMP6988 reading error")
        else:
            print(f"Temperature BMP       : {TempOutBMP:.2f} °C")
            print(f"Pressure BMP          : {PressOut:.2f} hPa\n")
            
        # Get the end time and the time difference to sleep
        measurement_duration_stop = time.time()
        measurement_duration = measurement_duration_stop - measurement_duration_start
        
        print(f"Script running time   : {measurement_duration:.2f} s\n")
        if (1 - measurement_duration) > 0:
            time.sleep(1 - measurement_duration)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)