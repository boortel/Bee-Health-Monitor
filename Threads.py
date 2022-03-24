import threading
import datetime
import logging
import csv

# Import the sensors
from Camera import Camera
from Microphone import Microphone
from Sensors import DHT11, SGP30, SHT31, LightS


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
                writer = csv.writer(csvFile)
                writer.writerow(row)
        except:
            now = datetime.datetime.now()
            timeStamp = now.strftime("%y%m%d_%H%M")
            logging.error(timeStamp + ': Initialization of the log file failed.')

    def run(self):
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
                writer = csv.writer(csvFile)
                writer.writerow(row)

            logging.info(timeStamp + ': Sensor data were writen to the log.')
            self.errorLog = 0
        except:
            if self.errorLog == 0:
                logging.error(timeStamp + ': Writing to log file failed.')
                self.errorLog = 1

        # Record the sound
        self.microphone.record()

# Camera handle thread
class CameraThread(threading.Thread):
    def __init__(self, name, baseLog, config):
        super(CameraThread,self).__init__()
        self.name = name

        # Load the cfg from the ini-file
        fps = config.getint('Camera', 'fps')
        exp = config.getint('Camera', 'exp')
        iso = config.getint('Camera', 'iso')
        ROI = [config.getfloat('Camera', 'x'), config.getfloat('Camera', 'y'), \
               config.getfloat('Camera', 'w'), config.getfloat('Camera', 'h')]

        self.camera = Camera(fps, exp, iso, ROI, baseLog)

    def run(self):
        self.camera.capture()