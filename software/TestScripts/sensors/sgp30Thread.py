import queue
import threading

from numpy import NaN

# Import the sensor libraries
from sensors.sgp30 import SGP30
from sensors.dht20 import DHT20
from sensors.sht31 import SHT31
from sensors.gy302 import GY302
from sensors.piqmp6988SM import piqmp6988SM as QMP6988

# Global variable to stop sensor logging
SGP30Status = True

# Event to stop the SGP30Thread internal loop
eventSGP30_run = threading.Event()

# Queue and its control event to send SGP30 data
BUFF = 1
queueSGP30 = queue.Queue(BUFF)
eventSGP30_read = threading.Event()

# Configuration of the QMP6988 atmospheric pressure sensor
config = {
    'temperature' : QMP6988.Oversampling.X4.value,
    'pressure' :    QMP6988.Oversampling.X32.value,
    'filter' :      QMP6988.Filter.COEFFECT_32.value,
    'mode' :        QMP6988.Powermode.NORMAL.value
}

# SGP30 sensor has to be run every 1s in background to ensure a correct online calibration 

# Sensor handle thread
class SGP30Thread(threading.Thread):
    def __init__(self):
        super(SGP30Thread,self).__init__()
        eventSGP30_run.set()
        
        # Create the sensor objects
        self.sht31 = SHT31(0x01, 0x44)
        self.dht20 = DHT20(0x01, 0x38)
        self.sgp30 = SGP30(0x01, 0x58)
        self.gy302 = GY302(0x01, 0x23)
        self.qmp = QMP6988.PiQmp6988(0x01, config)
        
        # Initialize the sensors
        if not self.sht31.begin():
            print("SHT31 sensor initialization failed") 
        if not self.dht20.begin():
            print("DHT20 sensor initialization failed")
        if not self.sgp30.begin():
            print("SGP30 sensor initialization failed")
        if not self.gy302.begin():
            print("GY302 sensor initialization failed")

    def run(self):
        # This loop is run until stopped from SensorThread
        while eventSGP30_run.is_set():
    
            # Get the data from SGP30
            co2_eq_ppm, tvoc_ppb, sgp_error = self.sgp30.get_air_quality()
            if sgp_error:
                co2_eq_ppm = NaN
                tvoc_ppb = NaN
                print("SGP30 CRC error")
            
            # DHT20 - inner temperature and humidity
            TempIn, HumIn, dht_error = self.dht20.get_temperature_and_humidity()
            if dht_error:
                TempIn = NaN
                HumIn = NaN
                print("DHT20 CRC error")

            # SHT31 - outer temperature, humidity and pressure
            TempOut, HumOut, sht_err = self.sht31.get_temperature_and_humidity()
            if sht_err:
                TempOut = NaN
                HumOut = NaN
                print("SHT31 CRC error")
                
            # GY302 - light intensity
            LightOut = self.gy302.read_light()
            if LightOut = -1:
                LightOut = NaN
                print("GY302 reading error")
            
            # QMP6988 - outer temperature, atmospheric pressure
            values = self.qmp.read()
            #TempOut = values['temperature']
            PressOut = values['pressure']
            if PressOut == False:
                PressOut = NaN
                print("QMP6988 reading error")


            # Put the data to the queue
            if eventSGP30_read.is_set():
                queueSGP30.put([co2_eq_ppm, tvoc_ppb])
                eventSGP30_read.clear()
                