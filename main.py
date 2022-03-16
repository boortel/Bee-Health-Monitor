import configparser
import threading
import datetime
import logging
import random
import queue
import time
import csv
import sys
import os

from numpy import NaN
from Camera import Camera
from Microphone import Microphone
from Sensors import DHT11, SGP30, SHT31, LightS

# Initialize program logging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

# Open the ini file
config = configparser.ConfigParser()
config.read('BeeLogger.ini')

class SensorThread(threading.Thread):
    def __init__(self, name):
        super(SensorThread,self).__init__()

        self.errorLog = 0
        self.name = name

        self.periodSensor = config.getint('Sensors', 'period_threadSensors')

        # Initialize the sensors objects
        self.DHT11_1 = DHT11(1, config.getint('Sensors', 'port_DHT11_1'))
        self.DHT11_2 = DHT11(2, config.getint('Sensors', 'port_DHT11_2'))
        self.SGP30_1 = SGP30(1)
        self.SHT31_1 = SHT31(1)
        self.Light_1 = LightS(1, config.getint('Sensors', 'port_LightS_1'))

        # Initialize the microphone
        self.recordTime = config.getint('Sensors', 'recordTime')
        self.microphone = Microphone(self.recordTime)

        # Open the log file and create header
        try:
            now = datetime.datetime.now()
            timeString = now.strftime("%y%m%d_%H%M")
            fileName = 'log/SensorLog_' + timeString + '.csv'

            with open(fileName, 'w') as f:
                # create the csv writer
                self.writer = csv.writer(f)

            row = ['Timestamp', 'CO2_eq (ppm)', 'TVOC (ppb)', 'TempIn_1 (°C)', 'HumIn_1 (%)', 'TempIn_2 (°C)', 'HumIn_2 (%)', 'TempOut (°C)', 'HumOut (%)', 'Pressure (hPa)', 'Light (-)']
            self.writer.writerow(row)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Initialization of the log file failed.')

    def run(self):
        # Get the sensor data
        timeStamp = datetime.datetime.now()

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
        try:
            row = [timeStamp, co2_eq_ppm, tvoc_ppb, TempIn_1, HumIn_1, TempIn_2, HumIn_2, TempOut, HumOut, PressOut, Light]
            self.writer.writerow(row)

            logging.info(timeStamp, ': Sensor data were writen to the log.')
            self.errorLog = 0
        except:
            if self.errorLog == 0:
                logging.error(timeStamp, ': Writing to log file failed.')
                self.errorLog = 1

        # Record the sound
        self.microphone.record()

        # Call the thread periodicaly
        threading.Timer(self.periodSensor, self.run).start()


class CameraThread(threading.Thread):
    def __init__(self, name):
        super(CameraThread,self).__init__()
        self.name = name

        # TODO: Pridat nacitani konfiguraci z ini souboru
        self.camera = Camera()

    def run(self):
        self.camera.start_preview()


class ControlThread(threading.Thread):
    def __init__(self, name):
        super(ControlThread, self).__init__()
        self.name = name
        return

    def run(self):
        while not q_ctl.empty():
            float_value1 = q_ctl.get()

            logging.debug('Getting ' + str(float_value1) + ' : ' + str(q_ctl.qsize()) + ' items in queue')
            time.sleep(random.random())
        return


if __name__ == '__main__':

    BUF_SIZE = 10
    q_ctl = queue.Queue(BUF_SIZE)

    p = SensorThread(name='producer')
    c = ControlThread(name='consumer')

    p.start()
    time.sleep(2)
    c.start()
    time.sleep(2)