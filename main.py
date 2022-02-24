import threading
import queue
import time
import datetime
import logging
import random
import sys
import os

from numpy import NaN

# Import Grove stuff
# TODO: Doresit snimani tlaku
import seeed_dht
import seeed_sgp30
from grove.i2c import Bus
from grove.factory import Factory
from grove.grove_sound_sensor import GroveSoundSensor
from grove.grove_light_sensor_v1_2 import GroveLightSensor
import grove.grove_temperature_humidity_sensor_sht3x as seed_sht31

# Import camera stuff
from picamera import PiCamera

# Initialize global variables
BUF_SIZE = 10
q_ctl = queue.Queue(BUF_SIZE)

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)


class SensorThread(threading.Thread):
    def __init__(self, name):
        super(SensorThread,self).__init__()
        self.name = name

        # TODO: Pridat nacitani portu z ini souboru
        self.relay = Factory.getGpioWrapper("Relay", 5)
        try:
            self.SGP30 = seeed_sgp30.grove_sgp30(bus=Bus(1))
            self.DHT11_1 = seeed_dht.DHT("11", 16)
            self.DHT11_2 = seeed_dht.DHT("11", 16)
            self.SHT31 = seed_sht31.GroveTemperatureHumiditySensorSHT3x(bus=Bus(1))
            # TODO: Doresit snimani tlaku
            self.daylg = GroveLightSensor(1)
        except:
            timeStamp = datetime.datetime.now()
            logging.error(timeStamp, ': Sensor initialization failure.')

        # Open the log file and create header
        # TODO: Pouzit csv writer?
        try:
            self.logSens = open('SensorLog.csv', "a+")
            self.logSens.write("Timestamp,CO2_eq (ppm),TVOC (ppb),TempIn_1 (°C),HumIn_1 (%),TempIn_2 (°C),HumIn_2 (%),TempOut (°C),HumOut (%),Pressure (hPa),Light (-)")
        except:
            logging.error(timeStamp, ': Initialization of the log file failed.')

    def run(self):
        # Get the sensor data
        timeStamp = datetime.datetime.now()

        try:
            gData = self.SGP30.read_measurements()
            co2_eq_ppm, tvoc_ppb = gData.data
        except:
            logging.error(timeStamp, ': Gass sensor (I2C) failure.')
            co2_eq_ppm = NaN
            tvoc_ppb = NaN

        try:
            HumIn_1, TempIn_1 = self.DHT11_1.read()
            HumIn_2, TempIn_2 = self.DHT11_2.read()
        except:
            logging.error(timeStamp, ': DHT11 sensor (I2C) failure.')
            HumIn_1 = NaN
            HumIn_1 = NaN
            TempIn_1 = NaN
            TempIn_1 = NaN

        try:
            TempOut, HumOut = self.SHT31.read()
            # TODO: Doresit snimani tlaku
        except:
            logging.error(timeStamp, ': Atmosphere sensor (I2C) failure.')
            TempOut = NaN
            HumOut = NaN

        try:
            Light = self.daylg.light
        except:
            logging.error(timeStamp, ': Grove hat I2C failure.')
            Light = NaN
        
        # Create log
        try:
            self.logSens.write(timeStamp, ",", co2_eq_ppm, ",", tvoc_ppb, ",", TempIn_1, ",", HumIn_1, ",", TempIn_2, ",", HumIn_2, ",", TempOut, ",", HumOut, ",", "Pressure", ",", Light)
            logging.info(timeStamp, ': Sensor data were writen to the log.')
        except:
            logging.error(timeStamp, ': Writing to log file failed.')

        # Call the thread periodicaly
        # TODO: nacitat periodu z ini souboru
        threading.Timer(300, self.run).start()


class MicrophoneThread(threading.Thread):
    def __init__(self, name):
        super(MicrophoneThread,self).__init__()
        self.name = name

        # TODO: Pridat nacitani portu z ini souboru
        self.microphone = GroveSoundSensor(2)

    def run(self):
        sound = self.microphone.sound


class CameraThread(threading.Thread):
    def __init__(self, name):
        super(CameraThread,self).__init__()
        self.name = name

        # TODO: Pridat nacitani portu z ini souboru
        self.camera = PiCamera()

    def run(self):
        self.camera.start_preview()

    def stop(self):
        self.camera.stop_preview()

class ConsumerThread(threading.Thread):
    def __init__(self, name):
        super(ConsumerThread,self).__init__()
        self.name = name
        return

    def run(self):
        while not q_ctl.empty():
            float_value1 = q_ctl.get()
            sqr_value1 = float_value1 * float_value1
            log1.write("The square of " + str(float_value1) + " is " + str(sqr_value1))
            logging.debug('Getting ' + str(float_value1) + ' : ' + str(q_ctl.qsize()) + ' items in queue')
            time.sleep(random.random())
        return

if __name__ == '__main__':

    p = SensorThread(name='producer')
    c = ConsumerThread(name='consumer')

    p.start()
    time.sleep(2)
    c.start()
    time.sleep(2)