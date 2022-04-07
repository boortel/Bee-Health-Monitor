import threading
import datetime
import logging
import time
import csv

# Import the sensors
from Microphone import Microphone
from Sensors import DHT11, SGP30, SHT31, LightS

# Global variable to stop sensor logging
sensLogStatus = True

# Function to stop the SensorThread internal loop
def stopSenThread():
    global sensLogStatus
    sensLogStatus = False


# Sensor handle thread
class SensorThread(threading.Thread):
    def __init__(self, name, baseLog, config):
        super(SensorThread,self).__init__()

        self.name = name
        self.errorLog = 0

        self.periodSensor = config.getint('Sensors', 'period_threadSensors')

        # Initialize the sensors objects
        self.DHT11_1 = DHT11(1, config.getint('Sensors', 'port_DHT11_1'))
        self.DHT11_2 = DHT11(2, config.getint('Sensors', 'port_DHT11_2'))
        self.SGP30_1 = SGP30(1)
        self.SHT31_1 = SHT31(1)
        self.Light_1 = LightS(1, config.getint('Sensors', 'port_LightS_1'))

        # Initialize the microphone
        self.recordTime = config.getint('Sensors', 'recordTime')
        self.microphone = Microphone(self.recordTime, baseLog)

        # Open the log file and create header
        try:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M")
            self.fileName = baseLog + '/SensorLog_' + timeStamp + '.csv'

            # Open the csv and write header
            row = ['Timestamp', 'CO2_eq (ppm)', 'TVOC (ppb)', 'TempIn_1 (°C)', 'HumIn_1 (%)', 'TempIn_2 (°C)', 'HumIn_2 (%)', 'TempOut (°C)', 'HumOut (%)', 'Pressure (hPa)', 'Light (-)']
            with open(self.fileName, 'w', newline = '') as csvFile:
                writer = csv.writer(csvFile, delimiter =';')
                writer.writerow(row)
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M")
            logging.error(timeStamp + ': Initialization of the log file failed.')

    def run(self):
        # This loop is run until stopped from main
        while sensLogStatus:
            # Get the start time
            t1 = time.time()

            # Get the sensor data
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M%S")
            timeStampM = now.strftime("%y.%m.%d_%H:%M:%S")

            # SGP30 - gass sensor
            co2_eq_ppm, tvoc_ppb = self.SGP30_1.measure()

            # DHT11 - inner temperature and humidity
            HumIn_1, TempIn_1 = self.DHT11_1.measure()
            HumIn_2, TempIn_2 = self.DHT11_2.measure()

            # SHT31 - outer temperature, humidity and pressure
            TempOut, HumOut, PressOut = self.SHT31_1.measure()

            # Light sensor value
            Light = self.Light_1.measure()
            
            # Create log
            row = [f'{timeStampM:s}', f'{co2_eq_ppm}', f'{tvoc_ppb}', f'{float(TempIn_1):.2f}', 
                f'{float(HumIn_1):.2f}', f'{float(TempIn_2):.2f}', f'{float(HumIn_2):.2f}', 
                f'{float(TempOut):.2f}', f'{float(HumOut):.2f}', f'{PressOut}', f'{Light}']

            try:    
                with open(self.fileName, 'a', newline = '') as csvFile:
                    writer = csv.writer(csvFile, delimiter =';')
                    writer.writerow(row)

                logging.info(timeStamp + ': Sensor data were writen to the log.')
                self.errorLog = 0
            except:
                if self.errorLog == 0:
                    logging.error(timeStamp + ': Writing to log file failed.')
                    self.errorLog = 1

            # Record the sound
            self.microphone.record()

            # Get the end time and sleep till the next period
            t2 = time.time()
            diff = t2 - t1

            if diff < self.periodSensor:
                while (diff < self.periodSensor) and sensLogStatus:
                    time.sleep(0.1)
                    t2 = time.time()
                    diff = t2 - t1
            else:
                logging.warning(timeStamp + ': Set period time was exceeded during the current iteration.')

