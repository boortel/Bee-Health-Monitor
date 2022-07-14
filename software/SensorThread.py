import threading
import datetime
import logging
import time
import csv

# Import the sensors
from Microphone import Microphone
from SGP30Thread import SGP30Thread, stopSGP30Thread, queueSGP30, eventSGP30
from Sensors import DHT11, SHT31, LightS

# Import the bee counters
from BeeCounter.BeeCounterThread import eventBeeCounterRead, queueBeeCounterRead

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
        self.SHT31_1 = SHT31(1)
        self.Light_1 = LightS(1, config.getint('Sensors', 'port_LightS_1'))

        # Initialize the microphone
        self.recordTime = config.getint('Sensors', 'recordTime')
        self.microphone = Microphone(self.recordTime, baseLog)

        # Initialize and run the SGP30Thread
        self.sgp30T = SGP30Thread()
        self.sgp30T.start()

        # Open the log file and create header
        try:
            self.fileName = baseLog + '/SensorLog' + '.csv'

            # Open the csv and write header
            row = ['Timestamp', 'CO2_eq (ppm)', 'TVOC (ppb)', 'TempIn_1 (°C)', 'HumIn_1 (%)', 'TempIn_2 (°C)', 'HumIn_2 (%)', 'TempOut (°C)', 'HumOut (%)', 'Pressure (hPa)', 'Light (-)', 'BeeIn (-)', 'BeeOut (-)']
            with open(self.fileName, 'w', newline = '') as csvFile:
                writer = csv.writer(csvFile, delimiter =';')
                writer.writerow(row)
        except:
            logging.error(': Initialization of the log file failed.')

    def __del__(self):
        # Stop the SGP30 thread
        stopSGP30Thread(True)

    def run(self):
        # This loop is run until stopped from main
        while sensLogStatus:
            # Get the start time
            t1 = time.time()

            # Get the sensor data
            now = datetime.datetime.now()
            timeStampM = now.strftime("%y.%m.%d %H:%M:%S")

            # SGP30 - gass sensor
            eventSGP30.set()
            co2_eq_ppm, tvoc_ppb = queueSGP30.get()

            # DHT11 - inner temperature and humidity
            HumIn_1, TempIn_1 = self.DHT11_1.measure()
            HumIn_2, TempIn_2 = self.DHT11_2.measure()

            # SHT31 - outer temperature, humidity and pressure
            TempOut, HumOut, PressOut = self.SHT31_1.measure()

            # Light sensor value
            Light = self.Light_1.measure()

            # Get the bee counters
            eventBeeCounterRead.set()
            BeeIn, BeeOut = queueBeeCounterRead.get()
            
            # Create log
            row = [f'{timeStampM:s}', f'{co2_eq_ppm}', f'{tvoc_ppb}', f'{float(TempIn_1):.2f}', 
                f'{float(HumIn_1):.2f}', f'{float(TempIn_2):.2f}', f'{float(HumIn_2):.2f}', 
                f'{float(TempOut):.2f}', f'{float(HumOut):.2f}', f'{PressOut}', f'{Light}',
                f'{BeeIn}', f'{BeeOut}']

            try:    
                with open(self.fileName, 'a', newline = '') as csvFile:
                    writer = csv.writer(csvFile, delimiter =';')
                    writer.writerow(row)

                logging.info(': Sensor data were writen to the log.')
                self.errorLog = 0
            except:
                if self.errorLog == 0:
                    logging.error(': Writing to log file failed.')
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
                logging.warning(': Set period time was exceeded during the current iteration.')

